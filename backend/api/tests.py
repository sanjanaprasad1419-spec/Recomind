from django.test import TestCase

import os
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIClient

from api.services.syllabus_service import parse_syllabus_into_units


VALID_NOTES = {
    "topic": "ignored by service",
    "definition": "A spherical shell has charge spread uniformly over its surface.",
    "explanation": "Gauss's law gives zero field inside and an inverse-square field outside.",
    "formulas": [{"formula": "E = Q/(4 pi epsilon_0 r^2)", "explanation": "For r > R.", "variables": "Q is charge; r is distance."}],
    "derivation": ["Choose a concentric Gaussian sphere.", "Apply Gauss's law."],
    "important_points": ["The field inside is zero."],
    "examples": ["At r less than R, E equals zero."],
    "diagram_guidance": "Draw the shell and concentric Gaussian surfaces.",
    "exam_tip": "State the enclosed charge before applying Gauss's law.",
    "quick_revision": "Inside: zero. Outside: kQ/r^2.",
}


class GenerateTopicNotesTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()
        self.payload = {
            "topic": "Uniformly Charged Thin Spherical Shell - Field Inside and Outside",
            "subject": "Physics",
            "education_level": "Class 12",
            "chapter": "Electric Charges and Fields",
            "syllabus_context": "Gauss's theorem applied to a uniformly charged thin spherical shell.",
        }

    @patch("api.views.generate_topic_notes", return_value=VALID_NOTES)
    def test_returns_structured_actual_notes(self, generate_notes):
        response = self.client.post("/api/generate-topic-notes/", self.payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertIn("definition", response.data["notes"])
        self.assertNotIn("topic", response.data["notes"])
        generate_notes.assert_called_once()

    def test_rejects_blank_topic(self):
        response = self.client.post("/api/generate-topic-notes/", {"topic": "   "}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("topic", response.data)

    @patch.dict(os.environ, {"GEMINI_API_KEY": ""})
    def test_reports_missing_backend_key_without_leaking_it(self):
        response = self.client.post("/api/generate-topic-notes/", self.payload, format="json")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["status"], "error")
        self.assertNotIn("GEMINI_API_KEY=", response.data["error"])


class SyllabusChapterParsingTests(SimpleTestCase):
    def test_extracts_all_chapters_without_promoting_subtopics(self):
        syllabus = """
        Chapter 1 - Electric Charges and Fields
        1.1 Electric Charge
        1.2 Coulomb's Law
        Chapter 02: Electrostatic Potential and Capacitance
        2.1 Potential Difference
        CHAPTER III: Current Electricity
        3.1 Drift Velocity
        4. Moving Charges and Magnetism
        4.1 Lorentz Force
        5 Magnetism and Matter
        5.1 Bar Magnet
        """
        chapters = parse_syllabus_into_units(syllabus)

        self.assertEqual(len(chapters), 5)
        self.assertEqual([chapter["number"] for chapter in chapters], ["1", "02", "III", "4", "5"])
        self.assertEqual(chapters[0]["name"], "Electric Charges and Fields")
        self.assertEqual(chapters[3]["name"], "Moving Charges and Magnetism")
        self.assertIn("Electric Charge", chapters[0]["topics"])
        self.assertNotIn("Chapter 1 — General Syllabus Topics", [chapter["title"] for chapter in chapters])

    def test_returns_no_fake_chapter_when_headings_are_not_present(self):
        chapters = parse_syllabus_into_units("Electric charge\nCoulomb's law\nElectric field")
        self.assertEqual(chapters, [])

    def test_extracts_a_heading_split_across_two_lines(self):
        chapters = parse_syllabus_into_units("Chapter 1\nElectric Charges and Fields\nElectric charge\n")
        self.assertEqual(chapters[0]["title"], "Chapter 1 — Electric Charges and Fields")
        self.assertIn("Electric charge", chapters[0]["topics"])


class NotesAnalysisTests(SimpleTestCase):
    @patch("api.services.notes_analyzer.get_sentence_transformer_model", return_value=None)
    def test_analyze_notes_returns_a_complete_response_for_larger_input(self, _get_model):
        notes = ("Electric charge produces an electric field. Coulomb's law gives force between charges. " * 300)
        response = APIClient().post(
            "/api/analyze-notes/",
            {
                "note_text": notes,
                "syllabus_text": "Electric Charge\nCoulomb's Law\nElectric Field",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertIn("coverage_percentage", response.data)
        self.assertIn("topics", response.data)
        self.assertIn("recommendations", response.data)
