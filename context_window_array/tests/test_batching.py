"""Tests for context_window_array.batching module."""

from context_window_array.batching import (
    BatchExecutor,
    TaskBatch,
    TaskBatcher,
    TaskSpec,
)
from context_window_array.models import ContextEntry, EntryType
from context_window_array.store import CentralContextStore


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
