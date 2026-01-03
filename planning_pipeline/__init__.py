"""Planning Pipeline - Python deterministic control for Claude Code planning."""

__version__ = "0.1.0"

from .pipeline import PlanningPipeline
from .beads_controller import BeadsController
from .claude_runner import run_claude_sync
from .helpers import extract_file_path, extract_open_questions, extract_phase_files, discover_thoughts_files, resolve_file_path
from .steps import step_research, step_planning, step_phase_decomposition, step_beads_integration
from .checkpoints import (
    interactive_checkpoint_research,
    interactive_checkpoint_plan,
    prompt_file_selection,
    prompt_search_days,
    prompt_custom_path,
    prompt_checkpoint_cleanup,
)
from .checkpoint_manager import (
    detect_resumable_checkpoint,
    get_checkpoint_age_days,
    check_checkpoint_cleanup_needed,
    cleanup_checkpoints_by_age,
    cleanup_all_checkpoints,
    write_checkpoint,
    delete_checkpoint,
)

__all__ = [
    "PlanningPipeline",
    "BeadsController",
    "run_claude_sync",
    "extract_file_path",
    "extract_open_questions",
    "extract_phase_files",
    "discover_thoughts_files",
    "resolve_file_path",
    "step_research",
    "step_planning",
    "step_phase_decomposition",
    "step_beads_integration",
    "interactive_checkpoint_research",
    "interactive_checkpoint_plan",
    "prompt_file_selection",
    "prompt_search_days",
    "prompt_custom_path",
    "prompt_checkpoint_cleanup",
    "detect_resumable_checkpoint",
    "get_checkpoint_age_days",
    "check_checkpoint_cleanup_needed",
    "cleanup_checkpoints_by_age",
    "cleanup_all_checkpoints",
    "write_checkpoint",
    "delete_checkpoint",
]
