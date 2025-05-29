# app/memory_manager.py

from datetime import datetime
from typing import List, Dict
import os
from pymongo import MongoClient
from memory.mongo_store import STMStore, BeliefStore
from memory.qdrant_store import LTMStore, RAGRetriever
from memory.embeddings import embed_text
from app.core_llm import LLMClient


class MemoryManager:
    def __init__(self):
        client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
        db = client["debate_engine"]
        self.db = db

        self.stm = STMStore()
        self.belief = BeliefStore(db)  # Includes contradictions in same doc
        self.ltm = LTMStore()
        self.rag = RAGRetriever()
        self.llm = LLMClient()

    # ---------------------------------------------
    # STM and LTM standardized return format
    # ---------------------------------------------
    def get_recent_stm(self, agent_id: str, limit: int = 10) -> List[Dict]:
        """Return recent messages in LLM format from STM."""
        turns = self.stm.get_recent_turns_raw(agent_id, limit=limit)
        return [{"role": "user", "content": t.get("message", "")} for t in turns]

    def get_all_stm(self, agent_id: str) -> List[Dict]:
        """Return all turns ever from STM in LLM format."""
        turns = self.stm.get_all_turns_raw(agent_id)
        return [{"role": "user", "content": t.get("message", "")} for t in turns]

    def summarize_memory(self, agent_id: str, preserve_last_n: int = 5) -> str:
        all_turns = self.get_all_stm(agent_id)
        if not all_turns:
            return "No memory available."

        older = all_turns[:-preserve_last_n] if len(all_turns) > preserve_last_n else []
        recent = all_turns[-preserve_last_n:]

        summary = ""
        if older:
            formatted = "\n".join(f"{t['role']}: {t['content']}" for t in older)
            prompt = [
                {"role": "system", "content": "You are a helpful memory summarizer for a debate system."},
                {"role": "user", "content": f"Summarize the following messages:\n\n{formatted}"}
            ]
            summary = self.llm.chat(prompt)

        recent_str = "\n".join(f"{t['role']}: {t['content']}" for t in recent)
        return "\n\n".join(filter(None, [summary, recent_str]))

    def add_turn(self, agent_id: str, message: str, phase: str = "normal") -> str:
        """Adds message to STM and LTM, returns inserted ID. Now also generates and stores a summary."""
        # Generate summary using LLM
        summary_prompt = [
            {"role": "system", "content": "Summarize the following message in 100 tokens or less, preserving the main point and speaker intent. Use plain language. return only the summary. DO NOT include any extra information or context."},
            {"role": "user", "content": message}
        ]
        summary = self.llm.chat(summary_prompt)
        # Store message and summary in STM
        turn_id = self.stm.store_turn(agent_id, message, summary=summary)
        tags = ["turn"]
        if phase != "normal":
            tags.append(phase)
        self.ltm.store_memory(agent_id, message, tags=tags)
        return turn_id

    # ---------------------------------------------
    # Beliefs and Contradictions
    # ---------------------------------------------
    def save_belief(self, agent_id: str, belief_data: Dict = None, new_belief: str = None, max_memory: int = 10):
        self.belief.save_belief(
            agent_id=agent_id,
            new_belief=new_belief,
            belief_data=belief_data,
            max_memory=max_memory
        )

    def get_beliefs(self, agent_id: str) -> str:
        return self.belief.get_beliefs(agent_id)

    def get_contradictions(self, agent_id: str) -> str:
        doc = self.belief.collection.find_one({"agent_id": agent_id})
        if not doc:
            return ""
        
        # The contradictions field is already a formatted string
        contradictions_str = doc.get("contradictions", "")
        if not contradictions_str:
            return ""
            
        # Return the string directly - it's already formatted
        return contradictions_str

    # ---------------------------------------------
    # LTM and RAG retrieval
    # ---------------------------------------------
    def get_ltm(self, agent_id: str, limit: int = 5) -> List[Dict]:
        results = self.ltm.query_ltm(agent_id, limit=limit)
        return [{"role": "user", "content": line} for line in results.splitlines() if line.strip()]

    def get_rag(self, agent_id: str, limit: int = 5) -> str:
        return self.rag.query_rag(agent_id, limit)

    def query_rag(self, query: str, top_k: int = 5) -> str:
        return self.rag.query_text(query, top_k)
