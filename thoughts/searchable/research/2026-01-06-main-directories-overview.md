---
date: 2026-01-06T07:27:18-05:00
researcher: maceo
git_commit: b4a02e30983242d0fcda527ff3ad47eb38d7c478
branch: main
repository: silmari-Context-Engine
topic: "Project Structure - Main Directories"
tags: [research, codebase, project-structure, directory-layout]
status: complete
last_updated: 2026-01-06
last_updated_by: maceo
---

```
┌─────────────────────────────────────────────────────────────┐
│         CONTEXT ENGINE - PROJECT STRUCTURE RESEARCH         │
│                    Main Directory Layout                     │
└─────────────────────────────────────────────────────────────┘
```

# Research: Project Structure - Main Directories

**Date**: 2026-01-06T07:27:18-05:00
**Researcher**: maceo
**Git Commit**: `b4a02e30983242d0fcda527ff3ad47eb38d7c478`
**Branch**: main
**Repository**: silmari-Context-Engine

## Research Question

What is the project structure? List main directories only.

## Summary

The **Context Engine** is an autonomous project builder for Claude Code featuring a four-layer memory architecture. The project contains 24 main directories organized into five functional categories: Core Application, Configuration & Memory, Development & Testing, Build & Output, and Supporting Tools.

The project uses Python as the primary language with additional Go components, BAML for LLM prompt definitions, and various shell scripts for automation and setup.

## 📊 Main Directory Structure

### 🚀 Core Application Directories

| Directory | Purpose | Type |
|-----------|---------|------|
| `silmari_rlm_act/` | Main Python package implementing the core RLM/ACT system with agents, CLI, context management, phases, and pipeline | Python Package |
| `planning_pipeline/` | Planning pipeline implementation for autonomous feature planning | Python Module |
| `context_window_array/` | Context window management system | Python Module |
| `baml_src/` | BAML source files - DSL for defining type-safe LLM prompts as functions | BAML Source |
| `baml_client/` | Auto-generated client code from BAML definitions (created by `baml-cli generate`) | Generated Code |
| `go/` | Go language components and implementations | Go Package |
| `agents/` | Agent definitions and configurations | Config/Python |
| `commands/` | CLI command implementations | Python |

### ⚙️ Configuration & Memory Directories

| Directory | Purpose | Type |
|-----------|---------|------|
| `.agent/` | Agent memory storage (`memory.db`) and working context for runtime state | Database/Config |
| `.claude/` | Claude Code configuration and settings | Config |
| `.silmari/` | Silmari-specific configuration files | Config |
| `.beads/` | Beads issue tracking system storage | Database |
| `thoughts/` | Documentation, research, and knowledge base (symlinks to global thoughts system) | Documentation |

### 🧪 Development & Testing Directories

| Directory | Purpose | Type |
|-----------|---------|------|
| `tests/` | Test files for the project | Python Tests |
| `docs/` | Project documentation including architecture guides and setup instructions | Markdown Docs |
| `sprints/` | Sprint planning and tracking | Documentation |

### 📦 Build & Output Directories

| Directory | Purpose | Type |
|-----------|---------|------|
| `build/` | Build artifacts and compiled outputs | Build Output |
| `output/` | Generated outputs from runs and sessions | Generated Files |
| `.workflow-checkpoints/` | Workflow execution checkpoints for resumability | Checkpoints |
| `.rlm-act-checkpoints/` | RLM/ACT specific execution checkpoints | Checkpoints |

### 🔧 Supporting Tools & Cache Directories

| Directory | Purpose | Type |
|-----------|---------|------|
| `.venv/` | Python virtual environment | Python Venv |
| `__pycache__/` | Python bytecode cache | Cache |
| `.mypy_cache/` | MyPy type checking cache | Cache |
| `.ruff_cache/` | Ruff linter cache | Cache |
| `.pytest_cache/` | Pytest test cache | Cache |
| `.hypothesis/` | Hypothesis property testing data | Test Data |
| `.specstory/` | SpecStory test framework data | Test Data |
| `.git/` | Git version control metadata | Git |
| `.cursor/` | Cursor IDE configuration | IDE Config |

## 📝 Detailed Findings

### Core Application Structure

**`silmari_rlm_act/`** - The main Python package containing:
- `agents/` - Agent implementations
- `cli.py` - Command-line interface (13.4KB)
- `commands/` - CLI command handlers
- `context/` - Context management
- `hooks/` - Extension hooks
- `models.py` - Data models (17.5KB)
- `phases/` - Pipeline phases
- `pipeline.py` - Main pipeline orchestration (17.5KB)
- `checkpoints/` - Checkpoint management
- `tests/` - Package tests

**`planning_pipeline/`** - Autonomous planning system for breaking down features into implementation steps.

**`baml_src/` & `baml_client/`** - BAML (Basically, A Made-Up Language) integration:
- `baml_src/` contains type-safe LLM prompt definitions
- `baml_client/` is auto-generated (must run `baml-cli generate` after changes)
- Provides strongly-typed inputs/outputs for LLM calls
- Includes Jinja-based prompt templating

### Configuration & Memory Architecture

**`.agent/`** - Agent memory system:
- `memory.db` - SQLite database (40KB) storing persistent knowledge
- `working-context/` - Ephemeral context rebuilt each session
- Implements the four-layer memory model: Working Context, Episodic Memory, Semantic Memory, Procedural Memory

**`thoughts/`** - Knowledge management:
- Symlinked structure to global thoughts system
- `global/` → `/home/maceo/thoughts/global`
- `maceo/` → `/home/maceo/thoughts/repos/silmari-Context-Engine/maceo`
- `shared/` → `/home/maceo/thoughts/repos/silmari-Context-Engine/shared`
- `searchable/` - Hard links for search indexing (contains `research/` subdirectory)

### Key Root Files

| File | Purpose | Size |
|------|---------|------|
| `orchestrator.py` | Main orchestrator for project initialization and continuation | 50KB |
| `loop-runner.py` | Autonomous loop runner for unattended feature implementation | 50KB |
| `planning_orchestrator.py` | Planning-specific orchestration | 20KB |
| `setup-native-hooks.sh` | Native hooks mode setup for interactive Claude Code use | 41KB |
| `setup-context-engineered.sh` | Context-engineered harness setup | 52KB |
| `mcp-setup.py` | MCP (Model Context Protocol) configuration | 23KB |
| `docker-claude.sh` | Docker wrapper for Claude Code | 3KB |
| `install.sh` | Installation script | 2KB |
| `README.md` | Main project documentation | 12KB |
| `CLAUDE.md` | BAML reference guide for AI agents | 28KB |

## 🎯 Project Organization Patterns

### Two Operating Modes
The directory structure supports two distinct modes mentioned in the README:

1. **Native Hooks Mode** (Interactive)
   - Uses `.claude/` configuration
   - Hooks inject context on session start
   - Saves snapshots before `/compact`
   - Restores context after `/clear`

2. **Autonomous Loop** (Unattended)
   - Uses `orchestrator.py` and `loop-runner.py`
   - `.agent/` directory for memory persistence
   - `.workflow-checkpoints/` and `.rlm-act-checkpoints/` for resumability

### Memory Architecture
The directory structure reflects the four-layer memory model:
- **Working Context**: `.agent/working-context/` (rebuilt each session)
- **Episodic Memory**: `.agent/memory.db` (recent decisions)
- **Semantic Memory**: `.agent/memory.db` (project knowledge)
- **Procedural Memory**: `.agent/memory.db` (what worked/failed)

## 📚 Code References

- Root structure: `ls -la` output showing 24 main directories
- `.agent/memory.db` - 40KB SQLite database
- `silmari_rlm_act/` - Main package with 10 subdirectories
- `thoughts/searchable/` - Hard-linked directory for search

## 🏗️ Architecture Documentation

**Language Distribution:**
- **Python**: Primary language (`.py` files, `__pycache__/`, `.venv/`)
- **Go**: Secondary language (`go/`, `go.mod`, `go.sum`)
- **BAML**: LLM prompt DSL (`baml_src/`, `baml_client/`)
- **Shell**: Automation scripts (`.sh` files)
- **Markdown**: Documentation (`.md` files)

**Build & Development Tools:**
- Python: pytest, mypy, ruff, hypothesis
- Go: Go modules
- Docker: `Dockerfile`, `docker-compose.yml`, `docker-claude.sh`
- Git: Version control with hooks

**Configuration Files:**
- `.env` - Environment variables
- `.gitignore` - Git ignore patterns
- `.dockerignore` - Docker ignore patterns
- `pytest.ini` - Pytest configuration
- `mypy.ini` - MyPy type checking configuration

## Related Research

This research complements existing project structure documentation:
- `2026-01-06-project-structure.md` - Detailed structure analysis
- `2026-01-06-project-structure-main-directories.md` - Directory overview
- `2026-01-06-project-structure-directory-listing.md` - Comprehensive listing

## Open Questions

For future research:
1. How does the memory.db schema support the four-layer memory model?
2. What is the relationship between `silmari_rlm_act/` and the root-level scripts?
3. How does the planning pipeline integrate with the main orchestrator?
4. What are the specific agents defined in `agents/` and `silmari_rlm_act/agents/`?
5. How does the checkpoint system enable resumability?

---

**Note**: This research documents the directory structure as it exists. For implementation details and architecture deep dives, see the project's `docs/ARCHITECTURE.md` (referenced in README but not yet explored).
