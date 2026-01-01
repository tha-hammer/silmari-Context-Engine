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

    # Load research instructions from markdown file
    research_instructions_path = project_path / ".claude" / "commands" / "research_codebase.md"
    with open(research_instructions_path, "r", encoding="utf-8") as f:
        research_instructions = f.read()

    # Process the instructions: remove "Initial Setup" section and insert research question
    lines = research_instructions.split("\n")
    
    # Find where to insert the research question (after "# Research Codebase")
    insert_idx = 1
    for i, line in enumerate(lines):
        if line.strip() == "# Research Codebase":
            insert_idx = i + 1
            break
    
    # Insert research question section
    lines.insert(insert_idx, "")
    lines.insert(insert_idx + 1, "## Research Question")
    lines.insert(insert_idx + 2, research_prompt)
    lines.insert(insert_idx + 3, "")
    
    # Remove the "Initial Setup" section (for interactive use only)
    start_removal = None
    end_removal = None
    for i, line in enumerate(lines):
        if "## Initial Setup:" in line:
            start_removal = i
        if start_removal is not None and "Then wait for the user's research query." in line:
            end_removal = i + 1
            break
    
    if start_removal is not None and end_removal is not None:
        lines = lines[:start_removal] + lines[end_removal:]
    
    # Rejoin and replace date placeholder in filename section
    research_instructions = "\n".join(lines)
    research_instructions = research_instructions.replace(
        "Filename: `thoughts/shared/research/YYYY-MM-DD-ENG-XXXX-description.md`",
        f"Filename: `thoughts/shared/research/{date_str}-pipeline-research.md` (or `{date_str}-ENG-XXXX-description.md` if ticket exists)"
    )

    prompt = f"""{research_instructions}

After creating the document, output the path.
"""

    result = run_claude_sync(
        prompt=prompt,
        timeout=1200  # 20 minutes for research phase
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

    # Load planning instructions from markdown file
    planning_instructions_path = project_path / ".claude" / "commands" / "create_tdd_plan.md"
    with open(planning_instructions_path, "r", encoding="utf-8") as f:
        planning_instructions = f.read()

    # Process the instructions: remove "Initial Response" section and insert context
    lines = planning_instructions.split("\n")
    
    # Find where to insert the research document and context (after "# TDD Implementation Plan")
    insert_idx = 1
    for i, line in enumerate(lines):
        if line.strip() == "# TDD Implementation Plan":
            insert_idx = i + 1
            break
    
    # Insert research document and additional context sections
    lines.insert(insert_idx, "")
    lines.insert(insert_idx + 1, "## Research Document")
    lines.insert(insert_idx + 2, f"Read the research at: {research_path}")
    lines.insert(insert_idx + 3, "")
    
    if additional_context:
        lines.insert(insert_idx + 4, "## Additional Context")
        lines.insert(insert_idx + 5, additional_context)
        lines.insert(insert_idx + 6, "")
        insert_offset = 6
    else:
        insert_offset = 3
    
    # Remove the "Initial Response" section (for interactive use only)
    start_removal = None
    end_removal = None
    for i, line in enumerate(lines):
        if "## Initial Response" in line:
            start_removal = i
        if start_removal is not None and "## Process Steps" in line:
            end_removal = i
            break
    
    if start_removal is not None and end_removal is not None:
        lines = lines[:start_removal] + lines[end_removal:]
    
    # Rejoin and replace date placeholder in filename section
    planning_instructions = "\n".join(lines)
    planning_instructions = planning_instructions.replace(
        "`thoughts/shared/plans/YYYY-MM-DD-ENG-XXXX-tdd-description.md`",
        f"`thoughts/shared/plans/{date_str}-plan.md`"
    )
    planning_instructions = planning_instructions.replace(
        "- Format: `YYYY-MM-DD-ENG-XXXX-tdd-description.md`",
        f"- Format: `{date_str}-plan.md` (or `{date_str}-ENG-XXXX-tdd-description.md` if ticket exists)"
    )

    prompt = f"""{planning_instructions}

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


def step_memory_sync(
    project_path: Path,
    research_path: str,
    session_id: str
) -> dict[str, Any]:
    """Sync 4-layer memory and clear Claude context between phases.

    Runs between research and planning to:
    1. Record research as episodic memory
    2. Compile working context from all memory layers
    3. Clear Claude's context with /clear

    Args:
        project_path: Root path of the project
        research_path: Path to the research document
        session_id: Unique session identifier

    Returns:
        Dictionary with keys:
        - success: bool
        - episode_recorded: bool
        - context_compiled: bool
        - context_cleared: bool
    """
    import subprocess

    results = {
        "episode_recorded": False,
        "context_compiled": False,
        "context_cleared": False
    }

    # Read research summary for episodic memory
    try:
        research_file = project_path / research_path if not Path(research_path).is_absolute() else Path(research_path)
        if research_file.exists():
            content = research_file.read_text()
            # Extract first paragraph as summary (after title)
            lines = content.split('\n')
            summary_lines = []
            in_content = False
            for line in lines:
                if line.startswith('# '):
                    in_content = True
                    continue
                if in_content and line.strip():
                    summary_lines.append(line.strip())
                    if len(summary_lines) >= 3:
                        break
            summary = ' '.join(summary_lines)[:500] if summary_lines else f"Research session {session_id}"
        else:
            summary = f"Research session {session_id}"
    except Exception:
        summary = f"Research session {session_id}"

    # 1. Record episodic memory
    try:
        result = subprocess.run(
            ["silmari-oracle", "memory", "episode", session_id, summary],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(project_path)
        )
        results["episode_recorded"] = result.returncode == 0
    except Exception:
        results["episode_recorded"] = False

    # 2. Compile working context
    try:
        result = subprocess.run(
            ["silmari-oracle", "memory", "compile"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(project_path)
        )
        results["context_compiled"] = result.returncode == 0
    except Exception:
        results["context_compiled"] = False

    # 3. Clear Claude context
    try:
        result = subprocess.run(
            ["claude", "--print", "-p", "/clear"],
            capture_output=True,
            text=True,
            timeout=30
        )
        results["context_cleared"] = result.returncode == 0
    except Exception:
        results["context_cleared"] = False

    results["success"] = True  # Memory sync is best-effort, don't fail pipeline
    return results
