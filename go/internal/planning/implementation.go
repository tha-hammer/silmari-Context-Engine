package planning

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// Constants for the implementation loop
const (
	IMPL_LOOP_SLEEP     = 10 * time.Second
	IMPL_MAX_ITERATIONS = 100
	IMPL_TIMEOUT        = 3600 // 1 hour per iteration in seconds
	TEST_TIMEOUT        = 300  // 5 minutes for test execution
)

// ImplementationResult contains the result of the implementation phase.
type ImplementationResult struct {
	Success       bool     `json:"success"`
	Error         string   `json:"error,omitempty"`
	Iterations    int      `json:"iterations"`
	TestsPassed   bool     `json:"tests_passed"`
	PhasesClosed  []string `json:"phases_closed,omitempty"`
	Output        string   `json:"output,omitempty"`
}

// StepImplementation executes the autonomous implementation phase.
// This function implements the core TDD autonomous loop that:
// 1. Invokes Claude with the implementation prompt
// 2. Sleeps between iterations
// 3. Checks if all beads issues are closed
// 4. Runs tests when issues are closed
// 5. Returns success when tests pass
func StepImplementation(
	projectPath string,
	phasePaths []string,
	beadsIssueIDs []string,
	beadsEpicID string,
	maxIterations int,
) *ImplementationResult {
	result := &ImplementationResult{Success: true}

	// Set max iterations to default if not provided
	if maxIterations == 0 {
		maxIterations = IMPL_MAX_ITERATIONS
	}

	// Validate inputs
	if projectPath == "" {
		result.Success = false
		result.Error = "project_path is required"
		return result
	}

	if len(beadsIssueIDs) == 0 {
		result.Success = false
		result.Error = "beads_issue_ids is required"
		return result
	}

	// Build implementation prompt
	prompt := buildImplementationPrompt(phasePaths, beadsEpicID, beadsIssueIDs)

	// Start implementation loop
	fmt.Printf("\n=== Starting Implementation Loop (max %d iterations) ===\n", maxIterations)

	for i := 0; i < maxIterations; i++ {
		result.Iterations = i + 1

		fmt.Printf("\n--- Iteration %d/%d ---\n", result.Iterations, maxIterations)

		// Invoke Claude with the implementation prompt
		claudeResult := RunClaudeSync(prompt, IMPL_TIMEOUT, true, projectPath)
		if !claudeResult.Success {
			// Log error but continue loop (may be transient)
			fmt.Printf("WARNING: Claude iteration %d failed: %s\n", result.Iterations, claudeResult.Error)
			fmt.Println("Continuing to next iteration...")
		}

		// Capture output
		if claudeResult.Output != "" {
			result.Output += fmt.Sprintf("\n=== Iteration %d ===\n%s", result.Iterations, claudeResult.Output)
		}

		// Sleep before checking issue status
		fmt.Printf("Sleeping for %v before checking status...\n", IMPL_LOOP_SLEEP)
		time.Sleep(IMPL_LOOP_SLEEP)

		// Check if all beads issues are closed
		fmt.Println("Checking if all beads issues are closed...")
		allClosed, closedIssues := checkAllIssuesClosed(projectPath, beadsIssueIDs)
		result.PhasesClosed = closedIssues

		if allClosed {
			fmt.Println("All beads issues are closed! Running tests...")

			// Run tests
			testsPassed, testOutput := runTests(projectPath)
			result.TestsPassed = testsPassed

			if testsPassed {
				fmt.Println("SUCCESS: All tests passed!")
				result.Success = true
				result.Output += fmt.Sprintf("\n=== Test Output ===\n%s", testOutput)
				return result
			}

			fmt.Printf("Tests failed. Continuing loop to fix issues.\n")
			fmt.Printf("Test output:\n%s\n", testOutput)

			// Update prompt to include test failures
			prompt = buildImplementationPrompt(phasePaths, beadsEpicID, beadsIssueIDs) +
				fmt.Sprintf("\n\n## Test Failures from Previous Iteration\n```\n%s\n```\n\nFix these test failures and ensure all tests pass.\n", testOutput)
		} else {
			fmt.Printf("Not all issues closed yet. Open issues: %v\n", getOpenIssues(beadsIssueIDs, closedIssues))
		}
	}

	// Max iterations reached without success
	result.Success = false
	result.Error = fmt.Sprintf("max iterations (%d) reached without completing implementation", maxIterations)
	return result
}

// buildImplementationPrompt constructs the prompt for Claude to implement the TDD phases.
func buildImplementationPrompt(phasePaths []string, epicID string, issueIDs []string) string {
	var sb strings.Builder

	sb.WriteString("# TDD Implementation Task\n\n")
	sb.WriteString("You are implementing a TDD plan. Follow the Red-Green-Refactor cycle for each behavior.\n\n")

	// Add phase file references
	if len(phasePaths) > 0 {
		sb.WriteString("## TDD Plan Files\n")
		for i, path := range phasePaths {
			sb.WriteString(fmt.Sprintf("%d. Read the plan at: %s\n", i+1, path))
		}
		sb.WriteString("\n")
	}

	// Add beads epic reference
	if epicID != "" {
		sb.WriteString("## Beads Epic\n")
		sb.WriteString(fmt.Sprintf("Epic ID: %s\n", epicID))
		sb.WriteString(fmt.Sprintf("View: `bd show %s`\n\n", epicID))
	}

	// Add phase issues
	if len(issueIDs) > 0 {
		sb.WriteString("## Phase Issues\n")
		sb.WriteString("Complete these phases in order:\n")
		for i, id := range issueIDs {
			sb.WriteString(fmt.Sprintf("- Phase %d: %s (`bd show %s`)\n", i+1, id, id))
		}
		sb.WriteString("\n")
	}

	// Add implementation instructions
	sb.WriteString(`## Implementation Instructions

Follow these steps for EACH phase:

1. **Read the Phase Plan**: Carefully read the phase file to understand:
   - Requirements and testable behaviors
   - Success criteria
   - Dependencies

2. **Red-Green-Refactor Cycle**: For each testable behavior:
   a. Write a failing test (RED)
   b. Implement minimal code to make it pass (GREEN)
   c. Refactor if needed while keeping tests green (REFACTOR)

3. **Run Tests**: After implementing behaviors, run the test suite:
   - Use: pytest -v --tb=short
   - Or: make test
   - Ensure all tests pass before proceeding

4. **Close Phase Issue**: When a phase is complete and tests pass:
   - Close the issue: bd close <issue-id>
   - Add a comment with summary: bd comment <issue-id> "Implemented X behaviors, all tests pass"

5. **Clear Context**: After closing an issue, emit /clear to reset context

6. **Move to Next Phase**: Continue with the next phase issue

## Critical Rules

- ALWAYS run tests before closing an issue
- ALWAYS close issues when phase is complete
- ALWAYS emit /clear after closing issues
- DO NOT skip tests
- DO NOT close issues unless ALL behaviors are implemented and tests pass
- If tests fail, fix them before closing the issue

## Exit Conditions

The implementation is complete when:
1. All phase issues are closed
2. All tests pass
3. No open beads issues remain

Continue working until these conditions are met.
`)

	return sb.String()
}

// checkAllIssuesClosed checks if all beads issues are closed.
// Returns (allClosed bool, closedIssueIDs []string).
func checkAllIssuesClosed(projectPath string, issueIDs []string) (bool, []string) {
	if len(issueIDs) == 0 {
		return false, []string{}
	}

	closedIssues := []string{}

	for _, id := range issueIDs {
		if isIssueClosed(projectPath, id) {
			closedIssues = append(closedIssues, id)
		}
	}

	return len(closedIssues) == len(issueIDs), closedIssues
}

// isIssueClosed checks if a single beads issue is closed.
func isIssueClosed(projectPath, issueID string) bool {
	cmd := exec.Command("bd", "show", issueID)
	cmd.Dir = projectPath
	output, err := cmd.Output()
	if err != nil {
		// If bd command fails, assume issue is not closed
		return false
	}

	outputStr := strings.ToLower(string(output))

	// Check for common "closed" status indicators
	closedIndicators := []string{
		"status: closed",
		"status: done",
		"status: complete",
		"status:closed",
		"status:done",
		"status:complete",
	}

	for _, indicator := range closedIndicators {
		if strings.Contains(outputStr, indicator) {
			return true
		}
	}

	return false
}

// getOpenIssues returns the list of open issue IDs.
func getOpenIssues(allIssues, closedIssues []string) []string {
	closedSet := make(map[string]bool)
	for _, id := range closedIssues {
		closedSet[id] = true
	}

	openIssues := []string{}
	for _, id := range allIssues {
		if !closedSet[id] {
			openIssues = append(openIssues, id)
		}
	}

	return openIssues
}

// runTests executes the test suite and returns (passed bool, output string).
// Implements REQ_012.3: pytest-first strategy with fallback to make test only when pytest binary not found.
func runTests(projectPath string) (bool, string) {
	fmt.Println("Attempting to run tests with pytest...")

	// Try pytest first (REQ_012.1)
	passed, output, err := tryPytest(projectPath)

	// If pytest ran (even if tests failed), return the result
	// REQ_012.2: Only fallback when pytest binary is not found
	if err == nil {
		fmt.Printf("Tests executed with pytest. Passed: %v\n", passed)
		return passed, output
	}

	// Check if error is due to pytest not being found
	if err == exec.ErrNotFound || strings.Contains(err.Error(), "executable file not found") {
		fmt.Println("pytest not found, falling back to make test...")

		// Fallback to make test (REQ_012.2)
		passed, output = tryMakeTest(projectPath)
		if output != "" {
			fmt.Printf("Tests executed with make test. Passed: %v\n", passed)
			return passed, output
		}

		// Neither pytest nor make test available
		fmt.Println("No test command found (pytest and make test not available), skipping tests")
		return true, "No test command found, skipping"
	}

	// pytest exists but execution failed for another reason
	fmt.Printf("pytest execution failed: %v\n", err)
	return false, fmt.Sprintf("pytest execution error: %v\n%s", err, output)
}

// tryPytest attempts to run pytest with timeout.
// Implements REQ_012.1: Execute pytest as primary test command with verbose output.
// Returns (passed bool, output string, error).
// Error is non-nil only when pytest binary is not found or execution fails.
func tryPytest(projectPath string) (bool, string, error) {
	// Check if pytest is available first
	checkCmd := exec.Command("pytest", "--version")
	if err := checkCmd.Run(); err != nil {
		// pytest binary not found - return error to trigger fallback
		return false, "", err
	}

	// Run pytest with verbose output and short traceback (REQ_012.1)
	cmd := exec.Command("pytest", "-v", "--tb=short")
	cmd.Dir = projectPath

	// Create a channel to capture command result
	type cmdResult struct {
		output []byte
		err    error
	}
	resultChan := make(chan cmdResult, 1)

	// Run command in goroutine with timeout (REQ_012.1)
	go func() {
		output, err := cmd.CombinedOutput()
		resultChan <- cmdResult{output: output, err: err}
	}()

	// Wait for command to complete or timeout
	select {
	case result := <-resultChan:
		// Command completed within timeout
		// REQ_012.1: Return exit code 0 as success, non-zero as failure
		passed := result.err == nil
		return passed, string(result.output), nil

	case <-time.After(TEST_TIMEOUT * time.Second):
		// Timeout occurred (REQ_012.1)
		// Try to kill the process if it's still running
		if cmd.Process != nil {
			_ = cmd.Process.Kill()
		}
		return false, "", fmt.Errorf("pytest execution timed out after %d seconds", TEST_TIMEOUT)
	}
}

// tryMakeTest attempts to run make test with timeout.
// Implements REQ_012.2: Execute 'make test' as fallback when pytest not available.
func tryMakeTest(projectPath string) (bool, string) {
	// Check if Makefile exists
	makefilePath := filepath.Join(projectPath, "Makefile")
	if _, err := os.Stat(makefilePath); os.IsNotExist(err) {
		return false, ""
	}

	// Run make test with same timeout as pytest (REQ_012.2)
	cmd := exec.Command("make", "test")
	cmd.Dir = projectPath

	// Create a channel to capture command result
	type cmdResult struct {
		output []byte
		err    error
	}
	resultChan := make(chan cmdResult, 1)

	// Run command in goroutine with timeout
	go func() {
		output, err := cmd.CombinedOutput()
		resultChan <- cmdResult{output: output, err: err}
	}()

	// Wait for command to complete or timeout
	select {
	case result := <-resultChan:
		// Command completed within timeout
		passed := result.err == nil
		return passed, string(result.output)

	case <-time.After(TEST_TIMEOUT * time.Second):
		// Timeout occurred
		if cmd.Process != nil {
			_ = cmd.Process.Kill()
		}
		return false, fmt.Sprintf("make test execution timed out after %d seconds", TEST_TIMEOUT)
	}
}

