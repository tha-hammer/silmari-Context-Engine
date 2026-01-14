# Phase 7: Integration Tests

## Overview

Full integration testing between `LoopRunner` and `IntegratedOrchestrator` with real (or near-real) components. Validates the complete workflow: discover plans, execute phases, update status, resume from interruption.

## Dependencies

- **Requires**: Phases 1-6 (all previous phases)
- **Blocks**: None (final phase)

## Changes Required

### tests/test_loop_orchestrator_integration.py (new file)

```python
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch
from planning_pipeline.autonomous_loop import LoopRunner, LoopState
from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator


class TestLoopOrchestratorIntegration:
    """Integration tests for LoopRunner + IntegratedOrchestrator."""

    @pytest.fixture
    def temp_plan_dir(self):
        """Create temporary directory with test plans."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan1 = Path(tmpdir) / "01-setup.md"
            plan1.write_text("""# Setup Plan
## Phase: setup
- Initialize project
""")
            plan2 = Path(tmpdir) / "02-implementation.md"
            plan2.write_text("""# Implementation Plan
## Phase: implementation
- Implement features
""")
            yield tmpdir

    @pytest.fixture
    def orchestrator(self, temp_plan_dir):
        """Create orchestrator pointing to test plans."""
        return IntegratedOrchestrator(plans_directory=temp_plan_dir)

    @pytest.mark.asyncio
    async def test_full_execution_cycle(self, orchestrator):
        """Full cycle: discover plans, execute phases, update status."""
        runner = LoopRunner(orchestrator=orchestrator)
        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.run()
        assert runner.state == LoopState.COMPLETED
        features = orchestrator.get_all_features()
        completed = [f for f in features if f.status == "COMPLETED"]
        assert len(completed) == len(features)

    @pytest.mark.asyncio
    async def test_resume_after_interruption(self, orchestrator):
        """Should correctly resume after pause/interruption."""
        runner = LoopRunner(orchestrator=orchestrator)
        execution_count = 0

        async def mock_execute():
            nonlocal execution_count
            execution_count += 1
            if execution_count == 1:
                await runner.pause()
                return True
            return True

        with patch.object(runner, '_execute_phase', side_effect=mock_execute):
            await runner.run()
        assert runner.state == LoopState.PAUSED

        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True
            await runner.resume()
        assert runner.state == LoopState.COMPLETED

    @pytest.mark.asyncio
    async def test_handles_phase_failure(self, orchestrator):
        """Should handle phase failure gracefully."""
        runner = LoopRunner(orchestrator=orchestrator)
        with patch.object(runner, '_execute_phase', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = False
            await runner.run()
        assert runner.state == LoopState.FAILED
        current = orchestrator.get_current_feature()
        assert current is None or current.status == "FAILED"

    @pytest.mark.asyncio
    async def test_mixed_mode_explicit_path_with_orchestrator(self, orchestrator, temp_plan_dir):
        """Should use explicit plan_path even when orchestrator available."""
        explicit_plan = Path(temp_plan_dir) / "explicit.md"
        explicit_plan.write_text("# Explicit Plan\n")

        runner = LoopRunner(
            orchestrator=orchestrator,
            plan_path=str(explicit_plan)
        )
        with patch.object(runner, '_execute_loop', new_callable=AsyncMock):
            await runner.run()
        assert runner.plan_path == str(explicit_plan)
```

## Success Criteria

### Automated
- [x] Integration tests pass: `pytest tests/test_loop_orchestrator_integration.py -v`
- [x] Full test suite passes: `pytest tests/ -v`
- [x] Type checking passes: `mypy planning_pipeline/`
- [x] No import errors or circular dependencies

### Manual
- [x] End-to-end workflow works with real plans
- [x] Status correctly reflected in orchestrator state
- [x] Logging shows expected flow

## Human-Testable Function

```python
import asyncio
import tempfile
from pathlib import Path
from planning_pipeline.autonomous_loop import LoopRunner, LoopState
from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

# Create real temp directory with plans
tmpdir = tempfile.mkdtemp()
plan1 = Path(tmpdir) / "2026-01-01-tdd-feature-01-setup.md"
plan1.write_text("""# Setup Plan
---
phase: setup
status: not_started
---
## Overview
Setup phase for testing.
""")

plan2 = Path(tmpdir) / "2026-01-01-tdd-feature-02-implement.md"
plan2.write_text("""# Implementation Plan
---
phase: implementation
status: not_started
---
## Overview
Implementation phase for testing.
""")

# Create real orchestrator
orchestrator = IntegratedOrchestrator(plans_directory=tmpdir)
print(f"Plans discovered: {len(orchestrator.discover_plans())}")

# Create runner with orchestrator
runner = LoopRunner(orchestrator=orchestrator)
print(f"Initial state: {runner.state}")

# For full test, you'd run:
# await runner.run()
# assert runner.state == LoopState.COMPLETED

print(f"\n✓ Integration test setup complete")
print(f"  Plans directory: {tmpdir}")
print(f"  Runner ready for: await runner.run()")

# Cleanup
import shutil
shutil.rmtree(tmpdir)
```

## Final Verification

After all phases complete, run full verification:

```bash
# All unit tests
pytest tests/test_autonomous_loop.py -v

# Integration tests
pytest tests/test_loop_orchestrator_integration.py -v

# Type checking
mypy planning_pipeline/autonomous_loop.py planning_pipeline/integrated_orchestrator.py

# Full test suite
pytest tests/ -v --tb=short
```
