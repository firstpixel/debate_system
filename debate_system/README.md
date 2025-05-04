# 🧠 Autonomous Multi-LLM Markdown Debate Engine

This project simulates a full-scale multi-agent debate using local LLMs via **Ollama**, with agents reasoning entirely in **Markdown** and a fully traceable architecture. Supports MCTS turn logic, Delphi consensus, belief memory, contradiction detection, argument trees, and more.

---

## 🚀 Features

- Persona agents with evolving beliefs and roles
- Fully autonomous loop: turn selection → LLM reasoning → belief update
- Supports `round_robin`, `mcts`, `priority`, `interrupt`, `delphi` turn strategies
- Summarizer, contradiction detector, scoring, consensus engine
- Recovery, replay, and persistent session storage
- Argument tree generation and export (Markdown + JSON)
- Real-time Streamlit UI
- Designed for local models (uses `gemma3:latest` via Ollama)

---

## 🧱 Folder Structure

```
debate_system/
├── app/                 # Core logic
│   ├── persona_agent.py
│   ├── mediator_agent.py
│   ├── consensus_engine.py
│   ├── context_builder.py
│   ├── argument_graph.py
│   ├── performance_logger.py
│   ├── config.py
│   ├── tools.py
│   ├── flow_control.py
│   ├── debate_manager.py
│   ├── session_recovery.py
│   ├── logger.py
│   ├── user_feedback.py
│   └── integration_plugin.py
├── ui/                  # Streamlit frontend
│   ├── streamlit_app.py
│   └── components.py
├── plugins/             # Custom validators/tools (optional)
├── sessions/            # Output folder per run
├── tests/               # Pytest-based validation
└── requirements.txt
```

---

## ⚙️ Setup

Install Ollama (https://ollama.com) and pull a model:

```bash
ollama pull gemma:7b
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
