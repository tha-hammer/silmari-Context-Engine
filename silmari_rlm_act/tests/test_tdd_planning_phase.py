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
from unittest.mock import patch

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

    def test_returns_success_result(self, tmp_path: Path) -> None:
        """Given successful planning, returns PhaseResult."""
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

        result = phase.execute(str(hierarchy_path), "test-plan")

        assert isinstance(result, PhaseResult)
        assert result.phase_type == PhaseType.TDD_PLANNING
        assert result.status == PhaseStatus.COMPLETE
        assert len(result.artifacts) > 0

    def test_includes_plan_path_in_artifacts(self, tmp_path: Path) -> None:
        """Given successful planning, includes plan path."""
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

        result = phase.execute(str(hierarchy_path), "test-plan")

        assert len(result.artifacts) == 1
        assert "test-plan" in result.artifacts[0]
        assert ".md" in result.artifacts[0]

    def test_includes_metadata(self, tmp_path: Path) -> None:
        """Given successful planning, includes metadata."""
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

        result = phase.execute(str(hierarchy_path), "test-plan")

        assert "cwa_entry_id" in result.metadata
        assert "requirements_count" in result.metadata
        assert result.metadata["requirements_count"] == 1

    def test_returns_error_on_missing_hierarchy(self, tmp_path: Path) -> None:
        """Given missing hierarchy, returns error."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute("nonexistent.json", "test-plan")

        assert result.status == PhaseStatus.FAILED
        assert len(result.errors) > 0
        assert any("not found" in e.lower() for e in result.errors)

    def test_returns_error_on_invalid_json(self, tmp_path: Path) -> None:
        """Given invalid JSON, returns error."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json")

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(str(bad_file), "test-plan")

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
                str(hierarchy_path), "test-plan", auto_approve=False
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
                str(hierarchy_path), "test-plan", auto_approve=True
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
                str(hierarchy_path), "test-plan", auto_approve=False
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
                str(hierarchy_path), "test-plan", auto_approve=False
            )

        assert result.metadata.get("user_exit") is True
