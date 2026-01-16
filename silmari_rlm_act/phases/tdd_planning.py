"""TDD Planning phase implementation.

This module implements the TDD planning phase of the silmari-rlm-act pipeline,
which generates TDD plan documents from requirement hierarchies using
Red-Green-Refactor cycles.

Enhanced to use Claude Agent SDK for generating actual test code instead of
placeholder templates. Also includes post-generation review sessions.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from silmari_rlm_act.checkpoints.interactive import (
    collect_multiline_input,
    prompt_tdd_planning_action,
)
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseResult, PhaseStatus, PhaseType

from planning_pipeline.models import RequirementHierarchy, RequirementNode
from planning_pipeline.claude_runner import run_claude_sync, HAS_CLAUDE_SDK

logger = logging.getLogger(__name__)


# Review prompt template for 5-step discrete analysis
REVIEW_PROMPT_TEMPLATE = """You are reviewing a TDD implementation plan.

Read the plan at: {plan_path}

Perform 5-step discrete analysis:

## Step 1: Contract Analysis
Identify interfaces between components. Are they well-defined?

## Step 2: Interface Analysis
Check component boundaries. Are they clear and minimal?

## Step 3: Promise Analysis
Review assertions and expectations. Are they verifiable?

## Step 4: Data Model Analysis
Examine types and structures. Are they correct and complete?

## Step 5: API Analysis
Check endpoints and protocols. Are they documented?

Return JSON with:
{{
  "findings": [
    {{"step": "Contract", "severity": "critical|important|minor", "issue": "...", "suggestion": "..."}}
  ],
  "overall_quality": "good|needs_work|poor",
  "amendments": ["suggested change 1", "suggested change 2"]
}}
"""


def run_review_session(plan_path: str) -> dict[str, Any]:
    """Run review_plan skill on generated TDD plan in a fresh session.

    Creates an independent LLM session to review the generated plan
    using the 5-step discrete analysis from review_plan:
    1. Contract Analysis
    2. Interface Analysis
    3. Promise Analysis
    4. Data Model Analysis
    5. API Analysis

    Uses run_claude_sync() which wraps the claude_agent_sdk for
    synchronous LLM calls.

    Args:
        plan_path: Absolute path to the generated TDD plan file

    Returns:
        Review results with:
        - success: bool
        - output: review findings text
        - error: error message if failed
        - elapsed: time in seconds
    """
    review_prompt = REVIEW_PROMPT_TEMPLATE.format(plan_path=plan_path)

    return run_claude_sync(
        prompt=review_prompt,
        timeout=300,
        stream=False,
    )

# TDD Generation prompt template
TDD_GENERATION_PROMPT = """You are an expert TDD practitioner generating implementation-ready plans.

## Requirement
ID: {req_id}
Description: {req_description}

## Acceptance Criteria
{criteria_text}

Generate a TDD plan for EACH acceptance criterion following Red-Green-Refactor:

### Test Code Requirements (CRITICAL):
- Must be COMPLETE, RUNNABLE pytest code
- Must have real assertions (assert x == y, assert x in y, etc.)
- NEVER use `assert False` or `# TODO` placeholders
- Include proper imports, fixtures, and test setup
- Test the EXACT behavior described in the criterion

For each behavior, output:
1. Test Specification (Given/When/Then)
2. Edge Cases (2-3 scenarios)
3. 🔴 Red: Complete failing test with real assertions
4. 🟢 Green: Minimal implementation to pass
5. 🔵 Refactor: Improved implementation
6. Success Criteria (automated and manual checks)

Output ONLY markdown content, no additional commentary.
"""


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

    def _generate_requirement_tdd_plan(
        self,
        req: RequirementNode,
        plan_name: str,
    ) -> tuple[Path | None, dict[str, Any] | None]:
        """Generate TDD plan file for a single requirement and run review.

        Args:
            req: RequirementNode to generate plan for
            plan_name: Base name for the plan

        Returns:
            Tuple of (plan_path, review_result):
            - plan_path: Path to the generated plan file, or None if generation failed
            - review_result: Review session result dict, or None if review failed/skipped
        """
        # Generate content for this requirement
        content = self._generate_plan_content_for_requirement(req, plan_name)

        # Create file path with requirement ID
        date_str = datetime.now().strftime("%Y-%m-%d")
        plan_dir = self.project_path / "thoughts" / "searchable" / "shared" / "plans"
        plan_dir.mkdir(parents=True, exist_ok=True)

        # Pattern: YYYY-MM-DD-tdd-{plan_name}-{req_id}.md
        req_id_lower = req.id.lower().replace("-", "_")
        plan_path = plan_dir / f"{date_str}-tdd-{plan_name}-{req_id_lower}.md"

        plan_path.write_text(content, encoding="utf-8")

        # Run review session after plan is saved
        review_result = None
        try:
            logger.info(f"Running review session for {req.id}")
            review_result = run_review_session(str(plan_path))

            if review_result.get("success"):
                # Save review alongside plan
                review_path = plan_path.with_suffix(".review.md")
                self._write_review_file(review_path, review_result)
                logger.info(f"Review saved to {review_path}")
            else:
                logger.warning(
                    f"Review returned error for {req.id}: {review_result.get('error')}"
                )
        except Exception as e:
            logger.warning(f"Review session failed for {req.id}: {e}")
            # Don't fail - plan is still saved

        return plan_path, review_result

    def _write_review_file(
        self,
        review_path: Path,
        review_result: dict[str, Any],
    ) -> None:
        """Write review results to companion file.

        Args:
            review_path: Path to write review file
            review_result: Review result dict from run_review_session
        """
        content = [
            "# TDD Plan Review Results",
            "",
            f"**Generated**: {datetime.now().isoformat()}",
            "",
            "## Findings",
            "",
            review_result.get("output", "No findings available"),
        ]
        review_path.write_text("\n".join(content), encoding="utf-8")

    def _generate_plan_content_for_requirement(
        self,
        req: RequirementNode,
        plan_name: str,
    ) -> str:
        """Generate TDD plan content for a single requirement.

        Uses the Claude Agent SDK to generate actual test code instead of
        placeholder templates. Falls back to static templates if SDK
        is unavailable or fails.

        Args:
            req: RequirementNode to generate content for
            plan_name: Name of the plan (for context)

        Returns:
            Markdown content string
        """
        # Try LLM-based generation if SDK is available
        if HAS_CLAUDE_SDK and req.acceptance_criteria:
            try:
                return self._generate_llm_content(req, plan_name)
            except Exception as e:
                logger.warning(f"LLM generation failed for {req.id}: {e}, using fallback")

        # Fallback to static template generation
        return self._generate_fallback_content(req, plan_name)

    def _generate_llm_content(
        self,
        req: RequirementNode,
        plan_name: str,
    ) -> str:
        """Generate TDD plan content using Claude Agent SDK.

        Calls the LLM to generate actual test code instead of placeholders.

        Args:
            req: RequirementNode to generate content for
            plan_name: Name of the plan (for context)

        Returns:
            Markdown content string from LLM

        Raises:
            RuntimeError: If LLM call fails
        """
        # Build criteria text
        criteria_text = "\n".join(f"- {c}" for c in req.acceptance_criteria)

        # Build prompt
        prompt = TDD_GENERATION_PROMPT.format(
            req_id=req.id,
            req_description=req.description,
            criteria_text=criteria_text,
        )

        # Call LLM via Agent SDK
        logger.info(f"Generating TDD content for {req.id} via LLM")
        result = run_claude_sync(
            prompt=prompt,
            timeout=300,
            stream=False,  # Don't stream for content generation
        )

        if not result.get("success"):
            raise RuntimeError(f"LLM call failed: {result.get('error', 'Unknown error')}")

        llm_output = result.get("output", "")
        if not llm_output:
            raise RuntimeError("LLM returned empty response")

        # Format with header
        return self._format_llm_response(llm_output, req, plan_name)

    def _format_llm_response(
        self,
        llm_output: str,
        req: RequirementNode,
        plan_name: str,
    ) -> str:
        """Format LLM response into TDD plan markdown.

        Args:
            llm_output: Raw output from LLM
            req: RequirementNode for context
            plan_name: Name of the plan

        Returns:
            Formatted markdown document
        """
        lines = [
            f"# {req.id}: {req.description[:60]}",
            "",
            f"**Full Description**: {req.description}",
            "",
            "## Overview",
            "",
            f"This plan covers {len(req.acceptance_criteria)} testable behaviors for {req.id}.",
            "",
            "---",
            "",
            llm_output,  # LLM-generated content
            "",
            "## Success Criteria",
            "",
            "### Automated",
            f"- [ ] All tests pass: `pytest tests/test_{req.id.lower().replace('-', '_')}.py -v`",
            "- [ ] Type checking: `mypy .`",
            "- [ ] Lint: `ruff check .`",
            "",
            "### Manual",
            "- [ ] All behaviors implemented",
            "- [ ] Code reviewed",
            "- [ ] Documentation updated",
        ]

        return "\n".join(lines)

    def _generate_fallback_content(
        self,
        req: RequirementNode,
        plan_name: str,
    ) -> str:
        """Generate fallback TDD plan content when LLM is unavailable.

        Uses static templates with Given/When/Then parsing.

        Args:
            req: RequirementNode to generate content for
            plan_name: Name of the plan (for context)

        Returns:
            Markdown content string
        """
        lines = [
            f"# {req.id}: {req.description[:60]}",
            "",
            f"**Full Description**: {req.description}",
            "",
            "## Overview",
            "",
            f"This plan covers {len(req.acceptance_criteria)} testable behaviors for {req.id}.",
            "",
            "_LLM content generation unavailable. Using template generation._",
            "",
            "---",
            "",
        ]

        if not req.acceptance_criteria:
            lines.extend([
                "## Testable Behaviors",
                "",
                "_No acceptance criteria defined. Add criteria during implementation._",
                "",
            ])
        else:
            for i, criterion in enumerate(req.acceptance_criteria, 1):
                lines.extend(self._generate_behavior_tdd(req.id, i, criterion))

        # Add success criteria
        lines.extend([
            "## Success Criteria",
            "",
            "### Automated",
            f"- [ ] All tests pass: `pytest tests/test_{req.id.lower().replace('-', '_')}.py -v`",
            "- [ ] Type checking: `mypy .`",
            "- [ ] Lint: `ruff check .`",
            "",
            "### Manual",
            "- [ ] All behaviors implemented",
            "- [ ] Code reviewed",
            "- [ ] Documentation updated",
        ])

        return "\n".join(lines)

    def execute(
        self,
        plan_name: str,
        hierarchy_path: str,
    ) -> PhaseResult:
        """Execute TDD planning phase - generate one plan file per requirement.

        For each RequirementNode in the hierarchy, generates an individual
        TDD plan file with test specifications and Red-Green-Refactor cycles,
        then runs a review session for each plan.

        Args:
            plan_name: Base name for the plan files
            hierarchy_path: Path to hierarchy JSON file on disk

        Returns:
            PhaseResult with list of generated plan file paths
        """
        started_at = datetime.now()
        artifacts: list[str] = []
        errors: list[str] = []
        cwa_entry_ids: list[str] = []
        reviews_completed = 0
        review_failures = 0

        try:
            # Load hierarchy from file on disk
            hierarchy = self._load_hierarchy(hierarchy_path)

            # Generate individual plan for each requirement
            for req in hierarchy.requirements:
                try:
                    plan_path, review_result = self._generate_requirement_tdd_plan(
                        req, plan_name
                    )
                    if plan_path:
                        artifacts.append(str(plan_path))

                        # Store in CWA
                        content = plan_path.read_text(encoding="utf-8")
                        entry_id = self._store_plan_in_cwa(str(plan_path), content)
                        cwa_entry_ids.append(entry_id)

                        # Track review status
                        if review_result and review_result.get("success"):
                            reviews_completed += 1
                        elif review_result is not None:
                            # Review was attempted but failed
                            review_failures += 1
                except Exception as req_error:
                    errors.append(f"Failed to generate plan for {req.id}: {req_error}")

            # Determine status based on results
            if errors and not artifacts:
                status = PhaseStatus.FAILED
            elif errors or review_failures > 0:
                status = PhaseStatus.PARTIAL
            else:
                status = PhaseStatus.COMPLETE

            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            return PhaseResult(
                phase_type=PhaseType.TDD_PLANNING,
                status=status,
                artifacts=artifacts,
                errors=errors,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                metadata={
                    "cwa_entry_ids": cwa_entry_ids,
                    "requirements_count": len(hierarchy.requirements),
                    "plans_generated": len(artifacts),
                    "hierarchy_path": hierarchy_path,
                    "reviews_completed": reviews_completed,
                    "review_failures": review_failures,
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
