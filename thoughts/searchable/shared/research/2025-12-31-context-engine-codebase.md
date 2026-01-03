---
date: 2025-12-31T18:40:33-05:00
researcher: Claude
git_commit: 21d7704070c3ea218db0d13655f562e44dab7f08
branch: main
repository: silmari-Context-Engine
topic: "Complete Codebase Research: Context Engine Architecture and Components"
tags: [research, codebase, context-engine, orchestration, memory-architecture, planning-pipeline]
status: complete
last_updated: 2025-12-31
last_updated_by: Claude
---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                     SILMARI CONTEXT ENGINE                                  │
│                     Codebase Research Document                              │
│                                                                             │
│                     Status: Complete | 2025-12-31                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Research: Complete Codebase Analysis

**Date**: 2025-12-31T18:40:33-05:00
**Researcher**: Claude
**Git Commit**: 21d7704070c3ea218db0d13655f562e44dab7f08
**Branch**: main
**Repository**: silmari-Context-Engine

## Research Question

Comprehensive research of the silmari-Context-Engine codebase to understand its architecture, components, and how they interact.

---

## 📚 Executive Summary

The **Context Engine** is an autonomous project builder for Claude Code that solves the context degradation problem in long-running AI coding sessions. It implements a **four-layer memory architecture** based on cognitive science research, enabling Claude to build complete applications without human intervention.

| Metric | Value |
|--------|-------|
| **Core Python Files** | 3 (orchestrator.py, loop-runner.py, mcp-setup.py) |
| **Planning Pipeline Modules** | 7 Python modules + 6 test modules |
| **Sprint Documents** | 24 sprints across 7 phases |
| **Requirements Tracked** | 4,939 total (for Tanka AI project) |
| **Agent Definitions** | 4 root-level + 6 .claude agents |
| **Command Definitions** | 7 root-level + 17 .claude commands |

### Key Capabilities

```
┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│   Native Hooks     │     │  Autonomous Loop   │     │ Planning Pipeline  │
│   (Interactive)    │     │   (Unattended)     │     │  (Deterministic)   │
├────────────────────┤     ├────────────────────┤     ├────────────────────┤
│ • Context inject   │     │ • Feature-by-      │     │ • Research phase   │
│ • Pre-compact save │     │   feature build    │     │ • Plan generation  │
│ • Progress track   │     │ • Test validation  │     │ • Phase decomp     │
│ • Activity logging │     │ • Subagent review  │     │ • Beads integration│
└────────────────────┘     └────────────────────┘     └────────────────────┘
```

---

## 📊 Detailed Findings

### 1. Four-Layer Memory Architecture

The core innovation of Context Engine is its hierarchical memory system:

```
┌─────────────────────────────────────────────────────────────────┐
│                    WORKING CONTEXT                              │
│              (Rebuilt fresh each session)                       │
│                                                                 │
│  Current feature + relevant memory + recent patterns            │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ compile
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   EPISODIC    │   │    SEMANTIC     │   │   PROCEDURAL    │
│    MEMORY     │   │     MEMORY      │   │     MEMORY      │
├───────────────┤   ├─────────────────┤   ├─────────────────┤
│ Recent events │   │ Project facts   │   │ What worked     │
│ Decisions     │   │ Architecture    │   │ What failed     │
│ Patterns      │   │ Dependencies    │   │ Solutions       │
│               │   │ Conventions     │   │                 │
│ Rolling 10    │   │ Persistent      │   │ Append-only     │
└───────────────┘   └─────────────────┘   └─────────────────┘
```

| Layer | Purpose | Storage | Lifecycle |
|-------|---------|---------|-----------|
| **Working Context** | Current task focus | `.agent/working-context/` | Rebuilt each session |
| **Episodic Memory** | Recent decisions | `.agent/memory/episodes/` | Rolling window |
| **Semantic Memory** | Project knowledge | `.agent/memory/semantic/` | Persistent |
| **Procedural Memory** | Success/failure patterns | `.agent/memory/procedures/` | Append-only |

**Key Insight**: Context is *computed*, not *accumulated*. Each session starts fresh with exactly what it needs.

**File Reference**: `docs/ARCHITECTURE.md:17-56`

---

### 2. Python Orchestration System

#### 2.1 orchestrator.py (1,366 lines)

The main entry point for autonomous project building.

<details>
<summary>Core Components</summary>

| Component | Lines | Purpose |
|-----------|-------|---------|
| Feature Complexity Detection | 36-143 | Analyzes features for high/medium/low complexity |
| MCP Setup | 175-291 | Interactive Model Context Protocol configuration |
| Project Setup | 293-407 | Creates project directory and initializes harness |
| Feature Tracking | 417-502 | Manages feature_list.json state |
| Claude Integration | 504-1093 | Subprocess execution of Claude Code CLI |
| Session Logging | 1095-1128 | JSON and text logging of session results |
| Main Orchestration | 1129-1273 | New project and implementation workflows |

</details>

**Key Functions**:
- `build_init_prompt()` - Generates initialization instructions (`orchestrator.py:508-559`)
- `build_implement_prompt()` - Creates feature implementation prompts (`orchestrator.py:786-874`)
- `run_claude_code_interactive()` - Interactive Claude execution (`orchestrator.py:962-1093`)
- `orchestrate_implementation()` - Main autonomous loop (`orchestrator.py:1171-1245`)

**Complexity-Driven Workflow**:
- **High complexity**: All 3 subagents required (@code-reviewer, @test-runner, @feature-verifier)
- **Medium complexity**: Only @test-runner required
- **Low complexity**: Direct implementation, no subagent review

#### 2.2 loop-runner.py (1,380 lines)

Autonomous feature implementation loop for unattended operation.

<details>
<summary>Core Components</summary>

| Component | Lines | Purpose |
|-----------|-------|---------|
| Validation | 40-148 | Feature list schema validation, circular dependency detection |
| Dependency Management | 154-209 | Topological sort using Kahn's algorithm |
| Blocking Workflow | 215-298 | Mark/unblock features with metadata |
| Metrics & Artifacts | 304-342 | Hook-based tracking and session diffs |
| Feature Selection | 562-651 | Next feature algorithm with dependency checks |
| QA Prompts | 675-957 | Lite and full QA testing prompts |
| Session Execution | 959-1084 | Claude Code subprocess management |

</details>

**Feature Selection Algorithm** (`loop-runner.py:586-625`):
1. Load and parse `feature_list.json`
2. Identify completed feature IDs
3. Topological sort respecting dependencies
4. Filter: skip completed, blocked, unmet dependencies
5. Return first eligible feature

**Failure Recovery**:
- Consecutive failure counter (max 3 before user intervention)
- Auto-complete when tests pass but feature not marked
- Git history sync to recover missed updates

---

### 3. Planning Pipeline (Python TDD Implementation)

A deterministic, multi-step planning system in `planning_pipeline/`.

```
planning_pipeline/
├── __init__.py              # Package exports
├── pipeline.py              # Main PlanningPipeline class
├── steps.py                 # Individual step implementations
├── checkpoints.py           # Interactive user feedback
├── helpers.py               # Text parsing utilities
├── beads_controller.py      # Beads CLI wrapper
├── claude_runner.py         # Claude subprocess wrapper
└── tests/                   # 14-behavior TDD test suite
    ├── test_helpers.py      # Behaviors 1-3
    ├── test_beads.py        # Behaviors 4-6
    ├── test_claude.py       # Behavior 7
    ├── test_steps.py        # Behaviors 8-11
    ├── test_checkpoints.py  # Behaviors 12-13
    └── test_pipeline.py     # Behavior 14 (E2E)
```

**Pipeline Flow**:
```
╔═════════════════╗     ╔═════════════════╗     ╔═════════════════╗
║  Step 1:        ║     ║  Step 2:        ║     ║  Step 3:        ║
║  Research       ║────▶║  Planning       ║────▶║  Phase          ║
║  (Claude)       ║     ║  (+ feedback)   ║     ║  Decomposition  ║
╚═════════════════╝     ╚═════════════════╝     ╚═════════════════╝
                                                        │
╔═════════════════╗     ╔═════════════════╗             │
║  Step 5:        ║◀────║  Step 4:        ║◀────────────┘
║  Memory         ║     ║  Beads          ║
║  Capture        ║     ║  Integration    ║
╚═════════════════╝     ╚═════════════════╝
```

**Key Files**:
- `pipeline.py:27-157` - Main `run()` method orchestrating all steps
- `steps.py:174-234` - `step_beads_integration()` creates epic and phase issues
- `beads_controller.py:52-91` - Python wrapper for `bd` CLI commands

---

### 4. Sprint Planning System (Tanka AI)

The `sprints/` directory contains a comprehensive 24-sprint roadmap for building Tanka AI.

| Phase | Sprints | Focus | Testable Outcome |
|-------|---------|-------|------------------|
| **1. Foundation** | 1-4 | Database, Auth, API, UI | User can register and login |
| **2. Memory** | 5-8 | Storage, Vector DB, Search | User can create and search memories |
| **3. Communication** | 9-12 | Messaging, AI Chat, Groups | Users can chat with AI and each other |
| **4. Business Tools** | 13-16 | OAuth, Google, Microsoft | Connected account data visible |
| **5. AI Enhancement** | 17-20 | RAG, Automation, Docs | Context-aware AI responses |
| **6. Enterprise** | 21-22 | RBAC, Audit | Compliance and security |
| **7. Mobile & Scale** | 23-24 | Mobile App, Performance | Mobile functional, load tested |

**Requirements Distribution**:
- 4,939 total requirements (4,851 functional, 88 usability)
- 320 parent requirements → 947 sub-process → 3,584 implementation
- Organized into 701 requirement groups

**Key Dependencies**:
- Sprint 01 (Database) → All other sprints
- Sprint 03 (Celery/Redis) → Sprints 05, 06, 07, 10
- Sprint 09 (WebSocket) → Sprints 10, 11, 12
- Sprint 13 (OAuth) → Sprints 14, 15

**File Reference**: `sprints/MASTER_SPRINT_PLAN.md:1-298`

---

### 5. Agent and Command System

#### Root-Level Agents (`/agents/`)

| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| `@code-reviewer` | opus | Read, Grep, Glob, Bash | Reviews for quality, security, performance |
| `@test-runner` | opus | Read, Edit, Bash, Grep, Glob | Runs tests, analyzes and fixes failures |
| `@debugger` | opus | Read, Edit, Bash, Grep, Glob | Diagnoses errors with systematic approach |
| `@feature-verifier` | opus | Read, Bash, Grep, Glob | End-to-end verification for real users |

#### Root-Level Commands (`/commands/`)

| Command | Purpose |
|---------|---------|
| `/spec` | Display and analyze application specification |
| `/debug` | Collect diagnostics and analyze issues |
| `/status` | Show project progress and git state |
| `/blockers` | List blocked features and dependencies |
| `/verify` | Run tests, build, lint, health checks |
| `/revert` | Revert to last known good state (destructive) |
| `/next` | Find highest priority incomplete feature |

#### .claude Agents (`.claude/agents/`)

| Agent | Model | Purpose |
|-------|-------|---------|
| `codebase-analyzer` | sonnet | Documents implementation details without critique |
| `codebase-locator` | sonnet | Finds files and components by description |
| `codebase-pattern-finder` | sonnet | Finds similar implementations and examples |
| `thoughts-locator` | sonnet | Discovers relevant thoughts documents |
| `thoughts-analyzer` | sonnet | Extracts insights from specific documents |
| `web-search-researcher` | sonnet | Conducts web research with sources |

#### .claude Commands (`.claude/commands/`)

17 commands including:
- `create_plan.md` - Interactive implementation planning
- `implement_plan.md` - Plan execution
- `debug.md` - Debugging with beads integration
- `commit.md` - Commit automation
- `describe_pr.md` - PR description generation
- `create_handoff.md` - Session handoff documents

---

### 6. Native Hooks System

Four Python hooks integrate with Claude Code's lifecycle events:

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  SessionStart    │     │   PreCompact     │     │      Stop        │
│  Hook            │     │   Hook           │     │      Hook        │
├──────────────────┤     ├──────────────────┤     ├──────────────────┤
│ • Compile context│     │ • Save snapshot  │     │ • Track progress │
│ • Inject to      │     │ • Log to JSONL   │     │ • Log metrics    │
│   session        │     │ • Cleanup old    │     │ • Auto-complete  │
│ • Priority-based │     │   snapshots      │     │   (write mode)   │
│   truncation     │     │                  │     │                  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                                         │
                         ┌──────────────────┐            │
                         │  PostToolUse     │◀───────────┘
                         │  Hook            │
                         ├──────────────────┤
                         │ • Log Write/Edit │
                         │ • Activity JSONL │
                         └──────────────────┘
```

**Configuration**:
- `MAX_CONTEXT_CHARS = 6000` - Hard limit for context injection
- `MAX_SNAPSHOTS = 10` - Retained pre-compact snapshots
- `CONTEXT_ENGINE_WRITE_MODE=1` - Enables auto-completion

**File References**:
- `setup-native-hooks.sh:197-448` - session-start.py implementation
- `setup-native-hooks.sh:454-578` - pre-compact.py implementation
- `docs/NATIVE-HOOKS.md` - User documentation

---

### 7. Project Directory Structure

```
silmari-Context-Engine/
├── orchestrator.py          # Main autonomous project builder
├── loop-runner.py           # Autonomous feature loop
├── mcp-setup.py             # MCP configuration utility
├── setup-native-hooks.sh    # Native hooks installer
├── setup-context-engineered.sh  # Full architecture setup
├── install.sh               # Global installer
│
├── agents/                  # Root-level subagent definitions
│   ├── code-reviewer.md
│   ├── test-runner.md
│   ├── debugger.md
│   └── feature-verifier.md
│
├── commands/                # Root-level slash commands
│   ├── spec.md, debug.md, status.md, blockers.md
│   ├── verify.md, revert.md, next.md
│
├── docs/
│   ├── ARCHITECTURE.md      # Four-layer memory documentation
│   └── NATIVE-HOOKS.md      # Hooks system guide
│
├── sprints/                 # Tanka AI sprint planning
│   ├── MASTER_SPRINT_PLAN.md
│   └── sprint_01-24_*.md
│
├── planning_pipeline/       # Python deterministic pipeline
│   ├── pipeline.py, steps.py, checkpoints.py
│   ├── helpers.py, beads_controller.py, claude_runner.py
│   └── tests/
│
├── .claude/                 # Claude Code configuration
│   ├── settings.json        # Hooks and permissions
│   ├── agents/              # 6 specialized agents
│   └── commands/            # 17 workflow commands
│
├── .beads/                  # Issue tracking data
│
└── thoughts/                # Knowledge base
    ├── shared/research/     # Team research documents
    └── global/              # Cross-repository thoughts
```

---

## 🎯 Architecture Patterns

### Pattern 1: Computed Context
Each session starts fresh with context *computed* from memory layers, not accumulated from previous sessions.

### Pattern 2: Complexity-Driven Workflow
Features are classified by complexity, which determines:
- Required subagent review depth
- MCP documentation lookup requirements
- Test verification rigor

### Pattern 3: Git-Based State Recovery
The system reconciles `feature_list.json` with git commit history to recover from missed updates.

### Pattern 4: Subprocess Isolation
Claude Code runs in isolated subprocesses with:
- Timeout protection (1 hour default)
- Captured stdout/stderr for parsing
- Structured error handling

### Pattern 5: Priority-Based Truncation
Context sections have priority scores (60-100). Low-priority sections are removed first to stay within limits.

---

## 📁 Code References

### Core Files

| File | Lines | Purpose |
|------|-------|---------|
| `orchestrator.py:1-1366` | 1,366 | Main autonomous builder |
| `loop-runner.py:1-1380` | 1,380 | Feature implementation loop |
| `setup-native-hooks.sh:1-1200` | 1,200 | Native hooks installer |
| `setup-context-engineered.sh:1-1300` | 1,300 | Full architecture setup |
| `docs/ARCHITECTURE.md:1-238` | 238 | Memory architecture docs |
| `planning_pipeline/pipeline.py:1-158` | 158 | Planning pipeline class |

### Key Functions

| Function | Location | Purpose |
|----------|----------|---------|
| `get_feature_complexity()` | `orchestrator.py:39-101` | Analyze feature complexity |
| `build_implement_prompt()` | `orchestrator.py:786-874` | Generate implementation prompt |
| `topological_sort_features()` | `loop-runner.py:154-209` | Sort by dependencies |
| `get_next_feature()` | `loop-runner.py:586-625` | Select next eligible feature |
| `step_beads_integration()` | `steps.py:174-234` | Create beads issues |

---

## 🔗 Related Beads Issues

Currently open issues in this repository:

| ID | Type | Priority | Title |
|----|------|----------|-------|
| `silmari-Context-Engine-c0r` | epic | P2 | Python Deterministic Pipeline Control |
| `silmari-Context-Engine-umo` | task | P2 | Phase 1: Helper Functions (Behaviors 1-3) |
| `silmari-Context-Engine-evo` | task | P2 | Phase 2: BeadsController (Behaviors 4-6) |
| `silmari-Context-Engine-0br` | task | P2 | Phase 3: Claude Runner (Behavior 7) |
| `silmari-Context-Engine-2x3` | task | P2 | Phase 4: Pipeline Steps (Behaviors 8-11) |
| `silmari-Context-Engine-8jk` | task | P2 | Phase 5: Interactive Checkpoints (Behaviors 12-13) |
| `silmari-Context-Engine-eb4` | task | P2 | Phase 6: Full Pipeline E2E (Behavior 14) |

---

## ❓ Open Questions

1. **Relationship between Context Engine and silmari-oracle**: The `.claude/commands/` reference `silmari-oracle` CLI tool which is not part of this repository. What is the integration pattern?

2. **Sprint execution status**: The 24 sprints are defined but what is the actual implementation status of Tanka AI?

3. **Planning pipeline integration**: How does `planning_pipeline/` integrate with the main orchestrator workflow?

---

## 📖 Historical Context (from thoughts/)

### Research Documents Found

| Path | Purpose |
|------|---------|
| `thoughts/shared/research/2025-12-31-planning-command-architecture.md` | Research on planning command architecture |
| `thoughts/global/README.md` | Global thoughts directory documentation |

The thoughts/ directory is in early stages with:
- 1 research document (dated 2025-12-31)
- Placeholder directories for future content
- Structure supports shared team research and global cross-repository thoughts

---

## ✅ Summary

The Context Engine is a sophisticated system for autonomous AI-driven software development that:

1. **Solves context degradation** through a four-layer memory architecture
2. **Enables unattended builds** via orchestrator.py and loop-runner.py
3. **Supports interactive sessions** through native hooks
4. **Provides deterministic planning** via the planning_pipeline module
5. **Tracks 4,939 requirements** across 24 sprints for Tanka AI
6. **Integrates with Claude Code** through agents, commands, and hooks

The architecture is research-backed (MemGPT, Stanford Generative Agents, Anthropic) and has demonstrated success building 61 features for a Rust API server without human intervention.
