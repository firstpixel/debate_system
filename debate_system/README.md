# 🧠 Autonomous Multi-LLM Markdown Debate Engine

This project simulates a full-scale multi-agent debate using local LLMs via **Ollama**, with agents reasoning entirely in **Markdown** and a fully traceable architecture. Supports multiple turn strategies including round-robin and Delphi consensus, with tiered memory management, contradiction detection, argument trees, and more.

---

## 🚀 Features

- **Multi-Agent Debates**: Persona agents with evolving beliefs and roles
- **Autonomous Operation**: Fully autonomous loop with turn selection → LLM reasoning → belief update
- **Multi-Tiered Memory**: STM, LTM, and belief memory systems with intelligent summarization
- **Flexible Turn Strategies**: `round_robin`, `priority`, `interrupt`, `delphi` turn management
- **Advanced Analysis**: Contradiction detection with vector similarity and LLM verification
- **Document RAG Integration**: Upload PDFs, web content, GitHub repos, and YouTube transcripts
- **Session Management**: Recovery, replay, and persistent session storage
- **Argument Trees**: Generate and export structured argument graphs (Markdown + JSON)
- **Real-time UI**: Streamlit interface with streaming responses and live updates
- **Local-First**: Designed for local models via Ollama for privacy and control

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
│   ├── markdown_converter_agent.py # Document processing for RAG
│   └── main.py               # CLI entry point
├── memory/                # Memory systems
│   ├── mongo_store.py         # MongoDB-based STM and beliefs
│   ├── qdrant_store.py        # Vector DB for LTM and RAG
│   └── embeddings.py          # Embedding utilities
├── ui/                   # Streamlit frontend
│   ├── streamlit_app.py      # Main UI
│   └── pages/                # UI components
│       └── ContradictionHeatmap.py # Contradiction visualization
├── config/               # Configuration files
│   ├── config.yaml           # Default configuration
│   └── *.yaml                # Additional debate configurations
├── sessions/             # Generated output folder per run
├── tests/                # Pytest-based validation
├── docker-compose.yaml   # MongoDB & Qdrant containers
└── requirements.txt      # Python dependencies
```

---

## ⚙️ Setup

### Prerequisites

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

### 2. CLI Usage

You can run debates from the command line using a configuration file:

```bash
python3 -m app.main
```

By default, this uses `config.yaml` in the current directory. To use a specific configuration:

```bash
DEBATE_CONFIG=config/config.yaml python3 -m app.main
```

The system includes several pre-configured debate scenarios in the `config/` directory.

**Note**: Ensure MongoDB and Qdrant are running (via `docker-compose up -d`) and Ollama is installed with the required models before running debates.

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

## 📄 Document Upload & RAG Support

The system includes comprehensive document processing capabilities for uploading and converting various document formats to markdown for RAG (Retrieval-Augmented Generation) support.

### Supported Formats

- **PDF documents** - Automatically converted using the `docling` library
- **Text files** (.txt, .md)
- **Web URLs** - Content extracted and converted to markdown
- **GitHub repositories** - Code and documentation extraction
- **YouTube videos** - Transcript extraction when available

### Dependencies

Document processing is handled by the `docling` package, which is included in the requirements.txt. If you encounter issues with document upload, ensure all dependencies are properly installed:

```sh
pip install -r requirements.txt
```

The document processing is handled automatically through the Streamlit UI sidebar or can be integrated programmatically through the `MarkdownConverterAgent` class.

---

## 🧪 Testing

```bash
pytest tests/
```

---

## 🌟 LLM Configuration

The system supports any Ollama-compatible models and is designed to work with local models for privacy and control. The default configuration includes:

- **Default model**: `gemma3:latest` (configurable per agent in YAML configs)
- **Context window**: 16,384 tokens (configurable)
- **Response reserve**: 512 tokens (configurable)
- **Temperature**: Customizable per persona (0.1-1.0)

### Model Configuration

Each persona agent can use different models by specifying them in the configuration YAML:

```yaml
personas:
  - name: "TechAdvocate"
    model: "gemma3:latest"  # or any Ollama model
    temperature: 0.8
  - name: "Ethicist"
    model: "llama3.2:latest"
    temperature: 0.4
```

### Getting Started with Models

1. Install [Ollama](https://ollama.com)
2. Pull your desired model(s):
   ```bash
   ollama pull gemma3:latest
   # or
   ollama pull llama3.2:latest
   ```

---

## ✨ Contributions

PRs and feature suggestions welcome! Please check the roadmap below for planned features.

## 🗺️ Roadmap

### Upcoming Features
- Live argument graph visualization
- Custom tool integration
- Agent finetuning via debate feedback
- Support for additional local models
- Language configuration for multi-language debates
- Enhanced summary generation with language selection
- Argument graph display toggle in UI
- Full UI text export to markdown

### Document & RAG Enhancements
- Extended document format support
- Improved semantic search during debates
- Better context integration for RAG-based arguments

---

## 🧠 Maintained by

Gil B.
