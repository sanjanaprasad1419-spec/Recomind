import os
import logging
import joblib
from django.conf import settings

logger = logging.getLogger(__name__)

# Global singleton cache for trained model artifact
_MODEL_CACHE = None

def load_domain_model():
    """
    Loads trained ML model artifact once and caches it in memory.
    """
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    primary_path = os.path.join(settings.BASE_DIR, 'ML', 'saved_models', 'domain_classifier.joblib')
    fallback_path = os.path.join(settings.BASE_DIR, 'ML', 'saved_model', 'domain_classifier.joblib')

    model_path = None
    if os.path.exists(primary_path):
        model_path = primary_path
    elif os.path.exists(fallback_path):
        model_path = fallback_path

    if not model_path:
        logger.error(f"Domain classifier model file not found at {primary_path} or {fallback_path}")
        raise FileNotFoundError(f"Trained domain classifier model not found. Ensure training has run.")

    try:
        logger.info(f"Loading domain prediction model artifact from: {model_path}")
        _MODEL_CACHE = joblib.load(model_path)
        return _MODEL_CACHE
    except Exception as e:
        logger.error(f"Error loading domain classifier joblib model: {e}")
        raise RuntimeError(f"Failed to load domain prediction model: {e}")


def predict_domain(text: str) -> dict:
    """
    Predicts broad educational domain for a given text string using saved TF-IDF + Logistic Regression model.

    Args:
        text (str): Educational note text content.

    Returns:
        dict: {"predicted_domain": str, "confidence": float}
    """
    if not text or not isinstance(text, str) or not text.strip():
        raise ValueError("Text string is required and cannot be empty.")

    artifact = load_domain_model()
    vectorizer = artifact['vectorizer']
    model = artifact['model']

    cleaned_text = text.strip()

    # Perform TF-IDF transformation (using pre-fitted vectorizer)
    X_input = vectorizer.transform([cleaned_text])

    # Predict domain label
    predicted_domain = model.predict(X_input)[0]

    # Calculate prediction confidence score
    confidence = 0.0
    if hasattr(model, 'predict_proba'):
        probs = model.predict_proba(X_input)[0]
        classes_list = model.classes_.tolist()
        if predicted_domain in classes_list:
            max_idx = classes_list.index(predicted_domain)
            confidence = round(float(probs[max_idx]), 4)

    return {
        "predicted_domain": predicted_domain,
        "confidence": confidence
    }
