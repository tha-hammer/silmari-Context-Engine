#!/usr/bin/env python3
"""
Planning Pipeline Orchestrator
==============================
CLI entry point for running the planning pipeline.

Usage:
    python planning_orchestrator.py                    # Interactive mode
    python planning_orchestrator.py --project ~/app    # Specify project
    python planning_orchestrator.py --ticket AUTH-001  # With ticket ID
    python planning_orchestrator.py --auto-approve     # Skip checkpoints
"""

import argparse
import subprocess
from pathlib import Path
from typing import Any


def parse_args(args: list[str] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Planning Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python planning_orchestrator.py                    # Interactive prompt
  python planning_orchestrator.py --project ~/app    # Specify project path
  python planning_orchestrator.py --ticket AUTH-001  # Track with ticket ID
  python planning_orchestrator.py --auto-approve     # Skip interactive steps
        """
    )

    parser.add_argument(
        "--project", "-p",
        type=Path,
        default=Path.cwd(),
        help="Project path (default: current directory)"
    )
    parser.add_argument(
        "--ticket", "-t",
        type=str,
        default=None,
        help="Ticket ID for tracking"
    )
    parser.add_argument(
        "--auto-approve", "-y",
        action="store_true",
        help="Skip interactive checkpoints"
    )
    parser.add_argument(
        "--prompt-text",
        type=str,
        default=None,
        help="Research prompt (non-interactive mode)"
    )

    return parser.parse_args(args)


def collect_prompt() -> str:
    """Collect multi-line research prompt from user.

    Reads lines until user enters a blank line.

    Returns:
        Joined string of all input lines.
    """
    print("\nEnter your research prompt (blank line to finish):")
    print("-" * 40)

    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)

    return "\n".join(lines)


def check_prerequisites() -> dict[str, Any]:
    """Check that required CLI tools are installed.

    Returns:
        Dictionary with 'success' bool and optional 'error' message.
    """
    # Check claude CLI
    result = subprocess.run(["which", "claude"], capture_output=True)
    if result.returncode != 0:
        return {
            "success": False,
            "error": "claude command not found. Install from: https://docs.anthropic.com/claude-code"
        }

    # Check bd CLI
    result = subprocess.run(["which", "bd"], capture_output=True)
    if result.returncode != 0:
        return {
            "success": False,
            "error": "bd command not found. Install beads CLI."
        }

    return {"success": True}


def run_pipeline(
    project_path: Path,
    prompt: str,
    ticket_id: str = None,
    auto_approve: bool = False
) -> dict:
    """Run the planning pipeline.

    Args:
        project_path: Root path of the project
        prompt: Research prompt
        ticket_id: Optional ticket ID for tracking
        auto_approve: Skip interactive checkpoints if True

    Returns:
        Pipeline result dictionary.
    """
    if not prompt or not prompt.strip():
        return {"success": False, "error": "Research prompt cannot be empty"}

    from planning_pipeline import PlanningPipeline
    pipeline = PlanningPipeline(project_path)

    return pipeline.run(
        research_prompt=prompt,
        ticket_id=ticket_id,
        auto_approve=auto_approve
    )


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def display_result(result: dict) -> None:
    """Display pipeline result to user.

    Args:
        result: Pipeline result dictionary
    """
    print("\n" + "=" * 60)

    if result.get("success"):
        print(f"{Colors.GREEN}{Colors.BOLD}PIPELINE SUCCESS{Colors.END}")
        print("=" * 60)
        print(f"\nPlan directory: {result.get('plan_dir', 'N/A')}")
        print(f"Epic ID: {result.get('epic_id', 'N/A')}")
        print("\nNext steps:")
        print("  1. Review plan files in the plan directory")
        print("  2. Check beads issues with: bd list --status=open")
        print("  3. Begin implementation using phase files as guides")
    else:
        print(f"{Colors.RED}{Colors.BOLD}PIPELINE FAILED{Colors.END}")
        print("=" * 60)

        if result.get("stopped_at"):
            print(f"\nPipeline stopped by user at: {result['stopped_at']}")
        elif result.get("failed_at"):
            step = result["failed_at"]
            error = result.get("steps", {}).get(step, {}).get("error", "Unknown error")
            print(f"\nFailed at step: {step}")
            print(f"Error: {error}")
        else:
            print(f"\nError: {result.get('error', 'Unknown error')}")


def get_exit_code(result: dict) -> int:
    """Get exit code based on pipeline result.

    Args:
        result: Pipeline result dictionary

    Returns:
        0 for success, 1 for failure
    """
    return 0 if result.get("success") else 1


def main() -> int:
    """Main entry point."""
    import sys

    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{'Planning Pipeline Orchestrator':^60}{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.END}")

    # Parse arguments
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

    # Get prompt
    if args.prompt_text is not None:
        prompt = args.prompt_text
    else:
        prompt = collect_prompt()

    if not prompt.strip():
        print(f"\n{Colors.RED}Error: Research prompt cannot be empty{Colors.END}")
        return 1

    print(f"\n{Colors.CYAN}Starting pipeline...{Colors.END}")

    # Run pipeline
    result = run_pipeline(
        project_path=project_path,
        prompt=prompt,
        ticket_id=args.ticket,
        auto_approve=args.auto_approve
    )

    # Display result
    display_result(result)

    return get_exit_code(result)


if __name__ == "__main__":
    import sys
    sys.exit(main())
