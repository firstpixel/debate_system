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
        Constructs the full message history to be sent to the LLM using the agent's tracker only.
        Dynamically allocates context space based on available tokens.
        """
        messages = []
        available_tokens = self.context_length - self.response_reserve
        
        # Calculate token allocations
        token_allocations = self._calculate_token_allocations(available_tokens)
        
        logger.info(f"Context allocations for {agent_name}: {token_allocations}")
        
        # Optional system message per mode
        system_prompt = self._get_system_prompt_for_mode(mode)
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt.strip()
            })
            token_allocations["system"] -= self._estimate_tokens(system_prompt)

        # Include agent's beliefs from tracker (with token limits)
        # beliefs = tracker.get_beliefs()
        # if beliefs:
        #     belief_text = self._truncate_to_token_limit(
        #         f"🧠 Belief Summary:\n" + "\n".join(beliefs or []), 
        #         token_allocations["beliefs"]
        #     )
        #     messages.append({
        #         "role": "user",
        #         "content": belief_text
        #     })
        
        # Include LTM context if available tokens
        if token_allocations.get("ltm", 0) > 0:
            ltm_context = tracker.get_ltm_context(limit=5)  # Adjust limit based on content size
            if ltm_context:
                ltm_text = self._truncate_to_token_limit(
                    f"🌟 Long-Term Memory:\n{ltm_context}", 
                    token_allocations["ltm"]
                )
                messages.append({
                    "role": "user", 
                    "content": ltm_text
                })
        
        # Include RAG context if available tokens
        if token_allocations.get("rag", 0) > 0:
            rag_context = tracker.get_rag_context(limit=3)  # Adjust limit based on content size
            if rag_context:
                rag_text = self._truncate_to_token_limit(
                    f"📚 Knowledge Context:\n{rag_context}", 
                    token_allocations["rag"]
                )
                messages.append({
                    "role": "user",
                    "content": rag_text
                })
                
        # Add recent memory messages with remaining token allocations
        remaining_tokens = token_allocations.get("stm", 0)
        recent_messages = self._get_recent_messages_within_limit(
            tracker, agent_name, remaining_tokens
        )
        
        messages.extend(recent_messages)
        
        # Log final context size
        total_tokens = sum(self._estimate_tokens(m["content"]) for m in messages)
        logger.info(f"Final context size for {agent_name}: ~{total_tokens} tokens")
        
        # Adjust token distribution for different modes
        if mode == "delphi" or mode == "mediator":
            self.distribution_ratios.update({
                "beliefs": 0.05,    # Reduce belief context
                "stm": 0.60,        # Increase dialogue history
                "ltm": 0.05,        # Reduce LTM
                "rag": 0.05,        # Reduce RAG
                "system": 0.15,     # Increase system prompt
                "reserves": 0.10    # Keep some reserve
            })
            # Increase response reserve for synthesis
            self.response_reserve = int(self.context_length * 0.40)  # 40% for response
    
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
    
    def _truncate_to_token_limit(self, text: str, token_limit: int) -> str:
        """Truncate text to stay within token limit, preserving important content."""
        estimated_tokens = self._estimate_tokens(text)
        
        if estimated_tokens <= token_limit:
            return text
            
        # For bullet lists, try to keep whole bullets
        if text.startswith("🧠 Belief Summary") or "•" in text:
            lines = text.split("\n")
            header = lines[0]
            bullets = lines[1:]
            
            result = [header]
            current_tokens = self._estimate_tokens(header)
            
            for bullet in bullets:
                bullet_tokens = self._estimate_tokens(bullet)
                if current_tokens + bullet_tokens <= token_limit:
                    result.append(bullet)
                    current_tokens += bullet_tokens
                else:
                    break
                    
            return "\n".join(result)
            
        # Simple truncation with ellipsis for other text
        char_limit = token_limit * 4  # Approximate char to token conversion
        return text[:char_limit] + "..." if len(text) > char_limit else text
        
    def _get_recent_messages_within_limit(
        self, tracker: AgentStateTracker, agent_name: str, token_limit: int
    ) -> List[Dict]:
        """Get summarized short-term memory within token limit."""
        
        # Use summarized memory for longer conversations
        if self.context_scope in ["full", "summarized"]:
            # Get summarized STM that fits in token limit
            summarized_content = self.get_summarized_stm(tracker, agent_name, token_limit)
            
            if summarized_content:
                return [{
                    "role": "user",
                    "content": f"📝 Conversation Summary:\n{summarized_content}"
                }]
        
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

    def get_summarized_stm(self, tracker: AgentStateTracker, agent_name: str, token_limit: int) -> str:
        """Get summarized short-term memory that fits within token limit."""
        memory_mgr = tracker.memory
        summarized = memory_mgr.summarize_memory(agent_name, preserve_last_n=5)
        return self._truncate_to_token_limit(summarized, token_limit)

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
