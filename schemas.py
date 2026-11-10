"""Gemini JSON schema and defensive response parsing."""

import json
from typing import Any


RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "hazards": {"type": "ARRAY", "items": {"type": "STRING"}},
        "summary": {"type": "STRING"},
        "objects": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "confidence": {"type": "STRING", "enum": ["high", "medium", "low"]},
                },
                "required": ["name", "confidence"],
            },
        },
        "visible_text": {"type": "ARRAY", "items": {"type": "STRING"}},
        "answer": {"type": "STRING"},
        "why": {"type": "STRING"},
        "uncertain_items": {"type": "ARRAY", "items": {"type": "STRING"}},
        "suggestion": {"type": "STRING"},
        "transcribed_question": {"type": "STRING"},
    },
    "required": [
        "hazards",
        "summary",
        "objects",
        "visible_text",
        "answer",
        "why",
        "uncertain_items",
        "suggestion",
        "transcribed_question",
    ],
}


def parse_response(response_text: str) -> dict[str, Any]:
    """Parse and normalize Gemini's JSON response."""
    data = json.loads(response_text)
    if not isinstance(data, dict):
        raise ValueError("The response must be a JSON object.")

    normalized: dict[str, Any] = {
        "hazards": _string_list(data.get("hazards")),
        "summary": _string_value(data.get("summary")),
        "objects": _parse_objects(data.get("objects")),
        "visible_text": _string_list(data.get("visible_text")),
        "answer": _string_value(data.get("answer")),
        "why": _string_value(data.get("why")),
        "uncertain_items": _string_list(data.get("uncertain_items")),
        "suggestion": _string_value(data.get("suggestion")),
        "transcribed_question": _string_value(data.get("transcribed_question")),
    }
    if not normalized["summary"]:
        raise ValueError("The response did not contain a scene summary.")
    return normalized


def _string_value(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _parse_objects(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    objects: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            continue
        confidence = str(item.get("confidence", "low")).lower()
        if confidence not in {"high", "medium", "low"}:
            confidence = "low"
        name = item["name"].strip()
        if name:
            objects.append({"name": name, "confidence": confidence})
    return objects