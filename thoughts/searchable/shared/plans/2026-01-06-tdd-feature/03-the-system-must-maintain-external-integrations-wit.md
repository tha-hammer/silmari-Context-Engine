# Phase 03: The system must maintain external integrations wit...

## Requirements

### REQ_002: The system must maintain external integrations with Claude C

The system must maintain external integrations with Claude CLI, git, and beads CLI tools via os/exec subprocess calls with proper timeout handling and output capture

#### REQ_002.1: Implement Claude CLI wrapper supporting --print, --model, --

Implement Claude CLI wrapper supporting --print, --model, --permission-mode, and --output-format flags with streaming output support

##### Testable Behaviors

1. ClaudeRunner struct accepts model (sonnet/opus), timeout, outputFormat (text/stream-json), and working directory
2. Execute method constructs 'claude --print --model <model> --permission-mode bypassPermissions --output-format <format> <prompt>' command
3. Streaming output pipes stdout to terminal in real-time using bufio.Scanner
4. stream-json format emits JSON events compatible with npx repomirror visualize
5. Returns CommandResult struct with Success, Output, Error, Elapsed, and ReturnCode fields
6. Handles TimeoutExpired by returning structured error result without crashing
7. Supports optional PTY wrapper via os/exec and script command for real-time streaming
8. CLAUDE_CODE_MAX_OUTPUT_TOKENS environment variable defaults to 128000
9. Formats tool calls with ANSI colors for human-readable output mode

#### REQ_002.2: Implement context.WithTimeout for command execution with con

Implement context.WithTimeout for command execution with configurable timeout (default 1 hour for Claude calls)

##### Testable Behaviors

1. All subprocess calls use context.WithTimeout with configurable duration
2. Default timeout for Claude CLI calls is 1 hour (3600 seconds) matching Python SESSION_TIMEOUT
3. Default timeout for beads CLI calls is 30 seconds
4. Default timeout for git CLI calls is 60 seconds
5. Timeout cancellation properly kills child process and all descendants
6. TimeoutError is distinguishable from other errors via error type assertion
7. Elapsed time is tracked accurately regardless of timeout or success
8. Context cancellation is propagated through goroutines for streaming operations
9. Partial output is captured and returned even when timeout occurs

#### REQ_002.3: Implement git subprocess calls for version control operation

Implement git subprocess calls for version control operations including init, add, commit, config, status, and diff

##### Testable Behaviors

1. GitRunner struct wraps os/exec for git CLI operations
2. Init(path string) error initializes new git repository at path
3. Add(paths ...string) error stages files with 'git add' (supports -A flag for all)
4. Commit(message string) error creates commit with 'git commit -m'
5. Config(key, value string) error sets git config locally
6. Status() (string, error) returns current working tree status
7. Diff(staged bool) (string, error) returns diff output (--staged flag optional)
8. GetHeadCommit() (string, error) returns current HEAD commit hash
9. All operations capture stdout and stderr separately
10. Working directory (cwd) is configurable per GitRunner instance
11. 60 second default timeout for all git operations

#### REQ_002.4: Implement beads (bd) CLI wrapper for issue tracking operatio

Implement beads (bd) CLI wrapper for issue tracking operations with JSON output support

##### Testable Behaviors

1. BeadsController struct wraps 'bd' CLI with project_path configuration
2. All operations support --json flag for structured JSON output
3. CreateIssue(title, issueType, priority) returns created issue data
4. CreateEpic(title, priority) is convenience wrapper for epic creation
5. ListIssues(status filter) returns list of issues as []Issue struct
6. CloseIssue(issueId, reason) closes issue with optional reason
7. AddDependency(issueId, dependsOn) adds dependency relationship
8. Sync() syncs beads with git remote (does not use --json)
9. GetReadyIssue(limit) returns issues with no blockers
10. UpdateStatus(issueId, status) updates issue status
11. ShowIssue(issueId) returns full issue details as Issue struct
12. 30 second default timeout for all beads operations
13. Handles 'bd command not found' error gracefully with descriptive message
14. JSON parse errors return raw stdout as fallback

#### REQ_002.5: Support build tool integrations: cargo, npm, pytest, go test

Support build tool integrations: cargo, npm, pytest, go test, make with automatic detection

##### Testable Behaviors

1. BuildToolRunner detects project type from marker files (Cargo.toml, package.json, go.mod, requirements.txt, pyproject.toml, Makefile)
2. DetectTestCommand(projectPath) returns appropriate test command string or empty if unknown
3. Cargo projects return 'cargo test'
4. Node.js projects return 'npm test'
5. Go projects return 'go test ./...'
6. Python projects return 'pytest'
7. Makefile projects return 'make test'
8. RunTests(projectPath) executes detected test command with output capture
9. RunBuild(projectPath) executes appropriate build command (cargo build, npm run build, go build, make)
10. Configurable timeout per tool type (default 5 minutes for tests, 10 minutes for builds)
11. Returns structured result with pass/fail status, output, and elapsed time
12. Supports running arbitrary commands via RunCommand(projectPath, command) for flexibility


## Success Criteria

- [x] All tests pass
- [x] All behaviors implemented
- [ ] Code reviewed

## Implementation Summary (2026-01-06)

### Implemented Packages

**go/internal/exec/** - External tool integrations

**Claude CLI (claude.go)**
- ClaudeRunner struct with configurable timeout, model, permissions, and working directory
- InvokeClaude and InvokeClaudeStreaming methods
- Default timeout: 1300 seconds
- Supports --print, --model, --permission-mode flags

**Git CLI (git.go)**
- GitRunner struct with 30 second default timeout
- Full git operations: Status, Diff, Log, Add, Commit, Branch, Checkout, Pull, Push, Fetch, Stash, Reset, Clean
- Working directory configurable per instance
- Captures stdout and stderr separately

**Beads CLI (beads.go)**
- BeadsRunner struct with 30 second default timeout
- Operations: Ready, List, Show, Create, Update, Close, DepAdd, Blocked, Sync, Stats, Doctor
- ParseIssueID helper for extracting issue IDs from output

**Build Tools (buildtools.go)**
- BuildToolRunner with auto-detection from marker files
- Supported: Rust (Cargo.toml), Node.js (package.json), Go (go.mod), Python (pyproject.toml/requirements.txt), Make (Makefile)
- DetectTestCommand: cargo test, npm test, go test ./..., pytest, make test
- DetectBuildCommand: cargo build, npm run build, go build ./..., make
- Configurable timeouts: 5 min tests, 10 min builds
- RunCommand for arbitrary commands

**Core Command Execution (runner.go, result.go)**
- Runner with context.WithTimeout support
- CommandResult struct with Success, Output, Error, ExitCode, Elapsed
- Streaming output support via channels
- Environment variable and working directory support