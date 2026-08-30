import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from api.models import Syllabus
from api.services.syllabus_service import parse_syllabus_into_units

def test():
    s = Syllabus.objects.get(id=5)
    sections = parse_syllabus_into_units(s.extracted_text)
    print(f"=================== Extracted {len(sections)} Themes ===================")
    for idx, sec in enumerate(sections, 1):
        print(f"{idx}. [{sec['id']}] Part: '{sec['part']}' | Label: '{sec['title']}' | Topics: {len(sec['topics'])}")
        print(f"   Topics Sample: {sec['topics'][:2]}")

if __name__ == "__main__":
    test()
