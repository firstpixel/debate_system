# app/logger.py

import os
import json
from typing import List, Dict
from app.argument_graph import ArgumentGraph
import logging

SESSION_DIR = "sessions"

def save_log_files(
    session_id: str,
    config: Dict,
    transcript: List[Dict],
    consensus_block: str,
    graph: ArgumentGraph
):
    path = f"{SESSION_DIR}/{session_id}/"
    os.makedirs(path, exist_ok=True)

    # ── MARKDOWN OUTPUT ───────────────────────────
    md_lines = [f"# 🧠 Debate Log – {config.get('topic', '')}\n"]

    md_lines.append("## 🧑‍🤝‍🧑 Agents:\n")
    for p in config.get("personas", []):
        md_lines.append(f"- **{p['name']}** ({p['role']})")

    md_lines.append("\n## 🔁 Debate Rounds:\n")
    for turn in transcript:
        md_lines.append(f"**{turn['agent']}**: {turn['content']}")

    md_lines.append("\n## 🌳 Argument Graph:\n")
    md_lines.append(graph.export_markdown())

    md_lines.append("\n## 🧠 Final Consensus:\n")
    md_lines.append(consensus_block)

    # Filter out None values before joining
    md_lines = [line for line in md_lines if line is not None]

    with open(path + "summary.md", "w") as f:
        f.write("\n\n".join(md_lines))


    print(f"📤 Logs saved to {path}summary.md and summary.json")

def log_turn(agent_name: str, duration: float):

    logger = logging.getLogger()
    logger.info(f"Agent {agent_name} turn took {duration:.2f} seconds")
    
    # Check for truncation in the console output if needed
    # This is separate from the main logging functionality
    return False
