"""Interactive prompts for pipeline control.

This module provides user interaction prompts for:
- Research phase completion actions
- Checkpoint resume decisions
- Autonomy mode selection
- File selection menus
- Multi-line input collection
- Cleanup operations
- Resume point selection
"""

from pathlib import Path
from typing import Any, Optional

from silmari_rlm_act.models import AutonomyMode


def prompt_research_action() -> str:
    """Prompt user for research checkpoint action.

    Displays a menu for the user to choose what to do after
    the research phase completes.

    Returns:
        One of: 'continue', 'revise', 'restart', 'exit'
    """
    valid_actions = {
        "c": "continue",
        "r": "revise",
        "s": "restart",
        "e": "exit",
        "": "continue",
    }

    while True:
        print("\nWhat would you like to do?")
        print("  [C]ontinue to decomposition (default)")
        print("  [R]evise research with additional context")
        print("  [S]tart over with new prompt")
        print("  [E]xit pipeline")

        response = input("\nChoice [C/r/s/e]: ").strip().lower()

        if response in valid_actions:
            return valid_actions[response]
        print(f"Invalid choice: '{response}'. Please enter C, R, S, or E.")


def prompt_decomposition_action() -> str:
    """Prompt user for decomposition checkpoint action.

    Displays a menu for the user to choose what to do after
    the decomposition phase completes.

    Returns:
        One of: 'continue', 'revise', 'restart', 'exit'
    """
    valid_actions = {
        "c": "continue",
        "r": "revise",
        "s": "restart",
        "e": "exit",
        "": "continue",
    }

    while True:
        print("\nWhat would you like to do?")
        print("  [C]ontinue to TDD planning (default)")
        print("  [R]evise decomposition with additional context")
        print("  [S]tart over from research")
        print("  [E]xit pipeline")

        response = input("\nChoice [C/r/s/e]: ").strip().lower()

        if response in valid_actions:
            return valid_actions[response]
        print(f"Invalid choice: '{response}'. Please enter C, R, S, or E.")


def prompt_tdd_planning_action() -> str:
    """Prompt user for TDD planning checkpoint action.

    Displays a menu for the user to choose what to do after
    the TDD planning phase completes.

    Returns:
        One of: 'continue', 'revise', 'restart', 'exit'
    """
    valid_actions = {
        "c": "continue",
        "r": "revise",
        "s": "restart",
        "e": "exit",
        "": "continue",
    }

    while True:
        print("\nWhat would you like to do?")
        print("  [C]ontinue to multi-doc generation (default)")
        print("  [R]evise TDD plan with feedback")
        print("  [S]tart over from decomposition")
        print("  [E]xit pipeline")

        response = input("\nChoice [C/r/s/e]: ").strip().lower()

        if response in valid_actions:
            return valid_actions[response]
        print(f"Invalid choice: '{response}'. Please enter C, R, S, or E.")


def prompt_use_checkpoint(
    timestamp: str,
    phase: str,
    artifacts: Optional[list[str]] = None,
) -> bool:
    """Prompt user to use existing checkpoint.

    Displays information about a found checkpoint and asks
    whether to resume from it.

    Args:
        timestamp: Checkpoint timestamp string
        phase: Phase name (e.g., "research-complete")
        artifacts: Optional list of artifact file paths

    Returns:
        True if user wants to use checkpoint, False otherwise
    """
    print(f"\nFound checkpoint from {timestamp}")
    print(f"  Phase: {phase}")
    if artifacts:
        print("  Artifacts:")
        for a in artifacts:
            print(f"    - {Path(a).name}")

    response = input("\nUse this checkpoint? [Y/n]: ").strip().lower()
    return response != "n"


def prompt_autonomy_mode(phase_count: int, epic_id: str) -> AutonomyMode:
    """Prompt user for implementation execution mode.

    Displays implementation readiness and asks for the desired
    execution mode.

    Args:
        phase_count: Number of implementation phases
        epic_id: Beads epic ID for tracking

    Returns:
        Selected AutonomyMode enum value
    """
    print(f"\n{'='*60}")
    print("IMPLEMENTATION READY")
    print(f"{'='*60}")
    print(f"\nPlan phases: {phase_count}")
    print(f"Beads epic: {epic_id}")

    print("\nSelect execution mode:")
    print("  [C]heckpoint - pause at each phase for review (recommended)")
    print("  [F]ully autonomous - run all phases without stopping")
    print("  [B]atch - run groups of phases, pause between groups")

    valid_modes = {
        "c": AutonomyMode.CHECKPOINT,
        "f": AutonomyMode.FULLY_AUTONOMOUS,
        "b": AutonomyMode.BATCH,
        "": AutonomyMode.CHECKPOINT,
    }

    while True:
        response = input("\nMode [C/f/b]: ").strip().lower()
        if response in valid_modes:
            return valid_modes[response]
        print(f"Invalid choice: '{response}'. Please enter C, F, or B.")


def prompt_file_selection(
    files: list[Path],
    file_type: str,
) -> tuple[str, Optional[Path]]:
    """Interactive menu to select a file.

    Displays a numbered list of files and options to search,
    specify a custom path, or exit.

    Args:
        files: List of discovered file paths
        file_type: "research" or "plans" for display purposes

    Returns:
        Tuple of (action, path) where action is one of:
        - "selected": user picked a file, path is the selected file
        - "search": user wants to search more days, path is None
        - "other": user wants to specify custom path, path is None
        - "exit": user wants to exit, path is None
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

    print("\n  [S] Search again (specify days)")
    print("  [O] Other (specify path)")
    print("  [E] Exit")

    while True:
        response = input("\nChoice: ").strip()

        if response.lower() == "s":
            return ("search", None)
        elif response.lower() == "o":
            return ("other", None)
        elif response.lower() == "e":
            return ("exit", None)
        elif response.isdigit():
            idx = int(response) - 1
            if files and 0 <= idx < len(files):
                return ("selected", files[idx])
            max_num = len(files) if files else 0
            if max_num > 0:
                print(f"Invalid number. Enter 1-{max_num}")
            else:
                print("No files available to select.")
        else:
            print("Invalid choice. Enter a number, S, O, or E.")


def collect_multiline_input(prompt: str = "") -> str:
    """Collect multi-line input from user.

    Reads lines until an empty line is entered.

    Args:
        prompt: Optional prompt to display before each line

    Returns:
        All lines joined with newlines
    """
    lines: list[str] = []
    while True:
        line = input(prompt)
        if not line:
            break
        lines.append(line)
    return "\n".join(lines)


def prompt_search_days(default: int = 7) -> int:
    """Prompt for number of days to search back.

    Args:
        default: Default number of days if Enter is pressed

    Returns:
        Number of days to search
    """
    while True:
        response = input(f"\nSearch how many days back? [{default}]: ").strip()
        if not response:
            return default
        if response.isdigit() and int(response) > 0:
            return int(response)
        print("Please enter a positive number.")


def prompt_phase_continue(
    phase_name: str,
    artifacts: list[str],
) -> dict[str, Any]:
    """Prompt user to continue after phase completion.

    Displays phase completion info and asks whether to continue
    or provide feedback for revision.

    Args:
        phase_name: Name of completed phase
        artifacts: List of artifact file paths produced

    Returns:
        Dictionary with:
        - 'continue': bool - whether to continue
        - 'feedback': str - feedback if not continuing
    """
    print(f"\n{'='*60}")
    print(f"PHASE COMPLETE: {phase_name.upper()}")
    print(f"{'='*60}")
    print("\nArtifacts produced:")
    for a in artifacts:
        print(f"  - {Path(a).name}")

    response = input("\nContinue to next phase? [Y/n]: ").strip().lower()

    if response == "n":
        print("\nEnter feedback (empty line to finish):")
        feedback = collect_multiline_input("> ")
        return {"continue": False, "feedback": feedback}

    return {"continue": True, "feedback": ""}


def prompt_custom_path(file_type: str) -> Optional[Path]:
    """Prompt for a custom file path.

    Validates that the path exists before returning.

    Args:
        file_type: "research" or "plan" for display

    Returns:
        Path if valid and exists, None otherwise
    """
    response = input(f"\nEnter path to {file_type} file: ").strip()
    if not response:
        return None

    path = Path(response).expanduser()
    if path.exists():
        return path

    print(f"Path does not exist: {path}")
    return None


def prompt_cleanup_menu(
    count: int,
    oldest: str,
) -> tuple[str, Optional[int]]:
    """Display cleanup options for old checkpoints.

    Args:
        count: Number of checkpoints found
        oldest: Date string of oldest checkpoint

    Returns:
        Tuple of (action, days) where action is one of:
        - "skip": don't delete anything
        - "oldest": delete only the oldest
        - "days": delete checkpoints older than days
        - "all": delete all checkpoints
    """
    print(f"\n{'='*60}")
    print("CHECKPOINT CLEANUP")
    print(f"{'='*60}")
    print(f"\nFound {count} checkpoint(s)")
    print(f"Oldest from: {oldest}")

    print("\nOptions:")
    print("  [S] Skip (keep all)")
    print("  [O] Delete oldest only")
    print("  [D] Delete older than N days")
    print("  [A] Delete all (requires confirmation)")

    while True:
        response = input("\nChoice [S/o/d/a]: ").strip().lower()

        if response == "" or response == "s":
            return ("skip", None)
        elif response == "o":
            return ("oldest", None)
        elif response == "d":
            days = prompt_search_days(default=7)
            return ("days", days)
        elif response == "a":
            confirm = input("Type 'ALL' to confirm deleting all checkpoints: ").strip()
            if confirm == "ALL":
                return ("all", None)
            print("Cancelled. No checkpoints deleted.")
            return ("skip", None)
        else:
            print("Invalid choice. Enter S, O, D, or A.")


def prompt_resume_point(phases: list[str]) -> str:
    """Prompt user to select which phase to resume from.

    Displays a numbered list of available phases.

    Args:
        phases: List of phase names to choose from

    Returns:
        Selected phase name
    """
    print(f"\n{'='*60}")
    print("SELECT RESUME POINT")
    print(f"{'='*60}")
    print("\nAvailable phases:")
    for i, phase in enumerate(phases, 1):
        print(f"  [{i}] {phase}")

    while True:
        response = input("\nChoice [1]: ").strip()

        if not response:
            return phases[0]
        if response.isdigit():
            idx = int(response) - 1
            if 0 <= idx < len(phases):
                return phases[idx]
            print(f"Invalid number. Enter 1-{len(phases)}")
        else:
            print("Please enter a number.")
