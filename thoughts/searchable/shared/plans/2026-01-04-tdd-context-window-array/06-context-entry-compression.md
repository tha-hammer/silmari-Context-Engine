# Phase 06: ContextEntry Compression State

## Behavior

Implement compression state management for entries (compress content, retain summary).

### Test Specification

**Given**: Entry with content
**When**: compress() called
**Then**: content=None, compressed=True, summary retained

**Given**: Compressed entry
**When**: attempt to access full content
**Then**: Raises ContextCompressedError

**Given**: Entry without summary
**When**: compress() called
**Then**: Raises ValueError (cannot compress without summary)

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_models.py`

```python
from context_window_array.exceptions import ContextCompressedError


class TestContextEntryCompression:
    """Behavior 6: ContextEntry compression state management."""

    def test_compress_removes_content(self):
        """Given entry with content, when compress(), then content is None."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def main(): pass",
            summary="Main function",
        )

        entry.compress()

        assert entry.content is None

    def test_compress_sets_compressed_flag(self):
        """Given entry, when compress(), then compressed=True."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def main(): pass",
            summary="Main function",
        )

        entry.compress()

        assert entry.compressed is True

    def test_compress_retains_summary(self):
        """Given entry with summary, when compress(), then summary retained."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def main(): pass",
            summary="Main function",
        )

        entry.compress()

        assert entry.summary == "Main function"

    def test_compress_without_summary_raises_error(self):
        """Given entry without summary, when compress(), then raises ValueError."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def main(): pass",
            summary=None,
        )

        with pytest.raises(ValueError, match="Cannot compress entry without summary"):
            entry.compress()

    def test_compress_already_compressed_is_noop(self):
        """Given already compressed entry, when compress(), then no error."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content=None,
            summary="Main function",
            compressed=True,
        )

        entry.compress()  # Should not raise

        assert entry.compressed is True
        assert entry.content is None

    def test_is_compressed_when_compressed(self):
        """Given compressed entry, when is_compressed(), then returns True."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content=None,
            summary="Main function",
            compressed=True,
        )

        assert entry.is_compressed() is True

    def test_is_compressed_when_not_compressed(self):
        """Given entry with content, when is_compressed(), then returns False."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def main(): pass",
            summary="Main function",
            compressed=False,
        )

        assert entry.is_compressed() is False

    def test_get_content_when_not_compressed(self):
        """Given entry with content, when get_content(), then returns content."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def main(): pass",
            summary="Main function",
        )

        assert entry.get_content() == "def main(): pass"

    def test_get_content_when_compressed_raises_error(self):
        """Given compressed entry, when get_content(), then raises ContextCompressedError."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content=None,
            summary="Main function",
            compressed=True,
        )

        with pytest.raises(ContextCompressedError, match="Entry ctx_001 is compressed"):
            entry.get_content()

    def test_get_content_or_summary_when_not_compressed(self):
        """Given entry with content, when get_content_or_summary(), then returns content."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def main(): pass",
            summary="Main function",
        )

        assert entry.get_content_or_summary() == "def main(): pass"

    def test_get_content_or_summary_when_compressed(self):
        """Given compressed entry, when get_content_or_summary(), then returns summary."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content=None,
            summary="Main function",
            compressed=True,
        )

        assert entry.get_content_or_summary() == "Main function"

    def test_can_compress_with_content_and_summary(self):
        """Given entry with both content and summary, when can_compress(), then True."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def main(): pass",
            summary="Main function",
        )

        assert entry.can_compress() is True

    def test_cannot_compress_without_summary(self):
        """Given entry without summary, when can_compress(), then False."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def main(): pass",
            summary=None,
        )

        assert entry.can_compress() is False

    def test_cannot_compress_already_compressed(self):
        """Given already compressed entry, when can_compress(), then False."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content=None,
            summary="Main function",
            compressed=True,
        )

        assert entry.can_compress() is False

    def test_set_summary(self):
        """Given entry, when set_summary(new), then summary updated."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def main(): pass",
            summary="Old summary",
        )

        entry.set_summary("New summary")

        assert entry.summary == "New summary"

    def test_set_summary_empty_raises_error(self):
        """Given entry, when set_summary(''), then raises ValueError."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def main(): pass",
            summary="Old summary",
        )

        with pytest.raises(ValueError, match="Summary must not be empty"):
            entry.set_summary("")
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_models.py::TestContextEntryCompression -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/exceptions.py`

```python
"""Custom exceptions for context window array module."""


class ContextWindowArrayError(Exception):
    """Base exception for context window array module."""

    pass


class ContextCompressedError(ContextWindowArrayError):
    """Raised when attempting to access content of a compressed entry."""

    def __init__(self, entry_id: str):
        self.entry_id = entry_id
        super().__init__(f"Entry {entry_id} is compressed; content is not available")
```

**File**: `context_window_array/models.py` (add methods to ContextEntry)

```python
from context_window_array.exceptions import ContextCompressedError


@dataclass
class ContextEntry:
    # ... existing fields and methods ...

    def compress(self) -> None:
        """Compress entry by removing content and retaining summary.

        Raises:
            ValueError: If entry has no summary to retain
        """
        if self.compressed:
            return  # Already compressed, no-op

        if self.summary is None:
            raise ValueError("Cannot compress entry without summary")

        object.__setattr__(self, "content", None)
        object.__setattr__(self, "compressed", True)

    def is_compressed(self) -> bool:
        """Check if entry is compressed.

        Returns:
            True if compressed flag is set, False otherwise.
        """
        return self.compressed

    def get_content(self) -> str:
        """Get full content of entry.

        Returns:
            Content string

        Raises:
            ContextCompressedError: If entry is compressed
        """
        if self.compressed:
            raise ContextCompressedError(self.id)
        return self.content  # type: ignore

    def get_content_or_summary(self) -> str:
        """Get content if available, otherwise summary.

        Returns:
            Content if not compressed, summary otherwise.
        """
        if self.content is not None:
            return self.content
        return self.summary  # type: ignore

    def can_compress(self) -> bool:
        """Check if entry can be compressed.

        Returns:
            True if entry has content, summary, and is not already compressed.
        """
        return (
            not self.compressed
            and self.content is not None
            and self.summary is not None
        )

    def set_summary(self, summary: str) -> None:
        """Set the summary value.

        Args:
            summary: New summary text

        Raises:
            ValueError: If summary is empty
        """
        if not summary or not summary.strip():
            raise ValueError("Summary must not be empty")
        object.__setattr__(self, "summary", summary)
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_models.py::TestContextEntryCompression -v
```

### 🔵 Refactor: Improve Code

Update `__init__.py` to export the new exception:

```python
"""Context Window Array Architecture."""

from context_window_array.models import ContextEntry, EntryType
from context_window_array.exceptions import ContextCompressedError, ContextWindowArrayError

__all__ = [
    "ContextEntry",
    "EntryType",
    "ContextCompressedError",
    "ContextWindowArrayError",
]
```

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): ImportError or AttributeError
- [ ] Test passes (Green): All 16 tests pass
- [ ] `compress()` removes content and sets compressed flag
- [ ] `compress()` without summary raises ValueError
- [ ] `get_content()` raises ContextCompressedError when compressed
- [ ] `get_content_or_summary()` returns fallback gracefully
- [ ] `can_compress()` correctly identifies compressible entries

**Manual:**
- [ ] Compression behavior matches research document section 5
- [ ] Exception messages are clear and helpful
