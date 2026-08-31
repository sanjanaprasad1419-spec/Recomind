import os
import sys
import json
import logging
from unittest.mock import patch

# Ensure backend directory is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.services.gemini_ai_coverage import (
    analyze_notes_coverage_ai,
    validate_gemini_coverage_response,
    GeminiCoverageValidationError,
    get_gemini_api_key
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def test_coverage_validation_offline():
    print("\n--- RUNNING OFFLINE COVERAGE VALIDATION TESTS ---")

    # Test A: Valid response
    valid_data = {
        "coverage_percentage": 67,
        "status": "NEEDS_IMPROVEMENT",
        "brief_reason": "Notes cover basic definitions but omit key formulas."
    }
    validated = validate_gemini_coverage_response(valid_data)
    assert validated["coverage_percentage"] == 67
    assert validated["status"] == "NEEDS_IMPROVEMENT"
    print("  [Pass] Valid coverage data validated successfully.")

    # Test B: Out of bounds percentage rejection
    invalid_pct_data = {
        "coverage_percentage": 150,
        "status": "GOOD",
        "brief_reason": "Everything is great."
    }
    try:
        validate_gemini_coverage_response(invalid_pct_data)
        assert False, "Failed to reject out-of-bounds percentage 150!"
    except GeminiCoverageValidationError as e:
        print(f"  [Pass] Correctly rejected out-of-bounds percentage: {e}")

    # Test C: Safe retry simulation
    mock_malformed = json.dumps({"coverage_percentage": "invalid_num"})
    mock_corrected = json.dumps({
        "coverage_percentage": 45,
        "status": "NEEDS_IMPROVEMENT",
        "brief_reason": "Partial coverage."
    })

    with patch("api.services.gemini_ai_coverage._call_gemini_raw", side_effect=[mock_malformed, mock_corrected]), \
         patch("api.services.gemini_ai_coverage.get_gemini_api_key", return_value="dummy_key"):
        res = analyze_notes_coverage_ai("Sample notes", "Sample syllabus", "Sample Chapter")
        assert res["coverage_percentage"] == 45
        assert res["status"] == "NEEDS_IMPROVEMENT"
        print("  [Pass] 1-retry recovery mechanism successfully parsed corrected response.")


def test_critical_content_ordering_suite():
    api_key = get_gemini_api_key()
    if not api_key:
        print("\n[NOTE] GEMINI_API_KEY is not currently exported in environment.")
        print("       Offline validation tests passed clean. Export GEMINI_API_KEY to run live Gemini 2.5 Flash critical ordering tests.")
        return

    print("\n==========================================================================")
    print("      RECOMIND STEP 2: CRITICAL AI CONTENT COVERAGE ORDERING TEST         ")
    print("==========================================================================")

    chapter_name = "Electrostatic Potential and Capacitance"
    syllabus_text = """
1. Definition of capacitance as capacity of conductor to store charge.
2. Formula for capacitance C = Q/V.
3. Parallel plate capacitor: structure, electric field, potential difference, and capacitance formula C = ε₀A/d.
4. Effect of dielectric medium on capacitance C = K ε₀A/d.
5. Energy stored in a capacitor U = 1/2 CV² = 1/2 Q²/C = 1/2 QV.
6. Derivation of energy stored in a parallel plate capacitor.
"""

    # Variant A: Detailed Student Notes
    notes_A_detailed = """
Capacitance is defined as the measure of the ability of a conductor to store electric charge per unit potential difference, expressed by C = Q/V.
For a parallel plate capacitor consisting of two conducting plates of area A separated by distance d in vacuum, electric field between plates is E = σ/ε₀ = Q/(ε₀A).
Potential difference V = E * d = (Qd)/(ε₀A). Therefore, capacitance is C = Q/V = (ε₀A)/d.
When a dielectric slab of dielectric constant K is introduced between the plates, capacitance increases to C = K ε₀A/d.
Energy stored in a capacitor is obtained by calculating work done in charging it: dW = v dq = (q/C) dq.
Integrating from 0 to Q gives total energy U = ∫ (q/C) dq = Q²/(2C) = 1/2 CV² = 1/2 QV.
"""

    # Variant B: Sparse Student Notes
    notes_B_sparse = """
Capacitance is the ability to store charge.
C = Q/V.
Parallel plate capacitor formula is C = ε₀A/d.
Dielectric constant increases capacitance.
Energy stored in capacitor formula is U = 1/2 CV².
"""

    # Variant C: Topic-Name-Only Notes
    notes_C_topic_only = """
Electrostatic Potential and Capacitance
- Definition of capacitance
- Parallel plate capacitor
- Dielectric effect
- Energy stored in capacitor
- Derivation
"""

    # Variant D: Unrelated Notes
    notes_D_unrelated = """
Photosynthesis is the biological process used by plants to convert light energy into chemical energy stored in glucose molecules.
Chlorophyll absorbs sunlight in chloroplasts, splitting water into oxygen and hydrogen ions during light reactions.
Carbon dioxide is fixed in the Calvin cycle to synthesize carbohydrates.
"""

    print("\nExecuting Gemini 2.5 Flash Coverage Evaluations across 4 content variants...\n")

    res_A = analyze_notes_coverage_ai(notes_A_detailed, syllabus_text, chapter_name)
    res_B = analyze_notes_coverage_ai(notes_B_sparse, syllabus_text, chapter_name)
    res_C = analyze_notes_coverage_ai(notes_C_topic_only, syllabus_text, chapter_name)
    res_D = analyze_notes_coverage_ai(notes_D_unrelated, syllabus_text, chapter_name)

    score_A = res_A.get("coverage_percentage", 0)
    score_B = res_B.get("coverage_percentage", 0)
    score_C = res_C.get("coverage_percentage", 0)
    score_D = res_D.get("coverage_percentage", 0)

    print(f"Variant A (Detailed Notes)   : {score_A}% [{res_A.get('status')}] - Reason: {res_A.get('brief_reason')}")
    print(f"Variant B (Sparse Notes)     : {score_B}% [{res_B.get('status')}] - Reason: {res_B.get('brief_reason')}")
    print(f"Variant C (Topic-Name Only)  : {score_C}% [{res_C.get('status')}] - Reason: {res_C.get('brief_reason')}")
    print(f"Variant D (Unrelated Notes)  : {score_D}% [{res_D.get('status')}] - Reason: {res_D.get('brief_reason')}")

    print("\n--- QUALITATIVE ORDERING VERIFICATION ---")
    print(f"Detailed ({score_A}%) > Sparse ({score_B}%) : {score_A > score_B}")
    print(f"Sparse ({score_B}%) > Topic-Only ({score_C}%) : {score_B > score_C}")
    print(f"Topic-Only ({score_C}%) > Unrelated ({score_D}%) : {score_C >= score_D}")

    assert score_A >= score_B, f"Detailed notes ({score_A}%) should be >= Sparse notes ({score_B}%)"
    assert score_B >= score_C, f"Sparse notes ({score_B}%) should be >= Topic-Only notes ({score_C}%)"
    assert score_D <= 15, f"Unrelated notes ({score_D}%) should be very low"

    print("\n==========================================================================")
    print("          CRITICAL CONTENT ORDERING TEST PASSED SUCCESSFULLY!             ")
    print("==========================================================================")


if __name__ == "__main__":
    test_coverage_validation_offline()
    test_critical_content_ordering_suite()
