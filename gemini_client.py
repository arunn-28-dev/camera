"""All Gemini requests and image preparation for SightGuide."""

import os
import time
from io import BytesIO
from typing import Any

import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

from config import API_COOLDOWN_SECONDS, JPEG_QUALITY, MAX_IMAGE_SIDE, MODEL_NAME
from prompts import SYSTEM_PROMPT, build_analysis_prompt, build_audio_prompt
from schemas import RESPONSE_SCHEMA, parse_response


class GeminiRequestError(RuntimeError):
    """A friendly, user-displayable Gemini request failure."""


def prepare_image(image_bytes: bytes) -> bytes:
    """Resize an image to at most 1024px on a side and encode it as JPEG."""
    if not image_bytes:
        raise GeminiRequestError("No camera image was provided. Take a snapshot and try again.")
    try:
        with Image.open(BytesIO(image_bytes)) as source:
            image = source.convert("RGB")
            image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
            output = BytesIO()
            image.save(output, format="JPEG", quality=JPEG_QUALITY, optimize=True)
            return output.getvalue()
    except Exception as error:
        raise GeminiRequestError("The camera image could not be read. Please take another snapshot.") from error


def analyze_image(
    image_bytes: bytes,
    task: str,
    question: str = "",
    correction: str = "",
) -> dict[str, Any]:
    """Analyze one frame, retrying once if the response JSON is invalid."""
    jpeg_bytes = prepare_image(image_bytes)
    prompt = build_analysis_prompt(task, question, correction)
    contents: list[Any] = [prompt, types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg")]
    return _request_and_parse(contents)


def answer_audio_question(image_bytes: bytes, task: str, audio_bytes: bytes) -> dict[str, Any]:
    """Transcribe a recorded question and answer it using the current image."""
    if not audio_bytes:
        raise GeminiRequestError("No audio was recorded. Try the microphone again or type your question.")
    jpeg_bytes = prepare_image(image_bytes)
    prompt = build_audio_prompt(task)
    contents: list[Any] = [
        prompt,
        types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg"),
        types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
    ]
    return _request_and_parse(contents)


def _request_and_parse(contents: list[Any]) -> dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise GeminiRequestError("GEMINI_API_KEY is missing. Add it to sightguide/.env and restart the app.")

    try:
        client = genai.Client(api_key=api_key)
    except Exception as error:
        raise GeminiRequestError("Gemini could not be initialized. Check your API key and network connection.") from error

    for attempt in range(2):
        response = _generate(client, contents)
        response_text = response.text or ""
        try:
            return parse_response(response_text)
        except (ValueError, TypeError) as error:
            if attempt == 1:
                raise GeminiRequestError(
                    "Gemini returned unreadable scene data twice. Please scan again."
                ) from error
            contents = contents + [
                "Your previous response was not valid for the required JSON schema. "
                "Return one complete JSON object matching the schema exactly."
            ]
    raise GeminiRequestError("Gemini could not analyze this image. Please try again.")


def _generate(client: genai.Client, contents: list[Any]) -> Any:
    """Apply the per-session cooldown and make one guarded model call."""
    elapsed = time.monotonic() - float(st.session_state.get("sg_last_api_call", 0.0))
    remaining = API_COOLDOWN_SECONDS - elapsed
    if remaining > 0:
        time.sleep(remaining)
    st.session_state["sg_last_api_call"] = time.monotonic()
    try:
        return client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
            ),
        )
    except Exception as error:
        detail = str(error).lower()
        if "429" in detail or "resource_exhausted" in detail or "rate" in detail:
            message = "Gemini's free-tier limit was reached. Wait a moment, then try again."
        elif "connection" in detail or "network" in detail or "timeout" in detail:
            message = "Gemini could not be reached. Check your internet connection and try again."
        elif "api key" in detail or "unauthenticated" in detail or "permission" in detail:
            message = "Gemini rejected the API key. Check GEMINI_API_KEY in sightguide/.env."
        else:
            message = "Gemini could not analyze the image. Please try again in a moment."
        raise GeminiRequestError(message) from error