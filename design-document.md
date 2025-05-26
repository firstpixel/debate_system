# 🧠 FINAL SYSTEM DESIGN DOCUMENT (v1.0)

**System Name:** Autonomous Multi-LLM Markdown Debate Engine  
**LLM Backend:** Ollama (multi-model local execution)  
**Interface:** Decoupled Streamlit UI (real-time feedback)  
**Input/Output Format:** Markdown only  
**Mode:** Fully Autonomous  
**Final Output:** Markdown debate log, structured consensus, argument tree, and JSON export

---

## ✅ SYSTEM GOALS

- Multi-agent debate with Markdown-only reasoning
- Dynamic loop, mediator, scoring, memory, contradiction detection
- Supports structured debates, Delphi method, argument trees, and MCTS decision paths
- Modular and traceable
- Includes Bayesian reasoning agent and real-time feedback loop
- Able to evolve debates with adaptive strategies based on input evaluation
- Embeddable into other LLM-based flows and systems via Markdown interface
- Real-time self-tracking mechanism to anchor agent perspectives, maintain identity coherence, and prevent topic drift or inconsistent evolution

---

## 📁 FOLDER & FILE STRUCTURE

```text
debate_system/
├── app/
│   ├── main.py                     # Entrypoint, initializes system
│   ├── config.py                   # Parses YAML/JSON/Markdown config
│   ├── agent_state_tracker.py      # Tracks evolving beliefs, contradictions, memory
│   ├── core_llm.py                 # LLM client wrapper for Ollama interaction
│   ├── debate_manager.py           # Orchestrates lifecycle and debate control
│   ├── flow_control.py             # Turn logic and loop dispatch
│   ├── persona_agent.py            # Implements Persona LLM agent behavior
│   ├── mediator_agent.py           # Mediator modes and logic
│   ├── context_builder.py          # Assembles prompts from memory/context
│   ├── memory_manager.py           # Maintains local agent memory/history
│   ├── consensus_engine.py         # Generates final consensus block
│   ├── logger.py                   # Handles Markdown + JSON exports
│   ├── argument_graph.py           # Builds and manages argument tree
│   ├── bayesian_tracker.py         # Tracks coherence, contradictions, topic drift
│   ├── tools.py                    # Central registry for scoring, fact check, etc.
│   └── turn_strategy/
│       └── mcts_turn_selector.py   # Implements MCTS for turn planning
├── prompts/
│   ├── system/
│   │   ├── persona_template.md
│   │   ├── mediator_template.md
│   │   ├── finalizer_templates.md
│   │   └── bayesian_observer.md
│   └── examples/
│       └── sample_inputs.md
├── ui/
│   ├── streamlit_app.py           # Streamlit interface controller
│   └── components.py              # Markdown viewers, status bars
├── output/
│   ├── debate_logs/               # Markdown debate histories
│   ├── summaries/                 # Final summaries per session
│   └── argument_trees/           # JSON or nested markdown structure
├── tests/
│   └── test_debate_flow.py       # Unit test for core flow lifecycle
└── requirements.txt              # Python dependencies
```

---

## ⚙️ CONFIGURATION STRUCTURE (config.py)

Supports `.yaml`, `.json`, or Markdown frontmatter.

```yaml
topic: "Should AI replace human drivers?"
rounds: 4
use_mediator: true
consensus_strategy: mediator_summary
logging_mode: markdown+json
turn_strategy: mcts
context_scope: rolling_window
argument_tree: true
bayesian_tracking: true
delphi:
  enabled: true
  rounds: 2
  summary_style: bullet_points
mcts:
  max_simulations: 10
  evaluation_metric:
    - argument_score
    - coherence_delta
personas:
  - name: "ProTech"
    model: "llama3"
    role: "AI Optimist"
    temperature: 0.7
  - name: "SafeGuard"
    model: "mistral"
    role: "Cautious Analyst"
    temperature: 0.5
mediator:
  type: active
  model: "llama3"
```

---

## 🔁 DEBATE LIFECYCLE

```text

User Input (.md / .yaml / .json)
        ↓
Config Parser (config.py) → Validates + Normalizes
        ↓
Debate Manager (debate_manager.py)
        ↓
Init: Persona Agents + Mediator + Bayesian Agent
        ↓
Loop: (flow_control.py)
  1. Select turn strategy: round_robin | priority | interrupt | delphi | mcts
  2. Build prompt via context_builder (Summary Tool, subject, beliefs)
     → Pass through Summary Tool to include subject focus, belief memory, last views
     → Input includes agent’s last known stance, memory track, subject anchoring
  3. Persona responds via Ollama
  4. Update memory + argument tree + agent state tracker
  5. Bayesian tracker evaluates coherence
  6. Mediator summarizes/interjects
  7. Contradiction detection/scoring
  8. Performance logging
        ↓
Exit: round limit | consensus | stable tree | Delphi convergence
        ↓
Consensus Engine → Summary | Vote | Ranking
        ↓
Logger exports .md + .json + tree
        ↓
 User feedback collected (user_feedback.py)
        ↓
UI updates (streamlit_app.py)

```

---

## 🧠 TURN & LOOP STRATEGIES

| Strategy      | Description                                                                 |
| ------------- | --------------------------------------------------------------------------- |
| `round_robin` | Each agent speaks once per round                                            |
| `priority`    | Agent with highest score or influence speaks next                           |
| `interrupt`   | Mediator allows direct rebuttal or urgent injection                         |
| `delphi`      | Anonymous, multi-round feedback loop with convergence consensus             |
| `mcts`        | Monte Carlo Tree Search explores future turn sequences and selects best path |

Strategies can be combined dynamically per round depending on feedback and coherence flags.

---

## 🌳 ARGUMENT TREE (argument_graph.py)

| Concept | Description                                        |
| ------- | -------------------------------------------------- |
| Node    | Agent claim (ID: ARG001, ARG002...)                |
| Edge    | supports, attacks, qualifies (Markdown-referenced) |
| Root    | Debate topic                                       |

### Markdown Format

```markdown
**ARG001** – ProTech: AI reduces accidents.
→ **But** [ARG002] – SafeGuard: Sensors fail in snow.
→ **However** [ARG003] – ProTech: Rare edge case.
```

### Output Formats

- Nested Markdown structure
- JSON format for UI/tree visualizer
- Graph metrics: depth, coherence, contradiction ratio

---

## 🧐 BAYESIAN TRACKER (bayesian_tracker.py)

Tracks and analyzes debate flow:

- Argument validity over time
- Flip-flops / contradictions (semantic + scoring)
- Topic drift via cosine similarity embeddings
- Relevance decay and agent focus loss

Outputs:

- Agent coherence score
- Contradiction likelihood signal
- Drift vector per agent per round
- Mediator injected feedback based on metrics

---

## 🤝 MEDIATOR AGENT

Modes:

- `silent` – passive, watches only
- `active` – may interrupt or redirect
- `judge` – picks best response
- `summarizer` – condenses rounds
- `delphi_facilitator` – manages anonymous consensus

Mediator can:

- Govern turns
- Reframe discussions
- Summarize trees
- Guide Delphi convergence
- Trigger stop conditions

---

## 🚧 INTEGRATION, TRACKING AND RECOVERY

Session Recovery (session_recovery.py)

Performance Logging (performance_logger.py)

User Analytics & Feedback (user_feedback.py)


---

## 📦 TOOLS

| Tool Name             | Purpose                                                           |
|----------------------|--------------------------------------------------------------------|
| SummarizerTool       | Condenses trees or rounds                                          |
| ScorerTool           | Ranks agent turns                                                  |
| ContradictionDetector| Flags internal logical flips                                       |
| KeywordTracker       | Tracks repetition / drift                                          |
| ConsensusExtractor   | Final agreement summary generator                                  |
| DelphiScoreAnalyzer  | Analyzes Delphi results                                            |
| FactCheckStub        | Placeholder for future fact validation                             |
| AgentStateTracker    | Persists and summarizes agent belief states and evolving opinions  |

All tools implement standard protocol and can be called via flow control or mediator.

---

## 📜 LOGGER

Markdown (.md):

- Round-by-round logs
- Agent Markdown responses
- Mediator summaries (quote blocks)
- Final consensus block

JSON (.json):

- Argument graph
- Agent metadata
- Round scoring
- Token usage (optional)

Export Paths:

- `output/debate_logs/`
- `output/argument_trees/`
- `output/summaries/`

---

## ☁️ UI (Streamlit)

### Core Views

- Config summary panel
- Live round viewer (per-turn display)
- Markdown argument tree
- Final consensus summary
- Agent state evolution panel

### Controls

- Config file upload or edit
- Start debate ("Run Debate")
- Export Markdown/JSON
- Highlight contradictions/coherence decay
- Toggle "agent memory tracking" (display each agent system prompt evolving)

### Visual Cues

- Color-coded agents
- Role-based icons (e.g., mediator, judge)
- Tree highlights for attack/support links

---

## ✅ FEATURES CHECKLIST

| Feature                                        | Status |
| ---------------------------------------------- | ------ |
| Markdown-only prompts and responses            | ✅      |
| 2–5 agents with LLM + roles                    | ✅      |
| Argument Tree with reference linking           | ✅      |
| Bayesian coherence + contradiction tracking    | ✅      |
| Round-based loop engine                        | ✅      |
| MCTS turn selection                            | ✅      |
| Delphi method with revision/synthesis          | ✅      |
| Mediator (5 modes)                             | ✅      |
| Logging: Markdown + JSON + graph               | ✅      |
| Streamlit live display                         | ✅      |
| Topic drift tracking + relevance decay         | ✅      |
| Agent scoring + voting + ranking               | ✅      |
| Contradiction alerts + self-reflection         | ✅      |
| Real-time belief tracking per agent            | ✅      |
| Summarized memory to fit within context limit  | ✅      |
| Evolving concept memory anchoring              | ✅      |

---

## 🚀 CONCLUSION

This **v1.0 FINAL** includes **ALL system features from prior discussions**:

- Full debate lifecycle
- Modular persona agents
- Tree-based reasoning
- Argument scoring and coherence metrics
- Multi-strategy loop control (round_robin → mcts)
- Consensus mechanisms and mediator behaviors
- Delphi consensus with post-synthesis ranking
- MCTS-based dynamic decision paths for debate evolution
- Fully streamable interface and export formats
- Real-time philosophical consistency engine: each persona retains coherent belief evolution, avoids flip-flops, and stays on topic
- System prompt generation is dynamically injected with last known beliefs and views, maintaining context within LLM limits via summarization

✅ Nothing missing  
✅ No features planned later  
✅ Ready for scaffold or production deployment
