from typing import List, Dict
import statistics

class ContradictionLog:
    def __init__(self):
        self.entries: List[Dict] = []

    def log(self, agent: str, new_belief: str, contradicted: List[str], similarity_scores: List[float] = []):
        self.entries.append({
            "agent": agent,
            "new_belief": new_belief,
            "contradicted_beliefs": contradicted,
            "similarity_scores": similarity_scores
        })

    def get_agent_log(self, agent: str) -> List[Dict]:
        return [entry for entry in self.entries if entry["agent"] == agent]

    def count_for(self, agent: str) -> int:
        return sum(len(e["contradicted_beliefs"]) for e in self.entries if e["agent"] == agent)

    def avg_similarity_for(self, agent: str) -> float:
        scores = []
        for entry in self.entries:
            if entry["agent"] == agent:
                scores.extend(entry.get("similarity_scores", []))
        return round(statistics.mean(scores), 3) if scores else 0.0

    def to_heatmap_data(self) -> Dict[str, int]:
        """Aggregate contradiction count per agent."""
        heatmap = {}
        for entry in self.entries:
            name = entry["agent"]
            heatmap[name] = heatmap.get(name, 0) + len(entry["contradicted_beliefs"])
        return heatmap

    def to_markdown(self) -> str:
        lines = ["# ❗ Contradiction Report"]

        # 🔢 Summary Table
        agent_stats = {}
        for entry in self.entries:
            agent = entry["agent"]
            count = len(entry["contradicted_beliefs"])
            scores = entry.get("similarity_scores", [])
            if agent not in agent_stats:
                agent_stats[agent] = {"count": 0, "scores": []}
            agent_stats[agent]["count"] += count
            agent_stats[agent]["scores"].extend(scores)

        if agent_stats:
            lines.append("## 📊 Contradiction Summary Table")
            lines.append("| Agent | Contradictions | Avg Similarity |")
            lines.append("|-------|----------------|----------------|")
            for agent, data in agent_stats.items():
                # Extract only the similarity values from (belief, similarity) tuples
                score_values = [s[1] if isinstance(s, tuple) and len(s) == 2 else s for s in data["scores"]]
                avg_score = round(statistics.mean(score_values), 3) if score_values else "–"
                lines.append(f"| {agent} | {data['count']} | {avg_score} |")
            lines.append("")

        # 🧾 Detailed Log
        for entry in self.entries:
            lines.append(f"## Agent: **{entry['agent']}**")
            lines.append(f"**New Belief:** {entry['new_belief']}")
            if entry["contradicted_beliefs"]:
                lines.append("**Contradicted Beliefs:**")
                for b in entry["contradicted_beliefs"]:
                    lines.append(f"- {b}")
            if entry.get("similarity_scores"):
                lines.append(f"**Scores:** {entry['similarity_scores']}")
            lines.append("")

        return "\n".join(lines)
