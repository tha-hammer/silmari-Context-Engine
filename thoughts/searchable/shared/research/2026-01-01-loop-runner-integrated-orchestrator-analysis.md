---
date: 2026-01-01T17:41:33-05:00
researcher: Claude
git_commit: 462509e6dddac668d1853d5062be31f271fed0b6
branch: main
repository: silmari-Context-Engine
topic: "Loop Runner vs IntegratedOrchestrator: Port or Create New?"
tags: [research, loop-runner, integrated-orchestrator, beads, planning-pipeline, autonomous-loop]
status: complete
last_updated: 2026-01-01
last_updated_by: Claude
last_updated_note: "Added design decisions based on user feedback"
---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     LOOP RUNNER ANALYSIS                                     │
│         Port to IntegratedOrchestrator or Create New?                        │
│                                                                             │
│  Status: COMPLETE (Revised)                  Date: 2026-01-01               │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Research: Loop Runner vs IntegratedOrchestrator Analysis

**Date**: 2026-01-01T17:41:33-05:00
**Researcher**: Claude
**Git Commit**: 462509e6dddac668d1853d5062be31f271fed0b6
**Branch**: main
**Repository**: silmari-Context-Engine

---

## Research Question

Should `loop-runner.py` be ported to use the `integrated_orchestrator.py` pipeline with beads tracking and the enhanced research/planning pipeline, or should a new autonomous loop runner be created?

---

## Summary

The analysis reveals that **`loop-runner.py` and `IntegratedOrchestrator` are parallel systems serving different purposes**. The `IntegratedOrchestrator` (all 8 phases marked complete) provides beads-based state management for the **planning pipeline**, while `loop-runner.py` is a **feature execution engine** that runs Claude Code sessions.

| Recommendation | Rationale |
|----------------|-----------|
| **Create a new `AutonomousLoopRunner` class** | Best approach - leverages IntegratedOrchestrator for state while preserving loop-runner execution patterns |
| Port loop-runner.py directly | Not recommended - would require rewriting 1,382 lines of execution logic |
| Keep systems separate | Suboptimal - misses opportunity for unified beads tracking |

---

## Design Decisions

The following design decisions have been finalized:

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           DESIGN DECISIONS                                     ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  1. METRICS HOOKS                                                             ║
║     Decision: Use existing `.agent/hooks/` pattern                            ║
║     Rationale: Proven pattern, no changes needed to hook infrastructure       ║
║                                                                               ║
║  2. QA FEATURE HANDLING                                                       ║
║     Decision: QA as category in beads                                         ║
║     Rationale: Unified tracking, no separate workflow needed                  ║
║     Implementation: `bd create --type=task --category=qa`                     ║
║                                                                               ║
║  3. BACKWARDS COMPATIBILITY                                                   ║
║     Decision: No backwards compatibility for feature_list.json                ║
║     Rationale: Clean break, no migration complexity                           ║
║     Impact: Existing feature_list.json files will be ignored                  ║
║                                                                               ║
║  4. COMPLEXITY DETECTION                                                      ║
║     Decision: Build dependency graph from beads epic and dependencies         ║
║     Rationale: Leverage existing beads dependency structure                   ║
║     Implementation: Query epic children + dependencies to compute complexity  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### Complexity Detection from Beads

The current `loop-runner.py` uses heuristic keyword matching (lines 348-405) for complexity. The new approach will compute complexity from the beads dependency graph:

```python
def get_issue_complexity(self, issue_id: str) -> str:
    """Compute complexity from beads dependency graph.

    Complexity factors:
    - Number of dependencies (issues this depends on)
    - Number of dependents (issues that depend on this)
    - Depth in dependency chain from epic root
    - Number of sibling issues in same phase

    Returns: 'high', 'medium', or 'low'
    """
    issue = self.bd.show_issue(issue_id)

    # Count direct dependencies
    dep_count = len(issue.get("dependencies", []))

    # Count dependents (issues blocked by this one)
    all_issues = self.bd.list_issues()["data"]
    dependent_count = sum(
        1 for i in all_issues
        if any(d["depends_on_id"] == issue_id for d in i.get("dependencies", []))
    )

    # Compute complexity score
    score = dep_count + (dependent_count * 2)

    if score >= 5:
        return "high"
    elif score >= 2:
        return "medium"
    return "low"
```

This approach:
- Uses **actual dependency relationships** rather than keyword heuristics
- **Issues that block many others** are high complexity (more risk)
- **Issues with many dependencies** need careful coordination
- **Isolated issues** are low complexity

---

## Detailed Findings

### Current System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CURRENT STATE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  loop-runner.py (1,382 lines)          planning_pipeline/ (8 modules)       │
│  ════════════════════════════          ════════════════════════════════     │
│  • Autonomous execution loop           • Research → Plan → Decompose        │
│  • feature_list.json state             • IntegratedOrchestrator              │
│  • Claude Code sessions                • BeadsController (bd CLI)            │
│  • QA testing modes                    • Checkpoints & resume                │
│  • Metrics tracking                    • Session logging                     │
│  • Complexity detection                                                      │
│                                                                             │
│         ↓                                      ↓                            │
│  Executes features                      Creates beads issues                 │
│  from JSON file                         for plan phases                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1. loop-runner.py Components

**Location**: `/home/maceo/Dev/silmari-Context-Engine/loop-runner.py`

| Component | Lines | Purpose |
|-----------|-------|---------|
| Feature Validation | 40-106 | Validates `feature_list.json` schema |
| Dependency Detection | 108-148 | Circular dependency detection via DFS |
| Topological Sort | 154-209 | Kahn's algorithm for feature ordering |
| Blocked Workflow | 215-298 | Mark/unblock features with metadata |
| Metrics Tracking | 304-342 | Session metrics via hook scripts |
| Complexity Detection | 348-405 | Heuristic complexity estimation |
| Subagent Instructions | 407-443 | Dynamic prompt building by complexity |
| Session Execution | 959-1084 | Claude Code subprocess invocation |
| Main Loop | 1086-1381 | Autonomous session orchestration |

**Key Features:**
- Uses `feature_list.json` for state (lines 40-106)
- Runs `claude --permission-mode bypassPermissions -p <prompt>` (line 1070-1076)
- Supports QA testing with comprehensive checklists (lines 675-957)
- Tracks metrics via `.agent/hooks/` scripts (lines 304-342)
- Auto-completes features when tests pass (lines 1301-1348)

### 2. IntegratedOrchestrator Components

**Location**: `/home/maceo/Dev/silmari-Context-Engine/planning_pipeline/integrated_orchestrator.py`

| Method | Lines | Purpose |
|--------|-------|---------|
| `get_project_info()` | 18-69 | LLM-powered techstack detection |
| `get_feature_status()` | 71-101 | Status from `bd list` commands |
| `get_next_feature()` | 103-119 | Next ready issue via `bd ready` |
| `sync_features_with_git()` | 121-124 | Sync via `bd sync` |
| `create_phase_issues()` | 126-185 | Create beads issues for phases |
| `log_session()` | 187-227 | Session logging to `.agent/sessions/` |

**Key Features:**
- All 8 phases marked complete in TDD plan
- Uses `BeadsController` wrapper for `bd` CLI
- Delegates state to beads (not JSON files)
- Session logging to `.agent/sessions/`

### 3. BeadsController Capabilities

**Location**: `/home/maceo/Dev/silmari-Context-Engine/planning_pipeline/beads_controller.py`

<details>
<summary>Available Methods (click to expand)</summary>

| Method | Line | BD Command |
|--------|------|------------|
| `create_issue()` | 52-64 | `bd create --title=... --type=... --priority=...` |
| `create_epic()` | 66-68 | `bd create --type=epic` |
| `list_issues()` | 70-75 | `bd list [--status=...]` |
| `close_issue()` | 77-82 | `bd close <id> [--reason=...]` |
| `add_dependency()` | 84-86 | `bd dep add <id> <depends_on>` |
| `sync()` | 88-91 | `bd sync` |
| `get_ready_issue()` | 93-95 | `bd ready --limit=...` |
| `update_status()` | 97-99 | `bd update <id> --status=...` |
| `show_issue()` | 101-103 | `bd show <id>` |

</details>

---

## Comparison Analysis

### State Management Comparison

| Aspect | loop-runner.py | IntegratedOrchestrator |
|--------|---------------|------------------------|
| **State Storage** | `feature_list.json` (single JSON) | `.beads/issues.jsonl` (append-only log) |
| **Modification** | Direct file I/O (error-prone) | CLI subprocess (atomic) |
| **Dependency Graph** | Built in Python (154-209) | Maintained by `bd` CLI |
| **Ready Feature** | Computed via topological sort | Pre-computed by `bd ready` |
| **Git Sync** | One-way (git → JSON) | Two-way (bidirectional) |
| **Blocked State** | Explicit field + metadata | Implicit from dependencies |
| **Validation** | Python (40-106) | Delegated to `bd` |
| **Complexity** | 460+ lines of state logic | 104 lines (wrapper only) |

### Feature Execution Comparison

| Aspect | loop-runner.py | IntegratedOrchestrator |
|--------|---------------|------------------------|
| **Session Execution** | Full subprocess management (959-1084) | Not implemented |
| **QA Testing** | Comprehensive prompts (675-957) | Not implemented |
| **Metrics** | Hook script integration (304-342) | Session logging only |
| **Complexity Heuristics** | Automatic detection (348-405) | Not implemented |
| **Subagent Prompts** | Dynamic by complexity (407-443) | Not implemented |
| **Test Verification** | Independent verification (499-519) | Not implemented |

---

## Architectural Decision

### Option 1: Port loop-runner.py (NOT Recommended)

```
╔════════════════════════════════════════════════════════════════╗
║                    NOT RECOMMENDED                              ║
╚════════════════════════════════════════════════════════════════╝

Pros:
- Single codebase

Cons:
- Would require rewriting 1,382 lines of execution logic
- loop-runner.py has features IntegratedOrchestrator doesn't need
- QA testing, metrics, complexity detection are execution concerns
- feature_list.json migration to beads non-trivial
```

### Option 2: Create New AutonomousLoopRunner (RECOMMENDED)

```
╔════════════════════════════════════════════════════════════════╗
║                    RECOMMENDED APPROACH                         ║
╚════════════════════════════════════════════════════════════════╝

Create: planning_pipeline/autonomous_loop.py

class AutonomousLoopRunner:
    """Autonomous loop runner using IntegratedOrchestrator for state."""

    def __init__(self, project_path: Path):
        self.orchestrator = IntegratedOrchestrator(project_path)

    def run(self, max_sessions: int = 100):
        """Main execution loop."""
        while session <= max_sessions:
            # Use orchestrator for state
            status = self.orchestrator.get_feature_status()
            feature = self.orchestrator.get_next_feature()

            # Compute complexity from beads dependency graph
            complexity = self.get_issue_complexity(feature["id"])

            # Execute session (preserve loop-runner patterns)
            self._run_session(feature, complexity)

            # Track via existing .agent/hooks/
            self._track_metrics(feature["id"], "session_complete")

            # Log via orchestrator
            self.orchestrator.log_session(...)
```

**Benefits:**
- Leverages existing IntegratedOrchestrator (all phases complete)
- Preserves valuable execution logic from loop-runner.py
- Unified beads tracking for both planning and execution
- Session logging already implemented in orchestrator
- Complexity computed from actual dependency graph

### Option 3: Keep Systems Separate (Suboptimal)

```
╔════════════════════════════════════════════════════════════════╗
║                    SUBOPTIMAL                                   ║
╚════════════════════════════════════════════════════════════════╝

- Misses opportunity for unified beads tracking
- Duplicate state management patterns
- No visibility between planning and execution phases
```

---

## Recommended Implementation Path

### Phase 1: Create AutonomousLoopRunner Scaffold

```
╔═══════════════════════════════════════════════════════════════════╗
║  PHASE 1: Scaffold                                                 ║
║  Create autonomous_loop.py with IntegratedOrchestrator integration ║
╚═══════════════════════════════════════════════════════════════════╝
```

**New File**: `planning_pipeline/autonomous_loop.py`

| Component | Source | Purpose |
|-----------|--------|---------|
| `AutonomousLoopRunner.__init__` | New | Initialize with IntegratedOrchestrator |
| `AutonomousLoopRunner.run` | New | Main loop using orchestrator |
| `get_issue_complexity` | New | Compute complexity from beads dependencies |
| `_run_session` | Port from loop-runner:959-1084 | Execute Claude Code session |

### Phase 2: Port Execution Components

```
╔═══════════════════════════════════════════════════════════════════╗
║  PHASE 2: Execution Logic                                          ║
║  Port session execution from loop-runner.py                        ║
╚═══════════════════════════════════════════════════════════════════╝
```

| Function | Original Location | Action |
|----------|-------------------|--------|
| `run_session()` | loop-runner:959-1084 | Port as method |
| `build_prompt()` | loop-runner:1024-1067 | Port with modifications |
| `detect_test_command()` | loop-runner:458-471 | Port unchanged |
| `run_tests()` | loop-runner:473-497 | Port unchanged |

### Phase 3: Port QA and Metrics (Using Existing Hooks)

```
╔═══════════════════════════════════════════════════════════════════╗
║  PHASE 3: QA and Metrics                                           ║
║  Port QA testing, use existing .agent/hooks/ for metrics           ║
╚═══════════════════════════════════════════════════════════════════╝
```

| Function | Original Location | Action |
|----------|-------------------|--------|
| `build_qa_prompt()` | loop-runner:727-957 | Port unchanged |
| `track_metrics()` | loop-runner:304-314 | Port unchanged (uses `.agent/hooks/`) |
| `save_session_diff()` | loop-runner:316-327 | Port unchanged |
| `print_metrics_report()` | loop-runner:329-342 | Port unchanged |

**QA Category in Beads:**
```python
# Create QA issue in beads
self.bd.create_issue(
    title=f"QA: {feature_name}",
    issue_type="task",
    priority=100  # QA runs after implementation
)
# Detection: issue title starts with "QA:" or has qa_origin field
```

### Phase 4: Beads-Only State (No feature_list.json)

```
╔═══════════════════════════════════════════════════════════════════╗
║  PHASE 4: Beads-Only State                                         ║
║  Remove all feature_list.json operations - beads is source of truth║
╚═══════════════════════════════════════════════════════════════════╝
```

| Original Function | Lines | Replacement |
|-------------------|-------|-------------|
| `validate_feature_list()` | 40-106 | **REMOVED** - beads handles validation |
| `detect_circular_dependencies()` | 108-148 | **REMOVED** - `bd` handles this |
| `topological_sort_features()` | 154-209 | **REMOVED** - `bd ready` handles this |
| `get_feature_status()` | 562-584 | `orchestrator.get_feature_status()` |
| `get_next_feature()` | 586-629 | `orchestrator.get_next_feature()` |
| `mark_feature_blocked()` | 215-241 | `bd update <id> --status=blocked` |
| `get_feature_complexity()` | 348-405 | `get_issue_complexity()` (from dependency graph) |

### Phase 5: Complexity from Dependency Graph

```
╔═══════════════════════════════════════════════════════════════════╗
║  PHASE 5: Dependency-Based Complexity                              ║
║  Compute complexity from beads epic structure and dependencies     ║
╚═══════════════════════════════════════════════════════════════════╝
```

**New Method**: `AutonomousLoopRunner.get_issue_complexity()`

| Factor | Weight | Rationale |
|--------|--------|-----------|
| Direct dependencies | +1 each | More deps = more coordination |
| Dependents (blockers) | +2 each | Blocking others = high risk |
| Epic root distance | +1 per level | Deeper = more context needed |

**Complexity Thresholds:**
- **High**: score >= 5 (multiple deps, blocks others)
- **Medium**: score 2-4 (some deps or blockers)
- **Low**: score < 2 (isolated issue)

---

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TARGET STATE                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  planning_pipeline/autonomous_loop.py                                       │
│  ═══════════════════════════════════                                        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  AutonomousLoopRunner                                                │   │
│  │  ├── orchestrator: IntegratedOrchestrator                           │   │
│  │  │   └── bd: BeadsController (all state)                            │   │
│  │  │                                                                   │   │
│  │  ├── run()              → Main loop using orchestrator              │   │
│  │  ├── get_issue_complexity() → From beads dependency graph           │   │
│  │  ├── _run_session()     → Claude Code subprocess                    │   │
│  │  ├── _build_prompt()    → Dynamic by complexity                     │   │
│  │  ├── _build_qa_prompt() → QA checklists (category=qa in beads)     │   │
│  │  └── _track_metrics()   → Uses .agent/hooks/ (unchanged)           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  State Flow:                                                                │
│  ══════════                                                                 │
│  bd ready → get_next_feature() → get_issue_complexity() → _run_session()   │
│       ↓                                    ↓                    ↓           │
│  Beads deps      Dependency graph      Claude Code session                  │
│       ↓                                    ↓                                │
│  bd close → orchestrator.log_session() → .agent/sessions/                  │
│                                                                             │
│  No feature_list.json anywhere!                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Code References

### loop-runner.py Key Sections

| Section | Lines | Description |
|---------|-------|-------------|
| Feature validation | `loop-runner.py:40-106` | JSON schema checking |
| Dependency detection | `loop-runner.py:108-148` | Circular dependency DFS |
| Topological sort | `loop-runner.py:154-209` | Kahn's algorithm |
| Blocked workflow | `loop-runner.py:215-298` | Block/unblock with metadata |
| Metrics tracking | `loop-runner.py:304-342` | Hook script integration |
| Complexity detection | `loop-runner.py:348-405` | Heuristic estimation |
| Subagent instructions | `loop-runner.py:407-443` | Dynamic prompt building |
| QA prompts | `loop-runner.py:675-957` | Comprehensive QA checklists |
| Session execution | `loop-runner.py:959-1084` | Claude Code subprocess |
| Main loop | `loop-runner.py:1086-1381` | Autonomous orchestration |

### IntegratedOrchestrator Key Sections

| Section | Lines | Description |
|---------|-------|-------------|
| Project info detection | `integrated_orchestrator.py:18-69` | LLM-powered techstack |
| Feature status | `integrated_orchestrator.py:71-101` | Beads-based counts |
| Next feature | `integrated_orchestrator.py:103-119` | `bd ready` wrapper |
| Git sync | `integrated_orchestrator.py:121-124` | `bd sync` wrapper |
| Phase issue creation | `integrated_orchestrator.py:126-185` | Create beads for phases |
| Session logging | `integrated_orchestrator.py:187-227` | `.agent/sessions/` logs |

### BeadsController Methods

| Method | Lines | BD Command |
|--------|-------|------------|
| `_run_bd()` | `beads_controller.py:20-50` | Core command executor |
| `create_issue()` | `beads_controller.py:52-64` | `bd create` |
| `list_issues()` | `beads_controller.py:70-75` | `bd list` |
| `add_dependency()` | `beads_controller.py:84-86` | `bd dep add` |
| `sync()` | `beads_controller.py:88-91` | `bd sync` |
| `get_ready_issue()` | `beads_controller.py:93-95` | `bd ready` |
| `update_status()` | `beads_controller.py:97-99` | `bd update` |

---

## Historical Context (from thoughts/)

| Document | Path | Relevance |
|----------|------|-----------|
| IntegratedOrchestrator TDD Plan | `thoughts/shared/plans/2026-01-01-tdd-integrated-orchestrator.md` | All 8 phases complete |
| Phase Overview | `thoughts/shared/plans/2026-01-01-ENG-XXXX-tdd-integrated-orchestrator-00-overview.md` | Implementation details |
| Python Deterministic Pipeline | `thoughts/shared/plans/2025-12-31-tdd-python-deterministic-pipeline.md` | Pipeline control patterns |
| Resume Pipeline Integration | `thoughts/shared/plans/2026-01-01-tdd-resume-pipeline-integration.md` | Checkpoint patterns |

---

## Related Beads Issues

| Issue ID | Title | Status |
|----------|-------|--------|
| silmari-Context-Engine-3kj | IntegratedOrchestrator Implementation | open |
| silmari-Context-Engine-c0r | Python Deterministic Pipeline Control | open |

---

## Conclusion

The **recommended approach is to create a new `AutonomousLoopRunner` class** that:

1. Uses `IntegratedOrchestrator` for all state management (beads-based, no feature_list.json)
2. Preserves the session execution patterns from `loop-runner.py`
3. Uses existing `.agent/hooks/` for metrics tracking
4. Treats QA as a category in beads (title prefix "QA:" or metadata)
5. Computes complexity from beads dependency graph (not keyword heuristics)
6. Provides unified tracking across planning and execution phases

This approach leverages the completed `IntegratedOrchestrator` implementation while preserving the valuable execution logic from `loop-runner.py` without requiring a complete rewrite or backwards compatibility concerns.

---

## Implementation Progress

### Phase 5: Complexity from Dependency Graph - COMPLETE ✓

**Date**: 2026-01-03
**Implemented in**: `planning_pipeline/autonomous_loop.py`

The following features were implemented:

| Feature | Status | Location |
|---------|--------|----------|
| `get_issue_complexity()` | ✓ Complete | `autonomous_loop.py:208-274` |
| `detect_test_command()` | ✓ Complete | `autonomous_loop.py:56-75` |
| `run_tests()` | ✓ Complete | `autonomous_loop.py:78-108` |
| `get_subagent_instructions()` | ✓ Complete | `autonomous_loop.py:115-155` |
| `_track_metrics()` | ✓ Complete | `autonomous_loop.py:276-293` |
| `_save_session_diff()` | ✓ Complete | `autonomous_loop.py:295-312` |

### Complexity Calculation Algorithm

The complexity is computed from the beads dependency graph:

```
score = direct_dependencies + (dependents * 2)

if score >= 5:
    return "high"
elif score >= 2:
    return "medium"
return "low"
```

- **Direct dependencies**: Issues this one depends on (+1 each)
- **Dependents**: Issues that depend on this one (+2 each, higher weight = higher risk)

### Test Coverage

45 tests added covering:
- `TestLoopRunnerComplexity` (9 tests): Complexity detection from beads
- `TestLoopRunnerMetrics` (3 tests): Metrics hook tracking
- `TestHelperFunctions` (9 tests): Test detection and subagent instructions

All tests pass: `pytest tests/test_autonomous_loop.py` ✓

### Additional Features

The implementation also includes:
- Plan phase discovery (`plan_discovery.py`)
- Enhanced prompt building with phase context
- Skip overview support
- Session diff tracking

### Remaining Work

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Scaffold | ✓ Complete | `LoopRunner` class implemented |
| Phase 2: Execution Components | ✓ Complete | Session execution with metrics |
| Phase 3: QA and Metrics | ⚡ Partial | Metrics complete, QA prompts pending |
| Phase 4: Beads-Only State | ✓ Complete | Uses `IntegratedOrchestrator` |
| Phase 5: Dependency Complexity | ✓ Complete | `get_issue_complexity()` implemented |

**Next Steps**:
- Port full QA prompt building (`build_qa_prompt`) from loop-runner.py
- Add integration tests for full execution flow
- Document the new `plan_dir`/`plan_prefix` mode
