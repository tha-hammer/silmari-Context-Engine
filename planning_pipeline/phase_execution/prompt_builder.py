"""Prompt generation for phase execution."""

from pathlib import Path
from typing import Optional


def build_phase_prompt(plan_path: str, current_phase: Optional[str]) -> str:
    """Build a prompt for executing the current phase.

    Args:
        plan_path: Path to the plan file
        current_phase: Current phase identifier (e.g., feature ID)

    Returns:
        Formatted prompt string for Claude

    Raises:
        FileNotFoundError: If plan_path doesn't exist
    """
    path = Path(plan_path)
    if not path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")

    plan_content = path.read_text()
    phase_id = current_phase or "unknown"

    return f"""## Phase: {phase_id}

## Plan Content
{plan_content}

## Instructions
1. Implement the requirements described in the plan above
2. Run tests to verify implementation
3. Commit changes with descriptive message
4. Use `bd sync` if beads changes were made

## Success Criteria
- All tests pass
- Changes are committed
- Code follows existing patterns
"""
