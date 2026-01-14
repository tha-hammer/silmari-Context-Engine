---
date: 2026-01-14 14:57:23 -05:00
researcher: tha-hammer
git_commit: 068f4c45f4898ff293e39e8bbffea0c3152d4225
branch: main
repository: silmari-Context-Engine
topic: "Project Structure - Main Directories"
tags: [research, codebase, structure, architecture, directories]
status: complete
last_updated: 2026-01-14
last_updated_by: tha-hammer
---

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│           SILMARI CONTEXT ENGINE PROJECT STRUCTURE          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

# Research: Project Structure - Main Directories

**Date**: 2026-01-14 14:57:23 -05:00
**Researcher**: tha-hammer
**Git Commit**: `068f4c45f4898ff293e39e8bbffea0c3152d4225`
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📋 Research Question

What is the project structure? List main directories only.

---

## 🎯 Summary

The Silmari Context Engine is a **hybrid Python/Go system** for autonomous AI-driven task management, featuring phase-based execution, context window management, and BAML-driven prompt engineering. The project is organized into **13 main directories** with clear separation between:

- **Core orchestration** (`silmari_rlm_act/`, `planning_pipeline/`)
- **Performance-critical components** (`go/`)
- **AI prompt management** (`baml_src/`, `baml_client/`)
- **Context management** (`context_window_array/`)
- **Configuration and documentation** (`agents/`, `commands/`, `docs/`)
- **Output and research** (`output/`, `thoughts/`)

The architecture follows a **modular phase-based design** with checkpoint/resume capabilities for long-running operations.

---

## 📊 Detailed Findings

### 🏗️ Core Application Directories

<table>
<tr>
<th>Directory</th>
<th>Purpose</th>
<th>Key Contents</th>
<th>Size/Complexity</th>
</tr>
<tr>
<td><strong>silmari_rlm_act/</strong></td>
<td>Core RLM (Recursive Loop Management) ACT (Agent Context Tool) system - main orchestration framework</td>
<td>
• <code>phases/</code> - Phase execution modules<br>
• <code>tests/</code> - Test suite<br>
• <code>agents/</code> - Agent definitions<br>
• <code>commands/</code> - Command implementations<br>
• <code>context/</code> - Context management<br>
• <code>checkpoints/</code> - Checkpoint management<br>
• <code>hooks/</code> - Hook implementations<br>
• <code>validation/</code> - Validation logic
</td>
<td>Large Python package<br>~27KB pipeline.py<br>~13KB models.py</td>
</tr>
<tr>
<td><strong>planning_pipeline/</strong></td>
<td>Autonomous planning loop, decomposition, and step execution for AI-driven task breakdown</td>
<td>
• <code>autonomous_loop.py</code> (32KB)<br>
• <code>decomposition.py</code> (35KB)<br>
• <code>claude_runner.py</code> (35KB)<br>
• <code>context_generation.py</code> (25KB)<br>
• <code>steps.py</code> (21KB)<br>
• <code>phase_execution/</code> subdirectory
</td>
<td>Substantial Python modules<br>~160KB total code</td>
</tr>
<tr>
<td><strong>go/</strong></td>
<td>Go implementation of context engine and loop-runner executables for performance</td>
<td>
• <code>cmd/</code> - context-engine, loop-runner<br>
• <code>internal/</code> - cli, models, planning, concurrent, exec, fs, json, paths<br>
• <code>build/</code> - Compiled binaries (darwin, linux, windows)
</td>
<td>Multi-platform Go project<br>Native executables</td>
</tr>
</table>

---

### 🤖 AI & Prompt Management

<table>
<tr>
<th>Directory</th>
<th>Purpose</th>
<th>Key Contents</th>
</tr>
<tr>
<td><strong>baml_src/</strong></td>
<td>BAML (Boundary Language) function and type definitions for AI prompt engineering</td>
<td>
• <code>functions.baml</code> (78KB)<br>
• <code>types.baml</code> (12KB)<br>
• <code>clients.baml</code><br>
• <code>generators.baml</code>
</td>
</tr>
<tr>
<td><strong>baml_client/</strong></td>
<td>Auto-generated client code from BAML definitions</td>
<td>Generated Python code</td>
</tr>
<tr>
<td><strong>context_window_array/</strong></td>
<td>Context window management, batching, and storage for managing AI token limits</td>
<td>
• <code>batching.py</code><br>
• <code>implementation_context.py</code><br>
• <code>models.py</code><br>
• <code>search_index.py</code><br>
• <code>store.py</code><br>
• <code>working_context.py</code>
</td>
</tr>
</table>

---

### ⚙️ Configuration & Specifications

<table>
<tr>
<th>Directory</th>
<th>Purpose</th>
<th>Contents</th>
</tr>
<tr>
<td><strong>agents/</strong></td>
<td>Markdown specifications for agent types</td>
<td>code-reviewer.md, debugger.md, feature-verifier.md, test-runner.md</td>
</tr>
<tr>
<td><strong>commands/</strong></td>
<td>CLI command specifications</td>
<td>spec.md, debug.md, status.md, blockers.md, verify.md, revert.md, next.md</td>
</tr>
</table>

---

### 📚 Documentation & Testing

<table>
<tr>
<th>Directory</th>
<th>Purpose</th>
<th>Contents</th>
</tr>
<tr>
<td><strong>docs/</strong></td>
<td>Architecture and implementation documentation</td>
<td>ARCHITECTURE.md, NATIVE-HOOKS.md, session-screenshot.jpg</td>
</tr>
<tr>
<td><strong>tests/</strong></td>
<td>High-level integration and orchestration tests</td>
<td>test_autonomous_loop.py, test_execute_phase.py, test_loop_orchestrator_integration.py</td>
</tr>
</table>

---

### 📦 Output & Research

<table>
<tr>
<th>Directory</th>
<th>Purpose</th>
<th>Contents</th>
</tr>
<tr>
<td><strong>output/</strong></td>
<td>Generated analysis and artifacts</td>
<td>silmari-Context-Engine/groups/ - file_groups.json, tech_stack.json</td>
</tr>
<tr>
<td><strong>thoughts/</strong></td>
<td>Searchable repository of research notes and planning documents</td>
<td>searchable/research/, searchable/shared/plans/, searchable/shared/research/</td>
</tr>
<tr>
<td><strong>silmari-messenger-plans/</strong></td>
<td>Related project sprint plans</td>
<td>24 sprint markdown files for Silmari Messenger project</td>
</tr>
</table>

---

## 🏛️ Architecture Documentation

### Directory Organization Patterns

```
┌─────────────────────────────────────────────────────────────┐
│                    ARCHITECTURAL LAYERS                      │
└─────────────────────────────────────────────────────────────┘

┌─ Entry Points ──────────────────────────────────────────────┐
│  loop-runner.py (50KB)         orchestrator.py (50KB)       │
│  planning_orchestrator.py (20KB)                            │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌─ Orchestration Layer ───────────────────────────────────────┐
│  silmari_rlm_act/          planning_pipeline/               │
│  • Phase execution         • Autonomous loops               │
│  • Checkpoints            • Decomposition                   │
│  • Context management     • Step execution                  │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌─ AI & Context Layer ────────────────────────────────────────┐
│  baml_src/ → baml_client/   context_window_array/           │
│  • Prompt templates         • Token management              │
│  • Structured outputs       • Context batching              │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌─ Execution Layer ───────────────────────────────────────────┐
│  go/                                                         │
│  • Native CLI executables                                   │
│  • Performance-critical operations                          │
└──────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **📦 Modularity**
   - Clear separation between planning, execution, and context management
   - Each directory has a focused responsibility
   - Tests co-located with implementation

2. **🔄 Phase-Based Execution**
   - Decomposition → Research → Planning → Implementation phases
   - Checkpoint/resume system for long-running operations
   - Phase-specific execution modules in `silmari_rlm_act/phases/`

3. **🚀 Hybrid Language Strategy**
   - Python for AI orchestration and high-level logic
   - Go for performance-critical CLI operations
   - Multi-platform binary compilation

4. **🎨 BAML-Driven Prompting**
   - Centralized AI prompt definitions
   - Type-safe structured outputs
   - Auto-generated client code

5. **🧠 Context Management**
   - Dedicated context window array system
   - Token-aware batching and storage
   - Working context vs implementation context separation

---

## 📂 Root-Level Organization

### Entry Point Scripts

| Script | Lines | Purpose |
|--------|-------|---------|
| `loop-runner.py` | ~50KB | Main loop execution runner |
| `orchestrator.py` | ~50KB | Pipeline orchestration |
| `planning_orchestrator.py` | ~20KB | Planning-specific orchestration |
| `resume_pipeline.py` | - | Pipeline resumption functionality |
| `resume_planning.py` | - | Planning resumption |
| `mcp-setup.py` | - | Model Context Protocol setup |
| `test-conversation.py` | - | Test conversation utility |

### Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python project configuration (Poetry) |
| `poetry.lock` | Dependency lock file |
| `pytest.ini` | Pytest configuration |
| `go.mod` / `go.sum` | Go module dependencies |
| `.env` | Environment variables |
| `docker-compose.yml` | Docker orchestration |
| `Dockerfile` | Container definition |

### Documentation Files

| File | Size | Purpose |
|------|------|---------|
| `README.md` | - | Main project overview |
| `CLAUDE.md` | 28KB | Claude-specific documentation |
| `DOCKER-SETUP.md` | - | Docker setup guide |
| `CONTRIBUTING.md` | - | Contribution guidelines |
| `PROMPT.md` | - | System prompt documentation |

---

## 🔗 Key Interdependencies

```
baml_src/ (definitions)
    ↓
baml_client/ (generated code)
    ↓
planning_pipeline/ + silmari_rlm_act/
    ↓
context_window_array/ (context management)
    ↓
go/ (native executables)
```

**Dependency Flow:**
1. `baml_src/` definitions are compiled to `baml_client/`
2. `silmari_rlm_act/` provides the main orchestration framework
3. `planning_pipeline/` handles decomposition and task breakdown
4. `go/` provides compiled executables for CLI operations
5. `context_window_array/` supports context management across all modules
6. Root-level scripts serve as entry points

---

## 📈 Project Statistics

<table>
<tr>
<td><strong>Total Main Directories</strong></td>
<td>13</td>
</tr>
<tr>
<td><strong>Primary Languages</strong></td>
<td>Python, Go, BAML</td>
</tr>
<tr>
<td><strong>Entry Point Scripts</strong></td>
<td>7</td>
</tr>
<tr>
<td><strong>Test Suites</strong></td>
<td>Package-level + Integration level</td>
</tr>
<tr>
<td><strong>Documentation Files</strong></td>
<td>5 root-level + docs/ directory</td>
</tr>
<tr>
<td><strong>Configuration Systems</strong></td>
<td>Python (Poetry), Go (modules), Docker</td>
</tr>
</table>

---

## 🎯 Directory Summary Table

<details>
<summary><strong>📊 Complete Directory Reference</strong> (click to expand)</summary>

| # | Directory | Type | Primary Purpose |
|---|-----------|------|-----------------|
| 1 | `silmari_rlm_act/` | Core | Main RLM ACT orchestration system |
| 2 | `planning_pipeline/` | Core | Autonomous planning and decomposition |
| 3 | `go/` | Core | Native executables for performance |
| 4 | `baml_src/` | AI | BAML prompt definitions |
| 5 | `baml_client/` | AI | Generated BAML client code |
| 6 | `context_window_array/` | AI | Context window management |
| 7 | `agents/` | Config | Agent specifications (Markdown) |
| 8 | `commands/` | Config | CLI command specifications |
| 9 | `docs/` | Docs | Architecture documentation |
| 10 | `tests/` | Testing | Integration test suite |
| 11 | `output/` | Output | Generated artifacts |
| 12 | `thoughts/` | Research | Searchable research repository |
| 13 | `silmari-messenger-plans/` | Related | Related project plans |

</details>

---

## 🔍 Code References

- `silmari_rlm_act/pipeline.py` - Main pipeline implementation (27KB)
- `planning_pipeline/autonomous_loop.py` - Autonomous loop execution (32KB)
- `planning_pipeline/decomposition.py` - Task decomposition logic (35KB)
- `planning_pipeline/claude_runner.py` - Claude integration (35KB)
- `baml_src/functions.baml` - BAML function definitions (78KB)
- `go/cmd/context-engine/` - Go context engine CLI
- `go/cmd/loop-runner/` - Go loop runner CLI
- `loop-runner.py` - Python loop runner entry point (50KB)
- `orchestrator.py` - Main orchestration entry point (50KB)

---

## 📚 Related Research

*No prior research documents found for project structure.*

---

## ✅ Conclusion

The Silmari Context Engine project follows a **well-organized, modular architecture** with clear separation of concerns:

- **13 main directories** organized by function
- **Hybrid Python/Go** implementation strategy
- **Phase-based execution** model with checkpoint/resume capabilities
- **BAML-driven** AI prompt management
- **Comprehensive testing** at multiple levels
- **Rich documentation** and configuration systems

The structure supports the project's goal of **autonomous AI-driven task management** with sophisticated context window handling and multi-phase execution workflows.
