package planning

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"
)

// ClaudeResult represents the result of a Claude SDK/CLI invocation.
type ClaudeResult struct {
	Success bool   `json:"success"`
	Output  string `json:"output"`
	Error   string `json:"error,omitempty"`
}

// RunClaudeSync runs Claude synchronously via the CLI.
// If stream is true, output is printed to stdout as it arrives.
// The cwd parameter sets the working directory for Claude execution.
func RunClaudeSync(prompt string, timeoutSecs int, stream bool, cwd string) *ClaudeResult {
	result := &ClaudeResult{Success: true}

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(timeoutSecs)*time.Second)
	defer cancel()

	// Build command
	args := []string{"--print"}
	if !stream {
		args = append(args, "--output-format", "json")
	}
	args = append(args, "-p", prompt)

	cmd := exec.CommandContext(ctx, "claude", args...)
	cmd.Dir = cwd // Set working directory

	if stream {
		// Stream output to stdout and capture it
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

		if err := cmd.Start(); err != nil {
			result.Success = false
			result.Error = fmt.Sprintf("failed to start claude: %v", err)
			return result
		}

		var outputBuilder strings.Builder

		// Stream stdout
		go func() {
			scanner := bufio.NewScanner(stdout)
			for scanner.Scan() {
				line := scanner.Text()
				fmt.Println(line)
				outputBuilder.WriteString(line)
				outputBuilder.WriteString("\n")
			}
		}()

		// Capture stderr
		var stderrBuilder strings.Builder
		go func() {
			scanner := bufio.NewScanner(stderr)
			for scanner.Scan() {
				stderrBuilder.WriteString(scanner.Text())
				stderrBuilder.WriteString("\n")
			}
		}()

		err = cmd.Wait()
		result.Output = outputBuilder.String()

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
	} else {
		// Non-streaming: capture all output
		output, err := cmd.Output()
		if err != nil {
			if ctx.Err() == context.DeadlineExceeded {
				result.Success = false
				result.Error = fmt.Sprintf("claude timed out after %d seconds", timeoutSecs)
			} else {
				if exitErr, ok := err.(*exec.ExitError); ok {
					result.Success = false
					result.Error = fmt.Sprintf("claude failed: %v\nstderr: %s", err, string(exitErr.Stderr))
				} else {
					result.Success = false
					result.Error = fmt.Sprintf("claude failed: %v", err)
				}
			}
			return result
		}
		result.Output = string(output)
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
