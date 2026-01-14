# Phase 2: Schema Definitions

## Overview

Define BAML schemas for structured output types: `ResearchOutput`, `Phase`, `PlanOutput`, and `PhaseDecompositionOutput`.

## Dependencies

- **Requires**: Phase 1 (Project Setup) - baml_client must be generatable
- **Blocks**: Phase 3 (Parsing Functions)

## Behaviors Covered

- Behavior 3: ResearchOutput Schema Definition
- Behavior 4: PlanOutput Schema Definition
- Behavior 5: PhaseDecompositionOutput Schema Definition

## Changes Required

### New Files

| File | Purpose |
|------|---------|
| `baml_src/schemas.baml` | All BAML schema definitions |
| `planning_pipeline/tests/test_baml_schemas.py` | Tests for schema behaviors |

### File Contents

**baml_src/schemas.baml**
```baml
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

## TDD Cycle

### Red: Write Failing Tests

```bash
pytest planning_pipeline/tests/test_baml_schemas.py -v
```

Expected failures:
- `test_research_output_model_exists` - ResearchOutput not defined
- `test_research_output_has_required_fields` - no fields
- `test_research_output_instantiation` - can't instantiate
- `test_research_output_empty_questions` - can't handle empty list
- `test_plan_output_model_exists` - PlanOutput not defined
- `test_phase_model_exists` - Phase not defined
- `test_plan_output_has_phases` - no phases field
- `test_phase_fields` - missing fields
- `test_phase_decomposition_output_exists` - not defined
- `test_phase_decomposition_has_files` - no phase_files field

### Green: Implement

1. Create `baml_src/schemas.baml` with all class definitions
2. Run `baml-cli generate`
3. Verify generated types in `baml_client/types.py`

### Refactor

- Adjust descriptions for clarity
- Add optional fields if needed

## Success Criteria

### Automated
- [ ] `pytest planning_pipeline/tests/test_baml_schemas.py::TestResearchOutputSchema -v` passes
- [ ] `pytest planning_pipeline/tests/test_baml_schemas.py::TestPlanOutputSchema -v` passes
- [ ] `pytest planning_pipeline/tests/test_baml_schemas.py::TestPhaseDecompositionOutputSchema -v` passes

### Manual
- [ ] IDE shows autocomplete for `ResearchOutput.research_path`
- [ ] IDE shows autocomplete for `PlanOutput.phases[0].name`
- [ ] Type checker validates field types

## Testable Function

**End of Phase Test**: After this phase, the following should succeed:

```python
from baml_client.types import ResearchOutput, PlanOutput, Phase, PhaseDecompositionOutput

# Test 1: ResearchOutput instantiation
research = ResearchOutput(
    research_path="thoughts/shared/research/2026-01-01-test.md",
    open_questions=["Question 1?"],
    summary="Test summary"
)
assert research.research_path.startswith("thoughts/")

# Test 2: PlanOutput with Phase
phase = Phase(
    number=1,
    name="Setup",
    dependencies=[],
    success_criteria=["Tests pass"]
)
plan = PlanOutput(
    plan_path="thoughts/shared/plans/2026-01-01-test/00-overview.md",
    phases=[phase],
    estimated_complexity="low"
)
assert len(plan.phases) == 1
assert plan.phases[0].name == "Setup"

# Test 3: PhaseDecompositionOutput
decomp = PhaseDecompositionOutput(
    phase_files=["00-overview.md", "01-setup.md"],
    overview_file="00-overview.md"
)
assert len(decomp.phase_files) == 2
```
