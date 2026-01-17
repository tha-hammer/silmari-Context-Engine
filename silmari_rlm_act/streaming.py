"""Shared streaming output service for consistent display across phases.

This module provides a single StreamingOutputService that uses
claude_runner style formatting (⏺ ToolName(arg) with ANSI colors).
"""

import sys
from typing import Any, TextIO


class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"


class StreamingOutputService:
    """Single source of truth for streaming output formatting.

    Uses claude_runner style: ⏺ ToolName(arg) with ANSI colors.

    Thread Safety: NOT thread-safe. External synchronization required
    for concurrent access from multiple coroutines.

    Lifecycle:
    1. Create instance before phase execution
    2. Pass to execute methods
    3. Access get_buffer()/get_tool_uses() after completion
    4. Call reset() before reuse OR create new instance

    Error Handling: IOError from output_stream.write() propagates
    to caller (not suppressed).
    """

    def __init__(
        self,
        output_stream: TextIO = sys.stdout,
        quiet: bool = False,
    ) -> None:
        """Initialize streaming service.

        Args:
            output_stream: Stream to write output to (default: stdout)
            quiet: If True, buffer content without writing to stream
        """
        self.output_stream = output_stream
        self.quiet = quiet
        self._text_buffer: list[str] = []
        self._tool_uses: list[dict[str, Any]] = []

    def format_text(self, text: str) -> None:
        """Write text to output stream with flush.

        Text is always buffered for later retrieval. When quiet=False,
        also writes to output stream.

        Args:
            text: Text to write
        """
        if text:
            self._text_buffer.append(text)
            if not self.quiet:
                self.output_stream.write(text)
                self.output_stream.flush()

    def format_tool_use(self, name: str, tool_input: dict[str, Any]) -> None:
        """Format and write tool use with claude_runner style.

        Formats as: ⏺ ToolName(key_arg) with CYAN tool name and GREEN argument.
        Tool uses are always recorded for later retrieval. When quiet=False,
        also writes to output stream.

        Args:
            name: Tool name
            tool_input: Tool input parameters
        """
        # Always record tool use
        self._tool_uses.append({"name": name, "input": tool_input})

        if not self.quiet:
            display = f"{Colors.CYAN}{name}{Colors.RESET}"

            key_arg = self._extract_key_arg(tool_input)
            if key_arg:
                display += f"({Colors.GREEN}{key_arg}{Colors.RESET})"

            self.output_stream.write(f"\n{Colors.CYAN}⏺{Colors.RESET} {display}\n")
            self.output_stream.flush()

    def get_buffer(self) -> str:
        """Get accumulated text buffer.

        Returns:
            All text passed to format_text() concatenated
        """
        return "".join(self._text_buffer)

    def get_tool_uses(self) -> list[dict[str, Any]]:
        """Get list of tool uses.

        Returns:
            Copy of recorded tool uses with 'name' and 'input' keys
        """
        return self._tool_uses.copy()

    def reset(self) -> None:
        """Reset buffers for reuse.

        Clears text buffer and tool use history.
        """
        self._text_buffer.clear()
        self._tool_uses.clear()

    def format_header(self, title: str, width: int = 60) -> None:
        """Print phase header with visual separation.

        Args:
            title: Phase title to display
            width: Width of border line (default: 60)
        """
        if self.quiet:
            return

        line = "=" * width
        self.output_stream.write(f"\n\n{line}\n{title}\n{line}\n\n")
        self.output_stream.flush()

    def format_summary(self, status: str, duration: float) -> None:
        """Print phase completion summary.

        Args:
            status: Completion status (e.g., "COMPLETE", "FAILED: reason")
            duration: Execution duration in seconds
        """
        if self.quiet:
            return

        tool_count = len(self._tool_uses)
        border = "─" * 32
        self.output_stream.write(f"\n{border}\n")
        self.output_stream.write(f"Summary: {status}\n")
        self.output_stream.write(f"  Tools used: {tool_count}\n")
        self.output_stream.write(f"  Duration: {duration:.1f}s\n")
        self.output_stream.write(f"{border}\n")
        self.output_stream.flush()

    def _extract_key_arg(self, tool_input: dict[str, Any]) -> str | None:
        """Extract key argument from tool input.

        Priority order: file_path > path > command > pattern > query > url > description

        Args:
            tool_input: Tool input parameters

        Returns:
            The extracted key argument string, or None if not found
        """
        if not tool_input:
            return None

        # Priority order per claude_runner._extract_key_arg
        if tool_input.get("file_path"):
            return tool_input["file_path"]
        if tool_input.get("path"):
            return tool_input["path"]
        if tool_input.get("command"):
            return self._truncate(tool_input["command"])
        if tool_input.get("pattern"):
            return f'"{tool_input["pattern"]}"'
        if tool_input.get("query"):
            return f'"{self._truncate(tool_input["query"], 30)}"'
        if tool_input.get("url"):
            return self._truncate(tool_input["url"])
        if tool_input.get("description"):
            return self._truncate(tool_input["description"])

        return None

    def _truncate(self, value: str, max_len: int = 50) -> str:
        """Truncate string with ellipsis.

        Args:
            value: String to truncate
            max_len: Maximum length before truncation (default 50)

        Returns:
            Truncated string with '...' if needed, original otherwise
        """
        if len(value) <= max_len:
            return value
        return value[:max_len] + "..."
