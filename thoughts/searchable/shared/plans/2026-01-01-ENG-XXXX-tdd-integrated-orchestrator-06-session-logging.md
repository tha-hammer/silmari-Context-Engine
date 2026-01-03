# Phase 6: Session Logging

## Overview

Implement `IntegratedOrchestrator.log_session()` method that writes session activity to `.agent/sessions/` directory, maintaining compatibility with existing session logging patterns.

## Dependencies

**Requires**: Phase 1-5 (complete orchestrator methods to log)
**Blocks**: Phase 8 (Integration)

## Changes Required

### Modify: `planning_pipeline/integrated_orchestrator.py`

Add `log_session()` method.

```python
# planning_pipeline/integrated_orchestrator.py:200-250
def log_session(
    self,
    session_id: str,
    action: str,
    result: dict[str, Any]
) -> None:
    """Log session activity to .agent/sessions/."""
    # Implementation here...
```

### Modify: `planning_pipeline/tests/test_integrated_orchestrator.py`

Add `TestSessionLogging` class.

```python
# planning_pipeline/tests/test_integrated_orchestrator.py:300-370
class TestSessionLogging:
    """Tests for session logging to .agent/sessions/."""
    # Test methods here...
```

## Test Specification

**Given**: Orchestrator operations occur
**When**: `log_session()` is called
**Then**: Logs are written to `.agent/sessions/` directory

### Test Cases

1. `test_logs_session_to_agent_sessions_directory` - Creates session log file
2. `test_creates_sessions_directory_if_missing` - Creates directory if it doesn't exist
3. `test_session_log_contains_required_fields` - Log contains timestamp, action, result

### Edge Cases

- Directory doesn't exist → create it
- Session file exists → append to it
- Invalid JSON in existing file → overwrite with new array

## Implementation

### Red Phase Test Code

```python
class TestSessionLogging:
    """Tests for session logging to .agent/sessions/."""

    def test_logs_session_to_agent_sessions_directory(self, tmp_path):
        """Given operation completes, logs to .agent/sessions/."""
        orchestrator = IntegratedOrchestrator(tmp_path)

        orchestrator.log_session(
            session_id="test-session-001",
            action="get_next_feature",
            result={"feature_id": "phase-1"}
        )

        sessions_dir = tmp_path / ".agent" / "sessions"
        assert sessions_dir.exists()

        # Find session file
        session_files = list(sessions_dir.glob("*.json"))
        assert len(session_files) >= 1

    def test_creates_sessions_directory_if_missing(self, tmp_path):
        """Given .agent/sessions/ doesn't exist, creates it."""
        orchestrator = IntegratedOrchestrator(tmp_path)

        sessions_dir = tmp_path / ".agent" / "sessions"
        assert not sessions_dir.exists()

        orchestrator.log_session(
            session_id="new-session",
            action="init",
            result={}
        )

        assert sessions_dir.exists()

    def test_session_log_contains_required_fields(self, tmp_path):
        """Given log is written, contains timestamp, action, result."""
        orchestrator = IntegratedOrchestrator(tmp_path)

        orchestrator.log_session(
            session_id="detail-session",
            action="sync",
            result={"synced": True}
        )

        sessions_dir = tmp_path / ".agent" / "sessions"
        session_file = list(sessions_dir.glob("*.json"))[0]

        import json
        content = json.loads(session_file.read_text())

        # Content is a list of log entries
        assert isinstance(content, list)
        assert len(content) == 1

        entry = content[0]
        assert "timestamp" in entry
        assert "action" in entry
        assert entry["action"] == "sync"
        assert "result" in entry
```

### Green Phase Implementation

```python
def log_session(
    self,
    session_id: str,
    action: str,
    result: dict[str, Any]
) -> None:
    """Log session activity to .agent/sessions/.

    Args:
        session_id: Unique session identifier
        action: Action performed (e.g., "get_next_feature")
        result: Result dictionary from the action
    """
    from datetime import datetime

    sessions_dir = self.project_path / ".agent" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "session_id": session_id,
        "action": action,
        "result": result
    }

    # Write to session-specific file
    session_file = sessions_dir / f"{session_id}.json"

    # Append to existing or create new
    existing = []
    if session_file.exists():
        try:
            existing = json.loads(session_file.read_text())
            if not isinstance(existing, list):
                existing = [existing]
        except json.JSONDecodeError:
            existing = []

    existing.append(log_entry)
    session_file.write_text(json.dumps(existing, indent=2))
```

## Success Criteria

### Automated

- [ ] Test fails for right reason (Red): `pytest planning_pipeline/tests/test_integrated_orchestrator.py::TestSessionLogging -v`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_integrated_orchestrator.py::TestSessionLogging -v`
- [ ] All tests pass: `pytest planning_pipeline/tests/`

### Manual (Human-Testable)

Run from project root:

```bash
python -c "
from pathlib import Path
from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

orchestrator = IntegratedOrchestrator(Path('.'))
orchestrator.log_session(
    session_id='manual-test-001',
    action='test_action',
    result={'test': True}
)
print('Session logged')
"
```

Then verify:
```bash
cat .agent/sessions/manual-test-001.json
```

**Expected**: JSON file with timestamp, session_id, action, and result fields

## References

- `.agent/sessions/` - Existing session logging location
- Session log format: JSON array of log entries
