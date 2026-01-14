---
date: 2026-01-14T13:52:30.924230-05:00
researcher: Claude
git_commit: 4e0990d42031d4f5d183283015d372b284cae4d0
branch: main
repository: silmari-Context-Engine
topic: "Project Structure - Main Directories (Comprehensive)"
tags: [research, codebase, project-structure, architecture]
status: complete
last_updated: 2026-01-14
last_updated_by: Claude
---

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           SILMARI CONTEXT ENGINE - PROJECT STRUCTURE        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

**Date**: 2026-01-14T13:52:30.924230-05:00
**Researcher**: Claude
**Git Commit**: `4e0990d42031d4f5d183283015d372b284cae4d0`
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📚 Research Question

What is the project structure? List main directories only.

---

## 🎯 Summary

The **silmari-Context-Engine** is a dual-language project (Python + Go) implementing a Recursive Loop Model (RLM) Act framework for autonomous AI development loops. The project follows a phase-based architecture with checkpoint-based resumption, BAML-driven AI function definitions, and specialized subagent delegation patterns.

The codebase is organized into **11 main functional directories** plus configuration and documentation areas:

---

## 📊 Main Directories

### Core Implementation Directories

| Directory | Purpose | Language | Key Features |
|-----------|---------|----------|--------------|
| **silmari_rlm_act/** | Primary RLM Act framework package | Python | Phases, agents, validation, checkpoints, CLI |
| **planning_pipeline/** | Planning & decomposition pipeline | Python | Autonomous loop, decomposition, context generation |
| **go/** | High-performance runtime | Go | Planning logic, CLI commands, concurrent execution |
| **baml_src/** | AI function definitions | BAML | Function schemas, types, clients, generators |
| **baml_client/** | Generated BAML client | Python | Auto-generated Python bindings |
| **context_window_array/** | Context management system | Python | Storage, indexing, batching, working context |

### Supporting Directories

| Directory | Purpose | Contents |
|-----------|---------|----------|
| **agents/** | Subagent templates | Agent instructions (code-reviewer, test-runner, feature-verifier, debugger) |
| **commands/** | CLI command definitions | Command implementations |
| **docs/** | Documentation | Architecture guides, native hooks docs, screenshots |
| **tests/** | Top-level test suite | Integration and unit tests |
| **thoughts/** | Knowledge base | Research documents, planning artifacts, searchable content |

### Generated & Output Directories

| Directory | Purpose |
|-----------|---------|
| **output/silmari-Context-Engine/** | Build artifacts, file groups, tech stack analysis |
| **silmari-messenger-plans/** | Messenger feature planning docs |

---

## 🏗️ Detailed Findings

### 🔷 silmari_rlm_act/

**Primary Python package** for the RLM Act framework.

<details>
<summary>📁 Internal Structure</summary>

- `phases/` - Phase implementations (decomposition, research, implementation, beads_sync, multi_doc, tdd_planning)
- `agents/` - Subagent definitions (codebase-analyzer, codebase-locator, codebase-pattern-finder, thoughts-analyzer, thoughts-locator, web-search-researcher)
- `validation/` - Validation models and services
- `checkpoints/` - Checkpoint management for session resumption
- `commands/` - CLI command implementations
- `context/` - Context generation and management
- `hooks/` - Integration hooks for Claude Code
- `tests/` - Test suite for RLM Act components
- `pipeline.py` - Main orchestration pipeline
- `cli.py` - Command-line interface
- `models.py` - Core data models

</details>

**Role**: Central orchestration layer for autonomous development loops

---

### 🔷 planning_pipeline/

**Python implementation** of the planning and decomposition pipeline.

<details>
<summary>📁 Internal Structure</summary>

- `autonomous_loop.py` - Main autonomous execution loop
- `claude_runner.py` - Claude API invocation and management
- `decomposition.py` - Feature decomposition logic
- `context_generation.py` - Context compilation for prompts
- `step_decomposition.py` - Breaking down implementation steps
- `beads_controller.py` - BEADS system integration
- `checkpoint_manager.py` - State persistence across sessions
- `models.py` - Pipeline data structures
- `steps.py` - Phase step definitions
- `pipeline.py` - Pipeline orchestration
- `phase_execution/` - Phase-specific execution logic
- `tests/` - Integration tests for pipeline

</details>

**Role**: High-level planning and task decomposition engine

---

### 🔷 go/

**Go language implementation** for performance-critical runtime components.

<details>
<summary>📁 Internal Structure</summary>

- `cmd/` - Command implementations:
  - `context-engine/` - Context engine CLI
  - `loop-runner/` - Loop execution CLI
- `internal/` - Core Go modules:
  - `planning/` - Planning logic with models, decomposition, implementation, checkpoint management, CLI, comprehensive tests
  - `models/`, `paths/`, `json/`, `exec/`, `fs/`, `concurrent/` - Utility packages
- `build/` - Compiled binaries for multiple platforms

</details>

**Role**: High-performance execution runtime for planning and loop operations

---

### 🔷 baml_src/

**BAML (Business Application Markup Language)** configuration for structured AI function definitions.

<details>
<summary>📁 Internal Structure</summary>

- `functions.baml` - Function definitions for AI prompts (78KB - largest file)
- `types.baml` - Type definitions for structured outputs
- `clients.baml` - Client configurations
- `generators.baml` - Generation configurations
- `schema/` - Schema definitions
- `resume.baml` - Resume-specific definitions
- `Gate1SharedClasses.baml` - Shared class definitions

</details>

**Role**: Declarative AI function interface definitions separate from imperative code

---

### 🔷 context_window_array/

**Context window management** and batching implementation.

<details>
<summary>📁 Internal Structure</summary>

- `store.py` - Context storage backend
- `search_index.py` - Indexing for context search
- `working_context.py` - Working context management
- `implementation_context.py` - Implementation-specific context
- `batching.py` - Batching strategies for large contexts
- `models.py` - Data models
- `exceptions.py` - Custom exceptions
- `tests/` - Unit tests

</details>

**Role**: Manages context windows, memory layers, and context batching for LLM interactions

---

### 🔷 baml_client/

**Generated Python client code** for BAML functions.

**Role**: Auto-generated Python bindings for BAML-defined AI functions

---

### 🔷 agents/

**Subagent configuration templates** used during autonomous implementation.

**Contents**:
- `code-reviewer.md` - Code review agent instructions
- `test-runner.md` - Test execution agent instructions
- `feature-verifier.md` - Feature verification agent instructions
- `debugger.md` - Debugging agent instructions

**Role**: Defines behavior and instructions for specialized subagents

---

### 🔷 commands/

**CLI command definitions** and implementations.

**Role**: Command-line interface implementations (legacy, with newer implementations in `silmari_rlm_act/commands/`)

---

### 🔷 docs/

**Project documentation** and architectural guides.

**Contents**:
- `ARCHITECTURE.md` - System architecture explanation
- `NATIVE-HOOKS.md` - Native hooks mode documentation
- `session-screenshot.jpg` - Example session screenshot

**Role**: Human-readable documentation and onboarding materials

---

### 🔷 tests/

**Top-level test suite** for integration testing.

**Contents**:
- `test_autonomous_loop.py` - Autonomous loop tests
- `test_execute_phase.py` - Phase execution tests
- `test_loop_orchestrator_integration.py` - Integration tests

**Role**: Integration and end-to-end testing across the system

---

### 🔷 thoughts/

**Knowledge base and research repository** containing searchable research documents and planning artifacts.

**Role**: Long-term memory and documentation storage for the project

---

## 🏛️ Architecture Documentation

### Key Structural Patterns

```
┌─────────────────────────────────────────────────────────────┐
│  1. DUAL LANGUAGE IMPLEMENTATION                            │
│  • Python: High-level orchestration, prototyping           │
│  • Go: Performance-critical runtime components             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  2. PHASE-BASED ARCHITECTURE                                │
│  • Decomposition → Research → Implementation → Validation   │
│  • Each phase has dedicated modules                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  3. CHECKPOINT SYSTEM                                       │
│  • Extensive state management for session resumption       │
│  • Multiple checkpoint directories (.rlm-act-checkpoints/, │
│    .workflow-checkpoints/)                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  4. SUBAGENT DELEGATION PATTERN                             │
│  • Specialized agents for specific tasks                    │
│  • Code review, testing, verification, debugging           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  5. BAML INTEGRATION                                        │
│  • Structured AI function definitions separate from code   │
│  • Auto-generated client bindings                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  6. MEMORY LAYERING                                         │
│  • Working, episodic, semantic, and procedural layers      │
│  • Context window management and batching                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  7. TESTING THROUGHOUT                                      │
│  • Test files alongside implementation                      │
│  • Coverage across both Python and Go                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Root-Level Organization

### Configuration Files

<table>
<tr>
<td width="50%">

**Python Configuration**
- `pyproject.toml` - Poetry project metadata
- `poetry.lock` - Locked dependencies
- `pytest.ini` - Test configuration
- `mypy.ini` - Type checking config

</td>
<td width="50%">

**Go Configuration**
- `go.mod` - Go module definitions
- `go.sum` - Dependency checksums

</td>
</tr>
<tr>
<td colspan="2">

**General Configuration**
- `.env` - Environment variables
- `Dockerfile` / `docker-compose.yml` - Container definitions

</td>
</tr>
</table>

### Documentation Files

- `README.md` - Main project documentation
- `CLAUDE.md` - Claude Code-specific instructions
- `PROMPT.md` - Prompt templates and guidelines
- `AGENTS.md` - Agent documentation
- `CONTRIBUTING.md` - Contribution guidelines
- `LICENSE` - Project license

### Root-Level Scripts

| Script | Purpose | Size |
|--------|---------|------|
| `loop-runner.py` | Autonomous loop execution | 50KB |
| `orchestrator.py` | Project orchestration and initialization | 50KB |
| `planning_orchestrator.py` | Planning phase orchestration | 20KB |
| `resume_pipeline.py` | Resume pipeline logic | - |
| `resume_planning.py` | Resume planning logic | - |
| `setup-context-engineered.sh` | Setup for context engineering | - |
| `setup-native-hooks.sh` | Setup for native hooks mode | - |
| `docker-claude.sh` | Docker execution wrapper | - |
| `loop.sh` | Simple loop runner | - |
| `install.sh` | Installation script | - |
| `mcp-setup.py` | MCP setup | - |

### Hidden Configuration Directories

<details>
<summary>🔒 System Directories (Click to expand)</summary>

- `.claude/` - Claude Code settings and agent definitions
- `.agent/` - Agent runtime state and memory
- `.beads/` - BEADS system state
- `.silmari/` - Silmari framework configuration
- `.specstory/` - Specstory history and tracking
- `.rlm-act-checkpoints/` - Checkpoint files for resumption
- `.workflow-checkpoints/` - Workflow state checkpoints

</details>

---

## 📋 Code References

### Primary Entry Points

- `silmari_rlm_act/pipeline.py` - Main orchestration pipeline
- `silmari_rlm_act/cli.py` - Command-line interface
- `planning_pipeline/autonomous_loop.py` - Autonomous execution loop
- `go/cmd/loop-runner/` - Go loop runner CLI
- `loop-runner.py` - Python loop runner script
- `orchestrator.py` - Project orchestrator

### Key Configuration

- `baml_src/functions.baml` - AI function definitions (78KB)
- `pyproject.toml` - Python dependencies and project metadata
- `go.mod` - Go module dependencies

---

## 🔗 Related Research

- `thoughts/research/2026-01-14-project-structure.md` - Previous project structure overview

---

## ❓ Open Questions

None - this is a structural overview documenting the existing directory layout.

---

## 📌 Summary Table

| Category | Count | Examples |
|----------|-------|----------|
| **Core Implementation Dirs** | 6 | silmari_rlm_act/, planning_pipeline/, go/, baml_src/, baml_client/, context_window_array/ |
| **Supporting Dirs** | 5 | agents/, commands/, docs/, tests/, thoughts/ |
| **Output Dirs** | 2 | output/, silmari-messenger-plans/ |
| **Hidden Config Dirs** | 7 | .claude/, .agent/, .beads/, .silmari/, .specstory/, .rlm-act-checkpoints/, .workflow-checkpoints/ |
| **Languages** | 2 | Python (primary), Go (runtime) |
| **Configuration Files** | 10+ | pyproject.toml, go.mod, pytest.ini, etc. |
| **Root Scripts** | 11 | loop-runner.py, orchestrator.py, etc. |

---

```
┌─────────────────────────────────────────────────────────────┐
│                    END OF RESEARCH                          │
│                                                             │
│  For follow-up questions, please ask and this document     │
│  will be updated with additional findings.                 │
└─────────────────────────────────────────────────────────────┘
```
