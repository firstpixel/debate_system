from unittest.mock import MagicMock
from app.memory_manager import MemoryManager
import pytest


def test_get_belief_summary_includes_scores(monkeypatch):
    # Patch heavy dependencies to avoid external calls
    monkeypatch.setattr("app.memory_manager.LTMStore", lambda *a, **k: MagicMock())
    monkeypatch.setattr("app.memory_manager.RAGRetriever", lambda *a, **k: MagicMock())
    monkeypatch.setattr("app.memory_manager.LLMClient", lambda *a, **k: MagicMock())

    mgr = MemoryManager()
    mock_store = MagicMock()
    mock_store.get_belief_summary.return_value = {
        "summary": "test belief",
        "scores": {"coherence": 0.8, "drift": 0.2},
        "topic": "AI",
        "round": 1,
    }
    mgr.belief = mock_store

    result = mgr.get_belief_summary("agent", return_type="dict")
    assert result["scores"]["coherence"] == 0.8
    assert result["scores"]["drift"] == 0.2
