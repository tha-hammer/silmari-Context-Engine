"""End-to-end tests for requirement decomposition step.

These tests use real files and (optionally) real BAML API calls to verify
the full decomposition pipeline works correctly.

Run with: pytest planning_pipeline/tests/test_decomposition_e2e.py -v -m e2e
"""

import json
import os
import pytest
from pathlib import Path

from planning_pipeline.step_decomposition import step_requirement_decomposition


@pytest.mark.e2e
@pytest.mark.slow
class TestDecompositionE2E:
    """End-to-end tests for the decomposition step."""

    def test_full_flow_with_mock_research(self, tmp_path):
        """Test full flow with a mock research file (no API calls)."""
        # Create a research directory and file
        research_dir = tmp_path / "thoughts" / "shared" / "research"
        research_dir.mkdir(parents=True)

        research_content = """# Research: User Authentication Feature

## Overview

This document describes requirements for implementing user authentication.

## Functional Requirements

1. **Login System**
   - Users should be able to log in with email and password
   - Form should validate email format
   - Failed logins should show error messages

2. **Session Management**
   - Sessions should be tracked using JWT tokens
   - Sessions should expire after 30 minutes of inactivity
   - Users should be able to log out

3. **Password Recovery**
   - Users should be able to request password reset
   - Reset link should be sent via email
   - Link should expire after 1 hour

## Implementation Notes

- Use bcrypt for password hashing
- Store sessions in Redis for scalability
- Implement rate limiting on login attempts
"""
        research_file = research_dir / "2026-01-02-auth-research.md"
        research_file.write_text(research_content)

        # Run the step with patched BAML
        from unittest.mock import patch, MagicMock
        from planning_pipeline.models import RequirementHierarchy, RequirementNode

        # Create mock hierarchy
        mock_hierarchy = RequirementHierarchy(
            requirements=[
                RequirementNode(
                    id="REQ_000",
                    description="User login with email and password",
                    type="parent",
                    acceptance_criteria=[
                        "Form validates email format",
                        "Failed logins show errors",
                    ],
                    children=[
                        RequirementNode(
                            id="REQ_000.1",
                            description="Email validation",
                            type="sub_process",
                            parent_id="REQ_000",
                            acceptance_criteria=["Email format is validated"],
                        ),
                    ],
                ),
                RequirementNode(
                    id="REQ_001",
                    description="Session management with JWT",
                    type="parent",
                    acceptance_criteria=["Sessions expire after 30 minutes"],
                ),
            ],
            metadata={"source": "test"},
        )

        with patch(
            "planning_pipeline.step_decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_hierarchy

            result = step_requirement_decomposition(
                project_path=tmp_path,
                research_path="thoughts/shared/research/2026-01-02-auth-research.md",
            )

        # Verify success
        assert result["success"] is True
        assert result["requirement_count"] >= 2

        # Verify hierarchy file
        hierarchy_path = Path(result["hierarchy_path"])
        assert hierarchy_path.exists()
        with open(hierarchy_path) as f:
            data = json.load(f)
        assert len(data["requirements"]) == 2
        assert data["metadata"]["source_research"] == "thoughts/shared/research/2026-01-02-auth-research.md"

        # Verify diagram file
        diagram_path = Path(result["diagram_path"])
        assert diagram_path.exists()
        content = diagram_path.read_text()
        assert content.startswith("flowchart")
        assert "REQ_000" in content

        # Verify test skeleton (if created)
        if result.get("tests_path"):
            tests_path = Path(result["tests_path"])
            assert tests_path.exists()
            content = tests_path.read_text()
            assert "hypothesis" in content.lower()

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    )
    def test_full_flow_with_real_research(self, tmp_path):
        """Test full flow with real BAML API call.

        This test makes actual API calls and requires ANTHROPIC_API_KEY.
        Run with: pytest -m e2e -k real_research
        """
        # Create research file
        research_dir = tmp_path / "thoughts" / "shared" / "research"
        research_dir.mkdir(parents=True)

        research_content = """# Research: Simple Counter Feature

## Overview

Implement a basic counter component.

## Requirements

1. Counter should display current count
2. User can increment the count
3. User can decrement the count
4. Count cannot go below zero
"""
        research_file = research_dir / "2026-01-02-counter-research.md"
        research_file.write_text(research_content)

        result = step_requirement_decomposition(
            project_path=tmp_path,
            research_path="thoughts/shared/research/2026-01-02-counter-research.md",
        )

        # With real API, should succeed or fail with known error
        if result["success"]:
            assert "hierarchy_path" in result
            assert "diagram_path" in result

            # Verify files exist and have content
            hierarchy_path = Path(result["hierarchy_path"])
            assert hierarchy_path.exists()

            with open(hierarchy_path) as f:
                data = json.load(f)
            assert "requirements" in data
            assert len(data["requirements"]) >= 1
        else:
            # BAML unavailable or API error is acceptable
            assert "error" in result


@pytest.mark.e2e
class TestDecompositionOutputStructure:
    """Tests verifying the output file structure."""

    def test_output_directory_structure(self, tmp_path):
        """Verify correct output directory structure is created."""
        from unittest.mock import patch
        from planning_pipeline.models import RequirementHierarchy, RequirementNode

        # Set up research file
        research_dir = tmp_path / "thoughts" / "shared" / "research"
        research_dir.mkdir(parents=True)
        (research_dir / "test.md").write_text("# Test Research")

        mock_hierarchy = RequirementHierarchy(
            requirements=[
                RequirementNode(
                    id="REQ_000",
                    description="Test requirement",
                    type="parent",
                )
            ]
        )

        with patch(
            "planning_pipeline.step_decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_hierarchy

            result = step_requirement_decomposition(
                project_path=tmp_path,
                research_path="thoughts/shared/research/test.md",
            )

        assert result["success"] is True

        output_dir = Path(result["output_dir"])

        # Check expected files exist
        assert (output_dir / "requirements_hierarchy.json").exists()
        assert (output_dir / "requirements_diagram.mmd").exists()

        # Check output_dir follows expected pattern
        assert "requirements" in output_dir.name

    def test_json_is_valid_and_complete(self, tmp_path):
        """Verify JSON output is valid and contains all expected fields."""
        from unittest.mock import patch
        from planning_pipeline.models import (
            RequirementHierarchy,
            RequirementNode,
            ImplementationComponents,
        )

        research_dir = tmp_path / "thoughts" / "shared" / "research"
        research_dir.mkdir(parents=True)
        (research_dir / "test.md").write_text("# Test Research")

        mock_hierarchy = RequirementHierarchy(
            requirements=[
                RequirementNode(
                    id="REQ_000",
                    description="Parent requirement",
                    type="parent",
                    acceptance_criteria=["AC1", "AC2"],
                    children=[
                        RequirementNode(
                            id="REQ_000.1",
                            description="Child requirement",
                            type="sub_process",
                            parent_id="REQ_000",
                            implementation=ImplementationComponents(
                                frontend=["ComponentA"],
                                backend=["ServiceB.method"],
                            ),
                        )
                    ],
                )
            ],
            metadata={"original_key": "value"},
        )

        with patch(
            "planning_pipeline.step_decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_hierarchy

            result = step_requirement_decomposition(
                project_path=tmp_path,
                research_path="thoughts/shared/research/test.md",
            )

        with open(result["hierarchy_path"]) as f:
            data = json.load(f)

        # Verify structure
        assert "requirements" in data
        assert "metadata" in data

        # Verify metadata
        assert "source_research" in data["metadata"]
        assert "decomposed_at" in data["metadata"]

        # Verify requirement structure
        req = data["requirements"][0]
        assert req["id"] == "REQ_000"
        assert req["description"] == "Parent requirement"
        assert req["type"] == "parent"
        assert "acceptance_criteria" in req
        assert "children" in req

        # Verify child
        child = req["children"][0]
        assert child["id"] == "REQ_000.1"
        assert child["parent_id"] == "REQ_000"
        assert child["implementation"]["frontend"] == ["ComponentA"]

    def test_mermaid_syntax_is_valid(self, tmp_path):
        """Verify Mermaid output has valid syntax."""
        from unittest.mock import patch
        from planning_pipeline.models import RequirementHierarchy, RequirementNode

        research_dir = tmp_path / "thoughts" / "shared" / "research"
        research_dir.mkdir(parents=True)
        (research_dir / "test.md").write_text("# Test Research")

        mock_hierarchy = RequirementHierarchy(
            requirements=[
                RequirementNode(
                    id="REQ_000",
                    description="Test requirement",
                    type="parent",
                    children=[
                        RequirementNode(
                            id="REQ_000.1",
                            description="Child",
                            type="sub_process",
                            parent_id="REQ_000",
                        )
                    ],
                )
            ]
        )

        with patch(
            "planning_pipeline.step_decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_hierarchy

            result = step_requirement_decomposition(
                project_path=tmp_path,
                research_path="thoughts/shared/research/test.md",
            )

        content = Path(result["diagram_path"]).read_text()

        # Verify basic Mermaid syntax
        assert content.startswith("flowchart")
        # Should have node definitions (REQ_XXX["..."])
        assert "REQ_000" in content or "REQ_000_" in content
        # Should have edges (-->)
        assert "-->" in content
