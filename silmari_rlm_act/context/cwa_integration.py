"""Context Window Array integration for silmari-rlm-act pipeline.

Provides a high-level interface for managing context entries throughout
the pipeline phases, including research, requirements, plans, and
command results.
"""

from contextlib import contextmanager
from typing import Generator, Optional

from context_window_array import (
    CentralContextStore,
    ContextEntry,
    EntryType,
    StoreSearchResult,
    TaskBatch,
    TaskBatcher,
    TaskSpec,
)
from context_window_array.batching import BatchExecutor, BatchHandler, BatchResult
from context_window_array.implementation_context import (
    ImplementationContext,
    ImplementationLLMContext,
)
from context_window_array.working_context import WorkingContext, WorkingLLMContext


class CWAIntegration:
    """Manages Context Window Array for pipeline phases.

    Provides methods for:
    - Storing research, requirements, plans, and command results
    - Building working LLM context (summaries only)
    - Building implementation LLM context (full content, bounded)
    - Searching for relevant context
    - TTL management and compression
    - Task batching and execution

    Example:
        >>> cwa = CWAIntegration()
        >>> research_id = cwa.store_research("doc.md", "content", "summary")
        >>> context = cwa.build_working_context()
        >>> with cwa.request_entries([research_id]) as impl_ctx:
        ...     # Use full content
        ...     pass
    """

    DEFAULT_REQUIREMENT_TTL = 20  # Turns until requirement expires

    def __init__(self, max_impl_entries: int = 200):
        """Initialize CWA integration.

        Args:
            max_impl_entries: Maximum entries for implementation context
        """
        self._store = CentralContextStore()
        self._working_ctx = WorkingLLMContext(self._store)
        self._impl_ctx = ImplementationLLMContext(self._store, max_entries=max_impl_entries)
        self._entry_counter = 0
        self._max_impl_entries = max_impl_entries
        self._batcher = TaskBatcher(max_entries_per_batch=max_impl_entries)
        self._executor = BatchExecutor(self._store, max_entries=max_impl_entries)

    @property
    def store(self) -> CentralContextStore:
        """Get the central context store."""
        return self._store

    @property
    def working_ctx(self) -> WorkingLLMContext:
        """Get working LLM context (summaries only)."""
        return self._working_ctx

    @property
    def impl_ctx(self) -> ImplementationLLMContext:
        """Get implementation LLM context (full content)."""
        return self._impl_ctx

    def _next_id(self, prefix: str = "ctx") -> str:
        """Generate next unique entry ID."""
        self._entry_counter += 1
        return f"{prefix}_{self._entry_counter:04d}"

    # =========================================================================
    # Behavior 2: Store Research Entry
    # =========================================================================

    def store_research(
        self,
        path: str,
        content: str,
        summary: str,
    ) -> str:
        """Store research document as FILE entry.

        Args:
            path: Path to research document
            content: Full document content
            summary: Brief summary for working LLM

        Returns:
            Entry ID
        """
        entry_id = self._next_id("research")
        entry = ContextEntry(
            id=entry_id,
            entry_type=EntryType.FILE,
            source=path,
            content=content,
            summary=summary,
        )
        self._store.add(entry)
        return entry_id

    # =========================================================================
    # Behavior 3: Store Requirement Entry
    # =========================================================================

    def store_requirement(
        self,
        req_id: str,
        description: str,
        summary: str,
        ttl: Optional[int] = None,
    ) -> str:
        """Store requirement as TASK entry.

        Args:
            req_id: Requirement ID from decomposition
            description: Full requirement description
            summary: Brief summary
            ttl: Time-to-live in turns (default: 20)

        Returns:
            Entry ID
        """
        entry_id = self._next_id("req")
        entry = ContextEntry(
            id=entry_id,
            entry_type=EntryType.TASK,
            source=f"requirement:{req_id}",
            content=description,
            summary=summary,
            ttl=ttl if ttl is not None else self.DEFAULT_REQUIREMENT_TTL,
        )
        self._store.add(entry)
        return entry_id

    # =========================================================================
    # Behavior 4: Store Plan Entry
    # =========================================================================

    def store_plan(
        self,
        path: str,
        content: str,
        summary: str,
    ) -> str:
        """Store TDD plan document as FILE entry.

        Args:
            path: Path to plan document
            content: Full plan content
            summary: Brief summary

        Returns:
            Entry ID
        """
        entry_id = self._next_id("plan")
        entry = ContextEntry(
            id=entry_id,
            entry_type=EntryType.FILE,
            source=path,
            content=content,
            summary=summary,
        )
        self._store.add(entry)
        return entry_id

    # =========================================================================
    # Behavior 5: Search Context
    # =========================================================================

    def search(
        self,
        query: str,
        max_results: int = 10,
        min_score: float = 0.1,
    ) -> list[StoreSearchResult]:
        """Search for relevant context entries.

        Args:
            query: Search query
            max_results: Maximum results to return
            min_score: Minimum similarity score

        Returns:
            List of search results with scores
        """
        return self._store.search(
            query=query,
            max_results=max_results,
            min_score=min_score,
        )

    # =========================================================================
    # Behavior 6: Build Working LLM Context
    # =========================================================================

    def build_working_context(
        self,
        entry_types: Optional[list[EntryType]] = None,
    ) -> WorkingContext:
        """Build context for working LLM (summaries only).

        Args:
            entry_types: Optional filter by entry types

        Returns:
            WorkingContext with all entries as summaries
        """
        return self._working_ctx.build(entry_types=entry_types)

    # =========================================================================
    # Behavior 7: Build Implementation Context
    # =========================================================================

    def build_impl_context(self, entry_ids: list[str]) -> ImplementationContext:
        """Build context for implementation LLM (full content).

        Args:
            entry_ids: List of entry IDs to include

        Returns:
            ImplementationContext with full content

        Raises:
            ValueError: If entry count exceeds max_entries
        """
        if not self._impl_ctx.validate_bounds(entry_ids):
            raise ValueError(
                f"Entry count {len(entry_ids)} exceeds max "
                f"{self._max_impl_entries}"
            )
        return self._impl_ctx.build(entry_ids)

    def validate_impl_bounds(self, entry_ids: list[str]) -> bool:
        """Check if entry IDs fit within implementation limit.

        Args:
            entry_ids: Entry IDs to check

        Returns:
            True if within bounds
        """
        return self._impl_ctx.validate_bounds(entry_ids)

    # =========================================================================
    # Behavior 8: Context Manager for Entries
    # =========================================================================

    @contextmanager
    def request_entries(
        self,
        entry_ids: list[str],
    ) -> Generator[ImplementationContext, None, None]:
        """Context manager for implementation LLM entries.

        Ensures entries are released even on exceptions.

        Args:
            entry_ids: Entry IDs to request

        Yields:
            ImplementationContext with full content
        """
        with self._impl_ctx.request(entry_ids) as context:
            yield context

    # =========================================================================
    # Behavior 9: Process Turn (TTL Management)
    # =========================================================================

    def process_turn(self) -> dict[str, int]:
        """Process a conversation turn: decrement TTLs and cleanup expired.

        Returns:
            Dictionary with 'decremented' and 'removed' counts
        """
        return self._store.process_turn()

    # =========================================================================
    # Behavior 10: Compress Old Entries
    # =========================================================================

    def compress_entries(self, entry_ids: list[str]) -> int:
        """Compress entries by removing content and retaining summary.

        Args:
            entry_ids: Entry IDs to compress

        Returns:
            Number of entries compressed
        """
        return self._store.compress_multiple(entry_ids)

    # =========================================================================
    # Behavior 11: Get Expiring Soon
    # =========================================================================

    def get_expiring_soon(self, threshold: int = 2) -> list[ContextEntry]:
        """Get entries that will expire soon.

        Args:
            threshold: TTL threshold (entries with TTL <= threshold)

        Returns:
            List of entries expiring soon
        """
        return self._store.get_expiring_soon(threshold=threshold)

    # =========================================================================
    # Behavior 12: Store Command Result
    # =========================================================================

    def store_command_result(
        self,
        command: str,
        result: str,
        summary: str,
        ttl: Optional[int] = None,
    ) -> str:
        """Store command execution result.

        Commands are discarded, only results are retained.

        Args:
            command: The command that was executed
            result: The output/result of the command
            summary: Summary of the result
            ttl: Optional time-to-live

        Returns:
            Entry ID of the result
        """
        return self._store.add_command_result(
            command=command,
            result=result,
            summary=summary,
            keep_command=False,  # Discard commands, keep results
            ttl=ttl,
        )

    # =========================================================================
    # Behavior 13: Task Batching
    # =========================================================================

    def create_batches(
        self,
        tasks: list[TaskSpec],
        max_entries: Optional[int] = None,
        sort_by_priority: bool = False,
    ) -> list[TaskBatch]:
        """Create task batches respecting entry limits.

        Args:
            tasks: Tasks to batch
            max_entries: Maximum entries per batch (default: impl_ctx max)
            sort_by_priority: If True, process high priority tasks first

        Returns:
            List of TaskBatch objects
        """
        if max_entries is not None and max_entries != self._batcher._max_entries:
            # Create a new batcher with custom limit
            batcher = TaskBatcher(max_entries_per_batch=max_entries)
            return batcher.create_batches(tasks, sort_by_priority=sort_by_priority)

        return self._batcher.create_batches(tasks, sort_by_priority=sort_by_priority)

    # =========================================================================
    # Behavior 14: Execute Batch
    # =========================================================================

    def execute_batch(
        self,
        batch: TaskBatch,
        handler: BatchHandler,
    ) -> BatchResult:
        """Execute a single batch with proper context management.

        Args:
            batch: Batch to execute
            handler: Function to process tasks with context

        Returns:
            BatchResult with execution results
        """
        return self._executor.execute_batch(batch, handler)

    def execute_all_batches(
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
        return self._executor.execute_all(batches, handler, continue_on_error)

    # =========================================================================
    # Behavior 15: Get Entries by Type
    # =========================================================================

    def get_by_type(self, entry_type: EntryType) -> list[ContextEntry]:
        """Get all entries of a specific type.

        Args:
            entry_type: Type to filter by

        Returns:
            List of entries matching the type
        """
        return self._store.get_by_type(entry_type)

    # =========================================================================
    # Additional Utility Methods
    # =========================================================================

    def count(self) -> int:
        """Get total number of entries in store."""
        return len(self._store)

    def get_entry(self, entry_id: str) -> Optional[ContextEntry]:
        """Get an entry by ID.

        Args:
            entry_id: Entry ID to retrieve

        Returns:
            ContextEntry if found, None otherwise
        """
        return self._store.get(entry_id)

    def remove_entry(self, entry_id: str) -> bool:
        """Remove an entry by ID.

        Args:
            entry_id: Entry ID to remove

        Returns:
            True if removed, False if not found
        """
        result = self._store.remove(entry_id)
        return bool(result)

    def clear(self) -> None:
        """Remove all entries from the store."""
        self._store.clear()
