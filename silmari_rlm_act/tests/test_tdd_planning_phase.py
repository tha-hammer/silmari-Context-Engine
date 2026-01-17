"""Tests for TDD Planning Phase - Phase 07.

This module tests the TDDPlanningPhase class which:
- Loads requirement hierarchy from decomposition metadata
- Generates TDD plan documents with Red-Green-Refactor cycles
- Includes test specifications (Given/When/Then)
- Includes code snippets for each behavior
- Stores plan in CWA as FILE entry
- Links plan to requirement entries
- Returns PhaseResult with plan path
- Handles planning failures gracefully
- Supports interactive checkpoints
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from context_window_array import EntryType
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseResult, PhaseStatus, PhaseType
from silmari_rlm_act.phases.tdd_planning import TDDPlanningPhase
from planning_pipeline.models import RequirementHierarchy, RequirementNode


class TestLoadHierarchy:
    """Behavior 1: Load Requirement Hierarchy."""

    def test_loads_from_json_path(self, tmp_path: Path) -> None:
        """Given JSON path, loads hierarchy."""
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "User login",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": [],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = phase._load_hierarchy(str(hierarchy_path))

        assert len(hierarchy.requirements) == 1
        assert hierarchy.get_by_id("REQ_001") is not None

    def test_loads_relative_path(self, tmp_path: Path) -> None:
        """Given relative path, resolves against project_path."""
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "User login",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": [],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = phase._load_hierarchy("hierarchy.json")

        assert len(hierarchy.requirements) == 1

    def test_raises_for_missing_file(self, tmp_path: Path) -> None:
        """Given nonexistent path, raises error."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        with pytest.raises(FileNotFoundError):
            phase._load_hierarchy("nonexistent.json")

    def test_raises_for_invalid_json(self, tmp_path: Path) -> None:
        """Given invalid JSON, raises error."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json")

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        with pytest.raises(json.JSONDecodeError):
            phase._load_hierarchy(str(bad_file))


class TestGeneratePlanDocument:
    """Behavior 2-4: Generate TDD Plan Document."""

    def test_generates_markdown(self, tmp_path: Path) -> None:
        """Given hierarchy, generates markdown document."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(
            RequirementNode(
                id="REQ_001",
                description="User login feature",
                type="parent",
                acceptance_criteria=["Given valid creds, when login, then authenticated"],
            )
        )

        plan = phase._generate_plan_document(hierarchy, "login-feature")

        assert "# " in plan  # Has headers
        assert "REQ_001" in plan
        assert "login" in plan.lower()

    def test_includes_red_green_refactor(self, tmp_path: Path) -> None:
        """Given behavior, includes TDD cycle."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(
            RequirementNode(
                id="REQ_001",
                description="Login feature",
                type="parent",
                acceptance_criteria=["Given valid creds, when login, then authenticated"],
            )
        )

        plan = phase._generate_plan_document(hierarchy, "login")

        # Check for TDD cycle markers (emoji or text)
        has_red = "Red" in plan or "🔴" in plan
        has_green = "Green" in plan or "🟢" in plan
        has_refactor = "Refactor" in plan or "🔵" in plan

        assert has_red, "Plan should include Red phase"
        assert has_green, "Plan should include Green phase"
        assert has_refactor, "Plan should include Refactor phase"

    def test_includes_test_specification(self, tmp_path: Path) -> None:
        """Given behavior, includes Given/When/Then."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(
            RequirementNode(
                id="REQ_001",
                description="Login feature",
                type="parent",
                acceptance_criteria=[
                    "Given valid credentials, when login submitted, then user authenticated"
                ],
            )
        )

        plan = phase._generate_plan_document(hierarchy, "login")

        assert "Given" in plan
        # Check for "When" or "when" (may be in lowercase in parsed form)
        assert "When" in plan or "when" in plan
        # Check for "Then" or "then"
        assert "Then" in plan or "then" in plan

    def test_includes_code_blocks(self, tmp_path: Path) -> None:
        """Given plan, includes code snippets."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(
            RequirementNode(
                id="REQ_001",
                description="Login feature",
                type="parent",
                acceptance_criteria=["Given valid creds, when login, then authenticated"],
            )
        )

        plan = phase._generate_plan_document(hierarchy, "login")

        assert "```" in plan  # Has code blocks

    def test_handles_empty_acceptance_criteria(self, tmp_path: Path) -> None:
        """Given requirement without criteria, generates placeholder."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(
            RequirementNode(
                id="REQ_001",
                description="Some feature",
                type="parent",
                acceptance_criteria=[],
            )
        )

        plan = phase._generate_plan_document(hierarchy, "feature")

        # Should still generate valid markdown
        assert "REQ_001" in plan
        assert "# " in plan

    def test_includes_summary_table(self, tmp_path: Path) -> None:
        """Given multiple requirements, includes summary table."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(
            RequirementNode(id="REQ_001", description="Feature 1", type="parent")
        )
        hierarchy.add_requirement(
            RequirementNode(id="REQ_002", description="Feature 2", type="parent")
        )

        plan = phase._generate_plan_document(hierarchy, "multi")

        # Check for table markers
        assert "|" in plan
        assert "REQ_001" in plan
        assert "REQ_002" in plan


class TestStorePlanInCWA:
    """Behavior 5-6: Store Plan in CWA."""

    def test_creates_file_entry(self, tmp_path: Path) -> None:
        """Given plan, creates FILE entry."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        plan_content = "# TDD Plan\n\n## Overview\n\nThis is a test plan."
        plan_path = tmp_path / "plan.md"
        plan_path.write_text(plan_content)

        entry_id = phase._store_plan_in_cwa(str(plan_path), plan_content)

        entry = cwa.get_entry(entry_id)
        assert entry is not None
        assert entry.entry_type == EntryType.FILE

    def test_stores_content_and_summary(self, tmp_path: Path) -> None:
        """Given plan, stores full content and summary."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        plan_content = "# My TDD Plan\n\n## Overview\n\nDetailed content here."
        plan_path = tmp_path / "plan.md"
        plan_path.write_text(plan_content)

        entry_id = phase._store_plan_in_cwa(str(plan_path), plan_content)

        entry = cwa.get_entry(entry_id)
        assert entry is not None
        assert entry.content == plan_content
        assert "TDD Plan" in entry.summary or "My TDD Plan" in entry.summary


class TestPlanPhaseResult:
    """Behavior 7-8: Return PhaseResult."""

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    @patch("silmari_rlm_act.phases.tdd_planning.run_review_session")
    def test_returns_success_result(self, mock_review: MagicMock, tmp_path: Path) -> None:
        """Given successful planning, returns PhaseResult."""
        mock_review.return_value = {
            "success": True,
            "output": '{"findings": [], "overall_quality": "good", "amendments": []}',
            "error": "",
            "elapsed": 1.0,
        }
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": ["Given valid input, when processed, then success returned"],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test-plan", hierarchy_path=str(hierarchy_path))

        assert isinstance(result, PhaseResult)
        assert result.phase_type == PhaseType.TDD_PLANNING
        assert result.status == PhaseStatus.COMPLETE
        assert len(result.artifacts) > 0

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    @patch("silmari_rlm_act.phases.tdd_planning.run_review_session")
    def test_includes_plan_path_in_artifacts(self, mock_review: MagicMock, tmp_path: Path) -> None:
        """Given successful planning, includes plan path."""
        mock_review.return_value = {
            "success": True,
            "output": '{"findings": [], "overall_quality": "good", "amendments": []}',
            "error": "",
            "elapsed": 1.0,
        }
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": ["Given valid input, when processed, then success returned"],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test-plan", hierarchy_path=str(hierarchy_path))

        assert len(result.artifacts) == 1
        assert "test-plan" in result.artifacts[0]
        assert ".md" in result.artifacts[0]

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    @patch("silmari_rlm_act.phases.tdd_planning.run_review_session")
    def test_includes_metadata(self, mock_review: MagicMock, tmp_path: Path) -> None:
        """Given successful planning, includes metadata."""
        mock_review.return_value = {
            "success": True,
            "output": '{"findings": [], "overall_quality": "good", "amendments": []}',
            "error": "",
            "elapsed": 1.0,
        }
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": ["Given valid input, when processed, then success returned"],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test-plan", hierarchy_path=str(hierarchy_path))

        # Now generates individual plans, so cwa_entry_ids is a list
        assert "cwa_entry_ids" in result.metadata
        assert "requirements_count" in result.metadata
        assert result.metadata["requirements_count"] == 1
        assert len(result.metadata["cwa_entry_ids"]) == 1

    def test_returns_error_on_missing_hierarchy(self, tmp_path: Path) -> None:
        """Given missing hierarchy, returns error."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test-plan", hierarchy_path="nonexistent.json")

        assert result.status == PhaseStatus.FAILED
        assert len(result.errors) > 0
        assert any("not found" in e.lower() for e in result.errors)

    def test_returns_error_on_invalid_json(self, tmp_path: Path) -> None:
        """Given invalid JSON, returns error."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json")

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test-plan", hierarchy_path=str(bad_file))

        assert result.status == PhaseStatus.FAILED
        assert len(result.errors) > 0


class TestInteractiveCheckpoint:
    """Behavior: Interactive Checkpoint Support."""

    def test_prompts_user_when_not_auto(self, tmp_path: Path) -> None:
        """Given non-auto mode, prompts user."""
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": [],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.tdd_planning.prompt_tdd_planning_action"
        ) as mock_prompt:
            mock_prompt.return_value = "continue"

            phase.execute_with_checkpoint(
                plan_name="test-plan",
                hierarchy_path=str(hierarchy_path),
                auto_approve=False,
            )

        mock_prompt.assert_called_once()

    def test_skips_prompt_when_auto(self, tmp_path: Path) -> None:
        """Given auto mode, skips user prompt."""
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": [],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.tdd_planning.prompt_tdd_planning_action"
        ) as mock_prompt:
            phase.execute_with_checkpoint(
                plan_name="test-plan",
                hierarchy_path=str(hierarchy_path),
                auto_approve=True,
            )

        mock_prompt.assert_not_called()

    def test_sets_user_action_in_metadata(self, tmp_path: Path) -> None:
        """Given user interaction, records action in metadata."""
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": [],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.tdd_planning.prompt_tdd_planning_action"
        ) as mock_prompt:
            mock_prompt.return_value = "continue"

            result = phase.execute_with_checkpoint(
                plan_name="test-plan",
                hierarchy_path=str(hierarchy_path),
                auto_approve=False,
            )

        assert result.metadata.get("user_action") == "continue"

    def test_handles_exit_action(self, tmp_path: Path) -> None:
        """Given exit action, returns with user_exit flag."""
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": [],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.tdd_planning.prompt_tdd_planning_action"
        ) as mock_prompt:
            mock_prompt.return_value = "exit"

            result = phase.execute_with_checkpoint(
                plan_name="test-plan",
                hierarchy_path=str(hierarchy_path),
                auto_approve=False,
            )

        assert result.metadata.get("user_exit") is True


class TestIndividualPlanGeneration:
    """Behavior 1: Generate individual plan files per requirement."""

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    @patch("silmari_rlm_act.phases.tdd_planning.run_review_session")
    def test_generates_one_file_per_requirement(self, mock_review: MagicMock, tmp_path: Path) -> None:
        """Given 3 requirements, when execute(), then 3 plan files created."""
        # Arrange
        mock_review.return_value = {
            "success": True,
            "output": '{"findings": [], "overall_quality": "good", "amendments": []}',
            "error": "",
            "elapsed": 1.0,
        }
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "User login",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": [
                        "Given creds, when login, then authenticated"
                    ],
                },
                {
                    "id": "REQ_002",
                    "description": "User logout",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": [
                        "Given session, when logout, then session ends"
                    ],
                },
                {
                    "id": "REQ_003",
                    "description": "Password reset",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": [
                        "Given email, when reset, then link sent"
                    ],
                },
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Act
        result = phase.execute(plan_name="test-plan", hierarchy_path=str(hierarchy_path))

        # Assert
        assert result.status == PhaseStatus.COMPLETE
        assert len(result.artifacts) == 3
        for artifact_path in result.artifacts:
            assert Path(artifact_path).exists()
            assert "REQ_" in artifact_path.upper() or "req_" in artifact_path.lower()

    def test_handles_empty_hierarchy(self, tmp_path: Path) -> None:
        """Given 0 requirements, when execute(), then 0 files created."""
        hierarchy_data = {"requirements": [], "metadata": {}}
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test-plan", hierarchy_path=str(hierarchy_path))

        assert result.status == PhaseStatus.COMPLETE
        assert len(result.artifacts) == 0

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    @patch("silmari_rlm_act.phases.tdd_planning.run_review_session")
    def test_single_requirement_creates_one_file(self, mock_review: MagicMock, tmp_path: Path) -> None:
        """Given 1 requirement, when execute(), then exactly 1 file created."""
        mock_review.return_value = {
            "success": True,
            "output": '{"findings": [], "overall_quality": "good", "amendments": []}',
            "error": "",
            "elapsed": 1.0,
        }
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Single feature",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": ["Given X, when Y, then Z"],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test-plan", hierarchy_path=str(hierarchy_path))

        assert result.status == PhaseStatus.COMPLETE
        assert len(result.artifacts) == 1
        assert Path(result.artifacts[0]).exists()

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    @patch("silmari_rlm_act.phases.tdd_planning.run_review_session")
    def test_file_names_follow_pattern(self, mock_review: MagicMock, tmp_path: Path) -> None:
        """Given requirement, when execute(), file name has correct pattern."""
        mock_review.return_value = {
            "success": True,
            "output": '{"findings": [], "overall_quality": "good", "amendments": []}',
            "error": "",
            "elapsed": 1.0,
        }
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test feature",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": ["criterion"],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="my-feature", hierarchy_path=str(hierarchy_path))

        assert len(result.artifacts) == 1
        file_name = Path(result.artifacts[0]).name
        # Pattern: YYYY-MM-DD-tdd-{plan_name}-{req_id}.md
        import re

        pattern = r"\d{4}-\d{2}-\d{2}-tdd-my-feature-req_001\.md"
        assert re.match(pattern, file_name), f"File name '{file_name}' doesn't match pattern"

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    @patch("silmari_rlm_act.phases.tdd_planning.run_review_session")
    def test_metadata_includes_plans_generated_count(self, mock_review: MagicMock, tmp_path: Path) -> None:
        """Given multiple requirements, metadata tracks plans generated."""
        mock_review.return_value = {
            "success": True,
            "output": '{"findings": [], "overall_quality": "good", "amendments": []}',
            "error": "",
            "elapsed": 1.0,
        }
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Feature 1",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": ["Given input, when processed, then output"],
                },
                {
                    "id": "REQ_002",
                    "description": "Feature 2",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": ["Given data, when validated, then stored"],
                },
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test", hierarchy_path=str(hierarchy_path))

        assert result.metadata.get("plans_generated") == 2
        assert result.metadata.get("requirements_count") == 2


class TestLLMContentGeneration:
    """Behavior 2: LLM generates actual TDD content via Agent SDK."""

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    def test_generates_actual_test_code_not_todos(self, tmp_path: Path) -> None:
        """Given requirement, when _generate_plan_content_for_requirement(), then no TODO placeholders."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        req = RequirementNode(
            id="REQ_001",
            description="User login feature",
            type="parent",
            acceptance_criteria=[
                "Given valid credentials, when login, then user authenticated"
            ],
        )

        # Act
        content = phase._generate_plan_content_for_requirement(req, "test")

        # Assert - should NOT have placeholder TODOs (once LLM integration is done)
        # For now, this test will fail because we still generate static templates
        assert "assert False  # TODO" not in content
        assert "# TODO: Implement" not in content
        assert "# TODO: Add minimal implementation" not in content
        # Should have actual test code (or at least descriptive content)
        assert "assert" in content.lower() or "test" in content.lower()

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    def test_includes_given_when_then_from_criteria(self, tmp_path: Path) -> None:
        """Given requirement with criteria, when generate, then Given/When/Then extracted."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        req = RequirementNode(
            id="REQ_001",
            description="User login",
            type="parent",
            acceptance_criteria=[
                "Given valid credentials, when login submitted, then session created"
            ],
        )

        content = phase._generate_plan_content_for_requirement(req, "test")

        # Should extract Given/When/Then format
        assert "**Given**:" in content or "Given:" in content or "given" in content.lower()
        assert "**When**:" in content or "When:" in content or "when" in content.lower()
        assert "**Then**:" in content or "Then:" in content or "then" in content.lower()

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    def test_fallback_when_sdk_unavailable(self, tmp_path: Path) -> None:
        """Given Agent SDK unavailable, when generate, then fallback to template."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        req = RequirementNode(
            id="REQ_001",
            description="User login",
            type="parent",
            acceptance_criteria=["Given creds, when login, then authenticated"],
        )

        content = phase._generate_plan_content_for_requirement(req, "test")

        # Fallback should still produce valid markdown
        assert "# " in content
        assert "REQ_001" in content

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    def test_generates_content_for_multiple_criteria(self, tmp_path: Path) -> None:
        """Given requirement with multiple criteria, generates content for each."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        req = RequirementNode(
            id="REQ_001",
            description="User authentication",
            type="parent",
            acceptance_criteria=[
                "Given valid credentials, when login, then session created",
                "Given invalid credentials, when login, then error shown",
                "Given expired session, when accessing, then redirected to login",
            ],
        )

        content = phase._generate_plan_content_for_requirement(req, "test")

        # Should have content for all 3 criteria
        # Check for coverage of all three scenarios (LLM may use different headings)
        assert "valid credentials" in content.lower() or "valid" in content.lower()
        assert "invalid credentials" in content.lower() or "invalid" in content.lower() or "error" in content.lower()
        assert "expired session" in content.lower() or "expired" in content.lower() or "redirect" in content.lower()
        # Should have multiple test functions or test sections
        assert content.count("def test_") >= 3 or content.count("### ") >= 3


class TestReviewPlanIntegration:
    """Behavior 3: Review plan runs after TDD generation."""

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    @patch("silmari_rlm_act.phases.tdd_planning.run_review_session")
    def test_review_session_called_after_plan_generated(
        self, mock_review: MagicMock, tmp_path: Path
    ) -> None:
        """Given plan generated, when complete, then review session initiated."""
        # Configure mock to return successful review
        mock_review.return_value = {
            "success": True,
            "output": '{"findings": [], "overall_quality": "good", "amendments": []}',
            "error": "",
            "elapsed": 1.0,
        }

        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Login",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": [
                        "Given creds, when login, then session"
                    ],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Act
        result = phase.execute(plan_name="test", hierarchy_path=str(hierarchy_path))

        # Assert
        assert result.status == PhaseStatus.COMPLETE
        mock_review.assert_called_once()
        # Verify it was called with the plan path
        call_args = mock_review.call_args
        assert "tdd-test-req_001" in call_args[0][0].lower()

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    @patch("silmari_rlm_act.phases.tdd_planning.run_review_session")
    def test_multiple_plans_each_get_review(
        self, mock_review: MagicMock, tmp_path: Path
    ) -> None:
        """Given 3 plans generated, when complete, then 3 review sessions."""
        # Configure mock to return successful review
        mock_review.return_value = {
            "success": True,
            "output": '{"findings": [], "overall_quality": "good", "amendments": []}',
            "error": "",
            "elapsed": 1.0,
        }

        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Login",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": ["criterion1"],
                },
                {
                    "id": "REQ_002",
                    "description": "Logout",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": ["criterion2"],
                },
                {
                    "id": "REQ_003",
                    "description": "Reset",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": ["criterion3"],
                },
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test", hierarchy_path=str(hierarchy_path))

        assert result.status == PhaseStatus.COMPLETE
        assert mock_review.call_count == 3

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    @patch("silmari_rlm_act.phases.tdd_planning.run_review_session")
    def test_plan_saved_even_if_review_fails(
        self, mock_review: MagicMock, tmp_path: Path
    ) -> None:
        """Given review fails, when plan generated, then plan still saved."""
        mock_review.side_effect = Exception("Review service unavailable")

        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Login",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": ["criterion"],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test", hierarchy_path=str(hierarchy_path))

        # Plan should still be saved even if review failed
        assert len(result.artifacts) == 1
        assert Path(result.artifacts[0]).exists()
        # When review fails by exception, review_result is None so review_failures is not incremented
        # The plan should still succeed with COMPLETE status
        assert result.status == PhaseStatus.COMPLETE

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    @patch("silmari_rlm_act.phases.tdd_planning.run_review_session")
    def test_review_file_created_alongside_plan(
        self, mock_review: MagicMock, tmp_path: Path
    ) -> None:
        """Given successful review, when complete, then review file created."""
        mock_review.return_value = {
            "success": True,
            "output": '{"findings": [{"step": "Contract", "severity": "minor", "issue": "test", "suggestion": "fix"}], "overall_quality": "good", "amendments": []}',
            "error": "",
            "elapsed": 1.0,
        }

        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Login",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": ["criterion"],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test", hierarchy_path=str(hierarchy_path))

        assert result.status == PhaseStatus.COMPLETE
        # Check that review file exists alongside plan
        plan_path = Path(result.artifacts[0])
        review_path = plan_path.with_suffix(".review.md")
        assert review_path.exists(), f"Review file not found: {review_path}"

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    @patch("silmari_rlm_act.phases.tdd_planning.run_review_session")
    def test_metadata_includes_review_status(
        self, mock_review: MagicMock, tmp_path: Path
    ) -> None:
        """Given review completed, when execute(), then metadata includes review info."""
        mock_review.return_value = {
            "success": True,
            "output": '{"findings": [], "overall_quality": "good", "amendments": []}',
            "error": "",
            "elapsed": 1.5,
        }

        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Login",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": ["criterion"],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test", hierarchy_path=str(hierarchy_path))

        assert result.status == PhaseStatus.COMPLETE
        # Metadata should include review count
        assert result.metadata.get("reviews_completed", 0) == 1

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    @patch("silmari_rlm_act.phases.tdd_planning.run_review_session")
    def test_review_failure_tracked_in_metadata(
        self, mock_review: MagicMock, tmp_path: Path
    ) -> None:
        """Given review returns error, when execute(), then failure tracked."""
        # Return a result with success=False (different from exception)
        mock_review.return_value = {
            "success": False,
            "output": "",
            "error": "API timeout",
            "elapsed": 30.0,
        }

        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Login",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": ["criterion"],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test", hierarchy_path=str(hierarchy_path))

        # Plan should still be saved
        assert len(result.artifacts) == 1
        # Status should be PARTIAL when review fails
        assert result.status == PhaseStatus.PARTIAL
        # Metadata should track the failure
        assert result.metadata.get("review_failures", 0) == 1
