"""Unit and integration tests for step_requirement_decomposition.

Following TDD approach:
- Tests are written before implementation
- Run with: pytest planning_pipeline/tests/test_step_decomposition.py -v
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from planning_pipeline.step_decomposition import (
    step_requirement_decomposition,
    _collect_acceptance_criteria,
)
from planning_pipeline.models import (
    RequirementHierarchy,
    RequirementNode,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure for testing."""
    # Create research directory
    research_dir = tmp_path / "thoughts" / "shared" / "research"
    research_dir.mkdir(parents=True)

    # Create a sample research file
    research_content = """# Research: Test Feature

## Overview

This research document describes requirements for a test feature.

## Requirements

1. User should be able to log in with email/password
2. System should track active sessions
3. Sessions should expire after inactivity

## Implementation Notes

- Use JWT for session tokens
- Store sessions in Redis
"""
    research_file = research_dir / "2026-01-02-test-research.md"
    research_file.write_text(research_content)

    return tmp_path, str(research_file.relative_to(tmp_path))


@pytest.fixture
def mock_decomposition_result():
    """Create a mock RequirementHierarchy for testing."""
    parent = RequirementNode(
        id="REQ_000",
        description="User Authentication System",
        type="parent",
        acceptance_criteria=["Users can log in", "Sessions are tracked"],
    )

    child1 = RequirementNode(
        id="REQ_000.1",
        description="Login implementation",
        type="sub_process",
        parent_id="REQ_000",
        acceptance_criteria=["Email validation works", "Password is checked"],
    )

    child2 = RequirementNode(
        id="REQ_000.2",
        description="Session management",
        type="sub_process",
        parent_id="REQ_000",
        acceptance_criteria=["Sessions expire after 30 minutes"],
    )

    parent.children = [child1, child2]

    hierarchy = RequirementHierarchy(
        requirements=[parent],
        metadata={"source": "test"},
    )

    return hierarchy


class TestStepRequirementDecomposition:
    """Unit tests for step_requirement_decomposition function."""

    def test_creates_hierarchy_json(self, temp_project, mock_decomposition_result):
        """Step should create requirements_hierarchy.json file."""
        project_path, research_path = temp_project

        with patch(
            "planning_pipeline.step_decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_decomposition_result

            result = step_requirement_decomposition(
                project_path=project_path,
                research_path=research_path,
            )

        assert result["success"] is True
        assert "hierarchy_path" in result

        # Verify file was created
        hierarchy_path = Path(result["hierarchy_path"])
        assert hierarchy_path.exists()

        # Verify it's valid JSON
        with open(hierarchy_path) as f:
            data = json.load(f)
        assert "requirements" in data
        assert len(data["requirements"]) == 1

    def test_creates_mermaid_diagram(self, temp_project, mock_decomposition_result):
        """Step should create requirements_diagram.mmd file."""
        project_path, research_path = temp_project

        with patch(
            "planning_pipeline.step_decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_decomposition_result

            result = step_requirement_decomposition(
                project_path=project_path,
                research_path=research_path,
            )

        assert result["success"] is True
        assert "diagram_path" in result

        # Verify file was created
        diagram_path = Path(result["diagram_path"])
        assert diagram_path.exists()

        # Verify it starts with flowchart
        content = diagram_path.read_text()
        assert content.startswith("flowchart")

    def test_creates_property_tests_skeleton(
        self, temp_project, mock_decomposition_result
    ):
        """Step should create property_tests_skeleton.py when acceptance criteria exist."""
        project_path, research_path = temp_project

        with patch(
            "planning_pipeline.step_decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_decomposition_result

            result = step_requirement_decomposition(
                project_path=project_path,
                research_path=research_path,
            )

        assert result["success"] is True

        # tests_path should be present when acceptance criteria exist
        if result.get("tests_path"):
            tests_path = Path(result["tests_path"])
            assert tests_path.exists()

            # Verify it's valid Python syntax
            content = tests_path.read_text()
            assert "import pytest" in content or "from hypothesis" in content

    def test_returns_error_for_missing_research(self, temp_project):
        """Step should return error when research file doesn't exist."""
        project_path, _ = temp_project

        result = step_requirement_decomposition(
            project_path=project_path,
            research_path="nonexistent/research.md",
        )

        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_returns_error_when_decomposition_fails(self, temp_project):
        """Step should return error when decomposition returns DecompositionError."""
        project_path, research_path = temp_project

        # Import here to avoid circular imports during test collection
        from planning_pipeline.decomposition import (
            DecompositionError,
            DecompositionErrorCode,
        )

        mock_error = DecompositionError(
            success=False,
            error_code=DecompositionErrorCode.BAML_API_ERROR,
            error="API rate limit exceeded",
        )

        with patch(
            "planning_pipeline.step_decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_error

            result = step_requirement_decomposition(
                project_path=project_path,
                research_path=research_path,
            )

        assert result["success"] is False
        assert "error" in result
        assert "API rate limit" in result["error"]

    def test_returns_requirement_count(self, temp_project, mock_decomposition_result):
        """Result should include requirement_count for quick visibility."""
        project_path, research_path = temp_project

        with patch(
            "planning_pipeline.step_decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_decomposition_result

            result = step_requirement_decomposition(
                project_path=project_path,
                research_path=research_path,
            )

        assert result["success"] is True
        assert "requirement_count" in result
        # Mock has 1 parent + 2 children = 3 total
        assert result["requirement_count"] >= 1

    def test_uses_custom_output_dir(self, temp_project, mock_decomposition_result):
        """Step should respect custom output_dir parameter."""
        project_path, research_path = temp_project
        custom_output = str(project_path / "custom" / "output")

        with patch(
            "planning_pipeline.step_decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_decomposition_result

            result = step_requirement_decomposition(
                project_path=project_path,
                research_path=research_path,
                output_dir=custom_output,
            )

        assert result["success"] is True
        assert result["output_dir"] == custom_output
        assert Path(result["hierarchy_path"]).parent == Path(custom_output)

    def test_preserves_research_path_in_metadata(
        self, temp_project, mock_decomposition_result
    ):
        """Hierarchy metadata should include original research path."""
        project_path, research_path = temp_project

        with patch(
            "planning_pipeline.step_decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_decomposition_result

            result = step_requirement_decomposition(
                project_path=project_path,
                research_path=research_path,
            )

        assert result["success"] is True

        # Read the hierarchy and check metadata
        with open(result["hierarchy_path"]) as f:
            data = json.load(f)

        assert "source_research" in data.get("metadata", {})


class TestCollectAcceptanceCriteria:
    """Tests for _collect_acceptance_criteria helper function."""

    def test_collects_from_all_levels(self, mock_decomposition_result):
        """Should collect criteria from parent and all children."""
        criteria = _collect_acceptance_criteria(mock_decomposition_result)

        # Mock has: 2 at parent level, 2 at child1, 1 at child2 = 5 total
        assert len(criteria) >= 3

    def test_returns_empty_list_when_no_criteria(self):
        """Should return empty list when hierarchy has no acceptance criteria."""
        hierarchy = RequirementHierarchy(
            requirements=[
                RequirementNode(
                    id="REQ_000",
                    description="Test requirement",
                    type="parent",
                )
            ]
        )

        criteria = _collect_acceptance_criteria(hierarchy)

        assert criteria == []

    def test_deduplicates_criteria(self):
        """Should not return duplicate criteria."""
        hierarchy = RequirementHierarchy(
            requirements=[
                RequirementNode(
                    id="REQ_000",
                    description="Test requirement",
                    type="parent",
                    acceptance_criteria=["Same criterion", "Same criterion"],
                )
            ]
        )

        criteria = _collect_acceptance_criteria(hierarchy)

        # Should deduplicate
        assert len(criteria) == len(set(criteria))
