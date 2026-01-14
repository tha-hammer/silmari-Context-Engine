# Phase 1: Prompt Generation

## Overview

Build a prompt generation function that reads plan file content and creates a formatted prompt for Claude Code execution. This is the first step in replacing the `_execute_phase()` stub.

## Dependencies

### Requires
- None (first phase)

### Blocks
- Phase 2: Claude Invocation
- Phase 4: Full Integration

## Changes Required

### New Files

**File**: `planning_pipeline/phase_execution/__init__.py`
```python
"""Phase execution module for autonomous loop."""
```

**File**: `planning_pipeline/phase_execution/prompt_builder.py:1-35`
```python
"""Prompt generation for phase execution."""

from pathlib import Path
from typing import Optional


def build_phase_prompt(plan_path: str, current_phase: Optional[str]) -> str:
    """Build a prompt for executing the current phase.

    Args:
        plan_path: Path to the plan file
        current_phase: Current phase identifier (e.g., feature ID)

    Returns:
        Formatted prompt string for Claude

    Raises:
        FileNotFoundError: If plan_path doesn't exist
    """
    path = Path(plan_path)
    if not path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")

    plan_content = path.read_text()
    phase_id = current_phase or "unknown"

    return f"""## Phase: {phase_id}

## Plan Content
{plan_content}

## Instructions
1. Implement the requirements described in the plan above
2. Run tests to verify implementation
3. Commit changes with descriptive message
4. Use `bd sync` if beads changes were made

## Success Criteria
- All tests pass
- Changes are committed
- Code follows existing patterns
"""
```

### Modified Files

**File**: `planning_pipeline/autonomous_loop.py:1-10` (add import)
```python
from planning_pipeline.phase_execution.prompt_builder import build_phase_prompt
```

**File**: `planning_pipeline/autonomous_loop.py` (add method to LoopRunner class)
```python
def _build_phase_prompt(self) -> str:
    """Build prompt for the current phase."""
    return build_phase_prompt(self.plan_path, self.current_phase)
```

### Test File

**File**: `tests/test_execute_phase.py:1-65`
```python
"""Tests for _execute_phase implementation."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from planning_pipeline.autonomous_loop import LoopRunner, LoopState


class TestPromptGeneration:
    """Tests for phase prompt building."""

    @pytest.fixture
    def temp_plan_file(self, tmp_path):
        """Create a temporary plan file."""
        plan_path = tmp_path / "test-plan.md"
        plan_path.write_text("""# Test Feature Plan

## Phase 1: Setup
- Create initial structure

## Phase 2: Implementation
- Implement the feature

## Success Criteria
- [ ] Tests pass
""")
        return str(plan_path)

    @pytest.mark.asyncio
    async def test_build_prompt_includes_plan_content(self, temp_plan_file):
        """Prompt should include the plan file content."""
        runner = LoopRunner(plan_path=temp_plan_file)
        runner.current_phase = "feature-1"

        prompt = runner._build_phase_prompt()

        assert "Test Feature Plan" in prompt
        assert "Phase 1: Setup" in prompt
        assert "Success Criteria" in prompt

    @pytest.mark.asyncio
    async def test_build_prompt_includes_phase_identifier(self, temp_plan_file):
        """Prompt should include the current phase identifier."""
        runner = LoopRunner(plan_path=temp_plan_file)
        runner.current_phase = "feature-xyz"

        prompt = runner._build_phase_prompt()

        assert "feature-xyz" in prompt

    def test_build_prompt_handles_missing_file(self, tmp_path):
        """Should raise FileNotFoundError for missing plan."""
        runner = LoopRunner(plan_path=str(tmp_path / "nonexistent.md"))
        runner.current_phase = "phase-1"

        with pytest.raises(FileNotFoundError):
            runner._build_phase_prompt()

    def test_build_prompt_handles_empty_plan(self, tmp_path):
        """Should handle empty plan file gracefully."""
        empty_plan = tmp_path / "empty.md"
        empty_plan.write_text("")
        runner = LoopRunner(plan_path=str(empty_plan))
        runner.current_phase = "phase-1"

        # Should not raise, but prompt should still include phase
        prompt = runner._build_phase_prompt()
        assert "phase-1" in prompt
```

## Success Criteria

### Automated
- [ ] Test fails initially (Red): `pytest tests/test_execute_phase.py::TestPromptGeneration -v`
- [ ] Tests pass after implementation (Green): `pytest tests/test_execute_phase.py::TestPromptGeneration -v`
- [ ] All existing tests still pass: `pytest tests/test_autonomous_loop.py -v`
- [ ] Type check passes: `mypy planning_pipeline/phase_execution/`

### Manual
- [ ] Create a test plan file manually and verify `_build_phase_prompt()` returns expected content
- [ ] Verify prompt is readable and actionable for Claude

## Human-Testable Function

After completing this phase, the following function is ready for manual testing:

```python
from planning_pipeline.autonomous_loop import LoopRunner

runner = LoopRunner(plan_path="path/to/plan.md")
runner.current_phase = "test-phase"
prompt = runner._build_phase_prompt()
print(prompt)
```

Expected output: A formatted prompt containing the plan file content and phase identifier.
