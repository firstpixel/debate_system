# 🧠 Autonomous Multi-LLM Markdown Debate Engine

This project simulates a full-scale multi-agent debate using local LLMs via **Ollama**, with agents reasoning entirely in **Markdown** and a fully traceable architecture. Supports multiple turn strategies including round-robin and Delphi consensus, with tiered memory management, contradiction detection, argument trees, and more.

---

## 🚀 Features

- Persona agents with evolving beliefs and roles
- Fully autonomous loop: turn selection → LLM reasoning → belief update
- Multi-tiered memory system (STM, LTM, belief memory)
- Supports `round_robin`, `priority`, `interrupt`, `delphi` turn strategies
- Advanced contradiction detection with vector similarity and LLM verification
- Memory summarization for handling long-running debates
- Recovery, replay, and persistent session storage
- Argument tree generation and export (Markdown + JSON)
- Real-time Streamlit UI with streaming responses
- Designed for local models (uses `gemma3:latest` via Ollama)

---

## 🧱 Architecture

```plaintext
debate_system/
├── app/                  # Core logic
│   ├── persona_agent.py      # Agent implementation
│   ├── mediator_agent.py     # Mediator/synthesis agent
│   ├── memory_manager.py     # Centralized memory manager
│   ├── agent_state_tracker.py# Agent state/memory tracking
│   ├── contradiction_detector.py # Detects belief contradictions
│   ├── context_builder.py    # Manages context window allocation
│   ├── consensus_engine.py   # Consensus generation
│   ├── delphi_engine.py      # Delphi method implementation
│   ├── argument_graph.py     # Tree of debate points
│   ├── debate_manager.py     # Orchestrates the debate
│   ├── flow_control.py       # Turn management strategies
│   ├── core_llm.py           # LLM client wrapper
│   ├── performance_logger.py # Performance tracking
│   ├── logger.py             # Logging functionality
│   └── main.py               # CLI entry point
├── memory/                # Memory systems
│   ├── mongo_store.py         # MongoDB-based STM and beliefs
│   ├── qdrant_store.py        # Vector DB for LTM and RAG
│   └── embeddings.py          # Embedding utilities
├── ui/                   # Streamlit frontend
│   ├── streamlit_app.py      # Main UI
│   └── pages/                # UI components
├── plugins/              # Custom validators/tools
├── sessions/             # Output folder per run
├── tests/                # Pytest-based validation
├── docker-compose.yaml   # MongoDB & Qdrant containers
└── requirements.txt      # Python dependencies
```

---

## ⚙️ Setup

Install Ollama (https://ollama.com) and pull a model:

```bash
ollama pull gemma3:4b
```

Create and activate your Python environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## ✅ Usage

### 1. Launch the UI

Run the following command from the `debate_system` directory:

```bash
python -m streamlit run ui/streamlit_app.py
```

Upload a `.yaml` config file and press “Start Debate”.

### 2. CLI / Dev Usage

```bash
python3 app/main.py
```

### 3. Explore Output

Results will be saved in:

```
sessions/{session_id}/
├── summary.md            # Markdown debate log
├── summary.json          # Structured output
├── performance_log.json
├── agent_states.json
├── argument_graph.json
├── user_feedback.json
```

---

## 🧠 Agent Capabilities

Agents:
- Anchor responses using memory
- Respond using Markdown only
- Avoid self-contradiction
- Adjust beliefs over time
- Interact with mediator and tools

---

## 🧪 Testing

```bash
pytest tests/
```

---

## 🧠 Default LLM Setup

All agents run `gemma3:latest` via Ollama, with real streamed chat (`stream=True`).

---

## ✨ Contributions

PRs and feature suggestions welcome. Future roadmap includes:
- Live graph visualizer
- Tool sandbox
- Agent retraining via feedback

---

## 🧠 Maintained by

Gil B. + ChatGPT
