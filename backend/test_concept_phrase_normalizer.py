import re

def normalize_concept_lines(raw_topics):
    cleaned_topics = []
    current_phrase = []

    for line in raw_topics:
        line = line.strip()
        if not line:
            continue

        # Check if line starts a new concept (bullet point, number, capital letter after punctuation)
        is_new_concept = (
            line.startswith('•') or 
            line.startswith('-') or 
            re.match(r'^\d+[\.\)]', line) or
            line.startswith('C1.') or line.startswith('C2.') or line.startswith('C3.') or line.startswith('C4.') or line.startswith('C5.')
        )

        cl = re.sub(r'^[•\*\-\+\d\.\)\s]+', '', line).strip()

        if is_new_concept:
            if current_phrase:
                full_p = " ".join(current_phrase).strip()
                full_p = re.sub(r'\s+', ' ', full_p)
                if len(full_p.split()) >= 1 and len(full_p) >= 3:
                    cleaned_topics.append(full_p)
                current_phrase = []
            if cl:
                current_phrase.append(cl)
        else:
            # Continuation of previous phrase
            if current_phrase:
                current_phrase.append(cl)
            else:
                if cl:
                    current_phrase.append(cl)

    if current_phrase:
        full_p = " ".join(current_phrase).strip()
        full_p = re.sub(r'\s+', ' ', full_p)
        if len(full_p.split()) >= 1 and len(full_p) >= 3:
            cleaned_topics.append(full_p)

    # Deduplicate while preserving order
    unique_topics = []
    seen = set()
    for t in cleaned_topics:
        t_key = t.lower()
        if t_key not in seen and len(t) >= 3:
            seen.add(t_key)
            unique_topics.append(t)

    return unique_topics
