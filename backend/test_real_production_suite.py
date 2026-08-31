import os
import django
import numpy as np

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.services.notes_analyzer import evaluate_topic_coverage, chunk_note_text

def run_real_production_tests():
    print("==========================================================================")
    print("         CRITICAL REAL PRODUCTION-STYLE TEST SUITE (8 SCENARIOS)          ")
    print("==========================================================================")

    chapter_title = "Electrostatic Potential and Capacitance"
    syllabus_title = "Physics Class 12 Syllabus"
    topics = ["Capacitance of a Parallel Plate Capacitor", "Energy Stored in a Capacitor"]

    test_scenarios = [
        (
            "1. Detailed Student Note",
            "Capacitance of a parallel plate capacitor in vacuum is C = e0 * A / d where A is plate area and d is separation. Energy stored in a charged capacitor is U = 1/2 C V^2 = Q^2 / (2C). Dielectric insertion increases capacitance to C = K * C0."
        ),
        (
            "2. Sparse Student Note",
            "Capacitor stores electric charge. Capacitance formula exists."
        ),
        (
            "3. Topic-Name-Only Note",
            "Capacitance of a Parallel Plate Capacitor and Energy Stored in a Capacitor."
        ),
        (
            "4. Unrelated Note",
            "Photosynthesis in plants converts solar energy into glucose using chlorophyll and RuBisCO enzyme."
        ),
        (
            "5. Formulas Without Explanations Note",
            "C = e0 * A / d. U = 1/2 C V^2."
        ),
        (
            "6. Explanations Without Formulas Note",
            "Capacitance depends directly on plate surface area and inversely on distance between parallel plates. Energy is stored in the electrostatic field between plates."
        ),
        (
            "7. Partial Derivation Note",
            "Gaussian surface for parallel plates gives electric field E = sigma / e0."
        ),
        (
            "8. Complete Derivation Note",
            "Electric field between plates is E = sigma / e0 = Q / (e0 * A). Potential difference V = E * d = Q * d / (e0 * A). Capacitance C = Q / V = e0 * A / d."
        )
    ]

    for name, text in test_scenarios:
        chunks = chunk_note_text(text)
        results = evaluate_topic_coverage(topics, chunks, chapter_title, syllabus_title)
        
        scores = [r["coverage_score"] for r in results]
        overall_cov = round(float(np.mean(scores)) * 100, 1)

        covered = [r["topic"] for r in results if r["status"] == "COVERED"]
        partial = [r["topic"] for r in results if r["status"] == "PARTIALLY_COVERED"]
        missing = [r["topic"] for r in results if r["status"] == "MISSING"]

        print(f"\n--- [{name}] ---")
        print(f"  Note Excerpt  : '{text[:80]}...'")
        print(f"  Overall Cov   : {overall_cov}%")
        print(f"  Covered Topics: {len(covered)}")
        print(f"  Partial Topics: {len(partial)}")
        print(f"  Missing Topics: {len(missing)}")
        for r in results:
            if r["missing_aspects"]:
                print(f"  Missing Aspects for '{r['topic'][:30]}...': {r['missing_aspects'][:2]}")

if __name__ == "__main__":
    run_real_production_tests()
