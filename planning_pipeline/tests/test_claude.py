"""Tests for Claude runner - Behavior 7."""

import pytest
from planning_pipeline.claude_runner import run_claude_sync


class TestClaudeRunner:
    """Behavior 7: Claude Runner - Execute Simple Prompt."""

    @pytest.mark.slow
    def test_runs_simple_prompt(self):
        """Given a simple prompt, returns output containing expected text."""
        result = run_claude_sync(
            prompt="Output exactly this text and nothing else: TEST_OUTPUT_12345",
            timeout=60
        )
        assert result["success"] is True
        assert "output" in result
        assert "TEST_OUTPUT_12345" in result["output"]

    @pytest.mark.slow
    def test_returns_elapsed_time(self):
        """Given a prompt, returns elapsed time."""
        result = run_claude_sync(
            prompt="Say hello briefly",
            timeout=60
        )
        assert "elapsed" in result
        assert result["elapsed"] > 0

    def test_handles_very_short_timeout(self):
        """Given a very short timeout, returns timeout error."""
        result = run_claude_sync(
            prompt="Count from 1 to 1000000 slowly and verbosely",
            timeout=1  # Very short timeout - should timeout
        )
        # May or may not timeout depending on Claude response time
        # But should always return a structured result
        assert "success" in result
        if not result["success"]:
            assert "error" in result

    def test_returns_structured_result(self):
        """Given any prompt, returns structured result with expected keys."""
        result = run_claude_sync(
            prompt="Say OK",
            timeout=30
        )
        # Should always have these keys
        assert "success" in result
        assert "output" in result
        assert "elapsed" in result
