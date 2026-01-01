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
    """Run command with real-time output streaming.

    Uses character-by-character reading to ensure output appears immediately,
    not waiting for newlines (which Claude may not produce until completion).
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

    output_chunks = []
    error_chunks = []

    try:
        # Make stdout non-blocking on Unix
        import fcntl
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
                            # Decode and output immediately
                            text = chunk.decode('utf-8', errors='replace')
                            sys.stdout.write(text)
                            sys.stdout.flush()
                            output_chunks.append(text)
                        else:
                            error_chunks.append(chunk.decode('utf-8', errors='replace'))
                except (IOError, BlockingIOError):
                    pass  # No data available, continue

            # Check if process finished
            if process.poll() is not None:
                # Drain remaining output
                try:
                    remaining_out = process.stdout.read()
                    if remaining_out:
                        text = remaining_out.decode('utf-8', errors='replace')
                        sys.stdout.write(text)
                        sys.stdout.flush()
                        output_chunks.append(text)
                except:
                    pass
                try:
                    remaining_err = process.stderr.read()
                    if remaining_err:
                        error_chunks.append(remaining_err.decode('utf-8', errors='replace'))
                except:
                    pass
                break

        elapsed = time.time() - start_time

        return {
            "success": process.returncode == 0,
            "output": "".join(output_chunks),
            "error": "".join(error_chunks),
            "elapsed": elapsed
        }

    except subprocess.TimeoutExpired:
        process.kill()
        raise
