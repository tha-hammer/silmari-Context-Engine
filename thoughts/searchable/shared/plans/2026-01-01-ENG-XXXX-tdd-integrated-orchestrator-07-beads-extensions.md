# Phase 7: BeadsController Extensions

## Overview

Extend `BeadsController` with additional helper methods: `get_ready_issue()`, `update_status()`, and `show_issue()`. These methods are required by the IntegratedOrchestrator.

## Dependencies

**Requires**: None (can run in parallel with Phase 1)
**Blocks**: Phase 2, 3, 4 (all methods that use BeadsController)

## Changes Required

### Modify: `planning_pipeline/beads_controller.py`

Add new methods to BeadsController class.

```python
# planning_pipeline/beads_controller.py:91-120
def get_ready_issue(self, limit: int = 1) -> dict[str, Any]:
    """Get next ready issue (no blockers, dependencies met)."""
    # Implementation here...

def update_status(self, issue_id: str, status: str) -> dict[str, Any]:
    """Update issue status."""
    # Implementation here...

def show_issue(self, issue_id: str) -> dict[str, Any]:
    """Get full issue details."""
    # Implementation here...
```

### New File: `planning_pipeline/tests/test_beads_controller.py`

Create test file with `TestBeadsControllerExtensions` class.

```python
# planning_pipeline/tests/test_beads_controller.py:1-60
import pytest
from unittest.mock import patch
from planning_pipeline.beads_controller import BeadsController


class TestBeadsControllerExtensions:
    """Tests for new BeadsController methods."""
    # Test methods here...
```

## Test Specification

**Given**: BeadsController needs additional methods
**When**: `get_ready_issue()`, `update_status()`, and `show_issue()` are called
**Then**: They execute correct bd CLI commands

### Test Cases

1. `test_get_ready_issue_calls_bd_ready` - Calls `bd ready --limit=N`
2. `test_update_status_calls_bd_update` - Calls `bd update <id> --status=<status>`
3. `test_show_issue_calls_bd_show` - Calls `bd show <id>`

### Edge Cases

- bd command fails → return error result
- bd returns empty data → return empty result

## Implementation

### Red Phase Test Code

```python
import pytest
from unittest.mock import patch
from planning_pipeline.beads_controller import BeadsController


class TestBeadsControllerExtensions:
    """Tests for new BeadsController methods."""

    def test_get_ready_issue_calls_bd_ready(self, tmp_path):
        """Given bd ready works, returns ready issue."""
        mock_result = {
            "success": True,
            "data": [{"id": "ready-1", "title": "Ready Issue"}]
        }

        with patch.object(BeadsController, '_run_bd', return_value=mock_result) as mock_bd:
            bd = BeadsController(tmp_path)
            result = bd.get_ready_issue(limit=1)

            mock_bd.assert_called_with('ready', '--limit=1')
            assert result["success"]
            assert result["data"][0]["id"] == "ready-1"

    def test_update_status_calls_bd_update(self, tmp_path):
        """Given issue id and status, calls bd update."""
        mock_result = {"success": True, "data": {"id": "issue-1", "status": "in_progress"}}

        with patch.object(BeadsController, '_run_bd', return_value=mock_result) as mock_bd:
            bd = BeadsController(tmp_path)
            result = bd.update_status("issue-1", "in_progress")

            mock_bd.assert_called_with('update', 'issue-1', '--status=in_progress')
            assert result["success"]

    def test_show_issue_calls_bd_show(self, tmp_path):
        """Given issue id, calls bd show."""
        mock_result = {"success": True, "data": {"id": "issue-1", "title": "Test", "description": "..."}}

        with patch.object(BeadsController, '_run_bd', return_value=mock_result) as mock_bd:
            bd = BeadsController(tmp_path)
            result = bd.show_issue("issue-1")

            mock_bd.assert_called_with('show', 'issue-1')
            assert result["success"]
```

### Green Phase Implementation

```python
def get_ready_issue(self, limit: int = 1) -> dict[str, Any]:
    """Get next ready issue (no blockers, dependencies met)."""
    return self._run_bd('ready', f'--limit={limit}')

def update_status(self, issue_id: str, status: str) -> dict[str, Any]:
    """Update issue status."""
    return self._run_bd('update', issue_id, f'--status={status}')

def show_issue(self, issue_id: str) -> dict[str, Any]:
    """Get full issue details."""
    return self._run_bd('show', issue_id)
```

## Success Criteria

### Automated

- [ ] Test fails for right reason (Red): `pytest planning_pipeline/tests/test_beads_controller.py::TestBeadsControllerExtensions -v`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_beads_controller.py::TestBeadsControllerExtensions -v`
- [ ] Existing tests still pass: `pytest planning_pipeline/tests/`

### Manual (Human-Testable)

Run from project root (requires beads initialized with issues):

```bash
python -c "
from pathlib import Path
from planning_pipeline.beads_controller import BeadsController

bd = BeadsController(Path('.'))

# Test get_ready_issue
ready = bd.get_ready_issue(limit=1)
print(f'Ready issue: {ready}')

# Test show_issue (if we have an issue ID)
if ready.get('success') and ready.get('data'):
    issue_id = ready['data'][0]['id'] if isinstance(ready['data'], list) else ready['data']['id']
    details = bd.show_issue(issue_id)
    print(f'Issue details: {details}')
"
```

**Expected**: Methods work correctly with real bd CLI commands

## References

- `planning_pipeline/beads_controller.py:9-91` - Existing BeadsController class
- `planning_pipeline/beads_controller.py:20-50` - _run_bd method pattern
