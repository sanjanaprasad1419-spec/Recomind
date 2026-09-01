"""Standalone Gemini service for generating syllabus-grounded study notes.

This module intentionally has no dependency on RecoMind's ML coverage analysis.
It is used only by the explicit topic-notes API in this implementation.
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except Exception:
    genai = None
    types = None
    GENAI_AVAILABLE = False


logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"


class TopicNotesGenerationError(Exception):
    """A safe, client-facing failure while generating educational notes."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class TopicNotesRequest:
    topic: str
    subject: str
    education_level: str
    chapter: str
    syllabus_context: str
    student_notes: str = ""
    reference_context: str = ""


NOTES_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "topic": {"type": "string"},
        "definition": {"type": "string"},
        "explanation": {"type": "string"},
        "formulas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "formula": {"type": "string"},
                    "explanation": {"type": "string"},
                    "variables": {"type": "string"},
                },
                "required": ["formula", "explanation", "variables"],
            },
        },
        "derivation": {"type": "array", "items": {"type": "string"}},
        "important_points": {"type": "array", "items": {"type": "string"}},
        "examples": {"type": "array", "items": {"type": "string"}},
        "diagram_guidance": {"type": "string"},
        "exam_tip": {"type": "string"},
        "quick_revision": {"type": "string"},
    },
    "required": [
        "topic", "definition", "explanation", "formulas", "derivation",
        "important_points", "examples", "diagram_guidance", "exam_tip",
        "quick_revision",
    ],
}


def _build_prompt(request: TopicNotesRequest) -> str:
    existing_notes_instruction = (
        "No student notes were provided; create complete notes for the topic."
        if not request.student_notes
        else (
            "Student notes are provided below. Preserve useful material conceptually and "
            "write only the missing or weak educational content; do not merely tell the "
            "student what to add.\n<Student notes>\n"
            f"{request.student_notes}\n</Student notes>"
        )
    )
    reference_instruction = (
        "No reference context was provided."
        if not request.reference_context
        else (
            "Use this supplied reference context only as grounding. Write original "
            "explanations; do not reproduce long passages.\n<Reference context>\n"
            f"{request.reference_context}\n</Reference context>"
        )
    )

    return f"""
You are RecoMind's educational-notes author. Generate original, accurate study notes,
not recommendations or a chat response. The notes must stay within the supplied
syllabus context and be suitable for the stated education level.

Subject: {request.subject}
Education level: {request.education_level}
Chapter: {request.chapter}
Topic: {request.topic}
Syllabus context: {request.syllabus_context}

{existing_notes_instruction}

{reference_instruction}

Return only a JSON object matching the requested schema. Populate fields with actual
educational content. Never write directives such as "add a definition", "include a
formula", or "study this topic". For technical subjects include correct formulas and
step-by-step derivations only when relevant. For non-technical subjects, use empty
arrays when formulas or derivations do not apply. Adapt naturally to the subject:
for example, biology needs biological processes rather than physics derivations, and
computer science may include operations, complexity, pseudocode or concise code where useful.
""".strip()


def _validate_notes(notes: Any, requested_topic: str) -> dict[str, Any]:
    if not isinstance(notes, dict):
        raise TopicNotesGenerationError("Gemini returned an invalid notes format.")

    for field in NOTES_SCHEMA["required"]:
        if field not in notes:
            raise TopicNotesGenerationError("Gemini returned incomplete structured notes.")

    for field in ("formulas", "derivation", "important_points", "examples"):
        if not isinstance(notes[field], list):
            raise TopicNotesGenerationError("Gemini returned invalid structured notes.")
    for field in ("topic", "definition", "explanation", "diagram_guidance", "exam_tip", "quick_revision"):
        if not isinstance(notes[field], str) or not notes[field].strip():
            raise TopicNotesGenerationError("Gemini returned incomplete structured notes.")

    # The requested topic is authoritative; this prevents a mismatched model heading.
    notes["topic"] = requested_topic
    return notes


def generate_topic_notes(
    *,
    topic: str,
    subject: str,
    education_level: str,
    chapter: str,
    syllabus_context: str,
    student_notes: str = "",
    reference_context: str = "",
) -> dict[str, Any]:
    """Generate validated, syllabus-grounded notes with Gemini 2.5 Flash."""
    request = TopicNotesRequest(
        topic=topic.strip(), subject=subject.strip(), education_level=education_level.strip(),
        chapter=chapter.strip(), syllabus_context=syllabus_context.strip(),
        student_notes=student_notes.strip(), reference_context=reference_context.strip(),
    )
    if not request.topic:
        raise TopicNotesGenerationError("topic is required.", status_code=400)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise TopicNotesGenerationError("Gemini is not configured. Set GEMINI_API_KEY on the backend.", status_code=503)

    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=30_000),
        )
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=_build_prompt(request),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=NOTES_SCHEMA,
                temperature=0.2,
                max_output_tokens=4096,
            ),
        )
        if not response.text:
            raise TopicNotesGenerationError("Gemini returned an empty response.")
        return _validate_notes(json.loads(response.text), request.topic)
    except TopicNotesGenerationError:
        raise
    except json.JSONDecodeError:
        logger.warning("Gemini returned malformed JSON for topic notes.")
        raise TopicNotesGenerationError("Gemini returned an invalid notes response.")
    except genai.errors.ClientError as exc:
        status_code = getattr(exc, "code", 502)
        if status_code == 429:
            raise TopicNotesGenerationError("Gemini is temporarily rate-limited. Please try again shortly.", status_code=429)
        logger.warning("Gemini rejected a topic-notes request: HTTP %s", status_code)
        raise TopicNotesGenerationError("Gemini could not process this request.", status_code=502)
    except genai.errors.ServerError as exc:
        logger.warning("Gemini server error: HTTP %s", getattr(exc, "code", "unknown"))
        raise TopicNotesGenerationError("Gemini is temporarily unavailable. Please try again later.", status_code=503)
    except Exception as exc:
        # Do not return provider details, which can contain operational information.
        logger.warning("Gemini topic-notes request failed: %s", exc.__class__.__name__)
        raise TopicNotesGenerationError("Unable to generate notes right now. Please try again later.")
