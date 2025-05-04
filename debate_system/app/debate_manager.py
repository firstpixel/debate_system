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

        # Shared context builder for all agents
        self.context_builder = ContextBuilder(
            topic=config.get("topic", "Open discussion"),
            context_scope=config.get("context_scope", "rolling"),
            window_size=config.get("window_size", 10),
        )

        # Initialize agents based on config
        self.agents = []
        for persona in self.config.get("personas", []):
            agent = PersonaAgent(
                name=persona["name"],
                role=persona["role"],
                temperature=persona.get("temperature", 0.7),
                model=persona.get("model", "gemma3:latest"),
            )
            agent.bayesian_tracker = self.tracker
            agent.contradiction_log = self.contradiction_log
            agent.perf_logger = self.performance_logger
            agent.context_builder = self.context_builder
            self.agents.append(agent)

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

            for _ in range(len(self.agents)):
                # FlowController determines next agent
                selected_name = self.flow_controller.next_turn({
                    "round": round_num,
                    "history": self.debate_history
                })

                self.flow_controller.update_scores(self.tracker.get_scores())
                agent = next(a for a in self.agents if a.name == selected_name)

                # Fetch opponent's last statement
                opponent = next((a for a in self.agents if a.name != agent.name), None)
                opponent_last = next(
                    (r["content"] for r in reversed(self.debate_history) if r["agent"] == opponent.name),
                    "" if opponent else ""
                )

                topic = self.config.get("topic", "")
                #prompt = f"{topic} Round {round_num + 1}, your turn:"
                delphi_comment = next((r["content"] for r in reversed(self.debate_history) if r["agent"] == "Delphi"), "")
                prompt = f"Topic: {topic} \n\nRound {round_num + 1}, your turn: {agent.name}\n\n🧠 Delphi Summary:\n{delphi_comment.strip()}"
                
                response = ""
                
                def stream_to_ui(token):
                    nonlocal response
                    response += token
                    if feedback_callback:
                        feedback_callback(token)
                    
                response = agent.interact(
                    user_prompt=prompt,
                    opponent_argument=opponent_last,
                    debate_history=self.debate_history,
                    topic=topic,
                    stream_callback=stream_to_ui
                )

                # Realtime feedback to Streamlit
                if feedback_callback:
                    feedback_callback(f"#### {agent.name} says:\n{response}")
                    
                

                self.tracker.track_turn(agent=agent.name, message=response, topic=topic)

                self.debate_history.append({
                    "round": round_num + 1,
                    "agent": agent.name,
                    "role": agent.role,
                    "content": response
                })

                self.argument_graph.add_argument(agent.name, response)

            
            # Run Delphi synthesis after all agents have spoken
            print("\n🔮 Delphi Synthesis Phase")

            delphi_output = self.delphi_engine.run(
                round_history=self.debate_history,
                topic=self.config.get("topic", "")
            )

            # Save for next round injection
            self.debate_history.append({
                "round": round_num + 1,
                "agent": "Delphi",
                "role": "Consensus Facilitator",
                "content": delphi_output
            })

            # Optional: Show Delphi result on UI
            if feedback_callback:
                feedback_callback("### 🧠 Delphi Synthesis Result:\n" + delphi_output)

            
            
            
            
        self.performance_logger.save()
        print("\n🧠 Performance log saved.")

        feedback = get_feedback_form()
        feedback["satisfaction"] = 9
        feedback["perceived_bias"] = "Neutral"
        feedback["clarity_score"] = 8
        feedback["coherence_score"] = 7
        feedback["comments"] = "Very insightful debate. Maybe reduce repetition."
        save_feedback(self.session_id, feedback)

        self.finalize_debate()

        save_log_files(
            session_id=self.session_id,
            config=self.config,
            transcript=self.debate_history,
            consensus_block=self.final_summary,
            graph=self.argument_graph,
            performance=self.performance_logger
        )

    def finalize_debate(self):
        engine = ConsensusEngine(
            strategy=self.config.get("consensus_strategy", "mediator_summary")
        )
        with open(f"logs/{self.session_id}_contradictions.md", "w") as f:
            f.write(self.tracker.export_logs())

        consensus = engine.generate_consensus(
            agents=[a.name for a in self.agents],
            agent_states={a.name: a.tracker for a in self.agents},
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
            tracker=self.tracker,
            graph=self.argument_graph
        )

        print("\n📋 Final Tester Audit Report:\n")
        print(audit_summary)
        

