# Phase 04: ContextEntry Serialization

## Behavior

Implement `to_dict()` and `from_dict()` methods for JSON serialization.

### Test Specification

**Given**: Entry with all fields
**When**: to_dict() called
**Then**: All fields serialized correctly (including datetime as ISO string)

**Given**: Dict with all fields
**When**: from_dict() called
**Then**: Entry reconstructed with correct types

**Given**: Entry
**When**: to_dict() → from_dict()
**Then**: Round-trips correctly (property-based test)

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_models.py`

```python
from hypothesis import given, strategies as st, settings


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
        from datetime import datetime

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
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_models.py::TestContextEntrySerialization -v
pytest context_window_array/tests/test_models.py::TestContextEntryPropertyBased -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/models.py` (add methods to ContextEntry)

```python
from typing import Any


@dataclass
class ContextEntry:
    # ... existing fields and __post_init__ ...

    def to_dict(self) -> dict[str, Any]:
        """Serialize entry to dictionary.

        Returns:
            Dictionary with all fields, datetime as ISO string, enum as string value.
        """
        return {
            "id": self.id,
            "entry_type": self.entry_type.value,
            "source": self.source,
            "content": self.content,
            "summary": self.summary,
            "created_at": self.created_at.isoformat(),
            "references": self.references,
            "searchable": self.searchable,
            "compressed": self.compressed,
            "ttl": self.ttl,
            "parent_id": self.parent_id,
            "derived_from": self.derived_from,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContextEntry":
        """Deserialize entry from dictionary.

        Args:
            data: Dictionary with entry fields

        Returns:
            Reconstructed ContextEntry
        """
        # Parse created_at if present
        created_at = None
        if "created_at" in data and data["created_at"]:
            created_at = datetime.fromisoformat(data["created_at"])

        # Parse entry_type from string
        entry_type = EntryType.from_string(data["entry_type"])

        return cls(
            id=data["id"],
            entry_type=entry_type,
            source=data["source"],
            content=data.get("content"),
            summary=data.get("summary"),
            created_at=created_at if created_at else datetime.now(),
            references=data.get("references", []),
            searchable=data.get("searchable", True),
            compressed=data.get("compressed", False),
            ttl=data.get("ttl"),
            parent_id=data.get("parent_id"),
            derived_from=data.get("derived_from", []),
        )
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_models.py::TestContextEntrySerialization -v
pytest context_window_array/tests/test_models.py::TestContextEntryPropertyBased -v
```

### 🔵 Refactor: Improve Code

The implementation is clean. Consider adding JSON schema validation in the future if needed.

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): AttributeError 'to_dict' or 'from_dict'
- [ ] Test passes (Green): All tests pass including property-based
- [ ] `to_dict()` serializes all fields correctly
- [ ] `from_dict()` reconstructs entry with correct types
- [ ] Round-trip preserves all data
- [ ] Property-based tests pass with 50 examples

**Manual:**
- [ ] JSON output is human-readable
- [ ] Datetime format is ISO 8601 compliant
