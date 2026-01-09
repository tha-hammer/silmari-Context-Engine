---
date: 2026-01-05T10:55:25-05:00
researcher: tha-hammer
git_commit: c2cdc625b868bde2e93168eca99355ee266b55f7
branch: main
repository: silmari-Context-Engine
topic: "Project Structure - Main Directories (Detailed)"
tags: [research, codebase, structure, architecture, detailed]
status: complete
last_updated: 2026-01-05
last_updated_by: tha-hammer
---

# Research: Project Structure - Main Directories (Detailed)

**Date**: 2026-01-05T10:55:25-05:00
**Researcher**: tha-hammer
**Git Commit**: c2cdc625b868bde2e93168eca99355ee266b55f7
**Branch**: main
**Repository**: silmari-Context-Engine

## Research Question
What is the project structure? List main directories only.

## Summary
The silmari-Context-Engine project (also known as Context Engine) is an autonomous project builder for Claude Code that implements a four-layer memory architecture. The codebase is organized into distinct functional areas for source code, testing, documentation, planning, and tooling support. The main directories represent a sophisticated autonomous development system with support for context management, planning pipelines, and agent-based workflows.

## 📊 Main Directory Structure

```
┌─────────────────────────────────────────────────────────────────┐
│              SILMARI-CONTEXT-ENGINE STRUCTURE                   │
└─────────────────────────────────────────────────────────────────┘
```

### 🎯 Core Application Directories

| Directory | Purpose | Key Components |
|-----------|---------|----------------|
| **`silmari_rlm_act/`** | Main source code - Autonomous TDD Pipeline (Research, Learn, Model, Act) | `pipeline.py`, `models.py`, `cli.py`, phases/, context/, checkpoints/ |
| **`planning_pipeline/`** | Python deterministic control for Claude Code planning | `pipeline.py`, `autonomous_loop.py`, `decomposition.py`, `context_generation.py` |
| **`context_window_array/`** | Context Window Array Architecture - Addressable context management | `store.py`, `models.py`, `working_context.py`, `search_index.py`, `batching.py` |

### 🧪 Testing & Quality

| Directory | Purpose |
|-----------|---------|
| **`tests/`** | Root-level test suite for integration and system tests |
| **`silmari_rlm_act/tests/`** | Unit tests for the RLM Act pipeline |
| **`planning_pipeline/tests/`** | Tests for planning pipeline components |
| **`context_window_array/tests/`** | Tests for context management |

### 📚 Documentation & Configuration

| Directory | Purpose |
|-----------|---------|
| **`docs/`** | Project documentation (ARCHITECTURE.md, NATIVE-HOOKS.md) |
| **`agents/`** | Specialized subagent definitions (code-reviewer, debugger, feature-verifier, test-runner) |
| **`commands/`** | Custom slash commands (status, next, verify, debug, spec, blockers, revert) |
| **`sprints/`** | Sprint planning documents (24 sprint files + master plan) |
| **`thoughts/`** | Research notes and searchable documentation (symlinked structure) |

### 🔧 Build & Tooling

| Directory | Purpose |
|-----------|---------|
| **`baml_src/`** | BAML (Boundary Aware ML) source definitions - AI function specifications |
| **`baml_client/`** | Generated BAML client code for AI integration |
| **`.claude/`** | Claude Code configuration (agents/, commands/, hooks/, settings.json) |
| **`.silmari/`** | Silmari-specific workflow and history tracking |
| **`.beads/`** | Beads issue tracking system |

### 📦 Environment & Output

| Directory | Purpose |
|-----------|---------|
| **`.venv/`** | Python virtual environment |
| **`output/`** | Generated outputs and artifacts |
| **`.workflow-checkpoints/`** | Workflow state checkpoints |
| **`__pycache__/`** | Python bytecode cache (root level) |

## Detailed Findings

### 🚀 Core Pipeline Architecture

#### silmari_rlm_act/
The main autonomous TDD pipeline implementation following the Research-Learn-Model-Act pattern.

**Structure:**
- `pipeline.py` - Main RLMActPipeline orchestration (16,658 bytes)
- `models.py` - Core data models: AutonomyMode, PhaseResult, PhaseStatus, PhaseType, PipelineState (13,435 bytes)
- `cli.py` - Command-line interface (8,109 bytes)
- `phases/` - Phase-specific implementations
- `context/` - Context management modules
- `checkpoints/` - Checkpoint handling for resumable workflows

**Key Exports:**
```python
from silmari_rlm_act import (
    AutonomyMode,
    PhaseResult,
    PhaseStatus,
    PhaseType,
    PipelineState,
    RLMActPipeline
)
```

#### planning_pipeline/
Python deterministic control layer for managing Claude Code planning sessions.

**Key Modules:**
- `autonomous_loop.py` - Main autonomous execution loop (32,767 bytes)
- `decomposition.py` - Task decomposition logic (34,550 bytes)
- `context_generation.py` - Context compilation for sessions (25,547 bytes)
- `claude_runner.py` - Claude subprocess management (17,546 bytes)
- `steps.py` - Pipeline step implementations (21,381 bytes)
- `phase_execution/` - Phase-specific execution logic

**Integration Points:**
- BeadsController for issue tracking
- CheckpointManager for resumable workflows
- PropertyGenerator for hypothesis-driven development
- Visualization for pipeline state

#### context_window_array/
Advanced context management system for separating working and implementation LLM contexts.

**Core Components:**
- `store.py` - Context storage and retrieval (12,457 bytes)
- `models.py` - Data models for context items (10,558 bytes)
- `working_context.py` - Working context management (5,394 bytes)
- `search_index.py` - Context search and indexing (9,357 bytes)
- `batching.py` - Task batching system (8,631 bytes)
- `implementation_context.py` - Implementation-specific context (8,520 bytes)

**Key Features:**
- Addressable context management
- Search indexing for quick retrieval
- Task batching for parallel operations
- Exception handling (ContextWindowArrayError, ContextCompressedError)

### 🛠️ Tooling & Integration

#### BAML Integration
**baml_src/** contains AI function specifications using BAML language:
- `functions.baml` - Main function definitions (76,976 bytes - largest file)
- `clients.baml` - AI client configurations (3,817 bytes)
- `types.baml` - Type definitions (12,025 bytes)
- `Gate1SharedClasses.baml` - Shared data structures (2,836 bytes)
- `schema/` - Schema definitions

**baml_client/** - Generated Python client code for interfacing with BAML-defined AI functions

#### Agent System
**agents/** directory contains markdown definitions for specialized subagents:
- `code-reviewer.md` (1,625 bytes) - Code review automation
- `debugger.md` (2,095 bytes) - Error analysis and debugging
- `feature-verifier.md` (2,207 bytes) - End-to-end feature verification
- `test-runner.md` (1,874 bytes) - Test execution and analysis

#### Custom Commands
**commands/** directory provides slash commands for workflow management:
- `status.md` (597 bytes) - Project status check
- `next.md` (1,239 bytes) - Next feature to implement
- `verify.md` (766 bytes) - Feature verification
- `debug.md` (1,563 bytes) - Debug assistance
- `spec.md` (1,087 bytes) - Feature specification
- `blockers.md` (1,506 bytes) - Blocker identification
- `revert.md` (1,302 bytes) - Safe revert operations

### 📋 Planning & Documentation

#### Sprint Planning
**sprints/** contains comprehensive sprint documentation:
- `MASTER_SPRINT_PLAN.md` (11,769 bytes) - Overall sprint strategy
- 24 individual sprint files covering:
  - Database schema (sprint 01)
  - Authentication (sprint 02)
  - API framework (sprint 03)
  - Web UI shell (sprint 04)
  - Memory storage & vector DB (sprints 05-07)
  - Messaging & chat (sprints 09-12)
  - OAuth integrations (sprints 13-15)
  - Search & RAG (sprints 16-17)
  - Task automation (sprint 18)
  - Knowledge management (sprints 19-20)
  - Security & compliance (sprints 21-22)
  - Mobile & performance (sprints 23-24)

#### Thoughts Directory
**thoughts/** is a symlinked structure for searchable documentation:
- `searchable/` - Hard links for full-text search
- `global` → `/home/maceo/thoughts/global` (symlink)
- `maceo` → `/home/maceo/thoughts/repos/silmari-Context-Engine/maceo` (symlink)
- `shared` → `/home/maceo/thoughts/repos/silmari-Context-Engine/shared` (symlink)

This structure enables fast grep-based searches while maintaining logical organization.

### ⚙️ Configuration & Metadata

#### Claude Code Configuration
**.claude/** directory structure:
- `agents/` - Agent definitions for Claude Code
- `commands/` - Slash command definitions
- `hooks/` - Git-style hooks for context injection
- `settings.json` (3,510 bytes) - Claude Code settings

#### Silmari Metadata
**.silmari/** contains:
- `workflow/` - Workflow state tracking
- `history/` - Historical workflow data

#### Beads Issue Tracking
**.beads/** - Local issue tracking system for development workflow

## 🏗️ Architecture Documentation

### Four-Layer Memory Model
As documented in README.md, the project implements a sophisticated context management system:

1. **Working Context** (`context_window_array/working_context.py`) - Current task only, rebuilt each session
2. **Episodic Memory** - Recent decisions and patterns (rolling window)
3. **Semantic Memory** - Project knowledge and architecture (persistent)
4. **Procedural Memory** - What worked/failed (append-only)

### Execution Modes

#### Native Hooks Mode (Interactive)
- Uses `.claude/hooks/` for context injection
- Auto-restores context on `/clear` and `/compact`
- Tracks metrics in `.agent/metrics/`

#### Autonomous Loop Mode
- Orchestrated by `loop-runner.py` and `orchestrator.py`
- Manages `feature_list.json` for atomic feature tracking
- Uses subagents for code review and testing
- Commits with "session: completed {feature_id}" pattern

### Pipeline Flow
```
┌─────────────────────────────────────────────────┐
│ Session Start                                   │
├─────────────────────────────────────────────────┤
│ 1. Compile fresh working context                │
│ 2. Check failure log                            │
│ 3. Look up docs via MCP                         │
│ 4. Implement single feature                     │
│ 5. Run tests (mandatory)                        │
│ 6. Subagent review                              │
│ 7. Update feature_list.json                     │
│ 8. Commit with session marker                   │
│ 9. Exit cleanly                                 │
└─────────────────────────────────────────────────┘
                     ↓
           Loop runner repeats
```

## Code References

### Main Entry Points
- `orchestrator.py:1` - Main orchestrator for new/existing projects (50,256 bytes)
- `loop-runner.py:1` - Autonomous loop execution script (50,339 bytes)
- `planning_orchestrator.py:1` - Planning-specific orchestrator (20,379 bytes)
- `resume_planning.py:1` - Resume interrupted planning sessions (989 bytes)
- `resume_pipeline.py:1` - Resume general pipeline execution (5,912 bytes)

### Setup Scripts
- `install.sh:1` - Installation script (1,897 bytes)
- `setup-native-hooks.sh:1` - Native hooks installation (40,686 bytes)
- `setup-context-engineered.sh:1` - Context engine setup (51,669 bytes)
- `mcp-setup.py:1` - MCP configuration helper (23,349 bytes)

### Docker Support
- `Dockerfile:1` - Container definition (1,771 bytes)
- `docker-compose.yml:1` - Compose configuration (832 bytes)
- `docker-claude.sh:1` - Docker helper script (3,064 bytes)
- `DOCKER-SETUP.md:1` - Docker setup guide (8,084 bytes)

### Configuration Files
- `pytest.ini:1` - Pytest configuration (75 bytes)
- `mypy.ini:1` - MyPy type checking config (317 bytes)
- `.env:1` - Environment variables (1,700 bytes)
- `.gitignore:1` - Git exclusions (258 bytes)

## Historical Context (from thoughts/)

The `thoughts/searchable/` directory contains research documents and notes. The symlinked structure (`global`, `maceo`, `shared`) enables:
- Personal notes in `maceo/` subdirectory
- Shared team documentation in `shared/` subdirectory
- Global cross-project references in `global/` subdirectory
- Fast grep-based searching via hard links in `searchable/`

## Related Research

- `thoughts/research/2026-01-05-project-structure.md` - Earlier overview of project structure (less detailed)
- This research provides enhanced detail including file sizes, component descriptions, and architectural patterns

## Open Questions

None. This research provides a comprehensive overview of the main directory structure as of commit c2cdc625.
