---
date: 2026-01-04 14:54:02 -05:00
researcher: maceo
git_commit: df5cf66a25f56c27090dda4e3fc6c639f57a213a
branch: main
repository: silmari-Context-Engine
topic: "Project Structure - Main Directories"
tags: [research, codebase, structure, architecture]
status: complete
last_updated: 2026-01-04
last_updated_by: maceo
---

```
┌─────────────────────────────────────────────────────────────┐
│         SILMARI CONTEXT ENGINE - PROJECT STRUCTURE          │
│                    Directory Overview                        │
└─────────────────────────────────────────────────────────────┘
```

**Date**: 2026-01-04 14:54:02 -05:00
**Researcher**: maceo
**Git Commit**: df5cf66a25f56c27090dda4e3fc6c639f57a213a
**Branch**: main
**Repository**: silmari-Context-Engine

## Research Question

What is the project structure? List main directories only.

## Summary

The **Silmari Context Engine** is an autonomous project builder for Claude Code that implements a four-layer memory architecture to prevent context degradation during long coding sessions. The project structure is organized into several key areas:

- **Core orchestration** (planning_pipeline, root scripts)
- **AI agent definitions** (agents)
- **Type-safe LLM integration** (baml_src, baml_client)
- **Project automation** (commands)
- **Documentation and memory** (docs, thoughts)
- **Testing** (tests)
- **Configuration** (various dotfile directories)

## 📊 Main Directory Structure

The project contains **11 main application directories** plus several configuration and build directories:

### 🎯 Core Application Directories

| Directory | Purpose | Key Contents |
|-----------|---------|--------------|
| **agents/** | Specialized subagent definitions | code-reviewer, test-runner, feature-verifier, debugger |
| **planning_pipeline/** | Autonomous task planning and execution | orchestrator, step decomposition, checkpoints, BAML integration |
| **commands/** | CLI command definitions | blockers, debug, next, revert, spec, status, verify |
| **baml_src/** | BAML type definitions (input) | LLM function definitions, types, clients |
| **baml_client/** | Generated BAML client code (output) | Auto-generated from baml_src |
| **tests/** | Test suite | Unit and integration tests |
| **docs/** | Project documentation | Architecture, guides, references |
| **thoughts/** | Research and planning documents | Searchable knowledge base |
| **sprints/** | Sprint planning and tracking | Feature lists, milestones |

### 🛠️ Root-Level Orchestration Scripts

| Script | Purpose | Mode |
|--------|---------|------|
| **orchestrator.py** | Main autonomous loop orchestrator | Autonomous |
| **loop-runner.py** | Continuous feature implementation loop | Autonomous |
| **planning_orchestrator.py** | Planning-focused orchestrator | Planning |
| **resume_pipeline.py** | Resume interrupted workflows | Recovery |
| **resume_planning.py** | Resume planning sessions | Planning |

### ⚙️ Configuration Directories

<details>
<summary>Click to expand configuration directories</summary>

| Directory | Purpose |
|-----------|---------|
| **.agent/** | Agent runtime configuration and memory |
| **.claude/** | Claude Code settings and agents |
| **.cursor/** | Cursor IDE configuration |
| **.silmari/** | Silmari-specific metadata |
| **.beads/** | Beads workflow tracking |
| **.specstory/** | Specification stories |
| **.workflow-checkpoints/** | Workflow checkpoint data |
| **.git/** | Git version control |

</details>

### 🏗️ Build and Cache Directories

<details>
<summary>Click to expand build/cache directories</summary>

| Directory | Purpose |
|-----------|---------|
| **__pycache__/** | Python bytecode cache |
| **.pytest_cache/** | Pytest cache |
| **.mypy_cache/** | MyPy type checker cache |
| **.hypothesis/** | Hypothesis testing cache |
| **.venv/** | Python virtual environment |

</details>

## 📚 Detailed Findings

### Core Orchestration Layer

The project uses a multi-tier orchestration approach:

1. **planning_pipeline/** - The main pipeline module containing:
   - `integrated_orchestrator.py` - Unified orchestration logic
   - `autonomous_loop.py` - Autonomous execution loop
   - `step_decomposition.py` - Breaks down tasks into steps
   - `beads_controller.py` - Integration with Beads workflow system
   - `checkpoint_manager.py` - Checkpoint management
   - `claude_runner.py` - Claude API interaction
   - `models.py` - Data models
   - `pipeline.py` - Pipeline coordination
   - `property_generator.py` - Property generation
   - `visualization.py` - Visualization utilities

2. **Root scripts** provide entry points:
   - `orchestrator.py` - Legacy/main orchestrator (50KB)
   - `loop-runner.py` - Autonomous feature loop (50KB)
   - `planning_orchestrator.py` - Planning-focused variant (20KB)

### Agent System

**agents/** directory contains specialized subagent definitions that Claude Code can invoke:

| Agent | File | Purpose |
|-------|------|---------|
| **Code Reviewer** | code-reviewer.md | Reviews code changes for issues |
| **Test Runner** | test-runner.md | Runs tests and analyzes failures |
| **Feature Verifier** | feature-verifier.md | End-to-end feature verification |
| **Debugger** | debugger.md | Analyzes errors and suggests fixes |

### BAML Integration (Type-Safe LLM)

The project uses **BAML** (Basically, A Made-Up Language) for type-safe LLM interactions:

- **baml_src/** - Source definitions (inputs written by developers)
- **baml_client/** - Generated client code (outputs, auto-generated)

BAML provides:
- Strongly-typed inputs/outputs for LLM calls
- Automatic JSON parsing and validation
- Jinja-based prompt templating
- Multi-language code generation

### Command System

**commands/** directory contains CLI command definitions:

| Command | File | Purpose |
|---------|------|---------|
| blockers | blockers.md | Show blocking issues |
| debug | debug.md | Debug commands |
| next | next.md | Get next task |
| revert | revert.md | Revert operations |
| spec | spec.md | Specification commands |
| status | status.md | Project status |
| verify | verify.md | Verification commands |

### Documentation and Memory

Two documentation systems:

1. **docs/** - Formal project documentation
2. **thoughts/** - Research, planning, and searchable knowledge base
   - Contains hard links for efficient searching
   - Organized by date and topic
   - Used for context recovery and decision tracking

## 🏗️ Architecture Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    Entry Point Layer                         │
│  orchestrator.py │ loop-runner.py │ planning_orchestrator.py│
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Core Pipeline Layer                          │
│              planning_pipeline/ module                       │
│  • Integrated orchestrator                                   │
│  • Autonomous loop                                           │
│  • Step decomposition                                        │
│  • Checkpoint management                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌────────────┐  ┌────────────┐  ┌────────────┐
│   BAML     │  │  Agents    │  │  Commands  │
│ Type-Safe  │  │ Subagents  │  │   CLI      │
│    LLM     │  │            │  │            │
└────────────┘  └────────────┘  └────────────┘
         │               │               │
         └───────────────┴───────────────┘
                         │
                         ▼
               ┌─────────────────┐
               │  Documentation  │
               │  docs/ thoughts/│
               └─────────────────┘
```

## 📝 Code References

Key entry points and modules:

- `orchestrator.py:1` - Main autonomous orchestrator (50,339 bytes)
- `loop-runner.py:1` - Continuous feature loop (50,339 bytes)
- `planning_orchestrator.py:1` - Planning variant (20,274 bytes)
- `planning_pipeline/integrated_orchestrator.py` - Core orchestration logic
- `planning_pipeline/step_decomposition.py` - Task decomposition
- `planning_pipeline/autonomous_loop.py` - Loop implementation
- `agents/code-reviewer.md` - Code review agent definition
- `agents/test-runner.md` - Test runner agent definition
- `baml_src/` - BAML type definitions (source)
- `baml_client/` - Generated BAML client (auto-generated)

## 🎯 Project Purpose

From the README, this is an **autonomous project builder for Claude Code** that:

1. **Prevents context degradation** during long coding sessions
2. **Implements four-layer memory architecture**:
   - Working Context (current task, rebuilt each session)
   - Episodic Memory (recent decisions, rolling window)
   - Semantic Memory (project knowledge, persistent)
   - Procedural Memory (what worked/failed, append-only)
3. **Enables fully autonomous building** (example: built 61 features overnight)
4. **Supports two modes**:
   - **Native Hooks Mode**: Interactive coding with persistent context
   - **Autonomous Loop Mode**: Unattended feature implementation

## 🔄 Session Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Session Start                                               │
├─────────────────────────────────────────────────────────────┤
│ 1. Compile fresh working context                            │
│    └─ Pull relevant memory, not everything                  │
│ 2. Check failure log                                        │
│    └─ Don't repeat past mistakes                            │
│ 3. Look up docs via MCP (Ref, Context7)                     │
│ 4. Implement single feature                                 │
│ 5. Run tests (mandatory)                                    │
│ 6. Subagent review (@code-reviewer, @test-runner)           │
│ 7. Update feature_list.json                                 │
│ 8. Commit with "session: completed {feature_id}"            │
│ 9. Exit cleanly                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    Loop runner starts next session
```

## 📦 External Dependencies

Key setup scripts:

- **install.sh** - Main installation script
- **setup-native-hooks.sh** - Sets up interactive hooks mode
- **setup-context-engineered.sh** - Sets up autonomous mode
- **mcp-setup.py** - MCP (Model Context Protocol) configuration

Configuration examples:

- **mcp-config.example.json** - Example MCP configuration
- **.env** - Environment variables

## 🧪 Testing Infrastructure

The **tests/** directory contains:
- Unit tests
- Integration tests
- Configuration: `pytest.ini`, `mypy.ini`

## 📖 Documentation Files

Root-level documentation:

- **README.md** - Main project documentation (11,686 bytes)
- **CLAUDE.md** - BAML reference guide for AI agents (27,995 bytes)
- **AGENTS.md** - Agent system documentation
- **PROMPT.md** - Prompt engineering guidance
- **CONTRIBUTING.md** - Contribution guidelines
- **LICENSE** - MIT License

## Related Research

This is the initial structural overview. Future research documents may explore:
- Planning pipeline architecture
- BAML integration patterns
- Agent system design
- Checkpoint and recovery mechanisms
- Memory architecture implementation

## Open Questions

- How does the planning_pipeline integrate with the root orchestrators?
- What is the relationship between planning_orchestrator.py and orchestrator.py?
- How do checkpoints work across sessions?
- What is the beads workflow system and how does it integrate?
