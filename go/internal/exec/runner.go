package exec

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"os/exec"
	"time"
)

// DefaultTimeout is the default command timeout.
const DefaultTimeout = 120 * time.Second

// Runner executes external commands with configurable options.
type Runner struct {
	timeout    time.Duration
	workingDir string
	env        []string
	stdout     io.Writer
	stderr     io.Writer
}

// RunnerOption is a functional option for configuring a Runner.
type RunnerOption func(*Runner)

// NewRunner creates a new Runner with the given options.
func NewRunner(opts ...RunnerOption) *Runner {
	r := &Runner{
		timeout: DefaultTimeout,
	}
	for _, opt := range opts {
		opt(r)
	}
	return r
}

// WithTimeout sets the command timeout.
func WithTimeout(d time.Duration) RunnerOption {
	return func(r *Runner) {
		r.timeout = d
	}
}

// WithWorkingDir sets the working directory for commands.
func WithWorkingDir(dir string) RunnerOption {
	return func(r *Runner) {
		r.workingDir = dir
	}
}

// WithEnv sets the environment variables for commands.
// The format is "KEY=VALUE".
func WithEnv(env []string) RunnerOption {
	return func(r *Runner) {
		r.env = env
	}
}

// WithStdout sets a writer to receive stdout in addition to capturing it.
func WithStdout(w io.Writer) RunnerOption {
	return func(r *Runner) {
		r.stdout = w
	}
}

// WithStderr sets a writer to receive stderr in addition to capturing it.
func WithStderr(w io.Writer) RunnerOption {
	return func(r *Runner) {
		r.stderr = w
	}
}

// Run executes a command and returns the result.
func (r *Runner) Run(ctx context.Context, name string, args ...string) (*CommandResult, error) {
	return r.RunWithStdin(ctx, nil, name, args...)
}

// RunWithStdin executes a command with stdin and returns the result.
func (r *Runner) RunWithStdin(ctx context.Context, stdin io.Reader, name string, args ...string) (*CommandResult, error) {
	// Apply timeout if not already set in context
	if r.timeout > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, r.timeout)
		defer cancel()
	}

	startTime := time.Now()

	cmd := exec.CommandContext(ctx, name, args...)

	// Set working directory if specified
	if r.workingDir != "" {
		cmd.Dir = r.workingDir
	}

	// Set environment if specified
	if len(r.env) > 0 {
		cmd.Env = r.env
	}

	// Set stdin if provided
	if stdin != nil {
		cmd.Stdin = stdin
	}

	// Set up stdout capture
	var stdoutBuf bytes.Buffer
	if r.stdout != nil {
		cmd.Stdout = io.MultiWriter(&stdoutBuf, r.stdout)
	} else {
		cmd.Stdout = &stdoutBuf
	}

	// Set up stderr capture
	var stderrBuf bytes.Buffer
	if r.stderr != nil {
		cmd.Stderr = io.MultiWriter(&stderrBuf, r.stderr)
	} else {
		cmd.Stderr = &stderrBuf
	}

	// Execute the command
	err := cmd.Run()
	elapsed := time.Since(startTime)

	// Check for context deadline exceeded (timeout)
	if ctx.Err() == context.DeadlineExceeded {
		return NewTimeoutResult(r.timeout), nil
	}

	// Check for context cancellation
	if ctx.Err() == context.Canceled {
		return &CommandResult{
			Success:  false,
			Output:   stdoutBuf.String(),
			Error:    "command cancelled",
			ExitCode: -1,
			Elapsed:  elapsed,
		}, nil
	}

	// Handle execution errors
	if err != nil {
		exitCode := -1
		if exitErr, ok := err.(*exec.ExitError); ok {
			exitCode = exitErr.ExitCode()
		}
		return NewCommandResult(false, stdoutBuf.String(), stderrBuf.String(), exitCode, elapsed), nil
	}

	return NewSuccessResult(stdoutBuf.String(), elapsed), nil
}

// RunStreaming executes a command and streams output to channels.
// The channels are closed when the command completes.
func (r *Runner) RunStreaming(ctx context.Context, name string, args ...string) (<-chan string, <-chan string, <-chan *CommandResult) {
	stdoutCh := make(chan string, 100)
	stderrCh := make(chan string, 100)
	resultCh := make(chan *CommandResult, 1)

	go func() {
		defer close(stdoutCh)
		defer close(stderrCh)
		defer close(resultCh)

		// Apply timeout if not already set in context
		if r.timeout > 0 {
			var cancel context.CancelFunc
			ctx, cancel = context.WithTimeout(ctx, r.timeout)
			defer cancel()
		}

		startTime := time.Now()

		cmd := exec.CommandContext(ctx, name, args...)

		if r.workingDir != "" {
			cmd.Dir = r.workingDir
		}

		if len(r.env) > 0 {
			cmd.Env = r.env
		}

		// Create pipes for streaming
		stdoutPipe, err := cmd.StdoutPipe()
		if err != nil {
			resultCh <- NewErrorResult(fmt.Errorf("failed to create stdout pipe: %w", err), time.Since(startTime))
			return
		}

		stderrPipe, err := cmd.StderrPipe()
		if err != nil {
			resultCh <- NewErrorResult(fmt.Errorf("failed to create stderr pipe: %w", err), time.Since(startTime))
			return
		}

		if err := cmd.Start(); err != nil {
			resultCh <- NewErrorResult(fmt.Errorf("failed to start command: %w", err), time.Since(startTime))
			return
		}

		var stdoutBuf, stderrBuf bytes.Buffer

		// Stream stdout
		go func() {
			buf := make([]byte, 1024)
			for {
				n, err := stdoutPipe.Read(buf)
				if n > 0 {
					chunk := string(buf[:n])
					stdoutBuf.WriteString(chunk)
					select {
					case stdoutCh <- chunk:
					case <-ctx.Done():
						return
					}
				}
				if err != nil {
					return
				}
			}
		}()

		// Stream stderr
		go func() {
			buf := make([]byte, 1024)
			for {
				n, err := stderrPipe.Read(buf)
				if n > 0 {
					chunk := string(buf[:n])
					stderrBuf.WriteString(chunk)
					select {
					case stderrCh <- chunk:
					case <-ctx.Done():
						return
					}
				}
				if err != nil {
					return
				}
			}
		}()

		err = cmd.Wait()
		elapsed := time.Since(startTime)

		if ctx.Err() == context.DeadlineExceeded {
			resultCh <- NewTimeoutResult(r.timeout)
			return
		}

		if ctx.Err() == context.Canceled {
			resultCh <- &CommandResult{
				Success:  false,
				Output:   stdoutBuf.String(),
				Error:    "command cancelled",
				ExitCode: -1,
				Elapsed:  elapsed,
			}
			return
		}

		if err != nil {
			exitCode := -1
			if exitErr, ok := err.(*exec.ExitError); ok {
				exitCode = exitErr.ExitCode()
			}
			resultCh <- NewCommandResult(false, stdoutBuf.String(), stderrBuf.String(), exitCode, elapsed)
			return
		}

		resultCh <- NewSuccessResult(stdoutBuf.String(), elapsed)
	}()

	return stdoutCh, stderrCh, resultCh
}
