import os
from app.debate_manager import DebateManager
from app.config import load_config
from app.argument_graph import ArgumentGraph

def test_full_feature_debate(tmp_path):
    config = load_config("tests/data/full_debate_config.yaml")
    dm = DebateManager(config)

    # Run debate
    dm.start()
    dm.finalize_debate()

    # ✅ Assert transcript exists
    assert len(dm.debate_history) >= 3, "Transcript missing or incomplete"

    # ✅ Assert argument graph is populated
    graph = dm.argument_graph
    assert isinstance(graph, ArgumentGraph)
    assert graph.graph.number_of_nodes() > 0
    assert graph.graph.number_of_edges() >= 0

    # ✅ Check consensus summary was generated
    assert dm.final_summary is not None
    assert isinstance(dm.final_summary, str)
    assert "summary" in dm.final_summary.lower() or "consensus" in dm.final_summary.lower()

    # ✅ Check graph metrics look sane
    metrics = graph.get_metrics()
    assert metrics["total_nodes"] > 0
    assert 0 <= metrics["contradiction_ratio"] <= 1

    # ✅ Save logs and validate markdown export works
    session_path = tmp_path / "test_session"
    session_path.mkdir()

    from app.logger import save_log_files
    from app.performance_logger import PerformanceLogger

    perf = PerformanceLogger("test_session")
    save_log_files(
        session_id="test_session",
        config=config,
        transcript=dm.debate_history,
        consensus_block=dm.final_summary,
        graph=graph,
        performance=perf
    )

    # Validate output files exist
    #md_path = os.path.join("output/debate_logs/test_session.md")
    #json_path = os.path.join("output/argument_trees/test_session.json")
    
    md_path = os.path.join("sessions", "test_session", "summary.md")
    json_path = os.path.join("sessions", "test_session", "summary.json")
    assert os.path.exists(md_path), "Markdown log was not saved"
    assert os.path.exists(json_path), "Argument tree JSON not saved"


