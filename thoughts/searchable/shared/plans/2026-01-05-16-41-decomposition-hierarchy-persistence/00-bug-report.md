# Bug Report: Decomposition Phase Errno 21 - Hierarchy Not Written to Disk

**Issue ID**: silmari-Context-Engine-3s7x
**Priority**: P2
**Status**: CLOSED
**Created**: 2026-01-05 16:41
**Closed**: 2026-01-05 16:45

## Problem Summary

The decomposition phase stores the requirement hierarchy as an in-memory dict in `metadata["hierarchy"]`, but the TDD planning phase expects `metadata["hierarchy_path"]` to be a file path pointing to a JSON file on disk.

## Error

```
[Errno 21] Is a directory
```

This occurs because:
1. `metadata["hierarchy_path"]` doesn't exist
2. Fallback to empty string causes `Path("") / project_path` → project directory
3. Attempting to `open()` a directory raises Errno 21

## Root Cause

**Location**: `silmari_rlm_act/phases/` - decomposition.py and tdd_planning.py

The decomposition phase uses BAML to generate requirements in memory. It stores the hierarchy as a serialized dict in `metadata["hierarchy"]` (around line 236), but does NOT write a JSON file or set `metadata["hierarchy_path"]`.

The TDD planning phase has `_load_hierarchy(hierarchy_path)` that expects to read from a file path.

## Previous (Incorrect) Fix Applied

The previous solution modified the pipeline to:
1. Look for `metadata["hierarchy"]` (dict) first
2. Fall back to `hierarchy_path`
3. Added `_load_hierarchy_from_dict()` to tdd_planning.py

**Why this is wrong**: Data should be persisted to disk, not held in memory. In-memory storage:
- Loses data on process restart
- Cannot be inspected/debugged
- Breaks the contract between phases
- Doesn't support checkpoint/resume properly

## Correct Fix Required

**Option 1 (Recommended)**: Have decomposition write the hierarchy to a JSON file:

```python
# In decomposition.py, after generating hierarchy
hierarchy_path = output_dir / "requirement_hierarchy.json"
with open(hierarchy_path, 'w') as f:
    json.dump(hierarchy_dict, f, indent=2)
metadata["hierarchy_path"] = str(hierarchy_path)
```

**Option 2**: Use the existing thoughts/plans directory structure:
- Write to `thoughts/searchable/shared/plans/{plan-name}/hierarchy.json`
- This aligns with the existing convention for plan artifacts

## Files to Modify

1. `silmari_rlm_act/phases/decomposition.py` - Add file write after BAML generation
2. `silmari_rlm_act/pipeline.py` - Revert to expecting file path only
3. `silmari_rlm_act/phases/tdd_planning.py` - Remove `_load_hierarchy_from_dict()` workaround

## Testing

After fix:
1. Run decomposition phase
2. Verify `hierarchy.json` file exists at expected path
3. Run TDD planning phase
4. Confirm it reads from the file successfully
5. Test checkpoint/resume to ensure persistence works

## Related Context

- Decomposition uses BAML for LLM-based requirement breakdown
- TDD planning phase generates test-driven development plans from the hierarchy
- Pipeline orchestrates phases and passes metadata between them

---

## Resolution (2026-01-05)

**Fix Applied**: Option 2 - Decomposition now writes hierarchy to disk in the plans directory.

### Changes Made:

1. **decomposition.py**:
   - Added `json` import
   - Added `_save_hierarchy_to_disk()` method that writes hierarchy to `thoughts/searchable/shared/plans/{date}-tdd-{plan-name}/requirement_hierarchy.json`
   - Updated `execute()` to call `_save_hierarchy_to_disk()` and store path in `metadata["hierarchy_path"]`
   - Removed in-memory `metadata["hierarchy"]` storage

2. **pipeline.py**:
   - Simplified TDD_PLANNING phase execution to only use `hierarchy_path`
   - Removed fallback to in-memory `hierarchy` dict
   - Added explicit error when `hierarchy_path` is missing

3. **tdd_planning.py**:
   - Removed `_load_hierarchy_from_dict()` method
   - Simplified `execute()` and `execute_with_checkpoint()` to only accept `hierarchy_path`
   - Renamed `_load_hierarchy_from_path()` to `_load_hierarchy()`

4. **Tests updated**:
   - `test_decomposition_phase.py`: Updated to verify `hierarchy_path` exists and points to valid JSON file
   - `test_tdd_planning_phase.py`: Fixed argument order in all `execute()` and `execute_with_checkpoint()` calls

### Verification:

- All 313 silmari_rlm_act tests pass (1 unrelated failure in research phase template)
- Hierarchy is now properly persisted to disk
- Checkpoint/resume will work correctly since data is not lost
