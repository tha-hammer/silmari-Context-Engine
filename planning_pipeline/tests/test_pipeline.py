"""Tests for the full pipeline - Behavior 14."""

import pytest
from pathlib import Path
from planning_pipeline.pipeline import PlanningPipeline
from planning_pipeline.beads_controller import BeadsController


@pytest.fixture
def project_path():
    """Return the root project path."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def beads_controller(project_path):
    """Create BeadsController with project path."""
    return BeadsController(project_path)


@pytest.fixture
def cleanup_issues(beads_controller):
    """Track and cleanup created issues after test."""
    created_ids = []
    yield created_ids
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
    beads_controller.sync()


class TestPipelineInit:
    """Test PlanningPipeline initialization."""

    def test_creates_pipeline_with_project_path(self, project_path):
        """Given project path, creates pipeline instance."""
        pipeline = PlanningPipeline(project_path)
        assert pipeline.project_path == project_path.resolve()

    def test_has_beads_controller(self, project_path):
        """Given project path, pipeline has beads controller."""
        pipeline = PlanningPipeline(project_path)
        assert pipeline.beads is not None


# Note: Full E2E tests are commented out as they require actual Claude calls
# and take significant time. Uncomment for integration testing.

# class TestPipelineE2E:
#     """Behavior 14: Full Pipeline E2E."""
#
#     @pytest.mark.slow
#     @pytest.mark.e2e
#     def test_full_pipeline_with_auto_approve(self, project_path, cleanup_issues):
#         """Given research prompt with auto-approve, runs complete pipeline."""
#         pipeline = PlanningPipeline(project_path)
#
#         result = pipeline.run(
#             research_prompt="What is the main purpose of this project? Brief answer.",
#             ticket_id="TEST-001",
#             auto_approve=True
#         )
#
#         assert result["success"] is True
#         assert "plan_dir" in result
#         assert result.get("epic_id") is not None
#
#         # Cleanup
#         if result.get("epic_id"):
#             cleanup_issues.append(result["epic_id"])
#         for pi in result.get("steps", {}).get("beads", {}).get("phase_issues", []):
#             if pi.get("issue_id"):
#                 cleanup_issues.append(pi["issue_id"])
