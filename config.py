"""Shared SightGuide settings."""

MODEL_NAME = "gemini-2.5-flash"
MAX_IMAGE_SIDE = 1024
JPEG_QUALITY = 85
API_COOLDOWN_SECONDS = 2.0

TASK_OPTIONS = (
    "General awareness",
    "Finding the exit",
    "Reading signs/labels",
    "Finding an object",
    "Checking surroundings for safety",
    "Shopping/identifying products",
    "Custom task",
)
DEFAULT_TASK = TASK_OPTIONS[0]

WELCOME_MESSAGE = (
    "I'm an AI assistant. I can describe scenes, identify objects, read visible text, "
    "and answer questions about what the camera sees. I may miss small, blurry, or "
    "poorly lit objects, so please don't rely on me alone for safety-critical decisions."
)

SAFETY_TASKS = {"Finding the exit", "Checking surroundings for safety"}