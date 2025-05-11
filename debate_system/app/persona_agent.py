import logging
import time
from typing import Callable, List, Dict, Optional
import numpy as np

from app.core_llm import LLMClient
from app.agent_state_tracker import AgentStateTracker
from app.contradiction_detector import ContradictionDetector
from app.context_builder import ContextBuilder
from app.discussion_lens import DiscussionLens

logger = logging.getLogger(__name__)

class PersonaAgent:
    def __init__(self, name: str, role: str, temperature: float = 0.7, model: str = "gemma3:latest"):
        self.name = name
        self.role = role
        self.temperature = temperature
        self.model = model
        self.llm = LLMClient(model=self.model, temperature=self.temperature)

        self.tracker = AgentStateTracker(agent_name=name, model=model, temperature=temperature)
        self.bayesian_tracker = None
        self.context_builder = None
        self.perf_logger = None
        self.contradiction_checker = ContradictionDetector()

    def _compose_system_prompt(self, topic: str, opponent_argument: str = "") -> str:
        beliefs = self.tracker.memory_cache["beliefs"]
        contradiction_warning = self.tracker.last_contradiction()

        prompt = (
            f"""
You are {self.name}, acting as a {self.role} in a formal debate.
Debate topic: "{topic}".

**Debate Protocol (follow strictly):**

1. **Length & Structure**
   • Max 150 tokens per turn.  
   • Begin with a one-sentence *definition* of any key term you'll rely on.  
   • Then supply up to **3 numbered points** (≤40 tokens each).  
   • End with:  
     - one concrete policy or experiment suggestion, and  
     - **one direct question** for your opponent.

2. **Steel-man Rule**
   • *Before* rebutting, restate your opponent's strongest recent point in ≤40 tokens and concede any part you find reasonable.

3. **Evidence**
   • For every factual claim include a parenthetical citation hint, try to find evidence from the last 5 years.:  
     `(source: WHO cancer study 2022)` or `(stat: McKinsey 2023 automation report)`.
    • If you can't find evidence, say so and use reasoning to prove the claim. `if a is true, then b is true.`

4. **Tone & Language**
   • No ad-hominem, motive-ascription, or loaded adjectives (e.g., “delusional,” “nihilistic”).  
   • First-person singular (“I”) and professional tone.  
   • Use plain language; avoid rhetorical flourishes, stage directions, and dramatic parentheses.
   • Make your argument clear and concise, avoiding unnecessary jargon.
   • Avoid repeating phrases or ideas from previous turns, unless it's from opponent's argument.

5. **Progress Checkpoint**
   • After two full exchanges on the same sub-topic, pivot: introduce *new* evidence or propose synthesis.

6. **Failure Modes—avoid:**  
   • Repetition of phrases across turns.  
   • Over 10% duplicate tokens with previous output (n-gram overlap >4).  
   • Vacuous “I agree/disagree” without novel reasoning.

7. **Beliefs, Contradictions and Coherence**
   • Anchor your answers on your past positions, and do not contradict your beliefs.
   • Keep your self coherent
   • Prevent contradictions by checking your beliefs, do not contradict your beliefs.
"""
        )

        if contradiction_warning:
            prompt += f"\n⚠️ Contradiction Alert:\n{contradiction_warning.strip()}\n"

        if opponent_argument:
            prompt += f"\n## Your Opponent's Last Statement:\n> {opponent_argument.strip()}"

        prompt += f"\n## Your Current Beliefs:\n{beliefs.strip()}"
        return prompt

    def interact(
        self,
        user_prompt: str,
        opponent_argument: str = "",
        debate_history: List[Dict] = [],
        topic: str = "",
        stream_callback: Optional[Callable[[str], None]] = None
    ) -> str:

        logger.info(f"########### Agent {self.name} interacting with prompt: {user_prompt}")
        
        # Save user prompt to STM
        self.tracker.save_message_to_stm(user_prompt, speaker="User")
        
        # Save opponent's argument to STM if provided
        if opponent_argument:
            self.tracker.save_message_to_stm(opponent_argument, speaker="Opponent")

        self.system_prompt = self._compose_system_prompt(topic, opponent_argument)

        if not self.context_builder:
            self.context_builder = ContextBuilder(
                topic=topic,
                context_scope="rolling",
                window_size=4
            )

        context_messages = self.context_builder.build_context_messages(
            agent_name=self.name,
            tracker=self.tracker,
            mode="default"
        )

       

        messages = [{"role": "system", "content": self.system_prompt}] + context_messages
        messages.append({"role": "user", "content": user_prompt})


        logger.debug(f"Messages sent to LLM: {messages}")

        response = ""
        start = time.time()
        for token in self.llm.stream_chat(messages):
            print(token, end="", flush=True)
            response += token
            if stream_callback:
                stream_callback(token)
        end = time.time()

        if self.perf_logger:
            self.perf_logger.log_turn(self.name, end - start)

        # Update belief memory
        self.tracker.save_belief(response)

        # Save the complete message to STM
        self.tracker.save_message_to_stm(response, speaker=self.name)

        # Optionally identify and save important parts to LTM
        important_parts = self._extract_important_info(response)
        if important_parts:
            for part in important_parts:
                self.tracker.save_to_ltm(part)

        logger.debug(f"[{self.name}] Response: {response}")
        return response

    def _extract_important_info(self, text: str) -> List[str]:
        """Extract important information from a response for long-term memory."""
        important_parts = []
        
        # Split text into sentences
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        for sentence in sentences:
            # Check for citations
            if '(source:' in sentence.lower() or '(stat:' in sentence.lower():
                important_parts.append(sentence + '.')
            
            # Check for policy suggestions or experimental designs
            if any(keyword in sentence.lower() for keyword in ['policy', 'experiment', 'suggest']):
                important_parts.append(sentence + '.')
                
            # Check for definitions (usually at the beginning of debates)
            if any(keyword in sentence.lower() for keyword in ['define', 'definition', 'means']):
                important_parts.append(sentence + '.')
        
        return important_parts


