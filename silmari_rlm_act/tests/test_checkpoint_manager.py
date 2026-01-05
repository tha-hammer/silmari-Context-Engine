"""Tests for CheckpointManager: pipeline checkpoint management.

Phase 02 of TDD implementation for silmari-rlm-act pipeline.
Tests 10 behaviors for checkpoint write, detect, cleanup, and load operations.
"""

import json
import re
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from silmari_rlm_act.checkpoints.manager import CheckpointManager
from silmari_rlm_act.models import (
    AutonomyMode,
    PhaseResult,
    PhaseStatus,
    PhaseType,
    PipelineState,
)


class TestWriteCheckpoint:
    """Behavior 1: Write Checkpoint."""

    def test_creates_checkpoint_file(self, tmp_path: Path) -> None:
        """Given state, creates JSON file."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState(
            project_path=str(tmp_path),
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )
        result = PhaseResult(phase_type=PhaseType.RESEARCH, status=PhaseStatus.COMPLETE)
        state.set_phase_result(PhaseType.RESEARCH, result)

        checkpoint_path = manager.write_checkpoint(state, "research-complete")

        assert Path(checkpoint_path).exists()
        assert checkpoint_path.endswith(".json")

    def test_checkpoint_contains_state_data(self, tmp_path: Path) -> None:
        """Given state with data, checkpoint contains it."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState(
            project_path=str(tmp_path),
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )
        result = PhaseResult(
            phase_type=PhaseType.RESEARCH,
            status=PhaseStatus.COMPLETE,
            artifacts=["/path/to/research.md"],
        )
        state.set_phase_result(PhaseType.RESEARCH, result)

        checkpoint_path = manager.write_checkpoint(state, "research-complete")

        with open(checkpoint_path) as f:
            data = json.load(f)

        assert data["phase"] == "research-complete"
        assert "state" in data
        assert data["state"]["phase_results"]["research"]["status"] == "complete"

    def test_checkpoint_stored_in_rlm_act_checkpoints_dir(self, tmp_path: Path) -> None:
        """Given project path, creates .rlm-act-checkpoints/."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState(
            project_path=str(tmp_path),
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )

        checkpoint_path = manager.write_checkpoint(state, "test")

        assert ".rlm-act-checkpoints" in checkpoint_path
        assert (tmp_path / ".rlm-act-checkpoints").is_dir()


class TestDetectResumableCheckpoint:
    """Behavior 2: Detect Resumable Checkpoint."""

    def test_returns_none_when_no_checkpoints(self, tmp_path: Path) -> None:
        """Given no checkpoints, returns None."""
        manager = CheckpointManager(tmp_path)

        checkpoint = manager.detect_resumable_checkpoint()

        assert checkpoint is None

    def test_returns_most_recent_checkpoint(self, tmp_path: Path) -> None:
        """Given multiple checkpoints, returns newest."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState(
            project_path=str(tmp_path),
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )

        # Create older checkpoint
        manager.write_checkpoint(state, "research-complete")
        time.sleep(0.1)  # Ensure different timestamps

        # Create newer checkpoint
        result = PhaseResult(
            phase_type=PhaseType.DECOMPOSITION, status=PhaseStatus.COMPLETE
        )
        state.set_phase_result(PhaseType.DECOMPOSITION, result)
        manager.write_checkpoint(state, "decomposition-complete")

        checkpoint = manager.detect_resumable_checkpoint()

        assert checkpoint is not None
        assert checkpoint["phase"] == "decomposition-complete"

    def test_checkpoint_includes_file_path(self, tmp_path: Path) -> None:
        """Given checkpoint, includes file_path key."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState(
            project_path=str(tmp_path),
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )
        manager.write_checkpoint(state, "test")

        checkpoint = manager.detect_resumable_checkpoint()

        assert checkpoint is not None
        assert "file_path" in checkpoint
        assert Path(checkpoint["file_path"]).exists()


class TestCheckpointAge:
    """Behavior 3: Checkpoint Age Calculation."""

    def test_returns_zero_for_today(self, tmp_path: Path) -> None:
        """Given checkpoint from today, returns 0."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState(
            project_path=str(tmp_path),
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )
        manager.write_checkpoint(state, "test")

        checkpoint = manager.detect_resumable_checkpoint()
        assert checkpoint is not None
        age = manager.get_checkpoint_age_days(checkpoint)

        assert age == 0

    def test_calculates_age_in_days(self, tmp_path: Path) -> None:
        """Given old timestamp, returns correct age."""
        manager = CheckpointManager(tmp_path)

        # Create checkpoint with old timestamp
        old_timestamp = (datetime.now() - timedelta(days=5)).isoformat() + "Z"
        checkpoint = {"timestamp": old_timestamp}

        age = manager.get_checkpoint_age_days(checkpoint)

        assert age == 5

    def test_handles_missing_timestamp(self, tmp_path: Path) -> None:
        """Given no timestamp, returns 0."""
        manager = CheckpointManager(tmp_path)

        age = manager.get_checkpoint_age_days({})

        assert age == 0


class TestDeleteCheckpoint:
    """Behavior 4: Delete Single Checkpoint."""

    def test_deletes_checkpoint_file(self, tmp_path: Path) -> None:
        """Given checkpoint path, deletes file."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState(
            project_path=str(tmp_path),
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )
        checkpoint_path = manager.write_checkpoint(state, "test")

        result = manager.delete_checkpoint(checkpoint_path)

        assert result is True
        assert not Path(checkpoint_path).exists()

    def test_returns_false_for_nonexistent(self, tmp_path: Path) -> None:
        """Given nonexistent path, returns False."""
        manager = CheckpointManager(tmp_path)

        result = manager.delete_checkpoint("/nonexistent/path.json")

        assert result is False


class TestCleanupByAge:
    """Behavior 5: Cleanup by Age."""

    def test_deletes_old_checkpoints(self, tmp_path: Path) -> None:
        """Given checkpoints older than N days, deletes them."""
        manager = CheckpointManager(tmp_path)
        manager.checkpoints_dir.mkdir()

        # Create old checkpoint manually
        old_checkpoint = manager.checkpoints_dir / "old.json"
        old_timestamp = (datetime.now() - timedelta(days=10)).isoformat() + "Z"
        old_checkpoint.write_text(
            json.dumps({"id": "old", "timestamp": old_timestamp, "phase": "test"})
        )

        # Create new checkpoint
        state = PipelineState(
            project_path=str(tmp_path),
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )
        new_path = manager.write_checkpoint(state, "new")

        deleted, failed = manager.cleanup_by_age(days=7)

        assert deleted == 1
        assert failed == 0
        assert not old_checkpoint.exists()
        assert Path(new_path).exists()


class TestCleanupAll:
    """Behavior 6: Cleanup All Checkpoints."""

    def test_deletes_all_checkpoints(self, tmp_path: Path) -> None:
        """Given multiple checkpoints, deletes all."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState(
            project_path=str(tmp_path),
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )

        manager.write_checkpoint(state, "test1")
        manager.write_checkpoint(state, "test2")

        deleted, failed = manager.cleanup_all()

        assert deleted == 2
        assert failed == 0
        assert len(list(manager.checkpoints_dir.glob("*.json"))) == 0


class TestCheckpointGitCommit:
    """Behavior 7: Checkpoint Includes Git Commit."""

    def test_includes_git_commit_hash(self, tmp_path: Path) -> None:
        """Given git repo, checkpoint includes commit hash."""
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )
        (tmp_path / "test.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )

        manager = CheckpointManager(tmp_path)
        state = PipelineState(
            project_path=str(tmp_path),
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )
        checkpoint_path = manager.write_checkpoint(state, "test")

        with open(checkpoint_path) as f:
            data = json.load(f)

        assert "git_commit" in data
        assert len(data["git_commit"]) == 40  # SHA-1 hash length

    def test_empty_git_commit_when_not_git_repo(self, tmp_path: Path) -> None:
        """Given non-git directory, git_commit is empty string."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState(
            project_path=str(tmp_path),
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )
        checkpoint_path = manager.write_checkpoint(state, "test")

        with open(checkpoint_path) as f:
            data = json.load(f)

        assert "git_commit" in data
        assert data["git_commit"] == ""


class TestCheckpointCWAEntries:
    """Behavior 8: Checkpoint Includes CWA Entry IDs."""

    def test_includes_context_entry_ids(self, tmp_path: Path) -> None:
        """Given state with entries, checkpoint includes them."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState(
            project_path=str(tmp_path),
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )
        state.track_context_entry(PhaseType.RESEARCH, "ctx_001")
        state.track_context_entry(PhaseType.RESEARCH, "ctx_002")

        checkpoint_path = manager.write_checkpoint(state, "test")

        with open(checkpoint_path) as f:
            data = json.load(f)

        assert "context_entry_ids" in data["state"]
        assert data["state"]["context_entry_ids"]["research"] == ["ctx_001", "ctx_002"]


class TestLoadCheckpoint:
    """Behavior 9: Load Checkpoint Returns PipelineState."""

    def test_load_returns_pipeline_state(self, tmp_path: Path) -> None:
        """Given checkpoint file, load returns PipelineState."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState(
            project_path=str(tmp_path),
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )
        result = PhaseResult(phase_type=PhaseType.RESEARCH, status=PhaseStatus.COMPLETE)
        state.set_phase_result(PhaseType.RESEARCH, result)
        state.track_context_entry(PhaseType.RESEARCH, "ctx_001")
        checkpoint_path = manager.write_checkpoint(state, "test")

        loaded_state = manager.load_checkpoint(checkpoint_path)

        assert isinstance(loaded_state, PipelineState)
        assert loaded_state.is_phase_complete(PhaseType.RESEARCH)
        assert loaded_state.get_context_entries(PhaseType.RESEARCH) == ["ctx_001"]

    def test_load_preserves_all_fields(self, tmp_path: Path) -> None:
        """Given checkpoint, load preserves all PipelineState fields."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState(
            project_path=str(tmp_path),
            autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
            current_phase=PhaseType.DECOMPOSITION,
            beads_epic_id="beads-xyz789",
            metadata={"user": "maceo"},
        )
        checkpoint_path = manager.write_checkpoint(state, "test")

        loaded_state = manager.load_checkpoint(checkpoint_path)

        assert loaded_state.project_path == str(tmp_path)
        assert loaded_state.autonomy_mode == AutonomyMode.FULLY_AUTONOMOUS
        assert loaded_state.current_phase == PhaseType.DECOMPOSITION
        assert loaded_state.beads_epic_id == "beads-xyz789"
        assert loaded_state.metadata == {"user": "maceo"}

    def test_load_nonexistent_raises_error(self, tmp_path: Path) -> None:
        """Given nonexistent path, raises FileNotFoundError."""
        manager = CheckpointManager(tmp_path)

        with pytest.raises(FileNotFoundError):
            manager.load_checkpoint("/nonexistent/path.json")


class TestCheckpointNaming:
    """Behavior 10: Checkpoint Naming Convention."""

    def test_filename_is_uuid(self, tmp_path: Path) -> None:
        """Given checkpoint, filename is UUID."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState(
            project_path=str(tmp_path),
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )

        checkpoint_path = manager.write_checkpoint(state, "test")
        filename = Path(checkpoint_path).stem

        # UUID pattern
        uuid_pattern = (
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        )
        assert re.match(uuid_pattern, filename)

    def test_checkpoint_id_matches_filename(self, tmp_path: Path) -> None:
        """Given checkpoint, id field matches filename."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState(
            project_path=str(tmp_path),
            autonomy_mode=AutonomyMode.CHECKPOINT,
        )

        checkpoint_path = manager.write_checkpoint(state, "test")
        filename = Path(checkpoint_path).stem

        with open(checkpoint_path) as f:
            data = json.load(f)

        assert data["id"] == filename
