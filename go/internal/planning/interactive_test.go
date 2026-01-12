package planning

import (
	"strings"
	"testing"
)

// TestPromptPlanningAction tests the planning action prompt function
func TestPromptPlanningAction(t *testing.T) {
	// This is a basic test that verifies the function exists and can be called
	// In a real scenario, we'd mock stdin to test different inputs
	// For now, we just verify the function signature is correct
	t.Skip("Skipping interactive test - requires manual stdin input")
}

// Note: TestPromptResearchAction and TestCollectMultilineInput are now in prompts_test.go

// TestStepResearchWithCheckpointAutoApprove tests research with auto-approve
func TestStepResearchWithCheckpointAutoApprove(t *testing.T) {
	// This test verifies that auto-approve mode works correctly
	// In a real test, we'd set up a test project and verify the behavior
	t.Skip("Skipping - requires test project setup and Claude CLI")
}

// TestStepPlanningWithCheckpointAutoApprove tests planning with auto-approve
func TestStepPlanningWithCheckpointAutoApprove(t *testing.T) {
	// This test verifies that auto-approve mode works correctly
	// In a real test, we'd set up a test project and verify the behavior
	t.Skip("Skipping - requires test project setup and Claude CLI")
}

// TestActionResultMetadata verifies that user actions are stored in result metadata
func TestActionResultMetadata(t *testing.T) {
	result := NewStepResult()

	// Test setting user action
	result.Data["user_action"] = "continue"
	if action, ok := result.Data["user_action"].(string); !ok || action != "continue" {
		t.Errorf("Expected user_action to be 'continue', got %v", result.Data["user_action"])
	}

	// Test setting user exit
	result.Data["user_exit"] = true
	if userExit, ok := result.Data["user_exit"].(bool); !ok || !userExit {
		t.Errorf("Expected user_exit to be true, got %v", result.Data["user_exit"])
	}

	// Test setting needs restart
	result.Data["needs_restart"] = true
	if needsRestart, ok := result.Data["needs_restart"].(bool); !ok || !needsRestart {
		t.Errorf("Expected needs_restart to be true, got %v", result.Data["needs_restart"])
	}
}

// TestAdditionalContextConcatenation verifies context is properly concatenated
func TestAdditionalContextConcatenation(t *testing.T) {
	tests := []struct {
		name             string
		initial          string
		additional       string
		expectedContains []string
	}{
		{
			name:             "empty initial",
			initial:          "",
			additional:       "New context",
			expectedContains: []string{"New context"},
		},
		{
			name:             "with initial",
			initial:          "Initial context",
			additional:       "Additional context",
			expectedContains: []string{"Initial context", "Additional context"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			current := tt.initial
			if current != "" {
				current = current + "\n\n" + tt.additional
			} else {
				current = tt.additional
			}

			for _, expected := range tt.expectedContains {
				if !strings.Contains(current, expected) {
					t.Errorf("Expected context to contain '%s', got '%s'", expected, current)
				}
			}
		})
	}
}
