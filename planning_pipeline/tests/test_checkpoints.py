"""Tests for checkpoint functions - Behaviors 12, 13."""

import pytest
from unittest.mock import patch
from planning_pipeline.checkpoints import (
    interactive_checkpoint_research,
    interactive_checkpoint_plan
)


class TestResearchCheckpoint:
    """Behavior 12: Interactive Checkpoint - Research."""

    def test_continues_on_c(self):
        """Given 'c' input, returns action='continue'."""
        research_result = {
            "research_path": "thoughts/shared/research/test.md",
            "open_questions": []
        }

        with patch('builtins.input', return_value='c'):
            result = interactive_checkpoint_research(research_result)

        assert result["action"] == "continue"
        assert result["continue"] is True
        assert result["answers"] == []

    def test_continues_on_empty_input(self):
        """Given empty input (default), returns action='continue'."""
        research_result = {
            "research_path": "thoughts/shared/research/test.md",
            "open_questions": []
        }

        with patch('builtins.input', return_value=''):
            result = interactive_checkpoint_research(research_result)

        assert result["action"] == "continue"
        assert result["continue"] is True

    def test_collects_answers_for_questions(self):
        """Given research result with questions, collects answers then prompts."""
        research_result = {
            "research_path": "thoughts/shared/research/test.md",
            "open_questions": ["Q1?", "Q2?"]
        }

        # Simulate: "Answer1", "Answer2", "" (empty to finish), then "c" to continue
        inputs = iter(["Answer1", "Answer2", "", "c"])
        with patch('builtins.input', lambda _: next(inputs)):
            result = interactive_checkpoint_research(research_result)

        assert result["action"] == "continue"
        assert result["answers"] == ["Answer1", "Answer2"]

    def test_revise_collects_revision_context(self):
        """Given 'r' input, collects revision context."""
        research_result = {
            "research_path": "thoughts/shared/research/test.md",
            "open_questions": []
        }

        # Simulate: "r", "Add more detail about auth", ""
        inputs = iter(["r", "Add more detail about auth", ""])
        with patch('builtins.input', lambda _: next(inputs)):
            result = interactive_checkpoint_research(research_result)

        assert result["action"] == "revise"
        assert result["continue"] is False
        assert "auth" in result["revision_context"]

    def test_restart_returns_action(self):
        """Given 's' input, returns action='restart'."""
        research_result = {
            "research_path": "thoughts/shared/research/test.md",
            "open_questions": []
        }

        with patch('builtins.input', return_value='s'):
            result = interactive_checkpoint_research(research_result)

        assert result["action"] == "restart"
        assert result["continue"] is False

    def test_exit_returns_action(self):
        """Given 'e' input, returns action='exit'."""
        research_result = {
            "research_path": "thoughts/shared/research/test.md",
            "open_questions": []
        }

        with patch('builtins.input', return_value='e'):
            result = interactive_checkpoint_research(research_result)

        assert result["action"] == "exit"
        assert result["continue"] is False

    def test_preserves_research_path(self):
        """Given research result, preserves research_path in output."""
        research_result = {
            "research_path": "thoughts/shared/research/my-research.md",
            "open_questions": []
        }

        with patch('builtins.input', return_value='c'):
            result = interactive_checkpoint_research(research_result)

        assert result["research_path"] == "thoughts/shared/research/my-research.md"

    def test_invalid_input_reprompts(self):
        """Given invalid input, reprompts until valid."""
        research_result = {
            "research_path": "thoughts/shared/research/test.md",
            "open_questions": []
        }

        # Simulate: "x" (invalid), "z" (invalid), "c" (valid)
        inputs = iter(["x", "z", "c"])
        with patch('builtins.input', lambda _: next(inputs)):
            result = interactive_checkpoint_research(research_result)

        assert result["action"] == "continue"


class TestPlanCheckpoint:
    """Behavior 13: Interactive Checkpoint - Planning."""

    def test_continues_on_yes(self):
        """Given plan result, continues on 'Y' input."""
        plan_result = {"plan_path": "thoughts/shared/plans/test.md"}

        with patch('builtins.input', return_value='Y'):
            result = interactive_checkpoint_plan(plan_result)

        assert result["continue"] is True
        assert result["feedback"] == ""

    def test_collects_feedback_on_no(self):
        """Given plan result, collects feedback on 'n' input."""
        plan_result = {"plan_path": "thoughts/shared/plans/test.md"}

        inputs = iter(['n', 'Need more detail on phase 2', ''])
        with patch('builtins.input', lambda _: next(inputs)):
            result = interactive_checkpoint_plan(plan_result)

        assert result["continue"] is False
        assert "more detail" in result["feedback"]

    def test_preserves_plan_path(self):
        """Given plan result, preserves plan_path in output."""
        plan_result = {"plan_path": "thoughts/shared/plans/my-plan.md"}

        with patch('builtins.input', return_value='Y'):
            result = interactive_checkpoint_plan(plan_result)

        assert result["plan_path"] == "thoughts/shared/plans/my-plan.md"

    def test_empty_input_treated_as_yes(self):
        """Given empty input, treats as 'yes' to continue."""
        plan_result = {"plan_path": "thoughts/shared/plans/test.md"}

        with patch('builtins.input', return_value=''):
            result = interactive_checkpoint_plan(plan_result)

        assert result["continue"] is True
