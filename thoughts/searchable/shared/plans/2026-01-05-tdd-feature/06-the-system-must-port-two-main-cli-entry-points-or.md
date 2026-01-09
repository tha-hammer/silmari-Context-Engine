# Phase 06: The system must port two main CLI entry points: or...

## Requirements

### REQ_005: The system must port two main CLI entry points: orchestrator

The system must port two main CLI entry points: orchestrator.py (~1,367 lines) as context-engine binary and loop-runner.py (~1,382 lines) as loop-runner binary

#### REQ_005.1: Create cmd/orchestrator/main.go entry point for context-engi

Create cmd/orchestrator/main.go entry point for context-engine binary that serves as the primary CLI interface for the context-engineered agent orchestrator

##### Testable Behaviors

1. main.go file exists at cmd/orchestrator/main.go with proper package declaration
2. Version information embedded via ldflags (-X main.version) during build
3. Root cobra command initialized with Use='context-engine', Short and Long descriptions
4. Signal handling implemented for SIGINT/SIGTERM with graceful shutdown
5. Exit codes follow Unix conventions (0=success, 1=general error, 2=misuse)
6. Main function calls cmd.Execute() and handles error return appropriately
7. Binary compiles successfully with 'go build -o bin/context-engine ./cmd/orchestrator'
8. Binary installs to /usr/local/bin via 'make install'
9. Help output (-h/--help) displays all available commands and flags
10. Version output (--version) displays embedded version string

#### REQ_005.2: Create cmd/loop-runner/main.go entry point for loop-runner b

Create cmd/loop-runner/main.go entry point for loop-runner binary that continuously runs Claude Code sessions for autonomous feature implementation

##### Testable Behaviors

1. main.go file exists at cmd/loop-runner/main.go with proper package declaration
2. Separate binary builds as 'loop-runner' distinct from 'context-engine'
3. Root cobra command initialized with Use='loop-runner' and appropriate descriptions
4. Supports loading feature list from features.json file
5. Implements continuous loop with configurable iteration limits
6. Graceful shutdown on SIGINT preserves session state
7. Recovery mechanism loads last checkpoint on restart
8. Progress reporting to stdout with colored output
9. Binary compiles with 'go build -o bin/loop-runner ./cmd/loop-runner'
10. Both binaries can be installed simultaneously via single 'make install'

#### REQ_005.3: Port orchestrator CLI flags including --project, --new, --mo

Port orchestrator CLI flags including --project, --new, --model, --max-sessions, --continue, --status, --mcp-preset, --with-qa, --debug using cobra flag system

##### Testable Behaviors

1. --project/-p flag accepts Path type and validates directory exists
2. --new flag accepts Path and validates parent directory is writable
3. --model/-m flag defaults to 'sonnet' and validates against allowed values (sonnet/opus)
4. --max-sessions flag defaults to 100 and accepts positive integers only
5. --continue/-c flag is boolean, mutually exclusive with --new
6. --status/-s flag is boolean, outputs status and exits without running
7. --mcp-preset flag validates against choices: rust, python, node, docs
8. --with-qa flag is boolean for enabling E2E QA feature generation
9. --debug/-d flag enables verbose debug output globally
10. Flags bound to environment variables (CONTEXT_ENGINE_MODEL, etc.)
11. Invalid flag combinations produce clear error messages
12. Flag help text matches Python argparse descriptions exactly

#### REQ_005.4: Implement feature list validation and topological sort for d

Implement feature list validation and topological sort for dependencies to ensure features are processed in correct dependency order

##### Testable Behaviors

1. Feature struct matches JSON schema with all fields (id, name, description, priority, etc.)
2. FeatureList struct contains Features slice and validation methods
3. LoadFeatureList function reads and parses features.json file
4. Validate method checks all required fields are present and valid
5. Validate method detects and reports circular dependencies
6. TopologicalSort method returns features ordered by dependencies
7. Features with no dependencies appear before dependent features
8. Blocked features are excluded from sorted output
9. Validation errors include line numbers and field names
10. Unit tests cover: valid lists, missing deps, circular deps, blocked features

#### REQ_005.5: Port complexity detection algorithm for feature assessment t

Port complexity detection algorithm for feature assessment to categorize features as simple, medium, or complex based on code analysis

##### Testable Behaviors

1. ComplexityLevel type defined as enum (simple, medium, complex)
2. DetectComplexity function analyzes feature and returns ComplexityLevel
3. Algorithm considers: file count, dependency count, description length, test requirements
4. Simple: 1-2 files, 0-1 dependencies, no tests specified
5. Medium: 3-5 files, 2-3 dependencies, basic tests
6. Complex: 6+ files, 4+ dependencies, comprehensive tests
7. Complexity affects session timeout and retry limits
8. Results cacheable to avoid recomputation
9. Algorithm matches Python implementation at loop-runner.py:348-405
10. Unit tests verify boundary conditions for each complexity level


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed