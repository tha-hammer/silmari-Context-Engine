"""CLI entry point for silmari-rlm-act pipeline.

This module provides the command-line interface for running the
RLM-Act pipeline, including commands for starting, resuming, and
checking status.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import AutonomyMode
from silmari_rlm_act.pipeline import RLMActPipeline
from planning_pipeline.beads_controller import BeadsController


@click.group()
@click.version_option(version="0.1.0", prog_name="silmari-rlm-act")
def main() -> None:
    """silmari-rlm-act: Autonomous TDD Pipeline.

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
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default=None,
    help="Path to existing TDD plan/hierarchy JSON (skips research and decomposition phases)",
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
            click.echo(f"  Plan/hierarchy document: {plan_path}")
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
