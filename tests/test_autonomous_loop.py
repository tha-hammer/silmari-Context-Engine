"""Tests for LoopRunner with orchestrator integration."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from planning_pipeline.autonomous_loop import LoopRunner, LoopState


# =============================================================================
# Phase 1: Orchestrator Initialization Tests
# =============================================================================


class TestLoopRunnerOrchestratorInit:
    """Tests for LoopRunner orchestrator initialization."""

    def test_accepts_orchestrator_parameter(self):
        """LoopRunner should accept an optional orchestrator parameter."""
        orchestrator = Mock()
        runner = LoopRunner(orchestrator=orchestrator)
        assert runner.orchestrator is orchestrator

    def test_orchestrator_defaults_to_none(self):
        """LoopRunner should default orchestrator to None for backward compat."""
        runner = LoopRunner()
        assert runner.orchestrator is None

    def test_accepts_both_orchestrator_and_plan_path(self):
        """LoopRunner should accept both orchestrator and explicit plan_path."""
        orchestrator = Mock()
        runner = LoopRunner(orchestrator=orchestrator, plan_path="/explicit/plan.md")
        assert runner.orchestrator is orchestrator
        assert runner.plan_path == "/explicit/plan.md"

    def test_initial_state_is_idle(self):
        """LoopRunner should start in IDLE state."""
        runner = LoopRunner()
        assert runner.state == LoopState.IDLE

    def test_accepts_current_phase(self):
        """LoopRunner should accept an optional current_phase parameter."""
        runner = LoopRunner(current_phase="phase-1")
        assert runner.current_phase == "phase-1"


# =============================================================================
# Phase 2: Plan Discovery Tests
# =============================================================================


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
        with patch.object(runner, "_execute_loop", new_callable=AsyncMock):
            await runner.run()
        mock_orchestrator.discover_plans.assert_called_once()
        assert runner.plan_path == "/plans/feature-a.md"

    @pytest.mark.asyncio
    async def test_explicit_plan_path_takes_precedence(self, mock_orchestrator):
        """Explicit plan_path should skip discovery."""
        runner = LoopRunner(
            orchestrator=mock_orchestrator, plan_path="/explicit/my-plan.md"
        )
        with patch.object(runner, "_execute_loop", new_callable=AsyncMock):
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
        with patch.object(runner, "_execute_loop", new_callable=AsyncMock):
            await runner.run()
        assert runner.plan_path == "/explicit/plan.md"


# =============================================================================
# Phase 3: Backward Compatibility Tests
# =============================================================================


class TestLoopRunnerBackwardCompat:
    """Tests ensuring backward compatibility without orchestrator."""

    @pytest.mark.asyncio
    async def test_runs_without_orchestrator(self):
        """Should run successfully with just plan_path, no orchestrator."""
        runner = LoopRunner(plan_path="/plans/my-plan.md")
        with patch.object(runner, "_execute_loop", new_callable=AsyncMock):
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
        with patch.object(runner, "_execute_loop", new_callable=AsyncMock):
            await runner.resume()
        assert runner.state == LoopState.RUNNING
        assert runner.current_phase == "phase-1"

    @pytest.mark.asyncio
    async def test_raises_without_plan_or_orchestrator(self):
        """Should raise error when neither plan_path nor orchestrator provided."""
        runner = LoopRunner()
        with pytest.raises(ValueError, match="No plan_path.*or orchestrator available"):
            await runner.run()


# =============================================================================
# Phase 4: Phase Progression Tests
# =============================================================================


class TestLoopRunnerPhaseProgression:
    """Tests for phase progression via orchestrator."""

    @pytest.fixture
    def mock_orchestrator_with_features(self):
        """Orchestrator that returns features in sequence."""
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = [Mock(path="/plans/main.md", priority=1)]

        # Mock bd for status updates
        orchestrator.bd = Mock()
        orchestrator.bd.update_status = Mock()

        features = [
            {"id": "feature-1", "title": "Feature 1", "status": "open"},
            {"id": "feature-2", "title": "Feature 2", "status": "open"},
            None,  # No more features
        ]
        orchestrator.get_next_feature.side_effect = features
        orchestrator.get_current_feature = Mock(return_value=None)
        return orchestrator

    @pytest.mark.asyncio
    async def test_queries_next_feature_after_phase_complete(
        self, mock_orchestrator_with_features
    ):
        """Should query orchestrator for next feature when phase completes."""
        runner = LoopRunner(orchestrator=mock_orchestrator_with_features)
        with patch.object(runner, "_execute_phase", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()
        assert mock_orchestrator_with_features.get_next_feature.call_count >= 1

    @pytest.mark.asyncio
    async def test_completes_when_no_more_features(self, mock_orchestrator_with_features):
        """Should set state to COMPLETED when no more features available."""
        runner = LoopRunner(orchestrator=mock_orchestrator_with_features)
        with patch.object(runner, "_execute_phase", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()
        assert runner.state == LoopState.COMPLETED

    @pytest.mark.asyncio
    async def test_skips_blocked_features(self):
        """Should skip BLOCKED features and move to next unblocked."""
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = [Mock(path="/plan.md", priority=1)]
        orchestrator.bd = Mock()
        orchestrator.bd.update_status = Mock()
        orchestrator.get_next_feature.side_effect = [
            {"id": "blocked-feature", "status": "BLOCKED"},
            {"id": "available-feature", "status": "open"},
            None,
        ]
        orchestrator.get_current_feature = Mock(return_value=None)
        runner = LoopRunner(orchestrator=orchestrator)
        with patch.object(runner, "_execute_phase", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()
        assert orchestrator.get_next_feature.call_count >= 2


# =============================================================================
# Phase 5: Status Updates Tests
# =============================================================================


class TestLoopRunnerStatusUpdates:
    """Tests for feature status updates to orchestrator."""

    @pytest.fixture
    def mock_orchestrator_with_status(self):
        """Orchestrator that tracks status updates."""
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = [Mock(path="/plan.md", priority=1)]
        orchestrator.get_next_feature.side_effect = [
            {"id": "feature-1", "title": "Feature 1", "status": "open"},
            None,
        ]
        orchestrator.bd = Mock()
        orchestrator.bd.update_status = Mock()
        orchestrator.get_current_feature = Mock(return_value=None)
        return orchestrator

    @pytest.mark.asyncio
    async def test_marks_feature_in_progress_when_starting(
        self, mock_orchestrator_with_status
    ):
        """Should update status to IN_PROGRESS when starting phase."""
        runner = LoopRunner(orchestrator=mock_orchestrator_with_status)
        with patch.object(runner, "_execute_phase", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()
        calls = mock_orchestrator_with_status.bd.update_status.call_args_list
        in_progress_calls = [c for c in calls if "in_progress" in str(c).lower()]
        assert len(in_progress_calls) >= 1

    @pytest.mark.asyncio
    async def test_marks_feature_completed_on_success(self, mock_orchestrator_with_status):
        """Should update status to COMPLETED when phase succeeds."""
        runner = LoopRunner(orchestrator=mock_orchestrator_with_status)
        with patch.object(runner, "_execute_phase", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()
        calls = mock_orchestrator_with_status.bd.update_status.call_args_list
        completed_calls = [c for c in calls if "completed" in str(c).lower()]
        assert len(completed_calls) >= 1

    @pytest.mark.asyncio
    async def test_marks_feature_failed_on_error(self, mock_orchestrator_with_status):
        """Should update status to FAILED when phase fails."""
        runner = LoopRunner(orchestrator=mock_orchestrator_with_status)
        with patch.object(runner, "_execute_phase", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = False
            await runner.run()
        calls = mock_orchestrator_with_status.bd.update_status.call_args_list
        failed_calls = [c for c in calls if "failed" in str(c).lower()]
        assert len(failed_calls) >= 1

    @pytest.mark.asyncio
    async def test_continues_on_status_update_failure(self):
        """Should log warning and continue if status update fails."""
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = [Mock(path="/plan.md", priority=1)]
        orchestrator.get_next_feature.side_effect = [
            {"id": "feature-1", "title": "Feature 1", "status": "open"},
            None,
        ]
        orchestrator.bd = Mock()
        orchestrator.bd.update_status.side_effect = Exception("DB error")
        orchestrator.get_current_feature = Mock(return_value=None)
        runner = LoopRunner(orchestrator=orchestrator)
        with patch.object(runner, "_execute_phase", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()  # Should not raise
        assert runner.state == LoopState.COMPLETED


# =============================================================================
# Phase 6: Resume Tests
# =============================================================================


class TestLoopRunnerResume:
    """Tests for resuming from orchestrator state."""

    @pytest.mark.asyncio
    async def test_resumes_from_in_progress_feature(self):
        """Should resume from feature marked IN_PROGRESS in orchestrator."""
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = [Mock(path="/plan.md", priority=1)]
        orchestrator.get_current_feature.return_value = {
            "id": "feature-2",
            "title": "Feature 2",
            "status": "IN_PROGRESS",
        }
        orchestrator.bd = Mock()
        orchestrator.bd.update_status = Mock()
        orchestrator.get_next_feature.side_effect = [
            {"id": "feature-2", "title": "Feature 2", "status": "IN_PROGRESS"},
            None,
        ]
        runner = LoopRunner(orchestrator=orchestrator)
        runner.state = LoopState.PAUSED
        with patch.object(runner, "_execute_phase", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.resume()
        assert runner.current_phase == "feature-2"

    @pytest.mark.asyncio
    async def test_starts_fresh_when_no_in_progress(self):
        """Should start from beginning when no IN_PROGRESS feature."""
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = [Mock(path="/plan.md", priority=1)]
        orchestrator.get_current_feature.return_value = None
        orchestrator.bd = Mock()
        orchestrator.bd.update_status = Mock()
        orchestrator.get_next_feature.side_effect = [
            {"id": "feature-1", "title": "Feature 1", "status": "open"},
            None,
        ]
        runner = LoopRunner(orchestrator=orchestrator)
        runner.state = LoopState.PAUSED
        with patch.object(runner, "_execute_phase", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.resume()
        assert runner.current_phase == "feature-1"

    @pytest.mark.asyncio
    async def test_resume_without_orchestrator_uses_stored_phase(self):
        """Backward compat: resume without orchestrator uses stored phase."""
        runner = LoopRunner(plan_path="/plan.md")
        runner.state = LoopState.PAUSED
        runner.current_phase = "stored-phase"
        with patch.object(runner, "_execute_loop", new_callable=AsyncMock):
            await runner.resume()
        assert runner.current_phase == "stored-phase"

    @pytest.mark.asyncio
    async def test_resume_raises_if_not_paused(self):
        """Should raise error when trying to resume from non-PAUSED state."""
        runner = LoopRunner(plan_path="/plan.md")
        runner.state = LoopState.IDLE
        with pytest.raises(ValueError, match="Cannot resume from state"):
            await runner.resume()
