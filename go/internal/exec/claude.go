package exec

import (
	"context"
	"time"
)

// DefaultClaudeTimeout is the default timeout for Claude invocations.
const DefaultClaudeTimeout = 1300 * time.Second

// DefaultClaudeModel is the default Claude model to use.
const DefaultClaudeModel = "claude-sonnet-4-20250514"

// ClaudeRunner executes Claude CLI commands.
type ClaudeRunner struct {
	runner           *Runner
	bypassPermissions bool
	model            string
	systemPrompt     string
}

// ClaudeOption is a functional option for configuring a ClaudeRunner.
type ClaudeOption func(*ClaudeRunner)

// NewClaudeRunner creates a new ClaudeRunner with the given options.
func NewClaudeRunner(opts ...ClaudeOption) *ClaudeRunner {
	cr := &ClaudeRunner{
		runner:           NewRunner(WithTimeout(DefaultClaudeTimeout)),
		bypassPermissions: true,
		model:            "",
	}
	for _, opt := range opts {
		opt(cr)
	}
	return cr
}

// WithClaudeTimeout sets the timeout for Claude invocations.
func WithClaudeTimeout(d time.Duration) ClaudeOption {
	return func(cr *ClaudeRunner) {
		cr.runner = NewRunner(WithTimeout(d))
	}
}

// WithClaudeWorkingDir sets the working directory for Claude invocations.
func WithClaudeWorkingDir(dir string) ClaudeOption {
	return func(cr *ClaudeRunner) {
		cr.runner = NewRunner(
			WithTimeout(DefaultClaudeTimeout),
			WithWorkingDir(dir),
		)
	}
}

// WithBypassPermissions sets whether to bypass permission checks.
func WithBypassPermissions(bypass bool) ClaudeOption {
	return func(cr *ClaudeRunner) {
		cr.bypassPermissions = bypass
	}
}

// WithModel sets the Claude model to use.
func WithModel(model string) ClaudeOption {
	return func(cr *ClaudeRunner) {
		cr.model = model
	}
}

// WithSystemPrompt sets a system prompt for Claude.
func WithSystemPrompt(prompt string) ClaudeOption {
	return func(cr *ClaudeRunner) {
		cr.systemPrompt = prompt
	}
}

// WithClaudeRunner sets a custom underlying runner.
func WithClaudeRunner(runner *Runner) ClaudeOption {
	return func(cr *ClaudeRunner) {
		cr.runner = runner
	}
}

// InvokeClaude invokes the Claude CLI with the given prompt.
func (cr *ClaudeRunner) InvokeClaude(ctx context.Context, prompt string) (*CommandResult, error) {
	args := cr.buildArgs(prompt)
	return cr.runner.Run(ctx, "claude", args...)
}

// InvokeClaudeWithModel invokes Claude with a specific model.
func (cr *ClaudeRunner) InvokeClaudeWithModel(ctx context.Context, prompt string, model string) (*CommandResult, error) {
	args := cr.buildArgsWithModel(prompt, model)
	return cr.runner.Run(ctx, "claude", args...)
}

// InvokeClaudeStreaming invokes Claude and streams output.
func (cr *ClaudeRunner) InvokeClaudeStreaming(ctx context.Context, prompt string) (<-chan string, <-chan string, <-chan *CommandResult) {
	args := cr.buildArgs(prompt)
	return cr.runner.RunStreaming(ctx, "claude", args...)
}

// buildArgs constructs the Claude CLI arguments.
func (cr *ClaudeRunner) buildArgs(prompt string) []string {
	args := []string{"--print"}

	if cr.bypassPermissions {
		args = append(args, "--permission-mode", "bypassPermissions")
	}

	if cr.model != "" {
		args = append(args, "--model", cr.model)
	}

	if cr.systemPrompt != "" {
		args = append(args, "--system-prompt", cr.systemPrompt)
	}

	args = append(args, "-p", prompt)

	return args
}

// buildArgsWithModel constructs Claude CLI arguments with a specific model override.
func (cr *ClaudeRunner) buildArgsWithModel(prompt string, model string) []string {
	args := []string{"--print"}

	if cr.bypassPermissions {
		args = append(args, "--permission-mode", "bypassPermissions")
	}

	args = append(args, "--model", model)

	if cr.systemPrompt != "" {
		args = append(args, "--system-prompt", cr.systemPrompt)
	}

	args = append(args, "-p", prompt)

	return args
}

// InvokeClaudeFunc is a convenience function for one-off Claude invocations.
func InvokeClaudeFunc(ctx context.Context, prompt string, timeout time.Duration) (*CommandResult, error) {
	cr := NewClaudeRunner(WithClaudeTimeout(timeout))
	return cr.InvokeClaude(ctx, prompt)
}

// InvokeClaudeWithDefaults invokes Claude with default settings (1300s timeout, bypassPermissions).
func InvokeClaudeWithDefaults(ctx context.Context, prompt string) (*CommandResult, error) {
	cr := NewClaudeRunner()
	return cr.InvokeClaude(ctx, prompt)
}
