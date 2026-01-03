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
        "Filename: `thoughts/shared/research/YYYY-MM-DD-description.md`",
        f"Filename: `thoughts/shared/research/{date_str}-pipeline-research.md` (or `{date_str}-description.md` if ticket exists)"
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

    # Validate that research_path was extracted - common failure when running from external directory
    if not research_path:
        return {
            "success": False,
            "error": "Research completed but no research file path found in output. "
                     "Claude may not have created a file, or the path pattern was not recognized. "
                     "Check that the project has a thoughts/shared/research/ directory.",
            "output": result["output"],
            "open_questions": open_questions
        }

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
        "`thoughts/shared/plans/YYYY-MM-DD-tdd-description.md`",
        f"`thoughts/shared/plans/{date_str}-plan.md`"
    )
    planning_instructions = planning_instructions.replace(
        "- Format: `YYYY-MM-DD-tdd-description.md`",
        f"- Format: `{date_str}-plan.md` (or `{date_str}-tdd-description.md` if ticket exists)"
    )

    prompt = f"""{planning_instructions}

Output the plan file path when complete.
"""

    # Loop to handle cases where Claude asks for clarification
    max_retries = 3
    for attempt in range(max_retries):
        result = run_claude_sync(
            prompt=prompt,
            timeout=1200  # 20 minutes for planning phase
        )

        if not result["success"]:
            return {"success": False, "error": result.get("error", "Planning failed")}

        plan_path = extract_file_path(result["output"], "plan")

        if plan_path:
            return {
                "success": True,
                "plan_path": plan_path,
                "output": result["output"]
            }

        # No plan path found - Claude may have asked for clarification
        # Check if output contains question indicators
        output_lower = result["output"].lower()
        is_question = any(q in output_lower for q in [
            "could you", "can you", "would you", "what is", "which",
            "clarify", "specify", "more information", "more details",
            "please provide", "i need to understand", "?"
        ])

        if is_question and attempt < max_retries - 1:
            print(f"\n{'='*60}")
            print("CLAUDE NEEDS CLARIFICATION")
            print(f"{'='*60}")
            print("\nClaude's response did not produce a plan file.")
            print("Please provide additional context or answers:\n")

            # Collect user input
            user_response = []
            print("(Enter your response, blank line to finish)")
            while True:
                line = input("> ").strip()
                if not line:
                    break
                user_response.append(line)

            if user_response:
                # Append user response to prompt and retry
                additional_input = "\n".join(user_response)
                prompt = f"""{prompt}

## User Clarification answering open questions in planning process. (Attempt {attempt + 2})
{additional_input}

Now create the plan file. Output the plan file path when complete.
"""
                print(f"Sending additional context...")
                continue

        # No plan path and not a question, or max retries reached
        break

    return {
        "success": True,
        "plan_path": None,  # Let caller handle missing plan_path
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
    if not plan_path:
        return {"success": False, "error": "plan_path is required but was None"}

    plan_dir = str(Path(plan_path).parent)

    prompt = f"""# Phase Decomposition Task

Read the plan file at: {plan_path}

## Instructions
Create distinct phase files based on the plan. Each phase should end with 1 human-testable function.

## Output Structure
Create files at: {plan_dir}/
Append YYYY-MM-DD-tdd-description to the filename of each file.
- YYYY-MM-DD-tdd-description-00-overview.md (links to all phases)
- YYYY-MM-DD-tdd-description-01-phase-1.md
- YYYY-MM-DD-tdd-description-02-phase-2.md
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
        timeout=1200  # 20 minutes for phase decomposition
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
    """Create beads issues for plan phases and annotate files with bd commands.

    This step:
    1. Creates an epic issue for the overall plan
    2. Creates task issues for each phase with dependencies
    3. Uses Claude SDK to add bd commands to overview and phase files
    4. Returns the created issue IDs

    Args:
        project_path: Root path of the project
        phase_files: List of phase file paths from decomposition
        epic_title: Title for the epic issue

    Returns:
        Dictionary with keys:
        - success: bool
        - epic_id: ID of created epic
        - phase_issues: list of phase issue details
        - files_annotated: list of files that were annotated with bd commands
    """
    bd = BeadsController(project_path)

    # Create epic
    epic_result = bd.create_epic(epic_title)
    if not epic_result["success"]:
        return {"success": False, "error": f"Failed to create epic: {epic_result.get('error')}"}

    epic_id = epic_result["data"].get("id") if isinstance(epic_result["data"], dict) else None

    # Separate overview file from phase files
    overview_file = None
    actual_phase_files = []
    for f in phase_files:
        if "overview" in f.lower() or f.endswith("00-overview.md"):
            overview_file = f
        else:
            actual_phase_files.append(f)

    # Create issues for each phase
    phase_issues: list[dict[str, Any]] = []
    for i, phase_file in enumerate(actual_phase_files):
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
        curr_id: str | None = phase_issues[i].get("issue_id")
        prev_id: str | None = phase_issues[i-1].get("issue_id")
        if curr_id and prev_id:
            bd.add_dependency(curr_id, prev_id)

    bd.sync()

    # Now use Claude SDK to annotate files with bd commands
    files_annotated = []

    # Build issue mapping for Claude
    issue_mapping = {
        "epic": {"id": epic_id, "title": epic_title},
        "phases": phase_issues
    }

    # Annotate overview file if it exists
    if overview_file:
        overview_path = Path(overview_file)
        if not overview_path.is_absolute():
            overview_path = project_path / overview_file

        if overview_path.exists():
            overview_content = overview_path.read_text()
            annotated = _annotate_overview_with_claude(
                project_path, overview_file, overview_content, issue_mapping
            )
            if annotated:
                files_annotated.append(overview_file)

    # Annotate each phase file
    for phase_info in phase_issues:
        pfile: str = phase_info["file"]
        phase_path = Path(pfile)
        if not phase_path.is_absolute():
            phase_path = project_path / pfile

        if phase_path.exists():
            phase_content = phase_path.read_text()
            overview_content = ""
            if overview_file:
                ov_path = project_path / overview_file if not Path(overview_file).is_absolute() else Path(overview_file)
                if ov_path.exists():
                    overview_content = ov_path.read_text()

            annotated = _annotate_phase_with_claude(
                project_path, pfile, phase_content, overview_content, phase_info
            )
            if annotated:
                files_annotated.append(pfile)

    return {
        "success": True,
        "epic_id": epic_id,
        "phase_issues": phase_issues,
        "files_annotated": files_annotated
    }


def _annotate_overview_with_claude(
    project_path: Path,
    overview_file: str,
    overview_content: str,
    issue_mapping: dict
) -> bool:
    """Use Claude SDK to add bd commands to overview file.

    Args:
        project_path: Root path of the project
        overview_file: Path to the overview file
        overview_content: Current content of the overview file
        issue_mapping: Dict with epic and phase issue information

    Returns:
        True if annotation was successful
    """
    epic_id = issue_mapping["epic"]["id"]
    phases = issue_mapping["phases"]

    # Build phase list for prompt
    phase_list = "\n".join([
        f"- Phase {p['phase']}: {p['file']} -> Issue ID: {p['issue_id']}"
        for p in phases
    ])

    prompt = f"""# Task: Add Beads Issue References to Overview File

You need to add `bd` command references to a plan overview file.

## File to Edit
Path: {overview_file}

## Current Content
```markdown
{overview_content}
```

## Issue Information
- Epic ID: {epic_id}
- Phase Issues:
{phase_list}

## Instructions

1. Add a "Beads Tracking" section at the top of the file (after the title) with:
   - Epic reference: `bd show {epic_id}`
   - List of phase issues with their IDs

2. In the phase list/links section, add the issue ID next to each phase reference.

3. Add helpful bd commands in a "Workflow Commands" subsection:
   - `bd ready` - see available work
   - `bd update <id> --status=in_progress` - start a phase
   - `bd close <id>` - complete a phase

Edit the file at {overview_file} with these additions.
Only add the beads information, do not change the existing plan content.
"""

    result = run_claude_sync(prompt=prompt, timeout=120)
    return result["success"]


def _annotate_phase_with_claude(
    project_path: Path,
    phase_file: str,
    phase_content: str,
    overview_content: str,
    phase_info: dict
) -> bool:
    """Use Claude SDK to add bd commands to a phase file.

    Args:
        project_path: Root path of the project
        phase_file: Path to the phase file
        phase_content: Current content of the phase file
        overview_content: Content of overview file for context
        phase_info: Dict with phase number, file, and issue_id

    Returns:
        True if annotation was successful
    """
    issue_id = phase_info["issue_id"]
    phase_num = phase_info["phase"]

    prompt = f"""# Task: Add Beads Issue Reference to Phase File

You need to add a `bd` command reference to a plan phase file.

## Overview Context
```markdown
{overview_content[:2000]}
```

## File to Edit
Path: {phase_file}

## Current Content
```markdown
{phase_content}
```

## Issue Information
- Phase {phase_num} Issue ID: {issue_id}

## Instructions

1. Add a small "Tracking" section at the top of the file (after the title) with:
   - Issue reference: `{issue_id}`
   - Start command: `bd update {issue_id} --status=in_progress`
   - Complete command: `bd close {issue_id}`

2. Keep it minimal - just 3-4 lines showing how to track this phase.

Edit the file at {phase_file} with these additions.
Only add the tracking information, do not change the existing phase content.
"""

    result = run_claude_sync(prompt=prompt, timeout=120)
    return result["success"]


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
