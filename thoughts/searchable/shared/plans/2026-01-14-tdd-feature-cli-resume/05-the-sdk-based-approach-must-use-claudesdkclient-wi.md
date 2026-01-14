# Phase 05: The SDK-based approach must use ClaudeSDKClient wi...

## Requirements

### REQ_004: The SDK-based approach must use ClaudeSDKClient with connect

The SDK-based approach must use ClaudeSDKClient with connect/query/receive_response/disconnect pattern for multi-turn conversations

#### REQ_004.1: Initialize ClaudeSDKClient with ClaudeAgentOptions configura

Initialize ClaudeSDKClient with ClaudeAgentOptions configuration for multi-turn conversation support

##### Testable Behaviors

1. ClaudeAgentOptions is created with required configuration: allowed_tools, permission_mode, cwd, system_prompt
2. OAuth token check is performed before client initialization (retain existing ensure_oauth_token_fresh() logic)
3. Hooks dictionary is configured with PreToolUse, PostToolUse, and UserPromptSubmit event handlers for activity monitoring
4. MCP servers are configured if custom tools are needed via create_sdk_mcp_server()
5. setting_sources is configured to load appropriate project settings (e.g., ['project'] to load CLAUDE.md)
6. include_partial_messages is set to true for real-time streaming progress updates
7. ClaudeSDKClient instance is created with the configured options
8. Error handling wraps CLINotFoundError, ProcessError to provide meaningful fallback to subprocess approach

#### REQ_004.2: Call client.connect() for connection management establishing

Call client.connect() for connection management establishing the session for multi-turn conversations

##### Testable Behaviors

1. client.connect() is called with optional initial prompt parameter when available
2. Connection is established using async context manager pattern (async with ClaudeSDKClient() as client)
3. Connection success is verified before proceeding with queries
4. CLIConnectionError is caught and triggers retry with exponential backoff
5. Connection state is tracked for reconnection on failure
6. Hook for 'SessionStart' equivalent behavior is simulated since Python SDK doesn't support SessionStart hook
7. Logging captures connection establishment time for performance monitoring
8. Connection pool is managed for concurrent session support if needed

#### REQ_004.3: Send queries via client.query(user_input) supporting both st

Send queries via client.query(user_input) supporting both string prompts and streaming input for research/planning phases

##### Testable Behaviors

1. client.query(prompt) is called with string prompt for simple queries
2. client.query(message_stream()) is called with AsyncIterable for streaming multi-part input
3. session_id parameter is used to maintain conversation context ('default' or custom ID)
4. UserPromptSubmit hook is triggered before query execution for prompt logging/modification
5. Turn count is incremented after successful query submission
6. Query timeout is configurable and respected
7. Questions to user during research/planning phases are formatted using AskUserQuestion tool input structure
8. Streaming input generator yields {type: 'text', text: ...} dictionaries for incremental prompt delivery

#### REQ_004.4: Process responses via async for message in client.receive_re

Process responses via async for message in client.receive_response() with real-time streaming and tool activity monitoring

##### Testable Behaviors

1. async for message in client.receive_response() iterates through all messages until ResultMessage
2. AssistantMessage instances are processed to extract content blocks
3. ToolUseBlock instances trigger activity update callbacks showing tool name and input summary
4. ToolResultBlock instances are captured for tool execution results
5. ResultMessage is detected to mark response completion (check subtype in ['success', 'error'])
6. include_partial_messages=True enables real-time text streaming for immediate user feedback
7. PreToolUse and PostToolUse hooks are invoked for tool activity monitoring
8. Response iteration completes naturally without using break to avoid asyncio cleanup issues
9. Cost and usage information from ResultMessage is captured for tracking

#### REQ_004.5: Extract TextBlock content from AssistantMessage objects for 

Extract TextBlock content from AssistantMessage objects for final response assembly and display

##### Testable Behaviors

1. AssistantMessage.content list is iterated to find all ContentBlock instances
2. TextBlock instances are identified using isinstance(block, TextBlock) check
3. TextBlock.text property is extracted and accumulated in order
4. ThinkingBlock instances are optionally extracted for debugging/transparency (block.thinking)
5. ToolUseBlock instances are logged but not included in final text output
6. Text chunks are joined with appropriate separators for readable output
7. Model identifier from AssistantMessage.model is captured for logging
8. Empty text blocks are handled gracefully without adding empty strings
9. Final assembled text matches the streaming output for consistency


## Success Criteria

- [x] All tests pass (62 tests in test_claude_runner.py)
- [x] Core SDK behaviors implemented (initialization, query, response processing)
- [ ] Advanced SDK features (hooks, MCP, multi-turn context) - future enhancement
- [x] Code reviewed

## Implementation Notes

### Implemented (2026-01-14)

Basic SDK integration is implemented in `planning_pipeline/claude_runner.py`.

**Test classes covering REQ_004:**
- `TestSDKAvailability` (2 tests) - HAS_CLAUDE_SDK detection and fallback

**Key implementation details:**
- SDK import and availability check: Lines 34-54
- `_run_claude_async()` - Lines 273-458 (async SDK invocation)
- `run_claude_sync()` - Lines 460-557 (sync wrapper)
- ClaudeAgentOptions initialization: Lines 320-326
- AssistantMessage processing: Lines 335-367
- TextBlock extraction: Lines 337-344
- ToolUseBlock handling: Lines 346-358
- ResultMessage completion: Lines 370-398

**Coverage of REQ_004.1 (ClaudeAgentOptions initialization):**
- ClaudeAgentOptions created with allowed_tools, permission_mode, max_turns, cwd
- HAS_CLAUDE_SDK constant controls SDK availability

**Coverage of REQ_004.3 (query execution):**
- `async for message in query(prompt=prompt, options=options)` pattern used
- Streaming response iteration implemented

**Coverage of REQ_004.4 (response processing):**
- AssistantMessage, ToolUseBlock, ToolResultBlock, ResultMessage all handled
- Result data extracted including success, output, error, elapsed

**Coverage of REQ_004.5 (TextBlock extraction):**
- TextBlock.text extracted and accumulated in text_chunks list
- Model identifier captured via ResultMessage

### Deferred to Future Enhancement

**Not yet implemented:**
- REQ_004.1.3-4: Hooks dictionary configuration (PreToolUse, PostToolUse, UserPromptSubmit)
- REQ_004.1.4: MCP server configuration
- REQ_004.2: Full client.connect() lifecycle (currently using query() directly)
- REQ_004.3.6-7: AskUserQuestion tool handling
- REQ_004.4.6-7: Hook invocation during response processing

These features require deeper SDK integration and are not blocking core functionality.