import os
import json
import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

GEMINI_MODELS = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash"]


class GeminiCoverageValidationError(Exception):
    """Raised when Gemini returns a coverage response that fails strict schema validation."""
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


def build_coverage_prompt(notes_text: str, syllabus_text: str, chapter_name: str = "") -> str:
    chapter_header = f"CHAPTER / SECTION: {chapter_name}\n" if chapter_name else ""
    return f"""You are an Academic Content Evaluator for RecoMind.

Your single task is to evaluate how thoroughly the student's extracted study notes cover the academic content required by the course syllabus.

{chapter_header}REQUIRED ACADEMIC SYLLABUS CONTENT:
{syllabus_text}

ACTUAL EXTRACTED STUDENT NOTES:
{notes_text}

STRICT ACADEMIC EVALUATION RULES:
1. EVALUATE CONTENT, NOT KEYWORDS OR TOPIC NAMES:
   Evaluate whether the specific ACADEMIC CONTENT (definitions, mathematical formulas, scientific explanations, derivation steps) is present in the student's notes. Topic-name presence alone is NOT evidence of coverage. For example, if the syllabus requires definitions, formulas, or derivations, and the student notes merely mention topic titles (e.g., "Capacitance"), award very low coverage percentage (e.g., 5-15%). Higher coverage requires actual explanations, correct formulas, and logical steps.
2. DO NOT USE FALSE METRICS:
   Do NOT base coverage on document length, page count, word count, or filename. Base coverage strictly on academic content overlap.
3. STATUS CATEGORIES:
   - "GOOD": 75% - 100% coverage
   - "NEEDS_IMPROVEMENT": 40% - 74% coverage
   - "WEAK": 0% - 39% coverage
4. BRIEF REASON:
   Provide a concise 1-2 sentence summary explaining what key academic content is covered vs missing.

OUTPUT FORMAT:
Return ONLY a valid, raw JSON object matching this exact schema and NOTHING ELSE:
{{
  "coverage_percentage": <integer between 0 and 100>,
  "status": "GOOD | NEEDS_IMPROVEMENT | WEAK",
  "brief_reason": "<concise 1-2 sentence explanation>"
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
                    max_output_tokens=2048,
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
                    "maxOutputTokens": 2048,
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


def validate_gemini_coverage_response(parsed_data: dict) -> dict:
    """
    Validates Gemini's coverage response strictly:
    - Must be a dict with coverage_percentage, status, and brief_reason.
    - coverage_percentage must be numeric and bounded between 0 and 100.
    - status must be strictly GOOD, NEEDS_IMPROVEMENT, or WEAK.
    - brief_reason must be a non-empty string.
    """
    if not isinstance(parsed_data, dict):
        raise GeminiCoverageValidationError("Gemini output is not a JSON object")

    if "coverage_percentage" not in parsed_data:
        raise GeminiCoverageValidationError("Missing required 'coverage_percentage' field")

    try:
        pct = float(parsed_data["coverage_percentage"])
        pct_int = int(round(pct))
    except (ValueError, TypeError):
        raise GeminiCoverageValidationError("'coverage_percentage' must be a valid number")

    if pct_int < 0 or pct_int > 100:
        raise GeminiCoverageValidationError(f"'coverage_percentage' ({pct_int}) out of bounds [0, 100]")

    status_str = str(parsed_data.get("status", "")).upper()
    if status_str not in ("GOOD", "NEEDS_IMPROVEMENT", "WEAK"):
        # Auto-derive status from percentage if Gemini gave an unexpected status string
        if pct_int >= 75:
            status_str = "GOOD"
        elif pct_int >= 40:
            status_str = "NEEDS_IMPROVEMENT"
        else:
            status_str = "WEAK"

    brief_reason = str(parsed_data.get("brief_reason", "") or "").strip()
    if not brief_reason:
        brief_reason = f"Student notes evaluate to {pct_int}% coverage against the requested syllabus."

    return {
        "coverage_percentage": pct_int,
        "status": status_str,
        "brief_reason": brief_reason
    }


def analyze_notes_coverage_ai(notes_text: str, syllabus_text: str, chapter_name: str = "") -> dict:
    """
    AI-Only Coverage MVP Service (Step 2).
    Evaluates extracted student notes against extracted syllabus content using Gemini 2.5 Flash.
    Returns:
      {
        "coverage_percentage": int,
        "status": "GOOD | NEEDS_IMPROVEMENT | WEAK",
        "brief_reason": str
      }
    """
    if not notes_text or not isinstance(notes_text, str) or not notes_text.strip():
        return {
            "error": "Unable to extract readable text from the uploaded notes. Please upload a readable notes file."
        }

    if not syllabus_text or not isinstance(syllabus_text, str) or not syllabus_text.strip():
        return {
            "error": "Unable to extract readable text from the uploaded syllabus. Please select or upload a valid syllabus."
        }

    api_key = get_gemini_api_key()
    if not api_key:
        return {
            "error": "AI analysis is currently unavailable because the Gemini API key is not configured."
        }

    prompt = build_coverage_prompt(notes_text.strip(), syllabus_text.strip(), chapter_name.strip())

    # Attempt 1
    logger.info("Executing Gemini AI Coverage Analysis (Attempt 1)...")
    raw_res = _call_gemini_raw(prompt, api_key)
    parsed = clean_and_parse_json(raw_res)

    first_err_msg = ""
    try:
        return validate_gemini_coverage_response(parsed)
    except GeminiCoverageValidationError as val_err:
        first_err_msg = str(val_err)
        logger.warning(f"Gemini Coverage Attempt 1 failed validation: {val_err}. Executing safe retry...")

    # Attempt 2 (Retry with error feedback)
    retry_prompt = prompt + f"\n\nCRITICAL FIX REQUIRED: Your previous response failed validation with error: '{first_err_msg}'. Return ONLY raw valid JSON with coverage_percentage (0-100), status (GOOD|NEEDS_IMPROVEMENT|WEAK), and brief_reason."
    raw_res_2 = _call_gemini_raw(retry_prompt, api_key)
    parsed_2 = clean_and_parse_json(raw_res_2)

    try:
        return validate_gemini_coverage_response(parsed_2)
    except GeminiCoverageValidationError as final_err:
        logger.error(f"Gemini Coverage Attempt 2 failed validation: {final_err}.")
        return {
            "error": f"AI analysis failed to produce valid coverage data after retry: {final_err}"
        }
