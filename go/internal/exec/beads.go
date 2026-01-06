package exec

import (
	"context"
	"strings"
	"time"
)

// DefaultBeadsTimeout is the default timeout for beads CLI commands.
const DefaultBeadsTimeout = 30 * time.Second

// BeadsRunner executes beads (bd) CLI commands for issue tracking.
type BeadsRunner struct {
	runner *Runner
}

// BeadsOption is a functional option for configuring a BeadsRunner.
type BeadsOption func(*BeadsRunner)

// NewBeadsRunner creates a new BeadsRunner with the given options.
func NewBeadsRunner(opts ...BeadsOption) *BeadsRunner {
	br := &BeadsRunner{
		runner: NewRunner(WithTimeout(DefaultBeadsTimeout)),
	}
	for _, opt := range opts {
		opt(br)
	}
	return br
}

// WithBeadsWorkingDir sets the working directory for beads commands.
func WithBeadsWorkingDir(dir string) BeadsOption {
	return func(br *BeadsRunner) {
		br.runner = NewRunner(
			WithTimeout(DefaultBeadsTimeout),
			WithWorkingDir(dir),
		)
	}
}

// WithBeadsTimeout sets the timeout for beads commands.
func WithBeadsTimeout(d time.Duration) BeadsOption {
	return func(br *BeadsRunner) {
		br.runner = NewRunner(WithTimeout(d))
	}
}

// WithBeadsRunner sets a custom underlying runner.
func WithBeadsRunner(runner *Runner) BeadsOption {
	return func(br *BeadsRunner) {
		br.runner = runner
	}
}

// Ready runs 'bd ready' to show issues ready to work on.
func (br *BeadsRunner) Ready(ctx context.Context) (*CommandResult, error) {
	return br.runner.Run(ctx, "bd", "ready")
}

// List runs 'bd list' with optional filters.
func (br *BeadsRunner) List(ctx context.Context, status string) (*CommandResult, error) {
	args := []string{"list"}
	if status != "" {
		args = append(args, "--status="+status)
	}
	return br.runner.Run(ctx, "bd", args...)
}

// Show runs 'bd show <id>' to display issue details.
func (br *BeadsRunner) Show(ctx context.Context, id string) (*CommandResult, error) {
	return br.runner.Run(ctx, "bd", "show", id)
}

// Create runs 'bd create' with the given parameters.
func (br *BeadsRunner) Create(ctx context.Context, title, issueType string, priority int) (*CommandResult, error) {
	args := []string{
		"create",
		"--title=" + title,
		"--type=" + issueType,
		"--priority=" + priorityToString(priority),
	}
	return br.runner.Run(ctx, "bd", args...)
}

// Update runs 'bd update <id>' with the given status.
func (br *BeadsRunner) Update(ctx context.Context, id, status string) (*CommandResult, error) {
	return br.runner.Run(ctx, "bd", "update", id, "--status="+status)
}

// UpdateAssignee runs 'bd update <id> --assignee=<user>'.
func (br *BeadsRunner) UpdateAssignee(ctx context.Context, id, assignee string) (*CommandResult, error) {
	return br.runner.Run(ctx, "bd", "update", id, "--assignee="+assignee)
}

// Close runs 'bd close <id>' to mark an issue complete.
func (br *BeadsRunner) Close(ctx context.Context, ids ...string) (*CommandResult, error) {
	args := append([]string{"close"}, ids...)
	return br.runner.Run(ctx, "bd", args...)
}

// CloseWithReason runs 'bd close <id> --reason="..."'.
func (br *BeadsRunner) CloseWithReason(ctx context.Context, id, reason string) (*CommandResult, error) {
	return br.runner.Run(ctx, "bd", "close", id, "--reason="+reason)
}

// DepAdd runs 'bd dep add <issue> <depends-on>'.
func (br *BeadsRunner) DepAdd(ctx context.Context, issue, dependsOn string) (*CommandResult, error) {
	return br.runner.Run(ctx, "bd", "dep", "add", issue, dependsOn)
}

// Blocked runs 'bd blocked' to show blocked issues.
func (br *BeadsRunner) Blocked(ctx context.Context) (*CommandResult, error) {
	return br.runner.Run(ctx, "bd", "blocked")
}

// Sync runs 'bd sync' to sync with git remote.
func (br *BeadsRunner) Sync(ctx context.Context) (*CommandResult, error) {
	return br.runner.Run(ctx, "bd", "sync")
}

// SyncStatus runs 'bd sync --status' to check sync status.
func (br *BeadsRunner) SyncStatus(ctx context.Context) (*CommandResult, error) {
	return br.runner.Run(ctx, "bd", "sync", "--status")
}

// Stats runs 'bd stats' for project statistics.
func (br *BeadsRunner) Stats(ctx context.Context) (*CommandResult, error) {
	return br.runner.Run(ctx, "bd", "stats")
}

// Doctor runs 'bd doctor' to check for issues.
func (br *BeadsRunner) Doctor(ctx context.Context) (*CommandResult, error) {
	return br.runner.Run(ctx, "bd", "doctor")
}

// priorityToString converts a priority int to the P0-P4 format.
func priorityToString(p int) string {
	if p < 0 {
		p = 0
	}
	if p > 4 {
		p = 4
	}
	return "P" + string(rune('0'+p))
}

// ParseIssueID extracts the issue ID from beads output.
// Returns empty string if not found.
func ParseIssueID(output string) string {
	// Look for patterns like "silmari-Context-Engine-xxxx"
	lines := strings.Split(output, "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if strings.Contains(line, "-") && len(line) > 10 {
			// Check if it looks like an issue ID
			parts := strings.Split(line, ":")
			if len(parts) > 0 {
				id := strings.TrimSpace(parts[0])
				if isValidIssueID(id) {
					return id
				}
			}
		}
	}
	return ""
}

// isValidIssueID checks if a string looks like a beads issue ID.
func isValidIssueID(s string) bool {
	// Issue IDs are like "project-name-xxxx"
	parts := strings.Split(s, "-")
	return len(parts) >= 2 && len(s) > 8
}
