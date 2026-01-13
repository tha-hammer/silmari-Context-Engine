package cli

import (
	"strings"
	"testing"
)

// TestPlanCommand_Defaults tests plan command defaults
func TestPlanCommand_Defaults(t *testing.T) {
	if planCmd.Use != "plan" {
		t.Errorf("Expected Use to be 'plan', got '%s'", planCmd.Use)
	}

	// Check alias
	found := false
	for _, alias := range planCmd.Aliases {
		if alias == "p" {
			found = true
			break
		}
	}
	if !found {
		t.Error("Expected plan command to have alias 'p'")
	}
}

// TestPlanCommand_Help tests plan command help output
func TestPlanCommand_Help(t *testing.T) {
	output, err := executeCommand(rootCmd, "plan", "--help")
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	expectedFlags := []string{
		"--project",
		"--ticket",
		"--auto-approve",
		"--prompt-text",
		"--resume",
		"--resume-step",
		"--research-path",
		"--plan-path",
	}

	for _, flag := range expectedFlags {
		if !strings.Contains(output, flag) {
			t.Errorf("Expected plan help to contain flag '%s'", flag)
		}
	}
}

// TestPlanCommand_ShortFlags tests plan command short flags
func TestPlanCommand_ShortFlags(t *testing.T) {
	output, _ := executeCommand(rootCmd, "plan", "--help")

	shortFlags := []string{"-p", "-t", "-y", "-r"}
	for _, flag := range shortFlags {
		if !strings.Contains(output, flag) {
			t.Errorf("Expected plan help to contain short flag '%s'", flag)
		}
	}
}

// TestPlanCommand_FlagsExist tests all plan flags are registered
func TestPlanCommand_FlagsExist(t *testing.T) {
	flags := []string{
		"project", "ticket", "auto-approve", "prompt-text",
		"resume", "resume-step", "research-path", "plan-path",
	}

	for _, flag := range flags {
		t.Run(flag, func(t *testing.T) {
			f := planCmd.Flags().Lookup(flag)
			if f == nil {
				t.Errorf("Expected flag '%s' to exist", flag)
			}
		})
	}
}

// TestPlanCommand_ResumeStepValidation tests resume step validation
func TestPlanCommand_ResumeStepValidation(t *testing.T) {
	tests := []struct {
		step      string
		shouldErr bool
	}{
		{"planning", false},
		{"requirement_decomposition", false},
		{"phase_decomposition", false},
		{"invalid", true},
	}

	for _, tt := range tests {
		t.Run(tt.step, func(t *testing.T) {
			err := validateChoice(tt.step, validResumeSteps, "resume-step")
			if tt.shouldErr && err == nil {
				t.Errorf("Expected error for step '%s', got none", tt.step)
			}
			if !tt.shouldErr && err != nil {
				t.Errorf("Unexpected error for step '%s': %v", tt.step, err)
			}
		})
	}
}

// TestPlanCommand_UnderscoredFlags tests backwards compatibility with underscored flags
func TestPlanCommand_UnderscoredFlags(t *testing.T) {
	// Test that underscore flags are normalized to dashes
	normalized := normalizeUnderscoredFlags(nil, "resume_step")
	if string(normalized) != "resume-step" {
		t.Errorf("Expected 'resume_step' to normalize to 'resume-step', got '%s'", normalized)
	}

	normalized = normalizeUnderscoredFlags(nil, "research_path")
	if string(normalized) != "research-path" {
		t.Errorf("Expected 'research_path' to normalize to 'research-path', got '%s'", normalized)
	}
}

// TestMCPSetupCommand_Defaults tests mcp-setup command defaults
func TestMCPSetupCommand_Defaults(t *testing.T) {
	if mcpSetupCmd.Use != "mcp-setup" {
		t.Errorf("Expected Use to be 'mcp-setup', got '%s'", mcpSetupCmd.Use)
	}

	// Check alias
	found := false
	for _, alias := range mcpSetupCmd.Aliases {
		if alias == "mcp" {
			found = true
			break
		}
	}
	if !found {
		t.Error("Expected mcp-setup command to have alias 'mcp'")
	}
}

// TestMCPSetupCommand_Help tests mcp-setup command help output
func TestMCPSetupCommand_Help(t *testing.T) {
	output, err := executeCommand(rootCmd, "mcp-setup", "--help")
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	expectedFlags := []string{
		"--project",
		"--preset",
		"--add",
		"--list",
		"--smart",
		"--output",
	}

	for _, flag := range expectedFlags {
		if !strings.Contains(output, flag) {
			t.Errorf("Expected mcp-setup help to contain flag '%s'", flag)
		}
	}
}

// TestMCPSetupCommand_FlagsExist tests all MCP setup flags are registered
func TestMCPSetupCommand_FlagsExist(t *testing.T) {
	flags := []string{
		"project", "preset", "add", "list", "smart", "output",
	}

	for _, flag := range flags {
		t.Run(flag, func(t *testing.T) {
			f := mcpSetupCmd.Flags().Lookup(flag)
			if f == nil {
				t.Errorf("Expected flag '%s' to exist", flag)
			}
		})
	}
}

// TestMCPSetupCommand_PresetValidation tests preset validation
func TestMCPSetupCommand_PresetValidation(t *testing.T) {
	tests := []struct {
		preset    string
		shouldErr bool
	}{
		{"web", false},
		{"fullstack", false},
		{"rust", false},
		{"invalid", true},
	}

	for _, tt := range tests {
		t.Run(tt.preset, func(t *testing.T) {
			err := validateChoice(tt.preset, validPresets, "preset")
			if tt.shouldErr && err == nil {
				t.Errorf("Expected error for preset '%s', got none", tt.preset)
			}
			if !tt.shouldErr && err != nil {
				t.Errorf("Unexpected error for preset '%s': %v", tt.preset, err)
			}
		})
	}
}

// TestResumeCommand_Structure tests resume command structure
func TestResumeCommand_Structure(t *testing.T) {
	if resumeCmd.Use != "resume" {
		t.Errorf("Expected Use to be 'resume', got '%s'", resumeCmd.Use)
	}

	// Check subcommands
	subcommands := []string{"planning", "decomposition", "beads"}
	for _, name := range subcommands {
		found := false
		for _, cmd := range resumeCmd.Commands() {
			if cmd.Use == name || strings.HasPrefix(cmd.Use, name) {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Expected resume to have subcommand '%s'", name)
		}
	}
}

// TestResumePlanningCommand_FlagsExist tests resume planning flags
func TestResumePlanningCommand_FlagsExist(t *testing.T) {
	flags := []string{"research-path", "additional-context"}

	for _, flag := range flags {
		t.Run(flag, func(t *testing.T) {
			f := resumePlanningCmd.Flags().Lookup(flag)
			if f == nil {
				t.Errorf("Expected flag '%s' to exist", flag)
			}
		})
	}
}

// TestResumeDecompositionCommand_FlagsExist tests resume decomposition flags
func TestResumeDecompositionCommand_FlagsExist(t *testing.T) {
	f := resumeDecompositionCmd.Flags().Lookup("plan-path")
	if f == nil {
		t.Error("Expected flag 'plan-path' to exist")
	}
}

// TestResumeBeadsCommand_FlagsExist tests resume beads flags
func TestResumeBeadsCommand_FlagsExist(t *testing.T) {
	flags := []string{"phase-files", "epic-title"}

	for _, flag := range flags {
		t.Run(flag, func(t *testing.T) {
			f := resumeBeadsCmd.Flags().Lookup(flag)
			if f == nil {
				t.Errorf("Expected flag '%s' to exist", flag)
			}
		})
	}
}

// TestResumeSubcommandAliases tests resume subcommand aliases
func TestResumeSubcommandAliases(t *testing.T) {
	tests := []struct {
		alias   string
		command string
	}{
		{"plan", "planning"},
		{"decomp", "decomposition"},
	}

	for _, tt := range tests {
		t.Run(tt.alias, func(t *testing.T) {
			for _, cmd := range resumeCmd.Commands() {
				if strings.HasPrefix(cmd.Use, tt.command) {
					found := false
					for _, alias := range cmd.Aliases {
						if alias == tt.alias {
							found = true
							break
						}
					}
					if !found {
						t.Errorf("Expected alias '%s' for resume subcommand '%s'", tt.alias, tt.command)
					}
					return
				}
			}
			t.Errorf("Resume subcommand '%s' not found", tt.command)
		})
	}
}

// TestResumePlanningCommand_RequiredFlag tests that research-path is required
func TestResumePlanningCommand_RequiredFlag(t *testing.T) {
	_, err := executeCommand(rootCmd, "resume", "planning")
	if err == nil {
		t.Error("Expected error when research-path is not provided")
	}
}

// TestResumeDecompositionCommand_RequiredFlag tests that plan-path is required
func TestResumeDecompositionCommand_RequiredFlag(t *testing.T) {
	_, err := executeCommand(rootCmd, "resume", "decomposition")
	if err == nil {
		t.Error("Expected error when plan-path is not provided")
	}
}

// TestResumeBeadsCommand_RequiredFlags tests that phase-files and epic-title are required
func TestResumeBeadsCommand_RequiredFlags(t *testing.T) {
	_, err := executeCommand(rootCmd, "resume", "beads")
	if err == nil {
		t.Error("Expected error when required flags are not provided")
	}
}

// TestReviewPlanCommand_Defaults tests review-plan command defaults
func TestReviewPlanCommand_Defaults(t *testing.T) {
	if reviewPlanCmd.Use != "review-plan" {
		t.Errorf("Expected Use to be 'review-plan', got '%s'", reviewPlanCmd.Use)
	}

	// Check aliases
	expectedAliases := []string{"rp", "review"}
	for _, expected := range expectedAliases {
		found := false
		for _, alias := range reviewPlanCmd.Aliases {
			if alias == expected {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Expected review-plan command to have alias '%s'", expected)
		}
	}
}

// TestReviewPlanCommand_Help tests review-plan command help output
func TestReviewPlanCommand_Help(t *testing.T) {
	output, err := executeCommand(rootCmd, "review-plan", "--help")
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	expectedFlags := []string{
		"--plan-path",
		"--phase",
		"--step",
		"--output",
		"--autonomy-mode",
		"--all-phases",
	}

	for _, flag := range expectedFlags {
		if !strings.Contains(output, flag) {
			t.Errorf("Expected review-plan help to contain flag '%s'", flag)
		}
	}
}

// TestReviewPlanCommand_FlagsExist tests all review-plan flags are registered
func TestReviewPlanCommand_FlagsExist(t *testing.T) {
	flags := []string{
		"plan-path", "phase", "step", "output", "autonomy-mode", "all-phases",
	}

	for _, flag := range flags {
		t.Run(flag, func(t *testing.T) {
			f := reviewPlanCmd.Flags().Lookup(flag)
			if f == nil {
				t.Errorf("Expected flag '%s' to exist", flag)
			}
		})
	}
}

// TestReviewPlanCommand_PhaseValidation tests phase validation
func TestReviewPlanCommand_PhaseValidation(t *testing.T) {
	tests := []struct {
		phase     string
		shouldErr bool
	}{
		{"research", false},
		{"decomposition", false},
		{"tdd_planning", false},
		{"multi_doc", false},
		{"beads_sync", false},
		{"implementation", false},
		{"invalid", true},
	}

	for _, tt := range tests {
		t.Run(tt.phase, func(t *testing.T) {
			err := validateChoice(tt.phase, validReviewPhases, "phase")
			if tt.shouldErr && err == nil {
				t.Errorf("Expected error for phase '%s', got none", tt.phase)
			}
			if !tt.shouldErr && err != nil {
				t.Errorf("Unexpected error for phase '%s': %v", tt.phase, err)
			}
		})
	}
}

// TestReviewPlanCommand_StepValidation tests step validation
func TestReviewPlanCommand_StepValidation(t *testing.T) {
	tests := []struct {
		step      string
		shouldErr bool
	}{
		{"contracts", false},
		{"interfaces", false},
		{"promises", false},
		{"data_models", false},
		{"apis", false},
		{"invalid", true},
	}

	for _, tt := range tests {
		t.Run(tt.step, func(t *testing.T) {
			err := validateChoice(tt.step, validReviewSteps, "step")
			if tt.shouldErr && err == nil {
				t.Errorf("Expected error for step '%s', got none", tt.step)
			}
			if !tt.shouldErr && err != nil {
				t.Errorf("Unexpected error for step '%s': %v", tt.step, err)
			}
		})
	}
}

// TestReviewPlanCommand_AutonomyModeValidation tests autonomy mode validation
func TestReviewPlanCommand_AutonomyModeValidation(t *testing.T) {
	tests := []struct {
		mode      string
		shouldErr bool
	}{
		{"checkpoint", false},
		{"batch", false},
		{"fully_autonomous", false},
		{"invalid", true},
	}

	for _, tt := range tests {
		t.Run(tt.mode, func(t *testing.T) {
			err := validateChoice(tt.mode, validAutonomyModes, "autonomy-mode")
			if tt.shouldErr && err == nil {
				t.Errorf("Expected error for mode '%s', got none", tt.mode)
			}
			if !tt.shouldErr && err != nil {
				t.Errorf("Unexpected error for mode '%s': %v", tt.mode, err)
			}
		})
	}
}

// TestReviewPlanCommand_AliasesWork tests that aliases work
func TestReviewPlanCommand_AliasesWork(t *testing.T) {
	aliases := []string{"rp", "review"}
	for _, alias := range aliases {
		t.Run(alias, func(t *testing.T) {
			output, err := executeCommand(rootCmd, alias, "--help")
			if err != nil {
				t.Fatalf("Unexpected error for alias '%s': %v", alias, err)
			}
			if !strings.Contains(output, "review-plan") {
				t.Errorf("Expected help for alias '%s' to mention 'review-plan'", alias)
			}
		})
	}
}

// TestReviewPlanCommand_ShortFlags tests review-plan command short flags
func TestReviewPlanCommand_ShortFlags(t *testing.T) {
	output, _ := executeCommand(rootCmd, "review-plan", "--help")

	shortFlags := []string{"-p", "-o"}
	for _, flag := range shortFlags {
		if !strings.Contains(output, flag) {
			t.Errorf("Expected review-plan help to contain short flag '%s'", flag)
		}
	}
}
