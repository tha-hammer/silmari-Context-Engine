# Phase 01: EntryType Enum

## Behavior

Define the `EntryType` enum for categorizing context entries.

### Test Specification

**Given**: Valid entry type strings
**When**: Convert to EntryType enum
**Then**: Returns correct enum value

**Given**: Invalid type string
**When**: Attempt to convert
**Then**: Raises ValueError

### Entry Types (from research)

| Type | Description |
|------|-------------|
| `file` | File content |
| `command` | Command invocation (removable) |
| `command_result` | Command result (retained) |
| `task` | Task description |
| `task_result` | Task execution result |
| `search_result` | Search/grep result |
| `summary` | Compressed summary |
| `context_request` | Worker request for more context |

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_models.py`

```python
"""Tests for context_window_array.models module."""

import pytest
from context_window_array.models import EntryType


class TestEntryType:
    """Behavior 1: EntryType enum defines valid context entry types."""

    def test_file_type_exists(self):
        """Given 'file' string, when accessed, then EntryType.FILE exists."""
        assert EntryType.FILE.value == "file"

    def test_command_type_exists(self):
        """Given 'command' string, when accessed, then EntryType.COMMAND exists."""
        assert EntryType.COMMAND.value == "command"

    def test_command_result_type_exists(self):
        """Given 'command_result' string, when accessed, then EntryType.COMMAND_RESULT exists."""
        assert EntryType.COMMAND_RESULT.value == "command_result"

    def test_task_type_exists(self):
        """Given 'task' string, when accessed, then EntryType.TASK exists."""
        assert EntryType.TASK.value == "task"

    def test_task_result_type_exists(self):
        """Given 'task_result' string, when accessed, then EntryType.TASK_RESULT exists."""
        assert EntryType.TASK_RESULT.value == "task_result"

    def test_search_result_type_exists(self):
        """Given 'search_result' string, when accessed, then EntryType.SEARCH_RESULT exists."""
        assert EntryType.SEARCH_RESULT.value == "search_result"

    def test_summary_type_exists(self):
        """Given 'summary' string, when accessed, then EntryType.SUMMARY exists."""
        assert EntryType.SUMMARY.value == "summary"

    def test_context_request_type_exists(self):
        """Given 'context_request' string, when accessed, then EntryType.CONTEXT_REQUEST exists."""
        assert EntryType.CONTEXT_REQUEST.value == "context_request"

    def test_from_string_valid(self):
        """Given valid type string, when from_string(), then returns enum."""
        assert EntryType.from_string("file") == EntryType.FILE
        assert EntryType.from_string("command") == EntryType.COMMAND
        assert EntryType.from_string("task_result") == EntryType.TASK_RESULT

    def test_from_string_invalid(self):
        """Given invalid type string, when from_string(), then raises ValueError."""
        with pytest.raises(ValueError, match="Invalid entry type"):
            EntryType.from_string("invalid_type")

    def test_all_types_have_string_values(self):
        """All EntryType members should have string values."""
        for entry_type in EntryType:
            assert isinstance(entry_type.value, str)
            assert len(entry_type.value) > 0
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_models.py::TestEntryType -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/models.py`

```python
"""Core data models for context window array architecture.

This module provides dataclasses and enums for representing context entries
in an addressable array structure.
"""

from enum import Enum


class EntryType(Enum):
    """Types of context entries in the store.

    Each type represents a different category of context:
    - FILE: File content from codebase
    - COMMAND: Command invocation (can be removed after execution)
    - COMMAND_RESULT: Result of command execution (retained)
    - TASK: Task description for implementation LLM
    - TASK_RESULT: Result from task execution
    - SEARCH_RESULT: Result from search/grep operations
    - SUMMARY: Compressed summary of other entries
    - CONTEXT_REQUEST: Worker request for additional context
    """

    FILE = "file"
    COMMAND = "command"
    COMMAND_RESULT = "command_result"
    TASK = "task"
    TASK_RESULT = "task_result"
    SEARCH_RESULT = "search_result"
    SUMMARY = "summary"
    CONTEXT_REQUEST = "context_request"

    @classmethod
    def from_string(cls, value: str) -> "EntryType":
        """Convert string to EntryType enum.

        Args:
            value: String representation of entry type

        Returns:
            Corresponding EntryType enum value

        Raises:
            ValueError: If value is not a valid entry type
        """
        for entry_type in cls:
            if entry_type.value == value:
                return entry_type
        valid_types = ", ".join(t.value for t in cls)
        raise ValueError(f"Invalid entry type '{value}'. Must be one of: {valid_types}")
```

**File**: `context_window_array/__init__.py`

```python
"""Context Window Array Architecture.

Provides addressable context management for separating working and
implementation LLMs.
"""

from context_window_array.models import EntryType

__all__ = ["EntryType"]
```

**File**: `context_window_array/tests/__init__.py`

```python
"""Tests for context_window_array module."""
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_models.py::TestEntryType -v
```

### 🔵 Refactor: Improve Code

No refactoring needed for this simple enum. The implementation is clean and follows Python conventions.

**Optional enhancement**: Add `__str__` method for better debugging:

```python
def __str__(self) -> str:
    return self.value
```

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): `pytest context_window_array/tests/test_models.py::TestEntryType -v` - ImportError or AttributeError
- [ ] Test passes (Green): `pytest context_window_array/tests/test_models.py::TestEntryType -v`
- [ ] All 8 entry types defined with correct string values
- [ ] `from_string()` converts valid strings to enum
- [ ] `from_string()` raises ValueError for invalid strings

**Manual:**
- [ ] Enum values match research document section 4
- [ ] Docstrings describe each type's purpose
