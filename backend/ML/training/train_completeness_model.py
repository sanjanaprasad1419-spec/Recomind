import os
import sys
import csv
import joblib
import numpy as np
from collections import Counter
from sklearn.model_selection import GroupShuffleSplit
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, f1_score
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, 'datasets', 'recomind_completeness_v1.csv')
SAVED_MODELS_DIR = os.path.join(BASE_DIR, 'saved_models')
os.makedirs(SAVED_MODELS_DIR, exist_ok=True)

MODEL_OUTPUT_PATH = os.path.join(SAVED_MODELS_DIR, 'completeness_classifier_v1.joblib')

# Fix Random Seeds for Reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

def extract_features(ref_embeds, student_embeds):
    """
    Constructs feature vectors from embeddings:
    [v_ref, v_student, |v_ref - v_student|, v_ref * v_student, cosine_sim]
    """
    features = []
    for r, s in zip(ref_embeds, student_embeds):
        r_norm = r / (np.linalg.norm(r) + 1e-9)
        s_norm = s / (np.linalg.norm(s) + 1e-9)
        
        abs_diff = np.abs(r - s)
        elem_prod = r * s
        cos_sim = np.dot(r_norm, s_norm)
        
        # Combine into a feature vector (384*4 + 1 = 1537 dimensions)
        feat_vec = np.hstack([r, s, abs_diff, elem_prod, [cos_sim]])
        features.append(feat_vec)
        
    return np.array(features)

def calculate_false_full_rate(y_true, y_pred):
    """
    Calculates False FULL Rate:
    (Count where True != FULL and Pred == FULL) / Total Predicted FULL
    """
    pred_full_indices = [i for i, p in enumerate(y_pred) if p == 2]
    if not pred_full_indices:
        return 0.0
    
    false_full_count = sum(1 for i in pred_full_indices if y_true[i] != 2)
    return false_full_count / len(pred_full_indices)

def run_training_pipeline():
    print("==========================================================================")
    print("      RECOMIND PHASE 3: SUPERVISED NOTE COMPLETENESS MODEL TRAINING        ")
    print("==========================================================================")

    if not os.path.exists(DATASET_PATH):
        print(f"[CRITICAL ERROR] Dataset file not found at: {DATASET_PATH}")
        sys.exit(1)

    records = []
    with open(DATASET_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    print(f"Loaded {len(records)} records from dataset.")

    # 1. Prepare Target Labels and Group Keys
    label_map = {"MISSING": 0, "PARTIALLY_COVERED": 1, "FULLY_COVERED": 2}
    inv_label_map = {0: "MISSING", 1: "PARTIALLY_COVERED", 2: "FULLY_COVERED"}

    y_all = np.array([label_map[r["label"]] for r in records])
    groups_all = np.array([r["topic_name"] for r in records])

    # 2. Leakage-Safe Group-Based Dataset Splitting (70% Train, 15% Val, 15% Test by Topic)
    gss_test = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=RANDOM_SEED)
    train_val_idx, test_idx = next(gss_test.split(records, y_all, groups=groups_all))

    train_val_records = [records[i] for i in train_val_idx]
    train_val_y = y_all[train_val_idx]
    train_val_groups = groups_all[train_val_idx]

    gss_val = GroupShuffleSplit(n_splits=1, test_size=0.176, random_state=RANDOM_SEED) # 0.176 * 0.85 approx 15%
    train_sub_idx, val_idx = next(gss_val.split(train_val_records, train_val_y, groups=train_val_groups))

    final_train_idx = train_val_idx[train_sub_idx]
    final_val_idx = train_val_idx[val_idx]

    train_records = [records[i] for i in final_train_idx]
    val_records = [records[i] for i in final_val_idx]
    test_records = [records[i] for i in test_idx]

    y_train = y_all[final_train_idx]
    y_val = y_all[final_val_idx]
    y_test = y_all[test_idx]

    print(f"\n--- Data Split Summary ---")
    print(f"  - Train Set: {len(train_records)} samples ({len(train_records)/len(records)*100:.1f}%)")
    print(f"  - Val Set  : {len(val_records)} samples ({len(val_records)/len(records)*100:.1f}%)")
    print(f"  - Test Set : {len(test_records)} samples ({len(test_records)/len(records)*100:.1f}%)")

    # Verify zero topic overlap between train and test
    train_topics = set(r["topic_name"] for r in train_records)
    test_topics = set(r["topic_name"] for r in test_records)
    topic_overlap = train_topics.intersection(test_topics)
    print(f"  - Topic Overlap between Train and Test: {len(topic_overlap)} topics (Leakage Safe [OK])")

    # 3. Generate SentenceTransformer Embeddings
    print("\n[INFO] Loading SentenceTransformer 'all-MiniLM-L6-v2' encoder...")
    encoder = SentenceTransformer('all-MiniLM-L6-v2')

    ref_texts_all = [r["reference_component"] for r in records]
    student_texts_all = [r["student_note_evidence"] for r in records]

    print("[INFO] Computing 384-dim embeddings for reference components and student evidence...")
    ref_embeds = encoder.encode(ref_texts_all, batch_size=32, show_progress_bar=False)
    student_embeds = encoder.encode(student_texts_all, batch_size=32, show_progress_bar=False)

    # 4. Feature Engineering
    X_all = extract_features(ref_embeds, student_embeds)
    X_train = X_all[final_train_idx]
    X_val = X_all[final_val_idx]
    X_test = X_all[test_idx]

    # 5. Baseline Evaluation (Zero-Shot Cosine Similarity + Threshold Rule)
    print("\n==========================================================================")
    print("                      1. BASELINE EVALUATION (Zero-Shot)                  ")
    print("==========================================================================")
    
    test_cos_sims = X_test[:, -1] # Last feature is cosine similarity
    y_pred_baseline = []
    for sim in test_cos_sims:
        if sim >= 0.70:
            y_pred_baseline.append(2) # FULL
        elif sim >= 0.45:
            y_pred_baseline.append(1) # PARTIAL
        else:
            y_pred_baseline.append(0) # MISSING

    acc_base = accuracy_score(y_test, y_pred_baseline)
    macro_f1_base = f1_score(y_test, y_pred_baseline, average='macro')
    false_full_base = calculate_false_full_rate(y_test, y_pred_baseline)

    print(f"  - Baseline Accuracy      : {acc_base * 100:.2f}%")
    print(f"  - Baseline Macro F1      : {macro_f1_base * 100:.2f}%")
    print(f"  - Baseline False FULL Rate: {false_full_base * 100:.2f}%")

    # 6. Train Candidate Supervised Classifiers
    print("\n==========================================================================")
    print("                     2. SUPERVISED MODELS TRAINING                       ")
    print("==========================================================================")

    models = {
        "Logistic Regression": LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=RANDOM_SEED),
        "Random Forest": RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=RANDOM_SEED),
        "HistGradientBoosting": HistGradientBoostingClassifier(max_iter=100, random_state=RANDOM_SEED)
    }

    best_model_name = None
    best_macro_f1 = -1.0
    best_model = None

    for m_name, m_obj in models.items():
        m_obj.fit(X_train, y_train)
        y_val_pred = m_obj.predict(X_val)
        val_acc = accuracy_score(y_val, y_val_pred)
        val_f1 = f1_score(y_val, y_val_pred, average='macro')
        val_false_full = calculate_false_full_rate(y_val, y_val_pred)

        print(f"  Model: {m_name:20s} | Val Acc: {val_acc*100:.2f}% | Val Macro F1: {val_f1*100:.2f}% | False FULL: {val_false_full*100:.2f}%")

        if val_f1 > best_macro_f1:
            best_macro_f1 = val_f1
            best_model_name = m_name
            best_model = m_obj

    print(f"\n[INFO] Selected Best Supervised Model: '{best_model_name}' (Val Macro F1 = {best_macro_f1*100:.2f}%)")

    # 7. Comprehensive Test Set Evaluation of Best Supervised Model
    print("\n==========================================================================")
    print(f"            3. TEST SET EVALUATION ({best_model_name.upper()})            ")
    print("==========================================================================")

    y_test_pred = best_model.predict(X_test)
    y_test_proba = best_model.predict_proba(X_test)

    acc_test = accuracy_score(y_test, y_test_pred)
    prec_test, rec_test, f1_test, _ = precision_recall_fscore_support(y_test, y_test_pred, average=None, labels=[0, 1, 2])
    macro_f1_test = f1_score(y_test, y_test_pred, average='macro')
    weighted_f1_test = f1_score(y_test, y_test_pred, average='weighted')
    false_full_test = calculate_false_full_rate(y_test, y_test_pred)
    cm_test = confusion_matrix(y_test, y_test_pred, labels=[0, 1, 2])

    print(f"  - Overall Accuracy      : {acc_test * 100:.2f}%")
    print(f"  - Macro F1-Score        : {macro_f1_test * 100:.2f}%")
    print(f"  - Weighted F1-Score     : {weighted_f1_test * 100:.2f}%")
    print(f"  - False FULL Rate       : {false_full_test * 100:.2f}% (Baseline was {false_full_base * 100:.2f}%)")
    
    print("\n  --- Confusion Matrix ---")
    print("  Pred:   MISSING  PARTIAL  FULL")
    print(f"  MISS  : {cm_test[0][0]:7d}  {cm_test[0][1]:7d}  {cm_test[0][2]:4d}")
    print(f"  PART  : {cm_test[1][0]:7d}  {cm_test[1][1]:7d}  {cm_test[1][2]:4d}")
    print(f"  FULL  : {cm_test[2][0]:7d}  {cm_test[2][1]:7d}  {cm_test[2][2]:4d}")

    print("\n  --- Per-Class Performance ---")
    for i, c_name in inv_label_map.items():
        print(f"  - {c_name:18s}: Precision = {prec_test[i]*100:.2f}% | Recall = {rec_test[i]*100:.2f}% | F1 = {f1_test[i]*100:.2f}%")

    # 8. Hard Negative Evaluation
    print("\n==========================================================================")
    print("                      4. HARD-NEGATIVE EVALUATION                         ")
    print("==========================================================================")

    test_hn_indices = [i for i, idx in enumerate(test_idx) if records[idx].get("is_hard_negative", "").strip().lower() == "true"]
    y_test_hn = y_test[test_hn_indices]
    y_pred_hn = y_test_pred[test_hn_indices]

    acc_hn = accuracy_score(y_test_hn, y_pred_hn)
    macro_f1_hn = f1_score(y_test_hn, y_pred_hn, average='macro')
    false_full_hn = calculate_false_full_rate(y_test_hn, y_pred_hn)

    print(f"  - Hard Negative Count   : {len(test_hn_indices)} samples")
    print(f"  - Hard Negative Accuracy: {acc_hn * 100:.2f}%")
    print(f"  - Hard Negative Macro F1: {macro_f1_hn * 100:.2f}%")
    print(f"  - Hard Negative False FULL Rate: {false_full_hn * 100:.2f}%")

    # 9. Subject-Wise Evaluation
    print("\n==========================================================================")
    print("                      5. SUBJECT-WISE EVALUATION                          ")
    print("==========================================================================")

    subjects = ["Physics", "Chemistry", "Biology", "Mathematics", "Geography"]
    subject_results = {}
    for subj in subjects:
        subj_indices = [i for i, idx in enumerate(test_idx) if records[idx]["subject"] == subj]
        if subj_indices:
            y_s_true = y_test[subj_indices]
            y_s_pred = y_test_pred[subj_indices]
            s_acc = accuracy_score(y_s_true, y_s_pred)
            s_f1 = f1_score(y_s_true, y_s_pred, average='macro')
            subject_results[subj] = (s_acc, s_f1, len(subj_indices))
            print(f"  - {subj:12s}: Acc = {s_acc*100:.2f}% | Macro F1 = {s_f1*100:.2f}% | N = {len(subj_indices)}")

    # 10. Critical Sanity Test Set Evaluation
    print("\n==========================================================================")
    print("                      6. CRITICAL SANITY TEST SUITE                       ")
    print("==========================================================================")

    sanity_cases = [
        ("Capacitance of a parallel plate capacitor is C = e0 * A / d.", "Capacitors store electric charge.", 0, "Topic-name-only"),
        ("Capacitance of a parallel plate capacitor is C = e0 * A / d.", "Capacitance depends on plate area and separation.", 1, "Partial concept without formula"),
        ("Capacitance of a parallel plate capacitor is C = e0 * A / d.", "For two parallel plates of area A separated by d in vacuum, C = e0 * A / d.", 2, "Full formula match"),
        ("Derivation of electric field due to infinitely long wire.", "Electric field due to a long wire is E = lambda / (2 * pi * e0 * r).", 1, "Final formula without derivation steps"),
        ("Locate major tectonic plates on a world map.", "Plate tectonics explains movement of lithospheric plates.", 0, "Keyword overlap missing map"),
        ("Energy stored in capacitor is U = 1/2 C V^2.", "Capacitor stores electrostatic potential energy.", 1, "Partial concept without math equation")
    ]

    sanity_results = []
    for r_t, s_t, expected_lbl, desc in sanity_cases:
        r_emb = encoder.encode([r_t], show_progress_bar=False)
        s_emb = encoder.encode([s_t], show_progress_bar=False)
        feat_vec = extract_features(r_emb, s_emb)
        pred_l = int(best_model.predict(feat_vec)[0])
        pred_p = best_model.predict_proba(feat_vec)[0]
        status_ok = (pred_l == expected_lbl)
        sanity_results.append((desc, inv_label_map[expected_lbl], inv_label_map[pred_l], status_ok))
        print(f"  - [{desc:35s}] Expected: {inv_label_map[expected_lbl]:8s} | Pred: {inv_label_map[pred_l]:8s} | Passed: {status_ok}")

    # 11. Error Analysis (Mandatory 30 Misclassifications)
    print("\n==========================================================================")
    print("               7. MANDATORY MISCLASSIFICATION ERROR ANALYSIS              ")
    print("==========================================================================")

    y_all_pred = best_model.predict(X_all)
    y_all_proba = best_model.predict_proba(X_all)
    mis_indices = [i for i in range(len(records)) if y_all[i] != y_all_pred[i]]
    print(f"  - Total Misclassifications Across Full Dataset: {len(mis_indices)} / {len(records)} ({len(mis_indices)/len(records)*100:.1f}%)")
    
    print("\n  Showing Sample Misclassified Records for Diagnostics:")
    for count, i in enumerate(mis_indices[:30]):
        rec = records[i]
        t_lbl = inv_label_map[y_all[i]]
        p_lbl = inv_label_map[y_all_pred[i]]
        probs = y_all_proba[i]
        print(f"  [{count+1:02d}] Subj: {rec['subject']:10s} | Topic: {rec['topic_name'][:25]:25s}")
        print(f"       Ref : {rec['reference_component'][:75]}...")
        print(f"       Note: {rec['student_note_evidence'][:75]}...")
        print(f"       True: {t_lbl:8s} | Pred: {p_lbl:8s} | Probs: [M:{probs[0]:.2f}, P:{probs[1]:.2f}, F:{probs[2]:.2f}]\n")

    # 12. Save Trained Pipeline & Metadata Artifact
    artifact = {
        "model_name": best_model_name,
        "model": best_model,
        "encoder_name": "sentence-transformers/all-MiniLM-L6-v2",
        "feature_dim": X_train.shape[1],
        "dataset_version": "v1.0 (888 records)",
        "label_map": label_map,
        "inv_label_map": inv_label_map,
        "metrics": {
            "accuracy": float(acc_test),
            "macro_f1": float(macro_f1_test),
            "weighted_f1": float(weighted_f1_test),
            "false_full_rate": float(false_full_test),
            "baseline_macro_f1": float(macro_f1_base),
            "baseline_false_full": float(false_full_base)
        }
    }

    joblib.dump(artifact, MODEL_OUTPUT_PATH)
    print(f"[SUCCESS] Saved Supervised Completeness Model Artifact to: {MODEL_OUTPUT_PATH}")

if __name__ == "__main__":
    run_training_pipeline()
