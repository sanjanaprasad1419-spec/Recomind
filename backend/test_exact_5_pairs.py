import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from api.services.notes_analyzer import analyze_notes_against_syllabus, evaluate_topic_coverage, chunk_note_text

def test_exact_5_pairs():
    print("==========================================================================")
    print("                  STEP 7: DIRECT KNOWN SEMANTIC PAIRS TEST               ")
    print("==========================================================================")

    pairs = [
        ("Theory of plate tectonics", "The Earth's lithosphere is divided into tectonic plates that move slowly over the asthenosphere."),
        ("Interior of the Earth", "The Earth consists of three main layers: crust, mantle and core."),
        ("Weathering and erosion", "Weathering breaks rocks into smaller particles while erosion transports the weathered material."),
        ("Agents of gradation", "Rivers, sea waves, wind, glaciers and underground water erode and transport sediments."),
        ("Plate tectonics", "Double entry bookkeeping records debit and credit transactions.")
    ]

    expected_statuses = ["COVERED", "COVERED", "COVERED", "COVERED", "MISSING"]

    for idx, (topic, note) in enumerate(pairs, 1):
        chunks = chunk_note_text(note)
        res = evaluate_topic_coverage([topic], chunks)[0]
        status = res['status']
        score = res['coverage_score']
        exp = expected_statuses[idx - 1]

        print(f"\nPAIR {idx}:")
        print(f"  Topic: '{topic}'")
        print(f"  Notes: '{note[:75]}...'")
        print(f"  Score: {score} | Assigned Status: {status} | Expected: {exp}")
        assert (exp == "COVERED" and status in ["COVERED", "PARTIALLY_COVERED"]) or (exp == "MISSING" and status == "MISSING"), f"PAIR {idx} failed expectation!"

    print("\n==========================================================================")
    print("                 ALL 5 DIRECT SEMANTIC PAIRS PASSED 100%                   ")
    print("==========================================================================")

if __name__ == "__main__":
    test_exact_5_pairs()
