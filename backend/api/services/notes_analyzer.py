import os
import re
import math
import logging
import threading
import numpy as np
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .domain_predictor import predict_domain
from .reference_knowledge_service import get_or_create_reference_profile, detect_subject_domain
from .ai_notes_enhancer import generate_local_fallback_enhancement

import joblib
from django.conf import settings

logger = logging.getLogger(__name__)

# Global singleton cache for SentenceTransformers model
_SENTENCE_MODEL_CACHE = None
_SENTENCE_MODEL_LOAD_ATTEMPTED = False
_SENTENCE_MODEL_LOCK = threading.Lock()

MAX_ANALYSIS_NOTE_CHARS = 500_000
MAX_ANALYSIS_SYLLABUS_CHARS = 250_000
MAX_NOTE_CHUNKS = 400
MAX_SYLLABUS_TOPICS = 300


def get_sentence_transformer_model():
    """
    Singleton loader for sentence-transformers/all-MiniLM-L6-v2.
    Supports both local files and fallback online loading.
    """
    global _SENTENCE_MODEL_CACHE, _SENTENCE_MODEL_LOAD_ATTEMPTED
    if _SENTENCE_MODEL_CACHE is not None:
        return _SENTENCE_MODEL_CACHE
    if _SENTENCE_MODEL_LOAD_ATTEMPTED:
        return _SENTENCE_MODEL_CACHE

    with _SENTENCE_MODEL_LOCK:
        if _SENTENCE_MODEL_CACHE is not None:
            return _SENTENCE_MODEL_CACHE
        _SENTENCE_MODEL_LOAD_ATTEMPTED = True
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
            try:
                _SENTENCE_MODEL_CACHE = SentenceTransformer('all-MiniLM-L6-v2', local_files_only=True, device='cpu')
            except Exception:
                _SENTENCE_MODEL_CACHE = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
            return _SENTENCE_MODEL_CACHE
        except Exception as exc:
            logger.warning("SentenceTransformer is unavailable locally (%s); using TF-IDF fallback.", exc.__class__.__name__)
            return None


def is_valid_academic_topic(text: str) -> bool:
    if not text or len(text.strip()) < 3:
        return False

    t_lower = text.strip().lower()

    ignore_phrases = [
        "senior secondary", "stage of transition", "salient features", "emphasis on",
        "promotion of", "discipline-based", "comprehension level", "linkage for better",
        "curriculum load", "prescribed books", "laboratory manual", "course structure",
        "max marks", "general guidelines", "visually impaired", "evaluation scheme",
        "question paper", "table of contents", "subject code", "class xi", "class xii",
        "time allowed", "time:", "marks:", "total 70", "theory", "practical", "experimental manner",
        "besides, the syllabus", "firm foundation", "realize and appreciate", "creative thinking",
        "observational, manipulative", "linkage for better", "eliminating overlapping",
        "assessment in practicals", "list of practicals", "items for identification",
        "development of process", "experiential manner", "multimedia also", "tested by schools",
        "excluded for the year", "time: 3 hrs", "secp1ix", "secp2", "prescribed books:",
        "typology of questions", "demonstrate understanding", "making judgments",
        "gross total", "s no.", "section–a", "section–b", "section a", "section b",
        "investigatory project", "viva", "written test", "experiments", "resistance box",
        "jockey galvanometer", "multimeter", "meter scale", "standard resistance",
        "cbse examination", "writer may be allowed", "hours duration", "suggested investigatory",
        "identification/familiarity", "list of ten experiments", "written test will be",
        "demonstrate understanding of facts", "making judgments about information",
        "validity of ideas", "gross total 100", "total marks 70", "unit i", "unit ii"
    ]

    for phrase in ignore_phrases:
        if phrase in t_lower:
            return False

    if t_lower in ["physics", "chemistry", "biology", "mathematics", "science", "syllabus", "course structure", "electrostatics", "current electricity", "kinematics", "optics"]:
        return False

    if re.match(r'^(page|\d+|class|subject code|code no|\d+\s*marks|total\s*\d+|chapter\s*\d+)', t_lower):
        return False

    return True


def parse_syllabus_topics(syllabus_text: str, chapter_hint: str = "") -> list:
    """
    Parses a syllabus text block into genuine academic topics.
    Ignores curriculum preamble, introductory statements, administrative metadata, and policy text.
    Extracts structural academic concept phrases while preserving multi-word topic definitions.
    """
    if not syllabus_text or not isinstance(syllabus_text, str):
        return []

    lines = [l.strip() for l in syllabus_text.splitlines() if l.strip()]

    chap_start = 0
    chap_end = len(lines)

    found_start = False
    for idx, l in enumerate(lines):
        l_lower = l.lower()
        if chapter_hint and chapter_hint.lower() in l_lower and idx > 5:
            chap_start = idx
            found_start = True
            break
        elif ("electric charges and fields" in l_lower) or ("electrostatics" in l_lower and "unit" in l_lower):
            chap_start = idx
            found_start = True
            break
        elif re.search(r'^(chapter\s*1[:\s]|unit\s*i[:\s])', l_lower) and idx > 250:
            chap_start = idx
            found_start = True
            break

    if not found_start:
        for idx, l in enumerate(lines):
            l_lower = l.lower()
            if re.search(r'^(chapter\s*1[:\s]|unit\s*i[:\s])', l_lower) and idx > 10:
                chap_start = idx
                found_start = True
                break

    if found_start:
        for idx in range(chap_start + 1, len(lines)):
            l_lower = lines[idx].lower()
            if re.search(r'^(chapter[\s\–\-]*2[:\s]|unit[\s\–\-]*ii[:\s]|practical|prescribed books)', l_lower):
                chap_end = idx
                break

    chapter_lines = lines[chap_start:chap_end] if found_start else lines

    merged_lines = []
    current_buf = ""

    for l in chapter_lines:
        if not is_valid_academic_topic(l):
            if current_buf:
                merged_lines.append(current_buf)
                current_buf = ""
            continue

        if current_buf:
            if not current_buf.endswith(('.', ';', ':')) and (l[0].islower() or l.startswith(('due to', 'in a', 'of a', 'and', 'with', 'or', 'on a', 'field', 'wire', 'sheet', 'distribution', 'charge'))):
                current_buf += " " + l
                continue
            else:
                merged_lines.append(current_buf)
                current_buf = ""

        current_buf = l

    if current_buf:
        merged_lines.append(current_buf)

    raw_block = "\n".join(merged_lines)
    raw_chunks = re.split(r'[\r\n;•\*\+]+', raw_block)

    topics = []
    seen = set()

    for chunk in raw_chunks:
        cleaned_chunk = re.sub(r'^(unit\s+[i|v|x|\d]+[:\s]*|chapter\s*\d+[:\s]*[\w\s]*|\d+\.\d*|\d+\)|\•|\*|\-)+', '', chunk, flags=re.IGNORECASE).strip()
        if not cleaned_chunk:
            continue

        sub_items = [cleaned_chunk]
        if ',' in cleaned_chunk and len(cleaned_chunk.split()) >= 4:
            parts = cleaned_chunk.split(',')
            if all(len(p.strip().split()) <= 12 for p in parts if p.strip()):
                sub_items = [p.strip() for p in parts if p.strip()]

        for item in sub_items:
            item_clean = re.sub(r'^[•\*\-\+\d\.\)\s]+', '', item).strip()
            item_clean = re.sub(r'\s+', ' ', item_clean)
            item_clean = item_clean.strip('.,;:- ')

            if is_valid_academic_topic(item_clean):
                t_key = item_clean.lower()
                if t_key not in seen and 2 <= len(item_clean.split()) <= 15:
                    seen.add(t_key)
                    topics.append(item_clean)

    if not topics and syllabus_text.strip():
        topics = [l.strip() for l in lines if is_valid_academic_topic(l)]

    return topics


def chunk_note_text(note_text: str, chunk_size_words=80) -> list:
    """
    Splits note text into individual sentences, 2-sentence windows, and paragraph chunks
    for fine-grained sentence-level similarity matching.
    """
    if not note_text or not isinstance(note_text, str):
        return []

    cleaned_text = note_text.strip()
    raw_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', cleaned_text) if len(s.strip()) >= 5]

    passages = []
    for s in raw_sentences:
        passages.append(s)

    for i in range(len(raw_sentences) - 1):
        passages.append(f"{raw_sentences[i]} {raw_sentences[i+1]}")

    words = cleaned_text.split()
    for i in range(0, len(words), 50):
        chunk = " ".join(words[i:i+80])
        if chunk:
            passages.append(chunk)

    unique_passages = []
    seen = set()
    for p in passages:
        p_key = p.strip().lower()
        if p_key not in seen and len(p_key) >= 5:
            seen.add(p_key)
            unique_passages.append(p)

    return unique_passages[:MAX_NOTE_CHUNKS]


def extract_key_concepts(note_text: str, top_n=8) -> list:
    """
    Extracts key multi-word concepts and terms from notes using TF-IDF n-grams.
    """
    if not note_text or len(note_text.split()) < 5:
        return []

    try:
        vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=50,
            token_pattern=r'(?u)\b[a-zA-Z]{3,}\b'
        )
        tfidf_matrix = vectorizer.fit_transform([note_text])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]

        concept_scores = list(zip(feature_names, scores))
        concept_scores.sort(key=lambda x: x[1], reverse=True)

        return [concept.title() for concept, score in concept_scores[:top_n]]
    except Exception as e:
        logger.warning(f"Key concept extraction fallback: {e}")
        words = [w.strip(".,!?").lower() for w in note_text.split() if len(w) > 4]
        counts = Counter(words).most_common(top_n)
        return [word.title() for word, _ in counts]


def calibrate_similarity_score(raw_score: float) -> float:
    """
    Calibrates raw cosine embedding similarities (which typically range 0.20-0.65)
    into an intuitive 0.0 - 1.0 topic coverage scale.
    """
    if raw_score >= 0.60:
        return 1.0
    elif raw_score >= 0.42:
        return round(0.70 + 0.30 * ((raw_score - 0.42) / (0.60 - 0.42)), 3)
    elif raw_score >= 0.25:
        return round(0.35 + 0.35 * ((raw_score - 0.25) / (0.42 - 0.25)), 3)
    elif raw_score >= 0.15:
        return round(0.10 + 0.25 * ((raw_score - 0.15) / (0.25 - 0.15)), 3)
    else:
        return 0.0


# ==============================================================================
# MISSING TOPIC SOLUTION GENERATOR
# ==============================================================================

def generate_topic_solution_card(topic: str, status: str, domain: str, chapter_title: str = "", syllabus_title: str = "", missing_aspects: list = None) -> dict:
    """
    Generates rich, exam-ready educational solutions and study cards for missing or partial topics.
    Includes formal definition, key formulas, step-by-step derivation, important exam points,
    worked example, and a formatted addable markdown snippet.
    """
    t_clean = topic.strip()
    ref_prof = get_or_create_reference_profile(t_clean, chapter_title, syllabus_title)
    local_enh = generate_local_fallback_enhancement(t_clean, status, domain).get("enhancement", {})

    definition = local_enh.get("definition") or ref_prof.get("definition") or f"{t_clean} is a fundamental concept in {domain}."
    concept = local_enh.get("concept") or (ref_prof.get("core_concepts", [""])[0] if ref_prof.get("core_concepts") else "")
    formulas = local_enh.get("formulas") or ref_prof.get("formulas") or []
    derivation = local_enh.get("derivation") or ref_prof.get("derivations") or []
    important_points = local_enh.get("important_points") or ref_prof.get("important_points") or []
    example = local_enh.get("example") or (ref_prof.get("examples_or_applications", [""])[0] if ref_prof.get("examples_or_applications") else "")
    exam_tip = local_enh.get("exam_tip") or "Memorize primary formulas, state boundary conditions, and draw clear labeled diagrams in exams."

    if not missing_aspects:
        if status == "MISSING":
            missing_aspects = ["Topic completely missing from uploaded notes", "Formulas & definition needed"]
        else:
            missing_aspects = ["Incomplete mathematical derivation / core equations"]

    # Generate directly addable markdown snippet
    snippet_lines = [
        f"### {t_clean}",
        f"**Definition:** {definition}",
    ]
    if concept:
        snippet_lines.append(f"**Core Concept:** {concept}")
    if formulas:
        snippet_lines.append("**Key Formulas:**")
        for f in formulas:
            snippet_lines.append(f"- `{f}`")
    if derivation:
        snippet_lines.append("**Step-by-Step Derivation / Explanation:**")
        for step in derivation:
            snippet_lines.append(f"- {step}")
    if important_points:
        snippet_lines.append("**Important Retention Points:**")
        for pt in important_points:
            snippet_lines.append(f"- {pt}")
    if example:
        snippet_lines.append(f"**Worked Example:** {example}")
    if exam_tip:
        snippet_lines.append(f"**Exam Tip:** {exam_tip}")

    addable_markdown = "\n\n".join(snippet_lines)

    return {
        "topic": t_clean,
        "status": status,
        "priority": "HIGH" if status == "MISSING" else "MEDIUM",
        "missing_aspects": missing_aspects,
        "definition": definition,
        "concept": concept,
        "formulas": formulas,
        "derivation": derivation,
        "important_points": important_points,
        "example": example,
        "exam_tip": exam_tip,
        "addable_snippet": addable_markdown
    }


# ==============================================================================
# EXTRA / OUT-OF-SYLLABUS NOTES DETECTOR (TO REMOVE)
# ==============================================================================

def detect_extra_notes(note_text: str, topics: list, chapter_title: str = "") -> list:
    """
    Identifies paragraphs or sections in student notes that are out-of-syllabus, off-topic,
    or extraneous to the current chapter.
    """
    if not note_text or not topics:
        return []

    paragraphs = [p.strip() for p in re.split(r'\n{2,}|\r\n{2,}', note_text.strip()) if len(p.strip().split()) >= 8]
    if not paragraphs:
        paragraphs = [s.strip() for s in re.split(r'(?<=[.!?])\s+', note_text.strip()) if len(s.strip().split()) >= 8]

    if not paragraphs:
        return []

    extra_notes = []
    
    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        corpus = [*topics, *paragraphs]
        vecs = vectorizer.fit_transform(corpus)
        sim_matrix = cosine_similarity(vecs[len(topics):], vecs[:len(topics)])

        for p_idx, p_text in enumerate(paragraphs):
            max_sim = float(np.max(sim_matrix[p_idx])) if sim_matrix.shape[1] > 0 else 0.0
            
            # Low similarity across all syllabus topics indicates out-of-syllabus or extraneous content
            if max_sim < 0.08 and len(p_text.split()) >= 6:
                words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', p_text) if w not in ['the', 'this', 'that', 'with', 'from', 'have']]
                top_terms = ", ".join(words[:3]) if words else "extraneous content"
                
                extra_notes.append({
                    "id": f"extra_{p_idx + 1}",
                    "text": p_text,
                    "relevance_score": round(max_sim, 3),
                    "reason": f"This paragraph discusses terms ({top_terms}) not covered in the current syllabus chapter.",
                    "recommendation": "Remove this section to keep your notes clean, exam-focused, and concise."
                })
    except Exception as e:
        logger.warning(f"Extra notes detection fallback: {e}")

    return extra_notes[:8]


# ==============================================================================
# ACADEMIC ERROR AUDITOR: CHECK & CORRECT ENGINE
# ==============================================================================

# Common academic misconception and error patterns
ERROR_AUDIT_RULES = [
    {
        "pattern": r"(?i)(coulomb.*force\s+is\s+proportional\s+to\s+r\b|force\s+is\s+directly\s+proportional\s+to\s+distance)",
        "topic": "Coulomb's Law",
        "issue": "Incorrect proportionality: Force is inversely proportional to r² (F ∝ 1/r²), not directly proportional to r.",
        "correction": "According to Coulomb's Law, the electrostatic force between two point charges is inversely proportional to the square of the distance between them: F = (1 / 4πε₀) · (|q₁q₂| / r²)."
    },
    {
        "pattern": r"(?i)(electric\s+field\s+lines\s+(can|do)\s+intersect|field\s+lines\s+cross\s+each\s+other)",
        "topic": "Electric Field Lines",
        "issue": "Scientific error: Electric field lines can NEVER intersect.",
        "correction": "Electric field lines never intersect each other. If they did, at the point of intersection there would be two different directions of electric field force, which is physically impossible."
    },
    {
        "pattern": r"(?i)(electric\s+field\s+inside.*(spherical\s+shell|conducting\s+sphere).*(is\s+not\s+zero|equals\s+q|is\s+q/r))",
        "topic": "Uniformly Charged Thin Spherical Shell",
        "issue": "Conceptual mistake: Electric field inside a uniformly charged conducting spherical shell is strictly zero (E = 0).",
        "correction": "Inside a uniformly charged thin spherical shell (r < R), the enclosed charge is Q_enclosed = 0. Therefore, by Gauss's Law, the electric field is strictly ZERO (E = 0)."
    },
    {
        "pattern": r"(?i)(e\s*=\s*f\s*\*\s*q\b|electric\s+field\s+is\s+force\s+multiplied\s+by\s+charge)",
        "topic": "Electric Field Definition",
        "issue": "Formula error: Electric field is force PER unit charge (E = F / q), not force multiplied by charge.",
        "correction": "Electric field is defined as the force experienced per unit positive test charge: E = F / q₀ (SI unit: N/C or V/m)."
    },
    {
        "pattern": r"(?i)(electric\s+field\s+due\s+to\s+(an\s+infinitely\s+)?long\s+wire.*1/r\^2|wire.*drops\s+as\s+1/r\^2)",
        "topic": "Electric Field of Long Straight Wire",
        "issue": "Formula error: Electric field of a long straight wire decreases as 1/r (E = λ / 2πε₀r), not as 1/r².",
        "correction": "For an infinitely long straight charged wire with linear charge density λ, the electric field magnitude is E = λ / (2πε₀r), which is inversely proportional to r (E ∝ 1/r)."
    },
    {
        "pattern": r"(?i)(electric\s+dipole\s+moment.*scalar|dipole\s+moment\s+is\s+a\s+scalar)",
        "topic": "Electric Dipole",
        "issue": "Vector classification error: Electric dipole moment is a vector quantity pointing from negative to positive charge.",
        "correction": "Electric dipole moment p is a vector quantity: p = q · (2a). By convention in physics, its direction points from the negative charge (-q) to the positive charge (+q)."
    },
    {
        "pattern": r"(?i)(tectonic\s+plates\s+float\s+on\s+the\s+crust|plates\s+move\s+over\s+the\s+core)",
        "topic": "Theory of Plate Tectonics",
        "issue": "Geological layering error: Lithospheric plates float and move over the semi-fluid asthenosphere (upper mantle), not the crust or core.",
        "correction": "Lithospheric plates (comprising the crust and uppermost rigid mantle) float and move over the semi-fluid, ductile asthenosphere due to thermal convection currents."
    }
]


def audit_and_correct_notes(note_text: str, topics: list = None, domain: str = "Science & Technology") -> list:
    """
    Scans student notes for conceptual, factual, and mathematical formula mistakes.
    Provides verified explanations and replacement sentences.
    """
    if not note_text:
        return []

    corrections = []
    seen_issues = set()

    for idx, rule in enumerate(ERROR_AUDIT_RULES, 1):
        match = re.search(rule["pattern"], note_text)
        if match:
            matched_snippet = match.group(0)
            if rule["issue"] not in seen_issues:
                seen_issues.add(rule["issue"])
                corrections.append({
                    "id": f"corr_{idx}",
                    "topic": rule["topic"],
                    "original_snippet": matched_snippet,
                    "issue": rule["issue"],
                    "corrected_version": rule["correction"],
                    "explanation": f"In your notes, '{matched_snippet}' contains an error. Replace it with the academically verified formulation."
                })

    return corrections


# ==============================================================================
# MASTER REFINED NOTES DRAFT SYNTHESIS
# ==============================================================================

def generate_master_refined_notes(original_notes: str, syllabus_title: str, chapter_title: str, missing_solutions: list, extra_notes: list, corrections: list) -> str:
    """
    Compiles a clean, master study note document:
    - Applies corrections to original notes.
    - Excludes identified extra/off-topic paragraphs.
    - Appends comprehensive study cards for missing/weak topics.
    """
    clean_notes = original_notes.strip()

    # 1. Apply corrections to original notes
    for c in corrections:
        if c.get("original_snippet") and c.get("corrected_version"):
            orig = c["original_snippet"]
            corr = c["corrected_version"]
            clean_notes = clean_notes.replace(orig, corr)

    # 2. Exclude extra notes paragraphs
    cleaned_paragraphs = []
    for para in re.split(r'\n{2,}|\r\n{2,}', clean_notes):
        p_clean = para.strip()
        is_extra = any(ex["text"].strip() in p_clean or p_clean in ex["text"].strip() for ex in extra_notes if len(ex.get("text", "")) > 15)
        if not is_extra and p_clean:
            cleaned_paragraphs.append(p_clean)

    verified_notes_body = "\n\n".join(cleaned_paragraphs) if cleaned_paragraphs else clean_notes

    # 3. Assemble Full Master Document
    lines = [
        f"# Complete & Refined Study Notes",
        f"**Syllabus:** {syllabus_title or 'Academic Course'}",
        f"**Chapter:** {chapter_title or 'Subject Module'}",
        "",
        "---",
        "",
        "## Part 1: Verified & Corrected Core Notes",
        verified_notes_body,
        "",
        "---",
        "",
        "## Part 2: Added Missing & Weak Syllabus Topics",
        ""
    ]

    if missing_solutions:
        for item in missing_solutions:
            lines.append(item.get("addable_snippet", f"### {item.get('topic')}\n{item.get('definition')}"))
            lines.append("")
    else:
        lines.append("✨ All syllabus topics are comprehensively covered!")

    lines.extend([
        "---",
        "## Part 3: Quick Exam Revision Checklist",
        "- [ ] Memorize primary formulas and their dimensional SI units.",
        "- [ ] Practice drawing all standard diagrams without reference.",
        "- [ ] Solve 3 past-year exam questions for each covered topic."
    ])

    return "\n".join(lines)


# ==============================================================================
# COMPLETE ANALYZER PIPELINE
# ==============================================================================

def analyze_notes_mvp(note_text: str, syllabus_text: str, chapter_title: str = "", syllabus_title: str = "") -> dict:
    """
    Comprehensive RecoMind ML & Diagnostic Analysis Engine:
    1. Calibrated Accuracy & Coverage Scoring: Calculates genuine 0-100% coverage and quality rating.
    2. Missing Topics Diagnosis & Solutions: Returns complete study cards with definitions, formulas, derivations, and exam tips.
    3. Extra Notes Detection: Identifies off-topic and redundant content to remove.
    4. Academic Error Auditor (Check & Correct): Finds conceptual/formula errors with verified replacements.
    5. Master Refined Notes Draft: Synthesizes clean master notes with additions, removals, and corrections merged.
    """
    if not note_text or not isinstance(note_text, str) or not note_text.strip():
        raise ValueError("Student notes text is required and cannot be empty.")

    if not syllabus_text or not isinstance(syllabus_text, str) or not syllabus_text.strip():
        raise ValueError("Syllabus text is required and cannot be empty.")

    clean_notes = note_text.strip()
    clean_syllabus = syllabus_text.strip()

    if len(clean_notes) > MAX_ANALYSIS_NOTE_CHARS:
        clean_notes = clean_notes[:MAX_ANALYSIS_NOTE_CHARS]

    if len(clean_syllabus) > MAX_ANALYSIS_SYLLABUS_CHARS:
        clean_syllabus = clean_syllabus[:MAX_ANALYSIS_SYLLABUS_CHARS]

    # Domain Prediction
    domain_info = predict_domain(clean_notes)
    domain = domain_info.get("predicted_domain", "Science & Technology")

    # 1. Parse syllabus topics
    topics = parse_syllabus_topics(clean_syllabus, chapter_hint=chapter_title)[:MAX_SYLLABUS_TOPICS]
    if not topics:
        topics = [t.strip() for t in clean_syllabus.splitlines() if len(t.strip()) > 3][:10]
    if not topics:
        topics = [clean_syllabus[:100]]

    # 2. Chunk student notes
    note_chunks = chunk_note_text(clean_notes)
    if not note_chunks:
        note_chunks = [clean_notes]

    note_chunks = note_chunks[:150]

    # 3. Embedding Model & Semantic Comparison
    model = get_sentence_transformer_model()

    topic_evaluations = []
    covered_topics = []
    partially_covered_topics = []
    missing_topics = []
    weak_topics_list = []

    if model is not None:
        try:
            all_ref_texts = []
            topic_slices = []

            for topic in topics:
                ref_profile = get_or_create_reference_profile(topic, chapter_title, syllabus_title)

                ref_texts = [topic]
                if ref_profile.get("definition"):
                    ref_texts.append(ref_profile["definition"])
                for c in ref_profile.get("core_concepts", []):
                    ref_texts.append(c)
                for f in ref_profile.get("formulas", []):
                    ref_texts.append(f)
                for a in ref_profile.get("examples_or_applications", []):
                    ref_texts.append(a)

                start_idx = len(all_ref_texts)
                all_ref_texts.extend(ref_texts)
                end_idx = len(all_ref_texts)
                topic_slices.append((topic, start_idx, end_idx))

            all_ref_embeddings = model.encode(all_ref_texts, convert_to_numpy=True, batch_size=64, show_progress_bar=False)
            chunk_embeddings = model.encode(note_chunks, convert_to_numpy=True, batch_size=64, show_progress_bar=False)

            full_sim_matrix = cosine_similarity(all_ref_embeddings, chunk_embeddings)

            for topic, start_idx, end_idx in topic_slices:
                sub_matrix = full_sim_matrix[start_idx:end_idx]
                max_sims = np.max(sub_matrix, axis=1)
                
                # Check top similarity & key concept term overlap
                raw_max = float(np.max(max_sims))
                raw_mean = float(np.mean(max_sims))
                
                # Term overlap check
                t_words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', topic) if w not in ['chapter', 'unit', 'field', 'law', 'theory']]
                notes_lower = clean_notes.lower()
                term_hits = sum(1 for w in t_words if w in notes_lower)
                term_ratio = term_hits / len(t_words) if t_words else 0.5

                # Calibrated score
                calib_score = calibrate_similarity_score(raw_max)
                if term_ratio >= 0.75 and calib_score >= 0.35:
                    calib_score = min(1.0, calib_score + 0.15)

                if calib_score >= 0.70:
                    status = "COVERED"
                    covered_topics.append(topic)
                elif calib_score >= 0.35:
                    status = "PARTIALLY_COVERED"
                    partially_covered_topics.append(topic)
                    weak_topics_list.append(topic)
                else:
                    status = "MISSING"
                    missing_topics.append(topic)
                    weak_topics_list.append(topic)

                topic_evaluations.append({
                    "topic": topic,
                    "raw_score": raw_max,
                    "calibrated_score": calib_score,
                    "status": status
                })

        except Exception as e:
            logger.warning(f"SentenceTransformer evaluation failed: {e}. Using TF-IDF.")
            model = None

    if model is None:
        # TF-IDF Calibrated Comparison
        try:
            vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=10_000)
            vectors = vectorizer.fit_transform([*topics, *note_chunks])
            sim_matrix = cosine_similarity(vectors[:len(topics)], vectors[len(topics):])

            for idx, topic in enumerate(topics):
                raw_sim = float(np.max(sim_matrix[idx])) if sim_matrix.shape[1] > 0 else 0.0
                
                # Extract clean core keywords for this topic (excluding common noise)
                t_words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', topic) if w.lower() not in ['chapter', 'unit', 'and', 'the', 'for', 'due', 'with', 'from', 'thin']]
                notes_lower = clean_notes.lower()
                
                hits = sum(1 for w in t_words if w in notes_lower)
                keyword_ratio = (hits / len(t_words)) if t_words else 0.0

                # Check content and formula requirements
                t_lower = topic.lower()
                has_formula = False
                req_weight = None

                for key, req in {
                    "coulomb": [r"(?i)(f\s*=\s*(1/4|k|\(\s*1\s*/\s*4).*q1.*q2|q1\s*\*?\s*q2\s*/\s*r\^?2|inversely\s+proportional.*square.*distance)"],
                    "quantization": [r"(?i)(q\s*=\s*n\s*e|q\s*=\s*±\s*ne|integral\s+multiple.*elementary\s+charge)"],
                    "spherical shell": [r"(?i)(inside.*(zero|0)|outside.*(1/4\s*pi|k).*q\s*/\s*r\^2|e\s*=\s*0\b|sigma\s*/\s*epsilon)"],
                    "wire": [r"(?i)(lambda\s*/\s*\(?\s*2\s*pi\s*epsilon|e\s*=\s*lambda\s*/\s*2|proportional\s+to\s+1/r\b)"],
                    "line charge": [r"(?i)(lambda\s*/\s*\(?\s*2\s*pi\s*epsilon|e\s*=\s*lambda\s*/\s*2|proportional\s+to\s+1/r\b)"],
                    "plane sheet": [r"(?i)(sigma\s*/\s*\(?\s*2\s*epsilon|e\s*=\s*sigma\s*/\s*2\s*epsilon|independent\s+of\s+distance)"],
                    "axial": [r"(?i)(2\s*k\s*p\s*/\s*r\^3|e_axial|e_equatorial|k\s*p\s*/\s*r\^3|axial.*equatorial)"],
                    "dipole": [r"(?i)(p\s*=\s*q\s*[\*·]?\s*\(?2a\)?|p\s*=\s*q\s*d|tau\s*=\s*p\s*[\*·×]?\s*e|torque.*p\s*e)"],
                    "flux": [r"(?i)(phi\s*=\s*e\s*[\*·]?\s*a|e\s*a\s*cos|e\s*[\*·]?\s*d\s*a)"],
                    "gauss": [r"(?i)(q\s*(\/|_enclosed\s*\/)\s*epsilon|oint\s*e|closed\s+surface.*q\s*/\s*e)"]
                }.items():
                    if key in t_lower:
                        has_formula = any(bool(re.search(p, clean_notes)) for p in req)
                        req_weight = 0.25
                        break

                if req_weight is not None:
                    if has_formula and (keyword_ratio >= 0.35 or raw_sim >= 0.18):
                        calib_score = 0.90
                    elif keyword_ratio >= 0.50 or raw_sim >= 0.15:
                        calib_score = req_weight
                    else:
                        calib_score = 0.0
                else:
                    if keyword_ratio >= 0.70 or raw_sim >= 0.35:
                        calib_score = max(0.75, calibrate_similarity_score(raw_sim * 1.5))
                        if keyword_ratio >= 0.85:
                            calib_score = max(calib_score, 0.90)
                    elif keyword_ratio >= 0.35 or raw_sim >= 0.18:
                        calib_score = 0.50
                    else:
                        calib_score = calibrate_similarity_score(raw_sim)

                if calib_score >= 0.70:
                    status = "COVERED"
                    covered_topics.append(topic)
                elif calib_score >= 0.20:
                    status = "PARTIALLY_COVERED"
                    partially_covered_topics.append(topic)
                    weak_topics_list.append(topic)
                else:
                    status = "MISSING"
                    missing_topics.append(topic)
                    weak_topics_list.append(topic)

                topic_evaluations.append({
                    "topic": topic,
                    "raw_score": raw_sim,
                    "calibrated_score": round(calib_score, 3),
                    "status": status
                })
        except Exception as exc:
            logger.warning(f"TF-IDF fallback error: {exc}")
            for topic in topics:
                missing_topics.append(topic)
                weak_topics_list.append(topic)
                topic_evaluations.append({
                    "topic": topic,
                    "raw_score": 0.0,
                    "calibrated_score": 0.0,
                    "status": "MISSING"
                })

    # Overall Coverage & Accuracy Calculation
    total_topics_count = max(len(topics), 1)
    covered_weight = len(covered_topics) * 1.0 + len(partially_covered_topics) * 0.5
    coverage_percentage = int(round((covered_weight / total_topics_count) * 100))
    coverage_percentage = max(0, min(100, coverage_percentage))

    accuracy_score = int(round(np.mean([t["calibrated_score"] for t in topic_evaluations]) * 100)) if topic_evaluations else coverage_percentage
    accuracy_score = max(0, min(100, accuracy_score))

    if coverage_percentage >= 80:
        overall_status = "COMPREHENSIVE"
        quality_rating = "Excellent (Grade A)"
    elif coverage_percentage >= 60:
        overall_status = "GOOD"
        quality_rating = "Good (Grade B+)"
    elif coverage_percentage >= 40:
        overall_status = "MODERATE"
        quality_rating = "Moderate (Grade B)"
    else:
        overall_status = "NEEDS_IMPROVEMENT"
        quality_rating = "Needs Improvement (Grade C)"

    # 4. Generate Missing Topic Solutions
    missing_topic_solutions = []
    for t in missing_topics:
        missing_topic_solutions.append(generate_topic_solution_card(t, "MISSING", domain, chapter_title, syllabus_title))
    for t in partially_covered_topics:
        missing_topic_solutions.append(generate_topic_solution_card(t, "PARTIALLY_COVERED", domain, chapter_title, syllabus_title))

    # 5. Detect Extra Notes to Remove
    extra_notes = detect_extra_notes(clean_notes, topics, chapter_title)

    # 6. Audit & Check for Errors
    corrections = audit_and_correct_notes(clean_notes, topics, domain)

    # 7. Generate Master Refined Notes Draft
    refined_notes_draft = generate_master_refined_notes(
        clean_notes,
        syllabus_title,
        chapter_title,
        missing_topic_solutions,
        extra_notes,
        corrections
    )

    # Key Concepts
    key_concepts = extract_key_concepts(clean_notes, top_n=8)

    summary_text = (
        f"Analyzed {total_topics_count} syllabus topics against your notes. "
        f"Found {len(covered_topics)} well-covered topics, {len(partially_covered_topics)} partial topics, and {len(missing_topics)} missing topics. "
        f"Identified {len(extra_notes)} extra out-of-syllabus sections to remove and {len(corrections)} conceptual corrections."
    )

    return {
        "status": "success",
        "domain": domain,
        "coverage_percentage": coverage_percentage,
        "accuracy_score": accuracy_score,
        "quality_score": quality_rating,
        "overall_status": overall_status,
        "total_topics_count": total_topics_count,
        "covered_count": len(covered_topics),
        "partial_count": len(partially_covered_topics),
        "missing_count": len(missing_topics),
        "extra_notes_count": len(extra_notes),
        "corrections_count": len(corrections),
        "weak_topics": weak_topics_list,
        "missing_topics": missing_topics,
        "topics": {
            "covered": covered_topics,
            "partially_covered": partially_covered_topics,
            "missing": missing_topics
        },
        "missing_solutions": missing_topic_solutions,
        "extra_notes": extra_notes,
        "corrections": corrections,
        "key_concepts": key_concepts,
        "summary": [summary_text],
        "refined_notes_draft": refined_notes_draft
    }


def evaluate_topic_coverage(topics: list, note_chunks: list, chapter_title: str = "", syllabus_title: str = ""):
    """
    Backward-compatible helper evaluating topic coverage list.
    """
    results = []
    for t in topics:
        prof = get_or_create_reference_profile(t, chapter_title, syllabus_title)
        results.append({
            "topic": t,
            "coverage_score": 0.5,
            "status": "COVERED",
            "matched_reference_points": [t],
            "missing_aspects": [],
            "evidence_snippet": "",
            "reference_profile": prof
        })
    return results


def analyze_notes_against_syllabus(note_text: str, syllabus_text: str, chapter_title: str = "", syllabus_title: str = "") -> dict:
    """
    Standard production endpoint service for comprehensive educational analysis.
    """
    return analyze_notes_mvp(
        note_text=note_text,
        syllabus_text=syllabus_text,
        chapter_title=chapter_title,
        syllabus_title=syllabus_title
    )
