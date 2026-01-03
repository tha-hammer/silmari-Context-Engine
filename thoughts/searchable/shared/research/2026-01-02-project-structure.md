---
date: 2026-01-02T13:25:18-05:00
researcher: claude
git_commit: 15fb65a46be0be1f91ad38e5ccdde4ea6eb4ebb9
branch: main
repository: silmari-Context-Engine
topic: "Project Structure - Main Directories"
tags: [research, codebase, structure, directories]
status: complete
last_updated: 2026-01-02
last_updated_by: claude
---

```
┌─────────────────────────────────────────────────────────────────┐
│            SILMARI CONTEXT ENGINE - PROJECT STRUCTURE           │
│                    Main Directories Overview                    │
│                         2026-01-02                              │
└─────────────────────────────────────────────────────────────────┘
```

# Research: Project Structure - Main Directories

**Date**: 2026-01-02T13:25:18-05:00
**Researcher**: claude
**Git Commit**: `15fb65a46be0be1f91ad38e5ccdde4ea6eb4ebb9`
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📋 Research Question

What is the project structure? List main directories only.

---

## 📊 Summary

The silmari-Context-Engine project contains **23 directories** at the root level, organized into:
- **10 source/application directories** for core functionality
- **13 configuration/hidden directories** for tooling and state

---

## 🎯 Main Directories

### Source Directories

| Directory | Purpose |
|-----------|---------|
| `agents/` | Agent definition files and configurations |
| `baml_client/` | Generated BAML client code (auto-generated) |
| `baml_src/` | BAML source definitions for LLM functions |
| `commands/` | CLI command implementations |
| `docs/` | Documentation files |
| `planning_pipeline/` | Python planning pipeline implementation |
| `sprints/` | Sprint planning and tracking files |
| `tests/` | Test suites and fixtures |
| `thoughts/` | Research documents, notes, and plans |

### Configuration/Tool Directories

| Directory | Purpose |
|-----------|---------|
| `.agent/` | Agent memory and state storage |
| `.beads/` | Beads workflow tracking system |
| `.claude/` | Claude Code configuration and commands |
| `.cursor/` | Cursor IDE configuration |
| `.git/` | Git version control |
| `.hypothesis/` | Hypothesis testing framework data |
| `.mypy_cache/` | MyPy type checking cache |
| `.pytest_cache/` | Pytest cache |
| `.silmari/` | Silmari oracle configuration |
| `.specstory/` | SpecStory history tracking |
| `.venv/` | Python virtual environment |
| `.workflow-checkpoints/` | Workflow checkpoint storage |
| `__pycache__/` | Python bytecode cache |

---

## 📁 Directory Tree (Depth 1)

```
silmari-Context-Engine/
├── agents/              # Agent definitions
├── baml_client/         # Generated BAML client
├── baml_src/            # BAML source files
├── commands/            # CLI commands
├── docs/                # Documentation
├── planning_pipeline/   # Planning pipeline code
├── sprints/             # Sprint tracking
├── tests/               # Test suites
├── thoughts/            # Research & notes
│
├── .agent/              # Agent state
├── .beads/              # Beads workflow
├── .claude/             # Claude Code config
├── .cursor/             # Cursor IDE config
├── .git/                # Git VCS
├── .hypothesis/         # Hypothesis testing
├── .mypy_cache/         # MyPy cache
├── .pytest_cache/       # Pytest cache
├── .silmari/            # Silmari config
├── .specstory/          # SpecStory history
├── .venv/               # Virtual environment
├── .workflow-checkpoints/  # Checkpoints
└── __pycache__/         # Python cache
```

---

## 📈 Key Root Files

| File | Purpose |
|------|---------|
| `orchestrator.py` | Main orchestrator script (50KB) |
| `loop-runner.py` | Loop runner implementation (50KB) |
| `planning_orchestrator.py` | Planning orchestrator (17KB) |
| `resume_pipeline.py` | Pipeline resume functionality |
| `mcp-setup.py` | MCP server setup script |
| `CLAUDE.md` | BAML reference guide for AI agents |
| `README.md` | Project documentation |
| `AGENTS.md` | Agent documentation |

---

## ✅ Code References

- Root directory: `/home/maceo/Dev/silmari-Context-Engine/`
- Source directories: 9 active development directories
- Configuration directories: 13 tool/cache directories

---

*Research completed 2026-01-02*
