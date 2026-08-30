import os
import sys
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'saved_models', 'domain_classifier.joblib')

def predict(text_input):
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")

    artifact = joblib.load(MODEL_PATH)
    vectorizer = artifact['vectorizer']
    model = artifact['model']

    # Vectorize input text
    X_input = vectorizer.transform([text_input])

    # Predict class
    predicted_domain = model.predict(X_input)[0]

    # Predict confidence score
    confidence = None
    if hasattr(model, 'predict_proba'):
        probs = model.predict_proba(X_input)[0]
        max_idx = model.classes_.tolist().index(predicted_domain)
        confidence = float(probs[max_idx])

    return {
        "text": text_input,
        "predicted_domain": predicted_domain,
        "confidence": confidence,
        "model_used": artifact.get('model_name', 'Logistic Regression')
    }

if __name__ == "__main__":
    test_samples = [
        "Binary search trees and hash tables provide log time complexity for search operations.",
        "Human anatomy details upper extremity vascular supply and skeletal muscular origins.",
        "Financial accounting principles record double entry bookkeeping, balance sheets, and cash flow statements.",
        "Constitutional law interprets fundamental rights guarantees and judicial review doctrines.",
        "Elementary science explains plant photosynthesis needing sunlight water, living nonliving things.",
        "Quantitative aptitude calculates speed distance time, work ratios, and interest rates."
    ]

    print("[INFO] Testing RecoMind Domain Classifier Prediction Pipeline:\n")
    for sample in test_samples:
        result = predict(sample)
        conf_percent = f"{result['confidence'] * 100:.1f}%" if result['confidence'] is not None else "N/A"
        print(f"Input Text : \"{result['text']}\"")
        print(f"Predicted  : {result['predicted_domain']} (Confidence: {conf_percent})")
        print("-" * 75)
