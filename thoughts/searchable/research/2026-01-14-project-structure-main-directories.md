---
date: 2026-01-14T13:05:40-05:00
researcher: Claude Sonnet 4.5
git_commit: 407bfa7c974e9abb4bf3099132a6940e5ebfd23b
branch: main
repository: tha-hammer/silmari-Context-Engine
topic: "Project Structure - Main Directories"
tags: [research, codebase, project-structure, architecture, directories]
status: complete
last_updated: 2026-01-14
last_updated_by: Claude Sonnet 4.5
---

```
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║              SILMARI CONTEXT ENGINE - PROJECT STRUCTURE               ║
║                          Main Directory Layout                        ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝

📅 Date: 2026-01-14T13:05:40-05:00
👤 Researcher: Claude Sonnet 4.5
🔄 Git Commit: 407bfa7c974e9abb4bf3099132a6940e5ebfd23b
🌿 Branch: main
📦 Repository: tha-hammer/silmari-Context-Engine
✅ Status: Complete
```

## 📚 Research Question

**What is the project structure? List main directories only.**

---

## 🎯 Summary

The **Silmari Context Engine** is organized into **15 main directories**, implementing a sophisticated autonomous TDD development system with multi-language support (Python, Go, BAML). The project features:

- **Dual implementation strategy** - Python primary + Go port for performance
- **AI-driven orchestration** - BAML-based LLM integration with type-safe interfaces
- **Memory-augmented architecture** - 4-layer memory system (Working, Episodic, Semantic, Procedural)
- **6-phase autonomous pipeline** - Research → Learn → Model → Act → Verify → Deploy
- **Comprehensive knowledge management** - 363+ research documents, 100+ TDD plans

<details>
<summary><b>📊 Directory Statistics Table</b></summary>

| Directory | Type | Purpose | Lines of Code | Key Components |
|-----------|------|---------|---------------|----------------|
| **agents/** | Config | Agent specifications | ~500 | 4 specialized agents |
| **baml_client/** | Generated | BAML Python client | ~10,000 | 81 generated classes |
| **baml_src/** | Source | BAML schemas & functions | ~5,000 | 26 schema files |
| **commands/** | Docs | CLI command templates | ~2,000 | 7 workflow commands |
| **context_window_array/** | Library | Context management | ~3,000 | Core CWA library |
| **dist/** | Build | Distribution artifacts | N/A | .whl, .tar.gz packages |
| **docs/** | Docs | Architecture guides | ~530 | 2 major docs |
| **go/** | Source | Go implementation | ~24,877+ | CLI + planning pipeline |
| **output/** | Runtime | Runtime artifacts | N/A | JSON tracking files |
| **planning_pipeline/** | Source | Python TDD pipeline | ~8,000+ | 7-step orchestration |
| **silmari-messenger-plans/** | Data | Example plans | N/A | 24 sprint examples |
| **silmari_rlm_act/** | Source | Main RLM-Act pipeline | ~15,000+ | 6-phase system |
| **tests/** | Test | Integration tests | ~1,000+ | 40+ test files |
| **thoughts/** | Knowledge | Research & planning | N/A | 363+ documents |
| **__pycache__/** | Cache | Python bytecode | N/A | Auto-generated |

</details>

---

## 🔍 Detailed Findings

### 📂 Core Implementation Directories

<details>
<summary><b>1. agents/ - Specialized Agent Definitions</b></summary>

**Purpose:** Defines specialized subagent roles for autonomous workflow operations in Claude Code.

**📁 Contents:**
- `feature-verifier.md` - End-to-end feature verification specialist
- `test-runner.md` - Test automation specialist
- `code-reviewer.md` - Senior code review specialist
- `debugger.md` - Debug specialist for issue investigation

**🎯 Role:** Agent specifications (YAML frontmatter + markdown) that define autonomous roles invoked during the development pipeline. Each agent has specific tools (read, bash, grep, glob) and responsibilities for verification, testing, review, and debugging.

**🔗 Integration:** Invoked by `silmari_rlm_act` pipeline during implementation phases for quality assurance.

</details>

<details>
<summary><b>2. silmari_rlm_act/ - Main RLM-Act Pipeline (Python)</b></summary>

**Purpose:** Autonomous TDD pipeline implementing "Research, Learn, Model, Act" methodology using Context Window Array.

**📁 Main Files:**
- `pipeline.py` - `RLMActPipeline` class orchestrating 6 phases
- `models.py` - Data models (PhaseType, PhaseStatus, AutonomyMode, PipelineState)
- `cli.py` - Click-based CLI (start, resume, status commands)

**📁 Subdirectories:**
```
silmari_rlm_act/
├── phases/              # Phase implementations
│   ├── research.py      # Initial context gathering
│   ├── decomposition.py # Requirement breakdown
│   ├── tdd_planning.py  # Red-Green-Refactor plans
│   ├── multi_doc.py     # Plan document splitting
│   ├── beads_sync.py    # Progress tracking
│   └── implementation.py # TDD execution
├── checkpoints/         # Checkpoint management
│   ├── manager.py       # State file management
│   └── interactive.py   # Interactive prompts
├── commands/            # YAML agent commands
├── agents/              # Agent specifications
├── context/             # CWA integration
├── hooks/               # Pipeline extension hooks
└── tests/               # Pipeline test suite
```

**🎯 Role:** Top-level orchestrator implementing a complete 6-phase autonomous development cycle:
1. **RESEARCH** - Gather context
2. **DECOMPOSITION** - Break into testable requirements
3. **TDD_PLANNING** - Create Red-Green-Refactor plans
4. **MULTI_DOC** - Split into phase documents
5. **BEADS_SYNC** - Track with beads issues
6. **IMPLEMENTATION** - Execute TDD cycles

**⚙️ Autonomy Modes:**
- **CHECKPOINT** - Pause for human review
- **FULLY_AUTONOMOUS** - Unattended execution
- **BATCH** - Batch mode support

**🔗 Integration:** Uses `planning_pipeline` for decomposition, `context_window_array` for context management, and `agents` for quality assurance.

</details>

<details>
<summary><b>3. planning_pipeline/ - Python Planning Pipeline</b></summary>

**Purpose:** Deterministic planning and orchestration pipeline for Claude Code-driven software development.

**📁 Main Files:**
- `pipeline.py` - `PlanningPipeline` class (7-step orchestration)
- `models.py` - 3-tier requirement hierarchies (parent → sub_process → implementation)
- `integrated_orchestrator.py` - Beads-based state management
- `beads_controller.py` - Issue tracking for features
- `claude_runner.py` - Claude invocation (sync + subprocess)
- `decomposition.py` - Research → structured requirements (via BAML)
- `autonomous_loop.py` - Autonomous execution loop
- `steps.py` - Individual pipeline step implementations
- `checkpoint_manager.py` - Resumable checkpoint management
- `property_generator.py` - Testable property generation

**📁 Subdirectories:**
- `phase_execution/` - Plan discovery, prompt building, Claude invocation, result checking

**🎯 Role:** Provides Python control layer for deterministic planning. Converts vague research into structured requirement hierarchies with testable properties, driving implementation planning and beads issue tracking.

**🔗 Integration:** Called by `silmari_rlm_act` for DECOMPOSITION and TDD_PLANNING phases. Uses BAML schemas from `baml_src/`.

</details>

<details>
<summary><b>4. context_window_array/ - Context Management Library</b></summary>

**Purpose:** Addressable context management architecture separating working context (planning) from implementation context (code execution).

**📁 Main Files:**
- `models.py` - Core data models:
  - `EntryType` enum (FILE, COMMAND, TASK, SEARCH_RESULT, SUMMARY, etc.)
  - `ContextEntry` dataclass (ID: ctx_XXX, type, source, content, summary, timestamps)
- `store.py` - `CentralContextStore` (CRUD operations)
- `working_context.py` - Planning/orchestration context
- `implementation_context.py` - Code execution context
- `search_index.py` - Vector search for context entries
- `batching.py` - Task batching across context boundaries
- `exceptions.py` - Custom exceptions

**📁 Subdirectories:**
- `tests/` - Comprehensive test suite (models, store, search, batching, working/implementation contexts)

**🎯 Role:** Novel architecture for managing context in LLM workflows. Provides addressable context entries (ctx_000001) that can be referenced, searched, compressed, and batched. Enables separation between planning context and implementation context.

**🔗 Integration:** Foundational infrastructure used by both `planning_pipeline` and `silmari_rlm_act` for context management across phase boundaries.

</details>

<details>
<summary><b>5. go/ - Go Implementation (Cross-Platform)</b></summary>

**Purpose:** Complete Go language rewrite of the Python planning pipeline with cross-platform binary distribution.

**📁 Structure:**
```
go/
├── Makefile                 # Build automation
├── build/                   # Compiled binaries (macOS, Linux, Windows)
│   ├── context-engine       # Main orchestrator binary
│   └── loop-runner          # Autonomous loop runner binary
├── build-and-install.sh     # Installation script
├── cmd/                     # Entry points
│   ├── context-engine/main.go
│   └── loop-runner/main.go
└── internal/                # Core implementation (~24,877+ lines)
    ├── cli/                 # Cobra-based CLI (~1000 lines)
    ├── planning/            # Planning pipeline (~24,877 lines)
    │   ├── models.go        # RequirementNode, TestableProperty
    │   ├── orchestrator.go  # Phase orchestration
    │   ├── pipeline.go      # Main pipeline
    │   ├── decomposition.go # Requirement breakdown
    │   ├── implementation.go # Implementation phase
    │   ├── review.go        # Review logic (122.4 KB)
    │   ├── checkpoint.go    # State management
    │   └── *_test.go        # Comprehensive tests
    ├── exec/                # Execution wrappers (~800 lines)
    ├── concurrent/          # Concurrency utilities (~500 lines)
    ├── fs/                  # File system ops (~300 lines)
    └── models/              # Context entry models (~300 lines)
```

**🎯 Role:** Production Go implementation of the planning pipeline with:
- CLI for orchestrating autonomous code generation
- Multi-phase pipeline (requirement → implementation → review)
- Hierarchical requirement decomposition with testable properties
- Multiple autonomy modes (Checkpoint, Batch, FullyAutonomous)
- State checkpointing for crash recovery
- Cross-platform binaries (macOS ARM64/x86_64, Linux ARM64/x86_64, Windows x86_64)

**🔗 Integration:** Parallel implementation to Python pipeline, designed for performance and deployment flexibility.

</details>

---

### 🤖 BAML Integration Directories

<details>
<summary><b>6. baml_src/ - BAML Source Definitions</b></summary>

**Purpose:** Source definitions for BAML (Boundary ML) - type-safe LLM application framework. Contains client configs, function definitions, and data schemas.

**📁 Root Files:**
- `clients.baml` - LLM client configurations (OpenAI, Anthropic, Ollama + fallback strategies)
- `types.baml` - Gate 1/2/3 type definitions for interactive requirements analysis
- `functions.baml` - BAML function templates with prompt strings
- `resume.baml` - Example resume extraction function
- `generators.baml` - Code generation config (Python/Pydantic output)

**📁 schema/ Subdirectory (26 files):**
```
schema/
├── CommonSchema.baml                    # Shared classes
├── InitialExtractionSchema.baml         # Requirements extraction
├── GapAnalysisSchema.baml              # Gap analysis
├── SubprocessAnalysisSchema.baml       # Implementation details
├── CategoryAnalysisSchema.baml         # Category-based requirements
├── Category*Schema.baml                # Domain schemas (Functional, Security, Performance, etc.)
├── RequirementExpansionSchema.baml     # Requirement processing
├── UserInteractionsSchema.baml         # User interaction requirements
├── GuidedSearchSchema.baml             # Search findings
├── InterfaceMappingSchema.baml         # Service extraction
├── TechStackSchema.baml                # Technology stack analysis
└── Gate1SharedClasses.baml             # Gate 1 shared classes
```

**🎯 Role:** Source definitions compiled/generated into `baml_client/` Python code. Defines LLM prompts, clients, functions, and type contracts for structured LLM interactions.

**🔗 Integration:** Used by `planning_pipeline/decomposition.py` for converting research into structured requirements via Claude.

</details>

<details>
<summary><b>7. baml_client/ - Generated BAML Python Client</b></summary>

**Purpose:** Auto-generated Python client library providing type-safe LLM function calls.

**📁 Key Files:**
- `__init__.py` - Exports main client (`b`), types, config
- `sync_client.py` - `BamlSyncClient` for synchronous BAML function calls
- `async_client.py` - Async client variant
- `types.py` - 81 generated Pydantic models (AccessibilityFeatures, RequirementsAnalysis, etc.)
- `stream_types.py` - Partial/streaming response types
- `runtime.py` - Runtime execution environment
- `config.py` - Configuration management
- `parser.py` - LLM response parser
- `tracing.py` - Observability utilities
- `type_builder.py` - Dynamic type construction

**🎯 Role:** Generated artifact directory (DO NOT EDIT). Files auto-generated by `baml-cli generate` from `baml_src/`. Provides type-safe Python interface to LLM functions.

**🔗 Integration:** Imported by Python code to make structured LLM calls with Pydantic validation.

</details>

---

### 📋 Configuration & Command Directories

<details>
<summary><b>8. commands/ - Interactive CLI Command Documentation</b></summary>

**Purpose:** Markdown documentation describing workflow commands for project management.

**📁 Contents (7 files):**
- `spec.md` - Display/analyze app specification (app_spec.txt, APP_SPEC.md)
- `status.md` - Show project status (git, feature progress from feature_list.json)
- `next.md` - Find next feature to implement (priority, dependencies)
- `blockers.md` - Show blocked features and dependency chains
- `debug.md` - Collect diagnostics (versions, structure, logs, ports)
- `verify.md` - Verify working state (tests, build, lint, endpoints)
- `revert.md` - Revert to last known good state (last "session: completed" commit)

**🎯 Role:** Instruction templates for interactive development commands. Reference project artifacts like `feature_list.json`, `claude-progress.txt`, `app_spec.txt`.

**🔗 Integration:** Used by Claude Code for structured workflow automation.

</details>

---

### 📖 Documentation & Knowledge Directories

<details>
<summary><b>9. docs/ - Architecture Documentation</b></summary>

**Purpose:** User-facing architectural guides and setup instructions.

**📁 Contents:**
- `ARCHITECTURE.md` (238 lines) - Context Engine memory system documentation:
  - Problem: context degradation in long-running LLM sessions
  - 4-layer memory hierarchy (Working, Episodic, Semantic, Procedural)
  - Artifact system for large outputs
  - Feedback loop for learning
  - Research foundation citations (MemGPT, Generative Agents, Anthropic)

- `NATIVE-HOOKS.md` (295 lines) - Claude Code native hooks configuration:
  - Installation and setup
  - Hook lifecycle (SessionStart, PreCompact, Stop, PostToolUse)
  - Directory structure and memory management
  - Slash command reference
  - Feature tracking with feature_list.json
  - Troubleshooting guide

- `session-screenshot.jpg` - Visual reference

**🎯 Role:** End-user documentation for understanding the Context Engine architecture and setting up native hooks for interactive Claude Code sessions.

</details>

<details>
<summary><b>10. thoughts/ - Knowledge Management System</b></summary>

**Purpose:** Living knowledge base storing research documentation, technical plans, and session notes.

**📁 Structure:**
```
thoughts/
├── global/              # Symlink to shared user thoughts
├── maceo/               # Symlink to user-specific thoughts
├── shared/              # Symlink to shared repository thoughts
└── searchable/
    ├── global/
    ├── research/        # 363 markdown research documents
    │   ├── 2026-01-14-*.md    (Latest project analysis)
    │   ├── 2026-01-13-*.md    (Go runtime integration)
    │   ├── 2026-01-09-*.md    (RLMA pipeline analysis)
    │   └── (dated research files)
    └── shared/
        ├── docs/                # 5+ how-to guides
        │   ├── how-to-build-and-run-go-context-engine.md
        │   ├── how-to-use-context-window-array.md
        │   ├── how-to-run-pipeline-with-baml.md
        │   ├── how-to-use-cli-commands.md
        │   └── how-to-run-planning-pipeline.md
        ├── documentation/       # Usage docs
        │   └── how-to-use-rlma-pipeline.md
        └── plans/               # 100+ TDD feature plans
            ├── 2026-01-14-tdd-feature/
            ├── 2026-01-10-tdd-feature/  (20+ requirements)
            ├── 2026-01-13-tdd-feature/
            ├── 2026-01-04-tdd-rust-orchestrator-port/
            ├── 2026-01-04-tdd-context-window-array/
            ├── 2026-01-03-tdd-codewriter5-baml-context-generation/
            └── (dated plan directories)
```

**📊 Contents:**

| Category | Count | Description |
|----------|-------|-------------|
| Research Documents | 363+ | Technical analysis, architecture reviews, component investigation |
| How-To Guides | 5+ | Developer guides for using various components |
| TDD Feature Plans | 100+ | Comprehensive requirement breakdowns with phase-by-phase implementation |
| Usage Documentation | Multiple | Pipeline usage instructions |

**🎯 Role:** Captures:
- Architectural decisions and technical analysis
- Features broken into testable TDD requirements
- How-to guides for developers
- Research on technical topics (Go porting, orchestration, etc.)
- Historical work organized by date and feature

**🔗 Integration:** Referenced by research agents and used for historical context during planning phases.

</details>

---

### 🧪 Testing Directories

<details>
<summary><b>11. tests/ - Python Integration Test Suite</b></summary>

**Purpose:** Integration and unit tests for Python planning pipeline components.

**📁 Contents:**
- `test_autonomous_loop.py` (356 lines) - Tests LoopRunner orchestration:
  - Phase 1: Orchestrator initialization
  - Phase 2: Plan discovery
  - Phase 3: Backward compatibility
  - Phase 4: Phase progression
  - Phase 5: Status updates (IN_PROGRESS, COMPLETED, FAILED)
  - Phase 6: Resume from paused state

- `test_execute_phase.py` - Phase prompt generation and execution tests
- `test_loop_orchestrator_integration.py` - Integration tests between LoopRunner and PipelineOrchestrator
- `__pycache__/` - Python bytecode cache

**🎯 Role:** Validates autonomous loop execution, orchestrator integration, plan discovery, status tracking, and phase progression. Ensures backward compatibility and proper state management.

**🔗 Integration:** Tests components from `planning_pipeline/` and integration points with `silmari_rlm_act/`.

</details>

---

### 📦 Build & Distribution Directories

<details>
<summary><b>12. dist/ - Package Distribution Artifacts</b></summary>

**Purpose:** Contains built Python packages ready for distribution.

**📁 Contents:**
- `.whl` files (wheel packages)
- `.tar.gz` files (source distributions)

**🎯 Role:** Distribution artifacts generated by Python build tools (setuptools, poetry, etc.) for package installation.

</details>

<details>
<summary><b>13. output/ - Runtime Artifacts</b></summary>

**Purpose:** Runtime-generated tracking files and artifacts.

**📁 Contents:**
- `file_groups.json` - File grouping metadata
- `tech_stack.json` - Technology stack tracking

**🎯 Role:** Stores runtime state and metadata generated during pipeline execution.

</details>

---

### 📚 Example & Reference Directories

<details>
<summary><b>14. silmari-messenger-plans/ - Example Project Plans</b></summary>

**Purpose:** Example project demonstrating TDD planning pipeline output.

**📁 Contents:**
- 24 sprint plans
- Example requirement breakdowns
- Reference implementation patterns

**🎯 Role:** Reference material showing complete TDD planning pipeline output for a sample project.

</details>

<details>
<summary><b>15. __pycache__/ - Python Bytecode Cache</b></summary>

**Purpose:** Auto-generated Python bytecode cache for faster module loading.

**🎯 Role:** Performance optimization (ignored by git, automatically regenerated).

</details>

---

## 🏗️ Architecture Relationships

```
┌────────────────────────────────────────────────────────────────────┐
│                      Project Architecture Flow                      │
└────────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│ User Input      │
│ (requirements)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   silmari_rlm_act/ (Top-Level Orchestrator)     │
│                                                                 │
│  6-Phase Pipeline: RESEARCH → DECOMPOSITION → TDD_PLANNING →  │
│                    MULTI_DOC → BEADS_SYNC → IMPLEMENTATION     │
└──────┬────────────────────┬────────────────────┬───────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│ planning_       │  │ context_window_  │  │ agents/         │
│ pipeline/       │  │ array/           │  │                 │
│                 │  │                  │  │ - feature-      │
│ - Decomposes    │  │ - Manages        │  │   verifier      │
│   requirements  │  │   addressable    │  │ - test-runner   │
│ - Generates     │  │   context        │  │ - code-reviewer │
│   hierarchies   │  │ - Separates      │  │ - debugger      │
│ - Creates TDD   │  │   planning/impl  │  │                 │
│   plans         │  │   contexts       │  │                 │
└────────┬────────┘  └──────────────────┘  └─────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   baml_src/ + baml_client/                       │
│                                                                 │
│  BAML Source Definitions → Generated Python Client              │
│  - Type-safe LLM function calls                                 │
│  - 81 Pydantic models for structured outputs                    │
│  - Client configurations (OpenAI, Anthropic, Ollama)            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          Parallel Track                          │
│                                                                 │
│                         go/ (Go Port)                            │
│                                                                 │
│  - CLI: context-engine, loop-runner                             │
│  - planning/ package: Complete pipeline rewrite                 │
│  - Cross-platform binaries (macOS, Linux, Windows)              │
│  - Performance-optimized implementation                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Supporting Infrastructure                     │
│                                                                 │
│  thoughts/     - Knowledge management (363+ research docs)      │
│  docs/         - User documentation (ARCHITECTURE.md, etc.)     │
│  tests/        - Integration test suite (40+ test files)        │
│  commands/     - Workflow command templates                     │
└─────────────────────────────────────────────────────────────────┘
```

### 🔗 Integration Points

<table>
<tr>
<th>Component A</th>
<th>→</th>
<th>Component B</th>
<th>Integration Type</th>
</tr>
<tr>
<td><code>silmari_rlm_act/</code></td>
<td>→</td>
<td><code>planning_pipeline/</code></td>
<td>Calls for DECOMPOSITION and TDD_PLANNING phases</td>
</tr>
<tr>
<td><code>planning_pipeline/</code></td>
<td>→</td>
<td><code>baml_client/</code></td>
<td>Uses for structured LLM calls in decomposition</td>
</tr>
<tr>
<td><code>silmari_rlm_act/</code></td>
<td>→</td>
<td><code>context_window_array/</code></td>
<td>Uses for context management across phases</td>
</tr>
<tr>
<td><code>silmari_rlm_act/</code></td>
<td>→</td>
<td><code>agents/</code></td>
<td>Invokes specialized agents for QA tasks</td>
</tr>
<tr>
<td><code>baml_src/</code></td>
<td>→</td>
<td><code>baml_client/</code></td>
<td>Compiled/generated by baml-cli</td>
</tr>
<tr>
<td><code>go/</code></td>
<td>⟷</td>
<td><code>planning_pipeline/</code></td>
<td>Parallel implementations (Go port of Python)</td>
</tr>
<tr>
<td><code>tests/</code></td>
<td>→</td>
<td><code>planning_pipeline/</code></td>
<td>Tests pipeline components</td>
</tr>
<tr>
<td>All components</td>
<td>→</td>
<td><code>thoughts/</code></td>
<td>Reference for historical context and docs</td>
</tr>
</table>

---

## 📎 Code References

### Key Entry Points

| File | Lines | Purpose |
|------|-------|---------|
| `silmari_rlm_act/pipeline.py` | ~500 | Main RLMActPipeline orchestrator |
| `planning_pipeline/pipeline.py` | ~400 | PlanningPipeline 7-step orchestration |
| `go/cmd/context-engine/main.go` | ~100 | Go CLI entry point |
| `context_window_array/store.py` | ~300 | CentralContextStore implementation |
| `baml_src/clients.baml` | ~200 | LLM client configurations |

### Critical Models

| File | Purpose |
|------|---------|
| `silmari_rlm_act/models.py` | PhaseType, PhaseStatus, AutonomyMode, PipelineState |
| `planning_pipeline/models.py` | 3-tier RequirementNode hierarchy |
| `context_window_array/models.py` | ContextEntry, EntryType enums |
| `baml_client/types.py` | 81 generated Pydantic models |
| `go/internal/planning/models.go` | Go equivalents of Python models |

### Test Coverage

| File | Focus |
|------|-------|
| `tests/test_autonomous_loop.py` | LoopRunner orchestration (6 test phases) |
| `context_window_array/tests/test_store.py` | Context store CRUD operations |
| `go/internal/planning/pipeline_test.go` | Go pipeline integration tests |
| `go/internal/planning/implementation_test.go` | Go implementation phase (155.8 KB of tests) |

---

## 📚 Historical Context (from thoughts/)

### Related Documentation Found

**Recent Research (2026-01-14):**
- `thoughts/research/2026-01-14-project-structure.md` - Comprehensive project structure analysis
- `thoughts/research/2026-01-14-pytest-fixtures.md` - Testing infrastructure

**Architecture Documentation (2025-12-31):**
- `thoughts/shared/research/2025-12-31-codebase-architecture.md` - Foundational architecture document describing:
  - 4-layer memory architecture
  - 6-phase pipeline
  - Multi-language implementation strategy

**How-To Guides:**
- `thoughts/shared/docs/2026-01-06-how-to-build-and-run-go-context-engine.md`
- `thoughts/shared/docs/2026-01-05-how-to-use-context-window-array.md`
- `thoughts/shared/docs/2026-01-03-how-to-run-pipeline-with-baml.md`
- `thoughts/shared/docs/2026-01-01-how-to-use-cli-commands.md`
- `thoughts/shared/docs/2025-12-31-how-to-run-planning-pipeline.md`

**TDD Plans (100+ plans):**
- `thoughts/shared/plans/2026-01-10-tdd-feature/` - 20+ requirement documents
- `thoughts/shared/plans/2026-01-04-tdd-context-window-array/`
- `thoughts/shared/plans/2026-01-03-tdd-codewriter5-baml-context-generation/`

---

## 🔗 Related Research

Research documents found in `thoughts/searchable/research/`:
- `2026-01-14-project-structure.md` - Full project structure analysis
- `2025-12-31-codebase-architecture.md` - Core architecture documentation
- Multiple dated research documents (363+ total) covering various technical topics

---

## ❓ Open Questions

*None - Research question fully answered.*

---

## 📊 Summary Statistics

<table>
<tr>
<th>Metric</th>
<th>Count</th>
</tr>
<tr>
<td><b>Total Main Directories</b></td>
<td>15</td>
</tr>
<tr>
<td><b>Implementation Languages</b></td>
<td>3 (Python, Go, BAML)</td>
</tr>
<tr>
<td><b>Python Source Directories</b></td>
<td>4 (agents, planning_pipeline, silmari_rlm_act, context_window_array)</td>
</tr>
<tr>
<td><b>Go Lines of Code</b></td>
<td>~24,877+ (planning package alone)</td>
</tr>
<tr>
<td><b>Python Test Files</b></td>
<td>40+</td>
</tr>
<tr>
<td><b>BAML Schema Files</b></td>
<td>26</td>
</tr>
<tr>
<td><b>Generated Pydantic Models</b></td>
<td>81</td>
</tr>
<tr>
<td><b>Agent Definitions</b></td>
<td>4 (feature-verifier, test-runner, code-reviewer, debugger)</td>
</tr>
<tr>
<td><b>Workflow Commands</b></td>
<td>7 (spec, status, next, blockers, debug, verify, revert)</td>
</tr>
<tr>
<td><b>Research Documents</b></td>
<td>363+</td>
</tr>
<tr>
<td><b>TDD Feature Plans</b></td>
<td>100+</td>
</tr>
<tr>
<td><b>How-To Guides</b></td>
<td>5+</td>
</tr>
<tr>
<td><b>Cross-Platform Binaries</b></td>
<td>6 (macOS arm64/x86_64, Linux arm64/x86_64, Windows x86_64)</td>
</tr>
</table>

---

```
╔═══════════════════════════════════════════════════════════════════════╗
║                           END OF RESEARCH                             ║
║                                                                       ║
║  This document provides a complete structural overview of the         ║
║  Silmari Context Engine's 15 main directories, their purposes,        ║
║  and architectural relationships.                                     ║
╚═══════════════════════════════════════════════════════════════════════╝
```
