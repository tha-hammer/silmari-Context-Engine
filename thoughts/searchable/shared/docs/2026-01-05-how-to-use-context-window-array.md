---
date: 2026-01-05T04:50:00-05:00
researcher: Claude
git_commit: 845ac972dc4dc8318e52a768b1ef1bf932ba4320
branch: main
repository: silmari-Context-Engine
topic: "How to Use the Context Window Array Architecture"
tags: [how-to, context-window-array, context-management, llm-orchestration]
status: complete
last_updated: 2026-01-05
last_updated_by: Claude
---

# How to Use the Context Window Array Architecture

## Introduction

This guide walks you through using the Context Window Array Architecture to manage context for LLM orchestration. By the end, you will understand how to:

- Store and retrieve addressable context entries
- Search for relevant context using semantic similarity
- Build separate contexts for working (orchestrator) and implementation LLMs
- Batch tasks to respect entry limits

The architecture separates the **working LLM** (which sees only summaries) from **implementation LLMs** (which see full content, bounded to <200 entries).

## Prerequisites

Before starting, ensure you have:

- Python 3.12 or higher installed
- numpy installed (`pip install numpy`)
- pytest installed for running tests (`pip install pytest`)

No external API keys are required—this module is self-contained.

## Steps

### 1. Import the Core Components

```python
from context_window_array import (
    # Core models
    ContextEntry,
    EntryType,

    # Central store
    CentralContextStore,

    # Context builders (optional direct use)
    VectorSearchIndex,
    SearchResult,
    StoreSearchResult,

    # Batching
    TaskSpec,
    TaskBatch,
    TaskBatcher,
)

# These are imported separately as they're less common
from context_window_array.working_context import WorkingLLMContext
from context_window_array.implementation_context import ImplementationLLMContext
from context_window_array.batching import BatchExecutor, BatchResult
```

### 2. Create a Central Context Store

The `CentralContextStore` is the single source of truth for all context entries:

```python
store = CentralContextStore()
```

### 3. Add Context Entries

Create entries with unique IDs and add them to the store:

```python
# Add a file entry
file_entry = ContextEntry(
    id="ctx_001",
    entry_type=EntryType.FILE,
    source="src/auth.py",
    content="def authenticate(user, password): ...",
    summary="Authentication function that verifies user credentials",
)
store.add(file_entry)

# Add a command result entry
result_id = store.add_command_result(
    command="git status",
    result="On branch main\nnothing to commit",
    summary="Git status shows clean working tree",
    keep_command=False,  # Discard the command, keep only result
)

# Add a task entry with TTL (auto-expires after 5 turns)
task_entry = ContextEntry(
    id="ctx_task_001",
    entry_type=EntryType.TASK,
    source="orchestrator",
    content="Implement user login flow",
    summary="Login implementation task",
    ttl=5,  # Expires after 5 conversation turns
)
store.add(task_entry)
```

### 4. Query the Store

Retrieve entries by ID, type, or search:

```python
# Get by ID
entry = store.get("ctx_001")

# Get all entries of a type
files = store.get_by_type(EntryType.FILE)

# Search by semantic similarity
results = store.search(
    query="user authentication login",
    max_results=5,
    min_score=0.1,  # Minimum similarity threshold
)

for result in results:
    print(f"Found: {result.entry_id} (score: {result.score:.2f})")
    print(f"  Summary: {result.summary}")
```

### 5. Build Working LLM Context (Summaries Only)

The working LLM (orchestrator) sees only summaries to stay focused on coordination:

```python
working_ctx = WorkingLLMContext(store)

# Build context with all entries (summaries only)
context = working_ctx.build()
print(f"Total entries: {context.total_count}")
print(f"Estimated tokens: {context.summary_tokens}")

for entry_view in context.entries:
    # entry_view.content is always None
    print(f"  {entry_view.id}: {entry_view.summary}")

# Search from working LLM perspective
search_results = working_ctx.search("database connection")
for result in search_results:
    print(f"  Found {result.id} (score: {result.score:.2f})")
```

### 6. Build Implementation LLM Context (Full Content)

Implementation LLMs need full content but are bounded to <200 entries:

```python
impl_ctx = ImplementationLLMContext(store, max_entries=200)

# Check bounds before building
entry_ids = ["ctx_001", "ctx_002", "ctx_003"]
if impl_ctx.validate_bounds(entry_ids):
    context = impl_ctx.build(entry_ids)
    print(f"Entry count: {context.entry_count}")
    print(f"Total tokens: {context.total_tokens}")

    for entry in context.entries:
        # Full content available
        print(f"  {entry.id}: {entry.content[:100]}...")
```

### 7. Use Context Manager for Auto-Release

The `request()` context manager ensures entries are released even on exceptions:

```python
impl_ctx = ImplementationLLMContext(store)

with impl_ctx.request(["ctx_001", "ctx_002"]) as context:
    # Entries are marked as "in use"
    print(f"Working with {context.entry_count} entries")

    # Do your work here
    process_entries(context.entries)

# Entries automatically released here, even if exception occurred
```

### 8. Batch Tasks for Implementation LLMs

When you have many tasks, batch them to respect the <200 entry limit:

```python
# Define tasks with their required context
tasks = [
    TaskSpec(
        id="task_001",
        description="Implement login",
        required_entry_ids=["ctx_auth", "ctx_db", "ctx_session"],
        priority=1,
    ),
    TaskSpec(
        id="task_002",
        description="Add logout",
        required_entry_ids=["ctx_auth", "ctx_session"],  # Shares entries
        priority=2,
    ),
    TaskSpec(
        id="task_003",
        description="Fix database query",
        required_entry_ids=["ctx_db", "ctx_query"],
        priority=1,
    ),
]

# Create batches (shares entries when possible)
batcher = TaskBatcher(max_entries_per_batch=200)
batches = batcher.create_batches(tasks, sort_by_priority=True)

print(f"Created {len(batches)} batches")
for batch in batches:
    print(f"  {batch.batch_id}: {len(batch.tasks)} tasks, {batch.entry_count} entries")
```

### 9. Execute Task Batches

Use `BatchExecutor` to run batches with proper context lifecycle:

```python
def my_handler(context: ImplementationContext, tasks: list[TaskSpec]) -> dict:
    """Process tasks with the provided context."""
    results = {}
    for task in tasks:
        # Access full content from context.entries
        result = process_task(task, context.entries)
        results[task.id] = result
    return results

# Execute all batches
executor = BatchExecutor(store, max_entries=200)
batch_results = executor.execute_all(batches, my_handler, continue_on_error=True)

# Aggregate results
all_results = executor.get_all_task_results(batch_results)
for task_id, result in all_results.items():
    print(f"  {task_id}: {result}")
```

### 10. Manage Entry Lifecycle

Handle TTL expiration and compression:

```python
# Process a conversation turn (decrements TTLs, removes expired)
turn_stats = store.process_turn()
print(f"TTL decremented: {turn_stats['decremented']}")
print(f"Expired removed: {turn_stats['removed']}")

# Compress entries to save space (removes content, keeps summary)
store.compress("ctx_001")

# Compress multiple entries
compressed_count = store.compress_multiple(["ctx_002", "ctx_003"])

# Check for entries expiring soon
expiring = store.get_expiring_soon(threshold=2)
for entry in expiring:
    print(f"  {entry.id} expires in {entry.ttl} turns")
```

### 11. Verify Setup with Tests

Run the test suite to verify everything works:

```bash
# Run all tests
pytest context_window_array/tests/ -v

# Run specific module tests
pytest context_window_array/tests/test_models.py -v
pytest context_window_array/tests/test_store.py -v
pytest context_window_array/tests/test_search.py -v
pytest context_window_array/tests/test_working_context.py -v
pytest context_window_array/tests/test_implementation_context.py -v
pytest context_window_array/tests/test_batching.py -v

# Run with coverage
pytest context_window_array/tests/ --cov=context_window_array --cov-report=term-missing
```

## Common Patterns

### Pattern: Search Then Request

The working LLM searches, then implementation LLM processes:

```python
# Working LLM finds relevant entries
working = WorkingLLMContext(store)
search_results = working.search("authentication flow")

# Implementation LLM gets full content
impl = ImplementationLLMContext(store)
entry_ids = [r.id for r in search_results]

with impl.request(entry_ids) as context:
    # Full content available for implementation
    for entry in context.entries:
        print(f"{entry.source}: {entry.content}")
```

### Pattern: Command/Result Separation

Store command results while discarding the commands themselves:

```python
# Execute command and store result (command discarded)
result_id = store.add_command_result(
    command="find . -name '*.py' | head -20",
    result="./src/main.py\n./src/auth.py\n...",
    summary="Found 20 Python files in project",
    keep_command=False,  # Don't store the find command
)

# Later searches find the result, not the command
results = store.search("python files")
```

### Pattern: Context Compression for Long Conversations

Keep context manageable by compressing old entries:

```python
# Get uncompressed entries sorted by age
entries = store.get_uncompressed()
entries.sort(key=lambda e: e.created_at)

# Compress oldest entries
old_entries = entries[:len(entries) // 2]
for entry in old_entries:
    if entry.can_compress():
        entry.compress()
```

## Entry Types Reference

| Type | Description | Searchable | Typical TTL |
|------|-------------|------------|-------------|
| `FILE` | File content from codebase | Yes | None |
| `COMMAND` | Command invocation | No | Short |
| `COMMAND_RESULT` | Output from command | Yes | Medium |
| `TASK` | Task description | Yes | Until complete |
| `TASK_RESULT` | Task output | Yes | Medium |
| `SEARCH_RESULT` | Search/grep output | Yes | Short |
| `SUMMARY` | Compressed summary | Yes | None |
| `CONTEXT_REQUEST` | Request for more context | Yes | Short |

## Conclusion

You now know how to use the Context Window Array Architecture to:

- Store addressable context entries with unique IDs
- Search entries using semantic similarity (cosine similarity)
- Build separate contexts for working (summaries) and implementation (full content) LLMs
- Batch tasks to respect the <200 entry limit
- Manage entry lifecycle with TTL and compression

For implementation details, see:
- Models: `context_window_array/models.py`
- Store: `context_window_array/store.py`
- Search: `context_window_array/search_index.py`
- Contexts: `context_window_array/working_context.py`, `implementation_context.py`
- Batching: `context_window_array/batching.py`

For the design rationale, see the research document: `thoughts/searchable/shared/research/2026-01-04-context-window-array-architecture.md`
