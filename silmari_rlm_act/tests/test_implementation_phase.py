"""Tests for Implementation Phase - Phase 10.

This module tests the ImplementationPhase class which:
- Loads phase documents and extracts behaviors
- Executes TDD cycles (Red-Green-Refactor)
- Runs tests after each cycle
- Supports three autonomy modes (checkpoint, autonomous, batch)
- Stores results in CWA as COMMAND_RESULT entries
- Updates beads status on success
- Handles implementation failures gracefully
- Manages context bounds (<200 entries)
- Resumes from checkpoint
- Creates git commits after phase completion
"""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import AutonomyMode, PhaseStatus, PhaseType
from silmari_rlm_act.phases.implementation import ImplementationPhase


class MockRunner:
    """Mock runner for Claude invocations."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.return_value = {"success": True, "output": "Implemented"}
        self._fail_next = False

    def run_sync(self, prompt: str, timeout: int = 600) -> dict[str, Any]:
        self.calls.append({"prompt": prompt, "timeout": timeout})
        if self._fail_next:
            self._fail_next = False
            return {"success": False, "error": "Mock failure"}
        return self.return_value


class MockBeadsController:
    """Mock beads controller for testing."""

    def __init__(self) -> None:
        self.closed_issues: list[tuple[str, str]] = []
        self._fail_close = False

    def close_issue(self, issue_id: str, reason: str = "") -> dict[str, Any]:
        if self._fail_close:
            return {"success": False, "error": "Mock close error"}
        self.closed_issues.append((issue_id, reason))
        return {"success": True}


@pytest.fixture
def mock_runner() -> MockRunner:
    """Create a mock runner."""
    return MockRunner()


@pytest.fixture
def mock_beads() -> MockBeadsController:
    """Create mock beads controller."""
    return MockBeadsController()


@pytest.fixture
def sample_phase_doc(tmp_path: Path) -> Path:
    """Create a sample phase document."""
    phase_doc = tmp_path / "01-login.md"
    phase_doc.write_text("""# Phase 01: User Login

## Overview

Implement user authentication functionality.

## Testable Behaviors

1. Given valid credentials, when login, then user authenticated
2. Given invalid credentials, when login, then error shown
3. Given expired session, when accessing protected route, then redirect to login

## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
""")
    return phase_doc


@pytest.fixture
def sample_phase_docs(tmp_path: Path) -> list[str]:
    """Create sample phase documents for multi-phase tests."""
    docs_dir = tmp_path / "plans"
    docs_dir.mkdir(parents=True)

    docs = [
        ("01-login.md", """# Phase 01: Login

## Testable Behaviors

1. Given valid creds, when login, then authenticated
"""),
        ("02-auth.md", """# Phase 02: Auth

## Testable Behaviors

1. Given token, when validating, then user retrieved
"""),
        ("03-session.md", """# Phase 03: Session

## Testable Behaviors

1. Given session, when expired, then redirect
"""),
        ("04-logout.md", """# Phase 04: Logout

## Testable Behaviors

1. Given logged in, when logout, then session cleared
"""),
    ]

    paths = []
    for filename, content in docs:
        path = docs_dir / filename
        path.write_text(content)
        paths.append(str(path))

    return paths


class TestLoadPhaseDocument:
    """Behavior 1: Load Phase Document."""

    def test_loads_document_content(
        self,
        tmp_path: Path,
        sample_phase_doc: Path,
    ) -> None:
        """Given path, loads content."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        content = phase._load_phase_document(str(sample_phase_doc))

        assert "Login" in content
        assert "Testable Behaviors" in content

    def test_handles_relative_path(
        self,
        tmp_path: Path,
    ) -> None:
        """Given relative path, resolves against project_path."""
        doc = tmp_path / "doc.md"
        doc.write_text("# Test Document")

        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        content = phase._load_phase_document("doc.md")

        assert "Test Document" in content

    def test_raises_on_missing_file(
        self,
        tmp_path: Path,
    ) -> None:
        """Given missing file, raises FileNotFoundError."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        with pytest.raises(FileNotFoundError):
            phase._load_phase_document("nonexistent.md")


class TestExtractBehaviors:
    """Behavior 1 continued: Extract Behaviors from Document."""

    def test_extracts_numbered_behaviors(
        self,
        tmp_path: Path,
        sample_phase_doc: Path,
    ) -> None:
        """Given document with behaviors, extracts all."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        behaviors = phase._extract_behaviors(str(sample_phase_doc))

        assert len(behaviors) == 3
        assert "valid credentials" in behaviors[0]
        assert "invalid credentials" in behaviors[1]
        assert "expired session" in behaviors[2]

    def test_returns_empty_for_no_behaviors(
        self,
        tmp_path: Path,
    ) -> None:
        """Given document without behaviors section, returns empty."""
        doc = tmp_path / "no-behaviors.md"
        doc.write_text("# Phase 01\n\nNo behaviors here.")

        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        behaviors = phase._extract_behaviors(str(doc))

        assert behaviors == []

    def test_stops_at_next_section(
        self,
        tmp_path: Path,
    ) -> None:
        """Given document with sections after behaviors, stops correctly."""
        doc = tmp_path / "multi-section.md"
        doc.write_text("""# Phase

## Testable Behaviors

1. First behavior
2. Second behavior

## Success Criteria

- [ ] All tests pass

## Implementation Notes

More text here.
""")

        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        behaviors = phase._extract_behaviors(str(doc))

        assert len(behaviors) == 2
        assert "All tests pass" not in " ".join(behaviors)


class TestExecuteTDDCycle:
    """Behavior 2: Execute TDD Cycle."""

    def test_invokes_runner_for_implementation(
        self,
        tmp_path: Path,
        mock_runner: MockRunner,
    ) -> None:
        """Given behavior, invokes runner."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase._runner = mock_runner

        result = phase._execute_tdd_cycle(
            behavior="Given valid creds, when login, then authenticated",
            phase_context="# Phase 1: Login",
        )

        assert len(mock_runner.calls) == 1
        assert result["success"] is True

    def test_includes_behavior_in_prompt(
        self,
        tmp_path: Path,
        mock_runner: MockRunner,
    ) -> None:
        """Given behavior, prompt includes behavior text."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase._runner = mock_runner

        phase._execute_tdd_cycle(
            behavior="Given valid creds, when login, then authenticated",
            phase_context="# Context",
        )

        prompt = mock_runner.calls[0]["prompt"]
        assert "valid creds" in prompt
        assert "login" in prompt

    def test_handles_runner_failure(
        self,
        tmp_path: Path,
        mock_runner: MockRunner,
    ) -> None:
        """Given runner fails, returns failure result."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        mock_runner._fail_next = True
        phase._runner = mock_runner

        result = phase._execute_tdd_cycle(
            behavior="Test behavior",
            phase_context="Context",
        )

        assert result["success"] is False
        assert "error" in result


class TestRunTests:
    """Behavior 3: Run Tests After Each Cycle."""

    def test_runs_test_suite(
        self,
        tmp_path: Path,
    ) -> None:
        """Given implementation, runs tests."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="5 passed", stderr="")

            passed, output = phase._run_tests()

        assert passed is True
        assert "passed" in output

    def test_detects_test_failure(
        self,
        tmp_path: Path,
    ) -> None:
        """Given failing tests, returns failure."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="1 failed", stderr="")

            passed, output = phase._run_tests()

        assert passed is False
        assert "failed" in output

    def test_uses_specified_test_path(
        self,
        tmp_path: Path,
    ) -> None:
        """Given test path, uses it."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            phase._run_tests(test_path="custom/tests/")

            call_args = mock_run.call_args[0][0]
            assert "custom/tests/" in call_args


class TestCheckpointMode:
    """Behavior 4: Checkpoint Mode - Pause at Each Phase."""

    def test_checkpoint_mode_pauses_after_each(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
        mock_runner: MockRunner,
    ) -> None:
        """Given checkpoint mode, pauses after each phase."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase._runner = mock_runner

        pause_calls: list[str] = []

        def mock_pause(phase_path: str, result: dict[str, Any]) -> dict[str, Any]:
            pause_calls.append(phase_path)
            return {"continue": True}

        with patch.object(phase, "_pause_for_review", mock_pause):
            with patch.object(phase, "_run_tests", return_value=(True, "passed")):
                phase._execute_with_mode(
                    phases=sample_phase_docs[:2],
                    mode=AutonomyMode.CHECKPOINT,
                )

        assert len(pause_calls) == 2

    def test_checkpoint_mode_stops_on_no_continue(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
        mock_runner: MockRunner,
    ) -> None:
        """Given user declines continue, stops."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase._runner = mock_runner

        call_count = [0]

        def mock_pause(phase_path: str, result: dict[str, Any]) -> dict[str, Any]:
            call_count[0] += 1
            return {"continue": call_count[0] < 2}  # Stop after first

        with patch.object(phase, "_pause_for_review", mock_pause):
            with patch.object(phase, "_run_tests", return_value=(True, "passed")):
                results = phase._execute_with_mode(
                    phases=sample_phase_docs[:3],
                    mode=AutonomyMode.CHECKPOINT,
                )

        # Should only execute 2 phases (pause after 1st, user says no after 2nd)
        assert len(results) == 2


class TestAutonomousMode:
    """Behavior 5: Autonomous Mode - Run All Phases."""

    def test_autonomous_mode_no_pause(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
        mock_runner: MockRunner,
    ) -> None:
        """Given autonomous mode, runs without pause."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase._runner = mock_runner

        pause_calls: list[str] = []

        def mock_pause(phase_path: str, result: dict[str, Any]) -> dict[str, Any]:
            pause_calls.append(phase_path)
            return {"continue": True}

        with patch.object(phase, "_pause_for_review", mock_pause):
            with patch.object(phase, "_run_tests", return_value=(True, "passed")):
                phase._execute_with_mode(
                    phases=sample_phase_docs[:3],
                    mode=AutonomyMode.FULLY_AUTONOMOUS,
                )

        assert len(pause_calls) == 0

    def test_autonomous_mode_stops_on_failure(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
        mock_runner: MockRunner,
    ) -> None:
        """Given failure in autonomous mode, stops."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase._runner = mock_runner

        fail_count = [0]

        def mock_single(phase_path: str) -> dict[str, Any]:
            fail_count[0] += 1
            if fail_count[0] == 2:
                return {"success": False, "error": "Failed"}
            return {"success": True}

        with patch.object(phase, "_execute_single_phase", mock_single):
            results = phase._execute_with_mode(
                phases=sample_phase_docs[:4],
                mode=AutonomyMode.FULLY_AUTONOMOUS,
            )

        assert len(results) == 2  # Stopped at failure


class TestBatchMode:
    """Behavior 6: Batch Mode - Group Phases."""

    def test_batch_mode_groups_phases(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
        mock_runner: MockRunner,
    ) -> None:
        """Given batch mode, groups and pauses between groups."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase._runner = mock_runner
        phase.BATCH_SIZE = 2

        pause_calls: list[str] = []

        def mock_pause(phase_path: str, result: dict[str, Any]) -> dict[str, Any]:
            pause_calls.append(phase_path)
            return {"continue": True}

        with patch.object(phase, "_pause_for_review", mock_pause):
            with patch.object(phase, "_execute_single_phase", return_value={"success": True}):
                phase._execute_with_mode(
                    phases=sample_phase_docs,  # 4 phases
                    mode=AutonomyMode.BATCH,
                )

        # 4 phases / 2 per batch = 2 batches = 2 pauses
        assert len(pause_calls) == 2

    def test_batch_mode_stops_on_user_cancel(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
        mock_runner: MockRunner,
    ) -> None:
        """Given user cancels batch, stops after that batch."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase._runner = mock_runner
        phase.BATCH_SIZE = 2

        call_count = [0]

        def mock_pause(phase_path: str, result: dict[str, Any]) -> dict[str, Any]:
            call_count[0] += 1
            # Return False on first call to stop after first batch
            return {"continue": False}

        with patch.object(phase, "_pause_for_review", mock_pause):
            with patch.object(phase, "_execute_single_phase", return_value={"success": True}):
                results = phase._execute_with_mode(
                    phases=sample_phase_docs,  # 4 phases
                    mode=AutonomyMode.BATCH,
                )

        # First batch of 2 completed, user cancelled, stopped before second batch
        assert len(results) == 2
        assert call_count[0] == 1  # Only paused once after first batch


class TestStoreResultsInCWA:
    """Behavior 7: Store Results in CWA."""

    def test_stores_command_results(
        self,
        tmp_path: Path,
        sample_phase_doc: Path,
        mock_runner: MockRunner,
    ) -> None:
        """Given implementation, stores result in CWA."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase._runner = mock_runner

        with patch.object(phase, "_run_tests", return_value=(True, "passed")):
            phase._execute_single_phase(str(sample_phase_doc))

        # Should have stored results
        entries = cwa.get_by_type(entry_type=__import__("context_window_array").EntryType.COMMAND_RESULT)
        assert len(entries) > 0


class TestUpdateBeadsStatus:
    """Behavior 8: Update Beads Status."""

    def test_closes_beads_issue_on_success(
        self,
        tmp_path: Path,
        mock_beads: MockBeadsController,
    ) -> None:
        """Given success, closes beads issue."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase._beads_controller = mock_beads

        phase._close_beads_issue("beads-001", "Phase completed")

        assert len(mock_beads.closed_issues) == 1
        assert mock_beads.closed_issues[0][0] == "beads-001"

    def test_handles_beads_close_failure(
        self,
        tmp_path: Path,
        mock_beads: MockBeadsController,
    ) -> None:
        """Given beads close fails, handles gracefully."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        mock_beads._fail_close = True
        phase._beads_controller = mock_beads

        # Should not raise
        phase._close_beads_issue("beads-001", "Phase completed")

        assert len(mock_beads.closed_issues) == 0


class TestHandleImplementationFailure:
    """Behavior 9: Handle Implementation Failure."""

    def test_stops_on_test_failure(
        self,
        tmp_path: Path,
        sample_phase_doc: Path,
        mock_runner: MockRunner,
    ) -> None:
        """Given test failure, stops and reports."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase._runner = mock_runner

        with patch.object(phase, "_run_tests", return_value=(False, "1 failed")):
            result = phase._execute_single_phase(str(sample_phase_doc))

        assert result["success"] is False
        assert "failed" in result.get("error", "") or "failed" in result.get("test_output", "")

    def test_reports_failure_details(
        self,
        tmp_path: Path,
        sample_phase_doc: Path,
        mock_runner: MockRunner,
    ) -> None:
        """Given failure, includes details in result."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        mock_runner._fail_next = True
        phase._runner = mock_runner

        result = phase._execute_tdd_cycle("test behavior", "context")

        assert result["success"] is False
        assert "error" in result


class TestManageContextBounds:
    """Behavior 10: Manage Context Bounds."""

    def test_respects_200_entry_limit(
        self,
        tmp_path: Path,
    ) -> None:
        """Given many entries, respects limit."""
        cwa = CWAIntegration(max_impl_entries=200)
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        # Add many entries
        entry_ids = []
        for i in range(250):
            entry_id = cwa.store_research(f"doc{i}.md", f"content{i}", f"summary{i}")
            entry_ids.append(entry_id)

        # Build context should handle bounds
        context = phase._build_implementation_context(entry_ids[:100])

        assert len(context.entries) <= 200

    def test_limits_entries_in_context(
        self,
        tmp_path: Path,
    ) -> None:
        """Given too many entries, limits them."""
        cwa = CWAIntegration(max_impl_entries=50)
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        # Add entries
        entry_ids = []
        for i in range(60):
            entry_id = cwa.store_research(f"doc{i}.md", f"content{i}", f"summary{i}")
            entry_ids.append(entry_id)

        # Should only include first 50
        context = phase._build_implementation_context(entry_ids[:50])

        assert len(context.entries) <= 50


class TestResumeFromCheckpoint:
    """Behavior 11: Resume from Checkpoint."""

    def test_resumes_from_last_phase(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
        mock_runner: MockRunner,
    ) -> None:
        """Given checkpoint, resumes from last completed."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase._runner = mock_runner

        checkpoint = {"completed_phases": sample_phase_docs[:2]}

        executed: list[str] = []

        def mock_single(phase_path: str) -> dict[str, Any]:
            executed.append(phase_path)
            return {"success": True}

        with patch.object(phase, "_execute_single_phase", mock_single):
            phase.execute(
                phase_paths=sample_phase_docs,
                mode=AutonomyMode.FULLY_AUTONOMOUS,
                checkpoint=checkpoint,
            )

        # Should only execute the remaining phases
        assert len(executed) == 2
        assert sample_phase_docs[0] not in executed
        assert sample_phase_docs[2] in executed


class TestCreateCommit:
    """Behavior 12: Create Commit After Phase."""

    def test_creates_commit_after_phase(
        self,
        tmp_path: Path,
    ) -> None:
        """Given successful phase, creates commit."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            phase._commit_phase("phase1", "Implemented phase 1")

        # Verify git commands called
        calls = [str(c) for c in mock_run.call_args_list]
        assert any("git" in c and "add" in c for c in calls)
        assert any("git" in c and "commit" in c for c in calls)

    def test_handles_commit_failure(
        self,
        tmp_path: Path,
    ) -> None:
        """Given commit fails, returns gracefully."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="", stderr="error")

            result = phase._commit_phase("phase1", "msg")

        assert result["success"] is False


class TestExecuteMethod:
    """Main execute() method tests."""

    def test_returns_complete_status(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
        mock_runner: MockRunner,
    ) -> None:
        """Given successful execution, returns COMPLETE."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase._runner = mock_runner

        with patch.object(phase, "_run_tests", return_value=(True, "passed")):
            result = phase.execute(
                phase_paths=sample_phase_docs[:1],
                mode=AutonomyMode.FULLY_AUTONOMOUS,
            )

        assert result.status == PhaseStatus.COMPLETE
        assert result.phase_type == PhaseType.IMPLEMENTATION

    def test_returns_failed_status_on_error(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
        mock_runner: MockRunner,
    ) -> None:
        """Given failure, returns FAILED."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase._runner = mock_runner

        with patch.object(phase, "_run_tests", return_value=(False, "failed")):
            result = phase.execute(
                phase_paths=sample_phase_docs[:1],
                mode=AutonomyMode.FULLY_AUTONOMOUS,
            )

        assert result.status == PhaseStatus.FAILED
        assert len(result.errors) > 0

    def test_includes_timing(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
        mock_runner: MockRunner,
    ) -> None:
        """Given execution, includes timing info."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase._runner = mock_runner

        with patch.object(phase, "_run_tests", return_value=(True, "passed")):
            result = phase.execute(
                phase_paths=sample_phase_docs[:1],
                mode=AutonomyMode.FULLY_AUTONOMOUS,
            )

        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.duration_seconds is not None

    def test_handles_empty_phases(
        self,
        tmp_path: Path,
    ) -> None:
        """Given empty phases list, returns completed."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(
            phase_paths=[],
            mode=AutonomyMode.FULLY_AUTONOMOUS,
        )

        assert result.status == PhaseStatus.COMPLETE
        assert "already completed" in result.metadata.get("message", "").lower() or len(result.artifacts) == 0

    def test_closes_beads_issues_on_success(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
        mock_runner: MockRunner,
        mock_beads: MockBeadsController,
    ) -> None:
        """Given beads IDs, closes on success."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase._runner = mock_runner
        phase._beads_controller = mock_beads

        with patch.object(phase, "_run_tests", return_value=(True, "passed")):
            phase.execute(
                phase_paths=sample_phase_docs[:2],
                mode=AutonomyMode.FULLY_AUTONOMOUS,
                beads_issue_ids=["beads-001", "beads-002"],
            )

        assert len(mock_beads.closed_issues) == 2

    def test_records_artifacts(
        self,
        tmp_path: Path,
        sample_phase_docs: list[str],
        mock_runner: MockRunner,
    ) -> None:
        """Given successful phases, records artifacts."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase._runner = mock_runner

        with patch.object(phase, "_run_tests", return_value=(True, "passed")):
            result = phase.execute(
                phase_paths=sample_phase_docs[:2],
                mode=AutonomyMode.FULLY_AUTONOMOUS,
            )

        assert len(result.artifacts) == 2
