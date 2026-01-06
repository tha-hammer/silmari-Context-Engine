package exec

import (
	"context"
	"math"
	"math/rand"
	"time"
)

// RetryPolicy defines how retries should be handled.
type RetryPolicy struct {
	// MaxRetries is the maximum number of retry attempts (0 = no retries).
	MaxRetries int

	// InitialDelay is the delay before the first retry.
	InitialDelay time.Duration

	// MaxDelay is the maximum delay between retries.
	MaxDelay time.Duration

	// Multiplier is the factor by which the delay increases after each retry.
	Multiplier float64

	// Jitter adds randomness to delays to prevent thundering herd.
	// A value of 0.1 means ±10% jitter.
	Jitter float64

	// RetryIf determines whether to retry based on the result.
	// If nil, only retries on non-success results.
	RetryIf func(*CommandResult) bool
}

// DefaultRetryPolicy returns a sensible default retry policy.
func DefaultRetryPolicy() *RetryPolicy {
	return &RetryPolicy{
		MaxRetries:   3,
		InitialDelay: 200 * time.Millisecond,
		MaxDelay:     10 * time.Second,
		Multiplier:   1.5,
		Jitter:       0.1,
		RetryIf:      nil,
	}
}

// NoRetryPolicy returns a policy that never retries.
func NoRetryPolicy() *RetryPolicy {
	return &RetryPolicy{
		MaxRetries: 0,
	}
}

// shouldRetry determines if the result should trigger a retry.
func (p *RetryPolicy) shouldRetry(result *CommandResult) bool {
	if p.RetryIf != nil {
		return p.RetryIf(result)
	}
	// Default: retry on non-success
	return !result.Success
}

// getDelay calculates the delay for a given attempt number.
func (p *RetryPolicy) getDelay(attempt int) time.Duration {
	if attempt == 0 {
		return p.InitialDelay
	}

	delay := float64(p.InitialDelay) * math.Pow(p.Multiplier, float64(attempt))

	// Apply max delay cap
	if delay > float64(p.MaxDelay) {
		delay = float64(p.MaxDelay)
	}

	// Apply jitter
	if p.Jitter > 0 {
		jitterRange := delay * p.Jitter
		delay += (rand.Float64()*2 - 1) * jitterRange
	}

	return time.Duration(delay)
}

// RetryRunner wraps a Runner with retry capabilities.
type RetryRunner struct {
	runner *Runner
	policy *RetryPolicy
}

// NewRetryRunner creates a new RetryRunner with the given policy.
func NewRetryRunner(runner *Runner, policy *RetryPolicy) *RetryRunner {
	if policy == nil {
		policy = DefaultRetryPolicy()
	}
	return &RetryRunner{
		runner: runner,
		policy: policy,
	}
}

// Run executes a command with retries according to the policy.
func (r *RetryRunner) Run(ctx context.Context, name string, args ...string) (*CommandResult, error) {
	var lastResult *CommandResult

	for attempt := 0; attempt <= r.policy.MaxRetries; attempt++ {
		// Check context before attempting
		if ctx.Err() != nil {
			if lastResult != nil {
				return lastResult, nil
			}
			return &CommandResult{
				Success:  false,
				Error:    "context cancelled before command could complete",
				ExitCode: -1,
			}, nil
		}

		result, err := r.runner.Run(ctx, name, args...)
		if err != nil {
			return nil, err
		}

		lastResult = result

		// Check if we should retry
		if !r.policy.shouldRetry(result) {
			return result, nil
		}

		// Don't retry on last attempt
		if attempt >= r.policy.MaxRetries {
			break
		}

		// Wait before retrying
		delay := r.policy.getDelay(attempt)
		select {
		case <-time.After(delay):
			// Continue to next attempt
		case <-ctx.Done():
			return lastResult, nil
		}
	}

	return lastResult, nil
}

// WithRetry is a helper that adds retry to any command execution.
func WithRetry(ctx context.Context, runner *Runner, policy *RetryPolicy, name string, args ...string) (*CommandResult, error) {
	rr := NewRetryRunner(runner, policy)
	return rr.Run(ctx, name, args...)
}

// RetryableError checks if a result represents a transient/retryable error.
// This is useful as a RetryIf function.
func RetryableError(result *CommandResult) bool {
	if result.Success {
		return false
	}

	// Timeout is retryable
	if result.IsTimeout() {
		return true
	}

	// Exit codes that might be transient
	retryableCodes := map[int]bool{
		-1:  true, // Process killed/didn't start
		124: true, // timeout command exit code
		125: true, // timeout command invalid
		126: true, // Command invoked cannot execute
		127: true, // Command not found (might be PATH issue)
		137: true, // Killed by signal (SIGKILL)
		143: true, // Killed by signal (SIGTERM)
	}

	return retryableCodes[result.ExitCode]
}

// RetryOnExitCodes creates a RetryIf function that retries on specific exit codes.
func RetryOnExitCodes(codes ...int) func(*CommandResult) bool {
	codeSet := make(map[int]bool)
	for _, c := range codes {
		codeSet[c] = true
	}
	return func(result *CommandResult) bool {
		return !result.Success && codeSet[result.ExitCode]
	}
}
