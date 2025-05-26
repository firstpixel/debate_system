
# 📋 Full Task List for Autonomous Multi-LLM Markdown Debate Engine (Validated & Enhanced)

## High-Priority Initialization Tasks

### Task 1 - Setup Project Structure

- **Files:** All directories and initial files listed in the Folder & File Structure.
- **Description:** Create project directories, placeholder Python files, and ensure correct module imports. Confirm structure matches the design document, including folders like `app/`, `ui/`, `output/`, and `tests/`.
- **Goal:** All listed directories and placeholder files exist, and `main.py` can import modules without error.

### Task 2 - Environment and Dependencies

- **File:** `requirements.txt`
- **Description:** Define and test installation of required Python libraries (e.g., Streamlit, Ollama client, PyYAML, numpy, networkx, etc.). Ensure compatibility with local Ollama execution and Streamlit live UI.
- **Goal:** Running `pip install -r requirements.txt` installs all dependencies without errors and supports both backend and UI execution.

### Task 3 - Comprehensive Configuration Parser

- **File:** `app/config.py`
- **Description:** Implement a parser for YAML/JSON/Markdown frontmatter configuration. Must validate schema, normalize values, and expose options for turn strategies, delphi mode, mediator roles, and MCTS params.
- **Goal:** Given a valid config file, the parser returns a normalized Python dict and fails gracefully on invalid schema.

## Agent Implementation Tasks

### Task 3.5 - Core LLM Client Implementation

- **File:** `app/core_llm.py`
- **Description:** Implement the `LLMClient` class to handle communication with the Ollama API. Support both synchronous and streaming responses, configurable model parameters (temperature, etc.), and basic error handling/retry logic.
- **Goal:** The `LLMClient` can successfully connect to Ollama, send prompts, and receive both standard and streamed responses using specified models and parameters.

### Task 4 - Persona Agent Development

- **File:** `app/persona_agent.py`
- **Description:** Implement an LLM agent capable of responding in Markdown using Ollama. Support role configuration (optimist, skeptic, analyst, etc.), custom temperature, memory anchoring, and evolving belief systems.
- **Goal:** Agent responds to prompts using correct persona settings and updates its belief state in memory tracker.

### Task 5 - Mediator Agent Modes

- **File:** `app/mediator_agent.py`
- **Description:** Implement five operational modes (`silent`, `active`, `judge`, `summarizer`, `delphi_facilitator`). Each mode must influence debate flow, summaries, turn control, or consensus handling, according to configuration.
- **Goal:** Each mode runs without error, performs its role accurately in a test debate, and logs expected behavior.

### Task 6 - Bayesian Tracker Implementation

- **File:** `app/bayesian_tracker.py`
- **Description:** Build a module to analyze argument validity, coherence over time, contradiction signals, and topic drift. Must produce metrics and signals usable by the mediator and flow controller.
- **Goal:** Tracker outputs coherence score, contradiction signals, and drift vector for each agent per round.

### Task 7 - Agent State Tracking

- **File:** `app/agent_state_tracker.py`
- **Description:** Persist and update each agent’s evolving belief set. Provide summarization tools to compress state for LLM token limits while retaining internal consistency.
- **Goal:** Tracker can store, update, and return summarized belief history for each agent.

## Core Functionalities Tasks

### Task 8 - Flow Control and Turn Strategies

- **Files:** `app/flow_control.py`, `app/turn_strategy/mcts_turn_selector.py`
- **Description:** Implement loop logic with support for `round_robin`, `priority`, `interrupt`, `delphi`, and `mcts` strategies. MCTS selector must support simulation scoring using coherence and argument strength.
- **Goal:** Debate can run full loop using any strategy, and MCTS returns valid next turn decisions.

### Task 9 - Argument Graph Construction

- **File:** `app/argument_graph.py`
- **Description:** Build a directed graph of arguments with markdown-referenceable IDs (ARG001, etc). Support edge types: supports, attacks, qualifies. Export as both Markdown and JSON. Include metrics: contradiction ratio, depth, branching.
- **Goal:** Graph builds dynamically from debate input and exports valid JSON and Markdown formats with metrics.

### Task 10 - Context Building with Memory Integration

- **File:** `app/context_builder.py`
- **Description:** Assemble prompts that include subject, last known belief, previous stance, and memory summary. Coordinate with agent state tracker and summarizer.
- **Goal:** Output includes belief anchor, summary, and last view for the correct agent persona in prompt.

## Tools and Utilities Tasks

### Task 11 - Tools Module Development

- **File:** `app/tools.py`
- **Description:** Develop and register tool interfaces:
  - `SummarizerTool`
  - `ScorerTool`
  - `ContradictionDetector`
  - `KeywordTracker`
  - `ConsensusExtractor`
  - `DelphiScoreAnalyzer`
  - `FactCheckStub`
Each must follow callable protocol and expose structured output.
- **Goal:** All tools callable with input, return structured outputs, and register successfully in the system.

### Task 12 - Session Recovery Mechanism

- **File:** `app/session_recovery.py`
- **Description:** Enable system checkpointing per round/session. Support restore of debate state: config, agent states, argument graph, and memory.
- **Goal:** After interruption, session resumes from last checkpoint with all components restored.

### Task 13 - Performance Logger

- **File:** `app/performance_logger.py`
- **Description:** Track and log token usage, debate timing, agent response latency. Generate per-session performance summaries.
- **Goal:** Logs contain token counts, timestamps, and latency for each agent and session summary report.

### Task 14 - User Feedback Collection

- **File:** `app/user_feedback.py`
- **Description:** Collect user feedback after debates. Use structured forms to capture satisfaction, perceived coherence, bias, and suggestions for agent improvements.
- **Goal:** System collects and stores structured feedback linked to completed debate sessions.

## Output and Logging Tasks

### Task 16 - Comprehensive Logger

- **File:** `app/logger.py`
- **Description:** Produce structured Markdown and JSON logs per session:
  - Markdown agent turns
  - Mediator summaries
  - Final consensus blocks
  - Argument trees
  - Scoring tables
Export to `output/` directories with session IDs.
- **Goal:** Logs are created in Markdown and JSON for each debate session with all key components captured.

## UI Implementation Tasks

### Task 17 - Streamlit Interface Development

- **Files:** `ui/streamlit_app.py`, `ui/components.py`
- **Description:** Implement:
  - Config file uploader
  - Real-time markdown argument viewer
  - Tree visualizer panel
  - Agent state coherence map
  - Toggle buttons for contradiction highlights, agent evolution
- **Goal:** UI allows full debate setup, execution, visualization, and export without backend errors.

## Documentation Tasks

### Task 18 - Comprehensive Project Documentation

- **Files:** `README.md`, inline documentation
- **Description:** Provide usage guide, architecture overview, LLM setup, UI controls, and in-code docstrings. Ensure new contributors can set up and run the system from scratch.
- **Goal:** A developer unfamiliar with the project can set it up and run a debate using the documentation alone.

## Testing and Validation Tasks

### Task 19 - Debate Flow Testing

- **File:** `tests/test_debate_flow.py`
- **Description:** Unit tests for lifecycle from configuration → debate → logging. Include test configs for each loop strategy, mediator mode, and agent persona set.
- **Goal:** All unit tests pass for each loop strategy, config option, and persona interaction.

### Task 20 - Integration and End-to-End Testing

- **File:** Comprehensive testing setup
- **Description:** Run full debates under multiple configs. Validate argument tree structure, coherence stability, session recovery integrity, and UI responsiveness.
- **Goal:** Full-system tests validate lifecycle across configurations, tools, logging, UI, and recovery without failure.

---

✅ All task descriptions now align with validated system design  
✅ Includes updates from: design doc sections, debate lifecycle, loop strategies, MCTS, Delphi method, tools, and logging specs  
✅ Each task is self-contained with clear goals and file targets
