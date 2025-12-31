"""Pipeline step implementations for research, planning, and phase decomposition."""

from pathlib import Path
from datetime import datetime
from typing import Any

from .claude_runner import run_claude_sync
from .helpers import extract_file_path, extract_open_questions, extract_phase_files
from .beads_controller import BeadsController


def step_research(project_path: Path, research_prompt: str) -> dict[str, Any]:
    """Execute research phase of the pipeline.

    Args:
        project_path: Root path of the project
        research_prompt: The research question or topic

    Returns:
        Dictionary with keys:
        - success: bool
        - research_path: path to created document (if successful)
        - output: raw Claude output
        - open_questions: list of extracted questions
    """
    date_str = datetime.now().strftime('%Y-%m-%d')

    prompt = f"""# Research Task

{research_prompt}

## Instructions
1. Research the codebase to answer the question
2. Create a research document at: thoughts/shared/research/{date_str}-pipeline-research.md
3. Include file:line references for findings
4. List any open questions at the end under "## Open Questions"

After creating the document, output the path.
"""

    result = run_claude_sync(
        prompt=prompt,
        timeout=300
    )

    if not result["success"]:
        return {"success": False, "error": result.get("error", "Research failed")}

    research_path = extract_file_path(result["output"], "research")
    open_questions = extract_open_questions(result["output"])

    return {
        "success": True,
        "research_path": research_path,
        "output": result["output"],
        "open_questions": open_questions
    }


def step_planning(
    project_path: Path,
    research_path: str,
    additional_context: str = ""
) -> dict[str, Any]:
    """Execute planning phase of the pipeline.

    Args:
        project_path: Root path of the project
        research_path: Path to the research document
        additional_context: Additional context or feedback

    Returns:
        Dictionary with keys:
        - success: bool
        - plan_path: path to created plan (if successful)
        - output: raw Claude output
    """
    date_str = datetime.now().strftime('%Y-%m-%d')

    prompt = f"""# Create Implementation Plan

## Research Document
Read the research at: {research_path}

{f'## Additional Context{chr(10)}{additional_context}' if additional_context else ''}

## Instructions
1. Review the research findings
2. Identify implementation phases
3. Create a plan file at: thoughts/shared/plans/{date_str}-plan.md

## Plan Structure
Each phase must have:
- Overview of what it accomplishes
- Changes Required with file:line references
- Success Criteria (automated + manual)

Output the plan file path when complete.
"""

    result = run_claude_sync(
        prompt=prompt,
        timeout=300
    )

    if not result["success"]:
        return {"success": False, "error": result.get("error", "Planning failed")}

    plan_path = extract_file_path(result["output"], "plan")

    return {
        "success": True,
        "plan_path": plan_path,
        "output": result["output"]
    }


def step_phase_decomposition(project_path: Path, plan_path: str) -> dict[str, Any]:
    """Decompose plan into separate phase files.

    Args:
        project_path: Root path of the project
        plan_path: Path to the plan document

    Returns:
        Dictionary with keys:
        - success: bool
        - phase_files: list of created phase file paths
        - output: raw Claude output
    """
    plan_dir = str(Path(plan_path).parent)

    prompt = f"""# Phase Decomposition Task

Read the plan file at: {plan_path}

## Instructions
Create distinct phase files based on the plan. Each phase should end with 1 testable function.

## Output Structure
Create files at: {plan_dir}/
- 00-overview.md (links to all phases)
- 01-phase-1-<name>.md
- 02-phase-2-<name>.md
- etc.

## Phase File Template
Each phase file must contain:
- Overview
- Dependencies (requires/blocks)
- Changes Required with file:line
- Success Criteria

After creating all files, list the created file paths.
"""

    result = run_claude_sync(
        prompt=prompt,
        timeout=300
    )

    if not result["success"]:
        return {"success": False, "error": result.get("error", "Phase decomposition failed")}

    phase_files = extract_phase_files(result["output"])

    return {
        "success": True,
        "phase_files": phase_files,
        "output": result["output"]
    }


def step_beads_integration(
    project_path: Path,
    phase_files: list[str],
    epic_title: str
) -> dict[str, Any]:
    """Create beads issues for plan phases with dependencies.

    Args:
        project_path: Root path of the project
        phase_files: List of phase file paths
        epic_title: Title for the epic issue

    Returns:
        Dictionary with keys:
        - success: bool
        - epic_id: ID of created epic
        - phase_issues: list of phase issue details
    """
    bd = BeadsController(project_path)

    # Create epic
    epic_result = bd.create_epic(epic_title)
    if not epic_result["success"]:
        return {"success": False, "error": f"Failed to create epic: {epic_result.get('error')}"}

    epic_id = epic_result["data"].get("id") if isinstance(epic_result["data"], dict) else None

    # Create issues for each phase
    phase_issues = []
    for i, phase_file in enumerate(phase_files):
        # Extract phase name from filename like "01-phase-1-setup.md"
        phase_name = Path(phase_file).stem.split('-', 2)[-1].replace('-', ' ').title()

        result = bd.create_issue(
            title=f"Phase {i+1}: {phase_name}",
            issue_type="task",
            priority=2
        )

        if result["success"]:
            issue_id = result["data"].get("id") if isinstance(result["data"], dict) else None
            phase_issues.append({
                "phase": i + 1,
                "file": phase_file,
                "issue_id": issue_id
            })

    # Link dependencies (each phase depends on previous)
    for i in range(1, len(phase_issues)):
        curr_id = phase_issues[i].get("issue_id")
        prev_id = phase_issues[i-1].get("issue_id")
        if curr_id and prev_id:
            bd.add_dependency(curr_id, prev_id)

    bd.sync()

    return {
        "success": True,
        "epic_id": epic_id,
        "phase_issues": phase_issues
    }
