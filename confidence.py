"""Consistent confidence labels for visual object detections."""

# HAI: Communicating confidence five ways (L11): numeric, verbal, badge, range, and explicit text.
CONFIDENCE_STYLES = (
    "Qualitative badge",
    "Numeric estimate",
    "Verbal phrase",
    "Confidence range",
    "Explicit uncertainty",
)

_PRESENTATIONS = {
    "high": {
        "label": "High",
        "numeric": "High (~90%)",
        "verbal": "I'm fairly sure",
        "range": "Between 80% and 95% sure",
        "explicit": "High confidence; still verify important details.",
        "css": "high",
    },
    "medium": {
        "label": "Medium",
        "numeric": "Medium (~65%)",
        "verbal": "I think",
        "range": "Between 50% and 80% sure",
        "explicit": "Some uncertainty remains; please verify.",
        "css": "medium",
    },
    "low": {
        "label": "Low",
        "numeric": "Low (~35%)",
        "verbal": "I'm not sure",
        "range": "Between 20% and 50% sure",
        "explicit": "Low confidence; this may be incorrect.",
        "css": "low",
    },
}


def confidence_display(confidence: str, style: str) -> tuple[str, str]:
    """Return a confidence phrase and its qualitative style class."""
    level = confidence.lower() if confidence.lower() in _PRESENTATIONS else "low"
    presentation = _PRESENTATIONS[level]
    labels = {
        "Qualitative badge": "label",
        "Numeric estimate": "numeric",
        "Verbal phrase": "verbal",
        "Confidence range": "range",
        "Explicit uncertainty": "explicit",
    }
    return str(presentation[labels.get(style, "label")]), str(presentation["css"])