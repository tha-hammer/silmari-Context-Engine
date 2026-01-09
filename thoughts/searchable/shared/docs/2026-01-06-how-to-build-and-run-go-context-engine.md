---
date: 2026-01-06T07:44:57-05:00
researcher: Claude Sonnet 4.5
git_commit: be955131b4e296a977fac7970dacd0f7f912cbb8
branch: main
repository: silmari-Context-Engine
topic: "How to Build and Run the Go Version of the Context Engine"
tags: [documentation, go, build, deployment, context-engine, loop-runner]
status: complete
last_updated: 2026-01-06
last_updated_by: Claude Sonnet 4.5
---

# How to Build and Run the Go Version of the Context Engine

## Introduction

This guide provides step-by-step instructions for building and running the Go implementation of the Context Engine's orchestrator and loop runner. The Go codebase provides two main binaries: `context-engine` (the main orchestrator CLI) and `loop-runner` (the autonomous loop executor). By following this guide, you will build these binaries for your platform and execute them to manage context-engineered autonomous projects.

## Prerequisites

Before you begin, ensure you have:

- **Go 1.25.1 or later** installed and available in your PATH
- **Make** installed (standard on Linux/macOS, available via MinGW/WSL on Windows)
- **Git** installed for version operations
- **Claude Code CLI** installed and authenticated (the Go binaries invoke this)
- **Write access** to the project directory at `/home/maceo/Dev/silmari-Context-Engine/go`
- For user installation: `~/.local/bin` in your PATH (add with `export PATH="$HOME/.local/bin:$PATH"`)
- For system installation: `sudo` privileges

## Steps

### 1. Navigate to the Go Source Directory

Change to the Go source directory:

```bash
cd /home/maceo/Dev/silmari-Context-Engine/go
```

### 2. Build Binaries for Your Current Platform

Execute the default build target:

```bash
make build
```

This produces statically-linked binaries in the `build/` directory:
- `build/context-engine`
- `build/loop-runner`

**Build output:** The binaries are compiled with `CGO_ENABLED=0`, making them fully static with no external dependencies. On Linux x86-64, each binary is approximately 4MB.

### 3. Verify the Build

Confirm the binaries were created:

```bash
ls -lh build/
```

Check the version information:

```bash
./build/context-engine --version
./build/loop-runner --version
```

You should see output showing the Git commit hash, version, and build timestamp.

### 4. Install Binaries (Choose One Installation Method)

#### Option A: User Installation (Recommended, No Sudo Required)

Install to `~/.local/bin`:

```bash
make install-user
```

The binaries are now available as `context-engine` and `loop-runner` from any directory (assuming `~/.local/bin` is in your PATH).

#### Option B: System-Wide Installation

Install to `/usr/local/bin`:

```bash
sudo make install
```

To install to a custom prefix (e.g., `/opt/local`):

```bash
sudo make install PREFIX=/opt/local
```

### 5. Run the Context Engine Orchestrator

#### Run the Planning Pipeline

Execute the planning pipeline on an existing project:

```bash
context-engine plan --project ~/myapp
```

To specify a model:

```bash
context-engine plan --project ~/myapp --model opus
```

To resume from a checkpoint:

```bash
context-engine plan --project ~/myapp --resume
```

#### Create a New Project

Initialize a new project:

```bash
context-engine --new ~/projects/myapp --model sonnet
```

#### Configure MCP Servers

Set up MCP server configurations using presets:

```bash
context-engine mcp-setup --preset fullstack
```

Available presets: `web`, `fullstack`, `data`, `devops`, `minimal`, `rust`, `python`, `node`, `docs`

### 6. Run the Loop Runner (Autonomous Mode)

#### Run in the Current Directory

Execute the autonomous loop:

```bash
loop-runner
```

#### Run in a Specific Project

Specify a project directory:

```bash
loop-runner ~/projects/myapp --model opus
```

#### Enable Parallel Execution

Run with parallel feature execution (3 workers):

```bash
loop-runner ~/projects/myapp --parallel 3
```

#### Validate Feature List

Check the `feature_list.json` for errors before running:

```bash
loop-runner ~/projects/myapp --validate
```

#### View Metrics

Display progress and metrics:

```bash
loop-runner ~/projects/myapp --metrics
```

### 7. Cross-Compile for Other Platforms (Optional)

To build binaries for all supported platforms:

```bash
make build-all
```

This creates binaries in `build/` for:
- macOS Intel (darwin-amd64)
- macOS Apple Silicon (darwin-arm64)
- Linux x86-64 (linux-amd64)
- Linux ARM64 (linux-arm64)
- Windows x86-64 (windows-amd64)

Individual platform targets are also available:
```bash
make build-darwin-arm64
make build-linux-amd64
make build-windows-amd64
```

### 8. Run Tests (Optional)

Execute the test suite:

```bash
make test
```

For test coverage report:

```bash
make test-coverage
```

## Common Use Cases

### Building and Running the Planning Pipeline

```bash
cd /home/maceo/Dev/silmari-Context-Engine/go
make build
./build/context-engine plan --project ~/myapp --ticket PROJ-123
```

### Building Release Binaries for Distribution

```bash
cd /home/maceo/Dev/silmari-Context-Engine/go
make clean
make build-all
ls -lh build/
```

### Daily Development Workflow

```bash
# Install for regular use
make install-user

# Run from anywhere
context-engine plan --project ~/current-project
loop-runner ~/current-project --parallel 2
```

## Troubleshooting Guide

### Binary Not Found After Installation

Ensure the installation directory is in your PATH:

```bash
# For user installation
echo $PATH | grep ".local/bin"
# If not present, add to ~/.bashrc or ~/.zshrc:
export PATH="$HOME/.local/bin:$PATH"
```

### Build Fails with Missing Dependencies

Update Go modules:

```bash
cd /home/maceo/Dev/silmari-Context-Engine/go
go mod download
go mod tidy
```

### Claude Code CLI Not Found

The Go binaries invoke the Claude Code CLI. Verify it's installed:

```bash
claude --version
```

If not installed, install Claude Code CLI before running the Go binaries.

## Next Steps

For detailed command reference (all flags, subcommands, and options), use the built-in help:

```bash
context-engine --help
context-engine plan --help
loop-runner --help
```

For configuration options and advanced features, consult the Configuration Reference document (if available).

For understanding the internal architecture and design decisions, see the Architecture Explanation documents in `thoughts/searchable/shared/research/`.

For development and contribution guidelines, see the Development Guide (if available).
