# Phase 19: Context Request

## Behavior

Request and retrieve entries from central store for implementation context.

## Exception Handling Guarantee

**The context manager guarantees release even on exception.**

The `request()` context manager uses a `finally` block to ensure entries are always released, regardless of whether the handler succeeds or raises an exception:

```python
@contextmanager
def request(
    self,
    entry_ids: list[str],
    skip_validation: bool = False,
) -> Generator[ImplementationContext, None, None]:
    """Context manager for requesting and auto-releasing entries.

    Guarantees:
    - Entries are marked in_use when context is entered
    - Entries are ALWAYS released when context exits (success or exception)
    - release_context() is called in finally block
    """
    result = self.request_context(entry_ids, skip_validation=skip_validation)
    try:
        yield result
    finally:
        # ALWAYS releases, even if handler raises exception
        self.release_context(result.entry_ids)
```

This guarantee prevents context leaks:
- If handler succeeds: entries released normally
- If handler raises exception: entries still released before exception propagates
- If request_context fails: no entries acquired, nothing to release

### Test Specification

**Given**: Working context with search results
**When**: request_context(entry_ids)
**Then**: Entries retrieved and marked as in-use

**Given**: Implementation context
**When**: release_context()
**Then**: Entries marked as available

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_implementation_context.py`

```python
class TestContextRequest:
    """Behavior 19: Context request and release operations."""

    def test_request_context_retrieves_entries(self):
        """Given entry ids, when request_context(), then entries retrieved."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="auth.py",
            content="auth code",
            summary="Auth",
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="db.py",
            content="db code",
            summary="DB",
        ))

        context = ImplementationLLMContext(store)
        result = context.request_context(["ctx_001", "ctx_002"])

        assert result.entry_count == 2
        assert "ctx_001" in result.entry_ids
        assert "ctx_002" in result.entry_ids

    def test_request_context_marks_in_use(self):
        """Given entry ids, when request_context(), then entries marked in_use."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="Test",
        ))

        context = ImplementationLLMContext(store)
        context.request_context(["ctx_001"])

        # Entry should be marked as in_use
        assert context.is_in_use("ctx_001") is True

    def test_request_context_tracks_active_entries(self):
        """Given multiple requests, when get_active_entries(), then returns all in_use."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b"))
        store.add(ContextEntry(id="ctx_003", entry_type=EntryType.FILE, source="c.py", content="c", summary="c"))

        context = ImplementationLLMContext(store)
        context.request_context(["ctx_001", "ctx_002"])

        active = context.get_active_entries()
        assert active == {"ctx_001", "ctx_002"}

    def test_release_context_clears_in_use(self):
        """Given in_use entries, when release_context(), then cleared."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="Test",
        ))

        context = ImplementationLLMContext(store)
        context.request_context(["ctx_001"])
        assert context.is_in_use("ctx_001") is True

        context.release_context()

        assert context.is_in_use("ctx_001") is False
        assert context.get_active_entries() == set()

    def test_release_specific_entries(self):
        """Given in_use entries, when release_context(entry_ids), then only those released."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b"))

        context = ImplementationLLMContext(store)
        context.request_context(["ctx_001", "ctx_002"])

        context.release_context(["ctx_001"])

        assert context.is_in_use("ctx_001") is False
        assert context.is_in_use("ctx_002") is True

    def test_request_already_in_use_extends_lease(self):
        """Given entry already in_use, when request_context(), then lease extended."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="Test",
        ))

        context = ImplementationLLMContext(store)
        context.request_context(["ctx_001"])
        context.request_context(["ctx_001"])  # Request again

        # Should still be in_use, not error
        assert context.is_in_use("ctx_001") is True

    def test_request_context_from_search(self):
        """Given search results, when request_context from results, then entries retrieved."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="auth.py",
            content="authentication login user",
            summary="Auth module",
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="db.py",
            content="database connection",
            summary="DB module",
        ))

        # First search to find relevant entries
        working = WorkingLLMContext(store)
        search_results = working.search("authentication login")

        # Then request those entries for implementation
        impl = ImplementationLLMContext(store)
        entry_ids = [r.id for r in search_results]
        result = impl.request_context(entry_ids)

        assert result.entry_count > 0
        # Should have full content now
        assert result.entries[0].content is not None

    def test_request_context_validates_bounds(self):
        """Given too many entries, when request_context(), then raises EntryBoundsError."""
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

        with pytest.raises(EntryBoundsError):
            context.request_context(entry_ids)

    def test_request_context_returns_context_object(self):
        """Given entry ids, when request_context(), then returns ImplementationContext."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="Test",
        ))

        context = ImplementationLLMContext(store)
        result = context.request_context(["ctx_001"])

        assert isinstance(result, ImplementationContext)
        assert hasattr(result, 'entries')
        assert hasattr(result, 'entry_count')
        assert hasattr(result, 'total_tokens')

    def test_get_usage_stats(self):
        """Given context with activity, when get_usage_stats(), then returns stats."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b"))

        context = ImplementationLLMContext(store)
        context.request_context(["ctx_001"])
        context.request_context(["ctx_002"])
        context.release_context(["ctx_001"])

        stats = context.get_usage_stats()

        assert stats["active_count"] == 1
        assert stats["total_requests"] == 2
        assert stats["total_releases"] == 1

    def test_context_manager_support(self):
        """Given implementation context, when used as context manager, then auto-releases."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="Test",
        ))

        context = ImplementationLLMContext(store)

        with context.request(["ctx_001"]) as result:
            assert result.entry_count == 1
            assert context.is_in_use("ctx_001") is True

        # After context manager exits, should be released
        assert context.is_in_use("ctx_001") is False
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_implementation_context.py::TestContextRequest -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/implementation_context.py` (add request/release methods)

```python
from contextlib import contextmanager
from typing import Generator


class ImplementationLLMContext:
    def __init__(
        self,
        store: CentralContextStore,
        max_entries: int = DEFAULT_MAX_ENTRIES,
    ):
        self._store = store
        self._max_entries = max_entries
        self._active_entries: set[str] = set()
        self._total_requests: int = 0
        self._total_releases: int = 0

    # ... existing methods ...

    def is_in_use(self, entry_id: str) -> bool:
        """Check if an entry is currently in use.

        Args:
            entry_id: ID of entry to check

        Returns:
            True if entry is in active use
        """
        return entry_id in self._active_entries

    def get_active_entries(self) -> set[str]:
        """Get all currently active entry IDs.

        Returns:
            Set of entry IDs currently in use
        """
        return self._active_entries.copy()

    def request_context(
        self,
        entry_ids: list[str],
        skip_validation: bool = False,
    ) -> ImplementationContext:
        """Request entries for implementation context.

        Marks entries as in-use and returns full content.

        Args:
            entry_ids: IDs of entries to request
            skip_validation: If True, skip bounds validation

        Returns:
            ImplementationContext with requested entries

        Raises:
            EntryBoundsError: If entry count exceeds max_entries
        """
        # Build validates bounds
        result = self.build(entry_ids, skip_validation=skip_validation)

        # Mark entries as in_use
        for entry_id in result.entry_ids:
            self._active_entries.add(entry_id)

        self._total_requests += len(result.entry_ids)

        return result

    def release_context(self, entry_ids: Optional[list[str]] = None) -> None:
        """Release entries from active use.

        Args:
            entry_ids: Specific entries to release, or None to release all
        """
        if entry_ids is None:
            released = len(self._active_entries)
            self._active_entries.clear()
        else:
            released = 0
            for entry_id in entry_ids:
                if entry_id in self._active_entries:
                    self._active_entries.discard(entry_id)
                    released += 1

        self._total_releases += released

    def get_usage_stats(self) -> dict:
        """Get usage statistics.

        Returns:
            Dictionary with usage stats
        """
        return {
            "active_count": len(self._active_entries),
            "total_requests": self._total_requests,
            "total_releases": self._total_releases,
        }

    @contextmanager
    def request(
        self,
        entry_ids: list[str],
        skip_validation: bool = False,
    ) -> Generator[ImplementationContext, None, None]:
        """Context manager for requesting and auto-releasing entries.

        Args:
            entry_ids: IDs of entries to request
            skip_validation: If True, skip bounds validation

        Yields:
            ImplementationContext with requested entries
        """
        result = self.request_context(entry_ids, skip_validation=skip_validation)
        try:
            yield result
        finally:
            self.release_context(result.entry_ids)
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_implementation_context.py::TestContextRequest -v
```

### 🔵 Refactor: Improve Code

Consider adding entry locking for concurrent access scenarios.

---

## Success Criteria

**Automated:**
- [x] Test fails for right reason (Red): AttributeError for request_context
- [x] Test passes (Green): All 12 tests pass (added test for exception release)
- [x] `request_context()` retrieves full content
- [x] `request_context()` marks entries as in_use
- [x] `release_context()` clears in_use status
- [x] `release_context(entry_ids)` releases specific entries
- [x] Context manager auto-releases
- [x] Usage stats tracked correctly

**Manual:**
- [x] Request/release workflow matches RLM paper pattern
- [x] Stats useful for debugging context management
