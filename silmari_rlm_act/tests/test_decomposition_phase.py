"""Tests for Decomposition Phase - Phase 06.

This module tests the DecompositionPhase class which:
- Reads research documents from research phase artifacts
- Decomposes requirements using Claude agent SDK
- Stores requirements in CWA as TASK entries
- Returns PhaseResult with requirement hierarchy
- Handles failures gracefully
- Supports interactive checkpoints
- Supports revision with additional context
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from silmari_rlm_act.phases.decomposition import DecompositionPhase
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseResult, PhaseType, PhaseStatus
from context_window_array import EntryType
from planning_pipeline.models import RequirementHierarchy, RequirementNode
from planning_pipeline.decomposition import DecompositionError, DecompositionErrorCode


class TestLoadResearch:
    """Behavior 1: Load Research Document."""

    def test_loads_research_content(self, tmp_path: Path) -> None:
        """Given research path, loads content."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        content = phase._load_research(research_file)

        assert "Research" in content
        assert "Content here" in content

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        """Given missing file, raises FileNotFoundError."""
        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        with pytest.raises(FileNotFoundError):
            phase._load_research(tmp_path / "nonexistent.md")


class TestDecomposeRequirements:
    """Behavior 2: Decompose Requirements."""

    def test_invokes_decompose_requirements(self, tmp_path: Path) -> None:
        """Given research content, invokes decompose_requirements."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nImplement authentication system.")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        mock_hierarchy = RequirementHierarchy()
        mock_hierarchy.add_requirement(
            RequirementNode(
                id="REQ_001",
                description="Implement authentication",
                type="parent",
            )
        )

        with patch(
            "silmari_rlm_act.phases.decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_hierarchy

            phase.execute(research_file)

        mock_decompose.assert_called_once()
        assert "Implement authentication system" in mock_decompose.call_args[1]["research_content"]


class TestStoreInCWA:
    """Behavior 3: Store Requirements in CWA."""

    def test_stores_requirements_as_tasks(self, tmp_path: Path) -> None:
        """Given requirements, stores them as TASK entries."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        mock_hierarchy = RequirementHierarchy()
        parent = RequirementNode(
            id="REQ_001",
            description="Implement authentication",
            type="parent",
        )
        child = RequirementNode(
            id="REQ_001.1",
            description="Add login form",
            type="sub_process",
            parent_id="REQ_001",
        )
        parent.children.append(child)
        mock_hierarchy.add_requirement(parent)

        with patch(
            "silmari_rlm_act.phases.decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_hierarchy

            phase.execute(research_file)

        # Check that requirements were stored in CWA
        task_entries = cwa.get_by_type(EntryType.TASK)
        assert len(task_entries) >= 2  # Parent and child


class TestPhaseResult:
    """Behavior 4: Return PhaseResult."""

    def test_returns_complete_result(self, tmp_path: Path) -> None:
        """Given successful decomposition, returns complete result."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        mock_hierarchy = RequirementHierarchy()
        mock_hierarchy.add_requirement(
            RequirementNode(id="REQ_001", description="Test", type="parent")
        )

        with patch(
            "silmari_rlm_act.phases.decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_hierarchy

            result = phase.execute(research_file)

        assert isinstance(result, PhaseResult)
        assert result.phase_type == PhaseType.DECOMPOSITION
        assert result.status == PhaseStatus.COMPLETE

    def test_includes_hierarchy_in_metadata(self, tmp_path: Path) -> None:
        """Given successful decomposition, includes hierarchy in metadata."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        mock_hierarchy = RequirementHierarchy()
        mock_hierarchy.add_requirement(
            RequirementNode(id="REQ_001", description="Implement feature", type="parent")
        )

        with patch(
            "silmari_rlm_act.phases.decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_hierarchy

            result = phase.execute(research_file)

        assert "hierarchy" in result.metadata
        assert "requirements_count" in result.metadata
        assert result.metadata["requirements_count"] == 1


class TestHandleFailure:
    """Behavior 5: Handle Decomposition Failure."""

    def test_returns_failed_on_error(self, tmp_path: Path) -> None:
        """Given decomposition error, returns failed result."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        error = DecompositionError(
            error_code=DecompositionErrorCode.BAML_API_ERROR,
            error="API call failed",
        )

        with patch(
            "silmari_rlm_act.phases.decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = error

            result = phase.execute(research_file)

        assert result.status == PhaseStatus.FAILED
        assert "API call failed" in result.errors[0]

    def test_returns_failed_on_missing_file(self, tmp_path: Path) -> None:
        """Given missing research file, returns failed result."""
        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(tmp_path / "nonexistent.md")

        assert result.status == PhaseStatus.FAILED
        assert any("not found" in e for e in result.errors)


class TestInteractiveCheckpoint:
    """Behavior 6: Interactive Checkpoint."""

    def test_prompts_user_when_not_auto(self, tmp_path: Path) -> None:
        """Given non-auto mode, prompts user."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        mock_hierarchy = RequirementHierarchy()
        mock_hierarchy.add_requirement(
            RequirementNode(id="REQ_001", description="Test", type="parent")
        )

        with patch(
            "silmari_rlm_act.phases.decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_hierarchy

            with patch(
                "silmari_rlm_act.phases.decomposition.prompt_decomposition_action"
            ) as mock_prompt:
                mock_prompt.return_value = "continue"

                phase.execute_with_checkpoint(research_file, auto_approve=False)

        mock_prompt.assert_called_once()

    def test_skips_prompt_when_auto(self, tmp_path: Path) -> None:
        """Given auto mode, skips user prompt."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        mock_hierarchy = RequirementHierarchy()
        mock_hierarchy.add_requirement(
            RequirementNode(id="REQ_001", description="Test", type="parent")
        )

        with patch(
            "silmari_rlm_act.phases.decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_hierarchy

            with patch(
                "silmari_rlm_act.phases.decomposition.prompt_decomposition_action"
            ) as mock_prompt:
                phase.execute_with_checkpoint(research_file, auto_approve=True)

        mock_prompt.assert_not_called()


class TestAdditionalContext:
    """Behavior 7: Additional Context Support."""

    def test_appends_additional_context(self, tmp_path: Path) -> None:
        """Given additional context, appends to research content."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nBase content.")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        mock_hierarchy = RequirementHierarchy()
        mock_hierarchy.add_requirement(
            RequirementNode(id="REQ_001", description="Test", type="parent")
        )

        with patch(
            "silmari_rlm_act.phases.decomposition.decompose_requirements"
        ) as mock_decompose:
            mock_decompose.return_value = mock_hierarchy

            phase.execute(research_file, additional_context="Extra info here")

        call_args = mock_decompose.call_args
        assert "Extra info here" in call_args[1]["research_content"]
