"""TDD Planning phase implementation.

This module implements the TDD planning phase of the silmari-rlm-act pipeline,
which generates TDD plan documents from requirement hierarchies using
Red-Green-Refactor cycles.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from silmari_rlm_act.checkpoints.interactive import (
    collect_multiline_input,
    prompt_tdd_planning_action,
)
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseResult, PhaseStatus, PhaseType

from planning_pipeline.models import RequirementHierarchy, RequirementNode
from planning_pipeline.claude_runner import run_claude_sync


# Section headers for requirement context building
SECTION_HEADERS = {
    "description": "## Description",
    "criteria": "## Acceptance Criteria",
    "implementation": "## Implementation Components",
    "children": "## Sub-Requirements",
    "research": "## Research Document",
}


class TDDPlanningPhase:
    """Execute TDD planning phase.

    This phase:
    1. Loads requirement hierarchy from decomposition metadata
    2. Generates TDD plan document with Red-Green-Refactor cycles
    3. Includes test specifications (Given/When/Then)
    4. Includes code snippets for each behavior
    5. Stores plan in CWA as FILE entry
    6. Returns a PhaseResult with artifacts

    Attributes:
        project_path: Root directory of the project
        cwa: Context Window Array integration
        DEFAULT_TIMEOUT: Default timeout in seconds (10 minutes)
    """

    DEFAULT_TIMEOUT = 600  # 10 minutes

    def __init__(
        self,
        project_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Initialize TDD planning phase.

        Args:
            project_path: Root directory of the project
            cwa: Context Window Array integration instance
        """
        self.project_path = Path(project_path)
        self.cwa = cwa

    def _load_hierarchy(self, hierarchy_path: str) -> RequirementHierarchy:
        """Load requirement hierarchy from JSON file.

        Args:
            hierarchy_path: Path to hierarchy JSON file

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

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        return RequirementHierarchy.from_dict(data)

    def _build_requirement_context(
        self,
        requirement: RequirementNode,
        research_doc_path: Optional[str] = None,
    ) -> str:
        """Build formatted context string for a requirement.

        Args:
            requirement: Requirement node to build context for
            research_doc_path: Optional path to research document

        Returns:
            Formatted markdown string with requirement details
        """
        lines: list[str] = [
            f"# Requirement: {requirement.id}",
            "",
            SECTION_HEADERS["description"],
            requirement.description,
            "",
        ]

        # Add function_id if present
        if requirement.function_id:
            lines.extend([
                f"**Function ID**: `{requirement.function_id}`",
                "",
            ])

        # Add related concepts if present
        if requirement.related_concepts:
            lines.extend([
                "**Related Concepts**: " + ", ".join(requirement.related_concepts),
                "",
            ])

        # Add acceptance criteria
        if requirement.acceptance_criteria:
            lines.extend([SECTION_HEADERS["criteria"], ""])
            for i, criterion in enumerate(requirement.acceptance_criteria, 1):
                lines.append(f"{i}. {criterion}")
            lines.append("")

        # Add implementation components
        if requirement.implementation:
            lines.extend([SECTION_HEADERS["implementation"], ""])
            impl = requirement.implementation
            if impl.frontend:
                lines.append(f"**Frontend**: {', '.join(impl.frontend)}")
            if impl.backend:
                lines.append(f"**Backend**: {', '.join(impl.backend)}")
            if impl.middleware:
                lines.append(f"**Middleware**: {', '.join(impl.middleware)}")
            if impl.shared:
                lines.append(f"**Shared**: {', '.join(impl.shared)}")
            lines.append("")

        # Add children recursively
        if requirement.children:
            lines.extend([SECTION_HEADERS["children"], ""])
            for child in requirement.children:
                lines.append(f"### {child.id}: {child.description}")
                if child.acceptance_criteria:
                    lines.append("**Acceptance Criteria**:")
                    for criterion in child.acceptance_criteria:
                        lines.append(f"- {criterion}")
                lines.append("")

        # Add research doc reference
        if research_doc_path:
            lines.extend([
                SECTION_HEADERS["research"],
                f"See: `{research_doc_path}`",
                "",
            ])

        return "\n".join(lines)

    def _load_instruction_template(self, template_name: str) -> Optional[str]:
        """Load instruction template from .claude/commands/.

        Args:
            template_name: Name of template (without .md extension)

        Returns:
            Template content as string, or None if template not found

        Note:
            Logs warning if template file is missing - caller should handle None return
        """
        template_path = self.project_path / ".claude" / "commands" / f"{template_name}.md"
        if not template_path.exists():
            print(f"⚠️  Warning: Template not found: {template_path}")
            print(f"    Expected location: .claude/commands/{template_name}.md")
            return None
        return template_path.read_text(encoding="utf-8")

    def _generate_plan_path(self, requirement: RequirementNode) -> Path:
        """Generate file path for plan document.

        Args:
            requirement: Requirement to generate path for

        Returns:
            Path object for the plan file
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        req_slug = requirement.id.lower().replace("_", "-")
        desc_slug = requirement.description[:30].lower()
        desc_slug = "".join(c if c.isalnum() or c == " " else "" for c in desc_slug)
        desc_slug = "-".join(desc_slug.split())

        plan_dir = self.project_path / "thoughts" / "searchable" / "plans"
        plan_dir.mkdir(parents=True, exist_ok=True)

        return plan_dir / f"{date_str}-tdd-{req_slug}-{desc_slug}.md"

    def _review_plan(self, plan_path: Path) -> Optional[Path]:
        """Review TDD plan using Claude.

        Args:
            plan_path: Path to plan file to review

        Returns:
            Path to review file, or None on error
        """
        if not plan_path.exists():
            print(f"Error: Plan file not found: {plan_path}")
            return None

        # Load review instruction template
        instruction = self._load_instruction_template("review_plan")
        if not instruction:
            return None

        # Read plan content
        plan_content = plan_path.read_text(encoding="utf-8")

        # Build prompt
        prompt = (
            f"Using the instruction template below, review the TDD implementation plan.\n\n"
            f"# Instruction Template\n{instruction}\n\n---\n\n"
            f"# Plan to Review\n**File**: `{plan_path}`\n\n{plan_content}\n\n"
            f"Please provide a comprehensive review following the template structure."
        )

        # Invoke Claude
        result = run_claude_sync(
            prompt=prompt,
            timeout=self.DEFAULT_TIMEOUT,  # 10 minutes for review
            stream=True,
            cwd=self.project_path,
        )

        if not result["success"]:
            print(f"Error reviewing plan: {result['error']}")
            return None

        # Generate review file path (same name with -REVIEW suffix)
        review_path = plan_path.parent / plan_path.name.replace(".md", "-REVIEW.md")

        # Save review content
        review_path.write_text(result["output"], encoding="utf-8")

        return review_path

    def _generate_initial_plan(
        self,
        requirement: RequirementNode,
        research_doc_path: Optional[str] = None,
    ) -> Optional[Path]:
        """Generate initial TDD plan using Claude.

        Args:
            requirement: Requirement to plan for
            research_doc_path: Optional research document path

        Returns:
            Path to generated plan file, or None on error
        """
        # Build context and load template
        req_context = self._build_requirement_context(requirement, research_doc_path)
        instruction = self._load_instruction_template("create_tdd_plan")
        if not instruction:
            return None

        # Build and execute prompt
        prompt = (
            f"Using the instruction template below, create a TDD implementation plan.\n\n"
            f"# Instruction Template\n{instruction}\n\n---\n\n"
            f"# Requirement to Plan\n{req_context}\n\n"
            f"Please create a detailed TDD plan following the template structure."
        )

        result = run_claude_sync(
            prompt=prompt,
            timeout=1200,
            stream=True,
            cwd=self.project_path,
        )

        if not result["success"]:
            print(f"Error generating plan for {requirement.id}: {result['error']}")
            return None

        # Save plan
        plan_path = self._generate_plan_path(requirement)
        plan_path.write_text(result["output"], encoding="utf-8")

        return plan_path

    def _generate_plan_document(
        self,
        hierarchy: RequirementHierarchy,
        plan_name: str,
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
            f"This plan covers {len(hierarchy.requirements)} top-level requirements.",
            "",
        ]

        # Add summary table
        lines.extend(self._generate_summary_table(hierarchy))
        lines.append("")

        # Add each requirement section
        for req in hierarchy.requirements:
            lines.extend(self._generate_requirement_section(req))
            lines.append("")

        # Add success criteria
        lines.extend(self._generate_success_criteria(hierarchy))

        return "\n".join(lines)

    def _generate_summary_table(self, hierarchy: RequirementHierarchy) -> list[str]:
        """Generate summary table of requirements.

        Args:
            hierarchy: Requirement hierarchy

        Returns:
            List of markdown lines for the table
        """
        lines = [
            "## Requirements Summary",
            "",
            "| ID | Description | Criteria | Status |",
            "|-----|-------------|----------|--------|",
        ]

        for req in hierarchy.requirements:
            criteria_count = len(req.acceptance_criteria)
            desc = req.description[:40] + "..." if len(req.description) > 40 else req.description
            lines.append(f"| {req.id} | {desc} | {criteria_count} | Pending |")

        return lines

    def _generate_requirement_section(self, req: RequirementNode) -> list[str]:
        """Generate TDD section for a requirement.

        Args:
            req: Requirement node

        Returns:
            List of markdown lines for the section
        """
        lines = [
            f"## {req.id}: {req.description[:60]}",
            "",
            req.description,
            "",
        ]

        if not req.acceptance_criteria:
            lines.extend([
                "### Testable Behaviors",
                "",
                "_No acceptance criteria defined. Add criteria during implementation._",
                "",
            ])
            return lines

        for i, criterion in enumerate(req.acceptance_criteria, 1):
            lines.extend(self._generate_behavior_tdd(req.id, i, criterion))

        return lines

    def _generate_behavior_tdd(
        self,
        req_id: str,
        behavior_num: int,
        criterion: str,
    ) -> list[str]:
        """Generate Red-Green-Refactor section for a behavior.

        Args:
            req_id: Requirement ID
            behavior_num: Behavior number (1-indexed)
            criterion: Acceptance criterion text

        Returns:
            List of markdown lines for the TDD cycle
        """
        # Parse Given/When/Then from criterion
        given, when, then = self._parse_behavior(criterion)

        # Generate safe identifier from req_id
        safe_id = req_id.lower().replace("-", "_").replace(".", "_")

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
            f"**File**: `tests/test_{safe_id}.py`",
            "```python",
            f"def test_{safe_id}_behavior_{behavior_num}():",
            f'    """Test: {criterion[:60]}..."""',
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

    def _parse_behavior(self, criterion: str) -> tuple[str, str, str]:
        """Parse Given/When/Then from criterion string.

        Args:
            criterion: Acceptance criterion text

        Returns:
            Tuple of (given, when, then) strings
        """
        # Try to extract Given/When/Then
        given_match = re.search(r"[Gg]iven\s+(.+?)(?:,|\s+[Ww]hen)", criterion)
        when_match = re.search(r"[Ww]hen\s+(.+?)(?:,|\s+[Tt]hen)", criterion)
        then_match = re.search(r"[Tt]hen\s+(.+?)(?:$|\.)", criterion)

        given = given_match.group(1).strip() if given_match else "initial state"
        when = when_match.group(1).strip() if when_match else "action performed"
        then = then_match.group(1).strip() if then_match else "expected result"

        return given, when, then

    def _generate_success_criteria(self, hierarchy: RequirementHierarchy) -> list[str]:
        """Generate overall success criteria.

        Args:
            hierarchy: Requirement hierarchy

        Returns:
            List of markdown lines for success criteria
        """
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

    def _save_plan(self, content: str, plan_name: str) -> Path:
        """Save plan document to file.

        Args:
            content: Plan content
            plan_name: Plan name

        Returns:
            Path to saved plan file
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        plan_dir = self.project_path / "thoughts" / "searchable" / "shared" / "plans"
        plan_dir.mkdir(parents=True, exist_ok=True)

        plan_path = plan_dir / f"{date_str}-tdd-{plan_name}.md"
        plan_path.write_text(content, encoding="utf-8")
        return plan_path

    def _store_plan_in_cwa(self, plan_path: str, content: str) -> str:
        """Store plan in CWA as FILE entry.

        Args:
            plan_path: Path to plan file
            content: Plan content

        Returns:
            Entry ID
        """
        # Generate summary from first few lines
        lines = content.split("\n")[:10]
        summary = " ".join(line.strip("#").strip() for line in lines if line.strip())[:200]

        return self.cwa.store_plan(
            path=plan_path,
            content=content,
            summary=summary,
        )

    def execute(
        self,
        plan_name: str,
        hierarchy_path: str,
    ) -> PhaseResult:
        """Execute TDD planning phase.

        Args:
            plan_name: Name for the plan
            hierarchy_path: Path to hierarchy JSON file on disk

        Returns:
            PhaseResult with plan artifacts
        """
        started_at = datetime.now()

        try:
            # Load hierarchy from file on disk
            hierarchy = self._load_hierarchy(hierarchy_path)

            # Generate plan document
            plan_content = self._generate_plan_document(hierarchy, plan_name)

            # Save plan
            plan_path = self._save_plan(plan_content, plan_name)

            # Store in CWA
            entry_id = self._store_plan_in_cwa(str(plan_path), plan_content)

            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            return PhaseResult(
                phase_type=PhaseType.TDD_PLANNING,
                status=PhaseStatus.COMPLETE,
                artifacts=[str(plan_path)],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                metadata={
                    "cwa_entry_id": entry_id,
                    "requirements_count": len(hierarchy.requirements),
                    "plan_path": str(plan_path),
                    "hierarchy_path": hierarchy_path,
                },
            )

        except FileNotFoundError as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            return PhaseResult(
                phase_type=PhaseType.TDD_PLANNING,
                status=PhaseStatus.FAILED,
                errors=[str(e)],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
            )

        except json.JSONDecodeError as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            return PhaseResult(
                phase_type=PhaseType.TDD_PLANNING,
                status=PhaseStatus.FAILED,
                errors=[f"Invalid JSON: {e}"],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
            )

        except Exception as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            return PhaseResult(
                phase_type=PhaseType.TDD_PLANNING,
                status=PhaseStatus.FAILED,
                errors=[str(e)],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                metadata={"exception_type": type(e).__name__},
            )

    def execute_with_checkpoint(
        self,
        plan_name: str,
        hierarchy_path: str,
        auto_approve: bool = False,
    ) -> PhaseResult:
        """Execute TDD planning phase with interactive checkpoint.

        After planning completes, prompts user for action unless auto_approve is True.

        Args:
            plan_name: Name for the plan
            hierarchy_path: Path to hierarchy JSON file on disk
            auto_approve: If True, skip user prompts

        Returns:
            PhaseResult with plan artifacts and user action
        """
        result = self.execute(
            plan_name=plan_name,
            hierarchy_path=hierarchy_path,
        )

        # If failed or auto-approve, return immediately
        if result.status == PhaseStatus.FAILED or auto_approve:
            if auto_approve and result.status == PhaseStatus.COMPLETE:
                result.metadata["user_action"] = "continue"
            return result

        # Prompt user for action
        action = prompt_tdd_planning_action()
        result.metadata["user_action"] = action

        if action == "continue":
            return result
        elif action == "revise":
            # For TDD planning, revision means regenerating with feedback
            # The feedback would need to be handled at the pipeline level
            print("\nEnter feedback for revision (empty line to finish):")
            feedback = collect_multiline_input("> ")
            result.metadata["revision_feedback"] = feedback
            result.metadata["needs_revision"] = True
            return result
        elif action == "restart":
            # Indicate restart needed
            result.metadata["needs_restart"] = True
            return result
        elif action == "exit":
            result.metadata["user_exit"] = True
            return result
        else:
            # Unknown action, treat as continue
            return result
