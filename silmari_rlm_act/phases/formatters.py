"""Output formatters for SDK-based phases.

This module provides formatters for SDK streaming output to make it
human-readable with proper structure and real-time display.
"""

import sys
from typing import Any, TextIO


class OutputFormatter:
    """Format SDK streaming output for human readability.

    Handles real-time output formatting including:
    - Section headers and separators
    - Tool use display with clear boundaries
    - Proper newlines and spacing
    - Progress indicators
    """

    def __init__(
        self,
        output_stream: TextIO = sys.stdout,
        show_tool_details: bool = True,
    ) -> None:
        """Initialize output formatter.

        Args:
            output_stream: Stream to write output to (default: stdout)
            show_tool_details: Whether to show tool input details
        """
        self.output_stream = output_stream
        self.show_tool_details = show_tool_details
        self._tool_count = 0
        self._last_was_tool = False

    def write(self, text: str) -> None:
        """Write text to output stream with flush.

        Args:
            text: Text to write
        """
        self.output_stream.write(text)
        self.output_stream.flush()

    def format_header(self, title: str, width: int = 60) -> None:
        """Print a section header.

        Args:
            title: Header title
            width: Total width of header line
        """
        if self._last_was_tool:
            self.write("\n")
        self.write("\n")
        self.write("=" * width + "\n")
        self.write(f"{title}\n")
        self.write("=" * width + "\n")
        self.write("\n")
        self._last_was_tool = False

    def format_subheader(self, title: str) -> None:
        """Print a subsection header.

        Args:
            title: Subheader title
        """
        if self._last_was_tool:
            self.write("\n")
        self.write("\n")
        self.write(f"── {title} " + "─" * (56 - len(title)) + "\n")
        self.write("\n")
        self._last_was_tool = False

    def format_text(self, text: str) -> None:
        """Format and print text content.

        Ensures proper spacing and newlines.

        Args:
            text: Text content to print
        """
        if self._last_was_tool:
            self.write("\n")
            self._last_was_tool = False

        # Ensure text ends with newline for proper separation
        if text and not text.endswith("\n"):
            text += "\n"
        self.write(text)

    def format_tool_use(self, name: str, tool_input: dict[str, Any]) -> None:
        """Format and print tool use with clear boundaries.

        Args:
            name: Tool name
            tool_input: Tool input parameters
        """
        self._tool_count += 1

        # Add separator before tool if we had text
        if not self._last_was_tool:
            self.write("\n")

        self.write(f"┌─ Tool #{self._tool_count}: {name}\n")

        if self.show_tool_details:
            # Show abbreviated input for common tools
            if name == "Read":
                path = tool_input.get("file_path", "")
                self.write(f"│  file: {path}\n")
            elif name == "Write":
                path = tool_input.get("file_path", "")
                self.write(f"│  file: {path}\n")
            elif name == "Edit":
                path = tool_input.get("file_path", "")
                self.write(f"│  file: {path}\n")
            elif name == "Bash":
                cmd = tool_input.get("command", "")
                # Truncate long commands
                if len(cmd) > 60:
                    cmd = cmd[:57] + "..."
                self.write(f"│  cmd: {cmd}\n")
            elif name == "Glob":
                pattern = tool_input.get("pattern", "")
                self.write(f"│  pattern: {pattern}\n")
            elif name == "Grep":
                pattern = tool_input.get("pattern", "")
                self.write(f"│  pattern: {pattern}\n")
            elif name == "Task":
                desc = tool_input.get("description", "")
                self.write(f"│  task: {desc}\n")
            elif name == "TodoWrite":
                todos = tool_input.get("todos", [])
                self.write(f"│  items: {len(todos)} todo(s)\n")
            else:
                # For unknown tools, show first key-value
                for key, value in list(tool_input.items())[:1]:
                    val_str = str(value)
                    if len(val_str) > 50:
                        val_str = val_str[:47] + "..."
                    self.write(f"│  {key}: {val_str}\n")

        self.write("└─\n")
        self._last_was_tool = True

    def format_summary(
        self,
        tool_count: int,
        duration_seconds: float,
        status: str,
    ) -> None:
        """Print execution summary.

        Args:
            tool_count: Number of tools used
            duration_seconds: Total execution time
            status: Final status (COMPLETE, FAILED, etc.)
        """
        self.write("\n")
        self.write("─" * 60 + "\n")
        self.write(f"Summary: {status}\n")
        self.write(f"  Tools used: {tool_count}\n")
        self.write(f"  Duration: {duration_seconds:.1f}s\n")
        self.write("─" * 60 + "\n")

    def reset(self) -> None:
        """Reset formatter state for a new execution."""
        self._tool_count = 0
        self._last_was_tool = False
