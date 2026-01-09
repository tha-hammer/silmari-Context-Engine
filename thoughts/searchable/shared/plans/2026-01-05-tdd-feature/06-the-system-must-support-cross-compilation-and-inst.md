# Phase 06: The system must support cross-compilation and inst...

## Requirements

### REQ_005: The system must support cross-compilation and installation t

The system must support cross-compilation and installation to /usr/local/bin via Makefile and install scripts

#### REQ_005.1: Create a comprehensive Makefile with build, install, uninsta

Create a comprehensive Makefile with build, install, uninstall, and release targets that supports version injection, configurable PREFIX paths, and phony targets for reproducible builds

##### Testable Behaviors

1. Makefile defines BINARY_NAME=context-engine and LOOP_BINARY=loop-runner variables
2. Makefile defines PREFIX variable defaulting to /usr/local with override support via PREFIX=/custom/path
3. Makefile defines BINDIR=$(PREFIX)/bin for installation directory
4. VERSION variable extracts version from git describe --tags --always --dirty
5. LDFLAGS variable injects version via -ldflags "-X main.version=$(VERSION)"
6. build target compiles both binaries to bin/ directory with version injection
7. install target depends on build and uses install -d and install -m 755 commands
8. uninstall target removes both binaries from $(BINDIR)
9. release target builds all 5 platform variants with appropriate naming conventions
10. clean target removes bin/ directory and any build artifacts
11. All targets are declared as .PHONY to prevent conflicts with same-named files
12. test target runs go test ./... with coverage reporting
13. lint target runs golangci-lint or go vet
14. Makefile includes help target documenting all available targets

#### REQ_005.2: Build the context-engine binary from cmd/orchestrator/main.g

Build the context-engine binary from cmd/orchestrator/main.go with proper entry point, version information, and cobra CLI initialization

##### Testable Behaviors

1. cmd/orchestrator/main.go exists as the entry point for context-engine binary
2. main.go imports internal packages for app logic, CLI commands, and models
3. main.go defines var version string for ldflags injection
4. main.go calls cobra rootCmd.Execute() or equivalent CLI initialization
5. Binary compiles without errors using go build ./cmd/orchestrator
6. Binary runs with --help flag displaying usage information
7. Binary runs with --version flag displaying injected version string
8. Binary size is reasonable for a Go binary (typically 10-20MB without compression)
9. Binary has no external runtime dependencies (statically linked)
10. go.mod declares module path matching project structure (e.g., github.com/zeddy89/silmari-Context-Engine)
11. go.mod specifies Go version 1.21 or higher
12. go.sum contains locked dependency versions

#### REQ_005.3: Build the loop-runner binary from cmd/loop-runner/main.go wi

Build the loop-runner binary from cmd/loop-runner/main.go with autonomous loop execution capabilities and feature list management

##### Testable Behaviors

1. cmd/loop-runner/main.go exists as the entry point for loop-runner binary
2. main.go imports internal packages for loop runner logic and models
3. main.go defines var version string for ldflags injection
4. main.go initializes cobra CLI with loop runner specific commands
5. Binary compiles without errors using go build ./cmd/loop-runner
6. Binary runs with --help flag displaying loop runner usage
7. Binary accepts --features-file flag for feature list JSON path
8. Binary accepts --project flag for target project path
9. Binary accepts --max-iterations flag for loop limit
10. Binary validates feature list JSON structure on startup
11. Binary implements topological sort for feature dependencies
12. Binary supports --dry-run mode for testing without execution

#### REQ_005.4: Install compiled binaries to /usr/local/bin with 755 permiss

Install compiled binaries to /usr/local/bin with 755 permissions using install command, supporting both system-wide and user-local installation paths

##### Testable Behaviors

1. install target creates $(BINDIR) directory if it doesn't exist using install -d
2. install target copies context-engine binary with install -m 755
3. install target copies loop-runner binary with install -m 755
4. Installed binaries have owner read/write/execute and group/other read/execute permissions (755)
5. Installation to /usr/local/bin works with sudo when PREFIX=/usr/local
6. Installation to ~/.local/bin works without sudo when PREFIX=~/.local
7. Install script (install.sh) provides interactive installation with prompts
8. Install script detects if running as root and warns about permission implications
9. Install script verifies $(BINDIR) is in user's PATH and provides guidance if not
10. Install script supports --prefix flag for custom installation directory
11. Install script supports --dry-run flag to preview actions without executing
12. Post-installation message displays installed binary paths
13. Uninstall target cleanly removes binaries without affecting other files

#### REQ_005.5: Support cross-compilation for darwin-amd64, darwin-arm64, li

Support cross-compilation for darwin-amd64, darwin-arm64, linux-amd64, linux-arm64, and windows-amd64 using Go's built-in GOOS/GOARCH environment variables

##### Testable Behaviors

1. release target builds context-engine for all 5 target platforms
2. release target builds loop-runner for all 5 target platforms
3. Darwin AMD64 binaries named: context-engine-darwin-amd64, loop-runner-darwin-amd64
4. Darwin ARM64 binaries named: context-engine-darwin-arm64, loop-runner-darwin-arm64
5. Linux AMD64 binaries named: context-engine-linux-amd64, loop-runner-linux-amd64
6. Linux ARM64 binaries named: context-engine-linux-arm64, loop-runner-linux-arm64
7. Windows AMD64 binaries named: context-engine-windows-amd64.exe, loop-runner-windows-amd64.exe
8. All binaries are statically linked with CGO_ENABLED=0
9. All binaries include version information via ldflags
10. Release binaries are placed in bin/ or dist/ directory
11. Release target generates SHA256 checksums for all binaries
12. Makefile includes individual platform targets (build-darwin-amd64, etc.) for selective builds
13. Cross-compiled binaries are tested for correct architecture using file command or equivalent
14. Release process can be triggered from any host OS (e.g., build Linux binary from macOS)


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed