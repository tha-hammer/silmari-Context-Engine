# Phase 18: The Checkpoint struct must include all required fi...

## Requirements

### REQ_018: The Checkpoint struct must include all required fields for s

The Checkpoint struct must include all required fields for state persistence

#### REQ_018.1: UUID identifier field for unique checkpoint identification a

UUID identifier field for unique checkpoint identification across sessions

##### Testable Behaviors

1. ID field is defined as string type in Checkpoint struct
2. ID uses UUID v4 format (xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx)
3. ID is generated using github.com/google/uuid package
4. ID is set during WriteCheckpoint() before file creation
5. ID is used as the filename base (ID + .json)
6. ID is included in JSON serialization with json:"id" tag
7. ID cannot be empty when writing checkpoint
8. ID validation rejects non-UUID formatted strings on load

#### REQ_018.2: Phase field storing current pipeline phase name for resume t

Phase field storing current pipeline phase name for resume targeting

##### Testable Behaviors

1. Phase field is defined as string type in Checkpoint struct
2. Phase follows naming convention: {phase-name}-{status} (e.g., research-complete, decomposition-failed)
3. Phase is included in JSON serialization with json:"phase" tag
4. Phase cannot be empty when writing checkpoint
5. Phase value matches one of the valid pipeline phases: research, decomposition, planning, phase_decomposition, beads_integration, implementation
6. Phase status suffix is either 'complete' or 'failed'
7. DetectResumableCheckpoint() uses Phase to determine resume point
8. Phase is displayed in checkpoint status output

#### REQ_018.3: Timestamp field in RFC3339 format for checkpoint ordering an

Timestamp field in RFC3339 format for checkpoint ordering and age calculation

##### Testable Behaviors

1. Timestamp field is defined as string type in Checkpoint struct
2. Timestamp is formatted using time.RFC3339 (e.g., 2006-01-02T15:04:05Z07:00)
3. Timestamp is included in JSON serialization with json:"timestamp" tag
4. Timestamp is set to current time using time.Now().Format(time.RFC3339) during WriteCheckpoint()
5. Timestamp cannot be empty when writing checkpoint
6. DetectResumableCheckpoint() sorts checkpoints by Timestamp descending (newest first)
7. CleanupByAge() parses Timestamp to calculate age in days
8. Timestamp parsing handles both Z suffix and timezone offset formats
9. GetCheckpointAgeDays() returns correct age calculation from Timestamp

#### REQ_018.4: State field as map[string]interface{} for storing arbitrary 

State field as map[string]interface{} for storing arbitrary pipeline state data

##### Testable Behaviors

1. State field is defined as map[string]interface{} type in Checkpoint struct
2. State is included in JSON serialization with json:"state" tag
3. State stores complete pipeline state including: research_output, decomposition_result, planning_output, phase_files, beads_data
4. State is populated from PipelineResults.ToCheckpointMap() or equivalent method
5. State can be restored using FromCheckpointMap(state map[string]interface{}) method
6. State handles nested structures (maps, slices) during JSON round-trip
7. State preserves all keys and values after JSON marshal/unmarshal cycle
8. Empty State map is allowed but logged as warning
9. State field omits nil values using omitempty for cleaner JSON output

#### REQ_018.5: Errors field as string slice for tracking pipeline errors an

Errors field as string slice for tracking pipeline errors and failure reasons

##### Testable Behaviors

1. Errors field is defined as []string type in Checkpoint struct
2. Errors is included in JSON serialization with json:"errors,omitempty" tag
3. Errors contains human-readable error messages from failed pipeline steps
4. Errors is populated when WriteCheckpoint() is called with errors parameter
5. Errors can be nil/empty for successful checkpoints
6. Each error message is a complete description (not just error codes)
7. Errors are preserved in order of occurrence
8. DetectResumableCheckpoint() exposes Errors for user decision on resume
9. Errors are displayed in checkpoint status output for debugging

### REQ_019: The system must add new CLI commands for status and cleanup 

The system must add new CLI commands for status and cleanup operations

#### REQ_019.1: Implement the autonomous loop pattern for the implementation

Implement the autonomous loop pattern for the implementation phase, mimicking the Python code's behavior. This includes building the prompt, iterating up to a maximum of 100 times, invoking Claude with the prompt, sleeping for 10 seconds, and checking if all beads issues are closed. If so, run tests and break the loop. If tests fail, continue the loop.  Handle potential errors and timeouts gracefully.

##### Testable Behaviors

1. The code correctly builds the prompt with the TDD plan and beads issue IDs.
2. The loop iterates up to 100 times.
3. Claude is invoked with the prompt and streaming output is captured.
4. The code sleeps for 10 seconds.
5. The code checks if all beads issues are closed.
6. If all issues are closed, tests are run (pytest or make test).
7. If tests pass, the loop breaks and the phase is marked complete.
8. If tests fail, the loop continues to fix the issues.
9. The code handles potential errors and timeouts gracefully.
10. The function returns a PhaseResult with the iteration count.

#### REQ_019.2: Implement the autonomous loop pattern for the implementation

Implement the autonomous loop pattern for the implementation phase, mimicking the Python code's behavior. This involves building the prompt, iterating up to a maximum of 100 times, invoking Claude with the prompt, sleeping for 10 seconds, and checking if all beads issues are closed before proceeding to the next iteration.  If tests fail, the loop continues.  Finally, return a PhaseResult with the iteration count.

##### Testable Behaviors

1. The code correctly constructs the prompt with the TDD plan and beads issue IDs.
2. The code iterates up to 100 times.
3. The code invokes Claude with the prompt and streams the output.
4. The code sleeps for 10 seconds between Claude invocations.
5. The code checks if all beads issues are closed before proceeding to the next iteration.
6. If tests fail, the code continues the loop to fix the tests.
7. If tests pass, the code breaks the loop and marks the phase as complete.
8. The code returns a PhaseResult with the iteration count.
9. The code handles potential errors during Claude invocation and test execution.

#### REQ_019.3: Implement the autonomous loop pattern for the implementation

Implement the autonomous loop pattern for the implementation phase, mimicking the Python version. This includes building the prompt, iterating up to a maximum of 100 times, invoking Claude with the prompt, sleeping for 10 seconds, and checking if all beads issues are closed. If not, the loop continues.  If all issues are closed, tests are run, and if they pass, the loop breaks. If tests fail, the loop continues. Finally, the phase result is returned.

##### Testable Behaviors

1. The code correctly implements the autonomous loop pattern.
2. The code correctly invokes Claude with the generated prompt.
3. The code correctly sleeps for 10 seconds.
4. The code correctly checks if all beads issues are closed.
5. The code correctly runs tests (pytest or make test) when all issues are closed.
6. The code correctly handles test failures by continuing the loop.
7. The code returns a PhaseResult with the iteration count.


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed