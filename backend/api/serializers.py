import os
from rest_framework import serializers
from .models import Note, Syllabus

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png', 'txt'}

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB

class NoteSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving and displaying Note details.
    """
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = [
            'id',
            'original_filename',
            'uploaded_file',
            'file_url',
            'file_type',
            'upload_timestamp',
            'extracted_text',
            'overall_score',
            'status',
            'education_level',
            'subject_domain',
            'topic',
        ]
        read_only_fields = ['id', 'file_type', 'upload_timestamp', 'extracted_text', 'overall_score', 'status']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.uploaded_file and hasattr(obj.uploaded_file, 'url'):
            if request is not None:
                return request.build_absolute_uri(obj.uploaded_file.url)
            return obj.uploaded_file.url
        return None


class NoteUploadSerializer(serializers.Serializer):
    """
    Serializer for handling note file uploads with validation.
    """
    file = serializers.FileField(required=True)
    education_level = serializers.CharField(required=False, allow_blank=True, default="")
    subject_domain = serializers.CharField(required=False, allow_blank=True, default="")
    topic = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_file(self, value):
        ext = os.path.splitext(value.name)[1].lower().replace('.', '')
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file type '.{ext}'. Allowed file types are: PDF, DOCX, JPG, JPEG, PNG."
            )
        if value.size > MAX_FILE_SIZE_BYTES:
            raise serializers.ValidationError(
                f"File size exceeds maximum limit of 20MB."
            )
        return value


class SyllabusSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieved Syllabus objects.
    """
    file_url = serializers.SerializerMethodField()
    units_count = serializers.SerializerMethodField()

    class Meta:
        model = Syllabus
        fields = [
            'id',
            'title',
            'original_filename',
            'uploaded_file',
            'file_url',
            'file_type',
            'upload_timestamp',
            'extracted_text',
            'parsed_units',
            'units_count',
        ]
        read_only_fields = ['id', 'file_type', 'upload_timestamp', 'extracted_text', 'parsed_units']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.uploaded_file and hasattr(obj.uploaded_file, 'url'):
            if request is not None:
                return request.build_absolute_uri(obj.uploaded_file.url)
            return obj.uploaded_file.url
        return None

    def get_units_count(self, obj):
        if isinstance(obj.parsed_units, list):
            return len(obj.parsed_units)
        return 0


class SyllabusUploadSerializer(serializers.Serializer):
    """
    Serializer for uploading a syllabus document file.
    """
    file = serializers.FileField(required=True)
    title = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_file(self, value):
        ext = os.path.splitext(value.name)[1].lower().replace('.', '')
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported syllabus file type '.{ext}'. Allowed types: PDF, DOCX, JPG, JPEG, PNG."
            )
        if value.size > MAX_FILE_SIZE_BYTES:
            raise serializers.ValidationError("File size exceeds 20MB limit.")
        return value


class DomainPredictionSerializer(serializers.Serializer):
    """
    Serializer for domain prediction request payloads.
    """
    text = serializers.CharField(required=True, allow_blank=False)

    def validate_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Text string cannot be blank or whitespace only.")
        return value.strip()


class NoteAnalysisSerializer(serializers.Serializer):
    """
    Serializer for POST /api/analyze-notes/ endpoint.
    Accepts note_id or note_text, along with syllabus_id and optional unit_id / section_id.
    """
    note_id = serializers.IntegerField(required=False, allow_null=True)
    note_text = serializers.CharField(required=False, allow_blank=True, default="")
    
    syllabus_id = serializers.IntegerField(required=False, allow_null=True)
    syllabus_text = serializers.CharField(required=False, allow_blank=True, default="")
    
    unit_id = serializers.CharField(required=False, allow_blank=True, default="")
    section_title = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, data):
        note_id = data.get('note_id')
        note_text = data.get('note_text', '').strip()
        syllabus_id = data.get('syllabus_id')
        syllabus_text = data.get('syllabus_text', '').strip()

        if not note_id and not note_text:
            raise serializers.ValidationError({"non_field_errors": "Either note_id or note_text must be provided."})

        if not syllabus_id and not syllabus_text:
            raise serializers.ValidationError({"non_field_errors": "Either syllabus_id or syllabus_text must be provided."})

        return data


class NoteEnhancementSerializer(serializers.Serializer):
    """
    Serializer for POST /api/enhance-notes/ endpoint.
    """
    note_id = serializers.IntegerField(required=False, allow_null=True)
    note_text = serializers.CharField(required=False, allow_blank=True, default="")
    syllabus_id = serializers.IntegerField(required=False, allow_null=True)
    unit_id = serializers.CharField(required=False, allow_blank=True, default="")
    education_level = serializers.CharField(required=False, allow_blank=True, default="Class 12")

    def validate(self, data):
        if not data.get('note_id') and not data.get('note_text'):
            raise serializers.ValidationError({"non_field_errors": "Either note_id or note_text must be provided."})
        if not data.get('syllabus_id'):
            raise serializers.ValidationError({"non_field_errors": "syllabus_id is required for AI enhancement."})
        return data


class TopicNotesGenerationSerializer(serializers.Serializer):
    """Validation for the standalone Gemini topic-notes endpoint."""
    topic = serializers.CharField(required=True, allow_blank=False, max_length=500)
    subject = serializers.CharField(required=False, allow_blank=True, default="")
    education_level = serializers.CharField(required=False, allow_blank=True, default="")
    chapter = serializers.CharField(required=False, allow_blank=True, default="")
    syllabus_context = serializers.CharField(required=False, allow_blank=True, default="")
    student_notes = serializers.CharField(required=False, allow_blank=True, default="")
    reference_context = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_topic(self, value):
        if not value.strip():
            raise serializers.ValidationError("Topic cannot be blank.")
        return value.strip()
