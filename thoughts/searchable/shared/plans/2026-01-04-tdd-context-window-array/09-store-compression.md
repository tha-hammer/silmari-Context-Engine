# Phase 09: Store Compression

## Behavior

Implement store-level compression operations that delegate to entry compression.

### Test Specification

**Given**: Store with entry
**When**: compress(id)
**Then**: Entry.compressed=True, content=None

**Given**: Store with compressed entry
**When**: get_content(id)
**Then**: Raises ContextCompressedError

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_store.py`

```python
from context_window_array.exceptions import ContextCompressedError


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
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_store.py::TestStoreCompression -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/store.py` (add methods)

```python
class CentralContextStore:
    # ... existing methods ...

    def compress(self, entry_id: str) -> bool:
        """Compress an entry by ID, removing content and retaining summary.

        Args:
            entry_id: ID of entry to compress

        Returns:
            True if entry was found (and compressed or already compressed),
            False if entry not found

        Raises:
            ValueError: If entry has no summary
        """
        entry = self.get(entry_id)
        if entry is None:
            return False
        entry.compress()
        return True

    def compress_multiple(self, entry_ids: list[str]) -> int:
        """Compress multiple entries.

        Args:
            entry_ids: List of entry IDs to compress

        Returns:
            Number of entries successfully compressed
        """
        compressed = 0
        for entry_id in entry_ids:
            entry = self.get(entry_id)
            if entry is not None and entry.can_compress():
                entry.compress()
                compressed += 1
        return compressed

    def get_content(self, entry_id: str) -> Optional[str]:
        """Get content of an entry.

        Args:
            entry_id: ID of entry

        Returns:
            Content string, or None if entry not found

        Raises:
            ContextCompressedError: If entry is compressed
        """
        entry = self.get(entry_id)
        if entry is None:
            return None
        return entry.get_content()

    def get_summary(self, entry_id: str) -> Optional[str]:
        """Get summary of an entry.

        Args:
            entry_id: ID of entry

        Returns:
            Summary string, or None if entry not found
        """
        entry = self.get(entry_id)
        if entry is None:
            return None
        return entry.summary

    def get_compressed(self) -> list[ContextEntry]:
        """Get all compressed entries.

        Returns:
            List of compressed entries
        """
        return [e for e in self._entries.values() if e.compressed]

    def get_uncompressed(self) -> list[ContextEntry]:
        """Get all uncompressed entries.

        Returns:
            List of uncompressed entries
        """
        return [e for e in self._entries.values() if not e.compressed]
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_store.py::TestStoreCompression -v
```

### 🔵 Refactor: Improve Code

The implementation delegates to ContextEntry methods, keeping the store logic simple.

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): AttributeError for compress
- [ ] Test passes (Green): All 13 tests pass
- [ ] `compress()` delegates to entry.compress()
- [ ] `compress()` returns False for nonexistent entry
- [ ] `get_content()` returns content or raises ContextCompressedError
- [ ] `get_summary()` always returns summary (works for compressed)
- [ ] `get_compressed()` and `get_uncompressed()` filter correctly

**Manual:**
- [ ] Compression follows research document section 5
- [ ] Error handling is consistent
