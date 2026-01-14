---
date: 2026-01-14T16:25:23-05:00
researcher: tha-hammer
git_commit: 42056f3644677080e2ee3fcde22c311753ada1e2
branch: main
repository: silmari-Context-Engine
topic: "Project Structure - Main Directories"
tags: [research, codebase, project-structure, directories, architecture]
status: complete
last_updated: 2026-01-14
last_updated_by: tha-hammer
---

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              SILMARI CONTEXT ENGINE                          ║
║              Project Structure Research                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Status: ✅ Complete        Date: 2026-01-14T16:25:23-05:00
```

# Research: Project Structure - Main Directories

**Date**: 2026-01-14T16:25:23-05:00
**Researcher**: tha-hammer
**Git Commit**: `42056f3644677080e2ee3fcde22c311753ada1e2`
**Branch**: `main`
**Repository**: silmari-Context-Engine

## 📋 Research Question
What is the project structure? List main directories only.

## 🎯 Summary

The **silmari-Context-Engine** is a **polyglot Python+Go** autonomous AI orchestration system with **30 top-level directories** organized into functional categories. The main directories include core application code, configuration, build artifacts, workflow management, and documentation.

### 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────┐
│  Core Implementation (Python + Go + BAML)        │
├──────────────────────────────────────────────────┤
│  • silmari_rlm_act (Python framework)            │
│  • planning_pipeline (Autonomous orchestration)  │
│  • go (CLI tools & core utilities)               │
│  • baml_src & baml_client (AI functions)         │
│  • context_window_array (Memory management)      │
└──────────────────────────────────────────────────┘
```

---

## 📊 Main Directories

### 🔵 Core Application Code

| Directory | Purpose | Technology | Key Contents |
|-----------|---------|------------|--------------|
| **`silmari_rlm_act/`** | Main Python framework (RLM-Act = Reinforcement Loop Model - Act) | Python | `cli.py`, `pipeline.py`, `models.py`, `/phases`, `/agents`, `/commands` |
| **`planning_pipeline/`** | Autonomous loop orchestration | Python | `autonomous_loop.py`, `decomposition.py`, `claude_runner.py`, checkpoint management |
| **`go/`** | Go CLI tools & utilities | Go | `/cmd` (entry points), `/internal` (packages), `/build` (binaries) |
| **`baml_src/`** | BAML function definitions | BAML | `functions.baml` (78KB), `types.baml`, `clients.baml`, `generators.baml` |
| **`baml_client/`** | Generated BAML client | Python | Auto-generated sync/async clients, type builders |
| **`context_window_array/`** | Context window management | Python | `store.py`, `implementation_context.py`, `working_context.py`, `search_index.py` |

### 🟢 Supporting Code

| Directory | Purpose | Contents |
|-----------|---------|----------|
| **`agents/`** | AI agent role definitions | Markdown files: `code-reviewer.md`, `debugger.md`, `feature-verifier.md`, `test-runner.md` |
| **`commands/`** | CLI command definitions | Markdown files: `status.md`, `blockers.md`, `next.md`, `debug.md`, `verify.md`, `revert.md`, `spec.md` |
| **`tests/`** | Test suite | `test_autonomous_loop.py`, `test_execute_phase.py`, integration tests |
| **`docs/`** | Project documentation | `ARCHITECTURE.md`, `NATIVE-HOOKS.md`, screenshots |

### 🟡 Configuration & State

| Directory | Purpose | Type |
|-----------|---------|------|
| **`.agent/`** | Agent framework state | Contains `memory.db` |
| **`.beads/`** | BEADS framework integration | Build Execution Artifact Definition System |
| **`.claude/`** | Claude editor config | IDE configuration |
| **`.cursor/`** | Cursor editor config | IDE configuration |
| **`.silmari/`** | Application-specific config | Framework settings |
| **`.specstory/`** | Specification tracking | Spec and story history |

### 🟠 Workflow & Checkpoints

| Directory | Purpose | Contents |
|-----------|---------|----------|
| **`.rlm-act-checkpoints/`** | RLM-Act checkpoints | JSON checkpoint files for pipeline resumption |
| **`.workflow-checkpoints/`** | Workflow snapshots | JSON files for interrupted workflow recovery |

### 🔴 Build & Output

| Directory | Purpose | Contents |
|-----------|---------|----------|
| **`output/`** | Generated analysis | Analysis results, file groupings |
| **`dist/`** | Distribution packages | Python package distribution files |
| **`.venv/`** | Python virtual environment | Isolated dependencies |
| **`.pytest_cache/`** | Pytest cache | Test caching |
| **`.mypy_cache/`** | MyPy cache | Type checking cache |
| **`.ruff_cache/`** | Ruff cache | Linter cache |

### 🟣 Documentation & Planning

| Directory | Purpose | Organization |
|-----------|---------|--------------|
| **`thoughts/`** | Research & planning | `/searchable/research/`, `/searchable/shared/plans/` |
| **`silmari-messenger-plans/`** | Related project plans | Messenger/chat feature planning |

---

## 🔍 Detailed Findings

### Core Implementation Architecture

<details>
<summary><strong>📦 silmari_rlm_act/</strong> - Main Python Framework</summary>

**Purpose**: The core RLM-Act (Reinforcement Loop Model - Act) framework implementation

**Key Components**:
- **`cli.py`** - Command-line interface definition
- **`pipeline.py`** - Main orchestration pipeline
- **`models.py`** - Data models and schemas
- **`/phases`** - Phase implementations (decomposition, implementation, etc.)
- **`/agents`** - Agent definitions
- **`/commands`** - Command handlers
- **`/checkpoints`** - Checkpoint management for resumability
- **`/context`** - Context management utilities
- **`/validation`** - Input/output validation

**Technology**: Python
</details>

<details>
<summary><strong>🔄 planning_pipeline/</strong> - Autonomous Loop Orchestration</summary>

**Purpose**: Autonomous execution loop and planning orchestration

**Key Components**:
- **`autonomous_loop.py`** - Autonomous execution loop implementation
- **`decomposition.py`** - Requirement and task decomposition logic
- **`claude_runner.py`** - Claude API integration runner (35KB)
- **`pipeline.py`** - Pipeline orchestration
- **`steps.py`** - Step definitions and execution
- **`phase_execution/`** - Phase-specific execution logic
- **`checkpoint_manager.py`** - Checkpoint persistence and recovery
- **`beads_controller.py`** - BEADS framework integration

**Technology**: Python
</details>

<details>
<summary><strong>⚙️ go/</strong> - Go Language Implementation</summary>

**Purpose**: Go-based CLI tools and core utilities

**Structure**:
- **`/cmd`** - Command-line tool entry points
  - `context-engine` - Main context engine CLI
  - `loop-runner` - Loop runner utility
- **`/internal`** - Core Go packages:
  - `/planning` - Planning and decomposition logic
  - `/cli` - CLI argument handling
  - `/models` - Data structures
  - `/exec` - Execution utilities
  - `/concurrent` - Concurrency primitives
  - `/fs`, `/path`, `/paths` - File system and path utilities
  - `/json`, `/jsonutil` - JSON handling
- **`/build`** - Compiled binaries for different platforms (Linux, macOS, Windows)

**Technology**: Go
</details>

<details>
<summary><strong>🤖 baml_src/</strong> - BAML Function Definitions</summary>

**Purpose**: BAML (Branching Agent Modeling Language) function definitions for AI orchestration

**Key Files**:
- **`functions.baml`** - 78KB main function definitions
- **`types.baml`** - Type definitions
- **`clients.baml`** - Client configurations
- **`generators.baml`** - Code generation templates

**Technology**: BAML (DSL for structured AI functions)
</details>

<details>
<summary><strong>📝 baml_client/</strong> - Generated BAML Client</summary>

**Purpose**: Auto-generated Python client code for BAML functions

**Key Files**:
- **`sync_client.py`** - Synchronous client implementation
- **`async_client.py`** - Asynchronous client implementation
- **`type_builder.py`** - Dynamic type construction
- **`inlinedbaml.py`** - 191KB inlined BAML definitions

**Technology**: Python (generated)
</details>

<details>
<summary><strong>🧠 context_window_array/</strong> - Context Management</summary>

**Purpose**: Context window management for LLM interactions

**Key Files**:
- **`store.py`** - Context storage and retrieval
- **`implementation_context.py`** - Implementation-specific context
- **`working_context.py`** - Active working context
- **`search_index.py`** - Context search indexing
- **`batching.py`** - Context batching utilities

**Technology**: Python
</details>

---

## 🏛️ Architecture Patterns

### Technology Stack

```
┌─────────────────────────────────────────────────┐
│  Languages                                      │
├─────────────────────────────────────────────────┤
│  • Python (Framework, Pipeline, Context)       │
│  • Go (CLI Tools, Core Utilities)              │
│  • BAML (AI Function Definitions)              │
└─────────────────────────────────────────────────┘
```

### Key Design Patterns Documented

1. **🔄 Checkpoint-Based Resumability**
   - `.rlm-act-checkpoints/` - Pipeline checkpoints
   - `.workflow-checkpoints/` - Workflow state snapshots
   - Enables recovery from interruptions

2. **🎯 Phase-Based Pipeline**
   - Research → Learn → Model → Act → Verify → Deploy
   - Implemented in `silmari_rlm_act/phases/`

3. **🧩 Multi-Layer Memory Architecture**
   - Working Memory
   - Episodic Memory
   - Semantic Memory
   - Procedural Memory
   - Managed by `context_window_array/`

4. **🤝 Polyglot Implementation**
   - Python for high-level orchestration and AI integration
   - Go for performance-critical CLI tools and utilities
   - BAML for structured AI function definitions

5. **🔌 Framework Integration**
   - `.beads/` - Build Execution Artifact Definition System
   - `.agent/` - Agent framework state
   - `.specstory/` - Specification tracking

---

## 📂 Directory Tree Overview

```
silmari-Context-Engine/
├── 🔵 Core Application
│   ├── silmari_rlm_act/          # Main Python framework
│   ├── planning_pipeline/         # Autonomous orchestration
│   ├── go/                        # Go CLI tools
│   ├── baml_src/                  # BAML definitions
│   ├── baml_client/               # Generated BAML client
│   └── context_window_array/      # Context management
│
├── 🟢 Supporting Code
│   ├── agents/                    # Agent role definitions
│   ├── commands/                  # CLI commands
│   ├── tests/                     # Test suite
│   └── docs/                      # Documentation
│
├── 🟡 Configuration
│   ├── .agent/                    # Agent state
│   ├── .beads/                    # BEADS framework
│   ├── .claude/                   # Claude config
│   ├── .cursor/                   # Cursor config
│   ├── .silmari/                  # App config
│   └── .specstory/                # Spec tracking
│
├── 🟠 Checkpoints
│   ├── .rlm-act-checkpoints/      # Pipeline checkpoints
│   └── .workflow-checkpoints/     # Workflow snapshots
│
├── 🔴 Build & Output
│   ├── output/                    # Generated analysis
│   ├── dist/                      # Distribution packages
│   ├── .venv/                     # Virtual environment
│   └── [caches]/                  # .pytest_cache, .mypy_cache, .ruff_cache
│
└── 🟣 Documentation
    ├── thoughts/                  # Research & planning
    └── silmari-messenger-plans/   # Related plans
```

---

## 🔗 Code References

### Configuration Files (Root Level)
- `pyproject.toml` - Python project configuration
- `poetry.lock` - Python dependency lock file
- `go.mod` / `go.sum` - Go dependency management
- `.python-version` - Python version specification
- `.gitignore` - Git ignore patterns

### Entry Points
- `go/cmd/context-engine/` - Main Go CLI entry point
- `silmari_rlm_act/cli.py` - Python CLI entry point
- `planning_pipeline/autonomous_loop.py` - Autonomous loop entry

---

## 📚 Historical Context (from thoughts/)

### Existing Documentation Found

**Recent Project Structure Documentation**:

1. **`thoughts/searchable/research/2026-01-14-project-structure-comprehensive.md`**
   - Date: 2026-01-14 13:52:30 UTC
   - Comprehensive overview with 11 main functional directories
   - Detailed breakdown and architecture patterns

2. **`thoughts/searchable/research/2026-01-14-project-structure.md`**
   - Date: 2026-01-14 14:40:25 UTC
   - Lists 30 top-level directories in 6 categories
   - Includes directory tree visualization

3. **`thoughts/shared/research/2026-01-14-project-structure.md`**
   - Date: 2026-01-14 10:36:37 UTC
   - Focus on 15 main functional directories
   - Technical breakdown with code references

4. **`thoughts/shared/research/2026-01-06-project-structure.md`**
   - Date: 2026-01-06
   - Earlier version of structure documentation

**Note**: This research document provides a concise summary focusing specifically on main directories, while the comprehensive documents above provide deeper architectural analysis.

---

## 🔗 Related Research

- [2026-01-14 Project Structure Comprehensive](2026-01-14-project-structure-comprehensive.md)
- [2026-01-14 Project Structure Full](2026-01-14-project-structure.md)
- `docs/ARCHITECTURE.md` - System architecture documentation

---

## ✨ Key Insights

### 📌 Primary Finding
**30 top-level directories** organized into **6 functional categories**:
1. **Core Application** (6 dirs) - Python/Go/BAML implementation
2. **Supporting Code** (4 dirs) - Agents, commands, tests, docs
3. **Configuration** (6 dirs) - Framework and IDE settings
4. **Checkpoints** (2 dirs) - RLM-Act and workflow state
5. **Build & Output** (6 dirs) - Artifacts and caches
6. **Documentation** (2 dirs) - Research and planning

### 🎯 Architecture Highlights
- **Polyglot design**: Python for orchestration, Go for performance
- **Checkpoint-based**: Full resumability across interruptions
- **Memory-layered**: 4-layer context architecture
- **Framework-integrated**: BEADS, agent framework, spec tracking
- **BAML-powered**: Structured AI function definitions

---

## 📝 Notes

This research document focuses on **main directories only** as requested. For comprehensive details including subdirectory structures, file-level analysis, and deeper architectural patterns, see the related research documents listed above.

The project demonstrates a sophisticated autonomous AI orchestration system with strong emphasis on:
- **Resumability** (checkpoint systems)
- **Memory management** (context window arrays)
- **Multi-phase execution** (RLM-Act pipeline)
- **Developer tooling** (CLI, agents, commands)
- **Documentation** (thoughts/, docs/, architecture)
