from typing import List, Dict
from app.core_llm import LLMClient

class DelphiEngine:
    def __init__(self, model: str = "gemma3:latest", temperature: float = 0.3):
        self.llm = LLMClient(model=model, temperature=temperature)

    def run_consensus_round(self, agent_inputs: List[str]) -> Dict:

        joined = "\n\n".join(f"- {inp.strip()}" for inp in agent_inputs)
        system_prompt = (
            "You are a Delphi method facilitator. The following are anonymous responses from different participants.\n"
            "Your task is to:\n"
            "1. Identify areas of agreement.\n"
            "2. Highlight divergence or uncertainty.\n"
            "3. Compute an estimated convergence percentage.\n"
            "4. Suggest a final consensus or note if consensus was not reached.\n"
            "Output must be in structured Markdown with a `### Convergence` and `### Consensus` section."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": joined}
        ]

        output = ""
        for token in self.llm.stream_chat(messages):
            output += token

        return self._parse_output(output.strip())

    def run(self, round_history, topic):
        """
        Accepts the round history and topic, extracts agent responses for the current round,
        and runs the Delphi consensus round. Returns the consensus markdown.
        """
        # Extract only agent responses (exclude Delphi/mediator/system)
        agent_responses = [r["content"] for r in round_history if r.get("agent") not in ("Delphi", "Consensus Facilitator", "mediator", None)]
        result = self.run_consensus_round(agent_responses)
        # Return the raw markdown output for display
        return result.get("raw_markdown", "")

    def _parse_output(self, markdown: str) -> Dict:

        result = {
            "raw_markdown": markdown,
            "convergence": "",
            "consensus": ""
        }

        if "### Convergence" in markdown:
            parts = markdown.split("### Convergence")
            if len(parts) > 1:
                convergence_section = parts[1]
                convergence_block = convergence_section.split("###", 1)[0].strip()
                result["convergence"] = convergence_block

        if "### Consensus" in markdown:
            parts = markdown.split("### Consensus")
            if len(parts) > 1:
                consensus_section = parts[1]
                result["consensus"] = consensus_section.strip()

        return result
