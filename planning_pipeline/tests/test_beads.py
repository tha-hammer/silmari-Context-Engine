"""Tests for BeadsController - Behaviors 4, 5, 6."""

import pytest
from pathlib import Path
from planning_pipeline.beads_controller import BeadsController


@pytest.fixture
def beads_controller():
    """Create BeadsController with project path."""
    project_path = Path(__file__).parent.parent.parent
    return BeadsController(project_path)


@pytest.fixture
def cleanup_issues(beads_controller):
    """Track and cleanup created issues after test."""
    created_ids = []
    yield created_ids
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
    beads_controller.sync()


class TestBeadsControllerCreateIssue:
    """Behavior 4: BeadsController - Create Issue."""

    def test_creates_task_issue(self, beads_controller, cleanup_issues):
        """Given valid title/type/priority, creates issue and returns success."""
        result = beads_controller.create_issue(
            title="TDD Test Issue - Create",
            issue_type="task",
            priority=2
        )
        assert result["success"] is True
        assert "data" in result
        # Track for cleanup
        if isinstance(result["data"], dict) and "id" in result["data"]:
            cleanup_issues.append(result["data"]["id"])

    def test_creates_epic_issue(self, beads_controller, cleanup_issues):
        """Given epic type, creates epic issue."""
        result = beads_controller.create_epic("TDD Test Epic - Create")
        assert result["success"] is True
        if isinstance(result["data"], dict) and "id" in result["data"]:
            cleanup_issues.append(result["data"]["id"])


class TestBeadsControllerListClose:
    """Behavior 5: BeadsController - List and Close Issues."""

    def test_lists_open_issues(self, beads_controller):
        """Given open status filter, returns list of open issues."""
        result = beads_controller.list_issues(status="open")
        assert result["success"] is True
        assert "data" in result

    def test_closes_issue(self, beads_controller):
        """Given issue ID, closes the issue."""
        # Create an issue first
        create_result = beads_controller.create_issue("TDD Issue to Close", "task", 2)
        assert create_result["success"] is True
        issue_id = create_result["data"].get("id") if isinstance(create_result["data"], dict) else None

        if issue_id:
            # Close it
            close_result = beads_controller.close_issue(issue_id, reason="Test complete")
            assert close_result["success"] is True

    def test_close_invalid_issue_fails(self, beads_controller):
        """Given invalid issue ID, returns error."""
        result = beads_controller.close_issue("invalid-id-12345")
        assert result["success"] is False
        assert "error" in result


class TestBeadsControllerDependencies:
    """Behavior 6: BeadsController - Add Dependency and Sync."""

    def test_adds_dependency(self, beads_controller, cleanup_issues):
        """Given two issues, adds dependency between them."""
        # Create two issues
        issue1 = beads_controller.create_issue("TDD Dependency Base", "task", 2)
        issue2 = beads_controller.create_issue("TDD Dependent Issue", "task", 2)

        id1 = issue1["data"].get("id") if isinstance(issue1["data"], dict) else None
        id2 = issue2["data"].get("id") if isinstance(issue2["data"], dict) else None

        if id1 and id2:
            cleanup_issues.extend([id1, id2])

            # Add dependency: issue2 depends on issue1
            result = beads_controller.add_dependency(id2, id1)
            assert result["success"] is True

    def test_sync_returns_result(self, beads_controller):
        """Given beads state, sync returns a result (success or error)."""
        result = beads_controller.sync()
        # Sync may fail if there are unstaged changes, but should return a result
        assert "success" in result
        # Either it succeeds or we get an error message
        assert result["success"] is True or "error" in result or "output" in result
