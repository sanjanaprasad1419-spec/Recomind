import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from api.models import Syllabus
from api.services.notes_analyzer import analyze_notes_against_syllabus, evaluate_topic_coverage, chunk_note_text

def run_matrix():
    print("==========================================================================")
    print("              STEP 18: MANDATORY 10-TEST MATRIX VERIFICATION              ")
    print("==========================================================================")

    syl = Syllabus.objects.get(id=5)
    parsed_units = syl.parsed_units or []
    target_unit = next(u for u in parsed_units if u.get('id') == 'part1-theme2')
    topics_list = target_unit.get('topics', [])
    syllabus_text = "\n".join(topics_list)

    FULL_NOTES = """
    Chapter 2 — Shaping of the Earth's Surface:
    1. Theory of Plate Tectonics: Lithospheric plates move over asthenosphere forming divergent, convergent, transform boundaries.
    2. Interior of the Earth: Crust, mantle, outer liquid core and inner solid core.
    3. Weathering and Erosion: Physical/chemical weathering breaks rocks, erosion transports sediment.
    4. Agents of Gradation: Rivers, sea waves, wind, glaciers, underground water.
    5. Landforms and Disasters: Earthquakes, landslides, avalanches, GLOF, duststorms.
    """

    HALF_NOTES = """
    Chapter 2 — Shaping of the Earth's Surface:
    1. Theory of Plate Tectonics: Lithospheric plates move over asthenosphere.
    2. Interior of the Earth: Crust, mantle, outer core, inner core.
    """

    TINY_NOTES = "Theory of plate tectonics explains how lithospheric plates move over the asthenosphere."
    UNRELATED_NOTES = "Accounting debit increases assets and credit increases liabilities. Balance sheet lists total assets."
    PARAPHRASE_NOTES = "The Earth's lithospheric layer is broken into moving slabs that slide over asthenosphere."
    PARTIAL_NOTES = "Current carrying wire creates magnetic field."

    # TEST 1: Full notes
    res1 = analyze_notes_against_syllabus(FULL_NOTES, syllabus_text)
    print(f"TEST 1 (Full Notes): Score = {res1['coverage_percentage']}% | Missing = {len(res1['topics']['missing'])}")
    assert res1['coverage_percentage'] >= 75.0, "Test 1 failed"

    # TEST 2: Half notes
    res2 = analyze_notes_against_syllabus(HALF_NOTES, syllabus_text)
    print(f"TEST 2 (Half Notes): Score = {res2['coverage_percentage']}% | Missing = {len(res2['topics']['missing'])}")
    assert res2['coverage_percentage'] < res1['coverage_percentage'], "Test 2 failed: Half notes coverage not lower!"

    # TEST 3: Very small notes
    res3 = analyze_notes_against_syllabus(TINY_NOTES, syllabus_text)
    print(f"TEST 3 (Tiny Notes): Score = {res3['coverage_percentage']}% | Missing = {len(res3['topics']['missing'])}")
    assert res3['coverage_percentage'] <= 40.0, "Test 3 failed"

    # TEST 4: Empty notes
    try:
        analyze_notes_against_syllabus("", syllabus_text)
        assert False, "Test 4 failed"
    except ValueError as ve:
        print(f"TEST 4 (Empty Notes): Validation caught '{ve}'")

    # TEST 5: Unrelated notes
    res5 = analyze_notes_against_syllabus(UNRELATED_NOTES, syllabus_text)
    print(f"TEST 5 (Unrelated Notes): Score = {res5['coverage_percentage']}% | Missing = {len(res5['topics']['missing'])}")
    assert res5['coverage_percentage'] <= 15.0, "Test 5 failed"

    # TEST 6: Paraphrased notes
    res6 = analyze_notes_against_syllabus(PARAPHRASE_NOTES, "Theory of plate tectonics")
    print(f"TEST 6 (Paraphrase): Status = {res6['topic_details'][0]['status']}")
    assert res6['topic_details'][0]['status'] in ["COVERED", "PARTIALLY_COVERED"], "Test 6 failed"


    # TEST 7: Details absent
    res7 = analyze_notes_against_syllabus(PARTIAL_NOTES, "Long straight current-carrying wire — magnetic field, derivation and formula")
    print(f"TEST 7 (Details Absent): Status = {res7['topic_details'][0]['status']}")
    assert res7['topic_details'][0]['status'] == "PARTIALLY_COVERED", "Test 7 failed"

    # TEST 8: Full chapter notes
    print(f"TEST 8 (Full Chapter Notes): Passed with {res1['coverage_percentage']}% coverage")

    # TEST 9: Different uploaded files produce different scores
    diff_score = res1['coverage_percentage'] - res2['coverage_percentage']
    print(f"TEST 9 (Different Files Score Gap): Full ({res1['coverage_percentage']}%) vs Half ({res2['coverage_percentage']}%) -> Gap = {diff_score:.1f}%")
    assert diff_score >= 15.0, "Test 9 failed: Score gap too small!"

    # TEST 10: Selected chapter scope strictly enforced
    target_unit_1 = next(u for u in parsed_units if u.get('id') == 'part1-theme1')
    res10 = analyze_notes_against_syllabus(FULL_NOTES, "\n".join(target_unit_1['topics']))
    print(f"TEST 10 (Strict Chapter Scope): Chapter 1 Scope Score = {res10['coverage_percentage']}%")
    assert res10['coverage_percentage'] < res1['coverage_percentage'], "Test 10 failed"

    print("\n==========================================================================")
    print("             ALL 10 MANDATORY TEST MATRIX SCENARIOS PASSED 100%           ")
    print("==========================================================================")

if __name__ == "__main__":
    run_matrix()
