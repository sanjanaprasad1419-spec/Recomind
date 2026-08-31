import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from api.models import Syllabus
from api.services.notes_analyzer import analyze_notes_against_syllabus

def test_full_vs_half():
    print("==========================================================================")
    print("         STEP 5 / 9: FULL NOTES VS HALF NOTES REGRESSION TEST            ")
    print("==========================================================================")

    # Selected Chapter: Chapter 2 — Shaping of the Earth's Surface (10 topics)
    syl = Syllabus.objects.get(id=5)
    parsed_units = syl.parsed_units or []
    target_unit = next(u for u in parsed_units if u.get('id') == 'part1-theme2')
    topics_list = target_unit.get('topics', [])
    syllabus_text = "\n".join(topics_list)

    print(f"Selected Chapter: {target_unit.get('title')} ({len(topics_list)} topics)")

    # FULL NOTES: Covers topics 1-10 comprehensively
    FULL_NOTES = """
    Chapter 2 — Shaping of the Earth's Surface:
    1. Theory of Plate Tectonics: The Earth's lithosphere is divided into major and minor tectonic plates that move relative to each other over the asthenosphere. Divergent, convergent, and transform plate boundaries form mountains, oceanic trenches, and fault lines.
    2. Interior of the Earth: The Earth consists of three principal layers: the crust (silicates), mantle (viscous rock), and core (outer liquid iron-nickel core and inner solid core).
    3. Weathering and Erosion: Weathering is the in-situ physical breakdown and chemical alteration of rocks. Erosion is the active transport of weathered material by geomorphic agents.
    4. Agents of Gradation: Running water (rivers), ocean waves and currents, wind, glaciers, and underground water shape landforms through erosion, transportation, and deposition.
    5. Landforms and Natural Disasters: Earthquakes, landslides, avalanches, Glacial Lake Outburst Floods (GLOF), and duststorms are catastrophic geomorphic processes.
    6. Tectonic Plate Map & Dynamics: Plate tectonics explains continental drift, seafloor spreading, mountain building (orogeny), and volcanic belts like the Pacific Ring of Fire.
    7. Weathering Examples & Regional Processes: Frost wedging, oxidation, solution weathering, and biological activity break down bedrock in tropical and arid regions.
    8. Major Landforms Formation: V-shaped valleys, waterfalls, meanders, oxbow lakes, deltaic plains, U-shaped glacial troughs, sand dunes, and karst topography.
    9. Disaster Mitigation Strategies: Hazard mapping, early warning systems, slope stabilization, earthquake-resistant engineering, and afforestation reduce disaster risk.
    """

    # HALF NOTES: Only contains notes for topics 1-4 (topics 5-10 completely omitted!)
    HALF_NOTES = """
    Chapter 2 — Shaping of the Earth's Surface:
    1. Theory of Plate Tectonics: The Earth's lithosphere is divided into major and minor tectonic plates that move relative to each other over the asthenosphere.
    2. Interior of the Earth: The Earth consists of three principal layers: the crust, mantle, and core.
    3. Weathering and Erosion: Weathering is the in-situ physical breakdown of rocks. Erosion transports weathered material.
    """

    res_full = analyze_notes_against_syllabus(FULL_NOTES, syllabus_text)
    res_half = analyze_notes_against_syllabus(HALF_NOTES, syllabus_text)

    full_len = len(FULL_NOTES)
    half_len = len(HALF_NOTES)

    print(f"\nFULL NOTES: Length = {full_len} chars")
    print(f"  Coverage Score: {res_full['coverage_percentage']}%")
    print(f"  Covered Topics ({len(res_full['topics']['covered'])}): {res_full['topics']['covered']}")
    print(f"  Partially Covered ({len(res_full['topics']['partially_covered'])}): {res_full['topics']['partially_covered']}")
    print(f"  Missing Topics ({len(res_full['topics']['missing'])}): {res_full['topics']['missing']}")

    print(f"\nHALF NOTES: Length = {half_len} chars")
    print(f"  Coverage Score: {res_half['coverage_percentage']}%")
    print(f"  Covered Topics ({len(res_half['topics']['covered'])}): {res_half['topics']['covered']}")
    print(f"  Partially Covered ({len(res_half['topics']['partially_covered'])}): {res_half['topics']['partially_covered']}")
    print(f"  Missing Topics ({len(res_half['topics']['missing'])}): {res_half['topics']['missing']}")

    diff = res_full['coverage_percentage'] - res_half['coverage_percentage']
    print(f"\nCoverage Difference (Full - Half): {diff:.1f}%")

if __name__ == "__main__":
    test_full_vs_half()
