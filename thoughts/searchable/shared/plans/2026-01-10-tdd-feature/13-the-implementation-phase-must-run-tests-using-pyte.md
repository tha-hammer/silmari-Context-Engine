# Phase 13: The Implementation Phase must run tests using pyte...

## Requirements

### REQ_012: The Implementation Phase must run tests using pytest with fa

The Implementation Phase must run tests using pytest with fallback to make test

#### REQ_012.1: Execute pytest as the primary test command with verbose outp

Execute pytest as the primary test command with verbose output and short traceback format

##### Testable Behaviors

1. MUST execute 'pytest -v --tb=short' command in the project directory
2. MUST set working directory to projectPath before execution
3. MUST capture both stdout and stderr output streams
4. MUST use a configurable timeout (default 300 seconds / 5 minutes)
5. MUST return exit code 0 as success, non-zero as failure
6. MUST handle subprocess.TimeoutExpired exception gracefully
7. MUST return tuple of (passed: bool, output: string) with combined stdout+stderr
8. MUST propagate FileNotFoundError when pytest binary is not found to trigger fallback
9. MUST NOT modify or interfere with test environment variables

#### REQ_012.2: Execute 'make test' as fallback when pytest command is not a

Execute 'make test' as fallback when pytest command is not available or fails to start

##### Testable Behaviors

1. MUST only be invoked when pytest execution fails with FileNotFoundError or exec.ErrNotFound
2. MUST NOT be invoked when pytest runs but tests fail (exit code non-zero)
3. MUST execute 'make test' command in the project directory
4. MUST set working directory to projectPath before execution
5. MUST capture both stdout and stderr output streams
6. MUST use same timeout as pytest (300 seconds default)
7. MUST return exit code 0 as success, non-zero as failure
8. MUST handle case where Makefile or 'test' target doesn't exist gracefully
9. MUST return (true, 'No test command found, skipping') if neither pytest nor make test available

#### REQ_012.3: Orchestrate test execution with pytest-first strategy and au

Orchestrate test execution with pytest-first strategy and automatic make test fallback

##### Testable Behaviors

1. MUST attempt pytest -v --tb=short first before any fallback
2. MUST fallback to make test ONLY when pytest binary is not found (FileNotFoundError/exec.ErrNotFound)
3. MUST NOT fallback when pytest runs but tests fail (tests failing is a valid result, not an error)
4. MUST return (passed: bool, output: string) tuple matching Python implementation signature
5. MUST combine all output from whichever command runs for debugging purposes
6. MUST log which test command was used for transparency
7. MUST handle timeout errors from either command consistently
8. MUST return (true, 'No test command found, skipping') only if both pytest and make are unavailable

#### REQ_012.4: Continue the implementation loop when tests fail, allowing C

Continue the implementation loop when tests fail, allowing Claude to fix issues in subsequent iterations

##### Testable Behaviors

1. MUST continue loop iteration when tests fail (tests_passed = false)
2. MUST NOT exit loop or mark implementation as complete when tests fail
3. MUST log test failure output for debugging: fmt.Printf('Tests failed, continuing loop:\n%s\n', output)
4. MUST include test failure output in next Claude prompt context if applicable
5. MUST track consecutive test failures to detect non-convergent implementations
6. MUST respect max_iterations limit even when tests consistently fail
7. MUST clear previous test failure errors when tests eventually pass: errors.clear() equivalent
8. MUST only break loop when BOTH all beads issues are closed AND tests pass


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed