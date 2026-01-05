# Phase 10: Implementation Phase TDD Plan

## Overview

Implement the autonomous implementation phase that executes TDD cycles for each phase document, supporting three execution modes.

## Testable Behaviors

### Behavior 1: Load Phase Document
**Given**: Phase document path
**When**: Starting implementation
**Then**: Document content loaded

### Behavior 2: Execute TDD Cycle
**Given**: Phase with behaviors
**When**: Running implementation
**Then**: Red-Green-Refactor executed

### Behavior 3: Run Tests After Each Cycle
**Given**: Implementation complete
**When**: Verifying
**Then**: Test suite executed

### Behavior 4: Checkpoint Mode - Pause at Each Phase
**Given**: Checkpoint mode selected
**When**: Phase completes
**Then**: Pauses for user review

### Behavior 5: Autonomous Mode - Run All Phases
**Given**: Autonomous mode selected
**When**: Running
**Then**: All phases executed without stopping

### Behavior 6: Batch Mode - Group Phases
**Given**: Batch mode selected
**When**: Running
**Then**: Groups executed, pause between groups

### Behavior 7: Store Results in CWA
**Given**: Implementation results
**When**: Phase completes
**Then**: COMMAND_RESULT entries created

### Behavior 8: Update Beads Status
**Given**: Phase implemented
**When**: Tests pass
**Then**: Beads issue closed

### Behavior 9: Handle Implementation Failure
**Given**: Tests fail
**When**: Error detected
**Then**: Stops and reports error

### Behavior 10: Manage Context Bounds
**Given**: Many entries in context
**When**: Building impl context
**Then**: Respects <200 entry limit

### Behavior 11: Resume from Checkpoint
**Given**: Checkpoint exists
**When**: Resuming
**Then**: Continues from last phase

### Behavior 12: Create Commit After Phase
**Given**: Successful phase
**When**: Mode allows
**Then**: Git commit created

---

## TDD Cycle: Behavior 1-2 - Load and Execute

### 🔴 Red: Write Failing Tests

**File**: `silmari-rlm-act/tests/test_implementation_phase.py`
```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from silmari_rlm_act.phases.implementation import ImplementationPhase
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import AutonomyMode


class TestLoadPhaseDocument:
    """Behavior 1: Load Phase Document."""

    def test_loads_document_content(self, tmp_path):
        """Given path, loads content."""
        phase_doc = tmp_path / "01-login.md"
        phase_doc.write_text("# Phase 1: Login\n\n## Requirements...")

        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        content = phase._load_phase_document(str(phase_doc))

        assert "Login" in content
        assert "Requirements" in content

    def test_extracts_behaviors(self, tmp_path):
        """Given document, extracts behaviors."""
        phase_doc = tmp_path / "01-login.md"
        phase_doc.write_text("""# Phase 1: Login

## Testable Behaviors

1. Given valid creds, when login, then authenticated
2. Given invalid creds, when login, then error shown
""")

        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        behaviors = phase._extract_behaviors(str(phase_doc))

        assert len(behaviors) == 2
        assert "valid creds" in behaviors[0]


class TestExecuteTDDCycle:
    """Behavior 2: Execute TDD Cycle."""

    def test_invokes_claude_for_implementation(self, tmp_path):
        """Given behavior, invokes Claude."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        mock_runner = Mock()
        mock_runner.run_sync.return_value = {
            "success": True,
            "output": "Implemented test and code"
        }

        with patch.object(phase, '_runner', mock_runner):
            result = phase._execute_tdd_cycle(
                behavior="Given valid creds, when login, then authenticated",
                phase_context="# Phase 1: Login"
            )

        mock_runner.run_sync.assert_called_once()
        assert result["success"] is True
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/phases/implementation.py`
```python
"""Implementation phase implementation."""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Callable
from silmari_rlm_act.models import PhaseResult, AutonomyMode
from silmari_rlm_act.context.cwa_integration import CWAIntegration


class ImplementationPhase:
    """Execute TDD implementation for plan phases."""

    IMPLEMENTATION_TIMEOUT = 600  # 10 minutes per behavior
    TEST_TIMEOUT = 120  # 2 minutes for test runs

    def __init__(
        self,
        project_path: Path,
        cwa: CWAIntegration,
    ):
        self.project_path = Path(project_path)
        self.cwa = cwa
        self._runner = None  # Claude runner
        self._beads_controller = None  # Beads controller

    def _load_phase_document(self, phase_path: str) -> str:
        """Load phase document content."""
        path = Path(phase_path)
        if not path.is_absolute():
            path = self.project_path / path
        return path.read_text()

    def _extract_behaviors(self, phase_path: str) -> List[str]:
        """Extract testable behaviors from phase document.

        Args:
            phase_path: Path to phase document

        Returns:
            List of behavior strings
        """
        content = self._load_phase_document(phase_path)

        behaviors = []

        # Look for numbered list under "Testable Behaviors"
        in_behaviors = False
        for line in content.split("\n"):
            if "Testable Behaviors" in line:
                in_behaviors = True
                continue
            if in_behaviors:
                if line.strip().startswith(("#", "##")):
                    break
                match = re.match(r"\d+\.\s+(.+)", line.strip())
                if match:
                    behaviors.append(match.group(1))

        return behaviors

    def _execute_tdd_cycle(
        self,
        behavior: str,
        phase_context: str
    ) -> Dict:
        """Execute Red-Green-Refactor cycle for a behavior.

        Args:
            behavior: The behavior to implement
            phase_context: Context from phase document

        Returns:
            Dict with success status and output
        """
        prompt = self._build_implementation_prompt(behavior, phase_context)

        try:
            result = self._runner.run_sync(
                prompt,
                timeout=self.IMPLEMENTATION_TIMEOUT
            )
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _build_implementation_prompt(self, behavior: str, context: str) -> str:
        """Build prompt for TDD implementation."""
        return f"""Implement the following behavior using TDD (Red-Green-Refactor):

## Behavior
{behavior}

## Context
{context}

## Instructions
1. **Red**: Write a failing test for this behavior
2. **Green**: Write minimal code to make the test pass
3. **Refactor**: Clean up the code while keeping tests green

After each step, run the tests to verify.
"""
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_implementation_phase.py::TestLoadPhaseDocument -v`
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_implementation_phase.py::TestExecuteTDDCycle -v`

---

## TDD Cycle: Behavior 3-6 - Test Running and Modes

### 🔴 Red: Write Failing Tests

**File**: `silmari-rlm-act/tests/test_implementation_phase.py`
```python
class TestRunTests:
    """Behavior 3: Run Tests After Each Cycle."""

    def test_runs_test_suite(self, tmp_path):
        """Given implementation, runs tests."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="5 passed")

            passed, output = phase._run_tests()

        assert passed is True
        assert "passed" in output


class TestAutonomyModes:
    """Behavior 4-6: Autonomy Modes."""

    def test_checkpoint_mode_pauses(self, tmp_path):
        """Given checkpoint mode, pauses after each phase."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        pause_called = []
        def mock_pause():
            pause_called.append(True)
            return {"continue": True}

        with patch.object(phase, '_pause_for_review', mock_pause):
            phase._execute_with_mode(
                phases=["phase1", "phase2"],
                mode=AutonomyMode.CHECKPOINT
            )

        assert len(pause_called) == 2  # Paused after each

    def test_autonomous_mode_no_pause(self, tmp_path):
        """Given autonomous mode, runs without pause."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

        pause_called = []
        def mock_pause():
            pause_called.append(True)
            return {"continue": True}

        with patch.object(phase, '_pause_for_review', mock_pause):
            with patch.object(phase, '_execute_single_phase', return_value={"success": True}):
                phase._execute_with_mode(
                    phases=["phase1", "phase2"],
                    mode=AutonomyMode.AUTONOMOUS
                )

        assert len(pause_called) == 0  # No pauses

    def test_batch_mode_groups_phases(self, tmp_path):
        """Given batch mode, groups and pauses between groups."""
        cwa = CWAIntegration()
        phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)
        phase.BATCH_SIZE = 2

        pause_called = []
        def mock_pause():
            pause_called.append(True)
            return {"continue": True}

        with patch.object(phase, '_pause_for_review', mock_pause):
            with patch.object(phase, '_execute_single_phase', return_value={"success": True}):
                phase._execute_with_mode(
                    phases=["p1", "p2", "p3", "p4"],
                    mode=AutonomyMode.BATCH
                )

        # 4 phases, batch size 2 = 2 batches = 2 pauses
        assert len(pause_called) == 2
```

### 🟢 Green: Implement Modes

**File**: `silmari-rlm-act/phases/implementation.py`
```python
import subprocess


class ImplementationPhase:
    # ... existing code ...

    BATCH_SIZE = 3  # Phases per batch in batch mode

    def _run_tests(self, test_path: str = "tests/") -> tuple[bool, str]:
        """Run test suite.

        Args:
            test_path: Path to tests

        Returns:
            Tuple of (passed, output)
        """
        try:
            result = subprocess.run(
                ["pytest", test_path, "-v"],
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=self.TEST_TIMEOUT
            )
            return result.returncode == 0, result.stdout
        except Exception as e:
            return False, str(e)

    def _pause_for_review(self, phase_path: str, result: Dict) -> Dict:
        """Pause for user review (interactive).

        Args:
            phase_path: Path to completed phase
            result: Result from phase execution

        Returns:
            Dict with continue flag and optional feedback
        """
        from silmari_rlm_act.checkpoints.interactive import prompt_phase_continue

        return prompt_phase_continue(
            phase_name=Path(phase_path).stem,
            artifacts=[phase_path]
        )

    def _execute_single_phase(self, phase_path: str) -> Dict:
        """Execute a single phase.

        Args:
            phase_path: Path to phase document

        Returns:
            Dict with success and results
        """
        behaviors = self._extract_behaviors(phase_path)
        context = self._load_phase_document(phase_path)

        results = []
        for behavior in behaviors:
            result = self._execute_tdd_cycle(behavior, context)
            results.append(result)

            if not result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed on behavior: {behavior}",
                    "results": results
                }

            # Run tests after each cycle
            passed, output = self._run_tests()
            if not passed:
                return {
                    "success": False,
                    "error": f"Tests failed after: {behavior}",
                    "test_output": output,
                    "results": results
                }

        return {"success": True, "results": results}

    def _execute_with_mode(
        self,
        phases: List[str],
        mode: AutonomyMode
    ) -> List[Dict]:
        """Execute phases according to mode.

        Args:
            phases: List of phase paths
            mode: Execution mode

        Returns:
            List of results per phase
        """
        all_results = []

        if mode == AutonomyMode.AUTONOMOUS:
            # Run all without stopping
            for phase_path in phases:
                result = self._execute_single_phase(phase_path)
                all_results.append(result)
                if not result.get("success"):
                    break

        elif mode == AutonomyMode.CHECKPOINT:
            # Pause after each phase
            for phase_path in phases:
                result = self._execute_single_phase(phase_path)
                all_results.append(result)

                review = self._pause_for_review(phase_path, result)
                if not review.get("continue"):
                    break

        elif mode == AutonomyMode.BATCH:
            # Group phases, pause between batches
            for i in range(0, len(phases), self.BATCH_SIZE):
                batch = phases[i:i + self.BATCH_SIZE]

                for phase_path in batch:
                    result = self._execute_single_phase(phase_path)
                    all_results.append(result)
                    if not result.get("success"):
                        return all_results

                # Pause after batch
                review = self._pause_for_review(batch[-1], {"batch": i // self.BATCH_SIZE})
                if not review.get("continue"):
                    break

        return all_results
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_implementation_phase.py::TestRunTests -v`
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_implementation_phase.py::TestAutonomyModes -v`

---

## TDD Cycle: Behavior 7-12 - CWA, Beads, Resume

### Condensed Test Specifications

**Behavior 7: Store Results in CWA**
```python
def test_stores_command_results():
    result = phase._execute_single_phase(phase_path)

    # Check CWA has entries
    entries = cwa.get_by_type(EntryType.COMMAND_RESULT)
    assert len(entries) > 0
```

**Behavior 8: Update Beads Status**
```python
def test_closes_beads_issue_on_success():
    mock_beads.close_issue.return_value = {"success": True}

    phase._complete_phase("beads-001", phase_path)

    mock_beads.close_issue.assert_called_with("beads-001")
```

**Behavior 9: Handle Failure**
```python
def test_stops_on_test_failure():
    mock_run.return_value = Mock(returncode=1, stdout="1 failed")

    result = phase.execute(phases, mode=AutonomyMode.AUTONOMOUS)

    assert result.success is False
    assert "failed" in result.error
```

**Behavior 10: Manage Context Bounds**
```python
def test_respects_200_entry_limit():
    # Add many entries
    for i in range(250):
        cwa.store_research(f"doc{i}.md", f"content{i}", f"summary{i}")

    # Should not crash, should batch or limit
    result = phase._build_implementation_context(phase_path)

    assert len(result.entries) <= 200
```

**Behavior 11: Resume from Checkpoint**
```python
def test_resumes_from_last_phase():
    # Create checkpoint at phase 2
    checkpoint = {"completed_phases": ["phase1", "phase2"]}

    result = phase.execute(
        phases=["phase1", "phase2", "phase3"],
        mode=AutonomyMode.CHECKPOINT,
        checkpoint=checkpoint
    )

    # Should only execute phase3
    assert mock_execute.call_count == 1
```

**Behavior 12: Create Commit**
```python
def test_creates_commit_after_phase():
    mock_git.return_value = Mock(returncode=0)

    phase._commit_phase("phase1", "Implemented phase 1")

    # Verify git commands called
    assert any("git add" in str(c) for c in mock_git.call_args_list)
    assert any("git commit" in str(c) for c in mock_git.call_args_list)
```

---

## Execute Method

**File**: `silmari-rlm-act/phases/implementation.py`
```python
class ImplementationPhase:
    # ... existing code ...

    def execute(
        self,
        phase_paths: List[str],
        mode: AutonomyMode,
        beads_issue_ids: Optional[List[str]] = None,
        checkpoint: Optional[Dict] = None
    ) -> PhaseResult:
        """Execute implementation phase.

        Args:
            phase_paths: Paths to phase documents
            mode: Execution mode
            beads_issue_ids: Optional beads issue IDs to close
            checkpoint: Optional checkpoint to resume from

        Returns:
            PhaseResult with implementation status
        """
        try:
            # Filter to remaining phases if resuming
            if checkpoint:
                completed = checkpoint.get("completed_phases", [])
                phase_paths = [p for p in phase_paths if p not in completed]

            if not phase_paths:
                return PhaseResult(
                    phase="implementation",
                    success=True,
                    output="All phases already completed"
                )

            # Execute according to mode
            results = self._execute_with_mode(phase_paths, mode)

            # Check overall success
            all_passed = all(r.get("success") for r in results)

            # Close beads issues for successful phases
            if beads_issue_ids:
                for i, result in enumerate(results):
                    if result.get("success") and i < len(beads_issue_ids):
                        self._close_beads_issue(beads_issue_ids[i])

            return PhaseResult(
                phase="implementation",
                success=all_passed,
                artifacts=[p for p, r in zip(phase_paths, results) if r.get("success")],
                output=f"Completed {sum(1 for r in results if r.get('success'))}/{len(results)} phases"
            )

        except Exception as e:
            return PhaseResult(
                phase="implementation",
                success=False,
                error=str(e)
            )

    def _close_beads_issue(self, issue_id: str) -> None:
        """Close a beads issue."""
        if self._beads_controller:
            self._beads_controller.close_issue(issue_id, "Phase completed")
```

### Success Criteria
**Automated:**
- [ ] All implementation tests pass: `pytest silmari-rlm-act/tests/test_implementation_phase.py -v`

**Manual:**
- [ ] TDD cycles execute correctly
- [ ] All three modes work as expected
- [ ] Tests run and verify after each cycle
- [ ] Beads issues updated
- [ ] Resume from checkpoint works

## Summary

This phase implements the implementation executor with:
- Phase document loading
- Behavior extraction
- TDD cycle execution
- Test running and verification
- Three autonomy modes (checkpoint, autonomous, batch)
- CWA result storage
- Beads status updates
- Failure handling
- Context bound management
- Checkpoint resume
- Git commit creation
