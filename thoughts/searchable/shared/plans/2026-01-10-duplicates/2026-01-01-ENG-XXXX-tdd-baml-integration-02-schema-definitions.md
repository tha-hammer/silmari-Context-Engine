# Phase 2: Schema Definitions

## Overview

Define BAML schemas for all output types: ResearchOutput, PlanOutput, Phase, and PhaseDecompositionOutput. These schemas define the typed structures that replace untyped `dict[str, Any]` returns.

**Behaviors Covered**: 3, 4, 5
**Human-Testable Function**: `from baml_client.types import ResearchOutput, PlanOutput, Phase, PhaseDecompositionOutput` imports successfully and models can be instantiated

## Dependencies

- **Requires**: Phase 1 (Project Setup) - baml-cli and generator must be configured
- **Blocks**: Phase 3 (BAML Functions)

## Changes Required

### Behavior 3: ResearchOutput Schema

| File | Line | Change Description |
|------|------|-------------------|
| `baml_src/schemas.baml` | NEW:1-5 | Define ResearchOutput class |

**Test File**: `planning_pipeline/tests/test_baml_schemas.py`

```python
class TestResearchOutputSchema:
    """Behavior 3: ResearchOutput schema definition."""

    def test_research_output_model_exists(self):
        """Given generated client, ResearchOutput model exists."""
        # Imports: from baml_client.types import ResearchOutput

    def test_research_output_has_required_fields(self):
        """Given ResearchOutput, it has research_path, open_questions, summary fields."""
        # Checks: model_fields contains all required fields

    def test_research_output_instantiation(self):
        """Given valid data, ResearchOutput can be instantiated."""
        # Creates instance with all fields, verifies values

    def test_research_output_empty_questions(self):
        """Given no open questions, open_questions can be empty list."""
        # Creates instance with empty open_questions list
```

**Implementation**: `baml_src/schemas.baml`
```baml
class ResearchOutput {
  research_path string @description("Path to created research document, e.g. thoughts/shared/research/2026-01-01-topic.md")
  open_questions string[] @description("List of unanswered questions discovered during research")
  summary string @description("Brief summary of research findings")
}
```

---

### Behavior 4: PlanOutput and Phase Schema

| File | Line | Change Description |
|------|------|-------------------|
| `baml_src/schemas.baml` | NEW:7-19 | Define Phase and PlanOutput classes |

**Test File**: `planning_pipeline/tests/test_baml_schemas.py`

```python
class TestPlanOutputSchema:
    """Behavior 4: PlanOutput schema definition."""

    def test_plan_output_model_exists(self):
        """Given generated client, PlanOutput model exists."""
        # Imports: from baml_client.types import PlanOutput

    def test_phase_model_exists(self):
        """Given generated client, Phase model exists."""
        # Imports: from baml_client.types import Phase

    def test_plan_output_has_phases(self):
        """Given PlanOutput, it has phases field as list of Phase."""
        # Creates PlanOutput with Phase list

    def test_phase_fields(self):
        """Given Phase, it has number, name, dependencies, success_criteria."""
        # Creates Phase with all fields, verifies values
```

**Implementation**: `baml_src/schemas.baml` (append)
```baml
class Phase {
  number int @description("1-indexed phase number")
  name string @description("Phase name, e.g. 'Setup', 'Implementation', 'Testing'")
  dependencies string[] @description("List of phase names this depends on")
  success_criteria string[] @description("Automated and manual verification criteria")
}

class PlanOutput {
  plan_path string @description("Path to plan document, e.g. thoughts/shared/plans/2026-01-01-feature/00-overview.md")
  phases Phase[] @description("List of implementation phases")
  estimated_complexity string @description("low, medium, or high")
}
```

---

### Behavior 5: PhaseDecompositionOutput Schema

| File | Line | Change Description |
|------|------|-------------------|
| `baml_src/schemas.baml` | NEW:21-24 | Define PhaseDecompositionOutput class |

**Test File**: `planning_pipeline/tests/test_baml_schemas.py`

```python
class TestPhaseDecompositionOutputSchema:
    """Behavior 5: PhaseDecompositionOutput schema definition."""

    def test_phase_decomposition_output_exists(self):
        """Given generated client, PhaseDecompositionOutput model exists."""
        # Imports: from baml_client.types import PhaseDecompositionOutput

    def test_phase_decomposition_has_files(self):
        """Given PhaseDecompositionOutput, it has phase_files field."""
        # Creates instance with phase_files list and overview_file
```

**Implementation**: `baml_src/schemas.baml` (append)
```baml
class PhaseDecompositionOutput {
  phase_files string[] @description("List of created phase file paths in order")
  overview_file string @description("Path to the 00-overview.md file")
}
```

## Success Criteria

### Automated Tests
```bash
# Red phase - tests should fail
pytest planning_pipeline/tests/test_baml_schemas.py -v

# Green phase - after implementation
baml-cli generate
pytest planning_pipeline/tests/test_baml_schemas.py -v
```

### Manual Verification
- [ ] `from baml_client.types import ResearchOutput` works in REPL
- [ ] `from baml_client.types import PlanOutput, Phase` works in REPL
- [ ] `from baml_client.types import PhaseDecompositionOutput` works in REPL
- [ ] IDE shows autocomplete for all model fields
- [ ] Type checker validates field types

## Implementation Steps

1. Create `baml_src/schemas.baml` with ResearchOutput
2. Run `baml-cli generate`
3. Run Behavior 3 tests (should pass)
4. Add Phase and PlanOutput to schemas.baml
5. Run `baml-cli generate`
6. Run Behavior 4 tests (should pass)
7. Add PhaseDecompositionOutput to schemas.baml
8. Run `baml-cli generate`
9. Run all Phase 2 tests (should all pass)

## Complete schemas.baml File

```baml
// schemas.baml - Type definitions for pipeline outputs

class ResearchOutput {
  research_path string @description("Path to created research document, e.g. thoughts/shared/research/2026-01-01-topic.md")
  open_questions string[] @description("List of unanswered questions discovered during research")
  summary string @description("Brief summary of research findings")
}

class Phase {
  number int @description("1-indexed phase number")
  name string @description("Phase name, e.g. 'Setup', 'Implementation', 'Testing'")
  dependencies string[] @description("List of phase names this depends on")
  success_criteria string[] @description("Automated and manual verification criteria")
}

class PlanOutput {
  plan_path string @description("Path to plan document, e.g. thoughts/shared/plans/2026-01-01-feature/00-overview.md")
  phases Phase[] @description("List of implementation phases")
  estimated_complexity string @description("low, medium, or high")
}

class PhaseDecompositionOutput {
  phase_files string[] @description("List of created phase file paths in order")
  overview_file string @description("Path to the 00-overview.md file")
}
```

## Rollback Plan

If issues arise:
1. Remove `baml_src/schemas.baml`
2. Run `baml-cli generate` to regenerate client without schemas
3. Remove test file `planning_pipeline/tests/test_baml_schemas.py`
