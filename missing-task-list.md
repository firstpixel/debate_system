# 📋 Pending and Prioritized Task List for Autonomous Multi-LLM Markdown Debate Engine (Post-Wiring Validation)

This list includes only tasks that are still **incomplete or partially wired**, validated across full chat history and design documents. Tasks are now sorted based on dependency priority: memory → context → loop → tooling → logging.

---

## 🧠 Core Memory & Context Foundation

### Task 1 - Unified MemoryManager Final Wiring
- **File:** `app/memory_manager.py`
- **Description:** Complete centralized memory logic for STM (MongoDB), LTM (Qdrant), RAG sources, and belief persistence. Finalize core API functions:
  - `.add_turn()` – Store interaction per agent/round
  - `.get_context()` – Return scoped memory (rolling, rag, belief)
  - `.summarize()` – Compress belief/history as context
  - `.query_rag()` – Pull factual context from long-term sources
  - `.save_belief()` – Track evolving positions across debates
- **Goal:** All context, tools, and strategy flows pull memory exclusively from this interface.

### Task 2 - Context Builder + RAG/Belief Awareness
- **File:** `app/context_builder.py`, `app/memory_manager.py`
- **Description:** Assemble prompts using scoped memory (STM, LTM, beliefs) per agent + subject. Must dynamically select memory strategy from config and truncate properly.
- **Goal:** All persona prompts reflect belief anchor + relevant memory. Confirmed via log diff and context token trace.

---

## 🔥 High-Priority Core Logic

### Task 3 - Persona Agent Memory & Belief Integration
- **File:** `app/persona_agent.py`
- **Description:** Ensure persona agents update belief state post-response and reflect accurate context in each round. Integrate with `MemoryManager` for state logging.
- **Goal:** Each persona reflects consistent stance across rounds. Belief changes are stored and visible in logs.

### Task 4 - Mediator Agent: Delphi Facilitator Mode Finalization
- **File:** `app/mediator_agent.py`, `app/delphi_engine.py`
- **Description:** Enable mediator to initiate Delphi rounds, aggregate anonymous responses, guide feedback loops, and post consensus blocks.
- **Goal:** Delphi facilitator executes after each round, adds convergence block to Markdown log, and updates LTM.

### Task 5 - Bayesian Tracker Full Integration
- **File:** `app/bayesian_tracker.py`
- **Description:** Integrate coherence, contradiction, topic drift, and belief similarity analysis with the main loop, scoring tools, and memory updates.
- **Goal:** Tracker outputs metrics used by Delphi and MCTS systems. Values contribute to contradiction warnings and agent guidance.

### Task 6 - Agent State Tracker Consistency
- **File:** `app/agent_state_tracker.py`
- **Description:** Ensure summary of evolving beliefs per agent is accurate, consistent with MemoryManager, and truncated as needed for prompt injection.
- **Goal:** Agent state tracker exposes summary view used in prompt and logging layers.

---

## 🧪 Decision Loops & Strategy Systems

### Task 7 - Delphi Strategy (Engine + Convergence Metrics)
- **Files:** `app/flow_control.py`, `app/tools.py`, `app/delphi_engine.py`
- **Description:** Implement round-wide Delphi logic:
  - Gather anonymous inputs
  - Synthesize consensus or divergence map
  - Track convergence % and revision behavior
  - Store block in memory and export logs
- **Goal:** Delphi cycles run post-round, and feedback loop outputs are visualized + stored.

### Task 8 - LLM-Based MCTS with Multi-Branching
- **Files:** `app/turn_strategy/mcts_turn_selector.py`, `app/tools.py`, `app/bayesian_tracker.py`, `app/memory_manager.py`
- **Description:** Expand MCTS logic to generate argument tree branches using LLM. Score each using belief coherence, contradiction signals, and memory alignment.
- **Goal:** MCTS turn decisions reflect scored tree branches. Most consistent and relevant path is selected.

---

## 🛠 Tools and Plugins

### Task 9 - Finalize Tool Interfaces + Hook to MemoryManager
- **File:** `app/tools.py`
- **Description:** Complete `ScorerTool`, `DelphiScoreAnalyzer`, `ContradictionDetector`, `FactCheckStub` with full access to context from MemoryManager.
- **Goal:** All tools return structured output, use memory, and influence strategy decisions or logs.

### Task 10 - Plugin System Loader
- **File:** `app/integration_plugin.py`
- **Description:** Implement plugin discovery and loading system with YAML or Python entrypoints. Allow tools like `ExternalFactCheck` or `WebRAG` to be injected.
- **Goal:** Plugins can be added dynamically and executed from mediator/tool interfaces.

---

## 📜 Logging & Summarization

### Task 11 - Structured JSON Export + Belief Trails
- **File:** `app/logger.py`
- **Description:** Extend logging to export:
  - Agent belief history per round
  - Tool scoring + feedback
  - Delphi/MCTS reasoning and selected path
- **Goal:** JSON logs contain `{belief_evolution}`, `{tool_reasoning}`, `{strategy_trace}` fields per round.

### Task 12 - Final Documentation Pass
- **Files:** `README.md`, inline
- **Description:** Complete module docstrings, config examples, and tool interface documentation. Include how to wire plugins, enable Delphi/MCTS.
- **Goal:** All modules are documented. A new developer can configure, run, and extend the system.

### Task 13 - Flow + Tool Unit Testing
- **File:** `tests/test_debate_flow.py`
- **Description:** Write tests for:
  - MemoryManager consistency
  - MCTS branching outputs
  - Delphi consensus logic
  - Tool outputs given belief conflict/memory scenarios
- **Goal:** All modules achieve baseline test coverage. Tools are tested in isolation + flow integration.

---


