"""Tests for context_window_array.working_context module."""

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
