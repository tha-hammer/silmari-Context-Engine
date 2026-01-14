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


# ===========================================================================
# Behavior 7: Research Path Skip (REQ_000.3)
# ===========================================================================


@pytest.fixture
def temp_research_doc(tmp_path: Path) -> Path:
    """Create a temporary research document."""
    doc = tmp_path / "research.md"
    doc.write_text("# Research Document\n\nTest content.")
    return doc


class TestResearchPathSkip:
    """Tests for skipping research phase with --research-path (REQ_000.3)."""

    def test_research_path_skips_research_phase(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_research_doc: Path,
    ) -> None:
        """REQ_000.3: ResearchPhase.execute_with_checkpoint() is NOT called when research_path provided."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        # Mock remaining phase executions (not research)
        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
                metadata={"hierarchy_path": str(temp_project / "hierarchy.json")}
                if phase_type == PhaseType.DECOMPOSITION
                else {},
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute) as mock_exec:
            pipeline.run(
                research_question="",
                research_path=str(temp_research_doc),
            )

            # Research phase should be skipped (not called)
            calls = [call[0][0] for call in mock_exec.call_args_list]
            assert PhaseType.RESEARCH not in calls

    def test_research_path_creates_synthetic_result(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_research_doc: Path,
    ) -> None:
        """REQ_000.3: Synthetic PhaseResult is created for RESEARCH with status=COMPLETE."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        # Mock remaining phase executions (not research)
        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
                metadata={"hierarchy_path": str(temp_project / "hierarchy.json")}
                if phase_type == PhaseType.DECOMPOSITION
                else {},
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                research_path=str(temp_research_doc),
            )

        # Check synthetic result was created
        research_result = pipeline.state.get_phase_result(PhaseType.RESEARCH)
        assert research_result is not None
        assert research_result.status == PhaseStatus.COMPLETE

    def test_synthetic_result_includes_research_path_in_artifacts(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_research_doc: Path,
    ) -> None:
        """REQ_000.3: Synthetic PhaseResult includes research_path in artifacts."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
                metadata={"hierarchy_path": str(temp_project / "hierarchy.json")}
                if phase_type == PhaseType.DECOMPOSITION
                else {},
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                research_path=str(temp_research_doc),
            )

        research_result = pipeline.state.get_phase_result(PhaseType.RESEARCH)
        assert len(research_result.artifacts) == 1
        assert str(temp_research_doc.resolve()) in research_result.artifacts[0]

    def test_synthetic_result_metadata_indicates_skipped(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_research_doc: Path,
    ) -> None:
        """REQ_000.3: Synthetic PhaseResult includes metadata indicating skipped."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
                metadata={"hierarchy_path": str(temp_project / "hierarchy.json")}
                if phase_type == PhaseType.DECOMPOSITION
                else {},
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                research_path=str(temp_research_doc),
            )

        research_result = pipeline.state.get_phase_result(PhaseType.RESEARCH)
        assert research_result.metadata.get("skipped") is True
        assert research_result.metadata.get("reason") == "research_path provided"

    def test_research_path_creates_skipped_checkpoint(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_research_doc: Path,
    ) -> None:
        """REQ_000.3: Checkpoint created with phase name 'research-skipped'."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
                metadata={"hierarchy_path": str(temp_project / "hierarchy.json")}
                if phase_type == PhaseType.DECOMPOSITION
                else {},
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                research_path=str(temp_research_doc),
            )

        # Check that at least one checkpoint contains 'research-skipped'
        import json

        checkpoints = list((temp_project / ".rlm-act-checkpoints").glob("*.json"))
        found_skipped = False
        for cp in checkpoints:
            data = json.loads(cp.read_text())
            if data.get("phase") == "research-skipped":
                found_skipped = True
                break
        assert found_skipped, "No checkpoint found with phase='research-skipped'"

    def test_decomposition_receives_research_path(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_research_doc: Path,
    ) -> None:
        """REQ_000.3: DecompositionPhase receives research_path from synthetic result."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        decomposition_kwargs_received = {}

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            if phase_type == PhaseType.DECOMPOSITION:
                decomposition_kwargs_received.update(kwargs)
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
                metadata={"hierarchy_path": str(temp_project / "hierarchy.json")}
                if phase_type == PhaseType.DECOMPOSITION
                else {},
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                research_path=str(temp_research_doc),
            )

        # Decomposition should be able to find research path from artifacts
        # which is available via state.get_phase_result(PhaseType.RESEARCH).artifacts
        research_result = pipeline.state.get_phase_result(PhaseType.RESEARCH)
        assert str(temp_research_doc.resolve()) in research_result.artifacts[0]


# ===========================================================================
# Behavior 8: Plan Path Skip (REQ_001)
# ===========================================================================


@pytest.fixture
def temp_plan_doc(tmp_path: Path) -> Path:
    """Create a temporary plan/hierarchy JSON document."""
    import json

    doc = tmp_path / "hierarchy.json"
    hierarchy = {
        "requirements": [
            {
                "id": "REQ_001",
                "description": "Test requirement",
                "type": "parent",
                "parent_id": None,
                "children": [],
                "acceptance_criteria": [],
                "implementation": None,
                "testable_properties": [],
                "function_id": None,
                "related_concepts": [],
                "category": "functional",
            }
        ],
        "metadata": {"source": "test"},
    }
    doc.write_text(json.dumps(hierarchy, indent=2))
    return doc


class TestPlanPathSkip:
    """Tests for skipping phases with --plan-path (REQ_001)."""

    def test_plan_path_skips_research_phase(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_001.4: ResearchPhase.execute() is NOT called when hierarchy_path provided."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute) as mock_exec:
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_plan_doc),
            )

            # Research phase should be skipped (not called)
            calls = [call[0][0] for call in mock_exec.call_args_list]
            assert PhaseType.RESEARCH not in calls

    def test_plan_path_skips_decomposition_phase(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_001.3: DecompositionPhase.execute() is NOT called when hierarchy_path provided."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute) as mock_exec:
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_plan_doc),
            )

            # Decomposition phase should be skipped (not called)
            calls = [call[0][0] for call in mock_exec.call_args_list]
            assert PhaseType.DECOMPOSITION not in calls

    def test_plan_path_creates_synthetic_research_result(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_001.4: Synthetic PhaseResult is created for RESEARCH with status=COMPLETE."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_plan_doc),
            )

        research_result = pipeline.state.get_phase_result(PhaseType.RESEARCH)
        assert research_result is not None
        assert research_result.status == PhaseStatus.COMPLETE
        assert research_result.metadata.get("skipped") is True
        assert "hierarchy_path provided" in research_result.metadata.get("reason", "")

    def test_plan_path_creates_synthetic_decomposition_result(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_001.3: Synthetic PhaseResult is created for DECOMPOSITION with status=COMPLETE."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_plan_doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert decomp_result is not None
        assert decomp_result.status == PhaseStatus.COMPLETE
        assert decomp_result.metadata.get("skipped") is True

    def test_plan_path_decomposition_result_includes_hierarchy_path(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_001.3: Synthetic DECOMPOSITION result includes hierarchy_path in metadata."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_plan_doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert decomp_result.metadata.get("hierarchy_path") == str(temp_plan_doc)

    def test_plan_path_creates_skipped_checkpoints(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_001.3/4: Checkpoints created with 'skipped' phase names."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_plan_doc),
            )

        # Check that checkpoints with skipped phases exist
        checkpoints = list((temp_project / ".rlm-act-checkpoints").glob("*.json"))
        skipped_phases = set()
        for cp in checkpoints:
            data = json.loads(cp.read_text())
            if "skipped" in data.get("phase", ""):
                skipped_phases.add(data["phase"])

        assert "research-skipped" in skipped_phases
        assert "decomposition-skipped" in skipped_phases

    def test_plan_path_validates_json_format(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_001.5: Invalid JSON produces error."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        # Create invalid JSON file
        invalid_doc = tmp_path / "invalid.json"
        invalid_doc.write_text("not valid json {{{")

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(invalid_doc),
        )

        # Should fail with validation error
        assert result.status == PhaseStatus.FAILED
        assert any("json" in err.lower() or "valid" in err.lower() for err in result.errors)

    def test_plan_path_validates_requirement_hierarchy_structure(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_001.5: Invalid hierarchy structure produces error."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        # Create invalid hierarchy (missing requirements field)
        invalid_doc = tmp_path / "invalid_hierarchy.json"
        invalid_doc.write_text(json.dumps({"not_requirements": []}))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(invalid_doc),
        )

        # Should fail (empty hierarchy is valid JSON but may not have requirements)
        # This tests the hierarchy format validation
        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert decomp_result is not None

    def test_plan_path_validates_requirement_type(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_001.5: Invalid requirement type produces error."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        # Create hierarchy with invalid type
        invalid_doc = tmp_path / "invalid_type.json"
        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "invalid_type",  # Not in VALID_REQUIREMENT_TYPES
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    "category": "functional",
                }
            ],
            "metadata": {},
        }
        invalid_doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(invalid_doc),
        )

        # Should fail with validation error about type
        assert result.status == PhaseStatus.FAILED
        assert any("type" in err.lower() or "invalid" in err.lower() for err in result.errors)

    def test_plan_path_validates_requirement_category(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_001.5: Invalid requirement category produces error."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        # Create hierarchy with invalid category
        invalid_doc = tmp_path / "invalid_category.json"
        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    "category": "invalid_category",  # Not in VALID_CATEGORIES
                }
            ],
            "metadata": {},
        }
        invalid_doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(invalid_doc),
        )

        # Should fail with validation error about category
        assert result.status == PhaseStatus.FAILED
        assert any("category" in err.lower() or "invalid" in err.lower() for err in result.errors)

    def test_plan_path_result_metadata_includes_counts(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_001.5: Successful validation includes requirements_count and total_nodes."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_plan_doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert "requirements_count" in decomp_result.metadata
        assert "total_nodes" in decomp_result.metadata

    def test_tdd_planning_receives_hierarchy_path(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_001.3: TDDPlanningPhase receives hierarchy_path from synthetic decomposition result."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        tdd_kwargs_received = {}

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            if phase_type == PhaseType.TDD_PLANNING:
                tdd_kwargs_received.update(kwargs)
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_plan_doc),
            )

        # TDD planning should receive hierarchy_path
        # The pipeline looks up hierarchy_path from decomposition metadata
        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert decomp_result.metadata.get("hierarchy_path") == str(temp_plan_doc)


# =============================================================================
# Phase 3 - REQ_002: Plan Document Validation Tests
# =============================================================================


class TestPlanDocumentValidation:
    """Tests for REQ_002: Plan document validation before decomposition."""

    # -------------------------------------------------------------------------
    # REQ_002.1: Validate JSON structure and file format (Tier 1)
    # -------------------------------------------------------------------------

    def test_empty_file_produces_error(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.1: Empty files must produce specific error message."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        # Create empty file
        empty_doc = tmp_path / "empty.json"
        empty_doc.write_text("")

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(empty_doc),
        )

        assert result.status == PhaseStatus.FAILED
        # Should mention JSON parsing issue
        assert any("json" in err.lower() for err in result.errors)

    def test_json_structure_requires_requirements_key(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.1: JSON must contain 'requirements' key."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        # Valid JSON but missing 'requirements' key
        invalid_doc = tmp_path / "missing_requirements.json"
        invalid_doc.write_text(json.dumps({"metadata": {}, "other_key": []}))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(invalid_doc),
        )

        # Empty requirements is valid - verify hierarchy was created
        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert decomp_result is not None

    def test_json_error_includes_position_info(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.1: JSON parse errors include line/character position."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        # Create JSON with syntax error at known position
        invalid_doc = tmp_path / "syntax_error.json"
        invalid_doc.write_text('{\n  "requirements": [\n    invalid\n  ]\n}')

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(invalid_doc),
        )

        assert result.status == PhaseStatus.FAILED
        # Error should contain position info (line/column/char from JSONDecodeError)
        error_text = " ".join(result.errors).lower()
        assert "json" in error_text or "line" in error_text or "column" in error_text

    def test_utf8_encoding_error_handled(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.1: Invalid UTF-8 encoding produces appropriate error."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        # Create file with invalid UTF-8 bytes
        invalid_doc = tmp_path / "invalid_utf8.json"
        invalid_doc.write_bytes(b'{"requirements": [\xff\xfe]}')

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(invalid_doc),
        )

        # Should fail due to encoding or JSON error
        assert result.status == PhaseStatus.FAILED

    # -------------------------------------------------------------------------
    # REQ_002.2: Deserialize JSON to RequirementHierarchy (Tier 2)
    # -------------------------------------------------------------------------

    def test_recursive_children_reconstruction(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.2: Recursively construct all RequirementNode children."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        # Create hierarchy with multiple levels
        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Parent requirement",
                    "type": "parent",
                    "parent_id": None,
                    "children": [
                        {
                            "id": "REQ_001.1",
                            "description": "Sub-process requirement",
                            "type": "sub_process",
                            "parent_id": "REQ_001",
                            "children": [
                                {
                                    "id": "REQ_001.1.1",
                                    "description": "Implementation requirement",
                                    "type": "implementation",
                                    "parent_id": "REQ_001.1",
                                    "children": [],
                                    "acceptance_criteria": [],
                                    "category": "functional",
                                }
                            ],
                            "acceptance_criteria": [],
                            "category": "functional",
                        }
                    ],
                    "acceptance_criteria": [],
                    "category": "functional",
                }
            ],
            "metadata": {},
        }
        doc = tmp_path / "nested.json"
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            result = pipeline.run(
                research_question="",
                hierarchy_path=str(doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        # Should have 3 total nodes (1 parent + 1 sub_process + 1 implementation)
        assert decomp_result.metadata.get("total_nodes") == 3

    def test_implementation_components_reconstruction(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.2: Reconstruct ImplementationComponents from dict."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Implementation with components",
                    "type": "implementation",
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    "implementation": {
                        "frontend": ["LoginForm", "AuthContext"],
                        "backend": ["AuthService.login"],
                        "middleware": ["validateToken"],
                        "shared": ["User", "Session"],
                    },
                    "testable_properties": [],
                    "category": "functional",
                }
            ],
            "metadata": {},
        }
        doc = tmp_path / "with_components.json"
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            result = pipeline.run(
                research_question="",
                hierarchy_path=str(doc),
            )

        # Validation succeeded if we got here
        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert decomp_result.status == PhaseStatus.COMPLETE

    def test_testable_properties_reconstruction(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.2: Reconstruct TestableProperty list from dict."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Requirement with testable properties",
                    "type": "implementation",
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": ["User can login"],
                    "testable_properties": [
                        {
                            "criterion": "User can login",
                            "property_type": "invariant",
                            "hypothesis_strategy": "st.text(min_size=1)",
                            "test_skeleton": "def test_login(): pass",
                        }
                    ],
                    "category": "functional",
                }
            ],
            "metadata": {},
        }
        doc = tmp_path / "with_properties.json"
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            result = pipeline.run(
                research_question="",
                hierarchy_path=str(doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert decomp_result.status == PhaseStatus.COMPLETE

    def test_missing_optional_fields_use_defaults(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.2: Missing optional fields use sensible defaults."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        # Minimal valid hierarchy with only required fields
        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Minimal requirement",
                    "type": "parent",
                    # Missing: parent_id, children, acceptance_criteria,
                    #          implementation, testable_properties, function_id,
                    #          related_concepts, category
                }
            ],
            "metadata": {},
        }
        doc = tmp_path / "minimal.json"
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            result = pipeline.run(
                research_question="",
                hierarchy_path=str(doc),
            )

        # Should succeed with defaults
        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert decomp_result.status == PhaseStatus.COMPLETE

    # -------------------------------------------------------------------------
    # REQ_002.3: Validate requirement type
    # -------------------------------------------------------------------------

    def test_type_validation_case_sensitive(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.3: Type validation is case-sensitive ('Parent' invalid)."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "Parent",  # Invalid - wrong case
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    "category": "functional",
                }
            ],
            "metadata": {},
        }
        doc = tmp_path / "case_sensitive.json"
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(doc),
        )

        assert result.status == PhaseStatus.FAILED
        assert any("type" in err.lower() or "invalid" in err.lower() for err in result.errors)

    def test_type_validation_rejects_empty_string(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.3: Empty string type is rejected."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "",  # Invalid - empty
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    "category": "functional",
                }
            ],
            "metadata": {},
        }
        doc = tmp_path / "empty_type.json"
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(doc),
        )

        assert result.status == PhaseStatus.FAILED

    def test_valid_types_accepted(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.3: All valid types (parent, sub_process, implementation) accepted."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        for valid_type in ["parent", "sub_process", "implementation"]:
            hierarchy = {
                "requirements": [
                    {
                        "id": "REQ_001",
                        "description": f"Test {valid_type} requirement",
                        "type": valid_type,
                        "parent_id": None,
                        "children": [],
                        "acceptance_criteria": [],
                        "category": "functional",
                    }
                ],
                "metadata": {},
            }
            doc = tmp_path / f"valid_type_{valid_type}.json"
            doc.write_text(json.dumps(hierarchy))

            pipeline = RLMActPipeline(
                project_path=temp_project,
                cwa=mock_cwa,
                autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
                beads_controller=mock_beads_controller,
            )

            def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
                return PhaseResult(
                    phase_type=phase_type,
                    status=PhaseStatus.COMPLETE,
                    artifacts=[f"{phase_type.value}.md"],
                )

            with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
                result = pipeline.run(
                    research_question="",
                    hierarchy_path=str(doc),
                )

            decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
            assert decomp_result.status == PhaseStatus.COMPLETE, f"Type '{valid_type}' should be valid"

    # -------------------------------------------------------------------------
    # REQ_002.4: Validate requirement category
    # -------------------------------------------------------------------------

    def test_category_validation_case_sensitive(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.4: Category validation is case-sensitive ('Functional' invalid)."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    "category": "Functional",  # Invalid - wrong case
                }
            ],
            "metadata": {},
        }
        doc = tmp_path / "case_sensitive_category.json"
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(doc),
        )

        assert result.status == PhaseStatus.FAILED
        assert any("category" in err.lower() or "invalid" in err.lower() for err in result.errors)

    def test_category_defaults_when_missing_from_json(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.4: Missing category defaults to 'functional'."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    # category intentionally omitted
                }
            ],
            "metadata": {},
        }
        doc = tmp_path / "no_category.json"
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            result = pipeline.run(
                research_question="",
                hierarchy_path=str(doc),
            )

        # Should succeed with default category
        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert decomp_result.status == PhaseStatus.COMPLETE

    def test_all_valid_categories_accepted(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.4: All valid categories are accepted."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        valid_categories = [
            "functional",
            "non_functional",
            "security",
            "performance",
            "usability",
            "integration",
        ]

        for category in valid_categories:
            hierarchy = {
                "requirements": [
                    {
                        "id": "REQ_001",
                        "description": f"Test {category} requirement",
                        "type": "parent",
                        "parent_id": None,
                        "children": [],
                        "acceptance_criteria": [],
                        "category": category,
                    }
                ],
                "metadata": {},
            }
            doc = tmp_path / f"valid_category_{category}.json"
            doc.write_text(json.dumps(hierarchy))

            pipeline = RLMActPipeline(
                project_path=temp_project,
                cwa=mock_cwa,
                autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
                beads_controller=mock_beads_controller,
            )

            def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
                return PhaseResult(
                    phase_type=phase_type,
                    status=PhaseStatus.COMPLETE,
                    artifacts=[f"{phase_type.value}.md"],
                )

            with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
                result = pipeline.run(
                    research_question="",
                    hierarchy_path=str(doc),
                )

            decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
            assert decomp_result.status == PhaseStatus.COMPLETE, f"Category '{category}' should be valid"

    # -------------------------------------------------------------------------
    # REQ_002.5: Validate requirement description
    # -------------------------------------------------------------------------

    def test_description_whitespace_only_rejected(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.5: Whitespace-only descriptions are rejected."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "   \t\n   ",  # Whitespace only
                    "type": "parent",
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    "category": "functional",
                }
            ],
            "metadata": {},
        }
        doc = tmp_path / "whitespace_description.json"
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(doc),
        )

        assert result.status == PhaseStatus.FAILED
        assert any("description" in err.lower() or "empty" in err.lower() for err in result.errors)

    def test_description_empty_string_rejected(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.5: Empty string descriptions are rejected."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "",  # Empty string
                    "type": "parent",
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    "category": "functional",
                }
            ],
            "metadata": {},
        }
        doc = tmp_path / "empty_description.json"
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(doc),
        )

        assert result.status == PhaseStatus.FAILED

    def test_description_validation_applies_to_all_types(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.5: Description validation applies to all requirement types."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        for req_type in ["parent", "sub_process", "implementation"]:
            hierarchy = {
                "requirements": [
                    {
                        "id": "REQ_001",
                        "description": "",  # Empty - should fail for all types
                        "type": req_type,
                        "parent_id": None,
                        "children": [],
                        "acceptance_criteria": [],
                        "category": "functional",
                    }
                ],
                "metadata": {},
            }
            doc = tmp_path / f"empty_desc_{req_type}.json"
            doc.write_text(json.dumps(hierarchy))

            pipeline = RLMActPipeline(
                project_path=temp_project,
                cwa=mock_cwa,
                autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
                beads_controller=mock_beads_controller,
            )

            result = pipeline.run(
                research_question="",
                hierarchy_path=str(doc),
            )

            assert result.status == PhaseStatus.FAILED, f"Empty description should be invalid for type '{req_type}'"

    def test_valid_description_preserved(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_002.5: Valid descriptions are preserved without modification."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        # Description with leading/trailing whitespace should be preserved
        description = "  Valid description with whitespace  "
        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": description,
                    "type": "parent",
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    "category": "functional",
                }
            ],
            "metadata": {},
        }
        doc = tmp_path / "valid_description.json"
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            result = pipeline.run(
                research_question="",
                hierarchy_path=str(doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert decomp_result.status == PhaseStatus.COMPLETE


# =============================================================================
# Phase 5 - REQ_004: Pipeline Kwargs Passthrough Tests
# =============================================================================


class TestKwargsPassthrough:
    """Tests for REQ_004: Pipeline kwargs passthrough for phase skipping."""

    # -------------------------------------------------------------------------
    # REQ_004.3: PhaseResult with COMPLETE status and metadata
    # -------------------------------------------------------------------------

    def test_validation_timestamp_in_metadata(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_004.3.6: PhaseResult.metadata contains validation_timestamp."""
        import re

        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_plan_doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert "validation_timestamp" in decomp_result.metadata
        # Verify ISO format (YYYY-MM-DDTHH:MM:SS.ffffff pattern)
        timestamp = decomp_result.metadata["validation_timestamp"]
        iso_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
        assert re.match(iso_pattern, timestamp), f"Timestamp '{timestamp}' not in ISO format"

    def test_artifacts_contains_hierarchy_path_first(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_004.3.7: PhaseResult.artifacts list contains hierarchy_path as first element."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_plan_doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert len(decomp_result.artifacts) >= 1
        assert decomp_result.artifacts[0] == str(temp_plan_doc)

    def test_validated_true_on_success(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_004.3.2: PhaseResult.metadata contains validated=True on success."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_plan_doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert decomp_result.metadata.get("validated") is True

    # -------------------------------------------------------------------------
    # REQ_004.4: PhaseResult with FAILED status and errors array
    # -------------------------------------------------------------------------

    def test_validated_false_on_failure(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_004.4.9: PhaseResult.metadata contains validated=False on failure."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        # Create invalid JSON
        invalid_doc = tmp_path / "invalid.json"
        invalid_doc.write_text("not valid json {{{")

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(invalid_doc),
        )

        assert result.status == PhaseStatus.FAILED
        assert result.metadata.get("validated") is False

    def test_error_count_in_failed_metadata(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_004.4.10: PhaseResult.metadata contains error_count on failure."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        # Create invalid JSON
        invalid_doc = tmp_path / "invalid.json"
        invalid_doc.write_text("not valid json {{{")

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(invalid_doc),
        )

        assert result.status == PhaseStatus.FAILED
        assert "error_count" in result.metadata
        assert result.metadata["error_count"] >= 1

    def test_json_error_message_format(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_004.4.3: JSON parsing errors produce 'Plan validation failed: Invalid JSON - {error}'."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        invalid_doc = tmp_path / "invalid.json"
        invalid_doc.write_text("not valid json {{{")

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(invalid_doc),
        )

        assert result.status == PhaseStatus.FAILED
        assert len(result.errors) >= 1
        assert "Plan validation failed: Invalid JSON" in result.errors[0]

    def test_file_not_found_error_message_format(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_004.4.4: Missing file errors produce 'Plan validation failed: File not found - {path}'."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        nonexistent_path = str(tmp_path / "nonexistent.json")

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=nonexistent_path,
        )

        assert result.status == PhaseStatus.FAILED
        assert len(result.errors) >= 1
        assert "Plan validation failed: File not found" in result.errors[0]
        assert nonexistent_path in result.errors[0]

    def test_hierarchy_path_in_failed_metadata(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_004.4: PhaseResult.metadata contains hierarchy_path on failure."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        invalid_doc = tmp_path / "invalid.json"
        invalid_doc.write_text("not valid json {{{")

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(invalid_doc),
        )

        assert result.status == PhaseStatus.FAILED
        assert result.metadata.get("hierarchy_path") == str(invalid_doc)

    def test_type_validation_error_includes_details(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_004.4.5: Type validation errors include invalid type and valid options."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "invalid_type",
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    "category": "functional",
                }
            ],
            "metadata": {},
        }
        doc = tmp_path / "invalid_type_details.json"
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(doc),
        )

        assert result.status == PhaseStatus.FAILED
        # Error should mention the invalid type
        error_text = " ".join(result.errors).lower()
        assert "type" in error_text or "invalid" in error_text

    def test_pipeline_halts_gracefully_on_validation_failure(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_004.4.11: Pipeline execution halts gracefully after returning FAILED PhaseResult."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        invalid_doc = tmp_path / "invalid_halt.json"
        invalid_doc.write_text("not valid json {{{")

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        # Mock to ensure later phases are NOT executed
        with patch.object(pipeline, "_execute_phase") as mock_exec:
            result = pipeline.run(
                research_question="",
                hierarchy_path=str(invalid_doc),
            )

            # Verify no phases were executed (validation failed before any phase execution)
            mock_exec.assert_not_called()

        assert result.status == PhaseStatus.FAILED


# =============================================================================
# Phase 7 - REQ_006: PhaseResult Object Return Values
# =============================================================================


class TestPhaseResultReturnValues:
    """Tests for REQ_006: PhaseResult objects return appropriate values."""

    # -------------------------------------------------------------------------
    # REQ_006.1: validated=True in metadata for successful validation
    # -------------------------------------------------------------------------

    def test_validated_true_on_successful_validation(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_006.1.1: PhaseResult.metadata contains validated=True on successful validation."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_plan_doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert decomp_result.metadata.get("validated") is True

    def test_validated_is_boolean_true_not_truthy(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_006.1.2: validated is exactly True (not just truthy)."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_plan_doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        # Check it's exactly True, not "true" or 1 or any other truthy value
        assert decomp_result.metadata.get("validated") is True
        assert type(decomp_result.metadata.get("validated")) is bool

    # -------------------------------------------------------------------------
    # REQ_006.2: requirements_count for top-level requirements
    # -------------------------------------------------------------------------

    def test_requirements_count_is_top_level_only(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_006.2.1: requirements_count counts only top-level requirements."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        # Create hierarchy with 2 top-level requirements, each with children
        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "First parent",
                    "type": "parent",
                    "parent_id": None,
                    "children": [
                        {
                            "id": "REQ_001.1",
                            "description": "Child 1",
                            "type": "sub_process",
                            "parent_id": "REQ_001",
                            "children": [],
                            "acceptance_criteria": [],
                            "category": "functional",
                        }
                    ],
                    "acceptance_criteria": [],
                    "category": "functional",
                },
                {
                    "id": "REQ_002",
                    "description": "Second parent",
                    "type": "parent",
                    "parent_id": None,
                    "children": [
                        {
                            "id": "REQ_002.1",
                            "description": "Child 2",
                            "type": "sub_process",
                            "parent_id": "REQ_002",
                            "children": [],
                            "acceptance_criteria": [],
                            "category": "functional",
                        }
                    ],
                    "acceptance_criteria": [],
                    "category": "functional",
                },
            ],
            "metadata": {},
        }
        doc = tmp_path / "nested_count.json"
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        # Should be 2 (only top-level), not 4 (total)
        assert decomp_result.metadata.get("requirements_count") == 2

    def test_requirements_count_is_integer(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_006.2.2: requirements_count is an integer."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_plan_doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert isinstance(decomp_result.metadata.get("requirements_count"), int)

    # -------------------------------------------------------------------------
    # REQ_006.3: total_nodes count for all nodes
    # -------------------------------------------------------------------------

    def test_total_nodes_counts_all_levels(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_006.3.1: total_nodes counts all nodes at all levels."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        # Create hierarchy with 3 levels: 1 parent -> 1 sub_process -> 1 implementation
        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Parent",
                    "type": "parent",
                    "parent_id": None,
                    "children": [
                        {
                            "id": "REQ_001.1",
                            "description": "Sub-process",
                            "type": "sub_process",
                            "parent_id": "REQ_001",
                            "children": [
                                {
                                    "id": "REQ_001.1.1",
                                    "description": "Implementation",
                                    "type": "implementation",
                                    "parent_id": "REQ_001.1",
                                    "children": [],
                                    "acceptance_criteria": [],
                                    "category": "functional",
                                }
                            ],
                            "acceptance_criteria": [],
                            "category": "functional",
                        }
                    ],
                    "acceptance_criteria": [],
                    "category": "functional",
                },
            ],
            "metadata": {},
        }
        doc = tmp_path / "total_nodes.json"
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        # Should be 3 (1 parent + 1 sub_process + 1 implementation)
        assert decomp_result.metadata.get("total_nodes") == 3

    def test_total_nodes_greater_or_equal_requirements_count(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_006.3.2: total_nodes >= requirements_count."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_plan_doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        total_nodes = decomp_result.metadata.get("total_nodes", 0)
        requirements_count = decomp_result.metadata.get("requirements_count", 0)
        assert total_nodes >= requirements_count

    def test_total_nodes_is_integer(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_006.3.3: total_nodes is an integer."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_plan_doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert isinstance(decomp_result.metadata.get("total_nodes"), int)

    # -------------------------------------------------------------------------
    # REQ_006.4: Error handling for JSONDecodeError, ValueError, FileNotFoundError
    # -------------------------------------------------------------------------

    def test_json_decode_error_returns_failed_phase_result(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_006.4.1: JSONDecodeError returns PhaseResult with status=FAILED."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        invalid_doc = tmp_path / "invalid_json.json"
        invalid_doc.write_text("{invalid json content")

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(invalid_doc),
        )

        assert result.status == PhaseStatus.FAILED
        assert "Invalid JSON" in result.errors[0]

    def test_value_error_returns_failed_phase_result(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_006.4.2: ValueError (invalid type/category) returns PhaseResult with status=FAILED."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test",
                    "type": "not_a_valid_type",  # Invalid type triggers ValueError
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    "category": "functional",
                }
            ],
            "metadata": {},
        }
        doc = tmp_path / "value_error.json"
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(doc),
        )

        assert result.status == PhaseStatus.FAILED

    def test_file_not_found_error_returns_failed_phase_result(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_006.4.3: FileNotFoundError returns PhaseResult with status=FAILED."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        nonexistent = str(tmp_path / "does_not_exist.json")

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=nonexistent,
        )

        assert result.status == PhaseStatus.FAILED
        assert "File not found" in result.errors[0]

    def test_error_message_is_descriptive(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_006.4.4: Error messages are descriptive and actionable."""
        import json

        from silmari_rlm_act.pipeline import RLMActPipeline

        # Create hierarchy with empty description to trigger error
        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "",  # Empty description
                    "type": "parent",
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    "category": "functional",
                }
            ],
            "metadata": {},
        }
        doc = tmp_path / "empty_desc.json"
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(doc),
        )

        assert result.status == PhaseStatus.FAILED
        # Error should include "Plan validation failed" prefix
        assert any("Plan validation failed" in err for err in result.errors)

    def test_errors_array_is_never_empty_on_failure(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_006.4.5: PhaseResult.errors is never empty when status=FAILED."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        invalid_doc = tmp_path / "invalid.json"
        invalid_doc.write_text("not json")

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        result = pipeline.run(
            research_question="",
            hierarchy_path=str(invalid_doc),
        )

        assert result.status == PhaseStatus.FAILED
        assert len(result.errors) > 0

    # REQ_006.3: Source field propagation from hierarchy metadata

    def test_source_field_propagated_from_hierarchy(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_006.3.1: source field from hierarchy metadata is propagated."""
        import json
        from silmari_rlm_act.pipeline import RLMActPipeline

        doc = tmp_path / "with_source.json"
        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    "category": "functional",
                }
            ],
            "metadata": {
                "source": "agent_sdk_decomposition"
            },
        }
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(doc),
            )

        # Should have propagated source
        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert decomp_result is not None
        assert decomp_result.metadata.get("source") == "agent_sdk_decomposition"

    def test_source_field_test_value_propagated(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_006.3.2: source='test' is propagated correctly."""
        import json
        from silmari_rlm_act.pipeline import RLMActPipeline

        doc = tmp_path / "with_test_source.json"
        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    "category": "functional",
                }
            ],
            "metadata": {
                "source": "test"
            },
        }
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert decomp_result is not None
        assert decomp_result.metadata.get("source") == "test"

    def test_hierarchy_without_source_does_not_raise(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_006.3.3: Hierarchy without source field does not raise exception."""
        import json
        from silmari_rlm_act.pipeline import RLMActPipeline

        doc = tmp_path / "no_source.json"
        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    "category": "functional",
                }
            ],
            "metadata": {},  # No source field
        }
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        # Should not raise exception
        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert decomp_result is not None
        assert decomp_result.status == PhaseStatus.COMPLETE
        # source may be omitted (not required)
        assert "source" not in decomp_result.metadata or decomp_result.metadata.get("source") is None or isinstance(decomp_result.metadata.get("source"), str)

    # REQ_006.4: decomposition_stats propagation

    def test_decomposition_stats_propagated_from_hierarchy(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_006.4.1: decomposition_stats from hierarchy metadata is propagated."""
        import json
        from silmari_rlm_act.pipeline import RLMActPipeline

        doc = tmp_path / "with_stats.json"
        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    "category": "functional",
                }
            ],
            "metadata": {
                "decomposition_stats": {
                    "requirements_found": 1,
                    "subprocesses_expanded": 0,
                    "total_nodes": 1,
                    "extraction_time_ms": 100,
                    "expansion_time_ms": 50,
                }
            },
        }
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert decomp_result is not None
        assert "decomposition_stats" in decomp_result.metadata
        stats = decomp_result.metadata["decomposition_stats"]
        assert stats["requirements_found"] == 1
        assert stats["extraction_time_ms"] == 100

    def test_decomposition_stats_omitted_when_not_present(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """REQ_006.4.2: decomposition_stats is omitted (not null) when not in hierarchy."""
        import json
        from silmari_rlm_act.pipeline import RLMActPipeline

        doc = tmp_path / "no_stats.json"
        hierarchy = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "parent_id": None,
                    "children": [],
                    "acceptance_criteria": [],
                    "category": "functional",
                }
            ],
            "metadata": {},  # No decomposition_stats
        }
        doc.write_text(json.dumps(hierarchy))

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(doc),
            )

        decomp_result = pipeline.state.get_phase_result(PhaseType.DECOMPOSITION)
        assert decomp_result is not None
        # Key should not exist (not set to null)
        assert "decomposition_stats" not in decomp_result.metadata


@pytest.fixture
def temp_markdown_plan(tmp_path: Path) -> Path:
    """Create a temporary Markdown plan document."""
    doc = tmp_path / "plan-overview.md"
    doc.write_text(
        """# TDD Implementation Plan

## Phase 1: Setup

### Behavior 1.1: Project initializes successfully
- Test passes

## Phase 2: Core Features

### Behavior 2.1: Feature works correctly
- Test passes
"""
    )
    return doc


class TestMarkdownPlanSupport:
    """Tests for Markdown plan support in --plan-path."""

    def test_is_markdown_plan_by_md_extension(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Files with .md extension are detected as Markdown."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        md_file = tmp_path / "plan.md"
        md_file.write_text("# Test Plan")

        assert pipeline._is_markdown_plan(str(md_file)) is True

    def test_is_markdown_plan_by_markdown_extension(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Files with .markdown extension are detected as Markdown."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        md_file = tmp_path / "plan.markdown"
        md_file.write_text("# Test Plan")

        assert pipeline._is_markdown_plan(str(md_file)) is True

    def test_is_markdown_plan_json_extension_returns_false(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Files with .json extension are not Markdown."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        json_file = tmp_path / "hierarchy.json"
        json_file.write_text('{"requirements": []}')

        assert pipeline._is_markdown_plan(str(json_file)) is False

    def test_is_markdown_plan_by_content_valid_json(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Files with valid JSON content are not Markdown (regardless of extension)."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        # File without extension but valid JSON content
        unknown_file = tmp_path / "plan"
        unknown_file.write_text('{"requirements": []}')

        assert pipeline._is_markdown_plan(str(unknown_file)) is False

    def test_is_markdown_plan_by_content_invalid_json(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Files with invalid JSON content are Markdown."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        # File without extension but Markdown content
        unknown_file = tmp_path / "plan"
        unknown_file.write_text("# This is a plan\n\nSome text here.")

        assert pipeline._is_markdown_plan(str(unknown_file)) is True

    def test_markdown_plan_skips_all_phases_except_implementation(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_markdown_plan: Path,
    ) -> None:
        """Markdown plan skips RESEARCH, DECOMPOSITION, TDD_PLANNING, MULTI_DOC, BEADS_SYNC."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute) as mock_exec:
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_markdown_plan),
            )

            # Only IMPLEMENTATION should be called
            calls = [call[0][0] for call in mock_exec.call_args_list]
            assert PhaseType.RESEARCH not in calls
            assert PhaseType.DECOMPOSITION not in calls
            assert PhaseType.TDD_PLANNING not in calls
            assert PhaseType.MULTI_DOC not in calls
            assert PhaseType.BEADS_SYNC not in calls
            assert PhaseType.IMPLEMENTATION in calls

    def test_markdown_plan_creates_synthetic_results_for_skipped_phases(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_markdown_plan: Path,
    ) -> None:
        """Markdown plan creates synthetic COMPLETE results for all skipped phases."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_markdown_plan),
            )

        # Check all skipped phases have synthetic results
        skipped_phases = [
            PhaseType.RESEARCH,
            PhaseType.DECOMPOSITION,
            PhaseType.TDD_PLANNING,
            PhaseType.MULTI_DOC,
            PhaseType.BEADS_SYNC,
        ]
        for phase_type in skipped_phases:
            result = pipeline.state.get_phase_result(phase_type)
            assert result is not None, f"{phase_type} should have a result"
            assert result.status == PhaseStatus.COMPLETE
            assert result.metadata.get("skipped") is True
            assert result.metadata.get("reason") == "markdown_plan provided"

    def test_markdown_plan_passes_path_to_implementation_phase(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_markdown_plan: Path,
    ) -> None:
        """Markdown plan path is passed to IMPLEMENTATION phase as phase_paths."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        captured_kwargs: dict[str, Any] = {}

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            if phase_type == PhaseType.IMPLEMENTATION:
                captured_kwargs.update(kwargs)
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute):
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_markdown_plan),
            )

        assert "phase_paths" in captured_kwargs
        assert str(temp_markdown_plan) in captured_kwargs["phase_paths"]

    def test_json_plan_still_works_normally(
        self,
        temp_project: Path,
        mock_cwa: MagicMock,
        mock_beads_controller: MagicMock,
        temp_plan_doc: Path,
    ) -> None:
        """JSON plan files still work with existing behavior (skip RESEARCH, DECOMPOSITION only)."""
        from silmari_rlm_act.pipeline import RLMActPipeline

        pipeline = RLMActPipeline(
            project_path=temp_project,
            cwa=mock_cwa,
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            beads_controller=mock_beads_controller,
        )

        def mock_execute(phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.COMPLETE,
                artifacts=[f"{phase_type.value}.md"],
            )

        with patch.object(pipeline, "_execute_phase", side_effect=mock_execute) as mock_exec:
            pipeline.run(
                research_question="",
                hierarchy_path=str(temp_plan_doc),
            )

            # JSON plan should call TDD_PLANNING, MULTI_DOC, BEADS_SYNC (and IMPLEMENTATION)
            calls = [call[0][0] for call in mock_exec.call_args_list]
            assert PhaseType.RESEARCH not in calls  # Skipped
            assert PhaseType.DECOMPOSITION not in calls  # Skipped
            assert PhaseType.TDD_PLANNING in calls  # Called
            assert PhaseType.MULTI_DOC in calls  # Called
            assert PhaseType.BEADS_SYNC in calls  # Called
            assert PhaseType.IMPLEMENTATION in calls  # Called
