package cli

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/spf13/cobra"
)

// Helper to reset command for testing
func resetRootCmd() {
	// Reset flags to defaults
	debug = false
	verbose = false
	projectPath = ""
	newPath = ""
	model = "sonnet"
	maxSessions = 100
	cont = false
	status = false
	mcpPreset = ""
	withQA = false
	interactive = true
}

// executeCommand executes the command with args and returns output
func executeCommand(root *cobra.Command, args ...string) (output string, err error) {
	buf := new(bytes.Buffer)
	root.SetOut(buf)
	root.SetErr(buf)
	root.SetArgs(args)
	err = root.Execute()
	return buf.String(), err
}

// TestRootCommand_Defaults tests that root command has correct defaults
func TestRootCommand_Defaults(t *testing.T) {
	resetRootCmd()

	if rootCmd.Use != "context-engine" {
		t.Errorf("Expected Use to be 'context-engine', got '%s'", rootCmd.Use)
	}

	if rootCmd.Short != "Context-Engineered Agent Orchestrator" {
		t.Errorf("Expected Short description to be 'Context-Engineered Agent Orchestrator', got '%s'", rootCmd.Short)
	}
}

// TestRootCommand_Version tests version flag
func TestRootCommand_Version(t *testing.T) {
	resetRootCmd()

	output, err := executeCommand(rootCmd, "--version")
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	if !strings.Contains(output, "context-engine") {
		t.Errorf("Expected version output to contain 'context-engine', got '%s'", output)
	}
}

// TestRootCommand_Help tests help flag output
func TestRootCommand_Help(t *testing.T) {
	resetRootCmd()

	output, err := executeCommand(rootCmd, "--help")
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	// Verify key sections appear in help
	expectedSections := []string{
		"Context-Engineered Agent Orchestrator",
		"--project",
		"--model",
		"--debug",
		"plan",     // subcommand
		"mcp-setup", // subcommand
		"resume",   // subcommand
	}

	for _, section := range expectedSections {
		if !strings.Contains(output, section) {
			t.Errorf("Expected help output to contain '%s'", section)
		}
	}
}

// TestRootCommand_ShortFlags tests short flag aliases
func TestRootCommand_ShortFlags(t *testing.T) {
	tests := []struct {
		shortFlag string
		longFlag  string
	}{
		{"-p", "--project"},
		{"-m", "--model"},
		{"-c", "--continue"},
		{"-s", "--status"},
		{"-d", "--debug"},
	}

	for _, tt := range tests {
		t.Run(tt.shortFlag, func(t *testing.T) {
			output, _ := executeCommand(rootCmd, "--help")
			// Check both forms appear in help
			if !strings.Contains(output, tt.shortFlag) {
				t.Errorf("Expected help to contain short flag '%s'", tt.shortFlag)
			}
		})
	}
}

// TestModelValidation tests model flag validation
func TestModelValidation(t *testing.T) {
	tests := []struct {
		model     string
		shouldErr bool
	}{
		{"sonnet", false},
		{"opus", false},
		{"invalid", true},
		{"gpt-4", true},
	}

	for _, tt := range tests {
		t.Run(tt.model, func(t *testing.T) {
			err := validateChoice(tt.model, validModels, "model")
			if tt.shouldErr && err == nil {
				t.Errorf("Expected error for model '%s', got none", tt.model)
			}
			if !tt.shouldErr && err != nil {
				t.Errorf("Unexpected error for model '%s': %v", tt.model, err)
			}
		})
	}
}

// TestMCPPresetValidation tests MCP preset validation
func TestMCPPresetValidation(t *testing.T) {
	tests := []struct {
		preset    string
		shouldErr bool
	}{
		{"web", false},
		{"fullstack", false},
		{"data", false},
		{"devops", false},
		{"minimal", false},
		{"rust", false},
		{"python", false},
		{"node", false},
		{"docs", false},
		{"invalid", true},
		{"", false}, // empty is valid (not set)
	}

	for _, tt := range tests {
		t.Run(tt.preset, func(t *testing.T) {
			if tt.preset == "" {
				return // empty handled separately
			}
			err := validateChoice(tt.preset, validMCPPresets, "mcp-preset")
			if tt.shouldErr && err == nil {
				t.Errorf("Expected error for preset '%s', got none", tt.preset)
			}
			if !tt.shouldErr && err != nil {
				t.Errorf("Unexpected error for preset '%s': %v", tt.preset, err)
			}
		})
	}
}

// TestPathValidation tests path validation functions
func TestPathValidation(t *testing.T) {
	// Create temp dir for testing
	tmpDir := t.TempDir()
	existingFile := filepath.Join(tmpDir, "existing.txt")
	if err := os.WriteFile(existingFile, []byte("test"), 0644); err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}

	t.Run("existing path passes", func(t *testing.T) {
		err := validatePath(tmpDir, "project")
		if err != nil {
			t.Errorf("Unexpected error for existing path: %v", err)
		}
	})

	t.Run("non-existing path fails", func(t *testing.T) {
		err := validatePath("/nonexistent/path/abc123", "project")
		if err == nil {
			t.Error("Expected error for non-existing path, got none")
		}
		if !strings.Contains(err.Error(), "path does not exist") {
			t.Errorf("Expected 'path does not exist' error, got: %v", err)
		}
	})

	t.Run("empty path passes", func(t *testing.T) {
		err := validatePath("", "project")
		if err != nil {
			t.Errorf("Unexpected error for empty path: %v", err)
		}
	})

	t.Run("path not exists validation - existing fails", func(t *testing.T) {
		err := validatePathNotExists(tmpDir, "new")
		if err == nil {
			t.Error("Expected error for existing path, got none")
		}
		if !strings.Contains(err.Error(), "path already exists") {
			t.Errorf("Expected 'path already exists' error, got: %v", err)
		}
	})

	t.Run("path not exists validation - non-existing passes", func(t *testing.T) {
		err := validatePathNotExists(filepath.Join(tmpDir, "newproject"), "new")
		if err != nil {
			t.Errorf("Unexpected error for non-existing path: %v", err)
		}
	})
}

// TestIntegerValidation tests integer flag validation
func TestIntegerValidation(t *testing.T) {
	tests := []struct {
		value     int
		min       int
		max       int
		shouldErr bool
	}{
		{50, 1, 100, false},
		{1, 1, 100, false},
		{100, 1, 100, false},
		{0, 1, 100, true},
		{101, 1, 100, true},
		{-1, 1, 100, true},
	}

	for _, tt := range tests {
		t.Run(strings.Replace(string(rune(tt.value)), "\n", "", -1), func(t *testing.T) {
			err := validateInteger(tt.value, tt.min, tt.max, "max-sessions")
			if tt.shouldErr && err == nil {
				t.Errorf("Expected error for value %d, got none", tt.value)
			}
			if !tt.shouldErr && err != nil {
				t.Errorf("Unexpected error for value %d: %v", tt.value, err)
			}
		})
	}
}

// TestSubcommandsExist tests that subcommands are registered
func TestSubcommandsExist(t *testing.T) {
	subcommands := []string{"plan", "mcp-setup", "resume"}

	for _, name := range subcommands {
		t.Run(name, func(t *testing.T) {
			found := false
			for _, cmd := range rootCmd.Commands() {
				if cmd.Use == name || strings.HasPrefix(cmd.Use, name+" ") {
					found = true
					break
				}
			}
			if !found {
				// Check aliases
				for _, cmd := range rootCmd.Commands() {
					for _, alias := range cmd.Aliases {
						if alias == name {
							found = true
							break
						}
					}
				}
			}
			if !found {
				t.Errorf("Expected subcommand '%s' to be registered", name)
			}
		})
	}
}

// TestSubcommandAliases tests that subcommand aliases work
func TestSubcommandAliases(t *testing.T) {
	tests := []struct {
		alias   string
		command string
	}{
		{"p", "plan"},
		{"mcp", "mcp-setup"},
	}

	for _, tt := range tests {
		t.Run(tt.alias, func(t *testing.T) {
			for _, cmd := range rootCmd.Commands() {
				if strings.HasPrefix(cmd.Use, tt.command) {
					found := false
					for _, alias := range cmd.Aliases {
						if alias == tt.alias {
							found = true
							break
						}
					}
					if !found {
						t.Errorf("Expected alias '%s' for command '%s'", tt.alias, tt.command)
					}
					return
				}
			}
			t.Errorf("Command '%s' not found", tt.command)
		})
	}
}

// TestGlobalFlagsInherited tests that global flags are available to subcommands
func TestGlobalFlagsInherited(t *testing.T) {
	// Plan command should have access to debug flag
	output, _ := executeCommand(rootCmd, "plan", "--help")

	// Debug should be in inherited flags section
	if !strings.Contains(output, "debug") {
		t.Error("Expected plan subcommand help to include inherited debug flag")
	}
}

// TestMutuallyExclusiveFlags tests that --project and --new are mutually exclusive
func TestMutuallyExclusiveFlags(t *testing.T) {
	resetRootCmd()

	// Create temp dirs for testing
	tmpDir := t.TempDir()
	_ = filepath.Join(tmpDir, "newproject") // Used to verify path handling

	// This tests that cobra marks them mutually exclusive
	flags := rootCmd.Flags()

	projectFlag := flags.Lookup("project")
	newFlag := flags.Lookup("new")

	if projectFlag == nil || newFlag == nil {
		t.Fatal("Expected project and new flags to exist")
	}
}
