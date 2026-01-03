# Resume Pipeline Integration - Phase Overview

## Plan Reference
Original plan: `thoughts/searchable/shared/plans/2026-01-01-tdd-resume-pipeline-integration.md`

## Summary
Integrate `resume_pipeline.py` functionality into `planning_orchestrator.py` to provide:
1. Auto-detection of failed pipeline runs from `.workflow-checkpoints/` JSON files
2. Interactive file selection when research/plan documents aren't provided
3. Checkpoint cleanup with 30-day warning and interactive menu
4. Unified CLI entry point for both fresh runs and resumes

## Phase Files

| Phase | Title | Human-Testable Function | File |
|-------|-------|------------------------|------|
| 1 | [Checkpoint Management Module](./2026-01-01-tdd-resume-pipeline-integration-01-checkpoint-management.md) | `detect_resumable_checkpoint()` | checkpoint_manager.py |
| 2 | [File Discovery & Selection](./2026-01-01-tdd-resume-pipeline-integration-02-file-discovery.md) | `prompt_file_selection()` | helpers.py, checkpoints.py |
| 3 | [CLI Integration](./2026-01-01-tdd-resume-pipeline-integration-03-cli-integration.md) | `planning_orchestrator.py --resume` | planning_orchestrator.py |
| 4 | [Checkpoint Writing & Cleanup](./2026-01-01-tdd-resume-pipeline-integration-04-checkpoint-cleanup.md) | Pipeline auto-creates checkpoints on failure | pipeline.py |

## Dependency Graph

```
Phase 1: Checkpoint Management Module
    │
    ├──► Phase 2: File Discovery & Selection
    │         │
    │         ▼
    └──────► Phase 3: CLI Integration ◄───┐
                  │                       │
                  ▼                       │
              Phase 4: Checkpoint Writing ┘
```

## Verification Flow

1. **Phase 1**: `python -c "from planning_pipeline import detect_resumable_checkpoint"` succeeds
2. **Phase 2**: `python -c "from planning_pipeline import prompt_file_selection"` succeeds
3. **Phase 3**: `python planning_orchestrator.py --resume --help` shows resume options
4. **Phase 4**: Pipeline creates checkpoint on failure, deletes on success
