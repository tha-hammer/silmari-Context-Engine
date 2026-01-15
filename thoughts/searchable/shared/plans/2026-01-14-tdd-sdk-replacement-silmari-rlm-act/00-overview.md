# SDK Replacement for silmari-rlm-act Pipeline - TDD Implementation Plan

## Overview

Replace CLI-based Claude invocation (`run_claude_sync`, `run_claude_subprocess`) with the Claude Agent SDK in the `silmari-rlm-act` pipeline. This migration enables:

- **Hook-based artifact tracking** instead of regex parsing
- **Session continuity** across pipeline phases
- **Programmatic permission control** per phase
- **10x code reduction** (670 lines CLI → ~65 lines SDK)

## Current State Analysis

### Existing Implementation

| Component | File | Method | Runner |
|-----------|------|--------|--------|
| ResearchPhase | `silmari_rlm_act/phases/research.py:81` | `_run_claude()` | `run_claude_sync()` |
| ImplementationPhase | `silmari_rlm_act/phases/implementation.py:128` | `_invoke_claude()` | `run_claude_subprocess()` |

### Key Discoveries

1. **Return format is standardized**: `{"success": bool, "output": str, "error": str, "elapsed": float}`
2. **Tests mock at phase boundary**: `patch.object(phase, "_run_claude", mock_runner)`
3. **Artifact tracking uses regex**: `RESEARCH_PATH_PATTERNS` at `research.py:46-49`
4. **Timeouts differ by phase**: Research 1200s, Implementation 3600s

### Files to Create

```
silmari_rlm_act/
├── phases/
│   ├── research_sdk.py          # NEW: SDK-based research phase
│   └── implementation_sdk.py    # NEW: SDK-based implementation phase
└── tests/
    ├── test_research_phase_sdk.py      # NEW: TDD tests
    └── test_implementation_phase_sdk.py # NEW: TDD tests
```

## Desired End State

### Observable Behaviors

1. ResearchPhaseSDK tracks artifacts via `PostToolUse` hook (no regex)
2. ResearchPhaseSDK captures `session_id` for planning phase
3. ImplementationPhaseSDK resumes session from research
4. Both phases use `can_use_tool` for permission control
5. Streaming output works identically to current implementation
6. PhaseResult format unchanged (backward compatible)

## What We're NOT Doing

- Modifying existing `research.py` or `implementation.py` (parallel implementation)
- Changing `PhaseResult` structure
- Modifying `RLMActPipeline` orchestrator (feature flag added later)
- Removing `run_claude_sync` or `run_claude_subprocess` (deprecation phase)

## Testing Strategy

- **Framework**: pytest with existing fixtures
- **Mocking**: Mock `ClaudeSDKClient` and SDK `query()` function
- **Test Types**:
  - Unit: Each behavior independently
  - Integration: Full `execute()` flow with mocked SDK
- **Coverage**: All 14 behaviors with edge cases

## Phase Documents

1. [01-sdk-client-initialization.md](./01-sdk-client-initialization.md) - Behaviors 1-2
2. [02-permission-callbacks.md](./02-permission-callbacks.md) - Behaviors 3-4, 9
3. [03-session-management.md](./03-session-management.md) - Behaviors 5, 8
4. [04-streaming-and-output.md](./04-streaming-and-output.md) - Behaviors 6, 10
5. [05-phase-result-construction.md](./05-phase-result-construction.md) - Behaviors 7, 11-14

## Success Criteria

### Automated Verification

```bash
# Run all SDK migration tests
pytest silmari_rlm_act/tests/test_research_phase_sdk.py -v
pytest silmari_rlm_act/tests/test_implementation_phase_sdk.py -v

# Type checking
mypy silmari_rlm_act/phases/research_sdk.py
mypy silmari_rlm_act/phases/implementation_sdk.py

# Full test suite still passes
pytest silmari_rlm_act/tests/ -v
```

### Manual Verification

- [ ] SDK phases produce identical PhaseResult structure
- [ ] Streaming output displays in real-time
- [ ] Session ID propagates between phases
- [ ] Artifacts tracked without regex parsing

## References

- Research: `thoughts/searchable/shared/research/2026-01-14-sdk-replacement-silmari-rlm-act-pipeline.md`
- CLI vs SDK comparison: `thoughts/searchable/shared/research/2026-01-14-claude-runner-cli-vs-sdk.md`
- Existing tests: `silmari_rlm_act/tests/test_research_phase.py`
- SDK example: `test-conversation.py`
