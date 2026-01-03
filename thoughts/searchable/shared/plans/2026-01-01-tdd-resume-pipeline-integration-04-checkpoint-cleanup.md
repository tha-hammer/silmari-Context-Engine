# Phase 4: Checkpoint Writing & Cleanup

## Overview
Integrate checkpoint writing into the main pipeline on failure, and deprecate standalone `resume_pipeline.py`.

## Dependencies

| Requires | Blocks |
|----------|--------|
| Phase 1: Checkpoint Management Module | None |
| Phase 3: CLI Integration | |

## Changes Required

### 1. Add checkpoint writing on failure
**File**: `planning_pipeline/pipeline.py`
**Location**: `run()` method

| Location | Change |
|----------|--------|
| After research failure (~line 68) | Write checkpoint with empty artifacts |
| After planning failure (~line 138) | Write checkpoint with research path |
| After decomposition failure (~line 172) | Write checkpoint with research + plan paths |

**Example Pattern**:
```python
if not research["success"]:
    from .checkpoint_manager import write_checkpoint
    write_checkpoint(
        self.project_path,
        "research-failed",
        [],
        [research.get("error", "Unknown error")]
    )
    results["success"] = False
    results["failed_at"] = "research"
    return results
```

### 2. Delete checkpoint on success
**File**: `planning_pipeline/pipeline.py`
**Location**: Before final return (~line 210)

```python
from .checkpoint_manager import detect_resumable_checkpoint, delete_checkpoint
checkpoint = detect_resumable_checkpoint(self.project_path)
if checkpoint:
    delete_checkpoint(checkpoint.get("file_path", ""))
```

### 3. Deprecate resume_pipeline.py
**File**: `resume_pipeline.py`
**Location**: `if __name__ == "__main__":` block

Add deprecation warning:
```python
import warnings
warnings.warn(
    "resume_pipeline.py is deprecated. Use 'python planning_orchestrator.py --resume' instead.",
    DeprecationWarning
)
```

## Human-Testable Function
Pipeline auto-creates checkpoints on failure, deletes on success.

**Test Procedure (Failure Case)**:
1. Start pipeline: `python planning_orchestrator.py --prompt-text "test" --auto-approve`
2. Interrupt during planning step (Ctrl+C or let it fail)
3. Run: `ls .workflow-checkpoints/`
4. Verify: A new JSON checkpoint file exists
5. Verify: Checkpoint contains absolute paths in `state_snapshot.artifacts`

**Test Procedure (Success Case)**:
1. Create a checkpoint manually or from previous failure
2. Run full successful pipeline
3. Run: `ls .workflow-checkpoints/`
4. Verify: Checkpoint file has been deleted

**Test Procedure (Deprecation)**:
1. Run: `python resume_pipeline.py`
2. Verify: DeprecationWarning is displayed

## Success Criteria

### Automated Verification
- [ ] Pipeline writes checkpoint on failure: `ls .workflow-checkpoints/`
- [ ] Checkpoint JSON is valid: `python -c "import json; json.load(open('.workflow-checkpoints/xxx.json'))"`
- [ ] Checkpoint contains absolute paths (not `./thoughts/...`)
- [ ] Checkpoint is deleted after successful completion

### Manual Verification
- [ ] Interrupt pipeline during research → checkpoint created with empty artifacts
- [ ] Interrupt pipeline during planning → checkpoint created with research path
- [ ] Interrupt pipeline during decomposition → checkpoint created with research + plan paths
- [ ] Resume with `--resume` → uses checkpoint, completes successfully
- [ ] After successful resume → checkpoint file is deleted
- [ ] Old checkpoints > 30 days trigger cleanup prompt on next run
- [ ] Running `resume_pipeline.py` shows deprecation warning
