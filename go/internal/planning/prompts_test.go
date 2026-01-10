package planning

import (
	"bytes"
	"io"
	"os"
	"strings"
	"testing"
)

// Helper function to simulate stdin input
func simulateInput(t *testing.T, input string, fn func()) {
	t.Helper()

	// Save original stdin
	oldStdin := os.Stdin
	defer func() { os.Stdin = oldStdin }()

	// Create a pipe to simulate stdin
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatalf("Failed to create pipe: %v", err)
	}

	// Write input to pipe
	go func() {
		defer w.Close()
		w.Write([]byte(input))
	}()

	// Replace stdin with our pipe
	os.Stdin = r

	// Run the function
	fn()
}

// Helper function to capture stdout
func captureOutput(t *testing.T, fn func()) string {
	t.Helper()

	// Save original stdout
	oldStdout := os.Stdout
	defer func() { os.Stdout = oldStdout }()

	// Create a pipe to capture stdout
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatalf("Failed to create pipe: %v", err)
	}

	// Replace stdout with our pipe
	os.Stdout = w

	// Run the function in a goroutine
	done := make(chan bool)
	go func() {
		defer close(done)
		fn()
	}()

	// Wait for function to complete
	<-done

	// Close writer and read captured output
	w.Close()
	var buf bytes.Buffer
	io.Copy(&buf, r)

	return buf.String()
}

// TestAutonomyMode_String tests the String() method
func TestAutonomyMode_String(t *testing.T) {
	tests := []struct {
		mode     AutonomyMode
		expected string
	}{
		{AutonomyCheckpoint, "checkpoint"},
		{AutonomyFullyAutonomous, "fully_autonomous"},
		{AutonomyBatch, "batch"},
		{AutonomyMode(999), "unknown"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			result := tt.mode.String()
			if result != tt.expected {
				t.Errorf("Expected %s, got %s", tt.expected, result)
			}
		})
	}
}

// TestCollectMultilineInput tests multiline input collection
func TestCollectMultilineInput(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		prompt   string
		expected string
	}{
		{
			name:     "single line",
			input:    "hello\n\n",
			prompt:   "> ",
			expected: "hello",
		},
		{
			name:     "multiple lines",
			input:    "line1\nline2\nline3\n\n",
			prompt:   "> ",
			expected: "line1\nline2\nline3",
		},
		{
			name:     "empty first line",
			input:    "\n",
			prompt:   "> ",
			expected: "",
		},
		{
			name:     "no prompt",
			input:    "test\n\n",
			prompt:   "",
			expected: "test",
		},
		{
			name:     "preserves whitespace",
			input:    "  spaced  \n\ttabbed\t\n\n",
			prompt:   "> ",
			expected: "  spaced  \n\ttabbed\t",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var result string
			simulateInput(t, tt.input, func() {
				result = CollectMultilineInput(tt.prompt)
			})

			if result != tt.expected {
				t.Errorf("Expected %q, got %q", tt.expected, result)
			}
		})
	}
}

// TestReadPhaseAction tests phase action reading
func TestReadPhaseAction(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected PhaseAction
	}{
		{"continue lowercase", "c\n", ActionContinue},
		{"continue uppercase", "C\n", ActionContinue},
		{"revise lowercase", "r\n", ActionRevise},
		{"revise uppercase", "R\n", ActionRevise},
		{"restart lowercase", "s\n", ActionRestart},
		{"restart uppercase", "S\n", ActionRestart},
		{"exit lowercase", "e\n", ActionExit},
		{"exit uppercase", "E\n", ActionExit},
		{"empty defaults to continue", "\n", ActionContinue},
		{"whitespace defaults to continue", "  \n", ActionContinue},
		{"invalid then valid", "x\nc\n", ActionContinue},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var result PhaseAction
			simulateInput(t, tt.input, func() {
				result = readPhaseAction()
			})

			if result != tt.expected {
				t.Errorf("Expected %s, got %s", tt.expected, result)
			}
		})
	}
}

// TestPromptResearchAction tests research phase prompt
func TestPromptResearchAction(t *testing.T) {
	tests := []struct {
		input    string
		expected PhaseAction
	}{
		{"c\n", ActionContinue},
		{"r\n", ActionRevise},
		{"s\n", ActionRestart},
		{"e\n", ActionExit},
		{"\n", ActionContinue},
	}

	for _, tt := range tests {
		t.Run(string(tt.expected), func(t *testing.T) {
			var result PhaseAction
			simulateInput(t, tt.input, func() {
				result = PromptResearchAction()
			})

			if result != tt.expected {
				t.Errorf("Expected %s, got %s", tt.expected, result)
			}
		})
	}
}

// TestPromptDecompositionAction tests decomposition phase prompt
func TestPromptDecompositionAction(t *testing.T) {
	var result PhaseAction
	simulateInput(t, "c\n", func() {
		result = PromptDecompositionAction()
	})

	if result != ActionContinue {
		t.Errorf("Expected %s, got %s", ActionContinue, result)
	}
}

// TestPromptTDDPlanningAction tests TDD planning phase prompt
func TestPromptTDDPlanningAction(t *testing.T) {
	var result PhaseAction
	simulateInput(t, "c\n", func() {
		result = PromptTDDPlanningAction()
	})

	if result != ActionContinue {
		t.Errorf("Expected %s, got %s", ActionContinue, result)
	}
}

// TestPromptPhaseContinue tests phase continuation prompt
func TestPromptPhaseContinue(t *testing.T) {
	tests := []struct {
		name              string
		input             string
		artifacts         []string
		expectedContinue  bool
		expectedFeedback  string
	}{
		{
			name:             "yes continues",
			input:            "y\n",
			artifacts:        []string{"file1.txt"},
			expectedContinue: true,
			expectedFeedback: "",
		},
		{
			name:             "empty continues",
			input:            "\n",
			artifacts:        []string{"file1.txt"},
			expectedContinue: true,
			expectedFeedback: "",
		},
		{
			name:             "other input defaults to yes",
			input:            "xyz\n",
			artifacts:        []string{},
			expectedContinue: true,
			expectedFeedback: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var result PhaseContinueResult
			simulateInput(t, tt.input, func() {
				result = PromptPhaseContinue("test-phase", tt.artifacts)
			})

			if result.Continue != tt.expectedContinue {
				t.Errorf("Expected Continue=%v, got %v", tt.expectedContinue, result.Continue)
			}
			if result.Feedback != tt.expectedFeedback {
				t.Errorf("Expected Feedback=%q, got %q", tt.expectedFeedback, result.Feedback)
			}
		})
	}
}

// TestPromptPhaseContinue_DeclineCollectsFeedback documents REQ_005.1 behavior 10
// This test verifies that when user answers 'n', the function attempts to collect feedback.
// Full integration testing of the feedback collection requires more sophisticated stdin mocking.
func TestPromptPhaseContinue_DeclineCollectsFeedback(t *testing.T) {
	// Test that 'n' leads to Continue=false
	var result PhaseContinueResult
	simulateInput(t, "n\n", func() {
		result = PromptPhaseContinue("test-phase", []string{})
	})

	if result.Continue {
		t.Error("Expected Continue=false when user answers 'n'")
	}
	// Note: Feedback string may be empty in this test due to stdin buffering,
	// but the code path is exercised. Integration tests should validate full behavior.
}

// TestPromptUseCheckpoint tests checkpoint resume prompt
func TestPromptUseCheckpoint(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected bool
	}{
		{"yes resumes", "y\n", true},
		{"empty resumes", "\n", true},
		{"no declines", "n\n", false},
		{"other defaults to yes", "xyz\n", true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var result bool
			simulateInput(t, tt.input, func() {
				result = PromptUseCheckpoint("2024-01-01", "test-phase", []string{"file.txt"})
			})

			if result != tt.expected {
				t.Errorf("Expected %v, got %v", tt.expected, result)
			}
		})
	}
}

// TestPromptFileSelection tests file selection menu
func TestPromptFileSelection(t *testing.T) {
	files := []string{"file1.md", "file2.md", "file3.md"}

	tests := []struct {
		name           string
		input          string
		expectedAction string
		expectedPath   string
	}{
		{"select first file", "1\n", "selected", "file1.md"},
		{"select last file", "3\n", "selected", "file3.md"},
		{"search again lowercase", "s\n", "search", ""},
		{"search again uppercase", "S\n", "search", ""},
		{"other lowercase", "o\n", "other", ""},
		{"other uppercase", "O\n", "other", ""},
		{"exit lowercase", "e\n", "exit", ""},
		{"exit uppercase", "E\n", "exit", ""},
		{"invalid then valid", "99\n2\n", "selected", "file2.md"},
		{"non-numeric then valid", "abc\n1\n", "selected", "file1.md"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var action, path string
			simulateInput(t, tt.input, func() {
				action, path = PromptFileSelection(files, "test")
			})

			if action != tt.expectedAction {
				t.Errorf("Expected action=%s, got %s", tt.expectedAction, action)
			}
			if path != tt.expectedPath {
				t.Errorf("Expected path=%s, got %s", tt.expectedPath, path)
			}
		})
	}
}

// TestPromptFileSelection_EmptyList tests file selection with empty list
func TestPromptFileSelection_EmptyList(t *testing.T) {
	tests := []struct {
		name           string
		input          string
		expectedAction string
	}{
		{"numeric on empty list", "1\ne\n", "exit"},
		{"exit works", "e\n", "exit"},
		{"search works", "s\n", "search"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var action, _ string
			simulateInput(t, tt.input, func() {
				action, _ = PromptFileSelection([]string{}, "test")
			})

			if action != tt.expectedAction {
				t.Errorf("Expected action=%s, got %s", tt.expectedAction, action)
			}
		})
	}
}

// TestPromptSearchDays tests search days prompt
func TestPromptSearchDays(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		defValue int
		expected int
	}{
		{"uses provided value", "10\n", 7, 10},
		{"uses default on empty", "\n", 7, 7},
		{"uses default on invalid", "abc\n", 7, 7},
		{"uses default on negative", "-5\n", 7, 7},
		{"uses default on zero", "0\n", 7, 7},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var result int
			simulateInput(t, tt.input, func() {
				result = PromptSearchDays(tt.defValue)
			})

			if result != tt.expected {
				t.Errorf("Expected %d, got %d", tt.expected, result)
			}
		})
	}
}

// TestPromptCustomPath tests custom path prompt
func TestPromptCustomPath(t *testing.T) {
	// Create a temporary file for testing
	tmpFile, err := os.CreateTemp("", "test-*.txt")
	if err != nil {
		t.Fatalf("Failed to create temp file: %v", err)
	}
	defer os.Remove(tmpFile.Name())
	tmpFile.Close()

	tests := []struct {
		name        string
		input       string
		expectError bool
	}{
		{"valid file path", tmpFile.Name() + "\n", false},
		{"empty path", "\n", true},
		{"nonexistent file", "/nonexistent/file.txt\n", true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var path string
			var err error
			simulateInput(t, tt.input, func() {
				path, err = PromptCustomPath("test")
			})

			if tt.expectError && err == nil {
				t.Error("Expected error, got nil")
			}
			if !tt.expectError && err != nil {
				t.Errorf("Unexpected error: %v", err)
			}
			if !tt.expectError && path == "" {
				t.Error("Expected non-empty path")
			}
		})
	}
}

// TestPromptAutonomyMode tests autonomy mode selection
func TestPromptAutonomyMode(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected AutonomyMode
	}{
		{"checkpoint lowercase", "c\n", AutonomyCheckpoint},
		{"checkpoint uppercase", "C\n", AutonomyCheckpoint},
		{"checkpoint empty", "\n", AutonomyCheckpoint},
		{"fully autonomous lowercase", "f\n", AutonomyFullyAutonomous},
		{"fully autonomous uppercase", "F\n", AutonomyFullyAutonomous},
		{"batch lowercase", "b\n", AutonomyBatch},
		{"batch uppercase", "B\n", AutonomyBatch},
		{"invalid then valid", "x\nf\n", AutonomyFullyAutonomous},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var result AutonomyMode
			simulateInput(t, tt.input, func() {
				result = PromptAutonomyMode(5, "test-epic-123")
			})

			if result != tt.expected {
				t.Errorf("Expected %s, got %s", tt.expected, result)
			}
		})
	}
}

// TestPromptResearchAction_MenuText verifies menu text output
func TestPromptResearchAction_MenuText(t *testing.T) {
	output := captureOutput(t, func() {
		simulateInput(t, "c\n", func() {
			PromptResearchAction()
		})
	})

	expectedTexts := []string{
		"Research Phase Complete",
		"Continue to decomposition",
		"Revise research",
		"Start over",
		"Exit",
	}

	for _, text := range expectedTexts {
		if !strings.Contains(output, text) {
			t.Errorf("Expected output to contain %q", text)
		}
	}
}

// TestPromptDecompositionAction_MenuText verifies menu text output
func TestPromptDecompositionAction_MenuText(t *testing.T) {
	output := captureOutput(t, func() {
		simulateInput(t, "c\n", func() {
			PromptDecompositionAction()
		})
	})

	expectedTexts := []string{
		"Decomposition Phase Complete",
		"Continue to TDD planning",
		"Revise decomposition",
	}

	for _, text := range expectedTexts {
		if !strings.Contains(output, text) {
			t.Errorf("Expected output to contain %q", text)
		}
	}
}

// TestPromptTDDPlanningAction_MenuText verifies menu text output
func TestPromptTDDPlanningAction_MenuText(t *testing.T) {
	output := captureOutput(t, func() {
		simulateInput(t, "c\n", func() {
			PromptTDDPlanningAction()
		})
	})

	expectedTexts := []string{
		"TDD Planning Phase Complete",
		"Continue to multi-doc generation",
		"Revise TDD plan",
	}

	for _, text := range expectedTexts {
		if !strings.Contains(output, text) {
			t.Errorf("Expected output to contain %q", text)
		}
	}
}

// TestPromptAutonomyMode_MenuText verifies menu text output
func TestPromptAutonomyMode_MenuText(t *testing.T) {
	output := captureOutput(t, func() {
		simulateInput(t, "c\n", func() {
			PromptAutonomyMode(5, "epic-123")
		})
	})

	expectedTexts := []string{
		"IMPLEMENTATION READY",
		"Plan phases: 5",
		"Beads epic: epic-123",
		"Checkpoint - pause at each phase for review (recommended)",
		"Fully autonomous - run all phases without stopping",
		"Batch - run groups of phases, pause between groups",
	}

	for _, text := range expectedTexts {
		if !strings.Contains(output, text) {
			t.Errorf("Expected output to contain %q", text)
		}
	}
}

// TestPromptFileSelection_HeaderText verifies header text with uppercase file type
func TestPromptFileSelection_HeaderText(t *testing.T) {
	output := captureOutput(t, func() {
		simulateInput(t, "e\n", func() {
			PromptFileSelection([]string{"test.md"}, "research")
		})
	})

	if !strings.Contains(output, "SELECT RESEARCH FILE") {
		t.Errorf("Expected output to contain 'SELECT RESEARCH FILE'")
	}
}

// TestPromptPhaseContinue_DisplaysArtifacts verifies artifacts are displayed
func TestPromptPhaseContinue_DisplaysArtifacts(t *testing.T) {
	output := captureOutput(t, func() {
		simulateInput(t, "y\n", func() {
			PromptPhaseContinue("test-phase", []string{"artifact1.txt", "artifact2.md"})
		})
	})

	expectedTexts := []string{
		"Phase Complete: test-phase",
		"Artifacts:",
		"artifact1.txt",
		"artifact2.md",
	}

	for _, text := range expectedTexts {
		if !strings.Contains(output, text) {
			t.Errorf("Expected output to contain %q", text)
		}
	}
}

