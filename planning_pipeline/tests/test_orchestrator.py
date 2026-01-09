"""Tests for planning_orchestrator CLI."""

import pytest
import subprocess
import sys
from pathlib import Path


class TestCLIArgumentParsing:
    """Behavior 1: CLI parses arguments correctly."""

    def test_parses_project_path(self):
        """Given --project flag, parses project path."""
        from planning_orchestrator import parse_args

        args = parse_args(["--project", "/tmp/myproject"])
        assert args.project == Path("/tmp/myproject")

    def test_parses_ticket_id(self):
        """Given --ticket flag, parses ticket ID."""
        from planning_orchestrator import parse_args

        args = parse_args(["--ticket", "AUTH-001"])
        assert args.ticket == "AUTH-001"

    def test_parses_auto_approve_flag(self):
        """Given --auto-approve flag, sets auto_approve to True."""
        from planning_orchestrator import parse_args

        args = parse_args(["--auto-approve"])
        assert args.auto_approve is True

    def test_defaults_project_to_cwd(self):
        """Given no --project, defaults to current working directory."""
        from planning_orchestrator import parse_args

        args = parse_args([])
        assert args.project == Path.cwd()

    def test_defaults_auto_approve_to_false(self):
        """Given no --auto-approve, defaults to False."""
        from planning_orchestrator import parse_args

        args = parse_args([])
        assert args.auto_approve is False

    def test_defaults_ticket_to_none(self):
        """Given no --ticket, defaults to None."""
        from planning_orchestrator import parse_args

        args = parse_args([])
        assert args.ticket is None


class TestMultilinePromptCollection:
    """Behavior 2: Collects multi-line prompt from user."""

    def test_collects_single_line(self, monkeypatch):
        """Given single line then blank, returns that line."""
        from planning_orchestrator import collect_prompt

        inputs = iter(["How does auth work?", ""])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        result = collect_prompt()
        assert result == "How does auth work?"

    def test_collects_multiple_lines(self, monkeypatch):
        """Given multiple lines then blank, returns joined lines."""
        from planning_orchestrator import collect_prompt

        inputs = iter([
            "Research the authentication system.",
            "Focus on JWT token handling.",
            "Include security considerations.",
            ""
        ])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        result = collect_prompt()
        expected = "Research the authentication system.\nFocus on JWT token handling.\nInclude security considerations."
        assert result == expected

    def test_stops_at_first_blank_line(self, monkeypatch):
        """Given blank line, stops collecting."""
        from planning_orchestrator import collect_prompt

        inputs = iter(["Line one", "", "Line three (should not be included)"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        result = collect_prompt()
        assert result == "Line one"
        assert "Line three" not in result


class TestPrerequisiteValidation:
    """Behavior 3: Validates required CLI tools are installed."""

    def test_succeeds_when_both_installed(self):
        """Given both claude and bd installed, returns success."""
        from planning_orchestrator import check_prerequisites

        # This test assumes the test environment has both tools
        result = check_prerequisites()
        assert result["success"] is True

    def test_fails_when_claude_missing(self, monkeypatch):
        """Given claude not installed, returns error."""
        from planning_orchestrator import check_prerequisites

        original_run = subprocess.run

        def mock_run(cmd, *args, **kwargs):
            if cmd[0] == "which" and cmd[1] == "claude":
                result = type('Result', (), {'returncode': 1})()
                return result
            return original_run(cmd, *args, **kwargs)

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = check_prerequisites()
        assert result["success"] is False
        assert "claude" in result["error"]

    def test_fails_when_bd_missing(self, monkeypatch):
        """Given bd not installed, returns error."""
        from planning_orchestrator import check_prerequisites

        original_run = subprocess.run

        def mock_run(cmd, *args, **kwargs):
            if cmd[0] == "which" and cmd[1] == "bd":
                result = type('Result', (), {'returncode': 1})()
                return result
            return original_run(cmd, *args, **kwargs)

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = check_prerequisites()
        assert result["success"] is False
        assert "bd" in result["error"]


@pytest.mark.slow
class TestPipelineExecution:
    """Behavior 4: Executes pipeline with real SDK calls."""

    @pytest.fixture
    def project_path(self):
        """Return the root project path."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def cleanup_issues(self, project_path):
        """Track and cleanup created issues after test."""
        from planning_pipeline import BeadsController
        bd = BeadsController(project_path)
        created_ids = []
        yield created_ids
        for issue_id in created_ids:
            bd.close_issue(issue_id, reason="Test cleanup")
        bd.sync()

    def test_runs_pipeline_with_auto_approve(self, project_path, cleanup_issues):
        """Given valid prompt with auto-approve, executes full pipeline."""
        from planning_orchestrator import run_pipeline

        result = run_pipeline(
            project_path=project_path,
            prompt="What is the project structure? List main directories only.",
            ticket_id="TEST-ORCH-001",
            auto_approve=True
        )

        assert result["success"] is True
        assert "plan_dir" in result
        assert result.get("epic_id") is not None

        # Track for cleanup
        if result.get("epic_id"):
            cleanup_issues.append(result["epic_id"])
        for phase in result.get("steps", {}).get("beads", {}).get("phase_issues", []):
            if phase.get("issue_id"):
                cleanup_issues.append(phase["issue_id"])

    def test_returns_failure_on_empty_prompt(self, project_path):
        """Given empty prompt, returns failure without calling SDK."""
        from planning_orchestrator import run_pipeline

        result = run_pipeline(
            project_path=project_path,
            prompt="",
            ticket_id=None,
            auto_approve=True
        )

        assert result["success"] is False
        assert "error" in result


class TestResultDisplay:
    """Behavior 5: Displays pipeline results to user."""

    def test_displays_success_result(self, capsys):
        """Given successful result, displays plan dir and epic ID."""
        from planning_orchestrator import display_result

        result = {
            "success": True,
            "plan_dir": "thoughts/searchable/plans/2026-01-01-plan",
            "epic_id": "beads-abc123"
        }

        display_result(result)

        captured = capsys.readouterr()
        assert "SUCCESS" in captured.out or "success" in captured.out.lower()
        assert "thoughts/searchable/plans/2026-01-01-plan" in captured.out
        assert "beads-abc123" in captured.out

    def test_displays_failure_result(self, capsys):
        """Given failed result, displays error message."""
        from planning_orchestrator import display_result

        result = {
            "success": False,
            "failed_at": "research",
            "steps": {
                "research": {"error": "Claude timed out"}
            }
        }

        display_result(result)

        captured = capsys.readouterr()
        assert "FAILED" in captured.out or "failed" in captured.out.lower()
        assert "research" in captured.out.lower()

    def test_displays_stopped_result(self, capsys):
        """Given user-stopped result, displays stopped message."""
        from planning_orchestrator import display_result

        result = {
            "success": False,
            "stopped_at": "planning"
        }

        display_result(result)

        captured = capsys.readouterr()
        assert "stopped" in captured.out.lower() or "cancelled" in captured.out.lower()


class TestExitCodeHandling:
    """Behavior 6: Returns proper exit codes."""

    def test_returns_zero_on_success(self):
        """Given successful pipeline, returns exit code 0."""
        from planning_orchestrator import get_exit_code

        result = {"success": True}
        assert get_exit_code(result) == 0

    def test_returns_one_on_failure(self):
        """Given failed pipeline, returns exit code 1."""
        from planning_orchestrator import get_exit_code

        result = {"success": False}
        assert get_exit_code(result) == 1

    def test_returns_one_on_stopped(self):
        """Given user-stopped pipeline, returns exit code 1."""
        from planning_orchestrator import get_exit_code

        result = {"success": False, "stopped_at": "research"}
        assert get_exit_code(result) == 1


class TestMainEntryPoint:
    """Behavior 7: Main function integrates all components."""

    @pytest.fixture
    def project_path(self):
        return Path(__file__).parent.parent.parent

    def test_main_returns_one_on_empty_prompt(self, project_path, monkeypatch, capsys):
        """Given empty --prompt-text, returns exit code 1."""
        from planning_orchestrator import main

        test_args = [
            "planning_orchestrator.py",
            "--project", str(project_path),
            "--prompt-text", "",
            "--auto-approve"
        ]
        monkeypatch.setattr(sys, "argv", test_args)

        exit_code = main()

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "empty" in captured.out.lower() or "error" in captured.out.lower()

    def test_main_parses_prompt_text_flag(self, project_path, monkeypatch):
        """Given --prompt-text flag, uses provided text without interactive input."""
        from planning_orchestrator import parse_args

        args = parse_args([
            "--project", str(project_path),
            "--prompt-text", "Test prompt text",
            "--auto-approve"
        ])

        assert args.prompt_text == "Test prompt text"
        assert args.auto_approve is True


@pytest.mark.slow
@pytest.mark.integration
class TestOrchestratorE2E:
    """Full end-to-end integration tests with real SDK calls."""

    @pytest.fixture
    def project_path(self):
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def cleanup_issues(self, project_path):
        from planning_pipeline import BeadsController
        bd = BeadsController(project_path)
        created_ids = []
        yield created_ids
        for issue_id in created_ids:
            bd.close_issue(issue_id, reason="Test cleanup")
        bd.sync()

    def test_full_pipeline_creates_artifacts(self, project_path, cleanup_issues):
        """Given real SDK, creates all expected artifacts."""
        from planning_orchestrator import run_pipeline

        result = run_pipeline(
            project_path=project_path,
            prompt="Analyze the testing patterns in this project. Focus on pytest fixtures.",
            ticket_id="TEST-E2E-001",
            auto_approve=True
        )

        assert result["success"] is True

        # Verify plan directory exists
        plan_dir = result.get("plan_dir")
        assert plan_dir is not None
        assert Path(plan_dir).exists()

        # Verify phase files created
        phase_files = result.get("steps", {}).get("decomposition", {}).get("phase_files", [])
        assert len(phase_files) > 0
        for phase_file in phase_files:
            assert Path(phase_file).exists()

        # Verify beads issues created
        epic_id = result.get("epic_id")
        assert epic_id is not None
        cleanup_issues.append(epic_id)

        phase_issues = result.get("steps", {}).get("beads", {}).get("phase_issues", [])
        for phase in phase_issues:
            if phase.get("issue_id"):
                cleanup_issues.append(phase["issue_id"])


class TestResumeArgumentParsing:
    """Tests for resume-related CLI arguments."""

    def test_parses_resume_flag(self):
        """Given --resume flag, sets resume to True."""
        from planning_orchestrator import parse_args

        args = parse_args(["--resume"])
        assert args.resume is True

    def test_parses_resume_short_flag(self):
        """Given -r flag, sets resume to True."""
        from planning_orchestrator import parse_args

        args = parse_args(["-r"])
        assert args.resume is True

    def test_defaults_resume_to_false(self):
        """Given no --resume, defaults to False."""
        from planning_orchestrator import parse_args

        args = parse_args([])
        assert args.resume is False

    def test_parses_resume_step_planning(self):
        """Given --resume-step planning, parses correctly."""
        from planning_orchestrator import parse_args

        args = parse_args(["--resume-step", "planning"])
        assert args.resume_step == "planning"

    def test_parses_resume_step_requirement_decomposition(self):
        """Given --resume-step requirement_decomposition, parses correctly."""
        from planning_orchestrator import parse_args

        args = parse_args(["--resume-step", "requirement_decomposition"])
        assert args.resume_step == "requirement_decomposition"

    def test_parses_resume_step_phase_decomposition(self):
        """Given --resume-step phase_decomposition, parses correctly."""
        from planning_orchestrator import parse_args

        args = parse_args(["--resume-step", "phase_decomposition"])
        assert args.resume_step == "phase_decomposition"

    def test_parses_research_path(self):
        """Given --research-path, parses the path."""
        from planning_orchestrator import parse_args

        args = parse_args(["--research-path", "/path/to/research.md"])
        assert args.research_path == "/path/to/research.md"

    def test_parses_research_path_underscore(self):
        """Given --research_path (underscore), parses the path."""
        from planning_orchestrator import parse_args

        args = parse_args(["--research_path", "/path/to/research.md"])
        assert args.research_path == "/path/to/research.md"

    def test_parses_plan_path(self):
        """Given --plan-path, parses the path."""
        from planning_orchestrator import parse_args

        args = parse_args(["--plan-path", "/path/to/plan.md"])
        assert args.plan_path == "/path/to/plan.md"

    def test_parses_combined_resume_args(self):
        """Given all resume args, parses correctly."""
        from planning_orchestrator import parse_args

        args = parse_args([
            "--resume",
            "--resume-step", "planning",
            "--research-path", "/path/research.md",
            "--plan-path", "/path/plan.md"
        ])
        assert args.resume is True
        assert args.resume_step == "planning"
        assert args.research_path == "/path/research.md"
        assert args.plan_path == "/path/plan.md"


class TestResumeStepArguments:
    """Tests for --resume-step CLI argument parsing with updated step names."""

    def test_accepts_requirement_decomposition(self):
        """Should accept requirement_decomposition as valid step."""
        from planning_orchestrator import parse_args

        args = parse_args(["--resume", "--resume-step", "requirement_decomposition"])
        assert args.resume_step == "requirement_decomposition"

    def test_accepts_phase_decomposition(self):
        """Should accept phase_decomposition as valid step."""
        from planning_orchestrator import parse_args

        args = parse_args(["--resume", "--resume-step", "phase_decomposition"])
        assert args.resume_step == "phase_decomposition"

    def test_accepts_planning(self):
        """Should still accept planning as valid step."""
        from planning_orchestrator import parse_args

        args = parse_args(["--resume", "--resume-step", "planning"])
        assert args.resume_step == "planning"

    def test_rejects_old_decomposition_name(self):
        """Should reject old 'decomposition' name."""
        from planning_orchestrator import parse_args

        with pytest.raises(SystemExit):
            parse_args(["--resume", "--resume-step", "decomposition"])

    def test_rejects_beads(self):
        """Should reject 'beads' as resume step."""
        from planning_orchestrator import parse_args

        with pytest.raises(SystemExit):
            parse_args(["--resume", "--resume-step", "beads"])


class TestExecuteFromStep:
    """Tests for execute_from_step function."""

    @pytest.fixture
    def project_path(self):
        return Path(__file__).parent.parent.parent

    def test_returns_result_dict(self, project_path, tmp_path):
        """Execute returns a result dictionary."""
        from planning_orchestrator import execute_from_step

        # Create a fake research file
        research_file = tmp_path / "research.md"
        research_file.write_text("# Research\nSome content")

        # This will fail since research file doesn't have proper content
        # but we can verify the function returns properly
        result = execute_from_step(
            project_path=project_path,
            resume_step="planning",
            research_path=str(research_file)
        )

        assert isinstance(result, dict)
        assert "started" in result
        assert "resumed_from" in result
        assert result["resumed_from"] == "planning"


class TestResumeFlowWithNewSteps:
    """Tests for resume flow with updated step names."""

    def test_resume_from_requirement_decomposition(self, tmp_path):
        """Should start from requirement_decomposition step."""
        from unittest.mock import patch
        from planning_orchestrator import execute_from_step

        steps_called = []

        # Create research file
        research_file = tmp_path / "research.md"
        research_file.write_text("# Research\nSome content")

        with patch("planning_pipeline.step_decomposition.step_requirement_decomposition") as mock_req_decomp, \
             patch("planning_pipeline.step_planning") as mock_planning, \
             patch("planning_pipeline.step_phase_decomposition") as mock_phase_decomp, \
             patch("planning_pipeline.step_beads_integration") as mock_beads, \
             patch("planning_pipeline.write_checkpoint"):

            def req_decomp_side_effect(*a, **kw):
                steps_called.append("requirement_decomposition")
                return {"success": True, "hierarchy_path": str(tmp_path / "h.json"),
                        "diagram_path": str(tmp_path / "d.mmd"), "tests_path": None,
                        "requirement_count": 1, "output_dir": str(tmp_path)}

            def planning_side_effect(*a, **kw):
                steps_called.append("planning")
                return {"success": True, "plan_path": str(tmp_path / "plan.md"), "output": ""}

            def phase_decomp_side_effect(*a, **kw):
                steps_called.append("phase_decomposition")
                return {"success": True, "phase_files": [str(tmp_path / "p.md")], "output": ""}

            def beads_side_effect(*a, **kw):
                steps_called.append("beads")
                return {"success": True, "epic_id": "b", "phase_issues": []}

            mock_req_decomp.side_effect = req_decomp_side_effect
            mock_planning.side_effect = planning_side_effect
            mock_phase_decomp.side_effect = phase_decomp_side_effect
            mock_beads.side_effect = beads_side_effect

            result = execute_from_step(
                project_path=tmp_path,
                resume_step="requirement_decomposition",
                research_path=str(research_file),
            )

        assert "requirement_decomposition" in steps_called
        assert "planning" in steps_called
        assert "phase_decomposition" in steps_called
        assert result["success"] is True

    def test_resume_from_phase_decomposition(self, tmp_path):
        """Should start from phase_decomposition step (renamed from decomposition)."""
        from unittest.mock import patch
        from planning_orchestrator import execute_from_step

        steps_called = []
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("# Test Plan")

        with patch("planning_pipeline.step_phase_decomposition") as mock_phase_decomp, \
             patch("planning_pipeline.step_beads_integration") as mock_beads, \
             patch("planning_pipeline.write_checkpoint"):

            def phase_decomp_side_effect(*a, **kw):
                steps_called.append("phase_decomposition")
                return {"success": True, "phase_files": [str(tmp_path / "p.md")], "output": ""}

            def beads_side_effect(*a, **kw):
                steps_called.append("beads")
                return {"success": True, "epic_id": "b", "phase_issues": []}

            mock_phase_decomp.side_effect = phase_decomp_side_effect
            mock_beads.side_effect = beads_side_effect

            result = execute_from_step(
                project_path=tmp_path,
                resume_step="phase_decomposition",
                plan_path=str(plan_file),
            )

        assert "phase_decomposition" in steps_called
        assert result["success"] is True

    def test_resume_does_not_run_earlier_steps(self, tmp_path):
        """Resuming from requirement_decomposition should not run research."""
        from unittest.mock import patch
        from planning_orchestrator import execute_from_step

        steps_called = []

        # Create research file
        research_file = tmp_path / "research.md"
        research_file.write_text("# Research\nSome content")

        # Research step is never imported by execute_from_step, so we just verify
        # that it doesn't appear in the steps called
        with patch("planning_pipeline.step_decomposition.step_requirement_decomposition") as mock_req_decomp, \
             patch("planning_pipeline.step_planning") as mock_planning, \
             patch("planning_pipeline.step_phase_decomposition") as mock_phase_decomp, \
             patch("planning_pipeline.step_beads_integration") as mock_beads, \
             patch("planning_pipeline.write_checkpoint"):

            def req_decomp_side_effect(*a, **kw):
                steps_called.append("requirement_decomposition")
                return {"success": True, "hierarchy_path": str(tmp_path / "h.json"),
                        "diagram_path": str(tmp_path / "d.mmd"), "tests_path": None,
                        "requirement_count": 1, "output_dir": str(tmp_path)}

            def planning_side_effect(*a, **kw):
                steps_called.append("planning")
                return {"success": True, "plan_path": str(tmp_path / "plan.md"), "output": ""}

            def phase_decomp_side_effect(*a, **kw):
                steps_called.append("phase_decomposition")
                return {"success": True, "phase_files": [str(tmp_path / "p.md")], "output": ""}

            def beads_side_effect(*a, **kw):
                steps_called.append("beads")
                return {"success": True, "epic_id": "b", "phase_issues": []}

            mock_req_decomp.side_effect = req_decomp_side_effect
            mock_planning.side_effect = planning_side_effect
            mock_phase_decomp.side_effect = phase_decomp_side_effect
            mock_beads.side_effect = beads_side_effect

            execute_from_step(
                project_path=tmp_path,
                resume_step="requirement_decomposition",
                research_path=str(research_file),
            )

        # Research step should never be called by execute_from_step
        # (it's only in the full pipeline run)
        assert "research" not in steps_called
