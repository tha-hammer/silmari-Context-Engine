---
date: 2026-01-10 08:47:15 -05:00
researcher: tha-hammer
git_commit: 92cb760fdd2f79330506075b9390ca496dfca439
branch: main
repository: silmari-Context-Engine
topic: "What is the project structure? List main directories only."
tags: [research, codebase, project-structure, directories]
status: complete
last_updated: 2026-01-10
last_updated_by: tha-hammer
---

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│              CONTEXT ENGINE PROJECT STRUCTURE                │
│          Autonomous Project Builder for Claude Code         │
│                                                              │
└──────────────────────────────────────────────────────────────┘

Status: ✅ Complete
Date: 2026-01-10 08:47:15 -05:00
```

# Research: Project Structure - Main Directories

**Date**: 2026-01-10 08:47:15 -05:00
**Researcher**: tha-hammer
**Git Commit**: `92cb760fdd2f79330506075b9390ca496dfca439`
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📋 Research Question

What is the project structure? List main directories only.

---

## 📊 Summary

The **Context Engine** is an autonomous project builder for Claude Code that maintains a four-layer memory architecture. The project is organized into 15 main directories, each serving a specific purpose in the system's architecture. The codebase is primarily Python-based with some Go components, and includes comprehensive testing, documentation, and planning infrastructure.

---

## 🎯 Main Directories

<details>
<summary><strong>Click to expand detailed directory listing</strong></summary>

| Directory | Purpose | Type |
|-----------|---------|------|
| `agents/` | Specialized subagents for autonomous operations | Core |
| `baml_client/` | Generated BAML client code | Generated |
| `baml_src/` | BAML source definitions | Config |
| `build/` | Build artifacts and compiled outputs | Generated |
| `commands/` | Custom command implementations | Core |
| `context_window_array/` | Context window management components | Core |
| `docs/` | Project documentation | Documentation |
| `go/` | Go language components | Core |
| `output/` | Runtime output and artifacts | Runtime |
| `planning_pipeline/` | Planning and orchestration pipeline | Core |
| `silmari_rlm_act/` | RL-based action model components | Core |
| `sprints/` | Sprint planning and tracking | Process |
| `tests/` | Test suites and test infrastructure | Testing |
| `thoughts/` | Research documents and knowledge base | Documentation |
| `__pycache__/` | Python bytecode cache | Generated |

</details>

---

## 🚀 Core System Directories

### 🧠 **Memory & Context Management**
```
context_window_array/    # Context window management
silmari_rlm_act/         # RL-based action model
```

### 🤖 **Agent Infrastructure**
```
agents/                  # Specialized subagents (@code-reviewer, @test-runner, etc.)
commands/                # Custom command implementations
```

### 📋 **Planning & Orchestration**
```
planning_pipeline/       # Planning and orchestration pipeline
sprints/                 # Sprint planning and tracking
```

---

## 🛠️ **Development Infrastructure**

### 🧪 Testing
```
tests/                   # Comprehensive test suites
```

### 📚 Documentation
```
docs/                    # Technical documentation
thoughts/                # Research documents and knowledge base
```

### 🏗️ Build & Output
```
build/                   # Build artifacts
output/                  # Runtime outputs
__pycache__/            # Python bytecode cache (auto-generated)
```

---

## 🔧 Configuration & Integration

### 🌐 BAML Integration
```
baml_src/               # BAML source definitions
baml_client/            # Generated BAML client code
```

### 🐹 Go Components
```
go/                     # Go language components and modules
```

---

## 📁 Directory Tree Overview

```
silmari-Context-Engine/
│
├── 🤖 Agent Systems
│   ├── agents/                     # Subagents (@code-reviewer, @test-runner)
│   ├── commands/                   # Custom commands
│   └── silmari_rlm_act/           # RL-based action model
│
├── 🧠 Memory & Context
│   └── context_window_array/      # Context window management
│
├── 📋 Planning & Orchestration
│   ├── planning_pipeline/         # Planning pipeline
│   └── sprints/                   # Sprint tracking
│
├── 🔧 Configuration & Integration
│   ├── baml_src/                  # BAML source definitions
│   ├── baml_client/               # Generated BAML client
│   └── go/                        # Go components
│
├── 🧪 Testing & Documentation
│   ├── tests/                     # Test suites
│   ├── docs/                      # Technical docs
│   └── thoughts/                  # Research & knowledge base
│
└── 🏗️ Build & Runtime
    ├── build/                     # Build artifacts
    ├── output/                    # Runtime outputs
    └── __pycache__/              # Python cache (auto-generated)
```

---

## 🔍 Additional Context

### Project Overview
From the README, this is the **Context Engine** - an autonomous project builder for Claude Code that uses a four-layer memory architecture:

| Layer | Purpose | Lifecycle |
|-------|---------|-----------|
| **Working Context** | Current task only | Rebuilt each session |
| **Episodic Memory** | Recent decisions, patterns | Rolling window |
| **Semantic Memory** | Project knowledge, architecture | Persistent |
| **Procedural Memory** | What worked, what failed | Append-only |

### Key Features
- ✅ Autonomous feature implementation
- ✅ Persistent memory across sessions
- ✅ Subagent review system
- ✅ MCP integration for documentation lookup
- ✅ Test enforcement
- ✅ Git-based progress tracking

---

## 📌 Code References

- Root directory listing: `/home/maceo/Dev/silmari-Context-Engine/`
- All directories are at the project root level
- Total of 15 main directories (excluding hidden directories like `.git`, `.venv`, etc.)

---

## 🏗️ Architecture Documentation

The project follows a modular architecture with clear separation of concerns:

1. **Agent Layer**: Specialized subagents handle specific tasks (code review, testing, debugging)
2. **Memory Layer**: Context window and RL-based components manage state
3. **Planning Layer**: Pipeline and sprint systems orchestrate work
4. **Integration Layer**: BAML and Go components provide external integrations
5. **Infrastructure Layer**: Tests, docs, and build systems support development

---

## 📚 Related Documentation

Based on the README, additional documentation exists in:
- `docs/ARCHITECTURE.md` - Four-layer memory model details
- `docs/NATIVE-HOOKS.md` - Native hooks mode documentation
- `.agent/` directories in projects - Memory model and workflows

---

## ✅ Completion Notes

This research provides a high-level overview of the main directories in the Context Engine project. Each directory serves a specific purpose in the autonomous project building system, from agent orchestration to memory management to testing infrastructure.

The project demonstrates a well-organized structure that supports both autonomous operation (via loop-runner.py) and interactive development (via native hooks mode).
