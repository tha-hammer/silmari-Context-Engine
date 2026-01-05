"""Implementation LLM context management.

Implementation LLMs receive full content for a bounded set of entries
(<200 per task batch). This enables focused, detailed work without
overwhelming the context window.
"""

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Generator, Optional

from context_window_array.exceptions import EntryBoundsError
from context_window_array.models import ContextEntry, EntryType
from context_window_array.store import CentralContextStore


DEFAULT_MAX_ENTRIES = 200


@dataclass
class ImplementationEntryView:
    """Full view of a context entry for implementation LLMs.

    Contains full content (if not compressed).
    """

    id: str
    entry_type: EntryType
    source: str
    summary: Optional[str]
    content: Optional[str]  # Full content for implementation
    references: list[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    priority: int = 0
    compressed: bool = False


@dataclass
class ImplementationContext:
    """Context snapshot for an implementation LLM.

    Contains full content for requested entries.
    """

    entries: list[ImplementationEntryView]
    entry_count: int
    total_tokens: int
    entry_ids: list[str]


class ImplementationLLMContext:
    """Builds context for implementation LLMs.

    Implementation LLMs need full content to perform detailed work
    like code writing, analysis, or debugging.

    Entry bounds (<200 by default) ensure context windows stay focused.
    """

    def __init__(
        self,
        store: CentralContextStore,
        max_entries: int = DEFAULT_MAX_ENTRIES,
    ):
        """Initialize with a context store.

        Args:
            store: The central context store
            max_entries: Maximum entries allowed per build (default: 200)
        """
        self._store = store
        self._max_entries = max_entries
        self._active_entries: set[str] = set()
        self._total_requests: int = 0
        self._total_releases: int = 0

    def validate_bounds(self, entry_ids: list[str]) -> bool:
        """Check if entry count is within bounds.

        Args:
            entry_ids: List of entry IDs to validate

        Returns:
            True if within bounds, False otherwise
        """
        return len(entry_ids) <= self._max_entries

    def get_bounds_info(self) -> dict:
        """Get information about entry bounds.

        Returns:
            Dictionary with max_entries and other limit info
        """
        return {
            "max_entries": self._max_entries,
            "default": self._max_entries == DEFAULT_MAX_ENTRIES,
        }

    def split_into_batches(self, entry_ids: list[str]) -> list[list[str]]:
        """Split entry IDs into valid batches.

        Args:
            entry_ids: List of entry IDs to split

        Returns:
            List of batches, each within bounds
        """
        batches = []
        for i in range(0, len(entry_ids), self._max_entries):
            batches.append(entry_ids[i : i + self._max_entries])
        return batches

    def _estimate_tokens(self, entry: ContextEntry) -> int:
        """Estimate token count for an entry.

        Uses content if available, otherwise summary.
        Simple estimation: ~4 characters per token.
        """
        text = entry.content or entry.summary or ""
        return len(text) // 4

    def _entry_to_view(self, entry: ContextEntry) -> ImplementationEntryView:
        """Convert entry to implementation view."""
        return ImplementationEntryView(
            id=entry.id,
            entry_type=entry.entry_type,
            source=entry.source,
            summary=entry.summary,
            content=entry.content,  # Include full content
            references=entry.references,
            parent_id=entry.parent_id,
            priority=entry.priority,
            compressed=entry.compressed,
        )

    def build(
        self,
        entry_ids: list[str],
        decompress: bool = False,
        skip_validation: bool = False,
    ) -> ImplementationContext:
        """Build context for an implementation LLM.

        Returns full content for requested entries.

        Args:
            entry_ids: IDs of entries to include
            decompress: If True, attempt to decompress entries
            skip_validation: If True, skip bounds validation

        Returns:
            ImplementationContext with full entry views

        Raises:
            EntryBoundsError: If entry count exceeds max_entries
        """
        # Validate bounds
        if not skip_validation and not self.validate_bounds(entry_ids):
            raise EntryBoundsError(
                requested=len(entry_ids),
                max_allowed=self._max_entries,
            )

        entries = []
        total_tokens = 0

        for entry_id in entry_ids:
            entry = self._store.get(entry_id)
            if entry is None:
                continue

            entries.append(self._entry_to_view(entry))
            total_tokens += self._estimate_tokens(entry)

        return ImplementationContext(
            entries=entries,
            entry_count=len(entries),
            total_tokens=total_tokens,
            entry_ids=[e.id for e in entries],
        )

    def is_in_use(self, entry_id: str) -> bool:
        """Check if an entry is currently in use.

        Args:
            entry_id: ID of entry to check

        Returns:
            True if entry is in active use
        """
        return entry_id in self._active_entries

    def get_active_entries(self) -> set[str]:
        """Get all currently active entry IDs.

        Returns:
            Set of entry IDs currently in use
        """
        return self._active_entries.copy()

    def request_context(
        self,
        entry_ids: list[str],
        skip_validation: bool = False,
    ) -> ImplementationContext:
        """Request entries for implementation context.

        Marks entries as in-use and returns full content.

        Args:
            entry_ids: IDs of entries to request
            skip_validation: If True, skip bounds validation

        Returns:
            ImplementationContext with requested entries

        Raises:
            EntryBoundsError: If entry count exceeds max_entries
        """
        # Build validates bounds
        result = self.build(entry_ids, skip_validation=skip_validation)

        # Mark entries as in_use
        for entry_id in result.entry_ids:
            self._active_entries.add(entry_id)

        self._total_requests += len(result.entry_ids)

        return result

    def release_context(self, entry_ids: Optional[list[str]] = None) -> None:
        """Release entries from active use.

        Args:
            entry_ids: Specific entries to release, or None to release all
        """
        if entry_ids is None:
            released = len(self._active_entries)
            self._active_entries.clear()
        else:
            released = 0
            for entry_id in entry_ids:
                if entry_id in self._active_entries:
                    self._active_entries.discard(entry_id)
                    released += 1

        self._total_releases += released

    def get_usage_stats(self) -> dict:
        """Get usage statistics.

        Returns:
            Dictionary with usage stats
        """
        return {
            "active_count": len(self._active_entries),
            "total_requests": self._total_requests,
            "total_releases": self._total_releases,
        }

    @contextmanager
    def request(
        self,
        entry_ids: list[str],
        skip_validation: bool = False,
    ) -> Generator[ImplementationContext, None, None]:
        """Context manager for requesting and auto-releasing entries.

        Guarantees:
        - Entries are marked in_use when context is entered
        - Entries are ALWAYS released when context exits (success or exception)
        - release_context() is called in finally block

        Args:
            entry_ids: IDs of entries to request
            skip_validation: If True, skip bounds validation

        Yields:
            ImplementationContext with requested entries
        """
        result = self.request_context(entry_ids, skip_validation=skip_validation)
        try:
            yield result
        finally:
            # ALWAYS releases, even if handler raises exception
            self.release_context(result.entry_ids)
