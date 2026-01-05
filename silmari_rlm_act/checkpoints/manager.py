"""Checkpoint management for pipeline resume functionality.

This module provides the CheckpointManager class for:
- Writing pipeline state to checkpoint files
- Detecting and loading resumable checkpoints
- Cleanup operations (by age or all)
- Git commit tracking in checkpoints
"""

import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from silmari_rlm_act.models import PipelineState


class CheckpointManager:
    """Manages pipeline checkpoint files for resume functionality.

    Checkpoints are stored as JSON files in `.rlm-act-checkpoints/` directory.
    Each checkpoint contains:
    - Unique ID (UUID)
    - Phase name (e.g., "research-complete")
    - Timestamp
    - Full pipeline state
    - Git commit hash (if available)
    - Error messages (if any)

    Attributes:
        project_path: Root directory of the project
        checkpoints_dir: Path to checkpoint storage directory
    """

    CHECKPOINTS_DIR = ".rlm-act-checkpoints"

    def __init__(self, project_path: Path) -> None:
        """Initialize CheckpointManager.

        Args:
            project_path: Root directory of the project
        """
        self.project_path = Path(project_path).resolve()
        self.checkpoints_dir = self.project_path / self.CHECKPOINTS_DIR

    def write_checkpoint(
        self,
        state: PipelineState,
        phase: str,
        errors: Optional[list[str]] = None,
    ) -> str:
        """Write checkpoint file for current pipeline state.

        Creates a JSON file in `.rlm-act-checkpoints/` with a UUID filename.
        The checkpoint captures the complete pipeline state for resume.

        Args:
            state: Current pipeline state
            phase: Phase name (e.g., "research-complete", "decomposition-failed")
            errors: Optional list of error messages

        Returns:
            Absolute path to created checkpoint file
        """
        self.checkpoints_dir.mkdir(exist_ok=True)

        checkpoint_id = str(uuid.uuid4())
        checkpoint_file = self.checkpoints_dir / f"{checkpoint_id}.json"

        data: dict[str, Any] = {
            "id": checkpoint_id,
            "phase": phase,
            "timestamp": datetime.now().isoformat() + "Z",
            "state": state.to_checkpoint_dict(),
            "errors": errors or [],
            "git_commit": self._get_git_commit(),
        }

        with open(checkpoint_file, "w") as f:
            json.dump(data, f, indent=2)

        return str(checkpoint_file)

    def detect_resumable_checkpoint(self) -> Optional[dict[str, Any]]:
        """Find most recent checkpoint.

        Scans the checkpoints directory and returns the most recent
        checkpoint based on timestamp.

        Returns:
            Checkpoint data dict with 'file_path' added, or None if no checkpoints exist.
        """
        if not self.checkpoints_dir.exists():
            return None

        checkpoints: list[dict[str, Any]] = []
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

        # Sort by timestamp descending (most recent first)
        checkpoints.sort(key=lambda c: c.get("timestamp", ""), reverse=True)
        return checkpoints[0]

    def get_checkpoint_age_days(self, checkpoint: dict[str, Any]) -> int:
        """Calculate age of checkpoint in days.

        Args:
            checkpoint: Checkpoint dict with 'timestamp' key

        Returns:
            Age in days (0 if today or missing/invalid timestamp)
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

    def delete_checkpoint(self, checkpoint_path: str) -> bool:
        """Delete a single checkpoint file.

        Args:
            checkpoint_path: Absolute path to checkpoint JSON file

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            Path(checkpoint_path).unlink()
            return True
        except (IOError, OSError):
            return False

    def cleanup_by_age(self, days: int) -> tuple[int, int]:
        """Delete checkpoints older than specified days.

        Args:
            days: Delete checkpoints older than this many days

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
        """Delete all checkpoint files.

        Returns:
            Tuple of (deleted_count, failed_count)
        """
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

    def load_checkpoint(self, checkpoint_path: str) -> PipelineState:
        """Load PipelineState from checkpoint file.

        Args:
            checkpoint_path: Path to checkpoint JSON file

        Returns:
            Restored PipelineState

        Raises:
            FileNotFoundError: If checkpoint doesn't exist
            json.JSONDecodeError: If checkpoint is invalid JSON
            KeyError: If checkpoint is missing required fields
        """
        with open(checkpoint_path) as f:
            data = json.load(f)

        return PipelineState.from_checkpoint_dict(data["state"])

    def _get_git_commit(self) -> str:
        """Get current git commit hash.

        Returns:
            40-character SHA-1 hash or empty string if not in git repo
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(self.project_path),
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except Exception:
            return ""
