# Phase 10: The Claude Runner must support synchronous executi...

## Requirements

### REQ_009: The Claude Runner must support synchronous execution, file-b

The Claude Runner must support synchronous execution, file-based execution, and conversation mode

#### REQ_009.1: Implement synchronous Claude CLI execution with timeout supp

Implement synchronous Claude CLI execution with timeout support, stdin-based prompt delivery, and dual-mode output handling (streaming vs buffered)

##### Testable Behaviors

1. Function accepts prompt string, timeout in seconds, stream boolean flag, and working directory path
2. Creates context with configurable timeout using context.WithTimeout
3. Passes prompt via stdin pipe instead of -p flag to support large prompts
4. Uses --print flag for CLI output mode
5. Uses --output-format json flag when stream=false for structured output
6. Returns ClaudeResult struct with Success, Output, and Error fields
7. Handles context.DeadlineExceeded errors with descriptive timeout message
8. Captures both stdout and stderr in separate goroutines
9. Uses sync.WaitGroup to ensure all goroutines complete before returning
10. Sets working directory via cmd.Dir for project-scoped execution
11. Writes diagnostic debug logs to stderr for troubleshooting
12. Flushes stdout buffer after streaming completes using os.Stdout.Sync()

#### REQ_009.2: Implement file-based Claude execution that reads file conten

Implement file-based Claude execution that reads file content and combines it with a prompt for context-aware LLM calls

##### Testable Behaviors

1. Function accepts prompt string, file path, timeout seconds, stream flag, and working directory
2. Reads file content using os.ReadFile
3. Returns error result if file read fails with descriptive error message
4. Combines file content with prompt using structured format: 'File content from {path}:\n```\n{content}\n```\n\n{prompt}'
5. Delegates to RunClaudeSync with combined prompt
6. Preserves all RunClaudeSync parameters (timeout, stream, cwd)
7. Returns ClaudeResult with file read errors clearly distinguished from Claude execution errors

#### REQ_009.3: Implement multi-turn conversation support by formatting conv

Implement multi-turn conversation support by formatting conversation history into a structured prompt for Claude execution

##### Testable Behaviors

1. Define ConversationMessage struct with Role and Content string fields
2. Role field accepts 'user' or 'assistant' values
3. Function accepts slice of ConversationMessage, timeout, stream flag, and working directory
4. Formats messages with 'Human: ' prefix for user role
5. Formats messages with 'Assistant: ' prefix for assistant role
6. Separates messages with double newlines for clarity
7. Uses strings.Builder for efficient string concatenation
8. Delegates to RunClaudeSync with formatted conversation prompt
9. Returns ClaudeResult from RunClaudeSync execution

#### REQ_009.4: Implement real-time streaming output using goroutines for co

Implement real-time streaming output using goroutines for concurrent stdout/stderr processing with proper synchronization

##### Testable Behaviors

1. Stdout streaming goroutine reads line-by-line using bufio.Scanner
2. Each stdout line is immediately printed to console using fmt.Println for real-time display
3. Output is accumulated in strings.Builder for final ClaudeResult.Output
4. Stderr goroutine captures error output separately
5. sync.WaitGroup tracks goroutine completion with Add(1) before each and Done() at end
6. Main thread calls wg.Wait() after cmd.Wait() to ensure all output is captured
7. os.Stdout.Sync() called after wg.Wait() to flush output buffer
8. Debug logging shows line count progress every 10 lines for long-running operations
9. Goroutines handle scanner errors gracefully without panicking
10. Stdin write goroutine closes pipe after writing to signal EOF to Claude

#### REQ_009.5: Implement utility functions for Claude CLI availability chec

Implement utility functions for Claude CLI availability checking and version retrieval

##### Testable Behaviors

1. ClaudeAvailable() returns bool indicating if claude binary is in PATH
2. Uses exec.LookPath('claude') to check binary availability
3. Returns true if LookPath succeeds, false otherwise
4. GetClaudeVersion() returns version string and error
5. Executes 'claude --version' command
6. Captures and returns trimmed output string
7. Returns wrapped error if command fails
8. Both functions are safe to call without side effects


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed