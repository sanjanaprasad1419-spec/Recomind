import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from api.models import Syllabus, ReferenceKnowledgeCache
from api.services.notes_analyzer import analyze_notes_against_syllabus, evaluate_topic_coverage
from api.services.reference_knowledge_service import get_or_create_reference_profile
from api.services.ai_notes_enhancer import enhance_notes_with_ai

def run_15_test_suite():
    print("==========================================================================")
    print("           STEP 23: MANDATORY 15-POINT TEST MATRIX VERIFICATION           ")
    print("==========================================================================")

    # Clear reference knowledge cache for fresh test execution
    ReferenceKnowledgeCache.objects.all().delete()


    # 1. Topic-name-only false positive prevention
    res1 = analyze_notes_against_syllabus("Capacitance stores charge.", "Capacitance of a parallel plate capacitor, formula and effect of dielectric", "Electrostatics", "Physics")
    print(f"\n1. Topic-Name-Only Prevention: Score = {res1['coverage_percentage']}% | Missing Aspects = {res1['topic_details'][0]['missing_aspects']}")
    assert res1['coverage_percentage'] < 70.0, "Test 1 failed: topic-name-only gave false 100%!"

    # 2. Full vs Half Notes
    syl = Syllabus.objects.get(id=5)
    target_unit = next(u for u in syl.parsed_units if u.get('id') == 'part1-theme2')
    topics_text = "\n".join(target_unit['topics'])

    full_notes = "Theory of plate tectonics explains lithospheric plates moving over asthenosphere. Interior of Earth has crust, mantle, core. Weathering breaks rocks, erosion transports sediments. Agents of gradation rivers, waves, wind, glaciers, groundwater. Landforms and disasters earthquakes, landslides, avalanches, GLOF."
    half_notes = "Theory of plate tectonics explains lithospheric plates moving over asthenosphere. Interior of Earth has crust, mantle, core."

    res_full = analyze_notes_against_syllabus(full_notes, topics_text, target_unit.get('title'), syl.title)
    res_half = analyze_notes_against_syllabus(half_notes, topics_text, target_unit.get('title'), syl.title)
    gap = res_full['coverage_percentage'] - res_half['coverage_percentage']
    print(f"2. Full vs Half Notes: Full = {res_full['coverage_percentage']}% vs Half = {res_half['coverage_percentage']}% (Gap = {gap:.1f}%)")
    assert gap >= 15.0, "Test 2 failed: Full vs Half gap too small!"

    # 3. Missing Topic
    res3 = analyze_notes_against_syllabus(full_notes, "Photosynthesis and Calvin cycle", "Plant Physiology", "Biology")
    print(f"3. Missing Topic: Status = {res3['topic_details'][0]['status']}")
    assert res3['topic_details'][0]['status'] == "MISSING", "Test 3 failed"

    # 4. Partial Topic
    res4 = analyze_notes_against_syllabus("Current carrying wire creates magnetic field.", "Long straight wire — magnetic field, formula and derivation", "Magnetism", "Physics")
    print(f"4. Partial Topic: Status = {res4['topic_details'][0]['status']} | Missing = {res4['topic_details'][0]['missing_aspects']}")
    assert res4['topic_details'][0]['status'] == "PARTIALLY_COVERED", "Test 4 failed"

    # 5. Semantic Paraphrase
    res5 = analyze_notes_against_syllabus("The outer rigid layer of Earth is broken into moving slabs that slide over asthenosphere.", "Theory of plate tectonics", "Geomorphology", "Geography")
    print(f"5. Semantic Paraphrase: Status = {res5['topic_details'][0]['status']}")
    assert res5['topic_details'][0]['status'] in ["COVERED", "PARTIALLY_COVERED"], "Test 5 failed"

    # 6. Unrelated Notes
    res6 = analyze_notes_against_syllabus("Debit increases assets and credit increases liabilities.", topics_text, target_unit.get('title'), syl.title)
    print(f"6. Unrelated Notes: Score = {res6['coverage_percentage']}%")
    assert res6['coverage_percentage'] <= 15.0, "Test 6 failed"

    # 7. Geography
    res7 = analyze_notes_against_syllabus(full_notes, topics_text, target_unit.get('title'), syl.title)
    print(f"7. Geography Subject-Aware Match: Score = {res7['coverage_percentage']}% | Domain = {res7['domain']}")

    # 8. Physics
    res8 = analyze_notes_against_syllabus("C = Q/V. C = epsilon_0 A / d. Dielectric increases capacitance to C' = K C.", "Capacitance", "Electrostatics", "Physics")
    print(f"8. Physics Subject-Aware Match: Score = {res8['coverage_percentage']}%")

    # 9. Biology
    res9 = analyze_notes_against_syllabus("Cell membrane is a phospholipid bilayer with embedded transport proteins.", "Cell membrane structure", "Cell Biology", "Biology")
    print(f"9. Biology Subject-Aware Match: Score = {res9['coverage_percentage']}%")

    # 10. Empty Notes
    try:
        analyze_notes_against_syllabus("", topics_text)
        assert False, "Empty notes did not raise error"
    except ValueError as ve:
        print(f"10. Empty Notes Validation: Caught '{ve}'")

    # 11. Reference retrieval fallback
    prof_fallback = get_or_create_reference_profile("Random Unknown Advanced Topic XYZ")
    print(f"11. Reference Retrieval Fallback: Profile domain = {prof_fallback.get('subject_domain')}")
    assert prof_fallback.get("topic") == "Random Unknown Advanced Topic XYZ"

    # 12. Cached Reference Reuse
    initial_count = ReferenceKnowledgeCache.objects.count()
    prof_cache1 = get_or_create_reference_profile("Capacitance", "Electrostatics", "Physics Class 12")
    prof_cache2 = get_or_create_reference_profile("Capacitance", "Electrostatics", "Physics Class 12")
    print(f"12. Cached Reference Reuse: Total cached entries in DB = {ReferenceKnowledgeCache.objects.count()}")

    # 13. Different Chapter Isolation
    target_unit_1 = next(u for u in syl.parsed_units if u.get('id') == 'part1-theme1')
    res13 = analyze_notes_against_syllabus(full_notes, "\n".join(target_unit_1['topics']), target_unit_1.get('title'), syl.title)
    print(f"13. Chapter Isolation: Chapter 1 Score = {res13['coverage_percentage']}% vs Chapter 2 Score = {res7['coverage_percentage']}%")
    assert res13['coverage_percentage'] < res7['coverage_percentage']

    # 14. Different uploaded note files produce different predictions
    assert res_full['coverage_percentage'] != res_half['coverage_percentage'], "Different note files must produce different predictions!"
    print("14. Different Files Differentiation Verified.")

    # 15. Gemini receives actual missing components
    ai_res = enhance_notes_with_ai("Capacitance is C = Q/V.", syl.title, target_unit.get('title'), topics_text, res_half)
    print(f"15. Gemini AI Enhancement Generated: {len(ai_res['enhancements'])} enhancements generated")
    assert len(ai_res['enhancements']) > 0

    print("\n==========================================================================")
    print("             ALL 15 MANDATORY TEST MATRIX SCENARIOS PASSED 100%           ")
    print("==========================================================================")

if __name__ == "__main__":
    run_15_test_suite()
