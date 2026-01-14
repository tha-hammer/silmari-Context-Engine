---
date: 2026-01-14T12:32:43-05:00
researcher: maceo
git_commit: 5cdac13eab84a7e12ad4fbc5d147829819d33b79
branch: main
repository: tha-hammer/silmari-Context-Engine
topic: "Project Structure - Main Directories"
tags: [research, codebase, project-structure, architecture, directory-layout]
status: complete
last_updated: 2026-01-14
last_updated_by: maceo
---

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         SILMARI CONTEXT ENGINE - PROJECT STRUCTURE        ║
║                   Main Directories Overview               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

# Research: Project Structure - Main Directories

**Date**: 2026-01-14T12:32:43-05:00
**Researcher**: maceo
**Git Commit**: `5cdac13eab84a7e12ad4fbc5d147829819d33b79`
**Branch**: main
**Repository**: tha-hammer/silmari-Context-Engine

---

## 📋 Research Question

What is the project structure? List main directories only.

---

## 🎯 Summary

The **Silmari Context Engine** is an autonomous project builder for Claude Code with a comprehensive directory structure organized across **24 main functional directories**. The project implements a 4-layer memory architecture (Working Context, Episodic Memory, Semantic Memory, Procedural Memory) and supports both interactive and autonomous operational modes. The codebase uses a multi-language approach with Python (primary), Go (port), and BAML (LLM schemas).

---

## 📊 Main Directories

### Core Implementation Directories

| Directory | Purpose | Key Components |
|-----------|---------|----------------|
| **silmari_rlm_act/** | Main packaged application | 6-phase pipeline: Research → Learn → Model → Act → Verify → Deploy |
| **planning_pipeline/** | Planning phase implementation | Requirement decomposition, Python TDD pipeline |
| **context_window_array/** | Context management library | Core CWA structures for managing AI context |
| **go/** | Go runtime implementation | Complete Go port for performance and cross-platform deployment |

### Agent & Schema Definitions

| Directory | Purpose | Key Components |
|-----------|---------|----------------|
| **agents/** | Agent definitions | feature-verifier, test-runner, debugger, code-reviewer (Markdown) |
| **baml_src/** | BAML source schemas | Function and type definitions for structured AI interactions |
| **baml_client/** | Generated BAML code | Auto-generated client code from BAML schemas |

### Configuration & Commands

| Directory | Purpose | Key Components |
|-----------|---------|----------------|
| **commands/** | CLI command definitions | spec, debug, status, blockers, verify, revert, next (Markdown) |
| **.claude/** | Claude Code IDE config | Agent definitions and IDE settings |
| **.cursor/** | Cursor IDE config | IDE-specific agent and command definitions |

### Documentation & Knowledge

| Directory | Purpose | Key Components |
|-----------|---------|----------------|
| **docs/** | Architecture documentation | ARCHITECTURE.md, NATIVE-HOOKS.md |
| **thoughts/** | Research & planning notes | Research documents, architectural analysis, organized by date |
| **silmari-messenger-plans/** | Sprint plans | 24 sprint plans for related Silmari Messenger project |

### Execution & State Management

| Directory | Purpose | Key Components |
|-----------|---------|----------------|
| **.agent/** | Agent memory system | Agent rules, working context, persistent memory, artifacts, hooks |
| **.rlm-act-checkpoints/** | RLM Act checkpoints | Checkpoint files for resumable autonomous task execution |
| **.workflow-checkpoints/** | Workflow state | Checkpoint files for resuming workflow execution |
| **.specstory/** | Spec & story tracking | History of specifications and implementation stories |

### Build & Artifacts

| Directory | Purpose | Key Components |
|-----------|---------|----------------|
| **dist/** | Distribution artifacts | Compiled/packaged binaries and distribution files |
| **output/** | Generated outputs | Analysis results, file groups, tech stack information |
| **.beads/** | Build system artifacts | Sync state and build configuration |
| **.silmari/** | Project metadata | Silmari framework configuration and state |

### Testing & Development

| Directory | Purpose | Key Components |
|-----------|---------|----------------|
| **tests/** | Test suite | Project-level tests and test utilities |
| **.venv/** | Python virtual environment | Isolated Python environment with dependencies |
| **.pytest_cache/** | Testing cache | Pytest test result and cache data |
| **.hypothesis/** | Property testing cache | Hypothesis testing framework cache |
| **.mypy_cache/** | Type checking cache | MyPy static type checker cache files |
| **.ruff_cache/** | Linter cache | Ruff code linting tool cache |

### Version Control

| Directory | Purpose | Key Components |
|-----------|---------|----------------|
| **.git/** | Version control | Git repository metadata and history |

---

## 🏗️ Architecture Overview

### 🧠 4-Layer Memory System

```
┌─────────────────────────────────────────────────────┐
│  Layer 1: Working Context                           │
│  ├─ Current task state                              │
│  └─ Active files and code references                │
├─────────────────────────────────────────────────────┤
│  Layer 2: Episodic Memory                           │
│  ├─ Session history                                 │
│  └─ Recent interactions                             │
├─────────────────────────────────────────────────────┤
│  Layer 3: Semantic Memory                           │
│  ├─ Code structure knowledge                        │
│  └─ Architecture patterns                           │
├─────────────────────────────────────────────────────┤
│  Layer 4: Procedural Memory                         │
│  ├─ Best practices                                  │
│  └─ Development workflows                           │
└─────────────────────────────────────────────────────┘
```

### 🚀 6-Phase Autonomous Pipeline

```
Research → Learn → Model → Act → Verify → Deploy
    ↓         ↓        ↓       ↓       ↓        ↓
  Gather   Analyze  Design  Implement Test   Release
```

### 💻 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Primary Runtime** | Python 3.x | Main implementation language |
| **Performance Port** | Go | Cross-platform deployment and performance |
| **LLM Interface** | BAML | Structured AI interaction schemas |
| **Deployment** | Docker | Containerized execution environment |
| **Testing** | pytest, hypothesis | Unit and property-based testing |
| **Type Checking** | mypy | Static type analysis |
| **Linting** | ruff | Code quality enforcement |

---

## 📂 Root-Level Files

### 📚 Documentation Files

<details>
<summary><strong>Expand to see all documentation files</strong></summary>

| File | Purpose |
|------|---------|
| **README.md** | Main project documentation with quick start and usage |
| **CLAUDE.md** | Detailed Claude Code integration instructions (27KB) |
| **CONTRIBUTING.md** | Contribution guidelines |
| **AGENTS.md** | Documentation of available agents |
| **DOCKER-SETUP.md** | Docker configuration and setup instructions |
| **PROMPT.md** | Core system prompt |
| **docs/ARCHITECTURE.md** | Deep technical architecture explanation |
| **docs/NATIVE-HOOKS.md** | Native hooks mode documentation |
| **TEST_COVERAGE_ANALYSIS_REQ_008.md** | Test coverage analysis for requirement 008 |
| **TEST_COVERAGE_CHECKLIST_REQ_008.md** | Test coverage checklist |
| **TEST_COVERAGE_INDEX.md** | Index of test coverage |
| **TEST_COVERAGE_SUMMARY_REQ_008.md** | Test coverage summary |
| **QUICK_REFERENCE_TEST_COVERAGE.txt** | Quick reference test coverage guide |
| **PHASE_7_IMPLEMENTATION_SUMMARY.md** | Phase 7 implementation summary |

</details>

### ⚙️ Configuration Files

<details>
<summary><strong>Expand to see all configuration files</strong></summary>

| File | Purpose |
|------|---------|
| **pyproject.toml** | Python project configuration with dependencies |
| **poetry.lock** | Poetry dependency lock file |
| **go.mod** | Go module definition |
| **go.sum** | Go module checksums |
| **pytest.ini** | Pytest configuration |
| **mypy.ini** | MyPy type checker configuration |
| **.env** | Environment variables |
| **.gitignore** | Git ignore rules |
| **.gitattributes** | Git attributes |
| **.dockerignore** | Docker ignore rules |
| **docker-compose.yml** | Docker Compose configuration |
| **Dockerfile** | Docker image definition |
| **mcp-config.example.json** | Example MCP (Model Context Protocol) configuration |
| **.coverage** | Coverage test data |

</details>

### 🔧 Executable Scripts

<details>
<summary><strong>Expand to see all executable scripts</strong></summary>

| Script | Purpose |
|--------|---------|
| **orchestrator.py** | Main orchestration script for autonomous execution |
| **loop-runner.py** | Autonomous feature implementation loop |
| **planning_orchestrator.py** | Planning phase orchestrator |
| **resume_pipeline.py** | Pipeline resumption utility |
| **resume_planning.py** | Planning resumption utility |
| **install.sh** | Installation script |
| **setup-context-engineered.sh** | Context engine setup script |
| **setup-native-hooks.sh** | Native hooks setup script |
| **mcp-setup.py** | MCP configuration setup |
| **loop.sh** | Simple loop runner script |
| **docker-claude.sh** | Docker-based Claude runner |
| **test-conversation.py** | Test conversation utility |

</details>

---

## 🔗 Code References

| Location | Description |
|----------|-------------|
| **Root Directory** | `/home/maceo/Dev/silmari-Context-Engine` |
| **Total Main Directories** | 24 functional directories |
| **Documentation Files** | 14 documentation files at root level |
| **Configuration Files** | 14 configuration files |
| **Executable Scripts** | 12 scripts for various operations |

---

## 📖 Historical Context (from thoughts/)

The following documents provide additional context about the project structure:

| Document | Date | Focus |
|----------|------|-------|
| `thoughts/searchable/research/2026-01-14-project-structure.md` | 2026-01-14 | 15 main directories with detailed breakdown |
| `thoughts/searchable/research/2026-01-14-project-structure-main-directories.md` | 2026-01-14 | Main directories summary |
| `thoughts/searchable/shared/research/2026-01-14-project-structure.md` | 2026-01-14 | Comprehensive 15-directory analysis |
| `thoughts/searchable/shared/research/2026-01-13-project-structure.md` | 2026-01-13 | 16-directory structure with memory architecture |
| `thoughts/searchable/shared/research/2026-01-14-main-directories.md` | 2026-01-14 | Detailed directory descriptions |
| `thoughts/searchable/shared/research/2026-01-14-claude-runner-cli-vs-sdk.md` | 2026-01-14 | CLI vs SDK interaction patterns |
| `thoughts/searchable/shared/research/2026-01-14-silmari-rlm-act-poetry-packaging.md` | 2026-01-14 | Packaging analysis with dependency mapping |
| `thoughts/searchable/shared/plans/2026-01-01-tdd-planning-orchestrator.md` | 2026-01-01 | Planning orchestrator TDD plan |

---

## 🔍 Related Research

- Architecture deep dive: `thoughts/searchable/shared/research/2026-01-14-claude-runner-cli-vs-sdk.md`
- Packaging analysis: `thoughts/searchable/shared/research/2026-01-14-silmari-rlm-act-poetry-packaging.md`
- Planning implementation: `thoughts/searchable/shared/plans/2026-01-01-tdd-planning-orchestrator.md`

---

## 🎯 Key Characteristics

### Operational Modes

```
┌──────────────────────┬──────────────────────┐
│  Interactive Mode    │  Autonomous Mode     │
├──────────────────────┼──────────────────────┤
│  Claude Code IDE     │  Loop Runner         │
│  Native Hooks        │  Orchestrator        │
│  Real-time feedback  │  Unattended execution│
└──────────────────────┴──────────────────────┘
```

### Development Philosophy

- **Multi-language support**: Python primary, Go for performance
- **Comprehensive testing**: Unit, property-based, coverage tracking
- **Autonomous execution**: Checkpoint-based resumable operations
- **Memory persistence**: 4-layer architecture prevents degradation
- **IDE integration**: Claude Code and Cursor support

---

## ✅ Summary Table

| Metric | Count |
|--------|-------|
| **Main Directories** | 24 |
| **Core Implementation** | 4 (silmari_rlm_act, planning_pipeline, context_window_array, go) |
| **Agent Definitions** | 3 (agents, baml_src, baml_client) |
| **Configuration** | 3 (.claude, .cursor, commands) |
| **Documentation** | 3 (docs, thoughts, silmari-messenger-plans) |
| **Execution & State** | 4 (.agent, .rlm-act-checkpoints, .workflow-checkpoints, .specstory) |
| **Build & Artifacts** | 4 (dist, output, .beads, .silmari) |
| **Testing & Dev** | 6 (tests, .venv, .pytest_cache, .hypothesis, .mypy_cache, .ruff_cache) |
| **Version Control** | 1 (.git) |
| **Root Files** | 40+ (documentation, config, scripts) |

---

**End of Research Document**

```
┌─────────────────────────────────────────────────────────┐
│  Research Status: ✅ COMPLETE                           │
│  Last Updated: 2026-01-14                               │
│  By: maceo                                              │
└─────────────────────────────────────────────────────────┘
```
