# Phase 09: Beads Sync Phase TDD Plan

## Overview

Implement the beads synchronization phase that creates issues in the beads tracking system and links them to plan phases.

## Reference

See: `planning_pipeline/beads_controller.py` for existing patterns.

## Testable Behaviors

### Behavior 1: Create Epic Issue
**Given**: Plan name
**When**: Starting beads sync
**Then**: Epic issue created with plan name

### Behavior 2: Create Phase Issues
**Given**: Phase documents
**When**: Syncing to beads
**Then**: Task issue created per phase

### Behavior 3: Link Dependencies
**Given**: Sequential phases
**When**: Creating issues
**Then**: Phase N depends on Phase N-1

### Behavior 4: Update Issue Status
**Given**: Phase issue
**When**: Phase completed
**Then**: Issue marked closed

### Behavior 5: Sync to Remote
**Given**: Local beads changes
**When**: Phase completes
**Then**: `bd sync` executed

### Behavior 6: Store Issue IDs in CWA
**Given**: Created issues
**When**: Storing metadata
**Then**: Issue IDs associated with plan entries

### Behavior 7: Return PhaseResult
**Given**: Successful sync
**When**: Phase completes
**Then**: PhaseResult with epic ID and issue IDs

### Behavior 8: Handle Beads Errors
**Given**: Beads command fails
**When**: Error occurs
**Then**: PhaseResult with error

### Behavior 9: Annotate Phase Documents
**Given**: Phase documents
**When**: Sync completes
**Then**: Documents updated with beads IDs

### Behavior 10: Get Ready Issues
**Given**: Issues with dependencies
**When**: Checking ready work
**Then**: Returns unblocked issues

---

## TDD Cycle: Behavior 1 - Create Epic Issue

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_beads_sync_phase.py`
```python
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from silmari_rlm_act.phases.beads_sync import BeadsSyncPhase
from silmari_rlm_act.context.cwa_integration import CWAIntegration


class TestCreateEpic:
    """Behavior 1: Create Epic Issue."""

    def test_creates_epic_with_plan_name(self, tmp_path):
        """Given plan name, creates epic issue."""
        cwa = CWAIntegration()
        phase = BeadsSyncPhase(project_path=tmp_path, cwa=cwa)

        mock_controller = Mock()
        mock_controller.create_epic.return_value = {
            "success": True,
            "data": {"id": "beads-epic-001"}
        }

        with patch.object(phase, '_controller', mock_controller):
            epic_id = phase._create_epic("Login Feature TDD Plan")

        mock_controller.create_epic.assert_called_once_with("Login Feature TDD Plan")
        assert epic_id == "beads-epic-001"

    def test_raises_on_epic_failure(self, tmp_path):
        """Given beads failure, raises error."""
        cwa = CWAIntegration()
        phase = BeadsSyncPhase(project_path=tmp_path, cwa=cwa)

        mock_controller = Mock()
        mock_controller.create_epic.return_value = {
            "success": False,
            "error": "Connection failed"
        }

        with patch.object(phase, '_controller', mock_controller):
            with pytest.raises(RuntimeError, match="Connection failed"):
                phase._create_epic("Test Plan")
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/phases/beads_sync.py`
```python
"""Beads synchronization phase implementation."""

from pathlib import Path
from typing import List, Dict, Optional
from silmari_rlm_act.models import PhaseResult
from silmari_rlm_act.context.cwa_integration import CWAIntegration


class BeadsController:
    """Wrapper for beads CLI commands.

    Reuses pattern from planning_pipeline/beads_controller.py
    """

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self._timeout = 30

    def _run_bd(self, *args, use_json: bool = True) -> Dict:
        """Run bd command."""
        import subprocess
        import json

        cmd = ['bd'] + list(str(a) for a in args)
        if use_json:
            cmd.append('--json')

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=self._timeout
            )

            if result.returncode == 0:
                if use_json:
                    try:
                        return {"success": True, "data": json.loads(result.stdout)}
                    except json.JSONDecodeError:
                        return {"success": True, "data": result.stdout.strip()}
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {"success": False, "error": result.stderr.strip() or result.stdout.strip()}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out"}
        except FileNotFoundError:
            return {"success": False, "error": "bd command not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_epic(self, title: str, priority: int = 2) -> Dict:
        """Create an epic issue."""
        return self._run_bd(
            'create',
            f'--title={title}',
            '--type=epic',
            f'--priority={priority}'
        )

    def create_issue(self, title: str, issue_type: str = "task", priority: int = 2) -> Dict:
        """Create a task issue."""
        return self._run_bd(
            'create',
            f'--title={title}',
            f'--type={issue_type}',
            f'--priority={priority}'
        )

    def add_dependency(self, issue_id: str, depends_on: str) -> Dict:
        """Add dependency between issues."""
        return self._run_bd('dep', 'add', issue_id, depends_on)

    def close_issue(self, issue_id: str, reason: Optional[str] = None) -> Dict:
        """Close an issue."""
        args = ['close', issue_id]
        if reason:
            args.append(f'--reason={reason}')
        return self._run_bd(*args)

    def sync(self) -> Dict:
        """Sync with remote."""
        return self._run_bd('sync', use_json=False)

    def get_ready(self, limit: int = 10) -> Dict:
        """Get ready issues."""
        return self._run_bd('ready', f'--limit={limit}')

    def update_status(self, issue_id: str, status: str) -> Dict:
        """Update issue status."""
        return self._run_bd('update', issue_id, f'--status={status}')


class BeadsSyncPhase:
    """Synchronize plan phases with beads issue tracking."""

    def __init__(
        self,
        project_path: Path,
        cwa: CWAIntegration,
    ):
        self.project_path = Path(project_path)
        self.cwa = cwa
        self._controller = BeadsController(project_path)

    def _create_epic(self, plan_name: str) -> str:
        """Create epic issue for plan.

        Args:
            plan_name: Name for the epic

        Returns:
            Epic issue ID

        Raises:
            RuntimeError: If creation fails
        """
        result = self._controller.create_epic(plan_name)
        if not result.get("success"):
            raise RuntimeError(result.get("error", "Failed to create epic"))
        return result["data"]["id"]
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_beads_sync_phase.py::TestCreateEpic -v`

---

## TDD Cycle: Behavior 2-3 - Create Issues and Dependencies

### 🔴 Red: Write Failing Tests

**File**: `silmari-rlm-act/tests/test_beads_sync_phase.py`
```python
class TestCreatePhaseIssues:
    """Behavior 2: Create Phase Issues."""

    def test_creates_issue_per_phase(self, tmp_path):
        """Given phase docs, creates task issues."""
        cwa = CWAIntegration()
        phase = BeadsSyncPhase(project_path=tmp_path, cwa=cwa)

        phase_docs = [
            {"filename": "01-login.md", "title": "Phase 1: Login"},
            {"filename": "02-logout.md", "title": "Phase 2: Logout"},
        ]

        mock_controller = Mock()
        mock_controller.create_issue.side_effect = [
            {"success": True, "data": {"id": "beads-001"}},
            {"success": True, "data": {"id": "beads-002"}},
        ]

        with patch.object(phase, '_controller', mock_controller):
            issue_ids = phase._create_phase_issues(phase_docs, "beads-epic")

        assert len(issue_ids) == 2
        assert mock_controller.create_issue.call_count == 2


class TestLinkDependencies:
    """Behavior 3: Link Dependencies."""

    def test_links_sequential_phases(self, tmp_path):
        """Given phases, links N depends on N-1."""
        cwa = CWAIntegration()
        phase = BeadsSyncPhase(project_path=tmp_path, cwa=cwa)

        issue_ids = ["beads-001", "beads-002", "beads-003"]

        mock_controller = Mock()
        mock_controller.add_dependency.return_value = {"success": True}

        with patch.object(phase, '_controller', mock_controller):
            phase._link_dependencies(issue_ids)

        # Should have 2 dependency calls (2->1, 3->2)
        assert mock_controller.add_dependency.call_count == 2
        calls = mock_controller.add_dependency.call_args_list
        assert calls[0][0] == ("beads-002", "beads-001")
        assert calls[1][0] == ("beads-003", "beads-002")
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/phases/beads_sync.py`
```python
class BeadsSyncPhase:
    # ... existing code ...

    def _create_phase_issues(
        self,
        phase_docs: List[Dict],
        epic_id: str
    ) -> List[str]:
        """Create task issues for each phase.

        Args:
            phase_docs: List of phase document dicts
            epic_id: Parent epic ID

        Returns:
            List of created issue IDs
        """
        issue_ids = []

        for i, doc in enumerate(phase_docs):
            # Skip overview
            if "00-overview" in doc.get("filename", ""):
                continue

            result = self._controller.create_issue(
                title=doc.get("title", f"Phase {i}"),
                priority=i  # Lower number = higher priority
            )

            if result.get("success"):
                issue_ids.append(result["data"]["id"])
            else:
                # Log warning but continue
                print(f"Warning: Failed to create issue for {doc.get('title')}")

        return issue_ids

    def _link_dependencies(self, issue_ids: List[str]) -> None:
        """Link sequential dependencies between issues.

        Args:
            issue_ids: Ordered list of issue IDs
        """
        for i in range(1, len(issue_ids)):
            current = issue_ids[i]
            previous = issue_ids[i - 1]

            result = self._controller.add_dependency(current, previous)
            if not result.get("success"):
                print(f"Warning: Failed to link {current} -> {previous}")
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_beads_sync_phase.py::TestCreatePhaseIssues -v`
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_beads_sync_phase.py::TestLinkDependencies -v`

---

## TDD Cycle: Behavior 4-10 - Remaining Behaviors

### Condensed Test Specifications

**Behavior 4: Update Issue Status**
```python
def test_marks_completed_on_close():
    mock_controller.close_issue.return_value = {"success": True}

    phase._close_issue("beads-001", "Phase completed")

    mock_controller.close_issue.assert_called_with("beads-001", "Phase completed")
```

**Behavior 5: Sync to Remote**
```python
def test_calls_bd_sync():
    mock_controller.sync.return_value = {"success": True}

    phase._sync_to_remote()

    mock_controller.sync.assert_called_once()
```

**Behavior 6: Store Issue IDs in CWA**
```python
def test_stores_beads_metadata():
    phase._store_beads_metadata(
        epic_id="beads-epic",
        issue_ids=["beads-001", "beads-002"],
        phase_docs=docs
    )

    # Verify metadata stored (implementation-specific)
```

**Behavior 7: Return PhaseResult**
```python
def test_returns_success_result():
    result = phase.execute(phase_docs, "Test Plan")

    assert result.success is True
    assert "epic_id" in result.output or len(result.artifacts) > 0
```

**Behavior 8: Handle Errors**
```python
def test_returns_error_on_failure():
    mock_controller.create_epic.return_value = {"success": False, "error": "Failed"}

    result = phase.execute(phase_docs, "Test Plan")

    assert result.success is False
```

**Behavior 9: Annotate Documents**
```python
def test_adds_beads_id_to_doc():
    phase._annotate_documents(docs, issue_ids, output_dir)

    # Read updated doc
    content = (output_dir / "01-login.md").read_text()
    assert "beads-001" in content
```

**Behavior 10: Get Ready Issues**
```python
def test_returns_unblocked_issues():
    mock_controller.get_ready.return_value = {
        "success": True,
        "data": [{"id": "beads-002", "title": "Phase 2"}]
    }

    ready = phase.get_ready_issues()

    assert len(ready) == 1
```

---

## Execute Method

**File**: `silmari-rlm-act/phases/beads_sync.py`
```python
class BeadsSyncPhase:
    # ... existing code ...

    def execute(
        self,
        phase_docs: List[Dict],
        plan_name: str,
        output_dir: Optional[Path] = None
    ) -> PhaseResult:
        """Execute beads sync phase.

        Args:
            phase_docs: List of phase document dicts
            plan_name: Name for the epic
            output_dir: Optional output directory for annotation

        Returns:
            PhaseResult with beads IDs
        """
        try:
            # Create epic
            epic_id = self._create_epic(f"{plan_name} TDD Implementation")

            # Create phase issues
            issue_ids = self._create_phase_issues(phase_docs, epic_id)

            # Link dependencies
            if len(issue_ids) > 1:
                self._link_dependencies(issue_ids)

            # Annotate documents if output_dir provided
            if output_dir:
                self._annotate_documents(phase_docs, issue_ids, output_dir)

            # Sync to remote
            self._sync_to_remote()

            return PhaseResult(
                phase="beads_sync",
                success=True,
                artifacts=[epic_id] + issue_ids,
                output=f"Created epic {epic_id} with {len(issue_ids)} phase issues"
            )

        except Exception as e:
            return PhaseResult(
                phase="beads_sync",
                success=False,
                error=str(e)
            )

    def _sync_to_remote(self) -> None:
        """Sync beads to remote."""
        result = self._controller.sync()
        if not result.get("success"):
            print(f"Warning: Sync failed: {result.get('error')}")

    def _annotate_documents(
        self,
        phase_docs: List[Dict],
        issue_ids: List[str],
        output_dir: Path
    ) -> None:
        """Add beads IDs to document headers."""
        phase_idx = 0
        for doc in phase_docs:
            if "00-overview" in doc.get("filename", ""):
                continue

            if phase_idx < len(issue_ids):
                filepath = output_dir / doc["filename"]
                if filepath.exists():
                    content = filepath.read_text()
                    # Add beads ID to header
                    beads_line = f"\n**Beads Issue**: `{issue_ids[phase_idx]}`\n"
                    content = content.replace("## Requirements", beads_line + "\n## Requirements")
                    filepath.write_text(content)
                phase_idx += 1

    def get_ready_issues(self, limit: int = 10) -> List[Dict]:
        """Get issues ready to work on."""
        result = self._controller.get_ready(limit)
        if result.get("success"):
            return result.get("data", [])
        return []
```

### Success Criteria
**Automated:**
- [ ] All beads sync tests pass: `pytest silmari-rlm-act/tests/test_beads_sync_phase.py -v`

**Manual:**
- [ ] Epic created in beads
- [ ] Phase issues linked correctly
- [ ] Documents annotated with IDs
- [ ] Sync to remote works

## Summary

This phase implements beads synchronization with:
- Epic issue creation
- Phase task creation
- Sequential dependency linking
- Issue status updates
- Remote sync
- Document annotation
- Ready issue queries
