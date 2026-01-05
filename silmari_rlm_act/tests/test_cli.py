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
