# Phase 6: Resume from Orchestrator State

## Overview

Enable `LoopRunner.resume()` to query the orchestrator for any IN_PROGRESS feature and continue from that point. This enables resilient execution across interruptions.

## Dependencies

- **Requires**: Phase 4 (phase progression), Phase 5 (status updates - IN_PROGRESS is tracked)
- **Blocks**: Phase 7 (integration tests validate this)

## Changes Required

### planning_pipeline/integrated_orchestrator.py

May need to add `get_current_feature()` method if not present:

```python
# integrated_orchestrator.py (add if not present)
def get_current_feature(self) -> Optional[FeatureInfo]:
    """Get the currently IN_PROGRESS feature, if any."""
    for feature in self._features:
        if feature.status == "IN_PROGRESS":
            return feature
    return None
```

### planning_pipeline/autonomous_loop.py

Add resume state restoration:

```python
# autonomous_loop.py (add to LoopRunner class)

async def _restore_state_from_orchestrator(self) -> None:
    """Restore execution state from orchestrator if available."""
    if self.orchestrator is None:
        return

    current = self.orchestrator.get_current_feature()
    if current is not None and current.status == "IN_PROGRESS":
        self.current_phase = current.phase
        self._current_feature = current
        logger.info(f"Resuming from {current.name} at phase {current.phase}")


async def resume(self) -> None:
    """Resume execution from paused state."""
    if self.state != LoopState.PAUSED:
        raise ValueError(f"Cannot resume from state: {self.state}")

    self.state = LoopState.RUNNING
    await self._restore_state_from_orchestrator()
    await self._execute_loop()
```

### tests/test_autonomous_loop.py

Add resume tests:

```python
class TestLoopRunnerResume:
    """Tests for resuming from orchestrator state."""

    @pytest.mark.asyncio
    async def test_resumes_from_in_progress_feature(self):
        """Should resume from feature marked IN_PROGRESS in orchestrator."""
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = [Mock(path="/plan.md", priority=1)]
        orchestrator.get_current_feature.return_value = Mock(
            name="feature-2", phase="phase-2", status="IN_PROGRESS"
        )
        orchestrator.get_next_feature.side_effect = [
            Mock(name="feature-2", phase="phase-2", status="IN_PROGRESS"),
            None,
        ]
        runner = LoopRunner(orchestrator=orchestrator)
        runner.state = LoopState.PAUSED
        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.resume()
        assert runner.current_phase == "phase-2"

    @pytest.mark.asyncio
    async def test_starts_fresh_when_no_in_progress(self):
        """Should start from beginning when no IN_PROGRESS feature."""
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = [Mock(path="/plan.md", priority=1)]
        orchestrator.get_current_feature.return_value = None
        orchestrator.get_next_feature.side_effect = [
            Mock(name="feature-1", phase="phase-1", status="NOT_STARTED"),
            None,
        ]
        runner = LoopRunner(orchestrator=orchestrator)
        runner.state = LoopState.PAUSED
        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.resume()
        assert runner.current_phase == "phase-1"

    @pytest.mark.asyncio
    async def test_resume_without_orchestrator_uses_stored_phase(self):
        """Backward compat: resume without orchestrator uses stored phase."""
        runner = LoopRunner(plan_path="/plan.md")
        runner.state = LoopState.PAUSED
        runner.current_phase = "stored-phase"
        with patch.object(runner, '_execute_loop', new_callable=AsyncMock):
            await runner.resume()
        assert runner.current_phase == "stored-phase"
```

## Success Criteria

### Automated
- [x] Test fails initially (Red): `pytest tests/test_autonomous_loop.py::TestLoopRunnerResume -v`
- [x] Test passes after implementation (Green)
- [x] All existing tests still pass

### Manual
- [x] Resume correctly picks up from interrupted state
- [x] Progress persists across pause/resume cycles
- [x] Works with real orchestrator state

## Human-Testable Function

```python
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from planning_pipeline.autonomous_loop import LoopRunner, LoopState

# Simulate a runner that was interrupted mid-execution
orchestrator = Mock()
orchestrator.discover_plans.return_value = [Mock(path="/plan.md", priority=1)]

# Orchestrator remembers we were working on phase-2
orchestrator.get_current_feature.return_value = Mock(
    name="feature-2",
    phase="phase-2",
    status="IN_PROGRESS"
)
orchestrator.get_next_feature.side_effect = [
    Mock(name="feature-2", phase="phase-2", status="IN_PROGRESS"),
    Mock(name="feature-3", phase="phase-3", status="NOT_STARTED"),
    None,
]
orchestrator.update_feature_status = Mock()

runner = LoopRunner(orchestrator=orchestrator)
runner.state = LoopState.PAUSED  # Simulates previous interruption

async def test_resume():
    print(f"Before resume - state: {runner.state}, phase: {runner.current_phase}")

    with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = True
        await runner.resume()

    print(f"After resume - state: {runner.state}")
    print(f"Resumed from phase: phase-2 (correct if IN_PROGRESS was restored)")

asyncio.run(test_resume())
```
