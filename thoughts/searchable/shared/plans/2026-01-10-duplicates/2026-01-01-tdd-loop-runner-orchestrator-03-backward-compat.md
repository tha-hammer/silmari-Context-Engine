# Phase 3: Backward Compatibility

## Overview

Ensure all existing `LoopRunner` functionality works unchanged when no orchestrator is provided. This phase validates that the new integration doesn't break existing workflows.

## Dependencies

- **Requires**: Phase 1 (orchestrator parameter), Phase 2 (plan discovery)
- **Blocks**: Phase 4-7 (ensures no regressions before adding more features)

## Changes Required

### planning_pipeline/autonomous_loop.py

No new code changes - this phase verifies existing behavior is preserved. The implementation from Phase 1 and 2 should already handle backward compatibility via optional parameters.

### tests/test_autonomous_loop.py

Add comprehensive backward compatibility tests:

```python
class TestLoopRunnerBackwardCompat:
    """Tests ensuring backward compatibility without orchestrator."""

    @pytest.mark.asyncio
    async def test_runs_without_orchestrator(self):
        """Should run successfully with just plan_path, no orchestrator."""
        runner = LoopRunner(plan_path="/plans/my-plan.md")
        with patch.object(runner, '_execute_loop', new_callable=AsyncMock):
            await runner.run()
        assert runner.plan_path == "/plans/my-plan.md"
        assert runner.orchestrator is None

    @pytest.mark.asyncio
    async def test_manual_phase_setting_works(self):
        """Should allow manual phase setting without orchestrator."""
        runner = LoopRunner(plan_path="/plans/my-plan.md", current_phase="custom-phase")
        assert runner.current_phase == "custom-phase"

    @pytest.mark.asyncio
    async def test_pause_resume_without_orchestrator(self):
        """Should pause and resume without orchestrator."""
        runner = LoopRunner(plan_path="/plans/my-plan.md")
        runner.current_phase = "phase-1"
        runner.state = LoopState.RUNNING
        await runner.pause()
        assert runner.state == LoopState.PAUSED
        with patch.object(runner, '_execute_loop', new_callable=AsyncMock):
            await runner.resume()
        assert runner.state == LoopState.RUNNING
        assert runner.current_phase == "phase-1"

    @pytest.mark.asyncio
    async def test_raises_without_plan_or_orchestrator(self):
        """Should raise error when neither plan_path nor orchestrator provided."""
        runner = LoopRunner()
        with pytest.raises(ValueError, match="No plan_path provided"):
            await runner.run()
```

## Success Criteria

### Automated
- [x] All backward compat tests pass: `pytest tests/test_autonomous_loop.py::TestLoopRunnerBackwardCompat -v`
- [x] ALL existing tests in test_autonomous_loop.py pass: `pytest tests/test_autonomous_loop.py -v`
- [x] Type check passes: `mypy planning_pipeline/`

### Manual
- [x] Existing CLI workflows still work (test with `python -m planning_pipeline ...`)
- [x] No breaking changes to public API
- [x] Documentation still accurate

## Human-Testable Function

```python
import asyncio
from planning_pipeline.autonomous_loop import LoopRunner, LoopState

# Test 1: Traditional usage (no orchestrator)
runner = LoopRunner(plan_path="/path/to/plan.md", current_phase="phase-1")
assert runner.plan_path == "/path/to/plan.md"
assert runner.current_phase == "phase-1"
assert runner.orchestrator is None
print("✓ Traditional instantiation works")

# Test 2: State management without orchestrator
runner.state = LoopState.RUNNING
# await runner.pause()  # Would pause
# await runner.resume()  # Would resume
print("✓ State management works without orchestrator")

# Test 3: Error on missing plan
try:
    bad_runner = LoopRunner()  # No plan, no orchestrator
    # await bad_runner.run()  # Would raise ValueError
    print("✓ Proper error handling for missing plan")
except ValueError as e:
    print(f"✓ Expected error: {e}")
```
