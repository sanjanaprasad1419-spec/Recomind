import os
import re
import logging
import joblib
from django.conf import settings

logger = logging.getLogger(__name__)

# Global singleton cache for trained model artifact
_MODEL_CACHE = None

DOMAIN_KEYWORD_MAP = {
    "Humanities & Social Sciences": [
        r'\bgeography\b', r'\bplate tectonics\b', r'\bweathering\b', r'\berosion\b', 
        r'\bhistory\b', r'\bdemocracy\b', r'\belections\b', r'\bcivilisation\b', 
        r'\bsociety\b', r'\bpolity\b', r'\bconstitution\b', r'\bculture\b'
    ],
    "Business, Commerce & Economics": [
        r'\beconomics\b', r'\bmarket\b', r'\bdemand and supply\b', r'\binflation\b', 
        r'\bbudgeting\b', r'\bfinance\b', r'\baccounting\b', r'\bcommerce\b'
    ],
    "STEM: Physical Sciences & Mathematics": [
        r'\belectric field\b', r'\bcoulomb\b', r'\bgauss\b', r'\bcapacitance\b', 
        r'\bvelocity\b', r'\bacceleration\b', r'\bcalculus\b', r'\bphysics\b'
    ],
    "Medical & Life Sciences": [
        r'\banatomy\b', r'\bbiology\b', r'\bcell\b', r'\bpathology\b', r'\bpharmacology\b', r'\bhealth\b'
    ]
}


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
        logger.warning(f"Domain classifier model file not found at {primary_path} or {fallback_path}")
        return None

    try:
        logger.info(f"Loading domain prediction model artifact from: {model_path}")
        _MODEL_CACHE = joblib.load(model_path)
        return _MODEL_CACHE
    except Exception as e:
        logger.warning(f"Error loading domain classifier joblib model: {e}")
        return None


def predict_domain(text: str) -> dict:
    """
    Predicts broad educational domain for a given text string.
    Combines TF-IDF + Logistic Regression model with domain keyword hints for robust classification.
    Returns 'General / Mixed Academic Domain' when confidence is low (< 0.35).
    """
    if not text or not isinstance(text, str) or not text.strip():
        return {"predicted_domain": "General / Mixed Academic Domain", "confidence": 0.50}

    cleaned_text = text.strip()
    cleaned_lower = cleaned_text.lower()

    predicted_domain = "General / Mixed Academic Domain"
    confidence = 0.0

    artifact = None
    try:
        artifact = load_domain_model()
    except Exception as e:
        logger.warning(f"Domain model load skipped: {e}")

    if artifact:
        try:
            vectorizer = artifact['vectorizer']
            model = artifact['model']

            X_input = vectorizer.transform([cleaned_text])
            raw_pred = str(model.predict(X_input)[0])

            if hasattr(model, 'predict_proba'):
                probs = model.predict_proba(X_input)[0]
                classes_list = model.classes_.tolist()
                if raw_pred in classes_list:
                    max_idx = classes_list.index(raw_pred)
                    confidence = round(float(probs[max_idx]), 4)
            
            if confidence >= 0.35:
                predicted_domain = raw_pred
        except Exception as err:
            logger.warning(f"TF-IDF domain prediction fallback: {err}")

    # Apply domain keyword heuristics if confidence is low or default returned
    if confidence < 0.35:
        best_match_domain = None
        max_keyword_hits = 0

        for domain_name, patterns in DOMAIN_KEYWORD_MAP.items():
            hits = sum(1 for pat in patterns if re.search(pat, cleaned_lower))
            if hits > max_keyword_hits:
                max_keyword_hits = hits
                best_match_domain = domain_name

        if max_keyword_hits >= 2 and best_match_domain:
            predicted_domain = best_match_domain
            confidence = min(0.65, 0.40 + (max_keyword_hits * 0.10))
        elif confidence < 0.25:
            predicted_domain = "General / Mixed Academic Domain"
            confidence = 0.50

    return {
        "predicted_domain": str(predicted_domain),
        "confidence": confidence
    }
