# Phase 03: ContextEntry Validation

## Behavior

Validate ContextEntry fields in `__post_init__` to ensure data integrity.

### Test Specification

**Given**: Empty id
**When**: ContextEntry created
**Then**: Raises ValueError

**Given**: Invalid entry type (not EntryType enum)
**When**: ContextEntry created
**Then**: Raises TypeError

**Given**: Both content and summary are None
**When**: ContextEntry created
**Then**: Raises ValueError

**Given**: Negative TTL
**When**: ContextEntry created
**Then**: Raises ValueError

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_models.py`

```python
class TestContextEntryValidation:
    """Behavior 3: ContextEntry validation in __post_init__."""

    def test_empty_id_raises_error(self):
        """Given empty id, when created, then raises ValueError."""
        with pytest.raises(ValueError, match="id must not be empty"):
            ContextEntry(
                id="",
                entry_type=EntryType.FILE,
                source="test.py",
                content="test",
                summary="test",
            )

    def test_whitespace_id_raises_error(self):
        """Given whitespace-only id, when created, then raises ValueError."""
        with pytest.raises(ValueError, match="id must not be empty"):
            ContextEntry(
                id="   ",
                entry_type=EntryType.FILE,
                source="test.py",
                content="test",
                summary="test",
            )

    def test_empty_source_raises_error(self):
        """Given empty source, when created, then raises ValueError."""
        with pytest.raises(ValueError, match="source must not be empty"):
            ContextEntry(
                id="ctx_001",
                entry_type=EntryType.FILE,
                source="",
                content="test",
                summary="test",
            )

    def test_content_and_summary_both_none_raises_error(self):
        """Given both content and summary None, when created, then raises ValueError."""
        with pytest.raises(ValueError, match="content or summary must be provided"):
            ContextEntry(
                id="ctx_001",
                entry_type=EntryType.FILE,
                source="test.py",
                content=None,
                summary=None,
            )

    def test_content_only_is_valid(self):
        """Given content but no summary, when created, then valid."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test content",
            summary=None,
        )
        assert entry.content == "test content"
        assert entry.summary is None

    def test_summary_only_is_valid(self):
        """Given summary but no content, when created, then valid (compressed state)."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content=None,
            summary="test summary",
        )
        assert entry.content is None
        assert entry.summary == "test summary"

    def test_negative_ttl_raises_error(self):
        """Given negative TTL, when created, then raises ValueError."""
        with pytest.raises(ValueError, match="ttl must be non-negative"):
            ContextEntry(
                id="ctx_001",
                entry_type=EntryType.FILE,
                source="test.py",
                content="test",
                summary="test",
                ttl=-1,
            )

    def test_zero_ttl_is_valid(self):
        """Given TTL of 0, when created, then valid (will expire on next turn)."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            ttl=0,
        )
        assert entry.ttl == 0

    def test_none_ttl_is_valid(self):
        """Given TTL of None, when created, then valid (no expiry)."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            ttl=None,
        )
        assert entry.ttl is None

    def test_invalid_parent_id_type_raises_error(self):
        """Given non-string parent_id, when created, then raises TypeError."""
        with pytest.raises(TypeError, match="parent_id must be a string"):
            ContextEntry(
                id="ctx_001",
                entry_type=EntryType.FILE,
                source="test.py",
                content="test",
                summary="test",
                parent_id=123,  # type: ignore
            )

    def test_empty_parent_id_is_valid(self):
        """Given empty string parent_id, when created, then treated as None."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            parent_id="",
        )
        # Empty string should be normalized to None
        assert entry.parent_id is None

    def test_references_must_be_list_of_strings(self):
        """Given references with non-string elements, when created, then raises TypeError."""
        with pytest.raises(TypeError, match="references must be list of strings"):
            ContextEntry(
                id="ctx_001",
                entry_type=EntryType.FILE,
                source="test.py",
                content="test",
                summary="test",
                references=[123, 456],  # type: ignore
            )

    def test_derived_from_must_be_list_of_strings(self):
        """Given derived_from with non-string elements, when created, then raises TypeError."""
        with pytest.raises(TypeError, match="derived_from must be list of strings"):
            ContextEntry(
                id="ctx_001",
                entry_type=EntryType.FILE,
                source="test.py",
                content="test",
                summary="test",
                derived_from=[123],  # type: ignore
            )
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_models.py::TestContextEntryValidation -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/models.py` (update ContextEntry)

```python
@dataclass
class ContextEntry:
    """Single addressable entry in the context store."""

    # Required fields
    id: str
    entry_type: EntryType
    source: str
    content: Optional[str]
    summary: Optional[str]

    # Optional fields with defaults
    created_at: datetime = field(default_factory=datetime.now)
    references: list[str] = field(default_factory=list)
    searchable: bool = True
    compressed: bool = False
    ttl: Optional[int] = None
    parent_id: Optional[str] = None
    derived_from: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate entry after initialization."""
        # Validate id
        if not self.id or not self.id.strip():
            raise ValueError("id must not be empty")

        # Validate source
        if not self.source or not self.source.strip():
            raise ValueError("source must not be empty")

        # Validate content/summary (at least one required)
        if self.content is None and self.summary is None:
            raise ValueError("At least one of content or summary must be provided")

        # Validate TTL
        if self.ttl is not None and self.ttl < 0:
            raise ValueError("ttl must be non-negative")

        # Validate parent_id type
        if self.parent_id is not None:
            if not isinstance(self.parent_id, str):
                raise TypeError("parent_id must be a string or None")
            # Normalize empty string to None
            if not self.parent_id.strip():
                object.__setattr__(self, "parent_id", None)

        # Validate references
        if self.references:
            if not all(isinstance(r, str) for r in self.references):
                raise TypeError("references must be list of strings")

        # Validate derived_from
        if self.derived_from:
            if not all(isinstance(d, str) for d in self.derived_from):
                raise TypeError("derived_from must be list of strings")
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_models.py::TestContextEntryValidation -v
```

### 🔵 Refactor: Improve Code

Extract validation into helper methods for clarity:

```python
def __post_init__(self):
    """Validate entry after initialization."""
    self._validate_id()
    self._validate_source()
    self._validate_content_or_summary()
    self._validate_ttl()
    self._validate_parent_id()
    self._validate_string_lists()

def _validate_id(self) -> None:
    if not self.id or not self.id.strip():
        raise ValueError("id must not be empty")

def _validate_source(self) -> None:
    if not self.source or not self.source.strip():
        raise ValueError("source must not be empty")

def _validate_content_or_summary(self) -> None:
    if self.content is None and self.summary is None:
        raise ValueError("At least one of content or summary must be provided")

def _validate_ttl(self) -> None:
    if self.ttl is not None and self.ttl < 0:
        raise ValueError("ttl must be non-negative")

def _validate_parent_id(self) -> None:
    if self.parent_id is not None:
        if not isinstance(self.parent_id, str):
            raise TypeError("parent_id must be a string or None")
        if not self.parent_id.strip():
            object.__setattr__(self, "parent_id", None)

def _validate_string_lists(self) -> None:
    if self.references and not all(isinstance(r, str) for r in self.references):
        raise TypeError("references must be list of strings")
    if self.derived_from and not all(isinstance(d, str) for d in self.derived_from):
        raise TypeError("derived_from must be list of strings")
```

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): No validation errors raised
- [ ] Test passes (Green): All 13 tests pass
- [ ] Empty/whitespace id raises ValueError
- [ ] Empty source raises ValueError
- [ ] Both content and summary None raises ValueError
- [ ] Negative TTL raises ValueError
- [ ] Invalid types for references/derived_from raise TypeError

**Manual:**
- [ ] Error messages are descriptive
- [ ] Validation is comprehensive but not overly strict
