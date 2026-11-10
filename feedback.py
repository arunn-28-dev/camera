"""Append text-only user corrections to the local JSONL log."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# HAI: Human-centred feedback loop (L8): preserve user corrections as text-only records.
def log_correction(task: str, original_output: dict[str, Any], correction: str) -> None:
    """Write a correction record; image data is intentionally never logged."""
    path = Path(__file__).parent / "logs" / "corrections.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task": task,
        "original_output": original_output,
        "user_correction": correction,
    }
    with path.open("a", encoding="utf-8") as correction_file:
        correction_file.write(json.dumps(record, ensure_ascii=True) + "\n")