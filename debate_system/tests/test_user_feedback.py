from app.user_feedback import get_feedback_form, save_feedback
import os
import json

def test_feedback_save():
    session_id = "feedback_test"
    feedback = get_feedback_form()
    feedback["satisfaction"] = 10
    feedback["clarity_score"] = 9
    feedback["coherence_score"] = 8
    feedback["perceived_bias"] = "leaned pro-AI"
    feedback["comments"] = "Great arguments, especially from the skeptic."

    save_feedback(session_id, feedback)

    path = f"sessions/{session_id}/user_feedback.json"
    assert os.path.exists(path)

    with open(path) as f:
        data = json.load(f)

    assert "satisfaction" in data and data["comments"]
