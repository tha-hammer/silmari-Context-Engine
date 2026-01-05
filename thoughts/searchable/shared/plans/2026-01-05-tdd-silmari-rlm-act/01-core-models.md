# Phase 01: Core Models TDD Plan

## Overview

Define the core data models for the silmari-rlm-act pipeline. These are foundational types used across all phases.

## Testable Behaviors

### Behavior 1: PhaseResult Creation
**Given**: Phase name, success status, and optional output
**When**: Creating a PhaseResult
**Then**: All fields are set correctly and serializable

### Behavior 2: PhaseResult with Artifacts
**Given**: A successful phase with produced files
**When**: Creating PhaseResult with artifacts list
**Then**: Artifacts stored as absolute paths

### Behavior 3: PipelineState Initialization
**Given**: A new pipeline run
**When**: Creating initial PipelineState
**Then**: All phases show "pending" status

### Behavior 4: PipelineState Phase Transition
**Given**: A pipeline in progress
**When**: Completing a phase
**Then**: State updates to show phase as "completed"

### Behavior 5: PipelineState CWA Entry Tracking
**Given**: Context entries created during pipeline
**When**: Recording entry IDs in state
**Then**: Entry IDs associated with correct phase

### Behavior 6: AutonomyMode Enum
**Given**: The three execution modes
**When**: Selecting a mode
**Then**: Mode determines pause behavior

### Behavior 7: PhaseResult Serialization
**Given**: A PhaseResult instance
**When**: Calling to_dict()
**Then**: Returns JSON-serializable dictionary

### Behavior 8: PipelineState from Checkpoint
**Given**: A checkpoint JSON file
**When**: Loading into PipelineState
**Then**: All state restored correctly

---

## TDD Cycle: Behavior 1 - PhaseResult Creation

### Test Specification
**Given**: Phase name "research", success=True, output="Research complete"
**When**: Creating PhaseResult(phase="research", success=True, output="Research complete")
**Then**: phase="research", success=True, output="Research complete"

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_models.py`
```python
import pytest
from silmari_rlm_act.models import PhaseResult


class TestPhaseResult:
    """Behavior 1: PhaseResult Creation."""

    def test_creates_with_required_fields(self):
        """Given phase name and success, creates PhaseResult."""
        result = PhaseResult(phase="research", success=True)

        assert result.phase == "research"
        assert result.success is True
        assert result.output is None
        assert result.error is None
        assert result.artifacts == []

    def test_creates_with_output(self):
        """Given output string, stores it."""
        result = PhaseResult(
            phase="research",
            success=True,
            output="Research document created"
        )

        assert result.output == "Research document created"

    def test_creates_with_error_on_failure(self):
        """Given failure, stores error message."""
        result = PhaseResult(
            phase="research",
            success=False,
            error="LLM timeout"
        )

        assert result.success is False
        assert result.error == "LLM timeout"
```

### 🟢 Green: Minimal Implementation

**File**: `silmari-rlm-act/models.py`
```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PhaseResult:
    """Result from executing a pipeline phase."""

    phase: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    artifacts: list[str] = field(default_factory=list)
```

### 🔵 Refactor: Add Docstrings and Validation

**File**: `silmari-rlm-act/models.py`
```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PhaseResult:
    """Result from executing a pipeline phase.

    Attributes:
        phase: Name of the phase (e.g., "research", "decomposition")
        success: Whether the phase completed successfully
        output: Output text from the phase (if any)
        error: Error message (if failed)
        artifacts: List of absolute paths to produced files
    """

    phase: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    artifacts: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate phase name is not empty."""
        if not self.phase:
            raise ValueError("Phase name cannot be empty")
```

### Success Criteria
**Automated:**
- [ ] Test fails for right reason: `pytest silmari-rlm-act/tests/test_models.py::TestPhaseResult -v`
- [ ] Test passes after implementation
- [ ] All tests pass after refactor

**Manual:**
- [ ] PhaseResult can be instantiated in REPL

---

## TDD Cycle: Behavior 2 - PhaseResult with Artifacts

### Test Specification
**Given**: Artifacts ["path/to/file1.md", "path/to/file2.md"]
**When**: Creating PhaseResult with artifacts
**Then**: artifacts list contains both paths

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_models.py`
```python
class TestPhaseResultArtifacts:
    """Behavior 2: PhaseResult with Artifacts."""

    def test_stores_artifact_paths(self):
        """Given artifacts list, stores paths."""
        artifacts = ["/abs/path/file1.md", "/abs/path/file2.md"]
        result = PhaseResult(
            phase="tdd_planning",
            success=True,
            artifacts=artifacts
        )

        assert result.artifacts == artifacts
        assert len(result.artifacts) == 2

    def test_validates_absolute_paths(self):
        """Given relative path, raises ValueError."""
        with pytest.raises(ValueError, match="must be absolute"):
            PhaseResult(
                phase="tdd_planning",
                success=True,
                artifacts=["relative/path/file.md"]
            )
```

### 🟢 Green: Add Validation

**File**: `silmari-rlm-act/models.py`
```python
from pathlib import Path

@dataclass
class PhaseResult:
    # ... existing fields ...

    def __post_init__(self):
        if not self.phase:
            raise ValueError("Phase name cannot be empty")

        for artifact in self.artifacts:
            if not Path(artifact).is_absolute():
                raise ValueError(f"Artifact path must be absolute: {artifact}")
```

### 🔵 Refactor
No refactoring needed - implementation is minimal.

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_models.py::TestPhaseResultArtifacts -v`

---

## TDD Cycle: Behavior 3 - PipelineState Initialization

### Test Specification
**Given**: Starting a new pipeline
**When**: Creating PipelineState()
**Then**: All phases show "pending", no artifacts, no errors

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_models.py`
```python
from silmari_rlm_act.models import PipelineState, PhaseStatus


class TestPipelineState:
    """Behavior 3: PipelineState Initialization."""

    def test_initializes_all_phases_pending(self):
        """Given new pipeline, all phases are pending."""
        state = PipelineState()

        assert state.get_phase_status("research") == PhaseStatus.PENDING
        assert state.get_phase_status("decomposition") == PhaseStatus.PENDING
        assert state.get_phase_status("tdd_planning") == PhaseStatus.PENDING
        assert state.get_phase_status("multi_doc") == PhaseStatus.PENDING
        assert state.get_phase_status("beads_sync") == PhaseStatus.PENDING
        assert state.get_phase_status("implementation") == PhaseStatus.PENDING

    def test_tracks_started_timestamp(self):
        """Given new pipeline, records start time."""
        state = PipelineState()

        assert state.started is not None
        assert isinstance(state.started, str)  # ISO format

    def test_current_phase_is_none(self):
        """Given new pipeline, no phase is current."""
        state = PipelineState()

        assert state.current_phase is None
```

### 🟢 Green: Implement PipelineState

**File**: `silmari-rlm-act/models.py`
```python
from datetime import datetime
from enum import Enum


class PhaseStatus(Enum):
    """Status of a pipeline phase."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


PIPELINE_PHASES = [
    "research",
    "decomposition",
    "tdd_planning",
    "multi_doc",
    "beads_sync",
    "implementation"
]


@dataclass
class PipelineState:
    """State of the entire pipeline run."""

    started: str = field(default_factory=lambda: datetime.now().isoformat())
    current_phase: Optional[str] = None
    phase_statuses: dict[str, PhaseStatus] = field(default_factory=dict)
    phase_results: dict[str, PhaseResult] = field(default_factory=dict)
    context_entry_ids: dict[str, list[str]] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize all phases to pending."""
        for phase in PIPELINE_PHASES:
            if phase not in self.phase_statuses:
                self.phase_statuses[phase] = PhaseStatus.PENDING

    def get_phase_status(self, phase: str) -> PhaseStatus:
        """Get status of a specific phase."""
        return self.phase_statuses.get(phase, PhaseStatus.PENDING)
```

### 🔵 Refactor
Add type annotations and docstrings.

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_models.py::TestPipelineState -v`

---

## TDD Cycle: Behavior 4 - PipelineState Phase Transition

### Test Specification
**Given**: Pipeline with research in progress
**When**: Calling complete_phase("research", result)
**Then**: Research status is COMPLETED, decomposition is IN_PROGRESS

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_models.py`
```python
class TestPipelineStateTransitions:
    """Behavior 4: PipelineState Phase Transition."""

    def test_start_phase_sets_in_progress(self):
        """Given pending phase, start sets to in_progress."""
        state = PipelineState()

        state.start_phase("research")

        assert state.current_phase == "research"
        assert state.get_phase_status("research") == PhaseStatus.IN_PROGRESS

    def test_complete_phase_sets_completed(self):
        """Given in_progress phase, complete sets to completed."""
        state = PipelineState()
        state.start_phase("research")

        result = PhaseResult(phase="research", success=True)
        state.complete_phase("research", result)

        assert state.get_phase_status("research") == PhaseStatus.COMPLETED
        assert state.phase_results["research"] == result

    def test_fail_phase_sets_failed(self):
        """Given in_progress phase, fail sets to failed."""
        state = PipelineState()
        state.start_phase("research")

        result = PhaseResult(phase="research", success=False, error="Timeout")
        state.fail_phase("research", result)

        assert state.get_phase_status("research") == PhaseStatus.FAILED
        assert state.phase_results["research"] == result

    def test_get_next_phase_returns_first_pending(self):
        """Given completed phases, returns next pending."""
        state = PipelineState()
        state.complete_phase("research", PhaseResult(phase="research", success=True))

        assert state.get_next_phase() == "decomposition"
```

### 🟢 Green: Implement Transitions

**File**: `silmari-rlm-act/models.py`
```python
@dataclass
class PipelineState:
    # ... existing fields ...

    def start_phase(self, phase: str) -> None:
        """Mark a phase as in progress."""
        if phase not in PIPELINE_PHASES:
            raise ValueError(f"Unknown phase: {phase}")
        self.current_phase = phase
        self.phase_statuses[phase] = PhaseStatus.IN_PROGRESS

    def complete_phase(self, phase: str, result: PhaseResult) -> None:
        """Mark a phase as completed with result."""
        self.phase_statuses[phase] = PhaseStatus.COMPLETED
        self.phase_results[phase] = result
        self.current_phase = None

    def fail_phase(self, phase: str, result: PhaseResult) -> None:
        """Mark a phase as failed with result."""
        self.phase_statuses[phase] = PhaseStatus.FAILED
        self.phase_results[phase] = result
        self.current_phase = None

    def get_next_phase(self) -> Optional[str]:
        """Get next pending phase, or None if all done."""
        for phase in PIPELINE_PHASES:
            if self.phase_statuses.get(phase) == PhaseStatus.PENDING:
                return phase
        return None
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_models.py::TestPipelineStateTransitions -v`

---

## TDD Cycle: Behavior 5 - PipelineState CWA Entry Tracking

### Test Specification
**Given**: Context entries created during research phase
**When**: Recording entry IDs with track_entry(phase, entry_id)
**Then**: Entry IDs associated with research phase

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_models.py`
```python
class TestPipelineStateCWATracking:
    """Behavior 5: PipelineState CWA Entry Tracking."""

    def test_track_entry_adds_to_phase(self):
        """Given entry ID, associates with current phase."""
        state = PipelineState()
        state.start_phase("research")

        state.track_entry("research", "ctx_001")
        state.track_entry("research", "ctx_002")

        assert state.context_entry_ids["research"] == ["ctx_001", "ctx_002"]

    def test_get_phase_entries_returns_list(self):
        """Given phase with entries, returns entry IDs."""
        state = PipelineState()
        state.context_entry_ids["research"] = ["ctx_001", "ctx_002"]

        entries = state.get_phase_entries("research")

        assert entries == ["ctx_001", "ctx_002"]

    def test_get_all_entries_returns_flat_list(self):
        """Given multiple phases, returns all entry IDs."""
        state = PipelineState()
        state.context_entry_ids["research"] = ["ctx_001"]
        state.context_entry_ids["decomposition"] = ["ctx_002", "ctx_003"]

        all_entries = state.get_all_entries()

        assert set(all_entries) == {"ctx_001", "ctx_002", "ctx_003"}
```

### 🟢 Green: Implement Tracking

**File**: `silmari-rlm-act/models.py`
```python
@dataclass
class PipelineState:
    # ... existing fields ...

    def track_entry(self, phase: str, entry_id: str) -> None:
        """Track a CWA entry ID for a phase."""
        if phase not in self.context_entry_ids:
            self.context_entry_ids[phase] = []
        self.context_entry_ids[phase].append(entry_id)

    def get_phase_entries(self, phase: str) -> list[str]:
        """Get all entry IDs for a phase."""
        return self.context_entry_ids.get(phase, [])

    def get_all_entries(self) -> list[str]:
        """Get all entry IDs across all phases."""
        all_ids = []
        for ids in self.context_entry_ids.values():
            all_ids.extend(ids)
        return all_ids
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_models.py::TestPipelineStateCWATracking -v`

---

## TDD Cycle: Behavior 6 - AutonomyMode Enum

### Test Specification
**Given**: Three execution modes (checkpoint, autonomous, batch)
**When**: Selecting a mode
**Then**: Mode has correct string value

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_models.py`
```python
from silmari_rlm_act.models import AutonomyMode


class TestAutonomyMode:
    """Behavior 6: AutonomyMode Enum."""

    def test_checkpoint_mode(self):
        """Checkpoint mode pauses at each phase."""
        assert AutonomyMode.CHECKPOINT.value == "checkpoint"

    def test_autonomous_mode(self):
        """Autonomous mode runs without stopping."""
        assert AutonomyMode.AUTONOMOUS.value == "autonomous"

    def test_batch_mode(self):
        """Batch mode groups phases."""
        assert AutonomyMode.BATCH.value == "batch"

    def test_from_string(self):
        """Given 'c', returns CHECKPOINT."""
        assert AutonomyMode.from_input("c") == AutonomyMode.CHECKPOINT
        assert AutonomyMode.from_input("f") == AutonomyMode.AUTONOMOUS
        assert AutonomyMode.from_input("b") == AutonomyMode.BATCH
```

### 🟢 Green: Implement Enum

**File**: `silmari-rlm-act/models.py`
```python
class AutonomyMode(Enum):
    """Execution mode for implementation phase."""
    CHECKPOINT = "checkpoint"
    AUTONOMOUS = "autonomous"
    BATCH = "batch"

    @classmethod
    def from_input(cls, char: str) -> "AutonomyMode":
        """Parse single character input to mode."""
        mapping = {
            "c": cls.CHECKPOINT,
            "f": cls.AUTONOMOUS,
            "b": cls.BATCH,
            "": cls.CHECKPOINT,  # Default
        }
        return mapping.get(char.lower(), cls.CHECKPOINT)
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_models.py::TestAutonomyMode -v`

---

## TDD Cycle: Behavior 7 - PhaseResult Serialization

### Test Specification
**Given**: A PhaseResult instance
**When**: Calling to_dict()
**Then**: Returns dictionary with all fields

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_models.py`
```python
class TestPhaseResultSerialization:
    """Behavior 7: PhaseResult Serialization."""

    def test_to_dict_includes_all_fields(self):
        """Given PhaseResult, to_dict returns all fields."""
        result = PhaseResult(
            phase="research",
            success=True,
            output="Done",
            artifacts=["/path/to/file.md"]
        )

        d = result.to_dict()

        assert d["phase"] == "research"
        assert d["success"] is True
        assert d["output"] == "Done"
        assert d["artifacts"] == ["/path/to/file.md"]
        assert d["error"] is None

    def test_from_dict_restores_object(self):
        """Given dict, from_dict creates PhaseResult."""
        d = {
            "phase": "research",
            "success": True,
            "output": "Done",
            "error": None,
            "artifacts": ["/path/to/file.md"]
        }

        result = PhaseResult.from_dict(d)

        assert result.phase == "research"
        assert result.success is True
        assert result.artifacts == ["/path/to/file.md"]
```

### 🟢 Green: Implement Serialization

**File**: `silmari-rlm-act/models.py`
```python
@dataclass
class PhaseResult:
    # ... existing fields ...

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "phase": self.phase,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "artifacts": self.artifacts,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PhaseResult":
        """Deserialize from dictionary."""
        return cls(
            phase=d["phase"],
            success=d["success"],
            output=d.get("output"),
            error=d.get("error"),
            artifacts=d.get("artifacts", []),
        )
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_models.py::TestPhaseResultSerialization -v`

---

## TDD Cycle: Behavior 8 - PipelineState from Checkpoint

### Test Specification
**Given**: A checkpoint JSON with state data
**When**: Loading with PipelineState.from_checkpoint(data)
**Then**: All state fields restored

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_models.py`
```python
class TestPipelineStateCheckpoint:
    """Behavior 8: PipelineState from Checkpoint."""

    def test_to_checkpoint_dict(self):
        """Given state, to_checkpoint_dict includes all data."""
        state = PipelineState()
        state.start_phase("research")
        state.complete_phase("research", PhaseResult(phase="research", success=True))
        state.track_entry("research", "ctx_001")

        d = state.to_checkpoint_dict()

        assert d["started"] == state.started
        assert d["phase_statuses"]["research"] == "completed"
        assert d["context_entry_ids"]["research"] == ["ctx_001"]

    def test_from_checkpoint_dict_restores_state(self):
        """Given checkpoint dict, restores PipelineState."""
        d = {
            "started": "2026-01-05T10:00:00",
            "current_phase": None,
            "phase_statuses": {
                "research": "completed",
                "decomposition": "in_progress"
            },
            "phase_results": {
                "research": {
                    "phase": "research",
                    "success": True,
                    "output": None,
                    "error": None,
                    "artifacts": []
                }
            },
            "context_entry_ids": {
                "research": ["ctx_001"]
            }
        }

        state = PipelineState.from_checkpoint_dict(d)

        assert state.started == "2026-01-05T10:00:00"
        assert state.get_phase_status("research") == PhaseStatus.COMPLETED
        assert state.get_phase_status("decomposition") == PhaseStatus.IN_PROGRESS
        assert state.get_phase_entries("research") == ["ctx_001"]
```

### 🟢 Green: Implement Checkpoint Methods

**File**: `silmari-rlm-act/models.py`
```python
@dataclass
class PipelineState:
    # ... existing fields ...

    def to_checkpoint_dict(self) -> dict:
        """Serialize state for checkpoint."""
        return {
            "started": self.started,
            "current_phase": self.current_phase,
            "phase_statuses": {
                k: v.value for k, v in self.phase_statuses.items()
            },
            "phase_results": {
                k: v.to_dict() for k, v in self.phase_results.items()
            },
            "context_entry_ids": self.context_entry_ids,
        }

    @classmethod
    def from_checkpoint_dict(cls, d: dict) -> "PipelineState":
        """Restore state from checkpoint."""
        state = cls()
        state.started = d.get("started", state.started)
        state.current_phase = d.get("current_phase")

        for phase, status_str in d.get("phase_statuses", {}).items():
            state.phase_statuses[phase] = PhaseStatus(status_str)

        for phase, result_dict in d.get("phase_results", {}).items():
            state.phase_results[phase] = PhaseResult.from_dict(result_dict)

        state.context_entry_ids = d.get("context_entry_ids", {})

        return state
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_models.py::TestPipelineStateCheckpoint -v`
- [ ] All model tests pass: `pytest silmari-rlm-act/tests/test_models.py -v`

**Manual:**
- [ ] Models can be used in Python REPL
- [ ] Checkpoint serialization round-trips correctly

## Summary

This phase defines the core data models:
- `PhaseResult` - Result from a single phase execution
- `PipelineState` - State of the entire pipeline run
- `PhaseStatus` - Enum for phase states
- `AutonomyMode` - Enum for implementation modes

All models support:
- Serialization/deserialization for checkpoints
- CWA entry tracking
- Phase transitions
