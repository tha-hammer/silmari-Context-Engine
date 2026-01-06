package cli

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/spf13/cobra"
)

// resetLoopRunnerCmd resets loop runner flags for testing
func resetLoopRunnerCmd() {
	lrProjectPath = ""
	lrFeaturesPath = ""
	lrModel = "sonnet"
	lrMaxSessions = 100
	lrMaxIter = 0
	lrTimeout = 0
	lrParallel = 1
	lrDryRun = false
	lrResume = false
	lrVerbose = false
	lrInteractive = false
	lrSkipReview = false
	lrValidate = false
	lrShowBlocked = false
	lrUnblock = ""
	lrQAMode = "full"
	lrMetrics = false
	debug = false
}

// executeLoopRunnerCommand executes the loop runner command with args
func executeLoopRunnerCommand(root *cobra.Command, args ...string) (output string, err error) {
	buf := new(bytes.Buffer)
	root.SetOut(buf)
	root.SetErr(buf)
	root.SetArgs(args)
	err = root.Execute()
	return buf.String(), err
}

// TestLoopRunnerCommand_Defaults tests loop runner has correct defaults
func TestLoopRunnerCommand_Defaults(t *testing.T) {
	resetLoopRunnerCmd()

	if loopRunnerCmd.Use != "loop-runner [project]" {
		t.Errorf("Expected Use to be 'loop-runner [project]', got '%s'", loopRunnerCmd.Use)
	}

	if !strings.Contains(loopRunnerCmd.Short, "Autonomous loop runner") {
		t.Errorf("Expected Short to contain 'Autonomous loop runner', got '%s'", loopRunnerCmd.Short)
	}
}

// TestLoopRunnerCommand_Help tests help output
func TestLoopRunnerCommand_Help(t *testing.T) {
	resetLoopRunnerCmd()

	output, err := executeLoopRunnerCommand(loopRunnerCmd, "--help")
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	expectedFlags := []string{
		"--features",
		"--model",
		"--max-sessions",
		"--timeout",
		"--parallel",
		"--dry-run",
		"--resume",
		"--verbose",
		"--validate",
		"--show-blocked",
		"--unblock",
		"--qa-mode",
		"--metrics",
	}

	for _, flag := range expectedFlags {
		if !strings.Contains(output, flag) {
			t.Errorf("Expected help to contain flag '%s'", flag)
		}
	}
}

// TestLoopRunnerCommand_ShortFlags tests short flag aliases
func TestLoopRunnerCommand_ShortFlags(t *testing.T) {
	tests := []struct {
		shortFlag string
		longFlag  string
	}{
		{"-f", "--features"},
		{"-m", "--model"},
		{"-n", "--max-sessions"},
		{"-P", "--parallel"},
		{"-v", "--verbose"},
		{"-i", "--interactive"},
		{"-d", "--debug"},
	}

	output, _ := executeLoopRunnerCommand(loopRunnerCmd, "--help")

	for _, tt := range tests {
		t.Run(tt.shortFlag, func(t *testing.T) {
			if !strings.Contains(output, tt.shortFlag) {
				t.Errorf("Expected help to contain short flag '%s'", tt.shortFlag)
			}
		})
	}
}

// TestLoopRunnerCommand_FlagsExist tests all flags are registered
func TestLoopRunnerCommand_FlagsExist(t *testing.T) {
	flags := []string{
		"features", "model", "max-sessions", "max-iterations", "timeout",
		"parallel", "dry-run", "resume", "verbose", "interactive",
		"skip-review", "validate", "show-blocked", "unblock", "qa-mode", "metrics",
	}

	for _, flag := range flags {
		t.Run(flag, func(t *testing.T) {
			f := loopRunnerCmd.Flags().Lookup(flag)
			if f == nil {
				t.Errorf("Expected flag '%s' to exist", flag)
			}
		})
	}
}

// TestLoopRunnerCommand_DefaultValues tests flag default values
func TestLoopRunnerCommand_DefaultValues(t *testing.T) {
	tests := []struct {
		flag     string
		expected string
	}{
		{"model", "sonnet"},
		{"max-sessions", "100"},
		{"parallel", "1"},
		{"qa-mode", "full"},
		{"timeout", "1h0m0s"},
	}

	for _, tt := range tests {
		t.Run(tt.flag, func(t *testing.T) {
			f := loopRunnerCmd.Flags().Lookup(tt.flag)
			if f == nil {
				t.Fatalf("Flag '%s' not found", tt.flag)
			}
			if f.DefValue != tt.expected {
				t.Errorf("Expected default value '%s' for flag '%s', got '%s'", tt.expected, tt.flag, f.DefValue)
			}
		})
	}
}

// TestLoopRunnerCommand_Version tests version output
func TestLoopRunnerCommand_Version(t *testing.T) {
	resetLoopRunnerCmd()

	output, err := executeLoopRunnerCommand(loopRunnerCmd, "--version")
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	if !strings.Contains(output, "loop-runner") {
		t.Errorf("Expected version output to contain 'loop-runner', got '%s'", output)
	}
}

// TestLoopRunnerCommand_ValidateChoice tests the validateChoice function
func TestLoopRunnerCommand_ValidateChoice(t *testing.T) {
	// Test model validation
	modelTests := []struct {
		model     string
		shouldErr bool
	}{
		{"sonnet", false},
		{"opus", false},
		{"invalid", true},
	}

	for _, tt := range modelTests {
		t.Run("model_"+tt.model, func(t *testing.T) {
			err := validateChoice(tt.model, validModels, "model")
			if tt.shouldErr && err == nil {
				t.Errorf("Expected error for model '%s', got none", tt.model)
			}
			if !tt.shouldErr && err != nil {
				t.Errorf("Unexpected error for model '%s': %v", tt.model, err)
			}
		})
	}

	// Test QA mode validation
	qaModeTests := []struct {
		mode      string
		shouldErr bool
	}{
		{"full", false},
		{"lite", false},
		{"invalid", true},
	}

	for _, tt := range qaModeTests {
		t.Run("qamode_"+tt.mode, func(t *testing.T) {
			err := validateChoice(tt.mode, validQAModes, "qa-mode")
			if tt.shouldErr && err == nil {
				t.Errorf("Expected error for qa-mode '%s', got none", tt.mode)
			}
			if !tt.shouldErr && err != nil {
				t.Errorf("Unexpected error for qa-mode '%s': %v", tt.mode, err)
			}
		})
	}
}

// TestLoopRunnerCommand_PathValidation tests path validation
func TestLoopRunnerCommand_PathValidation(t *testing.T) {
	tmpDir := t.TempDir()
	featuresFile := filepath.Join(tmpDir, "features.json")
	if err := os.WriteFile(featuresFile, []byte(`{"features":[]}`), 0644); err != nil {
		t.Fatalf("Failed to create test features file: %v", err)
	}

	t.Run("existing path validates", func(t *testing.T) {
		err := validatePath(tmpDir, "project")
		if err != nil {
			t.Errorf("Unexpected error for existing path: %v", err)
		}
	})

	t.Run("non-existing path fails validation", func(t *testing.T) {
		err := validatePath("/nonexistent/path/abc123", "project")
		if err == nil {
			t.Error("Expected error for non-existent path, got none")
		}
		if !strings.Contains(err.Error(), "path does not exist") {
			t.Errorf("Expected 'path does not exist' error, got: %v", err)
		}
	})
}
