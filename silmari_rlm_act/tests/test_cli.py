"""Tests for CLI entry point.

This module tests the command-line interface for the silmari-rlm-act pipeline.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from silmari_rlm_act.models import (
    AutonomyMode,
    PhaseResult,
    PhaseStatus,
    PhaseType,
)


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    project = tmp_path / "test_project"
    project.mkdir()
    return project


# ===========================================================================
# Behavior 1: CLI Help
# ===========================================================================


class TestCLIHelp:
    """Tests for CLI help output."""

    def test_help_shows_usage(self, cli_runner: CliRunner) -> None:
        """--help shows usage information."""
        from silmari_rlm_act.cli import main

        result = cli_runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "silmari-rlm-act" in result.output or "main" in result.output

    def test_help_shows_commands(self, cli_runner: CliRunner) -> None:
        """--help lists available commands."""
        from silmari_rlm_act.cli import main

        result = cli_runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "run" in result.output
        assert "resume" in result.output
        assert "status" in result.output


# ===========================================================================
# Behavior 2: Run Command
# ===========================================================================


class TestRunCommand:
    """Tests for the run command."""

    def test_run_requires_question(self, cli_runner: CliRunner) -> None:
        """run command requires --question argument."""
        from silmari_rlm_act.cli import main

        result = cli_runner.invoke(main, ["run"])

        assert result.exit_code != 0
        assert "question" in result.output.lower() or "missing" in result.output.lower()

    def test_run_with_question_starts_pipeline(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
    ) -> None:
        """run command starts the pipeline with the research question."""
        from silmari_rlm_act.cli import main

        mock_result = PhaseResult(
            phase_type=PhaseType.RESEARCH,
            status=PhaseStatus.COMPLETE,
        )

        with patch("silmari_rlm_act.cli.RLMActPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = mock_result
            mock_pipeline_cls.return_value = mock_pipeline

            cli_runner.invoke(
                main,
                [
                    "run",
                    "--question",
                    "How does auth work?",
                    "--project",
                    str(temp_project),
                ],
            )

            # Should call pipeline.run()
            mock_pipeline.run.assert_called_once()


# ===========================================================================
# Behavior 3: Mode Selection
# ===========================================================================


class TestModeSelection:
    """Tests for autonomy mode selection."""

    def test_default_mode_is_checkpoint(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
    ) -> None:
        """Default mode is checkpoint."""
        from silmari_rlm_act.cli import main

        mock_result = PhaseResult(
            phase_type=PhaseType.RESEARCH,
            status=PhaseStatus.COMPLETE,
        )

        with patch("silmari_rlm_act.cli.RLMActPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = mock_result
            mock_pipeline_cls.return_value = mock_pipeline

            cli_runner.invoke(
                main,
                [
                    "run",
                    "--question",
                    "test",
                    "--project",
                    str(temp_project),
                ],
            )

            # Check the autonomy_mode passed to pipeline
            call_kwargs = mock_pipeline_cls.call_args.kwargs
            assert call_kwargs.get("autonomy_mode") == AutonomyMode.CHECKPOINT

    def test_autonomous_mode_flag(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
    ) -> None:
        """--autonomous flag sets fully autonomous mode."""
        from silmari_rlm_act.cli import main

        mock_result = PhaseResult(
            phase_type=PhaseType.RESEARCH,
            status=PhaseStatus.COMPLETE,
        )

        with patch("silmari_rlm_act.cli.RLMActPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = mock_result
            mock_pipeline_cls.return_value = mock_pipeline

            cli_runner.invoke(
                main,
                [
                    "run",
                    "--question",
                    "test",
                    "--project",
                    str(temp_project),
                    "--autonomous",
                ],
            )

            call_kwargs = mock_pipeline_cls.call_args.kwargs
            assert call_kwargs.get("autonomy_mode") == AutonomyMode.FULLY_AUTONOMOUS


# ===========================================================================
# Behavior 4: Status Command
# ===========================================================================


class TestStatusCommand:
    """Tests for the status command."""

    def test_status_shows_pipeline_state(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
    ) -> None:
        """status command shows current pipeline state."""
        from silmari_rlm_act.cli import main

        with patch("silmari_rlm_act.cli.RLMActPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.get_status_summary.return_value = {
                "project_path": str(temp_project),
                "autonomy_mode": "checkpoint",
                "phases_completed": ["research"],
                "phases_pending": ["decomposition", "tdd_planning"],
                "next_phase": "decomposition",
                "all_complete": False,
            }
            mock_pipeline_cls.return_value = mock_pipeline

            result = cli_runner.invoke(
                main,
                ["status", "--project", str(temp_project)],
            )

            assert result.exit_code == 0
            assert "research" in result.output.lower()


# ===========================================================================
# Behavior 5: Resume Command
# ===========================================================================


class TestResumeCommand:
    """Tests for the resume command."""

    def test_resume_loads_checkpoint(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
    ) -> None:
        """resume command loads from checkpoint."""
        from silmari_rlm_act.cli import main

        mock_result = PhaseResult(
            phase_type=PhaseType.DECOMPOSITION,
            status=PhaseStatus.COMPLETE,
        )

        with patch("silmari_rlm_act.cli.RLMActPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.resume_from_checkpoint.return_value = True
            mock_pipeline.run.return_value = mock_result
            mock_pipeline_cls.return_value = mock_pipeline

            cli_runner.invoke(
                main,
                ["resume", "--project", str(temp_project)],
            )

            # Should call resume_from_checkpoint
            mock_pipeline.resume_from_checkpoint.assert_called_once()


# ===========================================================================
# Behavior 6: Research Path Option (REQ_000)
# ===========================================================================


@pytest.fixture
def temp_research_doc(tmp_path: Path) -> Path:
    """Create a temporary research document."""
    doc = tmp_path / "research.md"
    doc.write_text("# Research Document\n\nTest content.")
    return doc


class TestResearchPathOption:
    """Tests for the --research-path option (REQ_000)."""

    def test_research_path_option_defined(self, cli_runner: CliRunner) -> None:
        """REQ_000.1: --research-path option is defined in CLI."""
        from silmari_rlm_act.cli import main

        result = cli_runner.invoke(main, ["run", "--help"])

        assert result.exit_code == 0
        assert "--research-path" in result.output
        assert "existing research document" in result.output.lower()

    def test_research_path_skips_research_text_in_help(
        self, cli_runner: CliRunner
    ) -> None:
        """REQ_000.1: Help text mentions skipping research phase."""
        from silmari_rlm_act.cli import main

        result = cli_runner.invoke(main, ["run", "--help"])

        assert "skips" in result.output.lower() or "skip" in result.output.lower()

    def test_research_path_validates_file_exists(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
    ) -> None:
        """REQ_000.4: Invalid paths produce clear error messages."""
        from silmari_rlm_act.cli import main

        result = cli_runner.invoke(
            main,
            [
                "run",
                "--research-path",
                "/nonexistent/path.md",
                "--project",
                str(temp_project),
            ],
        )

        assert result.exit_code != 0
        assert "does not exist" in result.output.lower() or "invalid" in result.output.lower()

    def test_research_path_rejects_directories(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
    ) -> None:
        """REQ_000.4: Paths to directories are rejected."""
        from silmari_rlm_act.cli import main

        result = cli_runner.invoke(
            main,
            [
                "run",
                "--research-path",
                str(temp_project),  # This is a directory
                "--project",
                str(temp_project),
            ],
        )

        assert result.exit_code != 0
        assert "directory" in result.output.lower() or "invalid" in result.output.lower()

    def test_research_path_without_question_succeeds(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
        temp_research_doc: Path,
    ) -> None:
        """REQ_000.5: Command succeeds with --research-path alone."""
        from silmari_rlm_act.cli import main

        mock_result = PhaseResult(
            phase_type=PhaseType.IMPLEMENTATION,
            status=PhaseStatus.COMPLETE,
        )

        with patch("silmari_rlm_act.cli.RLMActPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = mock_result
            mock_pipeline_cls.return_value = mock_pipeline

            result = cli_runner.invoke(
                main,
                [
                    "run",
                    "--research-path",
                    str(temp_research_doc),
                    "--project",
                    str(temp_project),
                ],
            )

            # Should not fail due to missing --question
            assert result.exit_code == 0 or mock_pipeline.run.called

    def test_research_path_passed_to_pipeline(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
        temp_research_doc: Path,
    ) -> None:
        """REQ_000.2: research_path is passed to pipeline.run() kwargs."""
        from silmari_rlm_act.cli import main

        mock_result = PhaseResult(
            phase_type=PhaseType.IMPLEMENTATION,
            status=PhaseStatus.COMPLETE,
        )

        with patch("silmari_rlm_act.cli.RLMActPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = mock_result
            mock_pipeline_cls.return_value = mock_pipeline

            cli_runner.invoke(
                main,
                [
                    "run",
                    "--research-path",
                    str(temp_research_doc),
                    "--project",
                    str(temp_project),
                ],
            )

            # Check pipeline.run was called with research_path
            call_kwargs = mock_pipeline.run.call_args.kwargs
            assert "research_path" in call_kwargs
            assert call_kwargs["research_path"] == str(temp_research_doc)

    def test_question_alone_still_works(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
    ) -> None:
        """REQ_000.5: Command succeeds with --question alone (original behavior)."""
        from silmari_rlm_act.cli import main

        mock_result = PhaseResult(
            phase_type=PhaseType.RESEARCH,
            status=PhaseStatus.COMPLETE,
        )

        with patch("silmari_rlm_act.cli.RLMActPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = mock_result
            mock_pipeline_cls.return_value = mock_pipeline

            result = cli_runner.invoke(
                main,
                [
                    "run",
                    "--question",
                    "Test question",
                    "--project",
                    str(temp_project),
                ],
            )

            # Original behavior should still work
            mock_pipeline.run.assert_called_once()

    def test_both_question_and_research_path_warns(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
        temp_research_doc: Path,
    ) -> None:
        """REQ_000.5: Warning when both --question and --research-path provided."""
        from silmari_rlm_act.cli import main

        mock_result = PhaseResult(
            phase_type=PhaseType.IMPLEMENTATION,
            status=PhaseStatus.COMPLETE,
        )

        with patch("silmari_rlm_act.cli.RLMActPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = mock_result
            mock_pipeline_cls.return_value = mock_pipeline

            result = cli_runner.invoke(
                main,
                [
                    "run",
                    "--question",
                    "Test question",
                    "--research-path",
                    str(temp_research_doc),
                    "--project",
                    str(temp_project),
                ],
            )

            # Should show warning
            assert "warning" in result.output.lower() or "ignored" in result.output.lower()

    def test_no_question_no_research_path_no_resume_fails(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
    ) -> None:
        """REQ_000.5: Command fails without any of the required options."""
        from silmari_rlm_act.cli import main

        result = cli_runner.invoke(
            main,
            ["run", "--project", str(temp_project)],
        )

        assert result.exit_code != 0
        assert (
            "question" in result.output.lower()
            or "required" in result.output.lower()
        )


# ===========================================================================
# Behavior 7: Plan Path Option (REQ_001)
# ===========================================================================


@pytest.fixture
def temp_plan_doc(tmp_path: Path) -> Path:
    """Create a temporary plan/hierarchy JSON document."""
    import json

    doc = tmp_path / "hierarchy.json"
    hierarchy = {
        "requirements": [
            {
                "id": "REQ_001",
                "description": "Test requirement",
                "type": "parent",
                "parent_id": None,
                "children": [],
                "acceptance_criteria": [],
                "implementation": None,
                "testable_properties": [],
                "function_id": None,
                "related_concepts": [],
                "category": "functional",
            }
        ],
        "metadata": {"source": "test"},
    }
    doc.write_text(json.dumps(hierarchy, indent=2))
    return doc


class TestPlanPathOption:
    """Tests for the --plan-path option (REQ_001)."""

    def test_plan_path_option_defined(self, cli_runner: CliRunner) -> None:
        """REQ_001.1: --plan-path option is defined in CLI."""
        from silmari_rlm_act.cli import main

        result = cli_runner.invoke(main, ["run", "--help"])

        assert result.exit_code == 0
        assert "--plan-path" in result.output

    def test_plan_path_help_mentions_skip_decomposition(
        self, cli_runner: CliRunner
    ) -> None:
        """REQ_001.1: Help text mentions skipping decomposition phase."""
        from silmari_rlm_act.cli import main

        result = cli_runner.invoke(main, ["run", "--help"])

        assert "decomposition" in result.output.lower() or "hierarchy" in result.output.lower()

    def test_plan_path_validates_file_exists(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
    ) -> None:
        """REQ_001.1: Invalid paths produce clear error messages."""
        from silmari_rlm_act.cli import main

        result = cli_runner.invoke(
            main,
            [
                "run",
                "--plan-path",
                "/nonexistent/hierarchy.json",
                "--project",
                str(temp_project),
            ],
        )

        assert result.exit_code != 0
        assert "does not exist" in result.output.lower() or "invalid" in result.output.lower()

    def test_plan_path_rejects_directories(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
    ) -> None:
        """REQ_001.1: Paths to directories are rejected."""
        from silmari_rlm_act.cli import main

        result = cli_runner.invoke(
            main,
            [
                "run",
                "--plan-path",
                str(temp_project),  # This is a directory
                "--project",
                str(temp_project),
            ],
        )

        assert result.exit_code != 0
        assert "directory" in result.output.lower() or "invalid" in result.output.lower()

    def test_plan_path_without_question_succeeds(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_001.4: Command succeeds with --plan-path alone (no --question required)."""
        from silmari_rlm_act.cli import main

        mock_result = PhaseResult(
            phase_type=PhaseType.IMPLEMENTATION,
            status=PhaseStatus.COMPLETE,
        )

        with patch("silmari_rlm_act.cli.RLMActPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = mock_result
            mock_pipeline_cls.return_value = mock_pipeline

            result = cli_runner.invoke(
                main,
                [
                    "run",
                    "--plan-path",
                    str(temp_plan_doc),
                    "--project",
                    str(temp_project),
                ],
            )

            # Should not fail due to missing --question
            assert result.exit_code == 0 or mock_pipeline.run.called

    def test_plan_path_passed_to_pipeline(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_001.2: hierarchy_path is passed to pipeline.run() kwargs."""
        from silmari_rlm_act.cli import main

        mock_result = PhaseResult(
            phase_type=PhaseType.IMPLEMENTATION,
            status=PhaseStatus.COMPLETE,
        )

        with patch("silmari_rlm_act.cli.RLMActPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = mock_result
            mock_pipeline_cls.return_value = mock_pipeline

            cli_runner.invoke(
                main,
                [
                    "run",
                    "--plan-path",
                    str(temp_plan_doc),
                    "--project",
                    str(temp_project),
                ],
            )

            # Check pipeline.run was called with hierarchy_path
            call_kwargs = mock_pipeline.run.call_args.kwargs
            assert "hierarchy_path" in call_kwargs
            assert call_kwargs["hierarchy_path"] == str(temp_plan_doc)

    def test_both_question_and_plan_path_warns(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_001.4: Warning when both --question and --plan-path provided."""
        from silmari_rlm_act.cli import main

        mock_result = PhaseResult(
            phase_type=PhaseType.IMPLEMENTATION,
            status=PhaseStatus.COMPLETE,
        )

        with patch("silmari_rlm_act.cli.RLMActPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = mock_result
            mock_pipeline_cls.return_value = mock_pipeline

            result = cli_runner.invoke(
                main,
                [
                    "run",
                    "--question",
                    "Test question",
                    "--plan-path",
                    str(temp_plan_doc),
                    "--project",
                    str(temp_project),
                ],
            )

            # Should show warning
            assert "warning" in result.output.lower() or "ignored" in result.output.lower()

    def test_plan_path_cli_validation_updated(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
    ) -> None:
        """REQ_001.4: CLI validation: --question required unless --research-path OR --plan-path OR --resume."""
        from silmari_rlm_act.cli import main

        result = cli_runner.invoke(
            main,
            ["run", "--project", str(temp_project)],
        )

        assert result.exit_code != 0
        # Should mention plan-path as one of the alternatives
        assert "plan-path" in result.output.lower() or "required" in result.output.lower()


# ===========================================================================
# Behavior 8: Validate Full Option (REQ_003)
# ===========================================================================


class TestValidateFullOption:
    """Tests for the --validate-full option (REQ_003)."""

    def test_validate_full_option_defined(self, cli_runner: CliRunner) -> None:
        """REQ_003.3.1: CLI accepts --validate-full or -vf flag."""
        from silmari_rlm_act.cli import main

        result = cli_runner.invoke(main, ["run", "--help"])

        assert result.exit_code == 0
        assert "--validate-full" in result.output
        assert "-vf" in result.output

    def test_validate_full_help_text(self, cli_runner: CliRunner) -> None:
        """REQ_003.3.5: Help text explains the tradeoff."""
        from silmari_rlm_act.cli import main

        result = cli_runner.invoke(main, ["run", "--help"])

        # Help should mention LLM-based and semantic validation
        assert "semantic" in result.output.lower() or "llm" in result.output.lower()

    def test_validate_full_defaults_to_false(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_003.3.2: Flag defaults to False when not specified."""
        from silmari_rlm_act.cli import main

        mock_result = PhaseResult(
            phase_type=PhaseType.IMPLEMENTATION,
            status=PhaseStatus.COMPLETE,
        )

        with patch("silmari_rlm_act.cli.RLMActPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = mock_result
            mock_pipeline_cls.return_value = mock_pipeline

            cli_runner.invoke(
                main,
                [
                    "run",
                    "--plan-path",
                    str(temp_plan_doc),
                    "--project",
                    str(temp_project),
                ],
            )

            # Check validate_full defaults to False
            call_kwargs = mock_pipeline.run.call_args.kwargs
            assert call_kwargs.get("validate_full") is False

    def test_validate_full_true_when_specified(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_003.3.3: When --validate-full is True, BAML validation is invoked."""
        from silmari_rlm_act.cli import main

        mock_result = PhaseResult(
            phase_type=PhaseType.IMPLEMENTATION,
            status=PhaseStatus.COMPLETE,
        )

        with patch("silmari_rlm_act.cli.RLMActPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = mock_result
            mock_pipeline_cls.return_value = mock_pipeline

            cli_runner.invoke(
                main,
                [
                    "run",
                    "--plan-path",
                    str(temp_plan_doc),
                    "--project",
                    str(temp_project),
                    "--validate-full",
                ],
            )

            # Check validate_full is True
            call_kwargs = mock_pipeline.run.call_args.kwargs
            assert call_kwargs.get("validate_full") is True

    def test_validate_full_short_form(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_003.3.1: -vf short form works."""
        from silmari_rlm_act.cli import main

        mock_result = PhaseResult(
            phase_type=PhaseType.IMPLEMENTATION,
            status=PhaseStatus.COMPLETE,
        )

        with patch("silmari_rlm_act.cli.RLMActPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = mock_result
            mock_pipeline_cls.return_value = mock_pipeline

            cli_runner.invoke(
                main,
                [
                    "run",
                    "--plan-path",
                    str(temp_plan_doc),
                    "--project",
                    str(temp_project),
                    "-vf",
                ],
            )

            call_kwargs = mock_pipeline.run.call_args.kwargs
            assert call_kwargs.get("validate_full") is True

    def test_validate_full_warns_without_plan_path(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
    ) -> None:
        """REQ_003.3.8: CLI displays warning if --validate-full used without --plan-path."""
        from silmari_rlm_act.cli import main

        mock_result = PhaseResult(
            phase_type=PhaseType.IMPLEMENTATION,
            status=PhaseStatus.COMPLETE,
        )

        with patch("silmari_rlm_act.cli.RLMActPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = mock_result
            mock_pipeline_cls.return_value = mock_pipeline

            result = cli_runner.invoke(
                main,
                [
                    "run",
                    "--question",
                    "Test question",
                    "--project",
                    str(temp_project),
                    "--validate-full",
                ],
            )

            # Should show warning about validate-full without plan-path
            assert "warning" in result.output.lower()
            assert "plan-path" in result.output.lower() or "no effect" in result.output.lower()

    def test_validate_full_compatible_with_plan_path(
        self,
        cli_runner: CliRunner,
        temp_project: Path,
        temp_plan_doc: Path,
    ) -> None:
        """REQ_003.3.6: Flag is mutually compatible with --plan-path argument."""
        from silmari_rlm_act.cli import main

        mock_result = PhaseResult(
            phase_type=PhaseType.IMPLEMENTATION,
            status=PhaseStatus.COMPLETE,
        )

        with patch("silmari_rlm_act.cli.RLMActPipeline") as mock_pipeline_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = mock_result
            mock_pipeline_cls.return_value = mock_pipeline

            result = cli_runner.invoke(
                main,
                [
                    "run",
                    "--plan-path",
                    str(temp_plan_doc),
                    "--project",
                    str(temp_project),
                    "--validate-full",
                ],
            )

            # Should not show error, should work
            assert result.exit_code == 0 or mock_pipeline.run.called
