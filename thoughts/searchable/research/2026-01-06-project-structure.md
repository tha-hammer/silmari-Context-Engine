---
date: 2026-01-06 06:57:01 -05:00
researcher: Maceo Chavez
git_commit: 3073da6330a379cb46a5fd26c154cbc96dede756
branch: main
repository: silmari-Context-Engine
topic: "Project Structure - Main Directories"
tags: [research, codebase, project-structure, architecture]
status: complete
last_updated: 2026-01-06
last_updated_by: Maceo Chavez
last_updated_note: "Updated with enhanced formatting and current git commit"
---

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         SILMARI CONTEXT ENGINE - PROJECT STRUCTURE        ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

# Research: Project Structure - Main Directories

**Date**: 2026-01-06 06:57:01 -05:00
**Researcher**: Maceo Chavez
**Git Commit**: 3073da6330a379cb46a5fd26c154cbc96dede756
**Branch**: main
**Repository**: silmari-Context-Engine

## 📋 Research Question

What is the project structure? List main directories only.

## 🎯 Summary

The silmari-Context-Engine is a sophisticated project combining **Python orchestration** and **Go implementation** for a context window engine with advanced planning and decomposition capabilities. The project follows a modular architecture with clear separation between:

- **Application code** (Python modules for context management, planning, and RLM phases)
- **Performance-critical components** (Go implementations for speed)
- **Configuration and code generation** (BAML for LLM integration)
- **Documentation and planning** (comprehensive docs and sprint plans)
- **Development tooling** (testing, Docker, IDE configurations)

The structure represents a hybrid Python/Go system with emphasis on planning orchestration, context window management, and autonomous loop execution.

---

## 📊 Detailed Findings

### 🏗️ Core Application Directories

| Directory | Type | Purpose | Key Components |
|-----------|------|---------|----------------|
| `context_window_array/` | Python Module | Context window management system | `store.py`, `search_index.py`, `working_context.py`, `batching.py`, `models.py` |
| `planning_pipeline/` | Python Module | Planning orchestration and decomposition | `decomposition.py`, `steps.py`, `claude_runner.py`, `pipeline.py`, `autonomous_loop.py` |
| `silmari_rlm_act/` | Python Package | RLM Act phase implementations | `cli.py`, `pipeline.py`, phases/, commands/, agents/, tests/ |
| `go/` | Go Project | Go language implementation/port | `cmd/`, `internal/`, `build/`, `Makefile` |

<details>
<summary>📁 Context Window Array Details</summary>

**Location**: `context_window_array/`

**Purpose**: Manages context windows for the system, providing storage, searching, and batching capabilities.

**Key Files**:
- `store.py` - Context storage management
- `search_index.py` - Search indexing functionality
- `working_context.py` - Working context handling
- `batching.py` - Batch processing of context data
- `models.py` - Data models and types
- `tests/` - Unit tests for the module

</details>

<details>
<summary>📁 Planning Pipeline Details</summary>

**Location**: `planning_pipeline/`

**Purpose**: Core orchestration system for planning, task decomposition, and autonomous execution.

**Key Files**:
- `decomposition.py` - Task decomposition logic
- `steps.py` - Step execution framework
- `claude_runner.py` - Claude API integration
- `pipeline.py` - Pipeline orchestration
- `autonomous_loop.py` - Autonomous loop execution
- `phase_execution/` - Phase execution utilities
  - `claude_invoker.py` - Claude invocation utilities
  - `plan_discovery.py` - Plan discovery logic
- `tests/` - Comprehensive test suite

</details>

<details>
<summary>📁 Silmari RLM Act Details</summary>

**Location**: `silmari_rlm_act/`

**Purpose**: Implements the RLM (Reasoning Loop Manager) Act phase with various execution modes.

**Structure**:
- **CLI**: `cli.py` - Command-line interface
- **Core**: `pipeline.py`, `models.py` - Pipeline and data models
- **Phases**: `phases/` subdirectory
  - `decomposition.py` - Task decomposition phase
  - `implementation.py` - Implementation phase
  - `research.py` - Research phase
  - `tdd_planning.py` - TDD planning phase
  - `multi_doc.py` - Multi-document processing
  - `beads_sync.py` - Beads synchronization
- **Commands**: `commands/` - Markdown-based command specifications
- **Support**: `context/`, `hooks/`, `checkpoints/`, `agents/`
- **Tests**: `tests/` - Comprehensive test suite

</details>

<details>
<summary>📁 Go Implementation Details</summary>

**Location**: `go/`

**Purpose**: Performance-critical components written in Go for speed and efficiency.

**Structure**:
- **Commands**: `cmd/` subdirectory
  - `context-engine/` - Context engine executable
  - `loop-runner/` - Loop runner executable
- **Internal Packages**: `internal/` subdirectory
  - `cli/` - CLI utilities
  - `planning/` - Planning logic
  - `models/` - Data models
  - `paths/`, `path/` - Path handling
  - `json/`, `jsonutil/` - JSON utilities
  - `fs/` - File system operations
  - `concurrent/` - Concurrency utilities
  - `exec/` - Execution utilities
  - `build/` - Build utilities
- **Build**: `build/` - Build artifacts
- **Build System**: `Makefile` - Build automation

</details>

---

### 🔧 planning_pipeline/
**Primary Purpose**: Core orchestration system for decomposing and executing planning phases

**Contains**:
- 17 Python modules
- Autonomous loops
- Checkpoint management
- Context generation
- Step/phase decomposition
- Claude integration
- Visualization tools
- Phase_execution submodule
- 3 test files

**Role in Project**: Provides deterministic planning control and orchestration

---

### 💾 context_window_array/
**Primary Purpose**: Implements context window array functionality for LLM orchestration

**Contains**:
- 6 core Python modules:
  - Search indexing
  - Storage
  - Batching
  - Working context management
- Comprehensive test suite:
  - 6 test files (~150KB of test code)
  - Coverage for batching, implementation context, models, search, store, working context

**Role in Project**: Advanced context management system supporting the planning pipeline

---

### 🐹 go/
**Primary Purpose**: Go language port/implementation of core system components

**Structure**:
```
go/
├── Makefile (build automation)
├── cmd/ (applications)
│   ├── context-engine/
│   └── loop-runner/
└── internal/ (13 packages)
    ├── CLI
    ├── Concurrency
    ├── Execution
    ├── File system
    ├── JSON handling
    ├── Models
    ├── Paths
    └── Planning modules
```

**Role in Project**: Modern language implementation of core components for performance and concurrency

---

### 🎨 baml_src/
**Primary Purpose**: Source definitions for BAML (Boundary Markup Language) framework

**Contains**:
- Function specifications (clients.baml, functions.baml - 76KB)
- Type definitions
- Client configurations
- Schema subdirectory with 23+ schema files covering:
  - Business rules
  - Category analysis
  - Data models
  - Various domain schemas

**Role in Project**: Type-safe AI function definitions that generate baml_client code

---

### 🔄 baml_client/
**Primary Purpose**: Auto-generated Python client library from baml_src

**Contains**:
- Async/sync client implementations
- Type builders
- Runtime utilities
- Streaming support
- Generated code for calling BAML functions

**Role in Project**: Provides Python interface to BAML-defined AI functions

**Note**: Auto-generated - do not edit directly, modify baml_src instead

---

### 🤝 agents/
**Primary Purpose**: Agent specification markdown files for Claude personas

**Contains**:
- code-reviewer
- debugger
- feature-verifier
- test-runner

**Role in Project**: Specialized agents invoked during development and testing workflows

---

### 💻 commands/
**Primary Purpose**: Workflow state documentation and debugging guides

**Contains Documentation for**:
- blockers
- debug
- next steps
- revert
- spec
- status
- verify

**Role in Project**: CLI/workflow command reference for development lifecycle

---

### 📖 docs/
**Primary Purpose**: Reference documentation for project infrastructure

**Contains**:
- ARCHITECTURE.md
- NATIVE-HOOKS.md
- Session screenshots

**Role in Project**: Architectural guides and system documentation

---

### 💭 thoughts/
**Primary Purpose**: Integration with external thought/research management system

**Structure**:
- Symbolic links to external repository
- Organized hierarchically by date and topic
- Contains:
  - Planning documents
  - Research notes
  - Feature analysis
  - Global shared documentation
  - User-specific (maceo) organization

**Role in Project**: Houses searchable research, plans, and documentation organized by date

---

### 🗓️ sprints/
**Primary Purpose**: Long-term sprint planning and roadmap for Tanka AI project

**Contains**:
- MASTER_SPRINT_PLAN.md
- sprint_01 through sprint_24 (24 sprint documents)

**Features Covered**:
- Database schema
- Authentication
- API framework
- Memory storage
- Vector database
- Messaging
- AI chat
- Permissions
- Compliance
- Scaling

**Role in Project**: Comprehensive product roadmap (4,939 requirements across 24 sprints)

---

### 🧪 tests/
**Primary Purpose**: Test suite for planning pipeline functionality

**Contains**:
- 3 test files:
  - Autonomous loop execution tests
  - Phase execution tests
  - Loop orchestrator integration tests

**Role in Project**: Ensures planning pipeline reliability and correctness

---

### 🏗️ build/
**Primary Purpose**: Build output directory

**Current State**: Empty (no files)

**Role in Project**: Stores build artifacts and compiled binaries

---

### 📤 output/
**Primary Purpose**: Stores output artifacts and results

**Contains**:
- silmari-Context-Engine subdirectory (test/build outputs)

**Role in Project**: Captures execution results and generated artifacts

---

## 🏛️ Architecture Documentation

### Multi-Layer System Design

The project implements a **4-layer architecture**:

1. **Application Layer**: silmari_rlm_act (main entry point)
2. **Orchestration Layer**: planning_pipeline (deterministic control)
3. **Context Management Layer**: context_window_array (LLM context handling)
4. **AI Integration Layer**: BAML (type-safe AI functions)

### Language Diversity

| Language | Purpose | Directories |
|----------|---------|-------------|
| **Python** | Main application logic, AI integration, pipeline orchestration | silmari_rlm_act, planning_pipeline, context_window_array, baml_client |
| **Go** | Performance-critical components, CLI tools, concurrent execution | go/ |
| **BAML** | AI function definitions and schemas | baml_src/ |
| **Markdown** | Documentation, agents, commands, sprints | docs, agents, commands, sprints, thoughts |

### Component Integration Pattern

```
┌─────────────────────────────────────────────────┐
│            silmari_rlm_act (Entry)              │
│  ┌───────────────────────────────────────────┐  │
│  │       planning_pipeline (Control)         │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │  context_window_array (Context)     │  │  │
│  │  │  ┌───────────────────────────────┐  │  │  │
│  │  │  │   BAML (AI Functions)         │  │  │  │
│  │  │  └───────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
         ↓                    ↓
    ┌────────┐          ┌──────────┐
    │ Agents │          │ Commands │
    └────────┘          └──────────┘
```

---

## 📚 Historical Context (from thoughts/)

### Related Research Documents

The `thoughts/` directory contains extensive historical documentation:

#### Most Recent Project Structure Research
- `thoughts/shared/research/2026-01-05-project-structure.md` - Comprehensive overview organized into Core Application, Configuration & Build, Development & Testing, Output & Storage sections
- `thoughts/shared/research/2026-01-05-project-structure-detailed.md` - Extremely detailed breakdown with file sizes, component descriptions, architectural patterns, and pipeline flow diagrams

#### Earlier Versions
- `thoughts/shared/research/2026-01-04-project-structure.md`
- `thoughts/shared/research/2026-01-03-project-structure.md`
- `thoughts/shared/research/2026-01-02-project-structure.md`
- `thoughts/shared/research/2026-01-01-project-structure.md`

#### Architecture Documentation
- `thoughts/shared/research/2025-12-31-codebase-architecture.md` - Full codebase architecture with four-layer memory details, native hooks system, data flow diagrams

#### How-To Guides
- `thoughts/shared/docs/2026-01-05-how-to-use-context-window-array.md` - Step-by-step guide for Context Window Array usage
- `thoughts/shared/docs/2026-01-01-how-to-use-cli-commands.md` - Complete CLI guide (orchestrator.py, planning_orchestrator.py, loop-runner.py)
- `thoughts/shared/docs/2026-01-03-how-to-run-pipeline-with-baml.md` - Guide for running planning pipeline with BAML
- `thoughts/shared/docs/2025-12-31-how-to-run-planning-pipeline.md` - Comprehensive planning pipeline guide with resume procedures

---

## 🔗 Code References

### Directory Listing
```bash
# Main project directories visible at root level
/home/maceo/Dev/silmari-Context-Engine/
├── agents/
├── baml_client/
├── baml_src/
├── build/
├── commands/
├── context_window_array/
├── docs/
├── go/
├── output/
├── planning_pipeline/
├── silmari_rlm_act/
├── sprints/
├── tests/
└── thoughts/
```

### Key Entry Points
- `silmari_rlm_act/` - Main application entry point
- `orchestrator.py` - Root-level orchestration script
- `planning_orchestrator.py` - Planning-specific orchestrator
- `loop-runner.py` - Autonomous loop execution
- `go/cmd/context-engine/` - Go CLI application
- `go/cmd/loop-runner/` - Go loop runner

---

## 🔗 Related Research

- [2026-01-05: Detailed Project Structure](thoughts/shared/research/2026-01-05-project-structure-detailed.md) - Comprehensive breakdown with file sizes and patterns
- [2025-12-31: Codebase Architecture](thoughts/shared/research/2025-12-31-codebase-architecture.md) - Full architecture documentation with data flow diagrams
- [2026-01-05: How to Use Context Window Array](thoughts/shared/docs/2026-01-05-how-to-use-context-window-array.md) - Usage guide
- [2026-01-01: How to Use CLI Commands](thoughts/shared/docs/2026-01-01-how-to-use-cli-commands.md) - CLI reference

---

## ❓ Open Questions

None - the project structure is well-documented and clear.

---

## 📝 Notes

This research was conducted on **2026-01-06** on the **main** branch at commit **6444e3fbd45c86ffbafba15b2f132c41040a8e1a**. The project structure is stable and well-organized with clear separation of concerns across 14 main directories.

The project demonstrates a sophisticated architecture combining:
- Python for AI/ML orchestration
- Go for performance-critical components
- BAML for type-safe AI function definitions
- Comprehensive testing and documentation
- Sprint-based planning for long-term roadmap

---

*Research completed successfully. All main directories documented and categorized.*
