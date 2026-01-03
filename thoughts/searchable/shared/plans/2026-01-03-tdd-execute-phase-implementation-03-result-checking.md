# Phase 3: Result Checking

## Overview

Create a function to validate Claude execution results by checking return codes, git changes, and running beads sync. This determines whether a phase execution was successful.

## Dependencies

### Requires
- Phase 2: Claude Invocation (provides the result dict to check)

### Blocks
- Phase 4: Full Integration

## Changes Required

### New Files

**File**: `planning_pipeline/phase_execution/result_checker.py:1-70`
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

### Test File

**File**: `tests/test_execute_phase.py` (append to existing)
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
            # Mock git status to return changes
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="M file.py")

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
                cmd = args[0] if args else kwargs.get('args', [])
                if "bd" in cmd:
                    raise FileNotFoundError("bd not found")
                return MagicMock(returncode=0, stdout="M file.py")
            mock_sub.run.side_effect = side_effect

            from planning_pipeline.phase_execution.result_checker import check_execution_result

            # Should still succeed without beads
            result = check_execution_result(
                claude_result={"success": True, "output": "done", "error": "", "elapsed": 5.0},
                project_path=temp_git_repo
            )

            assert result is True

    def test_check_result_success_without_changes(self, temp_git_repo):
        """Should return True even without git changes if Claude succeeded."""
        from planning_pipeline.phase_execution.result_checker import check_execution_result

        # No new files, no changes
        result = check_execution_result(
            claude_result={"success": True, "output": "done", "error": "", "elapsed": 5.0},
            project_path=temp_git_repo
        )

        # Still True because Claude succeeded (might be no-op phase)
        assert result is True
```

## Success Criteria

### Automated
- [ ] Tests fail initially (Red): `pytest tests/test_execute_phase.py::TestResultChecking -v`
- [ ] Tests pass after implementation (Green): `pytest tests/test_execute_phase.py::TestResultChecking -v`
- [ ] All tests pass: `pytest tests/ -v`

### Manual
- [ ] In a git repo, make a change and verify `_check_git_changes()` returns True
- [ ] Verify `bd sync` is called in a beads-enabled project
- [ ] Verify graceful handling when `bd` command is not installed

## Human-Testable Function

After completing this phase, the following function is ready for manual testing:

```python
from pathlib import Path
from planning_pipeline.phase_execution.result_checker import check_execution_result

# Test in your project directory
result = check_execution_result(
    claude_result={"success": True, "output": "test", "error": "", "elapsed": 1.0},
    project_path=Path.cwd()
)
print(f"Result check passed: {result}")
```

Expected output: `True` if Claude result shows success, `False` otherwise. bd sync runs if available.
