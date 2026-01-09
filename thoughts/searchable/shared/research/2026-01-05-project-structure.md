---
date: 2026-01-05T09:18:32-05:00
researcher: maceo
git_commit: 3ffb1f26f6d633ff8f841d0061dfd4d297de0197
branch: main
repository: silmari-Context-Engine
topic: "Project Structure - Main Directories"
tags: [research, codebase, structure, directories]
status: complete
last_updated: 2026-01-05
last_updated_by: maceo
---

# 📁 Research: Project Structure - Main Directories

**Date**: 2026-01-05T09:18:32-05:00
**Researcher**: maceo
**Git Commit**: `3ffb1f26f6d633ff8f841d0061dfd4d297de0197`
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 🎯 Research Question

What is the project structure? List main directories only.

---

## 📊 Summary

The **Context Engine** is an autonomous project builder for Claude Code with a four-layer memory architecture. The project is structured around a Python-based orchestration system with BAML integration, planning pipelines, and persistent memory storage.

**Project Type**: Python application with autonomous agent orchestration
**Primary Language**: Python
**Location**: `/home/maceo/Dev/silmari-Context-Engine`

---

## 📂 Main Directories

### Core Application

| Directory | Purpose | Description |
|-----------|---------|-------------|
| **`silmari_rlm_act/`** | Main Package | Primary application package containing core logic |
| **`planning_pipeline/`** | Planning System | Pipeline for planning and orchestration workflows |
| **`context_window_array/`** | Context Management | Context window array functionality for memory management |

### Configuration & Build

| Directory | Purpose | Description |
|-----------|---------|-------------|
| **`baml_src/`** | BAML Sources | BAML (Boundary Agent Markup Language) source files |
| **`baml_client/`** | BAML Client | Generated BAML client code |
| **`agents/`** | Agent Definitions | Agent configuration and definitions |
| **`commands/`** | CLI Commands | Command-line interface commands |

### Development & Testing

| Directory | Purpose | Description |
|-----------|---------|-------------|
| **`tests/`** | Test Suite | Test files for the application |
| **`docs/`** | Documentation | Project documentation |
| **`sprints/`** | Sprint Tracking | Sprint planning and tracking files |

### Output & Storage

| Directory | Purpose | Description |
|-----------|---------|-------------|
| **`output/`** | Generated Output | Output files from pipeline runs |
| **`thoughts/`** | Research & Notes | Knowledge base and research documents |

---

## 🔧 Configuration Directories

<details>
<summary>Hidden/Configuration Directories (Click to expand)</summary>

| Directory | Purpose |
|-----------|---------|
| `.agent/` | Agent configuration and memory storage |
| `.beads/` | Beads issue tracking system |
| `.claude/` | Claude Code configuration |
| `.silmari/` | Silmari-specific configuration |
| `.workflow-checkpoints/` | Workflow checkpoint storage |
| `.venv/` | Python virtual environment |
| `.git/` | Git version control |
| `.hypothesis/` | Property-based testing data |
| `.mypy_cache/` | MyPy type checking cache |
| `.pytest_cache/` | Pytest cache |
| `.ruff_cache/` | Ruff linter cache |
| `.specstory/` | Spec story configuration |

</details>

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────┐
│           CONTEXT ENGINE STRUCTURE                │
├──────────────────────────────────────────────────┤
│                                                   │
│  Core Application                                 │
│  ├── silmari_rlm_act/     (Main package)         │
│  ├── planning_pipeline/   (Orchestration)        │
│  └── context_window_array/ (Memory)              │
│                                                   │
│  Agent System                                     │
│  ├── agents/              (Definitions)          │
│  ├── baml_src/            (BAML sources)         │
│  └── baml_client/         (Generated code)       │
│                                                   │
│  Storage & Output                                 │
│  ├── .agent/              (Memory layers)        │
│  ├── thoughts/            (Knowledge base)       │
│  └── output/              (Generated files)      │
│                                                   │
└──────────────────────────────────────────────────┘
```

---

## 📄 Key Root Files

| File | Purpose |
|------|---------|
| `orchestrator.py` | Main orchestration script for autonomous loops |
| `loop-runner.py` | Autonomous feature implementation loop |
| `planning_orchestrator.py` | Planning phase orchestration |
| `resume_pipeline.py` | Pipeline resumption logic |
| `CLAUDE.md` | Instructions for Claude Code agent |
| `README.md` | Project overview and quick start guide |
| `feature_list.json` | Atomic features with status tracking |

---

## 🔗 Code References

- [`README.md:1-390`](https://github.com/tha-hammer/silmari-Context-Engine/blob/3ffb1f26f6d633ff8f841d0061dfd4d297de0197/README.md#L1-L390) - Full project documentation
- Root directory listing - 12 main application directories, 13 configuration directories

---

## 🔍 Related Beads Issues

The following open beads issues relate to the project structure and pipeline implementation:

- **silmari-Context-Engine-5t7c** [P1] - TDD: silmari-rlm-act Pipeline Implementation
- **silmari-Context-Engine-t5zd** [P1] - Phase 05: Research Phase
- **silmari-Context-Engine-c0r** [P2] - Python Deterministic Pipeline Control

---

## ✅ Research Completion

This research provides a complete overview of the Context Engine project structure. The codebase is organized into distinct layers for core application logic, agent orchestration, configuration, and knowledge storage, following the four-layer memory architecture described in the README.

For detailed architectural information, see `docs/ARCHITECTURE.md` (referenced but not yet explored).

---

**Research Status**: ✅ Complete
**Next Steps**: Available for follow-up questions about specific directories or components
