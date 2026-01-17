"""Validation module for silmari-rlm-act pipeline.

This module provides:
- BAML-level semantic validation for requirements
- Pre-TDD validation cascade for requirement hierarchies (REQ_006)
- Integration with ProcessGate1RequirementValidationPrompt
"""

from silmari_rlm_act.validation.service import (
    SemanticValidationService,
    ValidationConfig,
    ValidationError,
)
from silmari_rlm_act.validation.models import (
    SemanticValidationResult,
    ValidationSummary,
)
from silmari_rlm_act.validation.pre_tdd_validation import (
    FilteredHierarchy,
    PreTDDValidationConfig,
    PreTDDValidationResult,
    PreTDDValidator,
    run_pre_tdd_validation,
)

__all__ = [
    # Service-based validation
    "SemanticValidationService",
    "ValidationConfig",
    "ValidationError",
    "SemanticValidationResult",
    "ValidationSummary",
    # Pre-TDD validation (REQ_006)
    "FilteredHierarchy",
    "PreTDDValidationConfig",
    "PreTDDValidationResult",
    "PreTDDValidator",
    "run_pre_tdd_validation",
]
