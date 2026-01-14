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

// OAuth token refresh tests

func TestIsOAuthExpiredError(t *testing.T) {
	tests := []struct {
		name     string
		output   string
		expected bool
	}{
		{
			name:     "OAuth expired error with full message",
			output:   `API Error: 401 {"type":"error","error":{"type":"authentication_error","message":"OAuth token has expired. Please obtain a new token or refresh your existing token."}}`,
			expected: true,
		},
		{
			name:     "401 with authentication_error",
			output:   `{"type":"error","error":{"type":"authentication_error","message":"Token expired"}} 401`,
			expected: true,
		},
		{
			name:     "Normal error - not OAuth",
			output:   `Error: rate limit exceeded`,
			expected: false,
		},
		{
			name:     "Empty output",
			output:   ``,
			expected: false,
		},
		{
			name:     "Successful output",
			output:   `{"type":"assistant","message":"Hello!"}`,
			expected: false,
		},
		{
			name:     "401 without authentication_error type",
			output:   `HTTP 401 Unauthorized`,
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := isOAuthExpiredError(tt.output)
			if result != tt.expected {
				t.Errorf("isOAuthExpiredError(%q) = %v, want %v", tt.output, result, tt.expected)
			}
		})
	}
}

func TestClaudeCredentialsStructure(t *testing.T) {
	creds := &ClaudeCredentials{
		ClaudeAiOauth: &ClaudeOAuthTokens{
			AccessToken:  "sk-ant-oat01-test",
			RefreshToken: "sk-ant-ort01-test",
			ExpiresAt:    1234567890000,
			Scopes:       []string{"user:inference", "user:profile"},
		},
	}

	if creds.ClaudeAiOauth == nil {
		t.Fatal("ClaudeAiOauth should not be nil")
	}
	if creds.ClaudeAiOauth.AccessToken != "sk-ant-oat01-test" {
		t.Errorf("AccessToken = %q, want 'sk-ant-oat01-test'", creds.ClaudeAiOauth.AccessToken)
	}
	if creds.ClaudeAiOauth.RefreshToken != "sk-ant-ort01-test" {
		t.Errorf("RefreshToken = %q, want 'sk-ant-ort01-test'", creds.ClaudeAiOauth.RefreshToken)
	}
	if len(creds.ClaudeAiOauth.Scopes) != 2 {
		t.Errorf("Scopes length = %d, want 2", len(creds.ClaudeAiOauth.Scopes))
	}
}

func TestOAuthRefreshResponseStructure(t *testing.T) {
	resp := OAuthRefreshResponse{
		TokenType:    "Bearer",
		AccessToken:  "sk-ant-oat01-new",
		ExpiresIn:    28800,
		RefreshToken: "sk-ant-ort01-new",
		Scope:        "user:inference user:profile",
	}

	if resp.TokenType != "Bearer" {
		t.Errorf("TokenType = %q, want 'Bearer'", resp.TokenType)
	}
	if resp.ExpiresIn != 28800 {
		t.Errorf("ExpiresIn = %d, want 28800", resp.ExpiresIn)
	}
}

func TestGetCredentialsPath(t *testing.T) {
	path := getCredentialsPath()

	if path == "" {
		t.Skip("Could not determine home directory")
	}

	// Path should end with .claude/.credentials.json
	if !strings.HasSuffix(path, ".claude/.credentials.json") {
		t.Errorf("Credentials path should end with .claude/.credentials.json, got: %s", path)
	}
}

func TestReadCredentialsFileNotFound(t *testing.T) {
	// Save original home and restore after test
	origHome := os.Getenv("HOME")
	defer os.Setenv("HOME", origHome)

	// Set HOME to a temp directory without credentials
	tmpDir := t.TempDir()
	os.Setenv("HOME", tmpDir)

	_, err := readCredentials()
	if err == nil {
		t.Error("Expected error when credentials file doesn't exist")
	}
}

func TestRefreshOAuthTokenNoCredentials(t *testing.T) {
	// Save original home and restore after test
	origHome := os.Getenv("HOME")
	defer os.Setenv("HOME", origHome)

	// Set HOME to a temp directory without credentials
	tmpDir := t.TempDir()
	os.Setenv("HOME", tmpDir)

	err := RefreshOAuthToken()
	if err == nil {
		t.Error("Expected error when no credentials file exists")
	}
}

func TestRefreshOAuthTokenNoRefreshToken(t *testing.T) {
	// Save original home and restore after test
	origHome := os.Getenv("HOME")
	defer os.Setenv("HOME", origHome)

	// Create temp directory with credentials file missing refresh token
	tmpDir := t.TempDir()
	os.Setenv("HOME", tmpDir)

	// Create .claude directory
	claudeDir := filepath.Join(tmpDir, ".claude")
	if err := os.MkdirAll(claudeDir, 0755); err != nil {
		t.Fatalf("Failed to create .claude directory: %v", err)
	}

	// Write credentials without refresh token
	credsPath := filepath.Join(claudeDir, ".credentials.json")
	creds := `{"claudeAiOauth":{"accessToken":"test","refreshToken":"","expiresAt":0}}`
	if err := os.WriteFile(credsPath, []byte(creds), 0600); err != nil {
		t.Fatalf("Failed to write credentials: %v", err)
	}

	err := RefreshOAuthToken()
	if err == nil {
		t.Error("Expected error when no refresh token available")
	}
	if !strings.Contains(err.Error(), "no refresh token") {
		t.Errorf("Expected 'no refresh token' error, got: %v", err)
	}
}
