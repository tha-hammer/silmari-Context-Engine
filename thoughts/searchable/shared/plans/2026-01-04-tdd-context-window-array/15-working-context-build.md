# Phase 15: Working Context Build

## Behavior

Build context for the working (orchestrator) LLM from store entries.

### Test Specification

**Given**: Store with entries
**When**: working_context.build()
**Then**: Returns summaries only (not full content)

**Given**: Store with mixed entries
**When**: working_context.build(entry_types=[FILE])
**Then**: Returns only FILE entries

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_working_context.py`

```python
"""Tests for context_window_array.working_context module."""

import pytest
from context_window_array.models import ContextEntry, EntryType
from context_window_array.store import CentralContextStore
from context_window_array.working_context import WorkingLLMContext


class TestWorkingContextBuild:
    """Behavior 15: Working context build operations."""

    def test_build_returns_summaries_only(self):
        """Given store with entries, when build(), then returns summaries only."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="auth.py",
            content="def authenticate(): very long implementation code here...",
            summary="Authentication module",
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="db.py",
            content="def connect(): database connection code...",
            summary="Database module",
        ))

        context = WorkingLLMContext(store)
        result = context.build()

        # Should contain summaries, not full content
        assert len(result.entries) == 2
        for entry in result.entries:
            assert entry.content is None
            assert entry.summary is not None

    def test_build_includes_all_metadata(self):
        """Given store with entries, when build(), then includes all metadata."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="content",
            summary="Test file",
            references=["ctx_000"],
            parent_id="ctx_000",
        ))

        context = WorkingLLMContext(store)
        result = context.build()

        assert len(result.entries) == 1
        entry = result.entries[0]
        assert entry.id == "ctx_001"
        assert entry.entry_type == EntryType.FILE
        assert entry.source == "test.py"
        assert entry.summary == "Test file"
        assert entry.references == ["ctx_000"]
        assert entry.parent_id == "ctx_000"

    def test_build_filters_by_entry_type(self):
        """Given mixed entries, when build(entry_types=[FILE]), then only FILE entries."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="code",
            summary="File",
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.COMMAND_RESULT,
            source="bash",
            content="output",
            summary="Output",
        ))
        store.add(ContextEntry(
            id="ctx_003",
            entry_type=EntryType.TASK,
            source="orchestrator",
            content="task",
            summary="Task",
        ))

        context = WorkingLLMContext(store)
        result = context.build(entry_types=[EntryType.FILE])

        assert len(result.entries) == 1
        assert result.entries[0].id == "ctx_001"

    def test_build_filters_multiple_types(self):
        """Given mixed entries, when build(entry_types=[FILE, TASK]), then both types."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="code",
            summary="File",
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.COMMAND_RESULT,
            source="bash",
            content="output",
            summary="Output",
        ))
        store.add(ContextEntry(
            id="ctx_003",
            entry_type=EntryType.TASK,
            source="orchestrator",
            content="task",
            summary="Task",
        ))

        context = WorkingLLMContext(store)
        result = context.build(entry_types=[EntryType.FILE, EntryType.TASK])

        assert len(result.entries) == 2
        ids = {e.id for e in result.entries}
        assert ids == {"ctx_001", "ctx_003"}

    def test_build_excludes_non_searchable(self):
        """Given non-searchable entries, when build(), then excluded by default."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="code",
            summary="File",
            searchable=True,
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.COMMAND,
            source="bash",
            content="ls -la",
            summary="Command",
            searchable=False,
        ))

        context = WorkingLLMContext(store)
        result = context.build()

        assert len(result.entries) == 1
        assert result.entries[0].id == "ctx_001"

    def test_build_includes_non_searchable_if_requested(self):
        """Given non-searchable entries, when build(include_non_searchable=True), then included."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="code",
            summary="File",
            searchable=True,
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.COMMAND,
            source="bash",
            content="ls -la",
            summary="Command",
            searchable=False,
        ))

        context = WorkingLLMContext(store)
        result = context.build(include_non_searchable=True)

        assert len(result.entries) == 2

    def test_build_orders_by_relevance(self):
        """Given entries with different priorities, when build(), then ordered by priority."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="old.py",
            content="old code",
            summary="Old file",
            priority=1,
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.TASK,
            source="orchestrator",
            content="current task",
            summary="Current task",
            priority=3,
        ))
        store.add(ContextEntry(
            id="ctx_003",
            entry_type=EntryType.FILE,
            source="recent.py",
            content="recent code",
            summary="Recent file",
            priority=2,
        ))

        context = WorkingLLMContext(store)
        result = context.build()

        # Higher priority first
        assert result.entries[0].id == "ctx_002"
        assert result.entries[1].id == "ctx_003"
        assert result.entries[2].id == "ctx_001"

    def test_build_empty_store(self):
        """Given empty store, when build(), then returns empty context."""
        store = CentralContextStore()
        context = WorkingLLMContext(store)

        result = context.build()

        assert len(result.entries) == 0

    def test_build_returns_context_object(self):
        """Given store, when build(), then returns WorkingContext object."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="code",
            summary="File",
        ))

        context = WorkingLLMContext(store)
        result = context.build()

        assert hasattr(result, 'entries')
        assert hasattr(result, 'total_count')
        assert hasattr(result, 'summary_tokens')

    def test_build_tracks_token_count(self):
        """Given store with entries, when build(), then tracks estimated tokens."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="x" * 1000,  # Large content
            summary="Short summary",
        ))

        context = WorkingLLMContext(store)
        result = context.build()

        # Token count should be based on summaries, not content
        assert result.summary_tokens > 0
        assert result.summary_tokens < 100  # Summary is short
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_working_context.py::TestWorkingContextBuild -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/working_context.py`

```python
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
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_working_context.py::TestWorkingContextBuild -v
```

### 🔵 Refactor: Improve Code

Consider adding max_entries limit and pagination support.

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): ImportError for WorkingLLMContext
- [ ] Test passes (Green): All 10 tests pass
- [ ] `build()` returns summaries, not content
- [ ] `build()` filters by entry type
- [ ] `build()` excludes non-searchable by default
- [ ] `build()` orders by priority
- [ ] Token estimation works

**Manual:**
- [ ] Working context is memory efficient
- [ ] Summaries provide enough context for orchestration
