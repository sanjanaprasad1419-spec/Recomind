import os
import sys
import json
import logging
from unittest.mock import patch

# Ensure backend directory is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.services.gemini_notes_audit import (
    audit_student_notes_with_gemini,
    validate_gemini_audit_response,
    GeminiAuditValidationError,
    FORBIDDEN_KEYS,
    get_gemini_api_key
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def test_validation_rules_offline():
    print("\n--- RUNNING OFFLINE SCHEMA & BUSINESS RULE VALIDATION TESTS ---")
    
    reference_components = [
        {"id": "1", "component": "Definition of capacitance", "type": "definition"},
        {"id": "2", "component": "C = Q/V", "type": "formula"}
    ]

    # Test A: Rejection of forbidden coverage_percentage
    forbidden_data = {
        "components": [
            {"component_id": "1", "status": "FULL", "evidence": "Capacitance definition", "missing_aspects": []},
            {"component_id": "2", "status": "FULL", "evidence": "C = Q/V", "missing_aspects": []}
        ],
        "coverage_percentage": 100.0
    }
    try:
        validate_gemini_audit_response(forbidden_data, reference_components)
        assert False, "Failed to reject forbidden field 'coverage_percentage'!"
    except GeminiAuditValidationError as e:
        print(f"  [Pass] Correctly rejected forbidden field: {e}")

    # Test B: Rejection of missing component_id
    incomplete_data = {
        "components": [
            {"component_id": "1", "status": "FULL", "evidence": "Capacitance definition", "missing_aspects": []}
        ]
    }
    try:
        validate_gemini_audit_response(incomplete_data, reference_components)
        assert False, "Failed to reject missing reference component_id '2'!"
    except GeminiAuditValidationError as e:
        print(f"  [Pass] Correctly rejected incomplete component assessments: {e}")

    # Test C: Rejection of invalid status
    invalid_status_data = {
        "components": [
            {"component_id": "1", "status": "EXCELLENT", "evidence": "Capacitance definition", "missing_aspects": []},
            {"component_id": "2", "status": "FULL", "evidence": "C = Q/V", "missing_aspects": []}
        ]
    }
    try:
        validate_gemini_audit_response(invalid_status_data, reference_components)
        assert False, "Failed to reject invalid status 'EXCELLENT'!"
    except GeminiAuditValidationError as e:
        print(f"  [Pass] Correctly rejected invalid status: {e}")

    # Test D: Safe retry simulation
    mock_raw_malformed = json.dumps({"components": [], "coverage_percentage": 50.0})
    mock_raw_valid = json.dumps({
        "components": [
            {"component_id": "1", "status": "FULL", "evidence": "Capacitance is...", "missing_aspects": []},
            {"component_id": "2", "status": "FULL", "evidence": "C = Q/V", "missing_aspects": []}
        ]
    })

    with patch("api.services.gemini_notes_audit._call_gemini_raw", side_effect=[mock_raw_malformed, mock_raw_valid]), \
         patch("api.services.gemini_notes_audit.get_gemini_api_key", return_value="dummy_key"):
        res = audit_student_notes_with_gemini(
            chapter_name="Test Chapter",
            reference_components=reference_components,
            student_notes="Capacitance is... C = Q/V"
        )
        assert "components" in res
        assert len(res["components"]) == 2
        print("  [Pass] 1-retry safe retry mechanism successfully recovered valid response after initial malformed response.")


def test_live_gemini_academic_auditor():
    api_key = get_gemini_api_key()
    if not api_key:
        print("\n[NOTE] GEMINI_API_KEY is not currently exported in environment.")
        print("       Offline validation tests passed clean. Export GEMINI_API_KEY to run live Gemini 2.5 Flash calls.")
        return

    print("==========================================================================")
    print("      RECOMIND STEP 1: LIVE GEMINI ACADEMIC AUDITOR VALIDATION SUITE      ")
    print("==========================================================================")

    chapter_name = "Electrostatic Potential and Capacitance"
    
    reference_components = [
        {
            "id": "1",
            "component": "Definition of capacitance",
            "type": "definition"
        },
        {
            "id": "2",
            "component": "C = Q/V",
            "type": "formula"
        },
        {
            "id": "3",
            "component": "Parallel plate capacitor",
            "type": "concept"
        },
        {
            "id": "4",
            "component": "Energy stored U = 1/2 CV²",
            "type": "formula"
        },
        {
            "id": "5",
            "component": "Derivation of parallel plate capacitance",
            "type": "derivation"
        }
    ]

    # -------------------------------------------------------------------------
    # TEST 1: PARTIAL STUDENT NOTES
    # -------------------------------------------------------------------------
    student_notes_1 = """Capacitance is the ability of a conductor to store charge.
C = Q/V."""

    print("\n--- TEST 1: Partial Student Notes ---")
    print(f"Notes:\n{student_notes_1.strip()}\n")

    res1 = audit_student_notes_with_gemini(
        chapter_name=chapter_name,
        reference_components=reference_components,
        student_notes=student_notes_1
    )

    print("Gemini Output (STRICT JSON):")
    print(json.dumps(res1, indent=2))

    # Verify forbidden keys
    for k in FORBIDDEN_KEYS:
        assert k not in res1, f"Forbidden key '{k}' found in response!"

    evals_1 = {item["component_id"]: item for item in res1["components"]}
    assert evals_1["1"]["status"] == "FULL", f"Expected 1 -> FULL, got {evals_1['1']['status']}"
    assert evals_1["2"]["status"] == "FULL", f"Expected 2 -> FULL, got {evals_1['2']['status']}"
    assert evals_1["3"]["status"] == "MISSING", f"Expected 3 -> MISSING, got {evals_1['3']['status']}"
    assert evals_1["4"]["status"] == "MISSING", f"Expected 4 -> MISSING, got {evals_1['4']['status']}"
    assert evals_1["5"]["status"] == "MISSING", f"Expected 5 -> MISSING, got {evals_1['5']['status']}"
    print("✅ TEST 1 PASSED EXPECTED QUALITATIVE BEHAVIOR (1:FULL, 2:FULL, 3:MISSING, 4:MISSING, 5:MISSING)")

    # -------------------------------------------------------------------------
    # TEST 2: DETAILED STUDENT NOTES WITH DERIVATION
    # -------------------------------------------------------------------------
    student_notes_2 = """Capacitance is the ability of a conductor to store charge.
The capacitance of a parallel plate capacitor is C = ε₀A/d.
Using Gauss's law, electric field is obtained and potential difference
is calculated before applying C = Q/V."""

    print("\n--- TEST 2: Detailed Student Notes ---")
    print(f"Notes:\n{student_notes_2.strip()}\n")

    res2 = audit_student_notes_with_gemini(
        chapter_name=chapter_name,
        reference_components=reference_components,
        student_notes=student_notes_2
    )

    print("Gemini Output (STRICT JSON):")
    print(json.dumps(res2, indent=2))

    evals_2 = {item["component_id"]: item for item in res2["components"]}
    assert evals_2["1"]["status"] == "FULL", f"Expected 1 -> FULL, got {evals_2['1']['status']}"
    assert evals_2["2"]["status"] in ("FULL", "PARTIAL"), f"Expected 2 -> FULL/PARTIAL, got {evals_2['2']['status']}"
    assert evals_2["3"]["status"] == "FULL", f"Expected 3 -> FULL, got {evals_2['3']['status']}"
    assert evals_2["4"]["status"] == "MISSING", f"Expected 4 -> MISSING, got {evals_2['4']['status']}"
    assert evals_2["5"]["status"] in ("FULL", "PARTIAL"), f"Expected 5 -> FULL/PARTIAL, got {evals_2['5']['status']}"
    print("✅ TEST 2 PASSED EXPECTED QUALITATIVE BEHAVIOR")

    # -------------------------------------------------------------------------
    # TEST 3: TOPIC-NAME-ONLY PRESENCE TEST
    # -------------------------------------------------------------------------
    student_notes_3 = "Capacitance"
    ref_topic_only = [
        {
            "id": "4",
            "component": "Energy stored U = 1/2 CV²",
            "type": "formula"
        }
    ]

    print("\n--- TEST 3: Topic-Name-Only Presence Test ---")
    print("Student Notes: 'Capacitance'")
    print("Reference Component: 'Energy stored U = 1/2 CV²'")

    res3 = audit_student_notes_with_gemini(
        chapter_name=chapter_name,
        reference_components=ref_topic_only,
        student_notes=student_notes_3
    )

    print("Gemini Output (STRICT JSON):")
    print(json.dumps(res3, indent=2))

    evals_3 = {item["component_id"]: item for item in res3["components"]}
    assert evals_3["4"]["status"] == "MISSING", f"Expected MISSING for topic-name-only match, got {evals_3['4']['status']}"
    print("✅ TOPIC-NAME-ONLY TEST PASSED: Topic name presence alone is correctly evaluated as MISSING!")

    print("\n==========================================================================")
    print("          ALL STEP 1 GEMINI AUDITOR TESTS PASSED SUCCESSFULLY!            ")
    print("==========================================================================")


if __name__ == "__main__":
    test_validation_rules_offline()
    test_live_gemini_academic_auditor()
