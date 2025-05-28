from typing import List, Dict, Tuple, Optional
import os
from app.agent_state_tracker import AgentStateTracker
import logging

logger = logging.getLogger(__name__)

SUPPORTED_MODES = {"default", "judge", "delphi"}

# Default context sizes if not specified in environment
DEFAULT_CONTEXT_LENGTH = 4096
DEFAULT_RESPONSE_RESERVE = 1024  # Reserve space for response

class ContextBuilder:
    def __init__(
        self,
        topic: str,
        context_scope: str = "rolling",
        window_size: int = 10
    ):
        self.topic = topic
        self.context_scope = context_scope
        self.window_size = window_size
        self.context_length = int(os.environ.get("OLLAMA_CONTEXT_LENGTH", DEFAULT_CONTEXT_LENGTH))
        self.response_reserve = int(os.environ.get("RESPONSE_RESERVE_TOKENS", DEFAULT_RESPONSE_RESERVE))

    def build_context_messages(self, agent_name: str, tracker: AgentStateTracker, mode: str = "default") -> List[Dict]:
        """
        Constructs the full message history for the LLM, enforcing token limits:
          - Adds a summary of all rounds except the last 3 per persona (if available)
          - Adds the previous 3 messages from each persona (full messages)
          - Sets role: 'user' for the requesting agent, 'assistant' for others
        """
        messages = []
        available_tokens = self.context_length - self.response_reserve

        # Gather all messages from STM only
        if hasattr(tracker, "memory") and hasattr(tracker.memory.stm, "get_all_turns_all_agents"):
            all_msgs = tracker.memory.stm.get_all_turns_all_agents()
        else:
            all_msgs = []

        # Group messages by agent
        from collections import defaultdict, deque
        persona_msgs = defaultdict(deque)
        for msg in all_msgs:
            agent = msg.get("agent_id")
            if agent and msg.get("message"):
                persona_msgs[agent].append(msg)

        # For each persona, keep only the last 3 messages
        last_msgs = []
        for persona, msgs in persona_msgs.items():
            last_msgs.extend(list(msgs)[-3:])

        # Sort last_msgs by their order in all_msgs
        last_msgs = sorted(last_msgs, key=lambda m: all_msgs.index(m))
        last_msg_ids = set(id(m) for m in last_msgs)

        persona_count = len(persona_msgs)
        # Only build and add summary if every persona has at least 3 messages and total messages > persona_count * 3
        if all(len(msgs) >= 3 for msgs in persona_msgs.values()) and len(all_msgs) > persona_count * 3:
            # The rest are for summary
            summary_msgs = [m for m in all_msgs if id(m) not in last_msg_ids]

            # Build the summary string in the requested format
            summary_lines = []
            for m in summary_msgs:
                agent = m.get("agent_id")
                # Use summary if present, else fall back to content
                content = m.get("summary")
                if agent == agent_name:
                    summary_lines.append(f"I: {content}")
                else:
                    summary_lines.append(f"{agent}: {content}")
            summary_str = "\n".join(summary_lines)
            if summary_str:
                messages.append({
                    "role": "assistant",
                    "content": f"Summary of conversation so far:\n{summary_str}"
                })

        # Add the last 3 messages per persona as full messages, with correct roles
        for m in last_msgs:
            agent = m.get("agent_id")
            content = m.get("message", "")
            role = "assistant" if agent == agent_name else "user"
            messages.append({
                "role": role,
                "content": content
            })

        # Enforce token limit
        total_tokens = 0
        limited_messages = []
        for m in messages:
            msg_tokens = self._estimate_tokens(m["content"])
            if total_tokens + msg_tokens > available_tokens:
                break
            limited_messages.append(m)
            total_tokens += msg_tokens

        logger.info(f"Final context size for {agent_name}: ~{total_tokens} tokens")
        return limited_messages

    def _estimate_tokens(self, text: str) -> int:
        """Rough estimation of tokens in text (4 chars ~= 1 token for English text)."""
        return len(text) // 4

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
            return f"You are Agent {self.topic}. Engage in reasoned debate based on the beliefs, memory and current context. Avoid contradictions."
        return ""

    def _get_role(self, agent_name: str, speaker_name: str, mode: str) -> str:
        if mode in {"judge", "delphi"}:
            return "user"
        return "assistant" if speaker_name == agent_name else "user"

    # For compatibility with tests and legacy code
    def build_prompt(self, agent_name: str, agent_role: str, last_turns: list, tracker: AgentStateTracker) -> List[Dict]:
        """
        Legacy/test compatibility: builds a prompt with a system message and user turns.
        """
        system_prompt = f"You are {agent_name}, role: {agent_role}. Debate context: {self.topic}"
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        # Add last turns as user messages
        for msg in last_turns:
            messages.append({
                "role": "user", "content": f"{msg['agent']}: {msg['content']}"
            })
        return messages
