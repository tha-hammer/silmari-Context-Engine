package exec

import (
	"context"
	"fmt"
	"strconv"
	"strings"
	"time"
)

// DefaultGitTimeout is the default timeout for git commands.
const DefaultGitTimeout = 30 * time.Second

// GitRunner executes git commands.
type GitRunner struct {
	runner *Runner
}

// GitOption is a functional option for configuring a GitRunner.
type GitOption func(*GitRunner)

// NewGitRunner creates a new GitRunner with the given options.
func NewGitRunner(opts ...GitOption) *GitRunner {
	gr := &GitRunner{
		runner: NewRunner(WithTimeout(DefaultGitTimeout)),
	}
	for _, opt := range opts {
		opt(gr)
	}
	return gr
}

// WithGitWorkingDir sets the working directory for git commands.
func WithGitWorkingDir(dir string) GitOption {
	return func(gr *GitRunner) {
		gr.runner = NewRunner(
			WithTimeout(DefaultGitTimeout),
			WithWorkingDir(dir),
		)
	}
}

// WithGitTimeout sets the timeout for git commands.
func WithGitTimeout(d time.Duration) GitOption {
	return func(gr *GitRunner) {
		gr.runner = NewRunner(WithTimeout(d))
	}
}

// WithGitRunner sets a custom underlying runner.
func WithGitRunner(runner *Runner) GitOption {
	return func(gr *GitRunner) {
		gr.runner = runner
	}
}

// Status runs git status and returns the result.
func (gr *GitRunner) Status(ctx context.Context) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "status")
}

// StatusShort runs git status --short and returns the result.
func (gr *GitRunner) StatusShort(ctx context.Context) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "status", "--short")
}

// StatusPorcelain runs git status --porcelain for machine-readable output.
func (gr *GitRunner) StatusPorcelain(ctx context.Context) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "status", "--porcelain")
}

// Diff runs git diff and returns the result.
// If cached is true, shows staged changes (--cached).
func (gr *GitRunner) Diff(ctx context.Context, cached bool) (*CommandResult, error) {
	args := []string{"diff"}
	if cached {
		args = append(args, "--cached")
	}
	return gr.runner.Run(ctx, "git", args...)
}

// DiffFiles runs git diff with specific files.
func (gr *GitRunner) DiffFiles(ctx context.Context, cached bool, files ...string) (*CommandResult, error) {
	args := []string{"diff"}
	if cached {
		args = append(args, "--cached")
	}
	args = append(args, "--")
	args = append(args, files...)
	return gr.runner.Run(ctx, "git", args...)
}

// DiffBranch runs git diff between branches or refs.
func (gr *GitRunner) DiffBranch(ctx context.Context, ref1, ref2 string) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "diff", ref1+"..."+ref2)
}

// Log runs git log with a limit.
func (gr *GitRunner) Log(ctx context.Context, limit int) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "log", fmt.Sprintf("-%d", limit))
}

// LogOneline runs git log --oneline with a limit.
func (gr *GitRunner) LogOneline(ctx context.Context, limit int) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "log", "--oneline", fmt.Sprintf("-%d", limit))
}

// LogFormat runs git log with a custom format.
func (gr *GitRunner) LogFormat(ctx context.Context, format string, limit int) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "log", fmt.Sprintf("--format=%s", format), fmt.Sprintf("-%d", limit))
}

// Add runs git add with the given files.
func (gr *GitRunner) Add(ctx context.Context, files ...string) (*CommandResult, error) {
	args := []string{"add"}
	args = append(args, files...)
	return gr.runner.Run(ctx, "git", args...)
}

// AddAll runs git add --all.
func (gr *GitRunner) AddAll(ctx context.Context) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "add", "--all")
}

// Commit runs git commit with the given message.
func (gr *GitRunner) Commit(ctx context.Context, message string) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "commit", "-m", message)
}

// Branch returns the current branch name.
func (gr *GitRunner) Branch(ctx context.Context) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "branch", "--show-current")
}

// BranchList lists all branches.
func (gr *GitRunner) BranchList(ctx context.Context, all bool) (*CommandResult, error) {
	args := []string{"branch"}
	if all {
		args = append(args, "-a")
	}
	return gr.runner.Run(ctx, "git", args...)
}

// Checkout checks out a branch or file.
func (gr *GitRunner) Checkout(ctx context.Context, ref string) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "checkout", ref)
}

// CheckoutNewBranch creates and checks out a new branch.
func (gr *GitRunner) CheckoutNewBranch(ctx context.Context, branch string) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "checkout", "-b", branch)
}

// Pull runs git pull.
func (gr *GitRunner) Pull(ctx context.Context) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "pull")
}

// Push runs git push.
func (gr *GitRunner) Push(ctx context.Context) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "push")
}

// PushSetUpstream runs git push --set-upstream origin <branch>.
func (gr *GitRunner) PushSetUpstream(ctx context.Context, branch string) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "push", "--set-upstream", "origin", branch)
}

// Fetch runs git fetch.
func (gr *GitRunner) Fetch(ctx context.Context) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "fetch")
}

// FetchAll runs git fetch --all.
func (gr *GitRunner) FetchAll(ctx context.Context) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "fetch", "--all")
}

// RemoteURL returns the URL of the origin remote.
func (gr *GitRunner) RemoteURL(ctx context.Context) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "remote", "get-url", "origin")
}

// Rev returns the current HEAD revision.
func (gr *GitRunner) Rev(ctx context.Context) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "rev-parse", "HEAD")
}

// RevShort returns the short form of the current HEAD revision.
func (gr *GitRunner) RevShort(ctx context.Context) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "rev-parse", "--short", "HEAD")
}

// Stash runs git stash.
func (gr *GitRunner) Stash(ctx context.Context) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "stash")
}

// StashPop runs git stash pop.
func (gr *GitRunner) StashPop(ctx context.Context) (*CommandResult, error) {
	return gr.runner.Run(ctx, "git", "stash", "pop")
}

// Reset runs git reset with the given mode and ref.
func (gr *GitRunner) Reset(ctx context.Context, mode string, ref string) (*CommandResult, error) {
	args := []string{"reset"}
	if mode != "" {
		args = append(args, "--"+mode)
	}
	if ref != "" {
		args = append(args, ref)
	}
	return gr.runner.Run(ctx, "git", args...)
}

// Clean runs git clean with the given options.
func (gr *GitRunner) Clean(ctx context.Context, force bool, directories bool) (*CommandResult, error) {
	args := []string{"clean"}
	if force {
		args = append(args, "-f")
	}
	if directories {
		args = append(args, "-d")
	}
	return gr.runner.Run(ctx, "git", args...)
}

// IsRepo checks if the current directory is a git repository.
func (gr *GitRunner) IsRepo(ctx context.Context) (bool, error) {
	result, err := gr.runner.Run(ctx, "git", "rev-parse", "--is-inside-work-tree")
	if err != nil {
		return false, err
	}
	return result.Success && strings.TrimSpace(result.Output) == "true", nil
}

// GetCommitCount returns the number of commits in the current branch.
func (gr *GitRunner) GetCommitCount(ctx context.Context) (int, error) {
	result, err := gr.runner.Run(ctx, "git", "rev-list", "--count", "HEAD")
	if err != nil {
		return 0, err
	}
	if !result.Success {
		return 0, fmt.Errorf("git rev-list failed: %s", result.Error)
	}
	count, err := strconv.Atoi(strings.TrimSpace(result.Output))
	if err != nil {
		return 0, fmt.Errorf("failed to parse commit count: %w", err)
	}
	return count, nil
}
