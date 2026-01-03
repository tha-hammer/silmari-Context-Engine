---
date: 2026-01-02T19:37:56-05:00
researcher: claude
git_commit: ff5064e55e936a91617896a4fa68e67f7222126c
branch: main
repository: silmari-Context-Engine
topic: "Why Loop Runner Orchestrator Plans Are Complete But Loop Doesn't Execute"
tags: [research, autonomous-loop, orchestrator, execution-gap]
status: complete
last_updated: 2026-01-02
last_updated_by: claude
---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LOOP RUNNER ORCHESTRATOR RESEARCH                        │
│                     Plans Complete, Execution Missing                        │
│                              2026-01-02                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Research: Why Loop Runner Orchestrator Plans Are Complete But Loop Doesn't Execute

**Date**: 2026-01-02T19:37:56-05:00
**Researcher**: claude
**Git Commit**: ff5064e55e936a91617896a4fa68e67f7222126c
**Branch**: main
**Repository**: silmari-Context-Engine

## Research Question

The plans at `thoughts/shared/plans/2026-01-01-tdd-loop-runner-orchestrator-*.md` are marked as complete, but the autonomous coding loop does not actually execute. Why?

## 📊 Summary

| Finding | Status |
|---------|--------|
| Plans correctly marked complete | ✅ |
| All 30 tests pass | ✅ |
| Orchestration infrastructure implemented | ✅ |
| **Actual Claude invocation implemented** | ❌ **MISSING** |

The plans describe building **orchestration infrastructure**, not the actual execution. The `_execute_phase` method is a **placeholder stub** that doesn't invoke Claude Code.

## 🎯 Root Cause

The `_execute_phase` method in `autonomous_loop.py:146-155` is a stub:

```python
async def _execute_phase(self) -> bool:
    """Execute the current phase.

    Returns:
        True if phase completed successfully, False otherwise.
    """
    # Placeholder for actual phase execution
    # In real implementation, this would invoke Claude Code
    logger.info(f"Executing phase: {self.current_phase}")
    return True  # <-- Always returns True, does nothing
```

The comment explicitly states: **"In real implementation, this would invoke Claude Code"**

## 📚 Detailed Findings

### What The Plans Describe

The 7-phase TDD plan implemented the **orchestration framework**:

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Accept orchestrator parameter | ✅ Complete |
| 2 | Auto-discover plans from orchestrator | ✅ Complete |
| 3 | Backward compatibility with plan_path | ✅ Complete |
| 4 | Query orchestrator for next feature | ✅ Complete |
| 5 | Update feature status in orchestrator | ✅ Complete |
| 6 | Resume from orchestrator state | ✅ Complete |
| 7 | Integration tests | ✅ Complete |

All tests pass (30/30) because they **mock `_execute_phase`**:

```python
with patch.object(runner, "_execute_phase", new_callable=AsyncMock) as mock_exec:
    mock_exec.return_value = True
    await runner.run()
```

### What's Actually Missing

The **bridge between the orchestrator and Claude Code invocation** was never implemented. The infrastructure can:
- Discover plans from `thoughts/*/plans/`
- Track feature status via beads
- Progress through phases
- Resume from interrupted state

But it cannot:
- Read plan content and generate prompts
- Invoke Claude Code subprocess
- Parse Claude's output for success/failure
- Handle timeouts or errors

### Three Separate Execution Systems Exist

```
┌─────────────────────────────────────────────────────────────────┐
│                   EXECUTION SYSTEMS COMPARISON                   │
├───────────────────┬──────────────────┬──────────────────────────┤
│ System            │ Invokes Claude?  │ Status                   │
├───────────────────┼──────────────────┼──────────────────────────┤
│ autonomous_loop.py│ NO (stub)        │ Infrastructure only      │
│ loop-runner.py    │ YES              │ Uses feature_list.json   │
│ loop.sh           │ YES              │ Reads PROMPT.md directly │
└───────────────────┴──────────────────┴──────────────────────────┘
```

#### 1. `autonomous_loop.py` + `IntegratedOrchestrator` (New System)
- **File**: `planning_pipeline/autonomous_loop.py:1-235`
- Uses async/await pattern
- Integrates with beads for state management
- Discovers plans from `thoughts/*/plans/`
- **Does NOT invoke Claude** - `_execute_phase` is a stub

#### 2. `loop-runner.py` (Legacy System)
- **File**: `loop-runner.py:1-1382`
- Uses `feature_list.json` for feature tracking
- **Actually invokes Claude** via subprocess:
  ```python
  cmd = ["claude", "--model", model, "--permission-mode", "bypassPermissions", "-p", prompt]
  result = subprocess.run(cmd, cwd=str(project_path), timeout=3600)
  ```
- Has complexity detection, QA modes, metrics tracking
- Does NOT integrate with beads or plan files

#### 3. `loop.sh` (Simple Shell Loop)
- **File**: `loop.sh:1-10`
- Reads `PROMPT.md` and passes to Claude
- Visualizes with `repomirror`
- Loops with 10-second sleep

### How `claude_runner.py` Works

The codebase HAS a Claude invocation wrapper at `planning_pipeline/claude_runner.py:1-353`:

```python
def run_claude_sync(prompt: str, ...) -> dict[str, Any]:
    cmd = ["claude", "--print", "--verbose", "--permission-mode", "bypassPermissions",
           "--output-format", "stream-json", "-p", prompt]
    # ... subprocess execution with streaming
```

This is used by `IntegratedOrchestrator.get_project_info()` but NOT by `LoopRunner._execute_phase()`.

## 🗂️ Code References

| File | Lines | Description |
|------|-------|-------------|
| `planning_pipeline/autonomous_loop.py` | 146-155 | Stub `_execute_phase` method |
| `planning_pipeline/autonomous_loop.py` | 199-210 | `run()` method that calls the stub |
| `planning_pipeline/integrated_orchestrator.py` | 229-259 | `discover_plans()` implementation |
| `planning_pipeline/claude_runner.py` | 23-81 | Working `run_claude_sync()` function |
| `loop-runner.py` | 959-1084 | Working `run_session()` with Claude invocation |

## Architecture Documentation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CURRENT ARCHITECTURE GAP                             │
│                                                                             │
│  ┌─────────────────┐    ┌────────────────────┐    ┌─────────────────────┐  │
│  │                 │    │                    │    │                     │  │
│  │  IntegratedOr-  │───▶│   LoopRunner       │    │   Claude Code       │  │
│  │  chestrator     │    │   (async)          │    │   (subprocess)      │  │
│  │                 │    │                    │    │                     │  │
│  │  - discover_    │    │  - run()           │    │   NOT CONNECTED     │  │
│  │    plans()      │    │  - _execute_phase  │    │                     │  │
│  │  - get_next_    │    │    ↑               │    │                     │  │
│  │    feature()    │    │    │               │    │                     │  │
│  │  - bd (beads)   │    │    │               │    │                     │  │
│  │                 │    │    └── STUB ───────│────│─ should call ──▶    │  │
│  │                 │    │        returns True│    │   run_claude_sync() │  │
│  └─────────────────┘    └────────────────────┘    └─────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Historical Context (from thoughts/)

| Document | Relevance |
|----------|-----------|
| `thoughts/shared/research/2026-01-01-loop-runner-integrated-orchestrator-analysis.md` | Original research for the TDD plan |
| `thoughts/shared/plans/2026-01-01-tdd-loop-runner-orchestrator-00-overview.md` | The plan that was implemented |

The plans focused on the **orchestration layer** without specifying how `_execute_phase` would work.

## Open Questions

1. **Was `_execute_phase` implementation intentionally deferred?**
   - The TDD plan focuses on orchestration infrastructure
   - No phase covers implementing the actual Claude invocation

2. **Should `loop-runner.py` be deprecated or merged?**
   - It has working Claude invocation but uses different state management
   - The new system has better architecture but no execution

3. **What should `_execute_phase` do?**
   - Read the plan file content
   - Generate a prompt based on current phase
   - Call `run_claude_sync()` from `claude_runner.py`
   - Parse result and return True/False

## Recommendation Matrix

| Gap | Priority | Effort | Next Step |
|-----|----------|--------|-----------|
| Implement `_execute_phase` | 🔴 Critical | Medium | Create plan for Phase 8 |
| Port `loop-runner.py` features | 🟡 Important | High | Analyze which features to keep |
| Unify execution systems | 🟢 Nice-to-have | High | After core execution works |

---

## Appendix: Test Verification

All 30 tests pass as of 2026-01-02:

```
tests/test_autonomous_loop.py: 24 passed
tests/test_loop_orchestrator_integration.py: 6 passed
```

Tests pass because they mock `_execute_phase` - they test the orchestration infrastructure, not actual execution.
