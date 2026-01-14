# Loop Runner IntegratedOrchestrator TDD Implementation Plan

## Overview

This plan implements integration between `autonomous_loop.py` (LoopRunner) and `IntegratedOrchestrator` to enable LLM-driven plan discovery, dynamic resumption, and phase-aware execution. The integration maintains backward compatibility with existing CLI workflows while adding orchestrator capabilities.

## Current State Analysis

### LoopRunner (`planning_pipeline/autonomous_loop.py:15-200`)
- Manages autonomous execution loops with Claude
- Uses `LoopState` enum (IDLE, RUNNING, PAUSED, COMPLETED, FAILED)
- Has `plan_path` and `current_phase` attributes
- Implements `run()`, `pause()`, `resume()`, `stop()` methods
- Currently: plan and phase set manually, no dynamic discovery

### IntegratedOrchestrator (`planning_pipeline/integrated_orchestrator.py:1-400+`)
- Provides plan discovery via `discover_plans()`
- Has `get_next_feature()` for phase-aware progression
- Manages `FeatureStatus` (NOT_STARTED, IN_PROGRESS, COMPLETED, BLOCKED, SKIPPED)
- Supports multiple discovery strategies: filename patterns, directory scanning, frontmatter parsing

### Key Discoveries:
- `autonomous_loop.py:45-60`: LoopRunner.__init__ accepts `plan_path: Optional[str] = None`
- `autonomous_loop.py:85-95`: `run()` method currently requires manual plan setup
- `integrated_orchestrator.py:120-145`: `discover_plans()` returns `List[PlanInfo]`
- `integrated_orchestrator.py:180-210`: `get_next_feature()` returns `Optional[FeatureInfo]`
- `steps.py:1-50`: Step definitions that LoopRunner executes
- Both use Pydantic models for configuration

### Existing Test Patterns:
- `tests/test_autonomous_loop.py`: Uses pytest fixtures, mocks Claude responses
- `tests/test_integrated_orchestrator.py`: Tests plan discovery, feature status
- Both use `pytest-asyncio` for async tests

## Desired End State

LoopRunner can:
1. Accept an IntegratedOrchestrator instance for plan management
2. Discover plans dynamically when no explicit plan_path provided
3. Query orchestrator for next feature/phase during execution
4. Update feature status in orchestrator as work progresses
5. Resume from orchestrator-managed state after interruption
6. Fall back to manual plan_path when orchestrator not provided (backward compat)

### Observable Behaviors:
1. Given orchestrator with plans, when LoopRunner.run() called without plan_path, then discovers and uses first available plan
2. Given orchestrator, when current phase completes, then queries orchestrator for next feature
3. Given orchestrator with feature status, when LoopRunner resumes, then continues from correct phase
4. Given no orchestrator, when LoopRunner.run() called with plan_path, then works as before (backward compat)
5. Given orchestrator, when feature marked BLOCKED, then skips to next unblocked feature
6. Given orchestrator, when all features complete, then LoopRunner state becomes COMPLETED

## What We're NOT Doing

- Modifying IntegratedOrchestrator's core discovery logic
- Changing the Step execution model in steps.py
- Adding new CLI commands (that's separate work)
- Implementing new discovery strategies
- Modifying the Claude API interaction layer

## Testing Strategy

- **Framework**: pytest with pytest-asyncio
- **Test Types**:
  - Unit: Individual method behaviors in isolation
  - Integration: LoopRunner + IntegratedOrchestrator working together
- **Mocking**: Mock Claude responses, filesystem operations for plan discovery
- **Fixtures**: Reuse existing fixtures, add orchestrator-specific ones

---

## Behavior 1: LoopRunner Accepts Optional Orchestrator

### Test Specification
**Given**: LoopRunner class definition
**When**: Instantiated with `orchestrator` parameter
**Then**: Stores orchestrator reference, remains None if not provided

**Edge Cases**:
- orchestrator=None (default)
- Invalid orchestrator type raises TypeError

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `tests/test_autonomous_loop.py`
```python
import pytest
from planning_pipeline.autonomous_loop import LoopRunner
from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator
from unittest.mock import Mock, MagicMock


class TestLoopRunnerOrchestratorInit:
    """Tests for LoopRunner orchestrator initialization."""

    def test_accepts_orchestrator_parameter(self):
        """LoopRunner should accept an optional orchestrator parameter."""
        orchestrator = Mock(spec=IntegratedOrchestrator)
        runner = LoopRunner(orchestrator=orchestrator)

        assert runner.orchestrator is orchestrator

    def test_orchestrator_defaults_to_none(self):
        """LoopRunner should default orchestrator to None for backward compat."""
        runner = LoopRunner()

        assert runner.orchestrator is None

    def test_accepts_both_orchestrator_and_plan_path(self):
        """LoopRunner should accept both orchestrator and explicit plan_path."""
        orchestrator = Mock(spec=IntegratedOrchestrator)
        runner = LoopRunner(orchestrator=orchestrator, plan_path="/explicit/plan.md")

        assert runner.orchestrator is orchestrator
        assert runner.plan_path == "/explicit/plan.md"
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/autonomous_loop.py`
```python
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator


class LoopRunner:
    def __init__(
        self,
        plan_path: Optional[str] = None,
        current_phase: Optional[str] = None,
        orchestrator: Optional["IntegratedOrchestrator"] = None,
        # ... existing params
    ):
        self.plan_path = plan_path
        self.current_phase = current_phase
        self.orchestrator = orchestrator
        # ... existing initialization
```

#### 🔵 Refactor: Improve Code
No refactoring needed for this minimal change.

### Success Criteria
**Automated:**
- [ ] Test fails initially (Red): `pytest tests/test_autonomous_loop.py::TestLoopRunnerOrchestratorInit -v`
- [ ] Test passes after implementation (Green): `pytest tests/test_autonomous_loop.py::TestLoopRunnerOrchestratorInit -v`
- [ ] All existing tests still pass: `pytest tests/test_autonomous_loop.py -v`
- [ ] Type check passes: `mypy planning_pipeline/autonomous_loop.py`

**Manual:**
- [ ] Import works without circular dependency issues

---

## Behavior 2: Discover Plan When None Provided

### Test Specification
**Given**: LoopRunner with orchestrator, no explicit plan_path
**When**: `run()` is called
**Then**: Calls `orchestrator.discover_plans()` and uses first available plan

**Edge Cases**:
- No plans discovered (raises appropriate error)
- Multiple plans available (uses first based on priority)
- Explicit plan_path takes precedence over discovery

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `tests/test_autonomous_loop.py`
```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from planning_pipeline.autonomous_loop import LoopRunner, LoopState


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

        # Mock the actual execution to just check plan discovery
        with patch.object(runner, '_execute_loop', new_callable=AsyncMock):
            await runner.run()

        mock_orchestrator.discover_plans.assert_called_once()
        assert runner.plan_path == "/plans/feature-a.md"

    @pytest.mark.asyncio
    async def test_explicit_plan_path_takes_precedence(self, mock_orchestrator):
        """Explicit plan_path should skip discovery."""
        runner = LoopRunner(
            orchestrator=mock_orchestrator,
            plan_path="/explicit/my-plan.md"
        )

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

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/autonomous_loop.py`
```python
async def run(self) -> None:
    """Run the autonomous loop."""
    self.state = LoopState.RUNNING

    # Discover plan if not explicitly provided
    if self.plan_path is None and self.orchestrator is not None:
        plans = self.orchestrator.discover_plans()
        if not plans:
            raise ValueError("No plans available for execution")
        # Use first plan (highest priority)
        self.plan_path = plans[0].path

    # Existing run logic...
    await self._execute_loop()
```

#### 🔵 Refactor: Improve Code
**File**: `planning_pipeline/autonomous_loop.py`
```python
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

### Success Criteria
**Automated:**
- [ ] Test fails initially (Red): `pytest tests/test_autonomous_loop.py::TestLoopRunnerPlanDiscovery -v`
- [ ] Test passes after implementation (Green)
- [ ] All existing tests still pass: `pytest tests/test_autonomous_loop.py -v`

**Manual:**
- [ ] Plan discovery selects correct plan based on priority

---

## Behavior 3: Query Orchestrator for Next Feature

### Test Specification
**Given**: LoopRunner with orchestrator, current phase completing
**When**: Phase execution completes successfully
**Then**: Calls `orchestrator.get_next_feature()` and updates current_phase

**Edge Cases**:
- No next feature (all complete)
- Next feature is BLOCKED (skip to next unblocked)
- Orchestrator returns None (no more work)

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `tests/test_autonomous_loop.py`
```python
class TestLoopRunnerPhaseProgression:
    """Tests for phase progression via orchestrator."""

    @pytest.fixture
    def mock_orchestrator_with_features(self):
        """Orchestrator that returns features in sequence."""
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = [
            Mock(path="/plans/main.md", priority=1)
        ]

        # Simulate feature sequence
        features = [
            Mock(name="feature-1", phase="phase-1", status="NOT_STARTED"),
            Mock(name="feature-2", phase="phase-2", status="NOT_STARTED"),
            None,  # No more features
        ]
        orchestrator.get_next_feature.side_effect = features
        return orchestrator

    @pytest.mark.asyncio
    async def test_queries_next_feature_after_phase_complete(
        self, mock_orchestrator_with_features
    ):
        """Should query orchestrator for next feature when phase completes."""
        runner = LoopRunner(orchestrator=mock_orchestrator_with_features)

        # Simulate phase completion
        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True  # Phase completed successfully
            await runner.run()

        # Should have queried for next feature
        assert mock_orchestrator_with_features.get_next_feature.call_count >= 1

    @pytest.mark.asyncio
    async def test_updates_current_phase_from_feature(
        self, mock_orchestrator_with_features
    ):
        """Should update current_phase based on next feature."""
        runner = LoopRunner(orchestrator=mock_orchestrator_with_features)

        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()

        # Phase should have been updated during execution
        # (checking that the orchestrator was used to get phases)
        mock_orchestrator_with_features.get_next_feature.assert_called()

    @pytest.mark.asyncio
    async def test_completes_when_no_more_features(
        self, mock_orchestrator_with_features
    ):
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

        # First feature blocked, second available, third None
        orchestrator.get_next_feature.side_effect = [
            Mock(name="blocked-feature", status="BLOCKED"),
            Mock(name="available-feature", status="NOT_STARTED", phase="phase-1"),
            None,
        ]

        runner = LoopRunner(orchestrator=orchestrator)

        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()

        # Should have called get_next_feature multiple times to skip blocked
        assert orchestrator.get_next_feature.call_count >= 2
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/autonomous_loop.py`
```python
async def _get_next_phase(self) -> Optional[str]:
    """Get next phase from orchestrator or return None if complete."""
    if self.orchestrator is None:
        return None

    while True:
        feature = self.orchestrator.get_next_feature()
        if feature is None:
            return None
        if feature.status != "BLOCKED":
            return feature.phase
        # Continue loop to skip blocked features


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

#### 🔵 Refactor: Improve Code
```python
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
```

### Success Criteria
**Automated:**
- [ ] Test fails initially (Red): `pytest tests/test_autonomous_loop.py::TestLoopRunnerPhaseProgression -v`
- [ ] Test passes after implementation (Green)
- [ ] All existing tests still pass

**Manual:**
- [ ] Phase progression follows orchestrator's feature order
- [ ] Blocked features are skipped appropriately

---

## Behavior 4: Update Feature Status in Orchestrator

### Test Specification
**Given**: LoopRunner executing with orchestrator
**When**: Phase starts, completes, or fails
**Then**: Updates feature status in orchestrator (IN_PROGRESS, COMPLETED, FAILED)

**Edge Cases**:
- Status update fails (log warning, continue)
- Multiple rapid status updates

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `tests/test_autonomous_loop.py`
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
    async def test_marks_feature_in_progress_when_starting(
        self, mock_orchestrator_with_status
    ):
        """Should update status to IN_PROGRESS when starting phase."""
        runner = LoopRunner(orchestrator=mock_orchestrator_with_status)

        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()

        # Check that IN_PROGRESS was set
        calls = mock_orchestrator_with_status.update_feature_status.call_args_list
        in_progress_calls = [c for c in calls if c[0][1] == "IN_PROGRESS"]
        assert len(in_progress_calls) >= 1

    @pytest.mark.asyncio
    async def test_marks_feature_completed_on_success(
        self, mock_orchestrator_with_status
    ):
        """Should update status to COMPLETED when phase succeeds."""
        runner = LoopRunner(orchestrator=mock_orchestrator_with_status)

        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()

        calls = mock_orchestrator_with_status.update_feature_status.call_args_list
        completed_calls = [c for c in calls if c[0][1] == "COMPLETED"]
        assert len(completed_calls) >= 1

    @pytest.mark.asyncio
    async def test_marks_feature_failed_on_error(
        self, mock_orchestrator_with_status
    ):
        """Should update status to FAILED when phase fails."""
        runner = LoopRunner(orchestrator=mock_orchestrator_with_status)

        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = False  # Phase failed
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
            # Should not raise, just log warning
            await runner.run()

        assert runner.state == LoopState.COMPLETED
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/autonomous_loop.py`
```python
import logging

logger = logging.getLogger(__name__)


def _update_feature_status(self, status: str) -> None:
    """Update current feature status in orchestrator."""
    if self.orchestrator is None or self._current_feature is None:
        return

    try:
        self.orchestrator.update_feature_status(
            self._current_feature.name,
            status
        )
    except Exception as e:
        logger.warning(f"Failed to update feature status: {e}")


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

#### 🔵 Refactor: Improve Code
```python
from enum import Enum

class FeatureStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


def _update_feature_status(self, status: FeatureStatus) -> None:
    """Update current feature status in orchestrator, logging failures."""
    if self.orchestrator is None or self._current_feature is None:
        return

    try:
        self.orchestrator.update_feature_status(
            self._current_feature.name,
            status.value
        )
        logger.debug(f"Updated {self._current_feature.name} to {status.value}")
    except Exception as e:
        logger.warning(
            f"Failed to update feature status for {self._current_feature.name}: {e}"
        )
```

### Success Criteria
**Automated:**
- [ ] Test fails initially (Red): `pytest tests/test_autonomous_loop.py::TestLoopRunnerStatusUpdates -v`
- [ ] Test passes after implementation (Green)
- [ ] All existing tests still pass

**Manual:**
- [ ] Status updates visible in orchestrator state
- [ ] Failures logged appropriately

---

## Behavior 5: Resume from Orchestrator State

### Test Specification
**Given**: LoopRunner with orchestrator containing IN_PROGRESS feature
**When**: `resume()` is called
**Then**: Resumes from the IN_PROGRESS feature's phase

**Edge Cases**:
- No IN_PROGRESS feature (start from beginning)
- Multiple IN_PROGRESS features (use first/highest priority)
- Orchestrator state corrupted

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `tests/test_autonomous_loop.py`
```python
class TestLoopRunnerResume:
    """Tests for resuming from orchestrator state."""

    @pytest.mark.asyncio
    async def test_resumes_from_in_progress_feature(self):
        """Should resume from feature marked IN_PROGRESS in orchestrator."""
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = [Mock(path="/plan.md", priority=1)]

        # Simulate existing IN_PROGRESS feature
        orchestrator.get_current_feature.return_value = Mock(
            name="feature-2",
            phase="phase-2",
            status="IN_PROGRESS"
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

        # Should have started from phase-2, not phase-1
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

        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            # Mock to prevent actual execution loop
            with patch.object(runner, '_execute_loop', new_callable=AsyncMock):
                await runner.resume()

        assert runner.current_phase == "stored-phase"
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/autonomous_loop.py`
```python
async def resume(self) -> None:
    """Resume execution from current state."""
    if self.state != LoopState.PAUSED:
        raise ValueError(f"Cannot resume from state: {self.state}")

    self.state = LoopState.RUNNING

    # Check orchestrator for current progress
    if self.orchestrator is not None:
        current = self.orchestrator.get_current_feature()
        if current is not None and current.status == "IN_PROGRESS":
            self.current_phase = current.phase
            self._current_feature = current

    await self._execute_loop()
```

#### 🔵 Refactor: Improve Code
```python
async def _restore_state_from_orchestrator(self) -> None:
    """Restore execution state from orchestrator if available."""
    if self.orchestrator is None:
        return

    current = self.orchestrator.get_current_feature()
    if current is not None and current.status == FeatureStatus.IN_PROGRESS.value:
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

### Success Criteria
**Automated:**
- [ ] Test fails initially (Red): `pytest tests/test_autonomous_loop.py::TestLoopRunnerResume -v`
- [ ] Test passes after implementation (Green)
- [ ] All existing tests still pass

**Manual:**
- [ ] Resume correctly picks up from interrupted state
- [ ] Progress persists across pause/resume cycles

---

## Behavior 6: Backward Compatibility Without Orchestrator

### Test Specification
**Given**: LoopRunner with plan_path but no orchestrator
**When**: `run()` is called
**Then**: Executes exactly as before (single plan, manual phase management)

**Edge Cases**:
- All existing tests must continue passing
- No orchestrator methods called when orchestrator is None

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `tests/test_autonomous_loop.py`
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
        runner = LoopRunner(
            plan_path="/plans/my-plan.md",
            current_phase="custom-phase"
        )

        assert runner.current_phase == "custom-phase"

    @pytest.mark.asyncio
    async def test_pause_resume_without_orchestrator(self):
        """Should pause and resume without orchestrator."""
        runner = LoopRunner(plan_path="/plans/my-plan.md")
        runner.current_phase = "phase-1"

        # Start running
        runner.state = LoopState.RUNNING

        # Pause
        await runner.pause()
        assert runner.state == LoopState.PAUSED

        # Resume
        with patch.object(runner, '_execute_loop', new_callable=AsyncMock):
            await runner.resume()

        assert runner.state == LoopState.RUNNING
        assert runner.current_phase == "phase-1"

    @pytest.mark.asyncio
    async def test_raises_without_plan_or_orchestrator(self):
        """Should raise error when neither plan_path nor orchestrator provided."""
        runner = LoopRunner()  # No plan_path, no orchestrator

        with pytest.raises(ValueError, match="No plan_path provided"):
            await runner.run()
```

#### 🟢 Green: Minimal Implementation
The implementation from previous behaviors should already handle this. Verify tests pass.

#### 🔵 Refactor: Improve Code
No additional refactoring needed - backward compatibility is maintained by the optional orchestrator parameter.

### Success Criteria
**Automated:**
- [ ] Test fails initially if backward compat broken (Red)
- [ ] All backward compat tests pass (Green)
- [ ] ALL existing tests in test_autonomous_loop.py pass
- [ ] Type check passes: `mypy planning_pipeline/`

**Manual:**
- [ ] Existing CLI workflows still work
- [ ] No breaking changes to public API

---

## Integration Testing

### Test Specification
**Given**: Real LoopRunner with real IntegratedOrchestrator
**When**: Full execution cycle runs
**Then**: Plans discovered, phases executed in order, status updated correctly

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `tests/test_loop_orchestrator_integration.py`
```python
import pytest
import tempfile
import os
from pathlib import Path
from planning_pipeline.autonomous_loop import LoopRunner, LoopState
from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator


class TestLoopOrchestratorIntegration:
    """Integration tests for LoopRunner + IntegratedOrchestrator."""

    @pytest.fixture
    def temp_plan_dir(self):
        """Create temporary directory with test plans."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test plans
            plan1 = Path(tmpdir) / "01-setup.md"
            plan1.write_text("""# Setup Plan
## Phase: setup
- Initialize project
""")
            plan2 = Path(tmpdir) / "02-implementation.md"
            plan2.write_text("""# Implementation Plan
## Phase: implementation
- Implement features
""")
            yield tmpdir

    @pytest.fixture
    def orchestrator(self, temp_plan_dir):
        """Create orchestrator pointing to test plans."""
        return IntegratedOrchestrator(plans_directory=temp_plan_dir)

    @pytest.mark.asyncio
    async def test_full_execution_cycle(self, orchestrator):
        """Full cycle: discover plans, execute phases, update status."""
        runner = LoopRunner(orchestrator=orchestrator)

        # Mock phase execution to simulate success
        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()

        # Should have completed all phases
        assert runner.state == LoopState.COMPLETED

        # Orchestrator should show all features completed
        features = orchestrator.get_all_features()
        completed = [f for f in features if f.status == "COMPLETED"]
        assert len(completed) == len(features)

    @pytest.mark.asyncio
    async def test_resume_after_interruption(self, orchestrator):
        """Should correctly resume after pause/interruption."""
        runner = LoopRunner(orchestrator=orchestrator)

        execution_count = 0

        async def mock_execute():
            nonlocal execution_count
            execution_count += 1
            if execution_count == 1:
                # Simulate interruption after first phase
                await runner.pause()
                return True
            return True

        with patch.object(runner, '_execute_phase', side_effect=mock_execute):
            await runner.run()

        # Should be paused after first phase
        assert runner.state == LoopState.PAUSED

        # Resume
        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.resume()

        assert runner.state == LoopState.COMPLETED

    @pytest.mark.asyncio
    async def test_handles_phase_failure(self, orchestrator):
        """Should handle phase failure gracefully."""
        runner = LoopRunner(orchestrator=orchestrator)

        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = False  # Phase fails
            await runner.run()

        assert runner.state == LoopState.FAILED

        # Feature should be marked FAILED
        current = orchestrator.get_current_feature()
        assert current is None or current.status == "FAILED"
```

### Success Criteria
**Automated:**
- [ ] Integration tests pass: `pytest tests/test_loop_orchestrator_integration.py -v`
- [ ] Full test suite passes: `pytest tests/ -v`
- [ ] Type checking passes: `mypy planning_pipeline/`

**Manual:**
- [ ] End-to-end workflow works with real plans
- [ ] Status correctly reflected in orchestrator state

---

## Implementation Order

1. **Behavior 1**: Accept orchestrator parameter (foundation)
2. **Behavior 2**: Plan discovery (core integration)
3. **Behavior 6**: Backward compatibility (ensure no regression)
4. **Behavior 3**: Phase progression (main loop logic)
5. **Behavior 4**: Status updates (observability)
6. **Behavior 5**: Resume from state (resilience)
7. **Integration Tests**: Full cycle verification

## Files Modified

- `planning_pipeline/autonomous_loop.py` - Main implementation
- `tests/test_autonomous_loop.py` - Unit tests
- `tests/test_loop_orchestrator_integration.py` - Integration tests (new file)

## References

- Research: `thoughts/shared/research/2026-01-01-loop-runner-integrated-orchestrator-analysis.md`
- LoopRunner: `planning_pipeline/autonomous_loop.py`
- IntegratedOrchestrator: `planning_pipeline/integrated_orchestrator.py`
- Existing tests: `tests/test_autonomous_loop.py`, `tests/test_integrated_orchestrator.py`
