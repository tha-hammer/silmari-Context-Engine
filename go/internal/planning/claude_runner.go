package planning

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"sync"
	"time"
)

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
func RunClaudeSync(prompt string, timeoutSecs int, stream bool, cwd string) *ClaudeResult {
	result := &ClaudeResult{Success: true}
	startTime := time.Now()

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

			if lineCount%10 == 0 {
				fmt.Fprintf(os.Stderr, "[DEBUG] Processed %d lines from stdout\n", lineCount)
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

	fmt.Fprintf(os.Stderr, "[DEBUG] Waiting for Claude process to complete...\n")
	err = cmd.Wait()
	fmt.Fprintf(os.Stderr, "[DEBUG] Claude process exited, waiting for goroutines...\n")
	wg.Wait() // Wait for goroutines to finish processing all buffered data
	fmt.Fprintf(os.Stderr, "[DEBUG] All goroutines finished, syncing stdout...\n")
	os.Stdout.Sync() // Flush stdout buffer

	// Build output (matching Python lines 486-487)
	if finalResult != "" {
		result.Output = finalResult
	} else {
		result.Output = strings.Join(textChunks, "")
	}

	elapsed := time.Since(startTime).Seconds()
	fmt.Fprintf(os.Stderr, "[DEBUG] Output captured (%d bytes, %.2fs elapsed)\n", len(result.Output), elapsed)

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
