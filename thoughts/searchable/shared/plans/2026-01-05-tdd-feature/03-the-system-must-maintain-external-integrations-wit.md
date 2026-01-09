# Phase 03: The system must maintain external integrations wit...

## Requirements

### REQ_002: The system must maintain external integrations with Claude C

The system must maintain external integrations with Claude CLI, git, and beads CLI tools via os/exec subprocess calls

#### REQ_002.1: Implement Claude CLI wrapper using Go os/exec package with c

Implement Claude CLI wrapper using Go os/exec package with configurable timeout support, streaming output capture, and structured result handling for autonomous Claude Code sessions

##### Testable Behaviors

1. Execute Claude CLI commands with configurable timeout (default 1 hour, max configurable)
2. Support all Claude CLI flags: --print, --model, --permission-mode, --output-format
3. Capture stdout, stderr, and exit code in structured CommandResult
4. Implement context.WithTimeout for graceful cancellation
5. Support streaming output via io.Pipe or bufio.Scanner for real-time progress
6. Handle permission-mode 'bypassPermissions' for autonomous operation
7. Support model selection (sonnet/opus) via configuration
8. Return structured JSON response matching Python equivalent format
9. Implement retry logic with exponential backoff for transient failures
10. Log command execution details in debug mode
11. Handle working directory specification via cmd.Dir
12. Support environment variable passthrough to subprocess

#### REQ_002.2: Create comprehensive git integration for version control ope

Create comprehensive git integration for version control operations supporting status checks, commits, branching, and history analysis used throughout the orchestrator and loop-runner

##### Testable Behaviors

1. Execute git status to check working tree state
2. Execute git add with file path or '.' for all changes
3. Execute git commit with message and optional co-author support
4. Execute git log with configurable format and count
5. Execute git branch operations (create, list, switch, delete)
6. Execute git diff for staged and unstaged changes
7. Execute git describe --tags for version information
8. Parse git output into structured Go types
9. Support git operations in specified working directory
10. Handle non-zero exit codes with meaningful error messages
11. Support checking if directory is a git repository
12. Execute git rev-parse for commit hash retrieval
13. Support git remote operations for repository metadata

#### REQ_002.3: Build beads CLI wrapper as a public Go package (pkg/beads) f

Build beads CLI wrapper as a public Go package (pkg/beads) for issue tracking integration, providing a reusable API for creating, querying, and managing beads across projects

##### Testable Behaviors

1. Create public package at pkg/beads/client.go for external reuse
2. Execute 'bd' (beads) CLI commands via os/exec
3. Support bead creation with title, description, tags, and metadata
4. Support bead querying by ID, status, tags, or search terms
5. Support bead status updates (open, in-progress, closed, blocked)
6. Parse bead JSON output into structured Bead type
7. Support listing beads with filtering options
8. Support bead relationship management (blocked-by, related-to)
9. Handle beads CLI not installed error gracefully
10. Provide CheckInstalled() method to verify beads CLI availability
11. Support workspace/project-specific bead operations
12. Implement NewClient(workspacePath string) constructor pattern

#### REQ_002.4: Support build tools integration for cargo (Rust), npm (Node.

Support build tools integration for cargo (Rust), npm (Node.js), pytest (Python), go test (Go), and make commands with unified execution interface and result parsing

##### Testable Behaviors

1. Execute cargo build/test/run commands for Rust projects
2. Execute npm install/build/test/run commands for Node.js projects
3. Execute pytest commands with configurable arguments for Python projects
4. Execute go test/build commands for Go projects
5. Execute make targets with optional arguments
6. Parse test output to extract pass/fail counts where possible
7. Support working directory specification for all tools
8. Capture combined stdout/stderr with proper ordering
9. Support timeout configuration per build tool type
10. Detect project type from manifest files (Cargo.toml, package.json, pyproject.toml, go.mod, Makefile)
11. Return unified BuildResult with success, output, duration, and parsed metrics
12. Support environment variable injection for build commands
13. Handle tool not installed errors with helpful messages
14. Support verbose/quiet output modes


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed