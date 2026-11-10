"""Task-aware prompts for grounded scene analysis."""

# HAI: Hallucination prevention (L7), uncertainty (L7, L11), and anthropomorphism control (L5).
# HAI: Unpredictability reduction (L7): require short, neutral, consistent phrasing.
SYSTEM_PROMPT = """You are an AI visual assistant. Describe only what is visible in the supplied image.
Never guess hidden, blurry, or unreadable details. If asked about something not visible,
answer exactly: "I can't see that in the current image." Put ambiguous details in
uncertain_items. Prioritize the user's current task, but identify every visible safety
hazard regardless of task. Never omit a possible hazard; prefix low-confidence hazards
with "Possible hazard:". Use a lower evidence threshold for hazards than ordinary objects;
omit ordinary objects when the image does not support them clearly. If two possibilities
are similarly likely, state that clearly.
Use short, neutral, consistent phrasing. Do not claim to be human or use emotional language.
Keep spoken-ready text concise (about 60 words unless the user asks for detail).
Safety-related observations must be cautious and ask the user to verify. You advise; the
user decides. Return only the requested JSON object and never invent visual evidence."""


def build_analysis_prompt(task: str, question: str = "", correction: str = "") -> str:
    """Build the user message for a single image analysis request."""
    parts = [f"Current user task: {task or 'General awareness'}."]
    if question:
        parts.append(f"Question about this image: {question}")
    if correction:
        parts.append(
            "The user submitted this correction: " + correction +
            " Re-check it against visible evidence; do not accept details that the image does not support."
        )
    parts.append(
        "Return hazards, a task-relevant summary, visible objects with high/medium/low confidence, "
        "readable text, a direct answer when a question was asked, a short evidence-based why, "
        "uncertainties, and one practical suggestion only when useful. For spoken audio, also "
        "transcribe the question in transcribed_question. Use an empty string when no question was asked."
    )
    return "\n".join(parts)


def build_audio_prompt(task: str) -> str:
    """Ask Gemini to transcribe and answer a spoken question against the image."""
    return (
        build_analysis_prompt(task)
        + "\nThe attached audio is the user's question. Transcribe it faithfully into "
        "transcribed_question, then answer only using visible image evidence."
    )