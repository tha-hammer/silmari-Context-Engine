# Phase 14: The Checkpoint Manager must support write, detect,...

## Requirements

### REQ_013: The Checkpoint Manager must support write, detect, and clean

The Checkpoint Manager must support write, detect, and cleanup operations

#### REQ_013.1: Write checkpoint file with state, phase name, and error mess

Write checkpoint file with state, phase name, and error messages to enable pipeline resume functionality

##### Testable Behaviors

1. Creates `.rlm-act-checkpoints/` directory if it does not exist with 0755 permissions
2. Generates a unique UUID v4 for each checkpoint file name
3. Serializes checkpoint data to JSON with 2-space indentation
4. Checkpoint JSON contains: id, phase, timestamp (RFC3339), state, errors array, git_commit
5. Writes file atomically to prevent corruption on interruption
6. Returns absolute path to created checkpoint file on success
7. Returns error if directory creation fails
8. Returns error if JSON marshaling fails
9. Returns error if file write fails
10. Timestamp is in ISO 8601 format with UTC timezone indicator (Z suffix)
11. State parameter must be convertible to map[string]interface{} via ToCheckpointDict()
12. Errors parameter accepts nil/empty slice and stores as empty array

#### REQ_013.2: Detect and return the most recent checkpoint file for pipeli

Detect and return the most recent checkpoint file for pipeline resume operations

##### Testable Behaviors

1. Returns nil if checkpoints directory does not exist
2. Returns nil if checkpoints directory is empty
3. Scans all *.json files in checkpoints directory
4. Parses each JSON file and extracts timestamp field
5. Sorts checkpoints by timestamp in descending order (newest first)
6. Returns the checkpoint with most recent timestamp
7. Adds file_path field to returned checkpoint data containing absolute path
8. Gracefully skips files with JSON parse errors without failing
9. Gracefully skips files with IO read errors without failing
10. Returns error only for unexpected failures (not missing/empty directory)
11. Checkpoint validation includes checking required fields: id, phase, timestamp, state

#### REQ_013.3: Delete checkpoint files older than specified number of days 

Delete checkpoint files older than specified number of days to manage disk space

##### Testable Behaviors

1. Returns (0, 0) if checkpoints directory does not exist
2. Accepts days parameter as positive integer
3. Calculates cutoff time as current time minus days parameter
4. Parses timestamp from each checkpoint JSON file
5. Deletes files where checkpoint timestamp is before cutoff time
6. Returns tuple of (deleted_count, failed_count)
7. Increments deleted_count for each successfully removed file
8. Increments failed_count for each file that could not be removed
9. Does not count JSON parse failures as failed deletions (skips silently)
10. Handles timezone-aware timestamps (Z suffix and +00:00 format)
11. Age calculation uses days (24-hour periods), not calendar days

#### REQ_013.4: Delete all checkpoint files to reset pipeline state complete

Delete all checkpoint files to reset pipeline state completely

##### Testable Behaviors

1. Returns (0, 0) if checkpoints directory does not exist
2. Scans all *.json files in checkpoints directory
3. Attempts to delete each file found
4. Returns tuple of (deleted_count, failed_count)
5. Increments deleted_count for each successfully removed file
6. Increments failed_count for each file that could not be removed (permission errors, etc.)
7. Does not delete the checkpoints directory itself, only contents
8. Does not delete non-JSON files in the directory
9. Continues processing remaining files if one deletion fails

#### REQ_013.5: Retrieve and store current git commit SHA in checkpoint for 

Retrieve and store current git commit SHA in checkpoint for version tracking and reproducibility

##### Testable Behaviors

1. Executes `git rev-parse HEAD` in project directory
2. Returns 40-character SHA-1 commit hash on success
3. Returns empty string if not in a git repository
4. Returns empty string if git command fails (git not installed, etc.)
5. Returns empty string if working directory is invalid
6. Trims whitespace from command output
7. Does not propagate errors to caller (graceful degradation)
8. Uses project path as working directory for git command
9. Timeout on git command to prevent hanging (recommend 5 seconds)


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed