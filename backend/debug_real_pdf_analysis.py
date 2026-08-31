import os
import django
import hashlib
import logging

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from api.models import Note, Syllabus
from api.services.ocr_service import process_note_ocr
from api.services.notes_analyzer import analyze_notes_against_syllabus, chunk_note_text, get_sentence_transformer_model
from rest_framework.test import APIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_pdfs():
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    full_pdf_path = "FULL_NOTES_TEST.pdf"
    half_pdf_path = "HALF_NOTES_TEST.pdf"

    # 1. Generate Full Notes PDF
    c_full = canvas.Canvas(full_pdf_path, pagesize=letter)
    c_full.drawString(50, 750, "Chapter 2 — Shaping of the Earth's Surface Notes:")
    c_full.drawString(50, 730, "1. Theory of Plate Tectonics: Earth's lithospheric plates move over asthenosphere.")
    c_full.drawString(50, 710, "2. Interior of the Earth: Crust, mantle, outer liquid core, inner solid core.")
    c_full.drawString(50, 690, "3. Weathering and Erosion: Physical and chemical weathering breaks rocks, erosion transports.")
    c_full.drawString(50, 670, "4. Agents of Gradation: Rivers, sea waves, wind, glaciers, underground water.")
    c_full.drawString(50, 650, "5. Landforms and Disasters: Earthquakes, landslides, avalanches, GLOF, duststorms.")
    c_full.drawString(50, 630, "6. Tectonic Plate Boundaries: Divergent boundaries create rift valleys, convergent create mountains.")
    c_full.drawString(50, 610, "7. Landform Formations: Deltas, sand dunes, waterfalls, U-shaped valleys, karst topography.")
    c_full.drawString(50, 590, "8. Disaster Mitigation: Hazard mapping, early warning systems, slope stabilization.")
    c_full.save()

    # 2. Generate Half Notes PDF
    c_half = canvas.Canvas(half_pdf_path, pagesize=letter)
    c_half.drawString(50, 750, "Chapter 2 — Shaping of the Earth's Surface Notes:")
    c_half.drawString(50, 730, "1. Theory of Plate Tectonics: Earth's lithospheric plates move over asthenosphere.")
    c_half.drawString(50, 710, "2. Interior of the Earth: Crust, mantle, outer liquid core, inner solid core.")
    c_half.save()

    return full_pdf_path, half_pdf_path

def run_diagnostics():
    print("==========================================================================")
    print("           COMPREHENSIVE DATA-FLOW DIAGNOSTICS & EMBEDDING AUDIT          ")
    print("==========================================================================")

    full_path, half_path = create_sample_pdfs()

    client = APIClient()
    syl = Syllabus.objects.get(id=5)
    target_unit = next(u for u in syl.parsed_units if u.get('id') == 'part1-theme2')
    unit_id = target_unit.get('id') or target_unit.get('unit_id')

    # --- FULL NOTES DIAGNOSTICS ---
    with open(full_path, 'rb') as f_full:
        res_full_up = client.post('/api/notes/upload/', {'file': f_full}, format='multipart')
    
    assert res_full_up.status_code == 201, "Full notes upload failed"
    note_full_id = res_full_up.data['note']['id']
    note_full_obj = Note.objects.get(id=note_full_id)
    full_text = note_full_obj.extracted_text
    full_hash = hashlib.sha256(full_text.encode('utf-8')).hexdigest()
    full_chunks = chunk_note_text(full_text)

    print("\n--- [FULL NOTES DIAGNOSTIC METRICS] ---")
    print(f"Filename: {note_full_obj.original_filename}")
    print(f"File Size: {os.path.getsize(full_path)} bytes")
    print(f"Note ID: {note_full_id}")
    print(f"Extracted Text Length: {len(full_text)} chars")
    print(f"Word Count: {len(full_text.split())} words")
    print(f"Text Hash: {full_hash}")
    print(f"Chunk Count: {len(full_chunks)}")
    print(f"First 200 chars: {full_text[:200]!r}")
    print(f"Last 200 chars: {full_text[-200:]!r}")

    # Call API /api/analyze-notes/
    res_full_analysis = client.post('/api/analyze-notes/', {
        'note_id': note_full_id,
        'syllabus_id': syl.id,
        'unit_id': unit_id
    }, format='json')
    assert res_full_analysis.status_code == 200, "Full notes analysis failed"
    score_full = res_full_analysis.data['coverage_percentage']

    # --- HALF NOTES DIAGNOSTICS ---
    with open(half_path, 'rb') as f_half:
        res_half_up = client.post('/api/notes/upload/', {'file': f_half}, format='multipart')

    assert res_half_up.status_code == 201, "Half notes upload failed"
    note_half_id = res_half_up.data['note']['id']
    note_half_obj = Note.objects.get(id=note_half_id)
    half_text = note_half_obj.extracted_text
    half_hash = hashlib.sha256(half_text.encode('utf-8')).hexdigest()
    half_chunks = chunk_note_text(half_text)

    print("\n--- [HALF NOTES DIAGNOSTIC METRICS] ---")
    print(f"Filename: {note_half_obj.original_filename}")
    print(f"File Size: {os.path.getsize(half_path)} bytes")
    print(f"Note ID: {note_half_id}")
    print(f"Extracted Text Length: {len(half_text)} chars")
    print(f"Word Count: {len(half_text.split())} words")
    print(f"Text Hash: {half_hash}")
    print(f"Chunk Count: {len(half_chunks)}")
    print(f"First 200 chars: {half_text[:200]!r}")
    print(f"Last 200 chars: {half_text[-200:]!r}")

    # Call API /api/analyze-notes/
    res_half_analysis = client.post('/api/analyze-notes/', {
        'note_id': note_half_id,
        'syllabus_id': syl.id,
        'unit_id': unit_id
    }, format='json')
    assert res_half_analysis.status_code == 200, "Half notes analysis failed"
    score_half = res_half_analysis.data['coverage_percentage']

    # --- TOPIC LEVEL EVIDENCE COMPARISON ---
    print("\n--- [TOPIC-LEVEL EVIDENCE SCORES COMPARISON] ---")
    full_details = {item['topic']: item for item in res_full_analysis.data['topic_details']}
    half_details = {item['topic']: item for item in res_half_analysis.data['topic_details']}

    for t in target_unit['topics']:
        f_item = full_details.get(t, {})
        h_item = half_details.get(t, {})
        print(f"Topic: {t[:45]!r}")
        print(f"  FULL -> Status: {f_item.get('status')} | Score: {f_item.get('coverage_score')} | Matched: {len(f_item.get('matched_reference_points', []))}")
        print(f"  HALF -> Status: {h_item.get('status')} | Score: {h_item.get('coverage_score')} | Matched: {len(h_item.get('matched_reference_points', []))}")

    print("\n--------------------------------------------------------------------------")
    print(f"FULL NOTES COVERAGE: {score_full}%")
    print(f"HALF NOTES COVERAGE: {score_half}%")
    print(f"COVERAGE GAP (FULL - HALF): {score_full - score_half:.1f}%")
    print("--------------------------------------------------------------------------")

    # Cleanup test files
    if os.path.exists(full_path): os.remove(full_path)
    if os.path.exists(half_path): os.remove(half_path)

if __name__ == "__main__":
    run_diagnostics()
