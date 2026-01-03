"""Claude Code subprocess wrapper for deterministic pipeline control."""

import json
import subprocess
import sys
import time
from typing import Any, Optional


# ANSI color codes for terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'


def run_claude_sync(
    prompt: str,
    tools: Optional[list[str]] = None,
    timeout: int = 300,
    stream: bool = True
) -> dict[str, Any]:
    """Run Claude Code via subprocess and return structured result.

    Args:
        prompt: The prompt to send to Claude
        tools: Optional list of tools to enable (currently unused - Claude selects tools)
        timeout: Maximum time in seconds to wait for response
        stream: If True, pipe output to terminal in real-time

    Returns:
        Dictionary with keys:
        - success: bool indicating if command completed successfully
        - output: stdout from Claude
        - error: stderr or error message
        - elapsed: time in seconds
    """
    cmd = [
        "claude",
        "--print",
        "--verbose",  # Required for stream-json
        "--permission-mode", "bypassPermissions",
        "--output-format", "stream-json",  # Use streaming JSON for real-time output
        "-p", prompt
    ]

    start_time = time.time()

    try:
        if stream:
            return _run_with_streaming(cmd, timeout, start_time)
        else:
            return _run_capture_only(cmd, timeout, start_time)

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": f"Command timed out after {timeout}s",
            "elapsed": timeout
        }
    except FileNotFoundError:
        return {
            "success": False,
            "output": "",
            "error": "claude command not found",
            "elapsed": time.time() - start_time
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "elapsed": time.time() - start_time
        }


def _run_capture_only(cmd: list[str], timeout: int, start_time: float) -> dict[str, Any]:
    """Run command and capture output without streaming.

    Note: This uses text format for simpler capture without streaming.
    """
    # Use text format for non-streaming capture
    cmd_text = cmd.copy()
    for i, arg in enumerate(cmd_text):
        if arg == "stream-json":
            cmd_text[i] = "text"
            break

    result = subprocess.run(
        cmd_text,
        capture_output=True,
        text=True,
        timeout=timeout
    )

    elapsed = time.time() - start_time

    return {
        "success": result.returncode == 0,
        "output": result.stdout,
        "error": result.stderr,
        "elapsed": elapsed
    }


def _format_tool_call(tool_name: str, tool_input: dict) -> str:
    """Format a tool call for display."""
    display = f"{Colors.CYAN}{tool_name}{Colors.RESET}"

    # Extract the most relevant argument
    key_arg = None
    if tool_input:
        if tool_input.get("file_path"):
            key_arg = tool_input["file_path"]
        elif tool_input.get("path"):
            key_arg = tool_input["path"]
        elif tool_input.get("pattern"):
            key_arg = f'"{tool_input["pattern"]}"'
        elif tool_input.get("command"):
            cmd = tool_input["command"]
            key_arg = cmd[:50] + "..." if len(cmd) > 50 else cmd
        elif tool_input.get("query"):
            q = tool_input["query"]
            key_arg = f'"{q[:30]}..."' if len(q) > 30 else f'"{q}"'

    if key_arg:
        display += f"({Colors.GREEN}{key_arg}{Colors.RESET})"

    return display


def _run_with_streaming(cmd: list[str], timeout: int, start_time: float) -> dict[str, Any]:
    """Run command with real-time output streaming.

    Parses Claude's stream-json output format and displays text content
    as it arrives, along with formatted tool call information.
    """
    import select
    import os

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,  # Use binary mode for non-blocking reads
        bufsize=0    # Unbuffered
    )

    # Accumulated state
    line_buffer = b""
    final_result = ""
    text_chunks: list[str] = []  # Collect all text for output
    error_chunks: list[str] = []
    tool_calls: dict[str, Any] = {}  # Track tool calls by ID

    try:
        # Make stdout non-blocking on Unix
        import fcntl
        if process.stdout is None or process.stderr is None:
            raise RuntimeError("Process stdout/stderr not available")

        flags = fcntl.fcntl(process.stdout.fileno(), fcntl.F_GETFL)
        fcntl.fcntl(process.stdout.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)

        flags = fcntl.fcntl(process.stderr.fileno(), fcntl.F_GETFL)
        fcntl.fcntl(process.stderr.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)

        while True:
            # Check timeout
            if time.time() - start_time > timeout:
                process.kill()
                raise subprocess.TimeoutExpired(cmd, timeout)

            # Use select to wait for data with short timeout
            readable, _, _ = select.select(
                [process.stdout, process.stderr], [], [], 0.1
            )

            for stream in readable:
                try:
                    chunk = stream.read(4096)  # Read available bytes
                    if chunk:
                        if stream == process.stdout:
                            # Accumulate into line buffer
                            line_buffer += chunk

                            # Process complete lines
                            while b'\n' in line_buffer:
                                line_bytes, line_buffer = line_buffer.split(b'\n', 1)
                                _process_json_line(
                                    line_bytes.decode('utf-8', errors='replace'),
                                    text_chunks,
                                    tool_calls
                                )
                        else:
                            error_chunks.append(chunk.decode('utf-8', errors='replace'))
                except (IOError, BlockingIOError):
                    pass  # No data available, continue

            # Check if process finished
            if process.poll() is not None:
                # Drain remaining output (stdout/stderr verified non-None at start)
                try:
                    remaining_out = process.stdout.read() if process.stdout else None
                    if remaining_out:
                        line_buffer += remaining_out
                except Exception:
                    pass

                # Process any remaining lines
                for line in line_buffer.decode('utf-8', errors='replace').split('\n'):
                    if line.strip():
                        result = _process_json_line(line, text_chunks, tool_calls)
                        if result:
                            final_result = result

                try:
                    remaining_err = process.stderr.read() if process.stderr else None
                    if remaining_err:
                        error_chunks.append(remaining_err.decode('utf-8', errors='replace'))
                except Exception:
                    pass
                break

        elapsed = time.time() - start_time

        # Use final_result if available, otherwise join text chunks
        output = final_result if final_result else "".join(text_chunks)

        return {
            "success": process.returncode == 0,
            "output": output,
            "error": "".join(error_chunks),
            "elapsed": elapsed
        }

    except subprocess.TimeoutExpired:
        process.kill()
        raise


def _process_json_line(
    line: str,
    text_chunks: list[str],
    tool_calls: dict[str, Any]
) -> Optional[str]:
    """Process a single JSON line from Claude's stream-json output.

    Args:
        line: The JSON line to process
        text_chunks: List to append extracted text to
        tool_calls: Dict to track tool calls by ID

    Returns:
        Final result string if this is a result message, None otherwise
    """
    if not line.strip():
        return None

    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    msg_type = data.get("type", "")

    # Handle assistant messages (text output or tool calls)
    if msg_type == "assistant":
        message = data.get("message", {})
        content_list = message.get("content", [])

        for content in content_list:
            content_type = content.get("type", "")

            # Text content - display immediately
            if content_type == "text":
                text = content.get("text", "")
                if text:
                    sys.stdout.write(text)
                    sys.stdout.flush()
                    text_chunks.append(text)

            # Tool call - display formatted info
            elif content.get("name"):
                tool_name = content["name"]
                tool_input = content.get("input", {})
                tool_id = content.get("id", "")

                # Store for later result matching
                if tool_id:
                    tool_calls[tool_id] = {
                        "name": tool_name,
                        "input": tool_input
                    }

                # Display tool call
                formatted = _format_tool_call(tool_name, tool_input)
                sys.stdout.write(f"\n⏺ {formatted}\n")
                sys.stdout.flush()

    # Handle tool results
    elif msg_type == "user":
        message = data.get("message", {})
        content_list = message.get("content", [])

        for content in content_list:
            if content.get("type") == "tool_result":
                tool_use_id = content.get("tool_use_id", "")
                is_error = content.get("is_error", False)
                result_content = content.get("content", "")

                # Get tool name from stored calls
                tool_info = tool_calls.get(tool_use_id, {})
                tool_name = tool_info.get("name", "Unknown")

                # Display result summary
                icon = "❌" if is_error else "✅"
                color = Colors.RED if is_error else Colors.GREEN

                if isinstance(result_content, str):
                    lines = result_content.split('\n')
                    line_count = len(lines)
                    char_count = len(result_content)
                    summary = f"{line_count} lines, {char_count} chars"

                    # Show first line preview if available
                    preview = ""
                    if lines and lines[0].strip():
                        first_line = lines[0][:60]
                        if len(lines[0]) > 60:
                            first_line += "..."
                        preview = f"\n  ⎿  {Colors.DIM}{first_line}{Colors.RESET}"

                    sys.stdout.write(
                        f"  {icon} {color}Result{Colors.RESET} "
                        f"{Colors.DIM}({summary}){Colors.RESET}{preview}\n"
                    )
                    sys.stdout.flush()

    # Handle final result message
    elif msg_type == "result":
        result_text = data.get("result", "")
        if result_text:
            sys.stdout.write(f"\n{Colors.GREEN}{Colors.BOLD}=== Complete ==={Colors.RESET}\n\n")
            sys.stdout.flush()
            return result_text

    return None
