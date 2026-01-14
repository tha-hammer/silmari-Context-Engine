# Phase 3: CLI Integration

## Overview
Modify `planning_orchestrator.py` to add resume arguments and flow logic.

## Dependencies

| Requires | Blocks |
|----------|--------|
| Phase 1: Checkpoint Management Module | Phase 4: Checkpoint Writing & Cleanup |
| Phase 2: File Discovery & Selection | |

## Changes Required

### 1. Update argument parser
**File**: `planning_orchestrator.py`
**Location**: `parse_args()` function (~line 20-58)

Add new arguments:
| Argument | Type | Description |
|----------|------|-------------|
| `--resume`, `-r` | flag | Resume from a previous step |
| `--resume-step` | choice | Step to resume from: planning, decomposition, beads |
| `--research-path` | str | Path to existing research document |
| `--plan-path` | str | Path to existing plan document |

### 2. Add resume flow handler
**File**: `planning_orchestrator.py`
**Location**: After `main()` function (~line 191)

| Function | Line | Description |
|----------|------|-------------|
| `handle_resume_flow()` | (new) | Handle the --resume flow logic |
| `interactive_file_selection()` | (new) | Interactive loop to select a file |
| `execute_from_step()` | (new) | Execute pipeline from a specific step |

### 3. Modify main() function
**File**: `planning_orchestrator.py`
**Location**: `main()` function (~line 191-241)

Changes:
- Add checkpoint cleanup check at start
- Add `if args.resume:` branch to call `handle_resume_flow()`
- Import new functions from `planning_pipeline`

## Human-Testable Function
CLI command: `python planning_orchestrator.py --resume`

**Test Procedure**:
1. Ensure a checkpoint exists in `.workflow-checkpoints/`
2. Run: `python planning_orchestrator.py --resume`
3. Verify: Checkpoint is detected and displayed
4. Verify: User is prompted to confirm using checkpoint
5. Verify: Resume step is determined from checkpoint phase

**Alternative Test (no checkpoint)**:
1. Remove all files from `.workflow-checkpoints/`
2. Run: `python planning_orchestrator.py --resume`
3. Verify: Interactive file selection menu appears
4. Verify: User can select a research file or plan file

**Test with explicit path**:
1. Run: `python planning_orchestrator.py --resume --research-path /path/to/research.md`
2. Verify: Skips file selection, uses provided path

## Success Criteria

### Automated Verification
- [ ] `python planning_orchestrator.py --help` shows new arguments
- [ ] `python planning_orchestrator.py --resume --help` shows resume options
- [ ] Existing tests pass: `python -m pytest planning_pipeline/tests/test_orchestrator.py -v`

### Manual Verification
- [ ] `--resume` auto-detects from existing checkpoint
- [ ] `--resume` without checkpoint triggers file selection
- [ ] `--resume --research-path <path>` skips file selection
- [ ] `--resume --resume-step planning` runs planning → decomposition → beads
- [ ] `--resume --resume-step decomposition` runs decomposition → beads
- [ ] `--resume --resume-step beads` runs only beads step
- [ ] Checkpoint is deleted after successful resume
- [ ] Old checkpoints (>30 days) trigger cleanup prompt
