# Phase 02: ContextEntry Creation (Happy Path)

## Behavior

Create `ContextEntry` dataclass with all fields from research document section 4.

### Test Specification

**Given**: Valid parameters (id, type, content, summary)
**When**: ContextEntry created
**Then**: All fields populated correctly

**Given**: created_at not provided
**When**: ContextEntry created
**Then**: Defaults to current datetime

### Fields (from research)

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Unique identifier (ctx_001, ctx_002, ...) |
| `created_at` | datetime | Creation timestamp |
| `entry_type` | EntryType | Type of entry |
| `source` | str | Origin (file path, command, task_id) |
| `content` | Optional[str] | Full content (expandable) |
| `summary` | Optional[str] | Compressed summary |
| `references` | List[str] | References to other entry IDs |
| `searchable` | bool | Include in search index |
| `compressed` | bool | True if content removed |
| `ttl` | Optional[int] | Time-to-live in conversation turns |
| `parent_id` | Optional[str] | Parent entry if derived |
| `derived_from` | List[str] | Entry IDs this was derived from |

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_models.py`

```python
from datetime import datetime, timedelta
from context_window_array.models import ContextEntry, EntryType


class TestContextEntryCreation:
    """Behavior 2: ContextEntry creation with all fields."""

    def test_create_with_required_fields(self):
        """Given required fields, when created, then entry has all fields."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="src/main.py",
            content="def main(): pass",
            summary="Main entry point",
        )

        assert entry.id == "ctx_001"
        assert entry.entry_type == EntryType.FILE
        assert entry.source == "src/main.py"
        assert entry.content == "def main(): pass"
        assert entry.summary == "Main entry point"

    def test_created_at_defaults_to_now(self):
        """Given no created_at, when created, then defaults to current time."""
        before = datetime.now()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
        )
        after = datetime.now()

        assert before <= entry.created_at <= after

    def test_created_at_can_be_provided(self):
        """Given explicit created_at, when created, then uses provided value."""
        timestamp = datetime(2026, 1, 1, 12, 0, 0)
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            created_at=timestamp,
        )

        assert entry.created_at == timestamp

    def test_optional_fields_default_correctly(self):
        """Given only required fields, when created, then optionals have defaults."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
        )

        assert entry.references == []
        assert entry.searchable is True
        assert entry.compressed is False
        assert entry.ttl is None
        assert entry.parent_id is None
        assert entry.derived_from == []

    def test_create_with_all_fields(self):
        """Given all fields, when created, then all populated correctly."""
        timestamp = datetime(2026, 1, 1, 12, 0, 0)
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.COMMAND_RESULT,
            source="grep -rn 'class' src/",
            content="Found 50 matches...",
            summary="50 class definitions found",
            created_at=timestamp,
            references=["ctx_000"],
            searchable=True,
            compressed=False,
            ttl=5,
            parent_id="ctx_000",
            derived_from=["ctx_000"],
        )

        assert entry.id == "ctx_001"
        assert entry.entry_type == EntryType.COMMAND_RESULT
        assert entry.source == "grep -rn 'class' src/"
        assert entry.content == "Found 50 matches..."
        assert entry.summary == "50 class definitions found"
        assert entry.created_at == timestamp
        assert entry.references == ["ctx_000"]
        assert entry.searchable is True
        assert entry.compressed is False
        assert entry.ttl == 5
        assert entry.parent_id == "ctx_000"
        assert entry.derived_from == ["ctx_000"]

    def test_create_command_type(self):
        """Given COMMAND type, when created, then entry is command."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.COMMAND,
            source="bash",
            content="grep -rn 'class' src/",
            summary="Grep for class definitions",
        )

        assert entry.entry_type == EntryType.COMMAND

    def test_create_task_type(self):
        """Given TASK type, when created, then entry is task."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.TASK,
            source="orchestrator",
            content="Implement user authentication",
            summary="Auth implementation task",
        )

        assert entry.entry_type == EntryType.TASK

    def test_searchable_defaults_true(self):
        """Given no searchable param, when created, then defaults to True."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
        )

        assert entry.searchable is True

    def test_searchable_can_be_false(self):
        """Given searchable=False, when created, then entry not searchable."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.COMMAND,
            source="bash",
            content="ls -la",
            summary="List files",
            searchable=False,
        )

        assert entry.searchable is False
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_models.py::TestContextEntryCreation -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/models.py` (add to existing)

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ... EntryType enum from Phase 01 ...


@dataclass
class ContextEntry:
    """Single addressable entry in the context store.

    Represents a piece of context that can be stored, searched, compressed,
    and referenced by ID.

    Attributes:
        id: Unique identifier (format: ctx_XXX)
        entry_type: Type of context entry
        source: Origin (file path, command, task_id)
        content: Full content (can be None if compressed)
        summary: Compressed summary (always present after creation)
        created_at: Creation timestamp (defaults to now)
        references: List of referenced entry IDs
        searchable: Whether to include in search index
        compressed: True if content has been removed
        ttl: Time-to-live in conversation turns (None = no expiry)
        parent_id: ID of parent entry if derived
        derived_from: List of entry IDs this was derived from
    """

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
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_models.py::TestContextEntryCreation -v
```

### 🔵 Refactor: Improve Code

Add type hints and improve docstrings:

```python
@dataclass
class ContextEntry:
    """Single addressable entry in the context store.

    Represents a piece of context that can be stored, searched, compressed,
    and referenced by ID. Follows the Context Entry Schema from RLM research.

    Example:
        >>> entry = ContextEntry(
        ...     id="ctx_001",
        ...     entry_type=EntryType.FILE,
        ...     source="src/main.py",
        ...     content="def main(): pass",
        ...     summary="Main entry point function",
        ... )
        >>> entry.id
        'ctx_001'
    """
    # ... rest of implementation ...
```

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): `NameError: name 'ContextEntry' is not defined`
- [ ] Test passes (Green): All 9 tests pass
- [ ] `created_at` defaults to current datetime
- [ ] All optional fields have correct defaults
- [ ] All entry types can be used

**Manual:**
- [ ] Fields match research document section 4
- [ ] Dataclass is immutable-friendly (no post-init mutation of defaults)
