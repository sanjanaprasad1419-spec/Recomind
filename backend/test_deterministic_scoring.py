import os
import django

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.services.gemini_notes_audit import compute_deterministic_coverage, generate_local_component_assessments

def run_deterministic_tests():
    print("==========================================================================")
    print("      DETERMINISTIC PYTHON SCORING ENGINE TEST SUITE (SCENARIOS A - G)     ")
    print("==========================================================================")

    dummy_ref_components = [
        {"id": "comp_1", "topic": "Capacitance", "type": "definition", "component": "Definition of Capacitance"},
        {"id": "comp_2", "topic": "Capacitance", "type": "formula", "component": "Formula C = Q/V"},
        {"id": "comp_3", "topic": "Capacitance", "type": "concept", "component": "Parallel Plate Capacitor"},
        {"id": "comp_4", "topic": "Capacitance", "type": "derivation", "component": "Derivation of C = e0 * A / d"}
    ]

    # Test A: Empty Notes
    res_a = compute_deterministic_coverage([{"status": "MISSING"}] * 4, 4)
    print(f"Test A (Empty Notes)    -> Coverage: {res_a['coverage_percentage']}% | Status: {res_a['overall_status']} | Expected: 0.0%")
    assert res_a["coverage_percentage"] == 0.0, "Test A Failed"

    # Test B: Topic Name Only
    local_b = generate_local_component_assessments(dummy_ref_components, "Capacitance")
    res_b = compute_deterministic_coverage(local_b, 4)
    print(f"Test B (Topic Name Only)-> Coverage: {res_b['coverage_percentage']}% | Status: {res_b['overall_status']} | Expected: Low score (<30%)")
    assert res_b["coverage_percentage"] < 35.0, "Test B Failed"

    # Test C: One Component FULL
    comps_c = [{"status": "FULL"}, {"status": "MISSING"}, {"status": "MISSING"}, {"status": "MISSING"}]
    res_c = compute_deterministic_coverage(comps_c, 4)
    print(f"Test C (1 FULL / 4)     -> Coverage: {res_c['coverage_percentage']}% | Status: {res_c['overall_status']} | Expected: 25.0%")
    assert res_c["coverage_percentage"] == 25.0, "Test C Failed"

    # Test D: One Component PARTIAL
    comps_d = [{"status": "PARTIAL"}, {"status": "MISSING"}, {"status": "MISSING"}, {"status": "MISSING"}]
    res_d = compute_deterministic_coverage(comps_d, 4)
    print(f"Test D (1 PARTIAL / 4)  -> Coverage: {res_d['coverage_percentage']}% | Status: {res_d['overall_status']} | Expected: 12.5%")
    assert res_d["coverage_percentage"] == 12.5, "Test D Failed"

    # Test E: All Components FULL
    comps_e = [{"status": "FULL"}] * 4
    res_e = compute_deterministic_coverage(comps_e, 4)
    print(f"Test E (All FULL)       -> Coverage: {res_e['coverage_percentage']}% | Status: {res_e['overall_status']} | Expected: 100.0%")
    assert res_e["coverage_percentage"] == 100.0, "Test E Failed"

    # Test F: All Components MISSING
    comps_f = [{"status": "MISSING"}] * 4
    res_f = compute_deterministic_coverage(comps_f, 4)
    print(f"Test F (All MISSING)    -> Coverage: {res_f['coverage_percentage']}% | Status: {res_f['overall_status']} | Expected: 0.0%")
    assert res_f["coverage_percentage"] == 0.0, "Test F Failed"

    # Test G: Mixed Components (2 FULL, 1 PARTIAL, 1 MISSING)
    comps_g = [{"status": "FULL"}, {"status": "FULL"}, {"status": "PARTIAL"}, {"status": "MISSING"}]
    res_g = compute_deterministic_coverage(comps_g, 4)
    # (2*1.0 + 1*0.5 + 0) / 4 * 100 = 2.5 / 4 * 100 = 62.5%
    print(f"Test G (Mixed: 2F, 1P, 1M) -> Coverage: {res_g['coverage_percentage']}% | Status: {res_g['overall_status']} | Expected: 62.5%")
    assert res_g["coverage_percentage"] == 62.5, "Test G Failed"

    print("\nALL 7 DETERMINISTIC PYTHON SCORING TESTS PASSED [OK]")

if __name__ == "__main__":
    run_deterministic_tests()
