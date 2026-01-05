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
