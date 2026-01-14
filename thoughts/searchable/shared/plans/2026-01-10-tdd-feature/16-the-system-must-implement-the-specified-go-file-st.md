# Phase 16: The system must implement the specified Go file st...

## Requirements

### REQ_015: The system must implement the specified Go file structure wi

The system must implement the specified Go file structure with planning, checkpoints, context, and cli packages

#### REQ_015.1: Implements the autonomous loop for the implementation phase,

Implements the autonomous loop for the implementation phase, interacting with Claude and checking bead status.

##### Testable Behaviors

1. The function correctly constructs Claude prompts based on the TDD plan and bead issue IDs.
2. The function executes the Claude API with streaming output, capturing the response.
3. The function sleeps for 10 seconds after each Claude invocation.
4. The function checks if all bead issues are closed before proceeding to the next iteration.
5. If all bead issues are closed, the function executes tests (pytest or make test).
6. If tests pass, the function breaks the loop and marks the phase as complete.
7. If tests fail, the function continues the loop to fix the tests.
8. The function returns a PhaseResult with the iteration count.

#### REQ_015.1.1: Runs Claude with a given file, streaming output and handling

Runs Claude with a given file, streaming output and handling potential errors.

##### Testable Behaviors

1. The function correctly constructs the Claude prompt with the provided file content.
2. The function executes the Claude API with streaming output, capturing the response.
3. The function handles potential errors during the Claude API call (e.g., network errors, API errors).
4. The function returns the Claude response or an error if the API call fails.

#### REQ_015.2: Implement the autonomous loop pattern for the implementation

Implement the autonomous loop pattern for the implementation phase, mimicking the Python code's behavior. This includes building the prompt, iterating up to a maximum of 100 times, invoking Claude with the prompt, sleeping for 10 seconds, and checking if all beads issues are closed. If the loop completes without success, return a failure result.

##### Testable Behaviors

1. The code correctly constructs the prompt with the TDD plan and beads issue IDs.
2. The code iterates up to 100 times.
3. The code successfully invokes Claude with the prompt and captures the streaming output.
4. The code sleeps for 10 seconds between Claude invocations.
5. The code accurately checks if all beads issues are closed.
6. If all beads issues are closed, the code executes tests (pytest or make test).
7. If tests pass, the code breaks the loop and marks the phase as complete, returning a success result.
8. If tests fail, the code continues the loop to fix the issues.
9. The code returns a result object with the iteration count and a success/failure flag.

#### REQ_015.3: Implement the autonomous loop pattern for the implementation

Implement the autonomous loop pattern for the implementation phase, mimicking the Python code's behavior. This includes building the prompt, iterating up to a maximum of 100 times, invoking Claude with the prompt, sleeping for 10 seconds, and checking if all beads issues are closed. If all are closed, run tests and break the loop. If tests fail, continue the loop.  Handle timeouts gracefully.

##### Testable Behaviors

1. The loop executes up to 100 iterations.
2. Claude is invoked with the generated prompt.
3. The loop sleeps for 10 seconds between Claude invocations.
4. The code checks if all beads issues are closed before each Claude invocation.
5. If all beads issues are closed, the code runs tests (pytest or make test).
6. If tests pass, the loop breaks and the phase is marked complete.
7. If tests fail, the loop continues to fix the issue.
8. The code handles timeouts gracefully (e.g., returns an error if Claude doesn't respond within a reasonable time).
9. The code correctly tracks the iteration count.

#### REQ_015.4: Implement the autonomous loop for the implementation phase, 

Implement the autonomous loop for the implementation phase, mimicking the Python logic.

##### Testable Behaviors

1. The loop iterates a maximum of 100 times.
2. Each iteration invokes Claude with a prompt generated from the TDD plan and beads issue IDs.
3. Claude's streaming output is captured and processed.
4. A 10-second sleep is implemented between Claude calls.
5. The loop checks if all beads issues are closed after each Claude invocation.
6. If all issues are closed, the loop breaks, and a phase result is returned.
7. If tests fail, the loop continues to fix the issue.
8. The function returns a `StepResult` with the iteration count.

#### REQ_015.4.1: Implement the loop sleep functionality.

Implement the loop sleep functionality.

##### Testable Behaviors

1. The sleep duration is configurable (defaulting to 10 seconds).
2. The sleep duration is implemented using a Goroutine to avoid blocking the main thread.
3. The sleep duration is accurately measured and controlled.

#### REQ_015.4.2: Implement the loop iteration limit.

Implement the loop iteration limit.

##### Testable Behaviors

1. The loop iterates a maximum of 100 times.
2. The loop breaks when the iteration count exceeds 100.
3. The iteration count is accurately tracked and used to control the loop.

#### REQ_015.4.3: Implement the loop check for beads issue closure.

Implement the loop check for beads issue closure.

##### Testable Behaviors

1. The loop checks if all beads issues are closed after each Claude invocation.
2. The loop uses the Claude API to check the status of each beads issue.
3. The loop handles API errors gracefully.

#### REQ_015.4.4: Implement the loop break and phase result return.

Implement the loop break and phase result return.

##### Testable Behaviors

1. If all beads issues are closed, the loop breaks and a phase result is returned.
2. The phase result includes the iteration count.
3. The phase result is stored in a `StepResult` data structure.

#### REQ_015.4.5: Implement the loop continue for test failures.

Implement the loop continue for test failures.

##### Testable Behaviors

1. If tests fail, the loop continues to fix the issue.
2. The loop handles test execution errors gracefully.
3. The loop continues until the tests pass or the maximum iteration count is reached.

### REQ_016: The system must implement constants for Implementation Phase

The system must implement constants for Implementation Phase timing and limits

#### REQ_016.1: Define the sleep duration constant between implementation lo

Define the sleep duration constant between implementation loop iterations as 10 seconds using Go time.Duration

##### Testable Behaviors

1. IMPL_LOOP_SLEEP constant is defined as 10 * time.Second in go/internal/planning/implementation.go
2. Constant is exported (uppercase) for package-level visibility
3. Constant is of type time.Duration for direct use with time.Sleep()
4. Value exactly matches Python implementation specification of 10 seconds
5. Sleep duration does not count against IMPL_TIMEOUT iteration timeout
6. Sleep can be interrupted via context cancellation for graceful shutdown support
7. Constant is documented with godoc comment explaining its purpose in the implementation loop

#### REQ_016.2: Define the maximum number of implementation loop iterations 

Define the maximum number of implementation loop iterations constant as 100 to prevent infinite loops

##### Testable Behaviors

1. IMPL_MAX_ITERATIONS constant is defined as integer value 100 in go/internal/planning/implementation.go
2. Constant is exported (uppercase) for package-level visibility
3. Constant matches Python implementation specification of 100 maximum iterations
4. StepImplementation() uses this as default when maxIterations parameter is 0 or unspecified
5. maxIterations function parameter can override this default when non-zero
6. Loop terminates with error message when max iterations reached without success
7. ImplementationResult.Iterations tracks actual iteration count for reporting
8. Error message includes max iteration count: 'Max iterations (100) reached'

#### REQ_016.3: Define the per-iteration Claude invocation timeout constant 

Define the per-iteration Claude invocation timeout constant as 3600 seconds (1 hour) for long-running implementation tasks

##### Testable Behaviors

1. IMPL_TIMEOUT constant is defined as integer value 3600 in go/internal/planning/implementation.go
2. Constant represents seconds (matching RunClaudeSync timeoutSecs parameter type)
3. Constant is exported (uppercase) for package-level visibility
4. Value exactly matches Python implementation specification of 3600 seconds (1 hour)
5. This timeout applies per Claude invocation, not to the entire implementation phase
6. Timeout is passed to RunClaudeSync(prompt, IMPL_TIMEOUT, true, projectPath) in implementation loop
7. Claude timeout errors (context.DeadlineExceeded) do not terminate loop - loop continues to retry
8. Timeout is independent of IMPL_LOOP_SLEEP (sleep does not count against timeout)


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed