# app/performance_logger.py

import time
from typing import Dict, List
from app.session_recovery import save_json

class PerformanceLogger:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logs: List[Dict] = []

    def log_turn(self, agent: str, duration_sec: float):
        self.logs.append({
            "agent": agent,
            "duration_sec": round(duration_sec, 3)
        })

    def get_stats(self) -> Dict:
        by_agent = {}
        for entry in self.logs:
            a = entry["agent"]
            by_agent.setdefault(a, []).append(entry["duration_sec"])

        return {
            "per_agent_avg_time": {a: round(sum(times)/len(times), 3) for a, times in by_agent.items()},
            "total_turns": len(self.logs),
            "total_time_sec": round(sum(entry["duration_sec"] for entry in self.logs), 3)
        }

    def save(self):
        path = f"sessions/{self.session_id}/performance_log.json"
        save_json({
            "log": self.logs,
            "summary": self.get_stats()
        }, path)
