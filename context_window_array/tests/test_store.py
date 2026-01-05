"""Tests for context_window_array.store module."""

import pytest
from context_window_array.models import ContextEntry, EntryType
from context_window_array.store import CentralContextStore


class TestStoreAddGet:
    """Behavior 7: Store add/get operations."""

    def test_add_entry_to_empty_store(self):
        """Given empty store, when add(entry), then entry is stored."""
        store = CentralContextStore()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test content",
            summary="test summary",
        )

        store.add(entry)

        assert store.get("ctx_001") is not None

    def test_get_returns_added_entry(self):
        """Given store with entry, when get(id), then returns that entry."""
        store = CentralContextStore()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test content",
            summary="test summary",
        )
        store.add(entry)

        result = store.get("ctx_001")

        assert result is entry
        assert result.id == "ctx_001"
        assert result.content == "test content"

    def test_get_nonexistent_returns_none(self):
        """Given store, when get(nonexistent_id), then returns None."""
        store = CentralContextStore()

        result = store.get("nonexistent")

        assert result is None

    def test_add_multiple_entries(self):
        """Given store, when add multiple entries, then all retrievable."""
        store = CentralContextStore()
        entries = [
            ContextEntry(
                id=f"ctx_{i:03d}",
                entry_type=EntryType.FILE,
                source=f"file{i}.py",
                content=f"content {i}",
                summary=f"summary {i}",
            )
            for i in range(5)
        ]

        for entry in entries:
            store.add(entry)

        for i in range(5):
            result = store.get(f"ctx_{i:03d}")
            assert result is not None
            assert result.content == f"content {i}"

    def test_add_duplicate_id_raises_error(self):
        """Given store with entry, when add entry with same id, then raises ValueError."""
        store = CentralContextStore()
        entry1 = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="content 1",
            summary="summary 1",
        )
        entry2 = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.COMMAND,
            source="bash",
            content="content 2",
            summary="summary 2",
        )
        store.add(entry1)

        with pytest.raises(ValueError, match="Entry with id 'ctx_001' already exists"):
            store.add(entry2)

    def test_add_returns_entry_id(self):
        """Given store, when add(entry), then returns entry id."""
        store = CentralContextStore()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
        )

        result = store.add(entry)

        assert result == "ctx_001"

    def test_contains_returns_true_for_existing(self):
        """Given store with entry, when contains(id), then returns True."""
        store = CentralContextStore()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
        )
        store.add(entry)

        assert store.contains("ctx_001") is True

    def test_contains_returns_false_for_nonexistent(self):
        """Given store, when contains(nonexistent_id), then returns False."""
        store = CentralContextStore()

        assert store.contains("nonexistent") is False

    def test_len_returns_entry_count(self):
        """Given store with entries, when len(store), then returns count."""
        store = CentralContextStore()
        for i in range(3):
            store.add(
                ContextEntry(
                    id=f"ctx_{i:03d}",
                    entry_type=EntryType.FILE,
                    source=f"file{i}.py",
                    content=f"content {i}",
                    summary=f"summary {i}",
                )
            )

        assert len(store) == 3

    def test_len_empty_store(self):
        """Given empty store, when len(store), then returns 0."""
        store = CentralContextStore()

        assert len(store) == 0

    def test_get_all_returns_all_entries(self):
        """Given store with entries, when get_all(), then returns all entries."""
        store = CentralContextStore()
        for i in range(3):
            store.add(
                ContextEntry(
                    id=f"ctx_{i:03d}",
                    entry_type=EntryType.FILE,
                    source=f"file{i}.py",
                    content=f"content {i}",
                    summary=f"summary {i}",
                )
            )

        all_entries = store.get_all()

        assert len(all_entries) == 3
        ids = {e.id for e in all_entries}
        assert ids == {"ctx_000", "ctx_001", "ctx_002"}

    def test_get_by_type_filters_correctly(self):
        """Given store with mixed types, when get_by_type(FILE), then returns only files."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.COMMAND, source="bash", content="b", summary="b"))
        store.add(ContextEntry(id="ctx_003", entry_type=EntryType.FILE, source="c.py", content="c", summary="c"))

        files = store.get_by_type(EntryType.FILE)

        assert len(files) == 2
        assert all(e.entry_type == EntryType.FILE for e in files)

    def test_get_by_type_empty_result(self):
        """Given store without matching type, when get_by_type(), then returns empty list."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))

        commands = store.get_by_type(EntryType.COMMAND)

        assert commands == []


class TestStoreRemove:
    """Behavior 8: Store remove operations."""

    def test_remove_existing_entry(self):
        """Given store with entry, when remove(id), then entry removed."""
        store = CentralContextStore()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
        )
        store.add(entry)

        result = store.remove("ctx_001")

        assert result is True
        assert store.get("ctx_001") is None
        assert store.contains("ctx_001") is False

    def test_remove_nonexistent_returns_false(self):
        """Given store, when remove(nonexistent_id), then returns False."""
        store = CentralContextStore()

        result = store.remove("nonexistent")

        assert result is False

    def test_remove_updates_length(self):
        """Given store with entries, when remove(id), then length decreases."""
        store = CentralContextStore()
        for i in range(3):
            store.add(
                ContextEntry(
                    id=f"ctx_{i:03d}",
                    entry_type=EntryType.FILE,
                    source=f"file{i}.py",
                    content=f"content {i}",
                    summary=f"summary {i}",
                )
            )
        assert len(store) == 3

        store.remove("ctx_001")

        assert len(store) == 2

    def test_remove_and_readd(self):
        """Given removed entry, when add entry with same id, then succeeds."""
        store = CentralContextStore()
        entry1 = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="original",
            summary="original",
        )
        store.add(entry1)
        store.remove("ctx_001")

        entry2 = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="new content",
            summary="new summary",
        )
        store.add(entry2)

        result = store.get("ctx_001")
        assert result is not None
        assert result.content == "new content"

    def test_remove_returns_removed_entry(self):
        """Given store with entry, when remove(id, return_entry=True), then returns entry."""
        store = CentralContextStore()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
        )
        store.add(entry)

        removed = store.remove("ctx_001", return_entry=True)

        assert removed is entry
        assert store.get("ctx_001") is None

    def test_remove_nonexistent_with_return_entry(self):
        """Given store, when remove(nonexistent_id, return_entry=True), then returns None."""
        store = CentralContextStore()

        removed = store.remove("nonexistent", return_entry=True)

        assert removed is None

    def test_clear_removes_all_entries(self):
        """Given store with entries, when clear(), then all entries removed."""
        store = CentralContextStore()
        for i in range(5):
            store.add(
                ContextEntry(
                    id=f"ctx_{i:03d}",
                    entry_type=EntryType.FILE,
                    source=f"file{i}.py",
                    content=f"content {i}",
                    summary=f"summary {i}",
                )
            )
        assert len(store) == 5

        store.clear()

        assert len(store) == 0
        assert store.get_all() == []

    def test_remove_multiple(self):
        """Given store with entries, when remove_multiple(ids), then all removed."""
        store = CentralContextStore()
        for i in range(5):
            store.add(
                ContextEntry(
                    id=f"ctx_{i:03d}",
                    entry_type=EntryType.FILE,
                    source=f"file{i}.py",
                    content=f"content {i}",
                    summary=f"summary {i}",
                )
            )

        removed_count = store.remove_multiple(["ctx_001", "ctx_003", "ctx_999"])

        assert removed_count == 2  # ctx_999 doesn't exist
        assert len(store) == 3
        assert store.get("ctx_001") is None
        assert store.get("ctx_003") is None
        assert store.get("ctx_002") is not None
