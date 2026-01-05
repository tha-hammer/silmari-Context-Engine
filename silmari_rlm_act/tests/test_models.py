"""Tests for core models: PhaseResult, PipelineState, AutonomyMode, PhaseType.

Phase 01 of TDD implementation for silmari-rlm-act pipeline.
"""

import json

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from silmari_rlm_act.models import (
    AutonomyMode,
    PhaseResult,
    PhaseStatus,
    PhaseType,
    PipelineState,
)


class TestAutonomyMode:
    """Tests for AutonomyMode enum."""

    def test_has_checkpoint_mode(self):
        """Checkpoint mode pauses at each phase."""
        assert AutonomyMode.CHECKPOINT.value == "checkpoint"

    def test_has_fully_autonomous_mode(self):
        """Fully autonomous mode runs all phases without stopping."""
        assert AutonomyMode.FULLY_AUTONOMOUS.value == "fully_autonomous"

    def test_has_batch_mode(self):
        """Batch mode groups phases and pauses between groups."""
        assert AutonomyMode.BATCH.value == "batch"

    def test_from_string_valid(self):
        """Convert valid string to AutonomyMode."""
        assert AutonomyMode.from_string("checkpoint") == AutonomyMode.CHECKPOINT
        assert AutonomyMode.from_string("fully_autonomous") == AutonomyMode.FULLY_AUTONOMOUS
        assert AutonomyMode.from_string("batch") == AutonomyMode.BATCH

    def test_from_string_invalid(self):
        """Invalid string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid autonomy mode"):
            AutonomyMode.from_string("invalid_mode")

    def test_str_representation(self):
        """String representation returns the value."""
        assert str(AutonomyMode.CHECKPOINT) == "checkpoint"
        assert str(AutonomyMode.FULLY_AUTONOMOUS) == "fully_autonomous"


class TestPhaseType:
    """Tests for PhaseType enum."""

    def test_has_research_phase(self):
        """Research phase gathers context about the task."""
        assert PhaseType.RESEARCH.value == "research"

    def test_has_decomposition_phase(self):
        """Decomposition phase breaks into testable behaviors."""
        assert PhaseType.DECOMPOSITION.value == "decomposition"

    def test_has_tdd_planning_phase(self):
        """TDD planning creates Red-Green-Refactor plans."""
        assert PhaseType.TDD_PLANNING.value == "tdd_planning"

    def test_has_multi_doc_phase(self):
        """Multi-doc phase splits plan into phase documents."""
        assert PhaseType.MULTI_DOC.value == "multi_doc"

    def test_has_beads_sync_phase(self):
        """Beads sync tracks epochs and tasks."""
        assert PhaseType.BEADS_SYNC.value == "beads_sync"

    def test_has_implementation_phase(self):
        """Implementation phase executes TDD cycles."""
        assert PhaseType.IMPLEMENTATION.value == "implementation"

    def test_from_string_valid(self):
        """Convert valid string to PhaseType."""
        assert PhaseType.from_string("research") == PhaseType.RESEARCH
        assert PhaseType.from_string("decomposition") == PhaseType.DECOMPOSITION
        assert PhaseType.from_string("implementation") == PhaseType.IMPLEMENTATION

    def test_from_string_invalid(self):
        """Invalid string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid phase type"):
            PhaseType.from_string("invalid_phase")

    def test_str_representation(self):
        """String representation returns the value."""
        assert str(PhaseType.RESEARCH) == "research"


class TestPhaseStatus:
    """Tests for PhaseStatus enum."""

    def test_has_pending_status(self):
        """Pending status for phases not yet started."""
        assert PhaseStatus.PENDING.value == "pending"

    def test_has_in_progress_status(self):
        """In progress status for phases currently running."""
        assert PhaseStatus.IN_PROGRESS.value == "in_progress"

    def test_has_complete_status(self):
        """Complete status for successfully finished phases."""
        assert PhaseStatus.COMPLETE.value == "complete"

    def test_has_failed_status(self):
        """Failed status for phases that encountered errors."""
        assert PhaseStatus.FAILED.value == "failed"

    def test_from_string_valid(self):
        """Convert valid string to PhaseStatus."""
        assert PhaseStatus.from_string("pending") == PhaseStatus.PENDING
        assert PhaseStatus.from_string("complete") == PhaseStatus.COMPLETE

    def test_from_string_invalid(self):
        """Invalid string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid phase status"):
            PhaseStatus.from_string("unknown")


class TestPhaseResult:
    """Tests for PhaseResult dataclass."""

    def test_creation_minimal(self):
        """Create PhaseResult with required fields only."""
        result = PhaseResult(
            phase_type=PhaseType.RESEARCH,
            status=PhaseStatus.COMPLETE,
        )
        assert result.phase_type == PhaseType.RESEARCH
        assert result.status == PhaseStatus.COMPLETE
        assert result.artifacts == []
        assert result.errors == []
        assert result.duration_seconds is None

    def test_creation_with_all_fields(self, sample_timestamp, sample_artifacts, sample_errors):
        """Create PhaseResult with all fields populated."""
        result = PhaseResult(
            phase_type=PhaseType.RESEARCH,
            status=PhaseStatus.FAILED,
            artifacts=sample_artifacts,
            errors=sample_errors,
            started_at=sample_timestamp,
            completed_at=sample_timestamp,
            duration_seconds=120.5,
            metadata={"key": "value"},
        )
        assert result.artifacts == sample_artifacts
        assert result.errors == sample_errors
        assert result.started_at == sample_timestamp
        assert result.duration_seconds == 120.5
        assert result.metadata == {"key": "value"}

    def test_to_dict_serialization(self, sample_timestamp):
        """Serialize PhaseResult to dictionary."""
        result = PhaseResult(
            phase_type=PhaseType.DECOMPOSITION,
            status=PhaseStatus.COMPLETE,
            artifacts=["/path/to/file.md"],
            started_at=sample_timestamp,
            completed_at=sample_timestamp,
            duration_seconds=45.0,
        )
        data = result.to_dict()
        assert data["phase_type"] == "decomposition"
        assert data["status"] == "complete"
        assert data["artifacts"] == ["/path/to/file.md"]
        assert data["started_at"] == sample_timestamp.isoformat()
        assert data["duration_seconds"] == 45.0

    def test_from_dict_deserialization(self, sample_timestamp):
        """Deserialize PhaseResult from dictionary."""
        data = {
            "phase_type": "tdd_planning",
            "status": "in_progress",
            "artifacts": [],
            "errors": ["Error 1"],
            "started_at": sample_timestamp.isoformat(),
            "completed_at": None,
            "duration_seconds": None,
            "metadata": {},
        }
        result = PhaseResult.from_dict(data)
        assert result.phase_type == PhaseType.TDD_PLANNING
        assert result.status == PhaseStatus.IN_PROGRESS
        assert result.errors == ["Error 1"]
        assert result.started_at == sample_timestamp

    def test_round_trip_serialization(self, sample_timestamp, sample_artifacts):
        """Serialize and deserialize preserves all data."""
        original = PhaseResult(
            phase_type=PhaseType.IMPLEMENTATION,
            status=PhaseStatus.COMPLETE,
            artifacts=sample_artifacts,
            errors=[],
            started_at=sample_timestamp,
            completed_at=sample_timestamp,
            duration_seconds=300.0,
            metadata={"beads_id": "beads-123"},
        )
        data = original.to_dict()
        restored = PhaseResult.from_dict(data)
        assert restored.phase_type == original.phase_type
        assert restored.status == original.status
        assert restored.artifacts == original.artifacts
        assert restored.metadata == original.metadata

    def test_is_complete_property(self):
        """is_complete returns True only for COMPLETE status."""
        complete = PhaseResult(PhaseType.RESEARCH, PhaseStatus.COMPLETE)
        failed = PhaseResult(PhaseType.RESEARCH, PhaseStatus.FAILED)
        pending = PhaseResult(PhaseType.RESEARCH, PhaseStatus.PENDING)

        assert complete.is_complete is True
        assert failed.is_complete is False
        assert pending.is_complete is False

    def test_is_failed_property(self):
        """is_failed returns True only for FAILED status."""
        failed = PhaseResult(PhaseType.RESEARCH, PhaseStatus.FAILED)
        complete = PhaseResult(PhaseType.RESEARCH, PhaseStatus.COMPLETE)

        assert failed.is_failed is True
        assert complete.is_failed is False


class TestPipelineState:
    """Tests for PipelineState dataclass."""

    def test_creation_minimal(self):
        """Create PipelineState with required fields only."""
        state = PipelineState(
            project_path="/home/user/project",
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )
        assert state.project_path == "/home/user/project"
        assert state.autonomy_mode == AutonomyMode.CHECKPOINT
        assert state.current_phase is None
        assert state.phase_results == {}
        assert state.checkpoint_id is None

    def test_creation_with_all_fields(self, sample_timestamp):
        """Create PipelineState with all fields populated."""
        research_result = PhaseResult(PhaseType.RESEARCH, PhaseStatus.COMPLETE)
        state = PipelineState(
            project_path="/home/user/project",
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            current_phase=PhaseType.DECOMPOSITION,
            phase_results={PhaseType.RESEARCH: research_result},
            started_at=sample_timestamp,
            checkpoint_id="checkpoint-abc123",
            beads_epic_id="beads-xyz789",
            metadata={"user": "maceo"},
        )
        assert state.current_phase == PhaseType.DECOMPOSITION
        assert PhaseType.RESEARCH in state.phase_results
        assert state.beads_epic_id == "beads-xyz789"

    def test_to_dict_serialization(self, sample_timestamp):
        """Serialize PipelineState to dictionary."""
        result = PhaseResult(PhaseType.RESEARCH, PhaseStatus.COMPLETE)
        state = PipelineState(
            project_path="/home/user/project",
            autonomy_mode=AutonomyMode.BATCH,
            current_phase=PhaseType.RESEARCH,
            phase_results={PhaseType.RESEARCH: result},
            started_at=sample_timestamp,
        )
        data = state.to_dict()
        assert data["project_path"] == "/home/user/project"
        assert data["autonomy_mode"] == "batch"
        assert data["current_phase"] == "research"
        assert "research" in data["phase_results"]

    def test_from_dict_deserialization(self, sample_timestamp):
        """Deserialize PipelineState from dictionary."""
        data = {
            "project_path": "/home/user/project",
            "autonomy_mode": "checkpoint",
            "current_phase": "tdd_planning",
            "phase_results": {
                "research": {
                    "phase_type": "research",
                    "status": "complete",
                    "artifacts": [],
                    "errors": [],
                    "started_at": None,
                    "completed_at": None,
                    "duration_seconds": None,
                    "metadata": {},
                }
            },
            "started_at": sample_timestamp.isoformat(),
            "checkpoint_id": None,
            "beads_epic_id": None,
            "metadata": {},
        }
        state = PipelineState.from_dict(data)
        assert state.autonomy_mode == AutonomyMode.CHECKPOINT
        assert state.current_phase == PhaseType.TDD_PLANNING
        assert PhaseType.RESEARCH in state.phase_results

    def test_round_trip_serialization(self, sample_timestamp):
        """Serialize and deserialize preserves all data."""
        result = PhaseResult(PhaseType.DECOMPOSITION, PhaseStatus.IN_PROGRESS)
        original = PipelineState(
            project_path="/project",
            autonomy_mode=AutonomyMode.CHECKPOINT,
            current_phase=PhaseType.DECOMPOSITION,
            phase_results={PhaseType.DECOMPOSITION: result},
            started_at=sample_timestamp,
            beads_epic_id="epic-123",
        )
        data = original.to_dict()
        restored = PipelineState.from_dict(data)
        assert restored.project_path == original.project_path
        assert restored.autonomy_mode == original.autonomy_mode
        assert restored.beads_epic_id == original.beads_epic_id

    def test_get_phase_result_exists(self):
        """Get result for a completed phase."""
        result = PhaseResult(PhaseType.RESEARCH, PhaseStatus.COMPLETE)
        state = PipelineState(
            project_path="/project",
            autonomy_mode=AutonomyMode.CHECKPOINT,
            phase_results={PhaseType.RESEARCH: result},
        )
        assert state.get_phase_result(PhaseType.RESEARCH) == result

    def test_get_phase_result_not_exists(self):
        """Get result for phase not yet run returns None."""
        state = PipelineState(
            project_path="/project",
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )
        assert state.get_phase_result(PhaseType.RESEARCH) is None

    def test_set_phase_result(self):
        """Set result for a phase."""
        state = PipelineState(
            project_path="/project",
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )
        result = PhaseResult(PhaseType.RESEARCH, PhaseStatus.COMPLETE)
        state.set_phase_result(PhaseType.RESEARCH, result)
        assert state.get_phase_result(PhaseType.RESEARCH) == result

    def test_is_phase_complete(self):
        """Check if a specific phase is complete."""
        complete_result = PhaseResult(PhaseType.RESEARCH, PhaseStatus.COMPLETE)
        state = PipelineState(
            project_path="/project",
            autonomy_mode=AutonomyMode.CHECKPOINT,
            phase_results={PhaseType.RESEARCH: complete_result},
        )
        assert state.is_phase_complete(PhaseType.RESEARCH) is True
        assert state.is_phase_complete(PhaseType.DECOMPOSITION) is False

    def test_all_phases_complete(self):
        """Check if all phases are complete."""
        state = PipelineState(
            project_path="/project",
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )
        # Initially nothing is complete
        assert state.all_phases_complete() is False

        # Add all phases as complete
        for phase_type in PhaseType:
            result = PhaseResult(phase_type, PhaseStatus.COMPLETE)
            state.set_phase_result(phase_type, result)

        assert state.all_phases_complete() is True

    def test_validation_empty_project_path(self):
        """Empty project path raises ValueError."""
        with pytest.raises(ValueError, match="project_path must not be empty"):
            PipelineState(
                project_path="",
                autonomy_mode=AutonomyMode.CHECKPOINT,
            )

    def test_validation_whitespace_project_path(self):
        """Whitespace-only project path raises ValueError."""
        with pytest.raises(ValueError, match="project_path must not be empty"):
            PipelineState(
                project_path="   ",
                autonomy_mode=AutonomyMode.CHECKPOINT,
            )


class TestPhaseResultPropertyBased:
    """Property-based tests for PhaseResult serialization."""

    @given(
        duration=st.one_of(st.none(), st.floats(min_value=0, max_value=1e6, allow_nan=False)),
        metadata_keys=st.lists(st.text(min_size=1, max_size=10), max_size=5),
    )
    @settings(max_examples=50)
    def test_serialization_round_trip(self, duration, metadata_keys):
        """PhaseResult survives serialization round-trip."""
        metadata = {k: f"value_{i}" for i, k in enumerate(metadata_keys)}
        result = PhaseResult(
            phase_type=PhaseType.RESEARCH,
            status=PhaseStatus.COMPLETE,
            duration_seconds=duration,
            metadata=metadata,
        )
        data = result.to_dict()
        json_str = json.dumps(data)  # Verify JSON-serializable
        restored = PhaseResult.from_dict(json.loads(json_str))
        assert restored.phase_type == result.phase_type
        assert restored.status == result.status
        assert restored.metadata == result.metadata


class TestPipelineStatePropertyBased:
    """Property-based tests for PipelineState serialization."""

    @given(
        project_path=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    @settings(max_examples=50)
    def test_serialization_round_trip(self, project_path):
        """PipelineState survives serialization round-trip."""
        state = PipelineState(
            project_path=project_path,
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )
        data = state.to_dict()
        json_str = json.dumps(data)  # Verify JSON-serializable
        restored = PipelineState.from_dict(json.loads(json_str))
        assert restored.project_path == state.project_path
        assert restored.autonomy_mode == state.autonomy_mode
