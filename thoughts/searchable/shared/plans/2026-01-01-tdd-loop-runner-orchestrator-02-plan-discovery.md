# Phase 2: Automatic Plan Discovery

## Overview

Enable `LoopRunner.run()` to automatically discover plans from the orchestrator when no explicit `plan_path` is provided. The orchestrator's `discover_plans()` method returns available plans sorted by priority.

## Dependencies

- **Requires**: Phase 1 (orchestrator parameter)
- **Blocks**: Phase 4 (phase progression), Phase 6 (resume state)

## Changes Required

### planning_pipeline/autonomous_loop.py

Add plan discovery method and modify `run()`:

```python
# autonomous_loop.py:85-95 (modify run method)
async def _discover_or_validate_plan(self) -> str:
    """Discover plan from orchestrator or validate explicit path."""
    if self.plan_path is not None:
        return self.plan_path

    if self.orchestrator is None:
        raise ValueError("No plan_path provided and no orchestrator available")

    plans = self.orchestrator.discover_plans()
    if not plans:
        raise ValueError("No plans available for execution")

    return plans[0].path


async def run(self) -> None:
    """Run the autonomous loop."""
    self.state = LoopState.RUNNING
    self.plan_path = await self._discover_or_validate_plan()
    await self._execute_loop()
```

### tests/test_autonomous_loop.py

Add test class for plan discovery:

```python
class TestLoopRunnerPlanDiscovery:
    """Tests for automatic plan discovery via orchestrator."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator with plan discovery."""
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = [
            Mock(path="/plans/feature-a.md", priority=1),
            Mock(path="/plans/feature-b.md", priority=2),
        ]
        return orchestrator

    @pytest.mark.asyncio
    async def test_discovers_plan_when_none_provided(self, mock_orchestrator):
        """Should discover plan from orchestrator when plan_path is None."""
        runner = LoopRunner(orchestrator=mock_orchestrator)
        with patch.object(runner, '_execute_loop', new_callable=AsyncMock):
            await runner.run()
        mock_orchestrator.discover_plans.assert_called_once()
        assert runner.plan_path == "/plans/feature-a.md"

    @pytest.mark.asyncio
    async def test_explicit_plan_path_takes_precedence(self, mock_orchestrator):
        """Explicit plan_path should skip discovery."""
        runner = LoopRunner(orchestrator=mock_orchestrator, plan_path="/explicit/my-plan.md")
        with patch.object(runner, '_execute_loop', new_callable=AsyncMock):
            await runner.run()
        mock_orchestrator.discover_plans.assert_not_called()
        assert runner.plan_path == "/explicit/my-plan.md"

    @pytest.mark.asyncio
    async def test_raises_error_when_no_plans_discovered(self):
        """Should raise error when orchestrator finds no plans."""
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = []
        runner = LoopRunner(orchestrator=orchestrator)
        with pytest.raises(ValueError, match="No plans available"):
            await runner.run()

    @pytest.mark.asyncio
    async def test_works_without_orchestrator_with_explicit_path(self):
        """Backward compat: works with explicit path and no orchestrator."""
        runner = LoopRunner(plan_path="/explicit/plan.md")
        with patch.object(runner, '_execute_loop', new_callable=AsyncMock):
            await runner.run()
        assert runner.plan_path == "/explicit/plan.md"
```

## Success Criteria

### Automated
- [x] Test fails initially (Red): `pytest tests/test_autonomous_loop.py::TestLoopRunnerPlanDiscovery -v`
- [x] Test passes after implementation (Green)
- [x] All existing tests still pass: `pytest tests/test_autonomous_loop.py -v`

### Manual
- [x] Plan discovery selects correct plan based on priority
- [x] Error message is clear when no plans found

## Human-Testable Function

```python
import asyncio
from planning_pipeline.autonomous_loop import LoopRunner
from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

# Test: Run with orchestrator (discovers plan automatically)
orch = IntegratedOrchestrator(plans_directory="./thoughts/searchable/shared/plans")
runner = LoopRunner(orchestrator=orch)

# Dry run - check that plan would be discovered
plans = orch.discover_plans()
print(f"Would use plan: {plans[0].path if plans else 'NONE'}")

# For actual run, you'd call: await runner.run()
```
