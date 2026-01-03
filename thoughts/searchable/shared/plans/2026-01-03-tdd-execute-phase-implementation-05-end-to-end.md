# Phase 5: End-to-End Integration

## Overview

Validate the complete autonomous loop by testing the full flow: orchestrator discovers plans, `_execute_phase()` is called for each, and status is updated. This ensures all components work together correctly.

## Dependencies

### Requires
- Phase 4: Full Integration (complete `_execute_phase()` implementation)

### Blocks
- None (final phase)

## Changes Required

### Test File

**File**: `tests/test_loop_orchestrator_integration.py` (add new test class)
```python
"""End-to-end tests for autonomous loop with orchestrator."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from planning_pipeline.autonomous_loop import LoopRunner, LoopState


class TestExecutePhaseE2E:
    """End-to-end tests with real _execute_phase (mocked Claude)."""

    @pytest.fixture
    def full_setup(self, tmp_path):
        """Set up full orchestrator environment."""
        # Create plan file
        plans_dir = tmp_path / "thoughts" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        plan_file = plans_dir / "2026-01-03-test-feature.md"
        plan_file.write_text("""# Test Feature Plan

## Phase 1
- Implement feature

## Success
- Tests pass
""")

        # Initialize git
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
        (tmp_path / "README.md").write_text("# Test Project")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True)

        return tmp_path

    @pytest.mark.asyncio
    async def test_full_loop_with_mocked_claude(self, full_setup):
        """Should execute full loop with mocked Claude subprocess."""
        # Mock orchestrator
        orchestrator = Mock()
        orchestrator.discover_plans = Mock(return_value=[
            Mock(path=str(full_setup / "thoughts/shared/plans/2026-01-03-test-feature.md"), priority=1)
        ])

        feature_mock = {"id": "feature-1", "title": "Test Feature", "status": "open"}
        orchestrator.get_next_feature = Mock(side_effect=[feature_mock, None])
        orchestrator.get_current_feature = Mock(return_value=None)
        orchestrator.bd = Mock()
        orchestrator.bd.update_status = Mock()

        runner = LoopRunner(orchestrator=orchestrator)
        runner._project_path = full_setup
        runner.plan_path = str(full_setup / "thoughts/shared/plans/2026-01-03-test-feature.md")

        with patch('planning_pipeline.phase_execution.claude_invoker.invoke_claude') as mock_invoke:
            mock_invoke.return_value = {
                "success": True,
                "output": "Feature implemented successfully",
                "error": "",
                "elapsed": 10.0
            }
            with patch('planning_pipeline.phase_execution.result_checker._run_bd_sync'):
                await runner.run()

        # Verify Claude was invoked
        assert mock_invoke.call_count >= 1

    @pytest.mark.asyncio
    async def test_loop_handles_claude_failure(self, full_setup):
        """Should handle Claude failure and update status appropriately."""
        orchestrator = Mock()
        feature_mock = {"id": "feature-1", "title": "Test Feature", "status": "open"}
        orchestrator.get_next_feature = Mock(side_effect=[feature_mock, None])
        orchestrator.get_current_feature = Mock(return_value=None)
        orchestrator.bd = Mock()
        orchestrator.bd.update_status = Mock()

        runner = LoopRunner(orchestrator=orchestrator)
        runner._project_path = full_setup
        runner.plan_path = str(full_setup / "thoughts/shared/plans/2026-01-03-test-feature.md")
        runner.current_phase = "feature-1"

        with patch('planning_pipeline.phase_execution.claude_invoker.invoke_claude') as mock_invoke:
            mock_invoke.return_value = {
                "success": False,
                "output": "",
                "error": "Claude crashed",
                "elapsed": 5.0
            }

            result = await runner._execute_phase()

        assert result is False

    @pytest.mark.asyncio
    async def test_loop_with_multiple_phases(self, full_setup):
        """Should execute multiple phases in sequence."""
        # Create multiple plan files
        plans_dir = full_setup / "thoughts" / "shared" / "plans"
        (plans_dir / "2026-01-03-feature-a.md").write_text("# Feature A\n- Step 1")
        (plans_dir / "2026-01-03-feature-b.md").write_text("# Feature B\n- Step 1")

        orchestrator = Mock()
        features = [
            {"id": "feature-a", "title": "Feature A", "status": "open"},
            {"id": "feature-b", "title": "Feature B", "status": "open"},
        ]
        orchestrator.get_next_feature = Mock(side_effect=features + [None])
        orchestrator.get_current_feature = Mock(return_value=None)
        orchestrator.bd = Mock()
        orchestrator.bd.update_status = Mock()

        runner = LoopRunner(orchestrator=orchestrator)
        runner._project_path = full_setup

        call_count = 0
        with patch('planning_pipeline.phase_execution.claude_invoker.invoke_claude') as mock_invoke:
            def invoke_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                return {
                    "success": True,
                    "output": f"Phase {call_count} done",
                    "error": "",
                    "elapsed": 5.0
                }
            mock_invoke.side_effect = invoke_side_effect

            with patch('planning_pipeline.phase_execution.result_checker._run_bd_sync'):
                # Execute phases manually to test the flow
                for feature in features:
                    runner.current_phase = feature["id"]
                    runner.plan_path = str(plans_dir / f"2026-01-03-{feature['id']}.md")
                    await runner._execute_phase()

        # Verify Claude was invoked twice
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_loop_respects_timeout(self, full_setup):
        """Should handle timeout during Claude invocation."""
        runner = LoopRunner(
            plan_path=str(full_setup / "thoughts/shared/plans/2026-01-03-test-feature.md")
        )
        runner._project_path = full_setup
        runner.current_phase = "timeout-test"

        with patch('planning_pipeline.phase_execution.claude_invoker.invoke_claude') as mock_invoke:
            mock_invoke.return_value = {
                "success": False,
                "output": "",
                "error": "Command timed out after 3600s",
                "elapsed": 3600
            }

            result = await runner._execute_phase()

        assert result is False
```

### No Code Changes Required

This phase validates existing implementations from phases 1-4.

## Success Criteria

### Automated
- [ ] E2E test passes: `pytest tests/test_loop_orchestrator_integration.py::TestExecutePhaseE2E -v`
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Type check passes: `mypy planning_pipeline/`

### Manual
- [ ] Run the autonomous loop with a real plan file and mocked Claude
- [ ] Verify status updates flow correctly through orchestrator
- [ ] Verify bd sync is called after successful execution
- [ ] Run with real Claude on a small test project (integration test)

## Human-Testable Function

After completing this phase, the following function is ready for full end-to-end manual testing:

```python
import asyncio
from pathlib import Path
from planning_pipeline.autonomous_loop import LoopRunner

async def run_full_loop():
    """Run the full autonomous loop with real Claude."""
    runner = LoopRunner(
        plan_path="path/to/your/plan.md",
        project_path=Path.cwd()
    )

    # This will:
    # 1. Read the plan file
    # 2. Build a prompt
    # 3. Invoke Claude Code
    # 4. Check results and run bd sync
    await runner.run()

    print(f"Final state: {runner.state}")

# WARNING: This will actually invoke Claude!
# asyncio.run(run_full_loop())
```

Expected output: The loop executes the plan, invokes Claude, and reports final state.

## Integration Scenarios

### Scenario 1: Full Loop Execution
1. Create a plan file in `thoughts/shared/plans/`
2. Run `python -m planning_pipeline.autonomous_loop`
3. Verify Claude is invoked with the plan content
4. Verify status updates in beads

### Scenario 2: Resume from Interrupted State
1. Start a loop, then interrupt it mid-execution
2. Run the loop again
3. Verify it resumes from IN_PROGRESS feature

### Scenario 3: Handle Claude Failures
1. Create a plan that will cause Claude to fail
2. Run the loop
3. Verify status is updated to FAILED
4. Verify loop stops gracefully
