"""Integration tests for LoopRunner + IntegratedOrchestrator."""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from planning_pipeline.autonomous_loop import LoopRunner, LoopState
from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator, PlanInfo


class TestLoopOrchestratorIntegration:
    """Integration tests for LoopRunner + IntegratedOrchestrator."""

    @pytest.fixture
    def temp_plan_dir(self):
        """Create temporary directory with test plans."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan1 = Path(tmpdir) / "thoughts" / "searchable" / "shared" / "plans"
            plan1.mkdir(parents=True)

            overview = plan1 / "2026-01-01-test-feature-00-overview.md"
            overview.write_text(
                """# Test Feature Plan

## Overview
Test plan for integration testing.
"""
            )

            phase1 = plan1 / "2026-01-01-test-feature-01-setup.md"
            phase1.write_text(
                """# Phase 1: Setup

## Overview
Setup phase for testing.
"""
            )

            yield tmpdir

    @pytest.fixture
    def mock_orchestrator(self, temp_plan_dir):
        """Create a mock orchestrator that simulates real behavior."""
        orchestrator = Mock(spec=IntegratedOrchestrator)
        orchestrator.project_path = Path(temp_plan_dir)

        # Mock discover_plans to return test plans
        orchestrator.discover_plans.return_value = [
            PlanInfo(
                path=str(Path(temp_plan_dir) / "thoughts/searchable/shared/plans/2026-01-01-test-feature-00-overview.md"),
                name="test-feature",
                priority=1
            )
        ]

        # Mock bd controller
        orchestrator.bd = Mock()
        orchestrator.bd.update_status = Mock(return_value={"success": True})

        # Track features state
        features = [
            {"id": "feature-1", "title": "Setup", "status": "open"},
            {"id": "feature-2", "title": "Implement", "status": "open"},
            None,  # No more features
        ]
        orchestrator.get_next_feature.side_effect = features
        orchestrator.get_current_feature.return_value = None

        return orchestrator

    @pytest.mark.asyncio
    async def test_full_execution_cycle(self, mock_orchestrator):
        """Full cycle: discover plans, execute phases, update status."""
        runner = LoopRunner(orchestrator=mock_orchestrator)
        with patch.object(runner, "_execute_phase", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()

        assert runner.state == LoopState.COMPLETED

        # Check that status updates were called
        assert mock_orchestrator.bd.update_status.call_count >= 2  # in_progress + completed

    @pytest.mark.asyncio
    async def test_resume_after_interruption(self, mock_orchestrator):
        """Should correctly resume after pause/interruption."""
        runner = LoopRunner(orchestrator=mock_orchestrator)
        execution_count = 0

        async def mock_execute():
            nonlocal execution_count
            execution_count += 1
            if execution_count == 1:
                await runner.pause()
                return True
            return True

        with patch.object(runner, "_execute_phase", side_effect=mock_execute):
            await runner.run()

        assert runner.state == LoopState.PAUSED

        # Reset features for resume
        mock_orchestrator.get_next_feature.side_effect = [
            {"id": "feature-2", "title": "Implement", "status": "open"},
            None,
        ]

        with patch.object(runner, "_execute_phase", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.resume()

        assert runner.state == LoopState.COMPLETED

    @pytest.mark.asyncio
    async def test_handles_phase_failure(self, mock_orchestrator):
        """Should handle phase failure gracefully."""
        runner = LoopRunner(orchestrator=mock_orchestrator)
        with patch.object(runner, "_execute_phase", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = False
            await runner.run()

        assert runner.state == LoopState.FAILED

        # Check that failed status was updated
        calls = mock_orchestrator.bd.update_status.call_args_list
        failed_calls = [c for c in calls if "failed" in str(c).lower()]
        assert len(failed_calls) >= 1

    @pytest.mark.asyncio
    async def test_mixed_mode_explicit_path_with_orchestrator(
        self, mock_orchestrator, temp_plan_dir
    ):
        """Should use explicit plan_path even when orchestrator available."""
        explicit_plan = Path(temp_plan_dir) / "explicit.md"
        explicit_plan.write_text("# Explicit Plan\n")

        runner = LoopRunner(
            orchestrator=mock_orchestrator, plan_path=str(explicit_plan)
        )

        # Since explicit path is provided, discovery shouldn't be called
        with patch.object(runner, "_execute_loop", new_callable=AsyncMock):
            await runner.run()

        assert runner.plan_path == str(explicit_plan)
        mock_orchestrator.discover_plans.assert_not_called()


class TestPlanDiscoveryIntegration:
    """Tests for plan discovery with real file system."""

    @pytest.fixture
    def temp_project_with_plans(self):
        """Create a temporary project structure with plan files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create plans directory structure
            plans_dir = project_path / "thoughts" / "searchable" / "shared" / "plans"
            plans_dir.mkdir(parents=True)

            # Create overview plan
            (plans_dir / "2026-01-01-feature-a-00-overview.md").write_text(
                "# Feature A Overview\n"
            )

            # Create phase plans
            (plans_dir / "2026-01-01-feature-a-01-setup.md").write_text(
                "# Phase 1: Setup\n"
            )
            (plans_dir / "2026-01-01-feature-a-02-implement.md").write_text(
                "# Phase 2: Implement\n"
            )

            # Create beads directory (mock)
            beads_dir = project_path / ".beads"
            beads_dir.mkdir()

            yield project_path

    def test_discover_plans_finds_overview_files(self, temp_project_with_plans):
        """Should discover plan overview files."""
        with patch("planning_pipeline.integrated_orchestrator.BeadsController"):
            orchestrator = IntegratedOrchestrator(temp_project_with_plans)
            plans = orchestrator.discover_plans()

        assert len(plans) >= 1
        assert any("overview" in p.path.lower() for p in plans)

    def test_plans_sorted_by_priority(self, temp_project_with_plans):
        """Plans should be sorted by priority (filename prefix)."""
        # Add another plan with different priority
        plans_dir = temp_project_with_plans / "thoughts" / "searchable" / "shared" / "plans"
        (plans_dir / "2026-01-02-feature-b-00-overview.md").write_text(
            "# Feature B Overview\n"
        )

        with patch("planning_pipeline.integrated_orchestrator.BeadsController"):
            orchestrator = IntegratedOrchestrator(temp_project_with_plans)
            plans = orchestrator.discover_plans()

        # Plans should be sorted by priority
        priorities = [p.priority for p in plans]
        assert priorities == sorted(priorities)
