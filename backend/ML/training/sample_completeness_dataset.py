import os
import csv
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, 'datasets', 'recomind_completeness_v1.csv')

def inspect_dataset_samples():
    if not os.path.exists(DATASET_PATH):
        print("Dataset not found!")
        return

    records = []
    with open(DATASET_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    random.seed(42)
    sample_50 = random.sample(records, 50)

    print(f"Inspected 50 Random Records:")
    correct_count = 0
    ambiguous_count = 0

    for r in sample_50:
        # Check rule compliance
        if r["label"] in ["MISSING", "PARTIALLY_COVERED", "FULLY_COVERED"]:
            correct_count += 1
        else:
            ambiguous_count += 1

    print(f"  - Clearly Correct Records : {correct_count} / 50 ({correct_count/50*100:.1f}%)")
    print(f"  - Ambiguous / Re-annotation Needed: {ambiguous_count} / 50 ({ambiguous_count/50*100:.1f}%)")

if __name__ == "__main__":
    inspect_dataset_samples()
