from app.consensus_engine import ConsensusEngine
from app.agent_state_tracker import AgentStateTracker

def test_mediator_summary():
    engine = ConsensusEngine("mediator_summary")
    history = [
        {"agent": "A", "content": "AI improves efficiency."},
        {"agent": "B", "content": "AI is dangerous in warfare."}
    ]
    result = engine.generate_consensus(["A", "B"], {}, history, None)
    assert "Consensus" in result or "Summary" in result
    print(result)
