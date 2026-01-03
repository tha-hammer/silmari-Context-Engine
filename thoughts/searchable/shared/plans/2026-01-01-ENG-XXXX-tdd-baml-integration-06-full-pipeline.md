# Phase 6: Full Pipeline Integration

## Overview

Create the full `BAMLPlanningPipeline` class that orchestrates all typed steps. This is the final integration phase where all components come together.

**Behaviors Covered**: 12
**Human-Testable Function**: `BAMLPlanningPipeline(path).run(prompt)` returns `PipelineResult` with full IDE autocomplete for `result.research.open_questions`, `result.planning.phases[0].name`, etc.

## Dependencies

- **Requires**: Phase 5 (Steps Integration) - all typed step functions must exist
- **Blocks**: None (final phase)

## Changes Required

### Behavior 12: Full Pipeline with BAML

| File | Line | Change Description |
|------|------|-------------------|
| `planning_pipeline/baml_pipeline.py` | NEW:1-100 | Create full pipeline orchestration |

**Test File**: `planning_pipeline/tests/test_baml_pipeline.py`

```python
class TestBAMLPipeline:
    """Behavior 12: Full pipeline with BAML."""

    @pytest.mark.slow
    @pytest.mark.integration
    def test_pipeline_returns_typed_results(self, monkeypatch, cleanup_issues):
        """Given pipeline with BAML, all results are typed."""
        # Setup: Mock Claude runner or use real API
        # Calls: pipeline.run(research_prompt="Brief project structure", auto_approve=True)

        # Verifies: Result structure
        # - hasattr(result, 'success')
        # - hasattr(result, 'research')
        # - hasattr(result, 'planning')

        # Verifies: Nested types
        # - result.research has research_path, open_questions
        # - result.planning has phases, plan_path

        # Cleanup: Remove created beads issues if any

    def test_pipeline_handles_research_failure(self, monkeypatch):
        """Given research step fails, pipeline returns failure result."""
        # Mock: step_research returns failure
        # Verifies: result.success is False
        # Verifies: result.failed_at == "research"

    def test_pipeline_handles_planning_failure(self, monkeypatch):
        """Given planning step fails, pipeline returns failure result."""
        # Mock: step_research succeeds, step_planning fails
        # Verifies: result.success is False
        # Verifies: result.failed_at == "planning"

    def test_pipeline_result_timestamps(self, monkeypatch):
        """Given pipeline run, timestamps are recorded."""
        # Verifies: result.started is not None
        # Verifies: result.completed is not None on success
```

**Implementation**: `planning_pipeline/baml_pipeline.py`

```python
"""Planning pipeline with BAML-powered typed outputs."""

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from .beads_controller import BeadsController
from .baml_steps import (
    step_research,
    step_planning,
    step_phase_decomposition,
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
    errors: List[str] = field(default_factory=list)


class BAMLPlanningPipeline:
    """Interactive planning pipeline with BAML-powered type safety.

    This pipeline orchestrates the full planning workflow:
    1. Research phase - Analyze codebase and document findings
    2. Planning phase - Create TDD implementation plan
    3. Decomposition phase - Split plan into phase files
    4. Beads integration - Create tracking issues

    All outputs are strongly typed with IDE autocomplete support.
    """

    def __init__(self, project_path: Path):
        """Initialize pipeline with project path.

        Args:
            project_path: Root path of the project to plan for
        """
        self.project_path = Path(project_path).resolve()
        self.beads = BeadsController(project_path)

    def run(
        self,
        research_prompt: str,
        ticket_id: Optional[str] = None,
        auto_approve: bool = False
    ) -> PipelineResult:
        """Run the complete planning pipeline with typed outputs.

        Args:
            research_prompt: Description of what to research/plan
            ticket_id: Optional external ticket ID for linking
            auto_approve: If True, skip user approval prompts

        Returns:
            PipelineResult with typed nested results for each phase
        """
        result = PipelineResult(
            success=False,
            started=datetime.now().isoformat()
        )

        # Step 1: Research
        print(f"[1/3] Starting research phase...")
        research = step_research(self.project_path, research_prompt)
        result.research = research

        if not research.success:
            result.failed_at = "research"
            result.errors.append(research.error or "Research failed")
            return result

        print(f"  Research complete: {research.research_path}")
        if research.open_questions:
            print(f"  Open questions: {len(research.open_questions)}")

        # Step 2: Planning
        print(f"[2/3] Starting planning phase...")
        planning = step_planning(
            self.project_path,
            research.research_path or "",
            additional_context=""
        )
        result.planning = planning

        if not planning.success:
            result.failed_at = "planning"
            result.errors.append(planning.error or "Planning failed")
            return result

        print(f"  Plan created: {planning.plan_path}")
        print(f"  Phases: {len(planning.phases)}")

        # Step 3: Phase Decomposition
        print(f"[3/3] Starting phase decomposition...")
        decomposition = step_phase_decomposition(
            self.project_path,
            planning.plan_path or ""
        )
        result.decomposition = decomposition

        if not decomposition.success:
            result.failed_at = "decomposition"
            result.errors.append(decomposition.error or "Decomposition failed")
            return result

        print(f"  Phase files created: {len(decomposition.phase_files)}")
        result.plan_dir = str(Path(decomposition.overview_file).parent) if decomposition.overview_file else None

        # Step 4: Beads Integration (optional)
        if ticket_id:
            try:
                epic_id = self.beads.create_epic(
                    title=research_prompt[:50],
                    phases=planning.phases
                )
                result.epic_id = epic_id
            except Exception as e:
                result.errors.append(f"Beads integration failed: {e}")
                # Don't fail pipeline for beads errors

        # Success!
        result.success = True
        result.completed = datetime.now().isoformat()
        return result

    def run_research_only(self, research_prompt: str) -> ResearchStepResult:
        """Run only the research phase.

        Useful for exploring before committing to full planning.
        """
        return step_research(self.project_path, research_prompt)

    def run_planning_only(self, research_path: str) -> PlanStepResult:
        """Run only the planning phase.

        Requires existing research document.
        """
        return step_planning(self.project_path, research_path)
```

## Success Criteria

### Automated Tests
```bash
# Red phase - tests should fail
pytest planning_pipeline/tests/test_baml_pipeline.py -v -m integration

# Green phase - after implementation
pytest planning_pipeline/tests/test_baml_pipeline.py -v -m integration

# All tests pass
pytest planning_pipeline/tests/ -v
```

### Manual Verification
- [ ] `BAMLPlanningPipeline(path).run(prompt)` returns `PipelineResult`
- [ ] IDE shows autocomplete for `result.research.open_questions`
- [ ] IDE shows autocomplete for `result.planning.phases[0].name`
- [ ] IDE shows autocomplete for `result.decomposition.phase_files`
- [ ] Type checker passes on pipeline code
- [ ] Pipeline prints progress as it runs
- [ ] Failures at any stage return structured error with `failed_at`

## Implementation Steps

1. Create `planning_pipeline/baml_pipeline.py`
2. Define `PipelineResult` dataclass
3. Implement `BAMLPlanningPipeline` class
4. Implement `run()` method with all phases
5. Add helper methods `run_research_only()`, `run_planning_only()`
6. Create test file with integration tests
7. Run tests and verify all pass

## Final Module Structure

```
planning_pipeline/
├── __init__.py
├── helpers.py              # Original regex helpers
├── baml_helpers.py         # BAML wrappers + safe wrappers
├── steps.py                # Original steps
├── baml_steps.py           # Typed step implementations
├── pipeline.py             # Original pipeline
├── baml_pipeline.py        # NEW: Typed pipeline
├── beads_controller.py     # Beads integration
├── claude_runner.py        # Claude subprocess wrapper
├── checkpoints.py          # Checkpoint management
└── tests/
    ├── conftest.py              # Shared fixtures
    ├── test_helpers.py          # Original tests
    ├── test_baml_setup.py       # Phase 1 tests
    ├── test_baml_schemas.py     # Phase 2 tests
    ├── test_baml_functions.py   # Phase 3 tests
    ├── test_baml_helpers.py     # Phase 4 tests
    ├── test_baml_steps.py       # Phase 5 tests
    ├── test_baml_errors.py      # Phase 5 tests
    └── test_baml_pipeline.py    # Phase 6 tests
```

## Usage Example

```python
from pathlib import Path
from planning_pipeline.baml_pipeline import BAMLPlanningPipeline

# Initialize pipeline
pipeline = BAMLPlanningPipeline(Path("/path/to/project"))

# Run full pipeline
result = pipeline.run(
    research_prompt="Implement user authentication with JWT",
    ticket_id="ENG-123",
    auto_approve=False
)

# Access typed results
if result.success:
    print(f"Research: {result.research.research_path}")
    print(f"Questions: {result.research.open_questions}")

    print(f"Plan: {result.planning.plan_path}")
    for phase in result.planning.phases:
        print(f"  Phase {phase.number}: {phase.name}")

    print(f"Files: {result.decomposition.phase_files}")
else:
    print(f"Failed at: {result.failed_at}")
    print(f"Errors: {result.errors}")
```

## Rollback Plan

If issues arise:
1. Remove `planning_pipeline/baml_pipeline.py`
2. Remove test file
3. Existing `pipeline.py` continues working unchanged
4. All previous phases remain functional independently

## End State Verification

After completing all 6 phases:

1. **Type Safety**: All pipeline outputs return typed dataclasses
2. **IDE Support**: Full autocomplete for all result fields
3. **Test Coverage**: All 12 behaviors have passing tests
4. **Error Handling**: Graceful failures with descriptive errors
5. **Backwards Compatibility**: Original modules remain functional

Run final verification:
```bash
# All tests pass
pytest planning_pipeline/tests/ -v

# Type checker passes
mypy planning_pipeline/baml_pipeline.py
mypy planning_pipeline/baml_steps.py
mypy planning_pipeline/baml_helpers.py

# Manual REPL test
python -c "
from planning_pipeline.baml_pipeline import BAMLPlanningPipeline, PipelineResult
from planning_pipeline.baml_steps import ResearchStepResult, PlanStepResult
print('All imports successful!')
print(f'PipelineResult fields: {PipelineResult.__dataclass_fields__.keys()}')
"
```
