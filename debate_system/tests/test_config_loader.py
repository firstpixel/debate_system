import os
from app.config import load_config

def test_load_yaml_config():
    # Use the correct path to the config file in the config directory
    config_path = os.path.join("config", "config.yaml")
    config = load_config(config_path)
    assert "personas" in config
    assert config["turn_strategy"] in ["round_robin", "mcts", "priority", "interrupt", "delphi"]
    assert isinstance(config["rounds"], int)
    print("Config Loaded ✅", config)
