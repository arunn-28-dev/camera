"""SightGuide: a camera-based human-AI assistant."""

import hashlib
from html import escape
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from streamlit_mic_recorder import mic_recorder

from config import DEFAULT_TASK, SAFETY_TASKS, TASK_OPTIONS, WELCOME_MESSAGE
from confidence import CONFIDENCE_STYLES, confidence_display
from feedback import log_correction
from gemini_client import GeminiRequestError, analyze_image, answer_audio_question
from hazards import format_hazards, spoken_result
from speech import text_to_speech
from state import initialize_state, reset_session


st.set_page_config(page_title="SightGuide", page_icon="👁️", layout="wide")
load_dotenv()
initialize_state()

st.markdown(
    """
    <style>
    :root {
        --sg-blue: #2563EB;
        --sg-green: #16A34A;
        --sg-amber: #D97706;
        --sg-red: #DC2626;
        --sg-ink: #0F172A;
        --sg-muted: #64748B;
        --sg-border: #E2E8F0;
        --sg-surface: #FFFFFF;
    }
    html, body, [class*="css"] { font-size: 16px; }
    .stApp { background: #F8FAFC; color: var(--sg-ink); }
    .block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1440px; }
    .sg-header { display:flex; align-items:center; gap:12px; margin-bottom:2px; }
    .sg-header h1 { font-size:2rem; line-height:1.15; margin:0; color:var(--sg-ink); }
    .sg-ai { color:#1D4ED8; background:#EFF6FF; border:1px solid #BFDBFE; border-radius:999px; padding:4px 10px; font-size:14px; font-weight:650; }
    .sg-tagline { color:var(--sg-muted); margin:4px 0 18px 0; }
    .sg-card { background:var(--sg-surface); border:1px solid var(--sg-border); border-radius:14px; padding:18px 20px; box-shadow:0 1px 3px rgba(15,23,42,0.08); margin:8px 0 16px; }
    .sg-welcome { border-left:4px solid var(--sg-blue); }
    .sg-hazard { background:#FEF2F2; border:1px solid var(--sg-red); border-radius:14px; padding:16px 18px; margin:8px 0 16px; color:#7F1D1D; }
    .sg-hazard strong { color:#991B1B; }
    .sg-confidence { display:inline-block; padding:2px 9px; border-radius:999px; font-size:14px; font-weight:650; white-space:nowrap; }
    .sg-confidence.high { color:#166534; background:#DCFCE7; }
    .sg-confidence.medium { color:#92400E; background:#FEF3C7; }
    .sg-confidence.low { color:#991B1B; background:#FEE2E2; }
    .sg-object { display:flex; justify-content:space-between; align-items:center; gap:12px; border-bottom:1px solid #F1F5F9; padding:9px 0; }
    .sg-object:last-child { border-bottom:0; }
    .sg-muted { color:var(--sg-muted); }
    div.stButton > button { min-height:44px; font-weight:600; }
    button[kind="primary"] { background:var(--sg-blue); }
    @media (max-width: 700px) {
        .block-container { padding:1rem 1rem 2rem; }
        .sg-header { flex-wrap:wrap; }
        .sg-header h1 { font-size:1.75rem; }
        .sg-card { padding:15px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def current_task() -> str:
    """Resolve the selected or custom task."""
    choice = st.session_state.get("task_choice", DEFAULT_TASK)
    if choice == "Custom task":
        return st.session_state.get("custom_task", "").strip() or "General awareness"
    return choice


def store_result(result: dict[str, Any], task: str, action: str) -> None:
    """Cache a result and build its matching spoken output."""
    # HAI: Use deterministic code where AI isn't needed (L8): sort and count results locally.
    confidence_order = {"high": 0, "medium": 1, "low": 2}
    result["objects"].sort(
        key=lambda item: (confidence_order.get(item["confidence"], 2), item["name"].casefold())
    )
    result["hazard_details"] = format_hazards(result["hazards"], result["uncertain_items"])
    result["task"] = task
    result["action"] = action
    result["spoken_text"] = spoken_result(
        result["hazard_details"],
        result["summary"],
        result["answer"],
        result["uncertain_items"],
        task in SAFETY_TASKS,
    )
    st.session_state["sg_result"] = result
    st.session_state["sg_history"].append(
        {"task": task, "action": action, "summary": result["summary"], "answer": result["answer"]}
    )
    if st.session_state.get("voice_enabled", True):
        st.session_state["sg_audio"] = text_to_speech(
            result["spoken_text"], slow=st.session_state.get("speaking_speed") == "Slow"
        )
        st.session_state["sg_audio_autoplay"] = True
        st.session_state["sg_audio_stopped"] = False
    else:
        st.session_state["sg_audio"] = None
        st.session_state["sg_audio_autoplay"] = False


def analyze_current_image(image_bytes: bytes, task: str, action: str, question: str = "") -> None:
    """Run image analysis and retain the frame for follow-up questions."""
    st.session_state["sg_latest_image"] = image_bytes
    try:
        with st.spinner("Analysing the scene..."):
            result = analyze_image(image_bytes, task, question=question)
        store_result(result, task, action)
        if action == "Scan":
            st.session_state["sg_scan_count"] += 1
    except GeminiRequestError as error:
        st.error(str(error))


# HAI: Mental models and expectations (L5, L11): disclose capabilities and limitations.
# HAI: Anthropomorphism control (L5): clearly identify as AI and use neutral language.
# HAI: Calibrated trust (L6): remind users to verify important and safety-related information.
st.markdown(
    '<div class="sg-header"><h1>SightGuide</h1><span class="sg-ai">AI-powered</span></div>'
    '<p class="sg-tagline">A camera-based assistant for understanding the scene in front of you.</p>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Current task")
    st.selectbox("Prioritize for", TASK_OPTIONS, key="task_choice", label_visibility="collapsed")
    if st.session_state["task_choice"] == "Custom task":
        st.text_input("Describe your task", key="custom_task", placeholder="e.g. Find my blue bag")

    st.subheader("Voice output")
    st.toggle("Speak results", value=True, key="voice_enabled")
    st.selectbox("Speaking speed", ["Normal", "Slow"], key="speaking_speed")
    st.selectbox("Confidence style", CONFIDENCE_STYLES, key="confidence_style")

    # HAI: Mental models and expectations; communicates capabilities and limits.
    with st.expander("What I can and can't do"):
        st.markdown(
            "**Can do**\n\n"
            "- Describe scenes and identify common objects\n"
            "- Read printed text that is visible and clear\n"
            "- Answer questions about the current image\n"
            "- Highlight visible hazards and prioritize by task\n\n"
            "**Can't do**\n\n"
            "- See beyond the camera view or remember past scenes\n"
            "- Reliably read blurry or handwritten text\n"
            "- Judge exact distances or guarantee safety\n\n"
            "**How well it works**\n\nAccuracy drops in low light, motion blur, and cluttered scenes."
        )
        st.caption("Verify important information, especially anything safety-related.")

    st.subheader("Session stats")
    st.metric("Scans", st.session_state["sg_scan_count"])
    st.metric("Corrections", st.session_state["sg_correction_count"])
    if st.button("🔄  Reset session", use_container_width=True):
        reset_session()
        st.rerun()

# HAI: AI roles (L3): SightGuide assists and advises; it does not act autonomously.
# HAI: Human-in-the-Loop (L4): recommendations leave every decision with the user.
if not st.session_state["sg_welcome_seen"]:
    st.markdown(
        f'<div class="sg-card sg-welcome"><strong>Welcome to SightGuide</strong><br>{WELCOME_MESSAGE}</div>',
        unsafe_allow_html=True,
    )
    st.session_state["sg_welcome_seen"] = True
    if st.session_state["voice_enabled"]:
        st.session_state["sg_audio"] = text_to_speech(
            WELCOME_MESSAGE, slow=st.session_state["speaking_speed"] == "Slow"
        )
        st.session_state["sg_audio_autoplay"] = True
    if st.session_state.get("sg_audio"):
        st.audio(
            st.session_state["sg_audio"],
            format="audio/mp3",
            autoplay=st.session_state["sg_audio_autoplay"],
        )
        st.session_state["sg_audio_autoplay"] = False
else:
    st.info(WELCOME_MESSAGE, icon="ℹ️")

camera_column, result_column = st.columns([1, 1], gap="large")
with camera_column:
    st.subheader("Camera")
    camera_image = st.camera_input("Take a snapshot of the scene", key="camera_snapshot")
    st.caption("If the camera is unavailable, allow camera access in your browser and refresh this page.")
    if st.button("📷  Scan scene", type="primary", disabled=camera_image is None, use_container_width=True):
        if camera_image is not None:
            analyze_current_image(camera_image.getvalue(), current_task(), "Scan")

with result_column:
    st.subheader("Results")
    result = st.session_state.get("sg_result")
    if result:
        # HAI: Error cost = probability x consequence (L7): never hide a reported hazard.
        for hazard in result["hazard_details"]:
            label = "Possible hazard" if hazard["uncertain"] else "Hazard detected"
            st.markdown(
                f'<div class="sg-hazard"><strong>⚠️ {label}:</strong> '
                f'{escape(str(hazard["name"]))}. Please verify before moving.</div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<div class="sg-card"><strong>Scene summary</strong><br>{escape(result["summary"])}</div>',
            unsafe_allow_html=True,
        )
        if result["answer"]:
            st.markdown(f"**Answer:** {result['answer']}")
        if result["transcribed_question"]:
            st.caption("Transcribed question: " + result["transcribed_question"])

        st.markdown("**Detected objects**")
        if result["objects"]:
            for item in result["objects"]:
                label, style = confidence_display(item["confidence"], st.session_state["confidence_style"])
                st.markdown(
                    f'<div class="sg-object"><span>{escape(item["name"])}</span>'
                    f'<span class="sg-confidence {style}">{label}</span></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No objects could be identified confidently.")

        st.markdown("**Text I can read**")
        if result["visible_text"]:
            for text in result["visible_text"]:
                st.markdown(f"- {text}")
        else:
            st.caption("No readable text detected.")

        # HAI: Explanations (L12); Why? is available without another Gemini request.
        with st.expander("Why?", expanded=st.session_state["sg_show_why"]):
            st.write(result["why"] or "No additional visual explanation was provided.")
            if result["uncertain_items"]:
                st.markdown("**Uncertain details**: " + "; ".join(result["uncertain_items"]))
            if result["suggestion"]:
                st.markdown("**Suggestion**: " + result["suggestion"])

        # HAI: Multimodal interface; visual output is mirrored in optional spoken output.
        audio_bytes = st.session_state.get("sg_audio")
        if audio_bytes and not st.session_state.get("sg_audio_stopped"):
            st.audio(
                audio_bytes,
                format="audio/mp3",
                autoplay=st.session_state["sg_audio_autoplay"],
            )
            st.session_state["sg_audio_autoplay"] = False
    else:
        st.markdown('<div class="sg-card sg-muted">Take a snapshot, then scan to see a task-focused description.</div>', unsafe_allow_html=True)

st.markdown("---")
st.subheader("Ask a question")
st.caption("Questions are answered using the latest captured frame.")
question_column, mic_column = st.columns([3, 1], vertical_alignment="bottom")
with question_column:
    question_text = st.text_input("Type a question", placeholder="What does the sign say?", key="typed_question")
    ask_clicked = st.button(
        "💬  Ask about this image",
        disabled=not st.session_state.get("sg_latest_image") or not question_text.strip(),
    )
with mic_column:
    # HAI: Multimodal interface (L4): camera, voice, and typed input are available.
    audio_question = mic_recorder(
        start_prompt="🎙️ Record question",
        stop_prompt="⏹️ Stop recording",
        just_once=True,
        use_container_width=True,
        key="question_mic",
        format="wav",
    )

if ask_clicked and question_text.strip() and st.session_state.get("sg_latest_image"):
    analyze_current_image(
        st.session_state["sg_latest_image"], current_task(), "Question", question=question_text.strip()
    )
    st.rerun()

if audio_question and audio_question.get("bytes") and st.session_state.get("sg_latest_image"):
    audio_hash = hashlib.sha256(audio_question["bytes"]).hexdigest()
    if audio_hash != st.session_state.get("sg_last_audio_hash"):
        st.session_state["sg_last_audio_hash"] = audio_hash
        st.info("Your spoken question is being transcribed and answered from the latest image.")
        try:
            with st.spinner("Analysing your question..."):
                audio_result = answer_audio_question(
                    st.session_state["sg_latest_image"], current_task(), audio_question["bytes"]
                )
            store_result(audio_result, current_task(), "Spoken question")
            st.rerun()
        except GeminiRequestError as error:
            st.error(str(error))

# HAI: Human-on-the-Loop (L4): Stop, Repeat, and Scan again supervise and interrupt output.
control_columns = st.columns(5)
with control_columns[0]:
    if st.button("🔁  Repeat", disabled=not st.session_state.get("sg_result"), use_container_width=True):
        result = st.session_state["sg_result"]
        st.session_state["sg_audio"] = text_to_speech(
            result["spoken_text"], slow=st.session_state["speaking_speed"] == "Slow"
        )
        st.session_state["sg_audio_autoplay"] = True
        st.session_state["sg_audio_stopped"] = False
        st.rerun()
with control_columns[1]:
    if st.button("⏹  Stop speaking", disabled=not st.session_state.get("sg_audio"), use_container_width=True):
        st.session_state["sg_audio_stopped"] = True
        st.session_state["sg_audio"] = None
        st.session_state["sg_audio_autoplay"] = False
        st.rerun()
with control_columns[2]:
    if st.button("🔄  Scan again", disabled=not st.session_state.get("sg_latest_image"), use_container_width=True):
        analyze_current_image(st.session_state["sg_latest_image"], current_task(), "Scan")
        st.rerun()
with control_columns[3]:
    if st.button("❓  Why?", disabled=not st.session_state.get("sg_result"), use_container_width=True):
        st.session_state["sg_show_why"] = not st.session_state["sg_show_why"]
        st.rerun()
with control_columns[4]:
    if st.button("❌  That's wrong", disabled=not st.session_state.get("sg_result"), use_container_width=True):
        st.session_state["sg_correction_open"] = True
        st.rerun()

if st.session_state.get("sg_result"):
    # HAI: Recovery mechanisms (L7): correction re-check is an explicit user-controlled action.
    with st.expander("Submit a correction", expanded=st.session_state["sg_correction_open"]):
        with st.form("correction_form"):
            correction_text = st.text_area("What should be corrected?", placeholder="That is a phone, not a remote.")
            correction_submitted = st.form_submit_button("Save correction and re-check")
        if correction_submitted:
            if not correction_text.strip():
                st.warning("Enter a correction before submitting.")
            elif not st.session_state.get("sg_latest_image"):
                st.error("There is no captured image to re-check. Scan a new image first.")
            else:
                previous = st.session_state["sg_result"]
                try:
                    log_correction(current_task(), previous, correction_text.strip())
                    with st.spinner("Re-checking your correction against the image..."):
                        corrected = analyze_image(
                            st.session_state["sg_latest_image"],
                            current_task(),
                            correction=correction_text.strip(),
                        )
                    store_result(corrected, current_task(), "Corrected scan")
                    st.session_state["sg_correction_count"] += 1
                    st.session_state["sg_correction_open"] = False
                    st.success("Updated using your correction.")
                    st.rerun()
                except GeminiRequestError as error:
                    st.error(str(error))
                except OSError:
                    st.error("The correction could not be saved locally. Check write access to the project folder.")

# HAI: Mixed-initiative interaction (L4): hazards are proactive; follow-up questions remain user-initiated.
with st.expander("Interaction history"):
    history = st.session_state.get("sg_history", [])
    if not history:
        st.caption("Scans and questions from this session will appear here.")
    else:
        for entry in reversed(history):
            st.markdown(f"**{entry['action']} · {entry['task']}**  \n{entry['summary']}")
            if entry["answer"]:
                st.caption("Answer: " + entry["answer"])

st.caption("AI-generated information can be incomplete. Verify hazards and important details yourself.")