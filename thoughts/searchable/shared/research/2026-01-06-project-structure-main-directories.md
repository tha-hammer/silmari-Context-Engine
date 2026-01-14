---
date: 2026-01-06 07:11:37 -05:00
researcher: tha-hammer
git_commit: 6a8a69f3c33d65d8e5c34f988ec71a9005992229
branch: main
repository: silmari-Context-Engine
topic: "Project Structure - Main Directories"
tags: [research, codebase, project-structure, directories]
status: complete
last_updated: 2026-01-06
last_updated_by: tha-hammer
---

```
┌─────────────────────────────────────────────────────────┐
│          SILMARI CONTEXT ENGINE                         │
│          Project Structure Overview                     │
│                                                         │
│  Status: ✅ Complete    Date: 2026-01-06               │
└─────────────────────────────────────────────────────────┘
```

# Research: Project Structure - Main Directories

**Date**: 2026-01-06 07:11:37 -05:00
**Researcher**: tha-hammer
**Git Commit**: `6a8a69f3c33d65d8e5c34f988ec71a9005992229`
**Branch**: main
**Repository**: silmari-Context-Engine

## Research Question

What is the project structure? List main directories only.

## 📊 Summary

The **silmari-Context-Engine** project is organized into 14 main functional directories and 15 configuration/hidden directories. The project appears to be a multi-language system (Python, Go, BAML) focused on AI/ML orchestration and context management with extensive testing infrastructure.

## 📚 Main Project Directories

The following table shows the primary functional directories in the project:

| Directory | Type | Purpose |
|-----------|------|---------|
| **agents** | Python Module | Agent definitions and implementations |
| **baml_client** | Generated Code | BAML client library (auto-generated) |
| **baml_src** | Source | BAML source definitions |
| **build** | Build Output | Compiled artifacts and build outputs |
| **commands** | Commands | CLI command definitions |
| **context_window_array** | Python Module | Context window management system |
| **docs** | Documentation | Project documentation |
| **go** | Go Module | Go language implementations |
| **output** | Runtime Output | Runtime generated outputs |
| **planning_pipeline** | Python Module | Planning and orchestration pipeline |
| **silmari_rlm_act** | Python Module | Core RL/ML acting system |
| **sprints** | Planning | Sprint planning and tracking |
| **tests** | Testing | Project-wide test suite |
| **thoughts** | Documentation | Research, plans, and decision logs |

### 🎯 Key Functional Areas

<details>
<summary><strong>Core Systems (3 directories)</strong></summary>

- **context_window_array/** - Context window management
- **planning_pipeline/** - Planning and orchestration
- **silmari_rlm_act/** - RL/ML acting system

</details>

<details>
<summary><strong>Language Integrations (3 directories)</strong></summary>

- **baml_src/** - BAML source definitions
- **baml_client/** - Generated BAML client
- **go/** - Go implementations

</details>

<details>
<summary><strong>Configuration & Tools (4 directories)</strong></summary>

- **agents/** - Agent definitions
- **commands/** - CLI commands
- **docs/** - Documentation
- **thoughts/** - Research and plans

</details>

<details>
<summary><strong>Quality & Output (4 directories)</strong></summary>

- **tests/** - Test suite
- **sprints/** - Sprint tracking
- **build/** - Build outputs
- **output/** - Runtime outputs

</details>

## 🔧 Configuration & Hidden Directories

The project includes extensive development tooling and configuration:

| Directory | Purpose |
|-----------|---------|
| **.agent** | Agent-specific configuration and state |
| **.beads** | Beads issue tracking system |
| **.claude** | Claude Code integration |
| **.cursor** | Cursor IDE integration |
| **.git** | Git version control |
| **.hypothesis** | Hypothesis testing framework data |
| **.mypy_cache** | MyPy type checker cache |
| **.pytest_cache** | Pytest cache |
| **.rlm-act-checkpoints** | RL/ML checkpoints |
| **.ruff_cache** | Ruff linter cache |
| **.silmari** | Silmari system configuration |
| **.specstory** | Specification tracking |
| **.venv** | Python virtual environment |
| **.workflow-checkpoints** | Workflow state checkpoints |
| **__pycache__** | Python bytecode cache |

### 🛠️ Development Tools Detected

<table>
<tr>
<td><strong>Python Tooling</strong></td>
<td><strong>IDE Integration</strong></td>
</tr>
<tr>
<td>

- pytest
- mypy
- ruff
- hypothesis
- venv

</td>
<td>

- Claude Code
- Cursor IDE
- Custom agents

</td>
</tr>
<tr>
<td><strong>Version Control</strong></td>
<td><strong>Custom Systems</strong></td>
</tr>
<tr>
<td>

- Git
- GitHub integration

</td>
<td>

- Beads tracking
- Silmari config
- SpecStory

</td>
</tr>
</table>

## 📁 Directory Tree Structure

```
silmari-Context-Engine/
├── agents/                  # Agent definitions
├── baml_client/            # Generated BAML client
├── baml_src/               # BAML source files
├── build/                  # Build artifacts
├── commands/               # CLI commands
├── context_window_array/   # Context management module
├── docs/                   # Documentation
├── go/                     # Go implementations
├── output/                 # Runtime outputs
├── planning_pipeline/      # Planning system
├── silmari_rlm_act/       # Core RL/ML system
├── sprints/               # Sprint tracking
├── tests/                 # Test suite
└── thoughts/              # Research & plans
```

## 🔍 Architecture Patterns

Based on the directory structure, the project demonstrates:

1. **Multi-Language Architecture**: Python (primary), Go (performance), BAML (AI/ML)
2. **Modular Design**: Separate directories for distinct functional areas
3. **Testing-First Approach**: Dedicated test infrastructure (.pytest_cache, .hypothesis, tests/)
4. **Checkpoint-Based Workflows**: Multiple checkpoint directories for state management
5. **Documentation-Driven**: Extensive documentation (docs/, thoughts/, sprints/)
6. **AI/ML Focus**: BAML integration, agent systems, RL/ML components

## 📖 Code References

All directories exist at the project root level:
- [`/home/maceo/Dev/silmari-Context-Engine/`](https://github.com/zeddy89/Context-Engine/tree/6a8a69f3c33d65d8e5c34f988ec71a9005992229)

Main functional directories:
- [`agents/`](https://github.com/zeddy89/Context-Engine/tree/6a8a69f3c33d65d8e5c34f988ec71a9005992229/agents)
- [`baml_client/`](https://github.com/zeddy89/Context-Engine/tree/6a8a69f3c33d65d8e5c34f988ec71a9005992229/baml_client)
- [`baml_src/`](https://github.com/zeddy89/Context-Engine/tree/6a8a69f3c33d65d8e5c34f988ec71a9005992229/baml_src)
- [`context_window_array/`](https://github.com/zeddy89/Context-Engine/tree/6a8a69f3c33d65d8e5c34f988ec71a9005992229/context_window_array)
- [`go/`](https://github.com/zeddy89/Context-Engine/tree/6a8a69f3c33d65d8e5c34f988ec71a9005992229/go)
- [`planning_pipeline/`](https://github.com/zeddy89/Context-Engine/tree/6a8a69f3c33d65d8e5c34f988ec71a9005992229/planning_pipeline)
- [`silmari_rlm_act/`](https://github.com/zeddy89/Context-Engine/tree/6a8a69f3c33d65d8e5c34f988ec71a9005992229/silmari_rlm_act)
- [`tests/`](https://github.com/zeddy89/Context-Engine/tree/6a8a69f3c33d65d8e5c34f988ec71a9005992229/tests)
- [`thoughts/`](https://github.com/zeddy89/Context-Engine/tree/6a8a69f3c33d65d8e5c34f988ec71a9005992229/thoughts)

## 🔗 Related Research

Previous project structure research documents:
- `thoughts/shared/research/2026-01-04-project-structure.md` (if exists)
- `thoughts/shared/research/2026-01-05-project-structure.md` (if exists)
- `thoughts/shared/research/2026-01-05-project-structure-detailed.md` (if exists)

## 💡 Open Questions

For deeper investigation:
1. What is the relationship between `planning_pipeline/` and `silmari_rlm_act/`?
2. How does the Go module integrate with the Python codebase?
3. What is the BAML workflow and how is `baml_client/` generated?
4. What do the checkpoint directories track?
5. How do the custom systems (.beads, .silmari, .specstory) interact?

---

*This research document provides a high-level overview of the project directory structure. For detailed analysis of specific modules or systems, additional focused research is recommended.*
