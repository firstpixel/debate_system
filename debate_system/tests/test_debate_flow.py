from app.debate_manager import DebateManager
from app.config import load_config

def test_full_debate_cycle():
    config = load_config("tests/data/test_config.yaml")  # Include a working config
    dm = DebateManager(config)
    dm.start()
    assert len(dm.debate_history) > 0
    assert dm.argument_graph.graph.number_of_nodes() > 0
