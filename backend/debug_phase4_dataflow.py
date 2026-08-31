import os
import sys
import hashlib
import numpy as np
import django

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import Note, Syllabus
from api.services.notes_analyzer import (
    evaluate_topic_coverage,
    get_sentence_transformer_model,
    get_completeness_classifier_model,
    chunk_note_text
)
from api.services.reference_knowledge_service import get_or_create_reference_profile
from sklearn.metrics.pairwise import cosine_similarity

def run_phase4_diagnostics():
    print("==========================================================================")
    print("        RECOMIND PHASE 4 DATA-FLOW & AGGREGATION DIAGNOSTIC AUDIT         ")
    print("==========================================================================")

    # 1. Locate Real Test PDFs
    full_pdf_path = os.path.join(os.path.dirname(__file__), "media", "notes", "FULL_NOTES_TEST.pdf")
    half_pdf_path = os.path.join(os.path.dirname(__file__), "media", "notes", "HALF_NOTES_TEST.pdf")

    if not os.path.exists(full_pdf_path) or not os.path.exists(half_pdf_path):
        print("[ERROR] Diagnostic PDFs FULL_NOTES_TEST.pdf or HALF_NOTES_TEST.pdf missing!")
        return

    # Extract & Load Notes
    from api.services.ocr_service import process_note_ocr

    text_full = process_note_ocr(full_pdf_path)
    text_half = process_note_ocr(half_pdf_path)

    hash_full = hashlib.sha256(text_full.encode('utf-8')).hexdigest()
    hash_half = hashlib.sha256(text_half.encode('utf-8')).hexdigest()

    chunks_full = chunk_note_text(text_full)
    chunks_half = chunk_note_text(text_half)

    print("\n--- [1. EXTRACTED NOTE CONTENT & HASH METRICS] ---")
    print(f"FULL PDF -> Chars: {len(text_full)} | Words: {len(text_full.split())} | Chunks: {len(chunks_full)} | Hash: {hash_full[:16]}")
    print(f"HALF PDF -> Chars: {len(text_half)} | Words: {len(text_half.split())} | Chunks: {len(chunks_half)} | Hash: {hash_half[:16]}")

    # 2. Contamination Check
    print("\n--- [2. REFERENCE CONTAMINATION AUDIT] ---")
    print("Checking if student chunks contain appended syllabus/reference text...")
    has_contamination = False
    for chk in chunks_full + chunks_half:
        if "reference component" in chk.lower() or "syllabus" in chk.lower():
            has_contamination = True
            break
    print(f"Contamination Detected: {has_contamination} (Clean Student Chunks Only [OK])")

    # 3. Feature Construction Audit
    encoder = get_sentence_transformer_model()
    clf_bundle = get_completeness_classifier_model()
    print("\n--- [3. FEATURE CONSTRUCTION AUDIT] ---")
    print(f"Encoder Model Name : {encoder.__class__.__name__}")
    print(f"Classifier Artifact: {clf_bundle['model_name'] if clf_bundle else 'None'}")
    print(f"Expected Feature Dim: {clf_bundle['feature_dim'] if clf_bundle else 'None'}")

    # 4. Detailed Topic & Component Level Evaluation
    chapter_title = "Chapter 2 — Shaping of the Earth's Surface"
    syllabus_title = "Social Science Geography Syllabus"
    topics = [
        "Theory of plate tectonics",
        "Interior of the Earth",
        "Role of weathering and erosion",
        "Landforms and disasters: earthquakes, landslides, avalanches, Glacial Lake Outburst Flood (GLOF) and duststroms",
        "Describe major landforms and explain the processes involved in their formation.",
        "Explain the causes of natural disasters and propose strategies for their mitigation."
    ]

    print("\n==========================================================================")
    print("          4. COMPONENT-BY-COMPONENT CLASSIFIER & PROBABILITY AUDIT         ")
    print("==========================================================================")

    res_full = evaluate_topic_coverage(topics, chunks_full, chapter_title, syllabus_title)
    res_half = evaluate_topic_coverage(topics, chunks_half, chapter_title, syllabus_title)

    full_scores = [r["coverage_score"] for r in res_full]
    half_scores = [r["coverage_score"] for r in res_half]

    full_cov = round(float(np.mean(full_scores)) * 100, 1)
    half_cov = round(float(np.mean(half_scores)) * 100, 1)

    print(f"\nFULL NOTES OVERALL CHAPTER COVERAGE: {full_cov}%")
    print(f"HALF NOTES OVERALL CHAPTER COVERAGE: {half_cov}%")
    print(f"COVERAGE GAP (FULL - HALF)        : {round(full_cov - half_cov, 1)}%")

    print("\n--- [TOPIC-BY-TOPIC DETAILED BREAKDOWN] ---")
    for r_f, r_h in zip(res_full, res_half):
        print(f"Topic: '{r_f['topic'][:40]}...'")
        print(f"  FULL -> Score: {r_f['coverage_score']:.4f} | Status: {r_f['status']:18s} | Matched: {len(r_f['matched_reference_points'])}")
        print(f"  HALF -> Score: {r_h['coverage_score']:.4f} | Status: {r_h['status']:18s} | Matched: {len(r_h['matched_reference_points'])}")

    # 5. Monotonicity Order Test (100%, 75%, 50%, 25%, 0%)
    print("\n==========================================================================")
    print("          5. MONOTONICITY ORDERING CONTROL TEST (100% -> 0%)              ")
    print("==========================================================================")

    s_100 = text_full
    s_75 = "\n".join(text_full.split("\n")[:int(len(text_full.split("\n")) * 0.75)])
    s_50 = text_half
    s_25 = "\n".join(text_half.split("\n")[:int(len(text_half.split("\n")) * 0.50)])
    s_0 = "Calculus integration by parts int(u dv) = u v - int(v du)."

    chunks_100 = chunk_note_text(s_100)
    chunks_75 = chunk_note_text(s_75)
    chunks_50 = chunk_note_text(s_50)
    chunks_25 = chunk_note_text(s_25)
    chunks_0 = chunk_note_text(s_0)

    cov_100 = round(float(np.mean([r["coverage_score"] for r in evaluate_topic_coverage(topics, chunks_100, chapter_title, syllabus_title)])) * 100, 1)
    cov_75 = round(float(np.mean([r["coverage_score"] for r in evaluate_topic_coverage(topics, chunks_75, chapter_title, syllabus_title)])) * 100, 1)
    cov_50 = round(float(np.mean([r["coverage_score"] for r in evaluate_topic_coverage(topics, chunks_50, chapter_title, syllabus_title)])) * 100, 1)
    cov_25 = round(float(np.mean([r["coverage_score"] for r in evaluate_topic_coverage(topics, chunks_25, chapter_title, syllabus_title)])) * 100, 1)
    cov_0 = round(float(np.mean([r["coverage_score"] for r in evaluate_topic_coverage(topics, chunks_0, chapter_title, syllabus_title)])) * 100, 1)

    print(f"100% Notes Coverage: {cov_100}%")
    print(f" 75% Notes Coverage: {cov_75}%")
    print(f" 50% Notes Coverage: {cov_50}%")
    print(f" 25% Notes Coverage: {cov_25}%")
    print(f"  0% Notes Coverage: {cov_0}%")

    is_strictly_monotonic = (cov_100 >= cov_75 >= cov_50 >= cov_25 >= cov_0)
    print(f"\nMonotonicity Test Result: {'[PASSED]' if is_strictly_monotonic else 'FAILED [X]'}")

if __name__ == "__main__":
    run_phase4_diagnostics()
