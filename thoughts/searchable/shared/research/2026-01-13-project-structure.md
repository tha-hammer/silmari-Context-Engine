---
date: 2026-01-13T18:59:15+0000
researcher: maceo
git_commit: 11e21d1808d1a31b4bcb31822803d2e7080aeda5
branch: main
repository: silmari-Context-Engine
topic: "What is the project structure? List main directories only."
tags: [research, codebase, project-structure, directories]
status: complete
last_updated: 2026-01-13
last_updated_by: maceo
---

```
╔════════════════════════════════════════════════════════════════╗
║                    CONTEXT ENGINE PROJECT                      ║
║              Autonomous Project Builder for Claude             ║
╚════════════════════════════════════════════════════════════════╝
```

# Research: Project Structure and Main Directories

**Date**: 2026-01-13T18:59:15+0000
**Researcher**: maceo
**Git Commit**: `11e21d1808d1a31b4bcb31822803d2e7080aeda5`
**Branch**: `main`
**Repository**: silmari-Context-Engine

---

## 📋 Research Question

What is the project structure? List main directories only.

---

## 🎯 Summary

The **Context Engine** is an autonomous AI coding agent that maintains coherent context across long-running development sessions through a **four-layer memory architecture**. The repository is organized into 16 main directories, divided between:

- **Core Implementation** (Go + Python)
- **Agent Infrastructure** (BAML + Agents)
- **Configuration & Memory** (Claude Code + Runtime)
- **Documentation & Planning** (Docs + Thoughts)

---

## 📊 Main Directory Structure

| Directory | Language/Type | Purpose | Status |
|-----------|---------------|---------|--------|
| `go/` | Go | Compiled binaries and runtime implementation | ✅ Active |
| `planning_pipeline/` | Python | Requirement decomposition and planning pipeline | ✅ Active |
| `silmari_rlm_act/` | Python | RLM-Act autonomous execution phases | ✅ Active |
| `context_window_array/` | Python | Working context management and storage | ✅ Active |
| `baml_src/` | BAML | Type-safe LLM function definitions | ✅ Active |
| `baml_client/` | Python (Generated) | Auto-generated BAML Python client | ✅ Active |
| `agents/` | Markdown | Subagent definitions for Claude Code | ✅ Active |
| `docs/` | Markdown | Architecture and system documentation | ✅ Active |
| `commands/` | Markdown | CLI command specifications | ✅ Active |
| `silmari-messenger-plans/` | Markdown | Sprint plans for related Silmari project | 📦 Archive |
| `.claude/` | JSON/Markdown | Claude Code IDE configuration | ✅ Active |
| `.agent/` | SQLite/JSON | Runtime memory and working context | 🔄 Runtime |
| `thoughts/` | Markdown | Research, planning, and thinking docs | ✅ Active |
| `.venv/` | Python | Virtual environment | 🔧 Build |
| `.git/` | Git | Version control | 🔧 Build |
| Root Config | Various | Configuration, scripts, and documentation | ✅ Active |

---

## 📚 Detailed Findings

### 1️⃣ **Core Go Implementation** - `go/`

The compiled runtime for the context engine, providing CLI binaries and execution utilities.

```
go/
├── cmd/                    # Command entry points
│   ├── context-engine/    # Main CLI binary
│   └── loop-runner/       # Autonomous loop runner binary
├── internal/              # Core Go packages (13 modules)
│   ├── cli/              # Command-line interface
│   ├── planning/         # Planning orchestration
│   ├── models/           # Data models
│   ├── exec/             # Execution utilities
│   └── ...
├── build/                # Compiled binaries (multi-platform)
├── Makefile             # Build configuration
└── go.mod               # Dependencies (Cobra CLI, Google UUID)
```

**Key Components:**
- Multi-platform builds (Darwin/Linux/Windows, ARM64/AMD64)
- Cobra CLI framework for command handling
- Planning orchestration and decomposition logic
- File system and path utilities

---

### 2️⃣ **Planning Pipeline** - `planning_pipeline/`

Python-based requirement decomposition and planning orchestration using Claude Agent SDK and BAML.

**Key Modules:**
- `decomposition.py` - Decomposes research into requirement hierarchies
- `autonomous_loop.py` - Orchestrates autonomous feature implementation
- `pipeline.py` - Main pipeline orchestration
- `step_decomposition.py` - Breaks requirements into executable steps
- `checkpoint_manager.py` - Manages execution state
- `beads_controller.py` - BEADS protocol integration
- `context_generation.py` - Generates context from sources
- `phase_execution/` - Phase execution submodules

---

### 3️⃣ **RLM-Act Implementation** - `silmari_rlm_act/`

Implements the **Recursive Loop Machine (RLM)** autonomous execution phases.

**Six Execution Phases:**
```
phases/
├── decomposition.py       # Task decomposition
├── tdd_planning.py       # TDD-based planning
├── implementation.py     # Feature implementation
├── research.py           # Research phase
├── multi_doc.py          # Multi-document handling
└── beads_sync.py         # BEADS synchronization
```

**Support Infrastructure:**
- `checkpoints/` - Checkpoint persistence
- `context/` - Context management
- `hooks/` - Hook implementations
- `agents/` - Subagent definitions
- `commands/` - CLI commands

---

### 4️⃣ **Context Window Array (CWA)** - `context_window_array/`

Array-based working context management system, providing the memory foundation.

**Core Modules (50K+ lines):**
- `models.py` (10K) - Context entry types and data models
- `store.py` (12.5K) - Context storage and retrieval
- `search_index.py` (9.4K) - Indexing and search functionality
- `working_context.py` (5.4K) - Working context compilation
- `implementation_context.py` (8.5K) - Implementation context building
- `batching.py` (8.6K) - Task batching for parallel execution

---

### 5️⃣ **BAML Function Library** - `baml_src/`

Type-safe LLM prompt definitions using BAML (90K+ total).

**Key Files:**
- `functions.baml` (78K) - Core LLM function library
- `types.baml` (12K) - Type definitions
- `clients.baml` - Client configurations
- `Gate1SharedClasses.baml` - Shared class definitions
- `schema/` - JSON schema definitions

---

### 6️⃣ **Generated BAML Client** - `baml_client/`

Auto-generated Python client for invoking BAML functions (470K+ lines).

**Generated Files:**
- `sync_client.py` (76K) - Synchronous client
- `async_client.py` (78K) - Asynchronous client
- `inlinedbaml.py` (128K) - Inline BAML execution
- `type_builder.py` (191K) - Type construction utilities

---

### 7️⃣ **Subagent Definitions** - `agents/`

Markdown specifications for Claude Code subagents invoked during implementation.

**Available Subagents:**
- `code-reviewer.md` - Code review automation
- `test-runner.md` - Test execution
- `feature-verifier.md` - Feature verification
- `debugger.md` - Debugging assistance

---

### 8️⃣ **Documentation** - `docs/`

System architecture and usage documentation.

**Key Files:**
- `ARCHITECTURE.md` - Four-layer memory model deep dive
- `NATIVE-HOOKS.md` - Interactive hooks mode documentation
- `session-screenshot.jpg` - Session execution visual

---

### 9️⃣ **CLI Commands** - `commands/`

Markdown specifications for custom CLI commands.

**Available Commands:**
- `spec.md` - Specification command
- `debug.md` - Debug utilities
- `next.md` - Next feature command
- `revert.md` - Revert functionality
- `status.md` - Status checking
- `blockers.md` - Blocker identification
- `verify.md` - Verification utilities

---

### 🔟 **Claude Code Configuration** - `.claude/`

IDE-specific configuration and extensions.

```
.claude/
├── agents/          # Subagent definitions
├── commands/        # Custom commands
├── hooks/           # Event hooks (SessionStart, PreCompact, etc.)
└── settings.json    # Claude Code settings
```

---

### 1️⃣1️⃣ **Agent Runtime Memory** - `.agent/`

Runtime memory storage for the Context Engine system.

```
.agent/
├── memory.db               # SQLite memory database
└── working-context/        # Compiled working context (rebuilt each session)
```

---

### 1️⃣2️⃣ **Thinking & Research** - `thoughts/`

Documentation hub for plans, research, and thinking.

```
thoughts/
├── searchable/              # Searchable documentation
│   ├── shared/             # Shared project resources
│   ├── plans/              # TDD plans (2026-01-10 to 2026-01-13)
│   └── research/           # Research documents
├── global/                  # Global thinking (symlinked)
└── maceo/                   # Personal user directory (symlinked)
```

---

### 1️⃣3️⃣ **Root-Level Entry Points**

**Main Python Scripts:**
- `orchestrator.py` - Context-engineered agent orchestrator
- `loop-runner.py` - Autonomous loop runner
- `resume_pipeline.py` - Resume interrupted execution
- `planning_orchestrator.py` - Planning phase orchestration
- `resume_planning.py` - Resume planning
- `mcp-setup.py` - MCP setup utility

---

### 1️⃣4️⃣ **Configuration Files**

**Documentation:**
- `README.md` (11.7K) - Main project documentation
- `CLAUDE.md` (28K) - Claude Code instructions
- `CONTRIBUTING.md` - Contribution guidelines
- `PROMPT.md` - Prompt templates

**Build & Deploy:**
- `Dockerfile` & `docker-compose.yml` - Containerization
- `install.sh` - Installation script
- `setup-native-hooks.sh` - Interactive hooks setup
- `setup-context-engineered.sh` - Context engine setup
- `.env` - Environment configuration

**Go Module:**
- `go.mod` & `go.sum` - Go dependencies

---

### 1️⃣5️⃣ **Build & Cache Directories**

Hidden/cache directories for development tools:
- `.git/` - Version control
- `.venv/` - Python virtual environment
- `.pytest_cache/` - Pytest cache
- `.mypy_cache/` - Type checking cache
- `.ruff_cache/` - Linter cache
- `.rlm-act-checkpoints/` - RLM-Act state
- `.workflow-checkpoints/` - Workflow state
- `.beads/` - BEADS protocol state
- `.specstory/` - Spec story tracking

---

## 🏗️ Architecture Overview

### Four-Layer Memory Architecture

```
┌─────────────────────────────────────────┐
│    Layer 1: Working Context             │
│    - Current session's active context   │
│    - Rebuilt fresh each session         │
└─────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│    Layer 2: Episodic Memory             │
│    - Recent decisions and patterns      │
│    - Rolling window                     │
└─────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│    Layer 3: Semantic Memory             │
│    - Project architecture conventions   │
│    - Persistent across sessions         │
└─────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│    Layer 4: Procedural Memory           │
│    - What worked/failed + solutions     │
│    - Append-only learning log           │
└─────────────────────────────────────────┘
```

### Operational Modes

| Mode | Type | Purpose | Context Persistence |
|------|------|---------|---------------------|
| **Native Hooks** | Interactive | Claude Code integration | Survives `/clear` |
| **Autonomous Loop** | Unattended | Feature implementation | Checkpoint-based |

---

## 🔗 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Runtime** | Go | Compiled binaries, CLI, planning engine |
| **Orchestration** | Python | Memory management, pipeline coordination |
| **LLM Prompts** | BAML | Type-safe LLM function definitions |
| **Memory** | SQLite + JSON | Persistent memory storage |
| **CLI Framework** | Cobra (Go) | Command-line interface |
| **Agent SDK** | Claude Agent SDK | Claude orchestration |

---

## 📂 Code References

### Key Implementation Files

- `go/cmd/context-engine/main.go` - Main CLI entry point
- `go/internal/planning/orchestration.go` - Planning orchestration
- `planning_pipeline/decomposition.py` - Requirement decomposition
- `planning_pipeline/autonomous_loop.py` - Autonomous execution loop
- `context_window_array/store.py` - Context storage (12.5K lines)
- `context_window_array/models.py` - Memory data models (10K lines)
- `baml_src/functions.baml` - LLM function library (78K lines)
- `silmari_rlm_act/phases/implementation.py` - Implementation phase
- `orchestrator.py` - Main Python orchestrator

### Configuration Files

- `.claude/settings.json` - Claude Code configuration
- `.env` - Environment variables and API keys
- `go.mod` - Go module dependencies
- `docker-compose.yml` - Docker orchestration

---

## 🎓 Project Purpose

The Context Engine is an **autonomous AI coding agent** designed to solve the "context window problem" in long-running development sessions. Traditional AI assistants lose context after a few exchanges or when sessions are cleared. Context Engine maintains coherent understanding through:

1. **Persistent Memory** - Four-layer architecture preserves decisions, patterns, and learnings
2. **Autonomous Execution** - Set-and-forget feature implementation with checkpointing
3. **Interactive Hooks** - Context survives Claude Code `/clear` commands
4. **Type-Safe Prompts** - BAML ensures reliable LLM interactions
5. **Checkpoint Recovery** - Resume from any point in execution

---

## 📊 Directory Count Summary

| Category | Count | Examples |
|----------|-------|----------|
| **Core Directories** | 6 | `go/`, `planning_pipeline/`, `silmari_rlm_act/`, `context_window_array/`, `baml_src/`, `baml_client/` |
| **Agent Infrastructure** | 3 | `agents/`, `commands/`, `.claude/` |
| **Documentation** | 3 | `docs/`, `thoughts/`, `silmari-messenger-plans/` |
| **Runtime/Build** | 4 | `.agent/`, `.venv/`, `.git/`, cache directories |
| **Total Main Directories** | 16 | Excluding cache/build artifacts |

---

## 🔍 Related Research

- See `thoughts/searchable/research/` for additional codebase research
- See `thoughts/searchable/plans/` for TDD plans and feature breakdowns
- See `docs/ARCHITECTURE.md` for detailed memory architecture

---

## ✅ Research Complete

This documentation provides a comprehensive overview of the Context Engine project structure as it exists today. All directories have been identified and their purposes documented based on actual codebase inspection.

**Key Takeaway**: The project is organized into distinct layers for runtime (Go), orchestration (Python), memory management (CWA), and type-safe LLM interactions (BAML), all coordinated through Claude Code's agent infrastructure.
