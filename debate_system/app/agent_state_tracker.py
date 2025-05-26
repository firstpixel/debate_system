# app/agent_state_tracker.py

import datetime
from typing import List, Dict
from venv import logger
from app.core_llm import LLMClient
from app.contradiction_detector import ContradictionDetector
from app.memory_manager import MemoryManager


class AgentStateTracker:

    def __init__(self,
                 agent_name: str,
                 model: str = "gemma3:latest",
                 temperature: float = 0.5):
        self.agent_name = agent_name
        self.llm = LLMClient(model=model, temperature=temperature)
        self.contradiction_detector = ContradictionDetector()
        self.memory = MemoryManager()
        self._last_contradiction_msg: str = ""
        self.stm = []

        # Cache full context for startup or debugging (can be used in UI)
        self.memory_cache: Dict[str, str] = {
            "beliefs": self.memory.get_beliefs(agent_name),
            "contradictions": self.memory.get_contradictions(agent_name),
            "ltm_context": self.get_ltm_context(),
            "rag_context": self.get_rag_context()
        }

    # ------------------------------
    # Memory Access Wrappers
    # ------------------------------

    def get_beliefs(self) -> List[str]:
        return [
            line.lstrip("•").strip()
            for line in self.memory_cache["beliefs"].splitlines()
            if line.strip().startswith("•")
        ]

    def get_contradictions(self) -> str:
        return self.memory.get_contradictions(self.agent_name)

    def last_contradiction(self) -> str:
        return self._last_contradiction_msg

    def get_ltm_context(self, limit: int = 5) -> str:
        """Returns long-term memory as a single markdown string."""
        messages = self.memory.get_ltm(self.agent_name, limit)
        return "\n".join([m["content"] for m in messages])

    def get_rag_context(self, limit: int = 5) -> str:
        return self.memory.get_rag(self.agent_name, limit)

    def get_recent_messages(self, limit: int = 10) -> List[Dict]:
        raw_turns = self.memory.stm.get_recent_turns_raw(agent_id=self.agent_name, limit=limit)
        return [
            {
                "role": "assistant" if turn["agent_id"] == self.agent_name else "user",
                "content": turn.get("message", ""),
            }
            for turn in raw_turns
            if "message" in turn
        ]

    # ------------------------------
    # Belief Handling & Save
    # ------------------------------

    def save_belief(self, new_message: str) -> Dict:
        extracted_bullets = self._extract_bullet_beliefs(new_message)
        current_beliefs = self.get_beliefs()
        merged = self._merge_beliefs_llm(extracted_bullets, current_beliefs)

        contradictions: Dict[str, Dict] = {}
        for bullet in merged:
            conflicts = self.contradiction_detector.find_contradictions(bullet, current_beliefs)
            if conflicts:
                verify_msg = self.contradiction_detector.verify_with_llm(bullet, conflicts)
                contradictions[bullet] = {
                    "conflicts": conflicts,
                    "verification": verify_msg
                }
                self._last_contradiction_msg = verify_msg

        belief_md = "\n".join(f"• {b}" for b in merged)
        contradiction_md = "\n".join(
            f"• {b} ⟶ Conflicts: {', '.join(v['conflicts'])}\n  ↳ {v['verification']}"
            for b, v in contradictions.items()
        )

        self.memory.save_belief(
            agent_id=self.agent_name,
            new_belief=belief_md,
            belief_data={"contradictions": contradiction_md}
        )

        # Update snapshot cache
        self.memory_cache["beliefs"] = belief_md
        self.memory_cache["contradictions"] = contradiction_md

        return {
            "beliefs": len(merged),
            "contradictions": len(contradictions)
        }

    def save_message_to_stm(self, message: str, speaker: str = None) -> None:
        """Save a message to short-term memory (STM)."""
        if not speaker:
            speaker = self.agent_name

        # Check if message is already in JSON format (appears to be a string representation of a dict)
        if message.startswith("{") and "agent_id" in message and "message" in message:
            try:
                import json
                # Try to parse it as JSON
                message_obj = json.loads(message)
                actual_message = message_obj.get("message", message)
                # Use the extracted message instead of the whole JSON string
                message = actual_message
            except json.JSONDecodeError:
                # If it's not valid JSON, use the message as is
                pass


        # Save to MongoDB via memory manager
        self.memory.stm.store_turn(self.agent_name, message)

        logger.info(f"Saved message from {speaker} to STM for agent {self.agent_name}")

    def save_to_ltm(self, content: str, importance: float = 0.7) -> None:
        """Save important information to long-term memory (LTM)."""
        # Save to Qdrant via memory manager
        # Convert importance to tags
        importance_tag = "high_importance" if importance > 0.7 else "medium_importance"
        tags = ["memory", importance_tag]
        
        self.memory.ltm.store_memory(
            agent_id=self.agent_name,  # Use agent_name not agent_id
            text=content,
            tags=tags
        )

        logger.info(f"Saved important information to LTM for agent {self.agent_name}")

    # ------------------------------
    # Belief Extraction & Merge
    # ------------------------------

    def _extract_bullet_beliefs(self, text: str) -> List[str]:
        prompt = [
            {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ]
        raw = self.llm.chat(prompt)
        return [
            line.lstrip("•").strip()
            for line in raw.splitlines()
            if line.strip().startswith("•")
        ]

    def _merge_beliefs_llm(self, new_beliefs: List[str], existing_beliefs: List[str]) -> List[str]:
        if not new_beliefs:
            return existing_beliefs

        prompt = [
            {"role": "system", "content": _MERGE_PROMPT},
            {"role": "user",
             "content":
                 "EXISTING:\n" + "\n".join(f"• {b}" for b in existing_beliefs) +
                 "\n\nNEW:\n" + "\n".join(f"• {b}" for b in new_beliefs)
             }
        ]
        merged_text = self.llm.chat(prompt)

        return [
            ln.lstrip("•").strip()
            for ln in merged_text.splitlines()
            if ln.strip().startswith("•")
        ]

    def summary(self) -> str:
        return "\n".join([
            "## 🧠 Beliefs",
            self.memory_cache.get("beliefs", "").strip(),
            self.memory_cache.get("contradictions", "").strip()
        ])
        
        
    def get_total_rounds(self) -> int:
        # Suppose self.stm is a list of all messages in order
        return len(self.stm)

    def get_summary_of_rounds(self, start: int, end: int) -> str:
        # Summarize messages from self.stm[start-1:end]
        # For now, just join their content as a placeholder
        relevant = self.stm[start-1:end]
        return "\n".join(msg["content"] for msg in relevant)

# -------------------------------------------------------------------------
# Prompt constants
# -------------------------------------------------------------------------
# _EXTRACTION_SYSTEM_PROMPT = """### TASK: Extract Belief Statements as Bullets
# Identify every assertive claim (fact, prediction, prescription) in the speaker's
# message. For each claim produce a single bullet ≤20 words, sentence‑case.
# No duplicates, no commentary, bullet symbol "•" at start, end with period.
# Return ONLY the bullet list."""

_MERGE_PROMPT = """### TASK: Merge and deduplicate belief bullets
You will receive two unordered lists of concise belief statements.

• **EXISTING** - the agent's current belief bullets  
• **NEW**       - bullets extracted from the latest message

Actions:

1. Compare every NEW bullet against all EXISTING bullets.  
   - Two bullets are “duplicates” if they assert the **same core idea** (wording may differ).  
   - Treat near-synonyms or paraphrases as duplicates.

2. Build a **single final list** that contains  
   • every EXISTING bullet not similar
   • similar MERGED bullets from NEW
   • and any NEW bullets that are not duplicates of EXISTING.
   
3. Write the final list as Markdown bullets, one idea per line, ≤ 20 words each.  
   *Do not output any other text, labels, or commentary.*

### OUTPUT FORMAT (example)

• Humans excel at empathy and complex judgment.  
• AI will automate repetitive data-entry jobs.  
• Universal Basic Income should cushion workers during the AI transition.
"""



_EXTRACTION_SYSTEM_PROMPT = """### TASK: Extract Belief Statements as Bullets
You are given a single speaker's turn from a debate (could be many paragraphs).

Your job:
1. Identify every **assertive claim** about how the world *is*, *will be*, or *should be*.
2. Ignore scene-setting, jokes, rhetorical filler, hedging phrases ("in my view…").
3. Remove duplicates; if two sentences say the same thing, keep one.
4. Rewrite each claim as a **bullet ≤ 20 words**, starting with a strong noun or verb.

Constraints:
- DO NOT quote the original wording verbatim; paraphrase succinctly.
- One belief per bullet—no compound bullets.
- No contradictions inside the list.
- Return **only** the bullet list; no explanations, no numbering, no extra text.

### OUTPUT FORMAT
• Bullet 1 (sentence-case, ends with period)  
• Bullet 2.  
• Bullet 3.  
…

### EXAMPLE A (short)
SPEECH ►  
"AI will probably replace some routine jobs.  
But humans will still excel at empathy and complex judgment.  
Therefore we must redesign education so creativity is central."

EXPECTED BULLETS ►  
• AI will replace certain routine jobs.  
• Humans retain advantage in empathy and complex judgment.  
• Education should prioritize creativity to stay future-proof.

### EXAMPLE B (longer)
SPEECH ►  
"Look, I want to be prooved wrong, but history shows every big technology yields more jobs than it destroys.  
Yes, printers once feared the press, but literacy boomed and new roles appeared.  
I predict AI follows the same path—massive productivity surge, net job growth.  
Universal Basic Income is a safety net we should implement during the transition.  
And let's not forget: biased data can poison AI, so transparent audits are essential."

EXPECTED BULLETS ►  
• Past technologies created net employment despite initial fears.  
• AI will replicate this pattern with overall job growth.  
• Universal Basic Income should cushion workers during AI transition.  
• Transparent audits are essential to combat biased training data.

### NOW PROCESS THE NEW TEXT ↓
"""