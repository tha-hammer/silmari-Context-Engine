# Phase 07: Store Add/Get

## Behavior

Implement basic CRUD operations for the CentralContextStore.

### Test Specification

**Given**: Empty store
**When**: add(entry)
**Then**: Entry retrievable by id

**Given**: Store with entry
**When**: get(id)
**Then**: Returns entry

**Given**: Store
**When**: get(nonexistent_id)
**Then**: Returns None

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_store.py`

```python
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
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_store.py::TestStoreAddGet -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/store.py`

```python
"""Central context store for managing addressable context entries."""

from typing import Optional
from context_window_array.models import ContextEntry, EntryType


class CentralContextStore:
    """Addressable context store with CRUD operations.

    Stores context entries by ID and provides operations for
    adding, retrieving, removing, and querying entries.

    Attributes:
        entries: Dictionary mapping entry IDs to ContextEntry objects
    """

    def __init__(self):
        """Initialize empty context store."""
        self._entries: dict[str, ContextEntry] = {}

    def add(self, entry: ContextEntry) -> str:
        """Add an entry to the store.

        Args:
            entry: ContextEntry to add

        Returns:
            The entry's ID

        Raises:
            ValueError: If an entry with the same ID already exists
        """
        if entry.id in self._entries:
            raise ValueError(f"Entry with id '{entry.id}' already exists")
        self._entries[entry.id] = entry
        return entry.id

    def get(self, entry_id: str) -> Optional[ContextEntry]:
        """Get an entry by ID.

        Args:
            entry_id: ID of entry to retrieve

        Returns:
            ContextEntry if found, None otherwise
        """
        return self._entries.get(entry_id)

    def contains(self, entry_id: str) -> bool:
        """Check if store contains an entry with the given ID.

        Args:
            entry_id: ID to check

        Returns:
            True if entry exists, False otherwise
        """
        return entry_id in self._entries

    def get_all(self) -> list[ContextEntry]:
        """Get all entries in the store.

        Returns:
            List of all ContextEntry objects
        """
        return list(self._entries.values())

    def get_by_type(self, entry_type: EntryType) -> list[ContextEntry]:
        """Get all entries of a specific type.

        Args:
            entry_type: EntryType to filter by

        Returns:
            List of entries matching the type
        """
        return [e for e in self._entries.values() if e.entry_type == entry_type]

    def __len__(self) -> int:
        """Return the number of entries in the store."""
        return len(self._entries)
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_store.py::TestStoreAddGet -v
```

### 🔵 Refactor: Improve Code

Add type hints and update `__init__.py`:

```python
# context_window_array/__init__.py
from context_window_array.models import ContextEntry, EntryType
from context_window_array.store import CentralContextStore
from context_window_array.exceptions import ContextCompressedError, ContextWindowArrayError

__all__ = [
    "ContextEntry",
    "EntryType",
    "CentralContextStore",
    "ContextCompressedError",
    "ContextWindowArrayError",
]
```

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): ImportError for CentralContextStore
- [ ] Test passes (Green): All 14 tests pass
- [ ] `add()` stores entry and returns ID
- [ ] `add()` raises ValueError for duplicate ID
- [ ] `get()` returns entry or None
- [ ] `contains()` checks existence
- [ ] `len()` returns entry count
- [ ] `get_all()` returns all entries
- [ ] `get_by_type()` filters by entry type

**Manual:**
- [ ] Store operations match research document section 8
- [ ] Thread safety considerations documented (future work)
