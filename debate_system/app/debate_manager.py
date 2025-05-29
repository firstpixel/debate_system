# app/debate_manager.py

import re
from typing import Any, Callable, Dict, List, Optional
import uuid
from app.persona_agent import PersonaAgent
from app.logger import save_log_files
from app.user_feedback import get_feedback_form, save_feedback
from app.consensus_engine import ConsensusEngine
from app.argument_graph import ArgumentGraph
from app.contradiction_log import ContradictionLog
from app.flow_control import FlowController
from app.context_builder import ContextBuilder
from app.bayesian_tracker import BayesianTracker
from app.final_tester_agent import FinalTesterAgent
from app.delphi_engine import DelphiEngine
from app.mediator_agent import MediatorAgent
from app.contradiction_detector import ContradictionDetector
from app.discussion_lens import DiscussionLens

class DebateManager:
    def __init__(self, config: dict):
        self.config = config
        self.session_id = config.get("session_id") or str(uuid.uuid4())
        self.debate_history = []
        self.argument_graph = ArgumentGraph()
        self.final_summary = None
        self.tracker = BayesianTracker()
        self.contradiction_log = ContradictionLog()
        self.delphi_engine = DelphiEngine()
        self.contradiction_detector = ContradictionDetector()
        
        # Initialize mediator if enabled
        mediator_config = self.config.get("mediator", {})
        self.use_mediator = self.config.get("use_mediator", False)
        if self.use_mediator:
            self.mediator = MediatorAgent(
                mode=mediator_config.get("type", "summarizer"),
                model=mediator_config.get("model", "gemma3:latest"),
                temperature=mediator_config.get("temperature", 0.5)
            )
        else:
            self.mediator = None

        # Shared context builder for all agents
        self.context_builder = ContextBuilder(
            topic=config.get("topic", "Open discussion"),
            context_scope=config.get("context_scope", "rolling"),
            window_size=config.get("window_size", 10),
        )

        self.agents = []
        self.agent_trackers = {}

        for persona in self.config.get("personas", []):
            agent = PersonaAgent(
                name=persona["name"],
                role=persona["role"],
                temperature=persona.get("temperature", 0.7),
                model=persona.get("model", "gemma3:latest"),
            )
            self.agents.append(agent)
            self.agent_trackers[agent.name] = agent.agent_state_tracker

        # Now safe to initialize BayesianTracker with all trackers
        self.bayesian_tracker = BayesianTracker(agent_trackers=self.agent_trackers)

        # Attach tracker/log after it's fully constructed
        for agent in self.agents:
            agent.bayesian_tracker = self.bayesian_tracker
            agent.contradiction_log = self.contradiction_log

        self.flow_controller = FlowController(
            agent_names=[agent.name for agent in self.agents],
            strategy=self.config.get("turn_strategy", "round_robin")
        )

    def build_prompt(self, agent, round_num, sub_round=1, opponent_last="", delphi_comment="", theme=None, phase="NORMAL"):
        topic = self.config.get("topic", "")
        if round_num == 0:
            prompt = f"{topic} Round {round_num + 1}, your turn:"
        else:
            if theme is None and 1 <= (round_num - 3) <= 30:
                idx = round_num - 3
                try:
                    theme = f"Please consider this perspective or lens: {DiscussionLens.get_theme(idx)} \n"
                except Exception:
                    theme = None
            prompt = f"Topic: {topic}"
            if opponent_last:
                prompt += f"\n\nOpponent's last statement: {opponent_last.strip()}"
            if theme is not None:
                prompt += f" Debate Perspective: {theme}"
            prompt += f"  Round {round_num + 1}, your turn: {agent.name}"
            if delphi_comment:
                prompt += f"\n\nSummary: {delphi_comment.strip()}"
        return prompt

    def start(self, feedback_callback: Optional[Callable[[str], None]] = None):
        print("DebateManager started with config:")
        print(self.config)
        print("Session ID:", self.session_id)

        rounds = self.config.get("rounds", 3)
        print(f"Total rounds configured: {rounds}")



        total_rounds = rounds
        reflection_round = total_rounds - 2
        summary_round = total_rounds - 1
        merged_round = total_rounds  # Not looped; handled after summary

        for round_num in range(total_rounds):
            is_reflection = round_num == reflection_round
            is_summary = round_num == summary_round
            is_final = round_num >= merged_round
            sub_round_type = "REFLECTION" if is_reflection else "SUMMARY" if is_summary else "NORMAL"
            
            print(f"\n🔁 Starting Round {round_num + 1} / {rounds} ({sub_round_type})")

            print(f"\n🔁 Round {round_num + 1} / {rounds}")
            if feedback_callback:
                feedback_callback("Round_Marker", f"## 🔁 Round {round_num + 1} / {rounds}", round_num + 1, 1)

            topic = self.config.get("topic", "")
            sub_round1_order = []  # Track the order of agents in sub-round 1
            for _ in range(len(self.agents)):
                # FlowController determines next agent
                selected_name = self.flow_controller.next_turn({
                    "round": round_num,
                    "history": self.debate_history
                })
                print(f"DEBUG Manager: Round={round_num+1}, sub_round=1, Selected Agent by FlowController='{selected_name}'")

                # Always get the agent object before attempting to find an opponent
                agent = next(a for a in self.agents if a.name == selected_name)

                # Track which agents have spoken in this round to avoid duplicates
                if not hasattr(self, '_round_speakers') or round_num == 0 and _ == 0:
                    self._round_speakers = set()

                # Skip if this agent has already spoken in this round
                if selected_name in self._round_speakers:
                    print(f"DEBUG Manager: Skipping {selected_name} as they already spoke in Round {round_num+1}")
                    continue

                # Add agent to speakers for this round
                self._round_speakers.add(selected_name)
                sub_round1_order.append(agent)  # Record the order only after confirming not already spoken

                # Reset speakers at the end of the round
                if len(self._round_speakers) >= len(self.agents):
                    self._round_speakers = set()

                # Fetch opponent's last statement
                opponent = next((a for a in self.agents if a.name != agent.name), None)
                opponent_last = next(
                    (r["content"] for r in reversed(self.debate_history) if r["agent"] == (opponent.name if opponent else "")),
                    ""
                )


                # Build theme and delphi_comment for prompt
                theme = None
                delphi_comment = next((r["content"] for r in reversed(self.debate_history) if r["agent"] == "Delphi"), "")
                prompt = self.build_prompt(agent, round_num, sub_round=1, opponent_last=opponent_last, delphi_comment=delphi_comment, theme=theme, phase=sub_round_type)

                response = ""

                # Capture the current agent's name for the callback
                current_agent_name = agent.name
                
                # Define stream callback that passes both agent name and token, round, and sub_round
                def stream_to_ui(token, sub_round=1):
                    nonlocal response
                    response += token
                    if feedback_callback:
                        feedback_callback(current_agent_name, token, round_num + 1, sub_round)
                        
                print(f"Agent {agent.name} is interacting with prompt: {prompt}")
                print(f"Opponent's last statement: {opponent_last}")
                print(f"Debate history: {self.debate_history}")
                
                
                # In sub-round 1:
                response = agent.interact(
                    user_prompt=prompt,
                    opponent_argument=opponent_last,
                    topic=topic,
                    stream_callback=lambda token: stream_to_ui(token, 1),
                    debate_history=self.debate_history,
                    sub_round=1,
                    phase=sub_round_type
                )

                

                # Track this agent's turn for conflict detection later
                self.bayesian_tracker.track_turn(agent=agent.name, message=response, topic=topic)

                self.debate_history.append({
                    "round": round_num + 1,
                    "sub_round": 1,
                    "agent": agent.name,
                    "role": agent.role,
                    "content": response
                })
                if not response.strip() and (is_reflection or is_summary):
                    print(f"⚠️ Agent {agent.name} failed to respond during {sub_round_type} phase.")
                    # Try to retrieve their most recent message
                    last_valid = next(
                        (r["content"] for r in reversed(self.debate_history) if r["agent"] == agent.name),
                        ""
                    )
                    response = last_valid + "\n\n// NO UPDATE"

                self.argument_graph.add_argument(agent.name, response)
                
                # Check if mediator should intervene after this agent's turn
                if self.use_mediator and self.mediator and len(self.debate_history) > 1:
                    should_intervene = False
                    mediator_mode = self.mediator.mode
                    intervention_reason = ""
                    
                    # For "active" mode: Check for contradictions between agents using the contradiction detector
                    if mediator_mode == "active" and opponent:
                        # Get the last few statements from each agent in this round
                        agent_statements = [r["content"] for r in self.debate_history 
                                       if r["agent"] == agent.name and r["round"] == round_num + 1]
                        opponent_statements = [r["content"] for r in self.debate_history 
                                           if r["agent"] == opponent.name and r["round"] == round_num + 1]
                        
                        # Use contradiction detector to identify actual contradictions
                        if agent_statements and opponent_statements:
                            contradictions = self.contradiction_detector.find_contradictions(
                                agent_statements[-1], opponent_statements
                            )
                            
                            if contradictions:
                                should_intervene = True
                                llm_verification = self.contradiction_detector.verify_with_llm(
                                    agent_statements[-1], contradictions
                                )
                                intervention_reason = f"Detected contradiction: {llm_verification}"
                    
                    # For "judge" mode: Check if we need a judgment (after each agent has spoken)
                    elif mediator_mode == "judge" and len(self._round_speakers) >= len(self.agents):
                        should_intervene = True
                        intervention_reason = "Judging arguments from all agents in this round"
                    
                    # If intervention is needed, call the mediator
                    if should_intervene:
                        print(f"\n🧑‍⚖️ Mediator intervening: {intervention_reason} ----------------------------")
                        mediator_response = self.mediator.generate_response(
                            round_history=self.debate_history,
                            current_topic=self.config.get("topic", "")
                        )
                        
                        # Add mediator's response to the debate history
                        self.debate_history.append({
                            "round": round_num + 1,
                            "sub_round": 1,
                            "agent": "Mediator",
                            "role": "Debate Mediator",
                            "content": mediator_response
                        })
                        
                        # Show mediator's response in the UI
                        if feedback_callback:
                            feedback_callback("Mediator", f"### 🧑‍⚖️ Mediator Intervention:\n{mediator_response}", round_num + 1, 1)

            #if round_num % 10 == 0 :
            # Run Delphi synthesis after all agents have spoken, if enabled in config
            delphi_config = self.config.get("delphi", {})
            if delphi_config.get("enabled", False) and sub_round_type == "NORMAL":
                print("\n🔮 Delphi Synthesis Phase----------------------------------------------------")

                delphi_output = self.delphi_engine.run(
                    round_history=self.debate_history,
                    topic=self.config.get("topic", ""),
                    agents_num=len(self.agents)
                )

                # Save for next round injection
                self.debate_history.append({
                    "round": round_num + 1,
                    "sub_round": 1,
                    "agent": "Delphi",
                    "role": "Consensus Facilitator",
                    "content": delphi_output
                })

                # # Optional: Show Delphi result on UI
                # if feedback_callback:
                #    feedback_callback("Delphi", "#### 🧠 Delphi Synthesis Result:\n" + delphi_output, round_num + 1, 1)
                    
                
            else:
                print("\n🔮 Delphi Synthesis Phase (Disabled)")
                # Skip Delphi synthesis when disabled
        

            # --- SUB-ROUND 2: cross-persona reconciliation pass ---
            # reset speaker-tracker for this sub-round
            if sub_round_type == "NORMAL":
                self._round_speakers = set()
                # Use sub_round1_order directly, as it is now guaranteed unique and ordered
                for agent in sub_round1_order:
                    prompt = self.build_prompt(agent, round_num, sub_round=2, opponent_last=opponent_last, delphi_comment=delphi_comment, theme=theme)
                    response = ""
                    current_agent_name = agent.name
                    
                    # Define stream callback that passes both agent name and token, round, and sub_round
                    def stream_to_ui2(token, sub_round=1):
                        nonlocal response
                        response += token
                        if feedback_callback:
                            feedback_callback(current_agent_name, token, round_num + 1, sub_round)

                    response = agent.interact(
                        user_prompt=prompt,
                        opponent_argument=opponent_last,
                        topic=topic,
                        stream_callback=lambda token: stream_to_ui2(token, 2),
                        debate_history=self.debate_history,
                        sub_round=2
                    )
                    self.debate_history.append({
                        "round":     round_num + 1,
                        "sub_round": 2,
                        "agent":     agent.name,
                        "role":      agent.role,
                        "content":   response
                    })
                # --- OPTIONAL SUB-ROUND 3 if needed ---
                if self.needs_third_subround(self.debate_history, self.delphi_engine):
                    self._round_speakers = set()
                    for agent in sub_round1_order:
                        prompt = self.build_prompt(agent, round_num, sub_round=3, opponent_last=opponent_last, delphi_comment=delphi_comment, theme=theme)
                        
                        response = ""
                        current_agent_name = agent.name
                        # Define stream callback that passes both agent name and token, round, and sub_round
                        def stream_to_ui3(token, sub_round=1):
                            nonlocal response
                            response += token
                            if feedback_callback:
                                feedback_callback(current_agent_name, token, round_num + 1, sub_round)
                        
                        response = agent.interact(
                            user_prompt=prompt,
                            opponent_argument=opponent_last,
                            topic=topic,
                            stream_callback=lambda token: stream_to_ui3(token, 3),
                            debate_history=self.debate_history,
                            sub_round=3
                        )
                        self.debate_history.append({
                            "round":     round_num + 1,
                            "sub_round": 3,
                            "agent":     agent.name,
                            "role":      agent.role,
                            "content":   response
                        })
            else:
                print("\n🔁 Skipping sub-round 2 as this is not a normal round.")
            # --- END OF SUB-ROUNDS ---
            
        
        if self.final_summary is None:
            self.run_final_merge_phase(feedback_callback)


        self.finalize_debate(feedback_callback)


        save_log_files(
            session_id=self.session_id,
            config=self.config,
            transcript=self.debate_history,
            consensus_block=self.final_summary,
            graph=self.argument_graph
        )
        
        
    def run_final_merge_phase(self, feedback_callback=None):
        print("\n📄 Running Mediator Merge Phase (Final Consensus)...")

        reports = [
            r for r in self.debate_history
            if r["round"] == self.config["rounds"]
            and r["agent"] in [a.name for a in self.agents]
        ]

        if len(reports) != len(self.agents):
            print("⚠️ Not all summary reports found — skipping merge.")
            return

        merge_prompt = (
            "# MEDIATOR MERGE\n\n"
            "Structure:\n"
            "- **Unified Statement** (≤ 80 tokens)\n"
            "- **Remaining Divergences** (bullet list)\n"
            "- **Joint Action Plan** (≤ 60 tokens)\n"
            "- **Meta-data**: total rounds, date, agents\n\n"
            "Rules:\n"
            "- Use neutral tone\n"
            "- Quote both views if consensus differs (*italics*)\n"
            "- No new arguments"
        )

        merge_input = "\n\n".join(f"### {r['agent']}:\n{r['content']}" for r in reports)
        system_message = {"role": "system", "content": merge_prompt}
        user_message = {"role": "user", "content": merge_input}

        mediator = MediatorAgent(mode="silent", model="gemma3:latest", temperature=0.3)
        merged_response = mediator.llm.chat([system_message, user_message])

        self.final_summary = merged_response

        self.debate_history.append({
            "round": self.config["rounds"] + 1,
            "sub_round": 1,
            "agent": "MediatorMerge",
            "role": "Final Merge",
            "content": merged_response
        })

        if feedback_callback:
            feedback_callback("MediatorMerge", f"### 🧩 Final Consensus Report:\n\n{merged_response}", None, 1)

        

    def finalize_debate(self, feedback_callback=None):
        engine = ConsensusEngine(
            strategy=self.config.get("consensus_strategy", "mediator_summary")
        )
        with open(f"logs/{self.session_id}_contradictions.md", "w") as f:
            f.write(self.bayesian_tracker.export_logs())

        consensus = engine.generate_consensus(
            agents=[a.name for a in self.agents],
            agent_states={a.name: a.agent_state_tracker for a in self.agents},
            transcript=self.debate_history,
            graph=self.argument_graph
        )

        print("\n✅ Final Consensus:\n")
        print(consensus)
        

        self.final_summary = consensus

        tester = FinalTesterAgent()
        audit_summary = tester.analyze(
            session_id=self.session_id,
            consensus=self.final_summary,
            tracker=self.bayesian_tracker,
            graph=self.argument_graph
        )

        print("\n📋 Final Tester Audit Report:\n")
        print(audit_summary)
        
        # Send audit summary to UI
        if feedback_callback:
            feedback_callback("Audit Report", f"## 📋 Final Tester Audit Report:\n{audit_summary}", None, 1)





    def needs_third_subround(self,
        debate_history: List[Dict[str, Any]],
        delphi_engine: DelphiEngine,
        current_round: int = None,
        min_convergence: int = 2,
        max_tensions: int = 1
    ) -> bool:
        """
        Hybrid check: first a bullet-count heuristic, then (if needed)
        an LLM-based sanity check via DelphiEngine.

        Returns True if we still need a 3rd sub-round.
        """
        # 1. Determine which round to inspect
        rounds = [e.get("round", 0) for e in debate_history]
        if not rounds:
            return False
        current = current_round or max(rounds)

        # 2. Gather Sub-Round 2 entries (excluding Delphi)
        entries = [
            e for e in debate_history
            if e.get("round") == current
            and e.get("sub_round") == 2
            and e.get("agent") != "Delphi"
        ]
        if not entries:
            return False

        # 3. Helper to pull bullet lists under a section header
        def _parse_section(content: str, header: str) -> List[str]:
            pattern = rf"{re.escape(header)}(.*?)(?=\n\d+\.)"
            m = re.search(pattern, content, re.S)
            if not m:
                return []
            return re.findall(r"[-•]\s*(.+)", m.group(1))

        # 4. Deterministic pass
        need_round = False
        for entry in entries:
            text = entry["content"]
            conv = _parse_section(text, "4. Points of Convergence")
            tens = _parse_section(text, "2. Antithesis")
            if len(conv) < min_convergence or len(tens) > max_tensions:
                need_round = True
                break

        # 5. If heuristic says “no”, skip LLM altogether
        if not need_round:
            return False

        # 6. Fallback to Delphi LLM sanity check
        agent_texts = [e["content"] for e in entries]
        result = delphi_engine.run_consensus_round(agent_texts, agents_num=len(entries))
        consensus_md = result.get("consensus", "")
        # count bullets in the “#### Consensus” section
        bullets = re.findall(r"^-", consensus_md, re.M)

        # --- NEW: Append Delphi result to debate history for sub-round 2 ---
        # Only append if a third sub-round will be needed (i.e., if we return True)
        if len(bullets) < min_convergence:
            # Find current round number
            rounds = [e.get("round", 0) for e in debate_history]
            current = current_round or max(rounds)
            debate_history.append({
                "round": current,
                "sub_round": 2,
                "agent": "Delphi",
                "role": "Consensus Facilitator",
                "content": result.get("raw_markdown", "")
            })
            return True

        # 7. If Delphi sees enough consensus bullets, we can skip sub-round 3
        return False