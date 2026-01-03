"""Plan discovery and phase ordering for loop execution.

Discovers plan files in a directory and orders them for sequential execution.
Supports the naming convention: {prefix}-{NN}-{phase-name}.md where NN is 00-99.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional


@dataclass
class PlanPhase:
    """Represents a single phase from a plan document."""

    path: Path
    order: int
    name: str
    is_overview: bool = False

    @property
    def phase_id(self) -> str:
        """Return a unique ID for this phase (filename stem)."""
        return self.path.stem


def discover_plan_phases(plan_dir: Path, prefix: str) -> List[PlanPhase]:
    """Discover all phases for a plan with given prefix.

    Args:
        plan_dir: Directory containing plan files
        prefix: Common prefix for plan files (e.g., "2026-01-03-tdd-execute-phase-implementation")

    Returns:
        List of PlanPhase objects sorted by order

    Example:
        Given files:
            2026-01-03-tdd-execute-phase-implementation-00-overview.md
            2026-01-03-tdd-execute-phase-implementation-01-prompt-generation.md
            2026-01-03-tdd-execute-phase-implementation-02-claude-invocation.md

        discover_plan_phases(dir, "2026-01-03-tdd-execute-phase-implementation")
        Returns phases ordered [00-overview, 01-prompt-generation, 02-claude-invocation]
    """
    if not plan_dir.exists():
        return []

    # Pattern: {prefix}-{NN}-{name}.md
    pattern = re.compile(rf"^{re.escape(prefix)}-(\d{{2}})-(.+)\.md$")

    phases = []
    for file in plan_dir.glob(f"{prefix}-*.md"):
        match = pattern.match(file.name)
        if match:
            order = int(match.group(1))
            name = match.group(2)
            is_overview = name.lower() == "overview" or order == 0
            phases.append(PlanPhase(path=file, order=order, name=name, is_overview=is_overview))

    # Sort by order number
    phases.sort(key=lambda p: p.order)
    return phases


def find_plan_prefix_from_epic(plan_dir: Path, epic_id: str) -> Optional[str]:
    """Find the plan prefix associated with a beads epic.

    This searches for plan files that might be related to the given epic.
    Uses heuristics based on date and naming patterns.

    Args:
        plan_dir: Directory containing plan files
        epic_id: The beads epic ID (e.g., "silmari-Context-Engine-ydl")

    Returns:
        The plan prefix if found, None otherwise
    """
    # Look for files matching common patterns
    # Plans typically have format: YYYY-MM-DD-tdd-{feature-name}.md
    # or numbered phases: YYYY-MM-DD-tdd-{feature-name}-NN-{phase}.md

    from datetime import date

    today = date.today().isoformat()

    # Find all unique prefixes from today's plans
    prefixes = set()
    phase_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2}-.+?)-(\d{2})-.+\.md$")

    for file in plan_dir.glob(f"{today}-*.md"):
        match = phase_pattern.match(file.name)
        if match:
            prefixes.add(match.group(1))

    if len(prefixes) == 1:
        return prefixes.pop()

    # If multiple or none, return None - caller should specify explicitly
    return None


def iterate_plan_phases(
    plan_dir: Path,
    prefix: str,
    skip_overview: bool = False,
    start_from: Optional[int] = None,
) -> Iterator[PlanPhase]:
    """Iterate through plan phases in order.

    Args:
        plan_dir: Directory containing plan files
        prefix: Common prefix for plan files
        skip_overview: If True, skip the overview phase (00)
        start_from: If specified, start from this phase number

    Yields:
        PlanPhase objects in order
    """
    phases = discover_plan_phases(plan_dir, prefix)

    for phase in phases:
        if skip_overview and phase.is_overview:
            continue
        if start_from is not None and phase.order < start_from:
            continue
        yield phase


def get_next_phase(
    plan_dir: Path,
    prefix: str,
    current_phase: Optional[int] = None,
) -> Optional[PlanPhase]:
    """Get the next phase after the current one.

    Args:
        plan_dir: Directory containing plan files
        prefix: Common prefix for plan files
        current_phase: Current phase number (None means get first non-overview phase)

    Returns:
        Next PlanPhase or None if at end
    """
    phases = discover_plan_phases(plan_dir, prefix)

    if not phases:
        return None

    if current_phase is None:
        # Return first non-overview phase, or first phase if only overview exists
        for phase in phases:
            if not phase.is_overview:
                return phase
        return phases[0] if phases else None

    # Find next phase after current
    for i, phase in enumerate(phases):
        if phase.order == current_phase:
            if i + 1 < len(phases):
                return phases[i + 1]
            return None

    # Current phase not found, return first phase
    return phases[0] if phases else None
