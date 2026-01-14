# Phase 5: Update Feature Status in Orchestrator

## Overview

Enable `LoopRunner` to update feature status in the orchestrator as work progresses. Status transitions: NOT_STARTED → IN_PROGRESS → COMPLETED/FAILED. Status update failures are logged but don't stop execution.

## Dependencies

- **Requires**: Phase 4 (phase progression with `_current_feature`)
- **Blocks**: Phase 6 (resume state depends on status being tracked)

## Changes Required

### planning_pipeline/autonomous_loop.py

Add status update method:

```python
# autonomous_loop.py (add to LoopRunner class)
import logging

logger = logging.getLogger(__name__)


def _update_feature_status(self, status: str) -> None:
    """Update current feature status in orchestrator, logging failures."""
    if self.orchestrator is None or self._current_feature is None:
        return

    try:
        self.orchestrator.update_feature_status(
            self._current_feature.name,
            status
        )
        logger.debug(f"Updated {self._current_feature.name} to {status}")
    except Exception as e:
        logger.warning(
            f"Failed to update feature status for {self._current_feature.name}: {e}"
        )


async def _execute_loop(self) -> None:
    """Execute the main loop with status updates."""
    while self.state == LoopState.RUNNING:
        next_phase = await self._get_next_phase()
        if next_phase is None:
            self.state = LoopState.COMPLETED
            break

        self.current_phase = next_phase
        self._update_feature_status("IN_PROGRESS")

        success = await self._execute_phase()

        if success:
            self._update_feature_status("COMPLETED")
        else:
            self._update_feature_status("FAILED")
            self.state = LoopState.FAILED
            break

        if self.orchestrator is None:
            self.state = LoopState.COMPLETED
            break
```

### tests/test_autonomous_loop.py

Add status update tests:

```python
class TestLoopRunnerStatusUpdates:
    """Tests for feature status updates to orchestrator."""

    @pytest.fixture
    def mock_orchestrator_with_status(self):
        """Orchestrator that tracks status updates."""
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = [Mock(path="/plan.md", priority=1)]
        orchestrator.get_next_feature.side_effect = [
            Mock(name="feature-1", phase="phase-1", status="NOT_STARTED"),
            None,
        ]
        orchestrator.update_feature_status = Mock()
        return orchestrator

    @pytest.mark.asyncio
    async def test_marks_feature_in_progress_when_starting(self, mock_orchestrator_with_status):
        """Should update status to IN_PROGRESS when starting phase."""
        runner = LoopRunner(orchestrator=mock_orchestrator_with_status)
        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()
        calls = mock_orchestrator_with_status.update_feature_status.call_args_list
        in_progress_calls = [c for c in calls if c[0][1] == "IN_PROGRESS"]
        assert len(in_progress_calls) >= 1

    @pytest.mark.asyncio
    async def test_marks_feature_completed_on_success(self, mock_orchestrator_with_status):
        """Should update status to COMPLETED when phase succeeds."""
        runner = LoopRunner(orchestrator=mock_orchestrator_with_status)
        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()
        calls = mock_orchestrator_with_status.update_feature_status.call_args_list
        completed_calls = [c for c in calls if c[0][1] == "COMPLETED"]
        assert len(completed_calls) >= 1

    @pytest.mark.asyncio
    async def test_marks_feature_failed_on_error(self, mock_orchestrator_with_status):
        """Should update status to FAILED when phase fails."""
        runner = LoopRunner(orchestrator=mock_orchestrator_with_status)
        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = False
            await runner.run()
        calls = mock_orchestrator_with_status.update_feature_status.call_args_list
        failed_calls = [c for c in calls if c[0][1] == "FAILED"]
        assert len(failed_calls) >= 1

    @pytest.mark.asyncio
    async def test_continues_on_status_update_failure(self):
        """Should log warning and continue if status update fails."""
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = [Mock(path="/plan.md", priority=1)]
        orchestrator.get_next_feature.side_effect = [
            Mock(name="feature-1", phase="phase-1", status="NOT_STARTED"),
            None,
        ]
        orchestrator.update_feature_status.side_effect = Exception("DB error")
        runner = LoopRunner(orchestrator=orchestrator)
        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()  # Should not raise
        assert runner.state == LoopState.COMPLETED
```

## Success Criteria

### Automated
- [x] Test fails initially (Red): `pytest tests/test_autonomous_loop.py::TestLoopRunnerStatusUpdates -v`
- [x] Test passes after implementation (Green)
- [x] All existing tests still pass

### Manual
- [x] Status updates visible in orchestrator state
- [x] Failures logged appropriately (check logs)
- [x] Execution continues even if status update fails

## Human-Testable Function

```python
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from planning_pipeline.autonomous_loop import LoopRunner, LoopState

# Track status updates
status_updates = []

def track_status(feature_name, status):
    status_updates.append((feature_name, status))
    print(f"Status update: {feature_name} → {status}")

orchestrator = Mock()
orchestrator.discover_plans.return_value = [Mock(path="/plan.md", priority=1)]
orchestrator.get_next_feature.side_effect = [
    Mock(name="my-feature", phase="phase-1", status="NOT_STARTED"),
    None,
]
orchestrator.update_feature_status = track_status

runner = LoopRunner(orchestrator=orchestrator)

async def test_status():
    with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = True
        await runner.run()

    print(f"\nAll status updates: {status_updates}")
    # Should see: IN_PROGRESS, then COMPLETED

asyncio.run(test_status())
```
