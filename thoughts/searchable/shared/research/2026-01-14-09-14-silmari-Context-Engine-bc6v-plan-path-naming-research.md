---
date: 2026-01-14T09:14:27-05:00
researcher: claude
git_commit: c64152b21633f840a28e7aacd68cc111d09c979c
branch: main
repository: silmari-Context-Engine
topic: "CLI --plan-path option naming confusion and current implementation documentation"
tags: [research, cli, plan-path, hierarchy-path, file-formats, naming-convention]
status: complete
last_updated: 2026-01-14
last_updated_by: claude
beads_issue: silmari-Context-Engine-bc6v
---

```
+------------------------------------------------------------------------------+
|                     CLI --plan-path OPTION DOCUMENTATION                      |
|                                                                               |
|         Status: COMPLETE   |   Date: 2026-01-14                              |
|         Issue: silmari-Context-Engine-bc6v                                   |
+------------------------------------------------------------------------------+
```

# Research: CLI --plan-path Option Naming and Current Implementation

**Date**: 2026-01-14T09:14:27-05:00
**Researcher**: claude
**Git Commit**: c64152b21633f840a28e7aacd68cc111d09c979c
**Branch**: main
**Repository**: silmari-Context-Engine
**Beads Issue**: silmari-Context-Engine-bc6v

---

## Research Question

Document the current implementation of the CLI `--plan-path` option across all orchestrators, focusing on:
1. What file types each implementation expects (Markdown vs JSON)
2. How the option is named vs what it actually accepts
3. The relationship between TDD Plan Markdown files and Requirement Hierarchy JSON files

**Issue Context**: The `--plan-path` option is misleadingly named - it expects JSON hierarchy files, not Markdown plan files.

---

## Summary

The `--plan-path` CLI option has **inconsistent semantics** across different orchestrators in the codebase:

| CLI Implementation | Option Name | Expected File Type | Internal Variable |
|--------------------|-------------|-------------------|-------------------|
| `silmari_rlm_act/cli.py` | `--plan-path` | **JSON** (hierarchy) | `hierarchy_path` |
| `resume_pipeline.py` | `--plan-path` | **Markdown** (plan) | `plan_path` |
| `planning_orchestrator.py` | `--plan-path` | **Markdown** (plan) | `plan_path` |

The **core confusion** is:
- The name `--plan-path` suggests a TDD Plan Markdown file
- The `silmari_rlm_act/cli.py` implementation actually expects a Requirement Hierarchy JSON file
- The help text says "TDD plan/hierarchy JSON" which conflates two different file types

---

## Detailed Findings

### 1. File Type Distinction

The pipeline produces **two distinct artifact types** at different phases:

```
+-----------------------------------------------------------------------------+
|                        FILE TYPE COMPARISON                                  |
+-----------------------------------------------------------------------------+
| Attribute            | TDD Plan Markdown        | Requirement Hierarchy JSON |
|----------------------|--------------------------|----------------------------|
| File Extension       | .md                      | .json                      |
| Format               | Human-readable markdown  | Machine-readable JSON      |
| Production Phase     | TDDPlanningPhase         | DecompositionPhase         |
| Primary Consumer     | Implementation Phase     | TDDPlanningPhase           |
| Contains             | Phases, Testable Behav.  | Nested Requirement Tree    |
| Example Path         | 2026-01-14-tdd-feature/  | requirement_hierarchy.json |
|                      | 00-overview.md           |                            |
+-----------------------------------------------------------------------------+
```

#### TDD Plan Markdown Structure (produced by TDDPlanningPhase)

```markdown
# feature TDD Implementation Plan

## Phase Summary
| Phase | Description | Requirements | Status |
|-------|-------------|--------------|--------|
| 01 | The system must implement... | REQ_000 | Pending |

## Requirements
### REQ_000: The system must implement a complete 6-phase autonomous TDD...
#### REQ_000.1: Implement the autonomous loop...
##### Testable Behaviors
1. The loop executes a maximum of 100 iterations.
```

#### Requirement Hierarchy JSON Structure (produced by DecompositionPhase)

```json
{
  "requirements": [
    {
      "id": "REQ_000",
      "description": "The CLI must support...",
      "type": "parent",
      "parent_id": null,
      "children": [...],
      "acceptance_criteria": [...],
      "category": "functional"
    }
  ],
  "metadata": {
    "source": "agent_sdk_decomposition",
    "decomposition_stats": {...}
  }
}
```

---

### 2. CLI Implementations Analysis

#### 2.1 `silmari_rlm_act/cli.py` (Primary CLI)

**File**: `silmari_rlm_act/cli.py:79-84`

```python
@click.option(
    "--plan-path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default=None,
    help="Path to existing TDD plan/hierarchy JSON (skips research and decomposition phases)",
)
```

**Behavior**:
- **Expected file type**: JSON (despite name suggesting "plan")
- **Internal variable**: Passed as `hierarchy_path` to pipeline
- **Skips phases**: Both ResearchPhase AND DecompositionPhase
- **Validation**: Full JSON schema validation via `RequirementHierarchy.from_dict()`

**Evidence from code** (`cli.py:215`):
```python
result = pipeline.run(
    research_question=question or "",
    plan_name=plan_name,
    research_path=research_path,
    hierarchy_path=plan_path,  # <-- Note: plan_path becomes hierarchy_path
    validate_full=validate_full,
)
```

#### 2.2 `resume_pipeline.py`

**File**: `resume_pipeline.py:127-131`

```python
parser.add_argument(
    "--plan-path", "--plan_path",
    dest="plan_path",
    help="Path to plan document (required for decomposition step)"
)
```

**Behavior**:
- **Expected file type**: Markdown (.md)
- **Internal variable**: `plan_path`
- **Required for**: decomposition step only
- **Validation**: Presence check only (no format validation)

**Example from help** (`resume_pipeline.py:90`):
```
resume_pipeline.py decomposition --plan-path thoughts/searchable/plans/2025-12-31-plan.md
```

#### 2.3 `planning_orchestrator.py`

**File**: `planning_orchestrator.py:81-86`

```python
parser.add_argument(
    "--plan-path", "--plan_path",
    dest="plan_path",
    metavar="FILE",
    help="Plan .md file: full path, relative path, or just filename (auto-resolved)"
)
```

**Behavior**:
- **Expected file type**: Markdown (.md) - explicitly stated
- **Internal variable**: `plan_path`
- **Features**: Auto-resolution, interactive fallback
- **Validation**: Path resolution via `resolve_file_path()`

---

### 3. Test Case Documentation

The tests in `silmari_rlm_act/tests/test_cli.py` and `test_pipeline.py` reveal the **expected behavior is JSON**:

#### Test Fixture Creates JSON

```python
# test_cli.py:506-531 - temp_plan_doc fixture
{
  "requirements": [
    {
      "id": "REQ_001",
      "description": "Test requirement",
      "type": "parent",
      "parent_id": null,
      "children": [],
      "acceptance_criteria": [],
      "category": "functional"
    }
  ],
  "metadata": {"source": "test"}
}
```

#### Key Test Behaviors

| Test | Expected Behavior |
|------|------------------|
| `test_plan_path_validates_json_format` | Invalid JSON produces error |
| `test_plan_path_validates_requirement_type` | Validates against VALID_REQUIREMENT_TYPES |
| `test_plan_path_validates_requirement_category` | Validates against VALID_CATEGORIES |
| `test_plan_path_result_metadata_includes_counts` | Returns `requirements_count`, `total_nodes` |

---

### 4. Pipeline Data Flow

```
+-----------------------------------------------------------------------------+
|                         CURRENT PIPELINE DATA FLOW                           |
+-----------------------------------------------------------------------------+

                    --question
                        |
                        v
              +-------------------+
              |   ResearchPhase   |  --> research_document.md
              +-------------------+
                        |
                        v
              +-------------------+
              | DecompositionPhase|  --> requirement_hierarchy.json
              +-------------------+
                        |
                        v
              +-------------------+
              |  TDDPlanningPhase |  --> tdd_plan/ (multiple .md files)
              +-------------------+
                        |
                        v
              +-------------------+
              |ImplementationPhase|
              +-------------------+


+-----------------------------------------------------------------------------+
|                    WITH --plan-path (silmari_rlm_act CLI)                    |
+-----------------------------------------------------------------------------+

              --plan-path=/path/to/hierarchy.json
                        |
                        v
              +-------------------+
              | JSON Validation   |
              | (RequirementHier.)|
              +-------------------+
                        |
              [SKIP ResearchPhase]
              [SKIP DecompositionPhase]
                        |
                        v
              +-------------------+
              |  TDDPlanningPhase |
              +-------------------+
                        |
                        v
              +-------------------+
              |ImplementationPhase|
              +-------------------+
```

---

### 5. The Naming Inconsistency

The TDD plan document from `thoughts/shared/plans/2026-01-14-tdd-feature/02-the-cli-must-support-a---plan-path-option-that-acc.md` explicitly documents:

> **REQ_001**: The CLI must support a --plan-path option that accepts a path to an existing TDD plan/hierarchy **JSON** document

However, the terminology conflates:
- "TDD plan" (typically `.md` files)
- "hierarchy" (`.json` files)

The **internal variable naming** reveals the true intent:
- CLI calls it `plan_path`
- Pipeline receives it as `hierarchy_path`

---

## Code References

### Primary Implementation Files

| File | Lines | Description |
|------|-------|-------------|
| `silmari_rlm_act/cli.py` | 79-84, 215 | CLI option definition, pipeline passthrough |
| `silmari_rlm_act/pipeline.py` | 140-280 | Phase skipping logic |
| `resume_pipeline.py` | 127-131, 163-166 | Legacy CLI, expects .md |
| `planning_orchestrator.py` | 81-86, 383-392 | Legacy CLI, expects .md |

### Test Files

| File | Lines | Description |
|------|-------|-------------|
| `silmari_rlm_act/tests/test_cli.py` | 534-719 | TestPlanPathOption class |
| `silmari_rlm_act/tests/test_pipeline.py` | 724-1275 | TestPlanPathSkip, TestPlanDocumentValidation |

### Example Artifact Files

| Type | Example Path |
|------|--------------|
| TDD Plan MD | `thoughts/searchable/shared/plans/2026-01-14-tdd-feature/00-overview.md` |
| Hierarchy JSON | `thoughts/searchable/shared/plans/2026-01-14-03-52-tdd-.../requirement_hierarchy.json` |

---

## Architecture Documentation

### Current Validation Flow (silmari_rlm_act CLI)

```
1. CLI receives --plan-path=/path/to/file
        |
        v
2. click.Path(exists=True) validates file exists
        |
        v
3. Load JSON and parse to RequirementHierarchy
   +-- Triggers RequirementNode.__post_init__() for each node
   +-- Validates: type in VALID_REQUIREMENT_TYPES
   +-- Validates: category in VALID_CATEGORIES
   +-- Validates: description is non-empty
        |
        v
4. If valid: Skip Research + Decomposition phases
   If invalid: Return PhaseResult(status=FAILED, errors=[...])
```

### Valid Requirement Types

```python
VALID_REQUIREMENT_TYPES = frozenset(["parent", "sub_process", "implementation"])
```

### Valid Categories

```python
VALID_CATEGORIES = frozenset([
    "functional", "non_functional", "security",
    "performance", "usability", "integration"
])
```

---

## Historical Context (from thoughts/)

| Document | Path | Relevance |
|----------|------|-----------|
| CLI Arguments Research | `thoughts/shared/research/2026-01-14-03-48-cli-arguments-research-planning-documents.md` | Documents three-tier validation |
| TDD Plan Phase 02 | `thoughts/shared/plans/2026-01-14-tdd-feature/02-the-cli-must-support-a---plan-path-option-that-acc.md` | Original requirement specification |
| Resume Pipeline Integration | `thoughts/shared/research/2026-01-01-resume-pipeline-integration.md` | Legacy CLI argument patterns |

---

## Related Research

- `thoughts/shared/research/2026-01-14-03-48-cli-arguments-research-planning-documents.md`
- `thoughts/shared/research/2026-01-01-resume-pipeline-integration.md`
- `thoughts/shared/research/2026-01-02-orchestrator-brownfield-pipeline-integration.md`

---

## Beads Integration

**Related Issue**: `silmari-Context-Engine-bc6v` [P2] [bug] open - CLI --plan-path option is misleadingly named - expects JSON not Markdown

**Issue Recommendation from beads**:
> The option should: support both Markdown plans and JSON hierarchies with auto-detection. If a TDD plan file path is provided, then search for JSON, if no JSON, create JSON. If JSON provided and no TDD plan, search for TDD plan, if no plan, create TDD plan.

---

## Open Questions

1. **Should the option be renamed to `--hierarchy-path`?**
   - Would be more accurate but a breaking change

2. **Should auto-detection be implemented?**
   - Detect `.md` vs `.json` and handle accordingly
   - If `.md` provided, look for sibling `requirement_hierarchy.json`

3. **Should the legacy CLIs be updated?**
   - `resume_pipeline.py` and `planning_orchestrator.py` expect `.md`
   - `silmari_rlm_act/cli.py` expects `.json`
   - Inconsistent behavior across CLIs

4. **What is the relationship between the file types?**
   - TDD Plan `.md` files are **generated from** Requirement Hierarchy `.json`
   - They typically exist as siblings in the same directory
   - Pattern: `plans/2026-01-14-tdd-feature/requirement_hierarchy.json` + `plans/2026-01-14-tdd-feature/00-overview.md`
