# Phase 21: Batch Execution

## Behavior

Execute task batches with proper context management and result collection.

## Context Lifecycle Integration

BatchExecutor uses ImplementationLLMContext's context manager for proper context lifecycle management:

```python
def execute_batch(self, batch: TaskBatch, handler: BatchHandler) -> BatchResult:
    """Execute batch with automatic context management.

    Uses the request() context manager from Phase 19 to ensure:
    - Context is acquired before handler execution
    - Context is ALWAYS released after handler completes (success or failure)
    - No context leaks even on exceptions
    """
    entry_ids = list(batch.unique_entry_ids)

    # Context manager handles request + release lifecycle
    with self.impl_context.request(entry_ids) as ctx:
        # Handler receives full content context
        task_results = handler(ctx, batch.tasks)
        return BatchResult(
            batch_id=batch.batch_id,
            task_results=task_results,
            entry_count=ctx.entry_count,
            total_tokens=ctx.total_tokens,
        )
    # Context automatically released here (even on exception)
```

**Key Integration Points**:
1. `impl_context.request()` acquires entries and marks them in_use
2. Handler receives `ImplementationContext` with full content
3. On exit (success or exception), entries are automatically released
4. `impl_context.is_in_use()` returns False after batch completes

This pattern ensures the RLM paper workflow:
- Working LLM searches → selects entries
- Implementation LLM requests context → processes tasks → releases context
- Context returned to pool for next batch

### Test Specification

**Given**: Task batch
**When**: execute_batch(batch, handler)
**Then**: Handler called with implementation context, results collected

**Given**: Multiple batches
**When**: execute_all(batches, handler)
**Then**: All batches processed, results aggregated

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_batching.py`

```python
from context_window_array.batching import BatchExecutor, BatchResult


class TestBatchExecution:
    """Behavior 21: Batch execution operations."""

    def test_execute_batch_calls_handler(self):
        """Given batch, when execute_batch(handler), then handler called."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b"))

        batch = TaskBatch(
            batch_id="batch_001",
            tasks=[TaskSpec(id="task_001", description="Test", required_entry_ids=["ctx_001", "ctx_002"])],
            unique_entry_ids={"ctx_001", "ctx_002"},
        )

        handler_calls = []

        def handler(context, tasks):
            handler_calls.append((context, tasks))
            return {"task_001": "completed"}

        executor = BatchExecutor(store)
        result = executor.execute_batch(batch, handler)

        assert len(handler_calls) == 1
        assert result.batch_id == "batch_001"

    def test_execute_batch_provides_context(self):
        """Given batch, when execute_batch(handler), then handler receives context."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="full content here",
            summary="summary",
        ))

        batch = TaskBatch(
            batch_id="batch_001",
            tasks=[TaskSpec(id="task_001", description="Test", required_entry_ids=["ctx_001"])],
            unique_entry_ids={"ctx_001"},
        )

        received_context = None

        def handler(context, tasks):
            nonlocal received_context
            received_context = context
            return {}

        executor = BatchExecutor(store)
        executor.execute_batch(batch, handler)

        # Context should have full content
        assert received_context is not None
        assert len(received_context.entries) == 1
        assert received_context.entries[0].content == "full content here"

    def test_execute_batch_collects_results(self):
        """Given handler returning results, when execute_batch(), then results collected."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))

        batch = TaskBatch(
            batch_id="batch_001",
            tasks=[
                TaskSpec(id="task_001", description="Task 1", required_entry_ids=["ctx_001"]),
                TaskSpec(id="task_002", description="Task 2", required_entry_ids=["ctx_001"]),
            ],
            unique_entry_ids={"ctx_001"},
        )

        def handler(context, tasks):
            return {
                "task_001": {"status": "success", "output": "result 1"},
                "task_002": {"status": "success", "output": "result 2"},
            }

        executor = BatchExecutor(store)
        result = executor.execute_batch(batch, handler)

        assert result.task_results["task_001"]["status"] == "success"
        assert result.task_results["task_002"]["status"] == "success"

    def test_execute_batch_releases_context(self):
        """Given batch execution, when complete, then context released."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))

        batch = TaskBatch(
            batch_id="batch_001",
            tasks=[TaskSpec(id="task_001", description="Test", required_entry_ids=["ctx_001"])],
            unique_entry_ids={"ctx_001"},
        )

        def handler(context, tasks):
            return {}

        executor = BatchExecutor(store)
        executor.execute_batch(batch, handler)

        # Context should be released
        assert not executor.impl_context.is_in_use("ctx_001")

    def test_execute_batch_handles_error(self):
        """Given handler raises error, when execute_batch(), then error captured."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))

        batch = TaskBatch(
            batch_id="batch_001",
            tasks=[TaskSpec(id="task_001", description="Test", required_entry_ids=["ctx_001"])],
            unique_entry_ids={"ctx_001"},
        )

        def handler(context, tasks):
            raise ValueError("Handler failed")

        executor = BatchExecutor(store)
        result = executor.execute_batch(batch, handler)

        assert result.success is False
        assert result.error is not None
        assert "Handler failed" in str(result.error)

    def test_execute_batch_releases_context_on_error(self):
        """Given handler error, when execute_batch(), then context still released."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))

        batch = TaskBatch(
            batch_id="batch_001",
            tasks=[TaskSpec(id="task_001", description="Test", required_entry_ids=["ctx_001"])],
            unique_entry_ids={"ctx_001"},
        )

        def handler(context, tasks):
            raise ValueError("Handler failed")

        executor = BatchExecutor(store)
        executor.execute_batch(batch, handler)

        # Context should still be released despite error
        assert not executor.impl_context.is_in_use("ctx_001")

    def test_execute_all_batches(self):
        """Given multiple batches, when execute_all(), then all processed."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b"))

        batches = [
            TaskBatch(
                batch_id="batch_001",
                tasks=[TaskSpec(id="task_001", description="Task 1", required_entry_ids=["ctx_001"])],
                unique_entry_ids={"ctx_001"},
            ),
            TaskBatch(
                batch_id="batch_002",
                tasks=[TaskSpec(id="task_002", description="Task 2", required_entry_ids=["ctx_002"])],
                unique_entry_ids={"ctx_002"},
            ),
        ]

        def handler(context, tasks):
            return {t.id: "done" for t in tasks}

        executor = BatchExecutor(store)
        results = executor.execute_all(batches, handler)

        assert len(results) == 2
        assert results[0].batch_id == "batch_001"
        assert results[1].batch_id == "batch_002"

    def test_execute_all_aggregates_results(self):
        """Given multiple batches, when execute_all(), then results aggregated."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))

        batches = [
            TaskBatch(
                batch_id="batch_001",
                tasks=[TaskSpec(id="task_001", description="T1", required_entry_ids=["ctx_001"])],
                unique_entry_ids={"ctx_001"},
            ),
            TaskBatch(
                batch_id="batch_002",
                tasks=[TaskSpec(id="task_002", description="T2", required_entry_ids=["ctx_001"])],
                unique_entry_ids={"ctx_001"},
            ),
        ]

        def handler(context, tasks):
            return {t.id: {"value": t.id} for t in tasks}

        executor = BatchExecutor(store)
        results = executor.execute_all(batches, handler)

        all_task_results = executor.get_all_task_results(results)
        assert "task_001" in all_task_results
        assert "task_002" in all_task_results

    def test_execute_all_continues_on_error(self):
        """Given batch error, when execute_all(), then continues with remaining."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b"))

        batches = [
            TaskBatch(
                batch_id="batch_001",
                tasks=[TaskSpec(id="task_001", description="Will fail", required_entry_ids=["ctx_001"])],
                unique_entry_ids={"ctx_001"},
            ),
            TaskBatch(
                batch_id="batch_002",
                tasks=[TaskSpec(id="task_002", description="Will succeed", required_entry_ids=["ctx_002"])],
                unique_entry_ids={"ctx_002"},
            ),
        ]

        call_count = [0]

        def handler(context, tasks):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("First batch fails")
            return {t.id: "done" for t in tasks}

        executor = BatchExecutor(store)
        results = executor.execute_all(batches, handler, continue_on_error=True)

        assert len(results) == 2
        assert results[0].success is False
        assert results[1].success is True

    def test_execute_all_stops_on_error_if_requested(self):
        """Given batch error and continue_on_error=False, when execute_all(), then stops."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b"))

        batches = [
            TaskBatch(
                batch_id="batch_001",
                tasks=[TaskSpec(id="task_001", description="Will fail", required_entry_ids=["ctx_001"])],
                unique_entry_ids={"ctx_001"},
            ),
            TaskBatch(
                batch_id="batch_002",
                tasks=[TaskSpec(id="task_002", description="Won't run", required_entry_ids=["ctx_002"])],
                unique_entry_ids={"ctx_002"},
            ),
        ]

        def handler(context, tasks):
            raise ValueError("Batch fails")

        executor = BatchExecutor(store)
        results = executor.execute_all(batches, handler, continue_on_error=False)

        # Should stop after first failure
        assert len(results) == 1
        assert results[0].success is False

    def test_batch_result_has_timing(self):
        """Given batch execution, then result includes timing info."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))

        batch = TaskBatch(
            batch_id="batch_001",
            tasks=[TaskSpec(id="task_001", description="Test", required_entry_ids=["ctx_001"])],
            unique_entry_ids={"ctx_001"},
        )

        def handler(context, tasks):
            return {}

        executor = BatchExecutor(store)
        result = executor.execute_batch(batch, handler)

        assert hasattr(result, 'duration_ms')
        assert result.duration_ms >= 0

    def test_batch_result_has_entry_stats(self):
        """Given batch execution, then result includes entry statistics."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a" * 100, summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b" * 200, summary="b"))

        batch = TaskBatch(
            batch_id="batch_001",
            tasks=[TaskSpec(id="task_001", description="Test", required_entry_ids=["ctx_001", "ctx_002"])],
            unique_entry_ids={"ctx_001", "ctx_002"},
        )

        def handler(context, tasks):
            return {}

        executor = BatchExecutor(store)
        result = executor.execute_batch(batch, handler)

        assert result.entry_count == 2
        assert result.total_tokens > 0
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_batching.py::TestBatchExecution -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/batching.py` (add BatchExecutor)

```python
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from context_window_array.store import CentralContextStore
from context_window_array.implementation_context import (
    ImplementationLLMContext,
    ImplementationContext,
)


@dataclass
class BatchResult:
    """Result from executing a task batch.

    Attributes:
        batch_id: ID of the executed batch
        task_results: Results keyed by task ID
        success: True if batch executed without error
        error: Exception if execution failed
        duration_ms: Execution time in milliseconds
        entry_count: Number of entries in context
        total_tokens: Estimated tokens used
    """
    batch_id: str
    task_results: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[Exception] = None
    duration_ms: float = 0.0
    entry_count: int = 0
    total_tokens: int = 0


# Type alias for batch handler function
BatchHandler = Callable[[ImplementationContext, list[TaskSpec]], dict[str, Any]]


class BatchExecutor:
    """Executes task batches with proper context management.

    Handles context acquisition, handler invocation, result collection,
    and context release.
    """

    def __init__(self, store: CentralContextStore, max_entries: int = 200):
        """Initialize executor.

        Args:
            store: Central context store
            max_entries: Maximum entries per context
        """
        self._store = store
        self.impl_context = ImplementationLLMContext(store, max_entries=max_entries)

    def execute_batch(
        self,
        batch: TaskBatch,
        handler: BatchHandler,
    ) -> BatchResult:
        """Execute a single batch.

        Acquires context, calls handler, collects results, releases context.

        Args:
            batch: Batch to execute
            handler: Function to process tasks with context

        Returns:
            BatchResult with execution results
        """
        start_time = time.perf_counter()

        # Prepare result
        result = BatchResult(
            batch_id=batch.batch_id,
            entry_count=batch.entry_count,
        )

        try:
            # Request context for batch entries
            with self.impl_context.request(list(batch.unique_entry_ids)) as context:
                result.total_tokens = context.total_tokens

                # Call handler with context and tasks
                task_results = handler(context, batch.tasks)
                result.task_results = task_results
                result.success = True

        except Exception as e:
            result.success = False
            result.error = e

        # Record timing
        result.duration_ms = (time.perf_counter() - start_time) * 1000

        return result

    def execute_all(
        self,
        batches: list[TaskBatch],
        handler: BatchHandler,
        continue_on_error: bool = True,
    ) -> list[BatchResult]:
        """Execute all batches.

        Args:
            batches: Batches to execute
            handler: Function to process tasks
            continue_on_error: If True, continue after batch errors

        Returns:
            List of BatchResult for each batch
        """
        results = []

        for batch in batches:
            result = self.execute_batch(batch, handler)
            results.append(result)

            if not result.success and not continue_on_error:
                break

        return results

    def get_all_task_results(
        self,
        batch_results: list[BatchResult],
    ) -> dict[str, Any]:
        """Aggregate task results from all batches.

        Args:
            batch_results: Results from execute_all

        Returns:
            Dictionary mapping task IDs to their results
        """
        all_results = {}
        for batch_result in batch_results:
            all_results.update(batch_result.task_results)
        return all_results
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_batching.py::TestBatchExecution -v
```

### 🔵 Refactor: Improve Code

Consider adding:
- Async batch execution
- Progress callbacks
- Batch retry logic

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): ImportError for BatchExecutor
- [ ] Test passes (Green): All 13 tests pass
- [ ] `execute_batch()` calls handler with context
- [ ] `execute_batch()` collects results
- [ ] `execute_batch()` releases context
- [ ] `execute_batch()` handles errors gracefully
- [ ] `execute_all()` processes multiple batches
- [ ] `execute_all()` respects continue_on_error
- [ ] Results include timing and entry stats

**Manual:**
- [ ] Batch execution matches RLM paper workflow
- [ ] Error handling is robust
- [ ] Context properly released in all cases
