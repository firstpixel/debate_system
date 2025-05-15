
import pytest
from unittest.mock import MagicMock, PropertyMock
from app.debate_manager import DebateManager
from app.memory_manager import MemoryManager
from app.core_llm import LLMClient

# Replace with your actual function if config loading logic was moved
def load_config():
    return {
        "rounds": 1,
        "topic": "Can AI replace human jobs?",
        "turn_strategy": "round_robin",
        "use_mediator": True,
        "consensus_strategy": "mediator_summary",
        "context_scope": "rolling",
        "logging_mode": "markdown+json",
        "argument_tree": True,
        "bayesian_tracking": True,
        "delphi": {"enabled": False, "rounds": 2, "summary_style": "bullet_points"},
        "mcts": {"max_simulations": 10, "evaluation_metric": ["argument_score", "coherence_delta"]},
        "personas": [
            {"name": "TechAdvocate", "model": "gemma3:latest", "role": "Optimist", "temperature": 0.8},
            {"name": "Ethicist", "model": "gemma3:latest", "role": "Skeptic", "temperature": 0.6}
        ],
        "mediator": {"type": "active", "model": "gemma3:latest"}
    }

@pytest.fixture
def mock_llm():
    mock = MagicMock(spec=LLMClient)
    mock.stream_chat.return_value = iter(["AI ", "can ", "replace ", "some ", "jobs."])
    mock.embed.side_effect = lambda text: [0.1] * 768  # dummy vector
    return mock

@pytest.fixture
def mock_memory():
    memory = MagicMock(spec=MemoryManager)

    # Patch belief to a mock
    belief_mock = MagicMock()
    belief_mock.get_belief_summary.return_value = {"coherence": 1.0}
    type(memory).belief = PropertyMock(return_value=belief_mock)

    memory.get_context.return_value = "- AI is useful\n- AI helps with tasks"
    memory.add_turn.return_value = "turn_1"
    memory.save_belief.return_value = True

    return memory

def test_debate_flow_one_round(monkeypatch, mock_llm, mock_memory):
    # Monkeypatch trackers to use mocks instead of real instantiation
    monkeypatch.setattr("app.bayesian_tracker.LLMClient", lambda: mock_llm)
    monkeypatch.setattr("app.bayesian_tracker.MemoryManager", lambda: mock_memory)

    config = load_config()
    dm = DebateManager(config=config)

    result = dm.start(feedback_callback=lambda x: None)

    assert isinstance(result, dict)
    assert result.get("rounds_completed", 0) == 1

    assert mock_memory.add_turn.called
    assert mock_memory.save_belief.called
    assert mock_llm.stream_chat.called
