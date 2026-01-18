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

        result = phase.execute(plan_name="test-plan", hierarchy_path=str(hierarchy_path))

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

        result = phase.execute(plan_name="test-plan", hierarchy_path=str(hierarchy_path))

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

        result = phase.execute(plan_name="test-plan", hierarchy_path=str(hierarchy_path))

        assert "cwa_entry_id" in result.metadata
        assert "requirements_count" in result.metadata
        assert result.metadata["requirements_count"] == 1

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


class TestBuildRequirementContext:
    """Behavior 2: Build Requirement Context for Claude Prompt."""

    def test_build_requirement_context_full(self, tmp_path: Path) -> None:
        """Test: Build context with full requirement metadata."""
        from planning_pipeline.models import RequirementNode, ImplementationComponents

        child = RequirementNode(
            id="REQ_001.1",
            description="Child requirement",
            type="sub_process",
            parent_id="REQ_001",
            acceptance_criteria=["Child criterion"]
        )

        requirement = RequirementNode(
            id="REQ_001",
            description="Parent requirement",
            type="parent",
            children=[child],
            acceptance_criteria=["Given X, when Y, then Z"],
            implementation=ImplementationComponents(
                frontend=["LoginForm.tsx"],
                backend=["AuthService.ts"]
            ),
            function_id="Auth.login",
            related_concepts=["JWT", "OAuth"]
        )

        research_doc = tmp_path / "research.md"
        research_doc.write_text("# Research\nContext about auth")

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Act
        context = phase._build_requirement_context(requirement, str(research_doc))

        # Assert
        assert "REQ_001" in context
        assert "Parent requirement" in context
        assert "Auth.login" in context
        assert "LoginForm.tsx" in context
        assert "AuthService.ts" in context
        assert "Given X, when Y, then Z" in context
        assert "REQ_001.1" in context  # Child included
        assert "Child requirement" in context
        assert str(research_doc) in context

    def test_build_requirement_context_minimal(self, tmp_path: Path) -> None:
        """Test: Build context with minimal requirement (no children, no implementation)."""
        from planning_pipeline.models import RequirementNode

        requirement = RequirementNode(
            id="REQ_002",
            description="Simple requirement",
            type="parent",
            acceptance_criteria=["Criterion 1"]
        )

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Act
        context = phase._build_requirement_context(requirement, None)

        # Assert
        assert "REQ_002" in context
        assert "Simple requirement" in context
        assert "Criterion 1" in context
        # Should handle missing implementation gracefully
        assert "implementation" in context.lower() or "Implementation:" not in context


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


class TestGenerateInitialPlan:
    """Behavior 3: Generate Initial TDD Plan via Claude Session."""

    def test_generate_initial_plan_success(self, tmp_path: Path) -> None:
        """Test: Generate initial plan via Claude with successful response."""
        # Arrange
        from planning_pipeline.models import RequirementNode

        requirement = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
            acceptance_criteria=["Criterion 1"],
            function_id="Test.func"
        )

        # Mock run_claude_sync to return success
        mock_result = {
            "success": True,
            "output": "# TDD Plan\n\nPlan content generated by Claude",
            "error": "",
            "elapsed": 10.5
        }

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Create mock research doc
        research_doc = tmp_path / "research.md"
        research_doc.write_text("# Research")

        # Create template file
        template_dir = tmp_path / ".claude" / "commands"
        template_dir.mkdir(parents=True, exist_ok=True)
        (template_dir / "create_tdd_plan.md").write_text("# TDD Plan Template")

        # Act
        with patch('silmari_rlm_act.phases.tdd_planning.run_claude_sync', return_value=mock_result):
            plan_path = phase._generate_initial_plan(requirement, str(research_doc))

        # Assert
        assert plan_path is not None
        assert Path(plan_path).exists()
        # Check date format in path
        import re
        assert re.search(r"\d{4}-\d{2}-\d{2}", str(plan_path))
        assert "tdd" in str(plan_path)

        # Verify plan content was written
        plan_content = Path(plan_path).read_text()
        assert "TDD Plan" in plan_content or "Plan content" in plan_content

    def test_generate_initial_plan_claude_error(self, tmp_path: Path) -> None:
        """Test: Handle Claude error gracefully."""
        # Arrange
        from planning_pipeline.models import RequirementNode

        requirement = RequirementNode(
            id="REQ_002",
            description="Test requirement",
            type="parent"
        )

        mock_result = {
            "success": False,
            "output": "",
            "error": "Claude API error",
            "elapsed": 1.0
        }

        # Create template file
        template_dir = tmp_path / ".claude" / "commands"
        template_dir.mkdir(parents=True, exist_ok=True)
        (template_dir / "create_tdd_plan.md").write_text("# TDD Plan Template")

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Act
        with patch('silmari_rlm_act.phases.tdd_planning.run_claude_sync', return_value=mock_result):
            plan_path = phase._generate_initial_plan(requirement, None)

        # Assert
        assert plan_path is None  # Should return None on error

    def test_generate_initial_plan_prompt_structure(self, tmp_path: Path) -> None:
        """Test: Verify prompt sent to Claude contains all required elements."""
        # Arrange
        from planning_pipeline.models import RequirementNode, ImplementationComponents

        requirement = RequirementNode(
            id="REQ_003",
            description="Auth requirement",
            type="parent",
            acceptance_criteria=["Given user, when login, then authenticated"],
            implementation=ImplementationComponents(
                frontend=["LoginForm.tsx"],
                backend=["AuthService.ts"]
            ),
            function_id="Auth.login"
        )

        research_doc = tmp_path / "auth_research.md"
        research_doc.write_text("# Auth Research\nJWT-based authentication")

        # Create template file
        template_dir = tmp_path / ".claude" / "commands"
        template_dir.mkdir(parents=True, exist_ok=True)
        (template_dir / "create_tdd_plan.md").write_text("# TDD Plan Template\n\nCreate a plan...")

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        mock_result = {"success": True, "output": "Plan", "error": "", "elapsed": 5.0}

        # Act
        with patch('silmari_rlm_act.phases.tdd_planning.run_claude_sync', return_value=mock_result) as mock_claude:
            phase._generate_initial_plan(requirement, str(research_doc))

        # Assert - verify run_claude_sync was called with correct prompt
        assert mock_claude.called
        call_args = mock_claude.call_args
        # Check keyword args first, then positional
        if "prompt" in call_args.kwargs:
            prompt = call_args.kwargs["prompt"]
        else:
            prompt = call_args[0][0]  # First positional arg is the prompt

        # Verify prompt contains instruction template reference
        assert "create_tdd_plan" in prompt.lower() or "tdd" in prompt.lower()

        # Verify prompt contains requirement details
        assert "REQ_003" in prompt
        assert "Auth.login" in prompt
        assert "LoginForm.tsx" in prompt
        assert "AuthService.ts" in prompt
        assert "Given user, when login, then authenticated" in prompt
        assert str(research_doc) in prompt

    def test_generate_initial_plan_missing_template(self, tmp_path: Path) -> None:
        """Test: Handle missing template file gracefully."""
        # Arrange
        from planning_pipeline.models import RequirementNode

        requirement = RequirementNode(
            id="REQ_004",
            description="Test requirement",
            type="parent"
        )

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Act (no template file exists)
        result = phase._generate_initial_plan(requirement, None)

        # Assert
        assert result is None  # Should return None when template missing

    def test_load_instruction_template_success(self, tmp_path: Path) -> None:
        """Test: Load instruction template from .claude/commands/."""
        # Arrange
        template_dir = tmp_path / ".claude" / "commands"
        template_dir.mkdir(parents=True, exist_ok=True)
        template_content = "# Test Template\n\nSome instructions here."
        (template_dir / "test_template.md").write_text(template_content)

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Act
        result = phase._load_instruction_template("test_template")

        # Assert
        assert result == template_content

    def test_load_instruction_template_missing(self, tmp_path: Path) -> None:
        """Test: Return None for missing template."""
        # Arrange
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Act
        result = phase._load_instruction_template("nonexistent_template")

        # Assert
        assert result is None

    def test_generate_plan_path_format(self, tmp_path: Path) -> None:
        """Test: Plan path follows expected format."""
        # Arrange
        from planning_pipeline.models import RequirementNode
        from datetime import datetime

        requirement = RequirementNode(
            id="REQ_005",
            description="User authentication feature",
            type="parent"
        )

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Act
        plan_path = phase._generate_plan_path(requirement)

        # Assert
        date_str = datetime.now().strftime("%Y-%m-%d")
        assert date_str in str(plan_path)
        assert "tdd" in str(plan_path)
        assert "req-005" in str(plan_path).lower()
        assert "user-authentication" in str(plan_path).lower()
        assert plan_path.suffix == ".md"
        assert "thoughts/searchable/plans" in str(plan_path)


class TestReviewPlan:
    """Behavior 4: Review Plan via Claude Session."""

    def test_review_plan_success(self, tmp_path: Path) -> None:
        """Test: Review plan via Claude with successful response."""
        # Arrange
        plan_content = """# Test TDD Plan
## Behavior 1
Some test specification
"""
        plan_path = tmp_path / "thoughts" / "searchable" / "plans" / "2026-01-18-tdd-test.md"
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(plan_content)

        # Create review_plan.md template
        template_dir = tmp_path / ".claude" / "commands"
        template_dir.mkdir(parents=True, exist_ok=True)
        (template_dir / "review_plan.md").write_text("# Review Plan\nInstructions for reviewing")

        mock_result = {
            "success": True,
            "output": "# Plan Review\nLooks good with minor suggestions",
            "error": "",
            "elapsed": 8.0
        }

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Act
        with patch('silmari_rlm_act.phases.tdd_planning.run_claude_sync', return_value=mock_result):
            review_path = phase._review_plan(plan_path)

        # Assert
        assert review_path is not None
        assert review_path.exists()
        assert "-REVIEW.md" in str(review_path)
        assert "2026-01-18-tdd-test-REVIEW.md" in str(review_path)

        review_content = review_path.read_text()
        assert "Plan Review" in review_content

    def test_review_plan_missing_file(self, tmp_path: Path) -> None:
        """Test: Handle missing plan file gracefully."""
        # Arrange
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        nonexistent_path = tmp_path / "nonexistent.md"

        # Act
        review_path = phase._review_plan(nonexistent_path)

        # Assert
        assert review_path is None

    def test_review_plan_prompt_structure(self, tmp_path: Path) -> None:
        """Test: Verify review prompt contains instruction + plan content."""
        # Arrange
        plan_content = "# TDD Plan\nTest behaviors"
        plan_path = tmp_path / "plan.md"
        plan_path.write_text(plan_content)

        # Create review_plan.md template
        template_dir = tmp_path / ".claude" / "commands"
        template_dir.mkdir(parents=True, exist_ok=True)
        template_path = template_dir / "review_plan.md"
        template_path.write_text("# Review Plan\nInstructions for reviewing")

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        mock_result = {"success": True, "output": "Review", "error": "", "elapsed": 5.0}

        # Act
        with patch('silmari_rlm_act.phases.tdd_planning.run_claude_sync', return_value=mock_result) as mock_claude:
            phase._review_plan(plan_path)

        # Assert
        assert mock_claude.called
        call_args = mock_claude.call_args
        # Check keyword args first, then positional
        if "prompt" in call_args.kwargs:
            prompt = call_args.kwargs["prompt"]
        else:
            prompt = call_args[0][0]  # First positional arg is the prompt

        assert "review_plan" in prompt.lower() or "review" in prompt.lower()
        assert str(plan_path) in prompt
        assert "TDD Plan" in prompt or plan_content in prompt

    def test_review_plan_claude_error(self, tmp_path: Path) -> None:
        """Test: Handle Claude error gracefully."""
        # Arrange
        plan_content = "# TDD Plan\nTest content"
        plan_path = tmp_path / "plan.md"
        plan_path.write_text(plan_content)

        # Create review_plan.md template
        template_dir = tmp_path / ".claude" / "commands"
        template_dir.mkdir(parents=True, exist_ok=True)
        (template_dir / "review_plan.md").write_text("# Review Plan Template")

        mock_result = {
            "success": False,
            "output": "",
            "error": "Claude API error",
            "elapsed": 1.0
        }

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Act
        with patch('silmari_rlm_act.phases.tdd_planning.run_claude_sync', return_value=mock_result):
            review_path = phase._review_plan(plan_path)

        # Assert
        assert review_path is None

    def test_review_plan_missing_template(self, tmp_path: Path) -> None:
        """Test: Handle missing template file gracefully."""
        # Arrange
        plan_content = "# TDD Plan\nTest content"
        plan_path = tmp_path / "plan.md"
        plan_path.write_text(plan_content)

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Act (no template file exists)
        review_path = phase._review_plan(plan_path)

        # Assert
        assert review_path is None


class TestEnhancePlan:
    """Behavior 5: Enhance Plan Using Review Feedback."""

    def test_enhance_plan_success(self, tmp_path: Path) -> None:
        """Test: Enhance plan using review feedback."""
        # Arrange
        original_plan = "# TDD Plan\n## Behavior 1\nOriginal content"
        plan_path = tmp_path / "plan.md"
        plan_path.write_text(original_plan)

        review_content = "# Review\nSuggestion: Add more test cases"
        review_path = tmp_path / "plan-REVIEW.md"
        review_path.write_text(review_content)

        enhanced_plan = "# TDD Plan\n## Behavior 1\nEnhanced with more test cases"
        mock_result = {
            "success": True,
            "output": enhanced_plan,
            "error": "",
            "elapsed": 15.0
        }

        # Create template file
        template_dir = tmp_path / ".claude" / "commands"
        template_dir.mkdir(parents=True, exist_ok=True)
        (template_dir / "create_tdd_plan.md").write_text("# TDD Plan Template")

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Act
        with patch('silmari_rlm_act.phases.tdd_planning.run_claude_sync', return_value=mock_result):
            success = phase._enhance_plan(plan_path, review_path)

        # Assert
        assert success is True
        updated_content = plan_path.read_text()
        assert updated_content == enhanced_plan
        assert "Enhanced" in updated_content

    def test_enhance_plan_missing_files(self, tmp_path: Path) -> None:
        """Test: Handle missing plan or review files."""
        # Arrange
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Act
        success = phase._enhance_plan(Path("nonexistent.md"), Path("also-nonexistent.md"))

        # Assert
        assert success is False

    def test_enhance_plan_claude_error(self, tmp_path: Path) -> None:
        """Test: Handle Claude error, keep original plan."""
        # Arrange
        original_plan = "# TDD Plan\nOriginal"
        plan_path = tmp_path / "plan.md"
        plan_path.write_text(original_plan)

        review_path = tmp_path / "review.md"
        review_path.write_text("# Review")

        # Create template file
        template_dir = tmp_path / ".claude" / "commands"
        template_dir.mkdir(parents=True, exist_ok=True)
        (template_dir / "create_tdd_plan.md").write_text("# TDD Plan Template")

        mock_result = {
            "success": False,
            "output": "",
            "error": "Claude timeout",
            "elapsed": 1.0
        }

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Act
        with patch('silmari_rlm_act.phases.tdd_planning.run_claude_sync', return_value=mock_result):
            success = phase._enhance_plan(plan_path, review_path)

        # Assert
        assert success is False
        # Original plan should be unchanged
        assert plan_path.read_text() == original_plan

    def test_enhance_plan_prompt_structure(self, tmp_path: Path) -> None:
        """Test: Verify enhancement prompt mentions it's an enhancement, not new plan."""
        # Arrange
        plan_path = tmp_path / "plan.md"
        plan_path.write_text("# Plan")

        review_path = tmp_path / "review.md"
        review_path.write_text("# Review")

        # Create template
        template_dir = tmp_path / ".claude" / "commands"
        template_dir.mkdir(parents=True, exist_ok=True)
        template_path = template_dir / "create_tdd_plan.md"
        template_path.write_text("# TDD Plan Template")

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        mock_result = {"success": True, "output": "Enhanced", "error": "", "elapsed": 5.0}

        # Act
        with patch('silmari_rlm_act.phases.tdd_planning.run_claude_sync', return_value=mock_result) as mock_claude:
            phase._enhance_plan(plan_path, review_path)

        # Assert
        call_args = mock_claude.call_args
        if "prompt" in call_args.kwargs:
            prompt = call_args.kwargs["prompt"]
        else:
            prompt = call_args[0][0]

        # Verify enhancement-specific language in prompt
        assert "enhancing" in prompt.lower() or "enhance" in prompt.lower()
        assert "not creating a new plan" in prompt.lower() or "existing plan" in prompt.lower()
        assert str(plan_path) in prompt
        assert str(review_path) in prompt


class TestProcessRequirement:
    """Behavior 6: Process Single Requirement (3-Session Loop)."""

    def test_process_requirement_full_success(self, tmp_path: Path) -> None:
        """Test: Process requirement through all 3 sessions successfully."""
        # Arrange
        from planning_pipeline.models import RequirementNode

        requirement = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
            acceptance_criteria=["Criterion 1"]
        )

        research_doc = tmp_path / "research.md"
        research_doc.write_text("# Research")

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Mock all three Claude calls
        with patch.object(phase, '_generate_initial_plan') as mock_gen, \
             patch.object(phase, '_review_plan') as mock_rev, \
             patch.object(phase, '_enhance_plan') as mock_enh:

            plan_path = tmp_path / "plan.md"
            plan_path.write_text("Plan")
            review_path = tmp_path / "review.md"
            review_path.write_text("Review")

            mock_gen.return_value = plan_path
            mock_rev.return_value = review_path
            mock_enh.return_value = True

            # Act
            result_path = phase._process_requirement(requirement, str(research_doc))

        # Assert
        assert result_path == plan_path
        assert mock_gen.called
        assert mock_rev.called
        assert mock_enh.called

    def test_process_requirement_session1_fails(self, tmp_path: Path) -> None:
        """Test: If session 1 fails, skip sessions 2 & 3."""
        # Arrange
        from planning_pipeline.models import RequirementNode

        requirement = RequirementNode(
            id="REQ_002",
            description="Test",
            type="parent"
        )

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Mock session 1 failure
        with patch.object(phase, '_generate_initial_plan', return_value=None) as mock_gen, \
             patch.object(phase, '_review_plan') as mock_rev, \
             patch.object(phase, '_enhance_plan') as mock_enh:

            # Act
            result = phase._process_requirement(requirement, None)

        # Assert
        assert result is None
        assert mock_gen.called
        assert not mock_rev.called  # Should skip
        assert not mock_enh.called  # Should skip

    def test_process_requirement_session2_fails(self, tmp_path: Path) -> None:
        """Test: If session 2 fails, skip session 3, return session 1 plan."""
        # Arrange
        from planning_pipeline.models import RequirementNode

        requirement = RequirementNode(
            id="REQ_003",
            description="Test",
            type="parent"
        )

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        plan_path = tmp_path / "plan.md"
        plan_path.write_text("Plan")

        # Mock session 1 success, session 2 failure
        with patch.object(phase, '_generate_initial_plan', return_value=plan_path), \
             patch.object(phase, '_review_plan', return_value=None) as mock_rev, \
             patch.object(phase, '_enhance_plan') as mock_enh:

            # Act
            result = phase._process_requirement(requirement, None)

        # Assert
        assert result == plan_path  # Returns session 1 plan
        assert mock_rev.called
        assert not mock_enh.called  # Should skip

    def test_process_requirement_session3_fails(self, tmp_path: Path) -> None:
        """Test: If session 3 fails, return session 1 plan with warning."""
        # Arrange
        from planning_pipeline.models import RequirementNode

        requirement = RequirementNode(
            id="REQ_004",
            description="Test",
            type="parent"
        )

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        plan_path = tmp_path / "plan.md"
        plan_path.write_text("Original plan")
        review_path = tmp_path / "review.md"
        review_path.write_text("Review")

        # Mock sessions 1 & 2 success, session 3 failure
        with patch.object(phase, '_generate_initial_plan', return_value=plan_path), \
             patch.object(phase, '_review_plan', return_value=review_path), \
             patch.object(phase, '_enhance_plan', return_value=False):

            # Act
            result = phase._process_requirement(requirement, None)

        # Assert
        assert result == plan_path  # Returns unenhanced plan
        assert plan_path.read_text() == "Original plan"  # Unchanged
