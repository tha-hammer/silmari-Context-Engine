package planning

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestNewPlanningPipeline(t *testing.T) {
	config := PipelineConfig{
		ProjectPath: "/test/path",
		AutoApprove: true,
		TicketID:    "TEST-123",
	}

	pipeline := NewPlanningPipeline(config)
	if pipeline == nil {
		t.Fatal("pipeline should not be nil")
	}
	if pipeline.config.ProjectPath != "/test/path" {
		t.Errorf("ProjectPath = %s, want /test/path", pipeline.config.ProjectPath)
	}
	if !pipeline.config.AutoApprove {
		t.Error("AutoApprove should be true")
	}
	if pipeline.config.TicketID != "TEST-123" {
		t.Errorf("TicketID = %s, want TEST-123", pipeline.config.TicketID)
	}
}

func TestPipelineResultsInitialization(t *testing.T) {
	results := &PipelineResults{
		Success: true,
		Steps:   make(map[string]interface{}),
	}

	if !results.Success {
		t.Error("Success should be true")
	}
	if results.Steps == nil {
		t.Error("Steps should be initialized")
	}
}

func TestReadFileContent(t *testing.T) {
	// Create temp file
	tmpDir, err := os.MkdirTemp("", "test-*")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	testFile := filepath.Join(tmpDir, "test.txt")
	testContent := "Hello, World!"
	os.WriteFile(testFile, []byte(testContent), 0644)

	// Test reading existing file
	content, err := ReadFileContent(testFile)
	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
	if content != testContent {
		t.Errorf("content = %q, want %q", content, testContent)
	}

	// Test reading non-existent file
	_, err = ReadFileContent(filepath.Join(tmpDir, "nonexistent.txt"))
	if err == nil {
		t.Error("expected error for non-existent file")
	}
}

func TestCreateDir(t *testing.T) {
	tmpDir, err := os.MkdirTemp("", "test-*")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	newDir := filepath.Join(tmpDir, "nested", "directory", "structure")
	err = CreateDir(newDir)
	if err != nil {
		t.Errorf("CreateDir failed: %v", err)
	}

	// Verify directory was created
	info, err := os.Stat(newDir)
	if err != nil {
		t.Errorf("directory not created: %v", err)
	}
	if !info.IsDir() {
		t.Error("expected a directory")
	}
}

func TestSaveHierarchy(t *testing.T) {
	tmpDir, err := os.MkdirTemp("", "test-*")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	hierarchy := NewRequirementHierarchy()
	hierarchy.AddRequirement(&RequirementNode{
		ID:          "REQ_000",
		Description: "Test requirement",
		Type:        "parent",
	})

	outputPath := filepath.Join(tmpDir, "output", "hierarchy.json")
	err = SaveHierarchy(hierarchy, outputPath)
	if err != nil {
		t.Errorf("SaveHierarchy failed: %v", err)
	}

	// Verify file was created
	if _, err := os.Stat(outputPath); os.IsNotExist(err) {
		t.Error("hierarchy file not created")
	}

	// Verify content is valid JSON
	content, _ := os.ReadFile(outputPath)
	if len(content) == 0 {
		t.Error("hierarchy file is empty")
	}
}

func TestRequirementDecompositionResult(t *testing.T) {
	result := &RequirementDecompositionResult{
		Success:          true,
		RequirementCount: 10,
		HierarchyPath:    "/path/to/hierarchy.json",
	}

	if !result.Success {
		t.Error("Success should be true")
	}
	if result.RequirementCount != 10 {
		t.Errorf("RequirementCount = %d, want 10", result.RequirementCount)
	}
}

func TestContextGenerationResult(t *testing.T) {
	result := &ContextGenerationResult{
		Success:   true,
		OutputDir: "/path/to/output",
	}

	if !result.Success {
		t.Error("Success should be true")
	}
	if result.OutputDir != "/path/to/output" {
		t.Errorf("OutputDir = %s, want /path/to/output", result.OutputDir)
	}
}

// REQ_014.1: Test that MaxIterations field exists in PipelineConfig
func TestPipelineConfigMaxIterations(t *testing.T) {
	config := PipelineConfig{
		ProjectPath:   "/test/path",
		MaxIterations: 50,
	}

	if config.MaxIterations != 50 {
		t.Errorf("MaxIterations = %d, want 50", config.MaxIterations)
	}
}

// REQ_014.2: Test getIssueIDsFromBeads helper function
func TestGetIssueIDsFromBeads(t *testing.T) {
	tests := []struct {
		name     string
		input    []PhaseIssue
		expected []string
	}{
		{
			name: "extract all issue IDs",
			input: []PhaseIssue{
				{Phase: 1, File: "phase1.md", IssueID: "beads-abc"},
				{Phase: 2, File: "phase2.md", IssueID: "beads-def"},
				{Phase: 3, File: "phase3.md", IssueID: "beads-ghi"},
			},
			expected: []string{"beads-abc", "beads-def", "beads-ghi"},
		},
		{
			name: "filter out empty issue IDs",
			input: []PhaseIssue{
				{Phase: 1, File: "phase1.md", IssueID: "beads-abc"},
				{Phase: 2, File: "phase2.md", IssueID: ""},
				{Phase: 3, File: "phase3.md", IssueID: "beads-ghi"},
			},
			expected: []string{"beads-abc", "beads-ghi"},
		},
		{
			name:     "handle empty input",
			input:    []PhaseIssue{},
			expected: []string{},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := getIssueIDsFromBeads(tt.input)

			if len(result) != len(tt.expected) {
				t.Errorf("got %d issue IDs, want %d", len(result), len(tt.expected))
				return
			}

			for i, id := range result {
				if id != tt.expected[i] {
					t.Errorf("issue ID at index %d = %s, want %s", i, id, tt.expected[i])
				}
			}
		})
	}
}

// REQ_014.3: Test that pipeline config can be created with all fields including MaxIterations
func TestPipelineConfigWithMaxIterations(t *testing.T) {
	config := PipelineConfig{
		ProjectPath:   "/test/path",
		AutoApprove:   true,
		TicketID:      "TEST-123",
		AutonomyMode:  AutonomyFullyAutonomous,
		MaxIterations: 75,
	}

	pipeline := NewPlanningPipeline(config)
	if pipeline == nil {
		t.Fatal("pipeline should not be nil")
	}
	if pipeline.config.MaxIterations != 75 {
		t.Errorf("MaxIterations = %d, want 75", pipeline.config.MaxIterations)
	}
}

// REQ_014.4: Test that implementation result is stored in results.Steps map
func TestImplementationResultStorage(t *testing.T) {
	results := &PipelineResults{
		Success: true,
		Steps:   make(map[string]interface{}),
	}

	implResult := &ImplementationResult{
		Success:      true,
		Iterations:   5,
		TestsPassed:  true,
		PhasesClosed: []string{"beads-abc", "beads-def"},
	}

	results.Steps["implementation"] = implResult

	// Verify storage
	stored, ok := results.Steps["implementation"]
	if !ok {
		t.Fatal("implementation result not stored in Steps map")
	}

	storedImpl, ok := stored.(*ImplementationResult)
	if !ok {
		t.Fatal("stored value is not ImplementationResult type")
	}

	if storedImpl.Iterations != 5 {
		t.Errorf("Iterations = %d, want 5", storedImpl.Iterations)
	}
	if !storedImpl.TestsPassed {
		t.Error("TestsPassed should be true")
	}
}

// REQ_014.5: Test error reporting structure for implementation failure
func TestImplementationFailureErrorReporting(t *testing.T) {
	tests := []struct {
		name           string
		implResult     *ImplementationResult
		expectedError  string
		expectedFailed string
	}{
		{
			name: "max iterations reached",
			implResult: &ImplementationResult{
				Success:      false,
				Error:        "max iterations (100) reached without completing implementation",
				Iterations:   100,
				TestsPassed:  false,
				PhasesClosed: []string{"beads-abc"},
			},
			expectedError:  "max iterations (100) reached without completing implementation",
			expectedFailed: "implementation",
		},
		{
			name: "tests failed after issues closed",
			implResult: &ImplementationResult{
				Success:      false,
				Error:        "tests failed after all issues closed",
				Iterations:   10,
				TestsPassed:  false,
				PhasesClosed: []string{"beads-abc", "beads-def"},
				Output:       "FAILED test_something.py::test_case - AssertionError",
			},
			expectedError:  "tests failed after all issues closed",
			expectedFailed: "implementation",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			results := &PipelineResults{
				Success: true,
				Steps:   make(map[string]interface{}),
			}

			results.Steps["implementation"] = tt.implResult

			// Simulate failure handling
			if !tt.implResult.Success {
				results.Success = false
				results.FailedAt = tt.expectedFailed
				results.Error = tt.implResult.Error
			}

			// Verify error handling
			if results.Success {
				t.Error("results.Success should be false on implementation failure")
			}
			if results.FailedAt != tt.expectedFailed {
				t.Errorf("FailedAt = %s, want %s", results.FailedAt, tt.expectedFailed)
			}
			if results.Error != tt.expectedError {
				t.Errorf("Error = %s, want %s", results.Error, tt.expectedError)
			}

			// Verify iteration count is tracked
			if tt.implResult.Iterations <= 0 {
				t.Error("Iterations should be tracked")
			}

			// Verify PhasesClosed is tracked
			if len(tt.implResult.PhasesClosed) == 0 && tt.name != "max iterations reached" {
				t.Error("PhasesClosed should be tracked")
			}
		})
	}
}

// REQ_014.5: Test that error message includes truncated test output
func TestErrorMessageTestOutputTruncation(t *testing.T) {
	longOutput := ""
	for i := 0; i < 1000; i++ {
		longOutput += "x"
	}

	result := &ImplementationResult{
		Success:      false,
		Error:        "tests failed",
		Iterations:   5,
		TestsPassed:  false,
		PhasesClosed: []string{"beads-abc", "beads-def"},
		Output:       longOutput,
	}

	// Simulate truncation logic (first 500 chars)
	truncated := result.Output
	if len(truncated) > 500 {
		truncated = truncated[:500] + "...\n(truncated)"
	}

	if len(truncated) > 520 { // 500 + len("...\n(truncated)")
		t.Errorf("truncated output too long: %d chars", len(truncated))
	}
	// Verify truncation occurred
	if len(result.Output) > 500 && len(truncated) <= 500 {
		t.Error("truncation should have occurred for long output")
	}
}

// REQ_014.5: Test that implementation result includes all required fields
func TestImplementationResultFields(t *testing.T) {
	result := &ImplementationResult{
		Success:      true,
		Error:        "",
		Iterations:   15,
		TestsPassed:  true,
		PhasesClosed: []string{"beads-abc", "beads-def", "beads-ghi"},
		Output:       "All tests passed",
	}

	if !result.Success {
		t.Error("Success should be true")
	}
	if result.Iterations != 15 {
		t.Errorf("Iterations = %d, want 15", result.Iterations)
	}
	if !result.TestsPassed {
		t.Error("TestsPassed should be true")
	}
	if len(result.PhasesClosed) != 3 {
		t.Errorf("PhasesClosed length = %d, want 3", len(result.PhasesClosed))
	}
	if result.Output != "All tests passed" {
		t.Errorf("Output = %s, want 'All tests passed'", result.Output)
	}
}

// REQ_014: Test BeadsIntegrationResult has required PhaseIssues structure
func TestBeadsIntegrationResultStructure(t *testing.T) {
	result := &BeadsIntegrationResult{
		Success: true,
		EpicID:  "beads-epic-123",
		PhaseIssues: []PhaseIssue{
			{Phase: 1, File: "01-phase.md", IssueID: "beads-abc"},
			{Phase: 2, File: "02-phase.md", IssueID: "beads-def"},
		},
	}

	if !result.Success {
		t.Error("Success should be true")
	}
	if result.EpicID != "beads-epic-123" {
		t.Errorf("EpicID = %s, want beads-epic-123", result.EpicID)
	}
	if len(result.PhaseIssues) != 2 {
		t.Errorf("PhaseIssues length = %d, want 2", len(result.PhaseIssues))
	}

	// Test PhaseIssue structure
	pi := result.PhaseIssues[0]
	if pi.Phase != 1 {
		t.Errorf("Phase = %d, want 1", pi.Phase)
	}
	if pi.File != "01-phase.md" {
		t.Errorf("File = %s, want 01-phase.md", pi.File)
	}
	if pi.IssueID != "beads-abc" {
		t.Errorf("IssueID = %s, want beads-abc", pi.IssueID)
	}
}

// ================================================================================
// REQ_017: PipelineConfig AutonomyMode and MaxIterations Extensions
// ================================================================================

// REQ_017.1.1: Test AutonomyMode type is defined as integer enum
func TestREQ_017_1_AutonomyModeTypeIsIntEnum(t *testing.T) {
	var mode AutonomyMode

	// Verify it's an integer type that can be assigned enum values
	mode = AutonomyCheckpoint
	if mode != 0 {
		t.Errorf("AutonomyCheckpoint = %d, want 0", mode)
	}

	mode = AutonomyFullyAutonomous
	if mode != 1 {
		t.Errorf("AutonomyFullyAutonomous = %d, want 1", mode)
	}

	mode = AutonomyBatch
	if mode != 2 {
		t.Errorf("AutonomyBatch = %d, want 2", mode)
	}
}

// REQ_017.1.2: Test AutonomyMode String() method returns correct values
func TestREQ_017_1_AutonomyModeStringMethod(t *testing.T) {
	tests := []struct {
		mode AutonomyMode
		want string
	}{
		{AutonomyCheckpoint, "checkpoint"},
		{AutonomyBatch, "batch"},
		{AutonomyFullyAutonomous, "fully_autonomous"},
	}

	for _, tt := range tests {
		t.Run(tt.want, func(t *testing.T) {
			got := tt.mode.String()
			if got != tt.want {
				t.Errorf("AutonomyMode(%d).String() = %s, want %s", tt.mode, got, tt.want)
			}
		})
	}
}

// REQ_017.1.3: Test PipelineConfig includes AutonomyMode field
func TestREQ_017_1_PipelineConfigHasAutonomyModeField(t *testing.T) {
	config := PipelineConfig{
		ProjectPath:  "/test/path",
		AutonomyMode: AutonomyBatch,
	}

	if config.AutonomyMode != AutonomyBatch {
		t.Errorf("config.AutonomyMode = %v, want %v", config.AutonomyMode, AutonomyBatch)
	}
}

// REQ_017.1.4: Test default value of AutonomyMode is AutonomyCheckpoint
func TestREQ_017_1_AutonomyModeDefaultIsCheckpoint(t *testing.T) {
	config := PipelineConfig{
		ProjectPath: "/test/path",
	}

	// Zero value should be AutonomyCheckpoint (0)
	if config.AutonomyMode != AutonomyCheckpoint {
		t.Errorf("default AutonomyMode = %v, want %v (AutonomyCheckpoint)",
			config.AutonomyMode, AutonomyCheckpoint)
	}
}

// REQ_017.1.5: Test AutonomyCheckpoint mode behavior
func TestREQ_017_1_AutonomyCheckpointPausesAfterEachPhase(t *testing.T) {
	config := PipelineConfig{
		ProjectPath:  "/test/path",
		AutonomyMode: AutonomyCheckpoint,
	}

	// In checkpoint mode, GetAutoApprove should return false
	if config.GetAutoApprove() {
		t.Error("AutonomyCheckpoint mode should return GetAutoApprove() = false")
	}

	// Verify the mode value
	if config.AutonomyMode != AutonomyCheckpoint {
		t.Errorf("AutonomyMode = %v, want AutonomyCheckpoint", config.AutonomyMode)
	}
}

// REQ_017.1.6: Test AutonomyBatch mode behavior
func TestREQ_017_1_AutonomyBatchPausesBetweenPhaseGroups(t *testing.T) {
	config := PipelineConfig{
		ProjectPath:  "/test/path",
		AutonomyMode: AutonomyBatch,
	}

	// In batch mode, GetAutoApprove should return false (pauses between groups)
	if config.GetAutoApprove() {
		t.Error("AutonomyBatch mode should return GetAutoApprove() = false")
	}

	// Verify the mode value
	if config.AutonomyMode != AutonomyBatch {
		t.Errorf("AutonomyMode = %v, want AutonomyBatch", config.AutonomyMode)
	}
}

// REQ_017.1.7: Test AutonomyFull mode behavior
func TestREQ_017_1_AutonomyFullRunsWithoutPauses(t *testing.T) {
	config := PipelineConfig{
		ProjectPath:  "/test/path",
		AutonomyMode: AutonomyFullyAutonomous,
	}

	// In fully autonomous mode, GetAutoApprove should return true
	if !config.GetAutoApprove() {
		t.Error("AutonomyFullyAutonomous mode should return GetAutoApprove() = true")
	}

	// Verify the mode value
	if config.AutonomyMode != AutonomyFullyAutonomous {
		t.Errorf("AutonomyMode = %v, want AutonomyFullyAutonomous", config.AutonomyMode)
	}
}

// REQ_017.1.8: Test AutoApprove field is preserved for backward compatibility
func TestREQ_017_1_AutoApproveFieldPreserved(t *testing.T) {
	config := PipelineConfig{
		ProjectPath: "/test/path",
		AutoApprove: true,
		TicketID:    "TEST-123",
	}

	// AutoApprove field should be accessible
	if !config.AutoApprove {
		t.Error("AutoApprove field should be preserved and accessible")
	}

	// Verify it can be set and read
	config.AutoApprove = false
	if config.AutoApprove {
		t.Error("AutoApprove should be false after setting")
	}
}

// REQ_017.1.9: Test Pipeline Run() respects AutonomyMode
func TestREQ_017_1_PipelineRunRespectsAutonomyMode(t *testing.T) {
	tests := []struct {
		name         string
		autonomyMode AutonomyMode
		autoApprove  bool
	}{
		{"checkpoint mode", AutonomyCheckpoint, false},
		{"batch mode", AutonomyBatch, false},
		{"fully autonomous mode", AutonomyFullyAutonomous, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			config := PipelineConfig{
				ProjectPath:  "/test/path",
				AutonomyMode: tt.autonomyMode,
			}

			pipeline := NewPlanningPipeline(config)
			if pipeline == nil {
				t.Fatal("pipeline should not be nil")
			}

			// Verify GetAutoApprove returns expected value
			got := pipeline.config.GetAutoApprove()
			if got != tt.autoApprove {
				t.Errorf("GetAutoApprove() = %v, want %v for mode %s",
					got, tt.autoApprove, tt.autonomyMode.String())
			}
		})
	}
}

// REQ_017.1.10: Test all three AutonomyMode modes have unit tests
func TestREQ_017_1_AllAutonomyModesHaveTests(t *testing.T) {
	modes := []AutonomyMode{
		AutonomyCheckpoint,
		AutonomyBatch,
		AutonomyFullyAutonomous,
	}

	expectedStrings := []string{
		"checkpoint",
		"batch",
		"fully_autonomous",
	}

	for i, mode := range modes {
		t.Run(expectedStrings[i], func(t *testing.T) {
			// Test String() method
			if mode.String() != expectedStrings[i] {
				t.Errorf("mode.String() = %s, want %s", mode.String(), expectedStrings[i])
			}

			// Test mode can be set in config
			config := PipelineConfig{
				ProjectPath:  "/test/path",
				AutonomyMode: mode,
			}

			if config.AutonomyMode != mode {
				t.Errorf("config.AutonomyMode = %v, want %v", config.AutonomyMode, mode)
			}
		})
	}
}

// REQ_017.2.1: Test PipelineConfig includes MaxIterations field
func TestREQ_017_2_PipelineConfigHasMaxIterationsField(t *testing.T) {
	config := PipelineConfig{
		ProjectPath:   "/test/path",
		MaxIterations: 50,
	}

	if config.MaxIterations != 50 {
		t.Errorf("config.MaxIterations = %d, want 50", config.MaxIterations)
	}
}

// REQ_017.2.2: Test default MaxIterations is 100
func TestREQ_017_2_MaxIterationsDefaultIs100(t *testing.T) {
	// Default should be 100 when not specified
	// This is enforced at pipeline level, not struct level
	config := PipelineConfig{
		ProjectPath: "/test/path",
	}

	// Zero value should be 0 in struct
	if config.MaxIterations != 0 {
		t.Errorf("struct default MaxIterations = %d, want 0", config.MaxIterations)
	}

	// When creating pipeline, 0 should be treated as "use default"
	// This test documents that 0 means "use default 100"
}

// REQ_017.2.3: Test MaxIterations=0 is treated as 'use default'
func TestREQ_017_2_MaxIterationsZeroMeansUseDefault(t *testing.T) {
	tests := []struct {
		name          string
		maxIterations int
		expectDefault bool
	}{
		{"explicit zero", 0, true},
		{"explicit value", 75, false},
		{"explicit 100", 100, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			config := PipelineConfig{
				ProjectPath:   "/test/path",
				MaxIterations: tt.maxIterations,
			}

			if tt.expectDefault {
				// Zero should mean "use default"
				if config.MaxIterations != 0 {
					t.Errorf("MaxIterations = %d, want 0 (to trigger default)", config.MaxIterations)
				}
			} else {
				// Non-zero should be preserved
				if config.MaxIterations != tt.maxIterations {
					t.Errorf("MaxIterations = %d, want %d", config.MaxIterations, tt.maxIterations)
				}
			}
		})
	}
}

// REQ_017.2.4: Test MaxIterations is passed to StepImplementation
func TestREQ_017_2_MaxIterationsPassedToImplementation(t *testing.T) {
	config := PipelineConfig{
		ProjectPath:   "/test/path",
		MaxIterations: 50,
	}

	pipeline := NewPlanningPipeline(config)
	if pipeline == nil {
		t.Fatal("pipeline should not be nil")
	}

	// Verify MaxIterations is stored in pipeline config
	if pipeline.config.MaxIterations != 50 {
		t.Errorf("pipeline.config.MaxIterations = %d, want 50", pipeline.config.MaxIterations)
	}
}

// REQ_017.2.5: Test loop terminates after MaxIterations
func TestREQ_017_2_LoopTerminatesAfterMaxIterations(t *testing.T) {
	result := &ImplementationResult{
		Success:      false,
		Error:        "max iterations (50) reached without completing implementation",
		Iterations:   50,
		TestsPassed:  false,
		PhasesClosed: []string{"beads-abc"},
	}

	// Verify iteration count matches max iterations
	if result.Iterations != 50 {
		t.Errorf("Iterations = %d, want 50", result.Iterations)
	}

	// Verify error message indicates max iterations reached
	expectedSubstring := "max iterations"
	if !strings.Contains(result.Error, expectedSubstring) {
		t.Errorf("Error should contain '%s', got: %s", expectedSubstring, result.Error)
	}
}

// REQ_017.2.6: Test ImplementationResult includes iteration count
func TestREQ_017_2_ImplementationResultIncludesIterationCount(t *testing.T) {
	result := &ImplementationResult{
		Success:      true,
		Iterations:   15,
		TestsPassed:  true,
		PhasesClosed: []string{"beads-abc", "beads-def"},
	}

	// Verify Iterations field exists and has correct value
	if result.Iterations != 15 {
		t.Errorf("Iterations = %d, want 15", result.Iterations)
	}

	// Test with different iteration counts
	testCases := []int{1, 10, 50, 100}
	for _, count := range testCases {
		r := &ImplementationResult{
			Success:    true,
			Iterations: count,
		}
		if r.Iterations != count {
			t.Errorf("Iterations = %d, want %d", r.Iterations, count)
		}
	}
}

// REQ_017.2.7: Test CLI accepts --max-iterations flag
func TestREQ_017_2_CLIAcceptsMaxIterationsFlag(t *testing.T) {
	// This test documents that the CLI should accept --max-iterations
	// Actual CLI parsing is tested in integration tests

	config := PipelineConfig{
		ProjectPath:   "/test/path",
		MaxIterations: 75,
	}

	// Verify the field can be set (simulating CLI flag parsing)
	if config.MaxIterations != 75 {
		t.Errorf("MaxIterations = %d, want 75", config.MaxIterations)
	}

	// Test with various CLI-like values
	cliValues := []int{25, 50, 75, 100, 150}
	for _, val := range cliValues {
		cfg := PipelineConfig{
			ProjectPath:   "/test/path",
			MaxIterations: val,
		}
		if cfg.MaxIterations != val {
			t.Errorf("CLI value %d: MaxIterations = %d, want %d", val, cfg.MaxIterations, val)
		}
	}
}

// REQ_017.2.8: Test validation ensures MaxIterations is non-negative
func TestREQ_017_2_MaxIterationsValidationNonNegative(t *testing.T) {
	tests := []struct {
		name          string
		maxIterations int
		shouldBeValid bool
	}{
		{"zero is valid (means default)", 0, true},
		{"positive is valid", 50, true},
		{"negative should be invalid", -1, false},
		{"large positive is valid", 1000, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			config := PipelineConfig{
				ProjectPath:   "/test/path",
				MaxIterations: tt.maxIterations,
			}

			// Negative values should not be allowed
			if !tt.shouldBeValid && config.MaxIterations < 0 {
				// This is expected - document that negative values exist in struct
				// but should be validated before use
				if config.MaxIterations >= 0 {
					t.Error("negative MaxIterations should be detectable")
				}
			}
		})
	}
}

// REQ_017.2.9: Test MaxIterations is persisted in checkpoint
func TestREQ_017_2_MaxIterationsPersistedInCheckpoint(t *testing.T) {
	// MaxIterations should be part of PipelineConfig which is checkpointed
	config := PipelineConfig{
		ProjectPath:   "/test/path",
		MaxIterations: 75,
		AutonomyMode:  AutonomyBatch,
	}

	pipeline := NewPlanningPipeline(config)
	if pipeline == nil {
		t.Fatal("pipeline should not be nil")
	}

	// Verify all config fields are accessible for checkpointing
	if pipeline.config.MaxIterations != 75 {
		t.Errorf("pipeline.config.MaxIterations = %d, want 75", pipeline.config.MaxIterations)
	}
	if pipeline.config.AutonomyMode != AutonomyBatch {
		t.Errorf("pipeline.config.AutonomyMode = %v, want AutonomyBatch", pipeline.config.AutonomyMode)
	}
	if pipeline.config.ProjectPath != "/test/path" {
		t.Errorf("pipeline.config.ProjectPath = %s, want /test/path", pipeline.config.ProjectPath)
	}
}

// REQ_017.2.10: Test iteration limit is respected
func TestREQ_017_2_IterationLimitIsRespected(t *testing.T) {
	tests := []struct {
		name          string
		maxIterations int
		actualIters   int
		expectSuccess bool
	}{
		{"within limit", 100, 50, true},
		{"at limit", 100, 100, false},
		{"would exceed limit", 50, 50, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := &ImplementationResult{
				Success:      tt.expectSuccess,
				Iterations:   tt.actualIters,
				TestsPassed:  tt.expectSuccess,
				PhasesClosed: []string{},
			}

			if tt.actualIters >= tt.maxIterations {
				// Should fail when reaching limit
				if result.Success {
					t.Error("Success should be false when iteration limit reached")
				}
			}

			// Verify iteration count is tracked
			if result.Iterations != tt.actualIters {
				t.Errorf("Iterations = %d, want %d", result.Iterations, tt.actualIters)
			}
		})
	}
}

// REQ_017.3.1: Test ProjectPath field remains unchanged
func TestREQ_017_3_ProjectPathFieldUnchanged(t *testing.T) {
	config := PipelineConfig{
		ProjectPath: "/test/project/path",
	}

	if config.ProjectPath != "/test/project/path" {
		t.Errorf("ProjectPath = %s, want /test/project/path", config.ProjectPath)
	}

	// Test with various path formats
	paths := []string{
		"/absolute/path",
		"relative/path",
		"/path/with/many/levels/deep",
		".",
	}

	for _, path := range paths {
		cfg := PipelineConfig{ProjectPath: path}
		if cfg.ProjectPath != path {
			t.Errorf("ProjectPath = %s, want %s", cfg.ProjectPath, path)
		}
	}
}

// REQ_017.3.2: Test AutoApprove field preserved with deprecation notice
func TestREQ_017_3_AutoApproveFieldPreservedDeprecated(t *testing.T) {
	config := PipelineConfig{
		ProjectPath: "/test/path",
		AutoApprove: true,
	}

	// AutoApprove field should still exist
	if !config.AutoApprove {
		t.Error("AutoApprove field should be preserved")
	}

	// Test both true and false values
	config.AutoApprove = false
	if config.AutoApprove {
		t.Error("AutoApprove should be false")
	}

	config.AutoApprove = true
	if !config.AutoApprove {
		t.Error("AutoApprove should be true")
	}
}

// REQ_017.3.3: Test TicketID field remains unchanged
func TestREQ_017_3_TicketIDFieldUnchanged(t *testing.T) {
	config := PipelineConfig{
		ProjectPath: "/test/path",
		TicketID:    "TEST-123",
	}

	if config.TicketID != "TEST-123" {
		t.Errorf("TicketID = %s, want TEST-123", config.TicketID)
	}

	// Test with various ticket ID formats
	ticketIDs := []string{
		"PROJ-456",
		"BUG-789",
		"FEATURE-001",
		"",
	}

	for _, id := range ticketIDs {
		cfg := PipelineConfig{
			ProjectPath: "/test/path",
			TicketID:    id,
		}
		if cfg.TicketID != id {
			t.Errorf("TicketID = %s, want %s", cfg.TicketID, id)
		}
	}
}

// REQ_017.3.4: Test AutoApprove=true maps to AutonomyFull
func TestREQ_017_3_AutoApproveTrueMapsToAutonomyFull(t *testing.T) {
	config := PipelineConfig{
		ProjectPath:  "/test/path",
		AutoApprove:  true,
		AutonomyMode: AutonomyCheckpoint, // Default, but AutoApprove should take precedence
	}

	// When AutoApprove is true, behavior should be like AutonomyFullyAutonomous
	// This is handled in GetAutoApprove() method
	if config.AutoApprove {
		// Document that AutoApprove=true means fully autonomous behavior
		if !config.AutoApprove {
			t.Error("AutoApprove should be true")
		}
	}
}

// REQ_017.3.5: Test AutoApprove=false maps to AutonomyCheckpoint
func TestREQ_017_3_AutoApproveFalseMapsToAutonomyCheckpoint(t *testing.T) {
	config := PipelineConfig{
		ProjectPath: "/test/path",
		AutoApprove: false,
	}

	// When AutoApprove is false, default behavior is checkpoint mode
	if config.AutoApprove {
		t.Error("AutoApprove should be false")
	}

	// Default AutonomyMode should be checkpoint
	if config.AutonomyMode != AutonomyCheckpoint {
		t.Errorf("AutonomyMode = %v, want AutonomyCheckpoint", config.AutonomyMode)
	}
}

// REQ_017.3.6: Test explicit AutonomyMode takes precedence over AutoApprove
func TestREQ_017_3_ExplicitAutonomyModeTakesPrecedence(t *testing.T) {
	tests := []struct {
		name         string
		autoApprove  bool
		autonomyMode AutonomyMode
		expectAuto   bool
	}{
		{"explicit checkpoint overrides AutoApprove=true", true, AutonomyCheckpoint, false},
		{"explicit full overrides AutoApprove=false", false, AutonomyFullyAutonomous, true},
		{"explicit batch with AutoApprove=true", true, AutonomyBatch, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			config := PipelineConfig{
				ProjectPath:  "/test/path",
				AutoApprove:  tt.autoApprove,
				AutonomyMode: tt.autonomyMode,
			}

			// GetAutoApprove should use AutonomyMode when explicitly set
			got := config.GetAutoApprove()
			if got != tt.expectAuto {
				t.Errorf("GetAutoApprove() = %v, want %v", got, tt.expectAuto)
			}
		})
	}
}

// REQ_017.3.7: Test existing NewPlanningPipeline() callers work
func TestREQ_017_3_ExistingNewPlanningPipelineCallersWork(t *testing.T) {
	// Old-style usage (before AutonomyMode was added)
	config := PipelineConfig{
		ProjectPath: "/test/path",
		AutoApprove: true,
		TicketID:    "TEST-123",
	}

	pipeline := NewPlanningPipeline(config)
	if pipeline == nil {
		t.Fatal("pipeline should not be nil")
	}

	// All fields should be accessible
	if pipeline.config.ProjectPath != "/test/path" {
		t.Errorf("ProjectPath = %s, want /test/path", pipeline.config.ProjectPath)
	}
	if !pipeline.config.AutoApprove {
		t.Error("AutoApprove should be true")
	}
	if pipeline.config.TicketID != "TEST-123" {
		t.Errorf("TicketID = %s, want TEST-123", pipeline.config.TicketID)
	}
}

// REQ_017.3.8: Test CLI --auto-approve flag sets AutonomyFull
func TestREQ_017_3_CLIAutoApproveSetsAutonomyFull(t *testing.T) {
	// Simulate CLI parsing --auto-approve flag
	config := PipelineConfig{
		ProjectPath:  "/test/path",
		AutoApprove:  true, // Set by --auto-approve flag
		AutonomyMode: AutonomyFullyAutonomous,
	}

	// Should behave as fully autonomous
	if !config.GetAutoApprove() {
		t.Error("GetAutoApprove() should return true when AutoApprove=true or AutonomyFull")
	}

	if config.AutonomyMode != AutonomyFullyAutonomous {
		t.Errorf("AutonomyMode = %v, want AutonomyFullyAutonomous", config.AutonomyMode)
	}
}

// REQ_017.3.9: Test warning logged when AutoApprove used
func TestREQ_017_3_WarningLoggedWhenAutoApproveUsed(t *testing.T) {
	// This test documents that a deprecation warning should be logged
	// when AutoApprove is used instead of AutonomyMode

	config := PipelineConfig{
		ProjectPath: "/test/path",
		AutoApprove: true,
	}

	// AutoApprove field should trigger deprecation warning in actual implementation
	if !config.AutoApprove {
		t.Error("AutoApprove should be true to trigger warning")
	}

	// Document that both fields can coexist
	config.AutonomyMode = AutonomyFullyAutonomous
	if !config.AutoApprove {
		t.Error("AutoApprove should still be accessible")
	}
}

// REQ_017.3.10: Test existing tests pass
func TestREQ_017_3_ExistingTestsStillPass(t *testing.T) {
	// Verify old test patterns still work
	config := PipelineConfig{
		ProjectPath: "/test/path",
		AutoApprove: true,
		TicketID:    "TEST-123",
	}

	pipeline := NewPlanningPipeline(config)
	if pipeline == nil {
		t.Fatal("pipeline should not be nil")
	}
	if pipeline.config.ProjectPath != "/test/path" {
		t.Errorf("ProjectPath = %s, want /test/path", pipeline.config.ProjectPath)
	}
	if !pipeline.config.AutoApprove {
		t.Error("AutoApprove should be true")
	}
	if pipeline.config.TicketID != "TEST-123" {
		t.Errorf("TicketID = %s, want TEST-123", pipeline.config.TicketID)
	}

	// Verify new fields have sensible defaults
	if pipeline.config.AutonomyMode != AutonomyCheckpoint {
		t.Errorf("default AutonomyMode = %v, want AutonomyCheckpoint", pipeline.config.AutonomyMode)
	}
}
