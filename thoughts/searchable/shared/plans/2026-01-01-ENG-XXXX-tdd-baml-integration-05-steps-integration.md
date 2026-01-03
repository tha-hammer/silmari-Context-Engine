# Phase 5: Steps Integration

## Overview

Create typed step functions that replace `dict[str, Any]` returns with dataclasses. Add robust error handling for BAML parsing failures.

**Behaviors Covered**: 10, 11
**Human-Testable Function**: `step_research(path, prompt)` returns typed `ResearchStepResult` with IDE autocomplete; parsing errors return structured error results instead of crashing

## Dependencies

- **Requires**: Phase 4 (Helper Integration) - BAML helper functions must exist
- **Blocks**: Phase 6 (Full Pipeline Integration)

## Changes Required

### Behavior 10: Typed Step Functions

| File | Line | Change Description |
|------|------|-------------------|
| `planning_pipeline/baml_steps.py` | NEW:1-110 | Create typed step implementations |

**Test File**: `planning_pipeline/tests/test_baml_steps.py`

```python
class TestBAMLStepsIntegration:
    """Behavior 10: Steps using BAML parsing."""

    def test_step_research_returns_typed_result(self, monkeypatch):
        """Given research step, returns typed ResearchStepResult."""
        # Mock: run_claude_sync returns sample output
        # Calls: step_research(Path("."), "Test research")
        # Verifies: isinstance(result, ResearchStepResult)
        # Verifies: result.success is True
        # Verifies: result.research_path is not None

    def test_step_planning_returns_typed_result(self, monkeypatch):
        """Given planning step, returns typed PlanStepResult."""
        # Mock: run_claude_sync returns sample plan output
        # Calls: step_planning(Path("."), "test-research.md")
        # Verifies: isinstance(result, PlanStepResult)
```

**Implementation**: `planning_pipeline/baml_steps.py`

```python
"""Pipeline steps with BAML-powered typed outputs."""

from dataclasses import dataclass, field
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
    open_questions: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    raw_output: Optional[str] = None
    error: Optional[str] = None


@dataclass
class PlanStepResult:
    """Typed result from planning step."""
    success: bool
    plan_path: Optional[str] = None
    phases: List[Phase] = field(default_factory=list)
    estimated_complexity: Optional[str] = None
    raw_output: Optional[str] = None
    error: Optional[str] = None


@dataclass
class PhaseDecompositionResult:
    """Typed result from phase decomposition step."""
    success: bool
    phase_files: List[str] = field(default_factory=list)
    overview_file: Optional[str] = None
    raw_output: Optional[str] = None
    error: Optional[str] = None


def step_research(project_path: Path, research_prompt: str) -> ResearchStepResult:
    """Execute research phase with BAML-typed output."""
    prompt = f"Research: {research_prompt}"  # Full prompt in actual implementation

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
    prompt = f"Create plan based on: {research_path}"  # Full prompt in actual implementation

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


def step_phase_decomposition(
    project_path: Path,
    plan_path: str
) -> PhaseDecompositionResult:
    """Execute phase decomposition with BAML-typed output."""
    prompt = f"Decompose plan: {plan_path}"  # Full prompt in actual implementation

    result = run_claude_sync(prompt=prompt, timeout=300)

    if not result["success"]:
        return PhaseDecompositionResult(
            success=False,
            error=result.get("error", "Decomposition failed")
        )

    try:
        parsed = parse_phase_files(result["output"])
        return PhaseDecompositionResult(
            success=True,
            phase_files=parsed.phase_files,
            overview_file=parsed.overview_file,
            raw_output=result["output"]
        )
    except Exception as e:
        return PhaseDecompositionResult(
            success=False,
            error=f"BAML parsing failed: {e}",
            raw_output=result["output"]
        )
```

---

### Behavior 11: Error Handling

| File | Line | Change Description |
|------|------|-------------------|
| `planning_pipeline/baml_helpers.py` | NEW:40-70 | Add safe parsing wrapper with error handling |

**Test File**: `planning_pipeline/tests/test_baml_errors.py`

```python
class TestBAMLErrorHandling:
    """Behavior 11: BAML parsing error handling."""

    def test_parse_research_handles_empty_output(self):
        """Given empty output, returns error result."""
        # Calls: parse_research_output_safe("")
        # Verifies: result.success is False
        # Verifies: result.error is not None

    def test_parse_research_handles_no_path(self):
        """Given output without path, returns error with details."""
        # Calls: parse_research_output_safe("Just some text")
        # Verifies: result is not None

    def test_baml_api_error_handled(self, monkeypatch):
        """Given API error, returns graceful error."""
        # Mock: b.ParseResearchOutput raises Exception
        # Calls: parse_research_output_safe("Valid output")
        # Verifies: result.success is False
        # Verifies: "rate limit" or "API" in result.error
```

**Implementation**: `planning_pipeline/baml_helpers.py` (additions)

```python
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class ParseResult:
    """Generic result wrapper for BAML parsing."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


def parse_research_output_safe(raw_output: str) -> ParseResult:
    """Parse research output with error handling.

    Returns ParseResult with success=False on any error.
    """
    if not raw_output or not raw_output.strip():
        return ParseResult(
            success=False,
            error="Empty output provided"
        )

    try:
        result = b.ParseResearchOutput(raw_output=raw_output)
        return ParseResult(success=True, data=result)
    except Exception as e:
        return ParseResult(
            success=False,
            error=f"BAML parsing error: {str(e)}"
        )


def parse_plan_output_safe(raw_output: str) -> ParseResult:
    """Parse plan output with error handling."""
    if not raw_output or not raw_output.strip():
        return ParseResult(
            success=False,
            error="Empty output provided"
        )

    try:
        result = b.ParsePlanOutput(raw_output=raw_output)
        return ParseResult(success=True, data=result)
    except Exception as e:
        return ParseResult(
            success=False,
            error=f"BAML parsing error: {str(e)}"
        )


def parse_phase_files_safe(raw_output: str) -> ParseResult:
    """Parse phase files with error handling."""
    if not raw_output or not raw_output.strip():
        return ParseResult(
            success=False,
            error="Empty output provided"
        )

    try:
        result = b.ParsePhaseFiles(raw_output=raw_output)
        return ParseResult(success=True, data=result)
    except Exception as e:
        return ParseResult(
            success=False,
            error=f"BAML parsing error: {str(e)}"
        )
```

## Success Criteria

### Automated Tests
```bash
# Red phase - tests should fail
pytest planning_pipeline/tests/test_baml_steps.py -v
pytest planning_pipeline/tests/test_baml_errors.py -v

# Green phase - after implementation
pytest planning_pipeline/tests/test_baml_steps.py -v
pytest planning_pipeline/tests/test_baml_errors.py -v

# All tests pass
pytest planning_pipeline/tests/ -v
```

### Manual Verification
- [ ] `step_research()` returns `ResearchStepResult` with IDE autocomplete
- [ ] `step_planning()` returns `PlanStepResult` with IDE autocomplete
- [ ] `step_phase_decomposition()` returns `PhaseDecompositionResult` with IDE autocomplete
- [ ] Accessing `result.research_path`, `result.phases[0].name` works
- [ ] Empty input returns error result, doesn't crash
- [ ] API errors return error result with descriptive message

## Implementation Steps

1. Create `planning_pipeline/baml_steps.py` with dataclasses
2. Add `step_research` function
3. Add `step_planning` function
4. Add `step_phase_decomposition` function
5. Run Behavior 10 tests
6. Add safe wrapper functions to `baml_helpers.py`
7. Run Behavior 11 tests
8. Run all Phase 5 tests

## Module Structure After Phase 5

```
planning_pipeline/
├── __init__.py
├── helpers.py           # Original regex helpers (unchanged)
├── baml_helpers.py      # BAML wrappers + safe wrappers
├── steps.py             # Original steps (unchanged)
├── baml_steps.py        # NEW: Typed step implementations
└── tests/
    ├── test_helpers.py       # Original tests (unchanged)
    ├── test_baml_helpers.py  # Behavior 9 tests
    ├── test_baml_steps.py    # NEW: Behavior 10 tests
    └── test_baml_errors.py   # NEW: Behavior 11 tests
```

## Rollback Plan

If issues arise:
1. Remove `planning_pipeline/baml_steps.py`
2. Remove safe wrapper functions from `baml_helpers.py`
3. Remove test files
4. Existing `steps.py` continues working unchanged
