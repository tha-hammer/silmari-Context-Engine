# Planning Orchestrator TDD Implementation Plan

## Overview

Create a CLI entry point (`planning_orchestrator.py`) at the project root to run the planning pipeline. The orchestrator accepts a multi-line research prompt interactively and executes the full 5-step planning pipeline.

## Current State Analysis

### Existing Components:
- `planning_pipeline/pipeline.py:12` - `PlanningPipeline` class with `.run()` method
- `planning_pipeline/steps.py` - Individual step functions
- `planning_pipeline/checkpoints.py` - Interactive checkpoints
- `planning_pipeline/claude_runner.py:8` - `run_claude_sync()` for Claude CLI calls
- `planning_pipeline/beads_controller.py:9` - BeadsController for issue management

### Existing Patterns to Follow:
- `orchestrator.py:148-173` - Color output utilities (`Colors` class)
- `orchestrator.py:329-381` - Interactive prompts with multi-line input
- `loop-runner.py:1-50` - argparse setup with examples in epilog
- `planning_pipeline/claude_runner.py:35-74` - Subprocess error handling

### Key Discoveries:
- Multi-line input pattern at `orchestrator.py:370-381`: loop until empty line
- Prerequisite check pattern at `orchestrator.py:175-178`: `subprocess.run(["which", "claude"])`
- Color class reusable from existing codebase

## Desired End State

A CLI tool that:
```bash
python planning_orchestrator.py                    # Interactive mode
python planning_orchestrator.py --project ~/app    # Specify project
python planning_orchestrator.py --ticket AUTH-001  # With ticket ID
python planning_orchestrator.py --auto-approve     # Skip interactive checkpoints
```

### Observable Behaviors:
1. Given no arguments, prompts for multi-line research input
2. Given `--project` path, uses that as project root
3. Given `--ticket` ID, passes to pipeline for tracking
4. Given `--auto-approve`, skips interactive checkpoints
5. Given missing `claude` CLI, exits with error code 1
6. Given missing `bd` CLI, exits with error code 1
7. Given successful pipeline run, exits with code 0
8. Given failed pipeline run, exits with code 1 and shows error

## What We're NOT Doing

- Individual step execution (only full pipeline)
- Resume/checkpoint functionality
- Configuration file support
- Model selection (uses default)

## Testing Strategy

- **Framework**: pytest with real SDK calls
- **Test Types**:
  - Unit: CLI parsing, prompt collection, prerequisite checks
  - Integration: Full pipeline execution with real Claude calls
- **Markers**: `@pytest.mark.slow` for Claude-calling tests
- **Cleanup**: Tests create real beads issues, must clean up after

## Behavior 1: CLI Argument Parsing

### Test Specification
**Given**: Command line arguments `--project /path --ticket ABC-123 --auto-approve`
**When**: `parse_args()` is called
**Then**: Returns namespace with `project=/path`, `ticket=ABC-123`, `auto_approve=True`

**Edge Cases**:
- No arguments (defaults)
- Only `--project`
- Invalid path (handled later at validation)

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_orchestrator.py`
```python
"""Tests for planning_orchestrator CLI."""

import pytest
import sys
from pathlib import Path


class TestCLIArgumentParsing:
    """Behavior 1: CLI parses arguments correctly."""

    def test_parses_project_path(self):
        """Given --project flag, parses project path."""
        from planning_orchestrator import parse_args

        args = parse_args(["--project", "/tmp/myproject"])
        assert args.project == Path("/tmp/myproject")

    def test_parses_ticket_id(self):
        """Given --ticket flag, parses ticket ID."""
        from planning_orchestrator import parse_args

        args = parse_args(["--ticket", "AUTH-001"])
        assert args.ticket == "AUTH-001"

    def test_parses_auto_approve_flag(self):
        """Given --auto-approve flag, sets auto_approve to True."""
        from planning_orchestrator import parse_args

        args = parse_args(["--auto-approve"])
        assert args.auto_approve is True

    def test_defaults_project_to_cwd(self):
        """Given no --project, defaults to current working directory."""
        from planning_orchestrator import parse_args

        args = parse_args([])
        assert args.project == Path.cwd()

    def test_defaults_auto_approve_to_false(self):
        """Given no --auto-approve, defaults to False."""
        from planning_orchestrator import parse_args

        args = parse_args([])
        assert args.auto_approve is False

    def test_defaults_ticket_to_none(self):
        """Given no --ticket, defaults to None."""
        from planning_orchestrator import parse_args

        args = parse_args([])
        assert args.ticket is None
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_orchestrator.py`
```python
#!/usr/bin/env python3
"""
Planning Pipeline Orchestrator
==============================
CLI entry point for running the planning pipeline.

Usage:
    python planning_orchestrator.py                    # Interactive mode
    python planning_orchestrator.py --project ~/app    # Specify project
    python planning_orchestrator.py --ticket AUTH-001  # With ticket ID
    python planning_orchestrator.py --auto-approve     # Skip checkpoints
"""

import argparse
from pathlib import Path


def parse_args(args: list[str] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Planning Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python planning_orchestrator.py                    # Interactive prompt
  python planning_orchestrator.py --project ~/app    # Specify project path
  python planning_orchestrator.py --ticket AUTH-001  # Track with ticket ID
  python planning_orchestrator.py --auto-approve     # Skip interactive steps
        """
    )

    parser.add_argument(
        "--project", "-p",
        type=Path,
        default=Path.cwd(),
        help="Project path (default: current directory)"
    )
    parser.add_argument(
        "--ticket", "-t",
        type=str,
        default=None,
        help="Ticket ID for tracking"
    )
    parser.add_argument(
        "--auto-approve", "-y",
        action="store_true",
        help="Skip interactive checkpoints"
    )

    return parser.parse_args(args)
```

#### 🔵 Refactor: Improve Code
No refactoring needed for this behavior.

### Success Criteria
**Automated:**
- [ ] Test fails for right reason (Red): `python -m pytest planning_pipeline/tests/test_orchestrator.py::TestCLIArgumentParsing -v`
- [ ] Test passes (Green): `python -m pytest planning_pipeline/tests/test_orchestrator.py::TestCLIArgumentParsing -v`
- [ ] All tests pass after refactor: `python -m pytest planning_pipeline/tests/ -v -m "not slow"`

---

## Behavior 2: Multi-line Prompt Collection

### Test Specification
**Given**: User enters multiple lines followed by blank line
**When**: `collect_prompt()` is called
**Then**: Returns joined string of all lines

**Edge Cases**:
- Single line then blank
- Multiple lines with empty lines in between (should stop at first blank)

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_orchestrator.py`
```python
class TestMultilinePromptCollection:
    """Behavior 2: Collects multi-line prompt from user."""

    def test_collects_single_line(self, monkeypatch):
        """Given single line then blank, returns that line."""
        from planning_orchestrator import collect_prompt

        inputs = iter(["How does auth work?", ""])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        result = collect_prompt()
        assert result == "How does auth work?"

    def test_collects_multiple_lines(self, monkeypatch):
        """Given multiple lines then blank, returns joined lines."""
        from planning_orchestrator import collect_prompt

        inputs = iter([
            "Research the authentication system.",
            "Focus on JWT token handling.",
            "Include security considerations.",
            ""
        ])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        result = collect_prompt()
        expected = "Research the authentication system.\nFocus on JWT token handling.\nInclude security considerations."
        assert result == expected

    def test_stops_at_first_blank_line(self, monkeypatch):
        """Given blank line, stops collecting."""
        from planning_orchestrator import collect_prompt

        inputs = iter(["Line one", "", "Line three (should not be included)"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        result = collect_prompt()
        assert result == "Line one"
        assert "Line three" not in result
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_orchestrator.py` (add to existing)
```python
def collect_prompt() -> str:
    """Collect multi-line research prompt from user.

    Reads lines until user enters a blank line.

    Returns:
        Joined string of all input lines.
    """
    print("\nEnter your research prompt (blank line to finish):")
    print("-" * 40)

    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)

    return "\n".join(lines)
```

#### 🔵 Refactor: Improve Code
No refactoring needed.

### Success Criteria
**Automated:**
- [ ] Test fails for right reason (Red)
- [ ] Test passes (Green)
- [ ] All tests pass after refactor

---

## Behavior 3: Prerequisite Validation

### Test Specification
**Given**: `claude` CLI is not installed
**When**: `check_prerequisites()` is called
**Then**: Returns `{"success": False, "error": "claude command not found"}`

**Given**: `bd` CLI is not installed
**When**: `check_prerequisites()` is called
**Then**: Returns `{"success": False, "error": "bd command not found"}`

**Given**: Both CLIs are installed
**When**: `check_prerequisites()` is called
**Then**: Returns `{"success": True}`

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_orchestrator.py`
```python
import subprocess


class TestPrerequisiteValidation:
    """Behavior 3: Validates required CLI tools are installed."""

    def test_succeeds_when_both_installed(self):
        """Given both claude and bd installed, returns success."""
        from planning_orchestrator import check_prerequisites

        # This test assumes the test environment has both tools
        result = check_prerequisites()
        assert result["success"] is True

    def test_fails_when_claude_missing(self, monkeypatch):
        """Given claude not installed, returns error."""
        from planning_orchestrator import check_prerequisites

        original_run = subprocess.run

        def mock_run(cmd, *args, **kwargs):
            if cmd[0] == "which" and cmd[1] == "claude":
                result = type('Result', (), {'returncode': 1})()
                return result
            return original_run(cmd, *args, **kwargs)

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = check_prerequisites()
        assert result["success"] is False
        assert "claude" in result["error"]

    def test_fails_when_bd_missing(self, monkeypatch):
        """Given bd not installed, returns error."""
        from planning_orchestrator import check_prerequisites

        original_run = subprocess.run

        def mock_run(cmd, *args, **kwargs):
            if cmd[0] == "which" and cmd[1] == "bd":
                result = type('Result', (), {'returncode': 1})()
                return result
            return original_run(cmd, *args, **kwargs)

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = check_prerequisites()
        assert result["success"] is False
        assert "bd" in result["error"]
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_orchestrator.py` (add to existing)
```python
import subprocess


def check_prerequisites() -> dict[str, any]:
    """Check that required CLI tools are installed.

    Returns:
        Dictionary with 'success' bool and optional 'error' message.
    """
    # Check claude CLI
    result = subprocess.run(["which", "claude"], capture_output=True)
    if result.returncode != 0:
        return {"success": False, "error": "claude command not found. Install from: https://docs.anthropic.com/claude-code"}

    # Check bd CLI
    result = subprocess.run(["which", "bd"], capture_output=True)
    if result.returncode != 0:
        return {"success": False, "error": "bd command not found. Install beads CLI."}

    return {"success": True}
```

#### 🔵 Refactor: Improve Code
No refactoring needed.

### Success Criteria
**Automated:**
- [ ] Test fails for right reason (Red)
- [ ] Test passes (Green)
- [ ] All tests pass after refactor

---

## Behavior 4: Pipeline Execution with Real SDK

### Test Specification
**Given**: Valid project path and research prompt
**When**: `run_pipeline()` is called with real SDK
**Then**: Executes pipeline and returns result dictionary

This is a slow integration test that makes actual Claude API calls.

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_orchestrator.py`
```python
@pytest.mark.slow
class TestPipelineExecution:
    """Behavior 4: Executes pipeline with real SDK calls."""

    @pytest.fixture
    def project_path(self):
        """Return the root project path."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def cleanup_issues(self, project_path):
        """Track and cleanup created issues after test."""
        from planning_pipeline import BeadsController
        bd = BeadsController(project_path)
        created_ids = []
        yield created_ids
        for issue_id in created_ids:
            bd.close_issue(issue_id, reason="Test cleanup")
        bd.sync()

    def test_runs_pipeline_with_auto_approve(self, project_path, cleanup_issues):
        """Given valid prompt with auto-approve, executes full pipeline."""
        from planning_orchestrator import run_pipeline

        result = run_pipeline(
            project_path=project_path,
            prompt="What is the project structure? List main directories only.",
            ticket_id="TEST-ORCH-001",
            auto_approve=True
        )

        assert result["success"] is True
        assert "plan_dir" in result
        assert result.get("epic_id") is not None

        # Track for cleanup
        if result.get("epic_id"):
            cleanup_issues.append(result["epic_id"])
        for phase in result.get("steps", {}).get("beads", {}).get("phase_issues", []):
            if phase.get("issue_id"):
                cleanup_issues.append(phase["issue_id"])

    def test_returns_failure_on_empty_prompt(self, project_path):
        """Given empty prompt, returns failure without calling SDK."""
        from planning_orchestrator import run_pipeline

        result = run_pipeline(
            project_path=project_path,
            prompt="",
            ticket_id=None,
            auto_approve=True
        )

        assert result["success"] is False
        assert "error" in result
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_orchestrator.py` (add to existing)
```python
from planning_pipeline import PlanningPipeline


def run_pipeline(
    project_path: Path,
    prompt: str,
    ticket_id: str = None,
    auto_approve: bool = False
) -> dict:
    """Run the planning pipeline.

    Args:
        project_path: Root path of the project
        prompt: Research prompt
        ticket_id: Optional ticket ID for tracking
        auto_approve: Skip interactive checkpoints if True

    Returns:
        Pipeline result dictionary.
    """
    if not prompt or not prompt.strip():
        return {"success": False, "error": "Research prompt cannot be empty"}

    pipeline = PlanningPipeline(project_path)

    return pipeline.run(
        research_prompt=prompt,
        ticket_id=ticket_id,
        auto_approve=auto_approve
    )
```

#### 🔵 Refactor: Improve Code
No refactoring needed.

### Success Criteria
**Automated:**
- [ ] Test fails for right reason (Red)
- [ ] Test passes (Green): `python -m pytest planning_pipeline/tests/test_orchestrator.py::TestPipelineExecution -v`
- [ ] All tests pass after refactor

**Manual:**
- [ ] Beads issues created and visible with `bd list`
- [ ] Research document created in `thoughts/shared/research/`
- [ ] Plan files created in `thoughts/shared/plans/`

---

## Behavior 5: Result Display

### Test Specification
**Given**: Successful pipeline result
**When**: `display_result()` is called
**Then**: Prints success message with plan directory and epic ID

**Given**: Failed pipeline result
**When**: `display_result()` is called
**Then**: Prints error message with failure details

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_orchestrator.py`
```python
class TestResultDisplay:
    """Behavior 5: Displays pipeline results to user."""

    def test_displays_success_result(self, capsys):
        """Given successful result, displays plan dir and epic ID."""
        from planning_orchestrator import display_result

        result = {
            "success": True,
            "plan_dir": "thoughts/shared/plans/2026-01-01-plan",
            "epic_id": "beads-abc123"
        }

        display_result(result)

        captured = capsys.readouterr()
        assert "SUCCESS" in captured.out or "success" in captured.out.lower()
        assert "thoughts/shared/plans/2026-01-01-plan" in captured.out
        assert "beads-abc123" in captured.out

    def test_displays_failure_result(self, capsys):
        """Given failed result, displays error message."""
        from planning_orchestrator import display_result

        result = {
            "success": False,
            "failed_at": "research",
            "steps": {
                "research": {"error": "Claude timed out"}
            }
        }

        display_result(result)

        captured = capsys.readouterr()
        assert "FAILED" in captured.out or "failed" in captured.out.lower()
        assert "research" in captured.out.lower()

    def test_displays_stopped_result(self, capsys):
        """Given user-stopped result, displays stopped message."""
        from planning_orchestrator import display_result

        result = {
            "success": False,
            "stopped_at": "planning"
        }

        display_result(result)

        captured = capsys.readouterr()
        assert "stopped" in captured.out.lower() or "cancelled" in captured.out.lower()
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_orchestrator.py` (add to existing)
```python
class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    END = '\033[0m'


def display_result(result: dict) -> None:
    """Display pipeline result to user.

    Args:
        result: Pipeline result dictionary
    """
    print("\n" + "=" * 60)

    if result.get("success"):
        print(f"{Colors.GREEN}{Colors.BOLD}PIPELINE SUCCESS{Colors.END}")
        print("=" * 60)
        print(f"\nPlan directory: {result.get('plan_dir', 'N/A')}")
        print(f"Epic ID: {result.get('epic_id', 'N/A')}")
        print("\nNext steps:")
        print("  1. Review plan files in the plan directory")
        print("  2. Check beads issues with: bd list --status=open")
        print("  3. Begin implementation using phase files as guides")
    else:
        print(f"{Colors.RED}{Colors.BOLD}PIPELINE FAILED{Colors.END}")
        print("=" * 60)

        if result.get("stopped_at"):
            print(f"\nPipeline stopped by user at: {result['stopped_at']}")
        elif result.get("failed_at"):
            step = result["failed_at"]
            error = result.get("steps", {}).get(step, {}).get("error", "Unknown error")
            print(f"\nFailed at step: {step}")
            print(f"Error: {error}")
        else:
            print(f"\nError: {result.get('error', 'Unknown error')}")
```

#### 🔵 Refactor: Improve Code
No refactoring needed.

### Success Criteria
**Automated:**
- [ ] Test fails for right reason (Red)
- [ ] Test passes (Green)
- [ ] All tests pass after refactor

---

## Behavior 6: Exit Code Handling

### Test Specification
**Given**: Successful pipeline run
**When**: `main()` completes
**Then**: Process exits with code 0

**Given**: Failed pipeline run
**When**: `main()` completes
**Then**: Process exits with code 1

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_orchestrator.py`
```python
class TestExitCodeHandling:
    """Behavior 6: Returns proper exit codes."""

    def test_returns_zero_on_success(self, monkeypatch):
        """Given successful pipeline, returns exit code 0."""
        from planning_orchestrator import get_exit_code

        result = {"success": True}
        assert get_exit_code(result) == 0

    def test_returns_one_on_failure(self, monkeypatch):
        """Given failed pipeline, returns exit code 1."""
        from planning_orchestrator import get_exit_code

        result = {"success": False}
        assert get_exit_code(result) == 1

    def test_returns_one_on_stopped(self, monkeypatch):
        """Given user-stopped pipeline, returns exit code 1."""
        from planning_orchestrator import get_exit_code

        result = {"success": False, "stopped_at": "research"}
        assert get_exit_code(result) == 1
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_orchestrator.py` (add to existing)
```python
def get_exit_code(result: dict) -> int:
    """Get exit code based on pipeline result.

    Args:
        result: Pipeline result dictionary

    Returns:
        0 for success, 1 for failure
    """
    return 0 if result.get("success") else 1
```

#### 🔵 Refactor: Improve Code
No refactoring needed.

### Success Criteria
**Automated:**
- [ ] Test fails for right reason (Red)
- [ ] Test passes (Green)
- [ ] All tests pass after refactor

---

## Behavior 7: Main Entry Point

### Test Specification
**Given**: Script run with `python planning_orchestrator.py --auto-approve`
**When**: Main entry point executes
**Then**: Parses args, checks prerequisites, collects prompt (if needed), runs pipeline, displays result, exits

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_orchestrator.py`
```python
@pytest.mark.slow
class TestMainEntryPoint:
    """Behavior 7: Main function integrates all components."""

    @pytest.fixture
    def project_path(self):
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def cleanup_issues(self, project_path):
        from planning_pipeline import BeadsController
        bd = BeadsController(project_path)
        created_ids = []
        yield created_ids
        for issue_id in created_ids:
            bd.close_issue(issue_id, reason="Test cleanup")
        bd.sync()

    def test_main_with_prompt_flag(self, project_path, cleanup_issues, monkeypatch, capsys):
        """Given --prompt-text flag, runs without interactive input."""
        import sys
        from planning_orchestrator import main

        # Use --prompt-text for non-interactive testing
        test_args = [
            "planning_orchestrator.py",
            "--project", str(project_path),
            "--prompt-text", "List the main Python files in this project.",
            "--ticket", "TEST-MAIN-001",
            "--auto-approve"
        ]
        monkeypatch.setattr(sys, "argv", test_args)

        exit_code = main()

        captured = capsys.readouterr()
        # Should complete (success or failure, but no crash)
        assert exit_code in [0, 1]
        assert "PIPELINE" in captured.out
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_orchestrator.py` (complete file)
```python
#!/usr/bin/env python3
"""
Planning Pipeline Orchestrator
==============================
CLI entry point for running the planning pipeline.

Usage:
    python planning_orchestrator.py                    # Interactive mode
    python planning_orchestrator.py --project ~/app    # Specify project
    python planning_orchestrator.py --ticket AUTH-001  # With ticket ID
    python planning_orchestrator.py --auto-approve     # Skip checkpoints
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

from planning_pipeline import PlanningPipeline


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def parse_args(args: list[str] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Planning Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python planning_orchestrator.py                    # Interactive prompt
  python planning_orchestrator.py --project ~/app    # Specify project path
  python planning_orchestrator.py --ticket AUTH-001  # Track with ticket ID
  python planning_orchestrator.py --auto-approve     # Skip interactive steps
        """
    )

    parser.add_argument(
        "--project", "-p",
        type=Path,
        default=Path.cwd(),
        help="Project path (default: current directory)"
    )
    parser.add_argument(
        "--ticket", "-t",
        type=str,
        default=None,
        help="Ticket ID for tracking"
    )
    parser.add_argument(
        "--auto-approve", "-y",
        action="store_true",
        help="Skip interactive checkpoints"
    )
    parser.add_argument(
        "--prompt-text",
        type=str,
        default=None,
        help="Research prompt (non-interactive mode)"
    )

    return parser.parse_args(args)


def collect_prompt() -> str:
    """Collect multi-line research prompt from user."""
    print(f"\n{Colors.BOLD}Enter your research prompt:{Colors.END}")
    print("(Describe what you want to research. Blank line to finish.)")
    print("-" * 40)

    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)

    return "\n".join(lines)


def check_prerequisites() -> dict[str, Any]:
    """Check that required CLI tools are installed."""
    result = subprocess.run(["which", "claude"], capture_output=True)
    if result.returncode != 0:
        return {
            "success": False,
            "error": "claude command not found. Install from: https://docs.anthropic.com/claude-code"
        }

    result = subprocess.run(["which", "bd"], capture_output=True)
    if result.returncode != 0:
        return {
            "success": False,
            "error": "bd command not found. Install beads CLI."
        }

    return {"success": True}


def run_pipeline(
    project_path: Path,
    prompt: str,
    ticket_id: str = None,
    auto_approve: bool = False
) -> dict:
    """Run the planning pipeline."""
    if not prompt or not prompt.strip():
        return {"success": False, "error": "Research prompt cannot be empty"}

    pipeline = PlanningPipeline(project_path)

    return pipeline.run(
        research_prompt=prompt,
        ticket_id=ticket_id,
        auto_approve=auto_approve
    )


def display_result(result: dict) -> None:
    """Display pipeline result to user."""
    print("\n" + "=" * 60)

    if result.get("success"):
        print(f"{Colors.GREEN}{Colors.BOLD}PIPELINE SUCCESS{Colors.END}")
        print("=" * 60)
        print(f"\nPlan directory: {result.get('plan_dir', 'N/A')}")
        print(f"Epic ID: {result.get('epic_id', 'N/A')}")
        print("\nNext steps:")
        print("  1. Review plan files in the plan directory")
        print("  2. Check beads issues with: bd list --status=open")
        print("  3. Begin implementation using phase files as guides")
    else:
        print(f"{Colors.RED}{Colors.BOLD}PIPELINE FAILED{Colors.END}")
        print("=" * 60)

        if result.get("stopped_at"):
            print(f"\nPipeline stopped by user at: {result['stopped_at']}")
        elif result.get("failed_at"):
            step = result["failed_at"]
            error = result.get("steps", {}).get(step, {}).get("error", "Unknown error")
            print(f"\nFailed at step: {step}")
            print(f"Error: {error}")
        else:
            print(f"\nError: {result.get('error', 'Unknown error')}")


def get_exit_code(result: dict) -> int:
    """Get exit code based on pipeline result."""
    return 0 if result.get("success") else 1


def main() -> int:
    """Main entry point."""
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{'Planning Pipeline Orchestrator':^60}{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.END}")

    # Parse arguments
    args = parse_args()
    project_path = args.project.expanduser().resolve()

    print(f"\nProject: {project_path}")
    if args.ticket:
        print(f"Ticket: {args.ticket}")

    # Check prerequisites
    prereq = check_prerequisites()
    if not prereq["success"]:
        print(f"\n{Colors.RED}Error: {prereq['error']}{Colors.END}")
        return 1

    # Get prompt
    if args.prompt_text:
        prompt = args.prompt_text
    else:
        prompt = collect_prompt()

    if not prompt.strip():
        print(f"\n{Colors.RED}Error: Research prompt cannot be empty{Colors.END}")
        return 1

    print(f"\n{Colors.CYAN}Starting pipeline...{Colors.END}")

    # Run pipeline
    result = run_pipeline(
        project_path=project_path,
        prompt=prompt,
        ticket_id=args.ticket,
        auto_approve=args.auto_approve
    )

    # Display result
    display_result(result)

    return get_exit_code(result)


if __name__ == "__main__":
    sys.exit(main())
```

#### 🔵 Refactor: Improve Code
Consider extracting header printing to separate function if needed.

### Success Criteria
**Automated:**
- [ ] Test fails for right reason (Red)
- [ ] Test passes (Green): `python -m pytest planning_pipeline/tests/test_orchestrator.py -v`
- [ ] All tests pass: `python -m pytest planning_pipeline/tests/ -v`

**Manual:**
- [ ] `python planning_orchestrator.py --help` shows usage
- [ ] Interactive mode prompts for multi-line input
- [ ] `--auto-approve` skips checkpoints
- [ ] Exit code 0 on success, 1 on failure

---

## Integration Test: Full E2E with Real SDK

### Test Specification
**Given**: Real project with beads initialized
**When**: Full pipeline executed via orchestrator
**Then**: Creates research doc, plan, phases, and beads issues

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_orchestrator.py`
```python
@pytest.mark.slow
@pytest.mark.integration
class TestOrchestratorE2E:
    """Full end-to-end integration tests with real SDK calls."""

    @pytest.fixture
    def project_path(self):
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def cleanup_issues(self, project_path):
        from planning_pipeline import BeadsController
        bd = BeadsController(project_path)
        created_ids = []
        yield created_ids
        for issue_id in created_ids:
            bd.close_issue(issue_id, reason="Test cleanup")
        bd.sync()

    def test_full_pipeline_creates_artifacts(self, project_path, cleanup_issues):
        """Given real SDK, creates all expected artifacts."""
        from planning_orchestrator import run_pipeline

        result = run_pipeline(
            project_path=project_path,
            prompt="Analyze the testing patterns in this project. Focus on pytest fixtures.",
            ticket_id="TEST-E2E-001",
            auto_approve=True
        )

        assert result["success"] is True

        # Verify plan directory exists
        plan_dir = result.get("plan_dir")
        assert plan_dir is not None
        assert Path(plan_dir).exists()

        # Verify phase files created
        phase_files = result.get("steps", {}).get("decomposition", {}).get("phase_files", [])
        assert len(phase_files) > 0
        for phase_file in phase_files:
            assert Path(phase_file).exists()

        # Verify beads issues created
        epic_id = result.get("epic_id")
        assert epic_id is not None
        cleanup_issues.append(epic_id)

        phase_issues = result.get("steps", {}).get("beads", {}).get("phase_issues", [])
        for phase in phase_issues:
            if phase.get("issue_id"):
                cleanup_issues.append(phase["issue_id"])
```

#### 🟢 Green: Minimal Implementation
Already implemented in Behavior 7.

### Success Criteria
**Automated:**
- [ ] `python -m pytest planning_pipeline/tests/test_orchestrator.py::TestOrchestratorE2E -v`
- [ ] All artifacts verified to exist
- [ ] Cleanup successful

**Manual:**
- [ ] `bd list` shows created issues
- [ ] Research doc readable in `thoughts/shared/research/`
- [ ] Plan files have proper structure

---

## References

- Documentation: `thoughts/shared/docs/2025-12-31-how-to-run-planning-pipeline.md`
- Pipeline class: `planning_pipeline/pipeline.py:12`
- Existing orchestrator pattern: `orchestrator.py:1-1367`
- Test fixtures: `planning_pipeline/tests/conftest.py`
