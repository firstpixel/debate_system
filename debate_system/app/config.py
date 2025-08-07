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
        "rounds": 1,
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
    },
    "enforced_lens": False,
    "language": "english"
}
def get_project_root():
    """Return the path to the project root directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load_yaml(file_path: str) -> dict:
    # Always use the provided path as-is (assume absolute or correct relative)
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

    # Ensure enforced_lens is always present
    if "enforced_lens" not in cfg:
        cfg["enforced_lens"] = False

    # Ensure language is always present
    if "language" not in cfg:
        cfg["language"] = "english"

    return cfg

def load_config(file_path: str) -> dict:
    """Load and validate configuration file.
    
    Args:
        file_path: Path to configuration file
        
    Returns:
        Normalized configuration dictionary
        
    Raises:
        ValueError: If configuration format is unsupported or invalid
        FileNotFoundError: If configuration file doesn't exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    ext = os.path.splitext(file_path)[-1].lower()

    try:
        if ext in [".yaml", ".yml"]:
            user_cfg = _load_yaml(file_path)
        elif ext == ".json":
            user_cfg = _load_json(file_path)
        elif ext == ".md":
            user_cfg = _load_markdown_frontmatter(file_path)
        else:
            raise ValueError(f"Unsupported config format: {ext}. Supported formats: .yaml, .yml, .json, .md")
    except Exception as e:
        raise ValueError(f"Failed to parse configuration file {file_path}: {str(e)}")

    cfg = normalize_config(user_cfg)
    
    # Validate essential configuration
    _validate_config(cfg)
    
    return cfg

def _validate_config(config: dict) -> None:
    """Validate essential configuration parameters.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If configuration is invalid
    """
    # Check required fields
    required_fields = ["personas", "rounds"]
    missing_fields = [field for field in required_fields if field not in config or not config[field]]
    
    if missing_fields:
        raise ValueError(f"Missing required configuration fields: {missing_fields}")
    
    # Validate personas
    if not isinstance(config["personas"], list) or len(config["personas"]) == 0:
        raise ValueError("Configuration must include at least one persona")
    
    for i, persona in enumerate(config["personas"]):
        if not isinstance(persona, dict):
            raise ValueError(f"Persona {i} must be a dictionary")
        
        required_persona_fields = ["name", "role"]
        missing_persona_fields = [field for field in required_persona_fields if field not in persona]
        
        if missing_persona_fields:
            raise ValueError(f"Persona {i} missing required fields: {missing_persona_fields}")
    
    # Validate rounds
    if not isinstance(config["rounds"], int) or config["rounds"] < 1:
        raise ValueError("Rounds must be a positive integer")
    
    # Validate language if specified
    supported_languages = ["english", "spanish", "french", "german", "portuguese"]
    if config.get("language") and config["language"].lower() not in supported_languages:
        print(f"Warning: Language '{config['language']}' not in supported list: {supported_languages}")
    
    # Validate turn strategy
    supported_strategies = ["round_robin", "priority", "interrupt", "delphi"]
    if config.get("turn_strategy") and config["turn_strategy"] not in supported_strategies:
        raise ValueError(f"Unsupported turn strategy: {config['turn_strategy']}. Supported: {supported_strategies}")
