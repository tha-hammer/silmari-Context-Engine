# Requirement Decomposition Pipeline Integration - TDD Implementation Plan

## Beads Tracking

**Epic**: `silmari-Context-Engine-vxt` - Wire up requirement decomposition into planning pipeline

### Tasks

| Behavior | Issue ID | Status |
|----------|----------|--------|
| 1. CLI Argument Parsing | `silmari-Context-Engine-9a6` | closed |
| 2. Pipeline Imports | `silmari-Context-Engine-46d` | open |
| 3. Pipeline Integration | `silmari-Context-Engine-pjt` | open |
| 4. Failure Handling | `silmari-Context-Engine-7kr` | open |
| 5. Resume Flow | `silmari-Context-Engine-0su` | open |
| 6. Step Numbering | `silmari-Context-Engine-p1e` | open |

```bash
# View all tasks
bd show silmari-Context-Engine-vxt

# Work on a behavior
bd update silmari-Context-Engine-9a6 --status=in_progress  # Behavior 1
bd close silmari-Context-Engine-9a6                         # When done

# Complete the epic (after all tasks done)
bd close silmari-Context-Engine-vxt
```

## Overview

Wire up the existing `step_requirement_decomposition()` function into the planning pipeline and CLI resume flow. The step is fully implemented and tested but not currently called by the orchestrator.

**Pipeline Position Change**:
```
BEFORE: step_research() → step_memory_sync() → step_planning() → step_phase_decomposition() → step_beads_integration()

AFTER:  step_research() → step_memory_sync() → step_requirement_decomposition() → step_planning() → step_phase_decomposition() → step_beads_integration()
```

## Current State Analysis

### What Exists (Complete)
- `step_requirement_decomposition()` at `planning_pipeline/step_decomposition.py:34`
- 15 passing tests at `planning_pipeline/tests/test_step_decomposition.py`
- BAML-based decomposition with hierarchy, Mermaid diagrams, and property tests

### What's Missing (This Plan)
| Component | File | Current State |
|-----------|------|---------------|
| Pipeline integration | `planning_pipeline/pipeline.py:27` | Not called |
| Resume flow | `planning_orchestrator.py:423` | Not supported |
| CLI arguments | `planning_orchestrator.py:67` | Old step names |
| Interactive failure handling | N/A | Not implemented |

### Key Discoveries
- `PlanningPipeline.run()` at `pipeline.py:27-241` has 5 steps, needs 6
- `execute_from_step()` at `planning_orchestrator.py:423-535` handles resume
- Resume choices at `planning_orchestrator.py:67`: `["planning", "decomposition", "beads"]`
- Step imports at `pipeline.py:8`: Does not import `step_requirement_decomposition`

## Desired End State

### Observable Behaviors
1. Pipeline runs `step_requirement_decomposition()` after memory sync, before planning
2. On BAML failure, user sees interactive prompt: (R)etry or (C)ontinue
3. Retry re-runs decomposition; Continue skips to planning
4. CLI `--resume-step` accepts `requirement_decomposition` and `phase_decomposition`
5. Step numbering shows 6 steps total (STEP 1/6 through STEP 6/6)

### Success Verification
```bash
# Unit tests pass
pytest planning_pipeline/tests/test_pipeline.py -v -k "requirement_decomposition"

# Integration test with mock BAML
pytest planning_pipeline/tests/test_pipeline.py -v -k "integration"

# CLI help shows new options
python planning_orchestrator.py --help | grep -E "(requirement|phase)_decomposition"
```

## What We're NOT Doing

- Modifying `step_requirement_decomposition()` itself (already complete)
- Changing BAML schemas or decomposition logic
- Adding new CLI flags beyond resume step renaming
- Modifying beads integration logic
- Adding database persistence

## Testing Strategy

- **Framework**: pytest with existing fixtures from `conftest.py`
- **Test Types**:
  - Unit: Argument parsing, step ordering, interactive prompts
  - Integration: Full pipeline flow with mocked BAML
- **Mocking**: Patch `step_requirement_decomposition` to avoid BAML calls in unit tests
- **Key Fixtures**: `mock_decomposition_result` from `test_step_decomposition.py:54-87`

---

## Behavior 1: CLI Argument Parsing Updates

### Test Specification
**Given**: User runs CLI with `--resume-step`
**When**: Parsing arguments
**Then**: Valid choices are `planning`, `requirement_decomposition`, `phase_decomposition`

**Edge Cases**:
- Old value `decomposition` should fail with helpful message
- Old value `beads` should fail with helpful message

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_orchestrator.py`
```python
import pytest
from planning_orchestrator import parse_args


class TestResumeStepArguments:
    """Tests for --resume-step CLI argument parsing."""

    def test_accepts_requirement_decomposition(self):
        """Should accept requirement_decomposition as valid step."""
        args = parse_args(["--resume", "--resume-step", "requirement_decomposition"])
        assert args.resume_step == "requirement_decomposition"

    def test_accepts_phase_decomposition(self):
        """Should accept phase_decomposition as valid step."""
        args = parse_args(["--resume", "--resume-step", "phase_decomposition"])
        assert args.resume_step == "phase_decomposition"

    def test_accepts_planning(self):
        """Should still accept planning as valid step."""
        args = parse_args(["--resume", "--resume-step", "planning"])
        assert args.resume_step == "planning"

    def test_rejects_old_decomposition_name(self):
        """Should reject old 'decomposition' name."""
        with pytest.raises(SystemExit):
            parse_args(["--resume", "--resume-step", "decomposition"])

    def test_rejects_beads(self):
        """Should reject 'beads' as resume step."""
        with pytest.raises(SystemExit):
            parse_args(["--resume", "--resume-step", "beads"])
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_orchestrator.py:64-70`
```python
    parser.add_argument(
        "--resume-step", "--resume_step",
        dest="resume_step",
        choices=["planning", "requirement_decomposition", "phase_decomposition"],
        metavar="STEP",
        help="Step to resume from: planning, requirement_decomposition, or phase_decomposition"
    )
```

#### 🔵 Refactor: Improve Code
No refactoring needed - argparse handles validation.

### Success Criteria
**Automated:**
- [x] Test fails initially (Red): `pytest planning_pipeline/tests/test_orchestrator.py::TestResumeStepArguments -v`
- [x] Test passes after change (Green): same command
- [x] All existing tests pass: `pytest planning_pipeline/tests/test_orchestrator.py -v`

**Manual:**
- [x] `python planning_orchestrator.py --help` shows new step names

---

## Behavior 2: Pipeline Imports and Step Count

### Test Specification
**Given**: `PlanningPipeline` class
**When**: Inspecting module imports and docstrings
**Then**: `step_requirement_decomposition` is imported and docstring mentions 6 steps

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_pipeline.py`
```python
import pytest


class TestPipelineStructure:
    """Tests for pipeline module structure."""

    def test_imports_step_requirement_decomposition(self):
        """Pipeline should import step_requirement_decomposition."""
        from planning_pipeline.pipeline import step_requirement_decomposition
        assert callable(step_requirement_decomposition)

    def test_docstring_mentions_six_steps(self):
        """Pipeline docstring should mention 6 steps."""
        from planning_pipeline.pipeline import PlanningPipeline
        docstring = PlanningPipeline.__doc__
        assert "6 steps" in docstring or "six steps" in docstring.lower()
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/pipeline.py:8`
```python
from .steps import step_research, step_planning, step_phase_decomposition, step_beads_integration, step_memory_sync
from .step_decomposition import step_requirement_decomposition
```

**File**: `planning_pipeline/pipeline.py:12-22`
```python
class PlanningPipeline:
    """Interactive planning pipeline with deterministic control.

    Orchestrates 6 steps:
    1. Research - Analyze codebase and create research document
    2. Memory Sync - Record research and clear context
    3. Requirement Decomposition - Generate structured requirements hierarchy
    4. Planning - Create implementation plan from research
    5. Phase Decomposition - Split plan into phase files
    6. Beads Integration - Create issues and dependencies
    """
```

#### 🔵 Refactor: Improve Code
No refactoring needed.

### Success Criteria
**Automated:**
- [x] Test fails initially (Red): `pytest planning_pipeline/tests/test_pipeline.py::TestPipelineStructure -v`
- [x] Test passes after change (Green): same command

---

## Behavior 3: Pipeline Calls Requirement Decomposition Step

### Test Specification
**Given**: A `PlanningPipeline` with mocked steps
**When**: `pipeline.run()` is called
**Then**: `step_requirement_decomposition()` is called after memory sync, before planning

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_pipeline.py`
```python
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestPipelineRequirementDecomposition:
    """Tests for requirement decomposition integration in pipeline."""

    def test_calls_requirement_decomposition_after_memory_sync(self, tmp_path):
        """Pipeline should call step_requirement_decomposition after memory sync."""
        from planning_pipeline.pipeline import PlanningPipeline

        call_order = []

        def track_research(*args, **kwargs):
            call_order.append("research")
            return {"success": True, "research_path": "test/research.md", "output": ""}

        def track_memory_sync(*args, **kwargs):
            call_order.append("memory_sync")
            return {"success": True}

        def track_requirement_decomposition(*args, **kwargs):
            call_order.append("requirement_decomposition")
            return {
                "success": True,
                "hierarchy_path": str(tmp_path / "hierarchy.json"),
                "diagram_path": str(tmp_path / "diagram.mmd"),
                "tests_path": None,
                "requirement_count": 3,
                "output_dir": str(tmp_path),
            }

        def track_planning(*args, **kwargs):
            call_order.append("planning")
            return {"success": True, "plan_path": str(tmp_path / "plan.md"), "output": ""}

        def track_phase_decomposition(*args, **kwargs):
            call_order.append("phase_decomposition")
            return {"success": True, "phase_files": [str(tmp_path / "phase-1.md")], "output": ""}

        def track_beads(*args, **kwargs):
            call_order.append("beads")
            return {"success": True, "epic_id": "beads-001", "phase_issues": []}

        with patch.multiple(
            "planning_pipeline.pipeline",
            step_research=track_research,
            step_memory_sync=track_memory_sync,
            step_requirement_decomposition=track_requirement_decomposition,
            step_planning=track_planning,
            step_phase_decomposition=track_phase_decomposition,
            step_beads_integration=track_beads,
            interactive_checkpoint_research=lambda x: {"action": "continue", "answers": []},
            interactive_checkpoint_plan=lambda x: {"continue": True, "feedback": ""},
        ):
            pipeline = PlanningPipeline(tmp_path)
            result = pipeline.run("test prompt", auto_approve=True)

        assert result["success"] is True
        assert call_order.index("memory_sync") < call_order.index("requirement_decomposition")
        assert call_order.index("requirement_decomposition") < call_order.index("planning")

    def test_passes_research_path_to_requirement_decomposition(self, tmp_path):
        """Pipeline should pass research_path to step_requirement_decomposition."""
        from planning_pipeline.pipeline import PlanningPipeline

        captured_args = {}

        def capture_requirement_decomposition(project_path, research_path, **kwargs):
            captured_args["project_path"] = project_path
            captured_args["research_path"] = research_path
            return {
                "success": True,
                "hierarchy_path": str(tmp_path / "hierarchy.json"),
                "diagram_path": str(tmp_path / "diagram.mmd"),
                "tests_path": None,
                "requirement_count": 3,
                "output_dir": str(tmp_path),
            }

        with patch.multiple(
            "planning_pipeline.pipeline",
            step_research=lambda *a, **kw: {"success": True, "research_path": "thoughts/research.md", "output": ""},
            step_memory_sync=lambda *a, **kw: {"success": True},
            step_requirement_decomposition=capture_requirement_decomposition,
            step_planning=lambda *a, **kw: {"success": True, "plan_path": str(tmp_path / "plan.md"), "output": ""},
            step_phase_decomposition=lambda *a, **kw: {"success": True, "phase_files": [str(tmp_path / "p.md")], "output": ""},
            step_beads_integration=lambda *a, **kw: {"success": True, "epic_id": "b-1", "phase_issues": []},
            interactive_checkpoint_research=lambda x: {"action": "continue", "answers": []},
            interactive_checkpoint_plan=lambda x: {"continue": True, "feedback": ""},
        ):
            pipeline = PlanningPipeline(tmp_path)
            pipeline.run("test prompt", auto_approve=True)

        assert captured_args["research_path"] == "thoughts/research.md"
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/pipeline.py` (insert after memory sync, before planning loop)
```python
        # Step 2: Requirement Decomposition
        print("\n" + "="*60)
        print("STEP 2/6: REQUIREMENT DECOMPOSITION")
        print("="*60)

        req_decomp = step_requirement_decomposition(
            self.project_path,
            research["research_path"]
        )
        results["steps"]["requirement_decomposition"] = req_decomp

        if req_decomp["success"]:
            print(f"\nDecomposed into {req_decomp['requirement_count']} requirements")
            print(f"Hierarchy: {req_decomp['hierarchy_path']}")
            print(f"Diagram: {req_decomp['diagram_path']}")
```

#### 🔵 Refactor: Improve Code
Update step numbering throughout the file (STEP 3/6, STEP 4/6, etc.)

### Success Criteria
**Automated:**
- [x] Test fails initially (Red): `pytest planning_pipeline/tests/test_pipeline.py::TestPipelineRequirementDecomposition -v`
- [x] Test passes after change (Green): same command
- [x] All tests pass: `pytest planning_pipeline/tests/ -v`

---

## Behavior 4: Interactive Prompt on Decomposition Failure

### Test Specification
**Given**: `step_requirement_decomposition()` returns `success: False`
**When**: Pipeline is not in auto_approve mode
**Then**: User sees interactive prompt with (R)etry and (C)ontinue options

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_pipeline.py`
```python
from unittest.mock import patch, MagicMock


class TestDecompositionFailureHandling:
    """Tests for interactive failure handling in requirement decomposition."""

    def test_prompts_on_decomposition_failure(self, tmp_path, monkeypatch):
        """Should show (R)etry/(C)ontinue prompt when decomposition fails."""
        from planning_pipeline.pipeline import PlanningPipeline

        prompt_shown = {"called": False, "message": ""}

        # Simulate user choosing Continue
        inputs = iter(["c"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        def failing_decomposition(*args, **kwargs):
            return {"success": False, "error": "BAML API rate limit"}

        def capture_print(*args, **kwargs):
            message = " ".join(str(a) for a in args)
            if "(R)etry" in message or "(C)ontinue" in message:
                prompt_shown["called"] = True
                prompt_shown["message"] = message

        with patch.multiple(
            "planning_pipeline.pipeline",
            step_research=lambda *a, **kw: {"success": True, "research_path": "r.md", "output": ""},
            step_memory_sync=lambda *a, **kw: {"success": True},
            step_requirement_decomposition=failing_decomposition,
            step_planning=lambda *a, **kw: {"success": True, "plan_path": str(tmp_path / "p.md"), "output": ""},
            step_phase_decomposition=lambda *a, **kw: {"success": True, "phase_files": [str(tmp_path / "ph.md")], "output": ""},
            step_beads_integration=lambda *a, **kw: {"success": True, "epic_id": "b", "phase_issues": []},
            interactive_checkpoint_research=lambda x: {"action": "continue", "answers": []},
            interactive_checkpoint_plan=lambda x: {"continue": True, "feedback": ""},
        ):
            with patch("builtins.print", side_effect=capture_print):
                pipeline = PlanningPipeline(tmp_path)
                pipeline.run("test", auto_approve=False)

        assert prompt_shown["called"], "Should show retry/continue prompt"

    def test_retry_reruns_decomposition(self, tmp_path, monkeypatch):
        """Choosing (R)etry should re-run step_requirement_decomposition."""
        from planning_pipeline.pipeline import PlanningPipeline

        call_count = {"decomposition": 0}

        # First input: retry, second: continue (to break loop)
        inputs = iter(["r", "c"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        def counting_decomposition(*args, **kwargs):
            call_count["decomposition"] += 1
            if call_count["decomposition"] < 2:
                return {"success": False, "error": "temporary failure"}
            return {
                "success": True,
                "hierarchy_path": str(tmp_path / "h.json"),
                "diagram_path": str(tmp_path / "d.mmd"),
                "tests_path": None,
                "requirement_count": 1,
                "output_dir": str(tmp_path),
            }

        with patch.multiple(
            "planning_pipeline.pipeline",
            step_research=lambda *a, **kw: {"success": True, "research_path": "r.md", "output": ""},
            step_memory_sync=lambda *a, **kw: {"success": True},
            step_requirement_decomposition=counting_decomposition,
            step_planning=lambda *a, **kw: {"success": True, "plan_path": str(tmp_path / "p.md"), "output": ""},
            step_phase_decomposition=lambda *a, **kw: {"success": True, "phase_files": [str(tmp_path / "ph.md")], "output": ""},
            step_beads_integration=lambda *a, **kw: {"success": True, "epic_id": "b", "phase_issues": []},
            interactive_checkpoint_research=lambda x: {"action": "continue", "answers": []},
            interactive_checkpoint_plan=lambda x: {"continue": True, "feedback": ""},
        ):
            pipeline = PlanningPipeline(tmp_path)
            pipeline.run("test", auto_approve=False)

        assert call_count["decomposition"] == 2, "Should retry decomposition once"

    def test_continue_skips_to_planning(self, tmp_path, monkeypatch):
        """Choosing (C)ontinue should skip decomposition and proceed to planning."""
        from planning_pipeline.pipeline import PlanningPipeline

        steps_called = []

        inputs = iter(["c"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        def failing_decomposition(*args, **kwargs):
            steps_called.append("decomposition")
            return {"success": False, "error": "BAML failed"}

        def track_planning(*args, **kwargs):
            steps_called.append("planning")
            return {"success": True, "plan_path": str(tmp_path / "p.md"), "output": ""}

        with patch.multiple(
            "planning_pipeline.pipeline",
            step_research=lambda *a, **kw: {"success": True, "research_path": "r.md", "output": ""},
            step_memory_sync=lambda *a, **kw: {"success": True},
            step_requirement_decomposition=failing_decomposition,
            step_planning=track_planning,
            step_phase_decomposition=lambda *a, **kw: {"success": True, "phase_files": [str(tmp_path / "ph.md")], "output": ""},
            step_beads_integration=lambda *a, **kw: {"success": True, "epic_id": "b", "phase_issues": []},
            interactive_checkpoint_research=lambda x: {"action": "continue", "answers": []},
            interactive_checkpoint_plan=lambda x: {"continue": True, "feedback": ""},
        ):
            pipeline = PlanningPipeline(tmp_path)
            result = pipeline.run("test", auto_approve=False)

        assert "planning" in steps_called, "Should proceed to planning after Continue"
        assert result["success"] is True

    def test_auto_approve_skips_decomposition_on_failure(self, tmp_path):
        """In auto_approve mode, decomposition failure should skip to planning."""
        from planning_pipeline.pipeline import PlanningPipeline

        steps_called = []

        with patch.multiple(
            "planning_pipeline.pipeline",
            step_research=lambda *a, **kw: {"success": True, "research_path": "r.md", "output": ""},
            step_memory_sync=lambda *a, **kw: {"success": True},
            step_requirement_decomposition=lambda *a, **kw: (steps_called.append("decomp"), {"success": False, "error": "fail"})[1],
            step_planning=lambda *a, **kw: (steps_called.append("planning"), {"success": True, "plan_path": str(tmp_path / "p.md"), "output": ""})[1],
            step_phase_decomposition=lambda *a, **kw: {"success": True, "phase_files": [str(tmp_path / "ph.md")], "output": ""},
            step_beads_integration=lambda *a, **kw: {"success": True, "epic_id": "b", "phase_issues": []},
        ):
            pipeline = PlanningPipeline(tmp_path)
            result = pipeline.run("test", auto_approve=True)

        assert "planning" in steps_called
        assert result["success"] is True
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/pipeline.py` (in the requirement decomposition section)
```python
        # Step 2: Requirement Decomposition (with retry loop)
        while True:
            print("\n" + "="*60)
            print("STEP 2/6: REQUIREMENT DECOMPOSITION")
            print("="*60)

            req_decomp = step_requirement_decomposition(
                self.project_path,
                research["research_path"]
            )
            results["steps"]["requirement_decomposition"] = req_decomp

            if req_decomp["success"]:
                print(f"\nDecomposed into {req_decomp['requirement_count']} requirements")
                print(f"Hierarchy: {req_decomp['hierarchy_path']}")
                print(f"Diagram: {req_decomp['diagram_path']}")
                break

            # Decomposition failed
            print(f"\nDecomposition failed: {req_decomp.get('error', 'Unknown error')}")

            if auto_approve:
                print("Auto-approve mode: skipping to planning")
                break

            # Interactive prompt
            print("\nOptions:")
            print("  (R)etry - Try decomposition again")
            print("  (C)ontinue - Skip decomposition and proceed to planning")

            choice = input("\nChoice [R/c]: ").strip().lower()
            if choice == 'r' or choice == '':
                print("\nRetrying decomposition...")
                continue
            else:
                print("\nSkipping decomposition, continuing to planning...")
                break
```

#### 🔵 Refactor: Improve Code
Extract the interactive prompt into a helper function if needed.

### Success Criteria
**Automated:**
- [x] Test fails initially (Red): `pytest planning_pipeline/tests/test_pipeline.py::TestDecompositionFailureHandling -v`
- [x] Test passes after change (Green): same command
- [x] All tests pass: `pytest planning_pipeline/tests/ -v`

**Manual:**
- [ ] Run pipeline with failing BAML, see prompt, choose Retry
- [ ] Run pipeline with failing BAML, see prompt, choose Continue

---

## Behavior 5: Resume Flow Supports New Step Names

### Test Specification
**Given**: User runs `--resume --resume-step requirement_decomposition`
**When**: Resume flow executes
**Then**: Pipeline starts from requirement decomposition step

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_orchestrator.py`
```python
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestResumeFlowWithNewSteps:
    """Tests for resume flow with updated step names."""

    def test_resume_from_requirement_decomposition(self, tmp_path):
        """Should start from requirement_decomposition step."""
        from planning_orchestrator import execute_from_step

        steps_called = []

        with patch.multiple(
            "planning_orchestrator",
            step_requirement_decomposition=lambda *a, **kw: (
                steps_called.append("requirement_decomposition"),
                {"success": True, "hierarchy_path": str(tmp_path / "h.json"),
                 "diagram_path": str(tmp_path / "d.mmd"), "tests_path": None,
                 "requirement_count": 1, "output_dir": str(tmp_path)}
            )[1],
            step_planning=lambda *a, **kw: (
                steps_called.append("planning"),
                {"success": True, "plan_path": str(tmp_path / "plan.md"), "output": ""}
            )[1],
            step_phase_decomposition=lambda *a, **kw: (
                steps_called.append("phase_decomposition"),
                {"success": True, "phase_files": [str(tmp_path / "p.md")], "output": ""}
            )[1],
            step_beads_integration=lambda *a, **kw: (
                steps_called.append("beads"),
                {"success": True, "epic_id": "b", "phase_issues": []}
            )[1],
            write_checkpoint=lambda *a, **kw: None,
        ):
            result = execute_from_step(
                project_path=tmp_path,
                resume_step="requirement_decomposition",
                research_path=str(tmp_path / "research.md"),
            )

        assert "requirement_decomposition" in steps_called
        assert "planning" in steps_called
        assert "phase_decomposition" in steps_called
        assert result["success"] is True

    def test_resume_from_phase_decomposition(self, tmp_path):
        """Should start from phase_decomposition step (renamed from decomposition)."""
        from planning_orchestrator import execute_from_step

        steps_called = []
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("# Test Plan")

        with patch.multiple(
            "planning_orchestrator",
            step_phase_decomposition=lambda *a, **kw: (
                steps_called.append("phase_decomposition"),
                {"success": True, "phase_files": [str(tmp_path / "p.md")], "output": ""}
            )[1],
            step_beads_integration=lambda *a, **kw: (
                steps_called.append("beads"),
                {"success": True, "epic_id": "b", "phase_issues": []}
            )[1],
            write_checkpoint=lambda *a, **kw: None,
        ):
            result = execute_from_step(
                project_path=tmp_path,
                resume_step="phase_decomposition",
                plan_path=str(plan_file),
            )

        assert "phase_decomposition" in steps_called
        assert result["success"] is True

    def test_resume_does_not_run_earlier_steps(self, tmp_path):
        """Resuming from requirement_decomposition should not run research."""
        from planning_orchestrator import execute_from_step

        steps_called = []

        with patch.multiple(
            "planning_orchestrator",
            step_research=lambda *a, **kw: (steps_called.append("research"), {"success": True})[1],
            step_requirement_decomposition=lambda *a, **kw: (
                steps_called.append("requirement_decomposition"),
                {"success": True, "hierarchy_path": str(tmp_path / "h.json"),
                 "diagram_path": str(tmp_path / "d.mmd"), "tests_path": None,
                 "requirement_count": 1, "output_dir": str(tmp_path)}
            )[1],
            step_planning=lambda *a, **kw: (
                steps_called.append("planning"),
                {"success": True, "plan_path": str(tmp_path / "plan.md"), "output": ""}
            )[1],
            step_phase_decomposition=lambda *a, **kw: (
                steps_called.append("phase_decomposition"),
                {"success": True, "phase_files": [str(tmp_path / "p.md")], "output": ""}
            )[1],
            step_beads_integration=lambda *a, **kw: (
                steps_called.append("beads"),
                {"success": True, "epic_id": "b", "phase_issues": []}
            )[1],
            write_checkpoint=lambda *a, **kw: None,
        ):
            execute_from_step(
                project_path=tmp_path,
                resume_step="requirement_decomposition",
                research_path=str(tmp_path / "research.md"),
            )

        assert "research" not in steps_called
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_orchestrator.py:423-535` (update `execute_from_step`)
```python
def execute_from_step(
    project_path: Path,
    resume_step: str,
    research_path: str = None,
    plan_path: str = None,
    ticket_id: str = None,
    auto_approve: bool = False
) -> dict:
    """Execute pipeline from a specific step."""
    from datetime import datetime
    from planning_pipeline import (
        step_planning,
        step_phase_decomposition,
        step_beads_integration,
        write_checkpoint,
    )
    from planning_pipeline.step_decomposition import step_requirement_decomposition

    results = {
        "started": datetime.now().isoformat(),
        "resumed_from": resume_step,
        "steps": {}
    }

    try:
        # Step: Requirement Decomposition
        if resume_step == "requirement_decomposition":
            print(f"\n{'='*60}")
            print("STEP 2/6: REQUIREMENT DECOMPOSITION")
            print("="*60)

            req_decomp = step_requirement_decomposition(project_path, research_path)
            results["steps"]["requirement_decomposition"] = req_decomp

            if not req_decomp["success"]:
                if not auto_approve:
                    print(f"\nDecomposition failed: {req_decomp.get('error')}")
                    choice = input("(R)etry or (C)ontinue? [R/c]: ").strip().lower()
                    if choice == 'r' or choice == '':
                        # Recursive retry
                        return execute_from_step(project_path, resume_step, research_path, plan_path, ticket_id, auto_approve)
                print("Skipping decomposition, continuing to planning...")

        # Step: Planning (runs for requirement_decomposition and planning resume points)
        if resume_step in ("requirement_decomposition", "planning"):
            print(f"\n{'='*60}")
            print("STEP 3/6: PLANNING PHASE")
            print("="*60)

            planning = step_planning(project_path, research_path, "")
            results["steps"]["planning"] = planning

            if not planning["success"]:
                write_checkpoint(project_path, "planning-failed", [research_path])
                results["success"] = False
                results["failed_at"] = "planning"
                return results

            plan_path = planning.get("plan_path")
            if not plan_path:
                results["success"] = False
                results["error"] = "No plan_path extracted"
                return results

        # Step: Phase Decomposition
        if resume_step in ("requirement_decomposition", "planning", "phase_decomposition"):
            print(f"\n{'='*60}")
            print("STEP 4/6: PHASE DECOMPOSITION")
            print("="*60)

            decomposition = step_phase_decomposition(project_path, plan_path)
            results["steps"]["phase_decomposition"] = decomposition

            if not decomposition["success"]:
                artifacts = [research_path] if research_path else []
                if plan_path:
                    artifacts.append(plan_path)
                write_checkpoint(project_path, "phase_decomposition-failed", artifacts)
                results["success"] = False
                results["failed_at"] = "phase_decomposition"
                return results

            phase_files = decomposition.get("phase_files", [])
            print(f"\nCreated {len(phase_files)} phase files")

        # Step: Beads Integration (always runs for all resume points)
        print(f"\n{'='*60}")
        print("STEP 5/6: BEADS INTEGRATION")
        print("="*60)

        if "phase_decomposition" not in results["steps"]:
            plan_dir = Path(plan_path).parent
            phase_files = sorted(plan_dir.glob("*-phase-*.md"))
            phase_files = [str(f) for f in phase_files]
        else:
            phase_files = results["steps"]["phase_decomposition"].get("phase_files", [])

        epic_title = f"Plan: {ticket_id}" if ticket_id else f"Plan: {datetime.now().strftime('%Y-%m-%d')}"
        beads = step_beads_integration(project_path, phase_files, epic_title)
        results["steps"]["beads"] = beads

        if beads["success"]:
            print(f"\nCreated epic: {beads.get('epic_id')}")

        results["success"] = True
        results["completed"] = datetime.now().isoformat()

        if plan_path:
            results["plan_dir"] = str(Path(plan_path).parent)

        return results

    except Exception as e:
        results["success"] = False
        results["error"] = str(e)
        return results
```

#### 🔵 Refactor: Improve Code
Extract step execution into helper functions if the function becomes too long.

### Success Criteria
**Automated:**
- [x] Test fails initially (Red): `pytest planning_pipeline/tests/test_orchestrator.py::TestResumeFlowWithNewSteps -v`
- [x] Test passes after change (Green): same command
- [x] All tests pass: `pytest planning_pipeline/tests/test_orchestrator.py -v`

**Manual:**
- [ ] `python planning_orchestrator.py --resume --resume-step requirement_decomposition --research-path <path>` works

---

## Behavior 6: Update Step Numbering Throughout

### Test Specification
**Given**: Pipeline runs through all steps
**When**: Step headers are printed
**Then**: Numbers show X/6 format (not X/5)

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_pipeline.py`
```python
class TestStepNumbering:
    """Tests for correct step numbering in output."""

    def test_step_headers_show_six_total(self, tmp_path, capsys):
        """All step headers should show /6 format."""
        from planning_pipeline.pipeline import PlanningPipeline

        with patch.multiple(
            "planning_pipeline.pipeline",
            step_research=lambda *a, **kw: {"success": True, "research_path": "r.md", "output": ""},
            step_memory_sync=lambda *a, **kw: {"success": True},
            step_requirement_decomposition=lambda *a, **kw: {
                "success": True, "hierarchy_path": str(tmp_path / "h.json"),
                "diagram_path": str(tmp_path / "d.mmd"), "tests_path": None,
                "requirement_count": 1, "output_dir": str(tmp_path)
            },
            step_planning=lambda *a, **kw: {"success": True, "plan_path": str(tmp_path / "p.md"), "output": ""},
            step_phase_decomposition=lambda *a, **kw: {"success": True, "phase_files": [str(tmp_path / "ph.md")], "output": ""},
            step_beads_integration=lambda *a, **kw: {"success": True, "epic_id": "b", "phase_issues": []},
            interactive_checkpoint_research=lambda x: {"action": "continue", "answers": []},
            interactive_checkpoint_plan=lambda x: {"continue": True, "feedback": ""},
        ):
            pipeline = PlanningPipeline(tmp_path)
            pipeline.run("test", auto_approve=True)

        output = capsys.readouterr().out
        assert "STEP 1/6" in output
        assert "STEP 2/6" in output
        assert "STEP 3/6" in output
        assert "STEP 4/6" in output
        assert "STEP 5/6" in output
        assert "STEP 6/6" in output
        assert "/5" not in output  # No old numbering
```

#### 🟢 Green: Minimal Implementation
Update all step headers in `pipeline.py`:
- STEP 1/6: RESEARCH PHASE
- STEP 2/6: REQUIREMENT DECOMPOSITION
- STEP 3/6: PLANNING PHASE
- STEP 4/6: PHASE DECOMPOSITION
- STEP 5/6: BEADS INTEGRATION
- STEP 6/6: MEMORY CAPTURE

### Success Criteria
**Automated:**
- [x] Test passes: `pytest planning_pipeline/tests/test_pipeline.py::TestStepNumbering -v`

---

## Integration Testing

After all unit tests pass, run integration tests:

```bash
# All pipeline tests
pytest planning_pipeline/tests/test_pipeline.py -v

# All orchestrator tests
pytest planning_pipeline/tests/test_orchestrator.py -v

# Full test suite
pytest planning_pipeline/tests/ -v

# E2E test with real BAML (requires ANTHROPIC_API_KEY)
pytest planning_pipeline/tests/test_decomposition_e2e.py -v -m e2e
```

## Implementation Order

1. **Behavior 1**: CLI argument parsing (simplest, no dependencies)
2. **Behavior 2**: Pipeline imports and docstring update
3. **Behavior 6**: Step numbering update (mechanical change)
4. **Behavior 3**: Pipeline calls requirement decomposition
5. **Behavior 4**: Interactive failure handling
6. **Behavior 5**: Resume flow updates

## Files Modified

| File | Changes |
|------|---------|
| `planning_orchestrator.py` | Line 67: Update choices; Lines 423-535: Update `execute_from_step()` |
| `planning_pipeline/pipeline.py` | Line 8: Add import; Lines 12-22: Update docstring; Lines 110-130: Add decomposition step; All steps: Update numbering |
| `planning_pipeline/tests/test_pipeline.py` | Add new test classes |
| `planning_pipeline/tests/test_orchestrator.py` | Add new test classes |

## References

- Implementation: `planning_pipeline/step_decomposition.py:34-168`
- Existing tests: `planning_pipeline/tests/test_step_decomposition.py`
- Pipeline: `planning_pipeline/pipeline.py:12-241`
- Orchestrator: `planning_orchestrator.py:217-535`
- Original plan: `thoughts/searchable/shared/plans/2026-01-02-tdd-iterative-requirement-decomposition-00-overview.md`
