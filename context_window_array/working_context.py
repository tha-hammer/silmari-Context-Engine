"""Working LLM context management.

The Working LLM (orchestrator) only sees summaries, not full content.
This keeps the orchestrator's context window focused on high-level
task coordination rather than implementation details.
"""

from dataclasses import dataclass, field
from typing import Optional

from context_window_array.models import ContextEntry, EntryType
from context_window_array.store import CentralContextStore


@dataclass
class ContextEntryView:
    """Summary view of a context entry for the working LLM.

    Contains all metadata but content is None (summary only).
    """
    id: str
    entry_type: EntryType
    source: str
    summary: Optional[str]
    content: None = None  # Always None for working context
    references: list[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    priority: int = 0
    compressed: bool = False


@dataclass
class WorkingContext:
    """Context snapshot for the working LLM.

    Contains summary views of entries, not full content.
    """
    entries: list[ContextEntryView]
    total_count: int
    summary_tokens: int


class WorkingLLMContext:
    """Builds context for the working (orchestrator) LLM.

    The working LLM coordinates tasks and only needs summaries
    of what's in context, not the full content.
    """

    def __init__(self, store: CentralContextStore):
        """Initialize with a context store.

        Args:
            store: The central context store
        """
        self._store = store

    def _estimate_tokens(self, text: Optional[str]) -> int:
        """Estimate token count for text.

        Simple estimation: ~4 characters per token.
        """
        if not text:
            return 0
        return len(text) // 4

    def _entry_to_view(self, entry: ContextEntry) -> ContextEntryView:
        """Convert entry to summary view."""
        return ContextEntryView(
            id=entry.id,
            entry_type=entry.entry_type,
            source=entry.source,
            summary=entry.summary,
            content=None,  # Never include content
            references=entry.references,
            parent_id=entry.parent_id,
            priority=entry.priority,
            compressed=entry.compressed,
        )

    def build(
        self,
        entry_types: Optional[list[EntryType]] = None,
        include_non_searchable: bool = False,
    ) -> WorkingContext:
        """Build context for the working LLM.

        Returns summary views of entries, not full content.

        Args:
            entry_types: Optional filter by entry types
            include_non_searchable: If True, include non-searchable entries

        Returns:
            WorkingContext with summary views
        """
        # Get all entries
        entries = self._store.get_all()

        # Filter by type if specified
        if entry_types:
            entries = [e for e in entries if e.entry_type in entry_types]

        # Filter non-searchable unless requested
        if not include_non_searchable:
            entries = [e for e in entries if e.searchable]

        # Sort by priority (descending)
        entries.sort(key=lambda e: e.priority, reverse=True)

        # Convert to views
        views = [self._entry_to_view(e) for e in entries]

        # Calculate token count from summaries
        total_tokens = sum(self._estimate_tokens(v.summary) for v in views)

        return WorkingContext(
            entries=views,
            total_count=len(views),
            summary_tokens=total_tokens,
        )
