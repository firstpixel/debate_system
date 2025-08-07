# API Documentation

This document provides an overview of the core classes and APIs in the Debate System.

## Core Classes

### DebateManager

The main orchestrator for debates.

```python
from app.debate_manager import DebateManager

# Initialize with configuration
config = load_config("config/config_sample.yaml")
debate = DebateManager(config)

# Start the debate
debate.start()
```

**Key Methods:**
- `start(feedback_callback=None)` - Start the debate with optional UI callback
- `build_prompt(agent, round_num, ...)` - Build context prompt for agents

### PersonaAgent

Individual AI agents that participate in debates.

```python
from app.persona_agent import PersonaAgent

agent = PersonaAgent(
    name="Philosopher",
    role="Ethics Expert", 
    temperature=0.7,
    model="gemma3:latest",
    style="academic"
)
```

**Key Methods:**
- `generate_response(context, topic, ...)` - Generate agent response
- `update_beliefs(new_belief)` - Update agent's belief system

### LLMClient

Interface for communicating with Ollama LLM service.

```python
from app.core_llm import LLMClient

client = LLMClient(model="gemma3:latest")
response = client.chat([{"role": "user", "content": "Hello"}])

# Streaming
for chunk in client.stream_chat(messages):
    print(chunk, end="")
```

**Key Methods:**
- `chat(messages)` - Send chat request, get complete response
- `stream_chat(messages)` - Send streaming chat request

### Configuration System

Load and validate configuration files.

```python
from app.config import load_config

# Load configuration
config = load_config("config/my_config.yaml")

# Configuration structure
{
    "topic": "Discussion topic",
    "rounds": 3,
    "personas": [...],
    "mediator": {...},
    "turn_strategy": "round_robin"
}
```

**Supported Formats:**
- YAML (.yaml, .yml)
- JSON (.json)  
- Markdown with frontmatter (.md)

## Memory System

### AgentStateTracker

Tracks agent memory and state.

```python
from app.agent_state_tracker import AgentStateTracker

tracker = AgentStateTracker(agent_name="Alice")
tracker.add_memory("Short term memory item")
tracker.update_beliefs("New belief")
```

### BayesianTracker

Tracks belief changes and confidence levels.

```python
from app.bayesian_tracker import BayesianTracker

tracker = BayesianTracker()
tracker.update_belief_confidence("agent1", "topic", 0.8)
```

## Flow Control

### FlowController

Manages turn order and speaking strategies.

```python
from app.flow_control import FlowController

controller = FlowController(
    agent_names=["Alice", "Bob", "Charlie"],
    strategy="round_robin"
)

next_speaker = controller.next_turn(context)
```

**Supported Strategies:**
- `round_robin` - Each agent speaks in order
- `priority` - Priority-based selection
- `interrupt` - Allow interruptions
- `delphi` - Delphi method consensus

## Argument Processing

### ArgumentGraph

Build and analyze argument structures.

```python
from app.argument_graph import ArgumentGraph

graph = ArgumentGraph()
graph.add_argument("premise", "conclusion", agent="Alice")
graph.export_to_json("argument_structure.json")
```

### ContradictionDetector

Detect logical contradictions in arguments.

```python
from app.contradiction_detector import ContradictionDetector

detector = ContradictionDetector()
contradictions = detector.find_contradictions(statements)
```

## UI Components

### Streamlit App

Main UI application.

```python
# Run the UI
python -m streamlit run ui/streamlit_app.py
```

**Features:**
- Real-time debate viewing
- Configuration upload
- Document RAG integration
- Argument visualization

## Utility Functions

### Logging

```python
from app.logger import save_log_files

# Save debate logs
save_log_files(session_id, debate_history, summary, argument_graph)
```

### User Feedback

```python
from app.user_feedback import save_feedback

feedback = {
    "satisfaction": 8,
    "clarity_score": 7,
    "comments": "Great debate!"
}
save_feedback(session_id, feedback)
```

## Error Handling

All core functions include proper error handling:

```python
try:
    config = load_config("config.yaml")
except FileNotFoundError:
    # Handle missing file
except ValueError as e:
    # Handle invalid configuration
```

Common exceptions:
- `FileNotFoundError` - Configuration file not found
- `ValueError` - Invalid configuration or parameters
- `ConnectionError` - Cannot connect to Ollama service
- `RuntimeError` - General runtime errors

## Configuration Examples

### Basic Debate Config

```yaml
topic: "Should AI be regulated?"
rounds: 3
turn_strategy: round_robin

personas:
  - name: "Advocate"
    role: "AI Rights Supporter"
    temperature: 0.8
    style: "optimistic"
  
  - name: "Skeptic"  
    role: "AI Safety Researcher"
    temperature: 0.6
    style: "critical"
```

### Advanced Config with Mediator

```yaml
topic: "Future of renewable energy"
rounds: 5
use_mediator: true
consensus_strategy: vote

mediator:
  type: "summarizer"
  model: "gemma3:latest"

delphi:
  enabled: true
  rounds: 2
  summary_style: "bullet_points"

personas:
  - name: "Engineer"
    role: "Renewable Energy Engineer"  
    temperature: 0.7
    style: "technical"
```

## Development Tools

### Environment Validation

```bash
python setup_validator.py
```

### Quality Checks

```bash
python quality_check.py
```

### Development Setup

```bash
python dev_setup.py
```

For more detailed examples, see the `config/` directory and test files in `tests/`.