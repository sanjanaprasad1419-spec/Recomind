import os
from django.http import HttpResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status, generics

from .models import Note, Syllabus
from .serializers import (
    NoteSerializer, NoteUploadSerializer, 
    SyllabusSerializer, SyllabusUploadSerializer,
    DomainPredictionSerializer, NoteAnalysisSerializer, NoteEnhancementSerializer,
    TopicNotesGenerationSerializer,
)
from .services import (
    process_note_ocr, predict_domain, analyze_notes_against_syllabus,
    extract_syllabus_text, parse_syllabus_into_units, analyze_notes_mvp
)
from .services.gemini_ai_coverage import analyze_notes_coverage_ai
from .services.ai_notes_enhancer import enhance_notes_with_ai
from .services.gemini_topic_notes import generate_topic_notes, TopicNotesGenerationError
from .services.pdf_generator import generate_analysis_pdf



@api_view(['GET'])
def health_check(request):
    """
    Health-check endpoint for testing frontend-backend connectivity.
    """
    return Response({"status": "healthy", "message": "RecoMind Backend API is running smoothly."}, status=status.HTTP_200_OK)


# ==============================================================================
# NOTE MANAGEMENT ENDPOINTS
# ==============================================================================

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_note(request):
    """
    API endpoint for uploading study notes files (PDF, DOCX, JPG, JPEG, PNG).
    """
    serializer = NoteUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = serializer.validated_data['file']
    edu_level = serializer.validated_data.get('education_level', '')
    subj_domain = serializer.validated_data.get('subject_domain', '')
    user_topic = serializer.validated_data.get('topic', '')

    ext = os.path.splitext(uploaded_file.name)[1].lower().replace('.', '')

    note = Note.objects.create(
        uploaded_file=uploaded_file,
        original_filename=uploaded_file.name,
        file_type=ext,
        education_level=edu_level,
        subject_domain=subj_domain,
        topic=user_topic
    )

    try:
        extracted_text = process_note_ocr(note.uploaded_file.path, ext)
        note.extracted_text = extracted_text
        note.status = 'PROCESSED'
        note.save()
    except Exception as e:
        note.status = 'FAILED'
        note.save()
        return Response({"error": f"Failed to extract text from file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    response_serializer = NoteSerializer(note, context={'request': request})
    return Response({
        "message": "Study note uploaded and processed successfully.",
        "note": response_serializer.data
    }, status=status.HTTP_201_CREATED)


class NoteListAPIView(generics.ListAPIView):
    """
    API endpoint to list all saved study notes.
    """
    queryset = Note.objects.all().order_by('-upload_timestamp')
    serializer_class = NoteSerializer


class NoteDetailAPIView(generics.RetrieveDestroyAPIView):
    """
    API endpoint to retrieve or delete a specific study note.
    """
    queryset = Note.objects.all()
    serializer_class = NoteSerializer


# ==============================================================================
# SYLLABUS MANAGEMENT ENDPOINTS
# ==============================================================================

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_syllabus(request):
    """
    API endpoint for uploading course syllabus files (PDF, DOCX, JPG, JPEG, PNG).
    """
    serializer = SyllabusUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = serializer.validated_data['file']
    custom_title = serializer.validated_data.get('title', '').strip()

    ext = os.path.splitext(uploaded_file.name)[1].lower().replace('.', '')

    syllabus = Syllabus.objects.create(
        uploaded_file=uploaded_file,
        original_filename=uploaded_file.name,
        file_type=ext,
        title=custom_title if custom_title else os.path.splitext(uploaded_file.name)[0].replace('_', ' ').replace('-', ' ').title()
    )

    extracted_text = extract_syllabus_text(syllabus.uploaded_file.path, ext)
    parsed_units = parse_syllabus_into_units(extracted_text)

    syllabus.extracted_text = extracted_text
    syllabus.parsed_units = parsed_units
    syllabus.save()

    response_serializer = SyllabusSerializer(syllabus, context={'request': request})
    return Response({
        "message": "Syllabus uploaded and parsed successfully.",
        "syllabus": response_serializer.data
    }, status=status.HTTP_201_CREATED)


class SyllabusListAPIView(generics.ListAPIView):
    """
    API endpoint to list all saved syllabi.
    """
    queryset = Syllabus.objects.all().order_by('-upload_timestamp')
    serializer_class = SyllabusSerializer

    def get_queryset(self):
        syllabi = list(super().get_queryset())
        for syllabus in syllabi:
            parsed_units = syllabus.parsed_units or []
            is_legacy_fallback = (
                len(parsed_units) == 1
                and "general syllabus topics" in parsed_units[0].get("title", "").lower()
            )
            if is_legacy_fallback and syllabus.extracted_text:
                syllabus.parsed_units = parse_syllabus_into_units(syllabus.extracted_text)
                syllabus.save(update_fields=["parsed_units"])
        return syllabi


class SyllabusDetailAPIView(generics.RetrieveDestroyAPIView):
    """
    API endpoint to retrieve or delete a specific saved syllabus.
    """
    queryset = Syllabus.objects.all()
    serializer_class = SyllabusSerializer


@api_view(['GET'])
def syllabus_sections_view(request, pk):
    """
    GET /api/syllabus/<pk>/sections/
    Returns dynamically parsed units, chapters, modules, and subtopics for a specific syllabus.
    """
    try:
        syllabus = Syllabus.objects.get(pk=pk)
        parsed_units = syllabus.parsed_units or []
        is_legacy_fallback = (
            len(parsed_units) == 1
            and "general syllabus topics" in parsed_units[0].get("title", "").lower()
        )
        if is_legacy_fallback and syllabus.extracted_text:
            parsed_units = parse_syllabus_into_units(syllabus.extracted_text)
            syllabus.parsed_units = parsed_units
            syllabus.save(update_fields=["parsed_units"])

        return Response({
            "syllabus_id": syllabus.id,
            "title": syllabus.title,
            "sections": parsed_units,
            "chapter_extraction_status": "success" if parsed_units else "not_detected",
        }, status=status.HTTP_200_OK)
    except Syllabus.DoesNotExist:
        return Response({"error": f"Syllabus with ID {pk} not found."}, status=status.HTTP_404_NOT_FOUND)


# ==============================================================================
# ML PREDICTION & AI ENHANCEMENT ENDPOINTS
# ==============================================================================

@api_view(['POST'])
def predict_domain_view(request):
    """
    API endpoint for broad domain prediction on educational note text.
    """
    serializer = DomainPredictionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    text_input = serializer.validated_data['text']

    try:
        result = predict_domain(text_input)
        return Response({
            "status": "success",
            "predicted_domain": result["predicted_domain"],
            "confidence": result["confidence"]
        }, status=status.HTTP_200_OK)
    except Exception as err:
        return Response({
            "error": "Domain prediction failed",
            "details": str(err)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def analyze_notes_view(request):
    """
    Final Simplified RecoMind MVP Analysis Endpoint:
    Accepts 1-chapter syllabus document/ID and student notes document/ID.
    Extracts text for both, enriches reference context, and performs semantic ML comparison.
    Returns strictly coverage_percentage and weak_topics.
    """
    note_id = request.data.get('note_id')
    note_text = request.data.get('note_text', '').strip()
    
    syllabus_id = request.data.get('syllabus_id')
    syllabus_text = request.data.get('syllabus_text', '').strip()

    # Support raw file uploads directly in multipart form data
    if 'syllabus_file' in request.FILES:
        s_file = request.FILES['syllabus_file']
        ext = os.path.splitext(s_file.name)[1].lower().replace('.', '')
        s_obj = Syllabus.objects.create(
            uploaded_file=s_file,
            original_filename=s_file.name,
            file_type=ext,
            title=os.path.splitext(s_file.name)[0].replace('_', ' ').replace('-', ' ').title()
        )
        extracted = extract_syllabus_text(s_obj.uploaded_file.path, ext)
        s_obj.extracted_text = extracted
        s_obj.save()
        syllabus_text = extracted

    if 'note_file' in request.FILES:
        n_file = request.FILES['note_file']
        ext = os.path.splitext(n_file.name)[1].lower().replace('.', '')
        n_obj = Note.objects.create(
            uploaded_file=n_file,
            original_filename=n_file.name,
            file_type=ext
        )
        extracted = process_note_ocr(n_obj.uploaded_file.path, ext)
        n_obj.extracted_text = extracted
        n_obj.status = 'PROCESSED'
        n_obj.save()
        note_text = extracted

    # Fetch from Note model if note_id provided
    if note_id and not note_text:
        try:
            n_obj = Note.objects.get(id=note_id)
            extracted = n_obj.extracted_text.strip() if n_obj.extracted_text else ""
            if not extracted:
                extracted = process_note_ocr(n_obj.uploaded_file.path, n_obj.file_type)
                n_obj.extracted_text = extracted
                n_obj.status = 'PROCESSED'
                n_obj.save()
            note_text = extracted
        except Note.DoesNotExist:
            return Response({"error": f"Note with ID {note_id} does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Failed to read note file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    unit_id = request.data.get('unit_id') or request.data.get('section_id') or request.data.get('chapter_id')
    chapter_title = ""

    # Fetch from Syllabus model if syllabus_id provided
    if syllabus_id and not syllabus_text:
        try:
            s_obj = Syllabus.objects.get(id=syllabus_id)
            if unit_id and s_obj.parsed_units:
                for u in s_obj.parsed_units:
                    u_identifier = str(u.get('id') or u.get('unit_id') or '')
                    if u_identifier == str(unit_id):
                        u_topics = " ".join(u.get('topics', []))
                        chapter_title = u.get('title', '')
                        syllabus_text = f"{chapter_title} {u_topics}".strip()
                        break

            if not syllabus_text:
                syllabus_text = s_obj.extracted_text.strip() if s_obj.extracted_text else ""
                if not syllabus_text:
                    syllabus_text = extract_syllabus_text(s_obj.uploaded_file.path, s_obj.file_type)
                    s_obj.extracted_text = syllabus_text
                    s_obj.save()
        except Syllabus.DoesNotExist:
            return Response({"error": f"Syllabus with ID {syllabus_id} does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Failed to read syllabus file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    # OCR text length check > 0
    words_notes = [w for w in note_text.split() if len(w) >= 2]
    if not note_text or len(words_notes) < 2:
        return Response({
            "error": "Unable to extract readable text from the uploaded student notes. Please upload a valid document or image with readable text."
        }, status=status.HTTP_400_BAD_REQUEST)

    words_syl = [w for w in syllabus_text.split() if len(w) >= 1]
    if not syllabus_text or len(words_syl) < 1:
        return Response({
            "error": "Unable to extract readable text from the uploaded syllabus document. Please upload a valid syllabus PDF or image."
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        s_title = ""
        if syllabus_id:
            try:
                s_title = Syllabus.objects.get(id=syllabus_id).title
            except Exception:
                pass

        results = analyze_notes_mvp(
            note_text=note_text,
            syllabus_text=syllabus_text,
            chapter_title=chapter_title,
            syllabus_title=s_title
        )
        return Response(results, status=status.HTTP_200_OK)

    except ValueError as ve:
        return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": "Failed to perform notes analysis", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
def analyze_notes_ai_view(request):
    """
    Dedicated AI-Only Coverage endpoint (POST /api/analyze-notes-ai/).
    """
    return analyze_notes_view(request)


@api_view(['POST'])
def enhance_notes_view(request):
    """
    POST /api/enhance-notes/
    New API Endpoint invoking AI Enhancement layer after ML analysis.
    """
    serializer = NoteEnhancementSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    note_id = serializer.validated_data.get('note_id')
    note_text = serializer.validated_data.get('note_text', '').strip()
    syllabus_id = serializer.validated_data.get('syllabus_id')
    unit_id = serializer.validated_data.get('unit_id', '').strip()
    edu_level = serializer.validated_data.get('education_level', 'Class 12')

    if note_id:
        try:
            n_obj = Note.objects.get(id=note_id)
            note_text = n_obj.extracted_text.strip() if n_obj.extracted_text else f"Notes: {n_obj.original_filename}"
        except Note.DoesNotExist:
            return Response({"error": f"Note {note_id} not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        s_obj = Syllabus.objects.get(id=syllabus_id)
        syllabus_title = s_obj.title
        parsed_units = s_obj.parsed_units or []

        selected_unit = None
        if unit_id:
            for u in parsed_units:
                if u.get('unit_id') == unit_id:
                    selected_unit = u
                    break
        if not selected_unit and parsed_units:
            selected_unit = parsed_units[0]

        chapter_title = selected_unit.get('title', 'Syllabus Chapter') if selected_unit else 'General Chapter'
        chapter_topics = selected_unit.get('topics', []) if selected_unit else []
        syl_text_block = "\n".join(chapter_topics) if chapter_topics else s_obj.extracted_text

        # 1. Run ML Analysis
        ml_res = analyze_notes_against_syllabus(note_text, syl_text_block)

        # 2. Call AI Enhancement Layer
        ai_res = enhance_notes_with_ai(
            note_text=note_text,
            syllabus_title=syllabus_title,
            chapter_title=chapter_title,
            chapter_topics=chapter_topics,
            ml_results=ml_res,
            education_level=edu_level,
            domain=ml_res.get("domain", "Education")
        )

        return Response({
            "status": "success",
            "syllabus_title": syllabus_title,
            "section_title": chapter_title,
            "coverage_percentage": ml_res.get("coverage_percentage", 0),
            "ml_results": ml_res,
            "ai_enhancement": ai_res
        }, status=status.HTTP_200_OK)

    except Syllabus.DoesNotExist:
        return Response({"error": f"Syllabus {syllabus_id} not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": "Failed to enhance notes with AI", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def generate_topic_notes_view(request):
    """Generate standalone, syllabus-grounded educational notes with Gemini."""
    serializer = TopicNotesGenerationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        notes = generate_topic_notes(**serializer.validated_data)
        return Response({
            "status": "success",
            "topic": serializer.validated_data["topic"],
            "notes": {key: value for key, value in notes.items() if key != "topic"},
        }, status=status.HTTP_200_OK)
    except TopicNotesGenerationError as exc:
        return Response({"status": "error", "error": str(exc)}, status=exc.status_code)


@api_view(['POST'])
def download_pdf_report_view(request):
    """
    API endpoint generating a downloadable PDF summary report for RecoMind Analysis.
    """
    analysis_data = request.data
    if not analysis_data or not isinstance(analysis_data, dict):
        return Response({"error": "Valid analysis result JSON payload required."}, status=status.HTTP_400_BAD_REQUEST)

    syllabus_title = analysis_data.get('syllabus_title', 'RecoMind Educational Syllabus')
    section_title = analysis_data.get('section_title', 'Syllabus Analysis')

    try:
        pdf_bytes = generate_analysis_pdf(analysis_data, syllabus_title=syllabus_title, section_title=section_title)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="RecoMind_Analysis_Report.pdf"'
        return response
    except Exception as e:
        return Response({"error": "Failed to generate PDF report", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
