// Package exec provides command execution infrastructure for external CLI tools.
package exec

import (
	"encoding/json"
	"time"
)

// CommandResult represents the result of executing a command.
type CommandResult struct {
	// Success indicates whether the command completed successfully (exit code 0).
	Success bool `json:"success"`

	// Output contains the stdout from the command.
	Output string `json:"output"`

	// Error contains stderr or any error message from execution.
	Error string `json:"error,omitempty"`

	// ExitCode is the process exit code (-1 if process was killed or didn't start).
	ExitCode int `json:"exit_code"`

	// Elapsed is the duration the command took to execute.
	Elapsed time.Duration `json:"elapsed"`
}

// NewCommandResult creates a new CommandResult with the given parameters.
func NewCommandResult(success bool, output, errOutput string, exitCode int, elapsed time.Duration) *CommandResult {
	return &CommandResult{
		Success:  success,
		Output:   output,
		Error:    errOutput,
		ExitCode: exitCode,
		Elapsed:  elapsed,
	}
}

// NewSuccessResult creates a successful CommandResult.
func NewSuccessResult(output string, elapsed time.Duration) *CommandResult {
	return &CommandResult{
		Success:  true,
		Output:   output,
		ExitCode: 0,
		Elapsed:  elapsed,
	}
}

// NewFailureResult creates a failed CommandResult.
func NewFailureResult(errOutput string, exitCode int, elapsed time.Duration) *CommandResult {
	return &CommandResult{
		Success:  false,
		Error:    errOutput,
		ExitCode: exitCode,
		Elapsed:  elapsed,
	}
}

// NewTimeoutResult creates a CommandResult indicating a timeout.
func NewTimeoutResult(timeout time.Duration) *CommandResult {
	return &CommandResult{
		Success:  false,
		Error:    "command timed out after " + timeout.String(),
		ExitCode: -1,
		Elapsed:  timeout,
	}
}

// NewErrorResult creates a CommandResult from a Go error.
func NewErrorResult(err error, elapsed time.Duration) *CommandResult {
	return &CommandResult{
		Success:  false,
		Error:    err.Error(),
		ExitCode: -1,
		Elapsed:  elapsed,
	}
}

// IsTimeout returns true if the result represents a timeout.
func (r *CommandResult) IsTimeout() bool {
	return r.ExitCode == -1 && !r.Success && r.Error != ""
}

// String returns a string representation of the result.
func (r *CommandResult) String() string {
	data, _ := json.Marshal(r)
	return string(data)
}

// MarshalJSON implements custom JSON marshaling to format duration as seconds.
func (r *CommandResult) MarshalJSON() ([]byte, error) {
	type Alias CommandResult
	return json.Marshal(&struct {
		*Alias
		ElapsedSeconds float64 `json:"elapsed_seconds"`
	}{
		Alias:          (*Alias)(r),
		ElapsedSeconds: r.Elapsed.Seconds(),
	})
}
