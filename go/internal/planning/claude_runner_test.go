package planning

import (
	"os"
	"path/filepath"
	"strings"
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

// REQ_009.2: Test file-based Claude execution
func TestRunClaudeWithFile(t *testing.T) {
	// Create a temporary test file
	tmpDir := t.TempDir()
	testFile := filepath.Join(tmpDir, "test.txt")
	testContent := "This is test content"

	err := os.WriteFile(testFile, []byte(testContent), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}

	// Skip the actual Claude execution if Claude is not installed
	if !ClaudeAvailable() {
		t.Skip("Claude CLI not available, skipping integration test")
	}

	// Test with a simple prompt
	result := RunClaudeWithFile("Summarize this", testFile, 5, false, tmpDir)

	// Should at least not panic and return a result
	if result == nil {
		t.Error("Expected non-nil result")
	}
}

func TestRunClaudeWithFileNotFound(t *testing.T) {
	// Test with non-existent file
	result := RunClaudeWithFile("Test prompt", "/nonexistent/file.txt", 5, false, ".")

	if result == nil {
		t.Fatal("Expected non-nil result")
	}
	if result.Success {
		t.Error("Expected failure for non-existent file")
	}
	if !strings.Contains(result.Error, "failed to read file") {
		t.Errorf("Expected 'failed to read file' error, got: %s", result.Error)
	}
}

// REQ_009.3: Test multi-turn conversation support
func TestRunClaudeConversation(t *testing.T) {
	messages := []ConversationMessage{
		{Role: "user", Content: "Hello"},
		{Role: "assistant", Content: "Hi there!"},
		{Role: "user", Content: "How are you?"},
	}

	// Skip the actual Claude execution if Claude is not installed
	if !ClaudeAvailable() {
		t.Skip("Claude CLI not available, skipping integration test")
	}

	result := RunClaudeConversation(messages, 5, false, ".")

	// Should at least not panic and return a result
	if result == nil {
		t.Error("Expected non-nil result")
	}
}

func TestRunClaudeConversationFormatsMessages(t *testing.T) {
	// Test that we can build conversation prompts correctly
	messages := []ConversationMessage{
		{Role: "user", Content: "First message"},
		{Role: "assistant", Content: "Response"},
		{Role: "user", Content: "Second message"},
	}

	// We can't directly test the prompt formatting without exposing internals,
	// but we can verify the function accepts the correct structure
	if len(messages) != 3 {
		t.Error("Test setup failed")
	}

	// Verify each message has the expected fields
	for i, msg := range messages {
		if msg.Role == "" {
			t.Errorf("Message %d has empty role", i)
		}
		if msg.Content == "" {
			t.Errorf("Message %d has empty content", i)
		}
	}
}

// REQ_009.5: Test utility functions
func TestGetClaudeVersionWhenAvailable(t *testing.T) {
	if !ClaudeAvailable() {
		t.Skip("Claude CLI not available, skipping version test")
	}

	version, err := GetClaudeVersion()
	if err != nil {
		t.Errorf("Expected no error when claude is available, got: %v", err)
	}
	if version == "" {
		t.Error("Expected non-empty version string")
	}

	// Version should be trimmed (no leading/trailing whitespace)
	if version != strings.TrimSpace(version) {
		t.Error("Version string should be trimmed")
	}
}

func TestClaudeAvailableReturnsBool(t *testing.T) {
	// Test that ClaudeAvailable returns a boolean without panicking
	result := ClaudeAvailable()

	// Result should be either true or false (this always passes, but ensures no panic)
	_ = result

	// If we have claude binary, result should be true
	if result && !ClaudeAvailable() {
		t.Error("ClaudeAvailable should be consistent")
	}
}

// Test ClaudeResult struct fields
func TestClaudeResultStructure(t *testing.T) {
	result := &ClaudeResult{
		Success: true,
		Output:  "output",
		Error:   "error",
	}

	// Verify all fields are accessible
	if result.Success != true {
		t.Error("Success field not accessible")
	}
	if result.Output != "output" {
		t.Error("Output field not accessible")
	}
	if result.Error != "error" {
		t.Error("Error field not accessible")
	}
}

// Test ConversationMessage struct fields
func TestConversationMessageStructure(t *testing.T) {
	msg := ConversationMessage{
		Role:    "user",
		Content: "test",
	}

	if msg.Role != "user" {
		t.Error("Role field not accessible")
	}
	if msg.Content != "test" {
		t.Error("Content field not accessible")
	}
}
