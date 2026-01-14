# Phase 7: Pipeline Integration

## Overview

Create `baml_pipeline.py` that orchestrates the full planning pipeline with BAML-powered typed outputs. All step results are typed dataclasses, and the final `PipelineResult` provides complete type safety.

## Dependencies

- **Requires**: Phase 6 (Error Handling) - safe parsing must be available
- **Blocks**: None (final phase)

## Behaviors Covered

- Behavior 12: Full Pipeline with BAML Parsing

## Changes Required

### New Files

| File | Purpose |
|------|---------|
| `planning_pipeline/baml_pipeline.py:1-80` | Full pipeline with typed results |
| `planning_pipeline/tests/test_baml_pipeline.py` | Integration tests for pipeline |

### File Contents

**planning_pipeline/baml_pipeline.py**
```python
"""Planning pipeline with BAML-powered typed outputs."""

from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Optional

from .beads_controller import BeadsController
from .baml_steps import (
    step_research,
    step_planning,
    ResearchStepResult,
    PlanStepResult,
    PhaseDecompositionResult
)


@dataclass
class PipelineResult:
    """Typed result from full pipeline execution."""
    success: bool
    started: str
    completed: Optional[str] = None
    research: Optional[ResearchStepResult] = None
    planning: Optional[PlanStepResult] = None
    decomposition: Optional[PhaseDecompositionResult] = None
    epic_id: Optional[str] = None
    plan_dir: Optional[str] = None
    failed_at: Optional[str] = None
    stopped_at: Optional[str] = None


class BAMLPlanningPipeline:
    """Interactive planning pipeline with BAML-powered type safety."""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self.beads = BeadsController(project_path)

    def run(
        self,
        research_prompt: str,
        ticket_id: Optional[str] = None,
        auto_approve: bool = False
    ) -> PipelineResult:
        """Run the complete planning pipeline with typed outputs."""

        result = PipelineResult(
            success=False,
            started=datetime.now().isoformat()
        )

        # Step 1: Research
        research = step_research(self.project_path, research_prompt)
        result.research = research

        if not research.success:
            result.failed_at = "research"
            return result

        # Step 2: Planning
        planning = step_planning(
            self.project_path,
            research.research_path or ""
        )
        result.planning = planning

        if not planning.success:
            result.failed_at = "planning"
            return result

        # Success
        result.success = True
        result.completed = datetime.now().isoformat()
        return result
```

## TDD Cycle

### Red: Write Failing Tests

```bash
pytest planning_pipeline/tests/test_baml_pipeline.py -v -m integration
```

Expected failures:
- `test_pipeline_returns_typed_results` - module doesn't exist
- Pipeline result not a dataclass
- Nested results not typed

### Green: Implement

1. Create `planning_pipeline/baml_pipeline.py`
2. Define `PipelineResult` dataclass
3. Implement `BAMLPlanningPipeline` class
4. Integrate with beads controller
5. Chain step functions with error handling

### Refactor

- Add phase decomposition step
- Add user interaction points
- Improve error reporting

## Success Criteria

### Automated
- [ ] `pytest planning_pipeline/tests/test_baml_pipeline.py -v -m integration` passes
- [ ] `pytest planning_pipeline/tests/test_baml_*.py -v` all pass
- [ ] Pipeline returns `PipelineResult` dataclass
- [ ] Nested results are typed (`result.research.research_path`)

### Manual
- [ ] IDE shows correct types throughout pipeline
- [ ] Type checker passes on pipeline code
- [ ] Autocomplete works for `result.research.open_questions`
- [ ] Full pipeline executes successfully end-to-end

## Testable Function

**End of Phase Test**: After this phase, the following should succeed:

```python
from planning_pipeline.baml_pipeline import BAMLPlanningPipeline, PipelineResult
from planning_pipeline.baml_steps import ResearchStepResult, PlanStepResult
from pathlib import Path

# Test 1: Pipeline returns typed result
project_path = Path(__file__).parent.parent.parent
pipeline = BAMLPlanningPipeline(project_path)

# With mocked Claude output, run pipeline
result = pipeline.run(
    research_prompt="Brief project structure",
    auto_approve=True
)

# Verify typed structure
assert isinstance(result, PipelineResult)
assert hasattr(result, 'success')
assert hasattr(result, 'research')
assert hasattr(result, 'planning')

# Nested results are typed
if result.research:
    assert isinstance(result.research, ResearchStepResult)
    assert hasattr(result.research, 'research_path')
    assert hasattr(result.research, 'open_questions')

if result.planning:
    assert isinstance(result.planning, PlanStepResult)
    assert hasattr(result.planning, 'plan_path')
    assert hasattr(result.planning, 'phases')
```

## Final Verification

After all phases complete, run the full test suite:

```bash
# All BAML tests
pytest planning_pipeline/tests/test_baml_*.py -v

# Integration tests (may require API key)
pytest planning_pipeline/tests/test_baml_*.py -v -m integration

# Type checking
mypy planning_pipeline/baml_*.py

# Verify imports work
python -c "from planning_pipeline.baml_pipeline import BAMLPlanningPipeline; print('Success')"
```
