import os
import django

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.services.notes_analyzer import analyze_notes_against_syllabus

def test_presentation_ready_audit():
    print("==========================================================================")
    print("      RECOMIND PRESENTATION-READY GEMINI ACADEMIC AUDIT END-TO-END        ")
    print("==========================================================================")

    chapter_title = "Chapter 2 — Shaping of the Earth's Surface"
    syllabus_title = "Social Science Geography Syllabus"
    syllabus_text = """
    1. Theory of plate tectonics
    2. Interior of the Earth
    3. Role of weathering and erosion
    4. Agents of gradation - river, waves and currents, wind, glaciers, and underground water
    5. Landforms and disasters: earthquakes, landslides, avalanches, Glacial Lake Outburst Flood (GLOF) and duststorms
    """

    sample_student_notes = """
    Chapter 2 Notes:
    1. Theory of Plate Tectonics: Earth's lithospheric plates move over asthenosphere driven by convection currents in mantle.
    2. Interior of the Earth: Crust (continental and oceanic), Mantle, Outer core (liquid iron), Inner core (solid nickel-iron).
    3. Landforms & Disasters: Volcanic eruptions and earthquakes occur along plate boundaries. Landslides happen on steep slopes.
    """

    print(f"\nEvaluating Chapter: '{chapter_title}'")
    print(f"Notes Character Length: {len(sample_student_notes)} chars")

    results = analyze_notes_against_syllabus(
        sample_student_notes,
        syllabus_text,
        chapter_title,
        syllabus_title
    )

    print("\n--- [GEMINI ACADEMIC AUDIT RESULT SCHEMA] ---")
    print(f"Coverage Percentage : {results['coverage_percentage']}%")
    print(f"Overall Status      : {results.get('overall_status', 'N/A')}")
    print(f"Covered Topics      : {results['topics']['covered']}")
    print(f"Partially Covered   : {results['topics']['partially_covered']}")
    print(f"Missing Topics      : {results['topics']['missing']}")
    print(f"Summary             : {results['summary'][0] if results['summary'] else ''}")
    print(f"Key Concepts        : {results['key_concepts'][:5]}")
    print(f"Recommendations Count: {len(results['recommendations'])}")

if __name__ == "__main__":
    test_presentation_ready_audit()
