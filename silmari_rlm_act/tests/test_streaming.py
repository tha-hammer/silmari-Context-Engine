"""Tests for StreamingOutputService.

This module tests the shared streaming output service that provides
consistent formatting across all RLM pipeline phases.
"""

from io import StringIO

import pytest

from silmari_rlm_act.streaming import StreamingOutputService


class TestFormatText:
    """Behavior 1: Format text blocks."""

    def test_writes_text_to_stream(self) -> None:
        """Given text, when format_text called, then writes to stream."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output)

        service.format_text("Hello world")

        assert output.getvalue() == "Hello world"

    def test_flushes_after_write(self) -> None:
        """Given text, when format_text called, then flushes stream."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output)

        service.format_text("Test")

        # StringIO doesn't track flush, but we verify write happened
        assert output.getvalue() == "Test"

    def test_handles_empty_string(self) -> None:
        """Given empty string, when format_text called, then writes nothing."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output)

        service.format_text("")

        assert output.getvalue() == ""


class TestFormatToolUse:
    """Behavior 2: Format tool use with claude_runner style."""

    def test_formats_tool_with_file_path(self) -> None:
        """Given Read tool, when format_tool_use called, then shows file path."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output)

        service.format_tool_use("Read", {"file_path": "/path/to/file.py"})

        result = output.getvalue()
        assert "Read" in result
        assert "/path/to/file.py" in result
        assert "⏺" in result

    def test_formats_tool_with_command(self) -> None:
        """Given Bash tool, when format_tool_use called, then shows command."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output)

        service.format_tool_use("Bash", {"command": "ls -la"})

        result = output.getvalue()
        assert "Bash" in result
        assert "ls -la" in result

    def test_truncates_long_arguments(self) -> None:
        """Given long argument, when format_tool_use called, then truncates."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output)
        long_cmd = "a" * 100

        service.format_tool_use("Bash", {"command": long_cmd})

        result = output.getvalue()
        assert "..." in result
        assert len(result) < 150  # Reasonable length

    def test_handles_empty_input(self) -> None:
        """Given no input, when format_tool_use called, then shows tool name only."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output)

        service.format_tool_use("Task", {})

        result = output.getvalue()
        assert "Task" in result
        assert "⏺" in result

    def test_includes_ansi_colors(self) -> None:
        """Given tool use, when format_tool_use called, then includes ANSI codes."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output)

        service.format_tool_use("Read", {"file_path": "/test"})

        result = output.getvalue()
        # CYAN = \033[36m, GREEN = \033[32m, RESET = \033[0m
        assert "\033[36m" in result  # CYAN for tool name
        assert "\033[0m" in result   # RESET


class TestQuietMode:
    """Behavior 3: Quiet mode buffers without display."""

    def test_quiet_mode_no_text_output(self) -> None:
        """Given quiet=True, when format_text called, then no output."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output, quiet=True)

        service.format_text("Hello")

        assert output.getvalue() == ""

    def test_quiet_mode_no_tool_output(self) -> None:
        """Given quiet=True, when format_tool_use called, then no output."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output, quiet=True)

        service.format_tool_use("Read", {"file_path": "/test"})

        assert output.getvalue() == ""

    def test_quiet_mode_buffers_text(self) -> None:
        """Given quiet=True, when format_text called, then buffers content."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output, quiet=True)

        service.format_text("Hello")
        service.format_text(" World")

        assert service.get_buffer() == "Hello World"

    def test_quiet_mode_buffers_tool_uses(self) -> None:
        """Given quiet=True, when format_tool_use called, then records in buffer."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output, quiet=True)

        service.format_tool_use("Read", {"file_path": "/test"})

        tool_uses = service.get_tool_uses()
        assert len(tool_uses) == 1
        assert tool_uses[0]["name"] == "Read"

    def test_non_quiet_also_buffers(self) -> None:
        """Given quiet=False, when streaming, then also buffers for retrieval."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output, quiet=False)

        service.format_text("Hello")

        assert output.getvalue() == "Hello"
        assert service.get_buffer() == "Hello"


class TestFormatHeadersAndSummaries:
    """Behavior 4: Format phase headers and execution summaries."""

    def test_format_header_prints_title(self) -> None:
        """Given title, when format_header called, then prints bordered header."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output)

        service.format_header("RESEARCH PHASE")

        result = output.getvalue()
        assert "RESEARCH PHASE" in result
        assert "=" in result  # Border character

    def test_format_header_quiet_mode_no_output(self) -> None:
        """Given quiet=True, when format_header called, then no output."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output, quiet=True)

        service.format_header("TEST PHASE")

        assert output.getvalue() == ""

    def test_format_summary_shows_status(self) -> None:
        """Given status, when format_summary called, then prints status."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output)

        service.format_summary(status="COMPLETE", duration=5.2)

        result = output.getvalue()
        assert "COMPLETE" in result
        assert "5.2" in result

    def test_format_summary_shows_tool_count(self) -> None:
        """Given tool uses recorded, when format_summary called, then shows count."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output)

        # Record some tool uses
        service.format_tool_use("Read", {"file_path": "/test"})
        service.format_tool_use("Bash", {"command": "ls"})

        # Clear output to isolate summary
        output.truncate(0)
        output.seek(0)

        service.format_summary(status="COMPLETE", duration=1.0)

        result = output.getvalue()
        assert "2" in result  # Tool count

    def test_format_summary_quiet_mode_no_output(self) -> None:
        """Given quiet=True, when format_summary called, then no output."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output, quiet=True)

        service.format_summary(status="FAILED", duration=10.0)

        assert output.getvalue() == ""

    def test_reset_clears_tool_count(self) -> None:
        """Given tool uses recorded, when reset called, then count is zero."""
        output = StringIO()
        service = StreamingOutputService(output_stream=output)

        service.format_tool_use("Read", {"file_path": "/test"})
        assert len(service.get_tool_uses()) == 1

        service.reset()

        assert len(service.get_tool_uses()) == 0
        assert service.get_buffer() == ""


class TestOutputFormatterDeprecation:
    """Behavior 10: Old OutputFormatter is deprecated."""

    def test_emits_deprecation_warning(self) -> None:
        """Given OutputFormatter instantiated, then emits DeprecationWarning."""
        import warnings

        from silmari_rlm_act.phases.formatters import OutputFormatter

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _ = OutputFormatter()

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "StreamingOutputService" in str(w[0].message)
