from pymongo import MongoClient
from typing import List, Dict
from datetime import datetime
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "debate_engine"

class STMStore:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db["short_term_memory"]

    def store_turn(self, agent_id: str, message: str) -> str:
        doc = {
            "agent_id": agent_id,
            "message": message,
            "timestamp": datetime.utcnow()
        }
        result = self.collection.insert_one(doc)
        return str(result.inserted_id)

    def get_recent_turns(self, agent_id: str, limit: int = 5) -> str:
        cursor = self.collection.find({"agent_id": agent_id}).sort("timestamp", -1).limit(limit)
        turns = list(cursor)
        return "\n".join([t["message"] for t in reversed(turns)])

    def summarize_turns(self, agent_id: str, full_text: str) -> str:
        return full_text[:1000] + "..." if len(full_text) > 1000 else full_text

    def get_recent_turns_raw(self, agent_id: str, limit: int = 20) -> List[Dict]:
        cursor = self.collection.find({"agent_id": agent_id}).sort("timestamp", -1).limit(limit)
        turns = list(cursor)
        return list(reversed(turns))

    def get_all_turns_raw(self, agent_id: str) -> List[Dict]:
        cursor = self.collection.find({"agent_id": agent_id}).sort("timestamp", 1)
        return list(cursor)

class BeliefStore:
    def __init__(self, db):
        self.collection = db["agent_beliefs"]

    def save_full_belief(self, agent_id: str, new_belief: str, summary_generator=None, max_memory: int = 10):
        doc = self.collection.find_one({"agent_id": agent_id}) or {}
        all_beliefs = doc.get("all_beliefs", [])
        all_beliefs.append(new_belief)

        verbatim = all_beliefs[-max_memory:]
        overflow = all_beliefs[:-max_memory]
        summary = doc.get("summary", "")

        if overflow and summary_generator:
            summary = summary_generator(overflow)

        self.collection.update_one(
            {"agent_id": agent_id},
            {
                "$set": {
                    "all_beliefs": all_beliefs,
                    "verbatim": verbatim,
                    "summary": summary,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )

    def get_belief_summary(self, agent_id: str) -> str:
        doc = self.collection.find_one({"agent_id": agent_id})
        if not doc:
            return "No belief stored."

        lines = []
        summary = doc.get("summary", "")
        verbatim = doc.get("verbatim", [])

        if summary:
            lines.append("## 📌 Summary of Older Beliefs")
            lines.append(summary.strip())
        if verbatim:
            lines.append("\n## 🧠 Recent Beliefs")
            lines += [f"- {b}" for b in verbatim]

        return "\n".join(lines)

    def get_all_beliefs(self, agent_id: str):
        doc = self.collection.find_one({"agent_id": agent_id})
        return doc.get("all_beliefs", []) if doc else []

    def reset_beliefs(self, agent_id: str):
        self.collection.delete_one({"agent_id": agent_id})

    def append_belief(self, agent_id: str, belief: str):
        self.collection.insert_one({
            "agent_id": agent_id,
            "belief": belief,
            "timestamp": datetime.utcnow()
        })

    def get_raw_beliefs(self, agent_id: str) -> List[str]:
        cursor = self.collection.find({"agent_id": agent_id}).sort("timestamp", 1)
        return [doc["belief"] for doc in cursor if "belief" in doc]

    def get_beliefs(self, agent_id: str) -> str:
        cursor = self.collection.find({"agent_id": agent_id})
        return "\n".join(doc.get("belief", "") for doc in cursor if "belief" in doc)

    def save_belief(self, agent_id: str, belief: Dict):
        latest = list(self.collection.find({"agent_id": agent_id}).sort("belief_version", -1).limit(1))
        latest_version = latest[0].get("belief_version", 0) if latest else 0

        new_version = latest_version + 1

        self.collection.insert_one({
            "agent_id": agent_id,
            "belief": belief.get("belief", ""),
            "scores": belief.get("scores", {}),
            "topic": belief.get("topic", ""),
            "round": belief.get("round", None),
            "turn_id": belief.get("turn_id", None),
            "belief_version": new_version,
            "timestamp": datetime.utcnow()
        })
