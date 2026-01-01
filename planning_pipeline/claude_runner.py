"""Claude Code subprocess wrapper for deterministic pipeline control."""

import subprocess
import sys
import time
from typing import Any, Optional


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
        "--permission-mode", "bypassPermissions",
        "--output-format", "text",
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
    """Run command and capture output without streaming."""
    result = subprocess.run(
        cmd,
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


def _run_with_streaming(cmd: list[str], timeout: int, start_time: float) -> dict[str, Any]:
    """Run command with real-time output streaming."""
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1  # Line buffered
    )

    output_lines = []
    error_lines = []

    try:
        # Read stdout in real-time
        while True:
            # Check timeout
            if time.time() - start_time > timeout:
                process.kill()
                raise subprocess.TimeoutExpired(cmd, timeout)

            line = process.stdout.readline()
            if line:
                print(line, end='', flush=True)
                output_lines.append(line)
            elif process.poll() is not None:
                # Process finished
                break

        # Capture any remaining output
        remaining_out, remaining_err = process.communicate(timeout=5)
        if remaining_out:
            print(remaining_out, end='', flush=True)
            output_lines.append(remaining_out)
        if remaining_err:
            error_lines.append(remaining_err)

        elapsed = time.time() - start_time

        return {
            "success": process.returncode == 0,
            "output": "".join(output_lines),
            "error": "".join(error_lines),
            "elapsed": elapsed
        }

    except subprocess.TimeoutExpired:
        process.kill()
        raise
