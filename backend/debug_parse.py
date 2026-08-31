import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from api.services.syllabus_service import parse_syllabus_into_units, clean_text_formatting
import re

def debug():
    s = """Chapter 1 - Electric Charges and Fields
1.1 Electric Charge
1.2 Coulomb's Law
Chapter 02: Electrostatic Potential and Capacitance
2.1 Potential Difference
CHAPTER III: Current Electricity
3.1 Drift Velocity
4. Moving Charges and Magnetism
4.1 Lorentz Force
5 Magnetism and Matter
5.1 Bar Magnet"""

    explicit_chapter_pattern = re.compile(
        r'^\s*\b(?:chapter|ch|theme|module|unit)\b[\s\-:#]*(\d+|[IVXLCDM]+)\s*(?:[:\-\.\u2013\u2014])?\s*(.+)?$',
        re.IGNORECASE
    )
    numbered_chapter_pattern = re.compile(
        r'^\s*(\d{1,2})(?:[\.\)\-\:\u2013\u2014]|\s+)(?!\d)\s*([A-Za-z][A-Za-z0-9\s,\-\'\(\)]+)$'
    )

    lines = [clean_text_formatting(l) for l in s.splitlines()]
    for idx, l in enumerate(lines):
        m_exp = explicit_chapter_pattern.match(l)
        m_num = numbered_chapter_pattern.match(l)
        print(f"Line {idx+1}: '{l}' | MatchExp: {bool(m_exp)} | MatchNum: {bool(m_num)}")

if __name__ == "__main__":
    debug()
