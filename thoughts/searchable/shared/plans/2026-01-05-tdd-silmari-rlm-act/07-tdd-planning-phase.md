# Phase 07: TDD Planning Phase TDD Plan

## Overview

Implement the TDD planning phase that creates Red-Green-Refactor plans from the decomposed requirements.

## Testable Behaviors

### Behavior 1: Load Requirement Hierarchy
**Given**: Hierarchy JSON from decomposition
**When**: Starting TDD planning
**Then**: Hierarchy loaded into memory

### Behavior 2: Generate TDD Plan Document
**Given**: Requirement hierarchy
**When**: Creating plan
**Then**: Markdown document with Red-Green-Refactor cycles

### Behavior 3: Include Test Specifications
**Given**: Requirement with behaviors
**When**: Generating plan section
**Then**: Given/When/Then test specs included

### Behavior 4: Include Code Snippets
**Given**: Behavior specification
**When**: Generating Red/Green/Refactor
**Then**: Code blocks with language hints

### Behavior 5: Store Plan in CWA
**Given**: Generated plan
**When**: Phase completes
**Then**: FILE entry created in store

### Behavior 6: Link to Requirements
**Given**: Plan referencing requirements
**When**: Storing in CWA
**Then**: Plan entry linked to requirement entries

### Behavior 7: Return PhaseResult
**Given**: Successful planning
**When**: Phase completes
**Then**: PhaseResult with plan path

### Behavior 8: Handle Planning Failure
**Given**: LLM call fails
**When**: Error occurs
**Then**: PhaseResult with error

---

## TDD Cycle: Behavior 1 - Load Requirement Hierarchy

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_tdd_planning_phase.py`
```python
import pytest
import json
from pathlib import Path
from silmari_rlm_act.phases.tdd_planning import TDDPlanningPhase
from silmari_rlm_act.phases.decomposition import RequirementHierarchy, Requirement
from silmari_rlm_act.context.cwa_integration import CWAIntegration


class TestLoadHierarchy:
    """Behavior 1: Load Requirement Hierarchy."""

    def test_loads_from_json_path(self, tmp_path):
        """Given JSON path, loads hierarchy."""
        # Create hierarchy JSON
        hierarchy_data = {
            "requirements": [
                {
                    "id": "REQ-001",
                    "title": "Login",
                    "description": "User login",
                    "behaviors": ["Given..., When..., Then..."],
                    "children": []
                }
            ]
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = phase._load_hierarchy(str(hierarchy_path))

        assert hierarchy.root_count == 1
        assert hierarchy.get_by_id("REQ-001") is not None

    def test_raises_for_missing_file(self, tmp_path):
        """Given nonexistent path, raises error."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        with pytest.raises(FileNotFoundError):
            phase._load_hierarchy("nonexistent.json")

    def test_raises_for_invalid_json(self, tmp_path):
        """Given invalid JSON, raises error."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json")

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        with pytest.raises(json.JSONDecodeError):
            phase._load_hierarchy(str(bad_file))
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/phases/tdd_planning.py`
```python
"""TDD Planning phase implementation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from silmari_rlm_act.models import PhaseResult
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.phases.decomposition import RequirementHierarchy, Requirement


class TDDPlanningPhase:
    """Generate TDD plans from requirement hierarchy."""

    def __init__(
        self,
        project_path: Path,
        cwa: CWAIntegration,
    ):
        self.project_path = Path(project_path)
        self.cwa = cwa
        self._runner = None  # Claude runner

    def _load_hierarchy(self, hierarchy_path: str) -> RequirementHierarchy:
        """Load requirement hierarchy from JSON.

        Args:
            hierarchy_path: Path to hierarchy JSON

        Returns:
            RequirementHierarchy instance

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        path = Path(hierarchy_path)
        if not path.is_absolute():
            path = self.project_path / path

        if not path.exists():
            raise FileNotFoundError(f"Hierarchy not found: {path}")

        with open(path) as f:
            data = json.load(f)

        return RequirementHierarchy.from_dict(data)
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_tdd_planning_phase.py::TestLoadHierarchy -v`

---

## TDD Cycle: Behavior 2-4 - Generate Plan Document

### 🔴 Red: Write Failing Tests

**File**: `silmari-rlm-act/tests/test_tdd_planning_phase.py`
```python
class TestGeneratePlanDocument:
    """Behavior 2-4: Generate TDD Plan Document."""

    def test_generates_markdown(self, tmp_path):
        """Given hierarchy, generates markdown document."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy(requirements=[
            Requirement(
                id="REQ-001",
                title="Login",
                description="User login feature",
                behaviors=["Given valid creds, when login, then authenticated"]
            )
        ])

        plan = phase._generate_plan_document(hierarchy, "login-feature")

        assert "# " in plan  # Has headers
        assert "REQ-001" in plan
        assert "Login" in plan

    def test_includes_red_green_refactor(self, tmp_path):
        """Given behavior, includes TDD cycle."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy(requirements=[
            Requirement(
                id="REQ-001",
                title="Login",
                description="Login feature",
                behaviors=["Given valid creds, when login, then authenticated"]
            )
        ])

        plan = phase._generate_plan_document(hierarchy, "login")

        assert "Red" in plan or "🔴" in plan
        assert "Green" in plan or "🟢" in plan
        assert "Refactor" in plan or "🔵" in plan

    def test_includes_test_specification(self, tmp_path):
        """Given behavior, includes Given/When/Then."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy(requirements=[
            Requirement(
                id="REQ-001",
                title="Login",
                description="Login feature",
                behaviors=["Given valid credentials, when login submitted, then user authenticated"]
            )
        ])

        plan = phase._generate_plan_document(hierarchy, "login")

        assert "Given" in plan
        assert "When" in plan or "when" in plan
        assert "Then" in plan or "then" in plan

    def test_includes_code_blocks(self, tmp_path):
        """Given plan, includes code snippets."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy(requirements=[
            Requirement(
                id="REQ-001",
                title="Login",
                description="Login feature",
                behaviors=["Given valid creds, when login, then authenticated"]
            )
        ])

        plan = phase._generate_plan_document(hierarchy, "login")

        assert "```" in plan  # Has code blocks
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/phases/tdd_planning.py`
```python
class TDDPlanningPhase:
    # ... existing code ...

    def _generate_plan_document(
        self,
        hierarchy: RequirementHierarchy,
        plan_name: str
    ) -> str:
        """Generate TDD plan document from hierarchy.

        Args:
            hierarchy: Requirement hierarchy
            plan_name: Name for the plan

        Returns:
            Markdown document string
        """
        lines = [
            f"# {plan_name} TDD Implementation Plan",
            "",
            "## Overview",
            "",
            f"This plan covers {len(hierarchy.all_requirements())} requirements.",
            "",
        ]

        # Add summary table
        lines.extend(self._generate_summary_table(hierarchy))
        lines.append("")

        # Add each requirement section
        for req in hierarchy.all_requirements():
            lines.extend(self._generate_requirement_section(req))
            lines.append("")

        # Add success criteria
        lines.extend(self._generate_success_criteria(hierarchy))

        return "\n".join(lines)

    def _generate_summary_table(self, hierarchy: RequirementHierarchy) -> List[str]:
        """Generate summary table of requirements."""
        lines = [
            "## Requirements Summary",
            "",
            "| ID | Title | Behaviors | Status |",
            "|-----|-------|-----------|--------|",
        ]

        for req in hierarchy.all_requirements():
            behavior_count = len(req.behaviors)
            lines.append(f"| {req.id} | {req.title} | {behavior_count} | Pending |")

        return lines

    def _generate_requirement_section(self, req: Requirement) -> List[str]:
        """Generate TDD section for a requirement."""
        lines = [
            f"## {req.id}: {req.title}",
            "",
            req.description,
            "",
        ]

        if not req.behaviors:
            lines.extend([
                "### Testable Behaviors",
                "",
                "_No behaviors defined. Add behaviors during implementation._",
                "",
            ])
            return lines

        for i, behavior in enumerate(req.behaviors, 1):
            lines.extend(self._generate_behavior_tdd(req.id, i, behavior))

        return lines

    def _generate_behavior_tdd(
        self,
        req_id: str,
        behavior_num: int,
        behavior: str
    ) -> List[str]:
        """Generate Red-Green-Refactor section for a behavior."""
        # Parse Given/When/Then from behavior
        given, when, then = self._parse_behavior(behavior)

        return [
            f"### Behavior {behavior_num}",
            "",
            "#### Test Specification",
            f"**Given**: {given}",
            f"**When**: {when}",
            f"**Then**: {then}",
            "",
            "#### 🔴 Red: Write Failing Test",
            "",
            f"**File**: `tests/test_{req_id.lower().replace('-', '_')}.py`",
            "```python",
            f"def test_{req_id.lower().replace('-', '_')}_behavior_{behavior_num}():",
            f'    """Test: {behavior}"""',
            "    # Arrange",
            f"    # {given}",
            "",
            "    # Act",
            f"    # {when}",
            "",
            "    # Assert",
            f"    # {then}",
            "    assert False  # TODO: Implement",
            "```",
            "",
            "#### 🟢 Green: Minimal Implementation",
            "",
            "```python",
            "# TODO: Add minimal implementation to pass test",
            "```",
            "",
            "#### 🔵 Refactor: Improve Code",
            "",
            "```python",
            "# TODO: Refactor while keeping tests green",
            "```",
            "",
            "#### Success Criteria",
            "- [ ] Test fails for right reason (Red)",
            "- [ ] Test passes with minimal code (Green)",
            "- [ ] Code refactored, tests still pass (Refactor)",
            "",
        ]

    def _parse_behavior(self, behavior: str) -> tuple[str, str, str]:
        """Parse Given/When/Then from behavior string."""
        import re

        # Try to extract Given/When/Then
        given_match = re.search(r"[Gg]iven\s+(.+?)(?:,|\s+[Ww]hen)", behavior)
        when_match = re.search(r"[Ww]hen\s+(.+?)(?:,|\s+[Tt]hen)", behavior)
        then_match = re.search(r"[Tt]hen\s+(.+?)(?:$|\.)", behavior)

        given = given_match.group(1).strip() if given_match else "initial state"
        when = when_match.group(1).strip() if when_match else "action performed"
        then = then_match.group(1).strip() if then_match else "expected result"

        return given, when, then

    def _generate_success_criteria(self, hierarchy: RequirementHierarchy) -> List[str]:
        """Generate overall success criteria."""
        return [
            "## Overall Success Criteria",
            "",
            "### Automated",
            "- [ ] All tests pass: `pytest tests/ -v`",
            "- [ ] Type checking: `mypy .`",
            "- [ ] Lint: `ruff check .`",
            "",
            "### Manual",
            "- [ ] All behaviors implemented",
            "- [ ] Code reviewed",
            "- [ ] Documentation updated",
        ]
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_tdd_planning_phase.py::TestGeneratePlanDocument -v`

---

## TDD Cycle: Behavior 5-8 - Store and Return

### 🔴 Red: Write Failing Tests

**File**: `silmari-rlm-act/tests/test_tdd_planning_phase.py`
```python
from context_window_array import EntryType


class TestStorePlanInCWA:
    """Behavior 5-6: Store Plan in CWA."""

    def test_creates_file_entry(self, tmp_path):
        """Given plan, creates FILE entry."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        plan_content = "# TDD Plan\n\n## Overview..."
        plan_path = tmp_path / "plan.md"
        plan_path.write_text(plan_content)

        entry_id = phase._store_plan_in_cwa(str(plan_path), plan_content)

        entry = cwa.store.get(entry_id)
        assert entry.entry_type == EntryType.FILE


class TestPlanPhaseResult:
    """Behavior 7-8: Return PhaseResult."""

    def test_returns_success_result(self, tmp_path):
        """Given successful planning, returns PhaseResult."""
        # Create hierarchy
        hierarchy_data = {
            "requirements": [
                {"id": "REQ-001", "title": "Test", "description": "Test req", "behaviors": [], "children": []}
            ]
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(str(hierarchy_path), "test-plan")

        assert result.success is True
        assert result.phase == "tdd_planning"
        assert len(result.artifacts) > 0

    def test_returns_error_on_failure(self, tmp_path):
        """Given missing hierarchy, returns error."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute("nonexistent.json", "test-plan")

        assert result.success is False
        assert result.error is not None
```

### 🟢 Green: Implement Execute Method

**File**: `silmari-rlm-act/phases/tdd_planning.py`
```python
class TDDPlanningPhase:
    # ... existing code ...

    def execute(self, hierarchy_path: str, plan_name: str) -> PhaseResult:
        """Execute TDD planning phase.

        Args:
            hierarchy_path: Path to hierarchy JSON
            plan_name: Name for the plan

        Returns:
            PhaseResult with plan artifacts
        """
        try:
            # Load hierarchy
            hierarchy = self._load_hierarchy(hierarchy_path)

            # Generate plan document
            plan_content = self._generate_plan_document(hierarchy, plan_name)

            # Save plan
            plan_path = self._save_plan(plan_content, plan_name)

            # Store in CWA
            self._store_plan_in_cwa(str(plan_path), plan_content)

            return PhaseResult(
                phase="tdd_planning",
                success=True,
                artifacts=[str(plan_path)],
                output=f"Generated TDD plan with {len(hierarchy.all_requirements())} requirements"
            )

        except Exception as e:
            return PhaseResult(
                phase="tdd_planning",
                success=False,
                error=str(e)
            )

    def _save_plan(self, content: str, plan_name: str) -> Path:
        """Save plan document to file."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        plan_dir = self.project_path / "thoughts" / "searchable" / "shared" / "plans"
        plan_dir.mkdir(parents=True, exist_ok=True)

        plan_path = plan_dir / f"{date_str}-tdd-{plan_name}.md"
        plan_path.write_text(content)
        return plan_path

    def _store_plan_in_cwa(self, plan_path: str, content: str) -> str:
        """Store plan in CWA as FILE entry."""
        # Generate summary from first few lines
        lines = content.split("\n")[:10]
        summary = " ".join(l.strip("#").strip() for l in lines if l.strip())[:200]

        return self.cwa.store_plan(
            path=plan_path,
            content=content,
            summary=summary
        )
```

### Success Criteria
**Automated:**
- [ ] All TDD planning tests pass: `pytest silmari-rlm-act/tests/test_tdd_planning_phase.py -v`

**Manual:**
- [ ] Plan document is readable and well-formatted
- [ ] Red-Green-Refactor cycles are clear
- [ ] Test specifications are useful

## Summary

This phase implements TDD planning with:
- Hierarchy JSON loading
- Markdown document generation
- Red-Green-Refactor cycle templates
- Test specification parsing
- CWA storage
- PhaseResult return
