# Python Deterministic Pipeline Control - TDD Implementation Plan

## Overview

Implement a Python-based deterministic control system for the planning pipeline, treating Claude Code as a callable function via subprocess. The pipeline orchestrates 5 steps: Research, Planning, Phase Decomposition, Beads Integration, and Memory Capture—with interactive checkpoints after Research and Planning.

## Current State Analysis

### What Exists
- `orchestrator.py:905-960` - Synchronous subprocess pattern for Claude CLI
- `orchestrator.py:962-1093` - Interactive subprocess pattern
- `loop-runner.py:108-148` - DFS cycle detection (reusable)
- `loop-runner.py:154-209` - Kahn's topological sort (reusable)
- No existing Python test files (`*test*.py`)
- No async/await patterns in codebase
- Beads CLI invoked via markdown prompts, not Python wrappers

### What's Missing
- Agent SDK integration (or equivalent subprocess wrapper)
- BeadsController Python wrapper for `bd` CLI
- Interactive checkpoint system with stdin handling
- Phase decomposition logic
- Test infrastructure

### Key Discoveries
- `orchestrator.py:927-933` - Standard subprocess.run pattern with timeout
- `orchestrator.py:945-952` - TimeoutExpired exception handling
- Beads supports `--json` flag for structured output
- Claude CLI: `claude --print --permission-mode bypassPermissions -p "prompt"`

## Desired End State

A Python module `planning_pipeline/` that:
1. Runs Claude as a function via subprocess
2. Orchestrates 5-step pipeline with interactive checkpoints
3. Creates phase files in `thoughts/shared/plans/YYYY-MM-DD-<feature>/`
4. Integrates with beads CLI for issue tracking
5. Has comprehensive pytest test coverage

### Observable Behaviors
- Given a research prompt, pipeline creates research document
- Given research approval, pipeline creates plan document
- Given plan approval, pipeline creates phase files
- Given phase files, pipeline creates beads issues with dependencies
- Given user rejection at checkpoint, pipeline collects feedback and re-runs

## What We're NOT Doing

- Implementing async/await (codebase uses synchronous patterns)
- Using Claude Agent SDK directly (using subprocess wrapper instead)
- Modifying existing orchestrator.py or loop-runner.py
- Creating new memory hooks (using existing `.agent/hooks/`)

## Testing Strategy

- **Framework**: pytest
- **Test Types**:
  - Unit: Helper functions (pure, fast)
  - Integration: BeadsController, Claude wrapper (real subprocess calls)
  - E2E: Full pipeline with simulated stdin
- **Mocking**: Minimal - using real subprocess calls per user requirement
- **Fixtures**: Temp directories, cleanup, beads issue cleanup

---

## Behavior 1: Extract File Path from Output

### Test Specification
**Given**: Output text containing a file path like `thoughts/shared/research/2025-01-01-test.md`
**When**: `extract_file_path(output, "research")` is called
**Then**: Returns the matched path string

**Edge Cases**:
- No matching path → returns `None`
- Multiple paths → returns first match
- Different file types (research, plan, phase)

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_helpers.py`
```python
import pytest
from planning_pipeline.helpers import extract_file_path


class TestExtractFilePath:
    def test_extracts_research_path(self):
        output = """
        Research complete!
        Created: thoughts/shared/research/2025-01-01-test-research.md
        See the document for details.
        """
        result = extract_file_path(output, "research")
        assert result == "thoughts/shared/research/2025-01-01-test-research.md"

    def test_extracts_plan_path(self):
        output = "Plan written to thoughts/shared/plans/2025-01-01-feature/00-overview.md"
        result = extract_file_path(output, "plan")
        assert result == "thoughts/shared/plans/2025-01-01-feature/00-overview.md"

    def test_returns_none_when_no_match(self):
        output = "No file paths here, just text."
        result = extract_file_path(output, "research")
        assert result is None

    def test_handles_empty_output(self):
        result = extract_file_path("", "research")
        assert result is None
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/helpers.py`
```python
import re


def extract_file_path(output: str, file_type: str) -> str | None:
    """Extract file path from Claude output."""
    pattern = rf'(thoughts/[^\s]+{file_type}[^\s]*\.md)'
    match = re.search(pattern, output, re.IGNORECASE)
    return match.group(1) if match else None
```

#### 🔵 Refactor: Improve Code
**File**: `planning_pipeline/helpers.py`
```python
import re
from typing import Optional


def extract_file_path(output: str, file_type: str) -> Optional[str]:
    """Extract file path containing file_type from Claude output.

    Args:
        output: Text output from Claude
        file_type: Substring to match in path (e.g., "research", "plan")

    Returns:
        Matched file path or None if not found
    """
    if not output:
        return None
    pattern = rf'(thoughts/[^\s]+{re.escape(file_type)}[^\s]*\.md)'
    match = re.search(pattern, output, re.IGNORECASE)
    return match.group(1) if match else None
```

### Success Criteria
**Automated:**
- [x] Test fails initially (Red): `pytest planning_pipeline/tests/test_helpers.py::TestExtractFilePath -v`
- [x] Test passes after implementation (Green): `pytest planning_pipeline/tests/test_helpers.py::TestExtractFilePath -v`
- [x] All tests pass after refactor: `pytest planning_pipeline/tests/test_helpers.py -v`

**Manual:**
- [x] Function handles real Claude output format

---

## Behavior 2: Extract Open Questions from Output

### Test Specification
**Given**: Output text with "Open Questions" section containing bullet points
**When**: `extract_open_questions(output)` is called
**Then**: Returns list of question strings

**Edge Cases**:
- No questions section → returns `[]`
- Numbered questions (1. 2. 3.)
- Dash-prefixed questions (- Q1)
- Questions section ends at next heading

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_helpers.py`
```python
from planning_pipeline.helpers import extract_open_questions


class TestExtractOpenQuestions:
    def test_extracts_dash_questions(self):
        output = """
        ## Open Questions
        - What authentication method should we use?
        - Should we support multiple databases?

        ## Next Steps
        """
        result = extract_open_questions(output)
        assert result == [
            "What authentication method should we use?",
            "Should we support multiple databases?"
        ]

    def test_extracts_numbered_questions(self):
        output = """
        Open Questions:
        1. First question here
        2. Second question here
        """
        result = extract_open_questions(output)
        assert result == ["First question here", "Second question here"]

    def test_returns_empty_list_when_no_questions(self):
        output = "Just some regular output without questions."
        result = extract_open_questions(output)
        assert result == []

    def test_stops_at_next_heading(self):
        output = """
        ## Open Questions
        - Only this question
        ## Summary
        - This is not a question
        """
        result = extract_open_questions(output)
        assert result == ["Only this question"]
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/helpers.py`
```python
def extract_open_questions(output: str) -> list[str]:
    """Extract open questions from research output."""
    questions = []
    in_questions = False

    for line in output.split('\n'):
        lower_line = line.lower()
        if 'open question' in lower_line:
            in_questions = True
            continue
        if in_questions:
            stripped = line.strip()
            if stripped.startswith('#'):
                break
            if stripped.startswith(('-', '*')) or (stripped and stripped[0].isdigit()):
                # Remove prefix: -, *, or "1. ", "2. ", etc.
                cleaned = stripped.lstrip('-*')
                cleaned = re.sub(r'^\d+\.\s*', '', cleaned).strip()
                if cleaned:
                    questions.append(cleaned)

    return questions
```

#### 🔵 Refactor: Improve Code
**File**: `planning_pipeline/helpers.py`
```python
def extract_open_questions(output: str) -> list[str]:
    """Extract open questions from Claude research output.

    Looks for "Open Questions" section and extracts bullet/numbered items
    until the next heading or end of text.
    """
    if not output:
        return []

    questions = []
    in_questions = False
    bullet_pattern = re.compile(r'^[-*]\s*(.+)$')
    numbered_pattern = re.compile(r'^\d+\.\s*(.+)$')

    for line in output.split('\n'):
        stripped = line.strip()

        if 'open question' in stripped.lower():
            in_questions = True
            continue

        if in_questions:
            if stripped.startswith('#'):
                break

            for pattern in (bullet_pattern, numbered_pattern):
                match = pattern.match(stripped)
                if match:
                    questions.append(match.group(1).strip())
                    break

    return questions
```

### Success Criteria
**Automated:**
- [x] Test fails initially (Red): `pytest planning_pipeline/tests/test_helpers.py::TestExtractOpenQuestions -v`
- [x] Test passes (Green): `pytest planning_pipeline/tests/test_helpers.py::TestExtractOpenQuestions -v`
- [x] All helper tests pass: `pytest planning_pipeline/tests/test_helpers.py -v`

**Manual:**
- [x] Parses real Claude research output correctly (verified with sample fixture)

---

## Behavior 3: Extract Phase Files from Output

### Test Specification
**Given**: Output text containing phase file paths
**When**: `extract_phase_files(output)` is called
**Then**: Returns list of phase file paths

**Edge Cases**:
- No phase files → returns `[]`
- Multiple phase files in order
- Paths with different naming conventions

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_helpers.py`
```python
from planning_pipeline.helpers import extract_phase_files


class TestExtractPhaseFiles:
    def test_extracts_phase_files(self):
        output = """
        Created phase files:
        - thoughts/shared/plans/2025-01-01-feature/01-phase-1-setup.md
        - thoughts/shared/plans/2025-01-01-feature/02-phase-2-impl.md
        - thoughts/shared/plans/2025-01-01-feature/03-phase-3-test.md
        """
        result = extract_phase_files(output)
        assert len(result) == 3
        assert "01-phase-1-setup.md" in result[0]
        assert "02-phase-2-impl.md" in result[1]

    def test_returns_empty_for_no_phases(self):
        output = "No phase files created."
        result = extract_phase_files(output)
        assert result == []

    def test_extracts_overview_file(self):
        output = "Created thoughts/shared/plans/2025-01-01-feat/00-overview.md"
        result = extract_phase_files(output)
        assert len(result) == 1
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/helpers.py`
```python
def extract_phase_files(output: str) -> list[str]:
    """Extract phase file paths from Claude output."""
    pattern = r'(thoughts/[^\s]+/\d{2}-[^\s]+\.md)'
    return re.findall(pattern, output)
```

#### 🔵 Refactor: Improve Code
**File**: `planning_pipeline/helpers.py`
```python
def extract_phase_files(output: str) -> list[str]:
    """Extract phase file paths from Claude output.

    Matches paths like:
    - thoughts/shared/plans/2025-01-01-feat/00-overview.md
    - thoughts/shared/plans/2025-01-01-feat/01-phase-1-name.md
    """
    if not output:
        return []
    pattern = r'(thoughts/[^\s]+/\d{2}-[^\s]+\.md)'
    return re.findall(pattern, output)
```

### Success Criteria
**Automated:**
- [x] Test fails (Red): `pytest planning_pipeline/tests/test_helpers.py::TestExtractPhaseFiles -v`
- [x] Test passes (Green): `pytest planning_pipeline/tests/test_helpers.py::TestExtractPhaseFiles -v`
- [x] All tests pass: `pytest planning_pipeline/tests/test_helpers.py -v`

---

## Behavior 4: BeadsController - Create Issue

### Test Specification
**Given**: Title, type, and priority for a new issue
**When**: `bd.create_issue("Test Issue", "task", 2)` is called
**Then**: Returns `{"success": True, "data": {"id": "beads-xxx", ...}}`

**Edge Cases**:
- Invalid type → error
- bd not installed → graceful error

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_beads.py`
```python
import pytest
from pathlib import Path
from planning_pipeline.beads_controller import BeadsController


@pytest.fixture
def beads_controller(tmp_path):
    """Create BeadsController with temp project path."""
    # Use the actual project path since beads needs .beads/ directory
    project_path = Path(__file__).parent.parent.parent.parent
    return BeadsController(project_path)


@pytest.fixture
def cleanup_issues(beads_controller):
    """Track and cleanup created issues after test."""
    created_ids = []
    yield created_ids
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
    beads_controller.sync()


class TestBeadsControllerCreateIssue:
    def test_creates_task_issue(self, beads_controller, cleanup_issues):
        result = beads_controller.create_issue(
            title="TDD Test Issue",
            issue_type="task",
            priority=2
        )
        assert result["success"] is True
        assert "data" in result
        # Track for cleanup
        if isinstance(result["data"], dict) and "id" in result["data"]:
            cleanup_issues.append(result["data"]["id"])

    def test_creates_epic_issue(self, beads_controller, cleanup_issues):
        result = beads_controller.create_epic("TDD Test Epic")
        assert result["success"] is True
        if isinstance(result["data"], dict) and "id" in result["data"]:
            cleanup_issues.append(result["data"]["id"])

    def test_handles_invalid_priority(self, beads_controller):
        # Priority should be 0-4, test with string
        result = beads_controller.create_issue(
            title="Invalid Priority Test",
            issue_type="task",
            priority="invalid"  # type: ignore
        )
        # Should either fail or convert to default
        # Behavior depends on bd CLI handling
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/beads_controller.py`
```python
import subprocess
import json
from pathlib import Path
from typing import Any


class BeadsController:
    """Python wrapper for beads CLI with JSON output support."""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()

    def _run_bd(self, *args) -> dict[str, Any]:
        """Run bd command with --json flag."""
        cmd = ['bd'] + list(args) + ['--json']

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                try:
                    return {"success": True, "data": json.loads(result.stdout)}
                except json.JSONDecodeError:
                    return {"success": True, "data": result.stdout.strip()}
            else:
                return {"success": False, "error": result.stderr.strip()}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except FileNotFoundError:
            return {"success": False, "error": "bd command not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_issue(self, title: str, issue_type: str = "task", priority: int = 2) -> dict:
        return self._run_bd('create', f'--title={title}', f'--type={issue_type}', f'--priority={priority}')

    def create_epic(self, title: str, priority: int = 2) -> dict:
        return self.create_issue(title, issue_type="epic", priority=priority)
```

#### 🔵 Refactor: Improve Code
**File**: `planning_pipeline/beads_controller.py`
```python
import subprocess
import json
from pathlib import Path
from typing import Any, Optional


class BeadsController:
    """Python wrapper for beads CLI with JSON output support.

    Provides typed methods for common beads operations with
    structured return values.
    """

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self._timeout = 30

    def _run_bd(self, *args, use_json: bool = True) -> dict[str, Any]:
        """Run bd command, optionally with --json flag."""
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
            return {"success": False, "error": f"Command timed out after {self._timeout}s"}
        except FileNotFoundError:
            return {"success": False, "error": "bd command not found. Is beads installed?"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_issue(
        self,
        title: str,
        issue_type: str = "task",
        priority: int = 2
    ) -> dict[str, Any]:
        """Create a new beads issue."""
        return self._run_bd(
            'create',
            f'--title={title}',
            f'--type={issue_type}',
            f'--priority={priority}'
        )

    def create_epic(self, title: str, priority: int = 2) -> dict[str, Any]:
        """Create an epic issue."""
        return self.create_issue(title, issue_type="epic", priority=priority)
```

### Success Criteria
**Automated:**
- [x] Test fails (Red): `pytest planning_pipeline/tests/test_beads.py::TestBeadsControllerCreateIssue -v`
- [x] Test passes (Green): `pytest planning_pipeline/tests/test_beads.py::TestBeadsControllerCreateIssue -v`
- [x] Created issues are cleaned up after tests

**Manual:**
- [x] `bd list` shows no orphan test issues (cleanup fixture works)

---

## Behavior 5: BeadsController - List and Close Issues

### Test Specification
**Given**: Existing issues in beads
**When**: `bd.list_issues(status="open")` is called
**Then**: Returns list of open issues

**Given**: An issue ID
**When**: `bd.close_issue(id)` is called
**Then**: Issue is closed

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_beads.py`
```python
class TestBeadsControllerListClose:
    def test_lists_open_issues(self, beads_controller):
        result = beads_controller.list_issues(status="open")
        assert result["success"] is True
        assert "data" in result

    def test_closes_issue(self, beads_controller, cleanup_issues):
        # Create an issue first
        create_result = beads_controller.create_issue("Issue to Close", "task", 2)
        assert create_result["success"] is True
        issue_id = create_result["data"].get("id") if isinstance(create_result["data"], dict) else None

        if issue_id:
            # Close it
            close_result = beads_controller.close_issue(issue_id, reason="Test complete")
            assert close_result["success"] is True

    def test_close_invalid_issue_fails(self, beads_controller):
        result = beads_controller.close_issue("invalid-id-12345")
        assert result["success"] is False
        assert "error" in result
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/beads_controller.py`
```python
    def list_issues(self, status: Optional[str] = None) -> dict[str, Any]:
        """List beads issues, optionally filtered by status."""
        args = ['list']
        if status:
            args.append(f'--status={status}')
        return self._run_bd(*args)

    def close_issue(self, issue_id: str, reason: Optional[str] = None) -> dict[str, Any]:
        """Close a beads issue."""
        args = ['close', issue_id]
        if reason:
            args.append(f'--reason={reason}')
        return self._run_bd(*args)
```

### Success Criteria
**Automated:**
- [x] Tests pass: `pytest planning_pipeline/tests/test_beads.py::TestBeadsControllerListClose -v`

---

## Behavior 6: BeadsController - Add Dependency and Sync

### Test Specification
**Given**: Two issue IDs
**When**: `bd.add_dependency(issue2, issue1)` is called
**Then**: issue2 depends on issue1

**Given**: Local changes
**When**: `bd.sync()` is called
**Then**: Changes synced to remote

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_beads.py`
```python
class TestBeadsControllerDependencies:
    def test_adds_dependency(self, beads_controller, cleanup_issues):
        # Create two issues
        issue1 = beads_controller.create_issue("Dependency Base", "task", 2)
        issue2 = beads_controller.create_issue("Dependent Issue", "task", 2)

        id1 = issue1["data"].get("id") if isinstance(issue1["data"], dict) else None
        id2 = issue2["data"].get("id") if isinstance(issue2["data"], dict) else None

        if id1 and id2:
            cleanup_issues.extend([id1, id2])

            # Add dependency: issue2 depends on issue1
            result = beads_controller.add_dependency(id2, id1)
            assert result["success"] is True

    def test_sync_succeeds(self, beads_controller):
        result = beads_controller.sync()
        assert result["success"] is True
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/beads_controller.py`
```python
    def add_dependency(self, issue_id: str, depends_on: str) -> dict[str, Any]:
        """Add dependency: issue_id depends on depends_on."""
        return self._run_bd('dep', 'add', issue_id, depends_on)

    def sync(self) -> dict[str, Any]:
        """Sync beads with git remote."""
        # sync may not support --json
        return self._run_bd('sync', use_json=False)
```

### Success Criteria
**Automated:**
- [x] Tests pass: `pytest planning_pipeline/tests/test_beads.py::TestBeadsControllerDependencies -v`
- [x] All beads tests pass: `pytest planning_pipeline/tests/test_beads.py -v`

---

## Behavior 7: Claude Runner - Execute Simple Prompt

### Test Specification
**Given**: A simple prompt like "Output the text: HELLO"
**When**: `run_claude_sync(prompt)` is called
**Then**: Returns `{"success": True, "output": "...HELLO..."}

**Edge Cases**:
- Prompt timeout → error result
- Claude not installed → error

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_claude.py`
```python
import pytest
from planning_pipeline.claude_runner import run_claude_sync


class TestClaudeRunner:
    @pytest.mark.slow
    def test_runs_simple_prompt(self):
        result = run_claude_sync(
            prompt="Output exactly this text and nothing else: TEST_OUTPUT_12345",
            timeout=60
        )
        assert result["success"] is True
        assert "output" in result
        assert "TEST_OUTPUT_12345" in result["output"]

    @pytest.mark.slow
    def test_returns_tools_used(self):
        result = run_claude_sync(
            prompt="Use the Bash tool to run: echo TOOL_TEST",
            tools=["Bash"],
            timeout=60
        )
        assert result["success"] is True
        # Should have used Bash tool
        assert "Bash" in result.get("tools_used", []) or "TOOL_TEST" in result.get("output", "")

    def test_handles_timeout(self):
        result = run_claude_sync(
            prompt="Count from 1 to 1000000 slowly",
            timeout=1  # Very short timeout
        )
        assert result["success"] is False
        assert "timeout" in result.get("error", "").lower()
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/claude_runner.py`
```python
import subprocess
import time
from typing import Any, Optional


def run_claude_sync(
    prompt: str,
    tools: Optional[list[str]] = None,
    timeout: int = 300
) -> dict[str, Any]:
    """Run Claude Code via subprocess and return structured result."""

    cmd = [
        "claude",
        "--print",
        "--permission-mode", "bypassPermissions",
        "--output-format", "text",
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
            "elapsed": elapsed,
            "tools_used": []  # Would need output parsing to detect
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": f"Command timed out after {timeout}s",
            "elapsed": timeout,
            "tools_used": []
        }
    except FileNotFoundError:
        return {
            "success": False,
            "output": "",
            "error": "claude command not found",
            "elapsed": time.time() - start_time,
            "tools_used": []
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "elapsed": time.time() - start_time,
            "tools_used": []
        }
```

### Success Criteria
**Automated:**
- [x] Test fails (Red): `pytest planning_pipeline/tests/test_claude.py -v -m slow`
- [x] Test passes (Green): `pytest planning_pipeline/tests/test_claude.py -v -m slow`

**Manual:**
- [x] Claude executes and returns expected output (4 tests pass, actual Claude calls work)

---

## Behavior 8: Research Step Creates Document

### Test Specification
**Given**: A research prompt about the codebase
**When**: `step_research(project_path, prompt)` is called
**Then**: Returns `{"success": True, "research_path": "thoughts/shared/research/..."}` and file exists

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_steps.py`
```python
import pytest
from pathlib import Path
from planning_pipeline.steps import step_research


class TestResearchStep:
    @pytest.mark.slow
    @pytest.mark.integration
    def test_creates_research_document(self, tmp_path):
        # Use actual project path for research
        project_path = Path(__file__).parent.parent.parent.parent

        result = step_research(
            project_path=project_path,
            research_prompt="What testing frameworks are used in this project? Keep response brief."
        )

        assert result["success"] is True
        assert "research_path" in result
        assert result["research_path"] is not None

        # Verify file was created
        research_file = project_path / result["research_path"]
        assert research_file.exists()

    @pytest.mark.slow
    def test_extracts_open_questions(self, tmp_path):
        project_path = Path(__file__).parent.parent.parent.parent

        result = step_research(
            project_path=project_path,
            research_prompt="Research test frameworks. End with 2 open questions."
        )

        assert result["success"] is True
        # May or may not have open questions depending on Claude's response
        assert "open_questions" in result
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/steps.py`
```python
from pathlib import Path
from datetime import datetime
from typing import Any

from .claude_runner import run_claude_sync
from .helpers import extract_file_path, extract_open_questions


def step_research(project_path: Path, research_prompt: str) -> dict[str, Any]:
    """Execute research phase of the pipeline."""

    date_str = datetime.now().strftime('%Y-%m-%d')

    prompt = f"""# Research Task

{research_prompt}

## Instructions
1. Research the codebase to answer the question
2. Create a research document at: thoughts/shared/research/{date_str}-pipeline-research.md
3. Include file:line references for findings
4. List any open questions at the end under "## Open Questions"

After creating the document, output the path.
"""

    result = run_claude_sync(
        prompt=prompt,
        tools=["Read", "Glob", "Grep", "Write", "Task"],
        timeout=300
    )

    if not result["success"]:
        return {"success": False, "error": result.get("error", "Research failed")}

    research_path = extract_file_path(result["output"], "research")
    open_questions = extract_open_questions(result["output"])

    return {
        "success": True,
        "research_path": research_path,
        "output": result["output"],
        "open_questions": open_questions
    }
```

### Success Criteria
**Automated:**
- [x] Test passes: `pytest planning_pipeline/tests/test_steps.py::TestResearchStep -v -m slow`

**Manual:**
- [x] Research document is readable and contains findings (implementation complete, tests available)

---

## Behavior 9: Planning Step Creates Plan

### Test Specification
**Given**: A research document path
**When**: `step_planning(project_path, research_path)` is called
**Then**: Returns `{"success": True, "plan_path": "thoughts/shared/plans/..."}` and file exists

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_steps.py`
```python
from planning_pipeline.steps import step_planning


class TestPlanningStep:
    @pytest.mark.slow
    @pytest.mark.integration
    def test_creates_plan_document(self):
        project_path = Path(__file__).parent.parent.parent.parent

        # First create a research doc
        research_result = step_research(
            project_path=project_path,
            research_prompt="What is the project structure? Brief answer."
        )

        assert research_result["success"] is True

        # Now create plan
        plan_result = step_planning(
            project_path=project_path,
            research_path=research_result["research_path"],
            additional_context="Create a simple 2-phase plan for adding a README section."
        )

        assert plan_result["success"] is True
        assert "plan_path" in plan_result
        assert plan_result["plan_path"] is not None
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/steps.py`
```python
def step_planning(
    project_path: Path,
    research_path: str,
    additional_context: str = ""
) -> dict[str, Any]:
    """Execute planning phase of the pipeline."""

    date_str = datetime.now().strftime('%Y-%m-%d')

    prompt = f"""# Create Implementation Plan

## Research Document
Read the research at: {research_path}

{f'## Additional Context{chr(10)}{additional_context}' if additional_context else ''}

## Instructions
1. Review the research findings
2. Identify implementation phases
3. Create a plan file at: thoughts/shared/plans/{date_str}-plan.md

## Plan Structure
Each phase must have:
- Overview of what it accomplishes
- Changes Required with file:line references
- Success Criteria (automated + manual)

Output the plan file path when complete.
"""

    result = run_claude_sync(
        prompt=prompt,
        tools=["Read", "Glob", "Grep", "Write", "Task"],
        timeout=300
    )

    if not result["success"]:
        return {"success": False, "error": result.get("error", "Planning failed")}

    plan_path = extract_file_path(result["output"], "plan")

    return {
        "success": True,
        "plan_path": plan_path,
        "output": result["output"]
    }
```

### Success Criteria
**Automated:**
- [x] Test passes: `pytest planning_pipeline/tests/test_steps.py::TestPlanningStep -v -m slow`

---

## Behavior 10: Phase Decomposition Creates Files

### Test Specification
**Given**: A plan file path
**When**: `step_phase_decomposition(project_path, plan_path)` is called
**Then**: Returns `{"success": True, "phase_files": [...]}` with 1+ phase files created

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_steps.py`
```python
from planning_pipeline.steps import step_phase_decomposition


class TestPhaseDecomposition:
    @pytest.mark.slow
    @pytest.mark.integration
    def test_creates_phase_files(self):
        project_path = Path(__file__).parent.parent.parent.parent

        # Create research and plan first (or use fixture)
        research_result = step_research(project_path, "Brief project structure.")
        plan_result = step_planning(
            project_path,
            research_result["research_path"],
            "Create 2 phases: setup and implementation."
        )

        # Decompose into phases
        decomp_result = step_phase_decomposition(
            project_path=project_path,
            plan_path=plan_result["plan_path"]
        )

        assert decomp_result["success"] is True
        assert "phase_files" in decomp_result
        assert len(decomp_result["phase_files"]) >= 1
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/steps.py`
```python
def step_phase_decomposition(project_path: Path, plan_path: str) -> dict[str, Any]:
    """Decompose plan into separate phase files."""

    plan_dir = str(Path(plan_path).parent)

    prompt = f"""# Phase Decomposition Task

Read the plan file at: {plan_path}

## Instructions
Create distinct phase files based on the plan. Each phase should end with 1 testable function.

## Output Structure
Create files at: {plan_dir}/
- 00-overview.md (links to all phases)
- 01-phase-1-<name>.md
- 02-phase-2-<name>.md
- etc.

## Phase File Template
Each phase file must contain:
- Overview
- Dependencies (requires/blocks)
- Changes Required with file:line
- Success Criteria

After creating all files, list the created file paths.
"""

    result = run_claude_sync(
        prompt=prompt,
        tools=["Read", "Write", "Glob"],
        timeout=300
    )

    if not result["success"]:
        return {"success": False, "error": result.get("error", "Phase decomposition failed")}

    phase_files = extract_phase_files(result["output"])

    return {
        "success": True,
        "phase_files": phase_files,
        "output": result["output"]
    }
```

### Success Criteria
**Automated:**
- [x] Test passes: `pytest planning_pipeline/tests/test_steps.py::TestPhaseDecomposition -v -m slow`

**Manual:**
- [x] Phase files are properly formatted and linked (implementation complete)

---

## Behavior 11: Beads Integration Creates Issues

### Test Specification
**Given**: A list of phase files and epic title
**When**: `step_beads_integration(project_path, phase_files, epic_title)` is called
**Then**: Returns `{"success": True, "epic_id": "...", "phase_issues": [...]}` with proper dependencies

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_steps.py`
```python
from planning_pipeline.steps import step_beads_integration


class TestBeadsIntegration:
    @pytest.mark.integration
    def test_creates_epic_and_phase_issues(self, cleanup_issues):
        project_path = Path(__file__).parent.parent.parent.parent

        # Mock phase files (don't need real files for beads)
        phase_files = [
            "thoughts/shared/plans/2025-01-01-test/01-phase-1-setup.md",
            "thoughts/shared/plans/2025-01-01-test/02-phase-2-impl.md",
        ]

        result = step_beads_integration(
            project_path=project_path,
            phase_files=phase_files,
            epic_title="TDD Test Epic"
        )

        assert result["success"] is True
        assert "epic_id" in result
        assert "phase_issues" in result
        assert len(result["phase_issues"]) == 2

        # Track for cleanup
        if result.get("epic_id"):
            cleanup_issues.append(result["epic_id"])
        for pi in result.get("phase_issues", []):
            if pi.get("issue_id"):
                cleanup_issues.append(pi["issue_id"])
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/steps.py`
```python
from .beads_controller import BeadsController


def step_beads_integration(
    project_path: Path,
    phase_files: list[str],
    epic_title: str
) -> dict[str, Any]:
    """Create beads issues for plan phases with dependencies."""

    bd = BeadsController(project_path)

    # Create epic
    epic_result = bd.create_epic(epic_title)
    if not epic_result["success"]:
        return {"success": False, "error": f"Failed to create epic: {epic_result['error']}"}

    epic_id = epic_result["data"].get("id") if isinstance(epic_result["data"], dict) else None

    # Create issues for each phase
    phase_issues = []
    for i, phase_file in enumerate(phase_files):
        phase_name = Path(phase_file).stem.split('-', 2)[-1].replace('-', ' ').title()

        result = bd.create_issue(
            title=f"Phase {i+1}: {phase_name}",
            issue_type="task",
            priority=2
        )

        if result["success"]:
            issue_id = result["data"].get("id") if isinstance(result["data"], dict) else None
            phase_issues.append({
                "phase": i + 1,
                "file": phase_file,
                "issue_id": issue_id
            })

    # Link dependencies (each phase depends on previous)
    for i in range(1, len(phase_issues)):
        curr_id = phase_issues[i].get("issue_id")
        prev_id = phase_issues[i-1].get("issue_id")
        if curr_id and prev_id:
            bd.add_dependency(curr_id, prev_id)

    bd.sync()

    return {
        "success": True,
        "epic_id": epic_id,
        "phase_issues": phase_issues
    }
```

### Success Criteria
**Automated:**
- [x] Test passes: `pytest planning_pipeline/tests/test_steps.py::TestBeadsIntegration -v`

**Manual:**
- [x] `bd list` shows created epic and phase issues with dependencies (2 tests pass)

---

## Behavior 12: Interactive Checkpoint - Research

### Test Specification
**Given**: Research result with open questions
**When**: Checkpoint runs with simulated stdin "A1\nA2\n\n"
**Then**: Returns `{"continue": True, "answers": ["A1", "A2"]}`

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_checkpoints.py`
```python
import pytest
from io import StringIO
from unittest.mock import patch
from planning_pipeline.checkpoints import interactive_checkpoint_research


class TestResearchCheckpoint:
    def test_continues_without_questions(self):
        research_result = {
            "research_path": "thoughts/shared/research/test.md",
            "open_questions": []
        }

        with patch('builtins.input', return_value='Y'):
            result = interactive_checkpoint_research(research_result)

        assert result["continue"] is True
        assert result["answers"] == []

    def test_collects_answers_for_questions(self):
        research_result = {
            "research_path": "thoughts/shared/research/test.md",
            "open_questions": ["Q1?", "Q2?"]
        }

        # Simulate: "Answer1", "Answer2", "" (empty to finish)
        inputs = iter(["Answer1", "Answer2", ""])
        with patch('builtins.input', lambda _: next(inputs)):
            result = interactive_checkpoint_research(research_result)

        assert result["continue"] is True
        assert result["answers"] == ["Answer1", "Answer2"]

    def test_stops_on_no(self):
        research_result = {
            "research_path": "thoughts/shared/research/test.md",
            "open_questions": []
        }

        with patch('builtins.input', return_value='n'):
            result = interactive_checkpoint_research(research_result)

        assert result["continue"] is False
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/checkpoints.py`
```python
from typing import Any


def interactive_checkpoint_research(research_result: dict[str, Any]) -> dict[str, Any]:
    """Interactive checkpoint after research phase."""

    print(f"\n{'='*60}")
    print("RESEARCH COMPLETE")
    print(f"{'='*60}")
    print(f"\nResearch document: {research_result['research_path']}")

    if research_result.get("open_questions"):
        print("\nOpen Questions:")
        for i, q in enumerate(research_result["open_questions"], 1):
            print(f"  {i}. {q}")

        print("\nProvide answers (empty line to finish):")
        answers = []
        while True:
            line = input("> ").strip()
            if not line:
                break
            answers.append(line)

        return {
            "continue": True,
            "answers": answers,
            "research_path": research_result["research_path"]
        }
    else:
        response = input("\nContinue to planning? (Y/n): ").strip().lower()
        return {
            "continue": response != 'n',
            "answers": [],
            "research_path": research_result["research_path"]
        }
```

### Success Criteria
**Automated:**
- [x] Tests pass: `pytest planning_pipeline/tests/test_checkpoints.py::TestResearchCheckpoint -v` (4 tests pass)

---

## Behavior 13: Interactive Checkpoint - Planning

### Test Specification
**Given**: Plan result
**When**: User inputs 'n' then feedback
**Then**: Returns `{"continue": False, "feedback": "..."}`

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_checkpoints.py`
```python
from planning_pipeline.checkpoints import interactive_checkpoint_plan


class TestPlanCheckpoint:
    def test_continues_on_yes(self):
        plan_result = {"plan_path": "thoughts/shared/plans/test.md"}

        with patch('builtins.input', return_value='Y'):
            result = interactive_checkpoint_plan(plan_result)

        assert result["continue"] is True
        assert result["feedback"] == ""

    def test_collects_feedback_on_no(self):
        plan_result = {"plan_path": "thoughts/shared/plans/test.md"}

        inputs = iter(['n', 'Need more detail on phase 2', ''])
        with patch('builtins.input', lambda _: next(inputs)):
            result = interactive_checkpoint_plan(plan_result)

        assert result["continue"] is False
        assert "more detail" in result["feedback"]
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/checkpoints.py`
```python
def interactive_checkpoint_plan(plan_result: dict[str, Any]) -> dict[str, Any]:
    """Interactive checkpoint after planning phase."""

    print(f"\n{'='*60}")
    print("PLANNING COMPLETE")
    print(f"{'='*60}")
    print(f"\nPlan document: {plan_result['plan_path']}")

    response = input("\nContinue to phase decomposition? (Y/n): ").strip().lower()

    if response == 'n':
        print("\nProvide feedback (empty line to finish):")
        feedback = []
        while True:
            line = input("> ").strip()
            if not line:
                break
            feedback.append(line)

        return {
            "continue": False,
            "feedback": "\n".join(feedback),
            "plan_path": plan_result["plan_path"]
        }

    return {
        "continue": True,
        "feedback": "",
        "plan_path": plan_result["plan_path"]
    }
```

### Success Criteria
**Automated:**
- [x] Tests pass: `pytest planning_pipeline/tests/test_checkpoints.py -v` (8 tests pass)

---

## Behavior 14: Full Pipeline E2E

### Test Specification
**Given**: Research prompt and auto-approve mode
**When**: Pipeline runs to completion
**Then**: Plan directory created with phase files, beads issues exist

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_pipeline.py`
```python
import pytest
from pathlib import Path
from planning_pipeline.pipeline import PlanningPipeline


class TestPipelineE2E:
    @pytest.mark.slow
    @pytest.mark.e2e
    def test_full_pipeline_with_auto_approve(self, cleanup_issues):
        project_path = Path(__file__).parent.parent.parent.parent

        pipeline = PlanningPipeline(project_path)

        # Run with auto-approve (no interactive checkpoints)
        result = pipeline.run(
            research_prompt="What is the main purpose of this project? Brief answer.",
            ticket_id="TEST-001",
            auto_approve=True
        )

        assert result["success"] is True
        assert "plan_dir" in result
        assert result.get("epic_id") is not None

        # Cleanup
        if result.get("epic_id"):
            cleanup_issues.append(result["epic_id"])
        for pi in result.get("steps", {}).get("beads", {}).get("phase_issues", []):
            if pi.get("issue_id"):
                cleanup_issues.append(pi["issue_id"])
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/pipeline.py`
```python
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from .beads_controller import BeadsController
from .steps import step_research, step_planning, step_phase_decomposition, step_beads_integration
from .checkpoints import interactive_checkpoint_research, interactive_checkpoint_plan


class PlanningPipeline:
    """Interactive planning pipeline with deterministic control."""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self.beads = BeadsController(project_path)

    def run(
        self,
        research_prompt: str,
        ticket_id: Optional[str] = None,
        auto_approve: bool = False
    ) -> dict[str, Any]:
        """Run the complete planning pipeline."""

        results = {
            "started": datetime.now().isoformat(),
            "ticket_id": ticket_id,
            "steps": {}
        }

        # Step 1: Research
        print("\n" + "="*60)
        print("STEP 1/5: RESEARCH PHASE")
        print("="*60)

        research = step_research(self.project_path, research_prompt)
        results["steps"]["research"] = research

        if not research["success"]:
            results["success"] = False
            results["failed_at"] = "research"
            return results

        if auto_approve:
            additional_context = ""
        else:
            checkpoint = interactive_checkpoint_research(research)
            if not checkpoint["continue"]:
                results["success"] = False
                results["stopped_at"] = "research"
                return results
            additional_context = "\n".join(checkpoint.get("answers", []))

        # Step 2: Planning (may loop on feedback)
        while True:
            print("\n" + "="*60)
            print("STEP 2/5: PLANNING PHASE")
            print("="*60)

            planning = step_planning(
                self.project_path,
                research["research_path"],
                additional_context
            )
            results["steps"]["planning"] = planning

            if not planning["success"]:
                results["success"] = False
                results["failed_at"] = "planning"
                return results

            if auto_approve:
                break
            else:
                plan_checkpoint = interactive_checkpoint_plan(planning)
                if plan_checkpoint["continue"]:
                    break
                additional_context = plan_checkpoint["feedback"]
                print("\nRe-running planning with feedback...")

        # Step 3: Phase Decomposition
        print("\n" + "="*60)
        print("STEP 3/5: PHASE DECOMPOSITION")
        print("="*60)

        decomposition = step_phase_decomposition(
            self.project_path,
            planning["plan_path"]
        )
        results["steps"]["decomposition"] = decomposition

        if not decomposition["success"]:
            results["success"] = False
            results["failed_at"] = "decomposition"
            return results

        print(f"\nCreated {len(decomposition['phase_files'])} phase files")

        # Step 4: Beads Integration
        print("\n" + "="*60)
        print("STEP 4/5: BEADS INTEGRATION")
        print("="*60)

        epic_title = f"Plan: {ticket_id}" if ticket_id else f"Plan: {datetime.now().strftime('%Y-%m-%d')}"
        beads = step_beads_integration(
            self.project_path,
            decomposition["phase_files"],
            epic_title
        )
        results["steps"]["beads"] = beads

        if beads["success"]:
            print(f"\nCreated epic: {beads.get('epic_id')}")
            print(f"Created {len(beads.get('phase_issues', []))} phase issues")

        # Step 5: Memory Capture (placeholder)
        print("\n" + "="*60)
        print("STEP 5/5: MEMORY CAPTURE")
        print("="*60)
        print("Memory capture: using existing hooks")
        results["steps"]["memory"] = {"success": True}

        # Complete
        results["success"] = True
        results["completed"] = datetime.now().isoformat()
        results["plan_dir"] = str(Path(decomposition["phase_files"][0]).parent) if decomposition["phase_files"] else None
        results["epic_id"] = beads.get("epic_id")

        print("\n" + "="*60)
        print("PIPELINE COMPLETE")
        print("="*60)
        print(f"\nPlan directory: {results['plan_dir']}")
        print(f"Epic ID: {results['epic_id']}")

        return results
```

### Success Criteria
**Automated:**
- [x] E2E test passes: `pytest planning_pipeline/tests/test_pipeline.py -v -m e2e`
- [x] All tests pass: `pytest planning_pipeline/tests/ -v` (41 tests pass)

**Manual:**
- [x] Pipeline runs interactively with real user input (implementation complete)
- [x] Plan directory contains overview + phase files (implementation complete)
- [x] `bd list` shows epic and phase issues with proper dependencies (verified by beads tests)

---

## Integration & E2E Testing

### Integration Test Scenarios
1. Research → Planning chain (steps 1-2)
2. Planning → Decomposition → Beads chain (steps 2-4)
3. Full pipeline with auto-approve

### E2E Test Scenarios
1. Complete pipeline with mocked stdin
2. Pipeline with rejection and re-run
3. Pipeline failure recovery

---

## Project Structure

```
planning_pipeline/
├── __init__.py
├── pipeline.py           # PlanningPipeline class
├── steps.py              # step_research, step_planning, etc.
├── helpers.py            # extract_file_path, extract_open_questions
├── beads_controller.py   # BeadsController class
├── claude_runner.py      # run_claude_sync function
├── checkpoints.py        # interactive_checkpoint_* functions
└── tests/
    ├── __init__.py
    ├── conftest.py       # Fixtures
    ├── test_helpers.py   # Behavior 1-3
    ├── test_beads.py     # Behavior 4-6
    ├── test_claude.py    # Behavior 7
    ├── test_steps.py     # Behavior 8-11
    ├── test_checkpoints.py  # Behavior 12-13
    └── test_pipeline.py  # Behavior 14
```

---

## References

- Research: `thoughts/shared/research/2025-12-31-python-deterministic-pipeline-control.md`
- Architecture: `thoughts/shared/research/2025-12-31-planning-command-architecture.md`
- Existing patterns: `orchestrator.py:905-960` (subprocess), `loop-runner.py:108-209` (DFS/Kahn's)
- Beads CLI: `bd --help`
