# Phase 3: Get Next Feature from bd ready

## Overview

Implement `IntegratedOrchestrator.get_next_feature()` method that returns the first issue from `bd ready` (issues with no blockers and all dependencies met).

## Dependencies

**Requires**: Phase 7 (BeadsController Extensions) - needs `get_ready_issue()` method
**Blocks**: Phase 5 (Phase Priority), Phase 8 (Integration)

## Changes Required

### Modify: `planning_pipeline/integrated_orchestrator.py`

Add `get_next_feature()` method.

```python
# planning_pipeline/integrated_orchestrator.py:100-130
def get_next_feature(self) -> dict[str, Any] | None:
    """Get next ready issue from beads (no blockers, dependencies met)."""
    # Implementation here...
```

### Modify: `planning_pipeline/tests/test_integrated_orchestrator.py`

Add `TestGetNextFeature` class.

```python
# planning_pipeline/tests/test_integrated_orchestrator.py:150-200
class TestGetNextFeature:
    """Tests for getting next ready feature."""
    # Test methods here...
```

## Test Specification

**Given**: Beads issues exist with dependencies
**When**: `get_next_feature()` is called
**Then**: Returns the first issue from `bd ready` (no blockers, dependencies met)

### Test Cases

1. `test_returns_first_ready_issue` - Returns first ready issue
2. `test_returns_none_when_no_ready_issues` - Returns None when no issues ready
3. `test_handles_single_dict_response` - Handles bd ready returning single dict
4. `test_returns_none_on_bd_failure` - Returns None when bd command fails

### Edge Cases

- No ready issues → return None
- bd ready returns empty list → return None
- bd ready returns single dict → return it directly
- bd command fails → return None

## Implementation

### Red Phase Test Code

```python
class TestGetNextFeature:
    """Tests for getting next ready feature."""

    def test_returns_first_ready_issue(self, tmp_path):
        """Given ready issues exist, returns first one."""
        mock_ready = {
            "success": True,
            "data": [
                {"id": "phase-1", "title": "Phase 1: Setup", "priority": 1},
                {"id": "phase-2", "title": "Phase 2: Core", "priority": 2},
            ]
        }

        with patch.object(BeadsController, '_run_bd', return_value=mock_ready):
            orchestrator = IntegratedOrchestrator(tmp_path)
            feature = orchestrator.get_next_feature()

            assert feature is not None
            assert feature["id"] == "phase-1"
            assert feature["priority"] == 1

    def test_returns_none_when_no_ready_issues(self, tmp_path):
        """Given no ready issues, returns None."""
        mock_ready = {"success": True, "data": []}

        with patch.object(BeadsController, '_run_bd', return_value=mock_ready):
            orchestrator = IntegratedOrchestrator(tmp_path)
            feature = orchestrator.get_next_feature()

            assert feature is None

    def test_handles_single_dict_response(self, tmp_path):
        """Given bd ready returns dict (not list), handles it."""
        mock_ready = {
            "success": True,
            "data": {"id": "only-issue", "title": "Single Issue"}
        }

        with patch.object(BeadsController, '_run_bd', return_value=mock_ready):
            orchestrator = IntegratedOrchestrator(tmp_path)
            feature = orchestrator.get_next_feature()

            assert feature is not None
            assert feature["id"] == "only-issue"

    def test_returns_none_on_bd_failure(self, tmp_path):
        """Given bd ready fails, returns None."""
        mock_ready = {"success": False, "error": "Command failed"}

        with patch.object(BeadsController, '_run_bd', return_value=mock_ready):
            orchestrator = IntegratedOrchestrator(tmp_path)
            feature = orchestrator.get_next_feature()

            assert feature is None
```

### Green Phase Implementation

```python
def get_next_feature(self) -> dict[str, Any] | None:
    """Get next ready issue from beads (no blockers, dependencies met)."""
    result = self.bd._run_bd('ready', '--limit=1')

    if not result["success"]:
        return None

    data = result.get("data")
    if not data:
        return None

    if isinstance(data, list):
        return data[0] if data else None
    elif isinstance(data, dict):
        return data

    return None
```

## Success Criteria

### Automated

- [ ] Test fails for right reason (Red): `pytest planning_pipeline/tests/test_integrated_orchestrator.py::TestGetNextFeature -v`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_integrated_orchestrator.py::TestGetNextFeature -v`
- [ ] All tests pass: `pytest planning_pipeline/tests/`

### Manual (Human-Testable)

Run from project root (requires beads initialized with issues):

```bash
python -c "
from pathlib import Path
from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

orchestrator = IntegratedOrchestrator(Path('.'))
feature = orchestrator.get_next_feature()
if feature:
    print(f'Next feature: {feature[\"id\"]}')
    print(f'Title: {feature.get(\"title\", \"N/A\")}')
    print(f'Priority: {feature.get(\"priority\", \"N/A\")}')
else:
    print('No ready features')
"
```

**Expected**: Returns the same issue as `bd ready --limit=1`

## References

- `planning_pipeline/beads_controller.py:20-50` - _run_bd method
- `orchestrator.py:487-502` - Original get_next_feature function
