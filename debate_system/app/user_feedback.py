# app/user_feedback.py

import json
import logging
import os

logger = logging.getLogger(__name__)
SESSION_DIR = "sessions"

def get_feedback_form() -> dict:
    return {
        "satisfaction": None,       # 1–10
        "perceived_bias": "",       # (e.g., "leaned pro-AI")
        "clarity_score": None,      # 1–10
        "coherence_score": None,    # 1–10
        "comments": ""              # free text
    }

def save_feedback(session_id: str, feedback: dict):
    path = f"{SESSION_DIR}/{session_id}/user_feedback.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w") as f:
        json.dump(feedback, f, indent=2)

    logger.info(f"Feedback saved for session {session_id}")
    print(f"📝 Feedback saved to {path}")
