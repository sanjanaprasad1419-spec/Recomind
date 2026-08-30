import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from api.models import Syllabus
from api.services.syllabus_service import parse_syllabus_into_units

def reparse_all():
    syllabi = Syllabus.objects.all()
    print(f"Reparsing {len(syllabi)} syllabi in database...")
    for s in syllabi:
        if s.extracted_text:
            s.parsed_units = parse_syllabus_into_units(s.extracted_text)
            s.save()
            print(f"Updated Syllabus #{s.id} ('{s.title}') with {len(s.parsed_units)} clean sections.")

if __name__ == "__main__":
    reparse_all()
