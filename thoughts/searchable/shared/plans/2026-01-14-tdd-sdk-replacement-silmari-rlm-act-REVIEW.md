# Plan Review Report: SDK Replacement for silmari-rlm-act Pipeline

**Review Date**: 2026-01-14
**Plan Location**: `thoughts/searchable/shared/plans/2026-01-14-tdd-sdk-replacement-silmari-rlm-act/`
**Reviewer**: Claude

---

## Review Summary

| Category | Status | Issues Found |
|----------|--------|--------------|
| Contracts | ⚠️ Warning | 4 issues |
| Interfaces | ✅ Well-Defined | 1 minor issue |
| Promises | ⚠️ Warning | 3 issues |
| Data Models | ✅ Well-Defined | 0 issues |
| APIs | ⚠️ Warning | 2 issues |

**Overall Status**: ⚠️ **Needs Minor Revision** - Address warnings before proceeding

---

## Contract Review

### Well-Defined

- ✅ **PhaseResult contract preserved** - Plan explicitly states PhaseResult format unchanged and backward compatible (00-overview.md:49)
- ✅ **SDK return format standardized** - Plan documents that both phases will use `{"success": bool, "output": str, "session_id": str}` format
- ✅ **Permission callback return types** - Plan correctly specifies `PermissionResultAllow` and `PermissionResultDeny` return types (02-permission-callbacks.md)
- ✅ **Hook callback signatures** - PostToolUse hook signature matches SDK documentation: `(input_data, tool_use_id, context) -> dict`

### Missing or Unclear

- ⚠️ **Issue 1: SDK import contract not fully specified** - The plan references `claude_agent_sdk` imports but doesn't specify which import pattern to use. Codebase has two patterns:
  - Stateless: `from claude_agent_sdk import query` (used in `claude_runner.py`)
  - Stateful: `from claude_agent_sdk import ClaudeSDKClient` (used in `test-conversation.py`)

  **Impact**: Implementation may use wrong pattern, causing API mismatch.

- ⚠️ **Issue 2: HookMatcher registration not fully documented** - The plan shows hooks in ClaudeAgentOptions but actual SDK may use different registration pattern. Research shows `HookMatcher(hooks=[...], matcher="...")` pattern.

  **Impact**: Hook registration may fail at runtime.

- ⚠️ **Issue 3: Error contract for `_execute_sdk()` undefined** - Plan doesn't specify what exceptions `_execute_sdk()` can throw or how to handle SDK-specific errors.

  **Impact**: Unhandled exceptions may crash the pipeline.

- ⚠️ **Issue 4: Timeout handling contract missing** - Plan mentions `DEFAULT_TIMEOUT = 1200` but doesn't specify how SDK timeout is configured. The existing CLI uses subprocess timeout, SDK may use different mechanism.

  **Impact**: Long-running research may timeout incorrectly.

### Recommendations

1. **Specify import pattern explicitly** in Phase 01:
   ```python
   # Use stateful client pattern for research (multi-turn potential)
   from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, HookMatcher
   from claude_agent_sdk.types import (
       AssistantMessage, ResultMessage, TextBlock, ToolUseBlock,
       PermissionResultAllow, PermissionResultDeny
   )
   ```

2. **Document exception handling** for `_execute_sdk()`:
   ```python
   # Exceptions that can be raised:
   # - RuntimeError: SDK connection failed
   # - TimeoutError: Query exceeded timeout
   # - ValueError: Invalid options configuration
   # All caught and converted to PhaseResult(status=FAILED, errors=[str(e)])
   ```

3. **Add timeout configuration** to ClaudeAgentOptions:
   ```python
   options = ClaudeAgentOptions(
       cwd=self.project_path,
       # SDK doesn't have direct timeout - handle via asyncio.wait_for()
   )
   ```

---

## Interface Review

### Well-Defined

- ✅ **`ResearchPhaseSDK` matches existing interface** - Constructor takes `(project_path: Path, cwa: CWAIntegration)`
- ✅ **`execute()` method signature compatible** - Returns `PhaseResult`, accepts `research_question: str`
- ✅ **`ImplementationPhaseSDK` matches existing interface** - Same constructor pattern
- ✅ **Private method naming convention followed** - `_run_claude()` → `_execute_sdk()`, `_invoke_claude()` → `_invoke_claude_sdk()`
- ✅ **Permission callback interface correct** - `_auto_approve_reads(tool_name, input_data, context)`

### Missing or Unclear

- ⚠️ **Issue 1: `execute()` signature differs between phases** - Research phase uses positional args, Implementation uses keyword args. Plan shows different signatures:

  **Research** (01-sdk-client-initialization.md):
  ```python
  def execute(self, research_question: str, additional_context: str = "", timeout: Optional[int] = None) -> PhaseResult
  ```

  **Implementation** (03-session-management.md):
  ```python
  def execute(self, phase_paths: list[str], mode: AutonomyMode, ..., session_id: Optional[str] = None) -> PhaseResult
  ```

  **Impact**: Minor, but inconsistent with the stated goal of maintaining interface compatibility.

### Recommendations

1. **Verify execute() signatures match existing phases exactly**:
   ```python
   # ResearchPhase.execute() current signature (research.py:283):
   def execute(self, research_question: str, additional_context: str = "", timeout: Optional[int] = None) -> PhaseResult

   # ImplementationPhase.execute() current signature (implementation.py:203):
   def execute(self, phase_paths: list[str], mode: AutonomyMode, beads_issue_ids: Optional[list[str]] = None,
               beads_epic_id: Optional[str] = None, max_iterations: int = 100,
               checkpoint: Optional[dict[str, Any]] = None) -> PhaseResult
   ```

---

## Promise Review

### Well-Defined

- ✅ **Session continuity promise** - Plan clearly states session_id captured in ResearchPhaseSDK and passed to ImplementationPhaseSDK (03-session-management.md)
- ✅ **Artifact tracking guarantee** - PostToolUse hook will track Write operations to research paths
- ✅ **Streaming output promise** - Real-time streaming via `async for message in client.receive_response()`
- ✅ **Loop continuation on error** - ImplementationPhaseSDK continues loop on SDK failures (04-streaming-and-output.md:225-256)

### Missing or Unclear

- ⚠️ **Issue 1: Permission callback timeout not documented** - SDK permission callbacks have 60-second timeout (per research doc). Plan doesn't address this constraint.

  **Impact**: Complex permission logic may timeout, causing unexpected tool denials.

- ⚠️ **Issue 2: Async context manager cleanup not specified** - Plan uses `async with ClaudeSDKClient()` but doesn't document cleanup behavior on exceptions.

  **Impact**: Resource leaks possible if SDK connection not properly closed.

- ⚠️ **Issue 3: Session ID persistence across restarts undefined** - Plan mentions storing session_id in metadata, but doesn't specify checkpoint integration.

  **Impact**: Session continuity lost if pipeline restarts between phases.

### Recommendations

1. **Add permission callback timeout note** in Phase 02:
   ```python
   async def _auto_approve_reads(self, tool_name, input_data, context):
       # CRITICAL: This callback has 60-second timeout
       # Must return quickly - no user prompts or long operations
       ...
   ```

2. **Document context manager cleanup**:
   ```python
   async with ClaudeSDKClient(options=options) as client:
       try:
           await client.query(prompt)
           ...
       except Exception as e:
           # Context manager ensures disconnect() called
           raise
   ```

3. **Add session_id to checkpoint format** in Phase 03:
   ```python
   # Checkpoint schema addition:
   {
       "phase_results": {
           "research": {
               "metadata": {
                   "session_id": "session-abc-123"  # Persist for resumption
               }
           }
       }
   }
   ```

---

## Data Model Review

### Well-Defined

- ✅ **PhaseResult structure unchanged** - All 8 fields preserved (phase_type, status, artifacts, errors, started_at, completed_at, duration_seconds, metadata)
- ✅ **New metadata keys documented** - `session_id` added to ResearchPhaseSDK metadata
- ✅ **Serialization compatible** - Uses existing `to_dict()`/`from_dict()` methods
- ✅ **Enum usage correct** - PhaseType.RESEARCH, PhaseStatus.COMPLETE used correctly

### No Issues Found

The data model section is well-defined with no gaps.

---

## API Review

### Well-Defined

- ✅ **SDK API usage correct** - `ClaudeSDKClient` async context manager pattern matches SDK documentation
- ✅ **Hook registration pattern correct** - Uses `hooks={'PostToolUse': [HookMatcher(...)]}` format
- ✅ **Permission callback pattern correct** - Returns `PermissionResultAllow`/`PermissionResultDeny`

### Missing or Unclear

- ⚠️ **Issue 1: SDK `query()` stateless function vs `ClaudeSDKClient` class** - Plan uses `ClaudeSDKClient` class but existing `claude_runner.py` uses stateless `query()` function. These have different APIs:

  **Stateless (`query()`)**: Returns async iterator directly
  ```python
  async for message in query(prompt=prompt, options=options):
      ...
  ```

  **Stateful (`ClaudeSDKClient`)**: Requires separate query() and receive_response()
  ```python
  await client.query(prompt)
  async for message in client.receive_response():
      ...
  ```

  **Impact**: Using wrong pattern will cause AttributeError at runtime.

- ⚠️ **Issue 2: ResultMessage.session_id extraction not verified** - Plan assumes `message.session_id` attribute exists on ResultMessage, but codebase uses `getattr(message, 'session_id', None)` pattern suggesting it may be optional.

  **Impact**: AttributeError if session_id not present.

### Recommendations

1. **Choose one SDK pattern and document why**:
   ```python
   # Using ClaudeSDKClient (stateful) because:
   # 1. Multi-turn conversations within single phase
   # 2. Session ID capture for cross-phase continuity
   # 3. Clean async context manager cleanup
   ```

2. **Use safe attribute access for session_id** (already in plan but verify):
   ```python
   # Safe extraction pattern (already shown in 03-session-management.md:127):
   self.session_id = getattr(message, "session_id", None)
   ```

---

## Critical Issues (Must Address Before Implementation)

### 1. **SDK Import Pattern Ambiguity** (Contract)
- **Impact**: Wrong imports cause ImportError or AttributeError at runtime
- **Recommendation**: Add explicit import block to Phase 01 showing exact imports needed

### 2. **Permission Callback Timeout** (Promise)
- **Impact**: Complex permission logic may timeout, denying tools unexpectedly
- **Recommendation**: Add comment/warning about 60-second constraint in Phase 02

### 3. **Session ID Checkpoint Persistence** (Promise)
- **Impact**: Session continuity lost on pipeline restart
- **Recommendation**: Document how session_id flows through checkpoint system

---

## Suggested Plan Amendments

```diff
# In Phase 01: SDK Client Initialization

+ ## SDK Import Pattern
+
+ Use the stateful `ClaudeSDKClient` class (not the stateless `query()` function):
+
+ ```python
+ from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, HookMatcher
+ from claude_agent_sdk.types import (
+     AssistantMessage,
+     ResultMessage,
+     TextBlock,
+     ToolUseBlock,
+     PermissionResultAllow,
+     PermissionResultDeny,
+ )
+ ```
+
+ **Rationale**: ClaudeSDKClient enables session management via `resume` option,
+ which is required for cross-phase context continuity.

# In Phase 02: Permission Callbacks

+ ## Timeout Constraint
+
+ **CRITICAL**: SDK permission callbacks (`can_use_tool`) have a 60-second timeout.
+ The callback must return quickly - do not:
+ - Prompt for user input
+ - Make external API calls
+ - Perform expensive computations
+
+ If the callback times out, the tool use is denied by default.

# In Phase 03: Session Management

+ ## Checkpoint Integration
+
+ Session IDs must persist across pipeline restarts. When checkpointing:
+
+ 1. **Save**: Store `session_id` in PhaseResult.metadata during `to_dict()`
+ 2. **Load**: Extract `session_id` from restored PhaseResult during resume
+ 3. **Pass**: Include `session_id` in execute() call to ImplementationPhaseSDK
+
+ ```python
+ # In RLMActPipeline.resume_from_checkpoint():
+ research_result = state.get_phase_result(PhaseType.RESEARCH)
+ session_id = research_result.metadata.get("session_id") if research_result else None
+ implementation_phase.execute(..., session_id=session_id)
+ ```

# In Phase 05: PhaseResult Construction

+ ## Exception Handling
+
+ All SDK exceptions must be caught and converted to PhaseResult failures:
+
+ ```python
+ try:
+     result = await self._execute_sdk(prompt)
+ except Exception as e:
+     return PhaseResult(
+         phase_type=PhaseType.RESEARCH,
+         status=PhaseStatus.FAILED,
+         errors=[f"SDK error: {type(e).__name__}: {str(e)}"],
+         started_at=started_at,
+         completed_at=datetime.now(),
+     )
+ ```
```

---

## Review Checklist Summary

### Contracts
- [x] Component boundaries are clearly defined
- [x] Input/output contracts are specified
- [ ] **Error contracts enumerate all failure modes** ⚠️
- [x] Preconditions and postconditions are documented
- [x] Invariants are identified

### Interfaces
- [x] All public methods are defined with signatures
- [x] Naming follows codebase conventions
- [x] Interface matches existing patterns
- [x] Extension points are considered
- [x] Visibility modifiers are appropriate

### Promises
- [x] Behavioral guarantees are documented
- [ ] **Async operations have timeout/cancellation handling** ⚠️
- [x] Resource cleanup is specified (via async context manager)
- [x] Idempotency requirements are addressed
- [x] Ordering guarantees are documented where needed

### Data Models
- [x] All fields have types
- [x] Required vs optional is clear
- [x] Relationships are documented
- [x] Migration strategy is defined (backward compatible)
- [x] Serialization format is specified

### APIs
- [x] All endpoints are defined
- [x] Request/response formats are specified
- [x] Error responses are documented
- [ ] **Authentication requirements are clear** (N/A - SDK handles auth)
- [x] Versioning strategy is defined (parallel implementation)

---

## Approval Status

- [ ] **Ready for Implementation** - No critical issues
- [x] **Needs Minor Revision** - Address warnings before proceeding
- [ ] **Needs Major Revision** - Critical issues must be resolved first

**Next Steps**:
1. Add explicit SDK import pattern to Phase 01
2. Document permission callback timeout constraint in Phase 02
3. Add checkpoint integration for session_id in Phase 03
4. Document exception handling in Phase 05
5. Then proceed with implementation
