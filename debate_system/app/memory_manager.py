# app/memory_manager.py

from datetime import datetime
from typing import List, Dict, Literal
import os
from pymongo import MongoClient
from memory.mongo_store import STMStore, BeliefStore
from memory.qdrant_store import LTMStore, RAGRetriever
from memory.embeddings import embed_text
from app.core_llm import LLMClient  # ensure this is instantiated somewhere, e.g., at the module level


class MemoryManager:
    def __init__(self):
        client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
        db = client["debate_engine"]
        self.db = db
        self.stm = STMStore()
        self.belief = BeliefStore(db)
        self.ltm = LTMStore()
        self.rag = RAGRetriever()
        self.llm = LLMClient()

    def add_turn(self, agent_id: str, message: str) -> str:
        turn = {
            "agent_id": agent_id,
            "message": message,
            "timestamp": datetime.utcnow()
        }
        result = self.stm.collection.insert_one(turn)
        self.ltm.store_memory(agent_id, message, tags=["turn"])
        return str(result.inserted_id)


    def summarize(self, agent_id: str) -> str:
        history = self.stm.get_recent_turns(agent_id)
        return self.stm.summarize_turns(agent_id, history)
    
    
    
    def summarize_memory(self, agent_id: str, preserve_last_n: int = 5) -> str:
        # Use the new get_all_turns_raw method
        all_turns = self.stm.get_all_turns_raw(agent_id)

        if not all_turns:
            return "No memory available."

        if len(all_turns) <= preserve_last_n:
            recent = all_turns
            older = []
        else:
            older = all_turns[:-preserve_last_n]
            recent = all_turns[-preserve_last_n:]

        summary_text = ""
        if older:
            # Map fields to expected format
            formatted_older = "\n".join(f"{t.get('agent_id', t.get('agent', ''))}: {t.get('message', t.get('content', ''))}" for t in older)
            summary_prompt = [
                {"role": "system", "content": "You are a helpful memory summarizer for a debate system."},
                {"role": "user", "content": f"Summarize the following past messages for context:\n\n{formatted_older}"}
            ]
            summary_text = self.llm.chat(summary_prompt)

        recent_text = "\n".join(f"{t.get('agent_id', t.get('agent', ''))}: {t.get('message', t.get('content', ''))}" for t in recent)

        return "\n\n".join(part for part in [summary_text, recent_text] if part.strip())


    def query_rag(self, query: str) -> str:
        return self.rag.query_text(query)

    def save_belief(self, agent_id: str, belief: Dict):
        self.belief.save_belief(agent_id, belief)


    def get_context(self, agent_id: str, strategy: str = "rolling") -> str:
        if strategy == "rolling":
            turns = self.stm.get_recent_turns_raw(agent_id, limit=10)
            return "\n".join(f"{t['agent']}: {t['content']}" for t in turns)
        elif strategy == "ltm":
            return self.ltm.query_ltm(agent_id)
        elif strategy == "rag":
            return self.rag.query_rag(agent_id)
        elif strategy == "belief":
            return self.belief.get_beliefs(agent_id)
        else:
            return ""

