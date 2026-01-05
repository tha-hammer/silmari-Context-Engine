# Phase 11: Store TTL Processing

## Behavior

Implement TTL processing at the store level for batch operations.

### Test Specification

**Given**: Store with entries having TTL
**When**: process_ttl()
**Then**: All entry TTLs decremented

**Given**: Store with expired entries
**When**: cleanup_expired()
**Then**: Expired entries removed

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_store.py`

```python
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
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_store.py::TestStoreTTLProcessing -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/store.py` (add methods)

```python
class CentralContextStore:
    # ... existing methods ...

    def process_ttl(self) -> int:
        """Decrement TTL for all entries that have TTL set.

        Returns:
            Number of entries whose TTL was decremented
        """
        decremented = 0
        for entry in self._entries.values():
            if entry.has_ttl() and entry.ttl > 0:
                entry.decrement_ttl()
                decremented += 1
        return decremented

    def cleanup_expired(self) -> int:
        """Remove all expired entries (TTL = 0).

        Returns:
            Number of entries removed
        """
        expired_ids = [e.id for e in self._entries.values() if e.is_expired()]
        for entry_id in expired_ids:
            del self._entries[entry_id]
        return len(expired_ids)

    def get_expired(self) -> list[ContextEntry]:
        """Get all expired entries (TTL = 0).

        Returns:
            List of expired entries
        """
        return [e for e in self._entries.values() if e.is_expired()]

    def get_expiring_soon(self, threshold: int = 2) -> list[ContextEntry]:
        """Get entries that will expire soon.

        Args:
            threshold: TTL threshold (entries with TTL <= threshold)

        Returns:
            List of entries expiring soon
        """
        return [
            e for e in self._entries.values()
            if e.has_ttl() and e.ttl <= threshold
        ]

    def process_turn(self) -> dict[str, int]:
        """Process a conversation turn: decrement TTLs and cleanup expired.

        This should be called at the end of each conversation turn.

        Returns:
            Dictionary with 'decremented' and 'removed' counts
        """
        decremented = self.process_ttl()
        removed = self.cleanup_expired()
        return {"decremented": decremented, "removed": removed}

    def extend_ttl(self, entry_id: str, additional: int) -> bool:
        """Extend an entry's TTL.

        Args:
            entry_id: ID of entry to extend
            additional: Number of turns to add to TTL

        Returns:
            True if entry found and TTL extended, False if not found
        """
        entry = self.get(entry_id)
        if entry is None:
            return False

        if entry.ttl is None:
            entry.set_ttl(additional)
        else:
            entry.set_ttl(entry.ttl + additional)
        return True
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_store.py::TestStoreTTLProcessing -v
```

### 🔵 Refactor: Improve Code

Consider adding hooks for TTL events (on_expire, on_ttl_warning).

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): AttributeError for process_ttl
- [ ] Test passes (Green): All 12 tests pass
- [ ] `process_ttl()` decrements all TTLs
- [ ] `cleanup_expired()` removes TTL=0 entries
- [ ] `get_expired()` returns expired entries
- [ ] `get_expiring_soon()` filters by threshold
- [ ] `process_turn()` combines decrement and cleanup
- [ ] `extend_ttl()` increases TTL

**Manual:**
- [ ] TTL semantics match research expectations
- [ ] Cleanup is efficient (single pass where possible)
