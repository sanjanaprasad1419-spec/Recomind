import os
import json
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

GEMINI_MODELS = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash"]
FORBIDDEN_KEYS = {
    "coverage_percentage",
    "overall_score",
    "numeric_score",
    "final_percentage",
    "confidence_score",
    "overall_status",
    "good",
    "complete"
}


class GeminiAuditValidationError(Exception):
    """Raised when Gemini returns a response that fails strict schema/business validation."""
    pass


def get_gemini_api_key() -> str:
    """Retrieve Gemini API key from environment or backend/.env file."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("AI_API_KEY") or os.environ.get("GEMINI_KEY")
    if key:
        return key

    # Direct fallback to backend/.env
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        if k.strip() in ("GEMINI_API_KEY", "AI_API_KEY", "GEMINI_KEY"):
                            val = v.strip().strip('"').strip("'")
                            if val:
                                os.environ[k.strip()] = val
                                return val
        except Exception:
            pass
    return ""


def build_audit_prompt(chapter_name: str, reference_components: list, student_notes: str) -> str:
    comp_json = json.dumps(reference_components, indent=2)
    return f"""You are a strict, reliable Academic Content Auditor.

Your single task is to evaluate whether each expected academic component of the chapter is actually demonstrated in the student's extracted notes.

CHAPTER:
{chapter_name}

REFERENCE ACADEMIC COMPONENTS (GROUND TRUTH):
{comp_json}

STUDENT'S EXTRACTED NOTES:
{student_notes}

STRICT EVALUATION RULES:
1. CONTENT EVALUATION ONLY: Evaluate whether the specific ACADEMIC CONTENT (concept, definition, formula, derivation steps) is present in the student's notes. Evaluate CONTENT, not keywords.
2. ACADEMIC EVIDENCE RULE: Topic-name presence is NOT evidence. For example, if student notes mention "Capacitance", but reference component is "Energy stored in a capacitor is U = 1/2 CV²", the status must be "MISSING". Do NOT mark it FULL or PARTIAL merely because both concepts are semantically related.
3. FORMULA RULE: If the reference component requires a formula (e.g. "Energy stored in capacitor: U = 1/2 CV²"), the formula or mathematically equivalent expression must actually be present in the student notes. If student notes say "Capacitor stores energy" without the formula, status is "PARTIAL". If student notes contain "U = 1/2 CV²", status is "FULL".
4. DERIVATION RULE: A final formula alone does NOT demonstrate a derivation. For example, if reference is "Derivation of capacitance of parallel plate capacitor" and student notes say "C = ε₀A/d", status is "PARTIAL". If student notes contain the logical derivation steps and final result, status is "FULL".
5. EVIDENCE RULE: For every FULL or PARTIAL result, `evidence` MUST be copied or directly paraphrased from actual student notes. Do NOT invent evidence. For MISSING status, `evidence` MUST be an empty string "". Gemini must never claim the student wrote something that is not present.
6. REFERENCE COMPONENT RULE: You MUST evaluate EVERY supplied reference component by its exact `id`. Do NOT remove components, invent components, merge components, or add unrelated components.
7. NO HARD-CODED ACADEMIC KNOWLEDGE: Work generically from the supplied reference components.
8. ABSOLUTELY FORBIDDEN: Do NOT calculate or include coverage_percentage, overall_score, numeric_score, final_percentage, confidence_score, or any overall judgements like "student notes are good" or "student notes are complete".

OUTPUT FORMAT:
Return ONLY a raw, valid JSON object matching this exact schema and NOTHING ELSE:
{{
  "components": [
    {{
      "component_id": "<exact id matching reference component>",
      "status": "FULL | PARTIAL | MISSING",
      "evidence": "<copied or paraphrased snippet from student notes for FULL/PARTIAL, empty string for MISSING>",
      "missing_aspects": [
        "<specific missing detail or equation, or empty array if FULL>"
      ]
    }}
  ]
}}
"""


def _call_gemini_raw(prompt: str, api_key: str) -> str:
    """
    Call Gemini using google.genai SDK if available, trying available models (gemini-3.6-flash, gemini-2.5-flash, gemini-1.5-flash).
    """
    for model_name in GEMINI_MODELS:
        # 1. Official SDK
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=30_000))
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                    max_output_tokens=4096,
                ),
            )
            if response and response.text:
                return response.text
        except Exception as exc:
            logger.warning(f"google.genai SDK ({model_name}) call failed/skipped: {exc}. Trying fallback...")

        # 2. REST API Fallback
        try:
            import requests
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 4096,
                    "responseMimeType": "application/json"
                }
            }
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                res_json = res.json()
                candidates = res_json.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            else:
                logger.warning(f"Gemini REST API ({model_name}) HTTP {res.status_code}: {res.text[:200]}")
        except Exception as r_exc:
            logger.warning(f"Gemini REST API ({model_name}) error: {r_exc}")

    return ""


def clean_and_parse_json(text: str) -> dict:
    if not text:
        return {}
    cleaned = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r'\s*```$', '', cleaned.strip(), flags=re.MULTILINE)
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    try:
        return json.loads(cleaned)
    except Exception as e:
        logger.warning(f"Failed to parse JSON text: {e}")
        return {}


def validate_gemini_audit_response(parsed_data: dict, reference_components: list) -> dict:
    """
    Validates Gemini's response strictly:
    - Must be a dict with a 'components' list.
    - Must NOT contain any forbidden fields (coverage_percentage, overall_score, etc.).
    - Must contain an assessment for EVERY reference component id in reference_components.
    - status must be strictly FULL, PARTIAL, or MISSING.
    - evidence must be present for FULL/PARTIAL, empty for MISSING.
    - missing_aspects must be a list.
    Returns cleaned/validated response dict.
    Raises GeminiAuditValidationError on failure.
    """
    if not isinstance(parsed_data, dict):
        raise GeminiAuditValidationError("Gemini output is not a JSON object")

    # Check for forbidden fields anywhere in top-level JSON
    for forbidden in FORBIDDEN_KEYS:
        if forbidden in parsed_data:
            raise GeminiAuditValidationError(f"Forbidden field '{forbidden}' present in Gemini response")

    if "components" not in parsed_data or not isinstance(parsed_data["components"], list):
        raise GeminiAuditValidationError("Gemini response missing required 'components' list")

    ref_ids = [str(c["id"]) for c in reference_components]
    returned_components = parsed_data["components"]

    # Map component_id to entry
    comp_map = {}
    for comp in returned_components:
        if not isinstance(comp, dict):
            raise GeminiAuditValidationError("Component assessment element is not an object")
        c_id = str(comp.get("component_id", ""))
        if not c_id:
            raise GeminiAuditValidationError("Component assessment missing 'component_id'")
        comp_map[c_id] = comp

    # Verify every reference component has exactly one assessment
    validated_components = []
    for ref_comp in reference_components:
        ref_id = str(ref_comp["id"])
        if ref_id not in comp_map:
            raise GeminiAuditValidationError(f"Missing assessment for reference component_id '{ref_id}'")

        comp_eval = comp_map[ref_id]
        status = str(comp_eval.get("status", "")).upper()
        if status not in ("FULL", "PARTIAL", "MISSING"):
            raise GeminiAuditValidationError(f"Invalid status '{status}' for component_id '{ref_id}'")

        evidence = str(comp_eval.get("evidence", "") or "")
        missing_aspects = comp_eval.get("missing_aspects", [])
        if not isinstance(missing_aspects, list):
            missing_aspects = [str(missing_aspects)]

        if status in ("FULL", "PARTIAL") and not evidence.strip():
            raise GeminiAuditValidationError(f"Status '{status}' for component_id '{ref_id}' requires non-empty evidence")

        if status == "MISSING":
            evidence = ""  # Rule: for MISSING evidence should be empty string

        validated_components.append({
            "component_id": ref_id,
            "status": status,
            "evidence": evidence.strip(),
            "missing_aspects": [str(a) for a in missing_aspects]
        })

    return {
        "components": validated_components
    }


def audit_student_notes_with_gemini(
    chapter_name: str = "",
    reference_components: list = None,
    student_notes: str = "",
    syllabus_title: str = "",
    chapter_title: str = "",
) -> dict:
    """
    Gemini 2.5 Flash Academic Auditor (Step 1).
    Evaluates reference academic components against student notes.
    Returns STRICT JSON containing only component-level assessments.
    """
    effective_chapter = chapter_name or chapter_title or "Selected Chapter"
    if reference_components is None:
        reference_components = []

    api_key = get_gemini_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Cannot perform Gemini academic audit.")

    prompt = build_audit_prompt(effective_chapter, reference_components, student_notes)

    # 1st Attempt
    logger.info("Executing Gemini Academic Auditor (Attempt 1)...")
    raw_response = _call_gemini_raw(prompt, api_key)
    parsed = clean_and_parse_json(raw_response)

    first_err_msg = ""
    try:
        validated = validate_gemini_audit_response(parsed, reference_components)
        return validated
    except GeminiAuditValidationError as val_err:
        first_err_msg = str(val_err)
        logger.warning(f"Gemini Audit Attempt 1 validation failed: {val_err}. Executing safe retry...")

    # 2nd Attempt (Retry with error feedback)
    retry_prompt = prompt + f"\n\nCRITICAL FIX REQUIRED: Your previous output failed validation with error: '{first_err_msg}'. You MUST follow the JSON schema strictly and evaluate ALL reference components by their exact component_id."
    raw_response_2 = _call_gemini_raw(retry_prompt, api_key)
    parsed_2 = clean_and_parse_json(raw_response_2)

    try:
        validated_2 = validate_gemini_audit_response(parsed_2, reference_components)
        return validated_2
    except GeminiAuditValidationError as final_err:
        logger.error(f"Gemini Audit Attempt 2 validation failed: {final_err}.")
        raise RuntimeError(f"Gemini Academic Auditor failed to return valid JSON after retry: {final_err}")


def compute_deterministic_coverage(components_assessments: list, total_components_count: int) -> dict:
    """Legacy helper function for test compatibility."""
    full_count = 0
    partial_count = 0
    missing_count = 0
    total_score = 0.0

    for item in components_assessments:
        status = item.get("status", "MISSING").upper()
        if status == "FULL":
            full_count += 1
            total_score += 1.0
        elif status == "PARTIAL":
            partial_count += 1
            total_score += 0.5
        else:
            missing_count += 1
            total_score += 0.0

    total_units = max(total_components_count, len(components_assessments), 1)
    coverage_percentage = round((total_score / total_units) * 100, 1)

    if coverage_percentage >= 75.0:
        overall_status = "GOOD"
    elif coverage_percentage >= 40.0:
        overall_status = "NEEDS_IMPROVEMENT"
    else:
        overall_status = "WEAK"

    return {
        "coverage_percentage": coverage_percentage,
        "overall_status": overall_status,
        "full_count": full_count,
        "partial_count": partial_count,
        "missing_count": missing_count,
        "total_units": total_units
    }


def generate_local_component_assessments(reference_components: list, student_notes: str) -> list:
    """Legacy helper function for test compatibility."""
    notes_clean = student_notes.lower()
    assessments = []

    for comp in reference_components:
        c_id = comp["id"]
        c_text = comp["component"].lower()
        c_type = comp.get("type", "concept")

        words = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', c_text) if w not in ['topic', 'chapter', 'definition', 'formula']]
        matched_words = [w for w in words if w in notes_clean]

        if len(words) > 0 and len(matched_words) == len(words):
            assessments.append({
                "component_id": c_id,
                "status": "FULL",
                "evidence": f"Found matching terms ({', '.join(matched_words[:3])})",
                "missing_aspects": []
            })
        elif len(matched_words) >= 1:
            assessments.append({
                "component_id": c_id,
                "status": "PARTIAL",
                "evidence": f"Mentions {matched_words[0]}",
                "missing_aspects": [f"Missing complete {c_type} details"]
            })
        else:
            assessments.append({
                "component_id": c_id,
                "status": "MISSING",
                "evidence": "",
                "missing_aspects": [c_text]
            })

    return assessments
