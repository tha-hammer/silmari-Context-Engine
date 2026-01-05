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


class TestStoreCompression:
    """Behavior 9: Store compression operations."""

    def test_compress_entry_by_id(self):
        """Given store with entry, when compress(id), then entry is compressed."""
        store = CentralContextStore()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def main(): pass",
            summary="Main function",
        )
        store.add(entry)

        result = store.compress("ctx_001")

        assert result is True
        stored = store.get("ctx_001")
        assert stored.compressed is True
        assert stored.content is None
        assert stored.summary == "Main function"

    def test_compress_nonexistent_returns_false(self):
        """Given store, when compress(nonexistent_id), then returns False."""
        store = CentralContextStore()

        result = store.compress("nonexistent")

        assert result is False

    def test_compress_already_compressed_is_noop(self):
        """Given store with compressed entry, when compress(id), then returns True (noop)."""
        store = CentralContextStore()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content=None,
            summary="Main function",
            compressed=True,
        )
        store.add(entry)

        result = store.compress("ctx_001")

        assert result is True

    def test_compress_without_summary_raises_error(self):
        """Given entry without summary, when compress(id), then raises ValueError."""
        store = CentralContextStore()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def main(): pass",
            summary=None,
        )
        store.add(entry)

        with pytest.raises(ValueError, match="Cannot compress entry without summary"):
            store.compress("ctx_001")

    def test_get_content_from_store(self):
        """Given store with entry, when get_content(id), then returns content."""

        store = CentralContextStore()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def main(): pass",
            summary="Main function",
        )
        store.add(entry)

        content = store.get_content("ctx_001")

        assert content == "def main(): pass"

    def test_get_content_compressed_raises_error(self):
        """Given store with compressed entry, when get_content(id), then raises ContextCompressedError."""
        from context_window_array.exceptions import ContextCompressedError

        store = CentralContextStore()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content=None,
            summary="Main function",
            compressed=True,
        )
        store.add(entry)

        with pytest.raises(ContextCompressedError, match="ctx_001"):
            store.get_content("ctx_001")

    def test_get_content_nonexistent_returns_none(self):
        """Given store, when get_content(nonexistent_id), then returns None."""
        store = CentralContextStore()

        result = store.get_content("nonexistent")

        assert result is None

    def test_get_summary(self):
        """Given store with entry, when get_summary(id), then returns summary."""
        store = CentralContextStore()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def main(): pass",
            summary="Main function",
        )
        store.add(entry)

        summary = store.get_summary("ctx_001")

        assert summary == "Main function"

    def test_get_summary_compressed(self):
        """Given store with compressed entry, when get_summary(id), then returns summary."""
        store = CentralContextStore()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content=None,
            summary="Main function",
            compressed=True,
        )
        store.add(entry)

        summary = store.get_summary("ctx_001")

        assert summary == "Main function"

    def test_get_summary_nonexistent_returns_none(self):
        """Given store, when get_summary(nonexistent_id), then returns None."""
        store = CentralContextStore()

        result = store.get_summary("nonexistent")

        assert result is None

    def test_compress_multiple(self):
        """Given store with entries, when compress_multiple(ids), then all compressed."""
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

        compressed_count = store.compress_multiple(["ctx_000", "ctx_002"])

        assert compressed_count == 2
        assert store.get("ctx_000").compressed is True
        assert store.get("ctx_001").compressed is False
        assert store.get("ctx_002").compressed is True

    def test_get_compressed_entries(self):
        """Given store with mixed entries, when get_compressed(), then returns only compressed."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content=None, summary="b", compressed=True))
        store.add(ContextEntry(id="ctx_003", entry_type=EntryType.FILE, source="c.py", content=None, summary="c", compressed=True))

        compressed = store.get_compressed()

        assert len(compressed) == 2
        assert all(e.compressed for e in compressed)

    def test_get_uncompressed_entries(self):
        """Given store with mixed entries, when get_uncompressed(), then returns only uncompressed."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content=None, summary="b", compressed=True))
        store.add(ContextEntry(id="ctx_003", entry_type=EntryType.FILE, source="c.py", content="c", summary="c"))

        uncompressed = store.get_uncompressed()

        assert len(uncompressed) == 2
        assert all(not e.compressed for e in uncompressed)


class TestCommandResultSeparation:
    """Behavior 10: Command/result separation pattern."""

    def test_add_command_result_discards_command(self):
        """Given command and result, when add_command_result(keep_command=False), then only result stored."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="grep -rn 'class' src/",
            result="Found 50 matches:\n  src/main.py:10: class Main\n  ...",
            summary="50 class definitions found",
            keep_command=False,
        )

        # Result is stored
        result_entry = store.get(result_id)
        assert result_entry is not None
        assert result_entry.entry_type == EntryType.COMMAND_RESULT
        assert "50 matches" in result_entry.content
        assert result_entry.summary == "50 class definitions found"

        # No command entry exists (only 1 entry total)
        assert len(store) == 1

    def test_add_command_result_keeps_command(self):
        """Given command and result, when add_command_result(keep_command=True), then both stored."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="grep -rn 'class' src/",
            result="Found 50 matches:\n  src/main.py:10: class Main\n  ...",
            summary="50 class definitions found",
            keep_command=True,
        )

        # Both entries exist
        assert len(store) == 2

        # Result entry has parent_id pointing to command
        result_entry = store.get(result_id)
        assert result_entry is not None
        assert result_entry.parent_id is not None

        # Command entry exists
        command_entry = store.get(result_entry.parent_id)
        assert command_entry is not None
        assert command_entry.entry_type == EntryType.COMMAND
        assert command_entry.content == "grep -rn 'class' src/"

    def test_add_command_result_returns_result_id(self):
        """Given command and result, when add_command_result(), then returns result entry id."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="ls -la",
            result="total 100\ndrwxr-xr-x ...",
            summary="Directory listing",
            keep_command=False,
        )

        assert result_id.startswith("ctx_")
        assert store.contains(result_id)

    def test_add_command_result_generates_unique_ids(self):
        """Given multiple command results, when added, then unique IDs generated."""
        store = CentralContextStore()

        id1 = store.add_command_result(
            command="cmd1",
            result="result1",
            summary="summary1",
            keep_command=False,
        )
        id2 = store.add_command_result(
            command="cmd2",
            result="result2",
            summary="summary2",
            keep_command=False,
        )

        assert id1 != id2

    def test_add_command_result_with_source(self):
        """Given source parameter, when add_command_result(), then source set."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="npm test",
            result="All tests passed",
            summary="Tests passed",
            source="npm",
            keep_command=False,
        )

        result_entry = store.get(result_id)
        assert result_entry.source == "npm"

    def test_add_command_result_default_source(self):
        """Given no source parameter, when add_command_result(), then source is 'bash'."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="echo hello",
            result="hello",
            summary="Echo output",
            keep_command=False,
        )

        result_entry = store.get(result_id)
        assert result_entry.source == "bash"

    def test_add_command_result_command_not_searchable(self):
        """Given keep_command=True, when add_command_result(), then command is not searchable."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="grep pattern file",
            result="match found",
            summary="1 match",
            keep_command=True,
        )

        result_entry = store.get(result_id)
        command_entry = store.get(result_entry.parent_id)

        # Command should not be searchable (per research doc)
        assert command_entry.searchable is False
        # Result should be searchable
        assert result_entry.searchable is True

    def test_add_command_result_with_ttl(self):
        """Given ttl parameter, when add_command_result(), then result has TTL."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="ls",
            result="files",
            summary="file list",
            keep_command=False,
            ttl=5,
        )

        result_entry = store.get(result_id)
        assert result_entry.ttl == 5

    def test_remove_command_keeps_result(self):
        """Given command and result, when remove command, then result still accessible."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="grep pattern",
            result="match",
            summary="1 match",
            keep_command=True,
        )
        result_entry = store.get(result_id)
        command_id = result_entry.parent_id

        # Remove command
        store.remove(command_id)

        # Result still exists and accessible
        assert store.contains(result_id)
        result_after = store.get(result_id)
        assert result_after is not None
        assert result_after.content == "match"

    def test_compress_command_result_chain(self):
        """Given command and result, when compress result, then result compressed."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="grep -rn 'def' src/",
            result="Found 100 function definitions...",
            summary="100 functions found",
            keep_command=True,
        )

        # Compress result
        store.compress(result_id)

        result_entry = store.get(result_id)
        assert result_entry.compressed is True
        assert result_entry.summary == "100 functions found"


class TestStoreTTLProcessing:
    """Behavior 11: Store TTL processing operations."""

    def test_process_ttl_decrements_all(self):
        """Given store with TTL entries, when process_ttl(), then all TTLs decremented."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a", ttl=5))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b", ttl=3))
        store.add(ContextEntry(id="ctx_003", entry_type=EntryType.FILE, source="c.py", content="c", summary="c", ttl=1))

        store.process_ttl()

        assert store.get("ctx_001").ttl == 4
        assert store.get("ctx_002").ttl == 2
        assert store.get("ctx_003").ttl == 0

    def test_process_ttl_skips_none_ttl(self):
        """Given entry with ttl=None, when process_ttl(), then ttl stays None."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a", ttl=None))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b", ttl=5))

        store.process_ttl()

        assert store.get("ctx_001").ttl is None
        assert store.get("ctx_002").ttl == 4

    def test_process_ttl_zero_stays_zero(self):
        """Given entry with ttl=0, when process_ttl(), then ttl stays 0."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a", ttl=0))

        store.process_ttl()

        assert store.get("ctx_001").ttl == 0

    def test_cleanup_expired_removes_zero_ttl(self):
        """Given entries with ttl=0, when cleanup_expired(), then they are removed."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a", ttl=0))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b", ttl=5))
        store.add(ContextEntry(id="ctx_003", entry_type=EntryType.FILE, source="c.py", content="c", summary="c", ttl=0))

        removed = store.cleanup_expired()

        assert removed == 2
        assert len(store) == 1
        assert store.get("ctx_001") is None
        assert store.get("ctx_002") is not None
        assert store.get("ctx_003") is None

    def test_cleanup_expired_keeps_none_ttl(self):
        """Given entry with ttl=None, when cleanup_expired(), then entry kept."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a", ttl=None))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b", ttl=0))

        removed = store.cleanup_expired()

        assert removed == 1
        assert store.get("ctx_001") is not None
        assert store.get("ctx_002") is None

    def test_cleanup_expired_returns_zero_when_none_expired(self):
        """Given no expired entries, when cleanup_expired(), then returns 0."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a", ttl=5))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b", ttl=None))

        removed = store.cleanup_expired()

        assert removed == 0
        assert len(store) == 2

    def test_get_expired_entries(self):
        """Given store with mixed TTL entries, when get_expired(), then returns expired."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a", ttl=0))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b", ttl=5))
        store.add(ContextEntry(id="ctx_003", entry_type=EntryType.FILE, source="c.py", content="c", summary="c", ttl=0))

        expired = store.get_expired()

        assert len(expired) == 2
        assert all(e.ttl == 0 for e in expired)

    def test_get_expiring_soon(self):
        """Given store with entries, when get_expiring_soon(threshold=2), then returns entries with ttl <= 2."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a", ttl=1))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b", ttl=2))
        store.add(ContextEntry(id="ctx_003", entry_type=EntryType.FILE, source="c.py", content="c", summary="c", ttl=5))
        store.add(ContextEntry(id="ctx_004", entry_type=EntryType.FILE, source="d.py", content="d", summary="d", ttl=None))

        expiring = store.get_expiring_soon(threshold=2)

        assert len(expiring) == 2
        ids = {e.id for e in expiring}
        assert ids == {"ctx_001", "ctx_002"}

    def test_process_turn_combines_ttl_and_cleanup(self):
        """Given store, when process_turn(), then TTLs decremented and expired cleaned."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a", ttl=1))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b", ttl=2))
        store.add(ContextEntry(id="ctx_003", entry_type=EntryType.FILE, source="c.py", content="c", summary="c", ttl=None))

        result = store.process_turn()

        # ctx_001 was ttl=1, now 0, should be removed
        # ctx_002 was ttl=2, now 1, should remain
        # ctx_003 has no TTL, should remain
        assert result["decremented"] == 2
        assert result["removed"] == 1
        assert len(store) == 2
        assert store.get("ctx_001") is None
        assert store.get("ctx_002").ttl == 1
        assert store.get("ctx_003").ttl is None

    def test_extend_ttl(self):
        """Given entry with TTL, when extend_ttl(id, 5), then TTL increased."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a", ttl=3))

        result = store.extend_ttl("ctx_001", 5)

        assert result is True
        assert store.get("ctx_001").ttl == 8

    def test_extend_ttl_nonexistent(self):
        """Given store, when extend_ttl(nonexistent, 5), then returns False."""
        store = CentralContextStore()

        result = store.extend_ttl("nonexistent", 5)

        assert result is False

    def test_extend_ttl_with_none_ttl_sets_ttl(self):
        """Given entry with ttl=None, when extend_ttl(id, 5), then TTL set to 5."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a", ttl=None))

        result = store.extend_ttl("ctx_001", 5)

        assert result is True
        assert store.get("ctx_001").ttl == 5
