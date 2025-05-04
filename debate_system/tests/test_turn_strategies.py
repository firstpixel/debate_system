from app.flow_control import FlowController

def test_round_robin():
    ctrl = FlowController(["A", "B", "C"], "round_robin")
    assert ctrl.next_turn({}) == "A"
    assert ctrl.next_turn({}) == "B"
    assert ctrl.next_turn({}) == "C"
    assert ctrl.next_turn({}) == "A"

def test_mcts_selector():
    ctrl = FlowController(["X", "Y"], "mcts")
    turn = ctrl.next_turn({
        "topic": "Should AI be allowed in classrooms?",
        "history": [
            {"agent": "X", "content": "AI can personalize learning."},
            {"agent": "Y", "content": "It can also introduce bias."}
        ]
    })
    assert turn in ["X", "Y"]
    print(f"Selected via MCTS: {turn}")
