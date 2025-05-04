from typing import List
from app.core_llm import LLMClient
from app.contradiction_detector import ContradictionDetector
from memory.mongo_store import BeliefStore
import os
from pymongo import MongoClient
from memory.mongo_client import db
MAX_BELIEF_MEMORY = 10



class AgentStateTracker:
    def __init__(self, agent_name: str, model: str = "gemma3:latest", temperature: float = 0.5):
        self.client = db.client
        self.db = db
        
        self.agent_name = agent_name
        self.llm = LLMClient(model=model, temperature=temperature)
        self.contradiction_checker = ContradictionDetector()
        self.last_contradiction_check = ""
        self.belief_store = BeliefStore(self.db)
        self.memory: List[str] = self._load_beliefs()

    def _load_beliefs(self) -> List[str]:
        return self.belief_store.get_raw_beliefs(self.agent_name)

    def get_recent(self, n: int = MAX_BELIEF_MEMORY) -> List[str]:
        return self.memory[-n:]

    def get_summary_of_older(self) -> str:
        older = self.memory[:-MAX_BELIEF_MEMORY]
        if not older:
            return ""
        prompt = [
            {"role": "system", "content": "You are a memory compression agent. Summarize these older beliefs using Markdown bullet points."},
            {"role": "user", "content": "\n".join(f"- {m}" for m in older)}
        ]
        summary = ""
        for token in self.llm.stream_chat(prompt):
            summary += token
        return summary.strip()

    def update_belief(self, belief: str):
        contradictions = self.contradiction_checker.find_contradictions(belief, self.memory)
        if contradictions:
            self.last_contradiction_check = self.contradiction_checker.verify_with_llm(belief, contradictions)

        self.memory.append(belief)
        self.belief_store.append_belief(self.agent_name, belief)
        
    def add_belief(self, belief: str):
        self.memory.append(belief)
        self.belief_store.append_belief(self.agent_name, belief)

    def summary(self) -> str:
        recent = "\n".join(f"- {b}" for b in self.get_recent())
        older_summary = self.get_summary_of_older()
        if older_summary:
            return f"{recent}\n\n### Summary of Older Beliefs:\n{older_summary}"
        return recent
    
    def summarize_memory(self) -> str:
        return self.belief_store.get_belief_summary(self.agent_name)
    

    def last_contradiction(self) -> str:
        return self.last_contradiction_check or ""
