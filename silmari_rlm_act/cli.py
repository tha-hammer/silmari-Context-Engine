"""CLI entry point for silmari-codewriter-rlm pipeline.

This module provides the command-line interface for running the
RLM-Act pipeline, including commands for starting, resuming, and
checking status.
"""

import re
import sys
import time
from pathlib import Path
from typing import Optional

import click

from silmari_rlm_act import __version__


def _resolve_plan_path(plan_path: str) -> str:
    """Resolve plan path, handling directories with fallback logic.

    For directories, discovers entry file by:
    1. Look for *-overview.md or *overview.md
    2. Look for numbered files (00-*.md, 01-*.md, etc.)
    3. Fall back to alphabetical with 20 second warning

    Args:
        plan_path: Path to file or directory

    Returns:
        Resolved path to entry file

    Raises:
        click.UsageError: If directory contains no .md or .json files
    """
    path = Path(plan_path).resolve()

    # If it's a file, return as-is
    if path.is_file():
        return str(path)

    # It's a directory - discover entry file
    if not path.is_dir():
        raise click.UsageError(f"Path does not exist: {plan_path}")

    # Get all markdown files
    md_files = sorted(path.glob("*.md"))

    # Also check for JSON hierarchy
    json_files = list(path.glob("*.json"))
    hierarchy_json = [f for f in json_files if "hierarchy" in f.name.lower()]

    if not md_files and not json_files:
        raise click.UsageError(
            f"Directory contains no plan files (.md or .json): {plan_path}"
        )

    # Strategy 1: Look for overview files
    overview_patterns = ["*-overview.md", "*overview.md", "overview.md"]
    for pattern in overview_patterns:
        matches = list(path.glob(pattern))
        if matches:
            # Sort to get consistent result, prefer 00-overview over random-overview
            matches.sort()
            click.echo(f"Found overview file: {matches[0].name}")
            return str(matches[0])

    # Strategy 2: Look for numbered files (00-*.md, 01-*.md, etc.)
    numbered_pattern = re.compile(r"^(\d{2})-.*\.md$")
    numbered_files = [f for f in md_files if numbered_pattern.match(f.name)]
    if numbered_files:
        # Already sorted, first one is lowest number (usually 00 or 01)
        click.echo(f"Found numbered plan files, starting with: {numbered_files[0].name}")
        return str(numbered_files[0])

    # Strategy 3: Check for requirements_hierarchy.json
    if hierarchy_json:
        click.echo(f"Found hierarchy file: {hierarchy_json[0].name}")
        return str(hierarchy_json[0])

    # Strategy 4: Alphabetical fallback with warning
    if md_files:
        click.echo()
        click.echo("=" * 60)
        click.echo("WARNING: No overview or numbered files found!")
        click.echo(f"Will process {len(md_files)} files alphabetically.")
        click.echo(f"First file: {md_files[0].name}")
        click.echo("=" * 60)
        click.echo()
        click.echo("Proceeding in 20 seconds... (Ctrl+C to cancel)")

        # Countdown with visual feedback
        for remaining in range(20, 0, -1):
            click.echo(f"  {remaining}...", nl=False)
            time.sleep(1)
            if remaining > 1:
                click.echo("\r", nl=False)  # Carriage return to overwrite

        click.echo()  # Final newline
        click.echo("Proceeding with alphabetical order.")
        return str(md_files[0])

    # Should not reach here, but handle edge case
    if json_files:
        return str(json_files[0])

    raise click.UsageError(f"Could not determine entry file in directory: {plan_path}")


from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import AutonomyMode
from silmari_rlm_act.pipeline import RLMActPipeline
from planning_pipeline.beads_controller import BeadsController


@click.group()
@click.version_option(version=__version__, prog_name="silmari-codewriter-rlm")
def main() -> None:
    """silmari-codewriter-rlm: Autonomous TDD Pipeline.

    Research, Learn, Model, Act - an autonomous pipeline for TDD-based
    software development.
    """
    pass


@main.command()
@click.option(
    "--question",
    "-q",
    default=None,
    help="Research question to start the pipeline (required unless --resume)",
)
@click.option(
    "--project",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
    help="Project directory (default: current directory)",
)
@click.option(
    "--plan-name",
    "-n",
    default="feature",
    help="Name for the TDD plan (default: feature)",
)
@click.option(
    "--autonomous",
    "-a",
    is_flag=True,
    default=False,
    help="Run in fully autonomous mode (no pauses)",
)
@click.option(
    "--batch",
    "-b",
    is_flag=True,
    default=False,
    help="Run in batch mode (pause between groups)",
)
@click.option(
    "--resume",
    "-r",
    is_flag=True,
    default=False,
    help="Resume from last checkpoint instead of starting fresh",
)
@click.option(
    "--research-path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default=None,
    help="Path to existing research document (skips research phase)",
)
@click.option(
    "--plan-path",
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
    default=None,
    help="Path to plan document or directory containing plan files. For directories, discovers files by: 1) *-overview.md, 2) numbered files (00-*.md), 3) alphabetical (with 20s warning).",
)
@click.option(
    "--validate-full",
    "-vf",
    is_flag=True,
    default=False,
    help="Enable comprehensive LLM-based semantic validation (slower but more thorough)",
)
def run(
    question: Optional[str],
    project: str,
    plan_name: str,
    autonomous: bool,
    batch: bool,
    resume: bool,
    research_path: Optional[str],
    plan_path: Optional[str],
    validate_full: bool,
) -> None:
    """Run the full RLM-Act pipeline.

    Starts from research phase and runs through implementation.
    Use --resume to continue from a previous checkpoint.
    """
    project_path = Path(project).resolve()

    # Validate: question is required unless resuming, using research_path, or using plan_path
    if not resume and not question and not research_path and not plan_path:
        raise click.UsageError(
            "--question is required unless using --resume, --research-path, or --plan-path"
        )

    # Warn if both question and research_path are provided
    if question and research_path:
        click.echo(
            "Warning: Both --question and --research-path provided. "
            "Research phase will be skipped, --question will be ignored.",
            err=True,
        )

    # Warn if both question and plan_path are provided
    if question and plan_path:
        click.echo(
            "Warning: Both --question and --plan-path provided. "
            "Research and decomposition phases will be skipped, --question will be ignored.",
            err=True,
        )

    # Warn if both research_path and plan_path are provided
    if research_path and plan_path:
        click.echo(
            "Warning: Both --research-path and --plan-path provided. "
            "--plan-path takes precedence, --research-path will be ignored.",
            err=True,
        )

    # REQ_003.3: Warn if --validate-full used without --plan-path
    if validate_full and not plan_path:
        click.echo(
            "Warning: --validate-full has no effect without --plan-path. "
            "Semantic validation only applies to imported plan documents.",
            err=True,
        )

    # Resolve plan_path if it's a directory
    if plan_path:
        plan_path = _resolve_plan_path(plan_path)

    # Log validation mode for audit
    if validate_full and plan_path:
        import logging

        logging.getLogger("silmari_rlm_act.cli").info(
            f"Semantic validation enabled for plan: {plan_path}"
        )

    # Determine autonomy mode
    if autonomous:
        mode = AutonomyMode.FULLY_AUTONOMOUS
    elif batch:
        mode = AutonomyMode.BATCH
    else:
        mode = AutonomyMode.CHECKPOINT

    # Create CWA integration
    cwa = CWAIntegration()

    # Create beads controller
    beads = BeadsController(project_path)

    # Create pipeline
    pipeline = RLMActPipeline(
        project_path=project_path,
        cwa=cwa,
        autonomy_mode=mode,
        beads_controller=beads,
    )

    # Handle resume mode
    if resume:
        if not pipeline.resume_from_checkpoint():
            click.echo("No checkpoint found to resume from.")
            click.echo("Use 'silmari-rlm-act run -q <question>' to start a new pipeline.")
            sys.exit(1)

        status = pipeline.get_status_summary()
        click.echo("Resuming RLM-Act pipeline...")
        click.echo(f"  Project: {project_path}")
        click.echo(f"  Completed phases: {', '.join(status['phases_completed'])}")
        click.echo(f"  Next phase: {status['next_phase']}")
        click.echo(f"  Mode: {mode.value}")
        click.echo()

        result = pipeline.run(
            research_question="",  # Not needed when resuming
            plan_name=plan_name,
        )
    else:
        click.echo("Starting RLM-Act pipeline...")
        click.echo(f"  Project: {project_path}")
        if plan_path:
            if plan_path.endswith((".md", ".markdown")):
                click.echo(f"  Plan document (Markdown): {plan_path}")
                click.echo("  (Skipping research/decomposition/planning, running BEADS_SYNC → IMPLEMENTATION)")
            else:
                click.echo(f"  Requirement hierarchy JSON: {plan_path}")
                click.echo("  (Research and decomposition phases will be skipped)")
        elif research_path:
            click.echo(f"  Research document: {research_path}")
            click.echo("  (Research phase will be skipped)")
        else:
            click.echo(f"  Question: {question}")
        click.echo(f"  Mode: {mode.value}")
        click.echo()

        result = pipeline.run(
            research_question=question or "",
            plan_name=plan_name,
            research_path=research_path,
            hierarchy_path=plan_path,
            validate_full=validate_full,
        )

    # Report result
    if result.is_complete:
        click.echo()
        click.echo("=" * 60)
        click.echo("PIPELINE COMPLETE")
        click.echo("=" * 60)
        click.echo()
        click.echo("Artifacts produced:")
        for artifact in result.artifacts:
            click.echo(f"  - {artifact}")
    else:
        click.echo()
        click.echo("=" * 60)
        click.echo("PIPELINE FAILED")
        click.echo("=" * 60)
        click.echo()
        click.echo("Errors:")
        for error in result.errors:
            click.echo(f"  - {error}")
        sys.exit(1)


@main.command()
@click.option(
    "--project",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
    help="Project directory (default: current directory)",
)
@click.option(
    "--autonomous",
    "-a",
    is_flag=True,
    default=False,
    help="Continue in fully autonomous mode",
)
@click.option(
    "--batch",
    "-b",
    is_flag=True,
    default=False,
    help="Continue in batch mode (pause between groups)",
)
def resume(project: str, autonomous: bool, batch: bool) -> None:
    """Resume pipeline from last checkpoint.

    Loads the most recent checkpoint and continues execution.
    """
    project_path = Path(project).resolve()

    # Determine autonomy mode
    if autonomous:
        mode = AutonomyMode.FULLY_AUTONOMOUS
    elif batch:
        mode = AutonomyMode.BATCH
    else:
        mode = AutonomyMode.CHECKPOINT

    click.echo("Resuming RLM-Act pipeline...")
    click.echo(f"  Project: {project_path}")
    click.echo()

    # Create CWA integration
    cwa = CWAIntegration()

    # Create beads controller
    beads = BeadsController(project_path)

    # Create pipeline
    pipeline = RLMActPipeline(
        project_path=project_path,
        cwa=cwa,
        autonomy_mode=mode,
        beads_controller=beads,
    )

    # Try to resume
    if not pipeline.resume_from_checkpoint():
        click.echo("No checkpoint found to resume from.")
        click.echo("Use 'silmari-rlm-act run' to start a new pipeline.")
        sys.exit(1)

    # Show what we're resuming from
    status = pipeline.get_status_summary()
    click.echo("Resumed from checkpoint")
    click.echo(f"  Completed phases: {', '.join(status['phases_completed'])}")
    click.echo(f"  Next phase: {status['next_phase']}")
    click.echo()

    # Continue pipeline
    result = pipeline.run(
        research_question="",  # Not needed when resuming
    )

    # Report result
    if result.is_complete:
        click.echo()
        click.echo("=" * 60)
        click.echo("PIPELINE COMPLETE")
        click.echo("=" * 60)
    else:
        click.echo()
        click.echo("=" * 60)
        click.echo("PIPELINE FAILED")
        click.echo("=" * 60)
        for error in result.errors:
            click.echo(f"  - {error}")
        sys.exit(1)


@main.command()
@click.option(
    "--project",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
    help="Project directory (default: current directory)",
)
def status(project: str) -> None:
    """Show current pipeline status.

    Displays completed phases, pending work, and next steps.
    """
    project_path = Path(project).resolve()

    # Create CWA integration
    cwa = CWAIntegration()

    # Create beads controller
    beads = BeadsController(project_path)

    # Create pipeline
    pipeline = RLMActPipeline(
        project_path=project_path,
        cwa=cwa,
        beads_controller=beads,
    )

    # Try to load checkpoint
    pipeline.resume_from_checkpoint()

    # Get and display status
    summary = pipeline.get_status_summary()

    click.echo("=" * 60)
    click.echo("PIPELINE STATUS")
    click.echo("=" * 60)
    click.echo()
    click.echo(f"Project: {summary['project_path']}")
    click.echo(f"Mode: {summary['autonomy_mode']}")
    click.echo()

    if summary["phases_completed"]:
        click.echo("Completed phases:")
        for phase in summary["phases_completed"]:
            click.echo(f"  [x] {phase}")
    else:
        click.echo("No phases completed yet.")

    if summary["phases_pending"]:
        click.echo()
        click.echo("Pending phases:")
        for phase in summary["phases_pending"]:
            click.echo(f"  [ ] {phase}")

    click.echo()
    if summary["next_phase"]:
        click.echo(f"Next: {summary['next_phase']}")
    elif summary["all_complete"]:
        click.echo("All phases complete!")
    else:
        click.echo("Run 'silmari-rlm-act run' to start the pipeline.")


@main.command()
@click.option(
    "--project",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
    help="Project directory (default: current directory)",
)
@click.option(
    "--days",
    "-d",
    type=int,
    default=None,
    help="Delete checkpoints older than N days",
)
@click.option(
    "--all",
    "delete_all",
    is_flag=True,
    default=False,
    help="Delete all checkpoints",
)
def cleanup(project: str, days: Optional[int], delete_all: bool) -> None:
    """Clean up old checkpoints.

    Remove checkpoint files to free up space.
    """
    from silmari_rlm_act.checkpoints.manager import CheckpointManager

    project_path = Path(project).resolve()
    manager = CheckpointManager(project_path)

    if delete_all:
        deleted, failed = manager.cleanup_all()
        click.echo(f"Deleted {deleted} checkpoint(s), {failed} failed.")
    elif days is not None:
        deleted, failed = manager.cleanup_by_age(days)
        click.echo(f"Deleted {deleted} checkpoint(s) older than {days} days, {failed} failed.")
    else:
        # Show what would be cleaned up
        checkpoint = manager.detect_resumable_checkpoint()
        if checkpoint:
            age = manager.get_checkpoint_age_days(checkpoint)
            click.echo(f"Most recent checkpoint: {checkpoint.get('phase', 'unknown')}")
            click.echo(f"Age: {age} days")
            click.echo()
            click.echo("Use --days N or --all to delete checkpoints.")
        else:
            click.echo("No checkpoints found.")


if __name__ == "__main__":
    main()
