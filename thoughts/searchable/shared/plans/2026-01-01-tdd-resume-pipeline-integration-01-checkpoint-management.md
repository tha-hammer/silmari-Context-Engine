# Phase 1: Checkpoint Management Module

## Overview
Create checkpoint detection, age checking, and cleanup functions in a new module `planning_pipeline/checkpoint_manager.py`.

## Dependencies

| Requires | Blocks |
|----------|--------|
| None | Phase 2: File Discovery & Selection |
| | Phase 3: CLI Integration |

## Changes Required

### 1. Create new module
**File**: `planning_pipeline/checkpoint_manager.py` (NEW)

| Function | Line | Description |
|----------|------|-------------|
| `detect_resumable_checkpoint()` | 1-40 | Find most recent failed checkpoint |
| `get_checkpoint_age_days()` | 42-65 | Calculate age of checkpoint in days |
| `check_checkpoint_cleanup_needed()` | 67-105 | Check if cleanup warning should be shown |
| `delete_checkpoint()` | 107-120 | Delete a single checkpoint file |
| `cleanup_checkpoints_by_age()` | 122-145 | Delete checkpoints older than N days |
| `cleanup_all_checkpoints()` | 147-175 | Delete all checkpoint files |
| `write_checkpoint()` | 177-230 | Write checkpoint file for failed state |

### 2. Update exports
**File**: `planning_pipeline/__init__.py:9`
- Add imports for all checkpoint_manager functions

## Human-Testable Function
`detect_resumable_checkpoint(project_path: Path) -> Optional[dict]`

**Test Procedure**:
1. Ensure `.workflow-checkpoints/` exists with at least one JSON file
2. Run: `python -c "from planning_pipeline import detect_resumable_checkpoint; from pathlib import Path; print(detect_resumable_checkpoint(Path.cwd()))"`
3. Verify: Returns dict with keys: `id`, `phase`, `timestamp`, `state_snapshot`, `file_path`

## Success Criteria

### Automated Verification
- [ ] Unit tests pass: `python -m pytest planning_pipeline/tests/test_checkpoint_manager.py -v`
- [ ] Type checking passes: `python -m mypy planning_pipeline/checkpoint_manager.py`
- [ ] Module imports work: `python -c "from planning_pipeline import detect_resumable_checkpoint"`

### Manual Verification
- [ ] `detect_resumable_checkpoint()` finds existing checkpoint in `.workflow-checkpoints/`
- [ ] Age calculation works correctly for checkpoint timestamps
- [ ] Cleanup functions delete correct files
- [ ] `write_checkpoint()` creates valid JSON with absolute paths
