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
        
        # Get context length from environment or use default
        self.context_length = int(os.environ.get("OLLAMA_CONTEXT_LENGTH", DEFAULT_CONTEXT_LENGTH))
        self.response_reserve = int(os.environ.get("RESPONSE_RESERVE_TOKENS", DEFAULT_RESPONSE_RESERVE))
        
        # Default distribution ratios (can be adjusted)
        self.distribution_ratios = {
            "beliefs": 0.15,      # 15% for belief state
            "stm": 0.40,          # 40% for short-term memory
            "ltm": 0.15,          # 15% for long-term memory
            "rag": 0.15,          # 15% for RAG context
            "system": 0.05,       # 5% for system message
            "reserves": 0.10      # 10% reserve for flexibility
        }
        
        # These can be customized based on context_scope
        if context_scope == "belief-focused":
            self.distribution_ratios.update({
                "beliefs": 0.40, "stm": 0.25, "ltm": 0.10, "rag": 0.10
            })
        elif context_scope == "rag-enhanced":
            self.distribution_ratios.update({
                "beliefs": 0.10, "stm": 0.25, "ltm": 0.10, "rag": 0.40
            })
        elif context_scope == "full":
            self.distribution_ratios.update({
                "beliefs": 0.15, "stm": 0.30, "ltm": 0.25, "rag": 0.15
            })

    def build_context_messages(self, agent_name: str, tracker: AgentStateTracker, mode: str = "default") -> List[Dict]:
        """
        Constructs the full message history for the LLM:
          - Adds a summary of all rounds except the last 5 (if available)
          - Adds the previous 5 messages from all agents
          - Sets role: 'user' for the requesting agent, 'assistant' for others
        """
        messages = []
        available_tokens = self.context_length - self.response_reserve

        # Calculate token allocations
        token_allocations = self._calculate_token_allocations(available_tokens)
        logger.info(f"Context allocations for {agent_name}: {token_allocations}")

        # 1. Add summary of all rounds except the last 5
        if hasattr(tracker, "get_total_rounds") and hasattr(tracker, "get_summary_of_rounds"):
            total_rounds = tracker.get_total_rounds()
            if total_rounds > 5:
                summary = tracker.get_summary_of_rounds(1, total_rounds - 5)
                if summary:
                    messages.append({
                        "role": "user",
                        "content": f"Summary of rounds 1 to {total_rounds - 5}:\n{summary}"
                    })

        # 2. Add previous 5 messages from all agents, with correct roles
        if hasattr(tracker, "get_recent_messages"):
            recent_messages = tracker.get_recent_messages(limit=5)
            for msg in recent_messages:
                speaker = msg.get("speaker", "")
                content = msg.get("content", "")
                # Set role: 'user' if this is the requesting agent, else 'assistant'
                role = "user" if speaker == agent_name else "assistant"
                messages.append({
                    "role": role,
                    "content": content
                })

        # Log final context size
        total_tokens = sum(self._estimate_tokens(m["content"]) for m in messages)
        logger.info(f"Final context size for {agent_name}: ~{total_tokens} tokens")

        return messages

    def _calculate_token_allocations(self, available_tokens: int) -> Dict[str, int]:
        """Calculate token allocations based on distribution ratios and available tokens."""
        allocations = {}
        for key, ratio in self.distribution_ratios.items():
            allocations[key] = int(available_tokens * ratio)
        return allocations
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough estimation of tokens in text (4 chars ~= 1 token for English text)."""
        return len(text) // 4
    
        
    def _get_recent_messages_within_limit(
        self, tracker: AgentStateTracker, agent_name: str, token_limit: int
    ) -> List[Dict]:
        """Get summarized short-term memory within token limit."""
        
        
        # Fall back to original approach for shorter conversations or other scopes
        all_turns = tracker.get_recent_messages(limit=self.window_size)
        
        result = []
        tokens_used = 0
        
        for msg in all_turns:
            # Extract content and determine role
            content = msg.get("content", "")
            role = msg.get("role", "user")  # Default to user if role not specified
            
            # Calculate token usage
            msg_tokens = self._estimate_tokens(content)
            
            if tokens_used + msg_tokens <= token_limit:
                result.append({
                    "role": role,
                    "content": content
                })
                tokens_used += msg_tokens
            else:
                # If we can't fit any more full messages, break
                break
            
        return result



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
