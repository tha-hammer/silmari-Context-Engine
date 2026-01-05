"""Implementation LLM context management.

Implementation LLMs receive full content for a bounded set of entries
(<200 per task batch). This enables focused, detailed work without
overwhelming the context window.
"""

from dataclasses import dataclass, field
from typing import Optional

from context_window_array.models import ContextEntry, EntryType
from context_window_array.store import CentralContextStore


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
    """

    def __init__(self, store: CentralContextStore):
        """Initialize with a context store.

        Args:
            store: The central context store
        """
        self._store = store

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
    ) -> ImplementationContext:
        """Build context for an implementation LLM.

        Returns full content for requested entries.

        Args:
            entry_ids: IDs of entries to include
            decompress: If True, attempt to decompress entries

        Returns:
            ImplementationContext with full entry views
        """
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
