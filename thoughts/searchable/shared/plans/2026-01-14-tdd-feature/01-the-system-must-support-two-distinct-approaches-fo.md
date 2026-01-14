# Phase 01: The system must support two distinct approaches fo...

## Requirements

### REQ_000: The system must support two distinct approaches for invoking

The system must support two distinct approaches for invoking Claude Code: CLI/Subprocess approach (~670 lines) and Agent SDK approach (~65 lines)

#### REQ_000.1: Implement CLI-based claude_runner.py with subprocess managem

Implement CLI-based claude_runner.py with subprocess management including PTY wrapping, JSON stream parsing, OAuth token management, buffer management, and ANSI terminal output formatting

##### Testable Behaviors

1. CLI command is constructed with required flags: --print --verbose --permission-mode bypassPermissions --output-format stream-json -p {prompt}
2. Process is wrapped with 'script -q -c {cmd} /dev/null' to create pseudo-TTY for real-time streaming
3. JSON stream events are parsed line-by-line handling content_block_delta, assistant, and result event types
4. content_block_delta events extract text from delta.text when delta.type == 'text_delta'
5. assistant events extract text from message.content[].text where type == 'text'
6. result events extract the final result string
7. Buffer management handles partial JSON lines split across read chunks using 4096-byte reads
8. UTF-8 decoding with error replacement is implemented for robust character handling
9. OAuth credentials are read from ~/.claude/.credentials.json
10. OAuth tokens are proactively refreshed when less than 5 minutes to expiry
11. OAuth token refresh POSTs to the OAuth endpoint and saves credentials with .bak backup
12. 401/expired token errors trigger automatic OAuth refresh with single retry
13. ANSI color formatting is applied for terminal output using standard escape codes
14. Tool call formatting displays tool name in cyan with key argument in green
15. Stream-JSON events are emitted via sys.stdout.write(json.dumps(event) + '\n') with flush
16. Timeout handling supports up to 600000ms (10 minutes) with configurable default of 120000ms
17. Output truncation occurs when exceeding 30000 characters
18. Exit codes and error states are properly captured and returned

#### REQ_000.2: Implement SDK-based conversation session using ClaudeSDKClie

Implement SDK-based conversation session using ClaudeSDKClient with connect/query/receive_response/disconnect lifecycle, hooks for behavior modification, and tool I/O for user activity updates and question handling during research and planning phases

##### Testable Behaviors

1. ClaudeSDKClient is initialized with ClaudeAgentOptions configuration
2. Async context manager pattern is used: 'async with ClaudeSDKClient(options) as client'
3. client.connect() is called to establish session before first query
4. client.query(prompt) sends prompts while maintaining conversation context across turns
5. client.receive_response() returns AsyncIterator[Message] for streaming response processing
6. AssistantMessage content blocks are iterated to extract TextBlock.text for display
7. ToolUseBlock events are captured to show tool activity to user (e.g., 'Using: Read(file.py)')
8. ToolResultBlock events indicate tool completion status
9. ResultMessage signals conversation turn completion with session_id, duration_ms, total_cost_usd
10. client.interrupt() can stop Claude mid-execution for long-running tasks
11. client.disconnect() properly closes the session
12. PreToolUse hooks are registered to log/modify/block tool executions before they run
13. PostToolUse hooks are registered to log tool results after execution
14. UserPromptSubmit hooks can modify prompts (e.g., add timestamps, inject context)
15. HookMatcher.matcher field filters hooks to specific tools (e.g., 'Bash', 'Write|Edit')
16. HookMatcher.timeout field sets per-hook timeout (default 60s, configurable)
17. Hook callbacks return hookSpecificOutput with permissionDecision 'deny' to block tools
18. AskUserQuestion tool is used to pass questions to user during research/planning phases
19. Questions include header (max 12 chars), question text, and 2-4 options with labels and descriptions
20. multiSelect option allows multiple answers for non-mutually exclusive choices
21. User answers are collected in answers dict mapping question text to answer string
22. include_partial_messages=True enables real-time streaming events for progress updates
23. Permission mode is configurable: 'default', 'acceptEdits', 'plan', 'bypassPermissions'

#### REQ_000.3: Provide configuration options for selecting between CLI and 

Provide configuration options for selecting between CLI and SDK approaches with automatic fallback, feature detection, and unified interface abstraction

##### Testable Behaviors

1. Configuration option 'invocation_mode' accepts values: 'cli', 'sdk', 'auto' (default: 'auto')
2. Auto mode detects SDK availability via import check for claude_agent_sdk
3. Auto mode falls back to CLI if SDK import fails or CLINotFoundError is raised
4. CLI mode is forced when stream-json output format is required (e.g., repomirror visualize)
5. SDK mode is preferred when hooks are configured (hooks only supported in ClaudeSDKClient)
6. SDK mode is preferred when custom tools are configured (custom tools only in ClaudeSDKClient)
7. SDK mode is preferred when interrupt capability is needed
8. SDK mode is preferred for multi-turn conversations requiring context persistence
9. CLI mode retained when explicit OAuth token management is required (SDK auth unclear)
10. Unified invoke_claude() function abstracts both approaches with common interface
11. Return type is consistent: dict with success, output, error, duration_ms, session_id fields
12. Configuration can be set via environment variable CLAUDE_INVOCATION_MODE
13. Configuration can be set via settings.json at project or user level
14. Programmatic options override environment and settings file configuration
15. Feature compatibility matrix is documented for CLI vs SDK capabilities
16. Decision logging indicates which mode was selected and why in verbose mode


## Success Criteria

- [x] All tests pass (54 tests in test_claude_runner.py)
- [x] All REQ_000.1 behaviors implemented (CLI subprocess management)
- [x] All REQ_000.3 behaviors implemented (unified invoke_claude() interface)
- [ ] REQ_000.2 SDK behaviors (hooks, interrupt, multi-turn) - future enhancement
- [x] Code reviewed

## Implementation Notes

### Implemented (2026-01-14)

**REQ_000.1 (CLI-based claude_runner.py)**: All 18 testable behaviors implemented in `planning_pipeline/claude_runner.py`:
- `run_claude_subprocess()` - CLI subprocess with PTY wrapping
- JSON stream parsing for content_block_delta, assistant, result events
- Buffer management with 4096-byte reads
- OAuth token management with proactive refresh
- ANSI color formatting via `Colors` class
- Output truncation at 30000 characters

**REQ_000.3 (Configuration options)**: All 16 testable behaviors implemented:
- `invoke_claude()` - unified interface abstracting CLI and SDK
- `_get_invocation_mode()` - reads CLAUDE_INVOCATION_MODE env var
- `_select_invocation_mode()` - feature-based mode selection
- `_truncate_output()` - output truncation utility
- `ClaudeResult` TypedDict with all required fields
- Verbose decision logging when mode is selected

**Tests**: 54 comprehensive tests in `planning_pipeline/tests/test_claude_runner.py`:
- TestCLICommandConstruction (2 tests)
- TestJSONStreamParsing (3 tests)
- TestBufferManagement (2 tests)
- TestOAuthManagement (5 tests)
- TestTerminalFormatting (7 tests)
- TestTimeoutHandling (3 tests)
- TestExitCodeCapture (2 tests)
- TestInvocationModeConfiguration (3 tests)
- TestAutoModeDetection (3 tests)
- TestFeatureBasedModeSelection (5 tests)
- TestUnifiedInterface (4 tests)
- TestEnvironmentConfiguration (3 tests)
- TestConfigurationPrecedence (1 test)
- TestDecisionLogging (3 tests)
- Integration tests (4 slow tests)
- Error handling tests (2 tests)

### Deferred to Future Phases

**REQ_000.2 (SDK-based conversation session)**: SDK features not fully implemented:
- Hooks (PreToolUse, PostToolUse, UserPromptSubmit) - requires SDK hook API
- client.interrupt() capability
- Multi-turn conversation context
- AskUserQuestion tool handling

These features are SDK-specific and depend on the claude_agent_sdk package API.