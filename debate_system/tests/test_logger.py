from app.logger import save_log_files
from app.argument_graph import ArgumentGraph
from app.performance_logger import PerformanceLogger
import os

def test_log_files_export():
    session_id = "log_test"
    config = {
        "topic": "AI in medicine",
        "personas": [
            {"name": "ProTech", "role": "AI Optimist"},
            {"name": "SafeGuard", "role": "Cautious Analyst"}
        ]
    }

    history = [
        {"agent": "ProTech", "content": "AI saves lives in surgery."},
        {"agent": "SafeGuard", "content": "AI cannot yet replace diagnostic judgment."}
    ]

    graph = ArgumentGraph()
    graph.add_argument("ProTech", "AI improves precision.")
    graph.add_argument("SafeGuard", "But it fails in rare cases.", reply_to="ARG001", relation="attacks")

    perf = PerformanceLogger(session_id)
    perf.log_turn("ProTech", 1.2)
    perf.log_turn("SafeGuard", 1.1)

    save_log_files(session_id, config, history, "Consensus: Proceed with caution.", graph, perf)

    assert os.path.exists(f"sessions/{session_id}/summary.md")
    assert os.path.exists(f"sessions/{session_id}/summary.json")
