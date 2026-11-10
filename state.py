"""Session state defaults and reset behavior."""

import streamlit as st


def initialize_state() -> None:
    """Initialize app state without overwriting user selections."""
    defaults = {
        "sg_result": None,
        "sg_latest_image": None,
        "sg_history": [],
        "sg_scan_count": 0,
        "sg_correction_count": 0,
        "sg_audio": None,
        "sg_audio_autoplay": False,
        "sg_audio_stopped": False,
        "sg_show_why": False,
        "sg_last_audio_hash": "",
        "sg_last_api_call": 0.0,
        "sg_welcome_seen": False,
        "sg_correction_open": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_session() -> None:
    """Clear scan history and counts while preserving sidebar preferences."""
    for key in (
        "sg_result",
        "sg_latest_image",
        "sg_history",
        "sg_scan_count",
        "sg_correction_count",
        "sg_audio",
        "sg_audio_autoplay",
        "sg_audio_stopped",
        "sg_show_why",
        "sg_last_audio_hash",
        "sg_last_api_call",
        "sg_welcome_seen",
        "sg_correction_open",
    ):
        st.session_state.pop(key, None)
    initialize_state()