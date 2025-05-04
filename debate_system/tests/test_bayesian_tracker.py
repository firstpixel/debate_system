from app.bayesian_tracker import BayesianTracker

def test_bayesian_tracker_behavior():
    tracker = BayesianTracker()
    agent = "Skeptic"
    topic = "Should AI replace doctors?"

    tracker.update(agent, "AI cannot replace doctors because empathy is essential.")
    tracker.update(agent, "Actually, AI might fully automate surgeries and diagnosis.")

    result = tracker.analyze(agent, topic)
    print("\nTracker Metrics:", result)

    assert isinstance(result, dict)
    assert "coherence" in result and "drift" in result
