import os
import csv
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, 'datasets', 'recomind_domain_dataset.csv')
SAVED_MODELS_DIR = os.path.join(BASE_DIR, 'saved_models')

os.makedirs(SAVED_MODELS_DIR, exist_ok=True)

MODEL_OUTPUT_PATH = os.path.join(SAVED_MODELS_DIR, 'domain_classifier.joblib')

def train_and_evaluate():
    print("[INFO] Starting RecoMind Stage 1 Model Training & Evaluation...")

    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset file not found at: {DATASET_PATH}")

    texts = []
    labels = []

    with open(DATASET_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row['text'])
            labels.append(row['domain'])

    print(f"Loaded {len(texts)} samples across {len(set(labels))} unique domains.")

    # Train / Test Split (80% Train, 20% Test)
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        texts, labels, test_size=0.20, random_state=42, stratify=labels
    )

    print(f"Train samples: {len(X_train_raw)}, Test samples: {len(X_test_raw)}")

    # Vectorization: TF-IDF
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        sublinear_tf=True
    )

    X_train = vectorizer.fit_transform(X_train_raw)
    X_test = vectorizer.transform(X_test_raw)

    # 1. Model A: Logistic Regression
    lr_model = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    lr_model.fit(X_train, y_train)
    y_pred_lr = lr_model.predict(X_test)
    acc_lr = accuracy_score(y_test, y_pred_lr)

    # 2. Model B: Multinomial Naive Bayes
    nb_model = MultinomialNB()
    nb_model.fit(X_train, y_train)
    y_pred_nb = nb_model.predict(X_test)
    acc_nb = accuracy_score(y_test, y_pred_nb)

    print(f"\n--- Model Comparison ---")
    print(f"Logistic Regression Accuracy: {acc_lr * 100:.2f}%")
    print(f"Multinomial Naive Bayes Accuracy: {acc_nb * 100:.2f}%")

    # Select Best Model
    if acc_lr >= acc_nb:
        best_model = lr_model
        best_y_pred = y_pred_lr
        best_name = "Logistic Regression"
    else:
        best_model = nb_model
        best_y_pred = y_pred_nb
        best_name = "Multinomial Naive Bayes"

    print(f"\nSelected Best Model: {best_name}")

    # Detailed Metrics
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, best_y_pred, average='weighted')
    cm = confusion_matrix(y_test, best_y_pred, labels=sorted(list(set(labels))))

    print("\n--- Evaluation Metrics ---")
    print(f"Accuracy:  {accuracy_score(y_test, best_y_pred) * 100:.2f}%")
    print(f"Precision: {precision * 100:.2f}%")
    print(f"Recall:    {recall * 100:.2f}%")
    print(f"F1-Score:  {f1 * 100:.2f}%")

    print("\n--- Confusion Matrix ---")
    print(cm)

    # Save Pipeline Bundle (Model + Vectorizer)
    artifact = {
        'vectorizer': vectorizer,
        'model': best_model,
        'labels': sorted(list(set(labels))),
        'model_name': best_name
    }

    joblib.dump(artifact, MODEL_OUTPUT_PATH)

    # Also save copy in backend/ML/saved_model directory for compatibility
    legacy_saved_dir = os.path.join(BASE_DIR, 'saved_model')
    os.makedirs(legacy_saved_dir, exist_ok=True)
    joblib.dump(artifact, os.path.join(legacy_saved_dir, 'domain_classifier.joblib'))

    print(f"\n[SUCCESS] Saved best trained model bundle to: {MODEL_OUTPUT_PATH}")

if __name__ == "__main__":
    train_and_evaluate()
