from typing import List, Dict
from app.core_llm import LLMClient

class DelphiEngine:
    def __init__(self, model: str = "gemma3:latest", temperature: float = 0.2):
        self.llm = LLMClient(model=model, temperature=temperature)

    def run_consensus_round(self, agent_inputs: List[str], agents_num: int = 2) -> Dict:

        ##joined = "\n\n".join(f"- {inp.strip()}" for inp in agent_inputs)
        joined = self.join_last_items(agent_inputs, agents_num)
        system_prompt = (
            "# You are a Delphi method facilitator. The following are anonymous responses from different participants. Be very brief.\n"
            "## Maintain Neutrality - Refrain from injecting personal opinions; act solely as an honest broker of information.\n"
            "## Use Clarity & Brevity - Provide concise synopses; highlight quantifiable trends (e.g., “experts cite X as critical”)." 
            "# Your task is to:\n"
            "1. Identify areas of agreement.\n"
            "2. Highlight divergence or uncertainty. Isolate persistent disagreements. Present the core rationale on each side; ask experts to supply missing data that might resolve gaps.\n"
            "3. Suggest a final consensus or note if consensus was not reached.\n"
            "4. Encourage constructive revision. Invite panelists to modify views in light of peer arguments or new evidence.\n"
            "5. Gather individual responses without public cross-talk (to avoid bandwagon effects).\n"
            "# Output must be in structured Markdown with `#### Consensus` section and bullet points of consensus needed.\n"
            "## Make sure to be very brief, no more than than 100 tokens\n"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": joined}
        ]

        output = ""
        # for token in self.llm.stream_chat(messages):
        #     output += token
        output = self.llm.chat(messages)
        return self._parse_output(output.strip())

    def run(self, round_history, topic, agents_num):
        """
        Accepts the round history and topic, extracts agent responses for the current round,
        and runs the Delphi consensus round. Returns the consensus markdown.
        """
        # Extract only agent responses (exclude Delphi/mediator/system)
        agent_responses = [r["content"] for r in round_history if r.get("agent") not in ("Delphi", "Consensus Facilitator", "mediator", None)]
        result = self.run_consensus_round(agent_responses, agents_num)
        # Return the raw markdown output for display
        return result.get("raw_markdown", "")

    def _parse_output(self, markdown: str) -> Dict:

        result = {
            "raw_markdown": markdown,
            "consensus": ""
        }


        if "#### Consensus" in markdown:
            parts = markdown.split("#### Consensus")
            if len(parts) > 1:
                consensus_section = parts[1]
                result["consensus"] = consensus_section.strip()

        return result

    def join_last_items(self, items: list[str], n: int = 2) -> str:
        #get last agent talks to delphi
        return "\n\n".join(f"- {s.strip()}" for s in items[-n:])
