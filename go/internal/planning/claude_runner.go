package planning

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// OAuth configuration for Claude CLI
const (
	// Official Claude Code CLI OAuth client ID
	claudeOAuthClientID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
	// OAuth token refresh endpoint
	claudeOAuthEndpoint = "https://console.anthropic.com/api/oauth/token"
)

// ClaudeCredentials represents the OAuth credentials stored by Claude CLI
type ClaudeCredentials struct {
	ClaudeAiOauth *ClaudeOAuthTokens `json:"claudeAiOauth,omitempty"`
}

// ClaudeOAuthTokens represents the OAuth token structure
type ClaudeOAuthTokens struct {
	AccessToken  string   `json:"accessToken"`
	RefreshToken string   `json:"refreshToken"`
	ExpiresAt    int64    `json:"expiresAt"`
	Scopes       []string `json:"scopes"`
}

// OAuthRefreshResponse represents the response from the OAuth refresh endpoint
type OAuthRefreshResponse struct {
	TokenType    string `json:"token_type"`
	AccessToken  string `json:"access_token"`
	ExpiresIn    int    `json:"expires_in"`
	RefreshToken string `json:"refresh_token"`
	Scope        string `json:"scope"`
}

// getCredentialsPath returns the path to the Claude credentials file
func getCredentialsPath() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}
	return filepath.Join(home, ".claude", ".credentials.json")
}

// readCredentials reads the Claude OAuth credentials from disk
func readCredentials() (*ClaudeCredentials, error) {
	path := getCredentialsPath()
	if path == "" {
		return nil, fmt.Errorf("could not determine credentials path")
	}

	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read credentials file: %w", err)
	}

	var creds ClaudeCredentials
	if err := json.Unmarshal(data, &creds); err != nil {
		return nil, fmt.Errorf("failed to parse credentials: %w", err)
	}

	return &creds, nil
}

// saveCredentials writes updated OAuth credentials to disk
func saveCredentials(creds *ClaudeCredentials) error {
	path := getCredentialsPath()
	if path == "" {
		return fmt.Errorf("could not determine credentials path")
	}

	// Create backup before writing
	backupPath := path + ".bak"
	if data, err := os.ReadFile(path); err == nil {
		_ = os.WriteFile(backupPath, data, 0600)
	}

	data, err := json.MarshalIndent(creds, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal credentials: %w", err)
	}

	if err := os.WriteFile(path, data, 0600); err != nil {
		return fmt.Errorf("failed to write credentials: %w", err)
	}

	return nil
}

// RefreshOAuthToken refreshes the OAuth access token using the refresh token
func RefreshOAuthToken() error {
	creds, err := readCredentials()
	if err != nil {
		return fmt.Errorf("failed to read credentials: %w", err)
	}

	if creds.ClaudeAiOauth == nil || creds.ClaudeAiOauth.RefreshToken == "" {
		return fmt.Errorf("no refresh token available")
	}

	fmt.Fprintf(os.Stderr, "[DEBUG] Refreshing OAuth token...\n")

	// Build refresh request
	reqBody := map[string]string{
		"grant_type":    "refresh_token",
		"refresh_token": creds.ClaudeAiOauth.RefreshToken,
		"client_id":     claudeOAuthClientID,
	}

	reqData, err := json.Marshal(reqBody)
	if err != nil {
		return fmt.Errorf("failed to marshal refresh request: %w", err)
	}

	// Make HTTP request
	req, err := http.NewRequest("POST", claudeOAuthEndpoint, bytes.NewReader(reqData))
	if err != nil {
		return fmt.Errorf("failed to create refresh request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send refresh request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("failed to read refresh response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("OAuth refresh failed with status %d: %s", resp.StatusCode, string(body))
	}

	// Parse response
	var oauthResp OAuthRefreshResponse
	if err := json.Unmarshal(body, &oauthResp); err != nil {
		return fmt.Errorf("failed to parse refresh response: %w", err)
	}

	// Update credentials
	creds.ClaudeAiOauth.AccessToken = oauthResp.AccessToken
	creds.ClaudeAiOauth.RefreshToken = oauthResp.RefreshToken
	creds.ClaudeAiOauth.ExpiresAt = time.Now().UnixMilli() + int64(oauthResp.ExpiresIn*1000)

	// Parse scopes
	if oauthResp.Scope != "" {
		creds.ClaudeAiOauth.Scopes = strings.Split(oauthResp.Scope, " ")
	}

	// Save updated credentials
	if err := saveCredentials(creds); err != nil {
		return fmt.Errorf("failed to save refreshed credentials: %w", err)
	}

	fmt.Fprintf(os.Stderr, "[DEBUG] OAuth token refreshed successfully, expires at %s\n",
		time.UnixMilli(creds.ClaudeAiOauth.ExpiresAt).Format(time.RFC3339))

	return nil
}

// isOAuthExpiredError checks if the error indicates an expired OAuth token
func isOAuthExpiredError(output string) bool {
	return strings.Contains(output, "authentication_error") &&
		(strings.Contains(output, "OAuth token has expired") ||
			strings.Contains(output, "401"))
}

// ClaudeResult represents the result of a Claude SDK/CLI invocation.
type ClaudeResult struct {
	Success bool   `json:"success"`
	Output  string `json:"output"`
	Error   string `json:"error,omitempty"`
}

// shellQuote escapes a string for safe use in shell commands
func shellQuote(s string) string {
	// Simple single-quote escaping: replace ' with '\''
	return "'" + strings.ReplaceAll(s, "'", "'\\''") + "'"
}

// RunClaudeSync runs Claude synchronously via the CLI using stream-json format with PTY.
// This matches the Python implementation's approach for real-time streaming.
// The cwd parameter sets the working directory for Claude execution.
//
// Authentication: Uses OAuth tokens from ~/.claude/.credentials.json.
// If tokens expire, the function will automatically refresh them and retry.
func RunClaudeSync(prompt string, timeoutSecs int, stream bool, cwd string) *ClaudeResult {
	return runClaudeSyncWithRetry(prompt, timeoutSecs, stream, cwd, true)
}

// runClaudeSyncWithRetry is the internal implementation with retry control
func runClaudeSyncWithRetry(prompt string, timeoutSecs int, stream bool, cwd string, allowRetry bool) *ClaudeResult {
	result := &ClaudeResult{Success: true}
	startTime := time.Now()

	// Proactively check if OAuth token is about to expire (within 5 minutes)
	if creds, err := readCredentials(); err == nil && creds.ClaudeAiOauth != nil {
		expiresAt := time.UnixMilli(creds.ClaudeAiOauth.ExpiresAt)
		if time.Until(expiresAt) < 5*time.Minute {
			fmt.Fprintf(os.Stderr, "[DEBUG] OAuth token expires soon (%s), proactively refreshing...\n",
				time.Until(expiresAt).Round(time.Second))
			if err := RefreshOAuthToken(); err != nil {
				fmt.Fprintf(os.Stderr, "[DEBUG] Proactive OAuth refresh failed: %v\n", err)
			}
		}
	}

	// Diagnostic logging
	fmt.Fprintf(os.Stderr, "[DEBUG] RunClaudeSync called: stream=%v, timeout=%ds, cwd=%s, prompt_size=%d bytes\n",
		stream, timeoutSecs, cwd, len(prompt))

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(timeoutSecs)*time.Second)
	defer cancel()

	// Build the claude command string (matching Python line 354-356)
	claudeCmd := fmt.Sprintf("claude --print --verbose --permission-mode bypassPermissions --output-format stream-json -p %s",
		shellQuote(prompt))

	// Wrap in 'script' command for PTY support (matching Python line 363)
	// This enables real-time streaming from Claude CLI
	cmd := exec.CommandContext(ctx, "script", "-q", "-c", claudeCmd, "/dev/null")
	cmd.Dir = cwd

	fmt.Fprintf(os.Stderr, "[DEBUG] Executing: script -q -c \"claude --print ... -p <prompt>\" /dev/null\n")

	// Create pipes
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		result.Success = false
		result.Error = fmt.Sprintf("failed to create stdout pipe: %v", err)
		return result
	}

	stderr, err := cmd.StderrPipe()
	if err != nil {
		result.Success = false
		result.Error = fmt.Sprintf("failed to create stderr pipe: %v", err)
		return result
	}

	// Start the command
	if err := cmd.Start(); err != nil {
		result.Success = false
		result.Error = fmt.Sprintf("failed to start claude: %v", err)
		return result
	}

	fmt.Fprintf(os.Stderr, "[DEBUG] Claude process started (PID: %d)\n", cmd.Process.Pid)

	var textChunks []string
	var finalResult string
	var stderrBuilder strings.Builder
	var wg sync.WaitGroup

	// Process stdout - parse JSON stream events (matching Python lines 404-445)
	wg.Add(1)
	go func() {
		defer wg.Done()
		fmt.Fprintf(os.Stderr, "[DEBUG] stdout goroutine started\n")
		scanner := bufio.NewScanner(stdout)
		// Increase buffer size to handle large JSON objects (default is 64KB)
		// Set max token size to 10MB to handle large Claude outputs
		const maxCapacity = 10 * 1024 * 1024 // 10MB
		buf := make([]byte, maxCapacity)
		scanner.Buffer(buf, maxCapacity)
		lineCount := 0

		for scanner.Scan() {
			// Check timeout
			if time.Since(startTime) > time.Duration(timeoutSecs)*time.Second {
				fmt.Fprintf(os.Stderr, "[DEBUG] Timeout reached in stdout goroutine\n")
				return
			}

			line := scanner.Text()
			lineCount++

			// Skip empty lines and script noise
			line = strings.TrimSpace(line)
			if line == "" || strings.HasPrefix(line, "Script ") {
				continue
			}

			// Parse JSON to extract text (matching Python lines 418-445)
			var data map[string]interface{}
			if err := json.Unmarshal([]byte(line), &data); err != nil {
				// Not JSON - could be script noise or other output
				if !strings.HasPrefix(line, "{") {
					if stream {
						fmt.Println(line)
					}
					textChunks = append(textChunks, line+"\n")
				}
				continue
			}

			msgType, _ := data["type"].(string)

			switch msgType {
			case "content_block_delta":
				// Extract text delta (matching Python lines 422-429)
				if delta, ok := data["delta"].(map[string]interface{}); ok {
					if deltaType, _ := delta["type"].(string); deltaType == "text_delta" {
						if text, ok := delta["text"].(string); ok && text != "" {
							if stream {
								fmt.Print(text)
								os.Stdout.Sync()
							}
							textChunks = append(textChunks, text)
						}
					}
				}

			case "assistant":
				// Extract assistant message content (matching Python lines 430-437)
				if message, ok := data["message"].(map[string]interface{}); ok {
					if content, ok := message["content"].([]interface{}); ok {
						for _, contentItem := range content {
							if contentMap, ok := contentItem.(map[string]interface{}); ok {
								if contentType, _ := contentMap["type"].(string); contentType == "text" {
									if text, ok := contentMap["text"].(string); ok && text != "" {
										if stream {
											fmt.Print(text)
											os.Stdout.Sync()
										}
										textChunks = append(textChunks, text)
									}
								}
							}
						}
					}
				}

			case "result":
				// Capture final result (matching Python lines 438-439)
				if res, ok := data["result"].(string); ok {
					finalResult = res
				}
			}
		}

		if err := scanner.Err(); err != nil {
			fmt.Fprintf(os.Stderr, "[DEBUG] Scanner error: %v\n", err)
		}

		fmt.Fprintf(os.Stderr, "[DEBUG] stdout goroutine finished (%d lines total)\n", lineCount)
	}()

	// Capture stderr
	wg.Add(1)
	go func() {
		defer wg.Done()
		fmt.Fprintf(os.Stderr, "[DEBUG] stderr goroutine started\n")
		scanner := bufio.NewScanner(stderr)
		// Increase buffer size for stderr as well
		const maxCapacity = 10 * 1024 * 1024 // 10MB
		buf := make([]byte, maxCapacity)
		scanner.Buffer(buf, maxCapacity)
		for scanner.Scan() {
			stderrBuilder.WriteString(scanner.Text())
			stderrBuilder.WriteString("\n")
		}
		fmt.Fprintf(os.Stderr, "[DEBUG] stderr goroutine finished\n")
	}()

	err = cmd.Wait()
	wg.Wait() // Wait for goroutines to finish processing all buffered data
	os.Stdout.Sync() // Flush stdout buffer

	// Build output (matching Python lines 486-487)
	if finalResult != "" {
		result.Output = finalResult
	} else {
		result.Output = strings.Join(textChunks, "")
	}

	elapsed := time.Since(startTime).Seconds()

	// Log completion to stderr AFTER stdout is synced
	fmt.Fprintf(os.Stderr, "[DEBUG] Claude process completed: %d bytes in %.2fs\n", len(result.Output), elapsed)

	// Check for OAuth expiration in output (CLI may return non-zero exit but output the error)
	combinedOutput := result.Output + stderrBuilder.String()
	if isOAuthExpiredError(combinedOutput) && allowRetry {
		fmt.Fprintf(os.Stderr, "[DEBUG] OAuth token expired, refreshing and retrying...\n")
		if refreshErr := RefreshOAuthToken(); refreshErr != nil {
			result.Success = false
			result.Error = fmt.Sprintf("OAuth token expired and refresh failed: %v", refreshErr)
			return result
		}
		// Retry once after refresh
		fmt.Fprintf(os.Stderr, "[DEBUG] OAuth token refreshed, retrying Claude invocation...\n")
		return runClaudeSyncWithRetry(prompt, timeoutSecs, stream, cwd, false)
	}

	// Handle errors (matching Python lines 488-492)
	if err != nil {
		if ctx.Err() == context.DeadlineExceeded {
			result.Success = false
			result.Error = fmt.Sprintf("claude timed out after %d seconds", timeoutSecs)
		} else {
			result.Success = false
			result.Error = fmt.Sprintf("claude failed: %v\nstderr: %s", err, stderrBuilder.String())
		}
		return result
	}

	return result
}

// RunClaudeWithFile runs Claude with a file as input context.
func RunClaudeWithFile(prompt, filePath string, timeoutSecs int, stream bool, cwd string) *ClaudeResult {
	// Read file content
	content, err := os.ReadFile(filePath)
	if err != nil {
		return &ClaudeResult{
			Success: false,
			Error:   fmt.Sprintf("failed to read file %s: %v", filePath, err),
		}
	}

	// Combine file content with prompt
	fullPrompt := fmt.Sprintf("File content from %s:\n```\n%s\n```\n\n%s", filePath, string(content), prompt)
	return RunClaudeSync(fullPrompt, timeoutSecs, stream, cwd)
}

// RunClaudeConversation runs a multi-turn conversation with Claude.
type ConversationMessage struct {
	Role    string `json:"role"`    // "user" or "assistant"
	Content string `json:"content"`
}

// RunClaudeConversation runs Claude with conversation history.
func RunClaudeConversation(messages []ConversationMessage, timeoutSecs int, stream bool, cwd string) *ClaudeResult {
	// Build conversation prompt
	var promptBuilder strings.Builder
	for _, msg := range messages {
		if msg.Role == "user" {
			promptBuilder.WriteString("Human: ")
		} else {
			promptBuilder.WriteString("Assistant: ")
		}
		promptBuilder.WriteString(msg.Content)
		promptBuilder.WriteString("\n\n")
	}

	return RunClaudeSync(promptBuilder.String(), timeoutSecs, stream, cwd)
}

// ClaudeAvailable checks if the Claude CLI is available.
func ClaudeAvailable() bool {
	_, err := exec.LookPath("claude")
	return err == nil
}

// GetClaudeVersion returns the installed Claude CLI version.
func GetClaudeVersion() (string, error) {
	cmd := exec.Command("claude", "--version")
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("failed to get claude version: %w", err)
	}
	return strings.TrimSpace(string(output)), nil
}
