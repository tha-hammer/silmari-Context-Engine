"""Task batching for implementation LLM context.

Groups tasks into batches that fit within the <200 entry limit
for implementation LLM contexts.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from context_window_array.implementation_context import (
    ImplementationContext,
    ImplementationLLMContext,
)
from context_window_array.store import CentralContextStore


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
