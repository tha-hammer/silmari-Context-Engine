# silmari-rlm-act: Autonomous TDD Pipeline

## Overview

**silmari-rlm-act** (Research, Learn, Model, Act) is an autonomous pipeline for TDD-based software development. It orchestrates the full cycle from research through implementation using the Context Window Array for context management and beads for task tracking.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           silmari-rlm-act Pipeline                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐   ┌──────────────┐   ┌──────────┐   ┌───────────┐            │
│  │ Research │ → │ Decomposition│ → │ TDD Plan │ → │ Multi-Doc │            │
│  └──────────┘   └──────────────┘   └──────────┘   └───────────┘            │
│       │              │                  │              │                    │
│       ▼              ▼                  ▼              ▼                    │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │              Context Window Array (CWA)                      │           │
│  │  ┌────────────────────────────────────────────────────────┐ │           │
│  │  │ CentralContextStore                                    │ │           │
│  │  │   - Research findings (FILE entries)                   │ │           │
│  │  │   - Requirements (TASK entries)                        │ │           │
│  │  │   - Plan documents (FILE entries)                      │ │           │
│  │  │   - Implementation context (COMMAND_RESULT entries)    │ │           │
│  │  └────────────────────────────────────────────────────────┘ │           │
│  └─────────────────────────────────────────────────────────────┘           │
│       │                                                                     │
│       ▼                                                                     │
│  ┌──────────┐   ┌───────────────────────────────────────────────┐          │
│  │  Beads   │ → │ Autonomous Implementation (with 3 modes)       │          │
│  │ Tracking │   │   - Checkpoint: pause at each phase            │          │
│  └──────────┘   │   - Fully autonomous: run all phases           │          │
│                 │   - Batch: group phases, pause between groups  │          │
│                 └───────────────────────────────────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Pipeline Phases

| Phase | Name | Description | CWA Entry Types | Beads Status |
|-------|------|-------------|-----------------|--------------|
| 01 | Research | Gather context about the task | FILE, SEARCH_RESULT | Creates epic |
| 02 | Decomposition | Break into testable behaviors | TASK | Creates phase issues |
| 03 | TDD Plan | Create Red-Green-Refactor plans | FILE | Updates issues |
| 04 | Multi-Doc | Split plan into phase documents | FILE | Links dependencies |
| 05 | Beads Sync | Track epochs and tasks | - | Sync to remote |
| 06 | Implementation | Execute TDD cycles | COMMAND_RESULT, TASK_RESULT | Close issues |

## User Interaction Points

### End of Research Phase
```
============================================================
RESEARCH COMPLETE
============================================================

Research document: thoughts/shared/research/2026-01-05-topic.md

What would you like to do?
  [C]ontinue to decomposition (default)
  [R]evise research with additional context
  [S]tart over with new prompt
  [E]xit pipeline

Choice [C/r/s/e]:
```

### Checkpoint Resume
```
Project: /home/maceo/Dev/silmari-Context-Engine

Found checkpoint from 2026-01-05T10:30:00
  Phase: decomposition-complete
  Artifacts:
    - thoughts/shared/plans/2026-01-05-tdd-feature/00-overview.md

Use this checkpoint? [Y/n]:

============================================================
SELECT RESUME POINT
============================================================

  [1] Continue from TDD Plan phase
  [2] Re-run decomposition
  [3] Start from research

Choice [1]:
```

### Autonomy Mode Selection
```
============================================================
IMPLEMENTATION READY
============================================================

Plan phases: 6
Beads epic: beads-abc123

Select execution mode:
  [C]heckpoint - pause at each phase for review (recommended)
  [F]ully autonomous - run all phases without stopping
  [B]atch - run groups of phases, pause between groups

Mode [C/f/b]:
```

## Directory Structure

```
silmari-rlm-act/
├── __init__.py
├── pipeline.py              # Main RLMActPipeline class
├── phases/
│   ├── __init__.py
│   ├── research.py          # Research phase
│   ├── decomposition.py     # Requirement decomposition
│   ├── tdd_planning.py      # TDD plan creation
│   ├── multi_doc.py         # Multi-document generation
│   ├── beads_sync.py        # Beads integration
│   └── implementation.py    # Autonomous implementation
├── context/
│   ├── __init__.py
│   ├── cwa_integration.py   # Context Window Array integration
│   └── context_builder.py   # Build contexts for LLMs
├── checkpoints/
│   ├── __init__.py
│   ├── manager.py           # Checkpoint read/write
│   └── interactive.py       # Interactive prompts
├── cli.py                   # CLI entry point
└── tests/
    ├── conftest.py
    ├── test_pipeline.py
    ├── test_phases.py
    ├── test_context.py
    └── test_checkpoints.py
```

## Phase Details

### Phase 01: Research
- **Input**: Research prompt from user
- **Output**: Research document in `thoughts/searchable/shared/research/`
- **CWA**: Store research findings as FILE entries with summaries
- **Checkpoint**: `research-complete` or `research-failed`

### Phase 02: Decomposition
- **Input**: Research document path
- **Output**: Requirement hierarchy JSON
- **CWA**: Store each requirement as TASK entry
- **Checkpoint**: `decomposition-complete` or `decomposition-failed`

### Phase 03: TDD Plan
- **Input**: Requirement hierarchy
- **Output**: TDD plan document
- **CWA**: Store plan as FILE entry, link to requirements
- **Checkpoint**: `tdd-plan-complete` or `tdd-plan-failed`

### Phase 04: Multi-Doc
- **Input**: TDD plan document
- **Output**: Phase documents (00-overview, 01-phase-1, etc.)
- **CWA**: Store each phase doc, update relationships
- **Checkpoint**: `multi-doc-complete` or `multi-doc-failed`

### Phase 05: Beads Sync
- **Input**: Phase documents
- **Output**: Beads epic + phase issues with dependencies
- **CWA**: Store beads issue IDs as metadata
- **Checkpoint**: `beads-sync-complete`

### Phase 06: Implementation
- **Input**: Phase documents, beads issues
- **Output**: Implemented code, tests, commits
- **CWA**: Store command results, manage <200 entry limit
- **Checkpoint**: Per-phase checkpoints based on mode

## Success Criteria

### Automated
- [ ] All tests pass: `pytest silmari-rlm-act/tests/ -v`
- [ ] Type checking: `mypy silmari-rlm-act/`
- [ ] Lint: `ruff check silmari-rlm-act/`
- [ ] Coverage >80%: `pytest --cov=silmari-rlm-act --cov-report=term-missing`

### Manual
- [ ] Pipeline runs end-to-end with sample prompt
- [ ] Interactive checkpoints work correctly
- [ ] Beads issues created and linked properly
- [ ] Resume from checkpoint works
- [ ] All 3 autonomy modes function correctly

## Implementation Phases

| TDD Phase | Behavior | Est. Tests | Status |
|-----------|----------|------------|--------|
| 01 | Core Models (PhaseResult, PipelineState, AutonomyMode, PhaseType, PhaseStatus) | 42 | **DONE** |
| 02 | Checkpoint Manager | 21 | **DONE** |
| 03 | Interactive Prompts | 54 | **DONE** |
| 04 | CWA Integration | 47 | **DONE** |
| 05 | Research Phase | 25 | **DONE** |
| 06 | Decomposition Phase | 11 | **DONE** |
| 07 | TDD Planning Phase | 21 | **DONE** |
| 08 | Multi-Doc Phase | 17 | **DONE** |
| 09 | Beads Sync Phase | 10 | Pending |
| 10 | Implementation Phase | 12 | Pending |
| 11 | Pipeline Orchestration | 15 | Pending |
| 12 | CLI Entry Point | 8 | Pending |

## References

- Context Window Array How-To: `thoughts/searchable/shared/docs/2026-01-05-how-to-use-context-window-array.md`
- Existing Pipeline: `planning_pipeline/` (patterns to follow, keep separate)
- Beads Controller: `planning_pipeline/beads_controller.py` (can reuse)
- Checkpoint Manager: `planning_pipeline/checkpoint_manager.py` (can adapt patterns)
