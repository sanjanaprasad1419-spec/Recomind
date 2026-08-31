import os
import csv
import sys
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, 'datasets', 'recomind_completeness_v1.csv')

def validate_dataset():
    print("==========================================================================")
    print("      RECOMIND PHASE 2: DATASET VALIDATION (recomind_completeness_v1.csv) ")
    print("==========================================================================")

    if not os.path.exists(DATASET_PATH):
        print(f"[CRITICAL ERROR] Dataset file not found at: {DATASET_PATH}")
        sys.exit(1)

    records = []
    with open(DATASET_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    total_samples = len(records)
    print(f"\nTotal Records Loaded: {total_samples}")

    # 1. Total Count Validation (600 - 1,000)
    if total_samples < 600 or total_samples > 1000:
        print(f"[CRITICAL ERROR] Total samples ({total_samples}) outside target range 600-1,000!")
        sys.exit(1)
    else:
        print("  [OK] Total sample count within target range (600-1,000).")

    # 2. Field Completeness Check
    required_fields = [
        "id", "subject", "education_level", "chapter", "topic_name",
        "reference_component", "component_type", "student_note_evidence",
        "label", "numeric_score", "is_hard_negative", "source_type", "source_reference"
    ]
    
    empty_records = 0
    missing_source_metadata = 0
    invalid_labels = 0
    invalid_scores = 0

    valid_labels = {"MISSING", "PARTIALLY_COVERED", "FULLY_COVERED"}
    valid_scores = {"0.0", "0.5", "1.0", "0", "0.5", "1"}

    seen_pairs = set()
    duplicates = 0

    for idx, r in enumerate(records):
        # Check empty fields
        for field in required_fields:
            if not r.get(field, "").strip():
                empty_records += 1
                break

        # Check source metadata
        if not r.get("source_type") or not r.get("source_reference"):
            missing_source_metadata += 1

        # Check label and score validity
        lbl = r.get("label", "").strip()
        score = r.get("numeric_score", "").strip()
        if lbl not in valid_labels:
            invalid_labels += 1
        if score not in valid_scores:
            invalid_scores += 1

        # Check duplicate pairs
        pair_key = (r.get("reference_component", "").strip().lower(), r.get("student_note_evidence", "").strip().lower())
        if pair_key in seen_pairs:
            duplicates += 1
        seen_pairs.add(pair_key)

    print(f"  [OK] Empty/Incomplete Records: {empty_records}")
    print(f"  [OK] Missing Source Metadata: {missing_source_metadata}")
    print(f"  [OK] Duplicate Records: {duplicates}")
    print(f"  [OK] Invalid Labels: {invalid_labels}")
    print(f"  [OK] Invalid Scores: {invalid_scores}")

    if duplicates > 0 or invalid_labels > 0 or invalid_scores > 0 or empty_records > 0:
        print("[CRITICAL ERROR] Data integrity check failed!")
        sys.exit(1)

    # 3. Subject Distribution
    subjects = [r["subject"] for r in records]
    subject_counts = Counter(subjects)
    print("\n--- [SUBJECT DISTRIBUTION] ---")
    expected_subjects = {"Physics", "Chemistry", "Biology", "Mathematics", "Geography"}
    for subj in sorted(expected_subjects):
        cnt = subject_counts.get(subj, 0)
        pct = (cnt / total_samples) * 100
        print(f"  - {subj:12s}: {cnt:4d} records ({pct:.1f}%)")

    if not expected_subjects.issubset(set(subject_counts.keys())):
        print("[CRITICAL ERROR] Dataset missing one or more of the 5 required subjects!")
        sys.exit(1)

    # 4. Class Distribution
    labels = [r["label"] for r in records]
    label_counts = Counter(labels)
    print("\n--- [CLASS DISTRIBUTION] ---")
    for lbl in ["MISSING", "PARTIALLY_COVERED", "FULLY_COVERED"]:
        cnt = label_counts.get(lbl, 0)
        pct = (cnt / total_samples) * 100
        print(f"  - {lbl:18s}: {cnt:4d} records ({pct:.1f}%)")

    # 5. Hard Negative Count & Percentage
    hard_negs = [r for r in records if r.get("is_hard_negative", "").strip().lower() == "true"]
    hn_count = len(hard_negs)
    hn_pct = (hn_count / total_samples) * 100
    print("\n--- [HARD NEGATIVES] ---")
    print(f"  - Total Hard Negatives : {hn_count} records")
    print(f"  - Hard Negative Rate   : {hn_pct:.1f}%")

    if hn_pct < 25.0:
        print(f"[CRITICAL ERROR] Hard negative percentage ({hn_pct:.1f}%) is below required minimum of 25.0%!")
        sys.exit(1)
    else:
        print("  [OK] Hard negative constraint satisfied (>= 25.0%).")

    # 6. Component Types & Length Analysis
    comp_types = Counter([r["component_type"] for r in records])
    print("\n--- [COMPONENT TYPES] ---")
    for ct, count in comp_types.items():
        print(f"  - {ct:18s}: {count:4d} records")

    avg_ref_len = sum(len(r["reference_component"]) for r in records) / total_samples
    avg_note_len = sum(len(r["student_note_evidence"]) for r in records) / total_samples

    print("\n--- [TEXT LENGTH METRICS] ---")
    print(f"  - Average Reference Component Length : {avg_ref_len:.1f} chars")
    print(f"  - Average Student Evidence Length    : {avg_note_len:.1f} chars")

    print("\n==========================================================================")
    print("         ALL PHASE 2 DATASET VALIDATION CHECKS PASSED SUCCESSFULLY!       ")
    print("==========================================================================")
    sys.exit(0)

if __name__ == "__main__":
    validate_dataset()
