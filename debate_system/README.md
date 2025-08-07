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

### Quick Start

1. **Validate your environment:**
```bash
python setup_validator.py
```

2. **Or use the development setup script:**
```bash
python dev_setup.py
```

### Manual Setup

#### Prerequisites

1. **Ollama**: Install [Ollama](https://ollama.com) and pull the required model:

```bash
ollama pull gemma3:latest
```

2. **MongoDB & Qdrant**: You can run these using Docker:

```bash
cd debate_system
docker-compose up -d
```

Or install them locally following their documentation.

### Python Environment

Create and activate your Python environment:

```bash
python3 -m venv venv
source venv/bin/activate

# Option 1: Core dependencies only (recommended)
pip install -r requirements-core.txt

# Option 2: Full dependencies (if needed)
pip install -r requirements.txt
```

---

## 🚨 Troubleshooting

### Common Issues

**Installation timeouts:**
```bash
# Use core requirements for faster install
pip install -r requirements-core.txt
```

**Ollama connection errors:**
```bash
# Check if Ollama is running
ollama list

# Start Ollama service if needed
ollama serve
```

**Missing dependencies:**
```bash
# Run environment validation
python setup_validator.py

# Use development setup
python dev_setup.py
```

**MongoDB/Qdrant connection issues:**
```bash
# Start Docker services
docker-compose up -d

# Check service status
docker-compose ps
```

### Performance Tips

- Use `requirements-core.txt` for minimal installation
- Ensure Ollama model is downloaded: `ollama pull gemma3:latest`
- Increase Docker memory allocation for better performance
- Use GPU acceleration if available

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

```plaintext
sessions/{session_id}/
├── summary.md            # Markdown debate log
├── summary.json          # Structured output
├── turns.log             # Individual turn logs
├── performance_log.json  # Performance metrics
└── argument_graph.json   # Structured argument tree
```

---

## 🧠 Memory System

The debate system uses a multi-tiered memory architecture:

1. **Short-Term Memory (STM)** - Recent conversation turns stored in MongoDB
2. **Long-Term Memory (LTM)** - Historical semantic information stored in Qdrant
3. **Belief Memory** - Agent's core beliefs and contradictions
4. **RAG Retrieval** - Vector-based knowledge retrieval

Memory is dynamically summarized to fit within context windows, with intelligent token allocation between different memory components.

---

## ⚠️ PDF Upload Support

To enable PDF upload and conversion, you must install the `unstructured` package with PDF support:

```sh
pip install "unstructured[pdf]"
```

This will install `unstructured` and all required PDF dependencies. If you only install `unstructured` without the `[pdf]` extra, PDF upload will not work.

You may also want to ensure you have `pdfminer.six` and `pypdf` installed:

```sh
pip install pdfminer.six pypdf
```

---

## 🧪 Testing

```bash
pytest tests/
```

---

## 🌟 Default LLM Setup

All agents run `gemma3:latest` via Ollama, with real-time streamed responses. The system is designed to work with:

- Context window: 4096 tokens (configurable)
- Response reserve: 1024 tokens
- Customizable token allocation ratios

---

## ✨ Contributions

PRs and feature suggestions welcome. Future roadmap includes:

- Live argument graph visualization
- Custom tool integration
- Agent finetuning via debate feedback
- Support for additional local models

---

## 🧠 Maintained by

Gil B. 


## TODO
-add document rag, so user can upload documents to be used during the debate to defend points of view (youtube transcriptions, github code, papers, pdf, text, docx, ..) transform into markdown, chunk and upload to the rag.
-include a semantic search during the debate to search for facts on RAG to help defend points of view, using it as reference.

-add config for display or not argument_graph
-add language to config, so user can choose what language the debate will use
-fix summary, to create a breafy summary of the debate on language selected.
-make the full UI text, etc, to be saved on a markdown.
