#!/usr/bin/env python3
"""Resume a failed planning pipeline from a specific step."""

from pathlib import Path
import sys
import argparse
from planning_pipeline import (
    step_research,
    step_planning,
    step_phase_decomposition,
    step_beads_integration
)

def resume_pipeline(step: str, **kwargs):
    """Resume pipeline from a specific step.
    
    Args:
        step: One of 'research', 'planning', 'decomposition', 'beads'
        **kwargs: Required arguments for the step
    """
    project_path = Path.cwd()
    
    if step == "research":
        if "research_prompt" not in kwargs:
            print("Error: research_prompt required for research step")
            sys.exit(1)
        result = step_research(project_path, kwargs["research_prompt"])
        
    elif step == "planning":
        if "research_path" not in kwargs:
            print("Error: research_path required for planning step")
            sys.exit(1)
        result = step_planning(
            project_path,
            kwargs["research_path"],
            kwargs.get("additional_context", "")
        )
        
    elif step == "decomposition":
        if "plan_path" not in kwargs:
            print("Error: plan_path required for decomposition step")
            sys.exit(1)
        result = step_phase_decomposition(project_path, kwargs["plan_path"])
        
    elif step == "beads":
        if "phase_files" not in kwargs or "epic_title" not in kwargs:
            print("Error: phase_files and epic_title required for beads step")
            sys.exit(1)
        result = step_beads_integration(
            project_path,
            kwargs["phase_files"],
            kwargs["epic_title"]
        )
    else:
        print(f"Error: Unknown step '{step}'. Use: research, planning, decomposition, or beads")
        sys.exit(1)
    
    if result["success"]:
        print(f"✓ {step.capitalize()} step completed successfully")
        print(f"Result: {result}")
    else:
        print(f"✗ {step.capitalize()} step failed")
        print(f"Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)
    
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Resume a failed planning pipeline from a specific step",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Resume from planning
  resume_pipeline.py planning --research-path thoughts/shared/research/2025-12-31-research.md
  
  # Resume from planning with additional context
  resume_pipeline.py planning --research-path research.md --additional-context "Focus on authentication"
  
  # Resume from decomposition
  resume_pipeline.py decomposition --plan-path thoughts/shared/plans/2025-12-31-plan.md
  
  # Resume from beads integration
  resume_pipeline.py beads --phase-files file1.md file2.md --epic-title "My Epic"
  
  # Resume from research
  resume_pipeline.py research --research-prompt "How does authentication work?"
        """
    )
    
    parser.add_argument(
        "step",
        choices=["research", "planning", "decomposition", "beads"],
        help="Step to resume from"
    )
    
    # Arguments for research step
    parser.add_argument(
        "--research-prompt", "--research_prompt",
        dest="research_prompt",
        help="Research question/prompt (required for research step)"
    )

    # Arguments for planning step
    parser.add_argument(
        "--research-path", "--research_path",
        dest="research_path",
        help="Path to research document (required for planning step)"
    )
    parser.add_argument(
        "--additional-context", "--additional_context",
        dest="additional_context",
        default="",
        help="Additional context for planning step"
    )

    # Arguments for decomposition step
    parser.add_argument(
        "--plan-path", "--plan_path",
        dest="plan_path",
        help="Path to plan document (required for decomposition step)"
    )

    # Arguments for beads step
    parser.add_argument(
        "--phase-files", "--phase_files",
        dest="phase_files",
        nargs="+",
        help="List of phase file paths (required for beads step)"
    )
    parser.add_argument(
        "--epic-title", "--epic_title",
        dest="epic_title",
        help="Title for the epic (required for beads step)"
    )
    
    args = parser.parse_args()
    
    # Build kwargs based on step
    kwargs = {}
    
    if args.step == "research":
        if not args.research_prompt:
            parser.error("--research-prompt is required for research step")
        kwargs["research_prompt"] = args.research_prompt
        
    elif args.step == "planning":
        if not args.research_path:
            parser.error("--research-path is required for planning step")
        kwargs["research_path"] = args.research_path
        if args.additional_context:
            kwargs["additional_context"] = args.additional_context
            
    elif args.step == "decomposition":
        if not args.plan_path:
            parser.error("--plan-path is required for decomposition step")
        kwargs["plan_path"] = args.plan_path
        
    elif args.step == "beads":
        if not args.phase_files:
            parser.error("--phase-files is required for beads step")
        if not args.epic_title:
            parser.error("--epic-title is required for beads step")
        kwargs["phase_files"] = args.phase_files
        kwargs["epic_title"] = args.epic_title
    
    resume_pipeline(args.step, **kwargs)