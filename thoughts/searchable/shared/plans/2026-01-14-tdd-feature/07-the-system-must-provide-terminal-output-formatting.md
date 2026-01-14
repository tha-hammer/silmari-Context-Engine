# Phase 07: The system must provide terminal output formatting...

## Requirements

### REQ_006: The system must provide terminal output formatting with ANSI

The system must provide terminal output formatting with ANSI color codes and structured tool call display

#### REQ_006.1: Implement Colors class with ANSI escape code constants for t

Implement Colors class with ANSI escape code constants for terminal text formatting including RESET, BOLD, DIM, and standard colors (RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN)

##### Testable Behaviors

1. Colors class defines RESET constant as '\033[0m' for clearing all formatting
2. Colors class defines BOLD constant as '\033[1m' for bold text
3. Colors class defines DIM constant as '\033[2m' for dimmed/faded text
4. Colors class defines RED constant as '\033[31m' for red foreground
5. Colors class defines GREEN constant as '\033[32m' for green foreground
6. Colors class defines YELLOW constant as '\033[33m' for yellow foreground
7. Colors class defines BLUE constant as '\033[34m' for blue foreground
8. Colors class defines MAGENTA constant as '\033[35m' for magenta foreground
9. Colors class defines CYAN constant as '\033[36m' for cyan foreground
10. All color codes are class-level string constants accessible without instantiation
11. Colors can be concatenated with text strings (e.g., Colors.CYAN + 'text' + Colors.RESET)
12. Unit tests verify each color code outputs correct ANSI sequence
13. Colors gracefully degrade when terminal does not support ANSI (detect via environment)

#### REQ_006.2: Format tool call display with tool name in CYAN and key argu

Format tool call display with tool name in CYAN and key argument in GREEN, extracting the most relevant argument for each tool type

##### Testable Behaviors

1. Tool name is displayed wrapped in CYAN color codes
2. Key argument (when present) is displayed in parentheses wrapped in GREEN color codes
3. Format follows pattern: '{CYAN}tool_name{RESET}({GREEN}key_arg{RESET})'
4. When no key argument is extractable, display only '{CYAN}tool_name{RESET}' without parentheses
5. Function accepts tool_name (str) and tool_input (dict) as parameters
6. Output string is suitable for direct print() to terminal
7. Works correctly with SDK ToolUseBlock.name and ToolUseBlock.input properties
8. Integration test verifies correct ANSI sequence generation for sample tools

#### REQ_006.3: Extract the most relevant key argument from tool input based

Extract the most relevant key argument from tool input based on tool-specific patterns including file_path, command, pattern, query, and url fields

##### Testable Behaviors

1. For tools with 'file_path' input (Read, Write, Edit, NotebookEdit), extract and return file_path value
2. For Bash tool with 'command' input, extract command value
3. For Grep tool with 'pattern' input, extract pattern value
4. For Glob tool with 'pattern' input, extract pattern value
5. For WebFetch tool with 'url' input, extract url value
6. For WebSearch tool with 'query' input, extract query value
7. For Task tool, extract 'description' field as key argument
8. Return None when no recognized key field is present in tool_input
9. Function handles empty dict input returning None
10. Priority order for extraction: file_path > command > pattern > query > url > description
11. Unit tests cover all standard Claude Code tool types

#### REQ_006.4: Truncate long command arguments and other display strings to

Truncate long command arguments and other display strings to 50 characters with ellipsis suffix for terminal readability

##### Testable Behaviors

1. Arguments longer than 50 characters are truncated to 50 characters
2. Truncated arguments end with '...' ellipsis suffix
3. Total output length including ellipsis is 53 characters maximum (50 + '...')
4. Arguments 50 characters or shorter are returned unchanged
5. Empty string input returns empty string
6. None input returns None or empty string
7. Truncation happens at character boundary, not mid-word (optional enhancement)
8. Function is idempotent - truncating already truncated string produces same result
9. Works correctly with Unicode characters and multi-byte strings

#### REQ_006.5: Emit stream-json formatted events to stdout with type field 

Emit stream-json formatted events to stdout with type field and data payload for real-time tool activity display and structured event output

##### Testable Behaviors

1. Function accepts event_type (str) and data (dict) parameters
2. Output is a single JSON object per line (JSON-lines format)
3. Output JSON contains 'type' field set to event_type value
4. Output JSON contains all key-value pairs from data dict spread at top level
5. Each event is followed by newline character for streaming compatibility
6. stdout is flushed immediately after write for real-time display
7. JSON serialization handles common Python types (str, int, float, bool, list, dict)
8. Events match SDK streaming format: content_block_delta, assistant, result types
9. Function is synchronous and thread-safe for stdout writes
10. Integration with SDK hooks via PreToolUse/PostToolUse callbacks
11. Can be used in ClaudeAgentOptions.hooks for automatic event emission


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed