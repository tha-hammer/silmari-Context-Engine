"""Claude Code SDK wrapper for deterministic pipeline control.

Supports two invocation modes:
1. SDK-native (default): Uses claude_agent_sdk AsyncIterator for streaming
2. CLI subprocess: Uses subprocess with PTY wrapping for exact CLI compatibility

Streaming formats:
- text: Human-readable terminal output
- stream-json: JSON events compatible with `npx repomirror visualize`

Authentication:
- Uses OAuth tokens from ~/.claude/.credentials.json
- Automatically refreshes expired tokens using the refresh token
- Proactively refreshes tokens that expire within 5 minutes

Usage:
    # Unified interface (recommended) - auto-selects mode
    result = invoke_claude(prompt, invocation_mode="auto")

    # SDK-native streaming (default)
    result = invoke_claude(prompt, invocation_mode="sdk")

    # CLI subprocess for exact CLI compatibility
    result = invoke_claude(prompt, invocation_mode="cli")

    # Legacy functions (still supported)
    result = run_claude_sync(prompt, stream=True)
    result = run_claude_subprocess(prompt, stream_json=True)

Configuration:
    invocation_mode can be set via:
    1. Function parameter (highest priority)
    2. Environment variable: CLAUDE_INVOCATION_MODE
    3. Default: 'auto' (prefers SDK, falls back to CLI)
"""
from pathlib import Path
import asyncio
import json
import os
import requests
import shutil
import subprocess
import sys
import time
from typing import Any, Literal, Optional, TypedDict

# Optional import - claude_agent_sdk may not be installed
try:
    from claude_agent_sdk import query
    from claude_agent_sdk.types import (
        ClaudeAgentOptions,
        AssistantMessage,
        ResultMessage,
        TextBlock,
        ToolUseBlock,
        ToolResultBlock,
    )
    HAS_CLAUDE_SDK = True
except ImportError:
    HAS_CLAUDE_SDK = False
    # Stub types for when SDK is not available
    query = None  # type: ignore
    ClaudeAgentOptions = None  # type: ignore
    AssistantMessage = None  # type: ignore
    ResultMessage = None  # type: ignore
    TextBlock = None  # type: ignore
    ToolUseBlock = None  # type: ignore
    ToolResultBlock = None  # type: ignore

# Type aliases
OutputFormat = Literal["text", "stream-json"]
InvocationMode = Literal["cli", "sdk", "auto"]
PermissionMode = Literal["default", "acceptEdits", "plan", "bypassPermissions"]

# Output truncation limit (as per REQ_000.1.18)
MAX_OUTPUT_CHARS = 30000

# OAuth configuration for Claude CLI
CLAUDE_OAUTH_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"


class ClaudeResult(TypedDict):
    """Standardized result type for Claude invocations."""

    success: bool
    output: str
    error: str
    elapsed: float
    session_id: str  # Empty for CLI mode, session ID for SDK mode
    invocation_mode: str  # 'cli' or 'sdk'


def _get_invocation_mode() -> InvocationMode:
    """Get the configured invocation mode from environment.

    Returns:
        InvocationMode: 'cli', 'sdk', or 'auto' (default)
    """
    mode = os.environ.get("CLAUDE_INVOCATION_MODE", "auto").lower()
    if mode in ("cli", "sdk", "auto"):
        return mode  # type: ignore
    return "auto"


def _select_invocation_mode(
    mode: InvocationMode,
    output_format: OutputFormat = "text",
    has_hooks: bool = False,
    has_custom_tools: bool = False,
    needs_interrupt: bool = False,
    needs_multi_turn: bool = False,
    verbose: bool = False,
) -> Literal["cli", "sdk"]:
    """Select the actual invocation mode based on configuration and features.

    Args:
        mode: Requested mode ('cli', 'sdk', or 'auto')
        output_format: Output format - stream-json may prefer CLI
        has_hooks: Whether hooks are configured (SDK-only feature)
        has_custom_tools: Whether custom tools are configured (SDK-only feature)
        needs_interrupt: Whether interrupt capability is needed (SDK-only feature)
        needs_multi_turn: Whether multi-turn context is needed (SDK-only feature)
        verbose: Whether to log decision rationale

    Returns:
        Literal["cli", "sdk"]: The selected invocation mode
    """
    # If explicit mode requested, use it (unless SDK unavailable)
    if mode == "cli":
        if verbose:
            print("[DEBUG] Using CLI mode (explicitly requested)", file=sys.stderr)
        return "cli"

    if mode == "sdk":
        if not HAS_CLAUDE_SDK:
            if verbose:
                print("[DEBUG] SDK requested but unavailable, falling back to CLI", file=sys.stderr)
            return "cli"
        if verbose:
            print("[DEBUG] Using SDK mode (explicitly requested)", file=sys.stderr)
        return "sdk"

    # Auto mode: select based on features and availability
    # SDK-only features that force SDK mode
    sdk_required_features = []
    if has_hooks:
        sdk_required_features.append("hooks")
    if has_custom_tools:
        sdk_required_features.append("custom_tools")
    if needs_interrupt:
        sdk_required_features.append("interrupt")
    if needs_multi_turn:
        sdk_required_features.append("multi_turn")

    if sdk_required_features:
        if not HAS_CLAUDE_SDK:
            features_str = ", ".join(sdk_required_features)
            if verbose:
                print(f"[DEBUG] SDK required for {features_str} but unavailable, falling back to CLI", file=sys.stderr)
            return "cli"
        if verbose:
            features_str = ", ".join(sdk_required_features)
            print(f"[DEBUG] Using SDK mode (required for: {features_str})", file=sys.stderr)
        return "sdk"

    # For stream-json output, CLI is preferred for exact compatibility
    if output_format == "stream-json":
        if verbose:
            print("[DEBUG] Using CLI mode (stream-json format)", file=sys.stderr)
        return "cli"

    # Default: prefer SDK if available
    if HAS_CLAUDE_SDK:
        if verbose:
            print("[DEBUG] Using SDK mode (auto-selected, SDK available)", file=sys.stderr)
        return "sdk"

    if verbose:
        print("[DEBUG] Using CLI mode (auto-selected, SDK unavailable)", file=sys.stderr)
    return "cli"


def _truncate_output(output: str, max_chars: int = MAX_OUTPUT_CHARS) -> str:
    """Truncate output if it exceeds the maximum character limit.

    Args:
        output: The output string to truncate
        max_chars: Maximum number of characters allowed

    Returns:
        Truncated output with truncation notice if needed
    """
    if len(output) <= max_chars:
        return output
    truncated = output[:max_chars]
    return f"{truncated}\n\n[OUTPUT TRUNCATED - exceeded {max_chars} characters]"
CLAUDE_OAUTH_ENDPOINT = "https://console.anthropic.com/api/oauth/token"


def get_credentials_path() -> Path:
    """Get the path to the Claude credentials file."""
    return Path.home() / ".claude" / ".credentials.json"


def read_credentials() -> dict[str, Any]:
    """Read the Claude OAuth credentials from disk.

    Returns:
        Credentials dictionary with claudeAiOauth key

    Raises:
        FileNotFoundError: If credentials file doesn't exist
        json.JSONDecodeError: If credentials file is invalid JSON
    """
    path = get_credentials_path()
    with open(path, 'r') as f:
        return json.load(f)


def save_credentials(creds: dict[str, Any]) -> None:
    """Save updated OAuth credentials to disk.

    Creates a backup before writing.

    Args:
        creds: Credentials dictionary to save
    """
    path = get_credentials_path()

    # Create backup before writing
    backup_path = path.with_suffix('.json.bak')
    if path.exists():
        shutil.copy2(path, backup_path)

    with open(path, 'w') as f:
        json.dump(creds, f, indent=2)


def refresh_oauth_token() -> None:
    """Refresh the OAuth access token using the refresh token.

    Reads credentials from disk, calls the OAuth refresh endpoint,
    and saves the new tokens back to disk.

    Raises:
        FileNotFoundError: If credentials file doesn't exist
        ValueError: If no refresh token is available
        requests.HTTPError: If the refresh request fails
    """
    creds = read_credentials()

    oauth = creds.get('claudeAiOauth')
    if not oauth or not oauth.get('refreshToken'):
        raise ValueError("No refresh token available")

    print("[DEBUG] Refreshing OAuth token...", file=sys.stderr)

    # Build refresh request
    req_body = {
        'grant_type': 'refresh_token',
        'refresh_token': oauth['refreshToken'],
        'client_id': CLAUDE_OAUTH_CLIENT_ID,
    }

    # Make HTTP request
    response = requests.post(
        CLAUDE_OAUTH_ENDPOINT,
        json=req_body,
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()

    # Update credentials
    oauth['accessToken'] = data['access_token']
    oauth['refreshToken'] = data['refresh_token']
    oauth['expiresAt'] = int(time.time() * 1000) + (data['expires_in'] * 1000)

    # Parse scopes
    if data.get('scope'):
        oauth['scopes'] = data['scope'].split(' ')

    # Save updated credentials
    save_credentials(creds)

    from datetime import datetime
    expires_at = datetime.fromtimestamp(oauth['expiresAt'] / 1000)
    print(f"[DEBUG] OAuth token refreshed successfully, expires at {expires_at.isoformat()}", file=sys.stderr)


def is_oauth_expired_error(output: str) -> bool:
    """Check if the error indicates an expired OAuth token.

    Args:
        output: Combined stdout/stderr output from Claude CLI

    Returns:
        True if the output indicates OAuth token expiration
    """
    return ('authentication_error' in output and
            ('OAuth token has expired' in output or '401' in output))


def ensure_oauth_token_fresh() -> None:
    """Proactively refresh OAuth token if it expires within 5 minutes.

    This is called before running Claude to avoid mid-execution failures.
    """
    try:
        creds = read_credentials()
        oauth = creds.get('claudeAiOauth')
        if oauth and oauth.get('expiresAt'):
            expires_at_ms = oauth['expiresAt']
            now_ms = int(time.time() * 1000)
            time_until_expiry_ms = expires_at_ms - now_ms

            # Refresh if expires within 5 minutes (300000 ms)
            if time_until_expiry_ms < 300000:
                minutes_left = time_until_expiry_ms / 60000
                print(f"[DEBUG] OAuth token expires soon ({minutes_left:.1f} min), proactively refreshing...",
                      file=sys.stderr)
                refresh_oauth_token()
    except Exception as e:
        print(f"[DEBUG] Proactive OAuth refresh check failed: {e}", file=sys.stderr)


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


def _truncate_arg(value: str, max_len: int = 50) -> str:
    """Truncate a string to max_len characters with ellipsis suffix.

    REQ_006.4: Truncate long arguments to 50 characters for terminal readability.

    Args:
        value: The string to truncate
        max_len: Maximum length before truncation (default 50)

    Returns:
        Truncated string with '...' if needed, original otherwise
    """
    if not value:
        return value
    if len(value) <= max_len:
        return value
    return value[:max_len] + "..."


def _extract_key_arg(tool_input: dict) -> str | None:
    """Extract the most relevant key argument from tool input.

    REQ_006.3: Extract key argument based on tool-specific patterns.
    Priority order: file_path > path > command > pattern > query > url > description

    Args:
        tool_input: Dictionary of tool input parameters

    Returns:
        The extracted key argument string, or None if not found
    """
    if not tool_input:
        return None

    # Priority order per REQ_006.3
    if tool_input.get("file_path"):
        return tool_input["file_path"]
    if tool_input.get("path"):
        return tool_input["path"]
    if tool_input.get("command"):
        return _truncate_arg(tool_input["command"])
    if tool_input.get("pattern"):
        return f'"{tool_input["pattern"]}"'
    if tool_input.get("query"):
        q = tool_input["query"]
        return f'"{_truncate_arg(q, 30)}"' if len(q) > 30 else f'"{q}"'
    if tool_input.get("url"):
        return _truncate_arg(tool_input["url"])
    if tool_input.get("description"):
        return _truncate_arg(tool_input["description"])

    return None


def _format_tool_call(tool_name: str, tool_input: dict) -> str:
    """Format a tool call for display with colored output.

    REQ_006.2: Format tool call with tool name in CYAN and key argument in GREEN.

    Args:
        tool_name: Name of the tool being invoked
        tool_input: Dictionary of tool input parameters

    Returns:
        Formatted string suitable for terminal display
    """
    display = f"{Colors.CYAN}{tool_name}{Colors.RESET}"

    key_arg = _extract_key_arg(tool_input)
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
    if not HAS_CLAUDE_SDK:
        return {
            "success": False,
            "output": "",
            "error": "claude_agent_sdk not installed. Install with: pip install claude-agent-sdk",
            "elapsed": 0,
        }

    start_time = time.time()
    text_chunks: list[str] = []
    error_msg = ""
    result_data: dict[str, Any] | None = None
    tool_id_counter = 0  # For generating tool IDs when not provided

    # Determine if using stream-json format
    use_stream_json = output_format == "stream-json" and stream

    # Set max output tokens to allow longer responses (prevents truncation)
    os.environ.setdefault("CLAUDE_CODE_MAX_OUTPUT_TOKENS", "64000")
    os.environ.setdefault("CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS", "36000")
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

                # Apply output truncation (REQ_000.1.18)
                output = _truncate_output(output)

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
    # Apply output truncation (REQ_000.1.18)
    output = _truncate_output("".join(text_chunks))
    return {
        "success": False if error_msg else True,
        "output": output,
        "error": error_msg,
        "elapsed": elapsed,
    }


# Module-level event loop for reuse across SDK calls
# This prevents the "Event loop is closed" errors from subprocess cleanup
_claude_event_loop: Optional[asyncio.AbstractEventLoop] = None
_claude_loop_lock = None  # Will be initialized lazily


def _get_claude_event_loop() -> asyncio.AbstractEventLoop:
    """Get or create the shared event loop for Claude SDK calls.

    Using a shared loop prevents subprocess cleanup errors that occur when
    loops are created and destroyed repeatedly during garbage collection.

    Returns:
        The shared event loop for Claude SDK operations.
    """
    global _claude_event_loop, _claude_loop_lock
    import threading

    # Lazy initialize the lock
    if _claude_loop_lock is None:
        _claude_loop_lock = threading.Lock()

    with _claude_loop_lock:
        if _claude_event_loop is None or _claude_event_loop.is_closed():
            _claude_event_loop = asyncio.new_event_loop()
            # Set custom exception handler to suppress subprocess cleanup errors
            def _exception_handler(loop: asyncio.AbstractEventLoop, context: dict) -> None:
                exception = context.get("exception")
                # Suppress event loop closed errors during subprocess cleanup
                if exception and "Event loop is closed" in str(exception):
                    return
                # Suppress cancel scope errors from anyio
                if exception and "cancel scope" in str(exception):
                    return
                loop.default_exception_handler(context)

            _claude_event_loop.set_exception_handler(_exception_handler)

        return _claude_event_loop


def run_claude_sync(
    prompt: str,
    tools: Optional[list[str]] = None,
    timeout: int = 1200,
    stream: bool = True,
    output_format: OutputFormat = "text",
    cwd: Optional[Path] = None,
) -> dict[str, Any]:
    """Run Claude Code via Agent SDK and return structured result.

    This is a synchronous wrapper around the async SDK.

    Uses a shared event loop to avoid "Event loop is closed" errors that
    occur when subprocess cleanup happens after the event loop has been
    destroyed.

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
        # Use shared event loop to prevent subprocess cleanup errors
        loop = _get_claude_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_run_claude_async(prompt, tools, timeout, stream, output_format, cwd))
    except RuntimeError as e:
        # Handle case where loop was unexpectedly closed
        if "Event loop is closed" in str(e) or "cannot schedule" in str(e):
            # Reset the shared loop and retry once
            global _claude_event_loop
            _claude_event_loop = None
            try:
                loop = _get_claude_event_loop()
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(_run_claude_async(prompt, tools, timeout, stream, output_format, cwd))
            except Exception as retry_error:
                return {
                    "success": False,
                    "output": "",
                    "error": f"SDK retry failed: {retry_error}",
                    "elapsed": 0,
                }
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "elapsed": 0,
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "elapsed": 0,
        }


def run_claude_subprocess(
    prompt: str,
    timeout: int = 1200,
    stream_json: bool = True,
    cwd: Optional[str] = None,
    _allow_retry: bool = True,
) -> dict[str, Any]:
    """Run Claude Code via subprocess for exact CLI compatibility.

    Uses the 'script' command to wrap the process in a PTY, enabling
    real-time streaming output from the claude CLI.

    Authentication:
    - Uses OAuth tokens from ~/.claude/.credentials.json
    - Automatically refreshes expired tokens and retries on 401 errors

    Usage:
        # Pipe to repomirror visualize
        result = run_claude_subprocess(prompt, stream_json=True)

    Args:
        prompt: The prompt to send to Claude
        timeout: Maximum time in seconds to wait for response
        stream_json: If True, emit raw JSON lines to stdout for piping
        cwd: Working directory for the command
        _allow_retry: Internal flag to prevent infinite retry loops

    Returns:
        Dictionary with keys:
        - success: bool indicating if command completed successfully
        - output: stdout from Claude
        - error: stderr or error message
        - elapsed: time in seconds
    """
    import shlex

    # Proactively refresh OAuth token if it's about to expire
    ensure_oauth_token_fresh()

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

        # Apply output truncation (REQ_000.1.18)
        output = _truncate_output(output)

        # Check for OAuth expiration and retry if allowed
        if is_oauth_expired_error(output) and _allow_retry:
            print("[DEBUG] OAuth token expired, refreshing and retrying...", file=sys.stderr)
            try:
                refresh_oauth_token()
                print("[DEBUG] OAuth token refreshed, retrying Claude invocation...", file=sys.stderr)
                return run_claude_subprocess(prompt, timeout, stream_json, cwd, _allow_retry=False)
            except Exception as refresh_err:
                return {
                    "success": False,
                    "output": output,
                    "error": f"OAuth token expired and refresh failed: {refresh_err}",
                    "elapsed": elapsed
                }

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


def invoke_claude(
    prompt: str,
    invocation_mode: Optional[InvocationMode] = None,
    tools: Optional[list[str]] = None,
    timeout: int = 1200,
    stream: bool = True,
    output_format: OutputFormat = "text",
    permission_mode: PermissionMode = "bypassPermissions",
    cwd: Optional[Path] = None,
    verbose: bool = False,
    has_hooks: bool = False,
    has_custom_tools: bool = False,
    needs_interrupt: bool = False,
    needs_multi_turn: bool = False,
) -> ClaudeResult:
    """Unified interface for invoking Claude Code.

    This function abstracts over the CLI subprocess and SDK approaches,
    automatically selecting the best mode based on configuration and
    feature requirements.

    Args:
        prompt: The prompt to send to Claude
        invocation_mode: 'cli', 'sdk', or 'auto' (default from env or 'auto')
        tools: Optional list of tools to enable (SDK-only)
        timeout: Maximum time in seconds to wait for response
        stream: If True, pipe output to terminal in real-time
        output_format: Output format - "text" or "stream-json"
        permission_mode: Permission mode - 'default', 'acceptEdits', 'plan', 'bypassPermissions'
        cwd: Working directory for Claude Code
        verbose: If True, log mode selection rationale
        has_hooks: Hint that hooks are configured (forces SDK if available)
        has_custom_tools: Hint that custom tools are configured (forces SDK if available)
        needs_interrupt: Hint that interrupt capability is needed (forces SDK if available)
        needs_multi_turn: Hint that multi-turn context is needed (forces SDK if available)

    Returns:
        ClaudeResult with keys:
        - success: bool indicating if command completed successfully
        - output: text output from Claude
        - error: error message if any
        - elapsed: time in seconds
        - session_id: empty for CLI, session ID for SDK
        - invocation_mode: 'cli' or 'sdk' (which mode was actually used)

    Example:
        # Auto-select mode (recommended)
        result = invoke_claude("What is 2 + 2?")

        # Force CLI mode
        result = invoke_claude("What is 2 + 2?", invocation_mode="cli")

        # Force SDK mode
        result = invoke_claude("What is 2 + 2?", invocation_mode="sdk")
    """
    # Determine invocation mode
    if invocation_mode is None:
        invocation_mode = _get_invocation_mode()

    selected_mode = _select_invocation_mode(
        mode=invocation_mode,
        output_format=output_format,
        has_hooks=has_hooks,
        has_custom_tools=has_custom_tools,
        needs_interrupt=needs_interrupt,
        needs_multi_turn=needs_multi_turn,
        verbose=verbose,
    )

    # Invoke using the selected mode
    if selected_mode == "cli":
        # CLI subprocess mode
        result = run_claude_subprocess(
            prompt=prompt,
            timeout=timeout,
            stream_json=(output_format == "stream-json" and stream),
            cwd=str(cwd) if cwd else None,
        )
        return ClaudeResult(
            success=result["success"],
            output=result["output"],
            error=result.get("error", ""),
            elapsed=result["elapsed"],
            session_id="",  # CLI mode has no session ID
            invocation_mode="cli",
        )
    else:
        # SDK mode
        result = run_claude_sync(
            prompt=prompt,
            tools=tools,
            timeout=timeout,
            stream=stream,
            output_format=output_format,
            cwd=cwd,
        )
        return ClaudeResult(
            success=result["success"],
            output=result["output"],
            error=result.get("error", ""),
            elapsed=result["elapsed"],
            session_id=result.get("session_id", ""),  # May be set by SDK
            invocation_mode="sdk",
        )


# Export public API
__all__ = [
    # Main unified interface
    "invoke_claude",
    # Legacy functions
    "run_claude_sync",
    "run_claude_subprocess",
    # OAuth utilities
    "read_credentials",
    "save_credentials",
    "refresh_oauth_token",
    "ensure_oauth_token_fresh",
    "is_oauth_expired_error",
    # Configuration helpers
    "_get_invocation_mode",
    "_select_invocation_mode",
    "_truncate_output",
    # Types
    "ClaudeResult",
    "OutputFormat",
    "InvocationMode",
    "PermissionMode",
    # Constants
    "HAS_CLAUDE_SDK",
    "MAX_OUTPUT_CHARS",
    # Formatting helpers
    "Colors",
    "_format_tool_call",
]
