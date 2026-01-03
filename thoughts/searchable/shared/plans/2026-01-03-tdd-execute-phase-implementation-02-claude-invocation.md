# Phase 2: Claude Invocation

## Overview

Create a function to invoke Claude Code via subprocess and return structured results. This handles the actual execution of Claude with proper timeout handling and error recovery.

## Dependencies

### Requires
- Phase 1: Prompt Generation (provides the prompt to execute)

### Blocks
- Phase 4: Full Integration

## Changes Required

### New Files

**File**: `planning_pipeline/phase_execution/claude_invoker.py:1-55`
```python
"""Claude Code subprocess invocation."""

import subprocess
import time
from typing import Any


def invoke_claude(prompt: str, timeout: int = 300) -> dict[str, Any]:
    """Invoke Claude Code via subprocess.

    Args:
        prompt: The prompt to send to Claude
        timeout: Maximum time in seconds to wait

    Returns:
        Dictionary with:
        - success: bool indicating command completed successfully
        - output: stdout from Claude
        - error: stderr or error message
        - elapsed: time in seconds
    """
    cmd = [
        "claude",
        "--print",
        "--permission-mode", "bypassPermissions",
        "-p", prompt
    ]

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        elapsed = time.time() - start_time

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "elapsed": elapsed
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": f"Command timed out after {timeout}s",
            "elapsed": timeout
        }
    except FileNotFoundError:
        return {
            "success": False,
            "output": "",
            "error": "claude command not found",
            "elapsed": time.time() - start_time
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "elapsed": time.time() - start_time
        }
```

### Test File

**File**: `tests/test_execute_phase.py` (append to existing)
```python
class TestClaudeInvocation:
    """Tests for Claude subprocess invocation."""

    @pytest.fixture
    def mock_subprocess_success(self):
        """Mock successful subprocess run."""
        with patch('planning_pipeline.phase_execution.claude_invoker.subprocess') as mock:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "Success output"
            mock_process.stderr = ""
            mock.run.return_value = mock_process
            yield mock

    @pytest.mark.asyncio
    async def test_invoke_claude_returns_result_dict(self, mock_subprocess_success):
        """Should return structured result from Claude invocation."""
        from planning_pipeline.phase_execution.claude_invoker import invoke_claude

        result = invoke_claude("Test prompt", timeout=60)

        assert "success" in result
        assert "output" in result
        assert "error" in result
        assert "elapsed" in result

    @pytest.mark.asyncio
    async def test_invoke_claude_success_on_zero_return(self, mock_subprocess_success):
        """Should report success when return code is 0."""
        from planning_pipeline.phase_execution.claude_invoker import invoke_claude

        result = invoke_claude("Test prompt", timeout=60)

        assert result["success"] is True

    def test_invoke_claude_failure_on_nonzero_return(self):
        """Should report failure when return code is non-zero."""
        with patch('planning_pipeline.phase_execution.claude_invoker.subprocess') as mock:
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stdout = ""
            mock_process.stderr = "Error occurred"
            mock.run.return_value = mock_process

            from planning_pipeline.phase_execution.claude_invoker import invoke_claude
            result = invoke_claude("Test prompt", timeout=60)

            assert result["success"] is False

    def test_invoke_claude_handles_command_not_found(self):
        """Should handle missing claude command gracefully."""
        with patch('planning_pipeline.phase_execution.claude_invoker.subprocess') as mock:
            mock.run.side_effect = FileNotFoundError("claude not found")

            from planning_pipeline.phase_execution.claude_invoker import invoke_claude
            result = invoke_claude("Test prompt", timeout=60)

            assert result["success"] is False
            assert "not found" in result["error"].lower()

    def test_invoke_claude_handles_timeout(self):
        """Should handle subprocess timeout gracefully."""
        with patch('planning_pipeline.phase_execution.claude_invoker.subprocess') as mock:
            import subprocess as sp
            mock.run.side_effect = sp.TimeoutExpired("claude", 60)

            from planning_pipeline.phase_execution.claude_invoker import invoke_claude
            result = invoke_claude("Test prompt", timeout=60)

            assert result["success"] is False
            assert "timeout" in result["error"].lower()
```

## Success Criteria

### Automated
- [ ] Tests fail initially (Red): `pytest tests/test_execute_phase.py::TestClaudeInvocation -v`
- [ ] Tests pass after implementation (Green): `pytest tests/test_execute_phase.py::TestClaudeInvocation -v`
- [ ] All tests pass: `pytest tests/ -v`

### Manual
- [ ] Run `invoke_claude("echo hello")` without mocks and verify subprocess is called
- [ ] Verify timeout behavior with a long-running prompt

## Human-Testable Function

After completing this phase, the following function is ready for manual testing:

```python
from planning_pipeline.phase_execution.claude_invoker import invoke_claude

# Test with a simple prompt (requires claude CLI installed)
result = invoke_claude("Say hello", timeout=30)
print(f"Success: {result['success']}")
print(f"Output: {result['output']}")
print(f"Error: {result['error']}")
print(f"Elapsed: {result['elapsed']:.2f}s")
```

Expected output: A dictionary with success=True/False and captured output/error.
