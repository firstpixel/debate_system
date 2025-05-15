# app/session_recovery.py

import os
import json
import yaml
from typing import Dict, List
from app.argument_graph import ArgumentGraph
from app.agent_state_tracker import AgentStateTracker
from networkx.readwrite import json_graph

SESSION_DIR = "sessions"

def _ensure_path(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def save_json(data: Dict, path: str):
    _ensure_path(path)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def save_yaml(data: Dict, path: str):
    _ensure_path(path)
    with open(path, "w") as f:
        yaml.dump(data, f)

def load_json(path: str) -> Dict:
    with open(path, "r") as f:
        return json.load(f)

def load_yaml(path: str) -> Dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def save_session(session_id: str, config: Dict, agent_states: Dict[str, AgentStateTracker], graph: ArgumentGraph, history: List[Dict], turn_info: Dict):
    path = f"{SESSION_DIR}/{session_id}/"
    save_yaml(config, path + "config.yaml")

    # Serialize memory
    state_data = {name: tracker.memory for name, tracker in agent_states.items()}
    save_json(state_data, path + "agent_states.json")

    # Serialize graph
    save_json(graph.export_json(), path + "argument_graph.json")

    # Serialize history
    save_json(history, path + "debate_history.json")

    # Serialize current round/turn
    save_json(turn_info, path + "current_turn.json")


def load_session(session_id: str) -> Dict:
    path = f"{SESSION_DIR}/{session_id}/"

    config = load_yaml(path + "config.yaml")
    agent_state_data = load_json(path + "agent_states.json")
    graph_data = load_json(path + "argument_graph.json")
    history = load_json(path + "debate_history.json")
    turn_info = load_json(path + "current_turn.json")

    # Rebuild agent states
    agent_states = {}
    for name, memory in agent_state_data.items():
        tracker = AgentStateTracker(agent_name=name)
        for belief in memory:
            tracker.add_belief(belief)
        agent_states[name] = tracker

    # Rebuild graph
    graph = ArgumentGraph()
#    graph.graph = json_graph.node_link_graph(graph_data)
    graph.graph = json_graph.node_link_graph(graph_data, edges="links")
    graph.arg_count = len(graph.graph.nodes)

    return {
        "config": config,
        "agent_states": agent_states,
        "graph": graph,
        "history": history,
        "turn_info": turn_info
    }
