# Loop Runner IntegratedOrchestrator TDD Implementation Plan

## Overview

This plan implements integration between `autonomous_loop.py` (LoopRunner) and `IntegratedOrchestrator` to enable LLM-driven plan discovery, dynamic resumption, and phase-aware execution.

## Phases

| Phase | File | Description | Human-Testable Function |
|-------|------|-------------|-------------------------|
| 1 | [01-orchestrator-init](2026-01-01-tdd-loop-runner-orchestrator-01-orchestrator-init.md) | Accept orchestrator parameter | `LoopRunner(orchestrator=...)` |
| 2 | [02-plan-discovery](2026-01-01-tdd-loop-runner-orchestrator-02-plan-discovery.md) | Auto-discover plans from orchestrator | `runner.run()` with auto-discovery |
| 3 | [03-backward-compat](2026-01-01-tdd-loop-runner-orchestrator-03-backward-compat.md) | Ensure backward compatibility | `LoopRunner(plan_path=...)` works as before |
| 4 | [04-phase-progression](2026-01-01-tdd-loop-runner-orchestrator-04-phase-progression.md) | Query orchestrator for next feature | `runner.run()` progresses through phases |
| 5 | [05-status-updates](2026-01-01-tdd-loop-runner-orchestrator-05-status-updates.md) | Update feature status in orchestrator | Status reflected in orchestrator |
| 6 | [06-resume-state](2026-01-01-tdd-loop-runner-orchestrator-06-resume-state.md) | Resume from orchestrator state | `runner.resume()` continues from IN_PROGRESS |
| 7 | [07-integration-tests](2026-01-01-tdd-loop-runner-orchestrator-07-integration-tests.md) | Full integration testing | End-to-end workflow verification |

## Implementation Order

Phases should be implemented in order (1 → 7). Each phase builds on the previous.

## Files Modified

- `planning_pipeline/autonomous_loop.py` - Main implementation
- `tests/test_autonomous_loop.py` - Unit tests
- `tests/test_loop_orchestrator_integration.py` - Integration tests (new file)

## References

- Research: `thoughts/searchable/shared/research/2026-01-01-loop-runner-integrated-orchestrator-analysis.md`
- LoopRunner: `planning_pipeline/autonomous_loop.py`
- IntegratedOrchestrator: `planning_pipeline/integrated_orchestrator.py`
