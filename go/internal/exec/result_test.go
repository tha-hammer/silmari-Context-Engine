package exec

import (
	"encoding/json"
	"errors"
	"testing"
	"time"
)

func TestNewCommandResult(t *testing.T) {
	tests := []struct {
		name      string
		success   bool
		output    string
		errOutput string
		exitCode  int
		elapsed   time.Duration
	}{
		{
			name:      "successful command",
			success:   true,
			output:    "hello world",
			errOutput: "",
			exitCode:  0,
			elapsed:   100 * time.Millisecond,
		},
		{
			name:      "failed command with stderr",
			success:   false,
			output:    "",
			errOutput: "command not found",
			exitCode:  127,
			elapsed:   50 * time.Millisecond,
		},
		{
			name:      "command with both stdout and stderr",
			success:   false,
			output:    "partial output",
			errOutput: "error occurred",
			exitCode:  1,
			elapsed:   200 * time.Millisecond,
		},
		{
			name:      "killed process",
			success:   false,
			output:    "",
			errOutput: "signal: killed",
			exitCode:  -1,
			elapsed:   5 * time.Second,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := NewCommandResult(tt.success, tt.output, tt.errOutput, tt.exitCode, tt.elapsed)

			if result.Success != tt.success {
				t.Errorf("Success = %v, want %v", result.Success, tt.success)
			}
			if result.Output != tt.output {
				t.Errorf("Output = %q, want %q", result.Output, tt.output)
			}
			if result.Error != tt.errOutput {
				t.Errorf("Error = %q, want %q", result.Error, tt.errOutput)
			}
			if result.ExitCode != tt.exitCode {
				t.Errorf("ExitCode = %d, want %d", result.ExitCode, tt.exitCode)
			}
			if result.Elapsed != tt.elapsed {
				t.Errorf("Elapsed = %v, want %v", result.Elapsed, tt.elapsed)
			}
		})
	}
}

func TestNewSuccessResult(t *testing.T) {
	tests := []struct {
		name    string
		output  string
		elapsed time.Duration
	}{
		{
			name:    "simple output",
			output:  "test output",
			elapsed: 100 * time.Millisecond,
		},
		{
			name:    "empty output",
			output:  "",
			elapsed: 10 * time.Millisecond,
		},
		{
			name:    "multiline output",
			output:  "line1\nline2\nline3",
			elapsed: 500 * time.Millisecond,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := NewSuccessResult(tt.output, tt.elapsed)

			if !result.Success {
				t.Error("Success should be true")
			}
			if result.Output != tt.output {
				t.Errorf("Output = %q, want %q", result.Output, tt.output)
			}
			if result.Error != "" {
				t.Errorf("Error should be empty, got %q", result.Error)
			}
			if result.ExitCode != 0 {
				t.Errorf("ExitCode = %d, want 0", result.ExitCode)
			}
			if result.Elapsed != tt.elapsed {
				t.Errorf("Elapsed = %v, want %v", result.Elapsed, tt.elapsed)
			}
		})
	}
}

func TestNewFailureResult(t *testing.T) {
	tests := []struct {
		name      string
		errOutput string
		exitCode  int
		elapsed   time.Duration
	}{
		{
			name:      "typical failure",
			errOutput: "file not found",
			exitCode:  1,
			elapsed:   50 * time.Millisecond,
		},
		{
			name:      "permission denied",
			errOutput: "permission denied",
			exitCode:  126,
			elapsed:   25 * time.Millisecond,
		},
		{
			name:      "command not found",
			errOutput: "command not found",
			exitCode:  127,
			elapsed:   10 * time.Millisecond,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := NewFailureResult(tt.errOutput, tt.exitCode, tt.elapsed)

			if result.Success {
				t.Error("Success should be false")
			}
			if result.Output != "" {
				t.Errorf("Output should be empty, got %q", result.Output)
			}
			if result.Error != tt.errOutput {
				t.Errorf("Error = %q, want %q", result.Error, tt.errOutput)
			}
			if result.ExitCode != tt.exitCode {
				t.Errorf("ExitCode = %d, want %d", result.ExitCode, tt.exitCode)
			}
			if result.Elapsed != tt.elapsed {
				t.Errorf("Elapsed = %v, want %v", result.Elapsed, tt.elapsed)
			}
		})
	}
}

func TestNewTimeoutResult(t *testing.T) {
	tests := []struct {
		name    string
		timeout time.Duration
	}{
		{
			name:    "short timeout",
			timeout: 5 * time.Second,
		},
		{
			name:    "default timeout",
			timeout: DefaultTimeout,
		},
		{
			name:    "long timeout",
			timeout: 10 * time.Minute,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := NewTimeoutResult(tt.timeout)

			if result.Success {
				t.Error("Success should be false")
			}
			if result.Output != "" {
				t.Errorf("Output should be empty, got %q", result.Output)
			}
			expectedError := "command timed out after " + tt.timeout.String()
			if result.Error != expectedError {
				t.Errorf("Error = %q, want %q", result.Error, expectedError)
			}
			if result.ExitCode != -1 {
				t.Errorf("ExitCode = %d, want -1", result.ExitCode)
			}
			if result.Elapsed != tt.timeout {
				t.Errorf("Elapsed = %v, want %v", result.Elapsed, tt.timeout)
			}
		})
	}
}

func TestNewErrorResult(t *testing.T) {
	tests := []struct {
		name    string
		err     error
		elapsed time.Duration
	}{
		{
			name:    "simple error",
			err:     errors.New("something went wrong"),
			elapsed: 100 * time.Millisecond,
		},
		{
			name:    "wrapped error",
			err:     errors.New("failed to connect: network timeout"),
			elapsed: 5 * time.Second,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := NewErrorResult(tt.err, tt.elapsed)

			if result.Success {
				t.Error("Success should be false")
			}
			if result.Output != "" {
				t.Errorf("Output should be empty, got %q", result.Output)
			}
			if result.Error != tt.err.Error() {
				t.Errorf("Error = %q, want %q", result.Error, tt.err.Error())
			}
			if result.ExitCode != -1 {
				t.Errorf("ExitCode = %d, want -1", result.ExitCode)
			}
			if result.Elapsed != tt.elapsed {
				t.Errorf("Elapsed = %v, want %v", result.Elapsed, tt.elapsed)
			}
		})
	}
}

func TestCommandResult_IsTimeout(t *testing.T) {
	tests := []struct {
		name     string
		result   *CommandResult
		expected bool
	}{
		{
			name:     "timeout result",
			result:   NewTimeoutResult(5 * time.Second),
			expected: true,
		},
		{
			name:     "success result",
			result:   NewSuccessResult("output", 100*time.Millisecond),
			expected: false,
		},
		{
			name:     "failure with exit code",
			result:   NewFailureResult("error", 1, 100*time.Millisecond),
			expected: false,
		},
		{
			name:     "error result (also exit code -1)",
			result:   NewErrorResult(errors.New("error"), 100*time.Millisecond),
			expected: true, // Note: IsTimeout returns true for any failed result with exit code -1 and error
		},
		{
			name: "cancelled result",
			result: &CommandResult{
				Success:  false,
				Error:    "command cancelled",
				ExitCode: -1,
			},
			expected: true, // This is also considered timeout-like due to the implementation
		},
		{
			name: "exit code -1 but success true",
			result: &CommandResult{
				Success:  true,
				Error:    "some error",
				ExitCode: -1,
			},
			expected: false,
		},
		{
			name: "exit code -1 but empty error",
			result: &CommandResult{
				Success:  false,
				Error:    "",
				ExitCode: -1,
			},
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.result.IsTimeout(); got != tt.expected {
				t.Errorf("IsTimeout() = %v, want %v", got, tt.expected)
			}
		})
	}
}

func TestCommandResult_String(t *testing.T) {
	result := NewSuccessResult("hello world", 100*time.Millisecond)
	str := result.String()

	// Should be valid JSON
	var parsed map[string]interface{}
	if err := json.Unmarshal([]byte(str), &parsed); err != nil {
		t.Errorf("String() did not produce valid JSON: %v", err)
	}

	// Check that the JSON contains expected fields
	if _, ok := parsed["success"]; !ok {
		t.Error("String() JSON missing 'success' field")
	}
	if _, ok := parsed["output"]; !ok {
		t.Error("String() JSON missing 'output' field")
	}
	if _, ok := parsed["exit_code"]; !ok {
		t.Error("String() JSON missing 'exit_code' field")
	}
}

func TestCommandResult_MarshalJSON(t *testing.T) {
	tests := []struct {
		name            string
		result          *CommandResult
		expectedSeconds float64
	}{
		{
			name:            "100 milliseconds",
			result:          NewSuccessResult("output", 100*time.Millisecond),
			expectedSeconds: 0.1,
		},
		{
			name:            "5 seconds",
			result:          NewSuccessResult("output", 5*time.Second),
			expectedSeconds: 5.0,
		},
		{
			name:            "2.5 seconds",
			result:          NewSuccessResult("output", 2500*time.Millisecond),
			expectedSeconds: 2.5,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			data, err := json.Marshal(tt.result)
			if err != nil {
				t.Fatalf("MarshalJSON() error = %v", err)
			}

			var parsed map[string]interface{}
			if err := json.Unmarshal(data, &parsed); err != nil {
				t.Fatalf("Failed to unmarshal JSON: %v", err)
			}

			// Check elapsed_seconds field
			elapsedSeconds, ok := parsed["elapsed_seconds"].(float64)
			if !ok {
				t.Fatal("elapsed_seconds field not found or not a number")
			}
			if elapsedSeconds != tt.expectedSeconds {
				t.Errorf("elapsed_seconds = %v, want %v", elapsedSeconds, tt.expectedSeconds)
			}

			// Verify other fields
			if success, ok := parsed["success"].(bool); !ok || success != tt.result.Success {
				t.Errorf("success = %v, want %v", success, tt.result.Success)
			}
			if output, ok := parsed["output"].(string); !ok || output != tt.result.Output {
				t.Errorf("output = %q, want %q", output, tt.result.Output)
			}
		})
	}
}

func TestCommandResult_MarshalJSON_OmitsEmptyError(t *testing.T) {
	result := NewSuccessResult("output", 100*time.Millisecond)

	data, err := json.Marshal(result)
	if err != nil {
		t.Fatalf("MarshalJSON() error = %v", err)
	}

	var parsed map[string]interface{}
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("Failed to unmarshal JSON: %v", err)
	}

	// The error field should still be present but empty since the custom marshal
	// includes the embedded Alias struct
	if errField, ok := parsed["error"]; ok {
		if errStr, ok := errField.(string); ok && errStr != "" {
			t.Errorf("error field should be empty for success result, got %q", errStr)
		}
	}
}

func TestCommandResult_MarshalJSON_IncludesError(t *testing.T) {
	result := NewFailureResult("something went wrong", 1, 100*time.Millisecond)

	data, err := json.Marshal(result)
	if err != nil {
		t.Fatalf("MarshalJSON() error = %v", err)
	}

	var parsed map[string]interface{}
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("Failed to unmarshal JSON: %v", err)
	}

	errField, ok := parsed["error"].(string)
	if !ok {
		t.Fatal("error field not found")
	}
	if errField != "something went wrong" {
		t.Errorf("error = %q, want %q", errField, "something went wrong")
	}
}

func TestCommandResult_JSONRoundTrip(t *testing.T) {
	tests := []struct {
		name   string
		result *CommandResult
	}{
		{
			name:   "success result",
			result: NewSuccessResult("output data", 150*time.Millisecond),
		},
		{
			name:   "failure result",
			result: NewFailureResult("error message", 42, 500*time.Millisecond),
		},
		{
			name:   "timeout result",
			result: NewTimeoutResult(30 * time.Second),
		},
		{
			name:   "complex result",
			result: NewCommandResult(false, "partial output", "error occurred", 1, 2*time.Second),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Marshal to JSON
			data, err := json.Marshal(tt.result)
			if err != nil {
				t.Fatalf("Marshal error = %v", err)
			}

			// Unmarshal back (note: elapsed will be in elapsed_seconds, not Elapsed)
			var parsed struct {
				Success        bool    `json:"success"`
				Output         string  `json:"output"`
				Error          string  `json:"error"`
				ExitCode       int     `json:"exit_code"`
				ElapsedSeconds float64 `json:"elapsed_seconds"`
			}
			if err := json.Unmarshal(data, &parsed); err != nil {
				t.Fatalf("Unmarshal error = %v", err)
			}

			// Verify fields
			if parsed.Success != tt.result.Success {
				t.Errorf("Success = %v, want %v", parsed.Success, tt.result.Success)
			}
			if parsed.Output != tt.result.Output {
				t.Errorf("Output = %q, want %q", parsed.Output, tt.result.Output)
			}
			if parsed.Error != tt.result.Error {
				t.Errorf("Error = %q, want %q", parsed.Error, tt.result.Error)
			}
			if parsed.ExitCode != tt.result.ExitCode {
				t.Errorf("ExitCode = %d, want %d", parsed.ExitCode, tt.result.ExitCode)
			}

			expectedSeconds := tt.result.Elapsed.Seconds()
			if parsed.ElapsedSeconds != expectedSeconds {
				t.Errorf("ElapsedSeconds = %v, want %v", parsed.ElapsedSeconds, expectedSeconds)
			}
		})
	}
}

func TestDefaultTimeout(t *testing.T) {
	expected := 120 * time.Second
	if DefaultTimeout != expected {
		t.Errorf("DefaultTimeout = %v, want %v", DefaultTimeout, expected)
	}
}
