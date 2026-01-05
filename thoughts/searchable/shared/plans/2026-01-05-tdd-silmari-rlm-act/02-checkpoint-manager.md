# Phase 02: Checkpoint Manager TDD Plan

## Overview

Implement checkpoint management for the silmari-rlm-act pipeline. This enables resume functionality after failures or intentional pauses.

## Testable Behaviors

### Behavior 1: Write Checkpoint
**Given**: Pipeline state and phase name
**When**: Calling write_checkpoint()
**Then**: JSON file created in `.rlm-act-checkpoints/`

### Behavior 2: Detect Resumable Checkpoint
**Given**: Checkpoint files exist
**When**: Calling detect_resumable_checkpoint()
**Then**: Returns most recent checkpoint

### Behavior 3: Checkpoint Age Calculation
**Given**: Checkpoint with timestamp
**When**: Calling get_checkpoint_age_days()
**Then**: Returns correct age in days

### Behavior 4: Delete Single Checkpoint
**Given**: Checkpoint file path
**When**: Calling delete_checkpoint()
**Then**: File is removed

### Behavior 5: Cleanup by Age
**Given**: Multiple checkpoints of various ages
**When**: Calling cleanup_by_age(days=7)
**Then**: Checkpoints older than 7 days deleted

### Behavior 6: Cleanup All Checkpoints
**Given**: Multiple checkpoints
**When**: Calling cleanup_all()
**Then**: All checkpoints deleted

### Behavior 7: Checkpoint Includes Git Commit
**Given**: Git repository with commits
**When**: Writing checkpoint
**Then**: Current git commit hash stored

### Behavior 8: Checkpoint Includes CWA Entry IDs
**Given**: Pipeline with tracked context entries
**When**: Writing checkpoint
**Then**: Entry IDs stored in checkpoint

### Behavior 9: Load Checkpoint Returns PipelineState
**Given**: Valid checkpoint file
**When**: Calling load_checkpoint()
**Then**: Returns PipelineState object

### Behavior 10: Checkpoint Naming Convention
**Given**: New checkpoint
**When**: Writing checkpoint
**Then**: Filename is UUID.json

---

## TDD Cycle: Behavior 1 - Write Checkpoint

### Test Specification
**Given**: PipelineState with research completed
**When**: Calling write_checkpoint(state, "research-complete")
**Then**: JSON file created with correct structure

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_checkpoint_manager.py`
```python
import pytest
import json
from pathlib import Path
from silmari_rlm_act.checkpoints.manager import CheckpointManager
from silmari_rlm_act.models import PipelineState, PhaseResult


class TestWriteCheckpoint:
    """Behavior 1: Write Checkpoint."""

    def test_creates_checkpoint_file(self, tmp_path):
        """Given state, creates JSON file."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState()
        state.complete_phase("research", PhaseResult(phase="research", success=True))

        checkpoint_path = manager.write_checkpoint(state, "research-complete")

        assert Path(checkpoint_path).exists()
        assert checkpoint_path.endswith(".json")

    def test_checkpoint_contains_state_data(self, tmp_path):
        """Given state with data, checkpoint contains it."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState()
        state.complete_phase("research", PhaseResult(
            phase="research",
            success=True,
            artifacts=["/path/to/research.md"]
        ))

        checkpoint_path = manager.write_checkpoint(state, "research-complete")

        with open(checkpoint_path) as f:
            data = json.load(f)

        assert data["phase"] == "research-complete"
        assert data["state"]["phase_statuses"]["research"] == "completed"

    def test_checkpoint_stored_in_rlm_act_checkpoints_dir(self, tmp_path):
        """Given project path, creates .rlm-act-checkpoints/."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState()

        checkpoint_path = manager.write_checkpoint(state, "test")

        assert ".rlm-act-checkpoints" in checkpoint_path
        assert (tmp_path / ".rlm-act-checkpoints").is_dir()
```

### 🟢 Green: Implement Write Checkpoint

**File**: `silmari-rlm-act/checkpoints/manager.py`
```python
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from silmari_rlm_act.models import PipelineState


class CheckpointManager:
    """Manages pipeline checkpoint files."""

    CHECKPOINTS_DIR = ".rlm-act-checkpoints"

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self.checkpoints_dir = self.project_path / self.CHECKPOINTS_DIR

    def write_checkpoint(
        self,
        state: PipelineState,
        phase: str,
        errors: Optional[list[str]] = None
    ) -> str:
        """Write checkpoint file for current state.

        Args:
            state: Current pipeline state
            phase: Phase name (e.g., "research-complete")
            errors: Optional error messages

        Returns:
            Path to created checkpoint file
        """
        self.checkpoints_dir.mkdir(exist_ok=True)

        checkpoint_id = str(uuid.uuid4())
        checkpoint_file = self.checkpoints_dir / f"{checkpoint_id}.json"

        data = {
            "id": checkpoint_id,
            "phase": phase,
            "timestamp": datetime.now().isoformat() + "Z",
            "state": state.to_checkpoint_dict(),
            "errors": errors or [],
        }

        with open(checkpoint_file, "w") as f:
            json.dump(data, f, indent=2)

        return str(checkpoint_file)
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_checkpoint_manager.py::TestWriteCheckpoint -v`

---

## TDD Cycle: Behavior 2 - Detect Resumable Checkpoint

### Test Specification
**Given**: Multiple checkpoint files
**When**: Calling detect_resumable_checkpoint()
**Then**: Returns most recent checkpoint data

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_checkpoint_manager.py`
```python
import time


class TestDetectResumableCheckpoint:
    """Behavior 2: Detect Resumable Checkpoint."""

    def test_returns_none_when_no_checkpoints(self, tmp_path):
        """Given no checkpoints, returns None."""
        manager = CheckpointManager(tmp_path)

        checkpoint = manager.detect_resumable_checkpoint()

        assert checkpoint is None

    def test_returns_most_recent_checkpoint(self, tmp_path):
        """Given multiple checkpoints, returns newest."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState()

        # Create older checkpoint
        manager.write_checkpoint(state, "research-complete")
        time.sleep(0.1)  # Ensure different timestamps

        # Create newer checkpoint
        state.complete_phase("decomposition", PhaseResult(phase="decomposition", success=True))
        manager.write_checkpoint(state, "decomposition-complete")

        checkpoint = manager.detect_resumable_checkpoint()

        assert checkpoint is not None
        assert checkpoint["phase"] == "decomposition-complete"

    def test_checkpoint_includes_file_path(self, tmp_path):
        """Given checkpoint, includes file_path key."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState()
        manager.write_checkpoint(state, "test")

        checkpoint = manager.detect_resumable_checkpoint()

        assert "file_path" in checkpoint
        assert Path(checkpoint["file_path"]).exists()
```

### 🟢 Green: Implement Detection

**File**: `silmari-rlm-act/checkpoints/manager.py`
```python
class CheckpointManager:
    # ... existing methods ...

    def detect_resumable_checkpoint(self) -> Optional[dict]:
        """Find most recent checkpoint.

        Returns:
            Checkpoint data dict or None if no checkpoints exist.
        """
        if not self.checkpoints_dir.exists():
            return None

        checkpoints = []
        for f in self.checkpoints_dir.glob("*.json"):
            try:
                with open(f) as fp:
                    data = json.load(fp)
                    data["file_path"] = str(f)
                    checkpoints.append(data)
            except (json.JSONDecodeError, IOError):
                continue

        if not checkpoints:
            return None

        # Sort by timestamp descending
        checkpoints.sort(key=lambda c: c.get("timestamp", ""), reverse=True)
        return checkpoints[0]
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_checkpoint_manager.py::TestDetectResumableCheckpoint -v`

---

## TDD Cycle: Behavior 3 - Checkpoint Age Calculation

### Test Specification
**Given**: Checkpoint from 5 days ago
**When**: Calling get_checkpoint_age_days(checkpoint)
**Then**: Returns 5

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_checkpoint_manager.py`
```python
from datetime import datetime, timedelta


class TestCheckpointAge:
    """Behavior 3: Checkpoint Age Calculation."""

    def test_returns_zero_for_today(self, tmp_path):
        """Given checkpoint from today, returns 0."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState()
        manager.write_checkpoint(state, "test")

        checkpoint = manager.detect_resumable_checkpoint()
        age = manager.get_checkpoint_age_days(checkpoint)

        assert age == 0

    def test_calculates_age_in_days(self, tmp_path):
        """Given old timestamp, returns correct age."""
        manager = CheckpointManager(tmp_path)

        # Create checkpoint with old timestamp
        old_timestamp = (datetime.now() - timedelta(days=5)).isoformat() + "Z"
        checkpoint = {"timestamp": old_timestamp}

        age = manager.get_checkpoint_age_days(checkpoint)

        assert age == 5

    def test_handles_missing_timestamp(self, tmp_path):
        """Given no timestamp, returns 0."""
        manager = CheckpointManager(tmp_path)

        age = manager.get_checkpoint_age_days({})

        assert age == 0
```

### 🟢 Green: Implement Age Calculation

**File**: `silmari-rlm-act/checkpoints/manager.py`
```python
class CheckpointManager:
    # ... existing methods ...

    def get_checkpoint_age_days(self, checkpoint: dict) -> int:
        """Calculate age of checkpoint in days.

        Args:
            checkpoint: Checkpoint dict with 'timestamp' key

        Returns:
            Age in days (0 if today or missing timestamp)
        """
        timestamp_str = checkpoint.get("timestamp", "")
        if not timestamp_str:
            return 0

        try:
            # Handle ISO format with Z suffix
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"
            checkpoint_time = datetime.fromisoformat(timestamp_str)
            age = datetime.now(checkpoint_time.tzinfo) - checkpoint_time
            return age.days
        except (ValueError, TypeError):
            return 0
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_checkpoint_manager.py::TestCheckpointAge -v`

---

## TDD Cycle: Behavior 4-6 - Delete and Cleanup

### 🔴 Red: Write Failing Tests

**File**: `silmari-rlm-act/tests/test_checkpoint_manager.py`
```python
class TestDeleteCheckpoint:
    """Behavior 4: Delete Single Checkpoint."""

    def test_deletes_checkpoint_file(self, tmp_path):
        """Given checkpoint path, deletes file."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState()
        checkpoint_path = manager.write_checkpoint(state, "test")

        result = manager.delete_checkpoint(checkpoint_path)

        assert result is True
        assert not Path(checkpoint_path).exists()

    def test_returns_false_for_nonexistent(self, tmp_path):
        """Given nonexistent path, returns False."""
        manager = CheckpointManager(tmp_path)

        result = manager.delete_checkpoint("/nonexistent/path.json")

        assert result is False


class TestCleanupByAge:
    """Behavior 5: Cleanup by Age."""

    def test_deletes_old_checkpoints(self, tmp_path):
        """Given checkpoints older than N days, deletes them."""
        manager = CheckpointManager(tmp_path)
        manager.checkpoints_dir.mkdir()

        # Create old checkpoint manually
        old_checkpoint = manager.checkpoints_dir / "old.json"
        old_timestamp = (datetime.now() - timedelta(days=10)).isoformat() + "Z"
        old_checkpoint.write_text(json.dumps({
            "id": "old",
            "timestamp": old_timestamp,
            "phase": "test"
        }))

        # Create new checkpoint
        state = PipelineState()
        new_path = manager.write_checkpoint(state, "new")

        deleted, failed = manager.cleanup_by_age(days=7)

        assert deleted == 1
        assert failed == 0
        assert not old_checkpoint.exists()
        assert Path(new_path).exists()


class TestCleanupAll:
    """Behavior 6: Cleanup All Checkpoints."""

    def test_deletes_all_checkpoints(self, tmp_path):
        """Given multiple checkpoints, deletes all."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState()

        manager.write_checkpoint(state, "test1")
        manager.write_checkpoint(state, "test2")

        deleted, failed = manager.cleanup_all()

        assert deleted == 2
        assert failed == 0
        assert len(list(manager.checkpoints_dir.glob("*.json"))) == 0
```

### 🟢 Green: Implement Delete and Cleanup

**File**: `silmari-rlm-act/checkpoints/manager.py`
```python
class CheckpointManager:
    # ... existing methods ...

    def delete_checkpoint(self, checkpoint_path: str) -> bool:
        """Delete a single checkpoint file."""
        try:
            Path(checkpoint_path).unlink()
            return True
        except (IOError, OSError):
            return False

    def cleanup_by_age(self, days: int) -> tuple[int, int]:
        """Delete checkpoints older than specified days.

        Returns:
            Tuple of (deleted_count, failed_count)
        """
        if not self.checkpoints_dir.exists():
            return 0, 0

        deleted = 0
        failed = 0

        for f in self.checkpoints_dir.glob("*.json"):
            try:
                with open(f) as fp:
                    data = json.load(fp)
                age = self.get_checkpoint_age_days(data)
                if age >= days:
                    if self.delete_checkpoint(str(f)):
                        deleted += 1
                    else:
                        failed += 1
            except (json.JSONDecodeError, IOError):
                continue

        return deleted, failed

    def cleanup_all(self) -> tuple[int, int]:
        """Delete all checkpoint files."""
        if not self.checkpoints_dir.exists():
            return 0, 0

        deleted = 0
        failed = 0

        for f in self.checkpoints_dir.glob("*.json"):
            try:
                f.unlink()
                deleted += 1
            except (IOError, OSError):
                failed += 1

        return deleted, failed
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_checkpoint_manager.py::TestDeleteCheckpoint -v`
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_checkpoint_manager.py::TestCleanupByAge -v`
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_checkpoint_manager.py::TestCleanupAll -v`

---

## TDD Cycle: Behavior 7 - Git Commit in Checkpoint

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_checkpoint_manager.py`
```python
class TestCheckpointGitCommit:
    """Behavior 7: Checkpoint Includes Git Commit."""

    def test_includes_git_commit_hash(self, tmp_path):
        """Given git repo, checkpoint includes commit hash."""
        # Initialize git repo
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
        (tmp_path / "test.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True)

        manager = CheckpointManager(tmp_path)
        state = PipelineState()
        checkpoint_path = manager.write_checkpoint(state, "test")

        with open(checkpoint_path) as f:
            data = json.load(f)

        assert "git_commit" in data
        assert len(data["git_commit"]) == 40  # SHA-1 hash length
```

### 🟢 Green: Add Git Commit to Checkpoint

**File**: `silmari-rlm-act/checkpoints/manager.py`
```python
import subprocess


class CheckpointManager:
    # ... existing methods ...

    def _get_git_commit(self) -> str:
        """Get current git commit hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(self.project_path)
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except Exception:
            return ""

    def write_checkpoint(
        self,
        state: PipelineState,
        phase: str,
        errors: Optional[list[str]] = None
    ) -> str:
        # ... existing code ...

        data = {
            "id": checkpoint_id,
            "phase": phase,
            "timestamp": datetime.now().isoformat() + "Z",
            "state": state.to_checkpoint_dict(),
            "errors": errors or [],
            "git_commit": self._get_git_commit(),  # Add git commit
        }

        # ... rest of method ...
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_checkpoint_manager.py::TestCheckpointGitCommit -v`

---

## TDD Cycle: Behavior 8-10 - CWA Entry IDs and Load

### 🔴 Red: Write Failing Tests

**File**: `silmari-rlm-act/tests/test_checkpoint_manager.py`
```python
class TestCheckpointCWAEntries:
    """Behavior 8: Checkpoint Includes CWA Entry IDs."""

    def test_includes_context_entry_ids(self, tmp_path):
        """Given state with entries, checkpoint includes them."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState()
        state.track_entry("research", "ctx_001")
        state.track_entry("research", "ctx_002")

        checkpoint_path = manager.write_checkpoint(state, "test")

        with open(checkpoint_path) as f:
            data = json.load(f)

        assert data["state"]["context_entry_ids"]["research"] == ["ctx_001", "ctx_002"]


class TestLoadCheckpoint:
    """Behavior 9: Load Checkpoint Returns PipelineState."""

    def test_load_returns_pipeline_state(self, tmp_path):
        """Given checkpoint file, load returns PipelineState."""
        manager = CheckpointManager(tmp_path)
        state = PipelineState()
        state.complete_phase("research", PhaseResult(phase="research", success=True))
        state.track_entry("research", "ctx_001")
        checkpoint_path = manager.write_checkpoint(state, "test")

        loaded_state = manager.load_checkpoint(checkpoint_path)

        assert isinstance(loaded_state, PipelineState)
        assert loaded_state.get_phase_status("research") == PhaseStatus.COMPLETED
        assert loaded_state.get_phase_entries("research") == ["ctx_001"]


class TestCheckpointNaming:
    """Behavior 10: Checkpoint Naming Convention."""

    def test_filename_is_uuid(self, tmp_path):
        """Given checkpoint, filename is UUID."""
        import re
        manager = CheckpointManager(tmp_path)
        state = PipelineState()

        checkpoint_path = manager.write_checkpoint(state, "test")
        filename = Path(checkpoint_path).stem

        # UUID pattern
        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        assert re.match(uuid_pattern, filename)
```

### 🟢 Green: Implement Load

**File**: `silmari-rlm-act/checkpoints/manager.py`
```python
class CheckpointManager:
    # ... existing methods ...

    def load_checkpoint(self, checkpoint_path: str) -> PipelineState:
        """Load PipelineState from checkpoint file.

        Args:
            checkpoint_path: Path to checkpoint JSON file

        Returns:
            Restored PipelineState

        Raises:
            FileNotFoundError: If checkpoint doesn't exist
            json.JSONDecodeError: If checkpoint is invalid
        """
        with open(checkpoint_path) as f:
            data = json.load(f)

        return PipelineState.from_checkpoint_dict(data["state"])
```

### Success Criteria
**Automated:**
- [ ] All checkpoint manager tests pass: `pytest silmari-rlm-act/tests/test_checkpoint_manager.py -v`

**Manual:**
- [ ] Can create, detect, and load checkpoints
- [ ] Cleanup operations work correctly

## Summary

This phase implements the `CheckpointManager` class with:
- Write checkpoint to `.rlm-act-checkpoints/UUID.json`
- Detect most recent checkpoint
- Calculate checkpoint age
- Delete and cleanup operations
- Git commit tracking
- CWA entry ID preservation
- Load checkpoint to PipelineState
