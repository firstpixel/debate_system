# tests/test_streaming_agent.py

from app.persona_agent import PersonaAgent

def test_streamed_response():
    agent = PersonaAgent(name="ProAI", role="Technology Advocate", temperature=0.65)
    result = agent.interact("Why is AI useful in healthcare?")
    assert result and isinstance(result, str)
