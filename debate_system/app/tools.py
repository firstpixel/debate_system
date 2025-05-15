# app/tools.py

from typing import Dict, Any, Callable
from app.core_llm import LLMClient

tool_registry: Dict[str, Callable] = {}

def register_tool(name: str):
    def wrapper(cls):
        tool_registry[name] = cls
        return cls
    return wrapper

# ──────────────── TOOL BASE CLASS ────────────────

class BaseTool:
    def __init__(self, model: str = "gemma3:latest", temperature: float = 0.5):
        self.llm = LLMClient(model=model, temperature=temperature)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Tool must implement run()")

# ──────────────── TOOL IMPLEMENTATIONS ────────────────

@register_tool("SummarizerTool")
class SummarizerTool(BaseTool):
    def run(self, input_data: Dict) -> Dict:
        text = input_data["text"]
        prompt = [
            {"role": "system", "content": "Summarize the following in concise Markdown bullet points."},
            {"role": "user", "content": text}
        ]

        summary = ""
        for token in self.llm.stream_chat(prompt):
            summary += token

        return {"summary": summary.strip()}


@register_tool("ScorerTool")
class ScorerTool(BaseTool):
    def run(self, input_data: Dict) -> Dict:
        prompt = [
            {"role": "system", "content": "You are a debate judge. Rate the argument on Clarity, Logic, and Evidence (1-10)."},
            {"role": "user", "content": input_data["text"]}
        ]

        response = ""
        for token in self.llm.stream_chat(prompt):
            response += token

        return {"score": response.strip()}


@register_tool("ContradictionDetector")
class ContradictionDetector(BaseTool):
    def run(self, input_data: Dict) -> Dict:
        prompt = [
            {"role": "system", "content": "Does the following contradict itself? Reply with YES or NO and explain."},
            {"role": "user", "content": input_data["text"]}
        ]

        result = ""
        for token in self.llm.stream_chat(prompt):
            result += token

        return {"contradiction": "yes" in result.lower(), "explanation": result.strip()}


@register_tool("KeywordTracker")
class KeywordTracker(BaseTool):
    def run(self, input_data: Dict) -> Dict:
        text = input_data["text"].lower()
        keywords = input_data.get("keywords", [])
        found = [k for k in keywords if k.lower() in text]
        return {"found_keywords": found}


@register_tool("ConsensusExtractor")
class ConsensusExtractor(BaseTool):
    def run(self, input_data: Dict) -> Dict:
        entries = "\n".join(f"- {e}" for e in input_data["statements"])
        prompt = [
            {"role": "system", "content": "Summarize the common points across the following statements."},
            {"role": "user", "content": entries}
        ]

        summary = ""
        for token in self.llm.stream_chat(prompt):
            summary += token

        return {"consensus": summary.strip()}


@register_tool("DelphiScoreAnalyzer")
class DelphiScoreAnalyzer(BaseTool):
    def run(self, input_data: Dict) -> Dict:
        scores = input_data["scores"]  # List of {"agent": str, "score": float}
        avg = sum(x["score"] for x in scores) / len(scores)
        top_agent = max(scores, key=lambda x: x["score"])["agent"]
        return {"average_score": round(avg, 2), "top_agent": top_agent}


@register_tool("FactCheckStub")
class FactCheckStub(BaseTool):
    def run(self, input_data: Dict) -> Dict:
        return {
            "fact_checked": True,
            "accuracy": "unknown",
            "note": "This is a placeholder. Integrate with real source later."
        }
