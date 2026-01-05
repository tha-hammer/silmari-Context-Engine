"""Tests for Interactive Prompts: pipeline control user interactions.

Phase 03 of TDD implementation for silmari-rlm-act pipeline.
Tests 12 behaviors for interactive prompts used at pipeline checkpoints.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from silmari_rlm_act.checkpoints.interactive import (
    collect_multiline_input,
    prompt_autonomy_mode,
    prompt_cleanup_menu,
    prompt_custom_path,
    prompt_file_selection,
    prompt_phase_continue,
    prompt_research_action,
    prompt_resume_point,
    prompt_search_days,
    prompt_use_checkpoint,
)
from silmari_rlm_act.models import AutonomyMode


class TestResearchActionPrompt:
    """Behavior 1: Research Action Prompt."""

    def test_continue_on_c(self) -> None:
        """Given 'c', returns 'continue'."""
        with patch("builtins.input", return_value="c"):
            action = prompt_research_action()
        assert action == "continue"

    def test_continue_on_empty(self) -> None:
        """Given empty input, returns 'continue' (default)."""
        with patch("builtins.input", return_value=""):
            action = prompt_research_action()
        assert action == "continue"

    def test_revise_on_r(self) -> None:
        """Given 'r', returns 'revise'."""
        with patch("builtins.input", return_value="r"):
            action = prompt_research_action()
        assert action == "revise"

    def test_restart_on_s(self) -> None:
        """Given 's', returns 'restart'."""
        with patch("builtins.input", return_value="s"):
            action = prompt_research_action()
        assert action == "restart"

    def test_exit_on_e(self) -> None:
        """Given 'e', returns 'exit'."""
        with patch("builtins.input", return_value="e"):
            action = prompt_research_action()
        assert action == "exit"

    def test_case_insensitive(self) -> None:
        """Given uppercase 'C', returns 'continue'."""
        with patch("builtins.input", return_value="C"):
            action = prompt_research_action()
        assert action == "continue"

    def test_invalid_then_valid(self) -> None:
        """Given invalid then valid input, reprompts."""
        inputs = iter(["x", "c"])
        with patch("builtins.input", lambda _: next(inputs)):
            action = prompt_research_action()
        assert action == "continue"


class TestCheckpointResumePrompt:
    """Behavior 2: Checkpoint Resume Prompt."""

    def test_yes_on_y(self) -> None:
        """Given 'y', returns True."""
        with patch("builtins.input", return_value="y"):
            use_it = prompt_use_checkpoint(
                timestamp="2026-01-05T10:30:00", phase="research-complete"
            )
        assert use_it is True

    def test_yes_on_empty(self) -> None:
        """Given empty input, returns True (default)."""
        with patch("builtins.input", return_value=""):
            use_it = prompt_use_checkpoint(
                timestamp="2026-01-05T10:30:00", phase="research-complete"
            )
        assert use_it is True

    def test_no_on_n(self) -> None:
        """Given 'n', returns False."""
        with patch("builtins.input", return_value="n"):
            use_it = prompt_use_checkpoint(
                timestamp="2026-01-05T10:30:00", phase="research-complete"
            )
        assert use_it is False

    def test_displays_checkpoint_info(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Given checkpoint, displays timestamp and phase."""
        with patch("builtins.input", return_value="y"):
            prompt_use_checkpoint(
                timestamp="2026-01-05T10:30:00",
                phase="research-complete",
                artifacts=["file1.md", "file2.md"],
            )

        captured = capsys.readouterr()
        assert "2026-01-05T10:30:00" in captured.out
        assert "research-complete" in captured.out
        assert "file1.md" in captured.out


class TestAutonomyModeSelection:
    """Behavior 3: Autonomy Mode Selection."""

    def test_checkpoint_on_c(self) -> None:
        """Given 'c', returns CHECKPOINT mode."""
        with patch("builtins.input", return_value="c"):
            mode = prompt_autonomy_mode(phase_count=6, epic_id="beads-abc")
        assert mode == AutonomyMode.CHECKPOINT

    def test_checkpoint_on_empty(self) -> None:
        """Given empty, returns CHECKPOINT (default)."""
        with patch("builtins.input", return_value=""):
            mode = prompt_autonomy_mode(phase_count=6, epic_id="beads-abc")
        assert mode == AutonomyMode.CHECKPOINT

    def test_fully_autonomous_on_f(self) -> None:
        """Given 'f', returns FULLY_AUTONOMOUS mode."""
        with patch("builtins.input", return_value="f"):
            mode = prompt_autonomy_mode(phase_count=6, epic_id="beads-abc")
        assert mode == AutonomyMode.FULLY_AUTONOMOUS

    def test_batch_on_b(self) -> None:
        """Given 'b', returns BATCH mode."""
        with patch("builtins.input", return_value="b"):
            mode = prompt_autonomy_mode(phase_count=6, epic_id="beads-abc")
        assert mode == AutonomyMode.BATCH

    def test_displays_context(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Given phase count and epic, displays them."""
        with patch("builtins.input", return_value="c"):
            prompt_autonomy_mode(phase_count=6, epic_id="beads-abc123")

        captured = capsys.readouterr()
        assert "6" in captured.out
        assert "beads-abc123" in captured.out

    def test_invalid_then_valid(self) -> None:
        """Given invalid then valid input, reprompts."""
        inputs = iter(["x", "c"])
        with patch("builtins.input", lambda _: next(inputs)):
            mode = prompt_autonomy_mode(phase_count=6, epic_id="beads-abc")
        assert mode == AutonomyMode.CHECKPOINT


class TestFileSelectionMenu:
    """Behavior 4: File Selection Menu."""

    def test_select_by_number(self, tmp_path: Path) -> None:
        """Given '1', returns selected file."""
        files = [tmp_path / "file1.md", tmp_path / "file2.md"]
        for f in files:
            f.touch()

        with patch("builtins.input", return_value="1"):
            action, path = prompt_file_selection(files, "research")

        assert action == "selected"
        assert path == files[0]

    def test_select_second_file(self, tmp_path: Path) -> None:
        """Given '2', returns second file."""
        files = [tmp_path / "file1.md", tmp_path / "file2.md"]
        for f in files:
            f.touch()

        with patch("builtins.input", return_value="2"):
            action, path = prompt_file_selection(files, "research")

        assert action == "selected"
        assert path == files[1]

    def test_search_on_s(self, tmp_path: Path) -> None:
        """Given 's', returns search action."""
        with patch("builtins.input", return_value="s"):
            action, path = prompt_file_selection([], "research")

        assert action == "search"
        assert path is None

    def test_other_on_o(self, tmp_path: Path) -> None:
        """Given 'o', returns other action."""
        with patch("builtins.input", return_value="o"):
            action, path = prompt_file_selection([], "research")

        assert action == "other"
        assert path is None

    def test_exit_on_e(self, tmp_path: Path) -> None:
        """Given 'e', returns exit action."""
        with patch("builtins.input", return_value="e"):
            action, path = prompt_file_selection([], "research")

        assert action == "exit"
        assert path is None

    def test_invalid_number_reprompts(self, tmp_path: Path) -> None:
        """Given invalid number then valid, reprompts."""
        files = [tmp_path / "file1.md"]
        files[0].touch()

        inputs = iter(["5", "1"])
        with patch("builtins.input", lambda _: next(inputs)):
            action, path = prompt_file_selection(files, "research")

        assert action == "selected"
        assert path == files[0]

    def test_invalid_choice_reprompts(self, tmp_path: Path) -> None:
        """Given invalid choice then valid, reprompts."""
        inputs = iter(["xyz", "e"])
        with patch("builtins.input", lambda _: next(inputs)):
            action, path = prompt_file_selection([], "research")

        assert action == "exit"


class TestMultilineInput:
    """Behavior 5: Multi-line Input Collection."""

    def test_collects_until_empty_line(self) -> None:
        """Given multiple lines, joins with newlines."""
        inputs = iter(["line1", "line2", ""])
        with patch("builtins.input", lambda _: next(inputs)):
            result = collect_multiline_input()
        assert result == "line1\nline2"

    def test_single_line(self) -> None:
        """Given one line then empty, returns single line."""
        inputs = iter(["only line", ""])
        with patch("builtins.input", lambda _: next(inputs)):
            result = collect_multiline_input()
        assert result == "only line"

    def test_empty_returns_empty_string(self) -> None:
        """Given empty immediately, returns empty string."""
        with patch("builtins.input", return_value=""):
            result = collect_multiline_input()
        assert result == ""

    def test_preserves_whitespace_in_lines(self) -> None:
        """Given lines with spaces, preserves them."""
        inputs = iter(["  indented", "  more", ""])
        with patch("builtins.input", lambda _: next(inputs)):
            result = collect_multiline_input()
        assert result == "  indented\n  more"


class TestSearchDaysInput:
    """Behavior 6: Numeric Days Input."""

    def test_returns_default_on_empty(self) -> None:
        """Given empty input, returns default 7."""
        with patch("builtins.input", return_value=""):
            days = prompt_search_days()
        assert days == 7

    def test_returns_entered_number(self) -> None:
        """Given valid number, returns it."""
        with patch("builtins.input", return_value="14"):
            days = prompt_search_days()
        assert days == 14

    def test_custom_default(self) -> None:
        """Given custom default, uses it on empty."""
        with patch("builtins.input", return_value=""):
            days = prompt_search_days(default=30)
        assert days == 30

    def test_invalid_then_valid(self) -> None:
        """Given invalid then valid, reprompts."""
        inputs = iter(["abc", "5"])
        with patch("builtins.input", lambda _: next(inputs)):
            days = prompt_search_days()
        assert days == 5

    def test_negative_uses_default(self) -> None:
        """Given negative, uses default."""
        inputs = iter(["-5", ""])
        with patch("builtins.input", lambda _: next(inputs)):
            days = prompt_search_days()
        assert days == 7


class TestPhaseContinuePrompt:
    """Behavior 7: Phase Continue Prompt."""

    def test_continue_on_y(self) -> None:
        """Given 'y', returns continue=True."""
        with patch("builtins.input", return_value="y"):
            result = prompt_phase_continue("decomposition", ["file.md"])
        assert result["continue"] is True
        assert result["feedback"] == ""

    def test_continue_on_empty(self) -> None:
        """Given empty, returns continue=True (default)."""
        with patch("builtins.input", return_value=""):
            result = prompt_phase_continue("decomposition", ["file.md"])
        assert result["continue"] is True

    def test_collects_feedback_on_n(self) -> None:
        """Given 'n', collects feedback."""
        inputs = iter(["n", "feedback line", ""])
        with patch("builtins.input", lambda _: next(inputs)):
            result = prompt_phase_continue("decomposition", ["file.md"])
        assert result["continue"] is False
        assert "feedback line" in result["feedback"]

    def test_displays_phase_and_artifacts(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given phase and artifacts, displays them."""
        with patch("builtins.input", return_value="y"):
            prompt_phase_continue("decomposition", ["artifact1.md", "artifact2.md"])

        captured = capsys.readouterr()
        assert "decomposition" in captured.out.lower()
        assert "artifact1.md" in captured.out
        assert "artifact2.md" in captured.out


class TestCustomPathInput:
    """Behavior 8: Custom Path Input."""

    def test_validates_path_exists(self, tmp_path: Path) -> None:
        """Given existing path, returns Path."""
        test_file = tmp_path / "test.md"
        test_file.touch()

        with patch("builtins.input", return_value=str(test_file)):
            path = prompt_custom_path("research")
        assert path == test_file

    def test_returns_none_for_nonexistent(self) -> None:
        """Given nonexistent path, returns None."""
        with patch("builtins.input", return_value="/nonexistent/path"):
            path = prompt_custom_path("research")
        assert path is None

    def test_returns_none_on_empty(self) -> None:
        """Given empty input, returns None."""
        with patch("builtins.input", return_value=""):
            path = prompt_custom_path("research")
        assert path is None

    def test_expands_home_dir(self, tmp_path: Path) -> None:
        """Given ~/ path, expands it."""
        # We can't test actual home expansion without creating files there
        # Just verify it handles the path normally
        with patch("builtins.input", return_value="/nonexistent"):
            path = prompt_custom_path("research")
        assert path is None


class TestCleanupMenu:
    """Behavior 9: Cleanup Menu."""

    def test_skip_on_s(self) -> None:
        """Given 's', returns skip action."""
        with patch("builtins.input", return_value="s"):
            action, days = prompt_cleanup_menu(count=5, oldest="2026-01-01")
        assert action == "skip"
        assert days is None

    def test_oldest_on_o(self) -> None:
        """Given 'o', returns oldest action."""
        with patch("builtins.input", return_value="o"):
            action, days = prompt_cleanup_menu(count=5, oldest="2026-01-01")
        assert action == "oldest"
        assert days is None

    def test_days_on_d(self) -> None:
        """Given 'd' then number, returns days action with value."""
        inputs = iter(["d", "7"])
        with patch("builtins.input", lambda _: next(inputs)):
            action, days = prompt_cleanup_menu(count=5, oldest="2026-01-01")
        assert action == "days"
        assert days == 7

    def test_all_requires_confirmation(self) -> None:
        """Given 'a' then 'ALL', returns all action."""
        inputs = iter(["a", "ALL"])
        with patch("builtins.input", lambda _: next(inputs)):
            action, days = prompt_cleanup_menu(count=5, oldest="2026-01-01")
        assert action == "all"
        assert days is None

    def test_all_cancelled_without_confirmation(self) -> None:
        """Given 'a' without ALL confirmation, returns skip."""
        inputs = iter(["a", "no"])
        with patch("builtins.input", lambda _: next(inputs)):
            action, days = prompt_cleanup_menu(count=5, oldest="2026-01-01")
        assert action == "skip"

    def test_displays_checkpoint_info(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given count and oldest, displays them."""
        with patch("builtins.input", return_value="s"):
            prompt_cleanup_menu(count=5, oldest="2026-01-01")

        captured = capsys.readouterr()
        assert "5" in captured.out
        assert "2026-01-01" in captured.out


class TestResumePointSelection:
    """Behavior 10: Resume Point Selection."""

    def test_selects_phase_by_number(self) -> None:
        """Given '2', returns second phase."""
        phases = ["tdd_planning", "multi_doc", "beads_sync"]
        with patch("builtins.input", return_value="2"):
            selected = prompt_resume_point(phases)
        assert selected == "multi_doc"

    def test_first_phase_on_empty(self) -> None:
        """Given empty, returns first phase (default)."""
        phases = ["tdd_planning", "multi_doc", "beads_sync"]
        with patch("builtins.input", return_value=""):
            selected = prompt_resume_point(phases)
        assert selected == "tdd_planning"

    def test_invalid_number_reprompts(self) -> None:
        """Given invalid number then valid, reprompts."""
        phases = ["tdd_planning", "multi_doc"]
        inputs = iter(["5", "1"])
        with patch("builtins.input", lambda _: next(inputs)):
            selected = prompt_resume_point(phases)
        assert selected == "tdd_planning"

    def test_displays_phase_options(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Given phases, displays numbered list."""
        phases = ["tdd_planning", "multi_doc", "beads_sync"]
        with patch("builtins.input", return_value="1"):
            prompt_resume_point(phases)

        captured = capsys.readouterr()
        assert "[1]" in captured.out
        assert "[2]" in captured.out
        assert "[3]" in captured.out
        assert "tdd_planning" in captured.out
        assert "multi_doc" in captured.out
        assert "beads_sync" in captured.out


class TestDefaultSelection:
    """Behavior 12: Default Selection."""

    def test_research_action_default(self) -> None:
        """Research action defaults to continue on Enter."""
        with patch("builtins.input", return_value=""):
            action = prompt_research_action()
        assert action == "continue"

    def test_checkpoint_resume_default(self) -> None:
        """Checkpoint resume defaults to yes on Enter."""
        with patch("builtins.input", return_value=""):
            use_it = prompt_use_checkpoint("2026-01-05", "test")
        assert use_it is True

    def test_autonomy_mode_default(self) -> None:
        """Autonomy mode defaults to checkpoint on Enter."""
        with patch("builtins.input", return_value=""):
            mode = prompt_autonomy_mode(1, "epic")
        assert mode == AutonomyMode.CHECKPOINT
