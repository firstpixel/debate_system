
# 🧠 Multi-LLM Autonomous Debate System

# Full Feature Specification

---

## 🔹 1. **Input Interface & Initialization**

### **Supported Input Types**

- **Plain text** (e.g. a question or proposition)
- **Markdown** (preferred — structured debate prompt, context, or user background)

### **Input Preprocessing**

- Detects if Markdown or raw text
- Parses initial topic, optional system context, debate type
- Normalizes into internal Markdown structure

### **Configurable Parameters (can be included in the prompt header block):**

| Parameter | Description | Options |
|----------|-------------|---------|
| `topic` | The main debate proposition | Markdown heading or paragraph |
| `persona_count` | Number of debaters | 2–5 |
| `debate_format` | Structure of the debate | `round_robin`, `socratic`, `bp_style`, `fishbowl`, `chain_of_thought`, `open_fight` |
| `max_rounds` | Total number of response rounds | 1–10+ |
| `consensus_strategy` | How to end the debate | `agent_closing`, `mediator_summary`, `vote`, `no_consensus` |
| `use_mediator` | Include mediator role? | `true` / `false` |
| `logging_mode` | How output is tracked | `markdown`, `json_log`, `verbose`, `summary_only` |

---

## 🔹 2. **Persona Agent System**

### **Core Features**

- Each persona has:
  - **Name/Label**
  - **LLM model** (Ollama model name)
  - **System prompt** defining stance, tone, style
  - **Dedicated memory (dialogue + optional tool memory)**
- Behaves independently but shares common debate context

### **Configurable Parameters**

| Parameter | Description |
|----------|-------------|
| `persona_name` | Name displayed in Markdown |
| `role_description` | Defines position (e.g., Pro-AI, Anti-AI) |
| `model` | Ollama model identifier |
| `temperature` | Controls creativity |
| `max_tokens` | Limits verbosity |
| `style` | Formal, casual, bullet-point, paragraph |
| `tool_usage` | Allow tools (search, summarizer) — optional |

### **Capabilities**

- Responds in Markdown format
- Optional **reaction capability** (comment on another agent’s previous turn)
- Optional **self-reflection agent** (tracks contradictions or change of opinion)

---

## 🔹 3. **Debate Manager (Core Orchestrator)**

### **Responsibilities**

- Initialize debate structure
- Manage turn-based interaction between agents
- Maintain shared context (conversation history)
- Coordinate debate phases (start → rounds → end)
- Enforce configs and rules (e.g. skip inactive agents)

### **Configurable Behaviors**

| Parameter | Description | Options |
|----------|-------------|---------|
| `turn_mode` | Agent turn strategy | `round_robin`, `random`, `priority_order`, `reaction_triggered` |
| `context_scope` | What each agent sees | `full_log`, `last_n_turns`, `summary_only`, `persona_scoped` |
| `timeout_per_turn` | Max seconds to wait for a response | Integer |
| `debate_end_condition` | Stop early if... | `consensus_reached`, `no_new_arguments`, `rounds_exhausted` |

---

## 🔹 4. **Debate Phases and Flow**

### **Phases**

1. **Initialization Phase**
   - Input parsed
   - Personas, mediator, parameters created

2. **Opening Statements**
   - Each agent optionally gives stance

3. **Main Debate Rounds**
   - Sequential or dynamic speaking
   - Context updated
   - Mediator may summarize at midpoints

4. **Final Statements**
   - Each agent gives closing arguments
   - Optional rebuttals

5. **Consensus or Verdict**
   - Mediator, Judge Agent, or Voting
   - Summarized in Markdown

6. **Final Output**
   - Structured debate log
   - Summary, scoring, and agent comments

---

## 🔹 5. **Mediator Agent (Optional)**

### **Mediator Capabilities**

- Monitors all agents
- Enforces rules (e.g. if off-topic, issues warning)
- Injects prompts to guide tone, topic, or fairness
- Can **summarize after each round**
- Can **generate final consensus**, or trigger voting

### **Types**

| Mediator Type | Behavior |
|---------------|----------|
| `Silent` | Observes only, outputs summary at end |
| `Active` | Can interrupt, clarify, guide |
| `Judge` | Scores agents’ arguments |
| `Consensus` | Attempts to reconcile all views at end |
| `Reflector` | Asks agents to revise arguments |
| `ToolAgent` | Has access to summarizer, RAG, search |

### **Configurable Behavior**

- Frequency of interjection (every round / midpoint / final only)
- Style of summary (neutral, critical, persuasive)

---

## 🔹 6. **Memory System**

### **Memory Types**

- **Global debate log**: all exchanges
- **Per-agent context**: limited memory view
- **Summarized context**: generated every N rounds
- **Reflection memory**: track agent consistency, contradictions

### **Context Management Strategies**

| Strategy | Description |
|----------|-------------|
| `append_all` | Keeps full dialogue |
| `rolling_window` | Only last N turns |
| `summarize_past` | Summarize every few rounds to reduce size |
| `persona_masking` | Hide certain turns per agent |

---

## 🔹 7. **Consensus & Judging System**

### **Finalization Strategies**

| Strategy | Description |
|----------|-------------|
| `mediator_summary` | Mediator writes a closing synthesis |
| `agent_closing` | All agents give a final speech |
| `vote_based` | LLM Judge votes for winner |
| `ranked_reasons` | Judge ranks each agent by strength of argument |
| `no_consensus` | Log ends with perspectives preserved |

### **Optional Add-ons**

- Anonymous scoring from all personas
- Reasoned evaluation ("Agent A used better evidence, Agent B stayed on topic...")

---

## 🔹 8. **Tools Integration (Optional per Agent or Mediator)**

| Tool | Description |
|------|-------------|
| `SearchTool` | Look up data in real-time |
| `RAGTool` | Pull structured knowledge for factual grounding |
| `Summarizer` | Condense prior debate |
| `ScorerTool` | Score based on debate rules (clarity, evidence, originality) |

Agents can be given tool access explicitly or infer tool usage in context via prompting.

---

## 🔹 9. **Logging & Output Formatting**

### **Markdown-Based Log**

- Sections:
  - Debate header (topic, config)
  - Agent bios
  - Each round:
    - Persona responses with Markdown names
    - Mediator notes (italic or quote blocks)
  - Final statements
  - Consensus / summary

### **Options**

| Format | Description |
|--------|-------------|
| `full_markdown` | Complete structured log with agent names, sections |
| `summary_only` | Final agent summaries and consensus |
| `json_log` | Internal structure for metrics (tokens, turn times) |
| `visual_tree` | Output as argument tree (future feature) |

---

## 🔹 10. **Core LLM Client**

### **Features**

- Unified Ollama API integration
- Support for multiple models in a single debate
- Synchronous and streaming response capabilities
- Configurable parameters (temperature, top_p, presence_penalty, etc.)
- Error handling and retry mechanisms

### **Usage**

- Used by all persona agents, mediator, and MCTS for LLM interactions
- Centralizes model configuration and communication
- Enables both standard and real-time streaming responses

---

## 🔹 11. **Extended Features (Optional / Experimental)**

### ✅ Real-time scoring

- Mediator or Critique agent rates each turn

### ✅ Reflective agents

- Agents can revise their own past argument

### ✅ Chain of Thought support

- Multi-phase arguments with evidence steps

### ✅ Interruptions

- Agents can interrupt or reference another's argument (e.g. “I disagree with what X said…”)

### ✅ Agent evolution

- Agents adjust strategy based on prior rounds

### ✅ Multi-lingual debates

- Each persona can speak in a different language (optional)

### ✅ Emotional style

- Configure tone (passionate, sarcastic, logical, optimistic)

---

# ✅ Summary: System Blueprint

| Module | Description |
|--------|-------------|
| **Input Handler** | Parses and normalizes topic/context (Markdown preferred) |
| **Persona Manager** | Loads agents with prompts, models, settings |
| **Core LLM Client** | Handles all model interactions with Ollama API |
| **Orchestrator** | Drives round logic, turn selection, manages debate flow |
| **Memory Manager** | Handles context visibility, summarization, agent memory |
| **Mediator Agent** | (Optional) Scores, guides, summarizes, moderates |
| **Consensus Engine** | Determines outcome: summary, vote, or none |
| **Tool System** | Optional plugin system (search, RAG, summarization, score) |
| **Logger** | Produces structured Markdown + optional logs for metrics |

---
