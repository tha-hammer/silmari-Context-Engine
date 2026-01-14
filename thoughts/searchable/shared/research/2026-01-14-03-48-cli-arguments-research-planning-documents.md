---
date: 2026-01-14T03:48:38-05:00
researcher: claude
git_commit: fae276552b21ad71e8cb97f73cfda11383d4f534
branch: main
repository: silmari-Context-Engine
topic: "Adding CLI arguments for research and TDD planning documents with plan validation"
tags: [research, cli, arguments, tdd-planning, validation, decomposition]
status: complete
last_updated: 2026-01-14
last_updated_by: claude
---

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                   CLI ARGUMENTS RESEARCH                                       │
│                   Research & TDD Planning Document Integration                 │
│                                                                               │
│         Status: COMPLETE   |   Date: 2026-01-14                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

# Research: Adding CLI Arguments for Research and TDD Planning Documents

**Date**: 2026-01-14T03:48:38-05:00
**Researcher**: claude
**Git Commit**: fae276552b21ad71e8cb97f73cfda11383d4f534
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📚 Research Question

Research how to add additional CLI arguments to enable passing in:
1. An existing research document
2. An existing TDD planning document

For the planning document, research how to validate the plan before decomposing the plan.

---

## 📊 Summary

The silmari-Context-Engine codebase has comprehensive infrastructure for CLI argument handling and document validation. Adding arguments for existing research and TDD planning documents involves:

| Aspect | Current State | Required Changes |
|--------|---------------|------------------|
| CLI Framework | Click-based with established patterns | Add 2 new options |
| Research Document Input | Created by ResearchPhase | Add `--research-path` option |
| Planning Document Input | Created by TDDPlanningPhase | Add `--plan-path` option |
| Plan Validation | BAML + Python + Go validators exist | Invoke before decomposition |

---

## 🎯 Detailed Findings

### 1. Current CLI Architecture

**File**: `silmari_rlm_act/cli.py`

The CLI uses Click framework with established patterns for file path arguments:

```python
# Existing pattern for file path validation (lines 38-44)
@click.option(
    "--project",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
    help="Project directory (default: current directory)",
)
```

**Key Patterns Identified**:

| Pattern | Example | Location |
|---------|---------|----------|
| Required unless flag | `--question` required unless `--resume` | Line 88-89 |
| Path validation | `click.Path(exists=True, file_okay=True)` | Line 41 |
| Optional with default | `default="."` for project | Line 43 |
| Flag arguments | `is_flag=True` for `--autonomous` | Line 54 |

<details>
<summary>📄 Current CLI Options Structure</summary>

```python
# run command options (lines 31-71)
@click.option("--question", "-q", default=None)           # Research question
@click.option("--project", "-p", type=click.Path(...))     # Project directory
@click.option("--plan-name", "-n", default="feature")      # Plan name
@click.option("--autonomous", "-a", is_flag=True)          # Autonomous mode
@click.option("--batch", "-b", is_flag=True)               # Batch mode
@click.option("--resume", "-r", is_flag=True)              # Resume mode
```

</details>

---

### 2. Research Document Integration Point

**File**: `silmari_rlm_act/phases/research.py`

The ResearchPhase produces a research document path that flows to DecompositionPhase.

```
Current Flow:
┌───────────────────┐     ┌────────────────────────┐     ┌───────────────────┐
│   Research CLI    │────▶│   ResearchPhase        │────▶│ research_path     │
│   --question      │     │   execute()            │     │ artifacts[0]      │
└───────────────────┘     └────────────────────────┘     └───────────────────┘
                                                                   │
                                                                   ▼
                                                         ┌───────────────────┐
                                                         │ DecompositionPhase│
                                                         │ execute()         │
                                                         └───────────────────┘
```

**Integration Point** (`pipeline.py` lines 161-172):

```python
elif phase_type == PhaseType.DECOMPOSITION:
    # Get research path from previous phase
    research_result = self.state.get_phase_result(PhaseType.RESEARCH)
    if research_result and research_result.artifacts:
        research_path = Path(research_result.artifacts[0])
    else:
        research_path = Path(kwargs.get("research_path", ""))  # ← Already supports kwarg!
```

✅ **Key Finding**: The pipeline ALREADY supports `research_path` via kwargs - just needs CLI exposure.

---

### 3. TDD Planning Document Integration Point

**File**: `silmari_rlm_act/phases/tdd_planning.py`

The TDDPlanningPhase requires a `hierarchy_path` (JSON) not a plan markdown file. This is an important distinction:

| Document Type | Format | Phase That Produces It |
|---------------|--------|------------------------|
| Research Document | Markdown (`.md`) | ResearchPhase |
| Requirement Hierarchy | JSON (`.json`) | DecompositionPhase |
| TDD Plan | Markdown (`.md`) | TDDPlanningPhase |

**TDD Planning Inputs** (`tdd_planning.py` lines 80-95):

```python
def execute(
    self,
    plan_name: str,
    hierarchy_path: str,  # Path to requirement_hierarchy.json
) -> PhaseResult:
    """Execute TDD planning phase.

    Args:
        plan_name: Name for the plan (e.g., "login-feature")
        hierarchy_path: Path to JSON hierarchy file from decomposition
    """
```

**Pipeline Integration** (`pipeline.py` lines 174-201):

```python
elif phase_type == PhaseType.TDD_PLANNING:
    # Get hierarchy path from previous phase (file on disk)
    decomp_result = self.state.get_phase_result(PhaseType.DECOMPOSITION)
    hierarchy_path = None

    if decomp_result and decomp_result.metadata.get("hierarchy_path"):
        hierarchy_path = decomp_result.metadata["hierarchy_path"]
    else:
        hierarchy_path = kwargs.get("hierarchy_path")  # ← Already supports kwarg!
```

✅ **Key Finding**: Pipeline already supports `hierarchy_path` via kwargs - just needs CLI exposure.

---

### 4. Plan Validation Before Decomposition

The codebase has **three-tier validation** for plans:

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                        THREE-TIER VALIDATION ARCHITECTURE                       ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                                 ║
║   Tier 1: BAML Level (LLM-Driven)                                              ║
║   ├── ProcessGate1RequirementValidationPrompt()                                ║
║   └── Validates requirements against research scope                            ║
║                                                                                 ║
║   Tier 2: Model Level (Structural)                                             ║
║   ├── Python: RequirementNode.__post_init__()                                  ║
║   └── Go: RequirementNode.Validate()                                           ║
║                                                                                 ║
║   Tier 3: Checkpoint Level (Integrity)                                         ║
║   └── ValidateCheckpointPlan() - Plan hash validation                          ║
║                                                                                 ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

#### 4.1 BAML Validation Functions

**File**: `baml_src/functions.baml` (lines 1004-1045)

```baml
function ProcessGate1RequirementValidationPrompt(
  scope_text: string,
  current_requirements: string
) -> RequirementValidationResponse

class RequirementValidationResponse {
  validation_results: ValidationResult[]
  metadata: ResponseMetadata
  @@dynamic
}

class ValidationResult {
  requirement_id: string
  is_valid: bool
  validation_issues: string[]
  suggestions: string[]
  confidence_score: float?
}
```

#### 4.2 Python Model Validation

**File**: `planning_pipeline/models.py` (lines 145-158)

```python
VALID_REQUIREMENT_TYPES = frozenset(["parent", "sub_process", "implementation"])
VALID_CATEGORIES = frozenset([
    "functional", "non_functional", "security",
    "performance", "usability", "integration"
])

@dataclass
class RequirementNode:
    def __post_init__(self):
        if self.type not in VALID_REQUIREMENT_TYPES:
            raise ValueError(f"Invalid type '{self.type}'...")
        if not self.description or not self.description.strip():
            raise ValueError("Requirement description must not be empty")
        if self.category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category '{self.category}'...")
```

#### 4.3 Hierarchy Validation

**File**: `planning_pipeline/models.py` (lines 207-308)

```python
class RequirementHierarchy:
    requirements: list[RequirementNode]
    metadata: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict) -> "RequirementHierarchy":
        """Deserialize from JSON with recursive validation"""
        requirements = [RequirementNode.from_dict(r) for r in data["requirements"]]
        # Each node validated during construction
        return cls(requirements=requirements, metadata=data.get("metadata", {}))
```

---

### 5. Existing Thoughts Documentation

#### Resume CLI Integration Plan

**File**: `thoughts/shared/plans/2026-01-10-duplicates/2026-01-01-tdd-resume-pipeline-integration-03-cli-integration.md`

Already specifies similar arguments:

```
--resume, -r (flag)              - Resume from previous step
--resume-step (choice)           - Step: planning, decomposition, beads
--research-path, --research_path - Path to existing research document
--plan-path, --plan_path         - Path to existing plan document
```

#### CLI Gap Analysis

**File**: `thoughts/shared/research/2026-01-06-cli-checkpoint-resume-gaps.md`

| Gap | Priority | Status |
|-----|----------|--------|
| `--research-path` argument | 🔴 Critical | Not implemented |
| `--plan-path` argument | 🔴 Critical | Not implemented |
| Plan validation before decomposition | 🟡 Important | Infrastructure exists |

---

## 🚀 Implementation Approach

### New CLI Arguments

```python
# In silmari_rlm_act/cli.py

@main.command()
@click.option(
    "--question",
    "-q",
    default=None,
    help="Research question (required unless --research-path or --resume)",
)
@click.option(
    "--research-path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default=None,
    help="Path to existing research document (skips research phase)",
)
@click.option(
    "--plan-path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default=None,
    help="Path to existing TDD plan/hierarchy JSON (skips decomposition phase)",
)
# ... existing options ...
def run(
    question: Optional[str],
    research_path: Optional[str],
    plan_path: Optional[str],
    project: str,
    plan_name: str,
    autonomous: bool,
    batch: bool,
    resume: bool,
) -> None:
```

### Validation Flow for Plan Document

```python
def _validate_plan_before_decomposition(plan_path: Path) -> PhaseResult:
    """Validate an existing plan document before use.

    Validation steps:
    1. Check file exists and is valid JSON
    2. Deserialize to RequirementHierarchy (triggers __post_init__ validation)
    3. Optionally invoke BAML validation for semantic checking
    4. Return PhaseResult with validation status
    """
    try:
        # Structural validation
        with open(plan_path) as f:
            data = json.load(f)

        # Model validation (triggers RequirementNode.__post_init__ for each node)
        hierarchy = RequirementHierarchy.from_dict(data)

        # Count requirements for reporting
        node_count = sum(1 + len(r.children) for r in hierarchy.requirements)

        return PhaseResult(
            phase_type=PhaseType.TDD_PLANNING,
            status=PhaseStatus.COMPLETE,
            metadata={
                "validated": True,
                "requirements_count": len(hierarchy.requirements),
                "total_nodes": node_count,
            }
        )
    except (json.JSONDecodeError, ValueError, FileNotFoundError) as e:
        return PhaseResult(
            phase_type=PhaseType.TDD_PLANNING,
            status=PhaseStatus.FAILED,
            errors=[f"Plan validation failed: {e}"],
        )
```

---

## 📁 Code References

### Core Files

| File | Lines | Description |
|------|-------|-------------|
| `silmari_rlm_act/cli.py` | 31-163 | Current CLI implementation |
| `silmari_rlm_act/pipeline.py` | 140-280 | Phase execution with kwargs |
| `silmari_rlm_act/phases/research.py` | 286-443 | Research phase execution |
| `silmari_rlm_act/phases/decomposition.py` | 236-398 | Decomposition phase execution |
| `silmari_rlm_act/phases/tdd_planning.py` | 80-200 | TDD planning phase |
| `planning_pipeline/models.py` | 145-158, 207-308 | Validation logic |
| `baml_src/functions.baml` | 1004-1045 | BAML validation functions |

### Key Integration Points

```
silmari_rlm_act/cli.py:88-89         # Argument validation pattern
silmari_rlm_act/pipeline.py:161-172  # Research path passthrough (already exists!)
silmari_rlm_act/pipeline.py:174-201  # Hierarchy path passthrough (already exists!)
planning_pipeline/models.py:145-158  # RequirementNode validation
baml_src/Gate1SharedClasses.baml:80-87  # ValidationResult class
```

---

## 🛡️ Architecture Documentation

### Data Flow with New Arguments

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          WITH --research-path                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   CLI Arguments                    Pipeline                                 │
│   ├── --research-path ─────────▶  kwargs["research_path"] ──▶ SKIP Research │
│   │                                       │                                 │
│   │                                       ▼                                 │
│   │                               DecompositionPhase                        │
│   │                               (receives research_path)                  │
│   │                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          WITH --plan-path                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   CLI Arguments                    Pipeline                                 │
│   ├── --plan-path ─────────────▶  1. Validate JSON structure                │
│   │                               2. Validate RequirementHierarchy           │
│   │                               3. kwargs["hierarchy_path"] ──▶ SKIP Decomp│
│   │                                       │                                 │
│   │                                       ▼                                 │
│   │                               TDDPlanningPhase                          │
│   │                               (receives hierarchy_path)                 │
│   │                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Validation Sequence for --plan-path

```
1. CLI receives --plan-path=/path/to/hierarchy.json
        │
        ▼
2. click.Path(exists=True) validates file exists
        │
        ▼
3. Load JSON and parse to RequirementHierarchy
   └── Triggers RequirementNode.__post_init__() for each node
   └── Validates: type, description, category
        │
        ▼
4. (Optional) Invoke BAML validation
   └── ProcessGate1RequirementValidationPrompt()
   └── Returns ValidationResult[] with is_valid, issues, suggestions
        │
        ▼
5. If valid: Skip Research + Decomposition phases
   If invalid: Return PhaseResult(status=FAILED, errors=[...])
```

---

## 📖 Historical Context (from thoughts/)

| Document | Path | Relevance |
|----------|------|-----------|
| CLI Usage Guide | `thoughts/shared/docs/2026-01-01-how-to-use-cli-commands.md` | Existing CLI documentation |
| Resume Integration | `thoughts/shared/plans/2026-01-01-tdd-resume-pipeline-integration.md` | Similar argument patterns |
| CLI Integration Phase | `thoughts/shared/plans/2026-01-10-duplicates/2026-01-01-tdd-resume-pipeline-integration-03-cli-integration.md` | Specifies `--research-path`, `--plan-path` |
| CLI Gap Analysis | `thoughts/shared/research/2026-01-06-cli-checkpoint-resume-gaps.md` | Documents missing arguments |

---

## 🔗 Related Research

- `thoughts/shared/research/2026-01-01-resume-pipeline-integration.md` - Checkpoint architecture
- `thoughts/shared/research/2026-01-06-cli-checkpoint-resume-gaps.md` - CLI gaps analysis

---

## ❓ Open Questions

1. **Should `--plan-path` accept markdown TDD plans or only JSON hierarchies?**
   - Current TDDPlanningPhase expects JSON hierarchy (from DecompositionPhase)
   - May need to support both formats or clarify naming

2. **How much BAML validation to perform?**
   - Full validation adds latency (LLM call)
   - Structural validation is instant
   - Could offer `--validate-full` flag for comprehensive checking

3. **Phase skipping behavior:**
   - Should `--research-path` also skip question validation?
   - Should `--plan-path` auto-skip both Research AND Decomposition?

---

## ✅ Beads Integration

**Related Issues**:
- `silmari-Context-Engine-jiq` [P2] [task] open - Phase 3: CLI Integration
- `silmari-Context-Engine-l3e0` [P2] [feature] open - Implement resume CLI command stubs (planning + decomposition)

These issues relate to the resume functionality that would benefit from `--research-path` and `--plan-path` arguments.

