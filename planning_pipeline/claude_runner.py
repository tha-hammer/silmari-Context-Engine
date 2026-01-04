"""Claude Code SDK wrapper for deterministic pipeline control."""

import asyncio
import sys
import time
from typing import Any, Optional

from claude_agent_sdk import query
from claude_agent_sdk.types import (
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
)


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


async def _run_claude_async(
    prompt: str,
    tools: Optional[list[str]] = None,
    timeout: int = 300,
    stream: bool = True
) -> dict[str, Any]:
    """Run Claude Code via Agent SDK with proper error handling.

    Args:
        prompt: The prompt to send to Claude
        tools: Optional list of tools to enable
        timeout: Maximum time in seconds to wait for response
        stream: If True, pipe output to terminal in real-time

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
                            sys.stdout.write(block.text)
                            sys.stdout.flush()
                    elif isinstance(block, ToolUseBlock):
                        if stream:
                            formatted = _format_tool_call(block.name, block.input or {})
                            sys.stdout.write(f"\n{Colors.CYAN}⏺{Colors.RESET} {formatted}\n")
                            sys.stdout.flush()

            # Handle final result - store but don't return yet
            elif isinstance(message, ResultMessage):
                elapsed = time.time() - start_time
                if stream:
                    sys.stdout.write(f"\n{Colors.GREEN}{Colors.BOLD}=== Complete ==={Colors.RESET}\n\n")
                    sys.stdout.flush()

                # Use the result text, or join collected text chunks
                output = message.result if message.result else "".join(text_chunks)

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
    stream: bool = True
) -> dict[str, Any]:
    """Run Claude Code via Agent SDK and return structured result.

    This is a synchronous wrapper around the async SDK.

    Args:
        prompt: The prompt to send to Claude
        tools: Optional list of tools to enable
        timeout: Maximum time in seconds to wait for response
        stream: If True, pipe output to terminal in real-time

    Returns:
        Dictionary with keys:
        - success: bool indicating if command completed successfully
        - output: text output from Claude
        - error: error message if any
        - elapsed: time in seconds
    """
    try:
        return asyncio.run(_run_claude_async(prompt, tools, timeout, stream))
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "elapsed": 0,
        }
