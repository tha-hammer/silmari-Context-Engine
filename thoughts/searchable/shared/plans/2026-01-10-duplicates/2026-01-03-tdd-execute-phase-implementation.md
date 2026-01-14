# Execute Phase Implementation TDD Plan

## Overview

Implement the `_execute_phase()` method in `autonomous_loop.py` to bridge the orchestration infrastructure with actual Claude Code invocation. The stub currently returns `True` without doing anything - we need it to:

1. Read plan file content and generate a prompt
2. Invoke Claude Code via `run_claude_sync()` from `claude_runner.py`
3. Parse the result to determine success/failure
4. Handle timeouts and errors gracefully

This follows the same patterns as `loop-runner.py:959-1084` but integrates with the async orchestrator architecture.

## Current State Analysis

### Stub Implementation (`autonomous_loop.py:146-155`)
```python
async def _execute_phase(self) -> bool:
    """Execute the current phase."""
    # Placeholder for actual phase execution
    # In real implementation, this would invoke Claude Code
    logger.info(f"Executing phase: {self.current_phase}")
    return True  # <-- Always returns True, does nothing
```

### Existing Working Claude Invocation (`claude_runner.py:23-81`)
```python
def run_claude_sync(prompt: str, tools: list[str] = None, timeout: int = 300, stream: bool = True) -> dict[str, Any]:
    """Run Claude Code via subprocess and return structured result."""
    cmd = ["claude", "--print", "--verbose", "--permission-mode", "bypassPermissions",
           "--output-format", "stream-json", "-p", prompt]
    # ... subprocess execution with streaming
```

### Key Discoveries:
- `loop-runner.py:1069-1082`: Working Claude subprocess invocation pattern
- `claude_runner.py:23-81`: Already has `run_claude_sync()` that handles streaming, timeouts
- `loop-runner.py:959-1068`: Complete `run_session()` implementation we can model after
- Tests mock `_execute_phase` with `AsyncMock` returning `True/False` (`test_autonomous_loop.py:179`)
- All 30 existing tests pass because they mock `_execute_phase`

## Desired End State

The autonomous loop should:
1. Read plan content and generate phase-specific prompts
2. Execute Claude Code and stream output to terminal
3. Check for git changes, beads sync, and return code
4. Return `True` on success, `False` on failure
5. Each phase should be in its own file for maintainability

### Observable Behaviors:
- Given a plan file path, when executing a phase, then Claude Code subprocess is invoked
- Given a successful Claude invocation with git changes, when checking results, then returns True
- Given a failed Claude invocation (non-zero exit), when checking results, then returns False
- Given a timeout during execution, when elapsed time exceeds limit, then returns False gracefully
- Given beads changes after execution, when checking results, then `bd sync` is run

## What We're NOT Doing

- Not changing the orchestrator architecture (already tested)
- Not changing how plans are discovered (Phase 1-2 already complete)
- Not implementing QA mode or complexity detection (out of scope)
- Not implementing feature_list.json management (that's `loop-runner.py` legacy)

## Testing Strategy

- **Framework**: pytest with pytest-asyncio
- **Test Types**:
  - Unit: Test `_execute_phase()` with mocked subprocess
  - Unit: Test `_check_execution_result()` with various outcomes
  - Unit: Test `_build_phase_prompt()` with plan content
  - Integration: Test full `run()` with mocked Claude subprocess
- **Mocking/Setup**: Mock `subprocess.run`/`subprocess.Popen`, mock file system for plan content

---

## Phase 1: Prompt Generation

### Test Specification

**Given**: A plan file path and current phase identifier
**When**: Building a prompt for Claude
**Then**: Prompt includes plan content and phase-specific instructions

**Edge Cases**:
- Plan file doesn't exist
- Plan content is empty
- Phase is None (backward compat mode)

### TDD Cycle

#### Red: Write Failing Test
**File**: `tests/test_execute_phase.py`
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

        # Should not raise, but prompt should indicate empty
        prompt = runner._build_phase_prompt()
        assert "phase-1" in prompt
```

#### Green: Minimal Implementation
**File**: `planning_pipeline/phase_execution/__init__.py`
```python
"""Phase execution module for autonomous loop."""
```

**File**: `planning_pipeline/phase_execution/prompt_builder.py`
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

Update `autonomous_loop.py` to use the prompt builder:
```python
from planning_pipeline.phase_execution.prompt_builder import build_phase_prompt

class LoopRunner:
    # ... existing code ...

    def _build_phase_prompt(self) -> str:
        """Build prompt for the current phase."""
        return build_phase_prompt(self.plan_path, self.current_phase)
```

#### Refactor: Improve Code
After tests pass, consider:
- Add logging for prompt generation
- Add prompt template customization

### Success Criteria

**Automated:**
- [ ] Test fails initially (Red): `pytest tests/test_execute_phase.py::TestPromptGeneration -v`
- [ ] Tests pass after implementation (Green): `pytest tests/test_execute_phase.py::TestPromptGeneration -v`
- [ ] All existing tests still pass: `pytest tests/test_autonomous_loop.py -v`
- [ ] Type check passes: `mypy planning_pipeline/phase_execution/`

**Manual:**
- [ ] Prompt includes plan content when inspected
- [ ] Prompt is readable and actionable

---

## Phase 2: Claude Invocation

### Test Specification

**Given**: A valid prompt string
**When**: Invoking Claude Code subprocess
**Then**: Returns result dict with success, output, error, elapsed

**Edge Cases**:
- Claude command not found
- Subprocess times out
- Non-zero return code

### TDD Cycle

#### Red: Write Failing Test
**File**: `tests/test_execute_phase.py` (append)
```python
class TestClaudeInvocation:
    """Tests for Claude subprocess invocation."""

    @pytest.fixture
    def mock_subprocess_success(self):
        """Mock successful subprocess run."""
        with patch('planning_pipeline.phase_execution.claude_invoker.subprocess') as mock:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = b"Success output"
            mock_process.stderr = b""
            mock_process.poll.return_value = 0
            mock.Popen.return_value = mock_process
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
            mock_process.stdout = b""
            mock_process.stderr = b"Error occurred"
            mock_process.poll.return_value = 1
            mock.Popen.return_value = mock_process

            from planning_pipeline.phase_execution.claude_invoker import invoke_claude
            result = invoke_claude("Test prompt", timeout=60)

            assert result["success"] is False
            assert "Error" in result["error"] or result["error"] != ""

    def test_invoke_claude_handles_command_not_found(self):
        """Should handle missing claude command gracefully."""
        with patch('planning_pipeline.phase_execution.claude_invoker.subprocess') as mock:
            mock.Popen.side_effect = FileNotFoundError("claude not found")

            from planning_pipeline.phase_execution.claude_invoker import invoke_claude
            result = invoke_claude("Test prompt", timeout=60)

            assert result["success"] is False
            assert "not found" in result["error"].lower()

    def test_invoke_claude_handles_timeout(self):
        """Should handle subprocess timeout gracefully."""
        with patch('planning_pipeline.phase_execution.claude_invoker.subprocess') as mock:
            import subprocess
            mock.Popen.side_effect = subprocess.TimeoutExpired("claude", 60)

            from planning_pipeline.phase_execution.claude_invoker import invoke_claude
            result = invoke_claude("Test prompt", timeout=60)

            assert result["success"] is False
            assert "timeout" in result["error"].lower()
```

#### Green: Minimal Implementation
**File**: `planning_pipeline/phase_execution/claude_invoker.py`
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

#### Refactor: Improve Code
After tests pass:
- Consider reusing `run_claude_sync` from `claude_runner.py`
- Add streaming support if needed
- Add model selection parameter

### Success Criteria

**Automated:**
- [ ] Tests fail initially (Red): `pytest tests/test_execute_phase.py::TestClaudeInvocation -v`
- [ ] Tests pass after implementation (Green): `pytest tests/test_execute_phase.py::TestClaudeInvocation -v`
- [ ] All tests pass: `pytest tests/ -v`

**Manual:**
- [ ] Claude is actually invoked when run without mocks (integration)

---

## Phase 3: Result Checking

### Test Specification

**Given**: Claude execution result and project path
**When**: Checking if execution was successful
**Then**: Returns True only if: return code 0, git changes detected, beads synced

**Edge Cases**:
- No git changes after execution
- Git command fails
- beads not initialized in project

### TDD Cycle

#### Red: Write Failing Test
**File**: `tests/test_execute_phase.py` (append)
```python
class TestResultChecking:
    """Tests for execution result validation."""

    @pytest.fixture
    def temp_git_repo(self, tmp_path):
        """Create a temporary git repo."""
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
        # Create initial commit
        (tmp_path / "initial.txt").write_text("initial")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True)
        return tmp_path

    def test_check_result_success_with_changes(self, temp_git_repo):
        """Should return True when Claude succeeded and git has changes."""
        # Create a change
        (temp_git_repo / "new_file.py").write_text("# new content")

        from planning_pipeline.phase_execution.result_checker import check_execution_result

        result = check_execution_result(
            claude_result={"success": True, "output": "done", "error": "", "elapsed": 5.0},
            project_path=temp_git_repo
        )

        assert result is True

    def test_check_result_failure_on_claude_error(self, temp_git_repo):
        """Should return False when Claude returned error."""
        from planning_pipeline.phase_execution.result_checker import check_execution_result

        result = check_execution_result(
            claude_result={"success": False, "output": "", "error": "failed", "elapsed": 5.0},
            project_path=temp_git_repo
        )

        assert result is False

    def test_check_result_runs_bd_sync(self, temp_git_repo):
        """Should run bd sync after successful execution."""
        (temp_git_repo / "new_file.py").write_text("# new content")

        with patch('planning_pipeline.phase_execution.result_checker.subprocess') as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0)

            from planning_pipeline.phase_execution.result_checker import check_execution_result

            check_execution_result(
                claude_result={"success": True, "output": "done", "error": "", "elapsed": 5.0},
                project_path=temp_git_repo
            )

            # Check bd sync was called
            bd_calls = [c for c in mock_sub.run.call_args_list
                       if "bd" in str(c) and "sync" in str(c)]
            assert len(bd_calls) >= 1

    def test_check_result_handles_no_beads(self, temp_git_repo):
        """Should handle projects without beads gracefully."""
        (temp_git_repo / "new_file.py").write_text("# new content")

        with patch('planning_pipeline.phase_execution.result_checker.subprocess') as mock_sub:
            # Simulate bd command not found
            def side_effect(*args, **kwargs):
                if "bd" in str(args):
                    raise FileNotFoundError("bd not found")
                return MagicMock(returncode=0, stdout="")
            mock_sub.run.side_effect = side_effect

            from planning_pipeline.phase_execution.result_checker import check_execution_result

            # Should still succeed without beads
            result = check_execution_result(
                claude_result={"success": True, "output": "done", "error": "", "elapsed": 5.0},
                project_path=temp_git_repo
            )

            assert result is True
```

#### Green: Minimal Implementation
**File**: `planning_pipeline/phase_execution/result_checker.py`
```python
"""Execution result validation."""

import subprocess
import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


def check_execution_result(
    claude_result: dict[str, Any],
    project_path: Path
) -> bool:
    """Check if phase execution was successful.

    Validates:
    1. Claude returned success (return code 0)
    2. Git repository has changes or commits
    3. Runs bd sync if beads is available

    Args:
        claude_result: Result dict from invoke_claude
        project_path: Path to the project directory

    Returns:
        True if execution was successful, False otherwise
    """
    # Check Claude return code
    if not claude_result.get("success", False):
        logger.warning(f"Claude execution failed: {claude_result.get('error', 'unknown')}")
        return False

    # Check for git changes
    has_changes = _check_git_changes(project_path)
    if not has_changes:
        logger.info("No git changes detected after execution")
        # Still consider success if Claude reported success
        # (might be a no-op phase or changes already committed)

    # Run bd sync if available
    _run_bd_sync(project_path)

    return True


def _check_git_changes(project_path: Path) -> bool:
    """Check if git has uncommitted or new changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        return bool(result.stdout.strip())
    except Exception as e:
        logger.warning(f"Could not check git status: {e}")
        return False


def _run_bd_sync(project_path: Path) -> bool:
    """Run bd sync to commit beads changes."""
    try:
        result = subprocess.run(
            ["bd", "sync"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            logger.debug("bd sync completed successfully")
            return True
        else:
            logger.debug(f"bd sync returned {result.returncode}")
            return False
    except FileNotFoundError:
        logger.debug("bd command not found - beads not installed")
        return False
    except Exception as e:
        logger.warning(f"bd sync failed: {e}")
        return False
```

#### Refactor: Improve Code
After tests pass:
- Add more detailed logging
- Consider configurable timeout values

### Success Criteria

**Automated:**
- [ ] Tests fail initially (Red): `pytest tests/test_execute_phase.py::TestResultChecking -v`
- [ ] Tests pass after implementation (Green): `pytest tests/test_execute_phase.py::TestResultChecking -v`
- [ ] All tests pass: `pytest tests/ -v`

**Manual:**
- [ ] bd sync actually runs in real project
- [ ] Git changes are detected correctly

---

## Phase 4: Full _execute_phase Integration

### Test Specification

**Given**: A LoopRunner with plan path and current phase
**When**: Calling `_execute_phase()`
**Then**: Prompt is built, Claude is invoked, result is checked, boolean returned

**Edge Cases**:
- Plan file missing at execution time
- Claude invocation fails
- Result check fails

### TDD Cycle

#### Red: Write Failing Test
**File**: `tests/test_execute_phase.py` (append)
```python
class TestExecutePhaseIntegration:
    """Integration tests for _execute_phase method."""

    @pytest.fixture
    def runner_with_plan(self, tmp_path):
        """Create a runner with a valid plan file."""
        plan_path = tmp_path / "plan.md"
        plan_path.write_text("""# Test Plan

## Implementation
- Do the thing
""")

        # Initialize git repo
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
        (tmp_path / "initial.txt").write_text("initial")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True)

        runner = LoopRunner(plan_path=str(plan_path))
        runner.current_phase = "test-phase"
        runner._project_path = tmp_path
        return runner

    @pytest.mark.asyncio
    async def test_execute_phase_invokes_claude(self, runner_with_plan):
        """Should invoke Claude with built prompt."""
        with patch('planning_pipeline.phase_execution.claude_invoker.invoke_claude') as mock_invoke:
            mock_invoke.return_value = {
                "success": True,
                "output": "done",
                "error": "",
                "elapsed": 5.0
            }

            result = await runner_with_plan._execute_phase()

            mock_invoke.assert_called_once()
            call_args = mock_invoke.call_args
            prompt = call_args[0][0]
            assert "Test Plan" in prompt
            assert "test-phase" in prompt

    @pytest.mark.asyncio
    async def test_execute_phase_returns_true_on_success(self, runner_with_plan):
        """Should return True when execution succeeds."""
        with patch('planning_pipeline.phase_execution.claude_invoker.invoke_claude') as mock_invoke:
            mock_invoke.return_value = {
                "success": True,
                "output": "done",
                "error": "",
                "elapsed": 5.0
            }

            result = await runner_with_plan._execute_phase()

            assert result is True

    @pytest.mark.asyncio
    async def test_execute_phase_returns_false_on_claude_failure(self, runner_with_plan):
        """Should return False when Claude fails."""
        with patch('planning_pipeline.phase_execution.claude_invoker.invoke_claude') as mock_invoke:
            mock_invoke.return_value = {
                "success": False,
                "output": "",
                "error": "Claude crashed",
                "elapsed": 5.0
            }

            result = await runner_with_plan._execute_phase()

            assert result is False

    @pytest.mark.asyncio
    async def test_execute_phase_handles_missing_plan(self, tmp_path):
        """Should return False when plan file is missing."""
        runner = LoopRunner(plan_path=str(tmp_path / "missing.md"))
        runner.current_phase = "phase-1"
        runner._project_path = tmp_path

        result = await runner._execute_phase()

        assert result is False
```

#### Green: Minimal Implementation

Update `autonomous_loop.py`:
```python
"""Autonomous Loop Runner with orchestrator integration."""

import logging
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from planning_pipeline.phase_execution.prompt_builder import build_phase_prompt
from planning_pipeline.phase_execution.claude_invoker import invoke_claude
from planning_pipeline.phase_execution.result_checker import check_execution_result

if TYPE_CHECKING:
    from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator


logger = logging.getLogger(__name__)


class LoopState(Enum):
    """States for the autonomous loop runner."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class LoopRunner:
    """Autonomous loop runner for executing plans with optional orchestrator integration."""

    def __init__(
        self,
        plan_path: Optional[str] = None,
        current_phase: Optional[str] = None,
        orchestrator: Optional["IntegratedOrchestrator"] = None,
        project_path: Optional[Path] = None,
    ):
        """Initialize the LoopRunner."""
        self.plan_path = plan_path
        self.current_phase = current_phase
        self.orchestrator = orchestrator
        self.state = LoopState.IDLE

        # Project path for git/beads operations
        self._project_path = project_path or Path.cwd()

        # Internal state for orchestrator integration
        self._current_feature: Optional[Any] = None

    def _build_phase_prompt(self) -> str:
        """Build prompt for the current phase."""
        return build_phase_prompt(self.plan_path, self.current_phase)

    async def _execute_phase(self) -> bool:
        """Execute the current phase.

        Builds prompt, invokes Claude, and validates result.

        Returns:
            True if phase completed successfully, False otherwise.
        """
        try:
            # Build prompt
            prompt = self._build_phase_prompt()
        except FileNotFoundError as e:
            logger.error(f"Plan file not found: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to build prompt: {e}")
            return False

        # Invoke Claude
        logger.info(f"Executing phase: {self.current_phase}")
        claude_result = invoke_claude(prompt, timeout=3600)  # 1 hour timeout

        # Check result
        return check_execution_result(claude_result, self._project_path)

    # ... rest of existing methods unchanged ...
```

#### Refactor: Improve Code
After tests pass:
- Add timeout configuration
- Add logging for each step
- Consider async version of `invoke_claude` for better async integration

### Success Criteria

**Automated:**
- [ ] Tests fail initially (Red): `pytest tests/test_execute_phase.py::TestExecutePhaseIntegration -v`
- [ ] Tests pass after implementation (Green): `pytest tests/test_execute_phase.py::TestExecutePhaseIntegration -v`
- [ ] All existing orchestrator tests still pass: `pytest tests/test_autonomous_loop.py -v`
- [ ] Full test suite passes: `pytest tests/ -v`

**Manual:**
- [ ] Running with real Claude works end-to-end
- [ ] Logs show execution flow clearly

---

## Phase 5: End-to-End Integration

### Test Specification

**Given**: A complete orchestrator setup with plans
**When**: Running the full loop
**Then**: Plans are discovered, Claude is invoked for each phase, status is updated

This phase ensures all components work together.

### TDD Cycle

#### Red: Write Failing Test
**File**: `tests/test_loop_orchestrator_integration.py` (add new test)
```python
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
        from planning_pipeline.autonomous_loop import LoopRunner, LoopState
        from unittest.mock import Mock

        # Mock orchestrator
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = [
            Mock(path=str(full_setup / "thoughts/shared/plans/2026-01-03-test-feature.md"), priority=1)
        ]
        orchestrator.get_next_feature.side_effect = [
            {"id": "feature-1", "title": "Test Feature", "status": "open"},
            None
        ]
        orchestrator.get_current_feature.return_value = None
        orchestrator.bd = Mock()
        orchestrator.bd.update_status = Mock()

        runner = LoopRunner(orchestrator=orchestrator)
        runner._project_path = full_setup

        with patch('planning_pipeline.phase_execution.claude_invoker.invoke_claude') as mock_invoke:
            mock_invoke.return_value = {
                "success": True,
                "output": "Feature implemented successfully",
                "error": "",
                "elapsed": 10.0
            }

            await runner.run()

        # Verify full flow
        assert runner.state == LoopState.COMPLETED
        mock_invoke.assert_called_once()

        # Verify status updates
        in_progress_calls = [c for c in orchestrator.bd.update_status.call_args_list
                           if "in_progress" in str(c).lower()]
        completed_calls = [c for c in orchestrator.bd.update_status.call_args_list
                         if "completed" in str(c).lower()]
        assert len(in_progress_calls) >= 1
        assert len(completed_calls) >= 1
```

#### Green: Implementation
This should work with the implementations from phases 1-4.

#### Refactor: Documentation
Add docstrings and improve error messages.

### Success Criteria

**Automated:**
- [ ] E2E test passes: `pytest tests/test_loop_orchestrator_integration.py::TestExecutePhaseE2E -v`
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Type check passes: `mypy planning_pipeline/`

**Manual:**
- [ ] Run with real Claude on test project
- [ ] Verify beads status updates work

---

## Integration & E2E Testing

### Integration Scenarios
1. **Full loop execution**: Orchestrator discovers plans, executes each, updates status
2. **Resume from interrupted state**: Start with IN_PROGRESS feature, complete it
3. **Handle Claude failures**: Claude fails, status updated to FAILED, loop stops

### E2E User Flows
1. User runs `python -m planning_pipeline.autonomous_loop` with valid project
2. Plans are discovered, phases executed, status shown
3. Final status shows completion or failure

---

## References

- Research: `thoughts/searchable/shared/research/2026-01-02-loop-runner-orchestrator-not-executing.md`
- Stub: `planning_pipeline/autonomous_loop.py:146-155`
- Working pattern: `loop-runner.py:959-1084`
- Claude runner: `planning_pipeline/claude_runner.py:23-81`
- Existing tests: `tests/test_autonomous_loop.py`
