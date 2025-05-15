from app.tools import tool_registry

def test_summarizer_tool():
    tool = tool_registry["SummarizerTool"]()
    result = tool.run({"text": "AI can reduce human error, personalize education, and analyze large datasets quickly."})
    assert "•" in result["summary"] or "-" in result["summary"]
    print("Summary:", result["summary"])

def test_scorer_tool():
    tool = tool_registry["ScorerTool"]()
    result = tool.run({"text": "AI reduces costs and saves lives in surgery."})
    assert isinstance(result["score"], str)
    print("Score Output:", result["score"])
