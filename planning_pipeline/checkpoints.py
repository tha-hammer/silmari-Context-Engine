"""Interactive checkpoint functions for pipeline control."""

from typing import Any


def interactive_checkpoint_research(research_result: dict[str, Any]) -> dict[str, Any]:
    """Interactive checkpoint after research phase.

    Args:
        research_result: Result from step_research containing:
            - research_path: path to research document
            - open_questions: list of extracted questions

    Returns:
        Dictionary with keys:
        - continue: bool indicating whether to proceed
        - answers: list of answers to open questions
        - research_path: echoed research path
    """
    print(f"\n{'='*60}")
    print("RESEARCH COMPLETE")
    print(f"{'='*60}")
    print(f"\nResearch document: {research_result.get('research_path', 'N/A')}")

    if research_result.get("open_questions"):
        print("\nOpen Questions:")
        for i, q in enumerate(research_result["open_questions"], 1):
            print(f"  {i}. {q}")

        print("\nProvide answers (empty line to finish):")
        answers = []
        while True:
            line = input("> ").strip()
            if not line:
                break
            answers.append(line)

        return {
            "continue": True,
            "answers": answers,
            "research_path": research_result.get("research_path")
        }
    else:
        response = input("\nContinue to planning? (Y/n): ").strip().lower()
        return {
            "continue": response != 'n',
            "answers": [],
            "research_path": research_result.get("research_path")
        }


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
