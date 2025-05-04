# debate_system/app/main.py

import os
from app.config import load_config
from app.debate_manager import DebateManager

def run():
    config_path = os.getenv("DEBATE_CONFIG", "config.yaml")
    config = load_config(config_path)
    debate = DebateManager(config)
    debate.start()

if __name__ == "__main__":
    run()
