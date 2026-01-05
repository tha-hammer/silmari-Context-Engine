"""Tests for RLMActPipeline orchestration.

This module tests the pipeline orchestrator that coordinates all phases
of the silmari-rlm-act pipeline.
"""

import pytest
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from silmari_rlm_act.models import (
    AutonomyMode,
    PhaseResult,
    PhaseStatus,
    PhaseType,
)


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    project = tmp_path / "test_project"
    project.mkdir()
    (project / ".rlm-act-checkpoints").mkdir()
    return project


@pytest.fixture
def mock_cwa() -> MagicMock:
    """Create a mock CWA integration."""
    cwa = MagicMock()
    cwa.store_research.return_value = "research_001"
    cwa.store_requirement.return_value = "req_001"
    cwa.store_plan.return_value = "plan_001"
    return cwa


@pytest.fixture
def mock_beads_controller() -> MagicMock:
    """Create a mock beads controller."""
    beads = MagicMock()
    beads.create_epic.return_value = {"success": True, "data": {"id": "epic_001"}}
    beads.create_issue.return_value = {"success": True, "data": {"id": "issue_001"}}
    beads.add_dependency.return_value = {"success": True}
    beads.sync.return_value = {"success": True}
    return beads


@pytest.fixture
def sample_research_result() -> PhaseResult:
    """Create a sample research phase result."""
    return PhaseResult(
        phase_type=PhaseType.RESEARCH,
        status=PhaseStatus.COMPLETE,
        artifacts=["thoughts/research/doc.md"],
        started_at=datetime(2026, 1, 5, 10, 0, 0),
        completed_at=datetime(2026, 1, 5, 10, 5, 0),
        duration_seconds=300.0,
        metadata={"cwa_entry_id": "research_001"},
    )


@pytest.fixture
def sample_decomposition_result() -> PhaseResult:
    """Create a sample decomposition phase result."""
    return PhaseResult(
        phase_type=PhaseType.DECOMPOSITION,
        status=PhaseStatus.COMPLETE,
        artifacts=["hierarchy.json"],
        started_at=datetime(2026, 1, 5, 10, 5, 0),
        completed_at=datetime(2026, 1, 5, 10, 10, 0),
        duration_seconds=300.0,
        metadata={"requirements_count": 5},
    )


# ===========================================================================
# Behavior 1: Pipeline Initialization
# ===========================================================================


class TestPipelineInitialization:
    """Tests for RLMActPipeline initialization."""

    def test_init_creates_pipeline_state(self, temp_project: Path, mock_cwa: MagicMock) -> None:
        """Pipeline initializes with a PipelineState."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
        )

        assert pipeline.state is not None
        assert pipeline.state.project_path == str(temp_project)

    def test_init_default_autonomy_mode(self, temp_project: Path, mock_cwa: MagicMock) -> None:
        """Pipeline defaults to CHECKPOINT autonomy mode."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
        )

        assert pipeline.state.autonomy_mode == AutonomyMode.CHECKPOINT

    def test_init_custom_autonomy_mode(self, temp_project: Path, mock_cwa: MagicMock) -> None:
        """Pipeline accepts custom autonomy mode."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
        )

        assert pipeline.state.autonomy_mode == AutonomyMode.FULLY_AUTONOMOUS

    def test_init_creates_checkpoint_manager(
        self, temp_project: Path, mock_cwa: MagicMock
    ) -> None:
        """Pipeline creates a CheckpointManager."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
        )

        assert pipeline.checkpoint_manager is not None


# ===========================================================================
# Behavior 2: Phase Execution Order
# ===========================================================================


class TestPhaseExecutionOrder:
    """Tests for correct phase execution order."""

    def test_phase_order_is_sequential(self, temp_project: Path, mock_cwa: MagicMock) -> None:
        """Phases execute in the correct order."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(project_path=temp_project, cwa=mock_cwa)

        expected_order = [
            PhaseType.RESEARCH,
            PhaseType.DECOMPOSITION,
            PhaseType.TDD_PLANNING,
            PhaseType.MULTI_DOC,
            PhaseType.BEADS_SYNC,
            PhaseType.IMPLEMENTATION,
        ]

        assert pipeline.phase_order == expected_order

    def test_get_next_phase_after_none(
        self, temp_project: Path, mock_cwa: MagicMock
    ) -> None:
        """get_next_phase returns RESEARCH when no phases completed."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(project_path=temp_project, cwa=mock_cwa)

        next_phase = pipeline.get_next_phase()
        assert next_phase == PhaseType.RESEARCH

    def test_get_next_phase_after_research(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        sample_research_result: PhaseResult,
    ) -> None:
        """get_next_phase returns DECOMPOSITION after RESEARCH."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(project_path=temp_project, cwa=mock_cwa)
        pipeline.state.set_phase_result(PhaseType.RESEARCH, sample_research_result)

        next_phase = pipeline.get_next_phase()
        assert next_phase == PhaseType.DECOMPOSITION

    def test_get_next_phase_all_complete(
        self, temp_project: Path, mock_cwa: MagicMock
    ) -> None:
        """get_next_phase returns None when all phases complete."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(project_path=temp_project, cwa=mock_cwa)

        # Mark all phases complete
        for phase_type in PhaseType:
            result = PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
            )
            pipeline.state.set_phase_result(phase_type, result)

        next_phase = pipeline.get_next_phase()
        assert next_phase is None


# ===========================================================================
# Behavior 3: Checkpoint Integration
# ===========================================================================


class TestCheckpointIntegration:
    """Tests for checkpoint creation and resume."""

    def test_run_creates_checkpoint_after_phase(
        self, temp_project: Path, mock_cwa: MagicMock
    ) -> None:
        """Running a phase creates a checkpoint."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(project_path=temp_project, cwa=mock_cwa)

        # Mock the research phase
        mock_result = PhaseResult(
            phase_type=PhaseType.RESEARCH,
            status=PhaseStatus.COMPLETE,
            artifacts=["doc.md"],
        )

        with patch.object(pipeline, "_execute_phase", return_value=mock_result):
            pipeline.run_single_phase(PhaseType.RESEARCH, research_question="test")

        # Check checkpoint was created
        checkpoints = list((temp_project / ".rlm-act-checkpoints").glob("*.json"))
        assert len(checkpoints) == 1

    def test_resume_from_checkpoint_loads_state(
        self, temp_project: Path, mock_cwa: MagicMock
    ) -> None:
        """Resuming from checkpoint restores pipeline state."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        # Create initial pipeline and run a phase
        pipeline = RLMActPipeline(project_path=temp_project, cwa=mock_cwa)

        mock_result = PhaseResult(
            phase_type=PhaseType.RESEARCH,
            status=PhaseStatus.COMPLETE,
            artifacts=["doc.md"],
        )

        with patch.object(pipeline, "_execute_phase", return_value=mock_result):
            pipeline.run_single_phase(PhaseType.RESEARCH, research_question="test")

        # Create new pipeline and resume
        new_pipeline = RLMActPipeline(project_path=temp_project, cwa=mock_cwa)
        resumed = new_pipeline.resume_from_checkpoint()

        assert resumed is True
        assert new_pipeline.state.is_phase_complete(PhaseType.RESEARCH)


# ===========================================================================
# Behavior 4: Full Pipeline Execution
# ===========================================================================


class TestFullPipelineExecution:
    """Tests for running the full pipeline."""

    def test_run_executes_all_phases_autonomous(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
    ) -> None:
        """run() in FULLY_AUTONOMOUS mode executes all phases."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        # Mock all phase executions
        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            result = pipeline.run(research_question="test question")

        assert result.status == PhaseStatus.COMPLETE
        assert pipeline.state.all_phases_complete()

    def test_run_stops_on_failure(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
    ) -> None:
        """run() stops when a phase fails."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
        )

        # Mock research success, decomposition failure
        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            if phase_type == PhaseType.DECOMPOSITION:
                return PhaseResult(
                    phase_type=phase_type,
                    status=PhaseStatus.FAILED,
                    errors=["Test error"],
                )
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            result = pipeline.run(research_question="test question")

        assert result.status == PhaseStatus.FAILED
        assert not pipeline.state.all_phases_complete()
        assert pipeline.state.is_phase_complete(PhaseType.RESEARCH)
        assert not pipeline.state.is_phase_complete(PhaseType.DECOMPOSITION)


# ===========================================================================
# Behavior 5: State Tracking
# ===========================================================================


class TestStateTracking:
    """Tests for pipeline state tracking."""

    def test_state_tracks_completed_phases(
        self, temp_project: Path, mock_cwa: MagicMock
    ) -> None:
        """Pipeline state tracks which phases are completed."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(project_path=temp_project, cwa=mock_cwa)

        mock_result = PhaseResult(
            phase_type=PhaseType.RESEARCH,
            status=PhaseStatus.COMPLETE,
        )

        with patch.object(pipeline, "_execute_phase", return_value=mock_result):
            pipeline.run_single_phase(PhaseType.RESEARCH, research_question="test")

        assert pipeline.state.is_phase_complete(PhaseType.RESEARCH)
        assert not pipeline.state.is_phase_complete(PhaseType.DECOMPOSITION)

    def test_state_tracks_cwa_entry_ids(
        self, temp_project: Path, mock_cwa: MagicMock
    ) -> None:
        """Pipeline state tracks CWA entry IDs per phase."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(project_path=temp_project, cwa=mock_cwa)

        mock_result = PhaseResult(
            phase_type=PhaseType.RESEARCH,
            status=PhaseStatus.COMPLETE,
            metadata={"cwa_entry_id": "research_001"},
        )

        with patch.object(pipeline, "_execute_phase", return_value=mock_result):
            pipeline.run_single_phase(PhaseType.RESEARCH, research_question="test")

        entries = pipeline.state.get_context_entries(PhaseType.RESEARCH)
        assert "research_001" in entries


# ===========================================================================
# Behavior 6: Error Handling
# ===========================================================================


class TestErrorHandling:
    """Tests for pipeline error handling."""

    def test_handles_phase_exception(
        self, temp_project: Path, mock_cwa: MagicMock
    ) -> None:
        """Pipeline handles exceptions during phase execution."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(project_path=temp_project, cwa=mock_cwa)

        with patch.object(
            pipeline, "_execute_phase", side_effect=RuntimeError("Test error")
        ):
            result = pipeline.run_single_phase(PhaseType.RESEARCH, research_question="test")

        assert result.status == PhaseStatus.FAILED
        assert "Test error" in result.errors[0]

    def test_failed_phase_creates_checkpoint(
        self, temp_project: Path, mock_cwa: MagicMock
    ) -> None:
        """Failed phase still creates checkpoint with error state."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(project_path=temp_project, cwa=mock_cwa)

        mock_result = PhaseResult(
            phase_type=PhaseType.RESEARCH,
            status=PhaseStatus.FAILED,
            errors=["Test failure"],
        )

        with patch.object(pipeline, "_execute_phase", return_value=mock_result):
            pipeline.run_single_phase(PhaseType.RESEARCH, research_question="test")

        # Check checkpoint was created
        checkpoints = list((temp_project / ".rlm-act-checkpoints").glob("*.json"))
        assert len(checkpoints) == 1
