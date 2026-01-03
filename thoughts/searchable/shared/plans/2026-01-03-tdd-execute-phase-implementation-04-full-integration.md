# Phase 4: Full _execute_phase Integration

## Overview

Wire together the prompt builder, Claude invoker, and result checker into the `_execute_phase()` method of `LoopRunner`. This replaces the stub implementation with a fully functional phase executor.

## Dependencies

### Requires
- Phase 1: Prompt Generation (`build_phase_prompt`)
- Phase 2: Claude Invocation (`invoke_claude`)
- Phase 3: Result Checking (`check_execution_result`)

### Blocks
- Phase 5: End-to-End Integration

## Changes Required

### Modified Files

**File**: `planning_pipeline/autonomous_loop.py:1-20` (update imports)
```python
"""Autonomous Loop Runner with orchestrator integration."""

import logging
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from planning_pipeline.phase_execution.prompt_builder import build_phase_prompt
from planning_pipeline.phase_execution.claude_invoker import invoke_claude
from planning_pipeline.phase_execution.result_checker import check_execution_result

if TYPE_CHECKING:
    from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator


logger = logging.getLogger(__name__)
```

**File**: `planning_pipeline/autonomous_loop.py` (update __init__ method)
```python
def __init__(
    self,
    plan_path: Optional[str] = None,
    current_phase: Optional[str] = None,
    orchestrator: Optional["IntegratedOrchestrator"] = None,
    project_path: Optional[Path] = None,
):
    """Initialize the LoopRunner."""
    self.plan_path = plan_path
    self.current_phase = current_phase
    self.orchestrator = orchestrator
    self.state = LoopState.IDLE

    # Project path for git/beads operations
    self._project_path = project_path or Path.cwd()

    # Internal state for orchestrator integration
    self._current_feature: Optional[Any] = None
```

**File**: `planning_pipeline/autonomous_loop.py:146-175` (replace stub _execute_phase)
```python
def _build_phase_prompt(self) -> str:
    """Build prompt for the current phase."""
    return build_phase_prompt(self.plan_path, self.current_phase)

async def _execute_phase(self) -> bool:
    """Execute the current phase.

    Builds prompt, invokes Claude, and validates result.

    Returns:
        True if phase completed successfully, False otherwise.
    """
    try:
        # Build prompt
        prompt = self._build_phase_prompt()
    except FileNotFoundError as e:
        logger.error(f"Plan file not found: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to build prompt: {e}")
        return False

    # Invoke Claude
    logger.info(f"Executing phase: {self.current_phase}")
    claude_result = invoke_claude(prompt, timeout=3600)  # 1 hour timeout

    # Check result
    return check_execution_result(claude_result, self._project_path)
```

### Test File

**File**: `tests/test_execute_phase.py` (append to existing)
```python
class TestExecutePhaseIntegration:
    """Integration tests for _execute_phase method."""

    @pytest.fixture
    def runner_with_plan(self, tmp_path):
        """Create a runner with a valid plan file."""
        plan_path = tmp_path / "plan.md"
        plan_path.write_text("""# Test Plan

## Implementation
- Do the thing
""")

        # Initialize git repo
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
        (tmp_path / "initial.txt").write_text("initial")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True)

        runner = LoopRunner(plan_path=str(plan_path))
        runner.current_phase = "test-phase"
        runner._project_path = tmp_path
        return runner

    @pytest.mark.asyncio
    async def test_execute_phase_invokes_claude(self, runner_with_plan):
        """Should invoke Claude with built prompt."""
        with patch('planning_pipeline.phase_execution.claude_invoker.invoke_claude') as mock_invoke:
            mock_invoke.return_value = {
                "success": True,
                "output": "done",
                "error": "",
                "elapsed": 5.0
            }
            # Mock result checker to avoid subprocess calls
            with patch('planning_pipeline.phase_execution.result_checker.check_execution_result') as mock_check:
                mock_check.return_value = True

                result = await runner_with_plan._execute_phase()

                mock_invoke.assert_called_once()
                call_args = mock_invoke.call_args
                prompt = call_args[0][0]
                assert "Test Plan" in prompt
                assert "test-phase" in prompt

    @pytest.mark.asyncio
    async def test_execute_phase_returns_true_on_success(self, runner_with_plan):
        """Should return True when execution succeeds."""
        with patch('planning_pipeline.phase_execution.claude_invoker.invoke_claude') as mock_invoke:
            mock_invoke.return_value = {
                "success": True,
                "output": "done",
                "error": "",
                "elapsed": 5.0
            }
            with patch('planning_pipeline.phase_execution.result_checker.check_execution_result') as mock_check:
                mock_check.return_value = True

                result = await runner_with_plan._execute_phase()

                assert result is True

    @pytest.mark.asyncio
    async def test_execute_phase_returns_false_on_claude_failure(self, runner_with_plan):
        """Should return False when Claude fails."""
        with patch('planning_pipeline.phase_execution.claude_invoker.invoke_claude') as mock_invoke:
            mock_invoke.return_value = {
                "success": False,
                "output": "",
                "error": "Claude crashed",
                "elapsed": 5.0
            }
            with patch('planning_pipeline.phase_execution.result_checker.check_execution_result') as mock_check:
                mock_check.return_value = False

                result = await runner_with_plan._execute_phase()

                assert result is False

    @pytest.mark.asyncio
    async def test_execute_phase_handles_missing_plan(self, tmp_path):
        """Should return False when plan file is missing."""
        runner = LoopRunner(plan_path=str(tmp_path / "missing.md"))
        runner.current_phase = "phase-1"
        runner._project_path = tmp_path

        result = await runner._execute_phase()

        assert result is False

    @pytest.mark.asyncio
    async def test_execute_phase_passes_project_path_to_checker(self, runner_with_plan):
        """Should pass project path to result checker."""
        with patch('planning_pipeline.phase_execution.claude_invoker.invoke_claude') as mock_invoke:
            mock_invoke.return_value = {
                "success": True,
                "output": "done",
                "error": "",
                "elapsed": 5.0
            }
            with patch('planning_pipeline.phase_execution.result_checker.check_execution_result') as mock_check:
                mock_check.return_value = True

                await runner_with_plan._execute_phase()

                mock_check.assert_called_once()
                call_args = mock_check.call_args
                assert call_args[1]['project_path'] == runner_with_plan._project_path
```

## Success Criteria

### Automated
- [ ] Tests fail initially (Red): `pytest tests/test_execute_phase.py::TestExecutePhaseIntegration -v`
- [ ] Tests pass after implementation (Green): `pytest tests/test_execute_phase.py::TestExecutePhaseIntegration -v`
- [ ] All existing orchestrator tests still pass: `pytest tests/test_autonomous_loop.py -v`
- [ ] Full test suite passes: `pytest tests/ -v`

### Manual
- [ ] Run `_execute_phase()` with a real plan file (mocking Claude) and verify the flow
- [ ] Logs show "Executing phase: {phase_name}" message
- [ ] Error handling works when plan file is missing

## Human-Testable Function

After completing this phase, the following function is ready for manual testing:

```python
import asyncio
from pathlib import Path
from planning_pipeline.autonomous_loop import LoopRunner

async def test_execute():
    runner = LoopRunner(
        plan_path="path/to/your/plan.md",
        project_path=Path.cwd()
    )
    runner.current_phase = "test-feature"

    # This will actually invoke Claude if not mocked!
    result = await runner._execute_phase()
    print(f"Execution result: {result}")

asyncio.run(test_execute())
```

Expected output: `True` if Claude execution succeeds and result validation passes, `False` otherwise.
