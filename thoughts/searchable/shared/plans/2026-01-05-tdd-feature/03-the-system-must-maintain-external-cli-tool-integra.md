# Phase 03: The system must maintain external CLI tool integra...

## Requirements

### REQ_002: The system must maintain external CLI tool integrations by c

The system must maintain external CLI tool integrations by calling them via os/exec

#### REQ_002.1: Implement Claude CLI wrapper for claude command execution wi

Implement Claude CLI wrapper for claude command execution with timeout handling, output capture, and structured result parsing

##### Testable Behaviors

1. Must spawn claude CLI process using os/exec with correct arguments (--print, --model, --permission-mode, -p)
2. Must support configurable timeout with context.WithTimeout (default 1300s, max 3600s for long sessions)
3. Must capture stdout, stderr, and return code in CommandResult struct
4. Must handle FileNotFoundError when claude binary is not installed and return appropriate error
5. Must handle subprocess.TimeoutExpired equivalent and return timeout-specific error message
6. Must support --output-format options (text, stream-json) for different output modes
7. Must preserve working directory context when executing commands via cmd.Dir
8. Must validate claude binary exists before execution using exec.LookPath or 'which claude'
9. Must support model selection via --model flag (sonnet, opus, haiku)
10. Must support bypassPermissions and other permission modes
11. Must return elapsed execution time in result for metrics tracking
12. Must support prompt file path as alternative to inline prompt string
13. Must handle MCP list operations (claude mcp list, claude mcp add)

#### REQ_002.2: Implement git version control command wrapper for repository

Implement git version control command wrapper for repository operations including init, status, diff, add, commit, log, and rev-parse

##### Testable Behaviors

1. Must execute git init to initialize new repositories
2. Must execute git status --porcelain for machine-readable status output
3. Must execute git diff for viewing staged and unstaged changes
4. Must execute git add -A for staging all changes
5. Must execute git commit -m with HEREDOC format for multi-line messages
6. Must execute git log --oneline --grep for searching commit history by feature ID
7. Must execute git rev-parse HEAD to get current commit hash
8. Must execute git config for setting user.email and user.name
9. Must capture and return exit code, stdout, and stderr
10. Must handle non-git directories gracefully with appropriate error
11. Must support custom working directory via cmd.Dir for project-specific operations
12. Must implement timeout of 30 seconds for status operations, 10 seconds for simple commands
13. Must return boolean indicating if repository has uncommitted changes

#### REQ_002.3: Implement beads (bd) issue tracking CLI wrapper for issue cr

Implement beads (bd) issue tracking CLI wrapper for issue creation, listing, status updates, dependencies, and synchronization

##### Testable Behaviors

1. Must execute bd create with --title, --type, and --priority flags
2. Must execute bd list with optional --status filter and --json output
3. Must execute bd close with issue ID and optional --reason flag
4. Must execute bd dep add for adding issue dependencies
5. Must execute bd sync for synchronizing with git remote
6. Must execute bd ready --limit=N for getting next available issues
7. Must execute bd update with --status flag for status transitions
8. Must execute bd show for retrieving full issue details
9. Must parse JSON output from bd commands into typed Go structs
10. Must handle bd command not found error with descriptive message 'bd command not found. Is beads installed?'
11. Must support configurable timeout (default 30 seconds, 60 seconds for sync)
12. Must handle JSON decode errors and fall back to raw string output
13. Must validate issue ID format before executing commands

#### REQ_002.4: Support build tool execution for multiple ecosystems includi

Support build tool execution for multiple ecosystems including cargo (Rust), npm (Node.js), pytest (Python), go test (Go), and make (general)

##### Testable Behaviors

1. Must execute cargo test for Rust projects with capture of test output
2. Must execute cargo build for Rust compilation
3. Must execute npm run test for Node.js projects
4. Must execute npm install for dependency installation
5. Must execute npm run build for Node.js builds
6. Must execute pytest for Python test execution
7. Must execute go test ./... for Go test execution
8. Must execute make with optional target argument
9. Must auto-detect project type from manifest files (Cargo.toml, package.json, pyproject.toml, go.mod, Makefile)
10. Must capture test pass/fail counts from output where possible
11. Must support configurable timeout (default 120 seconds for tests, 300 seconds for builds)
12. Must preserve environment variables during execution
13. Must return structured result with success, output, and parsed test results
14. Must handle build tool not found errors with ecosystem-specific install instructions


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed