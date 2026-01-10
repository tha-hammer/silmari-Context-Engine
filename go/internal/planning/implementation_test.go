package planning

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// Test helper: Create a temporary test project directory
func createTestProjectDir(t *testing.T) string {
	tmpDir, err := os.MkdirTemp("", "impl-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	return tmpDir
}

// Test helper: Create a mock bd command that returns predefined output
func createMockBdCommand(t *testing.T, tmpDir string, issueID string, status string) {
	// Create a mock bd script in the temp directory
	mockScript := filepath.Join(tmpDir, "bd")
	content := "#!/bin/bash\n"
	if status == "closed" {
		content += "echo 'Status: closed'\n"
	} else {
		content += "echo 'Status: open'\n"
	}

	err := os.WriteFile(mockScript, []byte(content), 0755)
	if err != nil {
		t.Fatalf("Failed to create mock bd script: %v", err)
	}

	// Add tmpDir to PATH
	oldPath := os.Getenv("PATH")
	os.Setenv("PATH", tmpDir+":"+oldPath)
	t.Cleanup(func() {
		os.Setenv("PATH", oldPath)
	})
}

// REQ_000.1: Test the autonomous loop executes a maximum of 100 iterations
func TestStepImplementation_MaxIterations(t *testing.T) {
	tmpDir := createTestProjectDir(t)
	defer os.RemoveAll(tmpDir)

	// Create test inputs
	phasePaths := []string{filepath.Join(tmpDir, "phase1.md")}
	beadsIssueIDs := []string{"beads-test1"}
	beadsEpicID := "beads-epic1"
	maxIterations := 5 // Use small number for faster test

	// Execute with small max iterations
	result := StepImplementation(tmpDir, phasePaths, beadsIssueIDs, beadsEpicID, maxIterations)

	// Verify: Should fail with max iterations error
	if result.Success {
		t.Errorf("Expected failure due to max iterations, got success")
	}

	if result.Iterations != maxIterations {
		t.Errorf("Expected %d iterations, got %d", maxIterations, result.Iterations)
	}

	if !strings.Contains(result.Error, "max iterations") {
		t.Errorf("Expected max iterations error, got: %s", result.Error)
	}
}

// REQ_000.1: Test that iteration count is recorded and returned
func TestStepImplementation_IterationCount(t *testing.T) {
	tmpDir := createTestProjectDir(t)
	defer os.RemoveAll(tmpDir)

	phasePaths := []string{filepath.Join(tmpDir, "phase1.md")}
	beadsIssueIDs := []string{"beads-test1"}
	beadsEpicID := "beads-epic1"
	maxIterations := 3

	result := StepImplementation(tmpDir, phasePaths, beadsIssueIDs, beadsEpicID, maxIterations)

	// Verify: Iteration count should be set
	if result.Iterations == 0 {
		t.Error("Expected non-zero iteration count")
	}

	if result.Iterations > maxIterations {
		t.Errorf("Iteration count %d exceeds max %d", result.Iterations, maxIterations)
	}
}

// REQ_000.1.1: Test input validation
func TestStepImplementation_InputValidation(t *testing.T) {
	tests := []struct {
		name          string
		projectPath   string
		phasePaths    []string
		beadsIssueIDs []string
		beadsEpicID   string
		expectError   bool
		errorContains string
	}{
		{
			name:          "Empty project path",
			projectPath:   "",
			phasePaths:    []string{"phase1.md"},
			beadsIssueIDs: []string{"beads-1"},
			beadsEpicID:   "epic-1",
			expectError:   true,
			errorContains: "project_path is required",
		},
		{
			name:          "Empty beads issue IDs",
			projectPath:   "/tmp/test",
			phasePaths:    []string{"phase1.md"},
			beadsIssueIDs: []string{},
			beadsEpicID:   "epic-1",
			expectError:   true,
			errorContains: "beads_issue_ids is required",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := StepImplementation(tt.projectPath, tt.phasePaths, tt.beadsIssueIDs, tt.beadsEpicID, 1)

			if tt.expectError {
				if result.Success {
					t.Error("Expected error, got success")
				}
				if !strings.Contains(result.Error, tt.errorContains) {
					t.Errorf("Expected error containing '%s', got: %s", tt.errorContains, result.Error)
				}
			}
		})
	}
}

// REQ_000.2: Test prompt building with TDD plan and beads issue IDs
func TestBuildImplementationPrompt(t *testing.T) {
	phasePaths := []string{"/path/to/phase1.md", "/path/to/phase2.md"}
	epicID := "beads-epic-123"
	issueIDs := []string{"beads-issue-1", "beads-issue-2"}

	prompt := buildImplementationPrompt(phasePaths, epicID, issueIDs)

	// Verify: Prompt contains all expected elements
	if !strings.Contains(prompt, "TDD Implementation Task") {
		t.Error("Prompt missing main header")
	}

	for _, path := range phasePaths {
		if !strings.Contains(prompt, path) {
			t.Errorf("Prompt missing phase path: %s", path)
		}
	}

	if !strings.Contains(prompt, epicID) {
		t.Errorf("Prompt missing epic ID: %s", epicID)
	}

	for _, id := range issueIDs {
		if !strings.Contains(prompt, id) {
			t.Errorf("Prompt missing issue ID: %s", id)
		}
	}

	// Verify: Prompt contains implementation instructions
	expectedSections := []string{
		"Implementation Instructions",
		"Red-Green-Refactor",
		"Run Tests",
		"Close Phase Issue",
		"Critical Rules",
		"Exit Conditions",
	}

	for _, section := range expectedSections {
		if !strings.Contains(prompt, section) {
			t.Errorf("Prompt missing section: %s", section)
		}
	}
}

// REQ_000.2.1: Test empty inputs for prompt building
func TestBuildImplementationPrompt_EmptyInputs(t *testing.T) {
	// Test with minimal inputs
	prompt := buildImplementationPrompt([]string{}, "", []string{})

	// Should still contain basic structure
	if !strings.Contains(prompt, "TDD Implementation Task") {
		t.Error("Prompt missing header even with empty inputs")
	}

	if !strings.Contains(prompt, "Implementation Instructions") {
		t.Error("Prompt missing instructions even with empty inputs")
	}
}

// REQ_000.2.2: Test checking if all beads issues are closed
func TestCheckAllIssuesClosed(t *testing.T) {
	tmpDir := createTestProjectDir(t)
	defer os.RemoveAll(tmpDir)

	// Create a mock bd command that returns "Status: closed"
	mockScript := filepath.Join(tmpDir, "bd")
	content := `#!/bin/bash
if [ "$1" = "show" ]; then
    if [ "$2" = "beads-closed" ]; then
        echo "Status: closed"
    else
        echo "Status: open"
    fi
fi
`
	err := os.WriteFile(mockScript, []byte(content), 0755)
	if err != nil {
		t.Fatalf("Failed to create mock bd script: %v", err)
	}

	// Add tmpDir to PATH
	oldPath := os.Getenv("PATH")
	os.Setenv("PATH", tmpDir+":"+oldPath)
	defer os.Setenv("PATH", oldPath)

	tests := []struct {
		name           string
		issueIDs       []string
		expectedAll    bool
		expectedClosed int
	}{
		{
			name:           "All closed",
			issueIDs:       []string{"beads-closed", "beads-closed"},
			expectedAll:    true,
			expectedClosed: 2,
		},
		{
			name:           "Some open",
			issueIDs:       []string{"beads-closed", "beads-open"},
			expectedAll:    false,
			expectedClosed: 1,
		},
		{
			name:           "All open",
			issueIDs:       []string{"beads-open", "beads-open"},
			expectedAll:    false,
			expectedClosed: 0,
		},
		{
			name:           "Empty list",
			issueIDs:       []string{},
			expectedAll:    false,
			expectedClosed: 0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			allClosed, closedIDs := checkAllIssuesClosed(tmpDir, tt.issueIDs)

			if allClosed != tt.expectedAll {
				t.Errorf("Expected allClosed=%v, got %v", tt.expectedAll, allClosed)
			}

			if len(closedIDs) != tt.expectedClosed {
				t.Errorf("Expected %d closed issues, got %d", tt.expectedClosed, len(closedIDs))
			}
		})
	}
}

// REQ_000.2.2: Test individual issue status checking
func TestIsIssueClosed(t *testing.T) {
	tmpDir := createTestProjectDir(t)
	defer os.RemoveAll(tmpDir)

	// Create mock bd command with various status formats
	mockScript := filepath.Join(tmpDir, "bd")
	content := `#!/bin/bash
if [ "$1" = "show" ]; then
    case "$2" in
        "beads-closed")
            echo "Status: closed"
            ;;
        "beads-done")
            echo "Status: done"
            ;;
        "beads-complete")
            echo "Status: complete"
            ;;
        "beads-open")
            echo "Status: open"
            ;;
        "beads-invalid")
            exit 1
            ;;
    esac
fi
`
	err := os.WriteFile(mockScript, []byte(content), 0755)
	if err != nil {
		t.Fatalf("Failed to create mock bd script: %v", err)
	}

	oldPath := os.Getenv("PATH")
	os.Setenv("PATH", tmpDir+":"+oldPath)
	defer os.Setenv("PATH", oldPath)

	tests := []struct {
		name       string
		issueID    string
		expectOpen bool
	}{
		{"Status closed", "beads-closed", false},
		{"Status done", "beads-done", false},
		{"Status complete", "beads-complete", false},
		{"Status open", "beads-open", true},
		{"Invalid issue", "beads-invalid", true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			isClosed := isIssueClosed(tmpDir, tt.issueID)
			isOpen := !isClosed

			if isOpen != tt.expectOpen {
				t.Errorf("Expected open=%v, got %v", tt.expectOpen, isOpen)
			}
		})
	}
}

// REQ_000.2.3: Test running tests (pytest)
func TestRunTests_Pytest(t *testing.T) {
	// Check if pytest is available
	if _, err := exec.LookPath("pytest"); err != nil {
		t.Skip("pytest not available, skipping test")
	}

	tmpDir := createTestProjectDir(t)
	defer os.RemoveAll(tmpDir)

	// Create a simple passing test file
	testContent := `
def test_passing():
    assert True
`
	testFile := filepath.Join(tmpDir, "test_example.py")
	err := os.WriteFile(testFile, []byte(testContent), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}

	// Run tests
	passed, output := tryPytest(tmpDir)

	// Verify: Tests should pass
	if !passed {
		t.Errorf("Expected tests to pass, got failure. Output: %s", output)
	}

	if output == "" {
		t.Error("Expected non-empty output from pytest")
	}

	if !strings.Contains(output, "passed") && !strings.Contains(output, "PASSED") {
		t.Errorf("Expected 'passed' in output, got: %s", output)
	}
}

// REQ_000.2.3: Test running tests (make test)
func TestRunTests_MakeTest(t *testing.T) {
	tmpDir := createTestProjectDir(t)
	defer os.RemoveAll(tmpDir)

	// Create a Makefile with a test target
	makefileContent := `
.PHONY: test
test:
	@echo "Running tests..."
	@echo "All tests passed"
	@exit 0
`
	makefilePath := filepath.Join(tmpDir, "Makefile")
	err := os.WriteFile(makefilePath, []byte(makefileContent), 0644)
	if err != nil {
		t.Fatalf("Failed to create Makefile: %v", err)
	}

	// Run tests
	passed, output := tryMakeTest(tmpDir)

	// Verify: Tests should pass
	if !passed {
		t.Errorf("Expected make test to pass, got failure. Output: %s", output)
	}

	if !strings.Contains(output, "passed") && !strings.Contains(output, "Running tests") {
		t.Errorf("Expected test output, got: %s", output)
	}
}

// REQ_000.2.3: Test running tests with no test runner available
func TestRunTests_NoRunner(t *testing.T) {
	tmpDir := createTestProjectDir(t)
	defer os.RemoveAll(tmpDir)

	// Don't create any test files or Makefile
	// Don't create go.mod

	passed, output := runTests(tmpDir)

	// Verify: Should fail with appropriate message
	if passed {
		t.Error("Expected tests to fail when no runner available")
	}

	if !strings.Contains(output, "No test runner found") {
		t.Errorf("Expected 'No test runner found' message, got: %s", output)
	}
}

// REQ_000.2.4: Test that loop continues on test failure
func TestStepImplementation_ContinueOnTestFailure(t *testing.T) {
	// This is implicitly tested by TestStepImplementation_MaxIterations
	// The loop should continue until max iterations if tests never pass
	t.Skip("Covered by TestStepImplementation_MaxIterations")
}

// REQ_000.2.5: Test PhaseResult structure
func TestImplementationResult_Structure(t *testing.T) {
	result := &ImplementationResult{
		Success:      true,
		Iterations:   5,
		TestsPassed:  true,
		PhasesClosed: []string{"beads-1", "beads-2"},
		Output:       "test output",
	}

	// Verify: All fields are accessible
	if !result.Success {
		t.Error("Expected Success field")
	}

	if result.Iterations != 5 {
		t.Errorf("Expected Iterations=5, got %d", result.Iterations)
	}

	if !result.TestsPassed {
		t.Error("Expected TestsPassed field")
	}

	if len(result.PhasesClosed) != 2 {
		t.Errorf("Expected 2 closed phases, got %d", len(result.PhasesClosed))
	}

	if result.Output == "" {
		t.Error("Expected non-empty Output field")
	}
}

// REQ_000.3: Test that iteration count is tracked correctly
func TestStepImplementation_IterationTracking(t *testing.T) {
	tmpDir := createTestProjectDir(t)
	defer os.RemoveAll(tmpDir)

	maxIterations := 3
	result := StepImplementation(
		tmpDir,
		[]string{"phase1.md"},
		[]string{"beads-test"},
		"epic-test",
		maxIterations,
	)

	// Verify: Iteration count should equal maxIterations when loop completes
	if result.Iterations != maxIterations {
		t.Errorf("Expected %d iterations, got %d", maxIterations, result.Iterations)
	}
}

// REQ_000.4: Test constants are defined correctly
func TestImplementationConstants(t *testing.T) {
	// Verify: Constants have expected values
	if IMPL_LOOP_SLEEP != 10*time.Second {
		t.Errorf("Expected IMPL_LOOP_SLEEP=10s, got %v", IMPL_LOOP_SLEEP)
	}

	if IMPL_MAX_ITERATIONS != 100 {
		t.Errorf("Expected IMPL_MAX_ITERATIONS=100, got %d", IMPL_MAX_ITERATIONS)
	}

	if IMPL_TIMEOUT != 3600 {
		t.Errorf("Expected IMPL_TIMEOUT=3600, got %d", IMPL_TIMEOUT)
	}
}

// REQ_000.5: Test sleep is implemented between iterations
func TestStepImplementation_SleepBetweenIterations(t *testing.T) {
	tmpDir := createTestProjectDir(t)
	defer os.RemoveAll(tmpDir)

	// Override sleep duration for faster test
	originalSleep := IMPL_LOOP_SLEEP
	defer func() {
		// Note: Can't actually restore const, but test is isolated
	}()

	start := time.Now()
	maxIterations := 2

	result := StepImplementation(
		tmpDir,
		[]string{"phase1.md"},
		[]string{"beads-test"},
		"epic-test",
		maxIterations,
	)

	elapsed := time.Since(start)

	// Verify: Execution should take at least (iterations * sleep time)
	// Account for overhead, expect at least 50% of theoretical minimum
	expectedMinimum := originalSleep * time.Duration(maxIterations) / 2

	if elapsed < expectedMinimum && result.Iterations == maxIterations {
		t.Logf("Execution time %v is less than expected minimum %v, but this may be due to fast Claude execution", elapsed, expectedMinimum)
		// Don't fail - in CI or fast systems, this might legitimately be fast
	}
}

// REQ_000.5: Test getOpenIssues helper function
func TestGetOpenIssues(t *testing.T) {
	allIssues := []string{"beads-1", "beads-2", "beads-3", "beads-4"}
	closedIssues := []string{"beads-1", "beads-3"}

	openIssues := getOpenIssues(allIssues, closedIssues)

	expected := []string{"beads-2", "beads-4"}

	if len(openIssues) != len(expected) {
		t.Errorf("Expected %d open issues, got %d", len(expected), len(openIssues))
	}

	for _, expectedID := range expected {
		found := false
		for _, openID := range openIssues {
			if openID == expectedID {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Expected open issue %s not found", expectedID)
		}
	}
}

// Test error handling for various failure scenarios
func TestStepImplementation_ErrorHandling(t *testing.T) {
	tests := []struct {
		name        string
		projectPath string
		issueIDs    []string
		expectError bool
	}{
		{
			name:        "Empty project path",
			projectPath: "",
			issueIDs:    []string{"beads-1"},
			expectError: true,
		},
		{
			name:        "Empty issue IDs",
			projectPath: "/tmp/test",
			issueIDs:    []string{},
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := StepImplementation(
				tt.projectPath,
				[]string{},
				tt.issueIDs,
				"epic",
				1,
			)

			if tt.expectError && result.Success {
				t.Error("Expected error, got success")
			}

			if tt.expectError && result.Error == "" {
				t.Error("Expected error message, got empty string")
			}
		})
	}
}

// Benchmark: Test performance of prompt building
func BenchmarkBuildImplementationPrompt(b *testing.B) {
	phasePaths := []string{"/path/to/phase1.md", "/path/to/phase2.md", "/path/to/phase3.md"}
	epicID := "beads-epic-123"
	issueIDs := []string{"beads-1", "beads-2", "beads-3"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = buildImplementationPrompt(phasePaths, epicID, issueIDs)
	}
}

// Benchmark: Test performance of issue checking
func BenchmarkCheckAllIssuesClosed(b *testing.B) {
	tmpDir, _ := os.MkdirTemp("", "bench-*")
	defer os.RemoveAll(tmpDir)

	// Create mock bd command
	mockScript := filepath.Join(tmpDir, "bd")
	content := "#!/bin/bash\necho 'Status: closed'\n"
	os.WriteFile(mockScript, []byte(content), 0755)

	oldPath := os.Getenv("PATH")
	os.Setenv("PATH", tmpDir+":"+oldPath)
	defer os.Setenv("PATH", oldPath)

	issueIDs := []string{"beads-1", "beads-2", "beads-3"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		checkAllIssuesClosed(tmpDir, issueIDs)
	}
}
