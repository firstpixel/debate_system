from app.agent_state_tracker import AgentStateTracker

def test_belief_tracking_and_summary():
    tracker = AgentStateTracker("Skeptic")
    tracker.add_belief("AI lacks moral judgment.")
    tracker.add_belief("AI is unreliable in ethical decisions.")
    tracker.add_belief("AI could assist but not replace doctors.")
    tracker.add_belief("AI still can't handle edge cases.")
    tracker.add_belief("AI needs human supervision.")

    summary = tracker.summarize_memory()
    assert isinstance(summary, str) and len(summary.strip()) > 0
    print("\nBelief Summary:", summary)
