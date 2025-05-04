import logging
from typing import Callable, List, Dict, Optional
import os
import time
import numpy as np
from app.core_llm import LLMClient
from app.agent_state_tracker import AgentStateTracker
from app.contradiction_detector import ContradictionDetector
from app.context_builder import ContextBuilder
from memory.mongo_store import BeliefStore  # ✅ Added
from datetime import datetime
from memory.mongo_client import db
logger = logging.getLogger(__name__)

MAX_BELIEF_MEMORY = 10

class PersonaAgent:
    def __init__(self, name: str, role: str, temperature: float = 0.7, model: str = "gemma3:latest"):
        self.name = name
        self.role = role
        self.temperature = temperature
        self.model = model
        self.memory: List[Dict] = []

        self.llm = LLMClient(model=self.model, temperature=self.temperature)

        self.bayesian_tracker = None
        self.tracker = AgentStateTracker(agent_name=name)
        self.db = db
        self.belief_store = BeliefStore(self.db)  

        self.perf_logger = None
        self.contradiction_checker = ContradictionDetector()
        self.contradiction_log = None
        self.context_builder = None

    def _summarize_overflow_beliefs(self, beliefs: List[str]) -> str:
        if not beliefs:
            return ""
        prompt = [
            {"role": "system", "content": "Summarize the following beliefs in concise Markdown bullet points."},
            {"role": "user", "content": "\n".join(f"- {b}" for b in beliefs)}
        ]
        summary = ""
        for token in self.llm.stream_chat(prompt):
            summary += token
        return summary.strip()

    def _compose_system_prompt(self, opponent_argument: str = "") -> str:
        belief_summary = self.belief_store.get_belief_summary(self.name)  # ✅ Use new store
        contradiction_warning = self.tracker.last_contradiction()

        prompt = (
            f"You are {self.name}, acting as a {self.role} in a formal debate.\n"
            f"You must reply strictly in **Markdown**, follow your belief system, and stay coherent.\n"
            f"Anchor your answers on your past positions, and do not contradict your beliefs.\n\n"
        )

        if contradiction_warning:
            prompt += f"⚠️ Contradiction Alert:\n{contradiction_warning.strip()}\n\n"

        if opponent_argument:
            prompt += f"## Your Opponent's Last Statement:\n> {opponent_argument.strip()}\n\n"

        prompt += f"## Your Current Beliefs:\n{belief_summary}"
        return prompt

    def interact(
        self,
        user_prompt: str,
        opponent_argument: str = "",
        debate_history: List[Dict] = [],
        topic: str = "",
        stream_callback: Optional[Callable[[str], None]] = None
    ) -> str:

        logger.info(f"###########Agent {self.name} is interacting with prompt: {user_prompt}")

        self.system_prompt = self._compose_system_prompt(opponent_argument)

        if not self.context_builder:
            self.context_builder = ContextBuilder(
                topic=topic,
                context_scope="rolling",
                window_size=4,
                llm=self.llm
            )

        context_messages = self.context_builder.build_context_messages(
            agent_name=self.name,
            mode="default"
        )

        messages = [{"role": "system", "content": self.system_prompt}] + context_messages
        messages.append({"role": "user", "content": user_prompt})

        response = ""
        start = time.time()
        for token in self.llm.stream_chat(messages):
            print(token, end="", flush=True)
            response += token
            if stream_callback:
                stream_callback(token)
        end = time.time()

        if self.perf_logger:
            self.perf_logger.log_turn(self.name, end - start)

        self.memory.append({"role": "assistant", "content": response})

        # Update belief tracker (in-memory)
        self.tracker.update_belief(response)

        # Log contradictions
        contradictions = self.contradiction_checker.find_contradictions(response, self.tracker.memory)
        if contradictions and self.contradiction_log:
            scores = [self.contradiction_checker._cosine_similarity(
                np.array(self.contradiction_checker._embed(response)),
                np.array(self.contradiction_checker._embed(b))
            ) for b in contradictions]
            self.contradiction_log.log(self.name, response, contradictions, scores)


        logger.debug(f"Response: {response}")
        logger.debug(f"Contradictions found: {contradictions}")

        return response
