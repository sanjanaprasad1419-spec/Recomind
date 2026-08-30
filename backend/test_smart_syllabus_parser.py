import os
import re
import pypdf

def clean_str(s):
    if not s:
        return ""
    s = s.replace('\xa0', ' ').replace('\ufffd', '-').replace('\u2013', '-').replace('\u2014', '-')
    s = re.sub(r'[\s\t]+', ' ', s)
    return s.strip()

def normalize_concept_lines(raw_lines):
    cleaned_topics = []
    current_phrase = []

    for line in raw_lines:
        line = line.strip()
        if not line:
            continue

        is_new_concept = (
            line.startswith('•') or 
            line.startswith('-') or 
            re.match(r'^\d+[\.\)]', line) or
            ';' in line
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

    unique_topics = []
    seen = set()
    for t in cleaned_topics:
        t_key = t.lower()
        if t_key not in seen and len(t) >= 3:
            seen.add(t_key)
            unique_topics.append(t)

    return unique_topics

def parse_syllabus(pdf_path):
    reader = pypdf.PdfReader(pdf_path)
    full_text_lines = []

    for page in reader.pages:
        txt = page.extract_text() or ""
        for line in txt.splitlines():
            cl = clean_str(line)
            if cl:
                full_text_lines.append(cl)

    start_idx = 0
    for idx, line in enumerate(full_text_lines):
        if 'course outline' in line.lower():
            start_idx = idx
            break

    relevant_lines = full_text_lines[start_idx:] if start_idx > 0 else full_text_lines

    sections = []
    current_part = "Part 1"
    
    part_pattern = re.compile(r'^(part\s*[\d\wIVX]+|section\s*[\d\wA-Z]+|class\s*[\d\wIXV]+)', re.IGNORECASE)
    theme_start_pattern = re.compile(r'^(?:chapter\s*(\d+)[\:\.\-]*\s*|(\d+)[\.\)]\s+)(.*)$', re.IGNORECASE)

    learning_outcome_keywords = [
        'learning outcomes', 'pertinent', 'cgs, cs', 'students will be able to:',
        'explain how', 'describe how', 'understand the', 'analyse how', 'identify',
        'categorise', 'differentiate', 'appreciate', 'explore the', 'recognise',
        'illustrate', 'construct', 'use of', 's. no.', 'theme (time', 'outline/concepts',
        'hours)', 'unit-i', 'unit-ii'
    ]

    i = 0
    N = len(relevant_lines)
    raw_topic_buffers = {}

    while i < N:
        line = relevant_lines[i]
        line_lower = line.lower()

        if part_pattern.match(line) and len(line) < 35:
            current_part = line.strip()
            i += 1
            continue

        match = theme_start_pattern.match(line)
        if match:
            c1, c2, rest = match.groups()
            num = c1 or c2

            title_parts = [rest]
            j = i + 1
            
            while j < N:
                next_line = relevant_lines[j]
                next_lower = next_line.lower()

                if part_pattern.match(next_line) or theme_start_pattern.match(next_line):
                    break
                if re.match(r'^c\d+\.\d+', next_lower):
                    break
                if any(lo in next_lower for lo in ['students will be able', 'learning outcomes', 'cgs, cs']):
                    break

                if re.search(r'\(\d+\s*hours?\)', next_line, re.IGNORECASE):
                    title_parts.append(next_line)
                    j += 1
                    break
                
                if next_line.startswith('•') or next_line.startswith('-') or '  ' in next_line:
                    break

                if len(next_line) < 45 and not next_line.endswith('.') and not any(k in next_lower for k in ['explain', 'describe', 'understand', 'analyse', 'identify', 'categorise', 'differentiate']):
                    title_parts.append(next_line)
                    j += 1
                else:
                    break

            raw_title = " ".join(title_parts)
            clean_title = re.sub(r'\(\d+\s*hours?\)', '', raw_title, flags=re.IGNORECASE).strip()
            
            concept_split = re.split(r'[\•\-\:]', clean_title, maxsplit=1)
            theme_name = concept_split[0].strip()
            theme_name = re.sub(r'^\d+[\.\)]\s*', '', theme_name).strip()

            if theme_name and len(theme_name.split()) >= 1:
                part_slug = re.sub(r'[^a-zA-Z0-9]', '', current_part.lower())
                if not part_slug:
                    part_slug = "part1"

                theme_idx = len([s for s in sections if s["part"] == current_part]) + 1
                unique_id = f"{part_slug}-theme{num or theme_idx}"

                display_label = f"{num} \u2014 {theme_name}"

                current_theme = {
                    "id": unique_id,
                    "number": str(num or theme_idx),
                    "name": theme_name,
                    "title": display_label,
                    "part": current_part,
                    "topics": []
                }
                sections.append(current_theme)
                raw_topic_buffers[unique_id] = []

                if len(concept_split) > 1 and concept_split[1].strip():
                    raw_topic_buffers[unique_id].append(concept_split[1].strip())

                i = j
                continue

        if sections:
            curr = sections[-1]
            curr_id = curr["id"]
            is_lo = any(lo_kw in line_lower for lo_kw in learning_outcome_keywords) or re.match(r'^c\d+\.\d+', line_lower) or re.match(r'^\d+\s*$', line_lower)
            
            if not is_lo and len(line) >= 3 and not line.endswith(' Hours)'):
                if not re.match(r'^(page|\d+|class|subject code)', line, re.IGNORECASE):
                    raw_topic_buffers[curr_id].append(line)

        i += 1

    # Normalize concept lines for each section
    for s in sections:
        s_id = s["id"]
        raw_list = raw_topic_buffers.get(s_id, [])
        s["topics"] = normalize_concept_lines(raw_list)

    return sections

def main():
    pdf_path = r'C:\Users\a\OneDrive\Desktop\NotesEnhancer\backend\media\syllabi\SocialScience_SecP1IX_2026-27.pdf'
    sections = parse_syllabus(pdf_path)

    print("==========================================================================")
    print(f"      Extracted Syllabus Sections ({len(sections)} Total Themes Found)     ")
    print("==========================================================================")

    for idx, s in enumerate(sections, 1):
        print(f"\n{idx}. [{s['id']}] Part: '{s['part']}' | Display Label: '{s['title']}'")
        print(f"   Theme Name: '{s['name']}' | Concepts Count: {len(s['topics'])}")
        print(f"   Concepts: {s['topics'][:6]}")

    print("\n==========================================================================")

if __name__ == "__main__":
    main()
