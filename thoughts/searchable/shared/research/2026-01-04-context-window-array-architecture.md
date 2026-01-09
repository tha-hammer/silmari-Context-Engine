---
date: 2026-01-04T19:42:29-05:00
researcher: Claude
git_commit: de6c3943998016a246dca145bad7c797845f0088
branch: main
repository: silmari-Context-Engine
topic: "Context Window Array Architecture: Separating Working and Implementation LLMs"
tags: [research, context-management, llm-orchestration, recursive-language-models, codeact, architecture]
status: complete
last_updated: 2026-01-04
last_updated_by: Claude
---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│         CONTEXT WINDOW ARRAY ARCHITECTURE RESEARCH                          │
│   Separating Working and Implementation LLMs with Addressable Context       │
│                                                                             │
│  Status: COMPLETE                              Date: 2026-01-04             │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Research: Context Window Array Architecture

**Date**: 2026-01-04T19:42:29-05:00
**Researcher**: Claude
**Git Commit**: de6c3943998016a246dca145bad7c797845f0088
**Branch**: main
**Repository**: silmari-Context-Engine

---

## Research Question

Investigate ways to separate the "working" LLM from "implementation" LLMs, structuring the context window as an addressable array where each entry can be independently managed. This should enable:

1. Passing groups of tasks (<200) to single context windows
2. Removing command invocations (Bash, Find, Grep) while retaining results
3. Creating a "central store" for the working LLM to search and retrieve context
4. Enabling context compression without losing information

Based on analysis of:
- **Recursive Language Models (RLM)**: https://alexzhang13.github.io/blog/2025/rlm/
- **Executable Code Actions (CodeAct)**: https://arxiv.org/abs/2402.01030

---

## Summary

This research synthesizes patterns from RLM (recursive LLM architecture) and CodeAct (code-as-action) papers to propose a **Hierarchical Context Array** architecture that:

| Component | Description | Source |
|-----------|-------------|--------|
| **Working LLM** | Orchestrates without seeing full context | RLM root LM pattern |
| **Implementation LLMs** | Execute bounded tasks with scoped context | RLM child LM pattern |
| **Addressable Context Store** | Array with indexed, removable entries | RLM REPL variable model |
| **Command/Result Separation** | Remove commands, retain truncated results | RLM + CodeAct patterns |
| **Central Search Store** | Query interface for context retrieval | Novel synthesis |

---

## Detailed Findings

### 1. Recursive Language Models (RLM) Architecture

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    RLM HIERARCHICAL PROCESSING                                 ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  Level 0: Root LM (Working LLM)                                               ║
║  ═════════════════════════════                                                ║
║  • Receives ONLY the query (not full context)                                 ║
║  • Context stored as Python variable in REPL                                  ║
║  • Coordinates strategy, spawns child LMs                                     ║
║  • Context window "rarely clogged"                                            ║
║                                                                               ║
║  Level 1: Child LMs (Implementation LLMs)                                     ║
║  ═══════════════════════════════════════                                      ║
║  • Handles sub-queries over context subsets                                   ║
║  • Isolated environments with scoped context                                  ║
║  • Returns results back to parent                                             ║
║                                                                               ║
║  Key Insight: "Near infinite context" through partitioning                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

**Addressable Context Patterns from RLM:**

| Pattern | Description | Example |
|---------|-------------|---------|
| **Peeking** | Sample initial context structure | `context[:100]` |
| **Grepping** | Regex-based filtering | `re.findall(pattern, context)` |
| **Partition + Map** | Chunk and parallel process | `[child_lm(chunk) for chunk in chunks]` |
| **Summarization** | Extract key information | `summarize(subset)` |

**Command/Result Separation:**

```python
# LLM outputs executable Python code
code_block = """
result = search_files("*.py", pattern="class.*Controller")
"""

# Executor returns truncated output
output = "(truncated) Found 3 matches:\n  - controller.py:15\n  - api.py:42\n..."

# Final answer via markers
FINAL(summarized_answer)
FINAL_VAR(constructed_result)
```

### 2. CodeAct Architecture

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    CODEACT ORCHESTRATION MODEL                                 ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  LLM (Orchestrator)          Python Interpreter (Executor)                    ║
║  ═════════════════          ═══════════════════════════════                   ║
║  • Generates Python code     • Executes code directly                         ║
║  • Interprets results        • Returns observations                           ║
║  • Revises actions           • Provides immediate feedback                    ║
║                                                                               ║
║  Multi-Turn Pattern:                                                          ║
║  ───────────────────                                                          ║
║  User Query → Code Action → Observation → Revised Action → ... → Final        ║
║                                                                               ║
║  Self-Debugging:                                                              ║
║  ───────────────                                                              ║
║  Error in execution → LLM observes error → Generates fix → Re-executes        ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

**Key Differences from Text Actions:**

| Aspect | Text/JSON Actions | Code Actions (CodeAct) |
|--------|-------------------|------------------------|
| Action Space | Pre-defined, limited | Flexible, composable |
| Tool Composition | Manual per-tool calls | Programmatic combination |
| Error Handling | External retry logic | Self-debugging in code |
| Context Efficiency | Full action in context | Code + truncated result |

### 3. Proposed Architecture: Hierarchical Context Array

Based on RLM and CodeAct patterns, here is a proposed architecture for separating working and implementation LLMs with addressable context:

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║              HIERARCHICAL CONTEXT ARRAY ARCHITECTURE                           ║
╚═══════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│                         CENTRAL CONTEXT STORE                                │
│  ════════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  entries: List[ContextEntry] = [                                            │
│    {id: "ctx_001", type: "file", path: "src/main.py", content: "...",      │
│     summary: "Main entry point", searchable: true},                         │
│    {id: "ctx_002", type: "command_result", command: "grep 'class'",        │
│     result: "3 matches found...", summary: "Class definitions"},            │
│    {id: "ctx_003", type: "task_result", task_id: "task_15",                │
│     result: "Implemented feature X", files_modified: ["a.py", "b.py"]},    │
│    ...                                                                      │
│  ]                                                                          │
│                                                                             │
│  Operations:                                                                │
│  • get(id) → ContextEntry                                                   │
│  • search(query) → List[ContextEntry]                                       │
│  • add(entry) → id                                                          │
│  • remove(id) → void                                                        │
│  • compress(id) → summary_only                                              │
│  • expand(id) → full_content                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│     WORKING LLM (Orchestrator)  │  │   IMPLEMENTATION LLM (Workers)  │
│  ═══════════════════════════════│  │  ═══════════════════════════════│
│                                 │  │                                 │
│  Context Window:                │  │  Context Window:                │
│  ├── Query/Task description     │  │  ├── Scoped task (1-200 items) │
│  ├── Store index/summaries      │  │  ├── Retrieved context entries │
│  ├── Task status array          │  │  ├── Specific file contents    │
│  └── Search results (refs only) │  │  └── Local execution state     │
│                                 │  │                                 │
│  Operations:                    │  │  Operations:                    │
│  • Decompose tasks              │  │  • Execute bounded task         │
│  • Search store for context     │  │  • Return result + summary      │
│  • Dispatch to workers          │  │  • Request additional context   │
│  • Aggregate results            │  │  • Mark task complete           │
│                                 │  │                                 │
│  DOES NOT SEE:                  │  │  DOES NOT SEE:                  │
│  • Full file contents           │  │  • Other workers' context       │
│  • Command execution details    │  │  • Global task state            │
│  • Other workers' context       │  │  • Store index                  │
│                                 │  │                                 │
└─────────────────────────────────┘  └─────────────────────────────────┘
```

### 4. Context Entry Schema

```python
@dataclass
class ContextEntry:
    """Single addressable entry in the context store."""

    # Identity
    id: str                          # Unique identifier (ctx_001, ctx_002, ...)
    created_at: datetime             # Creation timestamp

    # Type and source
    type: Literal[
        "file",                      # File content
        "command",                   # Command invocation (removable)
        "command_result",            # Command result (retained)
        "task",                      # Task description
        "task_result",               # Task execution result
        "search_result",             # Search/grep result
        "summary",                   # Compressed summary
        "context_request",           # Worker request for more context
    ]
    source: str                      # Origin (file path, command, task_id)

    # Content (one of these populated)
    content: Optional[str]           # Full content (expandable)
    summary: Optional[str]           # Compressed summary (always present)
    references: List[str]            # References to other entry IDs

    # Metadata
    searchable: bool                 # Include in search index
    compressed: bool                 # True if content removed, summary retained
    ttl: Optional[int]               # Time-to-live in conversation turns

    # Lineage
    parent_id: Optional[str]         # Parent entry if derived
    derived_from: List[str]          # Entry IDs this was derived from
```

### 5. Command/Result Separation Pattern

The key insight from RLM is that **commands can be removed from context while retaining results**. This is implemented through the context store's compression mechanism:

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    COMMAND/RESULT COMPRESSION                                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝

BEFORE (in context):
───────────────────
[ctx_015] type: "command"
          command: "grep -rn 'class.*Controller' src/"
          content: <full grep command invocation>

[ctx_016] type: "command_result"
          parent_id: "ctx_015"
          content: """
            src/api/user_controller.py:15:class UserController:
            src/api/auth_controller.py:22:class AuthController:
            src/api/order_controller.py:8:class OrderController:
            ... (47 more lines)
          """
          summary: "Found 50 Controller classes in src/api/"


AFTER compression (ctx_015 removed, ctx_016 compressed):
─────────────────────────────────────────────────────────
[ctx_016] type: "command_result"
          parent_id: null  # Command entry removed
          content: null    # Full content removed
          compressed: true
          summary: "Found 50 Controller classes in src/api/"
          references: ["ctx_017"]  # Reference to file index entry

[ctx_017] type: "summary"
          content: """
            Controller locations:
            - UserController: src/api/user_controller.py:15
            - AuthController: src/api/auth_controller.py:22
            - OrderController: src/api/order_controller.py:8
          """
```

### 6. Working LLM Context Window Structure

The working LLM maintains a minimal context window with references to the store:

```python
class WorkingLLMContext:
    """Context window for the orchestrating LLM."""

    # Current task state
    task_queue: List[TaskReference] = []     # Task IDs only, not full content
    active_workers: Dict[str, str] = {}      # worker_id -> task_id mapping
    completed_tasks: List[str] = []          # Completed task IDs

    # Store interface (NOT the full store)
    store_index: Dict[str, str] = {}         # id -> summary mapping
    recent_results: List[ContextEntry] = []  # Last N results (compressed)

    # Search cache
    last_search_query: str = ""
    last_search_results: List[str] = []      # Entry IDs only

    def build_context_for_llm(self) -> str:
        """Build minimal context string for working LLM."""
        return f"""
## Current Task Status
- Pending: {len(self.task_queue)} tasks
- Active: {len(self.active_workers)} workers
- Complete: {len(self.completed_tasks)} tasks

## Recent Results (summaries)
{self._format_recent_summaries()}

## Available Context (searchable)
{self._format_store_index()}

## Actions Available
- search(query) -> retrieve relevant context entries
- dispatch(task, context_ids) -> send task to implementation LLM
- aggregate(result_ids) -> combine results
- compress(entry_id) -> compress entry to summary
"""
```

### 7. Implementation LLM Context Window Structure

Each implementation LLM receives a scoped, bounded context:

```python
class ImplementationLLMContext:
    """Context window for an implementation worker LLM."""

    # Task assignment (bounded to <200 items)
    task: TaskDescription               # Single task or task group
    assigned_entries: List[ContextEntry]  # Full content for assigned entries

    # Execution state
    execution_log: List[str] = []       # Actions taken
    results: List[str] = []             # Generated results

    # Context requests (for when more info needed)
    pending_requests: List[ContextRequest] = []

    def build_context_for_llm(self) -> str:
        """Build scoped context string for implementation LLM."""
        return f"""
## Your Task
{self.task.description}

## Available Context
{self._format_assigned_entries()}

## Execution Log
{self._format_execution_log()}

## Actions Available
- execute(code) -> run code and return result
- request_context(query) -> ask orchestrator for more context
- complete(result, summary) -> mark task complete with result
"""

    def get_entry_count(self) -> int:
        """Ensure bounded context."""
        return len(self.assigned_entries)

    def validate_bounds(self, max_entries: int = 200) -> bool:
        """Enforce <200 entry limit."""
        return self.get_entry_count() <= max_entries
```

### 8. Central Store Search Interface

The central store provides a search interface for the working LLM to retrieve context without loading everything:

```python
class CentralContextStore:
    """Addressable context store with search capabilities."""

    entries: Dict[str, ContextEntry] = {}
    search_index: SearchIndex = None  # e.g., BM25 or vector-based

    def search(
        self,
        query: str,
        max_results: int = 10,
        entry_types: Optional[List[str]] = None,
        include_compressed: bool = True
    ) -> List[ContextEntry]:
        """Search store and return relevant entries.

        Returns summaries by default, not full content.
        Working LLM can then request expansion of specific entries.
        """
        results = self.search_index.query(query, max_results)

        if entry_types:
            results = [r for r in results if r.type in entry_types]

        if not include_compressed:
            results = [r for r in results if not r.compressed]

        # Return with summaries only (not full content)
        return [self._to_summary_view(r) for r in results]

    def expand(self, entry_id: str) -> ContextEntry:
        """Get full content for a specific entry."""
        entry = self.entries[entry_id]
        if entry.compressed:
            raise ValueError(f"Entry {entry_id} is compressed, content unavailable")
        return entry

    def compress(self, entry_id: str) -> None:
        """Compress entry to summary only."""
        entry = self.entries[entry_id]
        if entry.summary is None:
            entry.summary = self._generate_summary(entry.content)
        entry.content = None
        entry.compressed = True

    def add_command_result(
        self,
        command: str,
        result: str,
        keep_command: bool = False
    ) -> str:
        """Add command result, optionally discarding command entry.

        This is the key pattern from RLM - commands can be removed
        while their results are retained (possibly compressed).
        """
        result_id = self._generate_id()

        if keep_command:
            command_id = self._generate_id()
            self.entries[command_id] = ContextEntry(
                id=command_id,
                type="command",
                content=command,
                summary=f"Executed: {command[:50]}...",
                searchable=False,  # Don't search command text
            )
        else:
            command_id = None

        self.entries[result_id] = ContextEntry(
            id=result_id,
            type="command_result",
            parent_id=command_id,
            content=result,
            summary=self._generate_summary(result),
            searchable=True,
        )

        return result_id
```

### 9. Integration with Existing Codebase

The proposed architecture maps to existing patterns in the codebase:

| Proposed Component | Existing Pattern | Location |
|-------------------|------------------|----------|
| CentralContextStore | Session logging | `integrated_orchestrator.py:187-227` |
| ContextEntry | Dictionary results | `steps.py:12-102` |
| WorkingLLMContext | IntegratedOrchestrator | `integrated_orchestrator.py` |
| ImplementationLLMContext | claude_runner result | `claude_runner.py:120-236` |
| Entry compression | Text chunks list | `claude_runner.py:145-177` |
| Search interface | BeadsController | `beads_controller.py` |

**Existing Patterns to Extend:**

1. **Dictionary Result Pattern** (`steps.py`):
```python
# Current pattern
return {
    "success": True,
    "research_path": path,
    "output": result["output"],
    "open_questions": questions
}

# Extended for context store
return ContextEntry(
    id=generate_id(),
    type="task_result",
    content=result["output"],
    summary=extract_summary(result["output"]),
    references=[path],
)
```

2. **BAML Structured Responses** (`baml_src/functions.baml`):
```baml
// Current: Returns structured data
function ProcessGate1(...) -> InitialExtractionResponse

// Extended: Returns with context metadata
class ContextAwareResponse {
    data InitialExtractionResponse
    context_entries ContextEntry[]  // Entries to add to store
    compress_ids string[]           // Entries to compress
}
```

3. **Streaming Accumulation** (`claude_runner.py`):
```python
# Current: Accumulate text chunks
text_chunks: list[str] = []
for message in stream:
    text_chunks.append(block.text)

# Extended: Accumulate as context entries
context_entries: list[ContextEntry] = []
for message in stream:
    entry = ContextEntry(
        type="stream_chunk",
        content=block.text,
        summary=None,  # Generate on completion
    )
    context_entries.append(entry)
```

### 10. Task Batching (<200 Entries)

The RLM paper demonstrates that bounded task groups work well. Here's the proposed batching strategy:

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    TASK BATCHING STRATEGY                                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Working LLM (Orchestrator):
───────────────────────────
1. Receive high-level task
2. Decompose into subtasks
3. Group subtasks by:
   - Shared context requirements
   - Dependencies (same dependency chain)
   - Type (all file edits, all tests, all docs)
4. Ensure each group has <200 context entries
5. Dispatch groups to implementation LLMs

Batching Rules:
───────────────
• Max 200 context entries per implementation LLM
• Max 50 files per batch
• Max 20 related tasks per batch
• Shared dependencies count as 1 entry (not N)

Example:
────────
Task: "Implement authentication system"

Batch 1 (43 entries):
├── Context: auth requirements doc, existing user model, 3 related files
└── Tasks: Create auth controller, Create login endpoint

Batch 2 (87 entries):
├── Context: auth controller (from batch 1), test patterns, 5 related files
└── Tasks: Write auth tests, Write integration tests

Batch 3 (112 entries):
├── Context: all auth files, documentation templates
└── Tasks: Write auth documentation, Update README
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         CONTEXT WINDOW ARRAY ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   User Request                                                                      │
│        │                                                                            │
│        ▼                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐       │
│   │                    WORKING LLM (Orchestrator)                            │       │
│   │                                                                          │       │
│   │  Context: [query, task_index, store_summaries, search_cache]            │       │
│   │           (minimal - no file contents, no command details)              │       │
│   │                                                                          │       │
│   │  Actions:                                                                │       │
│   │  1. Decompose task → subtasks                                           │       │
│   │  2. Search store → find relevant context                                │       │
│   │  3. Batch subtasks (<200 entries each)                                  │       │
│   │  4. Dispatch to workers                                                 │       │
│   │  5. Aggregate results                                                   │       │
│   │  6. Compress completed entries                                          │       │
│   └───────────────┬─────────────────────────────────────────┬───────────────┘       │
│                   │                                         │                       │
│        ┌──────────┴──────────┐               ┌──────────────┴──────────────┐        │
│        │    search(query)    │               │  dispatch(task, ctx_ids)   │        │
│        ▼                     │               ▼                             │        │
│   ┌──────────────────────────┴───────────────────────────────────────────┐ │        │
│   │                    CENTRAL CONTEXT STORE                              │ │        │
│   │                                                                       │ │        │
│   │  entries[]:                                                           │ │        │
│   │  ┌────────┬────────┬─────────────────┬──────────────────┬───────────┐│ │        │
│   │  │ ctx_001│ file   │ src/auth.py     │ content: "..."   │ summary  ││ │        │
│   │  │ ctx_002│ result │ grep class      │ content: null    │ "50 cls" ││◄┘        │
│   │  │ ctx_003│ task   │ "implement X"   │ content: "..."   │ summary  ││          │
│   │  │ ctx_004│ result │ task_003        │ content: "..."   │ summary  ││          │
│   │  └────────┴────────┴─────────────────┴──────────────────┴───────────┘│          │
│   │                                                                       │          │
│   │  Operations: add(), get(), search(), compress(), expand()            │          │
│   └───────────────────────────────────┬───────────────────────────────────┘          │
│                                       │                                             │
│        ┌──────────────────────────────┼──────────────────────────────┐              │
│        │                              │                              │              │
│        ▼                              ▼                              ▼              │
│   ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐          │
│   │ IMPLEMENTATION    │    │ IMPLEMENTATION    │    │ IMPLEMENTATION    │          │
│   │ LLM Worker 1      │    │ LLM Worker 2      │    │ LLM Worker N      │          │
│   │                   │    │                   │    │                   │          │
│   │ Context:          │    │ Context:          │    │ Context:          │          │
│   │ - Task: "impl X"  │    │ - Task: "test Y"  │    │ - Task: "doc Z"   │          │
│   │ - 43 entries      │    │ - 87 entries      │    │ - 112 entries     │          │
│   │ - Scoped files    │    │ - Test patterns   │    │ - Doc templates   │          │
│   │                   │    │                   │    │                   │          │
│   │ Returns:          │    │ Returns:          │    │ Returns:          │          │
│   │ - Result + summary│    │ - Result + summary│    │ - Result + summary│          │
│   └─────────┬─────────┘    └─────────┬─────────┘    └─────────┬─────────┘          │
│             │                        │                        │                    │
│             └────────────────────────┴────────────────────────┘                    │
│                                      │                                             │
│                                      ▼                                             │
│                             Store results in                                       │
│                             CentralContextStore                                    │
│                             (command removed,                                      │
│                              result retained)                                      │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Code References

### Papers Referenced

| Paper | URL | Key Pattern |
|-------|-----|-------------|
| Recursive Language Models | https://alexzhang13.github.io/blog/2025/rlm/ | Context as REPL variable, hierarchical LMs |
| Executable Code Actions (CodeAct) | https://arxiv.org/abs/2402.01030 | Code as action space, self-debugging |

### Existing Codebase Locations

| Component | Location | Relevance |
|-----------|----------|-----------|
| Dictionary result pattern | `planning_pipeline/steps.py:12-102` | Model for ContextEntry |
| Streaming text chunks | `planning_pipeline/claude_runner.py:145-177` | Accumulation pattern |
| Session logging | `planning_pipeline/integrated_orchestrator.py:187-227` | Store persistence |
| Dataclass models | `planning_pipeline/models.py:28-309` | Entry schema pattern |
| BAML responses | `baml_src/functions.baml:369-454` | Structured LLM responses |
| BeadsController | `planning_pipeline/beads_controller.py` | Search/query interface |

---

## Historical Context (from thoughts/)

| Document | Path | Relevance |
|----------|------|-----------|
| Loop Runner Analysis | `thoughts/shared/research/2026-01-01-loop-runner-integrated-orchestrator-analysis.md` | Orchestrator patterns |
| Terminal Streaming Output | `thoughts/shared/research/2026-01-04-terminal-streaming-output-flow.md` | Output handling |
| Planning Pipeline System | `thoughts/shared/research/2026-01-03-planning-pipeline-system-diagram.md` | Architecture overview |

---

## Implementation Recommendations

### Phase 1: Context Entry Schema

1. Define `ContextEntry` dataclass in `planning_pipeline/models.py`
2. Add `to_dict()` and `from_dict()` serialization
3. Define entry types enum
4. Add validation for bounded entries

### Phase 2: Central Store

1. Create `planning_pipeline/context_store.py`
2. Implement CRUD operations
3. Add compression/expansion logic
4. Integrate with existing session logging

### Phase 3: Search Interface

1. Add search index (BM25 or simple TF-IDF initially)
2. Implement `search()` with filtering
3. Add summary-only returns
4. Enable selective expansion

### Phase 4: Working/Implementation Split

1. Define context builder for working LLM
2. Define scoped context for implementation LLMs
3. Implement task batching with <200 entry limit
4. Add result aggregation

### Phase 5: Command/Result Separation

1. Modify `run_claude_sync` to emit context entries
2. Implement command removal with result retention
3. Add automatic compression for completed commands
4. Integrate with streaming output

---

## Open Questions

1. **Search Index Technology**: BM25 vs vector embeddings vs hybrid?
2. **Compression Timing**: When to auto-compress (after N turns? on memory pressure?)
3. **Entry TTL**: Should entries expire? How to handle long-running sessions?
4. **Worker Scaling**: Fixed pool vs dynamic spawning of implementation LLMs?
5. **Context Request Flow**: How should workers request more context from orchestrator?

---

## Related Research

- `thoughts/shared/research/2026-01-01-loop-runner-integrated-orchestrator-analysis.md`
- `thoughts/shared/research/2026-01-04-terminal-streaming-output-flow.md`
- `thoughts/shared/research/2026-01-03-planning-pipeline-system-diagram.md`

---

## Conclusion

The combination of RLM's hierarchical context management and CodeAct's code-as-action paradigm provides a strong foundation for the proposed architecture. Key innovations:

1. **Working LLM sees only summaries** - Never loads full file contents or command details
2. **Implementation LLMs get scoped context** - Bounded to <200 entries per worker
3. **Commands are removable** - Results retained with summaries, commands discarded
4. **Central store enables search** - Working LLM queries for context without loading
5. **Entry IDs enable reference** - Context is addressable and composable

This architecture directly addresses the research question of separating working and implementation LLMs while enabling efficient context management through an addressable array structure.
