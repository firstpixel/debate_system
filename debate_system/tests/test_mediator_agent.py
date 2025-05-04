from app.mediator_agent import MediatorAgent

def test_mediator_summarizer():
    mediator = MediatorAgent(mode="summarizer")

    history = [
        {"agent": "TechAdvocate", "content": "AI can reduce human error in driving."},
        {"agent": "SafeGuard", "content": "But AI fails in unpredictable scenarios like snow or ethics."}
    ]

    topic = "Should AI replace human drivers?"
    result = mediator.generate_response(history, topic)
    assert result and isinstance(result, str)
    print("\nMediator Summary:", result)
