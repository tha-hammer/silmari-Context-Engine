"""Checkpoint management for pipeline resume functionality."""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional


def detect_resumable_checkpoint(project_path: Path) -> Optional[dict]:
    """Find most recent failed checkpoint.

    Args:
        project_path: Root project directory

    Returns:
        Dict with checkpoint data or None if no checkpoints exist.
        Keys: 'id', 'phase', 'timestamp', 'state_snapshot', 'git_commit', 'file_path'
    """
    checkpoints_dir = project_path / ".workflow-checkpoints"
    if not checkpoints_dir.exists():
        return None

    checkpoints = []
    for f in checkpoints_dir.glob("*.json"):
        try:
            with open(f) as fp:
                data = json.load(fp)
                data["file_path"] = str(f)  # Track source file
                checkpoints.append(data)
        except (json.JSONDecodeError, IOError):
            continue

    if not checkpoints:
        return None

    # Sort by timestamp descending (most recent first)
    checkpoints.sort(key=lambda c: c.get("timestamp", ""), reverse=True)
    return checkpoints[0]


def get_checkpoint_age_days(checkpoint: dict) -> int:
    """Calculate age of checkpoint in days.

    Args:
        checkpoint: Checkpoint dict with 'timestamp' key

    Returns:
        Age in days (0 if today)
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


def check_checkpoint_cleanup_needed(project_path: Path, warn_days: int = 30) -> tuple[bool, list[dict]]:
    """Check if checkpoint cleanup warning should be shown.

    Args:
        project_path: Root project directory
        warn_days: Days after which to warn (default 30)

    Returns:
        Tuple of (should_warn, list of checkpoint dicts with age info)
    """
    checkpoints_dir = project_path / ".workflow-checkpoints"
    if not checkpoints_dir.exists():
        return False, []

    checkpoints = []

    for f in checkpoints_dir.glob("*.json"):
        try:
            with open(f) as fp:
                data = json.load(fp)
                data["file_path"] = str(f)
                age = get_checkpoint_age_days(data)
                data["age_days"] = age
                checkpoints.append(data)
        except (json.JSONDecodeError, IOError):
            continue

    if not checkpoints:
        return False, []

    # Check if any checkpoint exceeds warn_days
    max_age = max(c.get("age_days", 0) for c in checkpoints)
    return max_age >= warn_days, checkpoints


def delete_checkpoint(checkpoint_path: str) -> bool:
    """Delete a single checkpoint file.

    Args:
        checkpoint_path: Absolute path to checkpoint JSON file

    Returns:
        True if deleted successfully
    """
    try:
        Path(checkpoint_path).unlink()
        return True
    except (IOError, OSError):
        return False


def cleanup_checkpoints_by_age(
    checkpoints: list[dict],
    days_to_delete: int
) -> tuple[int, int]:
    """Delete checkpoints older than specified days.

    Args:
        checkpoints: List of checkpoint dicts with 'age_days' and 'file_path'
        days_to_delete: Delete checkpoints older than this many days

    Returns:
        Tuple of (deleted_count, failed_count)
    """
    deleted = 0
    failed = 0

    for cp in checkpoints:
        if cp.get("age_days", 0) >= days_to_delete:
            if delete_checkpoint(cp["file_path"]):
                deleted += 1
            else:
                failed += 1

    return deleted, failed


def cleanup_all_checkpoints(project_path: Path) -> tuple[int, int]:
    """Delete all checkpoint files.

    Args:
        project_path: Root project directory

    Returns:
        Tuple of (deleted_count, failed_count)
    """
    checkpoints_dir = project_path / ".workflow-checkpoints"
    if not checkpoints_dir.exists():
        return 0, 0

    deleted = 0
    failed = 0

    for f in checkpoints_dir.glob("*.json"):
        try:
            f.unlink()
            deleted += 1
        except (IOError, OSError):
            failed += 1

    return deleted, failed


def write_checkpoint(
    project_path: Path,
    phase: str,
    artifacts: list[str],
    errors: Optional[list[str]] = None
) -> str:
    """Write a checkpoint file for failed pipeline state.

    Args:
        project_path: Root project directory
        phase: Phase that failed (e.g., "planning-failed")
        artifacts: List of absolute paths to produced artifacts
        errors: Optional list of error messages

    Returns:
        Path to created checkpoint file
    """
    import uuid
    import subprocess

    checkpoints_dir = project_path / ".workflow-checkpoints"
    checkpoints_dir.mkdir(exist_ok=True)

    checkpoint_id = str(uuid.uuid4())
    checkpoint_file = checkpoints_dir / f"{checkpoint_id}.json"

    # Get current git commit
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(project_path)
        )
        git_commit = result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        git_commit = ""

    data = {
        "id": checkpoint_id,
        "phase": phase,
        "timestamp": datetime.now().isoformat() + "Z",
        "state_snapshot": {
            "phase": phase.replace("-failed", "").title(),
            "context_usage": 0.0,
            "artifacts": artifacts,  # Must be absolute paths
            "errors": errors or []
        },
        "git_commit": git_commit
    }

    with open(checkpoint_file, "w") as fp:
        json.dump(data, fp, indent=2)

    return str(checkpoint_file)
