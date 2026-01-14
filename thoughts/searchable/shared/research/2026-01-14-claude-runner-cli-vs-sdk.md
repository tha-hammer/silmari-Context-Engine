---
date: 2026-01-14T10:20:29-05:00
researcher: claude
git_commit: 0858e474bda8a4e25f6b76d428f62ba4985f77fd
branch: main
repository: silmari-Context-Engine
topic: "Claude Code CLI vs Agent SDK Interaction Patterns"
tags: [research, codebase, claude-runner, agent-sdk, cli, streaming]
status: complete
last_updated: 2026-01-14
last_updated_by: claude
---

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     Claude Code CLI vs Agent SDK Research                        │
│                                                                                 │
│  Status: Complete                                    Date: 2026-01-14          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

# Research: Claude Code CLI vs Agent SDK Interaction Patterns

**Date**: 2026-01-14T10:20:29-05:00
**Researcher**: claude
**Git Commit**: 0858e474bda8a4e25f6b76d428f62ba4985f77fd
**Branch**: main
**Repository**: silmari-Context-Engine

## Research Question

Document the current CLI-based interaction with Claude Code, including how Claude Code is called and how CLI output is rendered to screen. Compare to the simpler SDK approach demonstrated in `test-conversation.py`.

---

## Summary

The codebase uses **two distinct approaches** for invoking Claude Code:

| Approach | Implementation | Lines of Code | Complexity |
|----------|---------------|---------------|------------|
| CLI/Subprocess | `claude_runner.py` | ~670 lines | High |
| Agent SDK | `test-conversation.py` | ~65 lines | Low |

The CLI approach requires:
- PTY wrapping via `script` command for streaming
- JSON stream event parsing (3+ event types)
- OAuth token management with refresh
- Complex buffer management for partial lines
- ANSI color formatting for terminal output

The SDK approach handles all of this internally, exposing a simple async iterator pattern.

---

## Detailed Findings

### 1. CLI-Based Claude Runner (`planning_pipeline/claude_runner.py`)

#### Entry Points

| Function | Line | Purpose |
|----------|------|---------|
| `run_claude_sync()` | 421 | SDK-native streaming (when SDK available) |
| `run_claude_subprocess()` | 460 | Pure CLI subprocess with PTY wrapper |
| `_run_claude_async()` | 273 | Internal async SDK implementation |

#### CLI Command Construction

**From `run_claude_subprocess()` (line 502-505):**
```python
claude_cmd = (
    f'claude --print --verbose --permission-mode bypassPermissions '
    f'--output-format stream-json -p {shlex.quote(prompt)}'
)
```

**PTY Wrapper (line 511):**
```python
cmd = ["script", "-q", "-c", claude_cmd, "/dev/null"]
```

The `script` command creates a pseudo-TTY, enabling real-time streaming output from the Claude CLI.

#### JSON Stream Event Processing

The CLI outputs JSON events that must be parsed line-by-line:

| Event Type | Handler Location | Data Extraction |
|------------|-----------------|-----------------|
| `content_block_delta` | line 570-577 | `delta.text` from `delta.type == "text_delta"` |
| `assistant` | line 578-585 | `message.content[].text` where `type == "text"` |
| `result` | line 586-587 | `result` string |

**Event Processing Logic (lines 566-593):**
```python
try:
    data = json.loads(line)
    msg_type = data.get("type")

    if msg_type == "content_block_delta":
        delta = data.get("delta", {})
        if delta.get("type") == "text_delta":
            text = delta.get("text", "")
            text_chunks.append(text)
    elif msg_type == "assistant":
        for content in data.get("message", {}).get("content", []):
            if content.get("type") == "text":
                text_chunks.append(content.get("text", ""))
    elif msg_type == "result":
        final_result = data.get("result", "")
except json.JSONDecodeError:
    text_chunks.append(line + "\n")
```

#### Buffer Management

**Line buffer for partial JSON (lines 522-555):**
```python
line_buffer = b""
while True:
    chunk = process.stdout.read1(4096)
    if chunk:
        line_buffer += chunk
        while b'\n' in line_buffer:
            line_bytes, line_buffer = line_buffer.split(b'\n', 1)
            line = line_bytes.decode('utf-8', errors='replace').strip()
            # Process complete line...
```

This handles:
- Partial JSON lines split across read chunks
- UTF-8 decoding with error replacement
- Line-by-line extraction for JSON parsing

#### OAuth Token Management

| Component | Location | Purpose |
|-----------|----------|---------|
| `read_credentials()` | line 69-81 | Read `~/.claude/.credentials.json` |
| `save_credentials()` | line 84-100 | Write with `.bak` backup |
| `refresh_oauth_token()` | line 103-153 | POST to OAuth endpoint |
| `ensure_oauth_token_fresh()` | line 169-189 | Proactive refresh if <5 min to expiry |
| `is_oauth_expired_error()` | line 156-166 | Detect 401/expired token errors |

**Refresh Flow (lines 637-649):**
```python
if is_oauth_expired_error(output) and _allow_retry:
    try:
        refresh_oauth_token()
        return run_claude_subprocess(prompt, timeout, stream_json, cwd, _allow_retry=False)
    except Exception as refresh_err:
        return {"success": False, "error": f"OAuth token expired and refresh failed: {refresh_err}"}
```

#### Terminal Output Formatting

**ANSI Colors Class (lines 193-202):**
```python
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
```

**Tool Call Formatting (lines 205-228):**
```python
def _format_tool_call(tool_name: str, tool_input: dict) -> str:
    display = f"{Colors.CYAN}{tool_name}{Colors.RESET}"

    # Extract key argument for display
    if tool_input.get("file_path"):
        key_arg = tool_input["file_path"]
    elif tool_input.get("command"):
        cmd = tool_input["command"]
        key_arg = cmd[:50] + "..." if len(cmd) > 50 else cmd
    # ... more patterns

    if key_arg:
        display += f"({Colors.GREEN}{key_arg}{Colors.RESET})"
    return display
```

**Stream-JSON Event Emission (lines 231-270):**
```python
def _emit_stream_json(event_type: str, data: dict[str, Any]) -> None:
    event = {"type": event_type, **data}
    sys.stdout.write(json.dumps(event) + "\n")
    sys.stdout.flush()
```

---

### 2. SDK-Based Approach (`test-conversation.py`)

#### Complete Implementation (~65 lines)

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock
import asyncio

class ConversationSession:
    def __init__(self, options: ClaudeAgentOptions = None):
        self.client = ClaudeSDKClient(options)
        self.turn_count = 0

    async def start(self):
        await self.client.connect()

        while True:
            user_input = input(f"\n[Turn {self.turn_count + 1}] You: ")

            if user_input.lower() == 'exit':
                break

            await self.client.query(user_input)
            self.turn_count += 1

            # Simple response processing
            async for message in self.client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(block.text, end="")
            print()

        await self.client.disconnect()

async def main():
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode="acceptEdits"
    )
    session = ConversationSession(options)
    await session.start()

asyncio.run(main())
```

#### SDK Handles Internally

| CLI Responsibility | SDK Solution |
|-------------------|--------------|
| PTY/script wrapper | Connection management |
| JSON event parsing | Typed message objects |
| Buffer management | AsyncIterator protocol |
| OAuth refresh | Automatic authentication |
| ANSI formatting | N/A (structured data) |
| Timeout handling | Built-in timeouts |

---

### 3. Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Complexity Comparison                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CLI Approach                          SDK Approach                         │
│  ─────────────                         ────────────                         │
│                                                                             │
│  ┌──────────────────┐                  ┌──────────────────┐                │
│  │ OAuth Management │ ~90 lines        │                  │                │
│  ├──────────────────┤                  │  client.connect  │  1 line        │
│  │ PTY/Script Wrap  │ ~20 lines        │                  │                │
│  ├──────────────────┤                  └──────────────────┘                │
│  │ JSON Parsing     │ ~100 lines                                           │
│  ├──────────────────┤                  ┌──────────────────┐                │
│  │ Buffer Mgmt      │ ~80 lines        │                  │                │
│  ├──────────────────┤                  │  client.query()  │  1 line        │
│  │ ANSI Formatting  │ ~60 lines        │                  │                │
│  ├──────────────────┤                  └──────────────────┘                │
│  │ Error Handling   │ ~50 lines                                            │
│  ├──────────────────┤                  ┌──────────────────┐                │
│  │ Streaming Logic  │ ~150 lines       │ async for msg in │                │
│  ├──────────────────┤                  │ receive_response │  ~10 lines     │
│  │ Result Assembly  │ ~50 lines        │     print(text)  │                │
│  └──────────────────┘                  └──────────────────┘                │
│                                                                             │
│  Total: ~670 lines                     Total: ~65 lines                    │
│  Complexity: O(n) parsing              Complexity: O(1) iteration          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Code References

### Python Implementation

| File | Lines | Description |
|------|-------|-------------|
| `planning_pipeline/claude_runner.py:421-457` | `run_claude_sync()` | Synchronous SDK wrapper |
| `planning_pipeline/claude_runner.py:460-671` | `run_claude_subprocess()` | CLI/PTY subprocess |
| `planning_pipeline/claude_runner.py:273-418` | `_run_claude_async()` | Internal SDK async |
| `planning_pipeline/claude_runner.py:64-189` | OAuth functions | Token management |
| `planning_pipeline/claude_runner.py:193-270` | Output formatting | ANSI colors, stream-json |
| `test-conversation.py:1-65` | SDK example | Complete conversation session |

### Go Implementation

| File | Lines | Description |
|------|-------|-------------|
| `go/internal/planning/claude_runner.go:204-427` | `RunClaudeSync()` | CLI with OAuth |
| `go/internal/planning/claude_runner.go:28-176` | OAuth management | Credentials, refresh |
| `go/internal/planning/claude_runner.go:274-365` | Stream processing | JSON parsing goroutine |
| `go/internal/exec/claude.go:84-120` | Basic runner | Simple CLI wrapper |

### Usage Sites

| Location | Import | Usage |
|----------|--------|-------|
| `planning_pipeline/steps.py:7` | `run_claude_sync` | 5 calls for pipeline steps |
| `planning_pipeline/decomposition.py:23` | `run_claude_sync` | Requirement extraction |
| `silmari_rlm_act/phases/implementation.py:19` | `run_claude_subprocess` | Real-time streaming |
| `silmari_rlm_act/phases/research.py:21` | `run_claude_sync` | Research phase |
| `planning_pipeline/autonomous_loop.py:45` | `invoke_claude` | Autonomous implementation |

---

## Architecture Documentation

### Current CLI Flow

```
User Prompt
     │
     ▼
┌─────────────────────────┐
│  run_claude_subprocess  │
│  ───────────────────────│
│  1. OAuth check/refresh │
│  2. Build CLI command   │
│  3. Wrap in 'script'    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  subprocess.Popen       │
│  ───────────────────────│
│  stdin  → PIPE          │
│  stdout → PIPE          │
│  stderr → STDOUT        │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Read Loop              │
│  ───────────────────────│
│  while True:            │
│    read1(4096)          │
│    accumulate buffer    │
│    split on \n          │
│    parse JSON           │
│    extract text         │
│    print to stdout      │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Result Assembly        │
│  ───────────────────────│
│  final_result or        │
│  join(text_chunks)      │
└─────────────────────────┘
```

### SDK Flow

```
User Prompt
     │
     ▼
┌─────────────────────────┐
│  client.query(prompt)   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  async for message in   │
│  client.receive_response│
│  ───────────────────────│
│  → AssistantMessage     │
│    → TextBlock          │
│      → print(text)      │
└─────────────────────────┘
```

---

## Historical Context (from thoughts/)

| Document | Content |
|----------|---------|
| `thoughts/shared/research/2026-01-04-terminal-streaming-output-flow.md` | Detailed streaming architecture analysis |
| `thoughts/shared/research/2026-01-06-implementation-phase-runner-gap.md` | Gap analysis of Claude runner injection |
| `thoughts/shared/plans/2026-01-10-tdd-feature/10-the-claude-runner-must-support-synchronous-executi.md` | REQ_009 specification |

---

## Related Research

- `thoughts/shared/research/2026-01-09-20-53-rlma-go-port-guide.md` - Go port covering Claude runner mapping
- `thoughts/shared/research/2026-01-01-loop-runner-integrated-orchestrator-analysis.md` - Architecture recommendations

---

## Open Questions

1. **SDK Multi-Turn Conversations**: The current SDK usage in `claude_runner.py` uses the `query()` function which is stateless. `test-conversation.py` demonstrates the `ClaudeSDKClient` approach with `connect()`/`query()`/`receive_response()`/`disconnect()` for multi-turn conversations - how should the pipeline adopt this pattern?

2. **OAuth with SDK**: Does the Agent SDK handle OAuth automatically, or does the existing OAuth refresh logic need to be retained when using SDK-native mode?

3. **Stream-JSON Compatibility**: The `run_claude_subprocess()` function supports `stream-json` output format for `repomirror visualize`. Does the SDK have equivalent structured event emission?


Answers to questions: 1. The `query()` function is stateless but the Claude code session is not, the CLI handles
state. The SDK uses the same method by hooking into the Claude code "sessions" variable. The SDK documentation is
here: https://platform.claude.com/docs/en/agent-sdk/python#when-to-use-claude-sdk-client-continuous-conversation. We
 will use the SDK client; 2. it is unclear from the documentation how the agent sdk handles auth, retain the current
 methods; 3. yes see: https://platform.claude.com/docs/en/agent-sdk/python#streaming-mode-with-client.;
ADDITIONAL CONTEXT: think deeply about how to use hooks see:
https://platform.claude.com/docs/en/agent-sdk/python#using-hooks-for-behavior-modification
ADDITIONAL CONTEXT: think about how to use the tool I/O to update the user on activity as well as pass questions to
the user during the research and planning phases, see:
https://platform.claude.com/docs/en/agent-sdk/python#tool-input-output-types