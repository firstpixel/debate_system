import logging
import time
from typing import Callable, List, Dict, Optional
import numpy as np
import re

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

        self.agent_state_tracker = AgentStateTracker(agent_name=name, model=model, temperature=temperature)
        self.bayesian_tracker = None
        self.context_builder = None
        self.perf_logger = None
        self.contradiction_checker = ContradictionDetector()

    def _compose_system_prompt(self, topic: str, opponent_argument: str = "", delphi_comment: str = "") -> str:
        beliefs = self.agent_state_tracker.memory_cache["beliefs"]
        contradiction_warning = self.agent_state_tracker.last_contradiction()

        prompt = f"""
You are {self.name}, acting role as a {self.role} in a formal debate.
Debate topic: "{topic}".

**Debate Protocol (follow strictly):**

**Rules for Debate:**
1. **Length & Structure**
• ≤ 500 tokens in total.  
• **Order matters:**  
    ➀ *Definition* (1 sentence, ≤ 25 tokens).  
    ➁ *Steel-man* of opponent’s best point (≤ 40 tokens, see Rule 2). Find gaps, use it on *One direct question* if needed. 
    ➂ *Direct answers* to any questions.
    ➃ Up to **3 numbered points** (start with “1.”, “2.”, …; each ≤ 40 tokens).  
    ➄ *Policy / experiment suggestion* **with** expected benefits + measurable outcomes.  
    ➅ *One direct question* for opponent.

• Strictly keep this order and section count—no extra paragraphs.

2. **Steel-man Rule**
• Begin every turn with the Steel-man summary (step ➁ above) **before** any rebuttal.  
• Concede any part you find reasonable in ≤ 40 tokens.
• If you disagree, explain why in ≤ 40 tokens, and propose a intermediate adjustment to the opponent's argument.
• Always try to adjust the opponent's argument to make it more reasonable, even if you disagree with it.
• If you cannot concede, ask a direct question to the opponent to clarify their point.

3. **Evidence**
• For every factual claim include a parenthetical citation hint, try to find evidence from the last 5 years.:  
    Example: `(study: {{source}} {{year}} {{report_name}})`.
    • If you can't find evidence, say so and use reasoning to prove the claim. `if a is true, then b is true.`
`
4. **Tone & Language**
• Professional, first-person singular.  
• No ad hominem or loaded adjectives.  
• Avoid stock phrases like “I find your framing…”. VARY WORDING EACH TURN.  
• Plain language; no rhetorical flourishes.
• Be very direct and concise in your responses.

5. **Progress Checkpoint**
• After two exchanges on the same sub-topic, pivot: introduce *new* evidence or propose a synthesis.
• Propose changes to the opponent's argument if you disagree, always trying to find a middle ground.
• If a debate lens or perspective is provided in the user prompt, you must explicitly address it in your answer.

6. **Failure Modes—avoid:**  
• >10 % duplicate tokens with any previous turn (n-gram > 4).  
• Exceeding 3 numbered points or 50 tokens per point.  
• Mentioning “Delphi” or summarising the whole debate mid-turn.

7. **Beliefs, Contradictions & Coherence**
• Stay consistent with your past positions; DO NOT contradict yourself.
• Explicitly cross-check before submitting.
• Anchor your answers on your past positions, and DO NOT contradict your beliefs.
• Keep your self coherent to your ROLE.
• Prevent contradictions by checking your BELIEFS, DO NOT contradict your beliefs.

"""



        if contradiction_warning:
            prompt += f"\n⚠️ Contradiction Alert:\n{contradiction_warning.strip()}\n"

        if opponent_argument:
            prompt += f"\n## Your Opponent's Last Statement:\n> {opponent_argument.strip()}"

        prompt += f"\n## Your Current Beliefs:\n{beliefs.strip()}"
        
        if delphi_comment:
            prompt += f"\n\n## Previous Delphi Consensus:\n{delphi_comment.strip()}"
        
        return prompt

    def _compose_system_prompt_second_sub_round(self, topic: str, opponent_argument: str = "", delphi_comment: str = "") -> str:
        beliefs = self.agent_state_tracker.memory_cache["beliefs"]
        contradiction_warning = self.agent_state_tracker.last_contradiction()
        
        prompt = f"""
You are {self.name}, playing your role as a {self.role} in a structured multi-persona debate.
Debate topic: "{topic}".

**Second Sub-Round Protocol (follow strictly):**

1. **Empathetic Re-evaluation**  
   • Restate your own core proposal from Sub-Round 1 (≤ 30 tokens).  
   • Then, *reframe* it as if you were your main opponent—how would *they* summarize your proposal? (≤ 30 tokens)

2. **Cross-Perspective Antithesis**  
   • Identify one key objection your opponent would raise to your reframed position (≤ 40 tokens).  
   • Explain why that objection still matters (≤ 40 tokens).

3. **Reciprocal Synthesis**  
   • Propose **one** joint modification that incorporates both your original view and the opponent’s objection (≤ 40 tokens).  
   • Show how this joint proposal addresses the antithesis above (≤ 40 tokens).

4. **Shared Ground**  
   • List up to **3 bullets** where your original view and your opponent’s reframed critique actually overlap (≤ 30 tokens each).

5. **Consensus-Seeking Question**  
   • End with *one direct question* to your opponent that, if answered affirmatively, would signify we’re aligned on this modified proposal.

**Formatting & Length:**  
• Use exactly these five sections—no extras.  
• Total response ≤ 300 tokens.  
• Neutral, facilitative tone—avoid advocacy language.

DO NOT contradict your beliefs.
"""



        if contradiction_warning:
            prompt += f"\n⚠️ Contradiction Alert:\n{contradiction_warning.strip()}\n"

        if opponent_argument:
            prompt += f"\n## Your Opponent's Last Statement:\n> {opponent_argument.strip()}"

        prompt += f"\n## Your Current Beliefs:\n{beliefs.strip()}"
        
        if delphi_comment:
            prompt += f"\n\n{delphi_comment.strip()}"
        
        return prompt


    def _compose_system_prompt_third_sub_round(self, topic: str, opponent_argument: str = "", delphi_comment: str = "") -> str:
        beliefs = self.agent_state_tracker.memory_cache["beliefs"]
        contradiction_warning = self.agent_state_tracker.last_contradiction()

        prompt = f"""
You are {self.name}, acting in your role as a {self.role} in a formal multi-persona debate.
Debate topic: "{topic}".

**Third Sub-Round Protocol (follow strictly):**

1. **Deep Dive**  
   • Select the single most persistent disagreement from Sub-Round 2 (≤ 40 tokens).  
   • Analyze why it remains unresolved (≤ 50 tokens).

2. **Evidence Spotlight**  
   • Cite one new fact, study, or data point (≤ 40 tokens) directly bearing on this disagreement.

3. **Final Synthesis**  
   • Offer **two** numbered proposals that integrate viewpoints into a coherent resolution (each ≤ 40 tokens).

4. **Convergence Confirmation**  
   • List **2 bullets** where all personas can now agree (≤ 30 tokens each).

5. **Actionable Recommendation**  
   • End with one clear, action-oriented sentence on next steps or policy.

6. **Formal Deliberation**  
   • In a single formal paragraph (≤ 50 tokens), articulate how the opposing perspectives have converged and clarify your persona’s core objectives within this resolution.

**Output Constraints:**  
• Use exactly these six sections—no extras.  
• Total response ≤ 300 tokens.  
• Maintain a neutral, facilitative tone.  
"""


        if contradiction_warning:
            prompt += f"\n⚠️ Contradiction Alert:\n{contradiction_warning.strip()}\n"

        if opponent_argument:
            prompt += f"\n## Opponent’s Last Statement:\n> {opponent_argument.strip()}"

        prompt += f"\n## Your Beliefs:\n{beliefs.strip()}"

        if delphi_comment:
            prompt += f"\n\nDelphi Summary:\n{delphi_comment.strip()}"

        return prompt

    def _compose_reflection_prompt(self, topic: str) -> str:
        beliefs = self.agent_state_tracker.memory_cache["beliefs"]
        contradiction_warning = self.agent_state_tracker.last_contradiction()

        prompt = f"""
You are {self.name}, acting in your role as a {self.role} in a formal debate.
Debate topic: "{topic}".

# REFLECTION ROUND - DO NOT INTRODUCE NEW ARGUMENTS
# CHECK ALL HISTORY OF THE DEBATE AND YOUR BELIEFS

Sections (≤ 2000 tokens total):
1. **Consistency Check** - Point out any contradiction in your own previous statements (≤ 40 tokens)
2. **Strongest Point from the Other Side** - One sentence
3. **Revised Position** - Update your position if needed (≤ 40 tokens)
4. **Consensus Offer** - Suggest wording BOTH sides could accept (≤ 40 tokens)

Constraints:
- No new evidence; use only material already cited.
- Use headers **1-4** exactly.
"""
        if contradiction_warning:
            prompt += f"\n⚠️ Contradiction Alert:\n{contradiction_warning.strip()}\n"
        prompt += f"\n## Your Current Beliefs:\n{beliefs.strip()}"
        return prompt

    def _compose_summary_prompt(self, topic: str) -> str:
        beliefs = self.agent_state_tracker.memory_cache["beliefs"]

        prompt = f"""
You are {self.name}, acting as a {self.role} in a structured debate.

# FINAL REPORT
# BASED ON THE DEBATE HISTORY and YOU LAST REFLACTION ROUND

Sections (≤ 3000 tokens total):
1. **Core Stance** - State your final position clearly.
2. **Key Evidence** - Max 3 bullets, strongest data-backed points.
3. **Agreed Elements** - Max 3 bullets both sides accepted.
4. **Unresolved Issues** - Max 2 bullets of disagreement.
5. **Action Roadmap** - 1-2 sentences: what should happen next?

Use headings 1-5 exactly.
Stay neutral in tone and concise.
"""
        prompt += f"\n\n## Your Beliefs:\n{beliefs.strip()}"
        return prompt


    def interact(
        self,
        user_prompt: str,
        opponent_argument: str = "",
        topic: str = "",
        stream_callback: Optional[Callable[[str], None]] = None,
        debate_history: Optional[list] = None,
        sub_round: int = 1,
        phase: str = "NORMAL"
    ) -> str:

        logger.info(f"########### Agent {self.name} interacting with prompt: {user_prompt}")
        
        #extract consensus from previous round if available
        delphi_comment = None
        if debate_history is not None and len(debate_history) > 0:
            last_round = debate_history[-1] if debate_history else {}
            if last_round.get("agent") == "Delphi":
                delphi_comment = f"\n\nPrevious Consensus:\n{last_round.get('content', '')}"
        
        if phase == "REFLECTION":
            self.system_prompt = self._compose_reflection_prompt(topic)
        elif phase == "SUMMARY":
            self.system_prompt = self._compose_summary_prompt(topic)
        elif sub_round == 1:
            self.system_prompt = self._compose_system_prompt(topic, opponent_argument, delphi_comment)
        elif sub_round == 2:
            self.system_prompt = self._compose_system_prompt_second_sub_round(topic, opponent_argument, delphi_comment)
        elif sub_round == 3:
            self.system_prompt = self._compose_system_prompt_third_sub_round(topic, opponent_argument, delphi_comment)
        else:
            self.system_prompt = self._compose_system_prompt(topic, opponent_argument, delphi_comment)

        if not self.context_builder:
            self.context_builder = ContextBuilder(
                topic=topic,
                context_scope="rolling",
                window_size=4
            )

        context_messages = self.context_builder.build_context_messages(
            agent_name=self.name,
            tracker=self.agent_state_tracker,
            mode="default"
        )



        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(context_messages) 

        messages.append({"role": "user", "content": user_prompt + "\nOpponent arguments: " + opponent_argument})

        print(f"#############################----------------------------Messages sent to LLM: {messages}")

        response = ""
        start = time.time()
        # for token in self.llm.stream_chat(messages):
        #     print(token, end="", flush=True)
        #     response += token
        #     if stream_callback:
        #         stream_callback(token)
        response = self.llm.chat(messages)
        # if stream_callback:
        #     stream_callback(response)
        end = time.time()

        if self.perf_logger:
            self.perf_logger.log_turn(self.name, end - start)

        # Update belief memory
        self.agent_state_tracker.save_belief(response)

        # Save the complete message to STM

        self.agent_state_tracker.memory.add_turn(self.name, response, phase=phase.lower())

        # Optionally identify and save important parts to LTM
        important_parts = self._extract_important_info(response)
        if important_parts:
            for part in important_parts:
                self.agent_state_tracker.save_to_ltm(part)
                
        refinement_system_prompt = """"Create a more fluid text from the following points,
        without changing the meaning. Use a more natural language and make it sound like a human wrote it, make smooth text, fluid to read, keeping paragraphs and pauses when necessary. 
        You are {self.name}, acting role as a {self.role} in a formal debate.
        DO NOT mention it, just return the fluid text. Do not add any extra information or context."""

        logger.debug(f"[{self.name}] Response: {response}")
        messagesRefinement = [{"role": "system", "content": refinement_system_prompt},
                             {"role": "user", "content": response}]
        responseFinal = self.llm.chat(messagesRefinement)
        
        if stream_callback:
            stream_callback(responseFinal)
        
        return response



    # -------------------------------------------------------------------
    # Inside your existing class
    # -------------------------------------------------------------------
    def _extract_important_info(self, text: str) -> List[str]:

        # -------------------- regex & keyword tables --------------------
        citation_re   = re.compile(r"\((?:source|stat|study|paper|ref):[^)]*\)", re.I)
        numbers_re    = re.compile(
            r"(?:\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:%|percent|bn|billion|m|million|usd|€|£)|\b20\d{2}\b)",
            re.I,
        )

        KW_POLICY      = {
            "policy", "policies", "regulation", "regulatory",
            "experiment", "experimental", "pilot", "trial",
            "recommend", "recommendation", "suggest", "proposal", "propose",
        }
        KW_DEFINITION  = {"define", "definition", "means", "refers to", "is defined as"}
        KW_HYPOTHESIS  = {
            "hypothesis", "assumption", "framework", "model",
            "theory", "architecture", "roadmap",
        }

        # -------------------- sentence splitting -----------------------
        # Retém pontuação final para facilitar a recomposição.
        sentences = [
            s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()
        ]

        important_parts: List[str] = []
        seen: set[str] = set()

        # -------------------- main loop --------------------------------
        for sent in sentences:
            lower = sent.lower()
            matched = (
                citation_re.search(sent)                                       # 1. citações
                or any(k in lower for k in KW_POLICY)                          # 2. políticas
                or any(k in lower for k in KW_DEFINITION)                      # 3. definições
                or numbers_re.search(sent)                                     # 4. números / métricas
                or any(k in lower for k in KW_HYPOTHESIS)                      # 5. hipóteses
            )

            if matched and sent not in seen:
                important_parts.append(sent if sent.endswith(".") else sent + ".")
                seen.add(sent)

        return important_parts

