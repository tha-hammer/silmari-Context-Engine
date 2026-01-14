"""Tests for create_tdd_plan_from_hierarchy function.

Following TDD approach:
- Unit tests use mocked Claude runner (no API calls)
- Integration tests use real Claude (requires ANTHROPIC_API_KEY)
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from planning_pipeline.models import (
    RequirementHierarchy,
    RequirementNode,
    ImplementationComponents,
)


class TestLoadTDDPlanInstructions:
    """Behavior 3.1: Load TDD Plan Instructions."""

    def test_loads_instruction_file_from_project_path(self, tmp_path):
        """Given valid project with instruction file, when called, then loads successfully."""
        from planning_pipeline.decomposition import create_tdd_plan_from_hierarchy

        # Arrange: Create project structure with instruction file
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        instruction_file = commands_dir / "create_tdd_plan.md"
        instruction_file.write_text("# TDD Plan Instructions\nCreate tests first.")

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
        ))

        # Act - patch Claude to avoid API calls
        with patch("planning_pipeline.decomposition.run_claude_sync") as mock_claude:
            mock_claude.return_value = {
                "success": True,
                "output": "Created: thoughts/searchable/shared/plans/2026-01-14-tdd-feature.md",
                "error": "",
                "elapsed": 1.0,
            }
            result = create_tdd_plan_from_hierarchy(tmp_path, hierarchy)

        # Assert
        assert result["success"] is True

    def test_returns_error_when_instruction_file_missing(self, tmp_path):
        """Given project without instruction file, when called, then returns error."""
        from planning_pipeline.decomposition import create_tdd_plan_from_hierarchy

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
        ))

        # Act
        result = create_tdd_plan_from_hierarchy(tmp_path, hierarchy)

        # Assert
        assert result["success"] is False
        assert "create_tdd_plan.md" in result.get("error", "")

    def test_handles_empty_instruction_file(self, tmp_path):
        """Given empty instruction file, when called, then handles gracefully."""
        from planning_pipeline.decomposition import create_tdd_plan_from_hierarchy

        # Arrange
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        instruction_file = commands_dir / "create_tdd_plan.md"
        instruction_file.write_text("")

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
        ))

        # Act
        with patch("planning_pipeline.decomposition.run_claude_sync") as mock_claude:
            mock_claude.return_value = {
                "success": True,
                "output": "Created: thoughts/searchable/shared/plans/2026-01-14-tdd-feature.md",
                "error": "",
                "elapsed": 1.0,
            }
            result = create_tdd_plan_from_hierarchy(tmp_path, hierarchy)

        # Assert - should not crash, just may produce minimal output
        assert "success" in result


class TestProcessInstructionsWithHierarchyContext:
    """Behavior 3.2: Process Instructions with Hierarchy Context."""

    def test_hierarchy_serialized_as_complete_json(self, tmp_path):
        """Given hierarchy with 5 requirements, when processed, then serialized correctly as JSON."""
        from planning_pipeline.decomposition import _serialize_hierarchy_for_prompt

        # Arrange: Create hierarchy with multiple requirements
        hierarchy = RequirementHierarchy()
        for i in range(5):
            req = RequirementNode(
                id=f"REQ_{i:03d}",
                description=f"Requirement {i}",
                type="parent",
                acceptance_criteria=["Criterion 1", "Criterion 2"],
            )
            hierarchy.add_requirement(req)

        # Act
        json_str = _serialize_hierarchy_for_prompt(hierarchy)

        # Assert
        data = json.loads(json_str)
        assert "requirements" in data
        assert len(data["requirements"]) == 5
        assert data["requirements"][0]["acceptance_criteria"] == ["Criterion 1", "Criterion 2"]

    def test_nested_children_recursively_serialized(self, tmp_path):
        """Given hierarchy with nested children, when processed, then recursively serialized."""
        from planning_pipeline.decomposition import _serialize_hierarchy_for_prompt

        hierarchy = RequirementHierarchy()
        parent = RequirementNode(
            id="REQ_001",
            description="Parent requirement",
            type="parent",
        )
        child = RequirementNode(
            id="REQ_001.1",
            description="Child requirement",
            type="sub_process",
            parent_id="REQ_001",
            acceptance_criteria=["Child AC"],
        )
        parent.children.append(child)
        hierarchy.add_requirement(parent)

        # Act
        json_str = _serialize_hierarchy_for_prompt(hierarchy)

        # Assert
        data = json.loads(json_str)
        assert len(data["requirements"][0]["children"]) == 1
        assert data["requirements"][0]["children"][0]["acceptance_criteria"] == ["Child AC"]

    def test_empty_hierarchy_produces_valid_prompt(self, tmp_path):
        """Given empty hierarchy, when processed, then produces valid prompt."""
        from planning_pipeline.decomposition import _serialize_hierarchy_for_prompt

        hierarchy = RequirementHierarchy()

        # Act
        json_str = _serialize_hierarchy_for_prompt(hierarchy)

        # Assert
        data = json.loads(json_str)
        assert "requirements" in data
        assert data["requirements"] == []

    def test_all_requirement_keys_preserved_in_serialization(self, tmp_path):
        """Given requirement with all fields, when serialized, then all keys preserved."""
        from planning_pipeline.decomposition import _serialize_hierarchy_for_prompt

        hierarchy = RequirementHierarchy()
        req = RequirementNode(
            id="REQ_001.1",
            description="Full requirement",
            type="sub_process",
            parent_id="REQ_001",
            acceptance_criteria=["AC1", "AC2", "AC3"],
            implementation=ImplementationComponents(
                frontend=["Component"],
                backend=["Service"],
                middleware=["Filter"],
                shared=["Model"],
            ),
            testable_properties=[],
            function_id="Service.method",
            related_concepts=["concept1", "concept2"],
            category="functional",
        )
        hierarchy.add_requirement(req)

        # Act
        json_str = _serialize_hierarchy_for_prompt(hierarchy)

        # Assert
        data = json.loads(json_str)
        req_data = data["requirements"][0]

        # Verify all expected keys
        assert req_data["id"] == "REQ_001.1"
        assert req_data["description"] == "Full requirement"
        assert req_data["type"] == "sub_process"
        assert req_data["parent_id"] == "REQ_001"
        assert req_data["acceptance_criteria"] == ["AC1", "AC2", "AC3"]
        assert req_data["implementation"]["frontend"] == ["Component"]
        assert req_data["implementation"]["backend"] == ["Service"]
        assert req_data["implementation"]["middleware"] == ["Filter"]
        assert req_data["implementation"]["shared"] == ["Model"]
        assert req_data["function_id"] == "Service.method"
        assert req_data["related_concepts"] == ["concept1", "concept2"]
        assert req_data["category"] == "functional"

    def test_empty_acceptance_criteria_preserved_not_omitted(self, tmp_path):
        """Given requirement with empty acceptance_criteria, when serialized, then array preserved."""
        from planning_pipeline.decomposition import _serialize_hierarchy_for_prompt

        hierarchy = RequirementHierarchy()
        req = RequirementNode(
            id="REQ_001",
            description="Requirement without criteria",
            type="parent",
            acceptance_criteria=[],
        )
        hierarchy.add_requirement(req)

        # Act
        json_str = _serialize_hierarchy_for_prompt(hierarchy)

        # Assert
        data = json.loads(json_str)
        assert data["requirements"][0]["acceptance_criteria"] == []

    def test_null_implementation_serialized_as_null(self, tmp_path):
        """Given requirement with null implementation, when serialized, then null preserved."""
        from planning_pipeline.decomposition import _serialize_hierarchy_for_prompt

        hierarchy = RequirementHierarchy()
        req = RequirementNode(
            id="REQ_001",
            description="Parent requirement",
            type="parent",
            implementation=None,
        )
        hierarchy.add_requirement(req)

        # Act
        json_str = _serialize_hierarchy_for_prompt(hierarchy)

        # Assert
        data = json.loads(json_str)
        assert data["requirements"][0]["implementation"] is None


class TestInvokeClaudeWithProcessedPrompt:
    """Behavior 3.3: Invoke Claude with Processed Prompt."""

    def test_successful_claude_invocation_returns_output(self, tmp_path):
        """Given processed prompt, when calling run_claude_sync, then returns output."""
        from planning_pipeline.decomposition import create_tdd_plan_from_hierarchy

        # Arrange
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "create_tdd_plan.md").write_text("# Instructions")

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
        ))

        # Act
        with patch("planning_pipeline.decomposition.run_claude_sync") as mock_claude:
            mock_claude.return_value = {
                "success": True,
                "output": "Plan created!",
                "error": "",
                "elapsed": 1.0,
            }
            result = create_tdd_plan_from_hierarchy(tmp_path, hierarchy)

        # Assert
        assert result["success"] is True
        assert result["output"] == "Plan created!"

    def test_uses_appropriate_timeout(self, tmp_path):
        """Given prompt, when calling Claude, then uses 1200s (20 min) timeout."""
        from planning_pipeline.decomposition import create_tdd_plan_from_hierarchy

        # Arrange
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "create_tdd_plan.md").write_text("# Instructions")

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
        ))

        # Act
        with patch("planning_pipeline.decomposition.run_claude_sync") as mock_claude:
            mock_claude.return_value = {
                "success": True,
                "output": "Done",
                "error": "",
                "elapsed": 1.0,
            }
            create_tdd_plan_from_hierarchy(tmp_path, hierarchy)

        # Assert - verify timeout arg
        call_args = mock_claude.call_args
        # timeout is passed as keyword arg or positional
        assert 1200 in call_args[0] or call_args[1].get("timeout") == 1200 or call_args[0][1] == 1200

    def test_claude_failure_returns_structured_error(self, tmp_path):
        """Given Claude failure, when called, then returns structured error."""
        from planning_pipeline.decomposition import create_tdd_plan_from_hierarchy

        # Arrange
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "create_tdd_plan.md").write_text("# Instructions")

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
        ))

        # Act
        with patch("planning_pipeline.decomposition.run_claude_sync") as mock_claude:
            mock_claude.return_value = {
                "success": False,
                "output": "",
                "error": "API rate limit exceeded",
                "elapsed": 0.5,
            }
            result = create_tdd_plan_from_hierarchy(tmp_path, hierarchy)

        # Assert
        assert result["success"] is False
        assert "rate limit" in result.get("error", "").lower() or "API" in result.get("error", "")


class TestExtractPlanFilePaths:
    """Behavior 3.4: Extract Plan File Paths from Output."""

    def test_single_plan_file_extracted(self, tmp_path):
        """Given output with single plan path, when extracting, then found correctly."""
        from planning_pipeline.decomposition import create_tdd_plan_from_hierarchy

        # Arrange
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "create_tdd_plan.md").write_text("# Instructions")

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
        ))

        # Act
        with patch("planning_pipeline.decomposition.run_claude_sync") as mock_claude:
            mock_claude.return_value = {
                "success": True,
                "output": "Created: thoughts/searchable/shared/plans/2026-01-14-tdd-feature.md",
                "error": "",
                "elapsed": 1.0,
            }
            result = create_tdd_plan_from_hierarchy(tmp_path, hierarchy)

        # Assert
        assert len(result.get("plan_paths", [])) >= 1
        assert "2026-01-14-tdd-feature.md" in result["plan_paths"][0]

    def test_multiple_plan_files_captured(self, tmp_path):
        """Given output with multiple plan paths, when extracting, then all captured."""
        from planning_pipeline.decomposition import create_tdd_plan_from_hierarchy

        # Arrange
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "create_tdd_plan.md").write_text("# Instructions")

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
        ))

        # Act
        with patch("planning_pipeline.decomposition.run_claude_sync") as mock_claude:
            mock_claude.return_value = {
                "success": True,
                "output": """Created files:
- thoughts/searchable/shared/plans/2026-01-14-tdd-feature/00-overview.md
- thoughts/searchable/shared/plans/2026-01-14-tdd-feature/01-phase-1.md
- thoughts/searchable/shared/plans/2026-01-14-tdd-feature/02-phase-2.md
""",
                "error": "",
                "elapsed": 2.0,
            }
            result = create_tdd_plan_from_hierarchy(tmp_path, hierarchy)

        # Assert
        assert len(result.get("plan_paths", [])) == 3

    def test_no_plan_file_returns_empty_list(self, tmp_path):
        """Given output without plan paths, when extracting, then returns empty list."""
        from planning_pipeline.decomposition import create_tdd_plan_from_hierarchy

        # Arrange
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "create_tdd_plan.md").write_text("# Instructions")

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
        ))

        # Act
        with patch("planning_pipeline.decomposition.run_claude_sync") as mock_claude:
            mock_claude.return_value = {
                "success": True,
                "output": "Processing complete but no files created.",
                "error": "",
                "elapsed": 1.0,
            }
            result = create_tdd_plan_from_hierarchy(tmp_path, hierarchy)

        # Assert
        assert result.get("plan_paths", []) == []
        # Should still succeed since Claude did not error
        assert result["success"] is True


class TestReturnStructuredResult:
    """Behavior 3.5: Return Structured Result."""

    def test_success_includes_all_file_paths(self, tmp_path):
        """Given successful execution, when returning, then includes all paths."""
        from planning_pipeline.decomposition import create_tdd_plan_from_hierarchy

        # Arrange
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "create_tdd_plan.md").write_text("# Instructions")

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
        ))

        # Act
        with patch("planning_pipeline.decomposition.run_claude_sync") as mock_claude:
            mock_claude.return_value = {
                "success": True,
                "output": "Created: thoughts/searchable/shared/plans/2026-01-14-tdd-feature.md",
                "error": "",
                "elapsed": 1.0,
            }
            result = create_tdd_plan_from_hierarchy(tmp_path, hierarchy)

        # Assert
        assert result["success"] is True
        assert "plan_paths" in result
        assert "output" in result

    def test_failure_includes_descriptive_error(self, tmp_path):
        """Given failure, when returning, then includes error message."""
        from planning_pipeline.decomposition import create_tdd_plan_from_hierarchy

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
        ))

        # Act - no instruction file exists
        result = create_tdd_plan_from_hierarchy(tmp_path, hierarchy)

        # Assert
        assert result["success"] is False
        assert "error" in result
        assert result["error"] != ""

    def test_output_preserved_for_debugging(self, tmp_path):
        """Given execution, when returning, then output preserved."""
        from planning_pipeline.decomposition import create_tdd_plan_from_hierarchy

        # Arrange
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "create_tdd_plan.md").write_text("# Instructions")

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
        ))

        # Act
        with patch("planning_pipeline.decomposition.run_claude_sync") as mock_claude:
            mock_claude.return_value = {
                "success": True,
                "output": "Full Claude output for debugging",
                "error": "",
                "elapsed": 1.0,
            }
            result = create_tdd_plan_from_hierarchy(tmp_path, hierarchy)

        # Assert
        assert result["output"] == "Full Claude output for debugging"


class TestAcceptanceCriteriaToTestCaseMapping:
    """Behavior 3.2.1: Map Acceptance Criteria to TDD Test Cases.

    These tests verify the prompt construction ensures acceptance criteria
    are properly conveyed to Claude for TDD test generation.
    """

    def test_prompt_includes_all_acceptance_criteria(self, tmp_path):
        """Given hierarchy with acceptance criteria, when prompt built, then all criteria included."""
        from planning_pipeline.decomposition import _build_tdd_plan_prompt

        # Arrange
        hierarchy = RequirementHierarchy()
        req = RequirementNode(
            id="REQ_001.1",
            description="Login validation",
            type="sub_process",
            acceptance_criteria=[
                "Email format validated before submission",
                "Password minimum 8 characters enforced",
                "Clear error messages displayed for invalid inputs",
                "Form submission blocked until all validations pass",
            ],
            function_id="AuthService.validateLoginForm",
        )
        hierarchy.add_requirement(req)

        instruction_content = "# TDD Plan Instructions"

        # Act
        prompt = _build_tdd_plan_prompt(instruction_content, hierarchy, "feature")

        # Assert - all 4 acceptance criteria should be in the prompt
        assert "Email format validated before submission" in prompt
        assert "Password minimum 8 characters enforced" in prompt
        assert "Clear error messages displayed for invalid inputs" in prompt
        assert "Form submission blocked until all validations pass" in prompt
        assert "AuthService.validateLoginForm" in prompt

    def test_prompt_contains_tdd_mapping_instructions(self, tmp_path):
        """Given prompt, when built, then contains instructions to map AC to tests."""
        from planning_pipeline.decomposition import _build_tdd_plan_prompt

        hierarchy = RequirementHierarchy()
        req = RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
            acceptance_criteria=["Test criterion"],
        )
        hierarchy.add_requirement(req)

        instruction_content = "# TDD Plan Instructions"

        # Act
        prompt = _build_tdd_plan_prompt(instruction_content, hierarchy, "feature")

        # Assert - should have instructions about creating tests from acceptance criteria
        assert "acceptance_criteria" in prompt.lower() or "acceptance criteria" in prompt.lower()


@pytest.mark.integration
class TestCreateTDDPlanFromHierarchyIntegration:
    """Integration tests - require ANTHROPIC_API_KEY."""

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    )
    def test_real_claude_call_creates_plan(self, project_path):
        """Real API call - run with: pytest -m integration"""
        from planning_pipeline.decomposition import create_tdd_plan_from_hierarchy

        # Arrange
        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(RequirementNode(
            id="REQ_TEST_001",
            description="Test user authentication flow",
            type="parent",
            acceptance_criteria=[
                "User can login with email and password",
                "Invalid credentials show error message",
            ],
        ))

        # Act
        result = create_tdd_plan_from_hierarchy(project_path, hierarchy, plan_name="test-auth")

        # Assert
        assert result["success"] is True
        assert len(result.get("plan_paths", [])) >= 1
