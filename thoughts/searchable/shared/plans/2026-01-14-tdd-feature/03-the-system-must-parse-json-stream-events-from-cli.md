# Phase 03: The system must parse JSON stream events from CLI ...

## Requirements

### REQ_002: The system must parse JSON stream events from CLI output inc

The system must parse JSON stream events from CLI output including content_block_delta, assistant, and result event types

#### REQ_002.1: Parse content_block_delta events extracting delta.text from 

Parse content_block_delta events extracting delta.text from text_delta type for real-time streaming of assistant text content

##### Testable Behaviors

1. Parser correctly identifies events where type equals 'content_block_delta'
2. Parser extracts nested delta object from the event data structure
3. Parser validates delta.type equals 'text_delta' before extracting text
4. Parser extracts delta.text string and returns it for accumulation
5. Parser handles missing delta object gracefully by returning empty string
6. Parser handles missing delta.text field gracefully by returning empty string
7. Parser handles delta.type not equal to 'text_delta' by ignoring the event
8. Extracted text is immediately available for real-time display via sys.stdout.write()
9. Text chunks are accumulated into text_chunks list for final result assembly
10. When using SDK-native mode, equivalent logic uses TextBlock content type from AssistantMessage
11. Performance: Parser processes streaming chunks with O(1) per-event complexity

#### REQ_002.2: Parse assistant events extracting message.content[].text whe

Parse assistant events extracting message.content[].text where type is text for complete message content blocks

##### Testable Behaviors

1. Parser correctly identifies events where type equals 'assistant'
2. Parser extracts message object from event data structure
3. Parser extracts content array from message object
4. Parser iterates through each content block in the array
5. Parser filters content blocks where type equals 'text'
6. Parser extracts text field from filtered text content blocks
7. Parser handles missing message object gracefully
8. Parser handles missing content array gracefully with empty list default
9. Parser handles content blocks without type field gracefully
10. Parser handles content blocks without text field gracefully
11. Multiple text blocks in single message are concatenated in order
12. When using SDK-native mode, equivalent logic uses AssistantMessage and TextBlock types directly
13. Tool use blocks (type='tool_use') within same message are handled separately
14. Extracted text emitted via _emit_assistant_text() when output_format is stream-json

#### REQ_002.3: Parse result events extracting final result string indicatin

Parse result events extracting final result string indicating completion of Claude response

##### Testable Behaviors

1. Parser correctly identifies events where type equals 'result'
2. Parser extracts result field from event data as final response string
3. Parser handles missing result field gracefully with empty string default
4. Result event signals completion of the current response cycle
5. Parser extracts is_error field to determine success/failure status
6. When is_error is true, result contains error message
7. When is_error is false or missing, result contains successful response
8. Final result takes precedence over accumulated text_chunks for output
9. When using SDK-native mode, equivalent logic uses ResultMessage.result and ResultMessage.is_error
10. Result event emitted via _emit_result() when output_format is stream-json
11. Parser extracts session_id if present for session tracking
12. Parser extracts duration_ms if present for performance metrics

#### REQ_002.4: Handle JSON decode errors by appending raw line content as f

Handle JSON decode errors by appending raw line content as fallback for non-JSON output from CLI

##### Testable Behaviors

1. Parser catches json.JSONDecodeError exceptions during line parsing
2. When JSONDecodeError occurs, raw line content is preserved for output
3. Raw line appended to text_chunks with newline separator
4. Parser filters out 'Script ' prefix lines from 'script' command wrapper
5. Parser filters out empty lines from output
6. Parser filters out lines starting with '{' when not in stream_json mode (partial JSON)
7. Non-JSON lines displayed to user when stream_json is False
8. Non-JSON lines suppressed when stream_json is True to maintain clean pipe output
9. Original JSONDecodeError exception details logged for debugging if needed
10. Error handling does not interrupt main processing loop
11. Line content with decode errors still contributes to final text output assembly
12. UTF-8 decode errors in line_buffer handled with 'replace' error mode

#### REQ_002.5: Manage line buffer for partial JSON split across read chunks

Manage line buffer for partial JSON split across read chunks from subprocess stdout

##### Testable Behaviors

1. Buffer accumulates byte data from process.stdout.read1(4096) calls
2. Buffer splits on newline delimiter b'\n' to extract complete lines
3. Split operation returns complete line and remaining buffer separately
4. Complete lines are decoded from UTF-8 with 'replace' error handling
5. Decoded lines are stripped of whitespace before processing
6. Partial lines (without newline) remain in buffer for next iteration
7. Buffer handles multiple complete lines in single read chunk
8. Buffer handles JSON spanning multiple read chunks correctly
9. Buffer handles zero-length chunks (empty reads) without error
10. Buffer drains remaining content when process exits (process.poll() is not None)
11. Process exit triggers process.stdout.read() for remaining data
12. Remaining buffer processed line-by-line with same parsing logic
13. Buffer timeout integration with main processing loop timeout check
14. Small sleep (0.05s) prevents CPU busy loop when no data available


## Success Criteria

- [x] All tests pass (62 tests in test_claude_runner.py)
- [x] All behaviors implemented in planning_pipeline/claude_runner.py
- [x] Code reviewed

## Implementation Notes

### Implemented (2026-01-14)

All REQ_002 behaviors were implemented as part of Phase 1 and tested comprehensively.

**Test classes covering REQ_002:**
- `TestJSONStreamParsing` (3 tests) - content_block_delta, assistant, result parsing
- `TestBufferManagement` (2 tests) - Partial JSON handling
- `TestReadLoop` (4 tests) - Buffer management and error recovery

**Key implementation details:**
- JSON event parsing: claude_runner.py:566-627
- content_block_delta handling: Lines 570-577
- assistant event handling: Lines 578-585
- result event handling: Lines 586-587
- JSON decode error handling: Lines 588-593
- Line buffer management: Lines 549-553
- UTF-8 decode with replace: Line 554

**Coverage of REQ_002.1 (content_block_delta):**
- test_content_block_delta_text_extraction validates extraction
- Buffer tests cover partial JSON accumulation

**Coverage of REQ_002.2 (assistant events):**
- test_assistant_event_text_extraction validates parsing
- Content array iteration implemented

**Coverage of REQ_002.3 (result events):**
- test_result_event_extraction validates extraction
- Final result takes precedence over text_chunks

**Coverage of REQ_002.4 (JSON decode errors):**
- test_json_parse_errors_do_not_break_loop validates error recovery
- Non-JSON lines appended to output

**Coverage of REQ_002.5 (line buffer management):**
- test_buffer_handles_partial_json_lines validates split handling
- test_utf8_decoding_with_error_replacement validates decode errors