"""Tests for Beads Sync Phase - Phase 09.

This module tests the BeadsSyncPhase class which:
- Creates beads epic for the plan
- Creates phase issues for each phase document
- Links dependencies between phases (phase N depends on phase N-1)
- Stores beads issue IDs in CWA as metadata entries
- Syncs with remote (optional)
- Returns PhaseResult with created issue IDs
- Handles beads command failures gracefully
"""

from pathlib import Path
from typing import Any

import pytest

from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseStatus, PhaseType
from silmari_rlm_act.phases.beads_sync import BeadsSyncPhase


class MockBeadsController:
    """Mock BeadsController for testing."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.created_issues: list[dict[str, Any]] = []
        self.dependencies: list[tuple[str, str]] = []
        self.synced = False
        self._issue_counter = 0
        self._fail_on: set[str] = set()

    def _next_id(self) -> str:
        self._issue_counter += 1
        return f"beads-{self._issue_counter:04d}"

    def create_epic(self, title: str, priority: int = 1) -> dict[str, Any]:
        if "create_epic" in self._fail_on:
            return {"success": False, "error": "Mock error"}
        issue_id = self._next_id()
        self.created_issues.append({
            "id": issue_id,
            "title": title,
            "type": "epic",
            "priority": priority,
        })
        return {"success": True, "data": {"id": issue_id}}

    def create_issue(
        self,
        title: str,
        issue_type: str = "task",
        priority: int = 2,
    ) -> dict[str, Any]:
        if "create_issue" in self._fail_on:
            return {"success": False, "error": "Mock error"}
        issue_id = self._next_id()
        self.created_issues.append({
            "id": issue_id,
            "title": title,
            "type": issue_type,
            "priority": priority,
        })
        return {"success": True, "data": {"id": issue_id}}

    def add_dependency(self, issue_id: str, depends_on: str) -> dict[str, Any]:
        if "add_dependency" in self._fail_on:
            return {"success": False, "error": "Mock error"}
        self.dependencies.append((issue_id, depends_on))
        return {"success": True}

    def sync(self) -> dict[str, Any]:
        if "sync" in self._fail_on:
            return {"success": False, "error": "Mock sync error"}
        self.synced = True
        return {"success": True}


@pytest.fixture
def mock_beads() -> MockBeadsController:
    """Create mock beads controller."""
    return MockBeadsController(Path("/tmp/test"))


@pytest.fixture
def sample_phase_docs(tmp_path: Path) -> list[str]:
    """Create sample phase documents."""
    docs_dir = tmp_path / "plans"
    docs_dir.mkdir(parents=True)

    files = [
        ("00-overview.md", "# Overview\n\nPlan overview"),
        ("01-phase-1.md", "# Phase 01\n\nFirst phase"),
        ("02-phase-2.md", "# Phase 02\n\nSecond phase"),
        ("03-phase-3.md", "# Phase 03\n\nThird phase"),
    ]

    paths = []
    for filename, content in files:
        path = docs_dir / filename
        path.write_text(content)
        paths.append(str(path))

    return paths


class TestCreateEpic:
    """Behavior 1: Create Beads Epic."""

    def test_creates_epic_for_plan(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
    ) -> None:
        """Given phase docs, creates epic for the plan."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        result = phase.execute(
            phase_docs=sample_phase_docs,
            plan_name="test-feature",
        )

        assert result.status == PhaseStatus.COMPLETE
        epics = [i for i in mock_beads.created_issues if i["type"] == "epic"]
        assert len(epics) == 1
        assert "test-feature" in epics[0]["title"].lower()

    def test_epic_has_priority_1(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
    ) -> None:
        """Given plan, epic has P1 priority."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        phase.execute(
            phase_docs=sample_phase_docs,
            plan_name="feature",
        )

        epics = [i for i in mock_beads.created_issues if i["type"] == "epic"]
        assert epics[0]["priority"] == 1


class TestCreatePhaseIssues:
    """Behavior 2: Create Phase Issues."""

    def test_creates_issue_per_phase(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
    ) -> None:
        """Given 3 phase docs, creates 3 phase issues."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        # sample_phase_docs has 4 docs: overview + 3 phases
        phase.execute(
            phase_docs=sample_phase_docs,
            plan_name="feature",
        )

        tasks = [i for i in mock_beads.created_issues if i["type"] == "task"]
        assert len(tasks) == 3  # One per phase (excluding overview)

    def test_phase_issue_title_matches_doc(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
    ) -> None:
        """Given phase doc, issue title includes phase name."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        phase.execute(
            phase_docs=sample_phase_docs,
            plan_name="feature",
        )

        tasks = [i for i in mock_beads.created_issues if i["type"] == "task"]
        # Should have Phase 01, Phase 02, Phase 03 in titles
        titles = [t["title"] for t in tasks]
        assert any("01" in t or "Phase 1" in t for t in titles)


class TestLinkDependencies:
    """Behavior 3: Link Dependencies."""

    def test_links_phases_sequentially(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
    ) -> None:
        """Given 3 phases, phase 2 depends on 1, 3 depends on 2."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        phase.execute(
            phase_docs=sample_phase_docs,
            plan_name="feature",
        )

        # Should have 2 dependencies: phase2->phase1, phase3->phase2
        assert len(mock_beads.dependencies) == 2

    def test_first_phase_has_no_dependency(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
    ) -> None:
        """Given phases, first phase is not a dependent."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        phase.execute(
            phase_docs=sample_phase_docs,
            plan_name="feature",
        )

        # Get first phase issue ID (should be beads-0002, after epic beads-0001)
        tasks = [i for i in mock_beads.created_issues if i["type"] == "task"]
        first_phase_id = tasks[0]["id"]

        # First phase should not appear in "issue_id" position (left side) of deps
        dependents = [dep[0] for dep in mock_beads.dependencies]
        assert first_phase_id not in dependents


class TestStoreMetadata:
    """Behavior 4: Store Issue IDs in CWA."""

    def test_stores_epic_id_in_cwa(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
    ) -> None:
        """Given epic created, stores ID in CWA."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        result = phase.execute(
            phase_docs=sample_phase_docs,
            plan_name="feature",
        )

        # Epic ID should be in metadata
        assert "epic_id" in result.metadata
        assert result.metadata["epic_id"] == "beads-0001"

    def test_stores_phase_ids_in_metadata(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
    ) -> None:
        """Given phases created, stores phase IDs in metadata."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        result = phase.execute(
            phase_docs=sample_phase_docs,
            plan_name="feature",
        )

        assert "phase_issue_ids" in result.metadata
        assert len(result.metadata["phase_issue_ids"]) == 3


class TestSyncToRemote:
    """Behavior 5: Sync with Remote."""

    def test_syncs_after_creation(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
    ) -> None:
        """Given issues created, syncs to remote."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        phase.execute(
            phase_docs=sample_phase_docs,
            plan_name="feature",
            sync_remote=True,
        )

        assert mock_beads.synced is True

    def test_skips_sync_when_disabled(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
    ) -> None:
        """Given sync disabled, skips sync."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        phase.execute(
            phase_docs=sample_phase_docs,
            plan_name="feature",
            sync_remote=False,
        )

        assert mock_beads.synced is False


class TestPhaseResult:
    """Behavior 6: Return PhaseResult."""

    def test_returns_complete_status(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
    ) -> None:
        """Given successful execution, returns COMPLETE."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        result = phase.execute(
            phase_docs=sample_phase_docs,
            plan_name="feature",
        )

        assert result.status == PhaseStatus.COMPLETE
        assert result.phase_type == PhaseType.BEADS_SYNC

    def test_includes_timing(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
    ) -> None:
        """Given execution, includes timing info."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        result = phase.execute(
            phase_docs=sample_phase_docs,
            plan_name="feature",
        )

        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.duration_seconds is not None


class TestErrorHandling:
    """Behavior 7: Handle Errors Gracefully."""

    def test_handles_epic_creation_failure(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
    ) -> None:
        """Given epic creation fails, returns FAILED."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        mock_beads._fail_on.add("create_epic")
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        result = phase.execute(
            phase_docs=sample_phase_docs,
            plan_name="feature",
        )

        assert result.status == PhaseStatus.FAILED
        assert len(result.errors) > 0

    def test_handles_issue_creation_failure(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
    ) -> None:
        """Given issue creation fails, returns FAILED."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        mock_beads._fail_on.add("create_issue")
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        result = phase.execute(
            phase_docs=sample_phase_docs,
            plan_name="feature",
        )

        assert result.status == PhaseStatus.FAILED
        assert len(result.errors) > 0

    def test_handles_empty_phase_docs(
        self,
        tmp_path: Path,
    ) -> None:
        """Given empty docs list, returns FAILED."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        result = phase.execute(
            phase_docs=[],
            plan_name="feature",
        )

        assert result.status == PhaseStatus.FAILED
        assert len(result.errors) > 0


class TestParsePhaseNumber:
    """Behavior 8: Parse Phase Number from Filename."""

    def test_parses_phase_number(self, tmp_path: Path) -> None:
        """Given phase filename, extracts number."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        assert phase._parse_phase_number("01-login.md") == 1
        assert phase._parse_phase_number("02-auth.md") == 2
        assert phase._parse_phase_number("10-final.md") == 10

    def test_returns_zero_for_overview(self, tmp_path: Path) -> None:
        """Given overview filename, returns 0."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        assert phase._parse_phase_number("00-overview.md") == 0

    def test_returns_none_for_invalid(self, tmp_path: Path) -> None:
        """Given invalid filename, returns None."""
        cwa = CWAIntegration()
        mock_beads = MockBeadsController(tmp_path)
        phase = BeadsSyncPhase(
            project_path=tmp_path,
            cwa=cwa,
            beads_controller=mock_beads,
        )

        assert phase._parse_phase_number("README.md") is None
        assert phase._parse_phase_number("invalid") is None
