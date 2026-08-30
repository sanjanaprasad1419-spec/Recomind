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

logger = logging.getLogger(__name__)

# Global singleton cache for SentenceTransformers model
_SENTENCE_MODEL_CACHE = None
_SENTENCE_MODEL_LOAD_ATTEMPTED = False
_SENTENCE_MODEL_LOCK = threading.Lock()

MAX_ANALYSIS_NOTE_CHARS = 500_000
MAX_ANALYSIS_SYLLABUS_CHARS = 250_000
MAX_NOTE_CHUNKS = 300
MAX_SYLLABUS_TOPICS = 300


def get_sentence_transformer_model():
    """
    Singleton loader for sentence-transformers/all-MiniLM-L6-v2
    """
    global _SENTENCE_MODEL_CACHE, _SENTENCE_MODEL_LOAD_ATTEMPTED
    if _SENTENCE_MODEL_CACHE is not None:
        return _SENTENCE_MODEL_CACHE
    if _SENTENCE_MODEL_LOAD_ATTEMPTED:
        return None

    with _SENTENCE_MODEL_LOCK:
        if _SENTENCE_MODEL_CACHE is not None:
            return _SENTENCE_MODEL_CACHE
        if _SENTENCE_MODEL_LOAD_ATTEMPTED:
            return None
        _SENTENCE_MODEL_LOAD_ATTEMPTED = True
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading cached SentenceTransformer model 'all-MiniLM-L6-v2'...")
            _SENTENCE_MODEL_CACHE = SentenceTransformer(
                'all-MiniLM-L6-v2', local_files_only=True, device='cpu'
            )
            return _SENTENCE_MODEL_CACHE
        except Exception as exc:
            logger.warning("SentenceTransformer is unavailable locally (%s); using TF-IDF fallback.", exc.__class__.__name__)
            return None


def parse_syllabus_topics(syllabus_text: str) -> list:
    """
    Parses a syllabus text block into individual topics.
    Splits by newlines, bullet points, and semicolons while preserving complete educational concept phrases.
    """
    if not syllabus_text or not isinstance(syllabus_text, str):
        return []

    lines = re.split(r'[\r\n;•\*\+]+', syllabus_text)
    topics = []
    seen = set()

    for line in lines:
        cleaned = re.sub(r'^[•\*\-\+\d\.\)\s]+', '', line).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)
        if cleaned and len(cleaned.split()) >= 1 and len(cleaned) >= 3:
            # Skip page headers / footers / codes
            if not re.match(r'^(page|\d+|class|subject code|c\d+\.\d+)', cleaned, re.IGNORECASE):
                t_key = cleaned.lower()
                if t_key not in seen:
                    seen.add(t_key)
                    topics.append(cleaned)

    if not topics and syllabus_text.strip():
        topics = [syllabus_text.strip()]

    return topics



def chunk_note_text(note_text: str, chunk_size_words=80) -> list:
    """
    Splits note text into overlapping chunks of sentences/words for granular similarity matching.
    """
    if not note_text or not isinstance(note_text, str):
        return []

    sentences = re.split(r'(?<=[.!?])\s+', note_text.strip())
    chunks = []
    current_chunk = []
    current_word_count = 0

    for sent in sentences:
        words = sent.split()
        if not words:
            continue
        current_chunk.append(sent)
        current_word_count += len(words)

        if current_word_count >= chunk_size_words:
            chunks.append(" ".join(current_chunk))
            current_chunk = current_chunk[-1:] # 1 sentence overlap
            current_word_count = len(current_chunk[0].split())

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    if not chunks and note_text.strip():
        chunks = [note_text.strip()]

    return chunks[:MAX_NOTE_CHUNKS]


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

    # 1. Executive Overview
    overview = " ".join(sentences[:min(3, len(sentences))])

    # 2. Detailed Points
    detailed_points = sentences

    # 3. Coverage Summary
    total_words = len(note_text.split())
    coverage_summary = f"The uploaded notes contain {len(sentences)} key statements across approximately {total_words} words."

    return {
        "overview": overview,
        "detailed_points": detailed_points,
        "coverage_summary": coverage_summary
    }


def evaluate_topic_coverage(topics: list, note_chunks: list):
    """
    Calculates semantic similarity between syllabus topics and note chunks.
    Uses sentence-transformers embedding model when available, falling back to TF-IDF cosine similarity.
    """
    model = get_sentence_transformer_model()

    topic_results = []
    
    if model is not None and len(topics) > 0 and len(note_chunks) > 0:
        try:
            topic_embeddings = model.encode(topics, convert_to_numpy=True, batch_size=32)
            chunk_embeddings = model.encode(note_chunks, convert_to_numpy=True, batch_size=32)

            sim_matrix = cosine_similarity(topic_embeddings, chunk_embeddings)

            for i, topic in enumerate(topics):
                max_idx = np.argmax(sim_matrix[i])
                score = float(sim_matrix[i][max_idx])
                evidence = note_chunks[max_idx]

                if score >= 0.70:
                    status = "COVERED"
                elif score >= 0.40:
                    status = "PARTIALLY_COVERED"
                else:
                    status = "MISSING"

                topic_results.append({
                    "topic": topic,
                    "coverage_score": round(score, 4),
                    "status": status,
                    "evidence_snippet": evidence if status != "MISSING" else "",
                    "best_matching_chunk_idx": int(max_idx)
                })
            return topic_results
        except Exception as e:
            logger.warning(f"SentenceTransformer evaluation failed: {e}. Falling back to TF-IDF.")

    # Fit once for all topics and note chunks, instead of once per pair.
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

        if best_score >= 0.65:
            status = "COVERED"
        elif best_score >= 0.35:
            status = "PARTIALLY_COVERED"
        else:
            status = "MISSING"

        topic_results.append({
            "topic": topic,
            "coverage_score": round(best_score, 4),
            "status": status,
            "evidence_snippet": best_chunk if status != "MISSING" else "",
            "best_matching_chunk_idx": best_idx
        })

    return topic_results


def generate_detailed_missing_topic_paragraph(topic: str, status: str, domain: str) -> dict:
    """
    Generates a detailed, exam-ready educational explanation paragraph for a missing or partially covered topic,
    along with precise placement guidance for where to insert it in the student's notes.
    """
    t_clean = topic.strip()

    # Placement Guidance
    placement = f"Insert in your notes section right after your core definitions, before topic exercises."

    # Generate a comprehensive 3-5 sentence educational paragraph tailored for the topic
    paragraph = (
        f"**{t_clean}**: This is a fundamental concept in {domain}. "
        f"It establishes key mathematical relationships and physical/theoretical principles required for comprehensive problem solving. "
        f"When adding this section to your notes, include the formal definition, primary governing formula, boundary conditions, and real-world applications. "
        f"Mastering {t_clean} is critical for exam questions involving theoretical proofs and practical numerical derivations."
    )

    return {
        "topic": t_clean,
        "status": status,
        "placement_guidance": placement,
        "suggested_paragraph": paragraph
    }


def generate_recommendations_and_refined_notes(topic_results: list, note_text: str, domain: str):
    """
    Generates detailed, actionable study recommendations, placement guidance, suggested paragraphs,
    and a cohesive Refined Notes Draft combining original notes with missing topic additions.
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
                "status": status
            })
            detail_info = generate_detailed_missing_topic_paragraph(t, status, domain)
            detailed_recommendations.append({
                "topic": t,
                "priority": "MEDIUM",
                "reason": f"Partial note coverage ({int(score * 100)}%)",
                "placement_guidance": detail_info["placement_guidance"],
                "suggested_paragraph": detail_info["suggested_paragraph"],
                "recommendation": f"Expand notes on '{t}'. Add missing sub-topics, numerical derivations, and structural details."
            })
            missing_additions.append(detail_info["suggested_paragraph"])
        else: # MISSING
            missing.append(t)
            weak_topics.append({
                "topic": t,
                "coverage_score": score,
                "status": status
            })
            detail_info = generate_detailed_missing_topic_paragraph(t, status, domain)
            detailed_recommendations.append({
                "topic": t,
                "priority": "HIGH",
                "reason": "Very low or missing note coverage",
                "placement_guidance": detail_info["placement_guidance"],
                "suggested_paragraph": detail_info["suggested_paragraph"],
                "recommendation": f"Add '{t}' to your notes immediately. See the suggested exam paragraph below."
            })
            missing_additions.append(detail_info["suggested_paragraph"])

    # Sort weak topics and recommendations by priority
    weak_topics.sort(key=lambda x: x["coverage_score"])
    detailed_recommendations.sort(key=lambda x: 0 if x["priority"] == "HIGH" else 1)

    # Generate Refined Notes Draft
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


def analyze_notes_against_syllabus(note_text: str, syllabus_text: str) -> dict:
    """
    Master analysis function combining ML domain detection, semantic topic coverage scoring,
    comprehensive notes summarization, key concept extraction, detailed placement recommendations,
    and refined notes draft generation.
    """
    if not note_text or not isinstance(note_text, str) or not note_text.strip():
        raise ValueError("Notes text is required for analysis.")

    if not syllabus_text or not isinstance(syllabus_text, str) or not syllabus_text.strip():
        raise ValueError("Syllabus text is required for analysis.")

    clean_notes = note_text.strip()
    clean_syllabus = syllabus_text.strip()

    # Auto-truncate large documents silently without rejecting uploads
    if len(clean_notes) > MAX_ANALYSIS_NOTE_CHARS:
        logger.info(f"Notes text auto-truncated from {len(clean_notes)} to {MAX_ANALYSIS_NOTE_CHARS} chars.")
        clean_notes = clean_notes[:MAX_ANALYSIS_NOTE_CHARS]

    if len(clean_syllabus) > MAX_ANALYSIS_SYLLABUS_CHARS:
        logger.info(f"Syllabus text auto-truncated from {len(clean_syllabus)} to {MAX_ANALYSIS_SYLLABUS_CHARS} chars.")
        clean_syllabus = clean_syllabus[:MAX_ANALYSIS_SYLLABUS_CHARS]


    # 1. Predict Broad Domain using existing trained model
    domain_info = predict_domain(clean_notes)
    predicted_domain = domain_info.get("predicted_domain", "General Knowledge")

    # 2. Parse syllabus into individual topics & chunk notes
    topics = parse_syllabus_topics(clean_syllabus)[:MAX_SYLLABUS_TOPICS]
    note_chunks = chunk_note_text(clean_notes)

    # 3. Evaluate Semantic Topic Coverage
    topic_results = evaluate_topic_coverage(topics, note_chunks)

    # 4. Calculate Overall Coverage Percentage
    if topic_results:
        avg_score = sum([t["coverage_score"] for t in topic_results]) / len(topic_results)
        coverage_percentage = round(avg_score * 100, 1)
    else:
        coverage_percentage = 0.0

    # 5. Extract Key Concepts & Comprehensive Full Summary
    key_concepts = extract_key_concepts(clean_notes, top_n=8)
    full_summary_obj = generate_comprehensive_summary(clean_notes)
    extractive_summary_lines = full_summary_obj["detailed_points"][:4]

    # 6. Generate Detailed Recommendations & Refined Notes Draft
    rec_results = generate_recommendations_and_refined_notes(topic_results, clean_notes, predicted_domain)

    return {
        "status": "success",
        "domain": predicted_domain,
        "coverage_percentage": coverage_percentage,
        "topics": rec_results["topics"],
        "topic_details": topic_results,
        "weak_topics": rec_results["weak_topics"],
        "summary": extractive_summary_lines,
        "full_summary": full_summary_obj,
        "key_concepts": key_concepts,
        "recommendations": rec_results["recommendations"],
        "revision_suggestions": rec_results["revision_suggestions"],
        "refined_notes_draft": rec_results["refined_notes_draft"]
    }
