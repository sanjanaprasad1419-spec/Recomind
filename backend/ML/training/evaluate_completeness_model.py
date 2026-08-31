import os
import sys
import csv
import joblib
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, f1_score
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, 'datasets', 'recomind_completeness_v1.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'saved_models', 'completeness_classifier_v1.joblib')

def extract_features(ref_embeds, student_embeds):
    features = []
    for r, s in zip(ref_embeds, student_embeds):
        r_norm = r / (np.linalg.norm(r) + 1e-9)
        s_norm = s / (np.linalg.norm(s) + 1e-9)
        abs_diff = np.abs(r - s)
        elem_prod = r * s
        cos_sim = np.dot(r_norm, s_norm)
        feat_vec = np.hstack([r, s, abs_diff, elem_prod, [cos_sim]])
        features.append(feat_vec)
    return np.array(features)

def calculate_false_full_rate(y_true, y_pred):
    pred_full_indices = [i for i, p in enumerate(y_pred) if p == 2]
    if not pred_full_indices:
        return 0.0
    false_full_count = sum(1 for i in pred_full_indices if y_true[i] != 2)
    return false_full_count / len(pred_full_indices)

def evaluate_standalone_model():
    print("==========================================================================")
    print("     RECOMIND PHASE 3: STANDALONE MODEL EVALUATION & VERIFICATION         ")
    print("==========================================================================")

    if not os.path.exists(MODEL_PATH):
        print(f"[CRITICAL ERROR] Model artifact not found at: {MODEL_PATH}")
        sys.exit(1)

    if not os.path.exists(DATASET_PATH):
        print(f"[CRITICAL ERROR] Dataset file not found at: {DATASET_PATH}")
        sys.exit(1)

    # Load Artifact
    artifact = joblib.load(MODEL_PATH)
    model = artifact["model"]
    encoder_name = artifact["encoder_name"]
    inv_label_map = artifact["inv_label_map"]

    print(f"Loaded Trained Model: '{artifact['model_name']}'")
    print(f"Dataset Version     : '{artifact['dataset_version']}'")
    print(f"Feature Dimension   : {artifact['feature_dim']}")

    # Load Dataset
    records = []
    with open(DATASET_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    print(f"Loaded {len(records)} evaluation records.")

    # Load Encoder
    encoder = SentenceTransformer(encoder_name)
    ref_texts = [r["reference_component"] for r in records]
    student_texts = [r["student_note_evidence"] for r in records]

    ref_embeds = encoder.encode(ref_texts, batch_size=32, show_progress_bar=False)
    student_embeds = encoder.encode(student_texts, batch_size=32, show_progress_bar=False)
    X_all = extract_features(ref_embeds, student_embeds)
    y_all = np.array([artifact["label_map"][r["label"]] for r in records])

    # Predict Across Full Dataset
    y_pred = model.predict(X_all)
    y_proba = model.predict_proba(X_all)

    acc = accuracy_score(y_all, y_pred)
    macro_f1 = f1_score(y_all, y_pred, average='macro')
    false_full = calculate_false_full_rate(y_all, y_pred)

    print("\n--- Full Evaluation Dataset Performance ---")
    print(f"  - Overall Accuracy      : {acc * 100:.2f}%")
    print(f"  - Macro F1-Score        : {macro_f1 * 100:.2f}%")
    print(f"  - False FULL Rate       : {false_full * 100:.2f}%")

    print("\n==========================================================================")
    print("           STANDALONE MODEL EVALUATION COMPLETED SUCCESSFULLY            ")
    print("==========================================================================")

if __name__ == "__main__":
    evaluate_standalone_model()
