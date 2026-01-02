# Phase 1: Accept Orchestrator Parameter

## Overview

Add optional `orchestrator` parameter to `LoopRunner.__init__` to enable integration with `IntegratedOrchestrator`. This is the foundation for all subsequent phases.

## Dependencies

- **Requires**: None (first phase)
- **Blocks**: Phase 2-7 (all subsequent phases)

## Changes Required

### planning_pipeline/autonomous_loop.py

Add orchestrator parameter to `__init__`:

```python
# autonomous_loop.py:45-60 (approximate)
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator


class LoopRunner:
    def __init__(
        self,
        plan_path: Optional[str] = None,
        current_phase: Optional[str] = None,
        orchestrator: Optional["IntegratedOrchestrator"] = None,
        # ... existing params
    ):
        self.plan_path = plan_path
        self.current_phase = current_phase
        self.orchestrator = orchestrator
        # ... existing initialization
```

### tests/test_autonomous_loop.py

Add new test class:

```python
class TestLoopRunnerOrchestratorInit:
    """Tests for LoopRunner orchestrator initialization."""

    def test_accepts_orchestrator_parameter(self):
        """LoopRunner should accept an optional orchestrator parameter."""
        orchestrator = Mock(spec=IntegratedOrchestrator)
        runner = LoopRunner(orchestrator=orchestrator)
        assert runner.orchestrator is orchestrator

    def test_orchestrator_defaults_to_none(self):
        """LoopRunner should default orchestrator to None for backward compat."""
        runner = LoopRunner()
        assert runner.orchestrator is None

    def test_accepts_both_orchestrator_and_plan_path(self):
        """LoopRunner should accept both orchestrator and explicit plan_path."""
        orchestrator = Mock(spec=IntegratedOrchestrator)
        runner = LoopRunner(orchestrator=orchestrator, plan_path="/explicit/plan.md")
        assert runner.orchestrator is orchestrator
        assert runner.plan_path == "/explicit/plan.md"
```

## Success Criteria

### Automated
- [x] Test fails initially (Red): `pytest tests/test_autonomous_loop.py::TestLoopRunnerOrchestratorInit -v`
- [x] Test passes after implementation (Green): `pytest tests/test_autonomous_loop.py::TestLoopRunnerOrchestratorInit -v`
- [x] All existing tests still pass: `pytest tests/test_autonomous_loop.py -v`
- [x] Type check passes: `mypy planning_pipeline/autonomous_loop.py`

### Manual
- [x] Import works without circular dependency issues
- [x] Can instantiate `LoopRunner(orchestrator=IntegratedOrchestrator(...))` in Python REPL

## Human-Testable Function

```python
from planning_pipeline.autonomous_loop import LoopRunner
from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

# Test 1: With orchestrator
orch = IntegratedOrchestrator()
runner = LoopRunner(orchestrator=orch)
assert runner.orchestrator is orch  # Should pass

# Test 2: Without orchestrator (backward compat)
runner2 = LoopRunner(plan_path="/some/plan.md")
assert runner2.orchestrator is None  # Should pass
```
