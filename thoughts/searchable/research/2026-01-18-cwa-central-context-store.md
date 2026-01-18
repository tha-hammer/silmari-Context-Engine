---
date: 2026-01-18T13:10:45-05:00
researcher: Claude
git_commit: fe43a50b9fd07ad5b73defb44f28a56c30f0d73f
branch: cli-wrapper-restore
repository: silmari-Context-Engine
topic: "CWA Central Context Store Research"
tags: [research, cwa, context-window-array, context-management, central-context-store]
status: complete
last_updated: 2026-01-18
last_updated_by: Claude
---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│           CWA CENTRAL CONTEXT STORE RESEARCH                                 │
│   Comprehensive Analysis of the Addressable Context Management System       │
│                                                                             │
│  Status: COMPLETE                              Date: 2026-01-18             │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Research: CWA Central Context Store

**Date**: 2026-01-18T13:10:45-05:00
**Researcher**: Claude
**Git Commit**: fe43a50b9fd07ad5b73defb44f28a56c30f0d73f
**Branch**: cli-wrapper-restore
**Repository**: silmari-Context-Engine

---

## 📚 Research Question

What is the CWA's Central Context Store, how is it structured, what are its capabilities, and how does it integrate with the rest of the system?

---

## 📊 Summary

The **Central Context Store** (`CentralContextStore`) is the core component of the Context Window Array (CWA) architecture. It serves as a **single source of truth** for all addressable context entries, enabling:

| Capability | Description |
|------------|-------------|
| **Addressable Storage** | Store entries by unique ID (format: `ctx_XXXXXX`) |
| **CRUD Operations** | Add, get, remove, update context entries |
| **Semantic Search** | TF-IDF/cosine similarity search via `VectorSearchIndex` |
| **TTL Management** | Time-to-live expiration for entries |
| **Compression** | Remove content while retaining summaries |
| **Command/Result Separation** | Store results, optionally discard commands |
| **Type Filtering** | Query by entry type (FILE, COMMAND, TASK, etc.) |

The store separates **Working LLM** (orchestrator, sees summaries only) from **Implementation LLM** (workers, see full content, bounded to <200 entries).

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CENTRAL CONTEXT STORE                                │
│  ════════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  _entries: Dict[str, ContextEntry]  ──────┐                                 │
│  _id_counter: int                          │                                │
│  _search_index: VectorSearchIndex   ◄──────┘                                │
│                                                                             │
│  Operations:                                                                │
│  • add(entry) → id           • get(id) → entry                              │
│  • remove(id) → bool         • contains(id) → bool                          │
│  • search(query) → results   • compress(id) → bool                          │
│  • get_by_type(type) → list  • process_turn() → stats                       │
│                                                                             │
└────────────────────────────────────────────┬────────────────────────────────┘
                                             │
                   ┌─────────────────────────┼─────────────────────────┐
                   ▼                         ▼                         ▼
      ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐
      │  WorkingLLMContext     │  │ ImplementationLLMContext│  │    CWAIntegration      │
      │  (Summaries Only)      │  │ (Full Content, <200)   │  │  (High-Level API)      │
      └────────────────────────┘  └────────────────────────┘  └────────────────────────┘
```

---

## 📁 File Structure

| File | Purpose | Lines |
|------|---------|-------|
| `context_window_array/store.py` | Central store implementation | 414 |
| `context_window_array/models.py` | ContextEntry, EntryType | 320 |
| `context_window_array/search_index.py` | VectorSearchIndex | 295 |
| `context_window_array/working_context.py` | WorkingLLMContext | 190 |
| `context_window_array/implementation_context.py` | ImplementationLLMContext | 287 |
| `context_window_array/batching.py` | TaskBatcher, BatchExecutor | 294 |
| `context_window_array/exceptions.py` | Custom exceptions | 33 |
| `context_window_array/__init__.py` | Public exports | 37 |
| `silmari_rlm_act/context/cwa_integration.py` | Pipeline integration layer | 468 |

---

## 🔍 Core Components

### 1. CentralContextStore (`store.py`)

The main class that manages all context entries:

```python
class CentralContextStore:
    """Addressable context store with CRUD operations."""
    
    def __init__(self):
        self._entries: dict[str, ContextEntry] = {}
        self._id_counter: int = 0
        self._search_index: VectorSearchIndex = VectorSearchIndex()
```

**Key Methods:**

| Method | Description | Returns |
|--------|-------------|---------|
| `add(entry)` | Add entry to store | Entry ID |
| `get(entry_id)` | Retrieve entry by ID | `ContextEntry` or `None` |
| `remove(entry_id, return_entry)` | Remove entry | `bool` or removed entry |
| `contains(entry_id)` | Check if entry exists | `bool` |
| `get_all()` | Get all entries | `list[ContextEntry]` |
| `get_by_type(entry_type)` | Filter by type | `list[ContextEntry]` |
| `search(query, ...)` | Semantic search | `list[StoreSearchResult]` |
| `compress(entry_id)` | Compress to summary only | `bool` |
| `process_turn()` | TTL decrement + cleanup | `dict[str, int]` |
| `add_command_result(...)` | Store command result | Result entry ID |

### 2. ContextEntry (`models.py`)

The data structure for each context entry:

```python
@dataclass
class ContextEntry:
    # Required fields
    id: str                          # Unique ID (ctx_XXX)
    entry_type: EntryType            # FILE, COMMAND, TASK, etc.
    source: str                      # Origin (file path, command, etc.)
    content: Optional[str]           # Full content (None if compressed)
    summary: Optional[str]           # Compressed summary
    
    # Optional fields
    created_at: datetime             # Creation timestamp
    references: list[str]            # Referenced entry IDs
    searchable: bool = True          # Include in search index
    compressed: bool = False         # Is content removed?
    ttl: Optional[int] = None        # Time-to-live in turns
    parent_id: Optional[str] = None  # Parent entry ID
    derived_from: list[str] = []     # Derivation lineage
    priority: int = 0                # Priority for ordering
```

### 3. EntryType Enum (`models.py`)

```python
class EntryType(Enum):
    FILE = "file"                    # File content from codebase
    COMMAND = "command"              # Command invocation (removable)
    COMMAND_RESULT = "command_result" # Command output (retained)
    TASK = "task"                    # Task description
    TASK_RESULT = "task_result"      # Task execution result
    SEARCH_RESULT = "search_result"  # Search/grep output
    SUMMARY = "summary"              # Compressed summary
    CONTEXT_REQUEST = "context_request" # Worker context request
```

### 4. VectorSearchIndex (`search_index.py`)

TF-IDF based semantic search using numpy:

```python
class VectorSearchIndex:
    """Vector search index using TF-IDF and cosine similarity."""
    
    def __init__(self):
        self._entry_texts: dict[str, str] = {}    # id -> text
        self._entry_types: dict[str, EntryType] = {}  # id -> type
        self._vocabulary: set[str] = set()
        self._term_to_idx: dict[str, int] = {}
        self._vectors: dict[str, np.ndarray] = {}
```

**Search Features:**
- Tokenizes on word boundaries (`\b[a-zA-Z_][a-zA-Z0-9_]*\b`)
- Builds TF-IDF vectors per entry
- Computes cosine similarity between query and entries
- Filters by entry type
- Enforces minimum score threshold
- Results ranked by score (descending)

---

## 🎯 Key Patterns

### Pattern 1: Command/Result Separation

Commands can be discarded while retaining their results:

```python
result_id = store.add_command_result(
    command="grep -rn 'class' src/",
    result="Found 50 matches:\n  src/main.py:10...",
    summary="50 class definitions found",
    keep_command=False,  # Discard command, keep result
)
```

**Behavior:**
- If `keep_command=False`: Only result entry created
- If `keep_command=True`: Both command and result entries created
- Command entries are marked `searchable=False`
- Result entry gets `parent_id` pointing to command (if kept)

### Pattern 2: TTL (Time-to-Live) Management

Entries can auto-expire after N conversation turns:

```python
# Create entry with TTL
entry = ContextEntry(
    id="ctx_001",
    entry_type=EntryType.TASK,
    source="orchestrator",
    content="...",
    summary="...",
    ttl=5,  # Expires after 5 turns
)

# Process a turn (call at end of each conversation turn)
stats = store.process_turn()
# Returns: {"decremented": 3, "removed": 1}
```

**TTL Lifecycle:**
1. Entry created with `ttl=N`
2. Each `process_turn()` decrements TTL by 1
3. When `ttl=0`, entry is expired
4. `cleanup_expired()` removes expired entries

### Pattern 3: Compression

Remove content but retain summary for memory efficiency:

```python
# Compress an entry
store.compress("ctx_001")

# Entry after compression:
entry.compressed = True
entry.content = None
entry.summary = "Original summary preserved"
```

**Compression Rules:**
- Entry must have a summary to be compressed
- Already compressed entries are no-op
- Accessing content of compressed entry raises `ContextCompressedError`

### Pattern 4: Working vs Implementation Context Separation

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                    CONTEXT SEPARATION                                      ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  Working LLM (Orchestrator)         Implementation LLM (Workers)          ║
║  ──────────────────────────         ─────────────────────────────         ║
║  • Sees SUMMARIES only              • Sees FULL CONTENT                   ║
║  • No entry limit                   • Bounded to <200 entries             ║
║  • Coordinates tasks                • Executes specific tasks             ║
║  • Searches for context             • Gets pre-selected context           ║
║  • Uses WorkingLLMContext           • Uses ImplementationLLMContext       ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## 🔗 Integration Layer: CWAIntegration

The `CWAIntegration` class in `silmari_rlm_act/context/cwa_integration.py` provides a high-level API:

```python
class CWAIntegration:
    """Manages Context Window Array for pipeline phases."""
    
    def __init__(self, max_impl_entries: int = 200):
        self._store = CentralContextStore()
        self._working_ctx = WorkingLLMContext(self._store)
        self._impl_ctx = ImplementationLLMContext(self._store, max_entries=max_impl_entries)
        self._batcher = TaskBatcher(max_entries_per_batch=max_impl_entries)
        self._executor = BatchExecutor(self._store, max_entries=max_impl_entries)
```

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `store_research(path, content, summary)` | Store research document |
| `store_requirement(req_id, desc, summary, ttl)` | Store requirement (TTL=20) |
| `store_plan(path, content, summary)` | Store TDD plan |
| `store_command_result(cmd, result, summary)` | Store command output |
| `search(query, max_results, min_score)` | Search entries |
| `build_working_context(entry_types)` | Build orchestrator context |
| `build_impl_context(entry_ids)` | Build worker context |
| `request_entries(entry_ids)` | Context manager for impl context |
| `create_batches(tasks, max_entries)` | Create task batches |
| `execute_batch(batch, handler)` | Execute batch with context |
| `process_turn()` | Process TTL lifecycle |

---

## 📐 Task Batching

The `TaskBatcher` groups tasks to respect the <200 entry limit:

```python
# Define tasks with required context
tasks = [
    TaskSpec(id="t1", description="...", required_entry_ids=["ctx_001", "ctx_002"]),
    TaskSpec(id="t2", description="...", required_entry_ids=["ctx_002", "ctx_003"]),
    TaskSpec(id="t3", description="...", required_entry_ids=["ctx_004"]),
]

# Create batches
batcher = TaskBatcher(max_entries_per_batch=200)
batches = batcher.create_batches(tasks, sort_by_priority=True)

# Execute batches
executor = BatchExecutor(store, max_entries=200)
results = executor.execute_all(batches, handler_function)
```

**Batching Algorithm:**
1. Optionally sort tasks by priority
2. Accumulate tasks into current batch
3. Track unique entry IDs across tasks
4. When adding a task would exceed limit, start new batch
5. Mark batches that exceed limit as `exceeds_limit=True`

---

## 🧪 Test Coverage

The store has comprehensive tests in `context_window_array/tests/test_store.py`:

| Test Class | Behaviors Tested |
|------------|------------------|
| `TestStoreAddGet` | Add, get, contains, len, get_all, get_by_type |
| `TestStoreRemove` | Remove, remove_multiple, clear, return_entry |
| `TestStoreCompression` | Compress, get_content, get_summary, compress_multiple |
| `TestCommandResultSeparation` | add_command_result, keep_command, parent_id |
| `TestStoreTTLProcessing` | process_ttl, cleanup_expired, process_turn, extend_ttl |

---

## 📖 Usage Examples

### Basic Store Operations

```python
from context_window_array import CentralContextStore, ContextEntry, EntryType

# Create store
store = CentralContextStore()

# Add entry
entry = ContextEntry(
    id="ctx_001",
    entry_type=EntryType.FILE,
    source="src/auth.py",
    content="def authenticate(): ...",
    summary="Authentication function",
)
store.add(entry)

# Retrieve entry
retrieved = store.get("ctx_001")

# Search
results = store.search("authentication", max_results=5)
for r in results:
    print(f"{r.entry_id}: {r.summary} (score: {r.score:.2f})")
```

### Working LLM Context

```python
from context_window_array.working_context import WorkingLLMContext

working = WorkingLLMContext(store)

# Build context (summaries only)
context = working.build()
for entry in context.entries:
    print(f"{entry.id}: {entry.summary}")  # content is always None

# Search from working perspective
results = working.search("database connection")
```

### Implementation LLM Context

```python
from context_window_array.implementation_context import ImplementationLLMContext

impl = ImplementationLLMContext(store, max_entries=200)

# Request context with auto-release
with impl.request(["ctx_001", "ctx_002"]) as context:
    for entry in context.entries:
        print(f"{entry.id}: {entry.content}")  # Full content available
# Entries automatically released after with block
```

---

## 🔗 Related Files

| File | Description |
|------|-------------|
| `thoughts/shared/docs/2026-01-05-how-to-use-context-window-array.md` | How-to guide |
| `thoughts/shared/research/2026-01-04-context-window-array-architecture.md` | Architecture research |
| `thoughts/shared/plans/2026-01-04-tdd-context-window-array/` | TDD implementation plans |

---

## 📊 Design Principles

1. **Single Source of Truth**: All context lives in CentralContextStore
2. **Addressable**: Every entry has a unique ID for direct access
3. **Searchable**: Vector similarity enables semantic retrieval
4. **Bounded**: Implementation contexts limited to <200 entries
5. **Ephemeral**: TTL enables automatic cleanup
6. **Compressible**: Memory management via compression
7. **Separated**: Working (summaries) vs Implementation (content)

---

## 🏷️ Key Takeaways

| Aspect | Implementation |
|--------|----------------|
| Storage | Python dict with entry ID keys |
| Search | TF-IDF + cosine similarity (numpy) |
| Bounds | 200 entries max for impl context |
| Lifecycle | TTL-based expiration per turn |
| Memory | Compression removes content |
| Separation | Working=summaries, Impl=full content |
| Integration | CWAIntegration wraps for pipeline use |
