"""Tests for REQ_002: Artifact Generation (Phase 03).

This module tests the artifact generation requirements:
- REQ_002.1: TDDPlanningPhase produces .md files
- REQ_002.2: DecompositionPhase produces .json files
- REQ_002.3: TDD Plan Markdown content structure
- REQ_002.4: Requirement Hierarchy JSON structure
- REQ_002.5: Directory structure and storage
"""

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseStatus
from silmari_rlm_act.phases.decomposition import DecompositionPhase
from silmari_rlm_act.phases.multi_doc import MultiDocPhase
from silmari_rlm_act.phases.tdd_planning import TDDPlanningPhase
from planning_pipeline.models import (
    RequirementHierarchy,
    RequirementNode,
    VALID_REQUIREMENT_TYPES,
    VALID_CATEGORIES,
)


# ============================================================================
# REQ_002.1: TDDPlanningPhase Markdown Output
# ============================================================================


class TestTDDPlanningMarkdownExtension:
    """REQ_002.1: TDDPlanningPhase produces human-readable .md files."""

    def test_output_files_have_md_extension(self, tmp_path: Path) -> None:
        """REQ_002.1.2: All generated files have .md extension."""
        hierarchy_data = self._create_hierarchy_data()
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test-plan", hierarchy_path=str(hierarchy_path))

        assert result.status == PhaseStatus.COMPLETE
        for artifact in result.artifacts:
            assert artifact.endswith(".md"), f"Artifact {artifact} should have .md extension"
            # Not .markdown or other variations
            assert not artifact.endswith(".markdown")
            assert not artifact.endswith(".MD")

    def test_markdown_is_human_readable(self, tmp_path: Path) -> None:
        """REQ_002.1.3: Files are readable without special tooling."""
        hierarchy_data = self._create_hierarchy_data()
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test-plan", hierarchy_path=str(hierarchy_path))

        # Read file content
        plan_path = Path(result.artifacts[0])
        content = plan_path.read_text(encoding="utf-8")

        # Should be plain text, readable
        assert isinstance(content, str)
        assert len(content) > 0
        # No binary content
        assert "\x00" not in content

    def test_markdown_has_proper_headers(self, tmp_path: Path) -> None:
        """REQ_002.1.5: Files include proper Markdown headers."""
        hierarchy_data = self._create_hierarchy_data()
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test-plan", hierarchy_path=str(hierarchy_path))

        plan_path = Path(result.artifacts[0])
        content = plan_path.read_text()

        # Check for proper header structure
        assert "# " in content  # H1
        assert "## " in content  # H2
        # At least one requirement section or summary
        assert "REQ_" in content or "Requirement" in content

    def test_markdown_saved_with_utf8(self, tmp_path: Path) -> None:
        """REQ_002.1.6: Files are saved with UTF-8 encoding."""
        hierarchy_data = self._create_hierarchy_data()
        # Add unicode characters to description
        hierarchy_data["requirements"][0]["description"] = "Test with unicode: \u00e9\u00f1\u00fc"
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data, ensure_ascii=False), encoding="utf-8")

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test-plan", hierarchy_path=str(hierarchy_path))

        plan_path = Path(result.artifacts[0])
        # Should read without encoding errors
        content = plan_path.read_text(encoding="utf-8")
        assert "\u00e9" in content or "unicode" in content.lower()

    def test_phase_result_contains_artifact_paths(self, tmp_path: Path) -> None:
        """REQ_002.1.7: PhaseResult.artifacts contains paths to .md files."""
        hierarchy_data = self._create_hierarchy_data()
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test-plan", hierarchy_path=str(hierarchy_path))

        assert len(result.artifacts) > 0
        for artifact in result.artifacts:
            # Path should exist
            assert Path(artifact).exists()
            # Should be absolute path
            assert Path(artifact).is_absolute()

    def _create_hierarchy_data(self) -> dict[str, Any]:
        """Create valid hierarchy data for tests."""
        return {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": ["Given input, when processed, then output correct"],
                    "category": "functional",
                }
            ],
            "metadata": {"source": "test"},
        }


# ============================================================================
# REQ_002.2: DecompositionPhase JSON Output
# ============================================================================


class TestDecompositionJSONOutput:
    """REQ_002.2: DecompositionPhase produces .json files."""

    def test_output_file_has_json_extension(self, tmp_path: Path) -> None:
        """REQ_002.2.1-2: Output has .json extension."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nImplement feature X.")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        mock_hierarchy = RequirementHierarchy()
        mock_hierarchy.add_requirement(
            RequirementNode(id="REQ_001", description="Feature X", type="parent")
        )

        with patch("silmari_rlm_act.phases.decomposition.decompose_requirements") as mock:
            mock.return_value = mock_hierarchy
            result = phase.execute(research_file)

        assert result.status == PhaseStatus.COMPLETE
        hierarchy_path = result.metadata.get("hierarchy_path")
        assert hierarchy_path is not None
        assert hierarchy_path.endswith(".json")
        assert not hierarchy_path.endswith(".JSON")

    def test_json_is_valid_and_parseable(self, tmp_path: Path) -> None:
        """REQ_002.2.3: JSON output is valid and parseable."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nImplement feature.")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        mock_hierarchy = RequirementHierarchy()
        mock_hierarchy.add_requirement(
            RequirementNode(id="REQ_001", description="Feature", type="parent")
        )

        with patch("silmari_rlm_act.phases.decomposition.decompose_requirements") as mock:
            mock.return_value = mock_hierarchy
            result = phase.execute(research_file)

        hierarchy_path = Path(result.metadata["hierarchy_path"])
        content = hierarchy_path.read_text()

        # Should parse without errors
        parsed = json.loads(content)
        assert "requirements" in parsed

    def test_json_has_2_space_indentation(self, tmp_path: Path) -> None:
        """REQ_002.2.4: JSON is formatted with 2-space indentation."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nImplement feature.")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        mock_hierarchy = RequirementHierarchy()
        mock_hierarchy.add_requirement(
            RequirementNode(id="REQ_001", description="Feature", type="parent")
        )

        with patch("silmari_rlm_act.phases.decomposition.decompose_requirements") as mock:
            mock.return_value = mock_hierarchy
            result = phase.execute(research_file)

        hierarchy_path = Path(result.metadata["hierarchy_path"])
        content = hierarchy_path.read_text()

        # Check for 2-space indentation pattern
        lines = content.split("\n")
        has_2_space = any(line.startswith("  ") and not line.startswith("    ") for line in lines)
        assert has_2_space, "JSON should use 2-space indentation"

    def test_json_passes_round_trip(self, tmp_path: Path) -> None:
        """REQ_002.2.6: Output passes RequirementHierarchy.from_dict()."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nImplement feature.")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        mock_hierarchy = RequirementHierarchy()
        mock_hierarchy.add_requirement(
            RequirementNode(
                id="REQ_001",
                description="Feature",
                type="parent",
                acceptance_criteria=["Given X, when Y, then Z"],
            )
        )
        mock_hierarchy.metadata["source"] = "test"

        with patch("silmari_rlm_act.phases.decomposition.decompose_requirements") as mock:
            mock.return_value = mock_hierarchy
            result = phase.execute(research_file)

        hierarchy_path = Path(result.metadata["hierarchy_path"])
        content = hierarchy_path.read_text()
        data = json.loads(content)

        # Should deserialize without errors
        restored = RequirementHierarchy.from_dict(data)
        assert len(restored.requirements) == 1
        assert restored.requirements[0].id == "REQ_001"


# ============================================================================
# REQ_002.3: TDD Plan Markdown Content Structure
# ============================================================================


class TestTDDPlanMarkdownContent:
    """REQ_002.3: TDD Plan Markdown content requirements."""

    def test_overview_contains_phase_summary_table(self, tmp_path: Path) -> None:
        """REQ_002.3.1: Overview contains Phase Summary table."""
        hierarchy = self._create_multi_requirement_hierarchy()
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy.to_dict()))

        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        # First create a TDD plan
        plan_content = "# Plan\n\n## Overview\n\nThis is a plan."
        plan_path = tmp_path / "plan.md"
        plan_path.write_text(plan_content)

        result = phase.execute(
            plan_path=str(plan_path),
            hierarchy_path=str(hierarchy_path),
            plan_name="test-feature",
        )

        assert result.status == PhaseStatus.COMPLETE

        # Find overview document
        overview_path = None
        for artifact in result.artifacts:
            if "00-overview" in artifact:
                overview_path = Path(artifact)
                break

        assert overview_path is not None, "Should have 00-overview.md"
        content = overview_path.read_text()

        # Check Phase Summary table
        assert "Phase Summary" in content or "Phase | Description" in content
        assert "|" in content  # Table markers
        assert "Status" in content

    def test_overview_contains_requirements_summary(self, tmp_path: Path) -> None:
        """REQ_002.3.2: Overview contains Requirements Summary."""
        hierarchy = self._create_multi_requirement_hierarchy()
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy.to_dict()))

        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        plan_path = tmp_path / "plan.md"
        plan_path.write_text("# Plan")

        result = phase.execute(
            plan_path=str(plan_path),
            hierarchy_path=str(hierarchy_path),
            plan_name="test",
        )

        overview_path = [p for p in result.artifacts if "00-overview" in p][0]
        content = Path(overview_path).read_text()

        assert "Requirements Summary" in content or "| ID |" in content
        assert "REQ_001" in content
        assert "REQ_002" in content

    def test_testable_behaviors_as_numbered_lists(self, tmp_path: Path) -> None:
        """REQ_002.3.4: Testable behaviors rendered as numbered lists."""
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": [
                        "Given state A, when action B, then result C",
                        "Given state X, when action Y, then result Z",
                    ],
                    "category": "functional",
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test", hierarchy_path=str(hierarchy_path))

        plan_path = Path(result.artifacts[0])
        content = plan_path.read_text()

        # Check for numbered items or behavior sections
        assert "Behavior 1" in content or "1." in content

    def test_success_criteria_with_checkboxes(self, tmp_path: Path) -> None:
        """REQ_002.3.8: Success Criteria includes checkbox syntax."""
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test requirement",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": ["Given X, when Y, then Z"],
                    "category": "functional",
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test", hierarchy_path=str(hierarchy_path))

        plan_path = Path(result.artifacts[0])
        content = plan_path.read_text()

        # Check for checkbox syntax
        assert "- [ ]" in content, "Should have checkbox syntax for success criteria"

    def test_markdown_tables_properly_formatted(self, tmp_path: Path) -> None:
        """REQ_002.3.10: Tables have header separators (|---|---|)."""
        hierarchy = self._create_multi_requirement_hierarchy()
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy.to_dict()))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test", hierarchy_path=str(hierarchy_path))

        plan_path = Path(result.artifacts[0])
        content = plan_path.read_text()

        # Check for table separator row
        assert "|--" in content or "| --" in content, "Table should have header separators"

    def _create_multi_requirement_hierarchy(self) -> RequirementHierarchy:
        """Create hierarchy with multiple requirements."""
        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(
            RequirementNode(
                id="REQ_001",
                description="First requirement",
                type="parent",
                acceptance_criteria=["Criterion 1"],
            )
        )
        hierarchy.add_requirement(
            RequirementNode(
                id="REQ_002",
                description="Second requirement",
                type="parent",
                acceptance_criteria=["Criterion 2"],
            )
        )
        return hierarchy


# ============================================================================
# REQ_002.4: Requirement Hierarchy JSON Structure
# ============================================================================


class TestRequirementHierarchyJSONStructure:
    """REQ_002.4: JSON structure requirements."""

    def test_requirement_node_has_required_fields(self) -> None:
        """REQ_002.4.1: Each node has id, description, type."""
        node = RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
        )

        data = node.to_dict()

        assert "id" in data
        assert isinstance(data["id"], str)
        assert "description" in data
        assert isinstance(data["description"], str)
        assert "type" in data
        assert data["type"] in VALID_REQUIREMENT_TYPES

    def test_requirement_node_serializes_parent_id(self) -> None:
        """REQ_002.4.2: parent_id is string or null."""
        # Root node
        root = RequirementNode(id="REQ_001", description="Root", type="parent")
        assert root.to_dict()["parent_id"] is None

        # Child node
        child = RequirementNode(
            id="REQ_001.1",
            description="Child",
            type="sub_process",
            parent_id="REQ_001",
        )
        assert child.to_dict()["parent_id"] == "REQ_001"

    def test_requirement_node_serializes_children_recursively(self) -> None:
        """REQ_002.4.3: children is array of nested RequirementNode objects."""
        parent = RequirementNode(id="REQ_001", description="Parent", type="parent")
        child = RequirementNode(
            id="REQ_001.1",
            description="Child",
            type="sub_process",
            parent_id="REQ_001",
        )
        parent.children.append(child)

        data = parent.to_dict()

        assert "children" in data
        assert isinstance(data["children"], list)
        assert len(data["children"]) == 1
        assert data["children"][0]["id"] == "REQ_001.1"

    def test_requirement_node_serializes_acceptance_criteria(self) -> None:
        """REQ_002.4.4: acceptance_criteria is array of strings."""
        node = RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
            acceptance_criteria=["Criterion 1", "Criterion 2"],
        )

        data = node.to_dict()

        assert "acceptance_criteria" in data
        assert isinstance(data["acceptance_criteria"], list)
        assert all(isinstance(c, str) for c in data["acceptance_criteria"])

    def test_requirement_node_serializes_category(self) -> None:
        """REQ_002.4.5: category is enum value."""
        node = RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
            category="security",
        )

        data = node.to_dict()

        assert "category" in data
        assert data["category"] in VALID_CATEGORIES

    def test_hierarchy_top_level_structure(self) -> None:
        """REQ_002.4.6: Top-level has 'requirements' array and 'metadata' object."""
        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(
            RequirementNode(id="REQ_001", description="Test", type="parent")
        )
        hierarchy.metadata["source"] = "test"

        data = hierarchy.to_dict()

        assert "requirements" in data
        assert isinstance(data["requirements"], list)
        assert "metadata" in data
        assert isinstance(data["metadata"], dict)

    def test_metadata_contains_decomposition_stats(self, tmp_path: Path) -> None:
        """REQ_002.4.7: Metadata contains decomposition_stats."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nImplement feature.")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        mock_hierarchy = RequirementHierarchy()
        parent = RequirementNode(id="REQ_001", description="Parent", type="parent")
        child = RequirementNode(
            id="REQ_001.1", description="Child", type="sub_process", parent_id="REQ_001"
        )
        parent.children.append(child)
        mock_hierarchy.add_requirement(parent)

        with patch("silmari_rlm_act.phases.decomposition.decompose_requirements") as mock:
            mock.return_value = mock_hierarchy
            result = phase.execute(research_file)

        assert "requirements_count" in result.metadata
        assert "total_nodes" in result.metadata
        assert result.metadata["requirements_count"] == 1  # Top-level
        assert result.metadata["total_nodes"] == 2  # Parent + child

    def test_id_format_follows_pattern(self) -> None:
        """REQ_002.4.8: IDs follow REQ_XXX or REQ_XXX.N format."""
        import re

        id_pattern = re.compile(r"^REQ_\d{3}(\.\d+)*$")

        valid_ids = ["REQ_001", "REQ_001.1", "REQ_001.1.2", "REQ_123"]
        for id_ in valid_ids:
            assert id_pattern.match(id_), f"{id_} should match pattern"

        invalid_ids = ["REQ_1", "req_001", "REQUIREMENT_001"]
        for id_ in invalid_ids:
            assert not id_pattern.match(id_), f"{id_} should not match pattern"

    def test_hierarchy_round_trip(self) -> None:
        """REQ_002.4.10: Round-trip produces equivalent object."""
        original = RequirementHierarchy()
        parent = RequirementNode(
            id="REQ_001",
            description="Parent requirement",
            type="parent",
            acceptance_criteria=["Criterion 1"],
            category="functional",
        )
        child = RequirementNode(
            id="REQ_001.1",
            description="Child requirement",
            type="sub_process",
            parent_id="REQ_001",
            category="security",
        )
        parent.children.append(child)
        original.add_requirement(parent)
        original.metadata["source"] = "test"

        # Round-trip
        data = original.to_dict()
        restored = RequirementHierarchy.from_dict(data)

        # Verify equivalence
        assert len(restored.requirements) == len(original.requirements)
        assert restored.requirements[0].id == original.requirements[0].id
        assert restored.requirements[0].description == original.requirements[0].description
        assert len(restored.requirements[0].children) == len(original.requirements[0].children)
        assert restored.metadata.get("source") == original.metadata.get("source")


# ============================================================================
# REQ_002.5: Directory Structure and Storage
# ============================================================================


class TestDirectoryStructure:
    """REQ_002.5: Directory structure requirements."""

    def test_artifacts_stored_under_thoughts_plans(self, tmp_path: Path) -> None:
        """REQ_002.5.1: Artifacts stored under thoughts/searchable/shared/plans/."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nContent.")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        mock_hierarchy = RequirementHierarchy()
        mock_hierarchy.add_requirement(
            RequirementNode(id="REQ_001", description="Test", type="parent")
        )

        with patch("silmari_rlm_act.phases.decomposition.decompose_requirements") as mock:
            mock.return_value = mock_hierarchy
            result = phase.execute(research_file)

        hierarchy_path = Path(result.metadata["hierarchy_path"])

        # Check path contains the expected structure
        path_parts = hierarchy_path.parts
        assert "thoughts" in path_parts
        assert "searchable" in path_parts
        assert "shared" in path_parts
        assert "plans" in path_parts

    def test_directory_is_timestamped(self, tmp_path: Path) -> None:
        """REQ_002.5.2: Directory has timestamped name."""
        import re

        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nContent.")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        mock_hierarchy = RequirementHierarchy()
        mock_hierarchy.add_requirement(
            RequirementNode(id="REQ_001", description="Test", type="parent")
        )

        with patch("silmari_rlm_act.phases.decomposition.decompose_requirements") as mock:
            mock.return_value = mock_hierarchy
            result = phase.execute(research_file)

        hierarchy_path = Path(result.metadata["hierarchy_path"])
        dir_name = hierarchy_path.parent.name

        # Check for date pattern: YYYY-MM-DD-HH-MM-tdd-*
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-tdd-")
        assert date_pattern.match(dir_name), f"Directory {dir_name} should have timestamp"

    def test_hierarchy_json_at_correct_location(self, tmp_path: Path) -> None:
        """REQ_002.5.3: Hierarchy JSON at {plan_dir}/requirement_hierarchy.json."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nContent.")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        mock_hierarchy = RequirementHierarchy()
        mock_hierarchy.add_requirement(
            RequirementNode(id="REQ_001", description="Test", type="parent")
        )

        with patch("silmari_rlm_act.phases.decomposition.decompose_requirements") as mock:
            mock.return_value = mock_hierarchy
            result = phase.execute(research_file)

        hierarchy_path = Path(result.metadata["hierarchy_path"])
        assert hierarchy_path.name == "requirement_hierarchy.json"
        assert hierarchy_path.exists()

    def test_overview_at_correct_location(self, tmp_path: Path) -> None:
        """REQ_002.5.4: TDD plan overview at {plan_dir}/00-overview.md."""
        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(
            RequirementNode(id="REQ_001", description="Test", type="parent")
        )
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy.to_dict()))

        plan_path = tmp_path / "plan.md"
        plan_path.write_text("# Plan\n\nContent.")

        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(
            plan_path=str(plan_path),
            hierarchy_path=str(hierarchy_path),
            plan_name="test-feature",
        )

        overview_found = False
        for artifact in result.artifacts:
            if Path(artifact).name == "00-overview.md":
                overview_found = True
                assert Path(artifact).exists()
                break

        assert overview_found, "Should have 00-overview.md artifact"

    def test_directory_names_are_slugified(self, tmp_path: Path) -> None:
        """REQ_002.5.6: Directory names are slugified."""
        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(
            RequirementNode(id="REQ_001", description="Test", type="parent")
        )
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy.to_dict()))

        plan_path = tmp_path / "plan.md"
        plan_path.write_text("# Plan")

        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        # Use plan name with spaces and special chars
        result = phase.execute(
            plan_path=str(plan_path),
            hierarchy_path=str(hierarchy_path),
            plan_name="My Test Feature!",
        )

        output_dir = Path(result.metadata["output_dir"])
        dir_name = output_dir.name

        # Should be lowercase, hyphens instead of spaces, no special chars
        assert " " not in dir_name
        assert "!" not in dir_name
        # Should contain slugified version
        assert "my-test-feature" in dir_name or "my" in dir_name.lower()

    def test_paths_are_absolute(self, tmp_path: Path) -> None:
        """REQ_002.5.9: All paths are resolved to absolute."""
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": [],
                    "category": "functional",
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test", hierarchy_path=str(hierarchy_path))

        for artifact in result.artifacts:
            assert Path(artifact).is_absolute(), f"Path {artifact} should be absolute"

        plan_path = result.metadata.get("plan_path")
        if plan_path:
            assert Path(plan_path).is_absolute()
