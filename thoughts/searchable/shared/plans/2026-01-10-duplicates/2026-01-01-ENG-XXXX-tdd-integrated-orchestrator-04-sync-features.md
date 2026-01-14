# Phase 4: Sync Features with bd sync

## Overview

Implement `IntegratedOrchestrator.sync_features_with_git()` method that calls `bd sync` and returns success status.

## Dependencies

**Requires**: Phase 7 (BeadsController Extensions) - needs `sync()` method
**Blocks**: Phase 5 (Phase Priority), Phase 8 (Integration)

## Changes Required

### Modify: `planning_pipeline/integrated_orchestrator.py`

Add `sync_features_with_git()` method.

```python
# planning_pipeline/integrated_orchestrator.py:130-145
def sync_features_with_git(self) -> int:
    """Sync beads with git remote."""
    # Implementation here...
```

### Modify: `planning_pipeline/tests/test_integrated_orchestrator.py`

Add `TestSyncFeaturesWithGit` class.

```python
# planning_pipeline/tests/test_integrated_orchestrator.py:200-230
class TestSyncFeaturesWithGit:
    """Tests for beads sync."""
    # Test methods here...
```

## Test Specification

**Given**: Beads is initialized
**When**: `sync_features_with_git()` is called
**Then**: Calls `bd sync` and returns success status

### Test Cases

1. `test_returns_zero_on_success` - Returns 0 when bd sync succeeds
2. `test_returns_negative_one_on_failure` - Returns -1 when bd sync fails

### Edge Cases

- bd sync succeeds → return 0
- bd sync fails → return -1

## Implementation

### Red Phase Test Code

```python
class TestSyncFeaturesWithGit:
    """Tests for beads sync."""

    def test_returns_zero_on_success(self, tmp_path):
        """Given bd sync succeeds, returns 0."""
        mock_sync = {"success": True, "output": "Synced"}

        with patch.object(BeadsController, 'sync', return_value=mock_sync):
            orchestrator = IntegratedOrchestrator(tmp_path)
            result = orchestrator.sync_features_with_git()

            assert result == 0

    def test_returns_negative_one_on_failure(self, tmp_path):
        """Given bd sync fails, returns -1."""
        mock_sync = {"success": False, "error": "Sync failed"}

        with patch.object(BeadsController, 'sync', return_value=mock_sync):
            orchestrator = IntegratedOrchestrator(tmp_path)
            result = orchestrator.sync_features_with_git()

            assert result == -1
```

### Green Phase Implementation

```python
def sync_features_with_git(self) -> int:
    """Sync beads with git remote."""
    result = self.bd.sync()
    return 0 if result["success"] else -1
```

## Success Criteria

### Automated

- [ ] Test fails for right reason (Red): `pytest planning_pipeline/tests/test_integrated_orchestrator.py::TestSyncFeaturesWithGit -v`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_integrated_orchestrator.py::TestSyncFeaturesWithGit -v`

### Manual (Human-Testable)

Run from project root (requires beads initialized):

```bash
python -c "
from pathlib import Path
from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

orchestrator = IntegratedOrchestrator(Path('.'))
result = orchestrator.sync_features_with_git()
if result == 0:
    print('Sync successful')
else:
    print('Sync failed')
"
```

**Expected**: Returns 0 and beads syncs with git (verify with `bd sync --status`)

## References

- `planning_pipeline/beads_controller.py:80-91` - sync method
- `orchestrator.py:457-485` - Original sync_features_with_git function
