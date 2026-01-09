---
date: 2026-01-06T04:51:18-05:00
researcher: Claude
git_commit: 88cd087930933241926c63be76ef330208163a1e
branch: main
repository: silmari-Context-Engine
topic: "Pipeline Gap: TDD Plans Not Being Implemented"
tags: [research, codebase, implementation-phase, autonomous-loop, pipeline, tdd]
status: complete
last_updated: 2026-01-06
last_updated_by: Claude
---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│           RESEARCH: TDD Implementation Phase Runner Gap                      │
│                                                                             │
│  Status: COMPLETE                        Date: 2026-01-06                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Research: Pipeline Gap - TDD Plans Never Implemented

**Date**: 2026-01-06T04:51:18-05:00
**Researcher**: Claude
**Git Commit**: 88cd087930933241926c63be76ef330208163a1e
**Branch**: main
**Repository**: silmari-Context-Engine

## Research Question

After TDD plans are created, the pipeline moves to validation but plans are never actually implemented. The TDD files need to be sent to an LLM to implement the code. Where is the gap?

---

## Summary

**ROOT CAUSE IDENTIFIED**: The `ImplementationPhase` class has `self._runner = None` and no runner is ever injected, causing all implementation attempts to immediately return `{"success": False, "error": "No runner configured"}`.

| Component | Status | Issue |
|-----------|--------|-------|
| `autonomous_loop.py` | **WORKING** | Calls `invoke_claude()` directly |
| `ImplementationPhase` | **BROKEN** | `self._runner` is always `None` |
| `RLMActPipeline` | **GAP** | Never injects runner into ImplementationPhase |

---

## Detailed Findings

### Working Pattern: `autonomous_loop.py`

The autonomous loop correctly invokes Claude to implement plans:

**File**: `planning_pipeline/autonomous_loop.py:769-792`

```python
async def _execute_phase(self) -> bool:
    """Execute the current phase."""
    try:
        # Build prompt
        prompt = self._build_phase_prompt()
    except ...

    # Invoke Claude <-- THIS IS THE KEY LINE
    logger.info(f"Executing phase: {self.current_phase}")
    claude_result = invoke_claude(prompt, timeout=3600)  # 1 hour timeout

    # Check result
    return check_execution_result(claude_result, project_path=self._project_path)
```

**Key Components**:
- Uses `invoke_claude()` from `planning_pipeline/phase_execution/claude_invoker.py`
- Passes prompt directly to Claude CLI subprocess
- Checks results with `check_execution_result()`

### Broken Pattern: `ImplementationPhase`

**File**: `silmari_rlm_act/phases/implementation.py:71,155-181`

```python
def __init__(self, project_path: Path, cwa: CWAIntegration) -> None:
    ...
    self._runner: Optional[ClaudeRunnerProtocol] = None  # <-- NEVER SET!

def _execute_tdd_cycle(self, behavior: str, phase_context: str) -> dict[str, Any]:
    if self._runner is None:
        return {"success": False, "error": "No runner configured"}  # <-- ALWAYS FAILS

    prompt = self._build_implementation_prompt(behavior, phase_context)

    try:
        result = self._runner.run_sync(prompt, timeout=self.IMPLEMENTATION_TIMEOUT)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### The Gap in `RLMActPipeline`

**File**: `silmari_rlm_act/pipeline.py:122`

```python
# In RLMActPipeline.__init__():
self._implementation_phase = ImplementationPhase(self.project_path, self.cwa)
# ^-- No runner injected!
```

### Claude Invoker (Available but Unused)

**File**: `planning_pipeline/phase_execution/claude_invoker.py:8-68`

```python
def invoke_claude(prompt: str, timeout: int = 1300) -> dict[str, Any]:
    """Invoke Claude Code via subprocess."""
    cmd = [
        "claude",
        "--print",
        "--permission-mode", "bypassPermissions",
        "-p", prompt
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    return {
        "success": result.returncode == 0,
        "output": result.stdout,
        "error": result.stderr,
        "elapsed": elapsed
    }
```

---

## Architecture Documentation

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RLMActPipeline.run()                              │
│                                                                             │
│  1. RESEARCH         →  Research question → Research document               │
│  2. DECOMPOSITION    →  Research doc → RequirementHierarchy                 │
│  3. TDD_PLANNING     →  Hierarchy → TDD plan files                          │
│  4. MULTI_DOC        →  TDD plan → Phase documents                          │
│  5. BEADS_SYNC       →  Phase docs → Beads issues created                   │
│  6. IMPLEMENTATION   →  Phase docs → ??? (BROKEN - no runner)               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Two Implementation Paths Exist

| Path | Entry Point | Runner | Status |
|------|------------|--------|--------|
| Autonomous Loop | `LoopRunner.run()` | Uses `invoke_claude()` directly | WORKING |
| RLM-Act Pipeline | `RLMActPipeline.run()` | `ImplementationPhase._runner = None` | BROKEN |

---

## Code References

| File | Lines | Description |
|------|-------|-------------|
| `planning_pipeline/autonomous_loop.py` | 789 | Working `invoke_claude()` call |
| `planning_pipeline/phase_execution/claude_invoker.py` | 8-68 | Claude subprocess invoker |
| `silmari_rlm_act/phases/implementation.py` | 71 | `self._runner = None` |
| `silmari_rlm_act/phases/implementation.py` | 169-170 | Early return when no runner |
| `silmari_rlm_act/pipeline.py` | 122 | No runner injection |

---

## What autonomous_loop.py Does Right

The `LoopRunner` class in `autonomous_loop.py` shows the correct pattern:

1. **Discovers plan phases** via `discover_plan_phases()`
2. **Builds prompt** via `build_phase_prompt()`
3. **Invokes Claude directly** via `invoke_claude()` (not through a protocol)
4. **Checks results** via `check_execution_result()`
5. **Advances to next phase** via `_advance_to_next_plan_phase()`

**Key difference**: `autonomous_loop.py` doesn't rely on an injected runner - it imports and uses `invoke_claude` directly.

---

## Related Commands

The slash commands show the expected workflow:

```
/create_tdd_plan     →  Creates TDD plan files
/implement_plan      →  Manually implements (user runs this)
/validate_plan       →  Validates implementation was done
```

The `implement_plan.md` command is designed for manual execution by Claude, not for automated pipeline execution.

---

## Open Questions

1. **Design Intent**: Was `ClaudeRunnerProtocol` intended for dependency injection for testing, but the real runner was never implemented?

2. **Path Forward**: Should `ImplementationPhase` call `invoke_claude()` directly (like autonomous_loop.py), or should the runner injection pattern be completed?

3. **Integration**: Should `RLMActPipeline` use `LoopRunner` internally for implementation, rather than having a separate `ImplementationPhase`?

---

## Comparison Table

| Feature | `autonomous_loop.py` | `ImplementationPhase` |
|---------|---------------------|----------------------|
| Claude invocation | `invoke_claude()` direct call | `self._runner.run_sync()` |
| Runner setup | N/A - direct import | `self._runner = None` |
| Prompt building | `build_phase_prompt()` | `_build_implementation_prompt()` |
| Result checking | `check_execution_result()` | Manual success check |
| Plan discovery | `discover_plan_phases()` | Uses passed `phase_paths` |
| Phase iteration | `_advance_to_next_plan_phase()` | `_execute_with_mode()` loop |

---

## Historical Context

The codebase has two parallel systems:

1. **`planning_pipeline/`** - Older, working implementation
   - Uses `autonomous_loop.py` with `LoopRunner`
   - Has `invoke_claude()` integrated

2. **`silmari_rlm_act/`** - Newer TDD-focused pipeline
   - More structured phase separation
   - Protocol-based dependency injection
   - **Missing**: Actual runner implementation

The `silmari_rlm_act` pipeline appears to have been designed with testability in mind (using protocols), but the production runner was never wired in.
