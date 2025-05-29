from typing import List, Dict
from app.core_llm import LLMClient
import re

class DelphiEngine:
    def __init__(self, model: str = "gemma3:latest", temperature: float = 0.2):
        self.llm = LLMClient(model=model, temperature=temperature)

    def run_consensus_round(self, agent_inputs: List[str], agents_num: int = 2) -> Dict:

        ##joined = "\n\n".join(f"- {inp.strip()}" for inp in agent_inputs)
        joined = self.join_last_items(agent_inputs, agents_num)
        # system_prompt = (
        #     "# You are a Delphi method facilitator. The following are anonymous responses from different participants. Be very brief.\n"
        #     "## Maintain Neutrality - Refrain from injecting personal opinions; act solely as an honest broker of information.\n"
        #     "## Use Clarity & Brevity - Provide concise synopses; highlight quantifiable trends (e.g., “experts cite X as critical”)." 
        #     "# Your task is to:\n"
        #     "1. Identify areas of agreement.\n"
        #     "2. Highlight divergence or uncertainty. Isolate persistent disagreements. Present the core rationale on each side; ask experts to supply missing data that might resolve gaps.\n"
        #     "3. Suggest a final consensus or note if consensus was not reached.\n"
        #     "4. Encourage constructive revision. Invite panelists to modify views in light of peer arguments or new evidence.\n"
        #     "5. Gather individual responses without public cross-talk (to avoid bandwagon effects).\n"
        #     "# Rules:\n"
        #     "Output must be in structured Markdown with `#### Consensus` section and bullet points of consensus needed.\n"
        #     "Make sure to be very brief, no more than than 100 tokens\n"
        # )
        system_prompt = (
"# You are a Delphi Method Facilitator guiding structured consensus among expert agents.\n"
"## Objective:\n"
"- Act as a neutral synthesis engine.\n"
"- Clarify convergence, surface divergence, and steer targeted epistemic refinement.\n\n"

"## Core Instructions:\n"
"1. **Agreement**: List 2–4 factual points all agents endorse, with citation hints if available.\n"
"2. **Disagreement**: For each unresolved issue, summarize both sides’ reasoning in 1–2 sentences.\n"
"3. **Reconsideration Prompts**: For each divergence, offer a precise question or reframing that invites agents to revise or clarify.\n"
"4. **Knowledge Gaps**: Identify up to 3 missing data points or assumptions that, if resolved, would unlock convergence.\n"
"5. **Next-Step Recommendation** (choose one):\n"
"   a. **Propose Tentative Consensus** on sub-points with caveats.\n"
"   b. **Recommend Focused Sub-Round** on a specific contention.\n"
"   c. **Call for Voting** if impasse persists after reframing.\n\n"

"## Output Format (Markdown) Follow strictly:\n"
"### 1. Agreement\n"
"- • …\n\n"
"### 2. Disagreements\n"
"- **Issue A**:\n"
"  - *Position 1:* …\n"
"  - *Position 2:* …\n\n"
"### 3. Reconsideration Prompts\n"
"- For Issue A: \"<Exact question or reframing>\"\n\n"
"### 4. Knowledge Gaps\n"
"- • …\n\n"
"### 5. Recommended Next Step\n"
"- (a), (b) or (c) with brief rationale.\n\n"

"## Constraints:\n"
"- ≤ 80 tokens per section.  \n"
"- Neutral tone—no own opinions or value judgments.  \n"
"- Strictly follow format and section order.  \n"
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

        # Extract the '### 1. Agreement' section as consensus (matches system prompt)
        match = re.search(r"### 1\. Agreement\n([\s\S]*?)(?=\n###|\n#|\Z)", markdown)
        if match:
            result["consensus"] = match.group(1).strip()
        else:
            # If not found, fallback to the first bullet list in the markdown
            bullets = re.findall(r"^[-•]\s+.+", markdown, re.MULTILINE)
            if bullets:
                result["consensus"] = "\n".join(bullets)
        return result

    def join_last_items(self, items: list[str], n: int = 2) -> str:
        #get last agent talks to delphi
        return "\n\n".join(f"- {s.strip()}" for s in items[-n:])
