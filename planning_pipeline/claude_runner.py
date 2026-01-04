"""Claude Code SDK wrapper for deterministic pipeline control.

Supports two streaming modes:
1. SDK-native (default): Uses claude_agent_sdk AsyncIterator for streaming
2. stream-json: Emits JSON events compatible with `npx repomirror visualize`

Usage:
    # SDK-native streaming (default)
    result = run_claude_sync(prompt, stream=True)

    # JSON streaming for repomirror
    result = run_claude_sync(prompt, stream=True, output_format="stream-json")

    # Subprocess fallback for exact CLI compatibility
    result = run_claude_subprocess(prompt, stream_json=True)
"""

import asyncio
import json
import subprocess
import sys
import time
from typing import Any, Literal, Optional

from claude_agent_sdk import query
from claude_agent_sdk.types import (
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
)

# Type alias for output formats
OutputFormat = Literal["text", "stream-json"]


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


def _emit_stream_json(event_type: str, data: dict[str, Any]) -> None:
    """Emit a JSON event line compatible with stream-json format.

    This enables piping output to tools like `npx repomirror visualize`.

    Args:
        event_type: Event type (assistant, user, result, etc.)
        data: Event data dictionary
    """
    event = {"type": event_type, **data}
    sys.stdout.write(json.dumps(event) + "\n")
    sys.stdout.flush()


def _emit_assistant_text(text: str, tool_id: Optional[str] = None) -> None:
    """Emit stream-json event for assistant text."""
    content = [{"type": "text", "text": text}]
    _emit_stream_json("assistant", {"message": {"content": content}})


def _emit_tool_use(name: str, tool_input: dict[str, Any], tool_id: str) -> None:
    """Emit stream-json event for tool use."""
    content = [{"type": "tool_use", "id": tool_id, "name": name, "input": tool_input}]
    _emit_stream_json("assistant", {"message": {"content": content}})


def _emit_tool_result(tool_use_id: str, content: str, is_error: bool = False) -> None:
    """Emit stream-json event for tool result."""
    result_content = [{
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": content,
        "is_error": is_error
    }]
    _emit_stream_json("user", {"message": {"content": result_content}})


def _emit_result(result_text: str, is_error: bool = False) -> None:
    """Emit stream-json event for final result."""
    _emit_stream_json("result", {"result": result_text, "is_error": is_error})


async def _run_claude_async(
    prompt: str,
    tools: Optional[list[str]] = None,
    timeout: int = 300,
    stream: bool = True,
    output_format: OutputFormat = "text"
) -> dict[str, Any]:
    """Run Claude Code via Agent SDK with proper error handling.

    Args:
        prompt: The prompt to send to Claude
        tools: Optional list of tools to enable
        timeout: Maximum time in seconds to wait for response
        stream: If True, pipe output to terminal in real-time
        output_format: Output format - "text" for human-readable or
                      "stream-json" for JSON events (repomirror compatible)

    Returns:
        Dictionary with keys:
        - success: bool indicating if command completed successfully
        - output: text output from Claude
        - error: error message if any
        - elapsed: time in seconds
    """
    start_time = time.time()
    text_chunks: list[str] = []
    error_msg = ""
    result_data: dict[str, Any] | None = None
    tool_id_counter = 0  # For generating tool IDs when not provided

    # Determine if using stream-json format
    use_stream_json = output_format == "stream-json" and stream

    options = ClaudeAgentOptions(
        allowed_tools=tools if tools else [],
        permission_mode="bypassPermissions",
        max_turns=None,  # No limit on conversation turns
    )

    try:
        async for message in query(prompt=prompt, options=options):
            # Check timeout
            if time.time() - start_time > timeout:
                error_msg = f"Timed out after {timeout}s"
                continue  # Don't break - let iterator complete cleanly

            # Handle Assistant messages (text and tool calls)
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        text_chunks.append(block.text)
                        if stream:
                            if use_stream_json:
                                _emit_assistant_text(block.text)
                            else:
                                sys.stdout.write(block.text)
                                sys.stdout.flush()

                    elif isinstance(block, ToolUseBlock):
                        # Get or generate tool ID
                        tool_id = getattr(block, 'id', None) or f"tool_{tool_id_counter}"
                        tool_id_counter += 1
                        tool_input = block.input or {}

                        if stream:
                            if use_stream_json:
                                _emit_tool_use(block.name, tool_input, tool_id)
                            else:
                                formatted = _format_tool_call(block.name, tool_input)
                                sys.stdout.write(f"\n{Colors.CYAN}⏺{Colors.RESET} {formatted}\n")
                                sys.stdout.flush()

                    elif isinstance(block, ToolResultBlock):
                        # Handle tool results for stream-json format
                        if stream and use_stream_json:
                            tool_use_id = getattr(block, 'tool_use_id', '') or ''
                            content = getattr(block, 'content', '') or ''
                            is_error = getattr(block, 'is_error', False)
                            if isinstance(content, str):
                                _emit_tool_result(tool_use_id, content, is_error)

            # Handle final result - store but don't return yet
            elif isinstance(message, ResultMessage):
                elapsed = time.time() - start_time

                # Use the result text, or join collected text chunks
                output = message.result if message.result else "".join(text_chunks)

                if stream:
                    if use_stream_json:
                        _emit_result(output, message.is_error)
                    else:
                        sys.stdout.write(f"\n{Colors.GREEN}{Colors.BOLD}=== Complete ==={Colors.RESET}\n\n")
                        sys.stdout.flush()

                result_data = {
                    "success": not message.is_error,
                    "output": output,
                    "error": message.result if message.is_error else "",
                    "elapsed": elapsed,
                }
                # Don't return - let the iterator finish naturally

    except Exception as e:
        error_msg = str(e)

    # Return stored result if we got one
    if result_data:
        return result_data

    elapsed = time.time() - start_time
    return {
        "success": False if error_msg else True,
        "output": "".join(text_chunks),
        "error": error_msg,
        "elapsed": elapsed,
    }


def run_claude_sync(
    prompt: str,
    tools: Optional[list[str]] = None,
    timeout: int = 300,
    stream: bool = True,
    output_format: OutputFormat = "text"
) -> dict[str, Any]:
    """Run Claude Code via Agent SDK and return structured result.

    This is a synchronous wrapper around the async SDK.

    Args:
        prompt: The prompt to send to Claude
        tools: Optional list of tools to enable
        timeout: Maximum time in seconds to wait for response
        stream: If True, pipe output to terminal in real-time
        output_format: Output format - "text" for human-readable or
                      "stream-json" for JSON events (repomirror compatible)

    Returns:
        Dictionary with keys:
        - success: bool indicating if command completed successfully
        - output: text output from Claude
        - error: error message if any
        - elapsed: time in seconds
    """
    try:
        return asyncio.run(_run_claude_async(prompt, tools, timeout, stream, output_format))
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "elapsed": 0,
        }


def run_claude_subprocess(
    prompt: str,
    timeout: int = 300,
    stream_json: bool = True,
    cwd: Optional[str] = None
) -> dict[str, Any]:
    """Run Claude Code via subprocess for exact CLI compatibility.

    This fallback method uses the CLI directly with --output-format=stream-json
    for tools that require piping to external processes like repomirror.

    Usage:
        # Pipe to repomirror visualize
        result = run_claude_subprocess(prompt, stream_json=True)

    Args:
        prompt: The prompt to send to Claude
        timeout: Maximum time in seconds to wait for response
        stream_json: If True, use --output-format=stream-json
        cwd: Working directory for the command

    Returns:
        Dictionary with keys:
        - success: bool indicating if command completed successfully
        - output: stdout from Claude
        - error: stderr or error message
        - elapsed: time in seconds
    """
    import os
    import select

    cmd = [
        "claude",
        "--print",
        "--verbose",
        "--permission-mode", "bypassPermissions",
        "--output-format", "stream-json" if stream_json else "text",
        "-p", prompt
    ]

    start_time = time.time()

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            bufsize=0,
            cwd=cwd
        )

        # Non-blocking read setup
        import fcntl
        if process.stdout is None or process.stderr is None:
            raise RuntimeError("Process stdout/stderr not available")

        flags = fcntl.fcntl(process.stdout.fileno(), fcntl.F_GETFL)
        fcntl.fcntl(process.stdout.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)

        flags = fcntl.fcntl(process.stderr.fileno(), fcntl.F_GETFL)
        fcntl.fcntl(process.stderr.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)

        line_buffer = b""
        text_chunks: list[str] = []
        error_chunks: list[str] = []
        final_result = ""

        while True:
            if time.time() - start_time > timeout:
                process.kill()
                return {
                    "success": False,
                    "output": "".join(text_chunks),
                    "error": f"Timed out after {timeout}s",
                    "elapsed": timeout
                }

            readable, _, _ = select.select(
                [process.stdout, process.stderr], [], [], 0.1
            )

            for stream in readable:
                try:
                    chunk = stream.read(4096)
                    if chunk:
                        if stream == process.stdout:
                            line_buffer += chunk

                            # Process and emit complete lines
                            while b'\n' in line_buffer:
                                line_bytes, line_buffer = line_buffer.split(b'\n', 1)
                                line = line_bytes.decode('utf-8', errors='replace')
                                if line.strip():
                                    # Pass through to stdout for piping
                                    sys.stdout.write(line + "\n")
                                    sys.stdout.flush()

                                    # Parse JSON to extract text for return value
                                    try:
                                        data = json.loads(line)
                                        if data.get("type") == "assistant":
                                            for content in data.get("message", {}).get("content", []):
                                                if content.get("type") == "text":
                                                    text_chunks.append(content.get("text", ""))
                                        elif data.get("type") == "result":
                                            final_result = data.get("result", "")
                                    except json.JSONDecodeError:
                                        pass
                        else:
                            error_chunks.append(chunk.decode('utf-8', errors='replace'))
                except (IOError, BlockingIOError):
                    pass

            if process.poll() is not None:
                # Drain remaining output
                try:
                    remaining = process.stdout.read()
                    if remaining:
                        for line in remaining.decode('utf-8', errors='replace').split('\n'):
                            if line.strip():
                                sys.stdout.write(line + "\n")
                                sys.stdout.flush()
                except Exception:
                    pass
                break

        elapsed = time.time() - start_time
        output = final_result if final_result else "".join(text_chunks)

        return {
            "success": process.returncode == 0,
            "output": output,
            "error": "".join(error_chunks),
            "elapsed": elapsed
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
