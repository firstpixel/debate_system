# app/consensus_engine.py

from typing import List, Dict
from app.core_llm import LLMClient
from app.agent_state_tracker import AgentStateTracker
from app.argument_graph import ArgumentGraph

class ConsensusEngine:
    def __init__(self, strategy: str = "mediator_summary", model: str = "gemma3:latest", temperature: float = 0.5):
        self.strategy = strategy.lower()
        self.llm = LLMClient(model=model, temperature=temperature)

    def generate_consensus(
        self,
        agents: List[str],
        agent_states: Dict[str, AgentStateTracker],
        transcript: List[Dict],
        graph: ArgumentGraph
    ) -> str:
        if self.strategy == "no_consensus":
            return "❗ No consensus was reached. Each agent retains their position."

        elif self.strategy == "agent_closing":
            return self._agent_closing_block(agent_states)

        elif self.strategy == "mediator_summary":
            return self._mediator_summarize(transcript)

        elif self.strategy == "vote":
            return self._agent_vote_summary(agent_states)

        else:
            raise ValueError(f"Unknown consensus strategy: {self.strategy}")

    def _agent_closing_block(self, agent_states: Dict[str, AgentStateTracker]) -> str:
        block = ["### 🧠 Final Positions by Agent:\n"]
        for name, tracker in agent_states.items():
            summary = tracker.summarize_memory()
            block.append(f"**{name}**:\n{summary}\n")
        return "\n".join(block)

    def _mediator_summarize(self, transcript: List[Dict]) -> str:
        debate_text = "\n".join(f"**{m['agent']}**: {m['content']}" for m in transcript)

        prompt = [
            {"role": "system", "content": "You are a debate mediator. Summarize the key points and shared conclusions reached. Evaluate the arguments and provide a consensus summary. Check for contradictions."},
            {"role": "user", "content": f"Debate Transcript:\n\n{debate_text}"}
        ]

        result = ""
        for token in self.llm.stream_chat(prompt):
            result += token
        return f"### 🤝 Consensus Summary:\n{result.strip()}"

    def _agent_vote_summary(self, agent_states: Dict[str, AgentStateTracker]) -> str:
        beliefs = [tracker.summarize_memory() for tracker in agent_states.values()]
        prompt = [
            {"role": "system", "content": "Act as a neutral observer. Based on the following summaries, vote for the most persuasive and coherent stance. Contradictions should be noted and punished on the score."},
            {"role": "user", "content": "\n\n".join(f"- {b}" for b in beliefs)}
        ]

        result = ""
        for token in self.llm.stream_chat(prompt):
            result += token
        return f"### 🗳️ Voting Result:\n{result.strip()}"
