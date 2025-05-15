from app.session_recovery import save_session, load_session
from app.agent_state_tracker import AgentStateTracker
from app.argument_graph import ArgumentGraph

def test_session_roundtrip():
    session_id = "test123"
    config = {"topic": "Is AI safe?", "rounds": 3}
    agent_states = {
        "BotA": AgentStateTracker("BotA"),
        "BotB": AgentStateTracker("BotB")
    }
    agent_states["BotA"].add_belief("AI helps reduce errors.")
    agent_states["BotB"].add_belief("AI is unpredictable.")

    graph = ArgumentGraph()
    graph.add_argument("BotA", "AI is safer than humans.")
    graph.add_argument("BotB", "AI lacks ethics.", reply_to="ARG001", relation="attacks")

    history = [{"agent": "BotA", "content": "AI reduces errors."}]
    turn_info = {"current_turn": "BotB"}

    save_session(session_id, config, agent_states, graph, history, turn_info)
    data = load_session(session_id)

    assert data["config"]["topic"] == "Is AI safe?"
    assert "BotA" in data["agent_states"]
    assert len(data["graph"].graph.nodes) == 2
    print("Session Reloaded:", data["turn_info"])
