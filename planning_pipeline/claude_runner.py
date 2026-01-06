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
from pathlib import Path
import asyncio
import json
import os
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
    timeout: int = 1300,
    stream: bool = True,
    output_format: OutputFormat = "text",
    cwd: Optional[Path] = None,
) -> dict[str, Any]:
    """Run Claude Code via Agent SDK with proper error handling.

    Args:
        prompt: The prompt to send to Claude
        tools: Optional list of tools to enable
        timeout: Maximum time in seconds to wait for response
        stream: If True, pipe output to terminal in real-time
        output_format: Output format - "text" for human-readable or
                      "stream-json" for JSON events (repomirror compatible)
        cwd: Working directory for Claude Code. Defaults to current directory.

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

    # Set max output tokens to allow longer responses (prevents truncation)
    os.environ.setdefault("CLAUDE_CODE_MAX_OUTPUT_TOKENS", "128000")
    project_path = cwd if cwd else Path.cwd()

    options = ClaudeAgentOptions(
        allowed_tools=tools if tools else [],
        permission_mode="bypassPermissions",
        max_turns=None,  # No limit on conversation turns
        cwd=project_path,  # Working directory for Claude Code
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

                # Debug logging for error diagnosis (silmari-Context-Engine-cv34)
                if message.is_error:
                    print(f"\n{Colors.RED}[DEBUG] ResultMessage error: is_error={message.is_error}, result={repr(message.result)}{Colors.RESET}")

                # Use the result text, or join collected text chunks
                output = message.result if message.result else "".join(text_chunks)

                if stream:
                    if use_stream_json:
                        _emit_result(output, message.is_error)
                    else:
                        sys.stdout.write(f"\n{Colors.GREEN}{Colors.BOLD}=== Complete ==={Colors.RESET}\n\n")
                        sys.stdout.flush()

                # Fix: Handle None error from SDK (silmari-Context-Engine-cv34)
                error_value = ""
                if message.is_error:
                    error_value = message.result or "Unknown SDK error (ResultMessage.result was None)"

                result_data = {
                    "success": not message.is_error,
                    "output": output,
                    "error": error_value,
                    "elapsed": elapsed,
                }
                # Don't return - let the iterator finish naturally

    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {e}"
        # Log full traceback for debugging
        tb = traceback.format_exc()
        if "Fatal error" in str(e) or "exit code" in str(e):
            error_msg = f"{error_msg}\nTraceback:\n{tb}"

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
    output_format: OutputFormat = "text",
    cwd: Optional[Path] = None,
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
        cwd: Working directory for Claude Code. Defaults to current directory.

    Returns:
        Dictionary with keys:
        - success: bool indicating if command completed successfully
        - output: text output from Claude
        - error: error message if any
        - elapsed: time in seconds
    """
    try:
        return asyncio.run(_run_claude_async(prompt, tools, timeout, stream, output_format, cwd))
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

    Uses the 'script' command to wrap the process in a PTY, enabling
    real-time streaming output from the claude CLI.

    Usage:
        # Pipe to repomirror visualize
        result = run_claude_subprocess(prompt, stream_json=True)

    Args:
        prompt: The prompt to send to Claude
        timeout: Maximum time in seconds to wait for response
        stream_json: If True, emit raw JSON lines to stdout for piping
        cwd: Working directory for the command

    Returns:
        Dictionary with keys:
        - success: bool indicating if command completed successfully
        - output: stdout from Claude
        - error: stderr or error message
        - elapsed: time in seconds
    """
    import shlex

    start_time = time.time()

    # Build the claude command
    claude_cmd = (
        f'claude --print --verbose --permission-mode bypassPermissions '
        f'--output-format stream-json -p {shlex.quote(prompt)}'
    )

    # Use 'script' to wrap in a PTY for real-time streaming
    # -q: quiet (no "Script started" messages)
    # -c: command to run
    # /dev/null: don't save transcript to file
    cmd = ["script", "-q", "-c", claude_cmd, "/dev/null"]

    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=cwd,
        )

        line_buffer = b""
        text_chunks: list[str] = []
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

            # Read available data (blocking with small chunks)
            try:
                chunk = process.stdout.read1(4096)  # type: ignore
            except AttributeError:
                # Fallback for older Python
                import select as sel
                readable, _, _ = sel.select([process.stdout], [], [], 0.1)
                if readable:
                    chunk = process.stdout.read(4096)
                else:
                    chunk = b""

            if chunk:
                line_buffer += chunk

                # Process complete lines
                while b'\n' in line_buffer:
                    line_bytes, line_buffer = line_buffer.split(b'\n', 1)
                    line = line_bytes.decode('utf-8', errors='replace').strip()

                    # Skip empty lines and script noise
                    if not line or line.startswith('Script '):
                        continue

                    if stream_json:
                        # JSON mode: pass through raw JSON for piping
                        sys.stdout.write(line + "\n")
                        sys.stdout.flush()

                    # Parse JSON to extract text
                    try:
                        data = json.loads(line)
                        msg_type = data.get("type")

                        if msg_type == "content_block_delta":
                            delta = data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                text = delta.get("text", "")
                                if text and not stream_json:
                                    sys.stdout.write(text)
                                    sys.stdout.flush()
                                text_chunks.append(text)
                        elif msg_type == "assistant":
                            for content in data.get("message", {}).get("content", []):
                                if content.get("type") == "text":
                                    text = content.get("text", "")
                                    if text and not stream_json:
                                        sys.stdout.write(text)
                                        sys.stdout.flush()
                                    text_chunks.append(text)
                        elif msg_type == "result":
                            final_result = data.get("result", "")
                    except json.JSONDecodeError:
                        # Not JSON - could be script noise or other output
                        if not stream_json and not line.startswith('{'):
                            sys.stdout.write(line + "\n")
                            sys.stdout.flush()
                        text_chunks.append(line + "\n")

            # Check if process exited
            if process.poll() is not None:
                # Drain remaining output
                remaining = process.stdout.read()
                if remaining:
                    line_buffer += remaining

                # Process remaining buffer
                for line in line_buffer.decode('utf-8', errors='replace').split('\n'):
                    line = line.strip()
                    if not line or line.startswith('Script '):
                        continue
                    if stream_json:
                        sys.stdout.write(line + "\n")
                        sys.stdout.flush()
                    try:
                        data = json.loads(line)
                        if data.get("type") == "content_block_delta":
                            delta = data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                text = delta.get("text", "")
                                if text and not stream_json:
                                    sys.stdout.write(text)
                                    sys.stdout.flush()
                                text_chunks.append(text)
                        elif data.get("type") == "result":
                            final_result = data.get("result", "")
                    except json.JSONDecodeError:
                        if not stream_json and not line.startswith('{'):
                            sys.stdout.write(line + "\n")
                            sys.stdout.flush()
                        text_chunks.append(line + "\n")
                break

            # Small sleep to prevent busy loop when no data
            if not chunk:
                time.sleep(0.05)

        elapsed = time.time() - start_time
        output = final_result if final_result else "".join(text_chunks)

        return {
            "success": process.returncode == 0,
            "output": output,
            "error": "",
            "elapsed": elapsed
        }

    except FileNotFoundError:
        return {
            "success": False,
            "output": "",
            "error": "claude or script command not found",
            "elapsed": time.time() - start_time
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "elapsed": time.time() - start_time
        }
