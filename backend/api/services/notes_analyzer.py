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
from .reference_knowledge_service import get_or_create_reference_profile

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

    # Find best matching chapter start line
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
    # 1. Add individual sentences
    for s in raw_sentences:
        passages.append(s)

    # 2. Add 2-sentence sliding windows for context
    for i in range(len(raw_sentences) - 1):
        passages.append(f"{raw_sentences[i]} {raw_sentences[i+1]}")

    # 3. Add 80-word paragraph chunks
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


def generate_comprehensive_summary(note_text: str) -> dict:
    """
    Generates a comprehensive summary of the entire uploaded study notes.
    """
    if not note_text or not isinstance(note_text, str):
        return {"overview": "", "detailed_points": [], "coverage_summary": ""}

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', note_text.strip()) if len(s.strip().split()) >= 4]

    if not sentences:
        return {"overview": note_text.strip(), "detailed_points": [note_text.strip()], "coverage_summary": "Short notes provided."}

    overview = " ".join(sentences[:min(3, len(sentences))])
    detailed_points = sentences
    total_words = len(note_text.split())
    coverage_summary = f"The uploaded notes contain {len(sentences)} key statements across approximately {total_words} words."

    return {
        "overview": overview,
        "detailed_points": detailed_points,
        "coverage_summary": coverage_summary
    }


_COMPLETENESS_MODEL_CACHE = None


def get_completeness_classifier_model():
    """
    Singleton loader for trained Supervised Note Completeness Classifier (completeness_classifier_v1.joblib).
    """
    global _COMPLETENESS_MODEL_CACHE
    if _COMPLETENESS_MODEL_CACHE is not None:
        return _COMPLETENESS_MODEL_CACHE

    model_path = os.path.join(settings.BASE_DIR, 'ML', 'saved_models', 'completeness_classifier_v1.joblib')
    if os.path.exists(model_path):
        try:
            _COMPLETENESS_MODEL_CACHE = joblib.load(model_path)
            logger.info(f"Loaded Supervised Completeness Model from {model_path}")
        except Exception as e:
            logger.error(f"Error loading completeness model: {e}")
    return _COMPLETENESS_MODEL_CACHE


def evaluate_topic_coverage(topics: list, note_chunks: list, chapter_title: str = "", syllabus_title: str = ""):
    """
    Supervised Content-Aware ML Analysis Pipeline:
    Retrieves structured reference knowledge profiles and evaluates student notes using
    SentenceTransformer embeddings and the Supervised Completeness Model (completeness_classifier_v1.joblib).
    """
    model = get_sentence_transformer_model()
    completeness_classifier = get_completeness_classifier_model()
    topic_results = []

    if model is not None and len(topics) > 0 and len(note_chunks) > 0:
        try:
            chunk_embeddings = model.encode(note_chunks, convert_to_numpy=True, batch_size=32)

            for topic in topics:
                # 1. Retrieve or create reference knowledge profile
                ref_profile = get_or_create_reference_profile(topic, chapter_title, syllabus_title)

                # Collect reference content units
                ref_units = []
                if ref_profile.get("definition"):
                    ref_units.append(("definition", ref_profile["definition"]))
                for c in ref_profile.get("core_concepts", []):
                    ref_units.append(("core_concept", c))
                for s in ref_profile.get("subtopics", []):
                    ref_units.append(("subtopic", s))
                for f in ref_profile.get("formulas", []):
                    ref_units.append(("formula", f))
                for d in ref_profile.get("derivations", []):
                    ref_units.append(("derivation", d))
                for p in ref_profile.get("important_points", []):
                    ref_units.append(("important_point", p))
                for e in ref_profile.get("examples_or_applications", []):
                    ref_units.append(("example", e))

                if not ref_units:
                    ref_units = [("topic_name", topic)]

                # 2. Encode reference content units
                ref_unit_texts = [unit[1] for unit in ref_units]
                ref_embeddings = model.encode(ref_unit_texts, convert_to_numpy=True, batch_size=32)

                # 3. Compute reference-to-note similarity matrix
                sim_matrix = cosine_similarity(ref_embeddings, chunk_embeddings)

                matched_reference_points = []
                missing_aspects = []
                best_evidence = ""
                highest_sim_score = 0.0
                total_unit_score = 0.0

                for idx, (unit_type, unit_text) in enumerate(ref_units):
                    max_chunk_idx = int(np.argmax(sim_matrix[idx]))
                    max_score = float(sim_matrix[idx][max_chunk_idx])

                    if max_score > highest_sim_score:
                        highest_sim_score = max_score
                        best_evidence = note_chunks[max_chunk_idx]

                    # Component match condition with specific term validation
                    unit_lower = unit_text.lower()
                    chunk_ev = note_chunks[max_chunk_idx].lower()

                    requires_map = 'map' in unit_lower or 'world' in unit_lower
                    has_map = any(k in chunk_ev for k in ['map', 'world', 'location', 'coordinate'])

                    requires_mitigation = 'mitigation' in unit_lower or 'hazard' in unit_lower
                    has_mitigation = any(k in chunk_ev for k in ['mitigation', 'warning', 'hazard', 'stabilization', 'afforestation'])

                    unit_score = 0.0
                    if completeness_classifier is not None:
                        try:
                            r_vec = ref_embeddings[idx]
                            s_vec = chunk_embeddings[max_chunk_idx]
                            r_norm = r_vec / (np.linalg.norm(r_vec) + 1e-9)
                            s_norm = s_vec / (np.linalg.norm(s_vec) + 1e-9)

                            abs_diff = np.abs(r_vec - s_vec)
                            elem_prod = r_vec * s_vec
                            cos_sim = float(np.dot(r_norm, s_norm))

                            feat_vec = np.hstack([r_vec, s_vec, abs_diff, elem_prod, [cos_sim]]).reshape(1, -1)
                            comp_probs = completeness_classifier["model"].predict_proba(feat_vec)[0]
                            pred_class = int(np.argmax(comp_probs))

                            if pred_class == 0:
                                unit_score = 0.0
                            elif pred_class == 1:
                                unit_score = 0.5
                            else:
                                unit_score = 1.0
                        except Exception:
                            unit_score = 1.0 if max_score >= 0.70 else (0.5 if max_score >= 0.45 else 0.0)
                    else:
                        unit_score = 1.0 if max_score >= 0.70 else (0.5 if max_score >= 0.45 else 0.0)

                    if (requires_map and not has_map) or (requires_mitigation and not has_mitigation):
                        unit_score = 0.0

                    if unit_score == 1.0:
                        matched_reference_points.append(unit_text)
                    else:
                        missing_aspects.append(unit_text)

                    total_unit_score += unit_score

                total_units = len(ref_units)
                completeness_ratio = total_unit_score / total_units if total_units > 0 else 0.0

                # Check math / derivation presence if formulas required
                has_formulas = len(ref_profile.get("formulas", [])) > 0
                notes_has_math = bool(re.search(r'[\=\/\*\+\-\^\u03bc\u03c0]', " ".join(note_chunks)))

                if has_formulas and not notes_has_math and completeness_ratio >= 0.60:
                    status = "PARTIALLY_COVERED"
                    completeness_ratio = min(completeness_ratio, 0.55)
                    missing_aspects.append("mathematical formulas & derivation equations")
                elif completeness_ratio >= 0.60:
                    status = "COVERED"
                elif completeness_ratio >= 0.25:
                    status = "PARTIALLY_COVERED"
                else:
                    status = "MISSING"



                topic_results.append({
                    "topic": topic,
                    "coverage_score": round(completeness_ratio, 4),
                    "status": status,
                    "matched_reference_points": matched_reference_points,
                    "missing_aspects": missing_aspects if status != "COVERED" else [],
                    "evidence_snippet": best_evidence if status != "MISSING" else "",
                    "reference_profile": ref_profile
                })

            return topic_results
        except Exception as e:
            logger.warning(f"SentenceTransformer evaluation failed: {e}. Falling back to TF-IDF.")

    # TF-IDF Fallback
    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=10_000)
        vectors = vectorizer.fit_transform([*topics, *note_chunks])
        sim_matrix = cosine_similarity(vectors[:len(topics)], vectors[len(topics):])
    except Exception as exc:
        logger.warning("TF-IDF fallback failed: %s", exc.__class__.__name__)
        sim_matrix = np.zeros((len(topics), len(note_chunks)))

    for topic_index, topic in enumerate(topics):
        best_idx = int(np.argmax(sim_matrix[topic_index]))
        best_score = float(sim_matrix[topic_index][best_idx])
        best_chunk = note_chunks[best_idx]

        if best_score >= 0.45:
            status = "COVERED"
        elif best_score >= 0.25:
            status = "PARTIALLY_COVERED"
        else:
            status = "MISSING"

        topic_results.append({
            "topic": topic,
            "coverage_score": round(best_score, 4),
            "status": status,
            "matched_reference_points": [topic] if status == "COVERED" else [],
            "missing_aspects": [topic] if status == "MISSING" else [],
            "evidence_snippet": best_chunk if status != "MISSING" else "",
            "reference_profile": get_or_create_reference_profile(topic, chapter_title, syllabus_title)
        })

    return topic_results


def generate_detailed_missing_topic_paragraph(topic: str, status: str, domain: str, missing_aspects: list = None) -> dict:
    """
    Generates a detailed, exam-ready educational explanation paragraph for a missing or partially covered topic.
    """
    t_clean = topic.strip()
    placement = f"Insert in your notes section right after your core definitions, before topic exercises."

    missing_str = ", ".join(missing_aspects[:3]) if missing_aspects else "core conceptual details and formulas"

    if status == "PARTIALLY_COVERED":
        reason_str = f"Topic is mentioned in your notes, but key reference components ({missing_str}) are missing."
        rec_str = f"Your notes mention '{t_clean}', but expand with missing reference content ({missing_str})."
    else:
        reason_str = "Topic was not found in your uploaded notes."
        rec_str = f"Add '{t_clean}' to your notes immediately. See the suggested exam paragraph below."

    paragraph = (
        f"**{t_clean}**: This is a fundamental concept in {domain}. "
        f"It establishes key mathematical relationships and physical/theoretical principles required for comprehensive problem solving. "
        f"When adding this section to your notes, include the formal definition, primary governing formula, boundary conditions, and real-world applications. "
        f"Mastering {t_clean} is critical for exam questions involving theoretical proofs and practical numerical derivations."
    )

    return {
        "topic": t_clean,
        "status": status,
        "reason": reason_str,
        "recommendation": rec_str,
        "placement_guidance": placement,
        "suggested_paragraph": paragraph,
        "missing_aspects": missing_aspects or []
    }


def generate_recommendations_and_refined_notes(topic_results: list, note_text: str, domain: str) -> dict:
    """
    Processes topic evaluation results and generates structured recommendations,
    revision suggestions, and a refined notes draft.
    """
    covered = []
    partially_covered = []
    missing = []

    weak_topics = []
    detailed_recommendations = []
    revision_suggestions = []
    missing_additions = []

    for item in topic_results:
        t = item["topic"]
        score = item["coverage_score"]
        status = item["status"]
        missing_aspects = item.get("missing_aspects", [])

        if status == "COVERED":
            covered.append(t)
            revision_suggestions.append({
                "topic": t,
                "suggestion": f"Strong coverage ({int(score * 100)}%). Review key formulas and practice numerical problems for retention."
            })
        elif status == "PARTIALLY_COVERED":
            partially_covered.append(t)
            weak_topics.append({
                "topic": t,
                "coverage_score": score,
                "status": status,
                "missing_aspects": missing_aspects
            })
            detail_info = generate_detailed_missing_topic_paragraph(t, status, domain, missing_aspects)
            detailed_recommendations.append({
                "topic": t,
                "priority": "MEDIUM",
                "reason": detail_info["reason"],
                "placement_guidance": detail_info["placement_guidance"],
                "suggested_paragraph": detail_info["suggested_paragraph"],
                "recommendation": detail_info["recommendation"],
                "missing_aspects": missing_aspects
            })
            missing_additions.append(detail_info["suggested_paragraph"])
        else: # MISSING
            missing.append(t)
            weak_topics.append({
                "topic": t,
                "coverage_score": score,
                "status": status,
                "missing_aspects": missing_aspects
            })
            detail_info = generate_detailed_missing_topic_paragraph(t, status, domain, missing_aspects)
            detailed_recommendations.append({
                "topic": t,
                "priority": "HIGH",
                "reason": detail_info["reason"],
                "placement_guidance": detail_info["placement_guidance"],
                "suggested_paragraph": detail_info["suggested_paragraph"],
                "recommendation": detail_info["recommendation"],
                "missing_aspects": missing_aspects
            })
            missing_additions.append(detail_info["suggested_paragraph"])

    weak_topics.sort(key=lambda x: x["coverage_score"])
    detailed_recommendations.sort(key=lambda x: 0 if x["priority"] == "HIGH" else 1)

    refined_draft_sections = [
        "=== YOUR ORIGINAL NOTES ===",
        note_text.strip(),
        "\n=== RECOMMENDED ADDITIONS (MISSING & WEAK TOPICS) ==="
    ]
    if missing_additions:
        for idx, add_para in enumerate(missing_additions, 1):
            refined_draft_sections.append(f"[{idx}] {add_para}")
    else:
        refined_draft_sections.append("Your notes already cover all required syllabus topics comprehensively!")

    refined_notes_draft = "\n\n".join(refined_draft_sections)

    return {
        "topics": {
            "covered": covered,
            "partially_covered": partially_covered,
            "missing": missing
        },
        "weak_topics": weak_topics,
        "recommendations": detailed_recommendations,
        "revision_suggestions": revision_suggestions,
        "refined_notes_draft": refined_notes_draft
    }


from .gemini_notes_audit import audit_student_notes_with_gemini


def analyze_notes_against_syllabus(note_text: str, syllabus_text: str, chapter_title: str = "", syllabus_title: str = "") -> dict:
    """
    Presentation-Ready Analysis Engine:
    Employs Gemini 2.5 Flash as the primary Academic Auditor grounded in actual Reference Context
    and extracted Student Notes.
    """
    if not note_text or not isinstance(note_text, str) or not note_text.strip():
        raise ValueError("Notes text is required for analysis.")

    if not syllabus_text or not isinstance(syllabus_text, str) or not syllabus_text.strip():
        raise ValueError("Syllabus text is required for analysis.")

    clean_notes = note_text.strip()
    clean_syllabus = syllabus_text.strip()

    if len(clean_notes) > MAX_ANALYSIS_NOTE_CHARS:
        logger.info(f"Notes text auto-truncated from {len(clean_notes)} to {MAX_ANALYSIS_NOTE_CHARS} chars.")
        clean_notes = clean_notes[:MAX_ANALYSIS_NOTE_CHARS]

    if len(clean_syllabus) > MAX_ANALYSIS_SYLLABUS_CHARS:
        logger.info(f"Syllabus text auto-truncated from {len(clean_syllabus)} to {MAX_ANALYSIS_SYLLABUS_CHARS} chars.")
        clean_syllabus = clean_syllabus[:MAX_ANALYSIS_SYLLABUS_CHARS]

    # 1. Predict Broad Domain Metadata
    domain_info = predict_domain(clean_notes)
    predicted_domain = domain_info.get("predicted_domain", "General / Mixed Academic Domain")

    # 2. Parse syllabus into individual topics & build structured reference components list
    topics = parse_syllabus_topics(clean_syllabus)[:MAX_SYLLABUS_TOPICS]

    reference_components = []
    comp_counter = 1
    for t in topics:
        ref_prof = get_or_create_reference_profile(t, chapter_title, syllabus_title)
        if ref_prof.get("definition"):
            reference_components.append({
                "id": f"comp_{comp_counter}",
                "topic": t,
                "type": "definition",
                "component": f"Definition of {t}: {ref_prof['definition']}"
            })
            comp_counter += 1
        for c in ref_prof.get("core_concepts", []):
            reference_components.append({
                "id": f"comp_{comp_counter}",
                "topic": t,
                "type": "concept",
                "component": f"Core Concept of {t}: {c}"
            })
            comp_counter += 1
        for f in ref_prof.get("formulas", []):
            reference_components.append({
                "id": f"comp_{comp_counter}",
                "topic": t,
                "type": "formula",
                "component": f"Formula for {t}: {f}"
            })
            comp_counter += 1
        for d in ref_prof.get("derivations", []):
            reference_components.append({
                "id": f"comp_{comp_counter}",
                "topic": t,
                "type": "derivation",
                "component": f"Derivation for {t}: {d}"
            })
            comp_counter += 1
        for p in ref_prof.get("important_points", []):
            reference_components.append({
                "id": f"comp_{comp_counter}",
                "topic": t,
                "type": "important_point",
                "component": f"Important Point for {t}: {p}"
            })
            comp_counter += 1
        for e in ref_prof.get("examples_or_applications", []):
            reference_components.append({
                "id": f"comp_{comp_counter}",
                "topic": t,
                "type": "example",
                "component": f"Example/Application for {t}: {e}"
            })
            comp_counter += 1

    if not reference_components:
        for t in topics:
            reference_components.append({
                "id": f"comp_{comp_counter}",
                "topic": t,
                "type": "concept",
                "component": f"Core academic content for {t}"
            })
            comp_counter += 1

    # 3. Call Gemini Academic Auditor with Reference Components
    audit_res = audit_student_notes_with_gemini(
        chapter_title=chapter_title or "Selected Syllabus Chapter",
        syllabus_title=syllabus_title or "Subject Syllabus",
        reference_components=reference_components,
        student_notes=clean_notes
    )

    # 4. Map Audit Output into Frontend API Response Schema
    covered_names = audit_res.get("covered", [])
    partial_names = audit_res.get("partially_covered", [])
    missing_names = audit_res.get("missing", [])

    weak_topics = []
    for t_name in partial_names:
        weak_topics.append({
            "topic": t_name,
            "coverage_score": 0.5,
            "status": "PARTIALLY_COVERED",
            "missing_aspects": ["Missing complete mathematical derivation or detailed equations"]
        })
    for t_name in missing_names:
        weak_topics.append({
            "topic": t_name,
            "coverage_score": 0.0,
            "status": "MISSING",
            "missing_aspects": ["No notes or evidence found in uploaded document"]
        })

    summary_text = audit_res.get("summary", "")
    if isinstance(summary_text, list):
        summary_text = " ".join(summary_text)

    key_concepts = audit_res.get("key_concepts", [])
    if not key_concepts:
        key_concepts = extract_key_concepts(clean_notes, top_n=8)

    rec_results = generate_recommendations_and_refined_notes(
        evaluate_topic_coverage(topics, chunk_note_text(clean_notes), chapter_title, syllabus_title),
        clean_notes,
        predicted_domain
    )

    return {
        "status": "success",
        "domain": predicted_domain,
        "coverage_percentage": float(audit_res.get("coverage_percentage", 0.0)),
        "overall_status": audit_res.get("overall_status", "NEEDS_IMPROVEMENT"),
        "components_evaluated_count": audit_res.get("components_evaluated_count", len(reference_components)),
        "full_count": audit_res.get("full_count", 0),
        "partial_count": audit_res.get("partial_count", 0),
        "missing_count": audit_res.get("missing_count", len(reference_components)),
        "components": audit_res.get("components", []),
        "topics": {
            "covered": covered_names,
            "partially_covered": partial_names,
            "missing": missing_names
        },
        "weak_topics": weak_topics,
        "missing_aspects": audit_res.get("missing_aspects", []),
        "summary": [summary_text] if summary_text else ["Analysis completed."],
        "key_concepts": key_concepts,
        "recommendations": audit_res.get("recommendations", rec_results["recommendations"]),
        "revision_suggestions": audit_res.get("revision_tips", []),
        "refined_notes_draft": rec_results["refined_notes_draft"]
    }


def analyze_notes_mvp(note_text: str, syllabus_text: str, chapter_title: str = "", syllabus_title: str = "") -> dict:
    """
    Final Simplified RecoMind MVP Analysis Engine:
    - Inputs: 1-chapter syllabus text and student notes text.
    - Extracts syllabus topics.
    - Enriches topics with concise academic reference context (reference_knowledge_service).
    - Chunks student notes into sentence passages.
    - Performs semantic similarity matching via SentenceTransformers (all-MiniLM-L6-v2) or TF-IDF fallback.
    - Calculates overall coverage percentage and identifies weak / missing topics.
    - Returns ONLY coverage_percentage, weak_topics, and missing_topics.
    """
    if not note_text or not isinstance(note_text, str) or not note_text.strip():
        raise ValueError("Student notes text is required and cannot be empty.")

    if not syllabus_text or not isinstance(syllabus_text, str) or not syllabus_text.strip():
        raise ValueError("Syllabus text is required and cannot be empty.")

    clean_notes = note_text.strip()
    clean_syllabus = syllabus_text.strip()

    # 1. Parse syllabus topics
    topics = parse_syllabus_topics(clean_syllabus)[:MAX_SYLLABUS_TOPICS]
    if not topics:
        topics = [clean_syllabus[:100]]

    # 2. Chunk student notes
    note_chunks = chunk_note_text(clean_notes)
    if not note_chunks:
        note_chunks = [clean_notes]

    note_chunks = note_chunks[:150]

    # 3. Model & Semantic Vector Comparison
    model = get_sentence_transformer_model()

    topic_scores = []
    weak_topics = []
    missing_topics = []

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
                topic_score = float(np.mean(max_sims))
                topic_scores.append(topic_score)

                if topic_score < 0.50:
                    weak_topics.append(topic)
                if topic_score < 0.30:
                    missing_topics.append(topic)

        except Exception as e:
            logger.warning(f"SentenceTransformer embedding comparison failed: {e}. Falling back to TF-IDF.")
            model = None

    if model is None:
        # TF-IDF Fallback Semantic Comparison
        try:
            vectorizer = TfidfVectorizer(stop_words='english', max_features=10_000)
            vectors = vectorizer.fit_transform([*topics, *note_chunks])
            sim_matrix = cosine_similarity(vectors[:len(topics)], vectors[len(topics):])

            for idx, topic in enumerate(topics):
                max_sim = float(np.max(sim_matrix[idx]))
                topic_scores.append(max_sim)
                if max_sim < 0.40:
                    weak_topics.append(topic)
                if max_sim < 0.20:
                    missing_topics.append(topic)
        except Exception as exc:
            logger.warning("TF-IDF evaluation fallback error: %s", exc)
            topic_scores = [0.0] * len(topics)
            weak_topics = list(topics)
            missing_topics = list(topics)

    total_topics = len(topics)
    if total_topics > 0 and topic_scores:
        avg_score = float(np.mean(topic_scores))
        coverage_percentage = int(round(avg_score * 100))
    else:
        coverage_percentage = 0

    coverage_percentage = max(0, min(100, coverage_percentage))

    return {
        "coverage_percentage": coverage_percentage,
        "weak_topics": weak_topics,
        "missing_topics": missing_topics
    }

