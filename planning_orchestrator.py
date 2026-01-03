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

    # Resume arguments
    parser.add_argument(
        "--resume", "-r",
        action="store_true",
        help="Resume from a previous step (auto-detects from checkpoints)"
    )
    parser.add_argument(
        "--resume-step", "--resume_step",
        dest="resume_step",
        choices=["planning", "requirement_decomposition", "phase_decomposition"],
        metavar="STEP",
        help="Step to resume from: planning, requirement_decomposition, or phase_decomposition"
    )
    parser.add_argument(
        "--research-path", "--research_path",
        dest="research_path",
        metavar="FILE",
        help="Research .md file: full path, relative path, or just filename (auto-resolved)"
    )
    parser.add_argument(
        "--plan-path", "--plan_path",
        dest="plan_path",
        metavar="FILE",
        help="Plan .md file: full path, relative path, or just filename (auto-resolved)"
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
    """Main entry point with resume support."""
    import sys
    from datetime import datetime, timedelta
    from planning_pipeline import (
        detect_resumable_checkpoint,
        check_checkpoint_cleanup_needed,
        cleanup_checkpoints_by_age,
        cleanup_all_checkpoints,
        prompt_checkpoint_cleanup,
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
    from planning_pipeline import (
        detect_resumable_checkpoint,
        discover_thoughts_files,
        prompt_file_selection,
        prompt_search_days,
        prompt_custom_path,
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
                if "requirement" in phase and "decomposition" in phase:
                    args.resume_step = "requirement_decomposition"
                elif "planning" in phase:
                    args.resume_step = "planning"
                elif "phase" in phase and "decomposition" in phase:
                    args.resume_step = "phase_decomposition"
                elif "decomposition" in phase:
                    # Legacy checkpoint - default to phase_decomposition
                    args.resume_step = "phase_decomposition"

    # Determine what step we're resuming from
    resume_step = args.resume_step

    # If no step specified, determine from available paths
    if not resume_step:
        if args.plan_path:
            resume_step = "phase_decomposition"
        elif args.research_path:
            resume_step = "planning"
        else:
            # Need to select a research file
            resume_step = "planning"

    # Get research path if needed for planning or requirement_decomposition steps
    if resume_step in ("planning", "requirement_decomposition"):
        if args.research_path:
            # Try to resolve the provided path (supports full, relative, or just filename)
            from planning_pipeline import resolve_file_path
            resolved = resolve_file_path(project_path, args.research_path, "research")
            if resolved:
                args.research_path = str(resolved)
                print(f"  Resolved research path: {resolved.name}")
            else:
                print(f"{Colors.YELLOW}Warning: Could not resolve '{args.research_path}'{Colors.END}")
                args.research_path = None

        if not args.research_path:
            args.research_path = interactive_file_selection(project_path, "research")
            if not args.research_path:
                return 1

    # Get plan path if needed for phase_decomposition step
    if resume_step == "phase_decomposition":
        if args.plan_path:
            # Try to resolve the provided path (supports full, relative, or just filename)
            from planning_pipeline import resolve_file_path
            resolved = resolve_file_path(project_path, args.plan_path, "plans")
            if resolved:
                args.plan_path = str(resolved)
                print(f"  Resolved plan path: {resolved.name}")
            else:
                print(f"{Colors.YELLOW}Warning: Could not resolve '{args.plan_path}'{Colors.END}")
                args.plan_path = None

        if not args.plan_path:
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
        resume_step: Step to start from (planning, requirement_decomposition, phase_decomposition)
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
    from planning_pipeline.step_decomposition import step_requirement_decomposition

    results = {
        "started": datetime.now().isoformat(),
        "resumed_from": resume_step,
        "steps": {}
    }

    try:
        # Step: Requirement Decomposition
        if resume_step == "requirement_decomposition":
            print(f"\n{'='*60}")
            print("STEP 2/6: REQUIREMENT DECOMPOSITION")
            print("="*60)

            req_decomp = step_requirement_decomposition(project_path, research_path)
            results["steps"]["requirement_decomposition"] = req_decomp

            if not req_decomp["success"]:
                if not auto_approve:
                    print(f"\nDecomposition failed: {req_decomp.get('error')}")
                    print("\nOptions:")
                    print("  (R)etry - Try decomposition again")
                    print("  (C)ontinue - Skip decomposition and proceed to planning")
                    choice = input("\nChoice [R/c]: ").strip().lower()
                    if choice == 'r' or choice == '':
                        # Recursive retry
                        return execute_from_step(project_path, resume_step, research_path, plan_path, ticket_id, auto_approve)
                print("Skipping decomposition, continuing to planning...")
            else:
                print(f"\nDecomposed into {req_decomp['requirement_count']} requirements")

        # Step: Planning (runs for requirement_decomposition and planning resume points)
        if resume_step in ("requirement_decomposition", "planning"):
            print(f"\n{'='*60}")
            print("STEP 3/6: PLANNING PHASE")
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

        # Step: Phase Decomposition
        if resume_step in ("requirement_decomposition", "planning", "phase_decomposition"):
            print(f"\n{'='*60}")
            print("STEP 4/6: PHASE DECOMPOSITION")
            print("="*60)

            decomposition = step_phase_decomposition(project_path, plan_path)
            results["steps"]["phase_decomposition"] = decomposition

            if not decomposition["success"]:
                artifacts = [research_path] if research_path else []
                if plan_path:
                    artifacts.append(plan_path)
                write_checkpoint(project_path, "phase_decomposition-failed", artifacts)
                results["success"] = False
                results["failed_at"] = "phase_decomposition"
                return results

            phase_files = decomposition.get("phase_files", [])
            print(f"\nCreated {len(phase_files)} phase files")

        # Step: Beads Integration (always runs for all resume points)
        print(f"\n{'='*60}")
        print("STEP 5/6: BEADS INTEGRATION")
        print("="*60)

        # Get phase_files from decomposition or discover them
        if "phase_decomposition" not in results["steps"]:
            # Need to discover phase files from plan directory
            plan_dir = Path(plan_path).parent
            phase_files = sorted(plan_dir.glob("*-phase-*.md"))
            phase_files = [str(f) for f in phase_files]
        else:
            phase_files = results["steps"]["phase_decomposition"].get("phase_files", [])

        epic_title = f"Plan: {ticket_id}" if ticket_id else f"Plan: {datetime.now().strftime('%Y-%m-%d')}"
        beads = step_beads_integration(project_path, phase_files, epic_title)
        results["steps"]["beads"] = beads

        if beads["success"]:
            print(f"\nCreated epic: {beads.get('epic_id')}")
            results["epic_id"] = beads.get("epic_id")

        results["success"] = True
        results["completed"] = datetime.now().isoformat()

        # Set plan_dir for display
        if plan_path:
            results["plan_dir"] = str(Path(plan_path).parent)

        return results

    except Exception as e:
        results["success"] = False
        results["error"] = str(e)
        return results


if __name__ == "__main__":
    import sys
    sys.exit(main())
