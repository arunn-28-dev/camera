"""Network-backed text-to-speech helpers."""

from io import BytesIO

from gtts import gTTS


def text_to_speech(text: str, slow: bool = False) -> bytes | None:
    """Return MP3 bytes, or None when speech generation is unavailable."""
    if not text.strip():
        return None
    try:
        audio = BytesIO()
        gTTS(text=text, lang="en", slow=slow).write_to_fp(audio)
        return audio.getvalue()
    except Exception:
        return None