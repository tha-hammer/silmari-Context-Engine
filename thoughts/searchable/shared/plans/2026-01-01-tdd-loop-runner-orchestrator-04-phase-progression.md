# Phase 4: Query Orchestrator for Next Feature

## Overview

Enable `LoopRunner` to query the orchestrator's `get_next_feature()` method to progress through phases automatically. When a phase completes, the runner asks the orchestrator what to do next. Blocked features are skipped.

## Dependencies

- **Requires**: Phase 1 (orchestrator parameter), Phase 2 (plan discovery), Phase 3 (backward compat verified)
- **Blocks**: Phase 5 (status updates), Phase 6 (resume state)

## Changes Required

### planning_pipeline/autonomous_loop.py

Add phase progression methods:

```python
# autonomous_loop.py (add to LoopRunner class)

async def _get_next_phase(self) -> Optional[str]:
    """Get next phase from orchestrator, skipping blocked features."""
    if self.orchestrator is None:
        return None

    max_attempts = 100  # Prevent infinite loop
    for _ in range(max_attempts):
        feature = self.orchestrator.get_next_feature()
        if feature is None:
            return None
        if feature.status != "BLOCKED":
            self._current_feature = feature  # Store for status updates
            return feature.phase

    raise RuntimeError("Too many blocked features encountered")


async def _execute_loop(self) -> None:
    """Execute the main loop, progressing through phases."""
    while self.state == LoopState.RUNNING:
        # Get next phase
        if self.orchestrator:
            next_phase = await self._get_next_phase()
            if next_phase is None:
                self.state = LoopState.COMPLETED
                break
            self.current_phase = next_phase

        # Execute current phase
        success = await self._execute_phase()

        if not success:
            self.state = LoopState.FAILED
            break

        # If no orchestrator, single-phase execution
        if self.orchestrator is None:
            self.state = LoopState.COMPLETED
            break
```

### tests/test_autonomous_loop.py

Add phase progression tests:

```python
class TestLoopRunnerPhaseProgression:
    """Tests for phase progression via orchestrator."""

    @pytest.fixture
    def mock_orchestrator_with_features(self):
        """Orchestrator that returns features in sequence."""
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = [Mock(path="/plans/main.md", priority=1)]
        features = [
            Mock(name="feature-1", phase="phase-1", status="NOT_STARTED"),
            Mock(name="feature-2", phase="phase-2", status="NOT_STARTED"),
            None,  # No more features
        ]
        orchestrator.get_next_feature.side_effect = features
        return orchestrator

    @pytest.mark.asyncio
    async def test_queries_next_feature_after_phase_complete(self, mock_orchestrator_with_features):
        """Should query orchestrator for next feature when phase completes."""
        runner = LoopRunner(orchestrator=mock_orchestrator_with_features)
        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()
        assert mock_orchestrator_with_features.get_next_feature.call_count >= 1

    @pytest.mark.asyncio
    async def test_completes_when_no_more_features(self, mock_orchestrator_with_features):
        """Should set state to COMPLETED when no more features available."""
        runner = LoopRunner(orchestrator=mock_orchestrator_with_features)
        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()
        assert runner.state == LoopState.COMPLETED

    @pytest.mark.asyncio
    async def test_skips_blocked_features(self):
        """Should skip BLOCKED features and move to next unblocked."""
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = [Mock(path="/plan.md", priority=1)]
        orchestrator.get_next_feature.side_effect = [
            Mock(name="blocked-feature", status="BLOCKED"),
            Mock(name="available-feature", status="NOT_STARTED", phase="phase-1"),
            None,
        ]
        runner = LoopRunner(orchestrator=orchestrator)
        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()
        assert orchestrator.get_next_feature.call_count >= 2
```

## Success Criteria

### Automated
- [x] Test fails initially (Red): `pytest tests/test_autonomous_loop.py::TestLoopRunnerPhaseProgression -v`
- [x] Test passes after implementation (Green)
- [x] All existing tests still pass

### Manual
- [x] Phase progression follows orchestrator's feature order
- [x] Blocked features are skipped appropriately
- [x] Runner completes when all features done

## Human-Testable Function

```python
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from planning_pipeline.autonomous_loop import LoopRunner, LoopState

# Create mock orchestrator with 3 phases
orchestrator = Mock()
orchestrator.discover_plans.return_value = [Mock(path="/plan.md", priority=1)]
orchestrator.get_next_feature.side_effect = [
    Mock(name="setup", phase="phase-1", status="NOT_STARTED"),
    Mock(name="implement", phase="phase-2", status="NOT_STARTED"),
    Mock(name="test", phase="phase-3", status="NOT_STARTED"),
    None,  # Done
]

runner = LoopRunner(orchestrator=orchestrator)

# Run with mocked execution
async def test_progression():
    with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = True
        await runner.run()

    print(f"Final state: {runner.state}")  # Should be COMPLETED
    print(f"Phases executed: {orchestrator.get_next_feature.call_count}")  # Should be 4

asyncio.run(test_progression())
```
