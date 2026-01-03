---
date: 2025-12-31T15:45:00+00:00
researcher: Claude
git_commit: 21d7704070c3ea218db0d13655f562e44dab7f08
branch: main
repository: silmari-Context-Engine
topic: "Complete Codebase Architecture Research"
tags: [research, codebase, architecture, memory-system, orchestration, commands, agents]
status: complete
last_updated: 2025-12-31
last_updated_by: Claude
---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                    🧠 CONTEXT ENGINE CODEBASE RESEARCH                      │
│                                                                             │
│                  Autonomous Project Builder for Claude Code                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Date**: 2025-12-31T15:45:00+00:00
**Researcher**: Claude
**Git Commit**: 21d7704070c3ea218db0d13655f562e44dab7f08
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📚 Research Question

Comprehensive documentation of the silmari-Context-Engine codebase - its architecture, components, and how they interact.

---

## 🎯 Executive Summary

The **Context Engine** is an autonomous project builder for Claude Code that prevents context degradation during long-running coding sessions. It implements a **four-layer memory architecture** based on research from Google ADK, Stanford ACE, and Anthropic to maintain coherence across sessions.

| Metric | Value |
|--------|-------|
| **Core Scripts** | 4 Python/Bash orchestration files |
| **Memory Layers** | 4 (Working Context, Sessions, Memory, Artifacts) |
| **Commands** | 20+ slash commands across `.claude/` and `commands/` |
| **Agents** | 10 specialized agents for review, testing, research |
| **Sprint Roadmap** | 24 sprints, 4,939 requirements for "Tanka AI" |
| **Deployment Modes** | 2 (Native Hooks for interactive, Autonomous Loop) |

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERACTION                                   │
│                                                                             │
│     ┌──────────────────┐              ┌──────────────────────────┐         │
│     │  Native Hooks    │              │   Autonomous Loop        │         │
│     │  (Interactive)   │              │   (Unattended)           │         │
│     └────────┬─────────┘              └───────────┬──────────────┘         │
│              │                                    │                         │
│              ▼                                    ▼                         │
│     setup-native-hooks.sh              orchestrator.py + loop-runner.py    │
│              │                                    │                         │
└──────────────┼────────────────────────────────────┼─────────────────────────┘
               │                                    │
               ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FOUR-LAYER MEMORY ARCHITECTURE                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ LAYER 1: WORKING CONTEXT (.agent/working-context/)                   │   │
│  │ • Computed fresh each session • 8000 token cap • Current task only  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ▲ compile-context.sh                           │
│        ┌─────────────────────┼─────────────────────┐                       │
│        ▼                     ▼                     ▼                        │
│  ┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐             │
│  │   LAYER 2     │   │    LAYER 3      │   │    LAYER 4      │             │
│  │   Sessions    │   │    Memory       │   │   Artifacts     │             │
│  ├───────────────┤   ├─────────────────┤   ├─────────────────┤             │
│  │ Full event    │   │ strategies/     │   │ tool-outputs/   │             │
│  │ log (JSONL)   │   │ failures/       │   │ documents/      │             │
│  │ snapshots/    │   │ constraints/    │   │ code-snapshots/ │             │
│  └───────────────┘   └─────────────────┘   └─────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             CLAUDE CODE CLI                                  │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Commands    │  │   Agents     │  │    MCPs      │  │    Hooks     │    │
│  │  /commit     │  │  @reviewer   │  │  Ref (docs)  │  │  SessionStart│    │
│  │  /create_plan│  │  @test-runner│  │  Postgres    │  │  PreCompact  │    │
│  │  /research   │  │  @debugger   │  │  Fetch       │  │  Stop        │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Core Components

### 1. Orchestration Scripts

| Script | Purpose | Location |
|--------|---------|----------|
| `orchestrator.py` | Project initialization, session management | `orchestrator.py:1-1366` |
| `loop-runner.py` | Autonomous feature implementation loop | `loop-runner.py:1-1381` |
| `install.sh` | System-wide installation to `~/tools/context-engine` | `install.sh:1-59` |
| `cli.js` | Bundled Claude Code CLI (4.4MB) | `cli.js` |

<details>
<summary><strong>orchestrator.py Key Functions</strong></summary>

| Function | Lines | Purpose |
|----------|-------|---------|
| `get_feature_complexity()` | 39-101 | Detects high/medium/low complexity |
| `get_subagent_instructions()` | 103-142 | Generates subagent invocation steps |
| `setup_mcps_interactive()` | 175-291 | Interactive MCP configuration |
| `get_project_info_interactive()` | 322-407 | Collects project details |
| `build_init_prompt()` | 508-559 | Creates initialization instructions |
| `build_implement_prompt()` | 786-874 | Creates implementation instructions |
| `run_claude_code_interactive()` | 962-1093 | Executes Claude Code session |
| `orchestrate_implementation()` | 1171-1245 | Main feature loop |

</details>

<details>
<summary><strong>loop-runner.py Key Functions</strong></summary>

| Function | Lines | Purpose |
|----------|-------|---------|
| `validate_feature_list()` | 40-106 | Schema validation |
| `detect_circular_dependencies()` | 108-148 | DFS cycle detection |
| `topological_sort_features()` | 154-209 | Kahn's algorithm ordering |
| `mark_feature_blocked()` | 215-241 | Blocking metadata |
| `run_session()` | 959-1084 | Single session execution |
| `verify_session_result()` | 499-519 | Independent test verification |

</details>

---

### 2. Four-Layer Memory Architecture

```
╔═════════════════════════════════════════════════════════════════════════════╗
║                              MEMORY LAYERS                                   ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  🔴 LAYER 1: Working Context                                                ║
║  ├── Location: .agent/working-context/current.md                            ║
║  ├── Lifecycle: Destroyed and rebuilt each session                          ║
║  ├── Token Cap: 8000 tokens (configurable)                                  ║
║  └── Contents: Current task + relevant memory + recent patterns             ║
║                                                                             ║
║  🟡 LAYER 2: Sessions                                                        ║
║  ├── Location: .agent/sessions/                                             ║
║  ├── Lifecycle: Persistent, grows over time                                 ║
║  ├── Format: JSONL (one JSON object per line)                               ║
║  └── Contents: Full event log, snapshots, activity                          ║
║                                                                             ║
║  🟢 LAYER 3: Memory                                                          ║
║  ├── Location: .agent/memory/{strategies,failures,constraints,entities}/    ║
║  ├── Lifecycle: Persistent, updated when patterns change                    ║
║  ├── Format: Markdown files with YAML frontmatter                           ║
║  └── Contents: What worked, what failed, active rules                       ║
║                                                                             ║
║  🔵 LAYER 4: Artifacts                                                       ║
║  ├── Location: .agent/artifacts/{tool-outputs,documents,code-snapshots}/    ║
║  ├── Lifecycle: Persistent, referenced not included                         ║
║  └── Contents: Large outputs stored by reference                            ║
║                                                                             ║
╚═════════════════════════════════════════════════════════════════════════════╝
```

**Key Principle**: Context is **computed**, not **accumulated**. Each session starts with exactly what it needs.

---

### 3. Native Hooks System

| Hook | Fires When | Script | Purpose |
|------|------------|--------|---------|
| `SessionStart` | Startup, resume, after `/clear` | `.claude/hooks/session-start.py` | Injects compiled context |
| `PreCompact` | Before `/compact` | `.claude/hooks/pre-compact.py` | Saves snapshot |
| `Stop` | Claude completes response | `.claude/hooks/stop.py` | Tracks metrics |
| `PostToolUse` | After Write/Edit/MultiEdit | `.claude/hooks/post-tool-use.py` | Logs activity |

**Priority-Based Truncation** (when over 6000 char limit):

| Section | Priority | Behavior |
|---------|----------|----------|
| Header | 100 | Always keep |
| Current Task | 90 | Critical |
| Constraints | 80 | Important |
| Failures | 70 | Important |
| Commands | 65 | Important |
| Strategies | 60 | Expendable first |

---

### 4. Planning Pipeline (New)

The `planning_pipeline/` directory implements a 5-step TDD-driven planning workflow:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PLANNING PIPELINE FLOW                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Step 1: Research ──► Step 2: Planning ──► Step 3: Decompose  │
│        │                     │                    │             │
│        ▼                     ▼                    ▼             │
│   thoughts/shared/     thoughts/shared/     Phase files:        │
│   research/*.md        plans/*.md           00-overview.md      │
│                                             01-phase-1.md       │
│                                             02-phase-2.md       │
│                                                                 │
│   Step 4: Beads Integration ──► Step 5: Memory Capture          │
│        │                              │                         │
│        ▼                              ▼                         │
│   Creates epic + tasks           Records constraints            │
│   Links dependencies             Stores artifacts               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

| Module | Purpose | Location |
|--------|---------|----------|
| `pipeline.py` | Main orchestration class | `planning_pipeline/pipeline.py:12-158` |
| `steps.py` | Step implementations | `planning_pipeline/steps.py` |
| `checkpoints.py` | Interactive user prompts | `planning_pipeline/checkpoints.py` |
| `beads_controller.py` | Beads CLI wrapper | `planning_pipeline/beads_controller.py` |
| `claude_runner.py` | Claude subprocess wrapper | `planning_pipeline/claude_runner.py` |

---

### 5. Commands Catalog

<details>
<summary><strong>Root Commands (commands/*.md)</strong></summary>

| Command | Purpose |
|---------|---------|
| `/spec` | Display and analyze application specification |
| `/debug` | Debug current project issues |
| `/status` | Show current project status |
| `/blockers` | Show blocked features and dependencies |
| `/verify` | Verify project is in working state |
| `/revert` | Revert to last known good state |
| `/next` | Find next feature to implement |

</details>

<details>
<summary><strong>Claude Commands (.claude/commands/*.md)</strong></summary>

| Command | Purpose | Key Features |
|---------|---------|--------------|
| `/commit` | Create git commits | Imperative mood, no co-author |
| `/create_plan` | Create implementation plans | Parallel research agents, phases |
| `/create_tdd_plan` | Create TDD plans | Given/When/Then, Red-Green-Refactor |
| `/implement_plan` | Implement approved plans | Checkbox updates, success criteria |
| `/implement_plan_with_checkpoints` | Enhanced implementation | Git checkpoints for recovery |
| `/research_codebase` | Comprehensive research | Parallel sub-agents, no critiques |
| `/plan_with_memory` | Planning with memory integration | 4-layer architecture, beads |
| `/describe_pr` | Generate PR descriptions | Template-based, auto-updates |
| `/create_handoff` | Create handoff documents | YAML frontmatter, artifacts |
| `/resume_handoff` | Resume from handoffs | Parallel verification |
| `/validate_plan` | Validate implementation | Deviation detection |
| `/documentation` | Generate How-to Guides | Diátaxis framework |
| `/reference_documentation` | Generate Reference docs | Austere, factual style |
| `/debug` | Debug issues | Read-only investigation |
| `/local_review` | Set up review environment | Worktree creation |
| `/founder_mode` | Quick experimental features | Cherry-pick + PR |
| `/create_worktree` | Set up worktree | silmari-oracle integration |

</details>

---

### 6. Agents Catalog

| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| **codebase-analyzer** | sonnet | Read, Grep, Glob, LS | Document HOW code works |
| **codebase-locator** | sonnet | Grep, Glob, LS | Find WHERE files live |
| **codebase-pattern-finder** | sonnet | Grep, Glob, Read, LS | Find similar implementations |
| **thoughts-locator** | sonnet | Grep, Glob, LS | Find documents in thoughts/ |
| **thoughts-analyzer** | sonnet | Read, Grep, Glob, LS | Extract insights from docs |
| **web-search-researcher** | sonnet | WebSearch, WebFetch, etc. | External research |
| **code-reviewer** | opus | Read, Bash, Grep, Glob | Code quality review |
| **test-runner** | opus | Read, Edit, Bash, Grep, Glob | Test automation |
| **feature-verifier** | opus | Read, Bash, Grep, Glob | E2E verification |
| **debugger** | opus | Read, Edit, Bash, Grep, Glob | Root cause analysis |

**Philosophy Split**:
- **Documentation agents** (codebase-*, thoughts-*): Document AS IT EXISTS - no suggestions
- **Quality agents** (code-reviewer, test-runner, etc.): Proactive verification and fixing

---

### 7. Sprint Roadmap (Tanka AI)

The `sprints/` directory contains a 24-sprint roadmap for building "Tanka AI" - an AI-powered business messenger.

```
╔═════════════════════════════════════════════════════════════════════════════╗
║                         TANKA AI DEVELOPMENT ROADMAP                         ║
║                        4,939 Requirements • 24 Sprints                       ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  PHASE 1: Foundation (Sprints 1-4) ✅ Validated                             ║
║  ├── Sprint 01: Database & Schema                                           ║
║  ├── Sprint 02: Authentication Core                                         ║
║  ├── Sprint 03: API Framework + Celery                                      ║
║  └── Sprint 04: Web UI Shell                                                ║
║                                                                             ║
║  PHASE 2: Memory System (Sprints 5-8) ✅ Validated                          ║
║  ├── Sprint 05: Memory Storage Core                                         ║
║  ├── Sprint 06: Vector Database + Embeddings                                ║
║  ├── Sprint 07: Memory Ingestion Pipeline                                   ║
║  └── Sprint 08: Memory Search UI                                            ║
║                                                                             ║
║  PHASE 3: Communication (Sprints 9-12) ✅ Validated                         ║
║  ├── Sprint 09: Direct Messaging + WebSocket                                ║
║  ├── Sprint 10: AI Chat Interface                                           ║
║  ├── Sprint 11: Group Channels                                              ║
║  └── Sprint 12: Chat Memory Integration                                     ║
║                                                                             ║
║  PHASE 4: Business Tools (Sprints 13-16) 📋 Defined                         ║
║  ├── Sprint 13: OAuth Integration Framework                                 ║
║  ├── Sprint 14: Google Workspace Integration                                ║
║  ├── Sprint 15: Microsoft 365 Integration                                   ║
║  └── Sprint 16: Unified Search                                              ║
║                                                                             ║
║  PHASE 5: AI Enhancement (Sprints 17-20) 📋 Defined                         ║
║  ├── Sprint 17: RAG Implementation                                          ║
║  ├── Sprint 18: Task Automation                                             ║
║  ├── Sprint 19: Document Generation                                         ║
║  └── Sprint 20: Knowledge Extraction                                        ║
║                                                                             ║
║  PHASE 6: Enterprise (Sprints 21-22) 📋 Defined                             ║
║  ├── Sprint 21: RBAC & Permissions                                          ║
║  └── Sprint 22: Audit & Compliance                                          ║
║                                                                             ║
║  PHASE 7: Mobile & Scale (Sprints 23-24) 📋 Defined                         ║
║  ├── Sprint 23: Mobile App MVP                                              ║
║  └── Sprint 24: Performance & Scaling                                       ║
║                                                                             ║
╚═════════════════════════════════════════════════════════════════════════════╝
```

---

### 8. Beads Integration

The project uses `bd` (beads) for local issue tracking:

| Command | Purpose |
|---------|---------|
| `bd ready` | Find available work (no blockers) |
| `bd create --title="..." --type=task --priority=2` | Create issue |
| `bd update <id> --status=in_progress` | Claim work |
| `bd close <id>` | Mark complete |
| `bd dep add <issue> <depends-on>` | Link dependencies |
| `bd sync` | Sync with git |

**Current Open Issues** (from session start):
- `silmari-Context-Engine-c0r` - Python Deterministic Pipeline Control (epic)
- Phases 1-6 for TDD Python Pipeline implementation

---

## 📁 Directory Structure

```
silmari-Context-Engine/
├── 📜 Core Scripts
│   ├── orchestrator.py          # Project initialization + management
│   ├── loop-runner.py           # Autonomous session loop
│   ├── cli.js                   # Claude Code CLI (bundled)
│   └── install.sh               # System-wide installer
│
├── 🔧 Setup Scripts
│   ├── setup-native-hooks.sh    # Interactive mode setup
│   ├── setup-context-engineered.sh  # Autonomous mode setup
│   └── mcp-setup.py             # MCP configuration wizard
│
├── 📂 planning_pipeline/        # TDD planning workflow
│   ├── pipeline.py              # Orchestration
│   ├── steps.py                 # Step implementations
│   ├── checkpoints.py           # User prompts
│   ├── beads_controller.py      # Beads CLI wrapper
│   ├── claude_runner.py         # Claude subprocess
│   ├── helpers.py               # Text extraction
│   └── tests/                   # Test coverage
│
├── 📂 agents/                   # Quality agents
│   ├── code-reviewer.md
│   ├── test-runner.md
│   ├── feature-verifier.md
│   └── debugger.md
│
├── 📂 commands/                 # Simple workflow commands
│   ├── spec.md, debug.md, status.md
│   ├── blockers.md, verify.md, revert.md
│   └── next.md
│
├── 📂 .claude/                  # Claude Code configuration
│   ├── commands/                # 20+ slash commands
│   ├── agents/                  # 6 research/analysis agents
│   └── hooks/                   # Native hook scripts (generated)
│
├── 📂 sprints/                  # Tanka AI roadmap
│   ├── MASTER_SPRINT_PLAN.md
│   └── sprint_01..sprint_24.md
│
├── 📂 docs/
│   ├── ARCHITECTURE.md          # Memory architecture docs
│   └── NATIVE-HOOKS.md          # Native hooks docs
│
├── 📂 thoughts/                 # Research & notes
│   └── shared/research/         # Research documents
│
├── 📂 .beads/                   # Local issue tracking
│   └── issues.jsonl
│
└── 📂 .agent/                   # Generated by setup (gitignored parts)
    ├── working-context/
    ├── sessions/
    ├── memory/
    ├── artifacts/
    ├── hooks/
    └── workflows/
```

---

## 🔄 Data Flow

### Interactive Mode (Native Hooks)

```
1. User runs: claude
2. SessionStart hook fires
3. session-start.py compiles context from memory layers
4. Context injected via additionalContext
5. User works normally
6. PostToolUse hook logs file operations
7. User runs /clear or /compact
8. PreCompact saves snapshot (if /compact)
9. SessionStart recompiles fresh context
10. Stop hook tracks metrics when Claude finishes
```

### Autonomous Mode (Loop Runner)

```
1. User runs: loop-runner.py ~/project --model opus
2. validate_feature_list() checks schema
3. topological_sort_features() orders by dependencies
4. Main loop:
   a. sync_features_with_git() fixes JSON/git mismatches
   b. get_next_feature() finds work
   c. get_feature_complexity() determines subagent needs
   d. run_session() builds prompt and executes Claude
   e. verify_session_result() runs tests independently
   f. Auto-marks complete if tests pass
   g. track_metrics() logs events
   h. Pause 3 seconds, repeat
5. Loop exits when all features complete or max sessions
```

---

## 📋 Code References

| Component | Key Files |
|-----------|-----------|
| **Orchestration** | `orchestrator.py:1279-1366` (CLI), `loop-runner.py:959-1084` (session) |
| **Memory Architecture** | `setup-context-engineered.sh:20-34` (structure), `docs/ARCHITECTURE.md` |
| **Context Compilation** | `setup-context-engineered.sh:166-301`, `session-start.py:301-409` |
| **Hooks** | `setup-native-hooks.sh:197-863` (creation), `.claude/settings.json` (config) |
| **Commands** | `.claude/commands/*.md` (20+ files) |
| **Agents** | `.claude/agents/*.md` (6 files), `agents/*.md` (4 files) |
| **Planning Pipeline** | `planning_pipeline/pipeline.py:27-157` (main flow) |
| **Sprint Roadmap** | `sprints/MASTER_SPRINT_PLAN.md` |

---

## 🏗️ Historical Context

From `thoughts/shared/research/2025-12-31-planning-command-architecture.md`:

- The `/plan_with_memory` command was designed to fully integrate with the 4-layer memory architecture
- Commands chain together: research → planning → implementation
- Beads integration provides persistent issue tracking across sessions
- The planning pipeline (`planning_pipeline/`) implements these concepts in Python

---

## ✅ Key Takeaways

1. **Context is Computed, Not Accumulated** - Each session starts fresh with exactly what's needed
2. **Four Layers Separate Concerns** - Working context, sessions, memory, artifacts serve different purposes
3. **Two Deployment Modes** - Native hooks for interactive, autonomous loop for unattended
4. **Specialized Agents** - Documentation agents describe, quality agents verify and fix
5. **Commands Are Workflows** - Slash commands orchestrate complex multi-step processes
6. **Beads for Persistence** - Local issue tracking survives session boundaries
7. **Sprint Roadmap Exists** - 24 sprints define Tanka AI development (separate product)

---

## 🔍 Open Questions

1. **Planning Pipeline Integration** - Currently standalone; not yet integrated with main orchestration
2. **Sprint Roadmap Relationship** - Tanka AI sprints vs Context Engine development unclear
3. **Memory.db** - File exists but unused; memory uses markdown files instead
