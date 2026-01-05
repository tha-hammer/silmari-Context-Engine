# Phase 18: Entry Bounds Validation

## Behavior

Enforce <200 entry limit for implementation LLM contexts.

### Test Specification

**Given**: Implementation context
**When**: build() with >200 entries
**Then**: Raises EntryBoundsError

**Given**: Implementation context
**When**: validate_bounds(entry_ids)
**Then**: Returns True if <= 200, False otherwise

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_implementation_context.py`

```python
from context_window_array.exceptions import EntryBoundsError


class TestEntryBoundsValidation:
    """Behavior 18: Entry bounds validation for implementation context."""

    def test_build_exceeding_bounds_raises_error(self):
        """Given >200 entries, when build(), then raises EntryBoundsError."""
        store = CentralContextStore()
        # Add 201 entries
        for i in range(201):
            store.add(ContextEntry(
                id=f"ctx_{i:03d}",
                entry_type=EntryType.FILE,
                source=f"file{i}.py",
                content=f"content {i}",
                summary=f"summary {i}",
            ))

        context = ImplementationLLMContext(store)
        entry_ids = [f"ctx_{i:03d}" for i in range(201)]

        with pytest.raises(EntryBoundsError) as exc_info:
            context.build(entry_ids)

        assert "201" in str(exc_info.value)
        assert "200" in str(exc_info.value)

    def test_build_at_bounds_succeeds(self):
        """Given exactly 200 entries, when build(), then succeeds."""
        store = CentralContextStore()
        for i in range(200):
            store.add(ContextEntry(
                id=f"ctx_{i:03d}",
                entry_type=EntryType.FILE,
                source=f"file{i}.py",
                content=f"content {i}",
                summary=f"summary {i}",
            ))

        context = ImplementationLLMContext(store)
        entry_ids = [f"ctx_{i:03d}" for i in range(200)]

        # Should not raise
        result = context.build(entry_ids)
        assert result.entry_count == 200

    def test_build_under_bounds_succeeds(self):
        """Given <200 entries, when build(), then succeeds."""
        store = CentralContextStore()
        for i in range(50):
            store.add(ContextEntry(
                id=f"ctx_{i:03d}",
                entry_type=EntryType.FILE,
                source=f"file{i}.py",
                content=f"content {i}",
                summary=f"summary {i}",
            ))

        context = ImplementationLLMContext(store)
        entry_ids = [f"ctx_{i:03d}" for i in range(50)]

        result = context.build(entry_ids)
        assert result.entry_count == 50

    def test_validate_bounds_under_limit(self):
        """Given <200 entries, when validate_bounds(), then returns True."""
        store = CentralContextStore()
        context = ImplementationLLMContext(store)

        entry_ids = [f"ctx_{i:03d}" for i in range(100)]
        is_valid = context.validate_bounds(entry_ids)

        assert is_valid is True

    def test_validate_bounds_at_limit(self):
        """Given exactly 200 entries, when validate_bounds(), then returns True."""
        store = CentralContextStore()
        context = ImplementationLLMContext(store)

        entry_ids = [f"ctx_{i:03d}" for i in range(200)]
        is_valid = context.validate_bounds(entry_ids)

        assert is_valid is True

    def test_validate_bounds_over_limit(self):
        """Given >200 entries, when validate_bounds(), then returns False."""
        store = CentralContextStore()
        context = ImplementationLLMContext(store)

        entry_ids = [f"ctx_{i:03d}" for i in range(201)]
        is_valid = context.validate_bounds(entry_ids)

        assert is_valid is False

    def test_validate_bounds_empty_list(self):
        """Given empty list, when validate_bounds(), then returns True."""
        store = CentralContextStore()
        context = ImplementationLLMContext(store)

        is_valid = context.validate_bounds([])
        assert is_valid is True

    def test_build_skip_validation_flag(self):
        """Given >200 entries, when build(skip_validation=True), then succeeds."""
        store = CentralContextStore()
        for i in range(250):
            store.add(ContextEntry(
                id=f"ctx_{i:03d}",
                entry_type=EntryType.FILE,
                source=f"file{i}.py",
                content=f"content {i}",
                summary=f"summary {i}",
            ))

        context = ImplementationLLMContext(store)
        entry_ids = [f"ctx_{i:03d}" for i in range(250)]

        # Should not raise with skip_validation
        result = context.build(entry_ids, skip_validation=True)
        assert result.entry_count == 250

    def test_custom_max_entries(self):
        """Given custom max_entries, when build with that limit exceeded, then raises."""
        store = CentralContextStore()
        for i in range(60):
            store.add(ContextEntry(
                id=f"ctx_{i:03d}",
                entry_type=EntryType.FILE,
                source=f"file{i}.py",
                content=f"content {i}",
                summary=f"summary {i}",
            ))

        context = ImplementationLLMContext(store, max_entries=50)
        entry_ids = [f"ctx_{i:03d}" for i in range(60)]

        with pytest.raises(EntryBoundsError):
            context.build(entry_ids)

    def test_get_bounds_info(self):
        """Given context, when get_bounds_info(), then returns limit info."""
        store = CentralContextStore()
        context = ImplementationLLMContext(store, max_entries=150)

        info = context.get_bounds_info()

        assert info["max_entries"] == 150
        assert "default" in info or info["max_entries"] == 150

    def test_entry_bounds_error_message(self):
        """Given bounds error, then message includes helpful info."""
        store = CentralContextStore()
        for i in range(210):
            store.add(ContextEntry(
                id=f"ctx_{i:03d}",
                entry_type=EntryType.FILE,
                source=f"file{i}.py",
                content=f"content {i}",
                summary=f"summary {i}",
            ))

        context = ImplementationLLMContext(store)
        entry_ids = [f"ctx_{i:03d}" for i in range(210)]

        with pytest.raises(EntryBoundsError) as exc_info:
            context.build(entry_ids)

        error = exc_info.value
        assert error.requested == 210
        assert error.max_allowed == 200
        assert "210" in str(error)
        assert "200" in str(error)

    def test_split_into_batches(self):
        """Given many entries, when split_into_batches(), then creates valid batches."""
        store = CentralContextStore()
        context = ImplementationLLMContext(store, max_entries=50)

        entry_ids = [f"ctx_{i:03d}" for i in range(120)]
        batches = context.split_into_batches(entry_ids)

        assert len(batches) == 3  # 50 + 50 + 20
        assert len(batches[0]) == 50
        assert len(batches[1]) == 50
        assert len(batches[2]) == 20
        assert all(context.validate_bounds(batch) for batch in batches)
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_implementation_context.py::TestEntryBoundsValidation -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/exceptions.py` (add exception)

```python
"""Custom exceptions for context_window_array module."""


class ContextWindowArrayError(Exception):
    """Base exception for context window array errors."""
    pass


class ContextCompressedError(ContextWindowArrayError):
    """Raised when attempting to access content of a compressed entry."""
    pass


class EntryBoundsError(ContextWindowArrayError):
    """Raised when entry count exceeds allowed bounds.

    Attributes:
        requested: Number of entries requested
        max_allowed: Maximum entries allowed
    """
    def __init__(self, requested: int, max_allowed: int):
        self.requested = requested
        self.max_allowed = max_allowed
        super().__init__(
            f"Entry count {requested} exceeds maximum allowed {max_allowed}. "
            f"Consider splitting into batches or using skip_validation=True."
        )
```

**File**: `context_window_array/implementation_context.py` (update)

```python
from context_window_array.exceptions import EntryBoundsError

DEFAULT_MAX_ENTRIES = 200


class ImplementationLLMContext:
    """Builds context for implementation LLMs.

    Implementation LLMs need full content to perform detailed work
    like code writing, analysis, or debugging.

    Entry bounds (<200 by default) ensure context windows stay focused.
    """

    def __init__(
        self,
        store: CentralContextStore,
        max_entries: int = DEFAULT_MAX_ENTRIES,
    ):
        """Initialize with a context store.

        Args:
            store: The central context store
            max_entries: Maximum entries allowed per build (default: 200)
        """
        self._store = store
        self._max_entries = max_entries

    def validate_bounds(self, entry_ids: list[str]) -> bool:
        """Check if entry count is within bounds.

        Args:
            entry_ids: List of entry IDs to validate

        Returns:
            True if within bounds, False otherwise
        """
        return len(entry_ids) <= self._max_entries

    def get_bounds_info(self) -> dict:
        """Get information about entry bounds.

        Returns:
            Dictionary with max_entries and other limit info
        """
        return {
            "max_entries": self._max_entries,
            "default": self._max_entries == DEFAULT_MAX_ENTRIES,
        }

    def split_into_batches(self, entry_ids: list[str]) -> list[list[str]]:
        """Split entry IDs into valid batches.

        Args:
            entry_ids: List of entry IDs to split

        Returns:
            List of batches, each within bounds
        """
        batches = []
        for i in range(0, len(entry_ids), self._max_entries):
            batches.append(entry_ids[i:i + self._max_entries])
        return batches

    # ... existing _estimate_tokens and _entry_to_view methods ...

    def build(
        self,
        entry_ids: list[str],
        decompress: bool = False,
        skip_validation: bool = False,
    ) -> ImplementationContext:
        """Build context for an implementation LLM.

        Returns full content for requested entries.

        Args:
            entry_ids: IDs of entries to include
            decompress: If True, attempt to decompress entries
            skip_validation: If True, skip bounds validation

        Returns:
            ImplementationContext with full entry views

        Raises:
            EntryBoundsError: If entry count exceeds max_entries
        """
        # Validate bounds
        if not skip_validation and not self.validate_bounds(entry_ids):
            raise EntryBoundsError(
                requested=len(entry_ids),
                max_allowed=self._max_entries,
            )

        entries = []
        total_tokens = 0

        for entry_id in entry_ids:
            entry = self._store.get(entry_id)
            if entry is None:
                continue

            entries.append(self._entry_to_view(entry))
            total_tokens += self._estimate_tokens(entry)

        return ImplementationContext(
            entries=entries,
            entry_count=len(entries),
            total_tokens=total_tokens,
            entry_ids=[e.id for e in entries],
        )
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_implementation_context.py::TestEntryBoundsValidation -v
```

### 🔵 Refactor: Improve Code

Consider adding token-based bounds in addition to entry count.

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): AttributeError or missing EntryBoundsError
- [ ] Test passes (Green): All 12 tests pass
- [ ] `build()` raises EntryBoundsError when >200 entries
- [ ] `build()` succeeds at exactly 200 entries
- [ ] `validate_bounds()` returns correct boolean
- [ ] `split_into_batches()` creates valid batches
- [ ] `skip_validation=True` bypasses check
- [ ] Custom `max_entries` works

**Manual:**
- [ ] Error messages are helpful
- [ ] Batching splits entries correctly
