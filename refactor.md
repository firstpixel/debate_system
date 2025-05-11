Here is a full **refactor task list** for implementing the "AgentStateTracker as the single source of truth" architecture, with full validation of dependencies, expected file changes, and interaction flow.

---

# ✅ Refactor Task List: Centralized Memory via `AgentStateTracker`

> 🎯 Goal: All agents interact **only** with `AgentStateTracker`, which manages all memory via `MemoryManager`.

---

## 🔹 TASK 1 — Unify `MemoryManager` Interfaces

**Files:**

* `app/memory_manager.py`
* `memory/qdrant_store.py`
* `memory/mongo_store.py`
* `memory/embeddings.py` (if needed for `rag`)

**Changes:**

* Add unified interface properties:

```python
self.belief
self.contradiction
self.stm
self.ltm
self.rag
```

* Each must expose required methods (`get_beliefs`, `save_belief`, `get_turns_raw`, `query_text`, etc.)
* Standardize return values:

  * Beliefs: Markdown string
  * Contradictions: Markdown string
  * STM/LTM: List of full LLM messages (dicts with `role`, `content`)
  * RAG: Markdown string

✅ Store `beliefs` and `contradictions` as a single Mongo doc per agent.
✅ Use overwrite logic, not append logic.

---

## 🔹 TASK 2 — Refactor `AgentStateTracker` to Own State Logic

**Files:**

* `app/agent_state_tracker.py`

**Changes:**

* Inject and wrap `MemoryManager`
* Move all logic into the tracker:

  * `get_beliefs()` → returns markdown string
  * `save_belief(text)` → extract bullets, deduplicate, contradiction check, save belief+contradiction
  * `get_recent_messages()` → from STM
  * `query_ltm()` → from LTM
  * `query_rag()` and `list_rag_docs()` → from RAG
  * `summarize_memory()` → summarize older STM
* Remove all raw list memory, only use Markdown output

✅ All belief/contradiction logic now calls `self.memory.belief` and `self.memory.contradiction`
✅ STM/LTM returns are structured as `{"role": "user", "content": ...}`

---

## 🔹 TASK 3 — Update `PersonaAgent` to Use Only `tracker`

**Files:**

* `app/persona_agent.py`

**Changes:**

* Remove all direct `belief_store` or `memory_manager` use
* Use only:

```python
beliefs = self.tracker.get_beliefs()
stm = self.tracker.get_recent_messages()
ltm = self.tracker.query_ltm()
rag = self.tracker.query_rag(query)
```

* Replace contradiction detection with `tracker.last_contradiction()`

✅ Remove `self.memory`, `self.belief_store`, `self.db`
✅ Move `contradiction_log` outside the agent — use `tracker` only

---

## 🔹 TASK 4 — Update `BayesianTracker` to Use Agent Trackers

**Files:**

* `app/bayesian_tracker.py`

**Changes:**

* Accept injected `agent_trackers: Dict[str, AgentStateTracker]`
* Replace any call to `memory.save_belief(...)` with:

```python
agent_tracker = self.trackers[agent_name]
agent_tracker.save_belief(message)
```

* Read beliefs via `agent_tracker.get_beliefs()`

✅ BayesianTracker becomes a pure analysis tool
✅ Does not persist state

---

## 🔹 TASK 5 — Update `DebateManager` to Wire Everything Correctly

**Files:**

* `app/debate_manager.py`

**Changes:**

* After creating each `PersonaAgent`, collect:

```python
self.agent_trackers = {a.name: a.tracker for a in self.agents}
```

* Inject `self.agent_trackers` into `BayesianTracker`

✅ No direct memory or belief access outside trackers

---

## 🔹 TASK 6 — Simplify `ContextBuilder` to Use Trackers

**Files:**

* `app/context_builder.py`

**Changes:**

* Use:

```python
beliefs = agent.tracker.get_beliefs()
context = agent.tracker.get_recent_messages()
```

* Stop accessing `memory.get_context(...)`

✅ All context is pulled from `AgentStateTracker` only

---

## 🔹 TASK 7 — Update `BeliefStore` and `ContradictionStore` Logic

**Files:**

* `memory/mongo_store.py`

**Changes:**

* Replace multiple document storage with:

  * **One doc per agent**, e.g. `_id = agent_name`
  * Overwrite strategy for save/update
* Beliefs and contradictions stored as:

```python
{
  "_id": agent_id,
  "all_beliefs": "• belief 1\n• belief 2\n...",
  "contradictions": "• conflict 1\n• conflict 2\n..."
}
```

✅ This removes DB bloat and keeps belief/contradiction clean

---

## 🔹 TASK 8 — Add `list_documents()` to `RAGRetriever`

**Files:**

* `memory/qdrant_store.py`

**Changes:**

* Add a method:

```python
def list_documents(self, agent_id: str) -> List[str]:
    ...
```

✅ Lets the agent browse what they’ve read via RAG

---

## 🔹 TASK 9 — Final Validation and Tests

**Files:**

* `tests/test_memory_interface.py`
* `tests/test_tracker_logic.py`
* `tests/test_debate_flow.py`

**Tests:**

* Agent can:

  * Read beliefs, STM, LTM, RAG
  * Save beliefs without duplication
  * See contradiction detection
* Debate runs with no memory call outside `tracker`

---

## Optional: Add `AgentMemorySummaryTool` Later

You can wrap this new unified interface as a tool:

```python
# app/tools/memory_summary_tool.py

class AgentMemorySummaryTool:
    def __init__(self, tracker: AgentStateTracker): ...
    def run(self) -> str: ...
```

---

Would you like the full implementation for **Task 1** to begin? Please upload any missing files if needed (like `mongo_store.py` or `qdrant_store.py`).
