# app/turn_strategy/mcts_turn_selector.py

from typing import List, Dict
import random
from app.core_llm import LLMClient

class MCTSTurnSelector:
    def __init__(self, agent_names: List[str], simulations: int = 5):
        self.agent_names = agent_names
        self.simulations = simulations
        self.llm = LLMClient()

    def select_next(self, context: Dict) -> str:
        topic = context.get("topic", "")
        last_turns = context.get("history", [])

        scores = {agent: 0.0 for agent in self.agent_names}

        for agent in self.agent_names:
            prompt = [
                {"role": "system", "content": f"You are a debate strategist. Predict the impact of giving the next turn to {agent}."},
                {"role": "user", "content": f"Debate Topic: {topic}\n\nLast Turns:\n" +
                                            "\n".join(f"{t['agent']}: {t['content']}" for t in last_turns[-3:])}
            ]

            result = ""
            for token in self.llm.stream_chat(prompt):
                result += token

            # Simple scoring: +1 if "clarify", +1 if "support", -1 if "off-topic"
            score = sum([
                result.lower().count("clarify") * 1.0,
                result.lower().count("support") * 1.0,
                result.lower().count("attack") * 0.5,
                -result.lower().count("off-topic") * 1.0
            ])
            scores[agent] += score

        return max(scores.items(), key=lambda x: x[1])[0]
