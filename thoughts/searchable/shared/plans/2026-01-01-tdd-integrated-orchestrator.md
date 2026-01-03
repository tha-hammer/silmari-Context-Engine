# IntegratedOrchestrator TDD Implementation Plan

## Overview

Create a new `IntegratedOrchestrator` class that bridges `planning_orchestrator.py` with `orchestrator.py`, replacing JSON file-based state tracking with beads CLI commands while maintaining session logging to `.agent/sessions/`. Uses Claude SDK for LLM-powered techstack detection from overview.md files.

## Current State Analysis

### Existing Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `PlanningPipeline` | `planning_pipeline/pipeline.py:12-241` | 5-step planning pipeline with checkpoints |
| `BeadsController` | `planning_pipeline/beads_controller.py:9-91` | Wrapper for bd CLI commands |
| `run_claude_sync()` | `planning_pipeline/claude_runner.py:23-81` | Claude SDK subprocess execution |
| `orchestrator.py` | `orchestrator.py:322-502` | Original functions to replace |

### Key Discoveries

- `get_project_info_interactive()` at `orchestrator.py:322-407` - Interactive prompts for project setup
- `get_feature_status()` at `orchestrator.py:421-444` - Reads `feature_list.json`
- `sync_features_with_git()` at `orchestrator.py:457-485` - Scans git history for completion markers
- `get_next_feature()` at `orchestrator.py:487-502` - Priority-sorted feature selection with dependency checking
- `BeadsController._run_bd()` at `beads_controller.py:20-50` - JSON output parsing from bd CLI
- Phase files use priority by phase order (phase 1 = priority 1, etc.)

### Session Logging Pattern

Current session logs at `.agent/sessions/` will be preserved. The `IntegratedOrchestrator` will write session state to the same location.

## Desired End State

A new `IntegratedOrchestrator` class in `planning_pipeline/integrated_orchestrator.py` that:

1. **Replaces `get_project_info_interactive()`** with LLM-powered techstack detection from overview.md
2. **Replaces `get_feature_status()`** with beads `bd list` commands
3. **Replaces `sync_features_with_git()`** with `bd sync`
4. **Replaces `get_next_feature()`** with `bd ready`
5. **Maintains session logging** to `.agent/sessions/`
6. **Uses phase order for priority** (phase 1 = priority 1, phase 2 = priority 2, etc.)

### Observable Behaviors

1. Given an overview.md file exists, when `get_project_info()` is called, then it returns project info with techstack from LLM analysis
2. Given beads issues exist, when `get_feature_status()` is called, then it returns status from bd list commands
3. Given issues with dependencies, when `get_next_feature()` is called, then it returns the first ready issue
4. Given phase files, when issues are created, then priority equals phase order number
5. Given session activity, when operations complete, then logs are written to `.agent/sessions/`

## What We're NOT Doing

- Modifying the original `orchestrator.py` functions (this is a new class)
- Changing the existing `PlanningPipeline` class
- Removing `.agent/sessions/` logging (we keep it)
- Adding new bd CLI subcommands to beads

## Testing Strategy

- **Framework**: pytest with subprocess mocking
- **Test Types**:
  - Unit tests for each method
  - Integration tests for LLM calls (mocked)
  - Integration tests for bd CLI (mocked subprocess)
- **Mocking**: Use `unittest.mock` for subprocess.run, file I/O

## Behavior 1: LLM-Powered Techstack Detection

### Test Specification

**Given**: An overview.md file exists at `thoughts/shared/plans/*-overview.md`
**When**: `get_project_info()` is called with a project path
**Then**: Returns dict with name, stack, description from LLM analysis

**Edge Cases**:
- No overview file found → fallback to README.md
- No files found → return defaults with project directory name
- LLM returns invalid JSON → return defaults
- Empty overview content → return defaults

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `planning_pipeline/tests/test_integrated_orchestrator.py`

```python
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator


class TestGetProjectInfo:
    """Tests for LLM-powered project info detection."""

    def test_extracts_techstack_from_overview_file(self, tmp_path):
        """Given overview.md exists, returns techstack from LLM analysis."""
        # Arrange
        plans_dir = tmp_path / "thoughts" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        overview = plans_dir / "2026-01-01-feature-00-overview.md"
        overview.write_text("""# Feature Implementation

## Tech Stack
- Python 3.11
- FastAPI
- PostgreSQL
""")

        mock_result = {
            "success": True,
            "output": '{"name": "Feature", "stack": "Python FastAPI PostgreSQL", "description": "A feature implementation"}'
        }

        with patch('planning_pipeline.integrated_orchestrator.run_claude_sync', return_value=mock_result):
            orchestrator = IntegratedOrchestrator(tmp_path)

            # Act
            info = orchestrator.get_project_info()

            # Assert
            assert info["name"] == "Feature"
            assert "Python" in info["stack"]
            assert "FastAPI" in info["stack"]
            assert info["path"] == tmp_path
            assert info["model"] == "sonnet"

    def test_fallback_to_readme_when_no_overview(self, tmp_path):
        """Given no overview file, falls back to README.md."""
        # Arrange
        readme = tmp_path / "README.md"
        readme.write_text("# My Project\nA Python CLI tool.")

        mock_result = {
            "success": True,
            "output": '{"name": "My Project", "stack": "Python CLI", "description": "A CLI tool"}'
        }

        with patch('planning_pipeline.integrated_orchestrator.run_claude_sync', return_value=mock_result):
            orchestrator = IntegratedOrchestrator(tmp_path)
            info = orchestrator.get_project_info()

            assert info["name"] == "My Project"

    def test_returns_defaults_when_no_files_found(self, tmp_path):
        """Given no overview or readme, returns defaults."""
        orchestrator = IntegratedOrchestrator(tmp_path)

        with patch('planning_pipeline.integrated_orchestrator.run_claude_sync') as mock_claude:
            mock_claude.return_value = {"success": False, "error": "No content"}
            info = orchestrator.get_project_info()

            assert info["name"] == tmp_path.name
            assert info["stack"] == "Unknown"
            assert info["path"] == tmp_path

    def test_handles_invalid_json_from_llm(self, tmp_path):
        """Given LLM returns invalid JSON, returns defaults."""
        overview = tmp_path / "thoughts" / "shared" / "plans" / "overview.md"
        overview.parent.mkdir(parents=True)
        overview.write_text("# Some content")

        mock_result = {"success": True, "output": "This is not JSON"}

        with patch('planning_pipeline.integrated_orchestrator.run_claude_sync', return_value=mock_result):
            orchestrator = IntegratedOrchestrator(tmp_path)
            info = orchestrator.get_project_info()

            assert info["name"] == tmp_path.name
            assert info["stack"] == "Unknown"
```

#### 🟢 Green: Minimal Implementation

**File**: `planning_pipeline/integrated_orchestrator.py`

```python
"""Integrated orchestrator using beads for state and Claude for LLM calls."""

import json
from pathlib import Path
from typing import Any, Optional

from .beads_controller import BeadsController
from .claude_runner import run_claude_sync


class IntegratedOrchestrator:
    """Orchestrator using planning_pipeline and beads for state management."""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self.bd = BeadsController(project_path)

    def get_project_info(self) -> dict[str, Any]:
        """Detect project info from overview.md via LLM."""
        # Priority order for finding project documentation
        search_patterns = [
            "thoughts/**/plans/*-overview.md",
            "thoughts/**/plans/*-00-overview.md",
            "thoughts/**/plans/*.md",
            "README.md",
        ]

        content = ""
        for pattern in search_patterns:
            files = list(self.project_path.glob(pattern))
            if files:
                # Sort by modification time, newest first
                files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                content = files[0].read_text()[:5000]
                break

        if not content:
            return self._default_project_info()

        prompt = f"""Analyze this project documentation and extract:
1. Project name
2. Tech stack (language, framework, database)
3. Brief description (1-2 sentences)

Documentation:
{content}

Return ONLY valid JSON: {{"name": "...", "stack": "...", "description": "..."}}"""

        result = run_claude_sync(prompt=prompt, timeout=60, stream=False)

        if not result["success"]:
            return self._default_project_info()

        try:
            info = json.loads(result["output"])
            info["path"] = self.project_path
            info["model"] = "sonnet"
            return info
        except json.JSONDecodeError:
            return self._default_project_info()

    def _default_project_info(self) -> dict[str, Any]:
        """Return default project info when detection fails."""
        return {
            "name": self.project_path.name,
            "path": self.project_path,
            "stack": "Unknown",
            "description": "",
            "model": "sonnet"
        }
```

#### 🔵 Refactor: Improve Code

**File**: `planning_pipeline/integrated_orchestrator.py`

```python
# After green, refactor to extract LLM prompt as constant and add logging
# (Implementation stays mostly the same, just cleaner organization)
```

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): `pytest planning_pipeline/tests/test_integrated_orchestrator.py::TestGetProjectInfo -v`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_integrated_orchestrator.py::TestGetProjectInfo -v`
- [ ] All tests pass after refactor: `pytest planning_pipeline/tests/`
- [ ] Type check passes: `mypy planning_pipeline/integrated_orchestrator.py`

**Manual:**
- [ ] LLM correctly extracts techstack from real overview files
- [ ] Fallback works when no files exist

---

## Behavior 2: Feature Status from Beads

### Test Specification

**Given**: Beads issues exist in the project
**When**: `get_feature_status()` is called
**Then**: Returns dict with total, completed, remaining, blocked counts from bd list

**Edge Cases**:
- No beads initialized → return zeros
- bd command fails → return zeros
- Mixed status issues → correct counting
- Issues with unmet dependencies → counted as blocked

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `planning_pipeline/tests/test_integrated_orchestrator.py`

```python
class TestGetFeatureStatus:
    """Tests for beads-based feature status."""

    def test_returns_status_from_beads_list(self, tmp_path):
        """Given beads issues exist, returns correct counts."""
        mock_all = {
            "success": True,
            "data": [
                {"id": "issue-1", "status": "open", "dependencies": []},
                {"id": "issue-2", "status": "closed", "dependencies": []},
                {"id": "issue-3", "status": "open", "dependencies": [{"depends_on_id": "issue-1"}]},
            ]
        }
        mock_open = {
            "success": True,
            "data": [
                {"id": "issue-1", "status": "open", "dependencies": []},
                {"id": "issue-3", "status": "open", "dependencies": [{"depends_on_id": "issue-1"}]},
            ]
        }
        mock_closed = {
            "success": True,
            "data": [{"id": "issue-2", "status": "closed", "dependencies": []}]
        }

        with patch.object(BeadsController, 'list_issues') as mock_list:
            mock_list.side_effect = [mock_all, mock_open, mock_closed]

            orchestrator = IntegratedOrchestrator(tmp_path)
            status = orchestrator.get_feature_status()

            assert status["total"] == 3
            assert status["completed"] == 1
            assert status["remaining"] == 2
            assert status["blocked"] == 1  # issue-3 blocked by issue-1
            assert len(status["features"]) == 3

    def test_returns_zeros_when_no_beads(self, tmp_path):
        """Given bd not initialized, returns zero counts."""
        with patch.object(BeadsController, 'list_issues') as mock_list:
            mock_list.return_value = {"success": False, "error": "Not initialized"}

            orchestrator = IntegratedOrchestrator(tmp_path)
            status = orchestrator.get_feature_status()

            assert status["total"] == 0
            assert status["completed"] == 0
            assert status["remaining"] == 0
            assert status["blocked"] == 0

    def test_correctly_identifies_blocked_by_open_dependencies(self, tmp_path):
        """Given issue depends on open issue, it's counted as blocked."""
        mock_all = {
            "success": True,
            "data": [
                {"id": "phase-1", "status": "open", "dependencies": []},
                {"id": "phase-2", "status": "open", "dependencies": [{"depends_on_id": "phase-1"}]},
                {"id": "phase-3", "status": "open", "dependencies": [{"depends_on_id": "phase-2"}]},
            ]
        }

        with patch.object(BeadsController, 'list_issues') as mock_list:
            mock_list.side_effect = [mock_all, mock_all, {"success": True, "data": []}]

            orchestrator = IntegratedOrchestrator(tmp_path)
            status = orchestrator.get_feature_status()

            # phase-2 blocked by phase-1, phase-3 blocked by phase-2
            assert status["blocked"] == 2
```

#### 🟢 Green: Minimal Implementation

**File**: `planning_pipeline/integrated_orchestrator.py`

```python
    def get_feature_status(self) -> dict[str, Any]:
        """Get feature status from beads issues."""
        all_result = self.bd.list_issues()
        open_result = self.bd.list_issues(status="open")
        closed_result = self.bd.list_issues(status="closed")

        if not all_result["success"]:
            return {"total": 0, "completed": 0, "remaining": 0, "blocked": 0, "features": []}

        all_issues = all_result.get("data", [])
        open_issues = open_result.get("data", []) if open_result["success"] else []
        closed_issues = closed_result.get("data", []) if closed_result["success"] else []

        # Build set of open issue IDs for dependency checking
        open_ids = {issue["id"] for issue in open_issues}

        # Count blocked: issues with any open dependency
        blocked = 0
        for issue in all_issues:
            for dep in issue.get("dependencies", []):
                if dep.get("depends_on_id") in open_ids:
                    blocked += 1
                    break

        return {
            "total": len(all_issues),
            "completed": len(closed_issues),
            "remaining": len(open_issues),
            "blocked": blocked,
            "features": all_issues
        }
```

#### 🔵 Refactor: Improve Code

Keep implementation as-is; it's already minimal and clear.

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): `pytest planning_pipeline/tests/test_integrated_orchestrator.py::TestGetFeatureStatus -v`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_integrated_orchestrator.py::TestGetFeatureStatus -v`
- [ ] All tests pass: `pytest planning_pipeline/tests/`

**Manual:**
- [ ] Correct counts with real beads issues

---

## Behavior 3: Get Next Feature from bd ready

### Test Specification

**Given**: Beads issues exist with dependencies
**When**: `get_next_feature()` is called
**Then**: Returns the first issue from `bd ready` (no blockers, dependencies met)

**Edge Cases**:
- No ready issues → return None
- bd ready returns empty list → return None
- bd ready returns single dict → return it directly

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `planning_pipeline/tests/test_integrated_orchestrator.py`

```python
class TestGetNextFeature:
    """Tests for getting next ready feature."""

    def test_returns_first_ready_issue(self, tmp_path):
        """Given ready issues exist, returns first one."""
        mock_ready = {
            "success": True,
            "data": [
                {"id": "phase-1", "title": "Phase 1: Setup", "priority": 1},
                {"id": "phase-2", "title": "Phase 2: Core", "priority": 2},
            ]
        }

        with patch.object(BeadsController, '_run_bd', return_value=mock_ready):
            orchestrator = IntegratedOrchestrator(tmp_path)
            feature = orchestrator.get_next_feature()

            assert feature is not None
            assert feature["id"] == "phase-1"
            assert feature["priority"] == 1

    def test_returns_none_when_no_ready_issues(self, tmp_path):
        """Given no ready issues, returns None."""
        mock_ready = {"success": True, "data": []}

        with patch.object(BeadsController, '_run_bd', return_value=mock_ready):
            orchestrator = IntegratedOrchestrator(tmp_path)
            feature = orchestrator.get_next_feature()

            assert feature is None

    def test_handles_single_dict_response(self, tmp_path):
        """Given bd ready returns dict (not list), handles it."""
        mock_ready = {
            "success": True,
            "data": {"id": "only-issue", "title": "Single Issue"}
        }

        with patch.object(BeadsController, '_run_bd', return_value=mock_ready):
            orchestrator = IntegratedOrchestrator(tmp_path)
            feature = orchestrator.get_next_feature()

            assert feature is not None
            assert feature["id"] == "only-issue"

    def test_returns_none_on_bd_failure(self, tmp_path):
        """Given bd ready fails, returns None."""
        mock_ready = {"success": False, "error": "Command failed"}

        with patch.object(BeadsController, '_run_bd', return_value=mock_ready):
            orchestrator = IntegratedOrchestrator(tmp_path)
            feature = orchestrator.get_next_feature()

            assert feature is None
```

#### 🟢 Green: Minimal Implementation

**File**: `planning_pipeline/integrated_orchestrator.py`

```python
    def get_next_feature(self) -> dict[str, Any] | None:
        """Get next ready issue from beads (no blockers, dependencies met)."""
        result = self.bd._run_bd('ready', '--limit=1')

        if not result["success"]:
            return None

        data = result.get("data")
        if not data:
            return None

        if isinstance(data, list):
            return data[0] if data else None
        elif isinstance(data, dict):
            return data

        return None
```

#### 🔵 Refactor: Improve Code

Add helper method `get_ready_issue()` to BeadsController if needed.

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red)
- [ ] Test passes (Green)
- [ ] All tests pass

**Manual:**
- [ ] Returns correct issue with real beads

---

## Behavior 4: Sync Features with bd sync

### Test Specification

**Given**: Beads is initialized
**When**: `sync_features_with_git()` is called
**Then**: Calls `bd sync` and returns success status

**Edge Cases**:
- bd sync succeeds → return 0
- bd sync fails → return -1

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `planning_pipeline/tests/test_integrated_orchestrator.py`

```python
class TestSyncFeaturesWithGit:
    """Tests for beads sync."""

    def test_returns_zero_on_success(self, tmp_path):
        """Given bd sync succeeds, returns 0."""
        mock_sync = {"success": True, "output": "Synced"}

        with patch.object(BeadsController, 'sync', return_value=mock_sync):
            orchestrator = IntegratedOrchestrator(tmp_path)
            result = orchestrator.sync_features_with_git()

            assert result == 0

    def test_returns_negative_one_on_failure(self, tmp_path):
        """Given bd sync fails, returns -1."""
        mock_sync = {"success": False, "error": "Sync failed"}

        with patch.object(BeadsController, 'sync', return_value=mock_sync):
            orchestrator = IntegratedOrchestrator(tmp_path)
            result = orchestrator.sync_features_with_git()

            assert result == -1
```

#### 🟢 Green: Minimal Implementation

**File**: `planning_pipeline/integrated_orchestrator.py`

```python
    def sync_features_with_git(self) -> int:
        """Sync beads with git remote."""
        result = self.bd.sync()
        return 0 if result["success"] else -1
```

#### 🔵 Refactor: Improve Code

Implementation is already minimal.

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red)
- [ ] Test passes (Green)

**Manual:**
- [ ] bd sync actually runs

---

## Behavior 5: Phase Priority from Order

### Test Specification

**Given**: Phase files are created from a plan
**When**: Issues are created for phases
**Then**: Priority equals phase order (phase 1 = priority 1, phase 2 = priority 2)

**Edge Cases**:
- Phase 0 (overview) → not created as issue
- Phase numbers extracted from filename pattern

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `planning_pipeline/tests/test_integrated_orchestrator.py`

```python
class TestPhaseIssueCreation:
    """Tests for phase issue creation with priority by order."""

    def test_creates_issues_with_priority_matching_phase_order(self, tmp_path):
        """Given phase files, creates issues with priority = phase number."""
        phase_files = [
            "thoughts/shared/plans/2026-01-01-feature-01-setup.md",
            "thoughts/shared/plans/2026-01-01-feature-02-core.md",
            "thoughts/shared/plans/2026-01-01-feature-03-ui.md",
        ]

        created_issues = []

        def mock_create(title, issue_type, priority):
            created_issues.append({"title": title, "priority": priority})
            return {"success": True, "data": {"id": f"issue-{len(created_issues)}"}}

        with patch.object(BeadsController, 'create_issue', side_effect=mock_create):
            with patch.object(BeadsController, 'add_dependency', return_value={"success": True}):
                with patch.object(BeadsController, 'sync', return_value={"success": True}):
                    orchestrator = IntegratedOrchestrator(tmp_path)
                    result = orchestrator.create_phase_issues(phase_files, "Epic Title")

        assert len(created_issues) == 3
        assert created_issues[0]["priority"] == 1
        assert created_issues[1]["priority"] == 2
        assert created_issues[2]["priority"] == 3

    def test_skips_overview_file(self, tmp_path):
        """Given overview file in list, skips it."""
        phase_files = [
            "thoughts/shared/plans/2026-01-01-feature-00-overview.md",
            "thoughts/shared/plans/2026-01-01-feature-01-setup.md",
        ]

        created_issues = []

        def mock_create(title, issue_type, priority):
            created_issues.append({"title": title, "priority": priority})
            return {"success": True, "data": {"id": f"issue-{len(created_issues)}"}}

        with patch.object(BeadsController, 'create_issue', side_effect=mock_create):
            with patch.object(BeadsController, 'add_dependency', return_value={"success": True}):
                with patch.object(BeadsController, 'sync', return_value={"success": True}):
                    orchestrator = IntegratedOrchestrator(tmp_path)
                    result = orchestrator.create_phase_issues(phase_files, "Epic Title")

        # Only 1 issue created (overview skipped)
        assert len(created_issues) == 1
        assert created_issues[0]["priority"] == 1
```

#### 🟢 Green: Minimal Implementation

**File**: `planning_pipeline/integrated_orchestrator.py`

```python
    def create_phase_issues(
        self,
        phase_files: list[str],
        epic_title: str
    ) -> dict[str, Any]:
        """Create beads issues for phases with priority by order.

        Args:
            phase_files: List of phase file paths
            epic_title: Title for the epic issue

        Returns:
            Dictionary with epic_id and phase_issues list
        """
        # Separate overview from phase files
        actual_phases = []
        for f in phase_files:
            if "overview" not in f.lower() and "-00-" not in f:
                actual_phases.append(f)

        # Create epic
        epic_result = self.bd.create_epic(epic_title)
        epic_id = None
        if epic_result["success"] and isinstance(epic_result["data"], dict):
            epic_id = epic_result["data"].get("id")

        # Create issues with priority = phase order
        phase_issues = []
        for i, phase_file in enumerate(actual_phases, start=1):
            phase_name = Path(phase_file).stem.split('-', 2)[-1].replace('-', ' ').title()

            result = self.bd.create_issue(
                title=f"Phase {i}: {phase_name}",
                issue_type="task",
                priority=i  # Priority matches phase order
            )

            if result["success"] and isinstance(result["data"], dict):
                issue_id = result["data"].get("id")
                phase_issues.append({
                    "phase": i,
                    "file": phase_file,
                    "issue_id": issue_id,
                    "priority": i
                })

        # Link dependencies (each phase depends on previous)
        for i in range(1, len(phase_issues)):
            curr_id = phase_issues[i].get("issue_id")
            prev_id = phase_issues[i - 1].get("issue_id")
            if curr_id and prev_id:
                self.bd.add_dependency(curr_id, prev_id)

        self.bd.sync()

        return {
            "success": True,
            "epic_id": epic_id,
            "phase_issues": phase_issues
        }
```

#### 🔵 Refactor: Improve Code

Extract phase number parsing into helper function.

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red)
- [ ] Test passes (Green)
- [ ] All tests pass

**Manual:**
- [ ] Real phase issues have correct priority

---

## Behavior 6: Session Logging to .agent/sessions/

### Test Specification

**Given**: Orchestrator operations occur
**When**: `log_session()` is called
**Then**: Logs are written to `.agent/sessions/` directory

**Edge Cases**:
- Directory doesn't exist → create it
- Session file exists → append or create new

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `planning_pipeline/tests/test_integrated_orchestrator.py`

```python
class TestSessionLogging:
    """Tests for session logging to .agent/sessions/."""

    def test_logs_session_to_agent_sessions_directory(self, tmp_path):
        """Given operation completes, logs to .agent/sessions/."""
        orchestrator = IntegratedOrchestrator(tmp_path)

        orchestrator.log_session(
            session_id="test-session-001",
            action="get_next_feature",
            result={"feature_id": "phase-1"}
        )

        sessions_dir = tmp_path / ".agent" / "sessions"
        assert sessions_dir.exists()

        # Find session file
        session_files = list(sessions_dir.glob("*.json"))
        assert len(session_files) >= 1

    def test_creates_sessions_directory_if_missing(self, tmp_path):
        """Given .agent/sessions/ doesn't exist, creates it."""
        orchestrator = IntegratedOrchestrator(tmp_path)

        sessions_dir = tmp_path / ".agent" / "sessions"
        assert not sessions_dir.exists()

        orchestrator.log_session(
            session_id="new-session",
            action="init",
            result={}
        )

        assert sessions_dir.exists()

    def test_session_log_contains_required_fields(self, tmp_path):
        """Given log is written, contains timestamp, action, result."""
        orchestrator = IntegratedOrchestrator(tmp_path)

        orchestrator.log_session(
            session_id="detail-session",
            action="sync",
            result={"synced": True}
        )

        sessions_dir = tmp_path / ".agent" / "sessions"
        session_file = list(sessions_dir.glob("*.json"))[0]

        import json
        content = json.loads(session_file.read_text())

        assert "timestamp" in content
        assert "action" in content
        assert content["action"] == "sync"
        assert "result" in content
```

#### 🟢 Green: Minimal Implementation

**File**: `planning_pipeline/integrated_orchestrator.py`

```python
    def log_session(
        self,
        session_id: str,
        action: str,
        result: dict[str, Any]
    ) -> None:
        """Log session activity to .agent/sessions/.

        Args:
            session_id: Unique session identifier
            action: Action performed (e.g., "get_next_feature")
            result: Result dictionary from the action
        """
        from datetime import datetime

        sessions_dir = self.project_path / ".agent" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "session_id": session_id,
            "action": action,
            "result": result
        }

        # Write to session-specific file
        session_file = sessions_dir / f"{session_id}.json"

        # Append to existing or create new
        existing = []
        if session_file.exists():
            try:
                existing = json.loads(session_file.read_text())
                if not isinstance(existing, list):
                    existing = [existing]
            except json.JSONDecodeError:
                existing = []

        existing.append(log_entry)
        session_file.write_text(json.dumps(existing, indent=2))
```

#### 🔵 Refactor: Improve Code

Extract timestamp generation, add optional log rotation.

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red)
- [ ] Test passes (Green)
- [ ] All tests pass

**Manual:**
- [ ] Session logs appear in real project

---

## Behavior 7: Helper Methods for BeadsController

### Test Specification

**Given**: BeadsController needs additional methods
**When**: `get_ready_issue()` and `update_status()` are called
**Then**: They execute correct bd CLI commands

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `planning_pipeline/tests/test_beads_controller.py`

```python
import pytest
from unittest.mock import patch
from planning_pipeline.beads_controller import BeadsController


class TestBeadsControllerExtensions:
    """Tests for new BeadsController methods."""

    def test_get_ready_issue_calls_bd_ready(self, tmp_path):
        """Given bd ready works, returns ready issue."""
        mock_result = {
            "success": True,
            "data": [{"id": "ready-1", "title": "Ready Issue"}]
        }

        with patch.object(BeadsController, '_run_bd', return_value=mock_result) as mock_bd:
            bd = BeadsController(tmp_path)
            result = bd.get_ready_issue(limit=1)

            mock_bd.assert_called_with('ready', '--limit=1')
            assert result["success"]
            assert result["data"][0]["id"] == "ready-1"

    def test_update_status_calls_bd_update(self, tmp_path):
        """Given issue id and status, calls bd update."""
        mock_result = {"success": True, "data": {"id": "issue-1", "status": "in_progress"}}

        with patch.object(BeadsController, '_run_bd', return_value=mock_result) as mock_bd:
            bd = BeadsController(tmp_path)
            result = bd.update_status("issue-1", "in_progress")

            mock_bd.assert_called_with('update', 'issue-1', '--status=in_progress')
            assert result["success"]

    def test_show_issue_calls_bd_show(self, tmp_path):
        """Given issue id, calls bd show."""
        mock_result = {"success": True, "data": {"id": "issue-1", "title": "Test", "description": "..."}}

        with patch.object(BeadsController, '_run_bd', return_value=mock_result) as mock_bd:
            bd = BeadsController(tmp_path)
            result = bd.show_issue("issue-1")

            mock_bd.assert_called_with('show', 'issue-1')
            assert result["success"]
```

#### 🟢 Green: Minimal Implementation

**File**: `planning_pipeline/beads_controller.py`

```python
    def get_ready_issue(self, limit: int = 1) -> dict[str, Any]:
        """Get next ready issue (no blockers, dependencies met)."""
        return self._run_bd('ready', f'--limit={limit}')

    def update_status(self, issue_id: str, status: str) -> dict[str, Any]:
        """Update issue status."""
        return self._run_bd('update', issue_id, f'--status={status}')

    def show_issue(self, issue_id: str) -> dict[str, Any]:
        """Get full issue details."""
        return self._run_bd('show', issue_id)
```

#### 🔵 Refactor: Improve Code

Already minimal.

### Success Criteria

**Automated:**
- [ ] Tests pass for all new methods
- [ ] Existing tests still pass

**Manual:**
- [ ] Methods work with real bd CLI

---

## Integration & E2E Testing

### Integration Test: Full Orchestration Flow

```python
class TestIntegratedOrchestratorFlow:
    """Integration tests for full orchestration workflow."""

    def test_full_workflow_with_mocked_beads(self, tmp_path):
        """Test complete workflow: get_project_info -> get_status -> get_next -> sync."""
        # Setup mock overview file
        plans_dir = tmp_path / "thoughts" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        overview = plans_dir / "2026-01-01-00-overview.md"
        overview.write_text("# Test Plan\n\n## Tech Stack\nPython, pytest")

        # Mock all external calls
        with patch('planning_pipeline.integrated_orchestrator.run_claude_sync') as mock_claude:
            mock_claude.return_value = {
                "success": True,
                "output": '{"name": "Test", "stack": "Python", "description": "Test project"}'
            }

            with patch.object(BeadsController, '_run_bd') as mock_bd:
                # Mock responses for different commands
                def bd_side_effect(*args, **kwargs):
                    cmd = args[0] if args else ""
                    if cmd == "list":
                        return {"success": True, "data": [
                            {"id": "p1", "status": "open", "dependencies": []},
                            {"id": "p2", "status": "open", "dependencies": [{"depends_on_id": "p1"}]}
                        ]}
                    elif cmd == "ready":
                        return {"success": True, "data": [{"id": "p1", "priority": 1}]}
                    elif cmd == "sync":
                        return {"success": True, "output": "Synced"}
                    return {"success": True, "data": {}}

                mock_bd.side_effect = bd_side_effect

                orchestrator = IntegratedOrchestrator(tmp_path)

                # Execute workflow
                info = orchestrator.get_project_info()
                assert info["name"] == "Test"

                status = orchestrator.get_feature_status()
                assert status["total"] == 2

                feature = orchestrator.get_next_feature()
                assert feature["id"] == "p1"

                sync_result = orchestrator.sync_features_with_git()
                assert sync_result == 0
```

### E2E Test Scenario (Manual)

1. Create a real project with `bd init`
2. Run planning pipeline to create phases
3. Use `IntegratedOrchestrator` to:
   - Detect project info from overview
   - Get feature status
   - Get next ready feature
   - Mark feature in progress
   - Complete feature
   - Sync with git

---

## References

- Ticket: N/A (Research-driven task)
- Research: `thoughts/searchable/shared/research/2026-01-01-planning-orchestrator-integration.md`
- Patterns:
  - `planning_pipeline/pipeline.py:12-241` - PlanningPipeline class structure
  - `planning_pipeline/beads_controller.py:9-91` - BeadsController patterns
  - `orchestrator.py:322-502` - Original functions being replaced
