from typing import List, Dict, Optional
from app.memory_manager import MemoryManager
from app.core_llm import LLMClient

MAX_VERBATIM_HISTORY = 5
MAX_SUMMARY_THRESHOLD = 6

SUPPORTED_STRATEGIES = {"rolling", "ltm", "rag", "belief"}
SUPPORTED_MODES = {"default", "judge", "delphi"}

class ContextBuilder:
    def __init__(
        self,
        topic: str,
        context_scope: str = "rolling",
        window_size: int = 10,
        memory: Optional[MemoryManager] = None,
        llm: Optional[LLMClient] = None
    ):
        self.topic = topic
        self.context_scope = context_scope
        self.window_size = window_size
        self.llm = llm
        self.memory = memory or MemoryManager()
        self._summary_cache: Dict[str, str] = {}

    def build_context_messages(self, agent_name: str, mode: str = "default") -> List[Dict]:
        messages = []

        system_prompt = self._get_system_prompt_for_mode(mode)
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt.strip()
            })

        summary = self._summary_cache.get(agent_name)
        if summary:
            messages.append({
                "role": "user",
                "content": f"🧠 Summary of previous rounds:\n{summary}"
            })

        turns = self._get_recent_turns(agent_name)
        turns = [t for t in turns if "message" in t or "content" in t]

        for turn in turns:
            speaker = turn.get("agent") or turn.get("name") or "unknown"
            message = turn.get("content") or turn.get("message") or ""
            role = self._get_role(agent_name, speaker, mode)

            messages.append({
                "role": role,
                "content": f"{speaker}: {message}"
            })

        return messages

    def set_strategy(self, strategy: str):
        if strategy in SUPPORTED_STRATEGIES:
            self.context_scope = strategy
        else:
            raise ValueError(f"Invalid memory strategy: {strategy}")

    def _get_recent_turns(self, agent_name: str) -> List[Dict]:
        if self.context_scope == "rolling":
            turns = self.memory.stm.get_recent_turns_raw(agent_id=agent_name, limit=self.window_size)

            if len(turns) > MAX_VERBATIM_HISTORY:
                to_summarize = turns[:-MAX_VERBATIM_HISTORY]
                if agent_name not in self._summary_cache:
                    self._summarize(agent_name, to_summarize)
                return turns[-MAX_VERBATIM_HISTORY:]

            return turns

        elif self.context_scope in {"ltm", "rag", "belief"}:
            context = self.memory.get_context(agent_name, strategy=self.context_scope)
            return self._format_text_as_turns(context)

        return []

    def _format_text_as_turns(self, text: str) -> List[Dict]:
        turns = []
        for line in text.splitlines():
            if ": " in line:
                speaker, content = line.split(": ", 1)
                turns.append({"agent": speaker.strip(), "content": content.strip()})
        return turns

    def _summarize(self, agent_name: str, turns: List[Dict]):
        if not self.llm or len(turns) < MAX_SUMMARY_THRESHOLD:
            return

        text = "\n".join(f"{t['agent']}: {t['content']}" for t in turns if "content" in t)
        prompt = [
            {"role": "system", "content": "Summarize the debate so far using Markdown bullet points."},
            {"role": "user", "content": text}
        ]

        summary = ""
        for token in self.llm.stream_chat(prompt):
            summary += token

        self._summary_cache[agent_name] = summary.strip()

    def _get_system_prompt_for_mode(self, mode: str) -> str:
        if mode == "judge":
            return (
                "You are a neutral judge. Your task is to evaluate the arguments presented so far "
                "and make observations about clarity, logic, and consistency without taking sides."
            )
        elif mode == "delphi":
            return (
                "You are participating in a Delphi method consensus round. Read previous arguments, "
                "then provide your own anonymous input or revise your opinion based on others. "
                "Do not refer to yourself or to others directly. Focus on collective reasoning."
            )
        elif mode == "default":
            return f"You are Agent {self.topic}. Engage in reasoned debate based on the memory and current context."
        return ""

    def _get_role(self, agent_name: str, speaker_name: str, mode: str) -> str:
        if mode in {"judge", "delphi"}:
            return "user"
        return "assistant" if speaker_name == agent_name else "user"
