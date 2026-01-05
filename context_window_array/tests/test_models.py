"""Tests for context_window_array.models module."""

from datetime import datetime

import pytest
from hypothesis import given, settings, strategies as st

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


class TestContextEntrySerialization:
    """Behavior 4: ContextEntry serialization with to_dict/from_dict."""

    def test_to_dict_includes_all_fields(self):
        """Given entry with all fields, when to_dict(), then all fields present."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="src/main.py",
            content="def main(): pass",
            summary="Main function",
            references=["ctx_000"],
            searchable=True,
            compressed=False,
            ttl=5,
            parent_id="ctx_000",
            derived_from=["ctx_000"],
        )

        result = entry.to_dict()

        assert result["id"] == "ctx_001"
        assert result["entry_type"] == "file"  # Enum serialized as string
        assert result["source"] == "src/main.py"
        assert result["content"] == "def main(): pass"
        assert result["summary"] == "Main function"
        assert result["references"] == ["ctx_000"]
        assert result["searchable"] is True
        assert result["compressed"] is False
        assert result["ttl"] == 5
        assert result["parent_id"] == "ctx_000"
        assert result["derived_from"] == ["ctx_000"]
        assert "created_at" in result  # ISO format string

    def test_to_dict_datetime_is_iso_string(self):
        """Given entry, when to_dict(), then created_at is ISO format string."""
        timestamp = datetime(2026, 1, 4, 12, 0, 0)
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
            created_at=timestamp,
        )

        result = entry.to_dict()

        assert result["created_at"] == "2026-01-04T12:00:00"

    def test_to_dict_none_values_included(self):
        """Given entry with None values, when to_dict(), then None preserved."""
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content=None,
            summary="test",
            ttl=None,
            parent_id=None,
        )

        result = entry.to_dict()

        assert result["content"] is None
        assert result["ttl"] is None
        assert result["parent_id"] is None

    def test_from_dict_reconstructs_entry(self):
        """Given dict with all fields, when from_dict(), then entry reconstructed."""
        data = {
            "id": "ctx_001",
            "entry_type": "file",
            "source": "src/main.py",
            "content": "def main(): pass",
            "summary": "Main function",
            "created_at": "2026-01-04T12:00:00",
            "references": ["ctx_000"],
            "searchable": True,
            "compressed": False,
            "ttl": 5,
            "parent_id": "ctx_000",
            "derived_from": ["ctx_000"],
        }

        entry = ContextEntry.from_dict(data)

        assert entry.id == "ctx_001"
        assert entry.entry_type == EntryType.FILE
        assert entry.source == "src/main.py"
        assert entry.content == "def main(): pass"
        assert entry.summary == "Main function"
        assert entry.created_at == datetime(2026, 1, 4, 12, 0, 0)
        assert entry.references == ["ctx_000"]
        assert entry.searchable is True
        assert entry.compressed is False
        assert entry.ttl == 5
        assert entry.parent_id == "ctx_000"
        assert entry.derived_from == ["ctx_000"]

    def test_from_dict_with_minimal_fields(self):
        """Given dict with minimal fields, when from_dict(), then defaults applied."""
        data = {
            "id": "ctx_001",
            "entry_type": "file",
            "source": "test.py",
            "content": "test",
            "summary": "test",
        }

        entry = ContextEntry.from_dict(data)

        assert entry.id == "ctx_001"
        assert entry.references == []
        assert entry.searchable is True
        assert entry.compressed is False
        assert entry.ttl is None
        assert entry.parent_id is None
        assert entry.derived_from == []

    def test_from_dict_with_none_created_at(self):
        """Given dict without created_at, when from_dict(), then defaults to now."""
        data = {
            "id": "ctx_001",
            "entry_type": "file",
            "source": "test.py",
            "content": "test",
            "summary": "test",
        }

        before = datetime.now()
        entry = ContextEntry.from_dict(data)
        after = datetime.now()

        assert before <= entry.created_at <= after

    def test_round_trip_preserves_data(self):
        """Given entry, when to_dict -> from_dict, then data preserved."""
        original = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.COMMAND_RESULT,
            source="grep command",
            content="Found 50 matches",
            summary="50 matches",
            references=["ctx_000"],
            ttl=10,
            parent_id="ctx_000",
            derived_from=["ctx_000"],
        )

        data = original.to_dict()
        restored = ContextEntry.from_dict(data)

        assert restored.id == original.id
        assert restored.entry_type == original.entry_type
        assert restored.source == original.source
        assert restored.content == original.content
        assert restored.summary == original.summary
        assert restored.references == original.references
        assert restored.searchable == original.searchable
        assert restored.compressed == original.compressed
        assert restored.ttl == original.ttl
        assert restored.parent_id == original.parent_id
        assert restored.derived_from == original.derived_from


# Property-based test for round-trip
@st.composite
def context_entry_strategy(draw):
    """Generate arbitrary ContextEntry instances."""
    entry_types = list(EntryType)

    return {
        "id": draw(st.text(min_size=1, max_size=20).filter(lambda x: x.strip())),
        "entry_type": draw(st.sampled_from(entry_types)),
        "source": draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip())),
        "content": draw(st.one_of(st.none(), st.text(min_size=1, max_size=100))),
        "summary": draw(st.text(min_size=1, max_size=50)),  # Always have summary for valid entry
        "references": draw(st.lists(st.text(min_size=1, max_size=10), max_size=5)),
        "searchable": draw(st.booleans()),
        "compressed": draw(st.booleans()),
        "ttl": draw(st.one_of(st.none(), st.integers(min_value=0, max_value=100))),
        "parent_id": draw(st.one_of(st.none(), st.text(min_size=1, max_size=10))),
        "derived_from": draw(st.lists(st.text(min_size=1, max_size=10), max_size=3)),
    }


class TestContextEntryPropertyBased:
    """Property-based tests for ContextEntry serialization."""

    @given(context_entry_strategy())
    @settings(max_examples=50)
    def test_round_trip_serialization(self, data):
        """ContextEntry should round-trip through dict serialization."""
        # Skip invalid combinations
        if data["content"] is None and not data["summary"]:
            return

        entry = ContextEntry(
            id=data["id"],
            entry_type=data["entry_type"],
            source=data["source"],
            content=data["content"],
            summary=data["summary"],
            references=data["references"],
            searchable=data["searchable"],
            compressed=data["compressed"],
            ttl=data["ttl"],
            parent_id=data["parent_id"] if data["parent_id"] and data["parent_id"].strip() else None,
            derived_from=data["derived_from"],
        )

        as_dict = entry.to_dict()
        restored = ContextEntry.from_dict(as_dict)

        assert restored.id == entry.id
        assert restored.entry_type == entry.entry_type
        assert restored.source == entry.source
        assert restored.content == entry.content
        assert restored.summary == entry.summary
        assert restored.ttl == entry.ttl


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
