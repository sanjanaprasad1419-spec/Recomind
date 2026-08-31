import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from rest_framework.test import APIClient
from api.models import Note, Syllabus

def test():
    client = APIClient()
    
    # Create sample note with real geography text
    geography_content = """
    Chapter 2 — Shaping of the Earth's Surface:
    The Theory of Plate Tectonics explains the movement of Earth's lithospheric plates across the asthenosphere.
    The lithosphere is broken into major plates such as Pacific, Eurasian, African, and Indo-Australian plates.
    Interior of the Earth consists of three distinct layers: the crust, mantle, and core (outer and inner core).
    Weathering and erosion are exogenic geomorphic processes that continuously shape landforms.
    Weathering breaks rocks into smaller fragments, while erosion transports sediment downstream.
    Agents of gradation — running water (rivers), sea waves, wind action, glaciers, and underground water.
    Rivers form V-shaped valleys, waterfalls, and deltas. Glaciers carve U-shaped valleys and cirques.
    Geological hazards and natural disasters include earthquakes, landslides, avalanches, and Glacial Lake Outburst Floods (GLOF).
    """

    note = Note.objects.create(
        original_filename="geography_notes.txt",
        file_type="txt",
        extracted_text=geography_content,
        status="PROCESSED"
    )

    syl = Syllabus.objects.get(id=5)

    payload = {
        "note_id": note.id,
        "syllabus_id": syl.id,
        "unit_id": "part1-theme2"
    }

    res = client.post("/api/analyze-notes/", payload, format="json")
    print("API Response Status Code:", res.status_code)
    print("Coverage Percentage:", res.data.get("coverage_percentage"))
    print("Domain:", res.data.get("domain"))
    print("Covered Topics Count:", len(res.data.get("topics", {}).get("covered", [])))
    print("Covered Topics:", res.data.get("topics", {}).get("covered", []))

    assert res.status_code == 200, "API returned non-200 status code"
    assert res.data.get("coverage_percentage") > 50.0, "Coverage score is too low!"
    assert len(res.data.get("topics", {}).get("covered", [])) >= 3, "Covered topics list is empty!"

    print("\n==========================================================================")
    print("            REAL GEOGRAPHY NOTE ANALYSIS TEST PASSED 100%                 ")
    print("==========================================================================")

if __name__ == "__main__":
    test()
