import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from rest_framework.test import APIClient

def test_api():
    client = APIClient()
    response = client.get('/api/syllabus/5/sections/')
    print(f"HTTP Status: {response.status_code}")
    data = response.json()
    print(f"Syllabus Title: {data.get('title')}")
    print(f"Total Sections Returned: {len(data.get('sections', []))}")
    print("\n--- SAMPLE SECTIONS FROM API ---")
    for sec in data.get('sections', [])[:5]:
        print(f"ID: '{sec.get('id')}' | Number: '{sec.get('number')}' | Title: '{sec.get('title')}' | Part: '{sec.get('part')}'")

if __name__ == "__main__":
    test_api()
