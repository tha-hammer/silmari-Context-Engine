---
date: 2026-01-14T17:04:05-05:00
researcher: Claude
git_commit: 52fed593d55ee464b173da4d5ee58c12d1885552
branch: main
repository: tha-hammer/silmari-Context-Engine
topic: "Project Structure - Main Directories"
tags: [research, codebase, project-structure, architecture]
status: complete
last_updated: 2026-01-14
last_updated_by: Claude
---

```
╔════════════════════════════════════════════════════════╗
║                                                        ║
║         SILMARI CONTEXT ENGINE                         ║
║         Project Structure Research                     ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

**Date**: 2026-01-14T17:04:05-05:00
**Researcher**: Claude
**Git Commit**: `52fed593d55ee464b173da4d5ee58c12d1885552`
**Branch**: `main`
**Repository**: tha-hammer/silmari-Context-Engine
**Status**: ✅ Complete

---

## 📋 Research Question

What is the project structure? List main directories only.

---

## 🎯 Summary

The Silmari Context Engine project is organized into **14 main directories** (excluding hidden directories), each serving a distinct purpose in the autonomous development pipeline. The project implements a comprehensive autonomous TDD system with three implementation layers: **Python** (core logic and ML), **Go** (production binaries), and **BAML** (type-safe LLM integration). A persistent knowledge layer (`thoughts/`) maintains semantic memory across sessions.

---

## 📊 Main Directories Overview

| Directory | Purpose | Layer |
|-----------|---------|-------|
| `agents/` | Specialized subagent definitions (review, test, debug) | 🤖 Quality |
| `baml_client/` | Auto-generated BAML client library for type-safe LLM calls | 🔗 Integration |
| `baml_src/` | BAML source definitions for LLM functions | 🔗 Integration |
| `commands/` | Custom slash commands for interactive sessions | 💻 CLI |
| `context_window_array/` | Context management architecture implementation | 🧠 Core |
| `dist/` | Built Python package distributions (.whl, .tar.gz) | 📦 Distribution |
| `docs/` | Project documentation (ARCHITECTURE.md, NATIVE-HOOKS.md) | 📚 Documentation |
| `go/` | Go implementation of planning pipeline and loop runner | ⚙️ Production |
| `output/` | Generated analysis artifacts (file groups, tech stack) | 📤 Output |
| `planning_pipeline/` | Python planning and execution pipeline | 🐍 Python Core |
| `silmari-messenger-plans/` | Reference project sprint plans (24 sprints, 61 features) | 📋 Examples |
| `silmari_rlm_act/` | RLM-Act pipeline (Research, Learn, Model, Act) | 🐍 Python Core |
| `tests/` | Integration tests for autonomous loop | ✅ Testing |
| `thoughts/` | Persistent knowledge base and planning documents | 🧠 Memory |

---

## 🔍 Detailed Findings

### 🤖 Quality & Agent Layer

#### **agents/** - Specialized Subagent Definitions
**Contents**: 4 agent definition files
- `code-reviewer.md` - Expert code review specialist
- `debugger.md` - Error analysis and debugging
- `feature-verifier.md` - End-to-end feature verification
- `test-runner.md` - Test execution and analysis

**Purpose**: Defines specialized subagents invoked during the autonomous pipeline using `@agent-name` syntax. Provides independent validation, testing, and review capabilities for quality assurance in autonomous feature implementation.

---

### 🔗 LLM Integration Layer

#### **baml_client/** - Generated BAML Client Library
**Size**: Multiple Python modules (auto-generated)
**Key Files**:
- `async_client.py` - Asynchronous Claude function calling
- `sync_client.py` - Synchronous Claude function calling
- `runtime.py`, `parser.py` - Runtime utilities
- `type_map.py`, `types.py` - Type definitions

**Purpose**: Auto-generated from `baml_src/` definitions. Provides type-safe, documented interfaces for calling Claude functions throughout the codebase, ensuring type-checked LLM interactions.

#### **baml_src/** - BAML Function Definitions
**Key Files**:
- `functions.baml` (78KB) - Main function definitions
- `types.baml` - Custom type definitions
- `clients.baml` - Client configuration
- `generators.baml` - Code generation config
- `schema/` - Database/data schemas

**Purpose**: Source files defining typed LLM function calls to Claude. Specifies inputs, outputs, and system prompts. Generates the `baml_client/` library and ensures type safety for all AI-powered functions.

---

### 🐍 Python Core Implementation

#### **context_window_array/** - Context Management Architecture
**Structure**: 4 core modules + comprehensive test suite
**Key Files**:
- `models.py` - Context entry and type definitions
- `store.py` - Central context storage
- `search_index.py` - Vector-based context search
- `batching.py` - Task batching for operations
- `implementation_context.py` - Implementation phase context
- `working_context.py` - Working context compilation
- `tests/` - 6 test files

**Purpose**: Implements the core "Context Window Array" architecture for separating and managing context between working and implementation LLMs. Provides addressable, searchable context storage with vector-based semantic search and task batching.

**Key Concepts**:
- 📦 Central context store for all information
- 🔍 Vector-based semantic search for relevant context
- 📊 Task batching to organize context retrieval
- 🎯 Implementation context separate from working context

#### **planning_pipeline/** - Python Planning Pipeline
**Size**: 35KB+ core modules
**Key Files**:
- `pipeline.py` - Main orchestration pipeline
- `autonomous_loop.py` - Autonomous execution loop
- `claude_runner.py` (35KB) - Claude subprocess invocation
- `decomposition.py` (35KB) - Feature/requirement decomposition
- `checkpoint_manager.py`, `checkpoints.py` - Checkpoint state management
- `context_generation.py` - Context compilation
- `models.py` - Pipeline state data models
- `phase_execution/` - Phase execution implementations
- `tests/` - 21 test files

**Purpose**: Python implementation of the complete TDD planning and execution pipeline. Orchestrates planning, decomposing requirements, implementing features, and running tests.

**Pipeline Phases**:
1. 🔬 **Research** - Gather project information
2. 📋 **Planning** - Create detailed plans
3. 🔨 **Decomposition** - Break down into implementable steps
4. ⚙️ **Execution** - Run code through Claude
5. ✅ **Testing** - Run and validate tests
6. 👀 **Review** - Code review by subagents

#### **silmari_rlm_act/** - RLM-Act Pipeline (Main Package)
**Structure**: Comprehensive Python package with CLI
**Key Components**:
- `pipeline.py` - Main RLMActPipeline implementation
- `models.py` - PhaseResult, PhaseStatus, AutonomyMode models
- `cli.py` (12KB) - Command-line interface
- `phases/` - Phase implementations (research, decomposition, implementation, TDD planning)
- `agents/` - Claude agent definitions
- `commands/` - CLI subcommands
- `context/` - Context management utilities
- `checkpoints/` - Checkpoint state persistence
- `tests/` - Integration test suite

**Purpose**: The main Python package implementing the 6-phase autonomous TDD pipeline. Implements the Research-Learn-Model-Act loop for autonomous software development.

**Key Features**:
- 🔄 Six autonomous phases with detailed phase models
- 🎚️ Three autonomy modes (checked, semi-autonomous, fully-autonomous)
- 💾 Checkpoint-based resumability
- 🧩 BEADS framework integration for step decomposition
- 🤖 Specialized agents for different aspects

---

### ⚙️ Production Layer

#### **go/** - Go Implementation
**Structure**: Complete Go project with build system
**Key Directories**:
- `cmd/` - Command entry points
  - `context-engine/` - Main context engine binary
  - `loop-runner/` - Autonomous loop runner binary
- `internal/` - Go implementation packages
  - `planning/` (26 files) - Planning and orchestration
  - `cli/` (11 files) - Command-line interface
  - `models/` - Data models
  - `exec/` - Execution utilities
  - `fs/`, `json/`, `path/`, `concurrent/` - Utilities
- `build/` - Compiled binaries

**Purpose**: Go language implementation of the planning pipeline and loop runner. Provides production-grade binaries for autonomous feature implementation without requiring Python.

**Key Components**:
- 🚀 Claude runner for subprocess-based invocation
- 💾 Checkpoint management for resumable pipelines
- 🔨 Decomposition engine for breaking down requirements
- ⚙️ Implementation orchestration with phase management
- 👀 Review and validation logic

#### **dist/** - Python Package Distributions
**Contents**:
- `silmari_rlm_act-0.1.0-py3-none-any.whl` - Wheel distribution
- `silmari_rlm_act-0.1.0.tar.gz` - Source distribution

**Purpose**: Pre-built Python package distributions for the `silmari_rlm_act` module. Enables pip installation of the autonomous pipeline package. Generated from `pyproject.toml` configuration.

---

### 💻 CLI & Commands

#### **commands/** - Custom Slash Commands
**Contents**: 7 command definition files
- `blockers.md` - Identify blocking issues
- `debug.md` - Debug command
- `next.md` - Show next task
- `spec.md` - Show current specification
- `status.md` - Show project status
- `verify.md` - Verify feature completion
- `revert.md` - Revert changes

**Purpose**: Defines custom slash commands for Claude Code interactive sessions, providing quick access to project status, debugging, and navigation utilities. Enhances interactive development experience in native hooks mode.

---

### 📚 Documentation & Knowledge

#### **docs/** - Project Documentation
**Contents**:
- `ARCHITECTURE.md` (8.9KB) - Four-layer memory architecture explanation
- `NATIVE-HOOKS.md` (8KB) - Native hooks mode documentation
- `session-screenshot.jpg` - Example session screenshot

**Purpose**: Core project documentation explaining the Context Engine's memory model, architecture, and usage patterns.

**Key Topics**:
- ❗ Problem statement (context degradation in long-running AI sessions)
- ✅ Solution (four-layer memory: working, episodic, semantic, procedural)
- 🔄 Context compilation algorithm
- 📦 Artifact system for large outputs
- 🔁 Feedback loop for learning

#### **thoughts/** - Persistent Knowledge Base
**Structure**:
```
thoughts/
├── searchable/         - Indexed thought directory
│   ├── research/      - Research documentation and analysis
│   ├── shared/        - Shared team knowledge and plans
│   └── global/        - Symlink to global thoughts directory
├── maceo/             - User-specific thoughts (symlink)
└── shared/            - Shared team thoughts (symlink)
```

**Purpose**: Persistent knowledge base containing research findings, TDD planning documents, testing patterns analysis, architecture research, and integration guides. Implements the **semantic memory** and **episodic memory** layers from the four-layer architecture.

**Key Role**: Persists learning across sessions so future sessions can benefit from past discoveries. Enables continuity in autonomous development.

---

### 📤 Output & Examples

#### **output/** - Generated Analysis Output
**Contents**:
- `silmari-Context-Engine/groups/`
  - `file_groups.json` - File grouping by functionality
  - `tech_stack.json` - Technology stack analysis

**Purpose**: Generated analysis artifacts from project discovery/analysis passes. Contains meta-information about project structure and technology composition, used by context generation phases to understand project topology.

#### **silmari-messenger-plans/** - Reference Project Plans
**Contents**: Complete sprint plan with 25 files
- `MASTER_SPRINT_PLAN.md` - Overview of 24 sprints
- `sprint_01_database_schema.md` through `sprint_24_performance_scaling.md`

**Purpose**: Complete sprint plan for the "Silmari Messenger" reference project (a real-world Rust application built with Context Engine). Demonstrates the level of detail and planning the system can handle for a 61-feature project across 24 logical sprints.

---

### ✅ Testing Layer

#### **tests/** - Integration Tests
**Contents**: 3 integration test files
- `test_autonomous_loop.py` - Autonomous execution loop tests
- `test_execute_phase.py` - Phase execution tests
- `test_loop_orchestrator_integration.py` - End-to-end integration tests

**Purpose**: High-level integration tests for the complete autonomous pipeline. Verifies that phases work together correctly and the loop orchestration functions as expected. Quality assurance for the complete autonomous system.

---

## 🏗️ Architecture Layers

The Silmari Context Engine is organized into **5 architectural layers**:

<table>
<tr>
<td width="50%">

### Layer 1: 📚 Concept
- `docs/` - Architecture & design principles

### Layer 2: 🐍 Python Core
- `planning_pipeline/` - TDD pipeline orchestration
- `silmari_rlm_act/` - RLM-Act autonomous loop
- `context_window_array/` - Context management

### Layer 3: ⚙️ Production
- `go/` - Production-grade Go implementation
- `dist/` - Built package distributions

</td>
<td width="50%">

### Layer 4: 🔗 Integration
- `baml_src/` - LLM function definitions
- `baml_client/` - Type-safe LLM client

### Layer 5: 🧠 Knowledge
- `thoughts/` - Persistent learning & planning

### Layer 6: ✅ Quality
- `agents/` - Verification infrastructure
- `tests/` - Integration testing

</td>
</tr>
</table>

---

## 📁 Code References

### Directory Structure
```bash
# Main directories (excluding hidden)
./agents/                  # Subagent definitions (4 files)
./baml_client/            # Generated BAML client (10+ modules)
./baml_src/               # BAML source definitions (8+ files)
./commands/               # Slash commands (7 files)
./context_window_array/   # Context management (6 modules + tests)
./dist/                   # Package distributions (2 files)
./docs/                   # Documentation (3 files)
./go/                     # Go implementation (37+ files)
./output/                 # Generated artifacts
./planning_pipeline/      # Python pipeline (21+ test files)
./silmari-messenger-plans/# Reference plans (25 files)
./silmari_rlm_act/       # Main RLM-Act package
./tests/                  # Integration tests (3 files)
./thoughts/               # Knowledge base
```

### Root Files Overview
```bash
# Key root files
orchestrator.py           # Main orchestrator (50KB)
loop-runner.py           # Loop runner (50KB)
planning_orchestrator.py # Planning orchestrator (20KB)
resume_pipeline.py       # Pipeline resumption
pyproject.toml           # Python project config
poetry.lock              # Dependency lock file (71KB)
go.mod, go.sum          # Go module dependencies
```

---

## 🧩 Implementation Levels

```
┌─────────────────────────────────────────────────────────────┐
│                     CONCEPT LAYER                           │
│                    (docs/)                                  │
│            Architecture & Design Principles                  │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                     PYTHON LAYER                            │
│   (planning_pipeline/, silmari_rlm_act/,                    │
│    context_window_array/)                                   │
│        Core Logic & ML Integration                          │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                     GO LAYER                                │
│                    (go/)                                    │
│        Production-Grade Binary Distribution                 │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                 INTEGRATION LAYER                           │
│              (baml_src/, baml_client/)                      │
│        Type-Safe LLM Function Definitions                   │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                 KNOWLEDGE LAYER                             │
│                  (thoughts/)                                │
│         Persistent Learning & Planning Documents            │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                  QUALITY LAYER                              │
│               (agents/, tests/)                             │
│        Verification & Testing Infrastructure                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Patterns

### 1. **Dual Implementation Strategy**
- 🐍 **Python**: Rapid development, ML integration, prototyping
- ⚙️ **Go**: Production deployment, performance, binary distribution

### 2. **Type-Safe LLM Integration**
- 📝 **BAML Source** (`baml_src/`) defines contracts
- 🔗 **Generated Client** (`baml_client/`) ensures type safety
- ✅ All LLM interactions are type-checked and documented

### 3. **Persistent Knowledge Architecture**
- 💾 **thoughts/searchable/** - Indexed for fast search
- 📚 **thoughts/research/** - Research documentation
- 🤝 **thoughts/shared/** - Team knowledge base
- 🧠 Implements semantic/episodic memory layers

### 4. **Checkpoint-Based Resumability**
- 💾 Both Python and Go implementations support checkpoints
- 🔄 Pipelines can be interrupted and resumed
- 📊 State persistence for long-running autonomous tasks

### 5. **Specialized Agent Architecture**
- 🤖 Subagents handle specific tasks (review, test, debug, verify)
- 🎯 Referenced via `@agent-name` syntax in pipeline
- ✅ Independent validation and quality assurance

---

## 📊 Statistics

| Metric | Count |
|--------|-------|
| **Main Directories** | 14 (excluding hidden) |
| **Python Packages** | 3 (context_window_array, planning_pipeline, silmari_rlm_act) |
| **Go Commands** | 2 (context-engine, loop-runner) |
| **Specialized Agents** | 4 (code-reviewer, debugger, feature-verifier, test-runner) |
| **Custom Commands** | 7 (blockers, debug, next, spec, status, verify, revert) |
| **Test Files** | 30+ (distributed across packages) |
| **BAML Functions** | 8+ source files |
| **Reference Sprint Plans** | 24 sprints |

---

## 🔗 Cross-Component Connections

### Pipeline Orchestration Flow
```
silmari_rlm_act/pipeline.py
         ↓
planning_pipeline/autonomous_loop.py
         ↓
planning_pipeline/claude_runner.py → baml_client/ → Claude API
         ↓
context_window_array/store.py ← thoughts/ (semantic memory)
         ↓
agents/ (verification subagents)
         ↓
tests/ (validation)
```

### Context Management Flow
```
User Request
     ↓
Research Phase → context_window_array/store.py
     ↓
Context Batching → context_window_array/batching.py
     ↓
Vector Search → context_window_array/search_index.py
     ↓
Implementation Context → context_window_array/implementation_context.py
     ↓
Claude Execution → baml_client/async_client.py
```

---

## 💡 Historical Context (from thoughts/)

*Note: No specific historical documents were referenced in this initial structure research. The `thoughts/` directory serves as the persistent knowledge base for future research and planning documents.*

---

## 🔍 Related Research

- `thoughts/research/` - Directory for future research documentation
- `docs/ARCHITECTURE.md` - Comprehensive four-layer memory architecture
- `docs/NATIVE-HOOKS.md` - Native hooks mode documentation

---

## ❓ Open Questions

None. The project structure is well-documented and clearly organized with each directory serving a distinct purpose in the autonomous development pipeline.

---

## 📝 Notes

- All main directories are at the root level with clear, descriptive names
- The project maintains both Python and Go implementations for flexibility
- BAML integration provides type safety for all LLM interactions
- The `thoughts/` directory implements the semantic memory layer
- Checkpoint-based resumability is a core feature across implementations
- Specialized agents provide independent quality assurance
- The reference project (silmari-messenger-plans) demonstrates real-world usage

---

**Research completed successfully** ✅
