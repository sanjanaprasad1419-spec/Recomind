import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from api.models import Syllabus
from api.services.syllabus_service import parse_syllabus_into_units

def test_ncert_parse():
    syl = Syllabus.objects.filter(id=3).first()
    if not syl:
        print("Syllabus 3 not found.")
        return

    text = syl.extracted_text
    print(f"Extracted text length: {len(text)} chars")

    parsed = parse_syllabus_into_units(text)
    print(f"\nExtracted Chapters Count: {len(parsed)}\n")

    for idx, ch in enumerate(parsed, 1):
        print(f"{idx}. '{ch['title']}' ({len(ch['topics'])} topics)")

if __name__ == "__main__":
    test_ncert_parse()
