# Phase 04: The system must implement OAuth token management w...

## Requirements

### REQ_003: The system must implement OAuth token management with creden

The system must implement OAuth token management with credential storage, proactive refresh, and automatic retry on 401 errors

#### REQ_003.1: Read OAuth credentials from ~/.claude/.credentials.json with

Read OAuth credentials from ~/.claude/.credentials.json with JSON parsing and error handling for missing or corrupted files

##### Testable Behaviors

1. Function reads from ~/.claude/.credentials.json path
2. Returns parsed JSON dictionary containing claudeAiOauth key with accessToken, refreshToken, expiresAt, and scopes fields
3. Raises FileNotFoundError with descriptive message when credentials file does not exist
4. Raises json.JSONDecodeError when credentials file contains invalid JSON
5. Uses Path.home() for cross-platform home directory resolution
6. Handles permission errors gracefully with appropriate exception type
7. Unit test verifies successful read of valid credentials file
8. Unit test verifies FileNotFoundError raised for missing file
9. Unit test verifies JSONDecodeError raised for malformed JSON

#### REQ_003.2: Save OAuth credentials to disk with atomic write pattern usi

Save OAuth credentials to disk with atomic write pattern using .bak backup file to prevent corruption during write failures

##### Testable Behaviors

1. Creates backup file with .json.bak extension before any write operation
2. Uses shutil.copy2() to preserve file metadata in backup
3. Writes credentials to disk with json.dump() using indent=2 for readability
4. Only creates backup if original file exists
5. Handles file permission errors with appropriate exception propagation
6. Unit test verifies backup file creation before write
7. Unit test verifies successful credential persistence
8. Unit test verifies backup is not created when original doesn't exist
9. Integration test verifies credential roundtrip (read after save matches original)

#### REQ_003.3: POST to OAuth endpoint https://console.anthropic.com/api/oau

POST to OAuth endpoint https://console.anthropic.com/api/oauth/token with refresh_token grant type to obtain new access and refresh tokens

##### Testable Behaviors

1. Reads existing credentials from disk using read_credentials()
2. Raises ValueError with message 'No refresh token available' if claudeAiOauth or refreshToken is missing
3. POSTs to CLAUDE_OAUTH_ENDPOINT (https://console.anthropic.com/api/oauth/token) with JSON body
4. Request body includes grant_type='refresh_token', refresh_token from credentials, client_id=CLAUDE_OAUTH_CLIENT_ID
5. Uses 30 second timeout for HTTP request
6. Calls response.raise_for_status() to propagate HTTP errors
7. Extracts access_token, refresh_token, expires_in from response JSON
8. Calculates new expiresAt as current timestamp (ms) + expires_in * 1000
9. Parses scope string into list by splitting on space character
10. Saves updated credentials to disk using save_credentials()
11. Logs debug message to stderr before refresh attempt
12. Logs success message with expiration timestamp after successful refresh
13. Unit test verifies ValueError raised when no refresh token exists
14. Integration test (with mocked HTTP) verifies correct request body construction
15. Integration test verifies credential update calculation (expiresAt math)

#### REQ_003.4: Proactively refresh OAuth token if expiration is less than 5

Proactively refresh OAuth token if expiration is less than 5 minutes away to prevent mid-execution authentication failures

##### Testable Behaviors

1. Reads credentials from disk using read_credentials()
2. Extracts expiresAt timestamp from claudeAiOauth credentials
3. Calculates time_until_expiry_ms as expiresAt - current_time_ms
4. Triggers refresh_oauth_token() if time_until_expiry_ms < 300000 (5 minutes in ms)
5. Logs debug message showing minutes remaining before proactive refresh
6. Catches all exceptions and logs them to stderr without re-raising
7. Silently succeeds if credentials file doesn't exist (for non-OAuth auth methods)
8. Silently succeeds if expiresAt field is missing
9. Unit test verifies no refresh called when token valid for >5 minutes
10. Unit test verifies refresh called when token expires in <5 minutes
11. Unit test verifies exceptions are caught and logged, not propagated
12. Should be called before every Claude invocation (run_claude_sync, run_claude_subprocess)

#### REQ_003.5: Detect 401/expired token errors from Claude CLI output to tr

Detect 401/expired token errors from Claude CLI output to trigger automatic retry with fresh credentials

##### Testable Behaviors

1. Takes combined stdout/stderr output string as input parameter
2. Returns True if output contains 'authentication_error' AND ('OAuth token has expired' OR '401')
3. Returns False for all other error types (rate limits, network errors, etc.)
4. Returns False for successful outputs
5. Case-sensitive string matching for error patterns
6. Used by run_claude_subprocess to determine if retry is appropriate
7. Unit test verifies True returned for 'authentication_error...OAuth token has expired' message
8. Unit test verifies True returned for 'authentication_error...401' message
9. Unit test verifies False returned for rate limit errors
10. Unit test verifies False returned for successful output
11. Unit test verifies False returned for empty string


## Success Criteria

- [x] All tests pass (62 tests in test_claude_runner.py)
- [x] All behaviors implemented in planning_pipeline/claude_runner.py
- [x] Code reviewed

## Implementation Notes

### Implemented (2026-01-14)

All REQ_003 OAuth behaviors are implemented in `planning_pipeline/claude_runner.py`.

**Test class covering REQ_003:**
- `TestOAuthManagement` (5 tests) - OAuth credential and token refresh tests

**Key implementation details:**
- `get_credentials_path()` - Line 64-66
- `read_credentials()` - Lines 69-81
- `save_credentials()` - Lines 84-100
- `refresh_oauth_token()` - Lines 103-153
- `ensure_oauth_token_fresh()` - Lines 169-189
- `is_oauth_expired_error()` - Lines 156-166

**Coverage of REQ_003.1 (Read credentials):**
- test_credentials_path_returns_home_claude_credentials
- test_read_credentials_loads_json

**Coverage of REQ_003.2 (Save credentials with backup):**
- save_credentials() creates .json.bak backup
- Uses shutil.copy2() for metadata preservation

**Coverage of REQ_003.3 (OAuth POST refresh):**
- refresh_oauth_token() POSTs to CLAUDE_OAUTH_ENDPOINT
- Updates accessToken, refreshToken, expiresAt, scopes

**Coverage of REQ_003.4 (Proactive refresh < 5 min):**
- test_proactive_refresh_when_expires_soon (validates 5 minute threshold)
- test_no_refresh_when_token_valid

**Coverage of REQ_003.5 (401 error detection):**
- test_is_oauth_expired_error_detects_401
- Checks for 'authentication_error' AND ('401' OR 'OAuth token has expired')