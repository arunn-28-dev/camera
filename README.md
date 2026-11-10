# SightGuide

SightGuide is a camera-based AI assistant for describing a visible scene, finding common objects, reading clear printed text, and answering questions about the current camera frame. It prioritizes the selected task and reports possible hazards cautiously. It does not take actions for the user.

## Features

- Snapshot-based scene analysis with Gemini 2.5 Flash and a constrained JSON response schema
- Task selector plus custom task, image-grounded text and spoken questions
- Hazard-first results, object confidence styles, visible text, uncertainty, and evidence-based explanations
- Optional spoken output, repeat and stop controls, correction/re-check flow, and in-session history
- Text-only correction log; camera images remain in memory and are never written to disk
- Light theme, responsive layout, capability disclosure, and safety reminders

## Setup

1. Use Python 3.10 or newer.
2. From this directory, install the listed dependencies: `python -m pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set `GEMINI_API_KEY` to a Google AI Studio API key.
4. Start the app: `streamlit run app.py`.
5. Allow camera access, choose a task, take a snapshot, and select **Scan scene**.

Microphone and gTTS features require browser microphone permission and network access. The experimental live-video mode is not included; snapshot scanning is the supported camera workflow.

## Human-AI interaction concepts

| Lecture concept | Implementation |
| --- | --- |
| AI roles (L3) | `app.py` labels the system as an assistant/advisor; it describes and prioritizes but takes no actions. |
| Human-in-the-Loop (L4) | `app.py` presents recommendations for the user to decide; no physical action is automatic. |
| Human-on-the-Loop (L4) | `app.py` exposes Repeat, Stop speaking, and Scan again controls. |
| Mixed initiative (L4) | `app.py` accepts user questions and displays hazards proactively after a scan. |
| Multimodal interface (L4) | `app.py` uses camera, typed and microphone questions, text results, and audio output. |
| Mental models and expectations (L5, L11) | `config.py` holds the startup disclosure; `app.py` presents capabilities, limitations, and accuracy caveats. |
| Anthropomorphism control (L5) | `prompts.py` requires neutral language and no human identity claims; `app.py` identifies SightGuide as AI-powered. |
| Calibrated trust (L6) | `hazards.py` and `app.py` use cautious safety phrasing; the UI reminds users to verify important details. |
| Error cost (L7) | `hazards.py` preserves all reported hazards and places them before summaries in speech; `app.py` shows them at the top. |
| False positives vs false negatives (L7) | `hazards.py` uses “Possible hazard” for uncertain detections instead of silently removing them. |
| Hallucination prevention (L7) | `prompts.py` requires visible-image grounding and an explicit response when an item cannot be seen. |
| Uncertainty (L7, L11) | `schemas.py`, `prompts.py`, and `app.py` retain uncertain items and show suggestions when provided. |
| Unpredictability reduction (L7) | `config.py`, `schemas.py`, and `gemini_client.py` use a fixed model, low temperature, and structured schema. |
| Recovery mechanisms (L7) | `app.py` offers Repeat, Scan again, Why?, and correction; `gemini_client.py` returns friendly errors and retries invalid JSON once. |
| Human-centred feedback loop (L8) | `feedback.py` records text corrections; `app.py` re-queries the same in-memory frame with the correction. |
| Deterministic code where appropriate (L8) | `confidence.py`, `hazards.py`, `schemas.py`, and `app.py` handle confidence labels, ordering, parsing, and counts in Python. |
| Five confidence styles (L11) | `confidence.py` maps high/medium/low to numeric, verbal, badge, range, or explicit uncertainty; `app.py` provides a selector. |
| Explanations (L12) | `app.py` exposes the model's evidence-based explanation through the Why? expander and button. |

## Demo script

1. Open the app and review the startup disclosure and capability panel.
2. Select **Reading signs/labels**, take a snapshot with visible printed text, and scan.
3. Change the confidence style and inspect the object list and Why? explanation.
4. Ask a typed or spoken question about the current frame; verify the transcript and answer.
5. Submit a correction, inspect the updated result, then demonstrate Repeat, Stop speaking, and session history.

## Limitations

- SightGuide only sees the captured frame; it cannot judge exact distances, guarantee safety, or remember earlier scenes after a reset.
- Low light, blur, occlusion, clutter, handwriting, model errors, API limits, and network quality can reduce accuracy.
- Voice generation and Gemini audio input use network services. Speech generation may be unavailable offline.
- The live-video experiment is intentionally not part of this snapshot-focused build.
- Treat all outputs, especially hazard observations, as assistive information rather than a substitute for direct judgment.