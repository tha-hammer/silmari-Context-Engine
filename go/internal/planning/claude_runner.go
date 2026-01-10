package planning

import (
	"bufio"
	"context"
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

// RunClaudeSync runs Claude synchronously via the CLI.
// If stream is true, output is printed to stdout as it arrives.
// The cwd parameter sets the working directory for Claude execution.
func RunClaudeSync(prompt string, timeoutSecs int, stream bool, cwd string) *ClaudeResult {
	result := &ClaudeResult{Success: true}

	// Diagnostic logging
	fmt.Fprintf(os.Stderr, "[DEBUG] RunClaudeSync called: stream=%v, timeout=%ds, cwd=%s, prompt_size=%d bytes\n", stream, timeoutSecs, cwd, len(prompt))

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(timeoutSecs)*time.Second)
	defer cancel()

	// Build command - pass prompt via stdin instead of -p flag for large prompts
	args := []string{"--print"}
	if !stream {
		args = append(args, "--output-format", "json")
	}
	// NOTE: Removed -p flag - prompt will be passed via stdin

	fmt.Fprintf(os.Stderr, "[DEBUG] Executing: claude %v (prompt via stdin)\n", args[0])
	cmd := exec.CommandContext(ctx, "claude", args...)
	cmd.Dir = cwd // Set working directory

	if stream {
		// Create stdin pipe to send prompt
		stdin, err := cmd.StdinPipe()
		if err != nil {
			result.Success = false
			result.Error = fmt.Sprintf("failed to create stdin pipe: %v", err)
			return result
		}

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

		fmt.Fprintf(os.Stderr, "[DEBUG] Claude process started (PID: %d), writing prompt to stdin...\n", cmd.Process.Pid)

		// Write prompt to stdin in a goroutine and close when done
		go func() {
			defer stdin.Close()
			fmt.Fprintf(os.Stderr, "[DEBUG] Writing %d bytes to stdin...\n", len(prompt))
			_, writeErr := stdin.Write([]byte(prompt))
			if writeErr != nil {
				fmt.Fprintf(os.Stderr, "[DEBUG] Error writing to stdin: %v\n", writeErr)
			} else {
				fmt.Fprintf(os.Stderr, "[DEBUG] Prompt written to stdin, closed pipe\n")
			}
		}()

		fmt.Fprintf(os.Stderr, "[DEBUG] Waiting for Claude output...\n")

		var outputBuilder strings.Builder
		var stderrBuilder strings.Builder
		var wg sync.WaitGroup

		// Stream stdout
		wg.Add(1)
		go func() {
			defer wg.Done()
			fmt.Fprintf(os.Stderr, "[DEBUG] stdout goroutine started\n")
			scanner := bufio.NewScanner(stdout)
			lineCount := 0
			for scanner.Scan() {
				line := scanner.Text()
				fmt.Println(line)
				outputBuilder.WriteString(line)
				outputBuilder.WriteString("\n")
				lineCount++
				if lineCount%10 == 0 {
					fmt.Fprintf(os.Stderr, "[DEBUG] Processed %d lines from stdout\n", lineCount)
				}
			}
			fmt.Fprintf(os.Stderr, "[DEBUG] stdout goroutine finished (%d lines total)\n", lineCount)
		}()

		// Capture stderr
		wg.Add(1)
		go func() {
			defer wg.Done()
			fmt.Fprintf(os.Stderr, "[DEBUG] stderr goroutine started\n")
			scanner := bufio.NewScanner(stderr)
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
		os.Stdout.Sync() // Flush stdout buffer to ensure all output is displayed
		fmt.Fprintf(os.Stderr, "[DEBUG] Output captured (%d bytes)\n", len(outputBuilder.String()))
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
		// Non-streaming: pass prompt via stdin and capture all output
		stdin, err := cmd.StdinPipe()
		if err != nil {
			result.Success = false
			result.Error = fmt.Sprintf("failed to create stdin pipe: %v", err)
			return result
		}

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

		fmt.Fprintf(os.Stderr, "[DEBUG] Non-streaming: writing prompt to stdin...\n")

		// Write prompt and close stdin
		go func() {
			defer stdin.Close()
			stdin.Write([]byte(prompt))
		}()

		// Read all output
		var outputBuilder strings.Builder
		var stderrBuilder strings.Builder
		var wg sync.WaitGroup

		wg.Add(1)
		go func() {
			defer wg.Done()
			scanner := bufio.NewScanner(stdout)
			for scanner.Scan() {
				outputBuilder.WriteString(scanner.Text())
				outputBuilder.WriteString("\n")
			}
		}()

		wg.Add(1)
		go func() {
			defer wg.Done()
			scanner := bufio.NewScanner(stderr)
			for scanner.Scan() {
				stderrBuilder.WriteString(scanner.Text())
				stderrBuilder.WriteString("\n")
			}
		}()

		err = cmd.Wait()
		wg.Wait()
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
