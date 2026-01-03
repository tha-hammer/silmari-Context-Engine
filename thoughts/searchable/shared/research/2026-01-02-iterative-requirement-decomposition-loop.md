---
date: 2026-01-02T08:12:10-05:00
researcher: maceo
git_commit: b82a157309757f73cde36f3a28eaabc6e2dbc10f
branch: main
repository: silmari-Context-Engine
topic: "Iterative Loop for Building Implementation Requirements Bottom-Up"
tags: [research, codebase, baml, requirements, iterative-loop, bottom-up-design, micro-steps, integration, pipeline]
status: complete
last_updated: 2026-01-02
last_updated_by: maceo
last_updated_note: "Added follow-up research for silmari-Context-Engine pipeline integration strategies"
---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│              ITERATIVE REQUIREMENT DECOMPOSITION LOOP RESEARCH              │
│                     Building Complex Systems Bottom-Up                      │
│                                                                             │
│                      Status: COMPLETE | Date: 2026-01-02                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Research: Iterative Loop for Building Implementation Requirements

**Date**: 2026-01-02T08:12:10-05:00
**Researcher**: maceo
**Git Commit**: b82a157309757f73cde36f3a28eaabc6e2dbc10f
**Branch**: main
**Repository**: silmari-Context-Engine

---

## Research Question

How to build an iterative loop for creating implementation requirements that starts with a single behavior and builds needed functionality in micro-steps to maximize LLM thinking power. The pattern should:

1. Start with individual tasks (finite number of 4-5 tasks)
2. Then build class structure: initialization needs, functions for each task
3. Build complex systems bottom-up using progressive decomposition

---

## 📚 Summary

The CodeWriter5 codebase implements a sophisticated **Gate-based iterative decomposition pattern** that progressively breaks down requirements into hierarchical structures using LLM-powered micro-step generation. The core pattern follows:

| Phase | Purpose | Output |
|-------|---------|--------|
| **Gate 1** | Initial Extraction | Top-level requirements with sub-processes |
| **Gate 2** | Gap Analysis | Missing requirements identified |
| **Gate 3** | Subprocess Analysis | Implementation details per sub-process |
| **Expansion** | Dimension Analysis | User interactions, data needs, business rules |

The pattern is implemented through:
- **BAML functions** (`functions.baml`) - Type-safe LLM prompts with schema validation
- **AnalysisOrchestrator** (`analysis_orchestrator.py`) - Phase-based loop controller
- **RequirementsProcessor** (`requirements_processor.py`) - Hierarchical state builder

---

## 📊 Detailed Findings

### 🎯 Pattern 1: Gate-Based Iterative Decomposition

**Location**: `/home/maceo/Dev/CodeWriter5/code-writer/baml_src/functions.baml`

The BAML functions define the iterative loop stages:

```
┌─────────────────────────────────────────────────────────────────┐
│                     GATE 1 DECOMPOSITION FLOW                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ProcessGate1InitialExtractionPrompt (line 408)                │
│              │                                                  │
│              ▼                                                  │
│   ProcessGate1GapAnalysisPrompt (line 497)                      │
│              │                                                  │
│              ▼                                                  │
│   ProcessGate1SubprocessAnalysisPrompt (line 523)               │
│              │                                                  │
│   ┌─────────┴─────────┐                                         │
│   ▼                   ▼                                         │
│ ProcessGate1SubprocessDetailsPrompt (line 618)                  │
│              │                                                  │
│   ┌─────────┼─────────┬─────────┐                               │
│   ▼         ▼         ▼         ▼                               │
│ Category  Category  Category  Category                          │
│ Functional Security  Perform.  Usability                        │
│ (line 663) (line 723) (line 762) (line 801)                     │
│                                                                 │
│              │                                                  │
│   ┌─────────┼─────────┬─────────┐                               │
│   ▼         ▼         ▼                                         │
│ UserInteractions  DataNeeds  BusinessRules                      │
│   (line 878)     (line 926)   (line 975)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key BAML Functions Table**:

| Function | Line | Purpose |
|----------|------|---------|
| `ProcessGate1InitialExtractionPrompt` | 408 | Extract top-level requirements |
| `ProcessGate1GapAnalysisPrompt` | 497 | Find missing requirements |
| `ProcessGate1SubprocessAnalysisPrompt` | 523 | Break into sub-processes |
| `ProcessGate1SubprocessDetailsPrompt` | 618 | Implementation details per sub-process |
| `ProcessGate1CategoryFunctionalPrompt` | 663 | Functional requirement analysis |
| `ProcessGate1CategorySecurityPrompt` | 723 | Security requirement analysis |
| `ProcessGate1UserInteractionsPrompt` | 878 | User interaction expansion |
| `ProcessGate1DataNeedsPrompt` | 926 | Data structure expansion |
| `ProcessGate1BusinessRulesPrompt` | 975 | Business rule expansion |

---

### 🎯 Pattern 2: Phase-Based Orchestration Loop

**Location**: `/home/maceo/Dev/CodeWriter5/code-writer/src2/scope/analysis_orchestrator.py:134-180`

The `AnalysisOrchestrator` implements the main iterative loop:

```python
async def run(self, scope_text: str, session_name: str = "default", max_steps: int = 1):
    state = self.sessions.load(session_name) or {"progress": 0, "requirements": None}
    steps = 0

    while steps < max_steps:
        if state["progress"] == 0:
            # Phase 1: Initial extraction
            state = await self._handle_initial_extraction_phase(scope_text, session_name, state)
        elif state["progress"] == 1:
            # Phase 2: Subprocess analysis
            state = await self._handle_subprocess_analysis_phase(session_name, state)
        else:
            break
        steps += 1

    return state
```

**Loop Characteristics**:
| Aspect | Implementation |
|--------|----------------|
| Progress Tracking | `state["progress"]` counter (0, 1, 2...) |
| State Persistence | `self.sessions.save(session_name, state)` after each phase |
| Error Handling | `_handle_phase_error()` with graceful degradation |
| Max Steps Guard | `max_steps` parameter prevents infinite loops |

---

### 🎯 Pattern 3: Hierarchical Requirement Building (3-Tier)

**Location**: `/home/maceo/Dev/CodeWriter5/code-writer/src2/scope/requirements_processor.py:281-364`

The `RequirementsProcessor` builds a 3-tier hierarchy:

```
┌─────────────────────────────────────────────────────────────────┐
│                   3-TIER REQUIREMENT HIERARCHY                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   TIER 1: Parent Requirement                                    │
│   ┌────────────────────────────────────────┐                    │
│   │ id: REQ_001                            │                    │
│   │ type: "parent"                         │                    │
│   │ parent_id: None                        │                    │
│   │ children: ["REQ_001.2", "REQ_001.3"]   │                    │
│   └────────────────────────────────────────┘                    │
│              │                                                  │
│   ┌──────────┴──────────┐                                       │
│   ▼                     ▼                                       │
│                                                                 │
│   TIER 2: Sub-Process Requirements                              │
│   ┌──────────────────────┐  ┌──────────────────────┐            │
│   │ id: REQ_001.2        │  │ id: REQ_001.3        │            │
│   │ type: "sub_process"  │  │ type: "sub_process"  │            │
│   │ parent_id: REQ_001   │  │ parent_id: REQ_001   │            │
│   │ children: [...]      │  │ children: [...]      │            │
│   └──────────────────────┘  └──────────────────────┘            │
│              │                                                  │
│   ┌──────────┴──────────┐                                       │
│   ▼                     ▼                                       │
│                                                                 │
│   TIER 3: Implementation Details                                │
│   ┌──────────────────────────┐  ┌──────────────────────────┐    │
│   │ id: REQ_001.2.1          │  │ id: REQ_001.2.2          │    │
│   │ type: "implementation"   │  │ type: "implementation"   │    │
│   │ parent_id: REQ_001.2     │  │ parent_id: REQ_001.2     │    │
│   │ acceptance_criteria: []  │  │ acceptance_criteria: []  │    │
│   │ implementation: {        │  │ implementation: {        │    │
│   │   frontend: [...],       │  │   frontend: [...],       │    │
│   │   backend: [...],        │  │   backend: [...],        │    │
│   │   middleware: [...],     │  │   middleware: [...],     │    │
│   │   shared: [...]          │  │   shared: [...]          │    │
│   │ }                        │  │ }                        │    │
│   └──────────────────────────┘  └──────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**ID Generation Strategy**:
| Method | ID Format | Example |
|--------|-----------|---------|
| `_next_top_id()` | `REQ_{counter:03d}` | REQ_001, REQ_002 |
| `add_child()` | `{parent_id}.{sequence}` | REQ_001.2, REQ_001.2.1 |

**Core Methods**:
| Method | Line | Purpose |
|--------|------|---------|
| `add_requirement()` | 146 | Create top-level requirement |
| `add_child()` | 173 | Add micro-step to parent |
| `create_sub_process_requirements()` | 281 | Build full 3-tier hierarchy |
| `analyze_sub_process_details()` | 366 | LLM expansion per sub-process |

---

### 🎯 Pattern 4: LLM Proposal and Review Loop

**Location**: `/home/maceo/Dev/CodeWriter5/code-writer/src2/scope/analysis_orchestrator.py:182-303`

The pattern for LLM-driven micro-step generation:

```python
# Step 1: LLM proposes subprocesses
proposals = await self._propose_subprocesses_via_llm(parent)

# Step 2: User reviews each proposal
for proposal in proposals:
    self.ui.display_subprocess_proposal(proposal, i, len(proposals))
    action = self.ui.prompt_for_choice("Action?", ["accept", "modify", "reject"])

    if action == "accept" or action == "modify":
        # Step 3: Add approved child
        child_id = rp.add_child(
            parent_id=parent["id"],
            description=proposal["description"],
            acceptance_criteria=proposal["acceptance_criteria"],
            implementation=proposal["implementation"],
        )
```

**Review Actions**:
| Action | Behavior |
|--------|----------|
| `accept` | Add proposal as-is |
| `modify` | Prompt for changes, then add |
| `reject` | Skip this proposal |

---

### 🎯 Pattern 5: Dimension-Based Expansion

**Location**: `/home/maceo/Dev/CodeWriter5/code-writer/src2/scope/analysis_orchestrator.py:1242-1406`

Expansion along three analytical dimensions:

| Dimension | BAML Function | Focus Area |
|-----------|---------------|------------|
| `user_interactions` | `ProcessGate1UserInteractionsPrompt` | UI/UX, workflows, user actions |
| `data_needs` | `ProcessGate1DataNeedsPrompt` | Data structures, storage, flow |
| `business_rules` | `ProcessGate1BusinessRulesPrompt` | Logic, validation, decisions |

Each dimension returns structured children with:
- `description` - What to implement
- `acceptance_criteria` - How to verify
- `related_concepts` - Dependencies
- `implementation` - Component breakdown (frontend/backend/middleware/shared)

---

### 🎯 Pattern 6: Incremental Save During Processing

**Location**: `/home/maceo/Dev/CodeWriter5/code-writer/src2/scope/analysis_orchestrator.py:798-859`

Critical for long-running LLM operations:

```python
for idx, req in enumerate(found, start=1):
    # Process requirement
    await self._process_requirement_hierarchy(req, parent_id, rp)

    # CRITICAL: Save after each requirement
    state["requirements"] = rp.to_dict()
    self.sessions.save(session_name, state)
    self.ui.print_info(f"Progress saved ({idx}/{total})")
```

**Benefits**:
| Benefit | How Achieved |
|---------|--------------|
| Crash recovery | Save after each requirement |
| Progress visibility | UI feedback on save |
| Resume capability | Session state persisted |

---

## 🚀 How to Apply This Pattern: "Subagent Tracker" Example

For building a "Subagent Tracker" using this pattern:

### Phase 1: Initial Behavior Identification
```
┌───────────────────────────────────────────────────────────────┐
│ Input: "Build a Subagent Tracker"                             │
│                                                               │
│ LLM Output (ProcessGate1InitialExtractionPrompt):             │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ requirements: [                                           │ │
│ │   {                                                       │ │
│ │     description: "Track subagent lifecycle",              │ │
│ │     sub_processes: [                                      │ │
│ │       "Initialize tracking",                              │ │
│ │       "Register new subagent",                            │ │
│ │       "Update subagent status",                           │ │
│ │       "Query active subagents",                           │ │
│ │       "Cleanup completed subagents"                       │ │
│ │     ]                                                     │ │
│ │   }                                                       │ │
│ │ ]                                                         │ │
│ └───────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

### Phase 2: Class Structure Derivation
```
┌───────────────────────────────────────────────────────────────┐
│ LLM Output (ProcessGate1SubprocessDetailsPrompt per task):    │
│                                                               │
│ For "Initialize tracking":                                    │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ implementation_details: [                                 │ │
│ │   {                                                       │ │
│ │     description: "Create SubagentTracker class",          │ │
│ │     implementation: {                                     │ │
│ │       backend: ["SubagentTracker.__init__()"],            │ │
│ │       shared: ["SubagentState enum", "SubagentInfo model"]│ │
│ │     }                                                     │ │
│ │   },                                                      │ │
│ │   {                                                       │ │
│ │     description: "Initialize tracking dictionary",        │ │
│ │     implementation: {                                     │ │
│ │       backend: ["self._agents: Dict[str, SubagentInfo]"]  │ │
│ │     }                                                     │ │
│ │   }                                                       │ │
│ │ ]                                                         │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                               │
│ For "Register new subagent":                                  │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ implementation_details: [                                 │ │
│ │   {                                                       │ │
│ │     description: "Implement register() method",           │ │
│ │     implementation: {                                     │ │
│ │       backend: ["SubagentTracker.register(agent_id, info)"]│ │
│ │     },                                                    │ │
│ │     acceptance_criteria: [                                │ │
│ │       "Must validate agent_id uniqueness",                │ │
│ │       "Must set initial state to PENDING",                │ │
│ │       "Must record registration timestamp"                │ │
│ │     ]                                                     │ │
│ │   }                                                       │ │
│ │ ]                                                         │ │
│ └───────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

### Phase 3: Resulting Hierarchy
```
REQ_001: Track subagent lifecycle (parent)
├── REQ_001.2: Initialize tracking (sub_process)
│   ├── REQ_001.2.1: Create SubagentTracker class (implementation)
│   └── REQ_001.2.2: Initialize tracking dictionary (implementation)
├── REQ_001.3: Register new subagent (sub_process)
│   └── REQ_001.3.1: Implement register() method (implementation)
├── REQ_001.4: Update subagent status (sub_process)
│   └── REQ_001.4.1: Implement update_status() method (implementation)
├── REQ_001.5: Query active subagents (sub_process)
│   └── REQ_001.5.1: Implement get_active() method (implementation)
└── REQ_001.6: Cleanup completed subagents (sub_process)
    └── REQ_001.6.1: Implement cleanup() method (implementation)
```

---

## 📋 Code References

### Primary Implementation Files

| File | Purpose |
|------|---------|
| `/home/maceo/Dev/CodeWriter5/code-writer/baml_src/functions.baml` | BAML function definitions |
| `/home/maceo/Dev/CodeWriter5/code-writer/src2/scope/analysis_orchestrator.py` | Main loop orchestrator |
| `/home/maceo/Dev/CodeWriter5/code-writer/src2/scope/requirements_processor.py` | Hierarchical state management |

### Prompt Template Files

| File | Purpose |
|------|---------|
| `src2/scope/prompts/requirement_extraction_prompts.py` | Initial extraction |
| `src2/scope/prompts/sub_process_analysis_prompts.py` | Subprocess details |
| `src2/scope/prompts/expansion_prompts.py` | Dimension expansions |
| `src2/scope/prompts/category_prompts.py` | Category analysis |

### Supporting Files

| File | Purpose |
|------|---------|
| `src2/scope/session_manager.py` | Session persistence |
| `src2/scope/interactive_ui.py` | User confirmation |
| `src2/scope/llm_conversation.py` | LLM communication |

---

## 🛡️ Architecture Documentation

### Loop Pattern Summary

```
┌────────────────────────────────────────────────────────────────────┐
│                    ITERATIVE DECOMPOSITION LOOP                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   ┌─────────────┐                                                  │
│   │ Start with  │                                                  │
│   │ Scope Text  │                                                  │
│   └──────┬──────┘                                                  │
│          │                                                         │
│          ▼                                                         │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │ GATE 1: Initial Extraction                                  │  │
│   │ ┌─────────────────────────────────────────────────────────┐ │  │
│   │ │ ProcessGate1InitialExtractionPrompt                     │ │  │
│   │ │ → Extract top-level requirements                        │ │  │
│   │ │ → Identify sub-processes (4-5 per requirement)          │ │  │
│   │ └─────────────────────────────────────────────────────────┘ │  │
│   └──────────────────────────┬──────────────────────────────────┘  │
│                              │                                     │
│          ┌───────────────────┴───────────────────┐                 │
│          ▼                                       ▼                 │
│   ┌────────────────────┐              ┌────────────────────┐       │
│   │ Gap Analysis       │              │ Subprocess Analysis│       │
│   │ (optional)         │              │ (per sub-process)  │       │
│   └────────────────────┘              └─────────┬──────────┘       │
│                                                 │                  │
│                                                 ▼                  │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │ SUBPROCESS DETAILS LOOP (per sub-process)                   │  │
│   │ ┌─────────────────────────────────────────────────────────┐ │  │
│   │ │ ProcessGate1SubprocessDetailsPrompt                     │ │  │
│   │ │ → Break into implementation details                     │ │  │
│   │ │ → Generate acceptance criteria                          │ │  │
│   │ │ → Identify components (frontend/backend/middleware)     │ │  │
│   │ └─────────────────────────────────────────────────────────┘ │  │
│   │                              │                              │  │
│   │                              ▼                              │  │
│   │ ┌─────────────────────────────────────────────────────────┐ │  │
│   │ │ USER REVIEW LOOP (per proposal)                         │ │  │
│   │ │ → Display proposal                                      │ │  │
│   │ │ → Accept / Modify / Reject                              │ │  │
│   │ │ → Add to hierarchy if approved                          │ │  │
│   │ └─────────────────────────────────────────────────────────┘ │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                              │                                     │
│                              ▼                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │ EXPANSION LOOP (optional, per dimension)                    │  │
│   │ ┌───────────────────┬──────────────────┬──────────────────┐ │  │
│   │ │ User Interactions │   Data Needs     │  Business Rules  │ │  │
│   │ │ → UI/UX flows     │   → Data models  │  → Validation    │ │  │
│   │ │ → User actions    │   → Storage      │  → Decisions     │ │  │
│   │ │ → Workflows       │   → Data flow    │  → Logic         │ │  │
│   │ └───────────────────┴──────────────────┴──────────────────┘ │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                              │                                     │
│                              ▼                                     │
│   ┌─────────────┐                                                  │
│   │ 3-Tier      │                                                  │
│   │ Hierarchy   │                                                  │
│   │ Complete    │                                                  │
│   └─────────────┘                                                  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| 3-tier hierarchy | Parent → Sub-Process → Implementation provides clear abstraction levels |
| ID encoding | Hierarchical IDs (REQ_001.2.1) make relationships visible in ID |
| Flat storage | All items in category bucket enables easy iteration and query |
| BAML + fallback | Type safety with graceful degradation to raw LLM |
| Incremental save | Prevents data loss during long LLM operations |
| User review loop | Human-in-the-loop ensures quality and relevance |

---

## 📖 Historical Context (from thoughts/)

Related planning documents using this pattern:

| Document | Description |
|----------|-------------|
| `thoughts/shared/plans/2026-01-01-tdd-baml-integration.md` | Master TDD plan for BAML integration |
| `thoughts/shared/plans/2026-01-01-tdd-integrated-orchestrator.md` | Orchestrator integration plan |
| `thoughts/shared/plans/2026-01-01-tdd-loop-runner-integrated-orchestrator.md` | Loop runner plan |
| `thoughts/shared/research/2026-01-01-baml-integration-research.md` | BAML research findings |
| `thoughts/shared/research/2025-12-31-python-deterministic-pipeline-control.md` | Pipeline control research |

All plans follow the same micro-step decomposition pattern:
- Master plan → Overview phase → Numbered implementation phases
- Each phase builds on previous (bottom-up)
- TDD approach with tests before implementation

---

## ❓ Open Questions

1. **Multi-language support**: How to extend the pattern for generating requirements in different tech stacks simultaneously?
2. **Parallelization**: Could subprocess analysis be parallelized across multiple LLM calls?
3. **Confidence scoring**: How to rank LLM proposals by confidence for better prioritization?

---

## 📚 Related Research

- `thoughts/shared/research/2026-01-01-baml-integration-research.md` - BAML schema patterns
- `thoughts/shared/research/2026-01-01-planning-orchestrator-integration.md` - Orchestrator patterns
- `thoughts/shared/research/2025-12-31-codebase-architecture.md` - Overall architecture

---

## Follow-up Research 2026-01-02T09:58:49-05:00

### Integration with silmari-Context-Engine Pipeline

The user asked: How to incorporate the BAML-based iterative requirement decomposition into the current silmari-Context-Engine pipeline, positioned **after research** and **before implementation planning**.

---

### 🎯 Current Pipeline Architecture Analysis

The silmari-Context-Engine has a **5-step planning pipeline**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CURRENT PIPELINE FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Step 1: Research (step_research)                                          │
│      │ • Loads research_codebase.md template                                │
│      │ • Calls Claude Code CLI via run_claude_sync()                        │
│      │ • Outputs: research.md file                                          │
│      ▼                                                                      │
│   [Checkpoint: approve/revise/restart]                                      │
│      │                                                                      │
│      ▼                                                                      │
│   Memory Sync (step_memory_sync)                                            │
│      │                                                                      │
│      ▼                                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 🎯 NEW: Requirement Decomposition Step (step_requirement_decomp)    │   │
│   │    • BAML-based iterative micro-step generation                     │   │
│   │    • Uses ProcessGate1InitialExtractionPrompt                       │   │
│   │    • Uses ProcessGate1SubprocessDetailsPrompt                       │   │
│   │    • Outputs: requirements_hierarchy.json                           │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│      │                                                                      │
│      ▼                                                                      │
│   Step 2: Planning (step_planning)                                          │
│      │ • Receives requirements_hierarchy.json as input                      │
│      │ • Generates implementation plan with micro-steps                     │
│      │ • Outputs: plan.md with structured tasks                             │
│      ▼                                                                      │
│   [Checkpoint: approve/provide feedback]                                    │
│      │                                                                      │
│      ▼                                                                      │
│   Step 3: Phase Decomposition                                               │
│      │                                                                      │
│      ▼                                                                      │
│   Step 4: Beads Integration                                                 │
│      │                                                                      │
│      ▼                                                                      │
│   Step 5: Memory Capture                                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Finding**: BAML functions are currently **defined but NOT integrated** into the pipeline. The pipeline uses `run_claude_sync()` which calls Claude Code CLI directly with text prompts.

---

### 📊 Integration Strategy Options

#### Strategy 1: Direct BAML Integration (Recommended)

**Approach**: Add a new pipeline step that uses BAML directly via Python API calls.

```python
# planning_pipeline/steps.py - NEW STEP

async def step_requirement_decomposition(
    project_path: Path,
    research_path: str
) -> dict[str, Any]:
    """
    Iterative requirement decomposition using BAML functions.

    Position: After research, before planning.
    Uses: BAML API calls (NOT Claude Code CLI)
    """
    from baml_client import b as baml_client
    import asyncio

    # 1. Read research document to extract scope
    research_content = Path(research_path).read_text()
    scope_text = extract_scope_from_research(research_content)

    # 2. Initial extraction (top-level requirements with sub-processes)
    initial_response = await asyncio.to_thread(
        baml_client.ProcessGate1InitialExtractionPrompt,
        scope_text=scope_text,
        analysis_framework="comprehensive",
        user_confirmation=True
    )

    requirements = []
    for req in initial_response.requirements:
        parent = {
            "id": generate_id(),
            "description": req.description,
            "type": "parent",
            "sub_processes": req.sub_processes,
            "children": []
        }

        # 3. Subprocess expansion (per sub-process)
        for sub_process in req.sub_processes:
            details_response = await asyncio.to_thread(
                baml_client.ProcessGate1SubprocessDetailsPrompt,
                sub_process=sub_process,
                parent_description=req.description,
                scope_text=scope_text,
                user_confirmation=True
            )

            for detail in details_response.implementation_details:
                child = {
                    "id": generate_child_id(parent["id"]),
                    "description": detail.description,
                    "type": "implementation",
                    "acceptance_criteria": detail.acceptance_criteria,
                    "implementation": {
                        "frontend": detail.implementation.frontend,
                        "backend": detail.implementation.backend,
                        "middleware": detail.implementation.middleware,
                        "shared": detail.implementation.shared
                    }
                }
                parent["children"].append(child)

        requirements.append(parent)

    # 4. Save requirements hierarchy
    output_path = project_path / "thoughts/searchable/shared/requirements_hierarchy.json"
    output_path.write_text(json.dumps(requirements, indent=2))

    return {
        "success": True,
        "requirements_path": str(output_path),
        "requirement_count": len(requirements),
        "total_micro_steps": sum(len(r["children"]) for r in requirements)
    }
```

**Pros**:
| Benefit | Description |
|---------|-------------|
| Type Safety | BAML provides schema validation automatically |
| No CLI Overhead | Direct Python API calls are faster |
| Structured Output | JSON requirements hierarchy for planning step |
| Retry Logic | BAML handles parsing retries internally |

**Cons**:
| Drawback | Description |
|----------|-------------|
| New Dependency | Requires BAML client in pipeline |
| Environment Setup | Needs OLLAMA_MODEL / API key env vars |

---

#### Strategy 2: Claude Code CLI with BAML Prompt Template

**Approach**: Generate BAML-style prompts but execute via existing `run_claude_sync()`.

```python
def step_requirement_decomposition_via_cli(
    project_path: Path,
    research_path: str
) -> dict[str, Any]:
    """
    Uses existing Claude Code CLI but with BAML-style structured prompts.
    """

    prompt = f"""
You are an expert software requirements analyst. Analyze the research document
and extract implementation requirements using a 3-tier hierarchy.

RESEARCH DOCUMENT:
{Path(research_path).read_text()}

OUTPUT FORMAT (JSON):
{{
  "requirements": [
    {{
      "id": "REQ_001",
      "description": "Top-level requirement",
      "type": "parent",
      "sub_processes": ["task1", "task2", "task3"],
      "children": [
        {{
          "id": "REQ_001.1",
          "description": "Implementation detail",
          "type": "implementation",
          "acceptance_criteria": ["criterion1", "criterion2"],
          "implementation": {{
            "frontend": ["Component1"],
            "backend": ["Service1"],
            "middleware": [],
            "shared": ["Model1"]
          }}
        }}
      ]
    }}
  ]
}}

Process each requirement:
1. Extract 4-5 sub_processes per requirement
2. For each sub_process, generate implementation details with acceptance criteria
3. Specify which components (frontend/backend/middleware/shared) are needed

Output ONLY the JSON, no explanations.
"""

    result = run_claude_sync(prompt=prompt, timeout=1200)

    # Parse and save
    requirements = extract_json_object(result["output"])
    output_path = project_path / "requirements_hierarchy.json"
    output_path.write_text(json.dumps(requirements, indent=2))

    return {"success": True, "requirements_path": str(output_path)}
```

**Pros**:
| Benefit | Description |
|---------|-------------|
| No New Dependencies | Uses existing `run_claude_sync()` |
| Familiar Pattern | Same CLI approach as other steps |

**Cons**:
| Drawback | Description |
|----------|-------------|
| No Type Safety | Manual JSON parsing needed |
| Larger Prompts | Full prompt in each call |
| No Retry Logic | Must handle failures manually |

---

#### Strategy 3: Hybrid Approach (Recommended for Production)

**Approach**: BAML for type-safe LLM calls, CLI for tool-enabled steps.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HYBRID INTEGRATION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   BAML Functions (API Calls)           Claude Code CLI (Subprocess)         │
│   ─────────────────────────            ───────────────────────────          │
│   • ProcessGate1Initial...             • Research step (needs tools)        │
│   • ProcessGate1Subprocess...          • Planning step (needs tools)        │
│   • ProcessGate1Category...            • Phase decomposition (needs tools)  │
│                                                                             │
│   Use When:                            Use When:                            │
│   ─────────                            ─────────                            │
│   • Pure LLM reasoning                 • File creation/editing              │
│   • Structured output needed           • Git operations                     │
│   • No tool access needed              • Multi-step tool sequences          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 📋 Data Model for Integration

**RequirementHierarchy**: Bridge between BAML output and pipeline.

```python
# planning_pipeline/models.py

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ImplementationComponents:
    """Component breakdown for implementation."""
    frontend: list[str] = field(default_factory=list)
    backend: list[str] = field(default_factory=list)
    middleware: list[str] = field(default_factory=list)
    shared: list[str] = field(default_factory=list)

@dataclass
class RequirementNode:
    """Single node in requirement hierarchy."""
    id: str
    description: str
    type: str  # "parent" | "sub_process" | "implementation"
    parent_id: Optional[str] = None
    children: list["RequirementNode"] = field(default_factory=list)
    sub_processes: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    related_concepts: list[str] = field(default_factory=list)
    implementation: Optional[ImplementationComponents] = None

@dataclass
class RequirementHierarchy:
    """Complete requirement hierarchy from decomposition."""
    requirements: list[RequirementNode]
    metadata: dict = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize for pipeline passing."""
        import json
        return json.dumps(self._to_dict(), indent=2)

    def to_planning_prompt_context(self) -> str:
        """Generate context for planning step prompt."""
        lines = ["## Requirements to Implement\n"]
        for req in self.requirements:
            lines.append(f"### {req.id}: {req.description}\n")
            for child in req.children:
                lines.append(f"- [ ] **{child.id}**: {child.description}")
                for criterion in child.acceptance_criteria:
                    lines.append(f"  - {criterion}")
                if child.implementation:
                    if child.implementation.backend:
                        lines.append(f"  - Backend: {', '.join(child.implementation.backend)}")
                    if child.implementation.frontend:
                        lines.append(f"  - Frontend: {', '.join(child.implementation.frontend)}")
            lines.append("")
        return "\n".join(lines)
```

---

### 🎯 Pipeline Integration Point

**Modified PlanningPipeline.run()** at `/home/maceo/Dev/silmari-Context-Engine/planning_pipeline/pipeline.py`:

```python
def run(self, research_prompt: str, ticket_id: Optional[str] = None,
        auto_approve: bool = False) -> dict[str, Any]:

    # ... existing Step 1: Research ...

    # Memory sync (existing)
    memory_result = step_memory_sync(self.project_path, research["research_path"], session_id)

    # NEW: Step 1.5 - Requirement Decomposition
    print_step_header("Step 1.5: Requirement Decomposition")
    decomp_result = step_requirement_decomposition(
        self.project_path,
        research["research_path"]
    )
    results["steps"]["decomposition"] = decomp_result

    if not decomp_result["success"]:
        write_checkpoint(self.project_path, "decomposition-failed", [], [decomp_result.get("error")])
        return results

    print(f"✅ Extracted {decomp_result['requirement_count']} requirements with "
          f"{decomp_result['total_micro_steps']} implementation steps")

    # Step 2: Planning (MODIFIED to receive requirements)
    additional_context = ""
    while True:
        planning = step_planning(
            self.project_path,
            research["research_path"],
            additional_context,
            requirements_path=decomp_result["requirements_path"]  # NEW PARAMETER
        )
        # ... rest of planning step ...
```

---

### 📊 Environment Configuration

**Required Environment Variables**:

```bash
# .env file for BAML client
OLLAMA_MODEL=gemma3:latest          # For local Ollama
# OR
ANTHROPIC_API_KEY=sk-...            # For Claude
# OR
OPENAI_API_KEY=sk-...               # For OpenAI

SRC2_LLM_PROVIDER=ollama             # Provider selection
```

**BAML Client Configuration** at `/home/maceo/Dev/silmari-Context-Engine/baml_src/clients.baml`:

```baml
client<llm> EnvironmentOllama {
  provider ollama
  options {
    base_url env.OLLAMA_BASE_URL
    model env.OLLAMA_MODEL
    temperature 0.7
  }
}
```

---

### 🚀 Implementation Checklist

| Task | Priority | Location |
|------|----------|----------|
| 1. Create `models.py` with data classes | 🔴 High | `planning_pipeline/models.py` |
| 2. Add `step_requirement_decomposition()` | 🔴 High | `planning_pipeline/steps.py` |
| 3. Modify `PlanningPipeline.run()` | 🔴 High | `planning_pipeline/pipeline.py` |
| 4. Update `step_planning()` to accept requirements | 🟡 Medium | `planning_pipeline/steps.py` |
| 5. Add BAML client initialization | 🟡 Medium | `planning_pipeline/baml_init.py` |
| 6. Add environment variable loading | 🟡 Medium | `planning_pipeline/__init__.py` |
| 7. Add tests for decomposition step | 🟢 Low | `tests/test_steps.py` |
| 8. Add checkpoint for decomposition | 🟢 Low | `planning_pipeline/checkpoints.py` |

---

### 📈 Benefits of Integration

| Benefit | Before | After |
|---------|--------|-------|
| **Requirement Granularity** | High-level plan only | Micro-step implementation details |
| **Component Mapping** | Manual in plan | Auto-generated per requirement |
| **Acceptance Criteria** | Sparse/missing | Comprehensive per step |
| **LLM Token Efficiency** | Large prompts | Type-safe focused calls |
| **Resume Capability** | Plan-level only | Requirement-level saves |

---

### 📁 File References

| File | Purpose |
|------|---------|
| `/home/maceo/Dev/silmari-Context-Engine/planning_pipeline/pipeline.py` | Main pipeline (modify) |
| `/home/maceo/Dev/silmari-Context-Engine/planning_pipeline/steps.py` | Step implementations (add step) |
| `/home/maceo/Dev/silmari-Context-Engine/baml_src/functions.baml` | BAML function definitions |
| `/home/maceo/Dev/silmari-Context-Engine/baml_src/Gate1SharedClasses.baml` | Shared BAML types |
| `/home/maceo/Dev/silmari-Context-Engine/baml_client/types.py` | Generated Pydantic models |
