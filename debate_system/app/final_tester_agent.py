import os
import logging
from typing import Dict, List
from app.core_llm import LLMClient
from app.bayesian_tracker import BayesianTracker
from app.argument_graph import ArgumentGraph
from app.agent_state_tracker import AgentStateTracker  # ✅ NEW: for belief summary

logger = logging.getLogger(__name__)


class FinalTesterAgent:
    def __init__(
        self,
        model: str = "gemma3:latest",
        temperature: float = 0.3
    ):
        self.llm = LLMClient(model=model, temperature=temperature)

    def analyze(
        self,
        session_id: str,
        consensus: str,
        tracker: BayesianTracker,
        graph: ArgumentGraph
    ) -> str:
        """
        Analyzes the final consensus, contradiction trends, and belief evolution.
        Produces a markdown-formatted audit report for the full debate session.
        """
        logger.info(f"📊 Running FinalTesterAgent on session: {session_id}")

        contradiction_report = tracker.export_logs()
        belief_table = self._build_agent_metrics_table(tracker)
        belief_snapshots = self._gather_belief_summaries(tracker.agent_history)
        argument_graph_summary = graph.export_markdown()

        system_prompt = (
            "You are a formal debate auditor. Your task is to evaluate the debate's logical consistency, "
            "belief coherence, contradiction patterns, and argument structure. After your analises, create a summary of the debate, pin pointing the consensus, highlighting the key points, definitions and what else we can extract as insights."
        )

        user_prompt = f"""
## 🟩 Final Consensus Block
{consensus}

## 📊 Agent Belief Metrics
{belief_table}

## ❗ Contradiction Logs
{contradiction_report}

## 🧠 Agent Belief Snapshots
{belief_snapshots}

## 🕸️ Argument Graph Summary
{argument_graph_summary}
"""

        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()}
        ]

        # Replace streaming with non-streaming call since the output isn't shown in real-time in the UI
        result = self.llm.chat(messages)

        report_path = f"sessions/{session_id}/audit_report.md"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as f:
            f.write(result.strip())

        logger.info(f"✅ FinalTesterAgent report saved to: {report_path}")
        return result.strip()

    def _build_agent_metrics_table(self, tracker: BayesianTracker) -> str:
        """
        Generates a markdown table of each agent's belief stats:
        - Coherence
        - Drift
        - Contradictions
        - Warning flag
        """
        headers = ["Agent", "Coherence", "Drift", "Contradictions", "⚠️ Flag"]
        rows = [headers, ["---"] * len(headers)]

        for agent in tracker.agent_history:
            belief_summary = tracker.get_agent_scores(agent)
            contradiction_count = tracker.contradiction_log.count_for(agent)

            coherence = belief_summary.get("coherence", 1.0)
            drift = belief_summary.get("drift", 0.0)
            contradiction_flag = "❌" if belief_summary.get("contradiction", False) else "✅"

            rows.append([
                agent,
                f"{coherence:.2f}",
                f"{drift:.2f}",
                str(contradiction_count),
                contradiction_flag
            ])

        return "\n".join("| " + " | ".join(row) + " |" for row in rows)

    def _gather_belief_summaries(self, agent_list: List[str]) -> str:
        """
        Retrieves belief memory summaries for each agent via AgentStateTracker.
        """
        summaries = []
        for agent in agent_list:
            tracker = AgentStateTracker(agent_name=agent)
            summaries.append(f"### {agent}\n{tracker.summary().strip()}\n")
        return "\n".join(summaries)
