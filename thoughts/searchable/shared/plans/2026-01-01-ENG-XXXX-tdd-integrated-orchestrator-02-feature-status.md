# Phase 2: Feature Status from Beads

## Overview

Implement `IntegratedOrchestrator.get_feature_status()` method that queries beads `bd list` commands to return feature counts (total, completed, remaining, blocked).

## Dependencies

**Requires**: Phase 7 (BeadsController Extensions) - needs `list_issues()` method
**Blocks**: Phase 5 (Phase Priority), Phase 8 (Integration)

## Changes Required

### Modify: `planning_pipeline/integrated_orchestrator.py`

Add `get_feature_status()` method.

```python
# planning_pipeline/integrated_orchestrator.py:60-100
def get_feature_status(self) -> dict[str, Any]:
    """Get feature status from beads issues."""
    # Implementation here...
```

### Modify: `planning_pipeline/tests/test_integrated_orchestrator.py`

Add `TestGetFeatureStatus` class.

```python
# planning_pipeline/tests/test_integrated_orchestrator.py:80-150
class TestGetFeatureStatus:
    """Tests for beads-based feature status."""
    # Test methods here...
```

## Test Specification

**Given**: Beads issues exist in the project
**When**: `get_feature_status()` is called
**Then**: Returns dict with total, completed, remaining, blocked counts from bd list

### Test Cases

1. `test_returns_status_from_beads_list` - Returns correct counts from beads
2. `test_returns_zeros_when_no_beads` - Returns zeros when bd not initialized
3. `test_correctly_identifies_blocked_by_open_dependencies` - Correctly counts blocked issues

### Edge Cases

- No beads initialized → return zeros
- bd command fails → return zeros
- Mixed status issues → correct counting
- Issues with unmet dependencies → counted as blocked

## Implementation

### Red Phase Test Code

```python
class TestGetFeatureStatus:
    """Tests for beads-based feature status."""

    def test_returns_status_from_beads_list(self, tmp_path):
        """Given beads issues exist, returns correct counts."""
        mock_all = {
            "success": True,
            "data": [
                {"id": "issue-1", "status": "open", "dependencies": []},
                {"id": "issue-2", "status": "closed", "dependencies": []},
                {"id": "issue-3", "status": "open", "dependencies": [{"depends_on_id": "issue-1"}]},
            ]
        }
        mock_open = {
            "success": True,
            "data": [
                {"id": "issue-1", "status": "open", "dependencies": []},
                {"id": "issue-3", "status": "open", "dependencies": [{"depends_on_id": "issue-1"}]},
            ]
        }
        mock_closed = {
            "success": True,
            "data": [{"id": "issue-2", "status": "closed", "dependencies": []}]
        }

        with patch.object(BeadsController, 'list_issues') as mock_list:
            mock_list.side_effect = [mock_all, mock_open, mock_closed]

            orchestrator = IntegratedOrchestrator(tmp_path)
            status = orchestrator.get_feature_status()

            assert status["total"] == 3
            assert status["completed"] == 1
            assert status["remaining"] == 2
            assert status["blocked"] == 1  # issue-3 blocked by issue-1
            assert len(status["features"]) == 3

    def test_returns_zeros_when_no_beads(self, tmp_path):
        """Given bd not initialized, returns zero counts."""
        with patch.object(BeadsController, 'list_issues') as mock_list:
            mock_list.return_value = {"success": False, "error": "Not initialized"}

            orchestrator = IntegratedOrchestrator(tmp_path)
            status = orchestrator.get_feature_status()

            assert status["total"] == 0
            assert status["completed"] == 0
            assert status["remaining"] == 0
            assert status["blocked"] == 0

    def test_correctly_identifies_blocked_by_open_dependencies(self, tmp_path):
        """Given issue depends on open issue, it's counted as blocked."""
        mock_all = {
            "success": True,
            "data": [
                {"id": "phase-1", "status": "open", "dependencies": []},
                {"id": "phase-2", "status": "open", "dependencies": [{"depends_on_id": "phase-1"}]},
                {"id": "phase-3", "status": "open", "dependencies": [{"depends_on_id": "phase-2"}]},
            ]
        }

        with patch.object(BeadsController, 'list_issues') as mock_list:
            mock_list.side_effect = [mock_all, mock_all, {"success": True, "data": []}]

            orchestrator = IntegratedOrchestrator(tmp_path)
            status = orchestrator.get_feature_status()

            # phase-2 blocked by phase-1, phase-3 blocked by phase-2
            assert status["blocked"] == 2
```

### Green Phase Implementation

```python
def get_feature_status(self) -> dict[str, Any]:
    """Get feature status from beads issues."""
    all_result = self.bd.list_issues()
    open_result = self.bd.list_issues(status="open")
    closed_result = self.bd.list_issues(status="closed")

    if not all_result["success"]:
        return {"total": 0, "completed": 0, "remaining": 0, "blocked": 0, "features": []}

    all_issues = all_result.get("data", [])
    open_issues = open_result.get("data", []) if open_result["success"] else []
    closed_issues = closed_result.get("data", []) if closed_result["success"] else []

    # Build set of open issue IDs for dependency checking
    open_ids = {issue["id"] for issue in open_issues}

    # Count blocked: issues with any open dependency
    blocked = 0
    for issue in all_issues:
        for dep in issue.get("dependencies", []):
            if dep.get("depends_on_id") in open_ids:
                blocked += 1
                break

    return {
        "total": len(all_issues),
        "completed": len(closed_issues),
        "remaining": len(open_issues),
        "blocked": blocked,
        "features": all_issues
    }
```

## Success Criteria

### Automated

- [ ] Test fails for right reason (Red): `pytest planning_pipeline/tests/test_integrated_orchestrator.py::TestGetFeatureStatus -v`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_integrated_orchestrator.py::TestGetFeatureStatus -v`
- [ ] All tests pass: `pytest planning_pipeline/tests/`

### Manual (Human-Testable)

Run from project root (requires beads initialized with issues):

```bash
python -c "
from pathlib import Path
from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

orchestrator = IntegratedOrchestrator(Path('.'))
status = orchestrator.get_feature_status()
print(f'Total: {status[\"total\"]}')
print(f'Completed: {status[\"completed\"]}')
print(f'Remaining: {status[\"remaining\"]}')
print(f'Blocked: {status[\"blocked\"]}')
"
```

**Expected**: Returns accurate counts matching `bd list` output

## References

- `planning_pipeline/beads_controller.py:52-65` - list_issues method
- `orchestrator.py:421-444` - Original get_feature_status function
