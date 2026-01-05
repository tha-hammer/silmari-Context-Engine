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
