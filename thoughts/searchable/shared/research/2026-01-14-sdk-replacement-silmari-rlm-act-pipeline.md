---
date: 2026-01-14T20:26:12-05:00
researcher: claude
git_commit: 7824616e10448ddc7b4dd24b463f7434d5dce26c
branch: main
repository: silmari-Context-Engine
topic: "SDK Replacement Strategy for silmari-rlm-act Pipeline"
tags: [research, codebase, claude-runner, agent-sdk, pipeline, silmari-rlm-act, migration]
status: complete
last_updated: 2026-01-14
last_updated_by: claude
---

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│               SDK Replacement Strategy for silmari-rlm-act Pipeline             │
│                                                                                 │
│  Status: Complete                                     Date: 2026-01-14          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

# Research: SDK Replacement Strategy for silmari-rlm-act Pipeline

**Date**: 2026-01-14T20:26:12-05:00
**Researcher**: claude
**Git Commit**: 7824616e10448ddc7b4dd24b463f7434d5dce26c
**Branch**: main
**Repository**: silmari-Context-Engine

## Research Question

How to completely replace the CLI wrapper (`run_claude_subprocess`, `run_claude_sync`) with the Claude Agent SDK in the `silmari-rlm-act` pipeline, building on the comparison research in `2026-01-14-claude-runner-cli-vs-sdk.md`.

---

## Summary

The `silmari-rlm-act` pipeline currently uses CLI-based Claude invocation through two functions: `run_claude_sync()` and `run_claude_subprocess()`. Replacing these with the Claude Agent SDK requires:

| Current Function | Used By | SDK Replacement Pattern |
|-----------------|---------|------------------------|
| `run_claude_sync()` | ResearchPhase | `ClaudeSDKClient` with streaming + `PostToolUse` hooks |
| `run_claude_subprocess()` | ImplementationPhase | `ClaudeSDKClient` with session resumption + hooks |

**Key Benefits of SDK Migration**:
- **10x code reduction**: 670 lines CLI → ~65 lines SDK
- **Session continuity**: Multi-turn conversations with context preservation
- **Programmatic hooks**: Replace output parsing with structured callbacks
- **Permission control**: Automatic tool approval based on phase rules

---

## 📚 Detailed Findings

### 1. Pipeline Architecture (`silmari_rlm_act/`)

```
silmari_rlm_act/
├── cli.py                    # Entry point: main(), run(), resume(), status()
├── pipeline.py               # RLMActPipeline orchestrator
├── models.py                 # AutonomyMode, PhaseType, PhaseStatus, PhaseResult
├── phases/
│   ├── research.py           # ResearchPhase - uses run_claude_sync()
│   ├── decomposition.py      # DecompositionPhase - standalone
│   ├── tdd_planning.py       # TDDPlanningPhase - standalone
│   ├── multi_doc.py          # MultiDocPhase - standalone
│   ├── beads_sync.py         # BeadsSyncPhase - standalone
│   └── implementation.py     # ImplementationPhase - uses run_claude_subprocess()
├── checkpoints/
│   ├── manager.py            # CheckpointManager
│   └── interactive.py        # User prompts
├── context/
│   └── cwa_integration.py    # Context Window Aware integration
└── validation/
    ├── models.py             # SemanticValidationResult
    └── service.py            # SemanticValidationService
```

### 2. Current Claude Runner Usage Sites

#### ResearchPhase (`silmari_rlm_act/phases/research.py`)

**Current Implementation** (lines 81, 304-366):
```python
from planning_pipeline.claude_runner import run_claude_sync

class ResearchPhase:
    def _run_claude(self, prompt: str, timeout: int | None = None) -> dict:
        return run_claude_sync(
            prompt=prompt,
            timeout=timeout or self.timeout,  # Default: 1200s (20 min)
            stream=True,
            cwd=self.project_path
        )

    def execute(self, inputs: dict) -> PhaseResult:
        result = self._run_claude(prompt)
        if not result["success"]:
            return PhaseResult(status=PhaseStatus.FAILED, error=result.get("error"))

        # Parse output for research path and open questions
        research_path = self._extract_research_path(result["output"])
        open_questions = self._extract_open_questions(result["output"])

        return PhaseResult(
            status=PhaseStatus.COMPLETED,
            artifacts=[research_path],
            metadata={"open_questions": open_questions}
        )
```

**Response Processing**:
- Checks `result["success"]` boolean
- Extracts `result["output"]` text
- Regex patterns find research file path (lines 46-49)
- Regex patterns extract open questions (lines 52-55)
- Stores research in CWA (lines 158-174)

#### ImplementationPhase (`silmari_rlm_act/phases/implementation.py`)

**Current Implementation** (lines 128-133, 264-278):
```python
from planning_pipeline.claude_runner import run_claude_subprocess

class ImplementationPhase:
    CLAUDE_TIMEOUT = 3600  # 1 hour per iteration
    LOOP_SLEEP = 10        # 10s between iterations

    def _invoke_claude(self, prompt: str) -> dict:
        return run_claude_subprocess(
            prompt,
            timeout=self.CLAUDE_TIMEOUT,
            stream_json=False,  # Text mode for human-readable output
            cwd=str(self.project_path),
        )

    def execute(self, inputs: dict) -> PhaseResult:
        iteration = 0
        while iteration < max_iterations:
            result = self._invoke_claude(prompt)

            if not result["success"]:
                print(f"Claude invocation failed: {result.get('error')}")

            time.sleep(self.LOOP_SLEEP)

            if self._check_completion():  # All beads issues closed
                if self._run_tests():     # Tests pass
                    return PhaseResult(status=PhaseStatus.COMPLETED)

            iteration += 1
```

**Key Differences from Research Phase**:
- Uses `run_claude_subprocess()` instead of `run_claude_sync()`
- Longer timeout: 3600s (1 hour) vs 1200s (20 min)
- Loop-based execution with polling
- Real-time streaming to terminal (`stream_json=False`)
- Completion tracked via beads issue status

---

### 3. SDK Patterns Available in Codebase

#### Pattern 1: Stateful Client (`test-conversation.py`)

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock

class ConversationSession:
    def __init__(self, options: ClaudeAgentOptions = None):
        self.client = ClaudeSDKClient(options)

    async def start(self):
        await self.client.connect()

        while True:
            await self.client.query(user_input)

            async for message in self.client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(block.text, end="")

        await self.client.disconnect()
```

#### Pattern 2: Stateless Query (`claude_runner.py:458-608`)

```python
from claude_agent_sdk import query
from claude_agent_sdk.types import ClaudeAgentOptions, AssistantMessage, ResultMessage

async def _run_claude_async(prompt: str, timeout: int, stream: bool):
    options = ClaudeAgentOptions(
        allowed_tools=tools,
        permission_mode="bypassPermissions",
        cwd=project_path,
    )

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            # Handle text and tool calls
        elif isinstance(message, ResultMessage):
            return {"success": not message.is_error, "output": output}
```

---

### 4. SDK Features for Pipeline Migration

#### 4.1 Hooks for Behavior Modification

**Hook Types Available**:
| Hook | Trigger | Use Case |
|------|---------|----------|
| `PreToolUse` | Before tool execution | Block dangerous operations, modify inputs |
| `PostToolUse` | After tool execution | Track artifacts, validate outputs |
| `UserPromptSubmit` | Before prompt sent | Inject context, modify prompts |
| `Stop` | Agent stops | Cleanup resources |

**Permission Callback Pattern**:
```python
async def can_use_tool(tool_name: str, input_data: dict, context):
    # Auto-approve read-only during research
    if tool_name in ["Read", "Glob", "Grep"]:
        return PermissionResultAllow(updated_input=input_data)

    # Auto-approve writes during implementation
    if context.get("phase") == "implementation":
        return PermissionResultAllow(updated_input=input_data)

    # Deny system directory writes
    if tool_name == "Write" and input_data.get("file_path", "").startswith("/etc"):
        return PermissionResultDeny(message="System write blocked")

    return PermissionResultAllow(updated_input=input_data)
```

#### 4.2 Session Management

```python
# Capture session ID during research
session_id = None
async for message in query(prompt="Research codebase"):
    if hasattr(message, 'subtype') and message.subtype == 'init':
        session_id = message.data.get('session_id')

# Resume session in planning phase
async for message in query(
    prompt="Create implementation plan",
    options=ClaudeAgentOptions(resume=session_id)
):
    # Claude remembers all research context
```

#### 4.3 Streaming with Context

```python
async with ClaudeSDKClient() as client:
    # Research turn
    await client.query("Analyze codebase")
    async for message in client.receive_response():
        print(message)

    # Planning turn - remembers research context
    await client.query("Create plan based on findings")
    async for message in client.receive_response():
        print(message)

    # Implementation turn - full context
    await client.query("Implement the plan")
```

---

## 📊 Migration Strategy

### Phase-by-Phase Replacement

```
╔═════════════════════════════════════════════════════════════════════════════╗
║                          PHASE 1: Research Migration                         ║
║                              (Low Risk, High Value)                          ║
╚═════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│  Current: run_claude_sync()           │  New: ClaudeSDKClient + hooks       │
│  ───────────────────────────────────  │  ─────────────────────────────────  │
│  - 670 lines parsing logic            │  - 65 lines client code             │
│  - Regex extraction of paths          │  - PostToolUse hook tracks files    │
│  - Manual streaming to stdout         │  - Native streaming via iterator    │
│  - No session continuity              │  - Session ID for planning phase    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### ResearchPhase SDK Implementation

```python
# silmari_rlm_act/phases/research_sdk.py
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, HookMatcher
from claude_agent_sdk.types import (
    AssistantMessage, ResultMessage, TextBlock, ToolUseBlock,
    PermissionResultAllow
)

class ResearchPhaseSDK:
    """SDK-based research phase with artifact tracking."""

    def __init__(self, project_path: Path, timeout: int = 1200):
        self.project_path = project_path
        self.timeout = timeout
        self.artifacts: list[str] = []
        self.session_id: str | None = None

    async def _track_artifacts(self, input_data: dict, tool_use_id: str, context):
        """PostToolUse hook to track written files."""
        if input_data.get('tool_name') == 'Write':
            file_path = input_data.get('tool_input', {}).get('file_path', '')
            if 'research' in file_path.lower():
                self.artifacts.append(file_path)
        return {}

    async def _auto_approve_reads(self, tool_name: str, input_data: dict, context):
        """Auto-approve read-only operations during research."""
        if tool_name in ["Read", "Glob", "Grep", "Task"]:
            return PermissionResultAllow(updated_input=input_data)
        # Allow writes to thoughts/ directory
        if tool_name == "Write":
            path = input_data.get("file_path", "")
            if "thoughts/" in path or "research" in path.lower():
                return PermissionResultAllow(updated_input=input_data)
        return PermissionResultAllow(updated_input=input_data)

    async def execute(self, inputs: dict) -> PhaseResult:
        """Execute research phase using SDK."""
        prompt = self._build_prompt(inputs)

        async with ClaudeSDKClient(options=ClaudeAgentOptions(
            cwd=self.project_path,
            allowed_tools=["Read", "Write", "Grep", "Glob", "Task", "WebFetch"],
            can_use_tool=self._auto_approve_reads,
            hooks={
                'PostToolUse': [HookMatcher(hooks=[self._track_artifacts])]
            }
        )) as client:

            await client.query(prompt)
            output_chunks: list[str] = []

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            output_chunks.append(block.text)
                            print(block.text, end="", flush=True)
                        elif isinstance(block, ToolUseBlock):
                            print(f"\n⏺ {block.name}({block.input.get('file_path', '')})")

                elif isinstance(message, ResultMessage):
                    self.session_id = getattr(message, 'session_id', None)

                    if message.is_error:
                        return PhaseResult(
                            status=PhaseStatus.FAILED,
                            error=message.result or "SDK error"
                        )

            # Extract open questions from output
            output = "".join(output_chunks)
            open_questions = self._extract_open_questions(output)

            # Use tracked artifacts from hook
            research_path = self.artifacts[0] if self.artifacts else None

            return PhaseResult(
                status=PhaseStatus.COMPLETED,
                artifacts=self.artifacts,
                metadata={
                    "open_questions": open_questions,
                    "session_id": self.session_id  # For planning phase resumption
                }
            )
```

### ImplementationPhase SDK Implementation

```python
# silmari_rlm_act/phases/implementation_sdk.py
class ImplementationPhaseSDK:
    """SDK-based implementation with session continuity."""

    CLAUDE_TIMEOUT = 3600
    LOOP_SLEEP = 10

    async def execute(self, inputs: dict) -> PhaseResult:
        """Execute implementation with session persistence."""
        session_id = inputs.get("session_id")  # From research/planning
        max_iterations = inputs.get("max_iterations", 100)

        async with ClaudeSDKClient(options=ClaudeAgentOptions(
            cwd=self.project_path,
            allowed_tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Task"],
            can_use_tool=self._implementation_permissions,
            resume=session_id,  # Resume from planning context
        )) as client:

            for iteration in range(max_iterations):
                prompt = self._build_iteration_prompt(inputs, iteration)

                await client.query(prompt)

                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                print(block.text, end="", flush=True)

                await asyncio.sleep(self.LOOP_SLEEP)

                if await self._check_completion():
                    if await self._run_tests():
                        return PhaseResult(status=PhaseStatus.COMPLETED)

            return PhaseResult(
                status=PhaseStatus.FAILED,
                error=f"Max iterations ({max_iterations}) reached"
            )

    async def _implementation_permissions(self, tool_name: str, input_data: dict, context):
        """Auto-approve most operations during implementation."""
        # Only block system directory writes
        if tool_name in ["Write", "Edit"]:
            path = input_data.get("file_path", "")
            if path.startswith("/etc") or path.startswith("/sys"):
                return PermissionResultDeny(message="System directory blocked")

        return PermissionResultAllow(updated_input=input_data)
```

---

## 🎯 Migration Comparison

### Before: CLI-Based

```python
# Research Phase - 50+ lines of output parsing
result = run_claude_sync(prompt, timeout=1200, stream=True, cwd=project_path)
if not result["success"]:
    return PhaseResult(status=PhaseStatus.FAILED, error=result["error"])

# Regex extraction (error-prone)
research_path = None
for pattern in [r'Research saved to:\s*([^\s]+)', r'File:\s*([^\s]+\.md)']:
    match = re.search(pattern, result["output"])
    if match:
        research_path = match.group(1)
        break

# No session continuity - planning starts fresh
```

### After: SDK-Based

```python
# Research Phase - Hooks handle artifact tracking
async with ClaudeSDKClient(options=ClaudeAgentOptions(
    hooks={'PostToolUse': [HookMatcher(hooks=[track_artifacts])]}
)) as client:
    await client.query(prompt)
    async for message in client.receive_response():
        pass

# Artifacts tracked automatically by PostToolUse hook
research_path = self.artifacts[0]

# Session ID captured for planning phase
planning_session_id = self.session_id
```

---

## 📋 Implementation Checklist

### Phase 1: Research Migration (Week 1)

| Task | Status | Notes |
|------|--------|-------|
| Create `research_sdk.py` | 🔲 | New file alongside `research.py` |
| Implement `PostToolUse` artifact hook | 🔲 | Track Write to thoughts/ |
| Implement `can_use_tool` callback | 🔲 | Auto-approve reads |
| Capture session ID | 🔲 | Pass to planning phase |
| Add feature flag in `RLMActPipeline` | 🔲 | `use_sdk=True` toggle |
| Write tests for SDK research phase | 🔲 | Mirror existing tests |

### Phase 2: Implementation Migration (Week 2)

| Task | Status | Notes |
|------|--------|-------|
| Create `implementation_sdk.py` | 🔲 | New file |
| Implement session resumption | 🔲 | From research session |
| Implement permission callback | 🔲 | Block system writes |
| Add interrupt support | 🔲 | For graceful cancellation |
| Write tests for SDK implementation phase | 🔲 | Integration tests |

### Phase 3: Integration (Week 3)

| Task | Status | Notes |
|------|--------|-------|
| Update `RLMActPipeline` for SDK phases | 🔲 | Session ID propagation |
| Update checkpoint format | 🔲 | Include session IDs |
| Add CLI flag `--use-sdk` | 🔲 | Feature toggle |
| Deprecation warnings for CLI phases | 🔲 | Gradual migration |
| Documentation updates | 🔲 | SDK usage guide |

### Phase 4: Deprecation (Week 4+)

| Task | Status | Notes |
|------|--------|-------|
| Remove CLI phases as default | 🔲 | SDK becomes default |
| Migrate remaining CLI usages | 🔲 | decomposition, steps |
| Remove `run_claude_subprocess` | 🔲 | After full validation |
| Archive CLI code | 🔲 | Keep for reference |

---

## ⚠️ Risk Mitigation

### SDK Stability Concerns

The existing research notes "Hooks deferred until SDK APIs stabilize". Mitigation:

1. **Feature flag approach**: `use_sdk=True/False` toggle in pipeline
2. **Parallel implementation**: Keep CLI phases until SDK proven stable
3. **Fallback mechanism**: If SDK fails, fall back to CLI automatically

### Session ID Persistence

| Storage Location | Pros | Cons |
|-----------------|------|------|
| Checkpoint files | Simple, persistent | Must serialize/deserialize |
| Environment variable | Easy access | Lost on process restart |
| SQLite database | Queryable, persistent | Additional dependency |

**Recommendation**: Store in checkpoint JSON alongside existing state.

### Permission Callback Timeout

SDK `canUseTool` callback has 60-second timeout. For long-running user prompts:

```python
async def can_use_tool_with_timeout(tool_name, input_data, context):
    if tool_name == "AskUserQuestion":
        # Queue question for async handling
        question_queue.put((tool_name, input_data))
        # Return immediately to avoid timeout
        return PermissionResultAllow(updated_input=input_data)
    return PermissionResultAllow(updated_input=input_data)
```

---

## Code References

| File | Lines | Description |
|------|-------|-------------|
| `silmari_rlm_act/phases/research.py:81` | `_run_claude()` | Current CLI invocation |
| `silmari_rlm_act/phases/research.py:304-366` | `execute()` | Research execution flow |
| `silmari_rlm_act/phases/implementation.py:128-133` | `_invoke_claude()` | Current CLI invocation |
| `silmari_rlm_act/phases/implementation.py:264-278` | Implementation loop | Iteration logic |
| `planning_pipeline/claude_runner.py:458-608` | `_run_claude_async()` | SDK pattern reference |
| `test-conversation.py:4-47` | `ConversationSession` | ClaudeSDKClient example |

---

## Historical Context (from thoughts/)

| Document | Content |
|----------|---------|
| `thoughts/shared/research/2026-01-14-claude-runner-cli-vs-sdk.md` | CLI vs SDK comparison (670 lines vs 65 lines) |
| `thoughts/shared/research/2026-01-06-implementation-phase-runner-gap.md` | Gap analysis of runner injection |
| `thoughts/shared/plans/2026-01-14-tdd-feature-cli-resume/00-overview.md` | Current CLI implementation plan (88 tests passing) |
| `thoughts/shared/plans/2026-01-14-tdd-feature-cli-resume/05-the-sdk-based-approach-*.md` | SDK hooks requirements (deferred) |

---

## Related Research

- `thoughts/shared/research/2026-01-14-claude-runner-cli-vs-sdk.md` - Foundation comparison document
- `thoughts/shared/research/2026-01-04-terminal-streaming-output-flow.md` - Streaming architecture

---

## Open Questions

1. **OAuth with SDK**: Should we retain the current OAuth token management when using SDK, or does the SDK handle authentication automatically?

2. **Hook Stability**: When will the SDK hooks API be considered stable for production use? The current plan defers hook implementation.

3. **Session Storage**: What's the best location to persist session IDs between pipeline phases - checkpoint files, environment variables, or a dedicated database?

4. **Test Strategy**: Should SDK phases have separate test suites, or should existing tests be parameterized to run against both CLI and SDK implementations?
