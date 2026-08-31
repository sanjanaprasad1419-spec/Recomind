import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from api.models import Syllabus
from api.services.notes_analyzer import analyze_notes_against_syllabus, evaluate_topic_coverage, get_or_create_reference_profile

def test_architecture():
    print("==========================================================================")
    print("      CONTENT-AWARE REFERENCE ML ANALYSIS ARCHITECTURE VERIFICATION      ")
    print("==========================================================================")

    # 1. Physics Capacitance Topic
    phys_syl = "Capacitance of a parallel plate capacitor, formula and effect of dielectric"
    
    FULL_PHYS_NOTES = """
    Capacitance is the ratio of electric charge Q to potential difference V (C = Q/V).
    For a parallel plate capacitor of area A and plate separation d, C = epsilon_0 * A / d.
    When a dielectric material of constant K is inserted between plates, capacitance increases to C' = K * C.
    The energy stored in a charged capacitor is U = 1/2 * C * V^2.
    """

    HALF_PHYS_NOTES = """
    Capacitors store electric charge. Capacitance is defined as C = Q/V.
    """

    res_full = analyze_notes_against_syllabus(FULL_PHYS_NOTES, phys_syl, "Electrostatics", "Physics Class 12")
    res_half = analyze_notes_against_syllabus(HALF_PHYS_NOTES, phys_syl, "Electrostatics", "Physics Class 12")

    print("\n--- PHYSICS FULL NOTES ---")
    print(f"Coverage Score: {res_full['coverage_percentage']}%")
    print(f"Status: {res_full['topic_details'][0]['status']}")
    print(f"Matched Reference Points ({len(res_full['topic_details'][0]['matched_reference_points'])}): {res_full['topic_details'][0]['matched_reference_points']}")
    print(f"Missing Aspects: {res_full['topic_details'][0]['missing_aspects']}")

    print("\n--- PHYSICS HALF NOTES ---")
    print(f"Coverage Score: {res_half['coverage_percentage']}%")
    print(f"Status: {res_half['topic_details'][0]['status']}")
    print(f"Matched Reference Points ({len(res_half['topic_details'][0]['matched_reference_points'])}): {res_half['topic_details'][0]['matched_reference_points']}")
    print(f"Missing Aspects: {res_half['topic_details'][0]['missing_aspects']}")

    assert res_full['coverage_percentage'] > res_half['coverage_percentage'], "Full notes score must be higher than half notes!"
    assert res_half['topic_details'][0]['status'] in ["PARTIALLY_COVERED", "NEEDS_IMPROVEMENT"], "Half notes must be PARTIALLY_COVERED / NEEDS_IMPROVEMENT!"

    assert len(res_half['topic_details'][0]['missing_aspects']) > 0, "Half notes must list missing reference aspects!"

    # 2. Geography Chapter 2
    syl = Syllabus.objects.get(id=5)
    parsed_units = syl.parsed_units or []
    target_unit = next(u for u in parsed_units if u.get('id') == 'part1-theme2')
    topics_list = target_unit.get('topics', [])
    syllabus_text = "\n".join(topics_list)

    GEO_FULL_NOTES = """
    Chapter 2 — Shaping of the Earth's Surface:
    The Theory of Plate Tectonics explains the movement of Earth's lithospheric plates over the asthenosphere.
    Interior of the Earth consists of the crust, mantle, and core.
    Weathering breaks rocks physically and chemically; erosion transports weathered sediments.
    Agents of gradation — running water (rivers), sea waves, wind, glaciers, and underground water.
    Landforms and natural disasters include earthquakes, landslides, avalanches, Glacial Lake Outburst Floods (GLOF), and duststorms.
    Tectonic plate boundaries include divergent, convergent, and transform faults.
    Geographical landforms include V-shaped valleys, waterfalls, deltas, U-shaped troughs, sand dunes, and karst topography.
    Disaster mitigation includes hazard mapping, early warning systems, slope stabilization, and afforestation.
    """

    GEO_HALF_NOTES = """
    Chapter 2 — Shaping of the Earth's Surface:
    The Theory of Plate Tectonics explains the movement of Earth's lithospheric plates over the asthenosphere.
    Interior of the Earth consists of the crust, mantle, and core.
    Weathering breaks rocks physically and chemically.
    """

    geo_full = analyze_notes_against_syllabus(GEO_FULL_NOTES, syllabus_text, target_unit.get('title'), syl.title)
    geo_half = analyze_notes_against_syllabus(GEO_HALF_NOTES, syllabus_text, target_unit.get('title'), syl.title)

    print("\n--- GEOGRAPHY FULL NOTES ---")
    print(f"Coverage Score: {geo_full['coverage_percentage']}% | Covered = {len(geo_full['topics']['covered'])} | Missing = {len(geo_full['topics']['missing'])}")

    print("\n--- GEOGRAPHY HALF NOTES ---")
    print(f"Coverage Score: {geo_half['coverage_percentage']}% | Covered = {len(geo_half['topics']['covered'])} | Missing = {len(geo_half['topics']['missing'])}")

    print(f"\nCoverage Gap (Full - Half): {geo_full['coverage_percentage'] - geo_half['coverage_percentage']:.1f}%")

    assert geo_full['coverage_percentage'] > geo_half['coverage_percentage'], "Full geography notes must score higher than half notes!"

    print("\n==========================================================================")
    print("      CONTENT-AWARE REFERENCE ML ANALYSIS ARCHITECTURE VERIFIED 100%       ")
    print("==========================================================================")

if __name__ == "__main__":
    test_architecture()
