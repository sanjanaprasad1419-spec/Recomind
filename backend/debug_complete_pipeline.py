import os
import django
import numpy as np

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from api.models import Note, Syllabus
from api.services.notes_analyzer import get_sentence_transformer_model, chunk_note_text, parse_syllabus_topics, evaluate_topic_coverage, analyze_notes_against_syllabus
from api.services.domain_predictor import predict_domain
from sklearn.metrics.pairwise import cosine_similarity

def debug_pipeline():
    print("==========================================================================")
    print("           STEP 1: COMPLETE PIPELINE DIAGNOSTIC TRACE LOG                 ")
    print("==========================================================================")

    # 1. Fetch Syllabus #5 (SocialScience SecP1IX 2026 27) and Chapter 2
    syl = Syllabus.objects.get(id=5)
    print(f"3. Selected Syllabus ID: {syl.id} ('{syl.title}')")
    
    parsed_units = syl.parsed_units or []
    target_unit = None
    for u in parsed_units:
        if u.get('id') == 'part1-theme2' or u.get('unit_id') == 'part1-theme2':
            target_unit = u
            break

    if not target_unit and parsed_units:
        target_unit = parsed_units[1] # Theme 2

    print(f"4. Selected Chapter ID: {target_unit.get('id') or target_unit.get('unit_id')}")
    print(f"5. Selected Chapter Title: {target_unit.get('title')}")
    
    topics = target_unit.get('topics', [])
    print(f"6. Number of Extracted Topics: {len(topics)}")
    print("7. Exact Topic Strings:")
    for idx, t in enumerate(topics, 1):
        print(f"   [{idx}] {t}")

    # 2. Test Note Text
    sample_geography_notes = """
    Chapter 2 — Shaping of the Earth's Surface:
    The Theory of Plate Tectonics explains the movement of Earth's lithospheric plates across the asthenosphere.
    The lithosphere is broken into major plates such as Pacific, Eurasian, African, and Indo-Australian plates.
    Interior of the Earth consists of three distinct layers: the crust, mantle, and core (outer and inner core).
    Weathering and erosion are exogenic geomorphic processes that continuously shape landforms.
    Weathering breaks rocks into smaller fragments, while erosion transports sediment downstream.
    Agents of gradation — running water (rivers), sea waves, wind action, glaciers, and underground water.
    Rivers form V-shaped valleys, waterfalls, and deltas. Glaciers carve U-shaped valleys and cirques.
    Geological hazards and natural disasters include earthquakes, landslides, avalanches, and Glacial Lake Outburst Floods (GLOF).
    """

    print(f"\n1. Note Text Length: {len(sample_geography_notes)} characters")
    print(f"2. Note Text First 500 Chars:\n{sample_geography_notes[:500]}")

    note_passages = chunk_note_text(sample_geography_notes)
    print(f"\n8. Number of Note Passages/Chunks: {len(note_passages)}")

    # 3. SentenceTransformer Model Check
    model = get_sentence_transformer_model()
    print(f"9. SentenceTransformer Model Loaded: {model is not None}")

    if model:
        topic_emb = model.encode(topics, convert_to_numpy=True)
        chunk_emb = model.encode(note_passages, convert_to_numpy=True)
        
        print(f"10. Topic Embeddings Shape: {topic_emb.shape}")
        print(f"    Chunk Embeddings Shape: {chunk_emb.shape}")

        sim_mat = cosine_similarity(topic_emb, chunk_emb)
        print(f"11. Similarity Matrix Dimensions: {sim_mat.shape}")
        print(f"12. Minimum Similarity: {float(np.min(sim_mat)):.4f}")
        print(f"13. Maximum Similarity: {float(np.max(sim_mat)):.4f}")
        print(f"14. Mean Similarity: {float(np.mean(sim_mat)):.4f}")

        print("\n15 & 16. Topic -> Best Similarity Score & Assigned Status:")
        eval_results = evaluate_topic_coverage(topics, note_passages)
        for res in eval_results:
            print(f"   • Topic: '{res['topic'][:45]}...'")
            print(f"     Score: {res['coverage_score']} | Status: {res['status']}")
            if res['evidence_snippet']:
                print(f"     Evidence Snippet: '{res['evidence_snippet'][:80]}...'")

    # 4. Domain Check
    dom_res = predict_domain(sample_geography_notes)
    print(f"\nDomain Classifier Output: {dom_res}")

    # 5. Master Analysis Check
    master_res = analyze_notes_against_syllabus(sample_geography_notes, "\n".join(topics))
    print(f"\nMaster Analysis Coverage Score: {master_res['coverage_percentage']}%")
    print(f"Covered Topics ({len(master_res['topics']['covered'])}): {master_res['topics']['covered']}")
    print(f"Partially Covered Topics ({len(master_res['topics']['partially_covered'])}): {master_res['topics']['partially_covered']}")
    print(f"Missing Topics ({len(master_res['topics']['missing'])}): {master_res['topics']['missing']}")

if __name__ == "__main__":
    debug_pipeline()
