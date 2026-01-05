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


class TestWorkingContextSearch:
    """Behavior 16: Working context search integration."""

    def test_search_returns_relevant_entries(self):
        """Given store with entries, when search(query), then returns relevant entries."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="auth.py",
            content="authenticate user login password session token",
            summary="User authentication module",
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="db.py",
            content="database postgresql connect query",
            summary="Database connection module",
        ))
        store.add(ContextEntry(
            id="ctx_003",
            entry_type=EntryType.FILE,
            source="api.py",
            content="http request handler endpoint",
            summary="API handler",
        ))

        context = WorkingLLMContext(store)
        results = context.search("user authentication login")

        assert len(results) > 0
        # Auth module should be most relevant
        assert results[0].id == "ctx_001"

    def test_search_returns_summary_views(self):
        """Given search results, then they are summary views (no content)."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test content with test data",
            summary="Test summary",
        ))

        context = WorkingLLMContext(store)
        results = context.search("test")

        assert len(results) > 0
        assert results[0].content is None
        assert results[0].summary == "Test summary"

    def test_search_max_results(self):
        """Given many entries, when search(query, max_results=3), then at most 3 returned."""
        store = CentralContextStore()
        for i in range(10):
            store.add(ContextEntry(
                id=f"ctx_{i:03d}",
                entry_type=EntryType.FILE,
                source=f"file{i}.py",
                content=f"python code module {i}",
                summary=f"Module {i}",
            ))

        context = WorkingLLMContext(store)
        results = context.search("python module", max_results=3)

        assert len(results) <= 3

    def test_search_with_type_filter(self):
        """Given mixed entries, when search with entry_types filter, then only those types."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="python code",
            summary="Python file",
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.TASK,
            source="orchestrator",
            content="task about python",
            summary="Python task",
        ))

        context = WorkingLLMContext(store)
        results = context.search("python", entry_types=[EntryType.FILE])

        assert all(r.entry_type == EntryType.FILE for r in results)

    def test_search_empty_query_returns_empty(self):
        """Given working context, when search(''), then returns empty list."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="content",
            summary="summary",
        ))

        context = WorkingLLMContext(store)
        results = context.search("")

        assert results == []

    def test_search_results_have_score(self):
        """Given search results, then each has a similarity score."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="python code",
            summary="Python file",
        ))

        context = WorkingLLMContext(store)
        results = context.search("python")

        assert len(results) > 0
        assert hasattr(results[0], 'score')
        assert 0 <= results[0].score <= 1

    def test_search_with_min_score(self):
        """Given entries, when search with min_score, then only high scores returned."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="exact.py",
            content="exact match python code",
            summary="Exact match",
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="unrelated.py",
            content="cooking recipes food",
            summary="Cooking",
        ))

        context = WorkingLLMContext(store)
        results = context.search("python code", min_score=0.3)

        assert all(r.score >= 0.3 for r in results)

    def test_search_results_include_metadata(self):
        """Given search results, then include all entry metadata."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test content",
            summary="Test summary",
            references=["ctx_000"],
            parent_id="ctx_000",
        ))

        context = WorkingLLMContext(store)
        results = context.search("test")

        assert len(results) > 0
        result = results[0]
        assert result.id == "ctx_001"
        assert result.entry_type == EntryType.FILE
        assert result.source == "test.py"
        assert result.references == ["ctx_000"]
        assert result.parent_id == "ctx_000"

    def test_search_compressed_entries(self):
        """Given compressed entries, when search, then searchable by summary."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content=None,  # Compressed
            summary="Python testing utilities and helpers",
            compressed=True,
        ))

        context = WorkingLLMContext(store)
        results = context.search("python testing")

        assert len(results) > 0
        assert results[0].id == "ctx_001"
        assert results[0].compressed is True
