"""Tests for Multi-Doc Phase - Phase 08.

This module tests the MultiDocPhase class which:
- Splits TDD plan into separate phase documents
- Creates overview document (00-overview.md) with summary
- Creates numbered phase documents (01-phase-1.md, etc.)
- Maintains links between documents
- Stores all documents in CWA as FILE entries
- Creates output directory with date prefix
- Returns PhaseResult with all document paths
- Groups requirements into reasonable phases
"""

import json
from pathlib import Path

from context_window_array import EntryType
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseStatus, PhaseType
from silmari_rlm_act.phases.multi_doc import MultiDocPhase
from planning_pipeline.models import RequirementHierarchy, RequirementNode


class TestSplitPlan:
    """Behavior 1: Split Plan by Requirements."""

    def test_creates_multiple_documents(self, tmp_path: Path) -> None:
        """Given plan with requirements, creates docs."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(
            RequirementNode(
                id="REQ_001",
                description="Login feature",
                type="parent",
                acceptance_criteria=[],
            )
        )
        hierarchy.add_requirement(
            RequirementNode(
                id="REQ_002",
                description="Logout feature",
                type="parent",
                acceptance_criteria=[],
            )
        )

        plan_content = """# TDD Plan

## REQ_001: Login
...content...

## REQ_002: Logout
...content...
"""

        docs = phase._split_plan(plan_content, hierarchy, "login-feature")

        # At least overview + 1 phase doc
        assert len(docs) >= 2

    def test_groups_related_requirements(self, tmp_path: Path) -> None:
        """Given child requirements, groups together."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        parent = RequirementNode(
            id="REQ_001",
            description="Authentication",
            type="parent",
            acceptance_criteria=[],
        )
        child1 = RequirementNode(
            id="REQ_001.1",
            description="Login",
            type="sub_process",
            parent_id="REQ_001",
            acceptance_criteria=[],
        )
        child2 = RequirementNode(
            id="REQ_001.2",
            description="Logout",
            type="sub_process",
            parent_id="REQ_001",
            acceptance_criteria=[],
        )
        parent.children = [child1, child2]

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(parent)

        docs = phase._split_plan("# Plan", hierarchy, "auth")

        # Parent and children should be in same phase
        phase_doc = next(d for d in docs if not d["filename"].startswith("00"))
        assert "REQ_001" in phase_doc["content"]


class TestOverviewDocument:
    """Behavior 2: Create Overview Document."""

    def test_creates_overview(self, tmp_path: Path) -> None:
        """Given plan, creates 00-overview.md."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(
            RequirementNode(
                id="REQ_001",
                description="Login feature",
                type="parent",
                acceptance_criteria=[],
            )
        )

        docs = phase._split_plan("# Plan", hierarchy, "feature")

        overview = next((d for d in docs if "00-overview" in d["filename"]), None)
        assert overview is not None

    def test_overview_has_summary_table(self, tmp_path: Path) -> None:
        """Given docs, overview has status table."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(
            RequirementNode(
                id="REQ_001",
                description="Login feature",
                type="parent",
                acceptance_criteria=[],
            )
        )
        hierarchy.add_requirement(
            RequirementNode(
                id="REQ_002",
                description="Logout feature",
                type="parent",
                acceptance_criteria=[],
            )
        )

        docs = phase._split_plan("# Plan", hierarchy, "feature")
        overview = next(d for d in docs if "00-overview" in d["filename"])

        # Check for table markers
        assert "|" in overview["content"]
        assert "REQ_001" in overview["content"] or "Phase" in overview["content"]


class TestPhaseDocuments:
    """Behavior 3: Create Phase Documents."""

    def test_creates_numbered_files(self, tmp_path: Path) -> None:
        """Given 3 requirements, creates phase docs."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(
            RequirementNode(
                id="REQ_001",
                description="Feature A",
                type="parent",
                acceptance_criteria=[],
            )
        )
        hierarchy.add_requirement(
            RequirementNode(
                id="REQ_002",
                description="Feature B",
                type="parent",
                acceptance_criteria=[],
            )
        )
        hierarchy.add_requirement(
            RequirementNode(
                id="REQ_003",
                description="Feature C",
                type="parent",
                acceptance_criteria=[],
            )
        )

        docs = phase._split_plan("# Plan", hierarchy, "feature")

        # Should have overview + at least 1 phase
        phase_docs = [d for d in docs if not d["filename"].startswith("00")]
        assert len(phase_docs) >= 1

        # Check numbering
        filenames = [d["filename"] for d in docs]
        assert any("01-" in f for f in filenames)

    def test_phase_includes_requirement_content(self, tmp_path: Path) -> None:
        """Given requirement, phase doc has its content."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(
            RequirementNode(
                id="REQ_001",
                description="User login feature",
                type="parent",
                acceptance_criteria=["Given creds, when login, then success"],
            )
        )

        docs = phase._split_plan("# Plan", hierarchy, "auth")
        phase_doc = next(d for d in docs if "01-" in d["filename"])

        assert "REQ_001" in phase_doc["content"]
        assert "login" in phase_doc["content"].lower()


class TestDocumentLinks:
    """Behavior 4: Maintain Document Links."""

    def test_overview_links_to_phases(self, tmp_path: Path) -> None:
        """Given phases, overview links to them."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy()
        hierarchy.add_requirement(
            RequirementNode(
                id="REQ_001",
                description="Login feature",
                type="parent",
                acceptance_criteria=[],
            )
        )

        docs = phase._split_plan("# Plan", hierarchy, "auth")
        overview = next(d for d in docs if "00-overview" in d["filename"])
        phase_doc = next(d for d in docs if "01-" in d["filename"])

        # Overview should link to phase doc
        assert phase_doc["filename"] in overview["content"]


class TestStoreDocs:
    """Behavior 5-6: Store Documents in CWA."""

    def test_creates_file_entries(self, tmp_path: Path) -> None:
        """Given docs, creates FILE entries."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        # Create output directory
        output_dir = tmp_path / "plans"
        output_dir.mkdir(parents=True)

        docs = [
            {"filename": "00-overview.md", "title": "Overview", "content": "# Overview"},
            {"filename": "01-login.md", "title": "Phase 1", "content": "# Login"},
        ]

        entry_ids = phase._store_docs_in_cwa(docs, output_dir)

        assert len(entry_ids) == 2
        for entry_id in entry_ids:
            entry = cwa.get_entry(entry_id)
            assert entry is not None
            assert entry.entry_type == EntryType.FILE


class TestMultiDocExecution:
    """Behavior 7-8: Execute and Return."""

    def test_returns_all_document_paths(self, tmp_path: Path) -> None:
        """Given successful execution, returns all paths."""
        # Create hierarchy JSON
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Login feature",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": [],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        # Create plan
        plan_path = tmp_path / "plan.md"
        plan_path.write_text("# TDD Plan\n\n## REQ_001: Login")

        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(
            plan_path=str(plan_path),
            hierarchy_path=str(hierarchy_path),
            plan_name="login",
        )

        assert result.status == PhaseStatus.COMPLETE
        assert len(result.artifacts) >= 2  # Overview + at least 1 phase

    def test_creates_output_directory(self, tmp_path: Path) -> None:
        """Given plan name, creates dated directory."""
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Login feature",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": [],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        plan_path = tmp_path / "plan.md"
        plan_path.write_text("# Plan")

        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(
            plan_path=str(plan_path),
            hierarchy_path=str(hierarchy_path),
            plan_name="login",
        )

        # Check directory exists and has expected name pattern
        assert result.status == PhaseStatus.COMPLETE
        first_artifact = Path(result.artifacts[0])
        assert "tdd-login" in str(first_artifact.parent)

    def test_returns_phase_type_multi_doc(self, tmp_path: Path) -> None:
        """Given execution, returns correct phase type."""
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test feature",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": [],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        plan_path = tmp_path / "plan.md"
        plan_path.write_text("# Plan")

        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(
            plan_path=str(plan_path),
            hierarchy_path=str(hierarchy_path),
            plan_name="test",
        )

        assert result.phase_type == PhaseType.MULTI_DOC

    def test_handles_missing_plan(self, tmp_path: Path) -> None:
        """Given missing plan, returns failed result."""
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test",
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
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(
            plan_path="nonexistent.md",
            hierarchy_path=str(hierarchy_path),
            plan_name="test",
        )

        assert result.status == PhaseStatus.FAILED
        assert len(result.errors) > 0

    def test_handles_missing_hierarchy(self, tmp_path: Path) -> None:
        """Given missing hierarchy, returns failed result."""
        plan_path = tmp_path / "plan.md"
        plan_path.write_text("# Plan")

        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(
            plan_path=str(plan_path),
            hierarchy_path="nonexistent.json",
            plan_name="test",
        )

        assert result.status == PhaseStatus.FAILED
        assert len(result.errors) > 0

    def test_handles_invalid_hierarchy_json(self, tmp_path: Path) -> None:
        """Given invalid JSON, returns failed result."""
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text("not valid json")

        plan_path = tmp_path / "plan.md"
        plan_path.write_text("# Plan")

        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(
            plan_path=str(plan_path),
            hierarchy_path=str(hierarchy_path),
            plan_name="test",
        )

        assert result.status == PhaseStatus.FAILED
        assert len(result.errors) > 0

    def test_includes_metadata(self, tmp_path: Path) -> None:
        """Given successful execution, includes metadata."""
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ_001",
                    "description": "Test feature",
                    "type": "parent",
                    "children": [],
                    "acceptance_criteria": [],
                }
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        plan_path = tmp_path / "plan.md"
        plan_path.write_text("# Plan")

        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(
            plan_path=str(plan_path),
            hierarchy_path=str(hierarchy_path),
            plan_name="test",
        )

        assert "document_count" in result.metadata
        assert "output_dir" in result.metadata


class TestLargePlanHandling:
    """Behavior 8: Handle Large Plans."""

    def test_groups_many_requirements(self, tmp_path: Path) -> None:
        """Given many requirements, groups into reasonable phases."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        # Create 10 requirements
        hierarchy = RequirementHierarchy()
        for i in range(10):
            hierarchy.add_requirement(
                RequirementNode(
                    id=f"REQ_{i+1:03d}",
                    description=f"Feature {i+1}",
                    type="parent",
                    acceptance_criteria=[],
                )
            )

        docs = phase._split_plan("# Plan", hierarchy, "big-feature")

        # Should have multiple phase docs (not one giant one)
        phase_docs = [d for d in docs if not d["filename"].startswith("00")]
        assert len(phase_docs) > 1

    def test_respects_max_per_phase(self, tmp_path: Path) -> None:
        """Given many requirements, respects max per phase limit."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)
        phase.MAX_REQS_PER_PHASE = 3  # Set low limit for testing

        hierarchy = RequirementHierarchy()
        for i in range(9):
            hierarchy.add_requirement(
                RequirementNode(
                    id=f"REQ_{i+1:03d}",
                    description=f"Feature {i+1}",
                    type="parent",
                    acceptance_criteria=[],
                )
            )

        docs = phase._split_plan("# Plan", hierarchy, "feature")

        phase_docs = [d for d in docs if not d["filename"].startswith("00")]
        # With 9 reqs and max 3 per phase, should have 3 phase docs
        assert len(phase_docs) >= 3
