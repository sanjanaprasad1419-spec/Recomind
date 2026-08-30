import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from rest_framework.test import APIClient
from api.models import Note, Syllabus
from api.services.ocr_service import process_note_ocr

def test_analysis():
    client = APIClient()
    
    geography_note_text = """
    Chapter 2: Shaping of the Earth's Surface
    Notes on Plate Tectonics and Physical Geography:
    - The Theory of Plate Tectonics explains the movement of Earth's lithospheric plates.
    - Interior of the Earth consists of the crust, mantle, outer core, and inner core.
    - Weathering and erosion are exogenic processes that break down rocks.
    - Agents of gradation include rivers, wind, glaciers, waves, and underground water.
    - Landforms created by rivers include V-shaped valleys, waterfalls, and meanders.
    - Earthquakes and landslides occur due to tectonic stress and gravity.
    """

    note = Note.objects.create(
        original_filename="geography_notes.pdf",
        file_type="pdf",
        extracted_text=geography_note_text
    )

    payload = {
        "note_id": note.id,
        "syllabus_id": 5,
        "unit_id": "part1-theme2"
    }

    print(f"Testing Note Analysis on Note #{note.id} ('{note.original_filename}') against Syllabus #5, Unit 'part1-theme2'...")
    response = client.post('/api/analyze-notes/', payload, format='json')
    
    print(f"HTTP Status: {response.status_code}")
    data = response.json()
    
    print(f"Syllabus Title: {data.get('syllabus_title')}")
    print(f"Section Title: {data.get('section_title')}")
    print(f"Domain: {data.get('domain')}")
    print(f"Coverage Score: {data.get('coverage_percentage')}%")
    print(f"Covered Topics ({len(data.get('topics', {}).get('covered', []))}): {data.get('topics', {}).get('covered', [])}")
    print(f"Partially Covered Topics ({len(data.get('topics', {}).get('partially_covered', []))}): {data.get('topics', {}).get('partially_covered', [])}")
    print(f"Missing Topics ({len(data.get('topics', {}).get('missing', []))}): {data.get('topics', {}).get('missing', [])}")

if __name__ == "__main__":
    test_analysis()
