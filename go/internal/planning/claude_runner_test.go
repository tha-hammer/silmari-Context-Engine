package planning

import (
	"testing"
)

func TestClaudeResultSuccess(t *testing.T) {
	result := &ClaudeResult{
		Success: true,
		Output:  "Test output",
	}

	if !result.Success {
		t.Error("Success should be true")
	}
	if result.Output != "Test output" {
		t.Errorf("Output = %q, want 'Test output'", result.Output)
	}
	if result.Error != "" {
		t.Error("Error should be empty for successful result")
	}
}

func TestClaudeResultFailure(t *testing.T) {
	result := &ClaudeResult{
		Success: false,
		Error:   "Something went wrong",
	}

	if result.Success {
		t.Error("Success should be false")
	}
	if result.Error != "Something went wrong" {
		t.Errorf("Error = %q, want 'Something went wrong'", result.Error)
	}
}

func TestConversationMessage(t *testing.T) {
	msg := ConversationMessage{
		Role:    "user",
		Content: "Hello, Claude!",
	}

	if msg.Role != "user" {
		t.Errorf("Role = %q, want 'user'", msg.Role)
	}
	if msg.Content != "Hello, Claude!" {
		t.Errorf("Content = %q, want 'Hello, Claude!'", msg.Content)
	}
}

func TestClaudeAvailable(t *testing.T) {
	// Just test that the function doesn't panic
	// The actual result depends on the system
	_ = ClaudeAvailable()
}

func TestGetClaudeVersionNoClaudeInstalled(t *testing.T) {
	// Skip if claude is actually installed
	if ClaudeAvailable() {
		t.Skip("Claude is installed, skipping failure test")
	}

	_, err := GetClaudeVersion()
	if err == nil {
		t.Error("expected error when claude is not installed")
	}
}
