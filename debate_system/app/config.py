# app/config.py

import os
import yaml
import json
from typing import Union
from markdown_it import MarkdownIt

DEFAULT_CONFIG = {
    "rounds": 3,
    "use_mediator": False,
    "consensus_strategy": "no_consensus",
    "turn_strategy": "round_robin",
    "context_scope": "rolling",
    "logging_mode": "markdown+json",
    "argument_tree": True,
    "bayesian_tracking": True,
    "delphi": {
        "enabled": False,
        "rounds": 2,
        "summary_style": "bullet_points"
    },
    "mcts": {
        "max_simulations": 10,
        "evaluation_metric": ["argument_score", "coherence_delta"]
    },
    "personas": [],
    "mediator": {
        "type": "silent",
        "model": "gemma3:latest"
    }
}
def get_project_root():
    """Return the path to the project root directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load_yaml(file_path: str) -> dict:
    # If file_path is not absolute, treat it as relative to project root
    if not os.path.isabs(file_path):
        file_path = os.path.join(get_project_root(), file_path)
    
    with open(file_path, "r") as f:
        return yaml.safe_load(f)
    
def _load_json(file_path: str) -> dict:
    with open(file_path, "r") as f:
        return json.load(f)

def _load_markdown_frontmatter(file_path: str) -> dict:
    with open(file_path, "r") as f:
        lines = f.readlines()

    if lines[0].strip() != "---":
        raise ValueError("Markdown config must start with --- frontmatter block")

    yaml_lines = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        yaml_lines.append(line)

    return yaml.safe_load("".join(yaml_lines))

def normalize_config(user_cfg: dict) -> dict:
    cfg = DEFAULT_CONFIG.copy()

    # Merge user values into default config
    for key, val in user_cfg.items():
        if isinstance(val, dict) and key in cfg:
            cfg[key].update(val)
        else:
            cfg[key] = val

    return cfg

def load_config(file_path: str) -> dict:
    ext = os.path.splitext(file_path)[-1]

    if ext in [".yaml", ".yml"]:
        user_cfg = _load_yaml(file_path)
    elif ext == ".json":
        user_cfg = _load_json(file_path)
    elif ext == ".md":
        user_cfg = _load_markdown_frontmatter(file_path)
    else:
        raise ValueError(f"Unsupported config format: {ext}")

    return normalize_config(user_cfg)
