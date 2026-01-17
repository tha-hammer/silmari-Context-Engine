"""silmari-codewriter-rlm: Autonomous TDD Pipeline.

Research, Learn, Model, Act - an autonomous pipeline for TDD-based
software development using the Context Window Array for context management.
"""

__version__ = "0.5.0"

from silmari_rlm_act.models import (
    AutonomyMode,
    PhaseResult,
    PhaseStatus,
    PhaseType,
    PipelineState,
)
from silmari_rlm_act.pipeline import RLMActPipeline

__all__ = [
    "AutonomyMode",
    "PhaseResult",
    "PhaseStatus",
    "PhaseType",
    "PipelineState",
    "RLMActPipeline",
]
