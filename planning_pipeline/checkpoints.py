"""Interactive checkpoint functions for pipeline control."""

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
