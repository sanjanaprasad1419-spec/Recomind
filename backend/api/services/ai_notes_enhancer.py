import os
import re
import json
import logging
import requests

logger = logging.getLogger(__name__)

# Environment configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("AI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
AI_MODEL = os.environ.get("AI_MODEL", "gemini-1.5-flash")


def call_gemini_api(prompt: str, api_key: str) -> str:
    """
    Calls Google Gemini REST API using requests.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 2048
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            res_json = response.json()
            candidates = res_json.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        else:
            logger.warning(f"Gemini API returned HTTP {response.status_code}: {response.text}")
    except Exception as e:
        logger.warning(f"Gemini API request failed: {e}")
    return ""


def call_openai_api(prompt: str, api_key: str) -> str:
    """
    Calls OpenAI Chat Completions REST API using requests.
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are RecoMind, an intelligent educational AI assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            res_json = response.json()
            choices = res_json.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
    except Exception as e:
        logger.warning(f"OpenAI API request failed: {e}")
    return ""


def generate_local_fallback_enhancement(topic: str, status: str, domain: str, education_level: str = "") -> dict:
    """
    Generates high-quality, subject-grounded educational study cards locally when external AI API is unavailable.
    Includes rich physics and domain-specific topic templates.
    """
    t_clean = topic.strip()
    t_lower = t_clean.lower()

    # Special Topic Template: Long Straight Charged Wire
    if 'wire' in t_lower or 'line charge' in t_lower or 'straight' in t_lower:
        return {
            "topic": t_clean,
            "status": status,
            "enhancement": {
                "definition": "The electric field produced by an infinitely long straight wire carrying uniform linear charge density λ at a radial distance r.",
                "concept": "Applying Gauss's Law to a cylindrical Gaussian surface coaxial with the line charge demonstrates that electric field vectors point purely radially outwards.",
                "formulas": ["E = λ / (2πε₀r)", "Φ = E · (2πrL) = Q_enclosed / ε₀"],
                "derivation": [
                    "1. Construct a cylindrical Gaussian surface of radius r and length L concentric with the wire.",
                    "2. Total charge enclosed inside the surface: Q_enclosed = λ · L.",
                    "3. Electric flux through flat circular end-caps is zero because E is parallel to surface (E · dA = 0).",
                    "4. Electric flux through curved surface: Φ = E · (2πrL).",
                    "5. Apply Gauss's Law: E · (2πrL) = (λL) / ε₀  =>  E = λ / (2πε₀r)."
                ],
                "important_points": [
                    "Field magnitude E is inversely proportional to distance r (E ∝ 1/r).",
                    "Direction is radially outward if λ > 0, and radially inward if λ < 0.",
                    "Flux through end caps of the cylinder is 0."
                ],
                "example": "For a long wire with linear charge density λ = 2 × 10⁻⁶ C/m at distance r = 0.1 m, E = (2 × 10⁻⁶) / (2 × π × 8.854×10⁻¹² × 0.1) ≈ 3.6 × 10⁵ N/C.",
                "diagram_guidance": "Draw a straight vertical line for the charged wire (+ + +). Surround it with a coaxial cylinder of radius r and length L. Show radial arrows E pointing outward perpendicularly from the curved surface.",
                "exam_tip": "In exams, always state why flux through end-caps is zero before equating total flux to Q_enclosed / ε₀.",
                "quick_revision": "Formula: E = λ / (2πε₀r). Field drops off as 1/r."
            }
        }

    # Special Topic Template: Spherical Shell
    if 'shell' in t_lower or 'sphere' in t_lower:
        return {
            "topic": t_clean,
            "status": status,
            "enhancement": {
                "definition": "The electric field produced by a thin, uniformly charged spherical shell of radius R and total charge Q.",
                "concept": "Using spherical Gaussian surfaces concentric with the shell to determine field intensity outside, on the surface, and inside the shell.",
                "formulas": [
                    "Outside (r > R): E = (1 / 4πε₀) · (Q / r²)",
                    "On Surface (r = R): E = (1 / 4πε₀) · (Q / R²)",
                    "Inside (r < R): E = 0"
                ],
                "derivation": [
                    "1. Outside (r > R): Choose a concentric spherical Gaussian surface of radius r. Q_enclosed = Q. Φ = E(4πr²) = Q/ε₀ => E = Q / (4πε₀r²).",
                    "2. Inside (r < R): Choose a concentric spherical Gaussian surface of radius r inside the shell. Since all charge resides on the outer surface, Q_enclosed = 0. Φ = E(4πr²) = 0 => E = 0."
                ],
                "important_points": [
                    "Inside a charged thin spherical shell, the electric field is strictly ZERO (E = 0).",
                    "Outside the shell, the field behaves as if the entire charge Q were concentrated at the center point.",
                    "Provides the physical basis for Electrostatic Shielding."
                ],
                "example": "A spherical shell of radius R = 0.2 m carries charge Q = 4 μC. At r = 0.1 m (inside), E = 0. At r = 0.4 m (outside), E = 9×10⁹ × 4×10⁻⁶ / (0.4)² = 2.25 × 10⁵ N/C.",
                "diagram_guidance": "Draw a thin sphere of radius R with charge +Q distributed on its surface. Draw a smaller concentric dotted circle inside (r < R) showing E = 0, and a larger dotted circle outside (r > R) showing radial field arrows.",
                "exam_tip": "Remember E = 0 inside the shell. On a graph of E vs r, E is 0 from r=0 to r=R, jumps to max at r=R, and decays as 1/r² for r > R.",
                "quick_revision": "Inside: E = 0 | Outside: E ∝ 1/r²."
            }
        }

    # Special Topic Template: Electric Field / Field Lines
    if 'electric field' in t_lower:
        return {
            "topic": t_clean,
            "status": status,
            "enhancement": {
                "definition": "Electric field is defined as the force experienced per unit positive test charge placed at a given point in space: E = F / q₀.",
                "concept": "An electric field represents the force field surrounding an electric charge, where another charge experiences an electrostatic force.",
                "formulas": [
                    "E = F / q₀",
                    "Due to point charge Q: E = (1 / 4πε₀) · (Q / r²)"
                ],
                "derivation": [
                    "1. Place test charge q₀ at distance r from charge Q.",
                    "2. According to Coulomb's Law, force F = (1 / 4πε₀) · (Q q₀ / r²).",
                    "3. By definition, E = F / q₀ = (1 / 4πε₀) · (Q / r²)."
                ],
                "important_points": [
                    "Electric field is a vector quantity. Direction is outward from positive charge, inward toward negative charge.",
                    "SI unit is Newton per Coulomb (N/C) or Volt per meter (V/m).",
                    "Electric field lines start at positive charges and end at negative charges; they never intersect."
                ],
                "example": "Find E at 0.3 m from a point charge Q = 3 nC: E = 9×10⁹ × 3×10⁻⁹ / (0.3)² = 300 N/C.",
                "diagram_guidance": "Draw radial outward lines for a positive charge +Q and radial inward lines for a negative charge -Q.",
                "exam_tip": "Never draw intersecting electric field lines in exam diagrams; state that if they intersected, there would be two directions of force at one point, which is impossible.",
                "quick_revision": "E = F/q = kQ/r². Vector quantity. SI unit N/C."
            }
        }

    # General Fallback Template
    return {
        "topic": t_clean,
        "status": status,
        "enhancement": {
            "definition": f"{t_clean} is a core syllabus topic in {domain}.",
            "concept": f"Establishes fundamental principles, mathematical relationships, and analytical formulations required for {t_clean}.",
            "formulas": [f"Standard equation for {t_clean}"],
            "derivation": [
                f"1. State basic definitions and boundary conditions for {t_clean}.",
                f"2. Apply fundamental governing equations.",
                f"3. Simplify to obtain the final relation."
            ],
            "important_points": [
                f"Core analytical principles for {t_clean}.",
                "State SI units, vector directions, or legal/clinical elements clearly.",
                "Identify boundary conditions and physical limitations."
            ],
            "example": f"Standard exam problem involving {t_clean}.",
            "diagram_guidance": f"Draw a clean labeled schematic showing setup for {t_clean}.",
            "exam_tip": f"State primary definitions before writing mathematical derivations for {t_clean}.",
            "quick_revision": f"Review key formulas and definitions for {t_clean}."
        }
    }


def generate_improved_notes_draft(original_notes: str, syllabus_title: str, chapter_title: str, enhancements: list) -> str:
    """
    Generates a structured, beautifully formatted study note draft combining original notes with AI enhancements.
    """
    lines = [
        f"# Refined & Enhanced Study Notes",
        f"**Syllabus:** {syllabus_title}",
        f"**Chapter:** {chapter_title}",
        "",
        "---",
        "",
        "## 1. Original Student Notes",
        original_notes.strip(),
        "",
        "---",
        "",
        "## 2. Topic-by-Topic Enhancements & Complete Study Content",
        ""
    ]

    for item in enhancements:
        topic = item.get("topic", "Syllabus Topic")
        status = item.get("status", "MISSING")
        enh = item.get("enhancement", {})

        lines.append(f"### {topic} [{status}]")
        
        if enh.get("definition"):
            lines.append(f"**Definition:** {enh['definition']}")
        if enh.get("concept"):
            lines.append(f"\n**Core Concept:** {enh['concept']}")
        if enh.get("formulas"):
            lines.append("\n**Key Formulas:**")
            for f in enh["formulas"]:
                lines.append(f"- `{f}`")
        if enh.get("derivation"):
            lines.append("\n**Step-by-Step Derivation:**")
            for step in enh["derivation"]:
                lines.append(f"  {step}")
        if enh.get("important_points"):
            lines.append("\n**Important Points:**")
            for pt in enh["important_points"]:
                lines.append(f"- {pt}")
        if enh.get("example"):
            lines.append(f"\n**Worked Example:** {enh['example']}")
        if enh.get("diagram_guidance"):
            lines.append(f"\n**Diagram Guidance:** {enh['diagram_guidance']}")
        if enh.get("exam_tip"):
            lines.append(f"\n**Exam Tip:** {enh['exam_tip']}")
        if enh.get("quick_revision"):
            lines.append(f"\n**Quick Revision:** {enh['quick_revision']}")
        lines.append("")

    lines.extend([
        "---",
        "## 3. Quick Revision Checklist",
        "- Review all key formulas and boundary conditions.",
        "- Draw and label all recommended diagrams.",
        "- Solve 3 past-year exam questions for each missing topic."
    ])

    return "\n".join(lines)


def enhance_notes_with_ai(
    note_text: str,
    syllabus_title: str,
    chapter_title: str,
    chapter_topics: list,
    ml_results: dict,
    education_level: str = "Class 12",
    domain: str = "Science & Technology"
) -> dict:
    """
    Master AI Enhancement Service operating AFTER ML analysis.
    Generates structured educational study cards for missing/partial topics.
    """
    topics_covered = ml_results.get("topics", {}).get("covered", [])
    topics_partial = ml_results.get("topics", {}).get("partially_covered", [])
    topics_missing = ml_results.get("topics", {}).get("missing", [])

    enhancements = []

    ai_raw_text = ""
    if GEMINI_API_KEY:
        logger.info("Calling Gemini API for grounded notes enhancement...")
        prompt = f"""
You are RecoMind AI, a grounded educational assistant.
Generate structured educational study material for missing and weak syllabus topics.

CONTEXT:
- Syllabus: {syllabus_title}
- Chapter: {chapter_title}
- Education Level: {education_level}
- Domain: {domain}
- Student Notes: {note_text[:1000]}

ML COVERAGE RESULTS:
- Missing Topics: {topics_missing}
- Partially Covered Topics: {topics_partial}
- Well-Covered Topics: {topics_covered}

TASK:
For each MISSING or PARTIALLY COVERED topic, provide:
1. Definition
2. Concept
3. Formulas
4. Derivation steps
5. Important Points
6. Example
7. Diagram Guidance
8. Exam Tip
9. Quick Revision

Format response as JSON list under key "enhancements".
"""
        ai_raw_text = call_gemini_api(prompt, GEMINI_API_KEY)

    elif OPENAI_API_KEY:
        logger.info("Calling OpenAI API for grounded notes enhancement...")
        prompt = f"""
Syllabus: {syllabus_title} | Chapter: {chapter_title} | Level: {education_level} | Domain: {domain}
Missing: {topics_missing} | Partial: {topics_partial} | Covered: {topics_covered}
Provide JSON object containing key 'enhancements' with educational study cards.
"""
        ai_raw_text = call_openai_api(prompt, OPENAI_API_KEY)

    parsed_ai_json = None
    if ai_raw_text:
        try:
            json_match = re.search(r'\{.*\}', ai_raw_text, re.DOTALL)
            if json_match:
                parsed_ai_json = json.loads(json_match.group(0))
        except Exception as e:
            logger.warning(f"Could not parse AI JSON output: {e}")

    if parsed_ai_json and "enhancements" in parsed_ai_json and isinstance(parsed_ai_json["enhancements"], list):
        enhancements = parsed_ai_json["enhancements"]
    else:
        # Local grounded educational cards for all weak/missing topics
        for t in topics_missing:
            enhancements.append(generate_local_fallback_enhancement(t, "MISSING", domain, education_level))
        for t in topics_partial:
            enhancements.append(generate_local_fallback_enhancement(t, "PARTIALLY_COVERED", domain, education_level))
        for t in topics_covered[:3]:
            enhancements.append(generate_local_fallback_enhancement(t, "COVERED", domain, education_level))

    improved_notes_draft = generate_improved_notes_draft(note_text, syllabus_title, chapter_title, enhancements)

    return {
        "status": "success",
        "syllabus_title": syllabus_title,
        "chapter_title": chapter_title,
        "education_level": education_level,
        "domain": domain,
        "enhancements": enhancements,
        "improved_notes_draft": improved_notes_draft
    }
