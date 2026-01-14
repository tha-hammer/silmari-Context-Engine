---
date: 2026-01-14 12:48:47 -05:00
researcher: maceo
git_commit: 10a8b690f0fa9849e7c689a33e8da766c1062470
branch: main
repository: silmari-Context-Engine
topic: "Project Structure - Main Directories"
tags: [research, codebase, project-structure, directories]
status: complete
last_updated: 2026-01-14
last_updated_by: maceo
---

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│          silmari-Context-Engine Project Structure         │
│                    Main Directories                        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Date**: 2026-01-14 12:48:47 -05:00
**Researcher**: maceo
**Git Commit**: `10a8b690f0fa9849e7c689a33e8da766c1062470`
**Branch**: main
**Repository**: silmari-Context-Engine
**Status**: ✅ Complete

---

## 📋 Research Question

**What is the project structure? List main directories only.**

---

## 📊 Summary

The **silmari-Context-Engine** project is a multi-language autonomous AI coding agent system with **13 main functional directories** at the root level, plus configuration files and hidden state directories. The architecture combines:

- 🐍 **Python** - Planning pipeline and agent orchestration (`planning_pipeline/`, `silmari_rlm_act/`)
- 🔷 **Go** - Runtime implementation of orchestration (`go/`)
- 🎯 **BAML** - Type-safe LLM prompt definitions (`baml_src/`, `baml_client/`)
- 🧠 **Context Management** - Efficient context window handling (`context_window_array/`)
- 📚 **Documentation** - Architecture docs and agent instructions (`docs/`, `thoughts/`)

The system implements a **four-layer memory architecture** for autonomous feature building with Claude Code, preventing context degradation across long sessions.

---

## 🗂️ Main Directories

### Core Implementation

| Directory | Purpose | Language | Key Features |
|-----------|---------|----------|--------------|
| **`agents/`** | Subagent prompt definitions | Markdown | code-reviewer, debugger, feature-verifier, test-runner |
| **`planning_pipeline/`** | Planning & decomposition pipeline | Python | autonomous_loop, decomposition, claude_runner, step execution |
| **`silmari_rlm_act/`** | Autonomous TDD Pipeline (RLM-ACT) | Python | Research, Learn, Model, Act phases with checkpoints |
| **`go/`** | Context engine runtime | Go | CLI tools, planning orchestration, concurrent execution |
| **`context_window_array/`** | Context window array management | Python | Batching, indexing, storage, working context |

### Schema & Type Safety

| Directory | Purpose | Language | Key Features |
|-----------|---------|----------|--------------|
| **`baml_src/`** | BAML source files | BAML | Type-safe LLM prompts, functions, schemas |
| **`baml_client/`** | Auto-generated code | Multi-lang | Generated Python/TypeScript/Go clients |

### Configuration & Commands

| Directory | Purpose | Language | Key Features |
|-----------|---------|----------|--------------|
| **`commands/`** | Command definitions | Markdown | status, debug, blockers, next, spec commands |

### Documentation & Knowledge

| Directory | Purpose | Language | Key Features |
|-----------|---------|----------|--------------|
| **`docs/`** | Project documentation | Markdown | ARCHITECTURE.md, NATIVE-HOOKS.md, screenshots |
| **`thoughts/`** | Research & planning docs | Markdown | Research documents, shared plans, symlinks to knowledge base |

### Output & Artifacts

| Directory | Purpose | Language | Key Features |
|-----------|---------|----------|--------------|
| **`output/`** | Generated output | Various | Analysis results, file groupings, technical stack |
| **`silmari-messenger-plans/`** | Integration planning | Markdown | Messenger integration plans |

### Testing

| Directory | Purpose | Language | Key Features |
|-----------|---------|----------|--------------|
| **`tests/`** | Top-level test suite | Python | autonomous_loop, execute_phase, orchestrator integration tests |

---

## 🏗️ Detailed Findings

### 🔹 **1. agents/**

**Purpose**: Defines specialized subagent prompts for Claude Code

**Key Files**:
- `code-reviewer.md` - Reviews code changes for issues
- `debugger.md` - Analyzes errors and suggests fixes
- `feature-verifier.md` - End-to-end feature verification
- `test-runner.md` - Runs tests and analyzes failures

**Integration**: These agents are invoked by Claude Code during different phases of the autonomous development cycle.

---

### 🔹 **2. baml_src/** & **3. baml_client/**

**Purpose**: Type-safe LLM prompt definitions using BAML (Basically, A Made-Up Language)

**baml_src/ Contents**:
- `functions.baml` - Main function definitions for LLM calls (78KB)
- `types.baml` - Type definitions for structured data
- `clients.baml` - Client configuration
- `generators.baml` - Code generation configuration
- `schema/` - Schema definitions

**baml_client/ Contents**:
- Auto-generated type-safe client code (Python/TypeScript/Go)
- Generated from baml_src definitions

**Integration**: Provides type-safe interfaces for all LLM interactions across the system.

---

### 🔹 **4. commands/**

**Purpose**: Command definitions for Claude Code interactive interface

**Contents**: Markdown files defining available commands (status, debug, blockers, next, spec)

**Integration**: Enables interactive control of the autonomous agent through slash commands.

---

### 🔹 **5. context_window_array/**

**Purpose**: Context window array management system for handling large context efficiently

**Key Files**:
- `batching.py` - Context batching logic
- `implementation_context.py` - Context for implementation phases
- `models.py` - Data models for context management
- `search_index.py` - Indexing for context retrieval
- `store.py` - Storage management
- `working_context.py` - Working context handling
- `tests/` - Test suite

**Integration**: Core component of the four-layer memory architecture, enabling efficient context management across long autonomous sessions.

---

### 🔹 **6. docs/**

**Purpose**: Project documentation

**Key Files**:
- `ARCHITECTURE.md` - Deep dive into system architecture
- `NATIVE-HOOKS.md` - Documentation for native hooks mode
- `session-screenshot.jpg` - Screenshot of autonomous session

**Integration**: Reference documentation for understanding the system's design and operation.

---

### 🔹 **7. go/**

**Purpose**: Go implementation of the context engine runtime

**Directory Structure**:
```
go/
├── cmd/                    # CLI tools
│   ├── context-engine/     # Main context engine CLI
│   └── loop-runner/        # Loop runner CLI
├── internal/               # Core Go packages (13 subdirectories)
│   ├── planning/           # Planning logic and orchestration
│   ├── cli/                # CLI argument parsing
│   ├── exec/               # Execution management
│   ├── models/             # Data models
│   ├── path/, paths/       # Path utilities
│   ├── fs/                 # File system operations
│   ├── concurrent/         # Concurrency primitives
│   ├── json/, jsonutil/    # JSON utilities
│   └── build/              # Build utilities
└── build/                  # Compiled binaries (darwin, linux, windows)
```

**Key Files**:
- `Makefile` - Build configuration
- `build-and-install.sh` - Build and installation script

**Integration**: Provides the runtime implementation of the orchestration layer, complementing the Python planning pipeline.

---

### 🔹 **8. output/**

**Purpose**: Generated output and analysis results

**Contents**:
- `silmari-Context-Engine/` subdirectory
- `groups/` - File groupings and technical stack analysis

**Integration**: Storage location for generated artifacts and analysis outputs.

---

### 🔹 **9. planning_pipeline/**

**Purpose**: Python implementation of the planning and decomposition pipeline

**Key Files** (Size Indicates Complexity):
- `autonomous_loop.py` (32KB) - Main autonomous loop implementation
- `decomposition.py` (35KB) - Feature decomposition logic
- `claude_runner.py` (35KB) - Claude Code execution management
- `helpers.py` - Utility functions
- `models.py` - Data models
- `pipeline.py` - Main pipeline orchestration
- `step_decomposition.py` - Step-level decomposition
- `steps.py` - Step execution logic
- `context_generation.py` - Context compilation
- `checkpoint_manager.py` - Checkpoint management
- `checkpoints.py` - Checkpoint operations
- `beads_controller.py` - BEADS sync integration
- `integrated_orchestrator.py` - Orchestrator integration
- `property_generator.py` - Property generation
- `visualization.py` - Visualization utilities
- `tests/` - Test suite

**Key Subdirectories**:
- `phase_execution/` - Phase execution logic
- `tests/` - Autonomous loop, execution, and orchestrator integration tests

**Integration**: Core orchestration layer that coordinates the autonomous development cycle.

---

### 🔹 **10. silmari_rlm_act/**

**Purpose**: Python package for Autonomous TDD Pipeline (Research, Learn, Model, Act)

**Directory Structure**:
```
silmari_rlm_act/
├── __init__.py
├── cli.py (12KB)          # Command-line interface
├── models.py (13KB)       # Data models
├── pipeline.py (27KB)     # Main pipeline orchestration
├── phases/                # Phase implementations
│   ├── decomposition.py
│   ├── implementation.py
│   ├── research.py
│   ├── beads_sync.py
│   ├── tdd_planning.py
│   └── multi_doc.py
├── agents/                # Agent implementations
├── commands/              # Command definitions
├── context/               # Context management
├── hooks/                 # Git/Claude hooks
├── checkpoints/           # Checkpoint system
├── validation/            # Input validation
└── tests/                 # Test suite
```

**Integration**: Implements the Research-Learn-Model-Act pattern for autonomous TDD with comprehensive phase management and checkpointing.

---

### 🔹 **11. tests/**

**Purpose**: Top-level test suite

**Key Files**:
- `test_autonomous_loop.py` (15KB) - Tests for autonomous loop
- `test_execute_phase.py` (14KB) - Tests for phase execution
- `test_loop_orchestrator_integration.py` (13KB) - Integration tests

**Integration**: Ensures correctness of the autonomous orchestration system.

---

### 🔹 **12. thoughts/**

**Purpose**: Research and planning documentation with symlinks to shared knowledge

**Directory Structure**:
- `searchable/` - Searchable documentation
  - `research/` - Research documents
  - `shared/` - Shared documentation and plans
  - `documentation/` - Additional documentation
- Symlinks to: `global`, `maceo` (personal), `shared` (shared knowledge base)

**Integration**: Central knowledge repository for research findings, planning documents, and architectural decisions.

---

### 🔹 **13. silmari-messenger-plans/**

**Purpose**: Planning documents for Silmari Messenger integration

**Integration**: Future integration planning with the Silmari Messenger system.

---

## 📦 Key Configuration Files (Root Level)

| File | Purpose |
|------|---------|
| `README.md` | Main project documentation (Context Engine overview) |
| `CLAUDE.md` | BAML reference guide and agent instructions |
| `pyproject.toml` | Poetry package configuration (Python) |
| `go.mod` | Go module dependencies |
| `Dockerfile` | Container configuration |
| `docker-compose.yml` | Multi-container orchestration |
| `CONTRIBUTING.md` | Contribution guidelines |
| `LICENSE` | License information |
| `AGENTS.md` | Agent documentation |
| `PROMPT.md` | Prompt reference |

---

## 🔐 Hidden/State Directories

These directories store agent state, memory, and development tool caches:

| Directory | Purpose |
|-----------|---------|
| `.agent/` | Agent state and memory (working context, memory, artifacts, hooks) |
| `.claude/` | Claude Code configuration and agents |
| `.git/` | Git repository |
| `.venv/` | Python virtual environment |
| `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` | Development tool caches |
| `.rlm-act-checkpoints/` | RLM-ACT checkpoint state |
| `.workflow-checkpoints/` | Workflow execution checkpoints |
| `.beads/`, `.specstory/`, `.hypothesis/` | Additional tool state |

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Four-Layer Memory Architecture            │
└─────────────────────────────────────────────────────────────┘

Layer 1: Working Context (context_window_array/)
         ↓
Layer 2: Planning Pipeline (planning_pipeline/)
         ↓
Layer 3: Agent Orchestration (silmari_rlm_act/)
         ↓
Layer 4: Runtime Execution (go/)
```

**Technology Stack**:
- **Python**: Planning, orchestration, context management
- **Go**: Runtime execution, CLI tools, concurrent processing
- **BAML**: Type-safe LLM interfaces
- **Markdown**: Agent definitions, documentation, research

---

## 📚 Code References

### Key Entry Points

- `planning_pipeline/autonomous_loop.py` - Main autonomous loop
- `silmari_rlm_act/cli.py` - RLM-ACT CLI interface
- `go/cmd/context-engine/` - Go context engine CLI
- `context_window_array/working_context.py` - Working context management

### Key Modules

- `planning_pipeline/decomposition.py` - Feature decomposition
- `planning_pipeline/claude_runner.py` - Claude execution
- `silmari_rlm_act/pipeline.py` - RLM-ACT pipeline
- `context_window_array/search_index.py` - Context indexing

---

## 📖 Historical Context (from thoughts/)

Multiple previous research documents exist documenting the project structure:

**Most Recent (2026-01-14)**:
- `thoughts/searchable/research/2026-01-14-project-structure.md` - 15 directories with detailed breakdown
- `thoughts/searchable/research/2026-01-14-project-structure-main-directories.md` - Main dirs with status
- `thoughts/searchable/research/2026-01-14-main-project-directories.md` - 24 directories including hidden

**Comprehensive Research (2026-01-14)**:
- `thoughts/shared/research/2026-01-14-project-structure.md` - Detailed component analysis
- `thoughts/shared/research/2026-01-06-main-directories-overview.md` - 15-directory overview

**Earlier Versions (2026-01-06)**:
- `thoughts/shared/research/2026-01-06-project-structure-main-directories.md` - Table format
- `thoughts/shared/research/2026-01-06-project-structure-directory-listing.md` - Categorized listing

**Architecture Deep Dives**:
- `thoughts/shared/research/2025-12-31-codebase-architecture.md` - Complete architecture analysis
- `thoughts/shared/research/2026-01-04-context-window-array-architecture.md` - LLM orchestration patterns

---

## 🔗 Related Research

- [2026-01-14 Project Structure](thoughts/searchable/research/2026-01-14-project-structure.md)
- [2026-01-14 Main Project Directories](thoughts/searchable/research/2026-01-14-main-project-directories.md)
- [2025-12-31 Codebase Architecture](thoughts/shared/research/2025-12-31-codebase-architecture.md)
- [2026-01-04 Context Window Array Architecture](thoughts/shared/research/2026-01-04-context-window-array-architecture.md)

---

## ❓ Open Questions

None - This research successfully documents all main directories in the project structure.

---

```
┌─────────────────────────────────────────────────────────────┐
│                    Research Complete ✅                      │
│                                                             │
│  13 main directories documented                             │
│  Multi-language architecture (Python, Go, BAML)             │
│  Four-layer memory system                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
