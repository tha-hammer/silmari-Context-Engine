# Phase 04: The system must implement a full Checkpoint System...

## Requirements

### REQ_003: The system must implement a full Checkpoint System with UUID

The system must implement a full Checkpoint System with UUID-based checkpoint files

#### REQ_003.1: Create UUID-based checkpoint files in .rlm-act-checkpoints/*

Create UUID-based checkpoint files in .rlm-act-checkpoints/*.json that capture complete pipeline state after each phase

##### Testable Behaviors

1. Checkpoint files are created in `.rlm-act-checkpoints/` directory relative to project root
2. Each checkpoint file is named with a UUID v4 format: `{uuid}.json`
3. Checkpoint JSON contains required fields: id, phase, timestamp, state, errors, git_commit
4. Timestamp is in RFC3339/ISO8601 format with timezone suffix (e.g., `2026-01-09T20:53:34Z`)
5. State field contains complete PipelineState serialized via `to_checkpoint_dict()` equivalent
6. Git commit hash is captured from current HEAD (40-character SHA-1) or empty string if not in git repo
7. Errors field is an array of error message strings (empty array if no errors)
8. Checkpoint directory is created automatically if it doesn't exist (mode 0755)
9. Checkpoint files are written with mode 0644
10. Function returns absolute path to created checkpoint file
11. WriteCheckpoint accepts PipelineState, phase name (string), and optional error list parameters

#### REQ_003.2: Automatically trigger checkpoint creation after successful c

Automatically trigger checkpoint creation after successful completion of each pipeline phase

##### Testable Behaviors

1. Checkpoint is written automatically after each phase completes (success or failure)
2. Phase name in checkpoint follows pattern: `{phase_type}-{status}` (e.g., `research-complete`, `decomposition-failed`)
3. Checkpoint includes all phase results accumulated up to that point
4. If checkpoint write fails, error is logged but pipeline continues (non-blocking)
5. Checkpoint is written BEFORE user prompt in checkpoint autonomy mode
6. Pipeline Run() method integrates CheckpointManager instance
7. Each step (Research, Decomposition, Planning, PhaseDecomposition, BeadsIntegration, Implementation) triggers checkpoint
8. PipelineConfig includes CheckpointManager reference or creates one internally

#### REQ_003.3: Load and restore pipeline state from any checkpoint file to 

Load and restore pipeline state from any checkpoint file to resume execution from that phase

##### Testable Behaviors

1. DetectResumableCheckpoint() returns most recent checkpoint based on timestamp field (not file mtime)
2. Returns nil/empty if no checkpoints exist or directory doesn't exist
3. Checkpoint data includes `file_path` field pointing to source file
4. LoadCheckpoint(checkpointPath string) deserializes JSON and returns PipelineState
5. LoadCheckpoint returns error if file doesn't exist, is invalid JSON, or missing required fields
6. GetCheckpointAgeDays(checkpoint) calculates age from timestamp field handling ISO8601 with Z suffix
7. Resume skips phases that are already marked complete in the loaded state
8. Resume starts execution from the first incomplete or failed phase
9. Loaded checkpoint_id is preserved in resumed state
10. beads_epic_id is restored for continued beads integration

#### REQ_003.4: Delete checkpoint files older than a specified number of day

Delete checkpoint files older than a specified number of days based on their timestamp

##### Testable Behaviors

1. CleanupByAge(days int) deletes all checkpoints with age >= days
2. Age is calculated from checkpoint timestamp field, not filesystem modification time
3. Returns tuple (deletedCount int, failedCount int)
4. Gracefully handles missing/empty checkpoints directory (returns 0, 0)
5. Skips files with invalid JSON (counts in failed)
6. Skips files that fail to delete (counts in failed)
7. Does not delete checkpoint files with missing or unparseable timestamps
8. Days parameter of 0 deletes all checkpoints created before today
9. Negative days parameter returns error or is treated as 0

#### REQ_003.5: Delete all checkpoint files in the checkpoints directory reg

Delete all checkpoint files in the checkpoints directory regardless of age

##### Testable Behaviors

1. CleanupAll() deletes all `*.json` files in `.rlm-act-checkpoints/` directory
2. Returns tuple (deletedCount int, failedCount int)
3. Gracefully handles missing checkpoints directory (returns 0, 0)
4. Does NOT delete the checkpoints directory itself
5. Does NOT delete non-JSON files in the directory
6. Continues processing remaining files if one deletion fails
7. Tracks both successful deletions and failures
8. Can be called safely when no checkpoints exist


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed