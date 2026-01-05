# Phase 08: Store Remove

## Behavior

Implement remove operation for the CentralContextStore.

### Test Specification

**Given**: Store with entry
**When**: remove(id)
**Then**: Entry no longer retrievable

**Given**: Store
**When**: remove(nonexistent_id)
**Then**: Returns False (no error)

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_store.py`

```python
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
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_store.py::TestStoreRemove -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/store.py` (add methods)

```python
from typing import Optional, Union


class CentralContextStore:
    # ... existing methods ...

    def remove(
        self,
        entry_id: str,
        return_entry: bool = False
    ) -> Union[bool, Optional[ContextEntry]]:
        """Remove an entry from the store.

        Args:
            entry_id: ID of entry to remove
            return_entry: If True, return the removed entry instead of bool

        Returns:
            If return_entry=False: True if entry was removed, False if not found
            If return_entry=True: The removed entry, or None if not found
        """
        if entry_id not in self._entries:
            return None if return_entry else False

        entry = self._entries.pop(entry_id)
        return entry if return_entry else True

    def remove_multiple(self, entry_ids: list[str]) -> int:
        """Remove multiple entries from the store.

        Args:
            entry_ids: List of entry IDs to remove

        Returns:
            Number of entries actually removed
        """
        removed = 0
        for entry_id in entry_ids:
            if entry_id in self._entries:
                del self._entries[entry_id]
                removed += 1
        return removed

    def clear(self) -> None:
        """Remove all entries from the store."""
        self._entries.clear()
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_store.py::TestStoreRemove -v
```

### 🔵 Refactor: Improve Code

Consider adding an `on_remove` callback hook for future extensibility (e.g., removing from search index).

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): AttributeError for remove
- [ ] Test passes (Green): All 8 tests pass
- [ ] `remove()` removes entry and returns True
- [ ] `remove()` returns False for nonexistent ID
- [ ] `remove(return_entry=True)` returns the removed entry
- [ ] `remove_multiple()` removes multiple and returns count
- [ ] `clear()` removes all entries

**Manual:**
- [ ] Remove operations are atomic
- [ ] No orphaned references after removal (future: search index cleanup)
