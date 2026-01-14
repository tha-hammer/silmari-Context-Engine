# Execute Phase Implementation - TDD Plan Overview

## Summary

Implement the `_execute_phase()` method in `autonomous_loop.py` to bridge the orchestration infrastructure with actual Claude Code invocation. This converts the stub implementation into a working phase executor.

## Goal

Transform the stub `_execute_phase()` that always returns `True` into a real implementation that:
1. Reads plan file content and generates a prompt
2. Invokes Claude Code via subprocess
3. Parses the result to determine success/failure
4. Handles timeouts and errors gracefully

## Phase Index

| Phase | File | Description | Human-Testable Function |
|-------|------|-------------|------------------------|
| 1 | [01-prompt-generation](2026-01-03-tdd-execute-phase-implementation-01-prompt-generation.md) | Build prompts from plan files | `_build_phase_prompt()` |
| 2 | [02-claude-invocation](2026-01-03-tdd-execute-phase-implementation-02-claude-invocation.md) | Invoke Claude subprocess | `invoke_claude()` |
| 3 | [03-result-checking](2026-01-03-tdd-execute-phase-implementation-03-result-checking.md) | Validate execution results | `check_execution_result()` |
| 4 | [04-full-integration](2026-01-03-tdd-execute-phase-implementation-04-full-integration.md) | Wire everything into `_execute_phase()` | `_execute_phase()` |
| 5 | [05-end-to-end](2026-01-03-tdd-execute-phase-implementation-05-end-to-end.md) | Full loop E2E testing | `LoopRunner.run()` |

## Dependency Graph

```
Phase 1 (Prompt Generation)
    │
    ▼
Phase 2 (Claude Invocation)
    │
    ▼
Phase 3 (Result Checking)
    │
    ▼
Phase 4 (Full Integration) ← Uses phases 1, 2, 3
    │
    ▼
Phase 5 (End-to-End) ← Validates full loop
```

## Key Files

- **Stub to replace**: `planning_pipeline/autonomous_loop.py:146-155`
- **Reference pattern**: `loop-runner.py:959-1084`
- **Existing runner**: `planning_pipeline/claude_runner.py:23-81`
- **Existing tests**: `tests/test_autonomous_loop.py`

## New Files to Create

```
planning_pipeline/phase_execution/
├── __init__.py
├── prompt_builder.py      # Phase 1
├── claude_invoker.py      # Phase 2
└── result_checker.py      # Phase 3

tests/
├── test_execute_phase.py  # Phases 1-4
└── test_loop_orchestrator_integration.py  # Phase 5 (extend existing)
```

## Success Criteria

- [x] All 5 phases implemented and tested
- [x] All 30 existing tests still pass (actually 24 - now 53 total)
- [x] New test file `test_execute_phase.py` passes (19 tests)
- [ ] Manual E2E test with real Claude works
- [x] Type check passes: `mypy planning_pipeline/phase_execution/`
