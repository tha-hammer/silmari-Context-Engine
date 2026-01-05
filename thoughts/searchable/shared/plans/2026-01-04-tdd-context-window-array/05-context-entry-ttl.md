# Phase 05: ContextEntry TTL

## Behavior

Implement TTL (time-to-live) decrement and expiration checking for entries.

### Test Specification

**Given**: Entry with ttl=5
**When**: decrement_ttl() called
**Then**: ttl becomes 4

**Given**: Entry with ttl=0
**When**: is_expired() called
**Then**: Returns True

**Given**: Entry with ttl=None
**When**: is_expired() called
**Then**: Returns False (no expiry)

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_models.py`

```python
class TestContextEntryTTL:
    """Behavior 5: ContextEntry TTL management."""

    def test_decrement_ttl_reduces_by_one(self):
        """Given entry with ttl=5, when decrement_ttl(), then ttl becomes 4."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            ttl=5,
        )

        entry.decrement_ttl()

        assert entry.ttl == 4

    def test_decrement_ttl_multiple_times(self):
        """Given entry with ttl=3, when decrement_ttl() 3 times, then ttl becomes 0."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            ttl=3,
        )

        entry.decrement_ttl()
        entry.decrement_ttl()
        entry.decrement_ttl()

        assert entry.ttl == 0

    def test_decrement_ttl_at_zero_stays_zero(self):
        """Given entry with ttl=0, when decrement_ttl(), then ttl stays 0."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            ttl=0,
        )

        entry.decrement_ttl()

        assert entry.ttl == 0

    def test_decrement_ttl_with_none_is_noop(self):
        """Given entry with ttl=None, when decrement_ttl(), then ttl stays None."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            ttl=None,
        )

        entry.decrement_ttl()

        assert entry.ttl is None

    def test_is_expired_when_ttl_zero(self):
        """Given entry with ttl=0, when is_expired(), then returns True."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            ttl=0,
        )

        assert entry.is_expired() is True

    def test_is_expired_when_ttl_positive(self):
        """Given entry with ttl=5, when is_expired(), then returns False."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            ttl=5,
        )

        assert entry.is_expired() is False

    def test_is_expired_when_ttl_none(self):
        """Given entry with ttl=None, when is_expired(), then returns False (no expiry)."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            ttl=None,
        )

        assert entry.is_expired() is False

    def test_has_ttl_when_ttl_set(self):
        """Given entry with ttl=5, when has_ttl(), then returns True."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            ttl=5,
        )

        assert entry.has_ttl() is True

    def test_has_ttl_when_ttl_none(self):
        """Given entry with ttl=None, when has_ttl(), then returns False."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            ttl=None,
        )

        assert entry.has_ttl() is False

    def test_has_ttl_when_ttl_zero(self):
        """Given entry with ttl=0, when has_ttl(), then returns True (TTL is set, just expired)."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            ttl=0,
        )

        assert entry.has_ttl() is True

    def test_set_ttl(self):
        """Given entry, when set_ttl(10), then ttl becomes 10."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            ttl=None,
        )

        entry.set_ttl(10)

        assert entry.ttl == 10

    def test_set_ttl_to_none(self):
        """Given entry with ttl=5, when set_ttl(None), then ttl becomes None."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            ttl=5,
        )

        entry.set_ttl(None)

        assert entry.ttl is None

    def test_set_ttl_negative_raises_error(self):
        """Given entry, when set_ttl(-1), then raises ValueError."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            ttl=5,
        )

        with pytest.raises(ValueError, match="ttl must be non-negative"):
            entry.set_ttl(-1)
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_models.py::TestContextEntryTTL -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/models.py` (add methods to ContextEntry)

```python
@dataclass
class ContextEntry:
    # ... existing fields, __post_init__, to_dict, from_dict ...

    def decrement_ttl(self) -> None:
        """Decrement TTL by 1 if set and positive.

        If TTL is None, does nothing (no expiry).
        If TTL is 0, stays at 0.
        """
        if self.ttl is not None and self.ttl > 0:
            object.__setattr__(self, "ttl", self.ttl - 1)

    def is_expired(self) -> bool:
        """Check if entry has expired based on TTL.

        Returns:
            True if TTL is 0, False if TTL is None or positive.
        """
        return self.ttl == 0

    def has_ttl(self) -> bool:
        """Check if entry has a TTL set.

        Returns:
            True if TTL is not None (even if 0), False otherwise.
        """
        return self.ttl is not None

    def set_ttl(self, ttl: Optional[int]) -> None:
        """Set the TTL value.

        Args:
            ttl: New TTL value (None for no expiry, 0+ for turns until expiry)

        Raises:
            ValueError: If ttl is negative
        """
        if ttl is not None and ttl < 0:
            raise ValueError("ttl must be non-negative")
        object.__setattr__(self, "ttl", ttl)
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_models.py::TestContextEntryTTL -v
```

### 🔵 Refactor: Improve Code

The implementation is straightforward. Note the use of `object.__setattr__` to modify the dataclass field after creation (since dataclass may be frozen in the future).

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): AttributeError for missing methods
- [ ] Test passes (Green): All 13 tests pass
- [ ] `decrement_ttl()` reduces TTL by 1
- [ ] `decrement_ttl()` is no-op when TTL is None or 0
- [ ] `is_expired()` returns True only when TTL is 0
- [ ] `has_ttl()` returns True when TTL is not None
- [ ] `set_ttl()` validates non-negative value

**Manual:**
- [ ] TTL semantics match research document expectations
- [ ] Methods are side-effect safe (only modify TTL field)
