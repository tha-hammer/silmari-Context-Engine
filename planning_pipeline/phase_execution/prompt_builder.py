"""Prompt generation for phase execution."""

from pathlib import Path
from typing import Optional

from planning_pipeline.phase_execution.plan_discovery import PlanPhase


def build_phase_prompt(
    plan_path: str,
    current_phase: Optional[str] = None,
    phase_info: Optional[PlanPhase] = None,
    total_phases: int = 1,
    current_phase_num: int = 1,
) -> str:
    """Build a prompt for executing the current phase.

    Args:
        plan_path: Path to the plan file
        current_phase: Current phase identifier (e.g., feature ID or beads issue ID)
        phase_info: Optional PlanPhase with structured phase metadata
        total_phases: Total number of phases in the plan
        current_phase_num: Current phase number (1-indexed for display)

    Returns:
        Formatted prompt string for Claude

    Raises:
        FileNotFoundError: If plan_path doesn't exist
    """
    path = Path(plan_path)
    if not path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")

    plan_content = path.read_text()

    # Build phase identifier
    if phase_info:
        phase_id = f"{phase_info.name} (Phase {current_phase_num}/{total_phases})"
    elif current_phase:
        phase_id = current_phase
    else:
        phase_id = "unknown"

    # Build progress indicator
    progress_indicator = ""
    if total_phases > 1:
        progress_bar = "█" * current_phase_num + "░" * (total_phases - current_phase_num)
        progress_indicator = f"\n## Progress: [{progress_bar}] Phase {current_phase_num} of {total_phases}\n"

    return f"""## Phase: {phase_id}
{progress_indicator}
## Plan Content
{plan_content}

## Instructions
1. Read the plan above carefully before starting
2. Implement the requirements described in the plan
3. Run tests to verify implementation: `pytest` or appropriate test command
4. Commit changes with descriptive message
5. Use `bd close <issue-id>` if completing a beads issue
6. Use `bd sync` to sync beads changes

## Success Criteria
- All tests pass
- Changes are committed
- Code follows existing patterns
- Any referenced beads issues are updated

## IMPORTANT
- Focus ONLY on this phase's requirements
- Do not implement features from other phases
- If blocked, document the blocker and mark phase incomplete
"""


def build_overview_prompt(overview_path: str, phase_count: int) -> str:
    """Build a prompt for reviewing the plan overview.

    Args:
        overview_path: Path to the overview document
        phase_count: Total number of phases (excluding overview)

    Returns:
        Formatted prompt for reviewing the plan
    """
    path = Path(overview_path)
    if not path.exists():
        raise FileNotFoundError(f"Overview file not found: {overview_path}")

    overview_content = path.read_text()

    return f"""## Plan Overview

{overview_content}

## Phase Summary
This plan contains {phase_count} implementation phase(s).
Each phase will be executed sequentially, with tests verified between phases.

## Instructions
Review this overview to understand:
1. The overall goal of this implementation
2. The phases and their dependencies
3. Key technical decisions and constraints

After review, proceed to Phase 1 implementation.
"""
