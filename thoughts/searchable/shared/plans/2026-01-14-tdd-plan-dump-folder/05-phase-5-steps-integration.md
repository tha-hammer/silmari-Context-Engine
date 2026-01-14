# Phase 5: Steps Integration

## Overview

Create `baml_steps.py` with pipeline step functions that return typed dataclasses instead of `dict[str, Any]`. Each step uses BAML parsing via `baml_helpers.py`.

## Dependencies

- **Requires**: Phase 4 (Helper Integration) - baml_helpers must be available
- **Blocks**: Phase 6 (Error Handling)

## Behaviors Covered

- Behavior 10: Step Functions Use BAML Parsing

## Changes Required

### New Files

| File | Purpose |
|------|---------|
| `planning_pipeline/baml_steps.py:1-110` | Pipeline steps with typed outputs |
| `planning_pipeline/tests/test_baml_steps.py` | Tests for step integration |

### File Contents

**planning_pipeline/baml_steps.py**
```python
"""Pipeline steps with BAML-powered typed outputs."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

from .claude_runner import run_claude_sync
from .baml_helpers import parse_research_output, parse_plan_output, parse_phase_files
from baml_client.types import Phase


@dataclass
class ResearchStepResult:
    """Typed result from research step."""
    success: bool
    research_path: Optional[str] = None
    open_questions: List[str] = None
    summary: Optional[str] = None
    raw_output: Optional[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.open_questions is None:
            self.open_questions = []


@dataclass
class PlanStepResult:
    """Typed result from planning step."""
    success: bool
    plan_path: Optional[str] = None
    phases: List[Phase] = None
    estimated_complexity: Optional[str] = None
    raw_output: Optional[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.phases is None:
            self.phases = []


@dataclass
class PhaseDecompositionResult:
    """Typed result from phase decomposition step."""
    success: bool
    phase_files: List[str] = None
    overview_file: Optional[str] = None
    raw_output: Optional[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.phase_files is None:
            self.phase_files = []


def step_research(project_path: Path, research_prompt: str) -> ResearchStepResult:
    """Execute research phase with BAML-typed output."""
    prompt = f"Research: {research_prompt}"

    result = run_claude_sync(prompt=prompt, timeout=300)

    if not result["success"]:
        return ResearchStepResult(
            success=False,
            error=result.get("error", "Research failed")
        )

    try:
        parsed = parse_research_output(result["output"])
        return ResearchStepResult(
            success=True,
            research_path=parsed.research_path,
            open_questions=parsed.open_questions,
            summary=parsed.summary,
            raw_output=result["output"]
        )
    except Exception as e:
        return ResearchStepResult(
            success=False,
            error=f"BAML parsing failed: {e}",
            raw_output=result["output"]
        )


def step_planning(
    project_path: Path,
    research_path: str,
    additional_context: str = ""
) -> PlanStepResult:
    """Execute planning phase with BAML-typed output."""
    prompt = f"Create plan based on: {research_path}"

    result = run_claude_sync(prompt=prompt, timeout=300)

    if not result["success"]:
        return PlanStepResult(
            success=False,
            error=result.get("error", "Planning failed")
        )

    try:
        parsed = parse_plan_output(result["output"])
        return PlanStepResult(
            success=True,
            plan_path=parsed.plan_path,
            phases=parsed.phases,
            estimated_complexity=parsed.estimated_complexity,
            raw_output=result["output"]
        )
    except Exception as e:
        return PlanStepResult(
            success=False,
            error=f"BAML parsing failed: {e}",
            raw_output=result["output"]
        )
```

## TDD Cycle

### Red: Write Failing Tests

```bash
pytest planning_pipeline/tests/test_baml_steps.py -v
```

Expected failures:
- `test_step_research_returns_typed_result` - module doesn't exist
- `test_step_planning_returns_typed_result` - function not implemented

### Green: Implement

1. Create `planning_pipeline/baml_steps.py`
2. Define dataclass result types
3. Implement step functions that use BAML helpers
4. Handle success and failure cases

### Refactor

- Extract common patterns
- Improve error messages

## Success Criteria

### Automated
- [ ] `pytest planning_pipeline/tests/test_baml_steps.py -v` passes
- [ ] Step functions return dataclass instances
- [ ] Mocked tests verify BAML parsing is called

### Manual
- [ ] IDE shows correct types for `result.research_path`
- [ ] Autocomplete works for `result.phases[0].name`
- [ ] Type checker validates step function returns

## Testable Function

**End of Phase Test**: After this phase, the following should succeed:

```python
from planning_pipeline.baml_steps import (
    step_research,
    step_planning,
    ResearchStepResult,
    PlanStepResult
)
from pathlib import Path

# Test with mocked Claude output
# (In actual tests, mock run_claude_sync)

# Verify result types
research = ResearchStepResult(
    success=True,
    research_path="thoughts/shared/research/2026-01-01-test.md",
    open_questions=["Question 1?"],
    summary="Test summary"
)
assert isinstance(research, ResearchStepResult)
assert research.research_path.startswith("thoughts/")

plan = PlanStepResult(
    success=True,
    plan_path="thoughts/shared/plans/2026-01-01-test/00-overview.md",
    phases=[],
    estimated_complexity="low"
)
assert isinstance(plan, PlanStepResult)
assert plan.estimated_complexity == "low"
```
