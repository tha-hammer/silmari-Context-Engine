package exec

import (
	"context"
	"testing"
	"time"
)

func TestDefaultRetryPolicy(t *testing.T) {
	p := DefaultRetryPolicy()

	if p.MaxRetries != 3 {
		t.Errorf("MaxRetries = %d, want 3", p.MaxRetries)
	}
	if p.InitialDelay != 200*time.Millisecond {
		t.Errorf("InitialDelay = %v, want 200ms", p.InitialDelay)
	}
	if p.MaxDelay != 10*time.Second {
		t.Errorf("MaxDelay = %v, want 10s", p.MaxDelay)
	}
	if p.Multiplier != 1.5 {
		t.Errorf("Multiplier = %v, want 1.5", p.Multiplier)
	}
}

func TestNoRetryPolicy(t *testing.T) {
	p := NoRetryPolicy()
	if p.MaxRetries != 0 {
		t.Errorf("MaxRetries = %d, want 0", p.MaxRetries)
	}
}

func TestRetryPolicyShouldRetry(t *testing.T) {
	p := DefaultRetryPolicy()

	// Default behavior: retry on failure
	successResult := &CommandResult{Success: true}
	if p.shouldRetry(successResult) {
		t.Error("shouldRetry(success) = true, want false")
	}

	failResult := &CommandResult{Success: false}
	if !p.shouldRetry(failResult) {
		t.Error("shouldRetry(failure) = false, want true")
	}

	// Custom RetryIf
	p.RetryIf = func(r *CommandResult) bool {
		return r.ExitCode == 42
	}

	customResult := &CommandResult{Success: false, ExitCode: 42}
	if !p.shouldRetry(customResult) {
		t.Error("shouldRetry with custom RetryIf failed")
	}

	otherResult := &CommandResult{Success: false, ExitCode: 1}
	if p.shouldRetry(otherResult) {
		t.Error("shouldRetry with custom RetryIf should return false for exit code 1")
	}
}

func TestRetryPolicyGetDelay(t *testing.T) {
	p := &RetryPolicy{
		InitialDelay: 100 * time.Millisecond,
		MaxDelay:     1 * time.Second,
		Multiplier:   2.0,
		Jitter:       0, // No jitter for predictable testing
	}

	// First delay should be initial delay
	if d := p.getDelay(0); d != 100*time.Millisecond {
		t.Errorf("getDelay(0) = %v, want 100ms", d)
	}

	// Second delay should be doubled
	if d := p.getDelay(1); d != 200*time.Millisecond {
		t.Errorf("getDelay(1) = %v, want 200ms", d)
	}

	// Third delay should be quadrupled
	if d := p.getDelay(2); d != 400*time.Millisecond {
		t.Errorf("getDelay(2) = %v, want 400ms", d)
	}

	// Delay should be capped at MaxDelay
	if d := p.getDelay(10); d != 1*time.Second {
		t.Errorf("getDelay(10) = %v, want 1s (max)", d)
	}
}

func TestRetryPolicyGetDelayWithJitter(t *testing.T) {
	p := &RetryPolicy{
		InitialDelay: 100 * time.Millisecond,
		MaxDelay:     1 * time.Second,
		Multiplier:   2.0,
		Jitter:       0.1, // ±10%
	}

	// With jitter, delay should be within range
	for i := 0; i < 10; i++ {
		d := p.getDelay(0)
		if d < 90*time.Millisecond || d > 110*time.Millisecond {
			t.Errorf("getDelay(0) with jitter = %v, want between 90ms and 110ms", d)
		}
	}
}

func TestRetryRunnerSuccess(t *testing.T) {
	runner := NewRunner(WithTimeout(5 * time.Second))
	policy := NoRetryPolicy()
	rr := NewRetryRunner(runner, policy)

	result, err := rr.Run(context.Background(), "echo", "hello")
	if err != nil {
		t.Fatalf("Run failed: %v", err)
	}
	if !result.Success {
		t.Errorf("Run success = false, want true")
	}
}

func TestRetryRunnerNoRetries(t *testing.T) {
	runner := NewRunner(WithTimeout(5 * time.Second))
	policy := NoRetryPolicy()
	rr := NewRetryRunner(runner, policy)

	// Command that fails
	result, err := rr.Run(context.Background(), "false")
	if err != nil {
		t.Fatalf("Run failed: %v", err)
	}
	if result.Success {
		t.Error("Expected failure")
	}
}

func TestRetryableError(t *testing.T) {
	tests := []struct {
		name   string
		result *CommandResult
		want   bool
	}{
		{
			name:   "success",
			result: &CommandResult{Success: true},
			want:   false,
		},
		{
			name:   "timeout",
			result: NewTimeoutResult(5 * time.Second),
			want:   true,
		},
		{
			name:   "killed",
			result: &CommandResult{Success: false, ExitCode: 137},
			want:   true,
		},
		{
			name:   "regular failure",
			result: &CommandResult{Success: false, ExitCode: 1},
			want:   false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := RetryableError(tt.result)
			if got != tt.want {
				t.Errorf("RetryableError() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestRetryOnExitCodes(t *testing.T) {
	fn := RetryOnExitCodes(1, 2, 3)

	tests := []struct {
		result *CommandResult
		want   bool
	}{
		{&CommandResult{Success: false, ExitCode: 1}, true},
		{&CommandResult{Success: false, ExitCode: 2}, true},
		{&CommandResult{Success: false, ExitCode: 3}, true},
		{&CommandResult{Success: false, ExitCode: 4}, false},
		{&CommandResult{Success: true, ExitCode: 0}, false},
	}

	for _, tt := range tests {
		got := fn(tt.result)
		if got != tt.want {
			t.Errorf("RetryOnExitCodes(%d) = %v, want %v", tt.result.ExitCode, got, tt.want)
		}
	}
}

func TestWithRetry(t *testing.T) {
	runner := NewRunner(WithTimeout(5 * time.Second))
	policy := NoRetryPolicy()

	result, err := WithRetry(context.Background(), runner, policy, "echo", "test")
	if err != nil {
		t.Fatalf("WithRetry failed: %v", err)
	}
	if !result.Success {
		t.Error("WithRetry success = false, want true")
	}
}

func TestRetryRunnerContextCancel(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel() // Cancel immediately

	runner := NewRunner(WithTimeout(5 * time.Second))
	policy := DefaultRetryPolicy()
	rr := NewRetryRunner(runner, policy)

	result, err := rr.Run(ctx, "echo", "hello")
	if err != nil {
		t.Fatalf("Run failed: %v", err)
	}
	if result.Success {
		t.Error("Expected context cancelled result")
	}
}
