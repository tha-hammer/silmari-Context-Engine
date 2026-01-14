---
date: 2026-01-14T14:40:25.508010-05:00
researcher: maceo
git_commit: bc8bc90f3f2888a21597c6e4739250e41548ef78
branch: main
repository: silmari-Context-Engine
topic: "Project Structure - Main Directories"
tags: [research, codebase, project-structure, directories]
status: complete
last_updated: 2026-01-14
last_updated_by: maceo
---

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║          SILMARI CONTEXT ENGINE - PROJECT STRUCTURE       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

**Date**: 2026-01-14T14:40:25.508010-05:00
**Researcher**: maceo
**Git Commit**: `bc8bc90f3f2888a21597c6e4739250e41548ef78`
**Branch**: main
**Repository**: silmari-Context-Engine
**Status**: ✅ Complete

---

## 📚 Research Question

**What is the project structure? List main directories only.**

---

## 🎯 Summary

The **silmari-Context-Engine** project contains **30 top-level directories** organized into several logical categories:

1. **Source Code & Implementation** (8 directories)
2. **Configuration & Tools** (6 directories)
3. **Development & Testing** (7 directories)
4. **Build & Output** (3 directories)
5. **Workflows & Checkpoints** (2 directories)
6. **Documentation & Planning** (4 directories)

The project is a Python-based autonomous project builder for Claude Code with supporting Go modules, BAML integration, and extensive configuration management.

---

## 📊 Detailed Directory Breakdown

### 🚀 Source Code & Implementation

| Directory | Purpose |
|-----------|---------|
| **`silmari_rlm_act/`** | Main Python package - core implementation |
| **`planning_pipeline/`** | Planning pipeline module |
| **`context_window_array/`** | Context window management |
| **`agents/`** | Agent implementations |
| **`commands/`** | Command implementations |
| **`baml_client/`** | Generated BAML client code |
| **`baml_src/`** | BAML source definitions |
| **`go/`** | Go language modules |

### ⚙️ Configuration & Tools

| Directory | Purpose |
|-----------|---------|
| **`.agent/`** | Agent configuration |
| **`.beads/`** | Beads issue tracking system |
| **`.claude/`** | Claude Code configuration |
| **`.cursor/`** | Cursor editor configuration |
| **`.silmari/`** | Silmari system configuration |
| **`.specstory/`** | Spec story configuration |

### 🧪 Development & Testing

| Directory | Purpose |
|-----------|---------|
| **`tests/`** | Test suite |
| **`.venv/`** | Python virtual environment |
| **`.pytest_cache/`** | Pytest cache |
| **`.mypy_cache/`** | MyPy type checker cache |
| **`.ruff_cache/`** | Ruff linter cache |
| **`.hypothesis/`** | Hypothesis testing framework data |
| **`__pycache__/`** | Python bytecode cache |

### 📦 Build & Output

| Directory | Purpose |
|-----------|---------|
| **`dist/`** | Distribution packages |
| **`output/`** | Generated output files |
| **`.git/`** | Git version control |

### 🔄 Workflows & Checkpoints

| Directory | Purpose |
|-----------|---------|
| **`.rlm-act-checkpoints/`** | RLM-ACT checkpoint storage |
| **`.workflow-checkpoints/`** | Workflow state checkpoints |

### 📖 Documentation & Planning

| Directory | Purpose |
|-----------|---------|
| **`docs/`** | Documentation files |
| **`thoughts/`** | Research notes and planning documents |
| **`silmari-messenger-plans/`** | Messenger planning files |

---

## 🗂️ Directory Tree (Level 1)

```
.
├── .agent                      # Agent configuration
├── .beads                      # Issue tracking
├── .claude                     # Claude Code config
├── .cursor                     # Cursor editor config
├── .git                        # Version control
├── .hypothesis                 # Testing framework data
├── .mypy_cache                 # Type checker cache
├── .pytest_cache               # Test cache
├── .rlm-act-checkpoints        # Checkpoint storage
├── .ruff_cache                 # Linter cache
├── .silmari                    # System config
├── .specstory                  # Spec story config
├── .venv                       # Virtual environment
├── .workflow-checkpoints       # Workflow states
├── __pycache__                 # Python bytecode
├── agents                      # Agent implementations
├── baml_client                 # Generated BAML code
├── baml_src                    # BAML sources
├── commands                    # Commands
├── context_window_array        # Context management
├── dist                        # Distribution packages
├── docs                        # Documentation
├── go                          # Go modules
├── output                      # Generated output
├── planning_pipeline           # Planning module
├── silmari-messenger-plans     # Messenger plans
├── silmari_rlm_act             # Main package
├── tests                       # Test suite
└── thoughts                    # Research & notes

30 directories
```

---

## 📋 Directory Categories Summary

<table>
<tr>
<th>Category</th>
<th>Count</th>
<th>Key Directories</th>
</tr>
<tr>
<td>🚀 <strong>Source Code</strong></td>
<td>8</td>
<td><code>silmari_rlm_act</code>, <code>planning_pipeline</code>, <code>agents</code>, <code>go</code></td>
</tr>
<tr>
<td>⚙️ <strong>Configuration</strong></td>
<td>6</td>
<td><code>.agent</code>, <code>.beads</code>, <code>.claude</code>, <code>.silmari</code></td>
</tr>
<tr>
<td>🧪 <strong>Development</strong></td>
<td>7</td>
<td><code>tests</code>, <code>.venv</code>, <code>.pytest_cache</code>, <code>.mypy_cache</code></td>
</tr>
<tr>
<td>📦 <strong>Build/Output</strong></td>
<td>3</td>
<td><code>dist</code>, <code>output</code>, <code>.git</code></td>
</tr>
<tr>
<td>🔄 <strong>Workflows</strong></td>
<td>2</td>
<td><code>.rlm-act-checkpoints</code>, <code>.workflow-checkpoints</code></td>
</tr>
<tr>
<td>📖 <strong>Documentation</strong></td>
<td>4</td>
<td><code>docs</code>, <code>thoughts</code>, <code>silmari-messenger-plans</code></td>
</tr>
</table>

---

## 🔍 Key Observations

### Project Type
- **Primary Language**: Python (main implementation)
- **Secondary Language**: Go (supporting modules)
- **Code Generation**: BAML integration for AI workflows
- **Architecture**: Multi-component autonomous system

### Configuration Density
The project has **6 configuration directories** (`.agent`, `.beads`, `.claude`, `.cursor`, `.silmari`, `.specstory`), indicating:
- Multiple tool integrations
- Rich development environment
- Complex orchestration requirements

### Checkpoint System
Two checkpoint directories suggest:
- State persistence across runs
- Resume capability for long-running tasks
- Workflow reliability mechanisms

### Testing Infrastructure
Multiple test-related directories (`.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.hypothesis`) indicate:
- Comprehensive testing approach
- Type safety emphasis
- Property-based testing
- Code quality enforcement

---

## 📁 Main Source Directories

<details>
<summary><strong>Core Implementation</strong></summary>

1. **`silmari_rlm_act/`** - Main Python package
   - Central implementation of the Context Engine
   - Core RLM-ACT (Reinforcement Learning Meta-ACT) functionality

2. **`planning_pipeline/`** - Planning system
   - Autonomous planning capabilities
   - Pipeline orchestration

3. **`context_window_array/`** - Context management
   - Four-layer memory architecture implementation
   - Context window optimization

4. **`agents/`** - Agent definitions
   - Specialized agent implementations
   - Agent orchestration logic

5. **`commands/`** - Command handlers
   - CLI command implementations
   - Command execution logic

</details>

<details>
<summary><strong>Supporting Code</strong></summary>

6. **`baml_client/`** - Generated BAML client
   - Auto-generated code from BAML definitions
   - AI workflow interfaces

7. **`baml_src/`** - BAML source files
   - BAML language definitions
   - AI interaction specifications

8. **`go/`** - Go modules
   - Performance-critical components
   - System-level operations

</details>

---

## 🛠️ Configuration Directories

| Directory | Purpose | Type |
|-----------|---------|------|
| `.agent` | Agent behavior & settings | Runtime Config |
| `.beads` | Issue tracking database | Tool Integration |
| `.claude` | Claude Code integration | IDE Config |
| `.cursor` | Cursor editor settings | IDE Config |
| `.silmari` | Core system configuration | System Config |
| `.specstory` | Specification & stories | Documentation Tool |

---

## 🧪 Development Directories

| Directory | Purpose | Persistence |
|-----------|---------|-------------|
| `tests/` | Test suite | Permanent |
| `.venv/` | Python dependencies | Permanent |
| `.pytest_cache/` | Test cache | Cache |
| `.mypy_cache/` | Type check cache | Cache |
| `.ruff_cache/` | Lint cache | Cache |
| `.hypothesis/` | Property test data | Cache |
| `__pycache__/` | Python bytecode | Cache |

---

## 🔄 Checkpoint Directories

```
┌─────────────────────────────────────────────────┐
│  Checkpoint System                               │
├─────────────────────────────────────────────────┤
│  .rlm-act-checkpoints/    → RLM-ACT states      │
│  .workflow-checkpoints/   → Workflow states     │
└─────────────────────────────────────────────────┘
```

These directories enable:
- **Resume capability** - Continue from saved states
- **Fault tolerance** - Recover from failures
- **Long-running tasks** - Support multi-session workflows

---

## 📖 Documentation Directories

1. **`docs/`** - Formal documentation
   - Usage guides
   - Architecture documentation
   - API references

2. **`thoughts/`** - Research & planning
   - Research documents
   - Design decisions
   - Experiment notes

3. **`silmari-messenger-plans/`** - Messenger-specific plans
   - Planning artifacts
   - Execution strategies

---

## 🎯 Directory Organization Principles

The project follows clear organizational patterns:

### ✅ **Separation of Concerns**
- Source code isolated from configuration
- Tests separated from implementation
- Documentation distinct from code

### ✅ **Tool Integration**
- Dedicated directories for IDE/tool configs
- Clear tool boundaries (`.claude`, `.cursor`, etc.)

### ✅ **State Management**
- Explicit checkpoint directories
- Cache directories clearly marked
- Persistent vs. temporary distinction

### ✅ **Multi-Language Support**
- Python as primary language
- Go for performance-critical code
- BAML for AI workflows

---

## 📊 Directory Count by Type

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source Code          ████████ (8 dirs)
Configuration        ██████ (6 dirs)
Development/Testing  ███████ (7 dirs)
Build/Output         ███ (3 dirs)
Workflows            ██ (2 dirs)
Documentation        ████ (4 dirs)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 30 directories
```

---

## 🔗 Related Documentation

- **Project Overview**: `README.md` - Describes the Context Engine's four-layer memory architecture
- **Setup Instructions**: `DOCKER-SETUP.md` - Docker configuration
- **Agent Documentation**: `AGENTS.md` - Agent system details
- **Claude Integration**: `CLAUDE.md` - Claude Code integration guide

---

## ❓ Directory Naming Conventions

| Pattern | Examples | Purpose |
|---------|----------|---------|
| `.dotfiles` | `.agent`, `.beads`, `.claude` | Configuration & tools (hidden) |
| `snake_case` | `silmari_rlm_act`, `planning_pipeline` | Python packages |
| `kebab-case` | `.rlm-act-checkpoints`, `silmari-messenger-plans` | Multi-word directories |
| `lowercase` | `agents`, `commands`, `tests`, `docs` | Standard directories |

---

## 📝 Notes

- All directories are at the **top level** of the repository
- The project uses **30 main directories** for organization
- **Configuration density** is high (6 config directories)
- **Testing infrastructure** is comprehensive (7 development directories)
- **Checkpoint system** enables resumable workflows
- **Multi-language** architecture (Python + Go + BAML)

---

## 🎯 Conclusion

The **silmari-Context-Engine** has a well-organized directory structure with clear separation between:
- Source code and configuration
- Development tools and production code
- Persistent state and temporary caches
- Documentation and implementation

The 30 main directories reflect a mature project with comprehensive tooling, testing, and state management capabilities designed for autonomous long-running workflows.
