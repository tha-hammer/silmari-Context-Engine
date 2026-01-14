# Phase 02: The CLI approach must implement PTY wrapping via t...

## Requirements

### REQ_001: The CLI approach must implement PTY wrapping via the 'script

The CLI approach must implement PTY wrapping via the 'script' command for real-time streaming output from Claude CLI

#### REQ_001.1: Wrap Claude CLI command with script -q -c command /dev/null 

Wrap Claude CLI command with script -q -c command /dev/null to enable real-time streaming output through pseudo-TTY emulation

##### Testable Behaviors

1. Claude CLI command is constructed with --print --verbose --permission-mode bypassPermissions --output-format stream-json -p flags
2. Command string is properly escaped using shlex.quote() to handle special characters in prompts
3. The script command is invoked with -q flag to suppress 'Script started/ended' messages
4. The script command uses -c flag to specify the claude command as the shell command to execute
5. Output transcript is discarded by directing to /dev/null as the final script argument
6. Full command array is ['script', '-q', '-c', claude_cmd, '/dev/null']
7. Command construction does not block or fail when prompt contains newlines, quotes, or shell metacharacters
8. Environment variables (especially CLAUDE_CODE_MAX_OUTPUT_TOKENS) are preserved through the script wrapper

#### REQ_001.2: Create pseudo-TTY environment for streaming output by levera

Create pseudo-TTY environment for streaming output by leveraging the Unix script command to allocate a PTY and capture unbuffered output

##### Testable Behaviors

1. The script command creates a PTY that makes Claude CLI believe it's running in an interactive terminal
2. Output from Claude is unbuffered and streams in real-time (not line-buffered or block-buffered)
3. The PTY correctly handles ANSI escape sequences and control characters from Claude CLI
4. No 'Script started' or 'Script done' messages appear in the captured output (verified by -q flag)
5. The PTY inherits the correct terminal settings (TERM environment variable) for proper formatting
6. Claude CLI's --output-format stream-json produces immediate JSON line emissions through the PTY
7. The script process terminates cleanly when the wrapped Claude CLI exits
8. PTY allocation failure is detected and reported with actionable error message

#### REQ_001.3: Handle stdin/stdout/stderr PIPE configuration in subprocess.

Handle stdin/stdout/stderr PIPE configuration in subprocess.Popen to enable bidirectional communication with the PTY-wrapped Claude process

##### Testable Behaviors

1. subprocess.Popen is configured with stdin=subprocess.PIPE for potential input passing
2. subprocess.Popen is configured with stdout=subprocess.PIPE to capture all output
3. stderr is redirected to stdout using stderr=subprocess.STDOUT to merge output streams
4. The cwd parameter is correctly passed to set the working directory for Claude execution
5. Popen does not set shell=True to avoid shell injection vulnerabilities
6. Process file descriptors are properly inherited and closed as needed
7. The process can be polled for completion using process.poll()
8. Process termination via process.kill() works correctly for timeout handling
9. FileNotFoundError is caught and returns descriptive error about missing script/claude commands

#### REQ_001.4: Implement read loop with read1(4096) buffer management for e

Implement read loop with read1(4096) buffer management for efficient streaming of JSON events from Claude CLI output

##### Testable Behaviors

1. Read loop uses process.stdout.read1(4096) for efficient chunk-based reading
2. Fallback to select() + read() when read1() is not available (older Python versions)
3. Line buffer (bytes) accumulates partial data until newline delimiter found
4. Complete lines are extracted using line_buffer.split(b'\n', 1) to preserve partial data
5. Lines are decoded from bytes to UTF-8 with errors='replace' for robustness
6. Empty lines and 'Script ' prefixed lines are filtered out before processing
7. Loop continues until process.poll() returns non-None (process exited)
8. Remaining buffer is drained after process exit to capture all output
9. Timeout is checked on each iteration and process is killed if exceeded
10. Small sleep (0.05s) prevents CPU spinning when no data available
11. JSON parsing errors do not break the loop - non-JSON lines are handled gracefully


## Success Criteria

- [x] All tests pass (62 tests in test_claude_runner.py)
- [x] All behaviors implemented in planning_pipeline/claude_runner.py
- [x] Code reviewed

## Implementation Notes

### Implemented (2026-01-14)

All REQ_001 behaviors were implemented as part of Phase 1 and are tested in `planning_pipeline/tests/test_claude_runner.py`.

**Test classes covering REQ_001:**
- `TestPTYWrapping` (3 tests) - REQ_001.1: script command wrapping
- `TestSubprocessConfiguration` (5 tests) - REQ_001.3: Popen configuration
- `TestReadLoop` (4 tests) - REQ_001.4: Buffer management
- `TestCLICommandConstruction` (2 tests) - Command structure
- `TestJSONStreamParsing` (3 tests) - JSON event parsing
- `TestBufferManagement` (2 tests) - Partial line handling

**Key implementation details:**
- `run_claude_subprocess()` in claude_runner.py:460-671
- PTY wrapping: `["script", "-q", "-c", claude_cmd, "/dev/null"]`
- Buffer management: `read1(4096)` with line accumulation
- UTF-8 decoding: `errors='replace'` for robustness
- Script noise filtering: Skips "Script " prefixed lines