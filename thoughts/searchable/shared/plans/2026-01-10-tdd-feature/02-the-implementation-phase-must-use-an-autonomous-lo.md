# Phase 02: The Implementation Phase must use an autonomous lo...

## Tracking
- Issue: `bd show <issue-id>`
- Start: `bd update <issue-id> --status=in_progress`
- Complete: `bd close <issue-id>`

## Requirements

### REQ_001: The Implementation Phase must use an autonomous loop pattern

The Implementation Phase must use an autonomous loop pattern with maximum 100 iterations

#### REQ_001.1: Construct the prompt for Claude, incorporating the TDD plan 

Construct the prompt for Claude, incorporating the TDD plan and IDs of open beads issues. This ensures Claude understands the context and desired outcome.

##### Testable Behaviors

1. The prompt includes the TDD plan details.
2. The prompt includes all relevant IDs of open beads issues.
3. The prompt is formatted according to Claude's prompt engineering guidelines.

#### REQ_001.1.1: Implement the autonomous loop to interact with Claude, itera

Implement the autonomous loop to interact with Claude, iterating up to 100 times.  Within the loop, construct and send the prompt, wait for a response, and check if all beads issues are closed.  If not, continue the loop. If all issues are closed, run tests and break the loop.

##### Testable Behaviors

1. The loop executes a maximum of 100 iterations.
2. For each iteration, the Claude prompt is constructed correctly.
3. The Claude API is called correctly to stream the output.
4. The loop waits for 10 seconds between Claude calls.
5. The loop checks if all beads issues are closed.
6. If all issues are closed, the tests are executed correctly.
7. If tests fail, the loop continues to the next iteration.
8. If tests pass, the loop breaks and the phase result is returned.

#### REQ_001.1.2: Determine if all open beads issues have been resolved. This 

Determine if all open beads issues have been resolved. This involves querying the beads issue system for the status of each issue and checking if all are closed.

##### Testable Behaviors

1. The function retrieves the status of all open beads issues.
2. The function accurately determines if all issues are closed.
3. The function returns a boolean value indicating the status.

#### REQ_001.1.3: Run the tests (pytest or make test) to verify the results of

Run the tests (pytest or make test) to verify the results of the Claude interaction.  If the tests pass, break the loop and mark the phase complete. If the tests fail, continue the loop to fix the issue.

##### Testable Behaviors

1. The tests are executed using pytest or make test.
2. The tests are executed with the correct inputs and configurations.
3. The tests are executed in a consistent environment.
4. The tests are executed with the correct dependencies.
5. The tests are executed with the correct timeouts.
6. The tests are executed with the correct logging levels.
7. The tests are executed with the correct error handling.

#### REQ_001.2: This function implements the autonomous loop pattern for the

This function implements the autonomous loop pattern for the implementation phase, iteratively invoking Claude with streaming output and checking for completion.

##### Testable Behaviors

1. The function executes the Claude API with streaming output.
2. The function sleeps for 10 seconds between Claude invocations.
3. The function checks if all beads issues are closed after each Claude invocation.
4. If all beads issues are closed, the function runs tests (pytest or make test) and breaks the loop if tests pass.
5. If tests fail, the function continues the loop to fix the tests.
6. The function returns a PhaseResult with the iteration count.
7. The loop executes a maximum of 100 iterations.
8. The function handles potential errors from the Claude API and tests.
9. The function correctly manages the timeout for the Claude API calls.

#### REQ_001.3: Execute the Claude loop to perform the implementation phase.

Execute the Claude loop to perform the implementation phase. This involves building the prompt, invoking Claude with streaming output, sleeping for 10 seconds, and checking if all beads issues are closed.

##### Testable Behaviors

1. Claude is invoked with the generated prompt.
2. Claude's output is streamed to the console.
3. The program sleeps for 10 seconds after each Claude invocation.
4. The program checks if all beads issues are closed before proceeding to the next iteration.
5. The loop executes a maximum of 100 iterations.
6. The program returns a `PhaseResult` with the iteration count.

#### REQ_001.3.1: Construct the Claude prompt based on the TDD plan and bead i

Construct the Claude prompt based on the TDD plan and bead issue IDs. This includes formatting the prompt for optimal Claude performance.

##### Testable Behaviors

1. The prompt includes the TDD plan and all relevant bead issue IDs.
2. The prompt is formatted according to Claude's best practices.
3. The prompt is validated to ensure it contains the required information.

#### REQ_001.3.2: Determine if all bead issues are closed. This requires integ

Determine if all bead issues are closed. This requires integration with the Beads API to query the status of each issue.

##### Testable Behaviors

1. The program successfully connects to the Beads API.
2. The program retrieves the status of all bead issues.
3. The program determines if all issues are closed.
4. The program returns a boolean indicating whether all issues are closed.

#### REQ_001.4: This function implements the core autonomous loop for the im

This function implements the core autonomous loop for the implementation phase. It constructs a prompt for Claude, sleeps for 10 seconds, and checks if all beads issues are closed before iterating again.  It also handles the loop termination condition.

##### Testable Behaviors

1. The function correctly constructs the Claude prompt with the TDD plan and beads issue IDs.
2. The function sleeps for 10 seconds.
3. The function accurately checks if all beads issues are closed (using a reliable method - e.g., API call to beads service).
4. The function terminates the loop after 100 iterations.
5. The function correctly returns the PhaseResult with the iteration count.

#### REQ_001.4.1: This function handles the loop termination conditions, ensur

This function handles the loop termination conditions, ensuring the loop runs for a maximum of 100 iterations or until all beads issues are closed.

##### Testable Behaviors

1. The function correctly limits the loop iterations to 100.
2. The function correctly terminates the loop when all beads issues are closed.
3. The function accurately tracks the iteration count.

#### REQ_001.4.2: This function handles the loop termination condition due to 

This function handles the loop termination condition due to a timeout (36 seconds).  It ensures the loop doesn't run indefinitely if the beads issues are not resolved within the timeout period.

##### Testable Behaviors

1. The function correctly terminates the loop after 36 seconds if all beads issues are not closed.
2. The function accurately tracks the elapsed time.

#### REQ_001.5: Execute the autonomous implementation loop, iterating up to 

Execute the autonomous implementation loop, iterating up to 100 times to invoke Claude and check for bead closure.

##### Testable Behaviors

1. The loop executes 100 times or until all beads are closed.
2. Each iteration invokes Claude with the current TDD plan and issue IDs.
3. Claude's output is streamed and processed.
4. The script sleeps for 10 seconds after each Claude invocation.
5. The script checks if all beads issues are closed after each sleep.
6. If all beads are closed, the script runs tests (pytest or make test).
7. If tests pass, the loop breaks, and the phase is marked complete.
8. If tests fail, the loop continues to fix the issues.
9. The iteration count is recorded and returned as part of the phase result.
10. The script handles potential errors during Claude invocation and test execution.


## Success Criteria

- [x] All tests pass
- [x] All behaviors implemented
- [x] Code reviewed

## Implementation Status

**COMPLETED** - 2026-01-10

All Phase 2 requirements are fully implemented and tested:

### Implemented Components

1. **Autonomous Loop Pattern** (`StepImplementation` in `go/internal/planning/implementation.go`)
   - ✅ Maximum 100 iterations (configurable)
   - ✅ 10-second sleep between iterations
   - ✅ Streaming Claude output
   - ✅ Iteration tracking and result reporting

2. **Prompt Construction** (`buildImplementationPrompt`)
   - ✅ Includes TDD plan file paths
   - ✅ Includes beads epic and issue IDs
   - ✅ Comprehensive implementation instructions
   - ✅ Red-Green-Refactor guidance
   - ✅ Exit conditions and critical rules

3. **Beads Issue Status Checking** (`checkAllIssuesClosed`, `isIssueClosed`)
   - ✅ Queries beads system for each issue
   - ✅ Supports multiple status formats (closed, done, complete)
   - ✅ Returns boolean and list of closed issues
   - ✅ Robust error handling

4. **Test Execution** (`runTests`, `tryPytest`, `tryMakeTest`, `tryGoTest`)
   - ✅ Multi-framework support (pytest, make test, go test)
   - ✅ Automatic test runner detection
   - ✅ Output capture and reporting
   - ✅ Pass/fail determination

5. **Loop Control Logic**
   - ✅ Continues on test failure
   - ✅ Breaks on test success
   - ✅ Updates prompt with test failures
   - ✅ Handles max iterations gracefully

### Test Coverage

All requirements verified with comprehensive tests in `go/internal/planning/implementation_test.go`:

- ✅ REQ_001.1: Prompt construction with TDD plan and beads IDs
- ✅ REQ_001.1.1: Autonomous loop with max 100 iterations
- ✅ REQ_001.1.2: Beads issue closure detection
- ✅ REQ_001.1.3: Test execution (pytest/make test)
- ✅ REQ_001.2-001.5: Loop implementation variations
- ✅ Input validation
- ✅ Error handling
- ✅ Constants validation
- ✅ Helper functions

### Files Modified

- `go/internal/planning/implementation_test.go` - Fixed TestRunTests_NoRunner to handle environments where pytest is available

### Test Results

```
PASS: TestBuildImplementationPrompt
PASS: TestBuildImplementationPrompt_EmptyInputs
PASS: TestCheckAllIssuesClosed (all variants)
PASS: TestIsIssueClosed (all status types)
PASS: TestRunTests_Pytest
PASS: TestRunTests_MakeTest
PASS: TestRunTests_NoRunner
PASS: TestImplementationResult_Structure
PASS: TestImplementationConstants
PASS: TestGetOpenIssues
```

All Phase 2 tests pass successfully.