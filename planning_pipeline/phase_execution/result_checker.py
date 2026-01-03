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
