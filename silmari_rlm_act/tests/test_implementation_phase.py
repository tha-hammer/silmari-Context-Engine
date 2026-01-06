"""Tests for Implementation Phase - Simple Claude Loop.

This module tests the ImplementationPhase class which:
- Injects beads tracking into TDD plans
- Invokes Claude with --dangerously-skip-permissions
- Checks for completion via beads status
- Runs tests to verify implementation
"""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch, MagicMock

import pytest

from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import AutonomyMode, PhaseStatus, PhaseType
from silmari_rlm_act.phases.implementation import ImplementationPhase


@pytest.fixture
def sample_plan(tmp_path: Path) -> Path:
    """Create a sample TDD plan document."""
    plan = tmp_path / "00-overview.md"
    plan.write_text("""# TDD Plan: User Authentication

## Overview

Implement user authentication functionality.

## Phases

1. Phase 01: Login
2. Phase 02: Auth tokens
3. Phase 03: Session management
""")
    return plan


@pytest.fixture
def cwa() -> CWAIntegration:
    """Create CWA integration."""
    return CWAIntegration()


class TestInjectBeadsIntoPlan:
    """Test beads injection into plan content."""

    def test_injects_epic_id(
        self,
        tmp_path: Path,
        sample_plan: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given epic ID, injects into plan."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        result = phase._inject_beads_into_plan(
            plan_path=sample_plan,
            epic_id="beads-epic-001",
            issue_ids=[],
        )

        assert "beads-epic-001" in result
        assert "Epic" in result

    def test_injects_issue_ids(
        self,
        tmp_path: Path,
        sample_plan: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given issue IDs, injects into plan."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        result = phase._inject_beads_into_plan(
            plan_path=sample_plan,
            epic_id=None,
            issue_ids=["beads-001", "beads-002", "beads-003"],
        )

        assert "beads-001" in result
        assert "beads-002" in result
        assert "beads-003" in result
        assert "Phase 1:" in result
        assert "Phase 2:" in result

    def test_preserves_original_content(
        self,
        tmp_path: Path,
        sample_plan: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given plan, preserves original content."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        result = phase._inject_beads_into_plan(
            plan_path=sample_plan,
            epic_id=None,
            issue_ids=[],
        )

        assert "User Authentication" in result
        assert "## Overview" in result
        assert "## Phases" in result

    def test_adds_beads_commands(
        self,
        tmp_path: Path,
        sample_plan: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given plan, adds bd command reference."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        result = phase._inject_beads_into_plan(
            plan_path=sample_plan,
            epic_id=None,
            issue_ids=[],
        )

        assert "bd ready" in result
        assert "bd close" in result
        assert "bd sync" in result


class TestInvokeClaude:
    """Test Claude invocation."""

    def test_invokes_claude_with_permissions_bypass(
        self,
        tmp_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given prompt, invokes claude with --dangerously-skip-permissions."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Implementation complete",
                stderr="",
            )

            result = phase._invoke_claude("Test prompt")

        assert result["success"] is True
        call_args = mock_run.call_args[0][0]
        assert "claude" in call_args
        assert "--dangerously-skip-permissions" in call_args

    def test_handles_timeout(
        self,
        tmp_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given timeout, returns error."""
        import subprocess
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=3600)

            result = phase._invoke_claude("Test prompt")

        assert result["success"] is False
        assert "timed out" in result["error"].lower()

    def test_handles_claude_not_found(
        self,
        tmp_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given claude not installed, returns error."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            result = phase._invoke_claude("Test prompt")

        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestCheckCompletion:
    """Test completion checking via beads."""

    def test_returns_true_when_all_closed(
        self,
        tmp_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given all issues closed, returns True."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                stdout="Status: closed\nTitle: Test",
                returncode=0,
            )

            result = phase._check_completion(["beads-001", "beads-002"])

        assert result is True

    def test_returns_false_when_open(
        self,
        tmp_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given open issues, returns False."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                stdout="Status: open\nTitle: Test",
                returncode=0,
            )

            result = phase._check_completion(["beads-001"])

        assert result is False

    def test_returns_true_for_empty_list(
        self,
        tmp_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given empty issue list, returns True."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        result = phase._check_completion([])

        assert result is True

    def test_handles_bd_error(
        self,
        tmp_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given bd error, returns False."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("bd error")

            result = phase._check_completion(["beads-001"])

        assert result is False


class TestRunTests:
    """Test test suite execution."""

    def test_runs_pytest(
        self,
        tmp_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given implementation, runs pytest."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="5 passed",
                stderr="",
            )

            passed, output = phase._run_tests()

        assert passed is True
        assert "passed" in output
        call_args = mock_run.call_args[0][0]
        assert "pytest" in call_args

    def test_detects_failure(
        self,
        tmp_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given failing tests, returns failure."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="2 failed",
                stderr="",
            )

            passed, output = phase._run_tests()

        assert passed is False

    def test_falls_back_to_make_test(
        self,
        tmp_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given pytest not found, falls back to make test."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise FileNotFoundError()
            return Mock(returncode=0, stdout="OK", stderr="")

        with patch("subprocess.run", side_effect=side_effect):
            passed, output = phase._run_tests()

        assert passed is True


class TestExecute:
    """Test main execute method."""

    def test_returns_complete_on_success(
        self,
        tmp_path: Path,
        sample_plan: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given successful loop, returns COMPLETE."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        with patch.object(phase, "_invoke_claude", return_value={"success": True, "output": "Done", "error": ""}):
            with patch.object(phase, "_check_completion", return_value=True):
                with patch.object(phase, "_run_tests", return_value=(True, "passed")):
                    result = phase.execute(
                        phase_paths=[str(sample_plan)],
                        mode=AutonomyMode.FULLY_AUTONOMOUS,
                        beads_issue_ids=["beads-001"],
                    )

        assert result.status == PhaseStatus.COMPLETE
        assert result.phase_type == PhaseType.IMPLEMENTATION

    def test_returns_failed_on_max_iterations(
        self,
        tmp_path: Path,
        sample_plan: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given max iterations reached, returns FAILED."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase.LOOP_SLEEP = 0  # Speed up test

        with patch.object(phase, "_invoke_claude", return_value={"success": True, "output": "", "error": ""}):
            with patch.object(phase, "_check_completion", return_value=False):
                result = phase.execute(
                    phase_paths=[str(sample_plan)],
                    mode=AutonomyMode.FULLY_AUTONOMOUS,
                    max_iterations=2,
                )

        assert result.status == PhaseStatus.FAILED
        assert "max iterations" in result.errors[0].lower()

    def test_handles_missing_plan(
        self,
        tmp_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given missing plan, returns FAILED."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(
            phase_paths=[str(tmp_path / "nonexistent.md")],
            mode=AutonomyMode.FULLY_AUTONOMOUS,
        )

        assert result.status == PhaseStatus.FAILED
        assert "not found" in result.errors[0].lower()

    def test_handles_empty_phases(
        self,
        tmp_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given empty phases, returns COMPLETE."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(
            phase_paths=[],
            mode=AutonomyMode.FULLY_AUTONOMOUS,
        )

        assert result.status == PhaseStatus.COMPLETE

    def test_includes_metadata(
        self,
        tmp_path: Path,
        sample_plan: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given execution, includes metadata."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        with patch.object(phase, "_invoke_claude", return_value={"success": True, "output": "", "error": ""}):
            with patch.object(phase, "_check_completion", return_value=True):
                with patch.object(phase, "_run_tests", return_value=(True, "passed")):
                    result = phase.execute(
                        phase_paths=[str(sample_plan)],
                        mode=AutonomyMode.FULLY_AUTONOMOUS,
                        beads_issue_ids=["beads-001"],
                    )

        assert "iterations" in result.metadata
        assert "mode" in result.metadata
        assert result.metadata["mode"] == "autonomous_loop"

    def test_continues_on_test_failure(
        self,
        tmp_path: Path,
        sample_plan: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Given test failure after completion, continues loop."""
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase.LOOP_SLEEP = 0

        check_calls = [0]
        test_calls = [0]

        def mock_check(ids):
            check_calls[0] += 1
            return True  # Always say complete

        def mock_tests():
            test_calls[0] += 1
            if test_calls[0] == 1:
                return (False, "failed")  # Fail first time
            return (True, "passed")  # Pass second time

        with patch.object(phase, "_invoke_claude", return_value={"success": True, "output": "", "error": ""}):
            with patch.object(phase, "_check_completion", mock_check):
                with patch.object(phase, "_run_tests", mock_tests):
                    result = phase.execute(
                        phase_paths=[str(sample_plan)],
                        mode=AutonomyMode.FULLY_AUTONOMOUS,
                        beads_issue_ids=["beads-001"],
                        max_iterations=5,
                    )

        assert result.status == PhaseStatus.COMPLETE
        assert test_calls[0] >= 2  # Ran tests multiple times
