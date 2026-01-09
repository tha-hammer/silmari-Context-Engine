# Phase 01: The system must rewrite core Python logic in Go, c...

## Requirements

### REQ_000: The system must rewrite core Python logic in Go, converting 

The system must rewrite core Python logic in Go, converting ~35,371 lines of Python code including subprocess management, JSON handling, and CLI parsing to idiomatic Go equivalents

#### REQ_000.1: Convert subprocess module usage to os/exec package for exter

Convert subprocess module usage to os/exec package for external command execution, implementing wrappers for Claude CLI, git, and beads CLI tools with timeout support, output streaming, and error handling

##### Testable Behaviors

1. Execute external commands (claude, git, bd) with configurable timeout using context.WithTimeout
2. Capture stdout and stderr separately or combined based on use case
3. Support working directory specification via cmd.Dir for project-scoped operations
4. Implement streaming output reading using bufio.Scanner for long-running commands
5. Handle process termination gracefully when context is cancelled
6. Return structured CommandResult with Success bool, Output string, Error string, and ExitCode int
7. Support environment variable injection via cmd.Env for Claude CLI configuration
8. Implement retry logic with exponential backoff for transient failures
9. Log command execution with sanitized arguments (hide sensitive data)
10. Support both synchronous execution (CombinedOutput) and async execution (goroutines with channels)

#### REQ_000.2: Convert json module to encoding/json for JSON parsing and se

Convert json module to encoding/json for JSON parsing and serialization, implementing marshaling/unmarshaling for all data models including Feature, FeatureList, RequirementNode, RequirementHierarchy, and checkpoint structures

##### Testable Behaviors

1. Define all struct types with proper json struct tags matching Python field names (snake_case)
2. Use pointer types for optional fields with omitempty tag to exclude null values
3. Implement custom MarshalJSON/UnmarshalJSON for complex types like RequirementNode with validation
4. Support JSON streaming for large files using json.Decoder with Token() method
5. Handle null values in JSON by using pointer types (*string, *int) for optional fields
6. Implement pretty-printing with json.MarshalIndent for human-readable output
7. Parse JSON files from disk using os.ReadFile + json.Unmarshal pattern
8. Write JSON files atomically using temp file + rename pattern to prevent corruption
9. Support parsing JSON embedded in Claude CLI text output (extract JSON from mixed content)
10. Validate JSON schema compatibility with existing Python-generated files

#### REQ_000.3: Convert pathlib.Path operations to path/filepath package for

Convert pathlib.Path operations to path/filepath package for cross-platform file system operations including path joining, resolution, existence checking, and directory traversal

##### Testable Behaviors

1. Implement path joining using filepath.Join for cross-platform compatibility (handles / vs \)
2. Convert absolute path resolution using filepath.Abs with error handling
3. Implement file/directory existence checking using os.Stat with proper error type checking
4. Support glob pattern matching using filepath.Glob for file discovery
5. Implement recursive directory walking using filepath.WalkDir for project scanning
6. Create directory trees using os.MkdirAll with configurable permissions (0755 default)
7. Implement path cleaning using filepath.Clean to normalize paths
8. Support home directory expansion (~/) using os.UserHomeDir
9. Handle symbolic links appropriately using filepath.EvalSymlinks when needed
10. Implement relative path calculation using filepath.Rel for display purposes

#### REQ_000.4: Convert Python dataclasses to Go structs with validation met

Convert Python dataclasses to Go structs with validation methods, implementing post-initialization validation, default values, and JSON serialization for all core data models

##### Testable Behaviors

1. Convert all Python @dataclass definitions to Go structs with exported fields
2. Implement Validate() error method on each struct for post-construction validation
3. Create NewXxx() constructor functions that apply defaults and run validation
4. Use pointer types for optional fields that have meaningful nil states
5. Implement String() method for human-readable representation (debugging)
6. Use embedded structs for common field patterns (timestamps, metadata)
7. Implement Validatable interface: type Validatable interface { Validate() error }
8. Support field-level validation with descriptive error messages
9. Implement custom type for enums using const + iota pattern with validation
10. Create DeepCopy() methods for structs that need cloning

#### REQ_000.5: Convert asyncio patterns to goroutines and channels for conc

Convert asyncio patterns to goroutines and channels for concurrent execution of pipeline steps, Claude sessions, and background tasks with proper synchronization and cancellation support

##### Testable Behaviors

1. Convert async def functions to goroutines with channel-based communication
2. Implement context.Context propagation for cancellation support throughout the call chain
3. Use sync.WaitGroup for coordinating multiple concurrent operations
4. Implement errgroup.Group for concurrent tasks that need first-error collection
5. Create buffered channels for producer-consumer patterns (streaming output)
6. Use select statement for multiplexing channel operations and timeout handling
7. Implement proper goroutine cleanup to prevent leaks on cancellation
8. Use sync.Mutex for protecting shared state in concurrent contexts
9. Implement rate limiting using time.Ticker for API call pacing
10. Support graceful shutdown with signal handling (SIGINT, SIGTERM)


## Success Criteria

- [x] All tests pass
- [x] All behaviors implemented
- [ ] Code reviewed

## Implementation Summary (2026-01-06)

### Implemented Packages

**go/internal/exec/** - Command execution
- `runner.go` - Core command runner with timeout, streaming, working dir support
- `result.go` - CommandResult struct with JSON serialization
- `retry.go` - Retry logic with exponential backoff and jitter
- `claude.go` - Claude CLI wrapper
- `git.go` - Git command wrapper
- `beads.go` - Beads (bd) CLI wrapper

**go/internal/fs/** - File system operations
- `path.go` - Cross-platform path operations (Join, Abs, Glob, WalkDir, etc.)
- Home directory expansion, symlink handling, atomic operations

**go/internal/jsonutil/** - JSON utilities
- `jsonutil.go` - File read/write, atomic writes, streaming, JSON extraction from mixed text

**go/internal/concurrent/** - Concurrency primitives
- `group.go` - errgroup wrapper with limits
- `worker.go` - Generic worker pool
- `stream.go` - Generic stream type with channels
- `ratelimit.go` - Token bucket rate limiter, throttle, debounce
- `signal.go` - Signal handling for graceful shutdown

**go/internal/models/** - Data models
- `context_entry.go` - ContextEntry with validation
- `entry_type.go` - EntryType enum with JSON serialization