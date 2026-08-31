import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from api.services.reference_knowledge_service import get_or_create_reference_profile

def test():
    prof1 = get_or_create_reference_profile("Theory of plate tectonics", "2 — Shaping of the Earth's Surface", "Social Science Class 9")
    print("Geography Profile:", prof1)

    prof2 = get_or_create_reference_profile("Capacitance", "Electrostatics", "Physics Class 12")
    print("\nPhysics Profile:", prof2)

    assert prof1["subject_domain"] == "Geography"
    assert "Capacitance" in prof2["topic"]

    print("\nReference Knowledge Service Test Passed!")

if __name__ == "__main__":
    test()
