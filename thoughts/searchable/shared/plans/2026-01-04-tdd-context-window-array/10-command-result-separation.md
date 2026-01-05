# Phase 10: Command/Result Separation

## Behavior

Implement command/result separation pattern: optionally discard commands while retaining results.

### Test Specification

**Given**: Command and result
**When**: add_command_result(keep_command=False)
**Then**: Only result stored, command discarded

**Given**: Command and result
**When**: add_command_result(keep_command=True)
**Then**: Both stored with parent_id link

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_store.py`

```python
class TestCommandResultSeparation:
    """Behavior 10: Command/result separation pattern."""

    def test_add_command_result_discards_command(self):
        """Given command and result, when add_command_result(keep_command=False), then only result stored."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="grep -rn 'class' src/",
            result="Found 50 matches:\n  src/main.py:10: class Main\n  ...",
            summary="50 class definitions found",
            keep_command=False,
        )

        # Result is stored
        result_entry = store.get(result_id)
        assert result_entry is not None
        assert result_entry.entry_type == EntryType.COMMAND_RESULT
        assert "50 matches" in result_entry.content
        assert result_entry.summary == "50 class definitions found"

        # No command entry exists (only 1 entry total)
        assert len(store) == 1

    def test_add_command_result_keeps_command(self):
        """Given command and result, when add_command_result(keep_command=True), then both stored."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="grep -rn 'class' src/",
            result="Found 50 matches:\n  src/main.py:10: class Main\n  ...",
            summary="50 class definitions found",
            keep_command=True,
        )

        # Both entries exist
        assert len(store) == 2

        # Result entry has parent_id pointing to command
        result_entry = store.get(result_id)
        assert result_entry is not None
        assert result_entry.parent_id is not None

        # Command entry exists
        command_entry = store.get(result_entry.parent_id)
        assert command_entry is not None
        assert command_entry.entry_type == EntryType.COMMAND
        assert command_entry.content == "grep -rn 'class' src/"

    def test_add_command_result_returns_result_id(self):
        """Given command and result, when add_command_result(), then returns result entry id."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="ls -la",
            result="total 100\ndrwxr-xr-x ...",
            summary="Directory listing",
            keep_command=False,
        )

        assert result_id.startswith("ctx_")
        assert store.contains(result_id)

    def test_add_command_result_generates_unique_ids(self):
        """Given multiple command results, when added, then unique IDs generated."""
        store = CentralContextStore()

        id1 = store.add_command_result(
            command="cmd1",
            result="result1",
            summary="summary1",
            keep_command=False,
        )
        id2 = store.add_command_result(
            command="cmd2",
            result="result2",
            summary="summary2",
            keep_command=False,
        )

        assert id1 != id2

    def test_add_command_result_with_source(self):
        """Given source parameter, when add_command_result(), then source set."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="npm test",
            result="All tests passed",
            summary="Tests passed",
            source="npm",
            keep_command=False,
        )

        result_entry = store.get(result_id)
        assert result_entry.source == "npm"

    def test_add_command_result_default_source(self):
        """Given no source parameter, when add_command_result(), then source is 'bash'."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="echo hello",
            result="hello",
            summary="Echo output",
            keep_command=False,
        )

        result_entry = store.get(result_id)
        assert result_entry.source == "bash"

    def test_add_command_result_command_not_searchable(self):
        """Given keep_command=True, when add_command_result(), then command is not searchable."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="grep pattern file",
            result="match found",
            summary="1 match",
            keep_command=True,
        )

        result_entry = store.get(result_id)
        command_entry = store.get(result_entry.parent_id)

        # Command should not be searchable (per research doc)
        assert command_entry.searchable is False
        # Result should be searchable
        assert result_entry.searchable is True

    def test_add_command_result_with_ttl(self):
        """Given ttl parameter, when add_command_result(), then result has TTL."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="ls",
            result="files",
            summary="file list",
            keep_command=False,
            ttl=5,
        )

        result_entry = store.get(result_id)
        assert result_entry.ttl == 5

    def test_remove_command_keeps_result(self):
        """Given command and result, when remove command, then result still accessible."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="grep pattern",
            result="match",
            summary="1 match",
            keep_command=True,
        )
        result_entry = store.get(result_id)
        command_id = result_entry.parent_id

        # Remove command
        store.remove(command_id)

        # Result still exists and accessible
        assert store.contains(result_id)
        result_after = store.get(result_id)
        assert result_after is not None
        assert result_after.content == "match"

    def test_compress_command_result_chain(self):
        """Given command and result, when compress result, then result compressed."""
        store = CentralContextStore()

        result_id = store.add_command_result(
            command="grep -rn 'def' src/",
            result="Found 100 function definitions...",
            summary="100 functions found",
            keep_command=True,
        )

        # Compress result
        store.compress(result_id)

        result_entry = store.get(result_id)
        assert result_entry.compressed is True
        assert result_entry.summary == "100 functions found"
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_store.py::TestCommandResultSeparation -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/store.py` (add method and ID generator)

```python
import uuid


class CentralContextStore:
    def __init__(self):
        """Initialize empty context store."""
        self._entries: dict[str, ContextEntry] = {}
        self._id_counter: int = 0

    def _generate_id(self) -> str:
        """Generate a unique entry ID."""
        self._id_counter += 1
        return f"ctx_{self._id_counter:06d}"

    # ... existing methods ...

    def add_command_result(
        self,
        command: str,
        result: str,
        summary: str,
        source: str = "bash",
        keep_command: bool = False,
        ttl: Optional[int] = None,
    ) -> str:
        """Add a command result, optionally discarding the command.

        This implements the command/result separation pattern from RLM:
        commands can be removed from context while their results are retained.

        Args:
            command: The command that was executed
            result: The output/result of the command
            summary: Summary of the result for compressed view
            source: Source identifier (default: "bash")
            keep_command: If True, store command entry; if False, discard
            ttl: Time-to-live for the result entry

        Returns:
            ID of the result entry
        """
        command_id = None

        if keep_command:
            # Create command entry (not searchable)
            command_id = self._generate_id()
            command_entry = ContextEntry(
                id=command_id,
                entry_type=EntryType.COMMAND,
                source=source,
                content=command,
                summary=f"Executed: {command[:50]}..." if len(command) > 50 else f"Executed: {command}",
                searchable=False,  # Commands not searchable
            )
            self.add(command_entry)

        # Create result entry
        result_id = self._generate_id()
        result_entry = ContextEntry(
            id=result_id,
            entry_type=EntryType.COMMAND_RESULT,
            source=source,
            content=result,
            summary=summary,
            parent_id=command_id,
            searchable=True,
            ttl=ttl,
        )
        self.add(result_entry)

        return result_id
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_store.py::TestCommandResultSeparation -v
```

### 🔵 Refactor: Improve Code

Consider adding a `derived_from` link as well for better lineage tracking.

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): AttributeError for add_command_result
- [ ] Test passes (Green): All 10 tests pass
- [ ] `keep_command=False` stores only result
- [ ] `keep_command=True` stores both with parent_id link
- [ ] Command entries are not searchable
- [ ] Result entries are searchable
- [ ] Unique IDs generated for each entry

**Manual:**
- [ ] Pattern matches research document section 5
- [ ] Removing command doesn't break result access
