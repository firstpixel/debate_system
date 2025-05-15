# app/flow_control.py

from typing import List, Dict
import random

class FlowController:
    def __init__(self, agent_names: List[str], strategy: str = "round_robin"):
        self.agent_names = agent_names
        self.strategy = strategy
        self.current_index = -1
        self.priority_scores = {name: 1.0 for name in agent_names}
        self._priority_order: List[str] = []  # For priority rotation

    def update_scores(self, new_scores: Dict[str, float]):
        self.priority_scores.update(new_scores)

        if self.strategy == "priority":
            # Sort once per round before iteration
            self._priority_order = sorted(
                self.priority_scores,
                key=lambda x: self.priority_scores[x],
                reverse=True
            )
            self.current_index = -1  # reset for new round

    def next_turn(self, context: Dict) -> str:
        strategy = self.strategy.lower()

        if strategy == "round_robin":
            self.current_index = (self.current_index + 1) % len(self.agent_names)
            return self.agent_names[self.current_index]

        elif strategy == "priority":
            if not self._priority_order:
                self._priority_order = sorted(
                    self.priority_scores,
                    key=lambda x: self.priority_scores[x],
                    reverse=True
                )
                self.current_index = -1

            self.current_index = (self.current_index + 1) % len(self._priority_order)
            return self._priority_order[self.current_index]

        elif strategy == "interrupt":
            flagged = context.get("interruption_request", None)
            return flagged if flagged in self.agent_names else random.choice(self.agent_names)

        elif strategy == "mcts":
            from app.turn_strategy.mcts_turn_selector import MCTSTurnSelector
            selector = MCTSTurnSelector(self.agent_names)
            return selector.select_next(context)

        else:
            raise ValueError(f"Unsupported turn strategy: {self.strategy}")
