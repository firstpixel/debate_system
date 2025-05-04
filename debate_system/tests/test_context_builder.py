from app.context_builder import ContextBuilder
from app.agent_state_tracker import AgentStateTracker

def test_prompt_generation():
    topic = "Should AI be used in education?"
    tracker = AgentStateTracker("EduAnalyst")
    tracker.add_belief("AI helps with personalized learning.")
    tracker.add_belief("But it could reduce critical thinking.")

    history = [
        {"agent": "TechSupporter", "content": "AI boosts productivity and automates lesson plans."},
        {"agent": "EduAnalyst", "content": "AI reduces teacher workload but increases screen time."}
    ]

    builder = ContextBuilder(topic)
    prompt = builder.build_prompt(
        agent_name="EduAnalyst",
        agent_role="Education Specialist",
        last_turns=history,
        tracker=tracker
    )

    assert isinstance(prompt, list)
    assert "system" in prompt[0]["role"]
    assert "user" in prompt[1]["role"]
    print("\nSystem Prompt:\n", prompt[0]["content"])
    print("\nUser Prompt:\n", prompt[1]["content"])
