---
date: 2026-01-03T16:00:30-05:00
researcher: maceo
git_commit: 3fa50945ad2f92ff43adcd0d4dce12065679868c
branch: main
repository: silmari-Context-Engine
topic: "Project Structure - Main Directories"
tags: [research, codebase, structure, directories]
status: complete
last_updated: 2026-01-03
last_updated_by: maceo
---

```
┌────────────────────────────────────────────────────────────┐
│        SILMARI CONTEXT ENGINE - PROJECT STRUCTURE          │
│                    Directory Overview                       │
└────────────────────────────────────────────────────────────┘
```

**Date**: 2026-01-03T16:00:30-05:00
**Researcher**: maceo
**Git Commit**: 3fa50945ad2f92ff43adcd0d4dce12065679868c
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📚 Research Question

What is the project structure? List main directories only.

## 🎯 Summary

The silmari-Context-Engine project has a well-organized directory structure with 17 main directories (excluding hidden system directories like `.git`, `.venv`, `.hypothesis`, `.pytest_cache`). The structure is organized into configuration directories, source code modules, documentation, testing infrastructure, and build artifacts.

---

## 📊 Detailed Findings

### Main Directory Structure

| Directory | Purpose | Type |
|-----------|---------|------|
| `planning_pipeline/` | Core planning pipeline module | Source Code |
| `agents/` | Agent configurations and definitions | Source Code |
| `commands/` | Command-line tools and scripts | Source Code |
| `baml_src/` | BAML source files (LLM function definitions) | Source Code |
| `baml_client/` | Generated BAML client code | Build Artifact |
| `tests/` | Test suite | Testing |
| `docs/` | Documentation files | Documentation |
| `thoughts/` | Research notes, plans, and documentation | Documentation |
| `sprints/` | Sprint planning and tracking | Project Management |
| `.agent/` | Claude Agent SDK configuration | Configuration |
| `.beads/` | Beads workflow tracking system | Configuration |
| `.claude/` | Claude Code configuration | Configuration |
| `.cursor/` | Cursor IDE configuration | Configuration |
| `.silmari/` | Silmari oracle configuration | Configuration |
| `.specstory/` | Spec story history tracking | Configuration |
| `.mypy_cache/` | MyPy type checking cache | Build Artifact |
| `.workflow-checkpoints/` | Workflow checkpoint storage | Runtime Data |

---

## 🏗️ Architecture Documentation

### Directory Categories

#### **Source Code (Core Functionality)**
```
├── planning_pipeline/     # Main pipeline implementation
├── agents/               # Agent definitions
├── commands/             # CLI commands
├── baml_src/             # BAML function definitions
└── baml_client/          # Generated BAML client (auto-generated)
```

#### **Testing & Documentation**
```
├── tests/                # Test suite
├── docs/                 # Project documentation
├── thoughts/             # Research, plans, notes
└── sprints/              # Sprint planning
```

#### **Configuration Directories**
```
├── .agent/               # Claude Agent SDK
├── .beads/               # Workflow tracking
├── .claude/              # Claude Code config
├── .cursor/              # Cursor IDE config
├── .silmari/             # Silmari oracle
└── .specstory/           # History tracking
```

#### **Runtime & Build Artifacts**
```
├── .workflow-checkpoints/  # Checkpoint data
└── .mypy_cache/           # Type checking cache
```

---

## 📋 Complete Directory Listing

<details>
<summary><strong>Configuration Directories (6 total)</strong></summary>

| Directory | Description |
|-----------|-------------|
| `.agent/` | Claude Agent SDK memory and configuration |
| `.beads/` | Beads workflow issue tracking system |
| `.claude/` | Claude Code settings and commands |
| `.cursor/` | Cursor IDE rules and commands |
| `.silmari/` | Silmari oracle configuration |
| `.specstory/` | Spec story history and tracking |

</details>

<details>
<summary><strong>Source Code Directories (5 total)</strong></summary>

| Directory | Description |
|-----------|-------------|
| `planning_pipeline/` | Core planning pipeline implementation |
| `agents/` | Agent configurations |
| `commands/` | CLI command scripts |
| `baml_src/` | BAML source files (LLM prompts) |
| `baml_client/` | Auto-generated BAML client code |

</details>

<details>
<summary><strong>Documentation & Testing (4 total)</strong></summary>

| Directory | Description |
|-----------|-------------|
| `tests/` | Test suite for the project |
| `docs/` | Project documentation |
| `thoughts/` | Research notes, plans, findings |
| `sprints/` | Sprint planning and tracking |

</details>

<details>
<summary><strong>Runtime & Build Artifacts (2 total)</strong></summary>

| Directory | Description |
|-----------|-------------|
| `.workflow-checkpoints/` | Checkpoint data storage |
| `.mypy_cache/` | MyPy type checking cache |

</details>

---

## 🔍 Code References

The project structure can be verified by examining:
- Root directory: `/home/maceo/Dev/silmari-Context-Engine/`
- All directories are at the project root level
- Configuration directories use dot-prefix naming convention

---

## 📌 Key Discoveries

| Discovery | Impact | Reference |
|-----------|--------|-----------|
| BAML integration present | Project uses BAML for LLM function definitions | `baml_src/`, `baml_client/` |
| Multiple IDE configurations | Supports both Claude Code and Cursor | `.claude/`, `.cursor/` |
| Comprehensive tooling | Has workflow tracking, history, and oracle systems | `.beads/`, `.silmari/`, `.specstory/` |
| Test infrastructure | Active testing with pytest and mypy | `tests/`, `.mypy_cache/` |

---

## 🔗 Related Research

This is the foundational project structure research. For deeper investigations into specific directories:
- Planning pipeline architecture → `planning_pipeline/` deep dive
- BAML integration details → `baml_src/` and `baml_client/` analysis
- Testing patterns → `tests/` exploration
- Documentation system → `thoughts/` structure research

---

## ❓ Open Questions

None - this is a complete listing of main directories as of commit `3fa5094`.

---

```
╔════════════════════════════════════════════════════════════╗
║  Total Main Directories: 17                                ║
║  Source Code: 5  |  Config: 6  |  Docs/Tests: 4  |  Build: 2  ║
╚════════════════════════════════════════════════════════════╝
```
