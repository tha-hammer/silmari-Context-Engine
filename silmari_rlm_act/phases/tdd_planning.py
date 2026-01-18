"""TDD Planning phase implementation.

This module implements the TDD planning phase of the silmari-rlm-act pipeline,
which generates TDD plan documents from requirement hierarchies using
Red-Green-Refactor cycles.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from planning_pipeline.claude_runner import run_claude_sync
from planning_pipeline.models import RequirementHierarchy, RequirementNode
from silmari_rlm_act.checkpoints.interactive import (
    collect_multiline_input,
    prompt_tdd_planning_action,
)
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseResult, PhaseStatus, PhaseType

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

    def _enhance_plan(self, plan_path: Path, review_path: Path) -> bool:
        """Enhance TDD plan using review feedback.

        Args:
            plan_path: Path to original plan file (will be updated)
            review_path: Path to review file

        Returns:
            True if enhancement succeeded, False otherwise
        """
        if not plan_path.exists() or not review_path.exists():
            print("Error: Plan or review file not found")
            return False

        # Load instruction template (reuse create_tdd_plan.md)
        instruction = self._load_instruction_template("create_tdd_plan")
        if not instruction:
            return False

        # Read plan and review content
        plan_content = plan_path.read_text(encoding="utf-8")
        review_content = review_path.read_text(encoding="utf-8")

        # Build enhancement prompt
        prompt = (
            f"You are NOT creating a new plan. You are ENHANCING an existing TDD plan.\n\n"
            f"Using the instruction template and review feedback below, enhance the existing plan.\n\n"
            f"# Instruction Template\n{instruction}\n\n---\n\n"
            f"# Existing Plan\n**File**: `{plan_path}`\n\n{plan_content}\n\n---\n\n"
            f"# Review Feedback\n**File**: `{review_path}`\n\n{review_content}\n\n---\n\n"
            f"Please enhance the plan by addressing the review feedback. "
            f"Output the complete enhanced plan (not just changes)."
        )

        # Invoke Claude
        result = run_claude_sync(
            prompt=prompt,
            timeout=1200,  # 20 minutes for enhancement
            stream=True,
            cwd=self.project_path,
        )

        if not result["success"]:
            print(f"Error enhancing plan: {result['error']}")
            return False

        # Update original plan file
        plan_path.write_text(result["output"], encoding="utf-8")

        return True

    def _process_requirement(
        self,
        requirement: RequirementNode,
        research_doc_path: Optional[str] = None,
    ) -> Optional[Path]:
        """Process requirement through 3-session TDD planning loop.

        Sessions:
        1. Generate initial plan
        2. Review plan
        3. Enhance plan using review

        Args:
            requirement: Requirement to process
            research_doc_path: Optional research document path

        Returns:
            Path to final plan file, or None if session 1 failed
        """
        print(f"\n{'='*60}")
        print(f"Processing requirement: {requirement.id}")
        print(f"{'='*60}")

        # Session 1: Generate initial plan
        print(f"\n[Session 1/3] Generating initial plan...")
        plan_path = self._generate_initial_plan(requirement, research_doc_path)
        if not plan_path:
            print(f"❌ Session 1 failed for {requirement.id}")
            return None
        print(f"✓ Initial plan created: {plan_path}")

        # Session 2: Review plan
        print(f"\n[Session 2/3] Reviewing plan...")
        review_path = self._review_plan(plan_path)
        if not review_path:
            print(f"⚠️  Session 2 failed, keeping unreviewed plan")
            return plan_path
        print(f"✓ Review created: {review_path}")

        # Session 3: Enhance plan
        print(f"\n[Session 3/3] Enhancing plan with review feedback...")
        success = self._enhance_plan(plan_path, review_path)
        if not success:
            print(f"⚠️  Session 3 failed, keeping unenhanced plan")
            return plan_path
        print(f"✓ Plan enhanced: {plan_path}")

        return plan_path

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

    def execute(
        self,
        hierarchy_path: str,
        research_doc_path: Optional[str] = None,
    ) -> PhaseResult:
        """Execute TDD planning phase with LLM-driven multi-session approach.

        For each top-level requirement in hierarchy:
        1. Generate initial plan using Claude + create_tdd_plan.md
        2. Review plan using Claude + review_plan.md
        3. Enhance plan using Claude + review feedback

        Args:
            hierarchy_path: Path to requirement hierarchy JSON file
            research_doc_path: Optional path to research document

        Returns:
            PhaseResult with plan artifacts and metadata
        """
        started_at = datetime.now()
        plan_paths: list[Path] = []
        cwa_entry_ids: list[str] = []
        failed_requirements: list[str] = []

        try:
            # Load hierarchy
            hierarchy = self._load_hierarchy(hierarchy_path)

            print(f"\n{'='*70}")
            print(f"TDD Planning Phase: Processing {len(hierarchy.requirements)} requirements")
            print(f"{'='*70}")

            # Process each top-level requirement
            for i, requirement in enumerate(hierarchy.requirements, 1):
                print(f"\n\n[Requirement {i}/{len(hierarchy.requirements)}]")

                # Process through 3-session loop
                plan_path = self._process_requirement(requirement, research_doc_path)

                if plan_path:
                    plan_paths.append(plan_path)

                    # Store in CWA
                    plan_content = plan_path.read_text(encoding="utf-8")
                    summary = f"TDD plan for {requirement.id}: {requirement.description[:100]}"
                    entry_id = self.cwa.store_plan(
                        path=str(plan_path),
                        content=plan_content,
                        summary=summary,
                    )
                    cwa_entry_ids.append(entry_id)
                    print(f"✓ Plan stored in CWA: {entry_id}")
                else:
                    failed_requirements.append(requirement.id)
                    print(f"❌ Failed to create plan for {requirement.id}")

            # Calculate results
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            successful_count = len(plan_paths)
            failed_count = len(failed_requirements)

            print(f"\n{'='*70}")
            print(f"TDD Planning Complete:")
            print(f"  ✓ Successful: {successful_count}/{len(hierarchy.requirements)}")
            if failed_count > 0:
                print(f"  ❌ Failed: {failed_count}")
                print(f"     {', '.join(failed_requirements)}")
            print(f"  Duration: {duration:.1f}s")
            print(f"{'='*70}\n")

            return PhaseResult(
                phase_type=PhaseType.TDD_PLANNING,
                status=PhaseStatus.COMPLETE,
                artifacts=[str(p) for p in plan_paths],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                metadata={
                    "hierarchy_path": hierarchy_path,
                    "research_doc_path": research_doc_path,
                    "requirements_count": len(hierarchy.requirements),
                    "successful_plans": successful_count,
                    "failed_plans": failed_count,
                    "failed_requirements": failed_requirements,
                    "cwa_entry_ids": cwa_entry_ids,
                    "intermediate_files_policy": "preserved_on_failure",
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
                errors=[f"Invalid hierarchy JSON: {e}"],
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
        hierarchy_path: str,
        research_doc_path: Optional[str] = None,
        auto_approve: bool = False,
    ) -> PhaseResult:
        """Execute TDD planning phase with interactive checkpoint.

        After planning completes, prompts user for action unless auto_approve is True.

        Args:
            hierarchy_path: Path to hierarchy JSON file on disk
            research_doc_path: Optional path to research document
            auto_approve: If True, skip user prompts

        Returns:
            PhaseResult with plan artifacts and user action
        """
        result = self.execute(
            hierarchy_path=hierarchy_path,
            research_doc_path=research_doc_path,
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
