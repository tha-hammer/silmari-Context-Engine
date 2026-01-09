---
date: 2026-01-04T19:06:03-05:00
researcher: claude-opus-4-5
git_commit: de6c3943998016a246dca145bad7c797845f0088
branch: main
repository: silmari-Context-Engine
topic: "Terminal Streaming Output Flow Analysis"
tags: [research, codebase, streaming, output, claude-runner, autonomous-loop, pipeline]
status: complete
last_updated: 2026-01-04
last_updated_by: claude-opus-4-5
---

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TERMINAL STREAMING OUTPUT FLOW                       │
│                           Research Document                             │
│                                                                         │
│  Status: Complete                              Date: 2026-01-04         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Date**: 2026-01-04T19:06:03-05:00
**Researcher**: claude-opus-4-5
**Git Commit**: de6c3943998016a246dca145bad7c797845f0088
**Branch**: main
**Repository**: silmari-Context-Engine

---

## Research Question

The migration from `claude_code_sdk` to `claude_agent_sdk` in commit d196c58 broke terminal streaming output. Fixes were implemented in `planning_pipeline/claude_runner.py` but the terminal still shows no output. Where does output flow and why isn't the user seeing it?

---

## Summary

The codebase has **two completely separate execution paths** for invoking Claude:

| Path | Entry Point | Claude Invocation | Output Behavior |
|------|-------------|-------------------|-----------------|
| **Pipeline Path** | `planning_orchestrator.py` | `claude_runner.py` | **WAS BROKEN** - SDK doesn't stream tokens |
| **Loop Path** | `loop-runner.py` | `claude_invoker.py` | **Captured/Hidden** |

> **UPDATE 2026-01-04**: The pipeline path was ALSO broken. The `claude_agent_sdk.query()` yields complete messages, not streaming tokens. Fix applied: switched to `run_claude_subprocess()` with `stream_json=False` for real-time line-by-line streaming.

The streaming fix was applied to `claude_runner.py`, but `autonomous_loop.py` uses `claude_invoker.py` instead - a completely different module that uses `subprocess.run(capture_output=True)`, which buffers all output until completion.

---

## Detailed Findings

### 📊 Architecture Overview

```
                           ┌─────────────────────────────────────┐
                           │           CLI ENTRY POINTS          │
                           └──────────────┬──────────────────────┘
                                          │
              ┌───────────────────────────┴───────────────────────────┐
              │                                                       │
              ▼                                                       ▼
┌─────────────────────────────────┐             ┌──────────────────────────────┐
│   planning_orchestrator.py      │             │     loop-runner.py           │
│   (Interactive Pipeline)        │             │   (Autonomous Loop)          │
└──────────────┬──────────────────┘             └──────────────┬───────────────┘
               │                                                │
               ▼                                                ▼
┌─────────────────────────────────┐             ┌──────────────────────────────┐
│   planning_pipeline/pipeline.py │             │ planning_pipeline/           │
│   PlanningPipeline.run()        │             │ autonomous_loop.py           │
└──────────────┬──────────────────┘             │ LoopRunner.run()             │
               │                                └──────────────┬───────────────┘
               ▼                                                │
┌─────────────────────────────────┐                             │
│   planning_pipeline/steps.py    │                             │
│   step_research(), step_plan()  │                             ▼
└──────────────┬──────────────────┘             ┌──────────────────────────────┐
               │                                │ planning_pipeline/           │
               ▼                                │ phase_execution/             │
┌─────────────────────────────────┐             │ claude_invoker.py            │
│   planning_pipeline/            │             │ invoke_claude()              │
│   claude_runner.py              │             └──────────────┬───────────────┘
│   run_claude_sync()             │                            │
└──────────────┬──────────────────┘                            │
               │                                               │
               ▼                                               ▼
    ┌──────────────────────┐               ┌────────────────────────────────┐
    │  sys.stdout.write()  │               │  subprocess.run(               │
    │  sys.stdout.flush()  │               │    capture_output=True         │
    │                      │               │  )                             │
    │  ✅ STREAMS TO       │               │                                │
    │     TERMINAL         │               │  ❌ OUTPUT CAPTURED/HIDDEN     │
    └──────────────────────┘               └────────────────────────────────┘
```

---

### 🔴 The Problem: Two Different Claude Invocation Modules

#### Module 1: `claude_runner.py` (HAS streaming)

**Location**: `planning_pipeline/claude_runner.py:239-273`

```python
def run_claude_sync(
    prompt: str,
    tools: Optional[list[str]] = None,
    timeout: int = 300,
    stream: bool = True,                    # ← Default: streams to terminal
    output_format: OutputFormat = "text"
) -> dict[str, Any]:
```

**Output Behavior**:
- Uses `claude_agent_sdk` async iterator
- Writes text to `sys.stdout` in real-time (`claude_runner.py:175-176`)
- Emits tool calls with colors (`claude_runner.py:188-190`)
- **User sees output as Claude generates it**

**Who Uses It**:
| Caller | File:Line | stream param |
|--------|-----------|--------------|
| `step_research()` | `steps.py:74` | `True` (default) |
| `step_planning()` | `steps.py:185` | `True` (default) |
| `step_phase_decomposition()` | `steps.py:293` | `True` (default) |
| `_annotate_overview_with_claude()` | `steps.py:494` | `True` (default) |
| `_annotate_phase_with_claude()` | `steps.py:553` | `True` (default) |
| `IntegratedOrchestrator.get_project_info()` | `integrated_orchestrator.py:48` | `False` |

#### Module 2: `claude_invoker.py` (NO streaming)

**Location**: `planning_pipeline/phase_execution/claude_invoker.py:8-68`

```python
def invoke_claude(prompt: str, timeout: int = 300) -> dict[str, Any]:
    cmd = [
        "claude",
        "--print",
        "--permission-mode", "bypassPermissions",
        "-p", prompt
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,      # ← ALL OUTPUT CAPTURED
        text=True,
        timeout=timeout
    )
```

**Output Behavior**:
- Uses `subprocess.run()` with `capture_output=True`
- **Stdout and stderr are buffered in memory**
- **Nothing reaches the terminal during execution**
- Output only available in return dict after completion

**Who Uses It**:
| Caller | File:Line |
|--------|-----------|
| `LoopRunner._execute_phase()` | `autonomous_loop.py:789` |

---

### 📁 File Reference Table

| Component | File Path | Role in Output Flow |
|-----------|-----------|---------------------|
| Interactive CLI | `planning_orchestrator.py` | Entry point, calls `PlanningPipeline` |
| Loop CLI | `loop-runner.py` | Entry point, calls `LoopRunner` |
| Pipeline Class | `planning_pipeline/pipeline.py` | Orchestrates steps |
| Step Functions | `planning_pipeline/steps.py` | Calls `run_claude_sync()` - **streams** |
| Streaming Runner | `planning_pipeline/claude_runner.py` | SDK wrapper with streaming support |
| Loop Runner | `planning_pipeline/autonomous_loop.py` | Async loop, calls `invoke_claude()` |
| Blocking Invoker | `planning_pipeline/phase_execution/claude_invoker.py` | subprocess with `capture_output=True` |
| Result Checker | `planning_pipeline/phase_execution/result_checker.py` | Validates results, **does not display output** |

---

### 🔍 Output Flow Analysis

#### Path A: `planning_orchestrator.py` → Terminal (FIXED)

> **Original Issue**: `run_claude_sync()` used `claude_agent_sdk.query()` which yields complete messages, not streaming tokens. Terminal appeared frozen for 5-20 minutes.

> **Fix Applied**: Switched to `run_claude_subprocess()` with `stream_json=False` which uses subprocess + `select.select()` for real-time line-by-line streaming.

```
planning_orchestrator.py
    │
    └──▶ PlanningPipeline.run()
            │
            └──▶ step_research()/step_planning()/etc.
                    │
                    └──▶ run_claude_subprocess(prompt, timeout=1200, stream_json=False)
                            │
                            └──▶ subprocess.Popen("claude --output-format text")
                                    │
                                    └──▶ select.select() for non-blocking I/O
                                            │
                                            └──▶ sys.stdout.write(line)
                                                 sys.stdout.flush()

                                    ✅ OUTPUT VISIBLE TO USER (line-by-line)
```

#### Path B: `loop-runner.py` → Hidden (BROKEN)

```
loop-runner.py
    │
    └──▶ LoopRunner.run()
            │
            └──▶ _execute_loop()
                    │
                    └──▶ _execute_phase()
                            │
                            └──▶ invoke_claude(prompt, timeout=3600)
                                    │
                                    └──▶ subprocess.run(
                                            cmd,
                                            capture_output=True,  # ← CAPTURES ALL OUTPUT
                                            text=True,
                                            timeout=timeout
                                         )

                                    ❌ OUTPUT CAPTURED IN MEMORY
                                    ❌ NOTHING REACHES TERMINAL

            │
            └──▶ check_execution_result(claude_result)
                    │
                    └──▶ Checks claude_result["success"]
                         Logs error if failed (logger.warning)

                         ❌ DOES NOT PRINT claude_result["output"]
                         ❌ USER NEVER SEES CLAUDE'S RESPONSE
```

---

### 📋 Existing Streaming Infrastructure

The fix in `claude_runner.py` includes comprehensive streaming support:

| Function | Location | Purpose |
|----------|----------|---------|
| `_emit_stream_json()` | `claude_runner.py:78-89` | Emit JSON event line |
| `_emit_assistant_text()` | `claude_runner.py:92-95` | Emit text block |
| `_emit_tool_use()` | `claude_runner.py:98-101` | Emit tool call |
| `_emit_tool_result()` | `claude_runner.py:104-112` | Emit tool result |
| `_emit_result()` | `claude_runner.py:115-117` | Emit final result |
| `run_claude_subprocess()` | `claude_runner.py:276-427` | Non-blocking subprocess with select() |

**These are NOT used by `autonomous_loop.py`**

---

### 🔧 What `claude_invoker.py` Does NOT Do

<details>
<summary>Missing functionality compared to claude_runner.py</summary>

| Feature | claude_runner.py | claude_invoker.py |
|---------|------------------|-------------------|
| Stream to terminal | ✅ Yes | ❌ No |
| Non-blocking I/O | ✅ Yes (`select.select()`) | ❌ No |
| SDK integration | ✅ Yes (`claude_agent_sdk`) | ❌ No (subprocess only) |
| Tool call formatting | ✅ Yes (with colors) | ❌ No |
| JSON streaming | ✅ Yes (`output_format="stream-json"`) | ❌ No |
| Timeout during stream | ✅ Yes (checks in loop) | ✅ Yes (`subprocess timeout`) |
| User visibility | ✅ Yes | ❌ No |

</details>

---

### 📊 Timeout Configuration

| Caller | Timeout | File:Line |
|--------|---------|-----------|
| `step_research()` | 1200s (20 min) | `steps.py:74` |
| `step_planning()` | 1200s (20 min) | `steps.py:185` |
| `step_phase_decomposition()` | 1200s (20 min) | `steps.py:293` |
| `_annotate_*()` | 120s (2 min) | `steps.py:494, 553` |
| `get_project_info()` | 60s (1 min) | `integrated_orchestrator.py:48` |
| `LoopRunner._execute_phase()` | **3600s (1 hour)** | `autonomous_loop.py:789` |

**Note**: The loop path has a 1-hour timeout during which **no output is visible**.

---

## Code References

| Description | Location |
|-------------|----------|
| SDK streaming implementation | `planning_pipeline/claude_runner.py:120-236` |
| Sync wrapper with streaming | `planning_pipeline/claude_runner.py:239-273` |
| Subprocess fallback with streaming | `planning_pipeline/claude_runner.py:276-427` |
| Blocking subprocess (no streaming) | `planning_pipeline/phase_execution/claude_invoker.py:8-68` |
| Loop phase execution | `planning_pipeline/autonomous_loop.py:769-792` |
| Result checker (no output display) | `planning_pipeline/phase_execution/result_checker.py:12-45` |
| Steps using streaming runner | `planning_pipeline/steps.py:74, 185, 293, 494, 553` |

---

## Architecture Documentation

### Invocation Modules

The codebase has evolved to have two separate Claude invocation modules:

1. **`claude_runner.py`** - Modern SDK-based implementation
   - Uses `claude_agent_sdk` for async streaming
   - Supports both text and stream-json output formats
   - Designed for interactive use where user needs real-time feedback

2. **`claude_invoker.py`** - Legacy subprocess implementation
   - Uses `subprocess.run()` with captured output
   - No streaming capability
   - Used by autonomous loop where output was deemed unnecessary

### Why Two Modules Exist

Based on imports and commit history:
- `claude_runner.py` was updated in commit d196c58 for SDK migration
- `claude_invoker.py` exists in `phase_execution/` subdirectory, separate from main module
- The loop path was designed for unattended execution

---

## Historical Context (from thoughts/)

No prior research documents were found specifically about streaming output. This research is the first comprehensive documentation of the output flow architecture.

---

## Related Research

- `thoughts/shared/research/2026-01-01-loop-runner-integrated-orchestrator-analysis.md` - Loop runner architecture (if exists)

---

## Open Questions

1. **Was the output hiding intentional for autonomous_loop.py?**
   - The code comments don't indicate why `capture_output=True` was chosen

2. **Should autonomous_loop.py use claude_runner.py instead?**
   - Would require refactoring to use SDK-based approach
   - Would need to handle async properly (it already uses `async def _execute_phase()`)

3. **What happens to clarifying questions in loop mode?**
   - Claude's questions are captured but never shown
   - User has no opportunity to respond
   - This breaks interactive workflows entirely

4. **Why does phase_execution/ have its own invoker?**
   - Potential code duplication
   - Different assumptions about output requirements

---

## Key Discovery Summary

```
┌────────────────────────────────────────────────────────────────────────┐
│                           KEY FINDING (UPDATED)                        │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ORIGINAL ISSUE: Both paths had streaming problems!                    │
│                                                                        │
│  1. steps.py used run_claude_sync() → claude_agent_sdk.query()         │
│     The SDK yields COMPLETE MESSAGES, not streaming tokens.            │
│     Terminal appeared frozen for 5-20 minutes.                         │
│                                                                        │
│  2. autonomous_loop.py uses claude_invoker.py → subprocess.run()       │
│     Uses capture_output=True which buffers all output.                 │
│                                                                        │
│  FIX APPLIED:                                                          │
│  ✅ steps.py now imports: from .claude_runner import run_claude_subprocess │
│     Uses subprocess.Popen + select.select() for real-time streaming    │
│                                                                        │
│  ❌ autonomous_loop.py still uses claude_invoker.py (NOT FIXED YET)    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```
