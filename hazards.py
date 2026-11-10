"""Deterministic hazard phrasing and speech ordering."""

from collections.abc import Iterable


# HAI: False positives vs false negatives (L7): mark uncertain hazards but never filter them.
def format_hazards(hazards: Iterable[str], uncertain_items: Iterable[str]) -> list[dict[str, str | bool]]:
    """Keep every reported hazard and mark items that also appear uncertain."""
    uncertain_text = " ".join(item.lower() for item in uncertain_items)
    found: list[dict[str, str | bool]] = []
    seen: set[str] = set()
    for hazard in hazards:
        name = hazard.strip()
        key = name.casefold()
        if not name or key in seen:
            continue
        seen.add(key)
        is_uncertain = key in uncertain_text or "possible" in name.casefold()
        display_name = name
        if is_uncertain:
            for prefix in ("possible hazard:", "possible hazard", "possible"):
                if display_name.casefold().startswith(prefix):
                    display_name = display_name[len(prefix):].lstrip(" :")
                    break
        found.append({"name": display_name or name, "uncertain": is_uncertain})
    return found


# HAI: Use deterministic code where AI isn't needed (L8): order and phrase hazards in Python.
def spoken_result(
    hazards: list[dict[str, str | bool]],
    summary: str,
    answer: str,
    uncertain_items: Iterable[str],
    safety_task: bool,
) -> str:
    """Compose spoken content in hazard-first order."""
    parts: list[str] = []
    for hazard in hazards:
        name = str(hazard["name"])
        if hazard["uncertain"]:
            parts.append(f"Possible hazard: {name}. Please verify before moving.")
        else:
            parts.append(f"Hazard detected: {name}. Please verify before moving.")
    if summary:
        lead = "Please verify: " if safety_task else ""
        parts.append(lead + summary)
    if answer:
        parts.append(answer)
    uncertain = list(uncertain_items)
    if uncertain:
        parts.append("Some details are uncertain: " + "; ".join(uncertain[:3]) + ".")
    return " ".join(parts)