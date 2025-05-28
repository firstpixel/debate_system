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

    def store_turn(self, agent_id: str, message: str, summary: str = None) -> str:
        doc = {
            "agent_id": agent_id,
            "message": message,
            "timestamp": datetime.utcnow()
        }
        if summary is not None:
            doc["summary"] = summary
        result = self.collection.insert_one(doc)
        return str(result.inserted_id)

    def get_recent_turns_raw(self, agent_id: str, limit: int = 20) -> List[Dict]:
        cursor = self.collection.find({"agent_id": agent_id}).sort("timestamp", -1).limit(limit)
        return list(reversed(list(cursor)))

    def get_all_turns_raw(self, agent_id: str) -> List[Dict]:
        cursor = self.collection.find({"agent_id": agent_id}).sort("timestamp", 1)
        return list(cursor)

    def get_all_turns_all_agents(self) -> List[Dict]:
        cursor = self.collection.find({}).sort("timestamp", 1)
        return list(cursor)

    def summarize_turns(self, agent_id: str, full_text: str) -> str:
        return full_text[:1000] + "..." if len(full_text) > 1000 else full_text


class BeliefStore:
    def __init__(self, db):
        self.collection = db["agent_beliefs"]

    def save_belief(self, agent_id: str, new_belief=None, max_memory: int = 10, belief_data: Dict = None):
        doc = self.collection.find_one({"agent_id": agent_id}) or {}
        all_beliefs = []

        if new_belief:
            all_beliefs.append(new_belief)
            belief_content = new_belief
        elif belief_data and "belief" in belief_data:
            all_beliefs.append(belief_data["belief"])
            belief_content = belief_data["belief"]
        else:
            belief_content = None

        if belief_content:
            update_data = {
                "all_beliefs": all_beliefs,
                "verbatim": all_beliefs[-max_memory:],
                "summary": doc.get("summary", ""),
                "updated_at": datetime.utcnow(),
            }

            if belief_data:
                for key in ["scores", "topic", "round", "turn_id", "contradictions"]:
                    if key in belief_data:
                        update_data[key] = belief_data[key]

            self.collection.update_one(
                {"agent_id": agent_id},
                {"$set": update_data},
                upsert=True
            )
            
    def save_belief(self, agent_id: str, new_belief: str = None, max_memory: int = 10, belief_data: Dict = None):
        if not new_belief and not (belief_data and "belief" in belief_data):
            return  # Nothing to save

        belief_str = new_belief or belief_data["belief"]

        # Prepare the new document — we replace everything.
        doc = {
            "agent_id": agent_id,
            "all_beliefs": belief_str,
            "verbatim": belief_str,
            "summary": belief_str,
            "updated_at": datetime.utcnow()
        }

        # Add optional metadata (e.g., contradictions)
        if belief_data:
            for key in ["scores", "topic", "round", "turn_id", "contradictions"]:
                if key in belief_data:
                    doc[key] = belief_data[key]

        # Replace the entire doc for this agent
        self.collection.replace_one(
            {"agent_id": agent_id},
            doc,
            upsert=True
        )

    def get_beliefs(self, agent_id: str) -> str:
        doc = self.collection.find_one({"agent_id": agent_id})
        if not doc:
            return ""

        result = []
        if "summary" in doc:
            result.append(doc["summary"])
        if "verbatim" in doc:
            result.extend(doc["verbatim"])
        return "\n".join(result)

    def get_contradictions(self, agent_id: str) -> str:
        doc = self.collection.find_one({"agent_id": agent_id})
        if not doc or "contradictions" not in doc:
            return ""
        return "\n".join(f"- {c}" for c in doc["contradictions"])
