"""Tests for context_window_array.models module."""

from datetime import datetime

import pytest

from context_window_array.models import ContextEntry, EntryType


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
