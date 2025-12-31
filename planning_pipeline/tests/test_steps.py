"""Tests for pipeline steps - Behaviors 8, 9, 10, 11."""

import pytest
from pathlib import Path
from planning_pipeline.steps import (
    step_research,
    step_planning,
    step_phase_decomposition,
    step_beads_integration
)
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


class TestBeadsIntegration:
    """Behavior 11: Beads Integration Creates Issues.

    Note: This test doesn't require Claude calls, just tests beads integration.
    """

    def test_creates_epic_and_phase_issues(self, project_path, cleanup_issues, beads_controller):
        """Given phase files list and epic title, creates beads issues."""
        # Mock phase files (don't need real files for beads)
        phase_files = [
            "thoughts/shared/plans/2025-01-01-test/01-phase-1-setup.md",
            "thoughts/shared/plans/2025-01-01-test/02-phase-2-impl.md",
        ]

        result = step_beads_integration(
            project_path=project_path,
            phase_files=phase_files,
            epic_title="TDD Test Epic - Beads Integration"
        )

        assert result["success"] is True
        assert "epic_id" in result
        assert "phase_issues" in result
        assert len(result["phase_issues"]) == 2

        # Track for cleanup
        if result.get("epic_id"):
            cleanup_issues.append(result["epic_id"])
        for pi in result.get("phase_issues", []):
            if pi.get("issue_id"):
                cleanup_issues.append(pi["issue_id"])

    def test_creates_dependencies_between_phases(self, project_path, cleanup_issues, beads_controller):
        """Given multiple phase files, creates proper dependencies."""
        phase_files = [
            "thoughts/shared/plans/2025-01-01-test/01-first.md",
            "thoughts/shared/plans/2025-01-01-test/02-second.md",
            "thoughts/shared/plans/2025-01-01-test/03-third.md",
        ]

        result = step_beads_integration(
            project_path=project_path,
            phase_files=phase_files,
            epic_title="TDD Dependency Test Epic"
        )

        assert result["success"] is True
        assert len(result["phase_issues"]) == 3

        # Track for cleanup
        if result.get("epic_id"):
            cleanup_issues.append(result["epic_id"])
        for pi in result.get("phase_issues", []):
            if pi.get("issue_id"):
                cleanup_issues.append(pi["issue_id"])


# Note: The following tests are marked as slow because they actually call Claude.
# They are commented out by default to allow quick test runs.
# Uncomment and run with `pytest -m slow` for integration testing.

# class TestResearchStep:
#     """Behavior 8: Research Step Creates Document."""
#
#     @pytest.mark.slow
#     @pytest.mark.integration
#     def test_creates_research_document(self, project_path):
#         """Given research prompt, creates research document."""
#         result = step_research(
#             project_path=project_path,
#             research_prompt="What testing frameworks are used in this project? Keep response brief."
#         )
#
#         assert result["success"] is True
#         assert "research_path" in result
#         # Note: research_path may be None if Claude doesn't output it in expected format
#
#
# class TestPlanningStep:
#     """Behavior 9: Planning Step Creates Plan."""
#
#     @pytest.mark.slow
#     @pytest.mark.integration
#     def test_creates_plan_document(self, project_path):
#         """Given research path, creates plan document."""
#         # First create research (or use existing)
#         research_result = step_research(
#             project_path=project_path,
#             research_prompt="What is the project structure? Brief answer."
#         )
#
#         if research_result["success"] and research_result.get("research_path"):
#             plan_result = step_planning(
#                 project_path=project_path,
#                 research_path=research_result["research_path"],
#                 additional_context="Create a simple 2-phase plan."
#             )
#
#             assert plan_result["success"] is True
#             assert "plan_path" in plan_result
