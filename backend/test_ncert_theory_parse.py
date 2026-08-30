import os
import re
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from api.models import Syllabus

def clean_text_formatting(text):
    if not text:
        return ""
    # Replace unicode replacement characters, en-dashes, em-dashes
    text = text.replace('\ufffd', '-').replace('\u2013', '-').replace('\u2014', '-').replace('\u2019', "'")
    # Fix multiple dashes/spaces
    text = re.sub(r'[\-\s]+\:\s*', ': ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_ncert_theory_chapters(syllabus_text):
    if not syllabus_text:
        return []

    lines = [line.strip() for line in syllabus_text.splitlines() if line.strip()]
    chapters = []
    current_ch = None
    seen_titles = set()

    # Pattern for genuine theory chapters: "Chapter 1: Electric Charges...", "Chapter-1: ...", "Chapter 1 - ..."
    ch_pattern = re.compile(
        r'^(?:unit\s*[\d\wIVXLCDM\-\:]+\s*)?chapter\s*[\-\:\s]*(\d+)\s*[\-\:\s]*(.*)$',
        re.IGNORECASE
    )

    # Keywords that indicate practicals/evaluations to ignore as chapter headers
    practical_keywords = ['to measure', 'to determine', 'to study', 'to verify', 'to observe', 'to find', 'to draw', 'to assemble', 'to design', 'list of practicals', 'evaluation scheme', 'section-a', 'section-b', 'prescribed books']

    for line in lines:
        line_clean = clean_text_formatting(line)
        line_lower = line_clean.lower()

        # Skip practical experiment lines as chapter headers
        if any(p_kw in line_lower for p_kw in practical_keywords):
            if current_ch and len(line_clean.split()) >= 3:
                current_ch["topics"].append(line_clean)
            continue

        match = ch_pattern.match(line_clean)

        is_chapter = False
        ch_num = ""
        ch_name = ""

        if match:
            c_num, c_name = match.groups()
            ch_num = c_num.strip()
            ch_name = c_name.strip()
            # Clean leading dashes/colons from name
            ch_name = re.sub(r'^[\:\-\s]+', '', ch_name).strip()
            if ch_name:
                is_chapter = True
        elif len(line_clean) < 60 and 'chapter' in line_lower and any(c.isdigit() for c in line_clean):
            parts = re.split(r'chapter\s*(\d+)[:\-\s]*', line_clean, flags=re.IGNORECASE)
            if len(parts) >= 3:
                ch_num = parts[1].strip()
                ch_name = parts[2].strip()
                if ch_name:
                    is_chapter = True

        if is_chapter:
            formatted_title = f"Chapter {ch_num} \u2014 {ch_name}"

            if current_ch and current_ch["topics"]:
                chapters.append(current_ch)

            current_ch = {
                "unit_id": f"chapter_{ch_num}_{len(chapters)+1}",
                "title": formatted_title,
                "topics": []
            }
        else:
            if current_ch is not None:
                cleaned_topic = re.sub(r'^[•\*\-\+\d\.\)\s]+', '', line_clean).strip()
                if cleaned_topic and len(cleaned_topic.split()) >= 2 and len(cleaned_topic) >= 4:
                    current_ch["topics"].append(cleaned_topic)

    if current_ch and current_ch["topics"]:
        chapters.append(current_ch)

    return chapters

def test():
    syl = Syllabus.objects.filter(id=3).first()
    if not syl:
        print("Syllabus 3 not found.")
        return

    chapters = parse_ncert_theory_chapters(syl.extracted_text)
    print(f"Total Theory Chapters Found: {len(chapters)}\n")
    for idx, c in enumerate(chapters, 1):
        print(f"{idx}. {c['title']} ({len(c['topics'])} topics)")

if __name__ == "__main__":
    test()
