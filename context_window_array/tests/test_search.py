"""Tests for context_window_array.search_index module."""

import pytest
import numpy as np
from context_window_array.models import ContextEntry, EntryType
from context_window_array.search_index import VectorSearchIndex


class TestSearchIndexAdd:
    """Behavior 12: Search index add operations."""

    def test_add_entry_with_content(self):
        """Given entry with content, when add(entry), then entry is indexed."""
        index = VectorSearchIndex()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def hello_world(): print('Hello, World!')",
            summary="Hello world function",
        )

        index.add(entry)

        assert index.contains("ctx_001")
        assert len(index) == 1

    def test_add_entry_with_summary_only(self):
        """Given compressed entry (summary only), when add(entry), then summary indexed."""
        index = VectorSearchIndex()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content=None,
            summary="Hello world function",
            compressed=True,
        )

        index.add(entry)

        assert index.contains("ctx_001")

    def test_add_multiple_entries(self):
        """Given multiple entries, when add each, then all indexed."""
        index = VectorSearchIndex()
        entries = [
            ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="auth code", summary="auth"),
            ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="database code", summary="db"),
            ContextEntry(id="ctx_003", entry_type=EntryType.FILE, source="c.py", content="api code", summary="api"),
        ]

        for entry in entries:
            index.add(entry)

        assert len(index) == 3
        assert index.contains("ctx_001")
        assert index.contains("ctx_002")
        assert index.contains("ctx_003")

    def test_add_duplicate_raises_error(self):
        """Given entry already indexed, when add same id, then raises ValueError."""
        index = VectorSearchIndex()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
        )
        index.add(entry)

        with pytest.raises(ValueError, match="already exists"):
            index.add(entry)

    def test_add_non_searchable_skipped(self):
        """Given entry with searchable=False, when add(entry), then not indexed."""
        index = VectorSearchIndex()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.COMMAND,
            source="bash",
            content="ls -la",
            summary="list files",
            searchable=False,
        )

        index.add(entry)

        # Entry tracked but marked as non-searchable
        assert not index.contains("ctx_001")
        assert len(index) == 0

    def test_add_returns_entry_id(self):
        """Given entry, when add(entry), then returns entry id."""
        index = VectorSearchIndex()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
        )

        result = index.add(entry)

        assert result == "ctx_001"

    def test_remove_entry(self):
        """Given indexed entry, when remove(id), then no longer searchable."""
        index = VectorSearchIndex()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
        )
        index.add(entry)
        assert index.contains("ctx_001")

        index.remove("ctx_001")

        assert not index.contains("ctx_001")
        assert len(index) == 0

    def test_remove_nonexistent_is_noop(self):
        """Given nonexistent id, when remove(id), then no error."""
        index = VectorSearchIndex()

        # Should not raise
        index.remove("nonexistent")

    def test_update_entry(self):
        """Given indexed entry, when update(new_entry), then new content indexed."""
        index = VectorSearchIndex()
        entry1 = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="original content",
            summary="original",
        )
        index.add(entry1)

        entry2 = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="updated content about authentication",
            summary="updated",
        )
        index.update(entry2)

        assert index.contains("ctx_001")
        # The vector should be updated (we'll verify via search in later tests)

    def test_get_vector(self):
        """Given indexed entry, when get_vector(id), then returns numpy array."""
        index = VectorSearchIndex()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="machine learning neural network",
            summary="ml code",
        )
        index.add(entry)

        vector = index.get_vector("ctx_001")

        assert isinstance(vector, np.ndarray)
        assert len(vector) > 0

    def test_get_vector_nonexistent_returns_none(self):
        """Given nonexistent id, when get_vector(id), then returns None."""
        index = VectorSearchIndex()

        vector = index.get_vector("nonexistent")

        assert vector is None


class TestSearchQuery:
    """Behavior 13: Search query operations."""

    def test_search_finds_relevant_entry(self):
        """Given indexed entries, when search(query), then finds relevant entry."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="auth.py",
            content="def authenticate_user(username, password): verify credentials and return token",
            summary="User authentication",
        ))
        index.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="db.py",
            content="def connect_database(): establish connection to postgresql",
            summary="Database connection",
        ))
        index.add(ContextEntry(
            id="ctx_003",
            entry_type=EntryType.FILE,
            source="api.py",
            content="def handle_request(): process incoming http request",
            summary="API handler",
        ))

        results = index.search("authenticate user login password")

        assert len(results) > 0
        # auth.py should be most relevant
        assert results[0].entry_id == "ctx_001"

    def test_search_returns_ranked_results(self):
        """Given indexed entries, when search(query), then results ranked by similarity."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="a.py",
            content="machine learning neural network deep learning",
            summary="ML code",
        ))
        index.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="b.py",
            content="simple function hello world",
            summary="Hello",
        ))
        index.add(ContextEntry(
            id="ctx_003",
            entry_type=EntryType.FILE,
            source="c.py",
            content="machine learning model training",
            summary="ML training",
        ))

        results = index.search("machine learning")

        # Both ML entries should be in top results
        top_ids = [r.entry_id for r in results[:2]]
        assert "ctx_001" in top_ids
        assert "ctx_003" in top_ids

    def test_search_max_results(self):
        """Given many entries, when search(query, max_results=2), then returns at most 2."""
        index = VectorSearchIndex()
        for i in range(10):
            index.add(ContextEntry(
                id=f"ctx_{i:03d}",
                entry_type=EntryType.FILE,
                source=f"file{i}.py",
                content=f"python code function {i}",
                summary=f"Code {i}",
            ))

        results = index.search("python code", max_results=2)

        assert len(results) <= 2

    def test_search_empty_query_returns_empty(self):
        """Given indexed entries, when search(''), then returns empty list."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test content",
            summary="test",
        ))

        results = index.search("")

        assert results == []

    def test_search_no_matches_returns_empty(self):
        """Given indexed entries, when search(unrelated query), then returns empty or low scores."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="auth.py",
            content="authentication login password",
            summary="Auth",
        ))

        results = index.search("quantum physics thermodynamics")

        # Should return empty or very low similarity results
        assert len(results) == 0 or all(r.score < 0.1 for r in results)

    def test_search_result_has_score(self):
        """Given search results, then each result has a similarity score."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="python programming code",
            summary="Code",
        ))

        results = index.search("python code")

        assert len(results) > 0
        assert hasattr(results[0], 'score')
        assert 0 <= results[0].score <= 1

    def test_search_result_has_entry_id(self):
        """Given search results, then each result has entry_id."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test content",
            summary="test",
        ))

        results = index.search("test")

        assert len(results) > 0
        assert results[0].entry_id == "ctx_001"

    def test_search_filter_by_entry_type(self):
        """Given mixed entries, when search with entry_types filter, then only those types returned."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="python code file",
            summary="Python file",
        ))
        index.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.COMMAND_RESULT,
            source="bash",
            content="python script output",
            summary="Command output",
        ))
        index.add(ContextEntry(
            id="ctx_003",
            entry_type=EntryType.FILE,
            source="test2.py",
            content="more python code",
            summary="More Python",
        ))

        # Need to store entry types for filtering
        results = index.search("python", entry_types=[EntryType.FILE])

        assert all(r.entry_type == EntryType.FILE for r in results)
        assert len(results) == 2

    def test_search_filter_multiple_types(self):
        """Given mixed entries, when search with multiple entry_types, then all matching types returned."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="code file",
            summary="File",
        ))
        index.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.COMMAND_RESULT,
            source="bash",
            content="command output",
            summary="Output",
        ))
        index.add(ContextEntry(
            id="ctx_003",
            entry_type=EntryType.TASK,
            source="orchestrator",
            content="task description",
            summary="Task",
        ))

        results = index.search("code output task", entry_types=[EntryType.FILE, EntryType.COMMAND_RESULT])

        result_types = {r.entry_type for r in results}
        assert EntryType.TASK not in result_types

    def test_search_with_threshold(self):
        """Given indexed entries, when search with min_score threshold, then only high scores returned."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="exact match python programming",
            summary="Exact",
        ))
        index.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="other.py",
            content="unrelated content about cooking recipes",
            summary="Cooking",
        ))

        results = index.search("python programming", min_score=0.3)

        # Should only return the relevant entry
        assert all(r.score >= 0.3 for r in results)

    def test_search_empty_index_returns_empty(self):
        """Given empty index, when search(query), then returns empty list."""
        index = VectorSearchIndex()

        results = index.search("any query")

        assert results == []
