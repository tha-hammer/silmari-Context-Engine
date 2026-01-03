---
date: 2026-01-01T10:30:00-05:00
author: maceo
git_commit: 1b4d995
branch: main
repository: silmari-Context-Engine
topic: "Resume Pipeline Integration Implementation Plan"
tags: [plan, tdd, planning-pipeline, resume, checkpoints]
status: approved
---

```
┌─────────────────────────────────────────────────────────────────┐
│       RESUME PIPELINE INTEGRATION - TDD IMPLEMENTATION PLAN     │
│                    silmari-Context-Engine                       │
│                        2026-01-01                               │
└─────────────────────────────────────────────────────────────────┘
```

# Resume Pipeline Integration Implementation Plan

## Overview

Integrate `resume_pipeline.py` functionality into `planning_orchestrator.py` to provide:
1. Auto-detection of failed pipeline runs from `.workflow-checkpoints/` JSON files
2. Interactive file selection when research/plan documents aren't provided
3. Checkpoint cleanup with 30-day warning and interactive menu
4. Unified CLI entry point for both fresh runs and resumes

## Current State Analysis

### Existing Components

| File | Purpose | Status |
|------|---------|--------|
| `planning_orchestrator.py` | Main CLI, runs full pipeline | Working |
| `resume_pipeline.py` | Standalone resume script | Working but not integrated |
| `planning_pipeline/helpers.py` | Path extraction utilities | Missing file discovery |
| `planning_pipeline/checkpoints.py` | Interactive checkpoint prompts | Missing file selection |
| `.workflow-checkpoints/*.json` | Failed run state | Uses relative paths |

### Key Discoveries
- `planning_pipeline/__init__.py:9` - Already exports step functions
- Checkpoint files use relative paths (`./thoughts/...`) - needs absolute per design
- `state_snapshot.artifacts` array holds produced file paths
- `phase` field indicates failure point (e.g., "planning-failed")

## Desired End State

After implementation:
```bash
# Auto-detect and resume from last checkpoint
python planning_orchestrator.py --resume

# Resume from specific step with file selection
python planning_orchestrator.py --resume --resume-step planning

# Resume with explicit path
python planning_orchestrator.py --resume --research-path /abs/path/to/research.md

# Normal fresh run (unchanged)
python planning_orchestrator.py
```

### Verification
- `--resume` without args auto-detects from `.workflow-checkpoints/`
- Missing paths trigger interactive file selection
- 30+ day old checkpoints trigger cleanup prompt
- Successful runs delete their checkpoint files
- All checkpoint paths are absolute

## What We're NOT Doing

| Out of Scope | What We ARE Doing |
|--------------|-------------------|
| Changing step implementations | Adding resume entry points to existing steps |
| Modifying beads integration | Using existing `step_beads_integration()` |
| Adding new pipeline steps | Orchestrating existing 4 steps |
| Changing thoughts/ structure | Reading from existing structure |
| Multi-checkpoint resume | Single most-recent checkpoint only |

---

╔═══════════════════════════════════════════════════════════════╗
║                         PHASE 1                               ║
║              Checkpoint Management Module                     ║
╚═══════════════════════════════════════════════════════════════╝

## Phase 1: Checkpoint Management Module

### Overview
Create checkpoint detection, age checking, and cleanup functions in a new module.

### Changes Required

#### 1. Create `planning_pipeline/checkpoint_manager.py`

**File**: `planning_pipeline/checkpoint_manager.py` (NEW)

```python
"""Checkpoint management for pipeline resume functionality."""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional


def detect_resumable_checkpoint(project_path: Path) -> Optional[dict]:
    """Find most recent failed checkpoint.

    Args:
        project_path: Root project directory

    Returns:
        Dict with checkpoint data or None if no checkpoints exist.
        Keys: 'id', 'phase', 'timestamp', 'state_snapshot', 'git_commit', 'file_path'
    """
    checkpoints_dir = project_path / ".workflow-checkpoints"
    if not checkpoints_dir.exists():
        return None

    checkpoints = []
    for f in checkpoints_dir.glob("*.json"):
        try:
            with open(f) as fp:
                data = json.load(fp)
                data["file_path"] = str(f)  # Track source file
                checkpoints.append(data)
        except (json.JSONDecodeError, IOError):
            continue

    if not checkpoints:
        return None

    # Sort by timestamp descending (most recent first)
    checkpoints.sort(key=lambda c: c.get("timestamp", ""), reverse=True)
    return checkpoints[0]


def get_checkpoint_age_days(checkpoint: dict) -> int:
    """Calculate age of checkpoint in days.

    Args:
        checkpoint: Checkpoint dict with 'timestamp' key

    Returns:
        Age in days (0 if today)
    """
    timestamp_str = checkpoint.get("timestamp", "")
    if not timestamp_str:
        return 0

    try:
        # Handle ISO format with Z suffix
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1] + "+00:00"
        checkpoint_time = datetime.fromisoformat(timestamp_str)
        age = datetime.now(checkpoint_time.tzinfo) - checkpoint_time
        return age.days
    except (ValueError, TypeError):
        return 0


def check_checkpoint_cleanup_needed(project_path: Path, warn_days: int = 30) -> tuple[bool, list[dict]]:
    """Check if checkpoint cleanup warning should be shown.

    Args:
        project_path: Root project directory
        warn_days: Days after which to warn (default 30)

    Returns:
        Tuple of (should_warn, list of checkpoint dicts with age info)
    """
    checkpoints_dir = project_path / ".workflow-checkpoints"
    if not checkpoints_dir.exists():
        return False, []

    checkpoints = []
    oldest_date = None

    for f in checkpoints_dir.glob("*.json"):
        try:
            with open(f) as fp:
                data = json.load(fp)
                data["file_path"] = str(f)
                age = get_checkpoint_age_days(data)
                data["age_days"] = age
                checkpoints.append(data)

                # Track oldest
                ts = data.get("timestamp", "")
                if ts and (oldest_date is None or ts < oldest_date):
                    oldest_date = ts
        except (json.JSONDecodeError, IOError):
            continue

    if not checkpoints:
        return False, []

    # Check if any checkpoint exceeds warn_days
    max_age = max(c.get("age_days", 0) for c in checkpoints)
    return max_age >= warn_days, checkpoints


def delete_checkpoint(checkpoint_path: str) -> bool:
    """Delete a single checkpoint file.

    Args:
        checkpoint_path: Absolute path to checkpoint JSON file

    Returns:
        True if deleted successfully
    """
    try:
        Path(checkpoint_path).unlink()
        return True
    except (IOError, OSError):
        return False


def cleanup_checkpoints_by_age(
    checkpoints: list[dict],
    days_to_delete: int
) -> tuple[int, int]:
    """Delete checkpoints older than specified days.

    Args:
        checkpoints: List of checkpoint dicts with 'age_days' and 'file_path'
        days_to_delete: Delete checkpoints older than this many days

    Returns:
        Tuple of (deleted_count, failed_count)
    """
    deleted = 0
    failed = 0

    for cp in checkpoints:
        if cp.get("age_days", 0) >= days_to_delete:
            if delete_checkpoint(cp["file_path"]):
                deleted += 1
            else:
                failed += 1

    return deleted, failed


def cleanup_all_checkpoints(project_path: Path) -> tuple[int, int]:
    """Delete all checkpoint files.

    Args:
        project_path: Root project directory

    Returns:
        Tuple of (deleted_count, failed_count)
    """
    checkpoints_dir = project_path / ".workflow-checkpoints"
    if not checkpoints_dir.exists():
        return 0, 0

    deleted = 0
    failed = 0

    for f in checkpoints_dir.glob("*.json"):
        try:
            f.unlink()
            deleted += 1
        except (IOError, OSError):
            failed += 1

    return deleted, failed


def write_checkpoint(
    project_path: Path,
    phase: str,
    artifacts: list[str],
    errors: list[str] = None
) -> str:
    """Write a checkpoint file for failed pipeline state.

    Args:
        project_path: Root project directory
        phase: Phase that failed (e.g., "planning-failed")
        artifacts: List of absolute paths to produced artifacts
        errors: Optional list of error messages

    Returns:
        Path to created checkpoint file
    """
    import uuid

    checkpoints_dir = project_path / ".workflow-checkpoints"
    checkpoints_dir.mkdir(exist_ok=True)

    checkpoint_id = str(uuid.uuid4())
    checkpoint_file = checkpoints_dir / f"{checkpoint_id}.json"

    # Get current git commit
    import subprocess
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(project_path)
        )
        git_commit = result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        git_commit = ""

    data = {
        "id": checkpoint_id,
        "phase": phase,
        "timestamp": datetime.now().isoformat() + "Z",
        "state_snapshot": {
            "phase": phase.replace("-failed", "").title(),
            "context_usage": 0.0,
            "artifacts": artifacts,  # Must be absolute paths
            "errors": errors or []
        },
        "git_commit": git_commit
    }

    with open(checkpoint_file, "w") as fp:
        json.dump(data, fp, indent=2)

    return str(checkpoint_file)
```

#### 2. Add to exports

**File**: `planning_pipeline/__init__.py`
**Changes**: Add checkpoint_manager imports

```python
from .checkpoint_manager import (
    detect_resumable_checkpoint,
    check_checkpoint_cleanup_needed,
    cleanup_checkpoints_by_age,
    cleanup_all_checkpoints,
    write_checkpoint,
    delete_checkpoint,
)
```

### Success Criteria

#### Automated Verification:
- [ ] Unit tests pass: `python -m pytest planning_pipeline/tests/test_checkpoint_manager.py -v`
- [ ] Type checking passes: `python -m mypy planning_pipeline/checkpoint_manager.py`
- [ ] Module imports work: `python -c "from planning_pipeline import detect_resumable_checkpoint"`

#### Manual Verification:
- [ ] `detect_resumable_checkpoint()` finds existing checkpoint in `.workflow-checkpoints/`
- [ ] Age calculation works correctly for checkpoint timestamps
- [ ] Cleanup functions delete correct files

---

╔═══════════════════════════════════════════════════════════════╗
║                         PHASE 2                               ║
║              File Discovery & Selection                       ║
╚═══════════════════════════════════════════════════════════════╝

## Phase 2: File Discovery & Selection

### Overview
Add functions to discover research/plan files from thoughts/ directory and present interactive selection menu.

### Changes Required

#### 1. Add to `planning_pipeline/helpers.py`

**File**: `planning_pipeline/helpers.py`
**Changes**: Add `discover_thoughts_files()` function

```python
from datetime import datetime, timedelta

def discover_thoughts_files(
    project_path: Path,
    file_type: str,
    days_back: int = 0
) -> list[Path]:
    """Discover research or plan files from thoughts directory.

    Args:
        project_path: Root project directory
        file_type: "research" or "plans"
        days_back: How many days back to search (0 = today only)

    Returns:
        List of matching file paths sorted alphabetically by filename
    """
    thoughts_dir = project_path / "thoughts"

    # Try both direct and searchable paths
    search_dirs = [
        thoughts_dir / "shared" / file_type,
        thoughts_dir / "searchable" / "shared" / file_type,
    ]

    search_dir = None
    for d in search_dirs:
        if d.exists():
            search_dir = d
            break

    if search_dir is None:
        return []

    cutoff_date = datetime.now() - timedelta(days=days_back)
    cutoff_str = cutoff_date.strftime('%Y-%m-%d')

    files = []
    for f in search_dir.glob("*.md"):
        # Files are named YYYY-MM-DD-description.md
        if len(f.stem) >= 10:
            date_part = f.stem[:10]
            if date_part >= cutoff_str:
                files.append(f)

    # Sort alphabetically by filename
    return sorted(files, key=lambda f: f.name)
```

#### 2. Add to `planning_pipeline/checkpoints.py`

**File**: `planning_pipeline/checkpoints.py`
**Changes**: Add interactive file selection and cleanup menu functions

```python
def prompt_file_selection(
    files: list[Path],
    file_type: str
) -> tuple[str, Path | None]:
    """Interactive menu to select a file or search/specify other.

    Args:
        files: List of discovered file paths
        file_type: "research" or "plans" for display

    Returns:
        Tuple of (action, path) where action is:
        - "selected": user picked a file, path is the file
        - "search": user wants to search more days
        - "other": user wants to specify custom path
        - "exit": user wants to exit
    """
    print(f"\n{'='*60}")
    print(f"SELECT {file_type.upper()} FILE")
    print(f"{'='*60}")

    if files:
        print(f"\nFound {len(files)} {file_type} file(s):")
        for i, f in enumerate(files, 1):
            print(f"  [{i}] {f.name}")
    else:
        print(f"\nNo {file_type} files found.")

    print(f"\n  [S] Search again (specify days)")
    print(f"  [O] Other (specify path)")
    print(f"  [E] Exit")

    while True:
        response = input(f"\nChoice: ").strip()

        if response.lower() == 's':
            return ("search", None)
        elif response.lower() == 'o':
            return ("other", None)
        elif response.lower() == 'e':
            return ("exit", None)
        elif response.isdigit():
            idx = int(response) - 1
            if 0 <= idx < len(files):
                return ("selected", files[idx])
            print(f"Invalid number. Enter 1-{len(files)}")
        else:
            print("Invalid choice. Enter a number, S, O, or E.")


def prompt_search_days() -> int:
    """Prompt user for number of days to search back.

    Returns:
        Number of days (minimum 0)
    """
    while True:
        response = input("Search how many days back? [7]: ").strip()
        if not response:
            return 7
        if response.isdigit():
            return int(response)
        print("Please enter a number.")


def prompt_custom_path(file_type: str) -> Path | None:
    """Prompt user to enter a custom file path.

    Args:
        file_type: "research" or "plans" for display

    Returns:
        Path object if valid, None if user cancels
    """
    print(f"\nEnter path to {file_type} file (or blank to cancel):")
    response = input("> ").strip()

    if not response:
        return None

    path = Path(response).expanduser().resolve()
    if not path.exists():
        print(f"File not found: {path}")
        return None

    return path


def prompt_checkpoint_cleanup(
    checkpoint_count: int,
    oldest_date: str
) -> tuple[str, int]:
    """Interactive cleanup menu for old checkpoints.

    Args:
        checkpoint_count: Total number of checkpoint files
        oldest_date: Date string of oldest checkpoint (YYYY-MM-DD)

    Returns:
        Tuple of (action, days) where action is:
        - "oldest": delete oldest 10 days
        - "last_n": delete last N days (days param filled)
        - "all": delete all (confirmed)
        - "skip": skip cleanup
    """
    print(f"\n{'='*60}")
    print(f"CHECKPOINT CLEANUP")
    print(f"{'='*60}")
    print(f"\n  You have {checkpoint_count} checkpoint file(s) (oldest: {oldest_date})")

    print(f"\n  [O] Delete oldest 10 days")
    print(f"  [L] Delete last N days (you specify)")
    print(f"  [A] Delete all (requires confirmation)")
    print(f"  [S] Skip cleanup")

    while True:
        response = input(f"\nChoice [S]: ").strip().lower()

        if response == '' or response == 's':
            return ("skip", 0)
        elif response == 'o':
            return ("oldest", 10)
        elif response == 'l':
            days = prompt_search_days()
            return ("last_n", days)
        elif response == 'a':
            # Double confirmation for delete all
            confirm = input(f"  This will delete ALL {checkpoint_count} checkpoint files. Type 'ALL' to confirm: ").strip()
            if confirm == "ALL":
                return ("all", 0)
            print("  Cancelled.")
        else:
            print("Invalid choice. Enter O, L, A, or S.")
```

#### 3. Update exports

**File**: `planning_pipeline/__init__.py`
**Changes**: Add new function exports

```python
from .helpers import extract_file_path, extract_open_questions, extract_phase_files, discover_thoughts_files
from .checkpoints import (
    interactive_checkpoint_research,
    interactive_checkpoint_plan,
    prompt_file_selection,
    prompt_search_days,
    prompt_custom_path,
    prompt_checkpoint_cleanup,
)
```

### Success Criteria

#### Automated Verification:
- [ ] Unit tests pass: `python -m pytest planning_pipeline/tests/test_helpers.py -v`
- [ ] Unit tests pass: `python -m pytest planning_pipeline/tests/test_checkpoints.py -v`
- [ ] Module imports work: `python -c "from planning_pipeline import discover_thoughts_files, prompt_file_selection"`

#### Manual Verification:
- [ ] `discover_thoughts_files()` finds today's research files
- [ ] `discover_thoughts_files()` with `days_back=7` finds last week's files
- [ ] Files are sorted alphabetically
- [ ] `prompt_file_selection()` displays menu correctly
- [ ] Cleanup menu options all work as expected

---

╔═══════════════════════════════════════════════════════════════╗
║                         PHASE 3                               ║
║                    CLI Integration                            ║
╚═══════════════════════════════════════════════════════════════╝

## Phase 3: CLI Integration

### Overview
Modify `planning_orchestrator.py` to add resume arguments and flow logic.

### Changes Required

#### 1. Update argument parser

**File**: `planning_orchestrator.py`
**Location**: `parse_args()` function (~line 20-58)

Add after existing arguments:

```python
# Resume arguments
parser.add_argument(
    "--resume", "-r",
    action="store_true",
    help="Resume from a previous step (auto-detects from checkpoints)"
)
parser.add_argument(
    "--resume-step", "--resume_step",
    dest="resume_step",
    choices=["planning", "decomposition", "beads"],
    help="Step to resume from (default: auto-detect)"
)
parser.add_argument(
    "--research-path", "--research_path",
    dest="research_path",
    help="Path to existing research document (for resume)"
)
parser.add_argument(
    "--plan-path", "--plan_path",
    dest="plan_path",
    help="Path to existing plan document (for resume)"
)
```

#### 2. Add resume flow to main()

**File**: `planning_orchestrator.py`
**Location**: `main()` function (~line 191-241)

Replace the main function with integrated resume logic:

```python
def main() -> int:
    """Main entry point with resume support."""
    import sys
    from planning_pipeline import (
        detect_resumable_checkpoint,
        check_checkpoint_cleanup_needed,
        cleanup_checkpoints_by_age,
        cleanup_all_checkpoints,
        discover_thoughts_files,
        prompt_file_selection,
        prompt_search_days,
        prompt_custom_path,
        prompt_checkpoint_cleanup,
        step_planning,
        step_phase_decomposition,
        step_beads_integration,
    )

    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{'Planning Pipeline Orchestrator':^60}{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.END}")

    args = parse_args()
    project_path = args.project.expanduser().resolve()

    print(f"\nProject: {project_path}")
    if args.ticket:
        print(f"Ticket: {args.ticket}")

    # Check prerequisites
    prereq = check_prerequisites()
    if not prereq["success"]:
        print(f"\n{Colors.RED}Error: {prereq['error']}{Colors.END}")
        return 1

    # Check for old checkpoints and offer cleanup
    should_warn, checkpoints = check_checkpoint_cleanup_needed(project_path)
    if should_warn:
        oldest = min(c.get("timestamp", "")[:10] for c in checkpoints)
        action, days = prompt_checkpoint_cleanup(len(checkpoints), oldest)

        if action == "oldest":
            deleted, failed = cleanup_checkpoints_by_age(checkpoints, days)
            print(f"  Deleted {deleted} checkpoint(s)")
        elif action == "last_n":
            cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            old_cps = [c for c in checkpoints if c.get("timestamp", "")[:10] <= cutoff]
            deleted, failed = cleanup_checkpoints_by_age(old_cps, 0)
            print(f"  Deleted {deleted} checkpoint(s)")
        elif action == "all":
            deleted, failed = cleanup_all_checkpoints(project_path)
            print(f"  Deleted {deleted} checkpoint(s)")

    # Resume flow
    if args.resume:
        return handle_resume_flow(args, project_path)

    # Normal flow
    if args.prompt_text is not None:
        prompt = args.prompt_text
    else:
        prompt = collect_prompt()

    if not prompt.strip():
        print(f"\n{Colors.RED}Error: Research prompt cannot be empty{Colors.END}")
        return 1

    print(f"\n{Colors.CYAN}Starting pipeline...{Colors.END}")

    result = run_pipeline(
        project_path=project_path,
        prompt=prompt,
        ticket_id=args.ticket,
        auto_approve=args.auto_approve
    )

    display_result(result)
    return get_exit_code(result)


def handle_resume_flow(args, project_path: Path) -> int:
    """Handle the --resume flow.

    Args:
        args: Parsed arguments
        project_path: Resolved project path

    Returns:
        Exit code (0 for success)
    """
    from datetime import datetime, timedelta
    from planning_pipeline import (
        detect_resumable_checkpoint,
        discover_thoughts_files,
        prompt_file_selection,
        prompt_search_days,
        prompt_custom_path,
        step_planning,
        step_phase_decomposition,
        step_beads_integration,
        delete_checkpoint,
    )

    # Try to auto-detect from checkpoint
    checkpoint = None
    if not args.research_path and not args.plan_path:
        checkpoint = detect_resumable_checkpoint(project_path)

    if checkpoint:
        print(f"\n{Colors.CYAN}Found checkpoint from {checkpoint.get('timestamp', 'unknown')[:19]}{Colors.END}")
        print(f"  Phase: {checkpoint.get('phase', 'unknown')}")
        artifacts = checkpoint.get("state_snapshot", {}).get("artifacts", [])
        if artifacts:
            print(f"  Artifacts: {', '.join(artifacts)}")

        use_checkpoint = input(f"\nUse this checkpoint? [Y/n]: ").strip().lower()
        if use_checkpoint != 'n':
            # Extract paths from checkpoint
            for artifact in artifacts:
                artifact_path = Path(artifact).resolve()
                if "research" in artifact.lower() and not args.research_path:
                    args.research_path = str(artifact_path)
                elif "plan" in artifact.lower() and not args.plan_path:
                    args.plan_path = str(artifact_path)

            # Determine resume step from checkpoint phase
            if not args.resume_step:
                phase = checkpoint.get("phase", "").lower()
                if "planning" in phase:
                    args.resume_step = "planning"
                elif "decomposition" in phase:
                    args.resume_step = "decomposition"
                elif "beads" in phase:
                    args.resume_step = "beads"

    # Determine what step we're resuming from
    resume_step = args.resume_step

    # If no step specified, determine from available paths
    if not resume_step:
        if args.plan_path:
            resume_step = "decomposition"
        elif args.research_path:
            resume_step = "planning"
        else:
            # Need to select a research file
            resume_step = "planning"

    # Get research path if needed for planning step
    if resume_step == "planning" and not args.research_path:
        args.research_path = interactive_file_selection(project_path, "research")
        if not args.research_path:
            return 1

    # Get plan path if needed for decomposition/beads steps
    if resume_step in ("decomposition", "beads") and not args.plan_path:
        args.plan_path = interactive_file_selection(project_path, "plans")
        if not args.plan_path:
            return 1

    print(f"\n{Colors.CYAN}Resuming from {resume_step} step...{Colors.END}")

    # Execute remaining steps
    result = execute_from_step(
        project_path=project_path,
        resume_step=resume_step,
        research_path=args.research_path,
        plan_path=args.plan_path,
        ticket_id=args.ticket,
        auto_approve=args.auto_approve
    )

    # Delete checkpoint on success
    if result.get("success") and checkpoint:
        delete_checkpoint(checkpoint.get("file_path", ""))
        print(f"\n{Colors.GREEN}Checkpoint cleaned up{Colors.END}")

    display_result(result)
    return get_exit_code(result)


def interactive_file_selection(project_path: Path, file_type: str) -> str | None:
    """Interactive loop to select a file.

    Args:
        project_path: Root project path
        file_type: "research" or "plans"

    Returns:
        Absolute path string or None if cancelled
    """
    from planning_pipeline import (
        discover_thoughts_files,
        prompt_file_selection,
        prompt_search_days,
        prompt_custom_path,
    )

    days_back = 0

    while True:
        files = discover_thoughts_files(project_path, file_type, days_back)
        action, path = prompt_file_selection(files, file_type)

        if action == "selected":
            return str(path.resolve())
        elif action == "search":
            days_back = prompt_search_days()
        elif action == "other":
            custom_path = prompt_custom_path(file_type)
            if custom_path:
                return str(custom_path)
        elif action == "exit":
            return None


def execute_from_step(
    project_path: Path,
    resume_step: str,
    research_path: str = None,
    plan_path: str = None,
    ticket_id: str = None,
    auto_approve: bool = False
) -> dict:
    """Execute pipeline from a specific step.

    Args:
        project_path: Root project path
        resume_step: Step to start from
        research_path: Path to research document
        plan_path: Path to plan document
        ticket_id: Optional ticket ID
        auto_approve: Skip interactive checkpoints

    Returns:
        Pipeline result dictionary
    """
    from datetime import datetime
    from planning_pipeline import (
        step_planning,
        step_phase_decomposition,
        step_beads_integration,
        write_checkpoint,
    )

    results = {
        "started": datetime.now().isoformat(),
        "resumed_from": resume_step,
        "steps": {}
    }

    try:
        if resume_step == "planning":
            # Step 2: Planning
            print(f"\n{'='*60}")
            print("STEP 2/5: PLANNING PHASE")
            print("="*60)

            planning = step_planning(project_path, research_path, "")
            results["steps"]["planning"] = planning

            if not planning["success"]:
                write_checkpoint(project_path, "planning-failed", [research_path])
                results["success"] = False
                results["failed_at"] = "planning"
                return results

            plan_path = planning.get("plan_path")
            if not plan_path:
                results["success"] = False
                results["error"] = "No plan_path extracted"
                return results

        if resume_step in ("planning", "decomposition"):
            # Step 3: Decomposition
            print(f"\n{'='*60}")
            print("STEP 3/5: PHASE DECOMPOSITION")
            print("="*60)

            decomposition = step_phase_decomposition(project_path, plan_path)
            results["steps"]["decomposition"] = decomposition

            if not decomposition["success"]:
                write_checkpoint(project_path, "decomposition-failed", [research_path, plan_path])
                results["success"] = False
                results["failed_at"] = "decomposition"
                return results

            phase_files = decomposition.get("phase_files", [])
            print(f"\nCreated {len(phase_files)} phase files")

        if resume_step in ("planning", "decomposition", "beads"):
            # Step 4: Beads
            print(f"\n{'='*60}")
            print("STEP 4/5: BEADS INTEGRATION")
            print("="*60)

            # Get phase_files from decomposition or discover them
            if "decomposition" not in results["steps"]:
                # Need to discover phase files from plan directory
                plan_dir = Path(plan_path).parent
                phase_files = sorted(plan_dir.glob("*-phase-*.md"))
                phase_files = [str(f) for f in phase_files]

            epic_title = f"Plan: {ticket_id}" if ticket_id else f"Plan: {datetime.now().strftime('%Y-%m-%d')}"
            beads = step_beads_integration(project_path, phase_files, epic_title)
            results["steps"]["beads"] = beads

            if beads["success"]:
                print(f"\nCreated epic: {beads.get('epic_id')}")

        results["success"] = True
        results["completed"] = datetime.now().isoformat()
        return results

    except Exception as e:
        results["success"] = False
        results["error"] = str(e)
        return results
```

### Success Criteria

#### Automated Verification:
- [ ] `python planning_orchestrator.py --help` shows new arguments
- [ ] `python planning_orchestrator.py --resume --help` shows resume options
- [ ] Existing tests pass: `python -m pytest planning_pipeline/tests/test_orchestrator.py -v`

#### Manual Verification:
- [ ] `--resume` auto-detects from existing checkpoint
- [ ] `--resume` without checkpoint triggers file selection
- [ ] `--resume --research-path <path>` skips file selection
- [ ] Resume from planning runs planning -> decomposition -> beads
- [ ] Resume from decomposition runs decomposition -> beads
- [ ] Checkpoint is deleted after successful resume

---

╔═══════════════════════════════════════════════════════════════╗
║                         PHASE 4                               ║
║              Checkpoint Writing & Cleanup                     ║
╚═══════════════════════════════════════════════════════════════╝

## Phase 4: Checkpoint Writing & Cleanup

### Overview
Integrate checkpoint writing into the main pipeline on failure, and deprecate standalone `resume_pipeline.py`.

### Changes Required

#### 1. Update `planning_pipeline/pipeline.py` to write checkpoints

**File**: `planning_pipeline/pipeline.py`
**Changes**: Add checkpoint writing on failure

In the `run()` method, after each step failure, add checkpoint writing:

```python
# After research failure (around line 68)
if not research["success"]:
    from .checkpoint_manager import write_checkpoint
    write_checkpoint(
        self.project_path,
        "research-failed",
        [],
        [research.get("error", "Unknown error")]
    )
    results["success"] = False
    results["failed_at"] = "research"
    return results

# After planning failure (around line 138)
if not planning["success"]:
    from .checkpoint_manager import write_checkpoint
    write_checkpoint(
        self.project_path,
        "planning-failed",
        [str(Path(research["research_path"]).resolve())],
        [planning.get("error", "Unknown error")]
    )
    results["success"] = False
    results["failed_at"] = "planning"
    return results

# After decomposition failure (around line 172)
if not decomposition["success"]:
    from .checkpoint_manager import write_checkpoint
    write_checkpoint(
        self.project_path,
        "decomposition-failed",
        [
            str(Path(research["research_path"]).resolve()),
            str(Path(planning["plan_path"]).resolve())
        ],
        [decomposition.get("error", "Unknown error")]
    )
    results["success"] = False
    results["failed_at"] = "decomposition"
    return results
```

#### 2. Delete checkpoint on success

**File**: `planning_pipeline/pipeline.py`
**Changes**: At end of successful run, clean up any old checkpoint

```python
# Before final return (around line 210)
# Clean up any checkpoint for this run
from .checkpoint_manager import detect_resumable_checkpoint, delete_checkpoint
checkpoint = detect_resumable_checkpoint(self.project_path)
if checkpoint:
    delete_checkpoint(checkpoint.get("file_path", ""))

results["success"] = True
results["completed"] = datetime.now().isoformat()
```

#### 3. Deprecate `resume_pipeline.py`

**File**: `resume_pipeline.py`
**Changes**: Add deprecation warning at top of main block

```python
if __name__ == "__main__":
    import warnings
    warnings.warn(
        "resume_pipeline.py is deprecated. Use 'python planning_orchestrator.py --resume' instead.",
        DeprecationWarning
    )
    # ... rest of existing code
```

### Success Criteria

#### Automated Verification:
- [ ] Pipeline writes checkpoint on failure: `ls .workflow-checkpoints/`
- [ ] Checkpoint contains absolute paths
- [ ] Checkpoint is deleted after successful completion
- [ ] Deprecation warning appears when running `resume_pipeline.py`

#### Manual Verification:
- [ ] Interrupt pipeline during planning -> checkpoint created
- [ ] Resume with `--resume` -> uses checkpoint
- [ ] Complete pipeline run -> no checkpoint files remain
- [ ] Old checkpoints > 30 days trigger cleanup prompt

---

## Testing Strategy

### Unit Tests

**File**: `planning_pipeline/tests/test_checkpoint_manager.py` (NEW)

```python
"""Tests for checkpoint management functions."""

import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta

from planning_pipeline.checkpoint_manager import (
    detect_resumable_checkpoint,
    get_checkpoint_age_days,
    check_checkpoint_cleanup_needed,
    write_checkpoint,
    delete_checkpoint,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with checkpoints dir."""
    checkpoints_dir = tmp_path / ".workflow-checkpoints"
    checkpoints_dir.mkdir()
    return tmp_path


def test_detect_resumable_checkpoint_empty(temp_project):
    """No checkpoints returns None."""
    # Remove the empty dir
    (temp_project / ".workflow-checkpoints").rmdir()
    assert detect_resumable_checkpoint(temp_project) is None


def test_detect_resumable_checkpoint_finds_latest(temp_project):
    """Finds most recent checkpoint."""
    checkpoints_dir = temp_project / ".workflow-checkpoints"

    # Create older checkpoint
    old = {
        "id": "old-id",
        "phase": "research-failed",
        "timestamp": "2025-12-30T10:00:00Z",
        "state_snapshot": {"artifacts": ["/old/path.md"]}
    }
    (checkpoints_dir / "old.json").write_text(json.dumps(old))

    # Create newer checkpoint
    new = {
        "id": "new-id",
        "phase": "planning-failed",
        "timestamp": "2025-12-31T10:00:00Z",
        "state_snapshot": {"artifacts": ["/new/path.md"]}
    }
    (checkpoints_dir / "new.json").write_text(json.dumps(new))

    result = detect_resumable_checkpoint(temp_project)
    assert result["id"] == "new-id"


def test_write_checkpoint_creates_file(temp_project):
    """write_checkpoint creates valid JSON file."""
    path = write_checkpoint(
        temp_project,
        "planning-failed",
        ["/abs/path/research.md"]
    )

    assert Path(path).exists()
    data = json.loads(Path(path).read_text())
    assert data["phase"] == "planning-failed"
    assert "/abs/path/research.md" in data["state_snapshot"]["artifacts"]


def test_get_checkpoint_age_days():
    """Age calculation works correctly."""
    now = datetime.now()
    yesterday = (now - timedelta(days=1)).isoformat() + "Z"

    checkpoint = {"timestamp": yesterday}
    age = get_checkpoint_age_days(checkpoint)
    assert age == 1
```

### Integration Tests

**File**: `planning_pipeline/tests/test_resume_integration.py` (NEW)

Test the full resume flow end-to-end with mocked Claude calls.

### Manual Testing Steps

1. Run pipeline and interrupt during planning (Ctrl+C)
2. Verify checkpoint file created in `.workflow-checkpoints/`
3. Run `python planning_orchestrator.py --resume`
4. Verify checkpoint is detected and displayed
5. Complete the resume
6. Verify checkpoint is deleted

---

## Performance Considerations

- Checkpoint file operations are minimal (single JSON read/write)
- File discovery uses glob which is efficient for small directories
- No performance impact on normal pipeline flow

---

## Migration Notes

- Existing `.workflow-checkpoints/` files with relative paths will still work
- New checkpoints will use absolute paths
- `resume_pipeline.py` deprecated but still functional with warning

---

## References

- Research document: `thoughts/shared/research/2026-01-01-resume-pipeline-integration.md`
- Original pipeline design: `thoughts/shared/research/2025-12-31-python-deterministic-pipeline-control.md`
- Current pipeline: `planning_pipeline/pipeline.py:1-213`
- Current orchestrator: `planning_orchestrator.py:1-242`
