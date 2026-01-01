"""Interactive checkpoint functions for pipeline control."""

from pathlib import Path
from typing import Any


def _collect_multiline_input(prompt: str = "> ") -> str:
    """Collect multi-line input until empty line."""
    lines = []
    while True:
        line = input(prompt).strip()
        if not line:
            break
        lines.append(line)
    return "\n".join(lines)


def _prompt_research_action() -> str:
    """Prompt user for research checkpoint action.

    Returns:
        One of: 'continue', 'revise', 'restart', 'exit'
    """
    valid_actions = {'c': 'continue', 'r': 'revise', 's': 'restart', 'e': 'exit', '': 'continue'}

    while True:
        print("\nWhat would you like to do?")
        print("  [C]ontinue to planning (default)")
        print("  [R]evise research with additional context")
        print("  [S]tart over with new prompt")
        print("  [E]xit pipeline")

        response = input("\nChoice [C/r/s/e]: ").strip().lower()

        if response in valid_actions:
            return valid_actions[response]
        print(f"Invalid choice: '{response}'. Please enter C, R, S, or E.")


def interactive_checkpoint_research(research_result: dict[str, Any]) -> dict[str, Any]:
    """Interactive checkpoint after research phase.

    Args:
        research_result: Result from step_research containing:
            - research_path: path to research document
            - open_questions: list of extracted questions

    Returns:
        Dictionary with keys:
        - action: 'continue' | 'revise' | 'restart' | 'exit'
        - continue: bool (True only if action='continue', for backward compat)
        - answers: list of answers to open questions
        - revision_context: additional context if action='revise'
        - research_path: echoed research path
    """
    print(f"\n{'='*60}")
    print("RESEARCH COMPLETE")
    print(f"{'='*60}")
    print(f"\nResearch document: {research_result.get('research_path', 'N/A')}")

    # If there are open questions, collect answers and auto-revise
    if research_result.get("open_questions"):
        print("\nOpen Questions:")
        for i, q in enumerate(research_result["open_questions"], 1):
            print(f"  {i}. {q}")

        print("\nProvide answers to refine research (empty line to skip):")
        answers = []
        while True:
            line = input("> ").strip()
            if not line:
                break
            answers.append(line)

        if answers:
            # Auto-revise with the answers
            print("\nRevising research with your answers...")
            return {
                "action": "revise",
                "continue": False,
                "answers": answers,
                "revision_context": "\n".join(answers),
                "research_path": research_result.get("research_path")
            }

    # No open questions or no answers provided - show action menu
    action = _prompt_research_action()

    result = {
        "action": action,
        "continue": action == "continue",
        "answers": [],
        "revision_context": "",
        "research_path": research_result.get("research_path")
    }

    if action == "revise":
        print("\nWhat additional context or refinements would you like?")
        print("(Empty line to finish)")
        result["revision_context"] = _collect_multiline_input()

    return result


def interactive_checkpoint_plan(plan_result: dict[str, Any]) -> dict[str, Any]:
    """Interactive checkpoint after planning phase.

    Args:
        plan_result: Result from step_planning containing:
            - plan_path: path to plan document

    Returns:
        Dictionary with keys:
        - continue: bool indicating whether to proceed
        - feedback: user feedback if not continuing
        - plan_path: echoed plan path
    """
    print(f"\n{'='*60}")
    print("PLANNING COMPLETE")
    print(f"{'='*60}")
    print(f"\nPlan document: {plan_result.get('plan_path', 'N/A')}")

    response = input("\nContinue to phase decomposition? (Y/n): ").strip().lower()

    if response == 'n':
        print("\nProvide feedback (empty line to finish):")
        feedback = []
        while True:
            line = input("> ").strip()
            if not line:
                break
            feedback.append(line)

        return {
            "continue": False,
            "feedback": "\n".join(feedback),
            "plan_path": plan_result.get("plan_path")
        }

    return {
        "continue": True,
        "feedback": "",
        "plan_path": plan_result.get("plan_path")
    }


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
