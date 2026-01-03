"""Phase execution module for autonomous loop.

Provides:
- plan_discovery: Discover and iterate through plan phase files
- prompt_builder: Build prompts for phase execution
- claude_invoker: Invoke Claude for execution
- result_checker: Validate execution results
"""

from planning_pipeline.phase_execution.plan_discovery import (
    PlanPhase,
    discover_plan_phases,
    find_plan_prefix_from_epic,
    get_next_phase,
    iterate_plan_phases,
)
from planning_pipeline.phase_execution.prompt_builder import (
    build_overview_prompt,
    build_phase_prompt,
)

__all__ = [
    "PlanPhase",
    "discover_plan_phases",
    "find_plan_prefix_from_epic",
    "get_next_phase",
    "iterate_plan_phases",
    "build_overview_prompt",
    "build_phase_prompt",
]
