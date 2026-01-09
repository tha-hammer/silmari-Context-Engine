---
date: 2026-01-06T07:16:34-05:00
researcher: Claude
git_commit: 8a3aa0aead862af5069a27e0f0a6f5751153ce65
branch: main
repository: silmari-Context-Engine
topic: "Project Structure - Main Directories"
tags: [research, codebase, structure, directories, architecture]
status: complete
last_updated: 2026-01-06
last_updated_by: Claude
---

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              SILMARI CONTEXT ENGINE                          ║
║              Project Structure Research                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

**Status**: ✅ Complete
**Date**: 2026-01-06T07:16:34-05:00
**Researcher**: Claude
**Git Commit**: `8a3aa0aead862af5069a27e0f0a6f5751153ce65`
**Branch**: `main`
**Repository**: silmari-Context-Engine

---

## 📚 Research Question

**What is the project structure? List main directories only.**

---

## 🎯 Summary

The **Silmari Context Engine** is an autonomous project builder for Claude Code with a four-layer memory architecture. The project has **16 main directories** organized into distinct functional areas:

- **Core Implementation** (Python & Go): `silmari_rlm_act/`, `planning_pipeline/`, `go/`
- **AI/ML Integration**: `baml_client/`, `baml_src/`, `agents/`
- **Infrastructure**: `commands/`, `context_window_array/`, `output/`, `build/`
- **Documentation & Knowledge**: `thoughts/`, `docs/`, `sprints/`
- **Testing**: `tests/`

---

## 📊 Main Directory Structure

### 🏗️ Core Application Directories

| Directory | Type | Purpose | Key Contents |
|-----------|------|---------|--------------|
| `silmari_rlm_act/` | Python Package | Main application package with agents, context management, hooks, and phase orchestration | `agents/`, `checkpoints/`, `cli.py`, `commands/`, `context/`, `hooks/`, `models.py`, `phases/` |
| `planning_pipeline/` | Python Module | Planning and pipeline orchestration logic | Pipeline processing components |
| `go/` | Go Package | Go language implementation components | Go modules and packages |

### 🤖 AI/ML Integration

| Directory | Type | Purpose | Key Contents |
|-----------|------|---------|--------------|
| `baml_src/` | BAML Source | BAML (Behavioral AI Markup Language) source definitions | `clients.baml`, `functions.baml`, `generators.baml`, `resume.baml`, `schema/`, `types.baml` |
| `baml_client/` | Generated Code | Auto-generated Python client from BAML definitions | `async_client.py`, `sync_client.py`, `types.py`, `runtime.py`, `parser.py` |
| `agents/` | Agent Definitions | Agent behavior specifications and configurations | `code-reviewer.md`, `debugger.md`, `feature-verifier.md`, `test-runner.md` |

### 🛠️ Infrastructure & Utilities

| Directory | Type | Purpose | Description |
|-----------|------|---------|-------------|
| `commands/` | CLI Commands | Custom command-line interface commands | Command implementations |
| `context_window_array/` | Context System | Context window management and array processing | Context handling utilities |
| `output/` | Output Storage | Generated outputs and artifacts | Build artifacts and results |
| `build/` | Build Artifacts | Compiled code and build outputs | Binary and compiled files |

### 📖 Documentation & Knowledge Management

| Directory | Type | Purpose | Structure |
|-----------|------|---------|----------|
| `thoughts/` | Knowledge Base | Research, notes, and documentation repository | `global/`, `maceo/`, `searchable/`, `shared/` |
| `docs/` | Documentation | Project documentation | Documentation files |
| `sprints/` | Sprint Planning | Sprint plans and tracking | Sprint-related documents |

### ✅ Testing

| Directory | Type | Purpose | Description |
|-----------|------|---------|-------------|
| `tests/` | Test Suite | Unit tests, integration tests, and test utilities | Python test files |

---

## 🗂️ Detailed Findings

### Core Implementation Stack

The project uses a **polyglot architecture**:

<table>
<tr>
<td width="50%">

**Python Components**
- `silmari_rlm_act/` - Main package
- `planning_pipeline/` - Planning logic
- `baml_client/` - Generated AI client

</td>
<td width="50%">

**Go Components**
- `go/` - Go implementation
- `go.mod`, `go.sum` - Go modules

</td>
</tr>
</table>

### AI/ML Architecture

```
┌─────────────────────────────────────────────┐
│  BAML Workflow                              │
├─────────────────────────────────────────────┤
│  baml_src/ (Source definitions)             │
│      ↓                                      │
│  baml_client/ (Generated Python client)     │
│      ↓                                      │
│  agents/ (Agent behaviors)                  │
└─────────────────────────────────────────────┘
```

**BAML Integration Details:**
- **Source Files** (`baml_src/`):
  - `clients.baml` - Client configurations
  - `functions.baml` - Function definitions
  - `generators.baml` - Code generators
  - `resume.baml` - Resume/continuation logic
  - `types.baml` - Type definitions
  - `schema/` - Schema definitions

- **Generated Client** (`baml_client/`):
  - `async_client.py` - Asynchronous API
  - `sync_client.py` - Synchronous API
  - `types.py` - Type definitions
  - `runtime.py` - Runtime engine
  - `parser.py` - Parser utilities

### Agent System

The `agents/` directory contains specialized agent definitions:

| Agent | Purpose |
|-------|---------|
| `code-reviewer.md` | Code review automation |
| `debugger.md` | Debugging assistance |
| `feature-verifier.md` | Feature verification |
| `test-runner.md` | Test execution |

### Knowledge Management (`thoughts/`)

The thoughts directory has a structured organization:

```
thoughts/
├── global/       # Global/shared knowledge
├── maceo/        # User-specific notes
├── searchable/   # Searchable hard links
└── shared/       # Shared team knowledge
```

---

## 🏛️ Architecture Patterns

### 📦 Package Organization

The project follows a **hybrid architecture**:

1. **Core Package**: `silmari_rlm_act/` contains the main application logic
   - Sub-packages: `agents/`, `commands/`, `context/`, `hooks/`, `phases/`
   - Entry point: `cli.py`
   - Data models: `models.py`

2. **Generated Code**: `baml_client/` auto-generated from `baml_src/`
   - Separation of source definitions from generated implementation
   - Clean client interfaces (async/sync)

3. **Cross-Language**: Python + Go hybrid implementation
   - Go modules managed via `go.mod`/`go.sum`
   - Python as primary language

### 🔄 Build & Development

**Root-level Scripts:**
- `orchestrator.py` - Main orchestration logic
- `planning_orchestrator.py` - Planning workflow
- `loop-runner.py` - Loop execution
- `resume_pipeline.py` - Pipeline resumption
- `mcp-setup.py` - MCP (Model Context Protocol) setup

**Docker Support:**
- `Dockerfile` - Container definition
- `docker-compose.yml` - Composition
- `docker-claude.sh` - Claude integration script
- `.dockerignore` - Build exclusions

### 📁 Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables |
| `pytest.ini` | pytest configuration |
| `mypy.ini` | Type checking configuration |
| `.gitignore` | Git exclusions |
| `.gitattributes` | Git attributes |

---

## 💾 Code References

### Main Package Structure
- `silmari_rlm_act/__init__.py` - Package initialization
- `silmari_rlm_act/cli.py` - CLI entry point
- `silmari_rlm_act/models.py` - Core data models

### BAML Definitions
- `baml_src/clients.baml` - AI client definitions
- `baml_src/functions.baml` - Function specifications
- `baml_src/types.baml` - Type system

### Agent Configurations
- `agents/code-reviewer.md` - Code review agent
- `agents/debugger.md` - Debug agent
- `agents/feature-verifier.md` - Feature verification agent
- `agents/test-runner.md` - Test execution agent

---

## 📈 Directory Statistics

```
┌──────────────────────────────────────────┐
│  Main Directories Count: 16              │
│  Configuration Files: 10+                │
│  Language Mix: Python + Go               │
│  AI Integration: BAML + Agents           │
└──────────────────────────────────────────┘
```

**Directory Breakdown by Category:**

| Category | Count | Directories |
|----------|-------|-------------|
| Core Implementation | 3 | `silmari_rlm_act/`, `planning_pipeline/`, `go/` |
| AI/ML Integration | 3 | `baml_src/`, `baml_client/`, `agents/` |
| Infrastructure | 4 | `commands/`, `context_window_array/`, `output/`, `build/` |
| Documentation | 3 | `thoughts/`, `docs/`, `sprints/` |
| Testing | 1 | `tests/` |
| **Total** | **16** | |

---

## 🔍 Hidden/Config Directories

<details>
<summary>Click to expand hidden directories (dot-prefixed)</summary>

These are development and configuration directories not part of the main application structure:

| Directory | Purpose |
|-----------|---------|
| `.agent` | Agent runtime data |
| `.beads` | Beads issue tracking |
| `.claude` | Claude Code configuration |
| `.cursor` | Cursor IDE settings |
| `.git` | Git version control |
| `.hypothesis` | Hypothesis testing framework |
| `.mypy_cache` | MyPy type checker cache |
| `.pytest_cache` | Pytest cache |
| `.rlm-act-checkpoints` | RLM-ACT checkpoints |
| `.ruff_cache` | Ruff linter cache |
| `.silmari` | Silmari system files |
| `.specstory` | Spec story artifacts |
| `.venv` | Python virtual environment |
| `.workflow-checkpoints` | Workflow state |

</details>

---

## 🎨 Project Identity

**Project Name**: Context Engine
**Tagline**: "Autonomous project builder for Claude Code that doesn't forget what it's doing"

**Core Technology Stack:**
- **Languages**: Python (primary), Go (secondary)
- **AI Framework**: BAML (Behavioral AI Markup Language)
- **CLI**: Custom Python-based
- **Containerization**: Docker
- **Testing**: pytest, Hypothesis
- **Type Checking**: MyPy
- **Linting**: Ruff

---

## 📋 Related Research

This is the foundational research document for the project structure. Future research may reference:
- Individual directory deep-dives
- Component interaction patterns
- Build and deployment workflows

---

## ❓ Open Questions

- What is the relationship between `silmari_rlm_act/` and `planning_pipeline/`?
- How does the Go implementation integrate with the Python components?
- What is the purpose of `context_window_array/` in the memory architecture?
- How are the four memory layers (mentioned in README) mapped to directories?

---

**Research Complete** ✅
*For follow-up questions about specific directories or components, please ask!*
