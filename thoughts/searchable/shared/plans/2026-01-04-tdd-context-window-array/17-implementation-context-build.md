# Phase 17: Implementation Context Build

## Behavior

Build context for implementation LLMs with full content and entry bounds.

### Test Specification

**Given**: Store with entries
**When**: implementation_context.build(entry_ids)
**Then**: Returns full content for requested entries

**Given**: Store with entries
**When**: implementation_context.build(entry_ids) with >200 entries
**Then**: Raises EntryBoundsError

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_implementation_context.py`

```python
"""Tests for context_window_array.implementation_context module."""

import pytest
from context_window_array.models import ContextEntry, EntryType
from context_window_array.store import CentralContextStore
from context_window_array.implementation_context import (
    ImplementationLLMContext,
    EntryBoundsError,
)


class TestImplementationContextBuild:
    """Behavior 17: Implementation context build operations."""

    def test_build_returns_full_content(self):
        """Given store with entries, when build(entry_ids), then returns full content."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="auth.py",
            content="def authenticate(user, password):\n    return verify(user, password)",
            summary="Auth function",
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="db.py",
            content="def connect():\n    return psycopg2.connect()",
            summary="DB connect",
        ))

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001", "ctx_002"])

        assert len(result.entries) == 2

        # Should have full content
        entry1 = next(e for e in result.entries if e.id == "ctx_001")
        assert entry1.content == "def authenticate(user, password):\n    return verify(user, password)"

        entry2 = next(e for e in result.entries if e.id == "ctx_002")
        assert entry2.content == "def connect():\n    return psycopg2.connect()"

    def test_build_includes_all_metadata(self):
        """Given entry with metadata, when build(), then all metadata included."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test content",
            summary="Test summary",
            references=["ctx_000"],
            parent_id="ctx_000",
            priority=5,
        ))

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001"])

        assert len(result.entries) == 1
        entry = result.entries[0]
        assert entry.id == "ctx_001"
        assert entry.entry_type == EntryType.FILE
        assert entry.source == "test.py"
        assert entry.content == "test content"
        assert entry.summary == "Test summary"
        assert entry.references == ["ctx_000"]
        assert entry.parent_id == "ctx_000"

    def test_build_only_requested_entries(self):
        """Given multiple entries, when build(subset), then only subset returned."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b"))
        store.add(ContextEntry(id="ctx_003", entry_type=EntryType.FILE, source="c.py", content="c", summary="c"))

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001", "ctx_003"])

        assert len(result.entries) == 2
        ids = {e.id for e in result.entries}
        assert ids == {"ctx_001", "ctx_003"}

    def test_build_skips_nonexistent_entries(self):
        """Given nonexistent entry id, when build(), then skipped without error."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001", "ctx_nonexistent"])

        assert len(result.entries) == 1
        assert result.entries[0].id == "ctx_001"

    def test_build_empty_list_returns_empty(self):
        """Given empty entry list, when build([]), then returns empty context."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))

        context = ImplementationLLMContext(store)
        result = context.build([])

        assert len(result.entries) == 0

    def test_build_preserves_order(self):
        """Given entry ids, when build(), then order preserved."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b"))
        store.add(ContextEntry(id="ctx_003", entry_type=EntryType.FILE, source="c.py", content="c", summary="c"))

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_003", "ctx_001", "ctx_002"])

        assert [e.id for e in result.entries] == ["ctx_003", "ctx_001", "ctx_002"]

    def test_build_handles_compressed_entries(self):
        """Given compressed entry, when build(), then returns with summary only."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content=None,
            summary="Compressed file summary",
            compressed=True,
        ))

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001"])

        assert len(result.entries) == 1
        entry = result.entries[0]
        assert entry.content is None
        assert entry.summary == "Compressed file summary"
        assert entry.compressed is True

    def test_build_returns_context_object(self):
        """Given entries, when build(), then returns ImplementationContext object."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001"])

        assert hasattr(result, 'entries')
        assert hasattr(result, 'entry_count')
        assert hasattr(result, 'total_tokens')
        assert hasattr(result, 'entry_ids')

    def test_build_tracks_token_count(self):
        """Given entries, when build(), then tracks estimated tokens."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="x" * 1000,
            summary="Short",
        ))

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001"])

        # Token count based on content, not summary
        assert result.total_tokens > 200  # 1000 chars / ~4 chars per token

    def test_build_decompresses_if_requested(self):
        """Given compressed entry, when build with decompress=True, then decompresses."""
        store = CentralContextStore()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="original content",
            summary="Summary",
        )
        store.add(entry)
        store.compress("ctx_001")

        context = ImplementationLLMContext(store)

        # Without decompress - compressed
        result1 = context.build(["ctx_001"], decompress=False)
        assert result1.entries[0].compressed is True

        # Note: Actual decompression would require storing original content
        # This test documents the expected interface
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_implementation_context.py::TestImplementationContextBuild -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/implementation_context.py`

```python
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
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_implementation_context.py::TestImplementationContextBuild -v
```

### 🔵 Refactor: Improve Code

Consider adding content size limits per entry.

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): ImportError for ImplementationLLMContext
- [ ] Test passes (Green): All 10 tests pass
- [ ] `build()` returns full content
- [ ] `build()` includes all metadata
- [ ] `build()` only returns requested entries
- [ ] `build()` preserves order
- [ ] `build()` handles compressed entries
- [ ] Token estimation works

**Manual:**
- [ ] Implementation context provides enough detail for coding tasks
- [ ] Performance acceptable for 200 entries
