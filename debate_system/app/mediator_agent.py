# app/mediator_agent.py
"""
Provides mediator functionality for debate sessions. 
This agent can take different roles in facilitation beyond what the Delphi engine provides.
Currently not actively used in the main debate flow, but provides functionality for:
- Active mediation/intervention
- Judging and scoring arguments
- Summarizing debate points
- Facilitating consensus (overlaps with Delphi engine)

The "delphi_facilitator" mode overlaps with the standalone Delphi engine implementation.
"""

from typing import List, Dict
from app.core_llm import LLMClient

class MediatorAgent:
    def __init__(self, mode: str = "silent", model: str = "gemma3:latest", temperature: float = 0.7):
        self.mode = mode.lower()
        self.llm = LLMClient(model=model, temperature=temperature)

    def should_interject(self) -> bool:
        return self.mode in ["active", "judge", "summarizer"]

    def generate_response(self, round_history: List[Dict], current_topic: str) -> str:
        if self.mode == "silent":
            return ""

        if not round_history:
            return ""

        prompt = self._build_prompt(round_history, current_topic)

        # The mediator's response IS shown in the UI, so we'll keep the streaming call
        response = ""
        for token in self.llm.stream_chat(prompt):
            print(token, end="", flush=True)
            response += token

        return response

    def _build_prompt(self, history: List[Dict], topic: str) -> List[Dict]:
        system_map = {
            "active": "You are an active debate mediator. Intervene when needed to clarify the argument or resolve conflicts. Respond in Markdown.",
            "judge": "You are a judge agent. Score each argument based on clarity, logic, and persuasiveness. Respond with a Markdown table or bullet points.",
            "summarizer": "You are a neutral debate summarizer. Summarize all arguments so far in bullet points. Be objective.",
        }

        messages = [
            {"role": "system", "content": system_map.get(self.mode, "You are a neutral debate observer.")},
            {"role": "user", "content": f"Debate Topic: **{topic}**\n\nDebate Transcript:\n\n" + self._render_history(history)}
        ]

        return messages

    def _render_history(self, history: List[Dict]) -> str:
        return "\n".join(f"**{entry['agent']}**: {entry['content']}" for entry in history)
