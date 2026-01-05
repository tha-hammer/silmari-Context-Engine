"""Core data models for silmari-rlm-act pipeline.

This module provides dataclasses and enums for:
- Pipeline execution modes (AutonomyMode)
- Pipeline phases (PhaseType, PhaseStatus)
- Phase execution results (PhaseResult)
- Overall pipeline state (PipelineState)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class AutonomyMode(Enum):
    """Execution modes for the pipeline.

    Controls how the pipeline pauses and requires user interaction:
    - CHECKPOINT: Pause at each phase for review (recommended)
    - FULLY_AUTONOMOUS: Run all phases without stopping
    - BATCH: Group phases, pause between groups
    """

    CHECKPOINT = "checkpoint"
    FULLY_AUTONOMOUS = "fully_autonomous"
    BATCH = "batch"

    @classmethod
    def from_string(cls, value: str) -> "AutonomyMode":
        """Convert string to AutonomyMode enum.

        Args:
            value: String representation of autonomy mode

        Returns:
            Corresponding AutonomyMode enum value

        Raises:
            ValueError: If value is not a valid autonomy mode
        """
        for mode in cls:
            if mode.value == value:
                return mode
        valid_modes = ", ".join(m.value for m in cls)
        raise ValueError(f"Invalid autonomy mode '{value}'. Must be one of: {valid_modes}")

    def __str__(self) -> str:
        return self.value


class PhaseType(Enum):
    """Types of phases in the RLM-Act pipeline.

    Each phase represents a stage in the TDD development cycle:
    - RESEARCH: Gather context about the task
    - DECOMPOSITION: Break into testable behaviors
    - TDD_PLANNING: Create Red-Green-Refactor plans
    - MULTI_DOC: Split plan into phase documents
    - BEADS_SYNC: Track epochs and tasks with beads
    - IMPLEMENTATION: Execute TDD cycles
    """

    RESEARCH = "research"
    DECOMPOSITION = "decomposition"
    TDD_PLANNING = "tdd_planning"
    MULTI_DOC = "multi_doc"
    BEADS_SYNC = "beads_sync"
    IMPLEMENTATION = "implementation"

    @classmethod
    def from_string(cls, value: str) -> "PhaseType":
        """Convert string to PhaseType enum.

        Args:
            value: String representation of phase type

        Returns:
            Corresponding PhaseType enum value

        Raises:
            ValueError: If value is not a valid phase type
        """
        for phase in cls:
            if phase.value == value:
                return phase
        valid_phases = ", ".join(p.value for p in cls)
        raise ValueError(f"Invalid phase type '{value}'. Must be one of: {valid_phases}")

    def __str__(self) -> str:
        return self.value


class PhaseStatus(Enum):
    """Status of a pipeline phase.

    Tracks the execution state of each phase:
    - PENDING: Not yet started
    - IN_PROGRESS: Currently executing
    - COMPLETE: Successfully finished
    - FAILED: Encountered errors
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"

    @classmethod
    def from_string(cls, value: str) -> "PhaseStatus":
        """Convert string to PhaseStatus enum.

        Args:
            value: String representation of phase status

        Returns:
            Corresponding PhaseStatus enum value

        Raises:
            ValueError: If value is not a valid phase status
        """
        for status in cls:
            if status.value == value:
                return status
        valid_statuses = ", ".join(s.value for s in cls)
        raise ValueError(f"Invalid phase status '{value}'. Must be one of: {valid_statuses}")

    def __str__(self) -> str:
        return self.value


@dataclass
class PhaseResult:
    """Result of executing a pipeline phase.

    Captures the outcome of running a single phase including:
    - Status (complete, failed, etc.)
    - Artifacts produced (file paths)
    - Errors encountered
    - Timing information

    Attributes:
        phase_type: Which phase was executed
        status: Execution status
        artifacts: List of file paths produced
        errors: List of error messages
        started_at: When execution started
        completed_at: When execution finished
        duration_seconds: Total execution time
        metadata: Additional key-value data
    """

    phase_type: PhaseType
    status: PhaseStatus
    artifacts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        """Check if phase completed successfully."""
        return self.status == PhaseStatus.COMPLETE

    @property
    def is_failed(self) -> bool:
        """Check if phase failed."""
        return self.status == PhaseStatus.FAILED

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary with all fields, enums as strings, datetimes as ISO format.
        """
        return {
            "phase_type": self.phase_type.value,
            "status": self.status.value,
            "artifacts": self.artifacts,
            "errors": self.errors,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PhaseResult":
        """Deserialize from dictionary.

        Args:
            data: Dictionary with phase result fields

        Returns:
            Reconstructed PhaseResult
        """
        started_at = None
        if data.get("started_at"):
            started_at = datetime.fromisoformat(data["started_at"])

        completed_at = None
        if data.get("completed_at"):
            completed_at = datetime.fromisoformat(data["completed_at"])

        return cls(
            phase_type=PhaseType.from_string(data["phase_type"]),
            status=PhaseStatus.from_string(data["status"]),
            artifacts=data.get("artifacts", []),
            errors=data.get("errors", []),
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=data.get("duration_seconds"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class PipelineState:
    """Complete state of the RLM-Act pipeline.

    Tracks the overall pipeline execution including:
    - Project configuration
    - Execution mode
    - Results from each phase
    - Checkpoint and beads integration

    Attributes:
        project_path: Root directory of the project
        autonomy_mode: How the pipeline handles pauses
        current_phase: Currently executing phase (if any)
        phase_results: Results from completed phases
        started_at: When the pipeline started
        checkpoint_id: ID of current checkpoint (for resume)
        beads_epic_id: Beads epic ID for task tracking
        metadata: Additional key-value data
    """

    project_path: str
    autonomy_mode: AutonomyMode
    current_phase: Optional[PhaseType] = None
    phase_results: dict[PhaseType, PhaseResult] = field(default_factory=dict)
    context_entry_ids: dict[PhaseType, list[str]] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    checkpoint_id: Optional[str] = None
    beads_epic_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate state after initialization."""
        self._validate_project_path()

    def _validate_project_path(self) -> None:
        """Validate project_path is non-empty."""
        if not self.project_path or not self.project_path.strip():
            raise ValueError("project_path must not be empty")

    def get_phase_result(self, phase_type: PhaseType) -> Optional[PhaseResult]:
        """Get the result for a specific phase.

        Args:
            phase_type: Which phase to get result for

        Returns:
            PhaseResult if phase was run, None otherwise
        """
        return self.phase_results.get(phase_type)

    def set_phase_result(self, phase_type: PhaseType, result: PhaseResult) -> None:
        """Set the result for a specific phase.

        Args:
            phase_type: Which phase to set result for
            result: The phase result
        """
        self.phase_results[phase_type] = result

    def is_phase_complete(self, phase_type: PhaseType) -> bool:
        """Check if a specific phase is complete.

        Args:
            phase_type: Which phase to check

        Returns:
            True if phase was run and completed successfully
        """
        result = self.get_phase_result(phase_type)
        return result is not None and result.is_complete

    def all_phases_complete(self) -> bool:
        """Check if all phases are complete.

        Returns:
            True if every phase type has a complete result
        """
        for phase_type in PhaseType:
            if not self.is_phase_complete(phase_type):
                return False
        return True

    def track_context_entry(self, phase_type: PhaseType, entry_id: str) -> None:
        """Track a Context Window Array entry ID for a phase.

        Args:
            phase_type: Which phase the entry belongs to
            entry_id: The CWA entry ID to track
        """
        if phase_type not in self.context_entry_ids:
            self.context_entry_ids[phase_type] = []
        self.context_entry_ids[phase_type].append(entry_id)

    def get_context_entries(self, phase_type: PhaseType) -> list[str]:
        """Get tracked CWA entry IDs for a phase.

        Args:
            phase_type: Which phase to get entries for

        Returns:
            List of entry IDs (empty list if none tracked)
        """
        return self.context_entry_ids.get(phase_type, [])

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary with all fields, enums as strings, datetimes as ISO format.
        """
        return {
            "project_path": self.project_path,
            "autonomy_mode": self.autonomy_mode.value,
            "current_phase": self.current_phase.value if self.current_phase else None,
            "phase_results": {
                phase_type.value: result.to_dict()
                for phase_type, result in self.phase_results.items()
            },
            "context_entry_ids": {
                phase_type.value: entry_ids
                for phase_type, entry_ids in self.context_entry_ids.items()
            },
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "checkpoint_id": self.checkpoint_id,
            "beads_epic_id": self.beads_epic_id,
            "metadata": self.metadata,
        }

    def to_checkpoint_dict(self) -> dict[str, Any]:
        """Serialize to checkpoint-compatible dictionary.

        This is an alias for to_dict(), provided for semantic clarity
        when writing checkpoints.

        Returns:
            Dictionary suitable for checkpoint storage.
        """
        return self.to_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineState":
        """Deserialize from dictionary.

        Args:
            data: Dictionary with pipeline state fields

        Returns:
            Reconstructed PipelineState
        """
        started_at = None
        if data.get("started_at"):
            started_at = datetime.fromisoformat(data["started_at"])

        current_phase = None
        if data.get("current_phase"):
            current_phase = PhaseType.from_string(data["current_phase"])

        phase_results = {}
        for phase_str, result_data in data.get("phase_results", {}).items():
            phase_type = PhaseType.from_string(phase_str)
            phase_results[phase_type] = PhaseResult.from_dict(result_data)

        context_entry_ids: dict[PhaseType, list[str]] = {}
        for phase_str, entry_ids in data.get("context_entry_ids", {}).items():
            phase_type = PhaseType.from_string(phase_str)
            context_entry_ids[phase_type] = entry_ids

        return cls(
            project_path=data["project_path"],
            autonomy_mode=AutonomyMode.from_string(data["autonomy_mode"]),
            current_phase=current_phase,
            phase_results=phase_results,
            context_entry_ids=context_entry_ids,
            started_at=started_at,
            checkpoint_id=data.get("checkpoint_id"),
            beads_epic_id=data.get("beads_epic_id"),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_checkpoint_dict(cls, data: dict[str, Any]) -> "PipelineState":
        """Deserialize from checkpoint dictionary.

        This is an alias for from_dict(), provided for semantic clarity
        when loading checkpoints.

        Args:
            data: Dictionary from checkpoint file's 'state' field

        Returns:
            Reconstructed PipelineState
        """
        return cls.from_dict(data)
