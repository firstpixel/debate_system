# app/debate_manager.py


from typing import Callable, Optional
import uuid
from app.performance_logger import PerformanceLogger
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
        self.performance_logger = PerformanceLogger(self.session_id)
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

    def start(self, feedback_callback: Optional[Callable[[str], None]] = None):

        print("DebateManager started with config:")
        print(self.config)
        print("Session ID:", self.session_id)
        self.performance_logger.save()

        rounds = self.config.get("rounds", 3)

        for round_num in range(rounds):
            print(f"\n🔁 Round {round_num + 1} / {rounds}")
            
            # Send round information to UI
            if feedback_callback:
                feedback_callback("Round_Marker", f"## 🔁 Round {round_num + 1} / {rounds}")

            for _ in range(len(self.agents)):
                # FlowController determines next agent
                selected_name = self.flow_controller.next_turn({
                    "round": round_num,
                    "history": self.debate_history
                })
                print(f"DEBUG Manager: Round={round_num+1}, Selected Agent by FlowController='{selected_name}'")

                # Always get the agent object before attempting to find an opponent
                agent = next(a for a in self.agents if a.name == selected_name)
                
                # Update priority scores before next agent selection if using priority strategy
                if self.config.get("turn_strategy") == "priority":
                    print(f"Using priority strategy. Current scores: {self.bayesian_tracker.get_scores()}")
                    self.flow_controller.update_scores(self.bayesian_tracker.get_scores())
                    print(f"Updated priority order: {self.flow_controller._priority_order}")

                # Track which agents have spoken in this round to avoid duplicates
                if not hasattr(self, '_round_speakers'):
                    self._round_speakers = set()
                
                # Skip if this agent has already spoken in this round
                if selected_name in self._round_speakers:
                    print(f"DEBUG Manager: Skipping {selected_name} as they already spoke in Round {round_num+1}")
                    continue
                    
                # Add agent to speakers for this round
                self._round_speakers.add(selected_name)
                
                # Reset speakers at the end of the round
                if len(self._round_speakers) >= len(self.agents):
                    self._round_speakers = set()
                
                # Fetch opponent's last statement
                opponent = next((a for a in self.agents if a.name != agent.name), None)
                opponent_last = next(
                    (r["content"] for r in reversed(self.debate_history) if r["agent"] == (opponent.name if opponent else "")),
                    ""
                )


                topic = self.config.get("topic", "")
                if(round_num == 0):
                    prompt = f"{topic} Round {round_num + 1}, your turn:"
                else:
                     # Sugestion themes
                     
                    rnd=round_num 
                    try:
                        idx = rnd - 3
                        if idx < 1 or idx > 30:
                            theme = None
                            print(f"Round {idx:2d} theme is not defined. Using free theme.")
                        else:
                            print(f"Round {idx:2d}: {DiscussionLens.get_theme(idx)}")
                            theme = f"Please consider this perspective or lens: {DiscussionLens.get_theme(idx)} \n"
                    except ValueError as e:
                        theme = None
                        print(f"Round {idx:2d}: {e}")
                    
                    
                    delphi_comment = next((r["content"] for r in reversed(self.debate_history) if r["agent"] == "Delphi"), "")
                    prompt = f"Topic: {topic}"
                    if theme != None:
                        prompt += f" Debate Perspective: {theme}"
                    prompt +=f"  Round {round_num + 1}, your turn: {agent.name}\n\nSummary: {delphi_comment.strip()}"


                response = ""

                # Capture the current agent's name for the callback
                current_agent_name = agent.name
                
                # Define stream callback that passes both agent name and token
                def stream_to_ui(token):
                    nonlocal response
                    response += token
                    if feedback_callback:
                        feedback_callback(current_agent_name, token, round_num + 1)
                        
                print(f"Agent {agent.name} is interacting with prompt: {prompt}")
                print(f"Opponent's last statement: {opponent_last}")
                print(f"Debate history: {self.debate_history}")
                response=""
                response = agent.interact(
                    user_prompt=prompt,
                    opponent_argument=opponent_last,
                    topic=topic,
                    stream_callback=stream_to_ui,
                    debate_history=self.debate_history  # Pass full debate history
                )

                # Realtime feedback to Streamlit
                #if feedback_callback:
                #    feedback_callback(f"#### {agent.name} says:\n{response}")
                    
                

                # Track this agent's turn for conflict detection later
                self.bayesian_tracker.track_turn(agent=agent.name, message=response, topic=topic)

                self.debate_history.append({
                    "round": round_num + 1,
                    "agent": agent.name,
                    "role": agent.role,
                    "content": response
                })

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
                            "agent": "Mediator",
                            "role": "Debate Mediator",
                            "content": mediator_response
                        })
                        
                        # Show mediator's response in the UI
                        if feedback_callback:
                            feedback_callback("Mediator", f"### 🧑‍⚖️ Mediator Intervention:\n{mediator_response}", round_num + 1)

            #if round_num % 10 == 0 :
            # Run Delphi synthesis after all agents have spoken, if enabled in config
            delphi_config = self.config.get("delphi", {})
            if delphi_config.get("enabled", False):
                print("\n🔮 Delphi Synthesis Phase----------------------------------------------------")

                delphi_output = self.delphi_engine.run(
                    round_history=self.debate_history,
                    topic=self.config.get("topic", ""),
                    agents_num=len(self.agents)
                )

                # Save for next round injection
                self.debate_history.append({
                    "round": round_num + 1,
                    "agent": "Delphi",
                    "role": "Consensus Facilitator",
                    "content": delphi_output
                })

                # # Optional: Show Delphi result on UI
                if feedback_callback:
                    feedback_callback("Delphi", "#### 🧠 Delphi Synthesis Result:\n" + delphi_output, round_num + 1)
            else:
                print("\n🔮 Delphi Synthesis Phase (Disabled)")
                # Skip Delphi synthesis when disabled
        
            
            
            
        self.performance_logger.save()
        print("\n🧠 Performance log saved.")

        # Mock feedback for demonstration purposes
        # demo_feedback = get_feedback_form()
        # demo_feedback["satisfaction"] = 10
        # demo_feedback["perceived_bias"] = "Neutral"
        # demo_feedback["clarity_score"] = 10
        # demo_feedback["coherence_score"] = 10
        # demo_feedback["comments"] = "Very insightful debate. Maybe reduce repetition."
        # save_feedback(self.session_id, demo_feedback)

        self.finalize_debate(feedback_callback)

        save_log_files(
            session_id=self.session_id,
            config=self.config,
            transcript=self.debate_history,
            consensus_block=self.final_summary,
            graph=self.argument_graph,
            performance=self.performance_logger
        )

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
            feedback_callback("Audit Report", f"## 📋 Final Tester Audit Report:\n{audit_summary}")


