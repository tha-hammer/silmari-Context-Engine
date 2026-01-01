"""Tests for checkpoint management functions."""

import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta

from planning_pipeline.checkpoint_manager import (
    detect_resumable_checkpoint,
    get_checkpoint_age_days,
    check_checkpoint_cleanup_needed,
    write_checkpoint,
    delete_checkpoint,
    cleanup_checkpoints_by_age,
    cleanup_all_checkpoints,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with checkpoints dir."""
    checkpoints_dir = tmp_path / ".workflow-checkpoints"
    checkpoints_dir.mkdir()
    return tmp_path


def test_detect_resumable_checkpoint_no_dir(tmp_path):
    """No checkpoints dir returns None."""
    assert detect_resumable_checkpoint(tmp_path) is None


def test_detect_resumable_checkpoint_empty(temp_project):
    """Empty checkpoints dir returns None."""
    # Dir exists but is empty
    assert detect_resumable_checkpoint(temp_project) is None


def test_detect_resumable_checkpoint_finds_latest(temp_project):
    """Finds most recent checkpoint."""
    checkpoints_dir = temp_project / ".workflow-checkpoints"

    # Create older checkpoint
    old = {
        "id": "old-id",
        "phase": "research-failed",
        "timestamp": "2025-12-30T10:00:00Z",
        "state_snapshot": {"artifacts": ["/old/path.md"]}
    }
    (checkpoints_dir / "old.json").write_text(json.dumps(old))

    # Create newer checkpoint
    new = {
        "id": "new-id",
        "phase": "planning-failed",
        "timestamp": "2025-12-31T10:00:00Z",
        "state_snapshot": {"artifacts": ["/new/path.md"]}
    }
    (checkpoints_dir / "new.json").write_text(json.dumps(new))

    result = detect_resumable_checkpoint(temp_project)
    assert result["id"] == "new-id"
    assert result["phase"] == "planning-failed"
    assert "file_path" in result


def test_detect_resumable_checkpoint_ignores_invalid_json(temp_project):
    """Invalid JSON files are skipped."""
    checkpoints_dir = temp_project / ".workflow-checkpoints"

    # Create invalid JSON
    (checkpoints_dir / "invalid.json").write_text("not valid json {")

    # Create valid checkpoint
    valid = {
        "id": "valid-id",
        "phase": "planning-failed",
        "timestamp": "2025-12-31T10:00:00Z",
        "state_snapshot": {"artifacts": []}
    }
    (checkpoints_dir / "valid.json").write_text(json.dumps(valid))

    result = detect_resumable_checkpoint(temp_project)
    assert result["id"] == "valid-id"


def test_write_checkpoint_creates_file(temp_project):
    """write_checkpoint creates valid JSON file."""
    path = write_checkpoint(
        temp_project,
        "planning-failed",
        ["/abs/path/research.md"]
    )

    assert Path(path).exists()
    data = json.loads(Path(path).read_text())
    assert data["phase"] == "planning-failed"
    assert "/abs/path/research.md" in data["state_snapshot"]["artifacts"]
    assert "id" in data
    assert "timestamp" in data


def test_write_checkpoint_with_errors(temp_project):
    """write_checkpoint includes errors."""
    path = write_checkpoint(
        temp_project,
        "research-failed",
        [],
        ["Error 1", "Error 2"]
    )

    data = json.loads(Path(path).read_text())
    assert data["state_snapshot"]["errors"] == ["Error 1", "Error 2"]


def test_write_checkpoint_creates_dir(tmp_path):
    """write_checkpoint creates checkpoints dir if missing."""
    assert not (tmp_path / ".workflow-checkpoints").exists()

    path = write_checkpoint(tmp_path, "test-failed", [])

    assert Path(path).exists()
    assert (tmp_path / ".workflow-checkpoints").exists()


def test_get_checkpoint_age_days_today():
    """Checkpoint from today has age 0."""
    now = datetime.now()
    checkpoint = {"timestamp": now.isoformat() + "Z"}
    age = get_checkpoint_age_days(checkpoint)
    assert age == 0


def test_get_checkpoint_age_days_yesterday():
    """Checkpoint from yesterday has age 1."""
    yesterday = datetime.now() - timedelta(days=1)
    checkpoint = {"timestamp": yesterday.isoformat() + "Z"}
    age = get_checkpoint_age_days(checkpoint)
    assert age == 1


def test_get_checkpoint_age_days_old():
    """Checkpoint from 30 days ago has age 30."""
    old = datetime.now() - timedelta(days=30)
    checkpoint = {"timestamp": old.isoformat() + "Z"}
    age = get_checkpoint_age_days(checkpoint)
    assert age == 30


def test_get_checkpoint_age_days_no_timestamp():
    """Missing timestamp returns 0."""
    checkpoint = {}
    age = get_checkpoint_age_days(checkpoint)
    assert age == 0


def test_get_checkpoint_age_days_invalid_timestamp():
    """Invalid timestamp returns 0."""
    checkpoint = {"timestamp": "not-a-date"}
    age = get_checkpoint_age_days(checkpoint)
    assert age == 0


def test_check_checkpoint_cleanup_needed_no_dir(tmp_path):
    """No checkpoints dir returns no warning."""
    should_warn, checkpoints = check_checkpoint_cleanup_needed(tmp_path)
    assert not should_warn
    assert checkpoints == []


def test_check_checkpoint_cleanup_needed_recent(temp_project):
    """Recent checkpoints don't trigger warning."""
    checkpoints_dir = temp_project / ".workflow-checkpoints"
    recent = {
        "id": "recent",
        "timestamp": datetime.now().isoformat() + "Z",
        "state_snapshot": {}
    }
    (checkpoints_dir / "recent.json").write_text(json.dumps(recent))

    should_warn, checkpoints = check_checkpoint_cleanup_needed(temp_project)
    assert not should_warn
    assert len(checkpoints) == 1


def test_check_checkpoint_cleanup_needed_old(temp_project):
    """Old checkpoints trigger warning."""
    checkpoints_dir = temp_project / ".workflow-checkpoints"
    old_date = datetime.now() - timedelta(days=35)
    old = {
        "id": "old",
        "timestamp": old_date.isoformat() + "Z",
        "state_snapshot": {}
    }
    (checkpoints_dir / "old.json").write_text(json.dumps(old))

    should_warn, checkpoints = check_checkpoint_cleanup_needed(temp_project)
    assert should_warn
    assert len(checkpoints) == 1
    assert checkpoints[0]["age_days"] >= 30


def test_delete_checkpoint(temp_project):
    """delete_checkpoint removes file."""
    checkpoints_dir = temp_project / ".workflow-checkpoints"
    file_path = checkpoints_dir / "test.json"
    file_path.write_text("{}")

    assert file_path.exists()
    result = delete_checkpoint(str(file_path))
    assert result is True
    assert not file_path.exists()


def test_delete_checkpoint_nonexistent(temp_project):
    """delete_checkpoint returns False for missing file."""
    result = delete_checkpoint(str(temp_project / "nonexistent.json"))
    assert result is False


def test_cleanup_checkpoints_by_age(temp_project):
    """cleanup_checkpoints_by_age deletes old checkpoints."""
    checkpoints_dir = temp_project / ".workflow-checkpoints"

    # Create files with age info
    old_file = checkpoints_dir / "old.json"
    old_file.write_text("{}")
    new_file = checkpoints_dir / "new.json"
    new_file.write_text("{}")

    checkpoints = [
        {"file_path": str(old_file), "age_days": 40},
        {"file_path": str(new_file), "age_days": 5}
    ]

    deleted, failed = cleanup_checkpoints_by_age(checkpoints, 30)

    assert deleted == 1
    assert failed == 0
    assert not old_file.exists()
    assert new_file.exists()


def test_cleanup_all_checkpoints(temp_project):
    """cleanup_all_checkpoints removes all files."""
    checkpoints_dir = temp_project / ".workflow-checkpoints"

    # Create multiple files
    (checkpoints_dir / "a.json").write_text("{}")
    (checkpoints_dir / "b.json").write_text("{}")
    (checkpoints_dir / "c.json").write_text("{}")

    deleted, failed = cleanup_all_checkpoints(temp_project)

    assert deleted == 3
    assert failed == 0
    assert list(checkpoints_dir.glob("*.json")) == []


def test_cleanup_all_checkpoints_no_dir(tmp_path):
    """cleanup_all_checkpoints handles missing dir."""
    deleted, failed = cleanup_all_checkpoints(tmp_path)
    assert deleted == 0
    assert failed == 0
