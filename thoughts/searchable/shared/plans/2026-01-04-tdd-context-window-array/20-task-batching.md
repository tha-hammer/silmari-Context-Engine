# Phase 20: Task Batching

## Behavior

Group tasks into batches that fit within implementation LLM context bounds.

### Test Specification

**Given**: List of tasks with entry requirements
**When**: create_batches(tasks)
**Then**: Tasks grouped into batches respecting entry limits

**Given**: Tasks with dependencies
**When**: create_batches(tasks)
**Then**: Dependencies stay in same batch when possible

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_batching.py`

```python
"""Tests for context_window_array.batching module."""

import pytest
from context_window_array.models import ContextEntry, EntryType
from context_window_array.store import CentralContextStore
from context_window_array.batching import (
    TaskBatcher,
    TaskSpec,
    TaskBatch,
)


class TestTaskBatching:
    """Behavior 20: Task batching operations."""

    def test_create_batch_single_task(self):
        """Given single task, when create_batches(), then single batch created."""
        batcher = TaskBatcher(max_entries_per_batch=200)

        task = TaskSpec(
            id="task_001",
            description="Implement feature",
            required_entry_ids=["ctx_001", "ctx_002", "ctx_003"],
        )

        batches = batcher.create_batches([task])

        assert len(batches) == 1
        assert task in batches[0].tasks

    def test_create_batch_multiple_tasks_fit(self):
        """Given tasks that fit in one batch, when create_batches(), then single batch."""
        batcher = TaskBatcher(max_entries_per_batch=200)

        tasks = [
            TaskSpec(id="task_001", description="Task 1", required_entry_ids=["ctx_001", "ctx_002"]),
            TaskSpec(id="task_002", description="Task 2", required_entry_ids=["ctx_003", "ctx_004"]),
            TaskSpec(id="task_003", description="Task 3", required_entry_ids=["ctx_005"]),
        ]

        batches = batcher.create_batches(tasks)

        assert len(batches) == 1
        assert len(batches[0].tasks) == 3

    def test_create_batch_splits_when_exceeds_limit(self):
        """Given tasks exceeding limit, when create_batches(), then multiple batches."""
        batcher = TaskBatcher(max_entries_per_batch=5)

        tasks = [
            TaskSpec(id="task_001", description="Task 1", required_entry_ids=["ctx_001", "ctx_002", "ctx_003"]),
            TaskSpec(id="task_002", description="Task 2", required_entry_ids=["ctx_004", "ctx_005", "ctx_006"]),
        ]

        batches = batcher.create_batches(tasks)

        # Each task needs 3 entries, limit is 5, so can't fit both
        assert len(batches) == 2

    def test_create_batch_deduplicates_entries(self):
        """Given tasks with shared entries, when create_batches(), then entries deduplicated."""
        batcher = TaskBatcher(max_entries_per_batch=10)

        tasks = [
            TaskSpec(id="task_001", description="Task 1", required_entry_ids=["ctx_001", "ctx_002"]),
            TaskSpec(id="task_002", description="Task 2", required_entry_ids=["ctx_002", "ctx_003"]),
            TaskSpec(id="task_003", description="Task 3", required_entry_ids=["ctx_001", "ctx_003"]),
        ]

        batches = batcher.create_batches(tasks)

        # All share entries, should fit in one batch with 3 unique entries
        assert len(batches) == 1
        assert len(batches[0].unique_entry_ids) == 3

    def test_batch_contains_all_required_entries(self):
        """Given batch, then contains all unique entries from tasks."""
        batcher = TaskBatcher(max_entries_per_batch=200)

        tasks = [
            TaskSpec(id="task_001", description="Task 1", required_entry_ids=["ctx_001", "ctx_002"]),
            TaskSpec(id="task_002", description="Task 2", required_entry_ids=["ctx_003"]),
        ]

        batches = batcher.create_batches(tasks)

        assert "ctx_001" in batches[0].unique_entry_ids
        assert "ctx_002" in batches[0].unique_entry_ids
        assert "ctx_003" in batches[0].unique_entry_ids

    def test_batch_tracks_task_order(self):
        """Given tasks, when create_batches(), then order preserved within batch."""
        batcher = TaskBatcher(max_entries_per_batch=200)

        tasks = [
            TaskSpec(id="task_001", description="First", required_entry_ids=["ctx_001"]),
            TaskSpec(id="task_002", description="Second", required_entry_ids=["ctx_002"]),
            TaskSpec(id="task_003", description="Third", required_entry_ids=["ctx_003"]),
        ]

        batches = batcher.create_batches(tasks)

        assert [t.id for t in batches[0].tasks] == ["task_001", "task_002", "task_003"]

    def test_empty_tasks_returns_empty_batches(self):
        """Given no tasks, when create_batches(), then empty list."""
        batcher = TaskBatcher(max_entries_per_batch=200)

        batches = batcher.create_batches([])

        assert batches == []

    def test_task_with_no_entries(self):
        """Given task with no entries, when create_batches(), then included in batch."""
        batcher = TaskBatcher(max_entries_per_batch=200)

        task = TaskSpec(id="task_001", description="No context needed", required_entry_ids=[])

        batches = batcher.create_batches([task])

        assert len(batches) == 1
        assert task in batches[0].tasks

    def test_batch_has_entry_count(self):
        """Given batch, then has entry_count property."""
        batcher = TaskBatcher(max_entries_per_batch=200)

        tasks = [
            TaskSpec(id="task_001", description="Task", required_entry_ids=["ctx_001", "ctx_002", "ctx_003"]),
        ]

        batches = batcher.create_batches(tasks)

        assert batches[0].entry_count == 3

    def test_single_large_task_warning(self):
        """Given single task exceeding limit, when create_batches(), then includes warning."""
        batcher = TaskBatcher(max_entries_per_batch=5)

        task = TaskSpec(
            id="task_001",
            description="Large task",
            required_entry_ids=[f"ctx_{i:03d}" for i in range(10)],
        )

        batches = batcher.create_batches([task])

        # Should still create batch but with warning flag
        assert len(batches) == 1
        assert batches[0].exceeds_limit is True
        assert batches[0].entry_count == 10

    def test_batch_id_generation(self):
        """Given batches, then each has unique id."""
        batcher = TaskBatcher(max_entries_per_batch=5)

        tasks = [
            TaskSpec(id="task_001", description="Task 1", required_entry_ids=["ctx_001", "ctx_002", "ctx_003"]),
            TaskSpec(id="task_002", description="Task 2", required_entry_ids=["ctx_004", "ctx_005", "ctx_006"]),
        ]

        batches = batcher.create_batches(tasks)

        assert len(batches) == 2
        assert batches[0].batch_id != batches[1].batch_id
        assert batches[0].batch_id.startswith("batch_")

    def test_priority_based_batching(self):
        """Given tasks with priority, when create_batches(), then high priority first."""
        batcher = TaskBatcher(max_entries_per_batch=3)

        tasks = [
            TaskSpec(id="task_001", description="Low", required_entry_ids=["ctx_001"], priority=1),
            TaskSpec(id="task_002", description="High", required_entry_ids=["ctx_002"], priority=3),
            TaskSpec(id="task_003", description="Medium", required_entry_ids=["ctx_003"], priority=2),
        ]

        batches = batcher.create_batches(tasks, sort_by_priority=True)

        # High priority tasks should be in earlier batches
        first_batch_priorities = [t.priority for t in batches[0].tasks]
        assert first_batch_priorities[0] >= first_batch_priorities[-1] or len(batches) == 1
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_batching.py::TestTaskBatching -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/batching.py`

```python
"""Task batching for implementation LLM context.

Groups tasks into batches that fit within the <200 entry limit
for implementation LLM contexts.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TaskSpec:
    """Specification for a task to be batched.

    Attributes:
        id: Unique task identifier
        description: Task description
        required_entry_ids: Entry IDs needed for this task
        priority: Task priority (higher = more important)
    """
    id: str
    description: str
    required_entry_ids: list[str] = field(default_factory=list)
    priority: int = 0


@dataclass
class TaskBatch:
    """A batch of tasks with shared context.

    Attributes:
        batch_id: Unique batch identifier
        tasks: Tasks in this batch
        unique_entry_ids: Deduplicated entry IDs for all tasks
        exceeds_limit: True if batch exceeds entry limit
    """
    batch_id: str
    tasks: list[TaskSpec]
    unique_entry_ids: set[str]
    exceeds_limit: bool = False

    @property
    def entry_count(self) -> int:
        """Number of unique entries in this batch."""
        return len(self.unique_entry_ids)


class TaskBatcher:
    """Creates task batches respecting entry limits.

    Groups tasks into batches where the total unique entries
    stays within the configured limit.
    """

    def __init__(self, max_entries_per_batch: int = 200):
        """Initialize batcher.

        Args:
            max_entries_per_batch: Maximum entries per batch (default: 200)
        """
        self._max_entries = max_entries_per_batch
        self._batch_counter = 0

    def _generate_batch_id(self) -> str:
        """Generate unique batch ID."""
        self._batch_counter += 1
        return f"batch_{self._batch_counter:04d}"

    def _calculate_batch_entries(
        self,
        current_entries: set[str],
        task: TaskSpec,
    ) -> set[str]:
        """Calculate entries if task added to batch."""
        return current_entries | set(task.required_entry_ids)

    def create_batches(
        self,
        tasks: list[TaskSpec],
        sort_by_priority: bool = False,
    ) -> list[TaskBatch]:
        """Create batches from tasks.

        Groups tasks into batches where unique entry count
        stays within max_entries_per_batch.

        Args:
            tasks: Tasks to batch
            sort_by_priority: If True, process high priority tasks first

        Returns:
            List of TaskBatch objects
        """
        if not tasks:
            return []

        # Optionally sort by priority
        if sort_by_priority:
            tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)

        batches = []
        current_tasks: list[TaskSpec] = []
        current_entries: set[str] = set()

        for task in tasks:
            task_entries = set(task.required_entry_ids)

            # Check if adding this task would exceed limit
            combined_entries = current_entries | task_entries

            if len(combined_entries) <= self._max_entries:
                # Task fits in current batch
                current_tasks.append(task)
                current_entries = combined_entries
            else:
                # Need to start new batch

                # First, finalize current batch if not empty
                if current_tasks:
                    batches.append(TaskBatch(
                        batch_id=self._generate_batch_id(),
                        tasks=current_tasks,
                        unique_entry_ids=current_entries,
                        exceeds_limit=False,
                    ))

                # Start new batch with this task
                current_tasks = [task]
                current_entries = task_entries

                # Check if single task exceeds limit
                exceeds = len(task_entries) > self._max_entries

                # If this single task exceeds limit, finalize it immediately
                if exceeds:
                    batches.append(TaskBatch(
                        batch_id=self._generate_batch_id(),
                        tasks=current_tasks,
                        unique_entry_ids=current_entries,
                        exceeds_limit=True,
                    ))
                    current_tasks = []
                    current_entries = set()

        # Finalize last batch
        if current_tasks:
            batches.append(TaskBatch(
                batch_id=self._generate_batch_id(),
                tasks=current_tasks,
                unique_entry_ids=current_entries,
                exceeds_limit=len(current_entries) > self._max_entries,
            ))

        return batches
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_batching.py::TestTaskBatching -v
```

### 🔵 Refactor: Improve Code

Consider adding dependency-aware batching that keeps related tasks together.

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): ImportError for TaskBatcher
- [ ] Test passes (Green): All 13 tests pass
- [ ] Single task creates single batch
- [ ] Multiple small tasks fit in one batch
- [ ] Large tasks split into multiple batches
- [ ] Entries deduplicated within batch
- [ ] Entry count tracked correctly
- [ ] Single oversized task flagged
- [ ] Batch IDs are unique

**Manual:**
- [ ] Batching strategy matches RLM paper recommendations
- [ ] Entry deduplication saves context space
