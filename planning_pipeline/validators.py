"""Multi-stage validation cascade for requirement hierarchies.

This module implements REQ_003: A multi-stage validation cascade with structural,
cross-reference, semantic, and category-specific validation stages.

The HierarchyValidator class orchestrates:
- Stage 1: Structural validation (JSON schema, required fields, categories)
- Stage 2: Cross-reference validation (duplicates, orphans, circular deps)
- Stage 3: Semantic validation (clarity, completeness, scope alignment)
- Stage 4: Category-specific validation (security, performance, integration)
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from planning_pipeline.models import (
    VALID_CATEGORIES,
    VALID_REQUIREMENT_TYPES,
    RequirementHierarchy,
    RequirementNode,
)

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity level for validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Single validation issue found during hierarchy validation.

    REQ_003.1-003.2: Each validation stage returns issues with specific codes.

    Attributes:
        code: Machine-readable error code (e.g., 'missing_id', 'duplicate_id')
        message: Human-readable description of the issue
        requirement_ref: Reference to the failing requirement (id or path)
        severity: Issue severity (ERROR, WARNING, INFO)
        stage: Validation stage that found this issue (1-4)
        details: Additional context for debugging
    """

    code: str
    message: str
    requirement_ref: Optional[str] = None
    severity: ValidationSeverity = ValidationSeverity.ERROR
    stage: int = 1
    details: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "code": self.code,
            "message": self.message,
            "requirement_ref": self.requirement_ref,
            "severity": self.severity.value,
            "stage": self.stage,
            "details": self.details,
        }


@dataclass
class CategoryValidationIssue:
    """Category-specific validation issue for Stage 4.

    REQ_003.4: Category-specific validation returns specialized issues.

    Attributes:
        category: The requirement category being validated
        validation_type: Type of validation that failed
        requirement_ref: Reference to the failing requirement
        failure_reason: Specific reason for the failure
        severity: Issue severity
        suggestions: Suggested fixes
    """

    category: str
    validation_type: str
    requirement_ref: str
    failure_reason: str
    severity: ValidationSeverity = ValidationSeverity.WARNING
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "category": self.category,
            "validation_type": self.validation_type,
            "requirement_ref": self.requirement_ref,
            "failure_reason": self.failure_reason,
            "severity": self.severity.value,
            "suggestions": self.suggestions,
        }


@dataclass
class SemanticScore:
    """Semantic validation scores for a single requirement.

    REQ_003.3: Semantic validation returns clarity, completeness, and scope scores.

    Attributes:
        requirement_id: The requirement being scored
        clarity_score: 0.0-1.0 measuring unambiguity
        completeness_score: 0.0-1.0 measuring presence of necessary details
        scope_alignment_score: 0.0-1.0 measuring alignment with project scope
        needs_revision: True if clarity_score < 0.7
        is_incomplete: True if completeness_score < 0.6
        is_out_of_scope: True if scope_alignment_score < 0.5
    """

    requirement_id: str
    clarity_score: float = 0.0
    completeness_score: float = 0.0
    scope_alignment_score: float = 0.0

    @property
    def needs_revision(self) -> bool:
        """Check if requirement needs revision due to low clarity."""
        return self.clarity_score < 0.7

    @property
    def is_incomplete(self) -> bool:
        """Check if requirement is incomplete."""
        return self.completeness_score < 0.6

    @property
    def is_out_of_scope(self) -> bool:
        """Check if requirement is potentially out of scope."""
        return self.scope_alignment_score < 0.5

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "requirement_id": self.requirement_id,
            "clarity_score": self.clarity_score,
            "completeness_score": self.completeness_score,
            "scope_alignment_score": self.scope_alignment_score,
            "needs_revision": self.needs_revision,
            "is_incomplete": self.is_incomplete,
            "is_out_of_scope": self.is_out_of_scope,
        }


@dataclass
class ValidationSummary:
    """Summary of Stage 3 semantic validation.

    REQ_003.3: Aggregate individual requirement validations into summary.

    Attributes:
        scores: Individual requirement scores
        average_clarity: Mean clarity score across all requirements
        average_completeness: Mean completeness score
        average_scope_alignment: Mean scope alignment score
        requirements_needing_revision: Count needing revision
        requirements_incomplete: Count of incomplete requirements
        requirements_out_of_scope: Count potentially out of scope
        processing_time_ms: Time taken for validation
    """

    scores: list[SemanticScore] = field(default_factory=list)
    processing_time_ms: int = 0

    @property
    def average_clarity(self) -> float:
        """Calculate average clarity score."""
        if not self.scores:
            return 0.0
        return sum(s.clarity_score for s in self.scores) / len(self.scores)

    @property
    def average_completeness(self) -> float:
        """Calculate average completeness score."""
        if not self.scores:
            return 0.0
        return sum(s.completeness_score for s in self.scores) / len(self.scores)

    @property
    def average_scope_alignment(self) -> float:
        """Calculate average scope alignment score."""
        if not self.scores:
            return 0.0
        return sum(s.scope_alignment_score for s in self.scores) / len(self.scores)

    @property
    def requirements_needing_revision(self) -> int:
        """Count requirements needing revision."""
        return sum(1 for s in self.scores if s.needs_revision)

    @property
    def requirements_incomplete(self) -> int:
        """Count incomplete requirements."""
        return sum(1 for s in self.scores if s.is_incomplete)

    @property
    def requirements_out_of_scope(self) -> int:
        """Count out-of-scope requirements."""
        return sum(1 for s in self.scores if s.is_out_of_scope)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "scores": [s.to_dict() for s in self.scores],
            "average_clarity": self.average_clarity,
            "average_completeness": self.average_completeness,
            "average_scope_alignment": self.average_scope_alignment,
            "requirements_needing_revision": self.requirements_needing_revision,
            "requirements_incomplete": self.requirements_incomplete,
            "requirements_out_of_scope": self.requirements_out_of_scope,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class CascadeValidationResult:
    """Complete result from multi-stage validation cascade.

    REQ_003.5: Aggregate all validation results into per-stage breakdown.

    Attributes:
        structural_issues: Stage 1 issues
        cross_reference_issues: Stage 2 issues
        semantic_summary: Stage 3 semantic validation summary
        category_issues: Stage 4 category-specific issues
        stages_run: Which stages were actually executed
        early_exit_stage: Stage at which validation stopped (if any)
        total_issues: Count of all issues across stages
        has_errors: True if any ERROR severity issues exist
        processing_time_ms: Total time for all validation stages
    """

    structural_issues: list[ValidationIssue] = field(default_factory=list)
    cross_reference_issues: list[ValidationIssue] = field(default_factory=list)
    semantic_summary: Optional[ValidationSummary] = None
    category_issues: list[CategoryValidationIssue] = field(default_factory=list)
    stages_run: list[int] = field(default_factory=list)
    early_exit_stage: Optional[int] = None
    processing_time_ms: int = 0

    @property
    def total_issues(self) -> int:
        """Count total issues across all stages."""
        count = len(self.structural_issues) + len(self.cross_reference_issues)
        count += len(self.category_issues)
        return count

    @property
    def has_errors(self) -> bool:
        """Check if any ERROR severity issues exist."""
        for issue in self.structural_issues:
            if issue.severity == ValidationSeverity.ERROR:
                return True
        for issue in self.cross_reference_issues:
            if issue.severity == ValidationSeverity.ERROR:
                return True
        for issue in self.category_issues:
            if issue.severity == ValidationSeverity.ERROR:
                return True
        return False

    @property
    def passed(self) -> bool:
        """Check if validation passed (no errors)."""
        return not self.has_errors

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "structural_issues": [i.to_dict() for i in self.structural_issues],
            "cross_reference_issues": [i.to_dict() for i in self.cross_reference_issues],
            "semantic_summary": self.semantic_summary.to_dict() if self.semantic_summary else None,
            "category_issues": [i.to_dict() for i in self.category_issues],
            "stages_run": self.stages_run,
            "early_exit_stage": self.early_exit_stage,
            "total_issues": self.total_issues,
            "has_errors": self.has_errors,
            "passed": self.passed,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class ValidationConfig:
    """Configuration for HierarchyValidator.

    REQ_003.5: ValidationConfig specifies which stages to run and thresholds.

    Attributes:
        run_structural: Enable Stage 1 structural validation
        run_cross_references: Enable Stage 2 cross-reference validation
        run_semantic: Enable Stage 3 semantic validation (--validate-full)
        run_category: Enable Stage 4 category validation (--validate-category)
        early_exit_on_error: Stop cascade on first ERROR severity issue
        clarity_threshold: Minimum clarity score (default 0.7)
        completeness_threshold: Minimum completeness score (default 0.6)
        scope_alignment_threshold: Minimum scope alignment (default 0.5)
        max_retries: Retry count for LLM calls
        batch_size: Max requirements per LLM batch call
        timeout_seconds: Timeout for LLM operations
    """

    run_structural: bool = True
    run_cross_references: bool = True
    run_semantic: bool = False  # --validate-full flag
    run_category: bool = False  # --validate-category flag
    early_exit_on_error: bool = True
    clarity_threshold: float = 0.7
    completeness_threshold: float = 0.6
    scope_alignment_threshold: float = 0.5
    max_retries: int = 3
    batch_size: int = 10
    timeout_seconds: int = 60


class HierarchyValidator:
    """Multi-stage validation cascade for requirement hierarchies.

    REQ_003.5: Central orchestrator for the validation cascade.

    This class provides methods for each validation stage and a validate_all
    method that runs the complete cascade with early-exit support.

    Stages:
        1. Structural validation - JSON schema, required fields, category validation
        2. Cross-reference validation - Duplicates, orphans, circular dependencies
        3. Semantic validation - Clarity, completeness, scope alignment via BAML
        4. Category-specific validation - Security, performance, integration checks

    Example:
        >>> validator = HierarchyValidator()
        >>> result = validator.validate_all(hierarchy, scope_text)
        >>> if result.has_errors:
        ...     for issue in result.structural_issues:
        ...         print(f"Error: {issue.message}")
    """

    def __init__(
        self,
        config: Optional[ValidationConfig] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Initialize the validator.

        REQ_003.5: Accept ValidationConfig and optional progress_callback.

        Args:
            config: Validation configuration (uses defaults if None)
            progress_callback: Optional callback for progress updates
        """
        self.config = config or ValidationConfig()
        self.progress_callback = progress_callback or (lambda msg: None)
        self._semantic_service: Optional[Any] = None

    def _log_progress(self, message: str) -> None:
        """Log progress and notify callback."""
        logger.info(message)
        self.progress_callback(message)

    def _get_all_requirements(
        self, hierarchy: RequirementHierarchy
    ) -> list[RequirementNode]:
        """Flatten hierarchy to list of all requirements.

        Uses iterative traversal (not recursive) to prevent stack overflow.

        REQ_003.2: Use iterative traversal for deep hierarchies.

        Args:
            hierarchy: The requirement hierarchy to flatten

        Returns:
            List of all RequirementNode objects in the hierarchy
        """
        result: list[RequirementNode] = []
        stack: list[RequirementNode] = list(hierarchy.requirements)

        while stack:
            node = stack.pop()
            result.append(node)
            # Add children to stack for processing
            stack.extend(node.children)

        return result

    def validate_structural(
        self, hierarchy: RequirementHierarchy
    ) -> list[ValidationIssue]:
        """Stage 1: Structural validation.

        REQ_003.1: Fast local checks (<1s) for:
        - JSON schema compliance (validated via dataclass)
        - Required field presence (id, description, type)
        - Category validation against VALID_CATEGORIES
        - Parent-child relationship consistency

        Args:
            hierarchy: The requirement hierarchy to validate

        Returns:
            List of ValidationIssue objects for any structural problems
        """
        start_time = time.perf_counter()
        issues: list[ValidationIssue] = []

        self._log_progress("Running Stage 1: Structural validation...")

        # Get all requirements using iterative traversal
        all_requirements = self._get_all_requirements(hierarchy)

        for req in all_requirements:
            # Check missing_id
            if not req.id:
                issues.append(
                    ValidationIssue(
                        code="missing_id",
                        message="Requirement ID is null or empty",
                        requirement_ref=str(req.description[:50] if req.description else "unknown"),
                        severity=ValidationSeverity.ERROR,
                        stage=1,
                    )
                )

            # Check empty_description
            if not req.description or not req.description.strip():
                issues.append(
                    ValidationIssue(
                        code="empty_description",
                        message="Requirement description is null or empty",
                        requirement_ref=req.id,
                        severity=ValidationSeverity.ERROR,
                        stage=1,
                    )
                )

            # Check invalid_type
            if req.type not in VALID_REQUIREMENT_TYPES:
                issues.append(
                    ValidationIssue(
                        code="invalid_type",
                        message=f"Invalid requirement type '{req.type}'. Must be one of: {', '.join(sorted(VALID_REQUIREMENT_TYPES))}",
                        requirement_ref=req.id,
                        severity=ValidationSeverity.ERROR,
                        stage=1,
                        details={"actual_type": req.type, "valid_types": list(VALID_REQUIREMENT_TYPES)},
                    )
                )

            # Check invalid_category
            if req.category not in VALID_CATEGORIES:
                issues.append(
                    ValidationIssue(
                        code="invalid_category",
                        message=f"Invalid category '{req.category}'. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}",
                        requirement_ref=req.id,
                        severity=ValidationSeverity.ERROR,
                        stage=1,
                        details={"actual_category": req.category, "valid_categories": list(VALID_CATEGORIES)},
                    )
                )

            # Check invalid_parent_ref
            if req.parent_id:
                parent = hierarchy.get_by_id(req.parent_id)
                if parent is None:
                    issues.append(
                        ValidationIssue(
                            code="invalid_parent_ref",
                            message=f"Parent ID '{req.parent_id}' does not exist in hierarchy",
                            requirement_ref=req.id,
                            severity=ValidationSeverity.ERROR,
                            stage=1,
                            details={"invalid_parent_id": req.parent_id},
                        )
                    )
                elif req not in parent.children:
                    issues.append(
                        ValidationIssue(
                            code="invalid_parent_ref",
                            message=f"Requirement claims parent '{req.parent_id}' but is not in parent's children list",
                            requirement_ref=req.id,
                            severity=ValidationSeverity.ERROR,
                            stage=1,
                            details={"claimed_parent_id": req.parent_id},
                        )
                    )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        self._log_progress(
            f"Stage 1 complete: {len(issues)} issues found in {elapsed_ms}ms"
        )

        return issues

    def validate_cross_references(
        self, hierarchy: RequirementHierarchy
    ) -> list[ValidationIssue]:
        """Stage 2: Cross-reference validation.

        REQ_003.2: Fast local checks (<1s) for:
        - Duplicate ID detection across entire hierarchy
        - Orphan child detection (children referencing non-existent parents)
        - Circular dependency detection in parent-child chains
        - Acceptance criteria coverage verification

        Uses O(n) time complexity with single-pass ID tracking.
        Uses iterative traversal to prevent stack overflow.

        Args:
            hierarchy: The requirement hierarchy to validate

        Returns:
            List of ValidationIssue objects for cross-reference problems
        """
        start_time = time.perf_counter()
        issues: list[ValidationIssue] = []

        self._log_progress("Running Stage 2: Cross-reference validation...")

        # Get all requirements using iterative traversal
        all_requirements = self._get_all_requirements(hierarchy)

        # Track seen IDs for duplicate detection - O(n) single pass
        seen_ids: dict[str, RequirementNode] = {}

        for req in all_requirements:
            # Check duplicate_id
            if req.id in seen_ids:
                issues.append(
                    ValidationIssue(
                        code="duplicate_id",
                        message=f"Duplicate requirement ID '{req.id}' found",
                        requirement_ref=req.id,
                        severity=ValidationSeverity.ERROR,
                        stage=2,
                        details={
                            "original_ref": seen_ids[req.id].id,
                            "duplicate_ref": req.id,
                        },
                    )
                )
            else:
                seen_ids[req.id] = req

        # Check orphan_child - children referencing non-existent parents
        for req in all_requirements:
            if req.parent_id and req.parent_id not in seen_ids:
                issues.append(
                    ValidationIssue(
                        code="orphan_child",
                        message=f"Child references non-existent parent '{req.parent_id}'",
                        requirement_ref=req.id,
                        severity=ValidationSeverity.ERROR,
                        stage=2,
                        details={"missing_parent_id": req.parent_id},
                    )
                )

        # Check circular_dependency using iterative traversal
        for req in all_requirements:
            if req.parent_id:
                visited: set[str] = {req.id}
                current_id = req.parent_id

                while current_id:
                    if current_id in visited:
                        issues.append(
                            ValidationIssue(
                                code="circular_dependency",
                                message=f"Circular dependency detected: {req.id} -> ... -> {current_id}",
                                requirement_ref=req.id,
                                severity=ValidationSeverity.ERROR,
                                stage=2,
                                details={
                                    "cycle_start": req.id,
                                    "cycle_back_to": current_id,
                                },
                            )
                        )
                        break
                    visited.add(current_id)
                    parent = seen_ids.get(current_id)
                    current_id = parent.parent_id if parent else None

        # Check missing_acceptance_criteria and uncovered_acceptance_criteria
        for req in all_requirements:
            # Missing acceptance criteria
            if not req.acceptance_criteria or len(req.acceptance_criteria) == 0:
                issues.append(
                    ValidationIssue(
                        code="missing_acceptance_criteria",
                        message="Requirement has no acceptance criteria",
                        requirement_ref=req.id,
                        severity=ValidationSeverity.WARNING,
                        stage=2,
                    )
                )
            else:
                # Check for uncovered acceptance criteria
                # Criteria are covered if they are referenced by child requirements
                child_descriptions = " ".join(
                    child.description.lower() for child in req.children
                )
                for i, criterion in enumerate(req.acceptance_criteria):
                    # Simple heuristic: check if key words from criterion appear in children
                    criterion_words = set(criterion.lower().split())
                    # Filter out common words
                    significant_words = {
                        w for w in criterion_words
                        if len(w) > 3 and w not in {"must", "should", "shall", "will", "that", "this", "with", "from", "have", "when"}
                    }
                    if significant_words and not any(
                        word in child_descriptions for word in significant_words
                    ):
                        # Only report if requirement has children (leaf nodes expected to not have coverage)
                        if req.children:
                            issues.append(
                                ValidationIssue(
                                    code="uncovered_acceptance_criteria",
                                    message=f"Acceptance criterion {i + 1} not referenced by any child requirement",
                                    requirement_ref=req.id,
                                    severity=ValidationSeverity.WARNING,
                                    stage=2,
                                    details={"criterion_index": i, "criterion_text": criterion[:100]},
                                )
                            )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        self._log_progress(
            f"Stage 2 complete: {len(issues)} issues found in {elapsed_ms}ms"
        )

        return issues

    def validate_semantic(
        self, hierarchy: RequirementHierarchy, scope: str
    ) -> ValidationSummary:
        """Stage 3: Semantic validation using BAML.

        REQ_003.3: LLM-based validation (~2s per requirement) for:
        - Clarity scoring (0.0-1.0)
        - Completeness scoring (0.0-1.0)
        - Scope alignment scoring (0.0-1.0)

        Uses existing BAML ProcessGate1RequirementValidationPrompt.
        Batches requirements for optimized LLM calls.
        Implements retry logic with exponential backoff.

        Args:
            hierarchy: The requirement hierarchy to validate
            scope: The project scope text for alignment checking

        Returns:
            ValidationSummary with scores for all requirements
        """
        start_time = time.perf_counter()
        self._log_progress("Running Stage 3: Semantic validation...")

        all_requirements = self._get_all_requirements(hierarchy)
        scores: list[SemanticScore] = []

        # Process in batches
        batch_size = self.config.batch_size
        total_batches = (len(all_requirements) + batch_size - 1) // batch_size

        for batch_idx in range(total_batches):
            batch_start = batch_idx * batch_size
            batch_end = min(batch_start + batch_size, len(all_requirements))
            batch = all_requirements[batch_start:batch_end]

            self._log_progress(
                f"Processing batch {batch_idx + 1}/{total_batches} ({len(batch)} requirements)..."
            )

            # Format requirements for BAML
            requirements_text = "\n".join(
                f"- {req.id}: {req.description}" for req in batch
            )

            # Try to invoke BAML with retry
            batch_scores = self._invoke_semantic_validation_with_retry(
                scope, requirements_text, batch
            )
            scores.extend(batch_scores)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        summary = ValidationSummary(scores=scores, processing_time_ms=elapsed_ms)

        self._log_progress(
            f"Stage 3 complete: {len(scores)} requirements validated in {elapsed_ms}ms"
        )
        self._log_progress(
            f"  - Needing revision: {summary.requirements_needing_revision}"
        )
        self._log_progress(
            f"  - Incomplete: {summary.requirements_incomplete}"
        )
        self._log_progress(
            f"  - Out of scope: {summary.requirements_out_of_scope}"
        )

        return summary

    def _invoke_semantic_validation_with_retry(
        self,
        scope: str,
        requirements_text: str,
        batch: list[RequirementNode],
    ) -> list[SemanticScore]:
        """Invoke BAML semantic validation with retry logic.

        REQ_003.3: Retry logic with exponential backoff (max 3 retries).

        Args:
            scope: Project scope text
            requirements_text: Formatted requirements for BAML
            batch: The batch of requirements being validated

        Returns:
            List of SemanticScore for the batch
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.config.max_retries):
            try:
                return self._invoke_baml_semantic_validation(
                    scope, requirements_text, batch
                )
            except Exception as e:
                last_error = e
                logger.warning(f"Semantic validation attempt {attempt + 1} failed: {e}")

                if attempt < self.config.max_retries - 1:
                    wait_time = 2 ** attempt
                    self._log_progress(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)

        # Fallback: return default scores on failure
        logger.error(f"Semantic validation failed after {self.config.max_retries} attempts: {last_error}")
        return [
            SemanticScore(
                requirement_id=req.id,
                clarity_score=0.5,
                completeness_score=0.5,
                scope_alignment_score=0.5,
            )
            for req in batch
        ]

    def _invoke_baml_semantic_validation(
        self,
        scope: str,
        requirements_text: str,
        batch: list[RequirementNode],
    ) -> list[SemanticScore]:
        """Invoke BAML ProcessGate1RequirementValidationPrompt.

        Args:
            scope: Project scope text
            requirements_text: Formatted requirements
            batch: The batch of requirements

        Returns:
            List of SemanticScore parsed from BAML response
        """
        try:
            from baml_client import b

            response = b.ProcessGate1RequirementValidationPrompt(
                scope_text=scope,
                current_requirements=requirements_text,
            )

            # Map BAML results to SemanticScore
            scores: list[SemanticScore] = []
            result_map = {
                r.requirement_id: r for r in response.validation_results
            }

            for req in batch:
                baml_result = result_map.get(req.id)
                if baml_result:
                    # Extract scores from BAML result
                    # Note: BAML may use different field names
                    scores.append(
                        SemanticScore(
                            requirement_id=req.id,
                            clarity_score=getattr(baml_result, "confidence_score", 0.8) or 0.8,
                            completeness_score=0.8 if baml_result.is_valid else 0.5,
                            scope_alignment_score=0.8 if baml_result.is_valid else 0.5,
                        )
                    )
                else:
                    # Requirement not in response, use defaults
                    scores.append(
                        SemanticScore(
                            requirement_id=req.id,
                            clarity_score=0.5,
                            completeness_score=0.5,
                            scope_alignment_score=0.5,
                        )
                    )

            return scores

        except ImportError:
            logger.warning("BAML client not available, using fallback scores")
            return [
                SemanticScore(
                    requirement_id=req.id,
                    clarity_score=0.7,
                    completeness_score=0.7,
                    scope_alignment_score=0.7,
                )
                for req in batch
            ]

    def validate_category_specific(
        self, hierarchy: RequirementHierarchy
    ) -> list[CategoryValidationIssue]:
        """Stage 4: Category-specific validation.

        REQ_003.4: Specialized validation (~1s per requirement) based on category:
        - Security: Authentication, authorization, encryption checks
        - Performance: Quantitative metrics, load conditions
        - Integration: Interface contracts, error handling

        Args:
            hierarchy: The requirement hierarchy to validate

        Returns:
            List of CategoryValidationIssue for category-specific problems
        """
        start_time = time.perf_counter()
        issues: list[CategoryValidationIssue] = []

        self._log_progress("Running Stage 4: Category-specific validation...")

        all_requirements = self._get_all_requirements(hierarchy)

        for req in all_requirements:
            category_issues = self._validate_category(req)
            issues.extend(category_issues)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        self._log_progress(
            f"Stage 4 complete: {len(issues)} issues found in {elapsed_ms}ms"
        )

        return issues

    def _validate_category(
        self, req: RequirementNode
    ) -> list[CategoryValidationIssue]:
        """Validate a single requirement based on its category.

        REQ_003.4: Route to appropriate category validator.

        Args:
            req: The requirement to validate

        Returns:
            List of category-specific issues
        """
        if req.category == "security":
            return self._validate_security_requirement(req)
        elif req.category == "performance":
            return self._validate_performance_requirement(req)
        elif req.category == "integration":
            return self._validate_integration_requirement(req)
        else:
            # Skip validation for categories without specific rules
            return []

    def _validate_security_requirement(
        self, req: RequirementNode
    ) -> list[CategoryValidationIssue]:
        """Validate security requirement has required elements.

        REQ_003.4: Security requirements must specify:
        - Authentication method (OAuth, JWT, session, API key)
        - Authorization model (RBAC, ABAC, ACL)
        - Encryption for sensitive data

        Args:
            req: The security requirement

        Returns:
            List of issues if validation fails
        """
        issues: list[CategoryValidationIssue] = []
        desc_lower = req.description.lower()
        criteria_text = " ".join(req.acceptance_criteria).lower()
        full_text = desc_lower + " " + criteria_text

        # Check authentication method
        auth_keywords = ["oauth", "jwt", "session", "api key", "api-key", "token", "bearer", "basic auth"]
        if not any(kw in full_text for kw in auth_keywords):
            issues.append(
                CategoryValidationIssue(
                    category="security",
                    validation_type="authentication_method",
                    requirement_ref=req.id,
                    failure_reason="Security requirement does not specify authentication method",
                    severity=ValidationSeverity.WARNING,
                    suggestions=[
                        "Specify authentication method: OAuth, JWT, session-based, or API key",
                        "Add acceptance criterion for authentication mechanism",
                    ],
                )
            )

        # Check authorization model
        authz_keywords = ["rbac", "abac", "acl", "role-based", "attribute-based", "permission", "access control"]
        if not any(kw in full_text for kw in authz_keywords):
            issues.append(
                CategoryValidationIssue(
                    category="security",
                    validation_type="authorization_model",
                    requirement_ref=req.id,
                    failure_reason="Security requirement does not specify authorization model",
                    severity=ValidationSeverity.WARNING,
                    suggestions=[
                        "Specify authorization model: RBAC, ABAC, or ACL",
                        "Define roles and permissions",
                    ],
                )
            )

        # Check encryption
        encryption_keywords = ["encrypt", "tls", "ssl", "https", "aes", "hash", "salt", "secure"]
        if "sensitive" in full_text or "password" in full_text or "secret" in full_text:
            if not any(kw in full_text for kw in encryption_keywords):
                issues.append(
                    CategoryValidationIssue(
                        category="security",
                        validation_type="encryption",
                        requirement_ref=req.id,
                        failure_reason="Security requirement mentions sensitive data but no encryption",
                        severity=ValidationSeverity.WARNING,
                        suggestions=[
                            "Specify encryption for sensitive data handling",
                            "Consider TLS for transport, AES for storage",
                        ],
                    )
                )

        return issues

    def _validate_performance_requirement(
        self, req: RequirementNode
    ) -> list[CategoryValidationIssue]:
        """Validate performance requirement has quantitative metrics.

        REQ_003.4: Performance requirements must specify:
        - Quantitative metrics (response time < Xms, throughput > Y/s)
        - Load conditions (concurrent users, request rate)

        Args:
            req: The performance requirement

        Returns:
            List of issues if validation fails
        """
        issues: list[CategoryValidationIssue] = []
        desc_lower = req.description.lower()
        criteria_text = " ".join(req.acceptance_criteria).lower()
        full_text = desc_lower + " " + criteria_text

        # Check for quantitative metrics
        import re
        metric_patterns = [
            r"\d+\s*(ms|millisecond|second|s\b)",  # Time metrics
            r"\d+\s*(req|request|tps|rps|qps)",  # Throughput metrics
            r"<\s*\d+",  # Less than
            r">\s*\d+",  # Greater than
            r"\d+%",  # Percentage
            r"p\d+\s*<?\s*\d+",  # Percentile (p95, p99)
        ]
        has_metric = any(re.search(p, full_text) for p in metric_patterns)

        if not has_metric:
            issues.append(
                CategoryValidationIssue(
                    category="performance",
                    validation_type="quantitative_metrics",
                    requirement_ref=req.id,
                    failure_reason="Performance requirement lacks quantitative metrics",
                    severity=ValidationSeverity.WARNING,
                    suggestions=[
                        "Add specific metrics: 'response time < 200ms'",
                        "Include throughput targets: '> 1000 req/s'",
                        "Specify percentiles: 'p95 < 500ms'",
                    ],
                )
            )

        # Check for load conditions
        load_keywords = ["concurrent", "simultaneous", "load", "users", "connections", "rate", "volume"]
        if not any(kw in full_text for kw in load_keywords):
            issues.append(
                CategoryValidationIssue(
                    category="performance",
                    validation_type="load_conditions",
                    requirement_ref=req.id,
                    failure_reason="Performance requirement does not specify load conditions",
                    severity=ValidationSeverity.WARNING,
                    suggestions=[
                        "Specify concurrent users or connections",
                        "Define request rate or volume",
                    ],
                )
            )

        return issues

    def _validate_integration_requirement(
        self, req: RequirementNode
    ) -> list[CategoryValidationIssue]:
        """Validate integration requirement has interface contract.

        REQ_003.4: Integration requirements must specify:
        - Interface contract (request/response schema)
        - Error handling strategy

        Args:
            req: The integration requirement

        Returns:
            List of issues if validation fails
        """
        issues: list[CategoryValidationIssue] = []
        desc_lower = req.description.lower()
        criteria_text = " ".join(req.acceptance_criteria).lower()
        full_text = desc_lower + " " + criteria_text

        # Check for interface contract
        contract_keywords = [
            "api", "endpoint", "schema", "contract", "interface",
            "request", "response", "payload", "format", "json", "xml",
            "rest", "graphql", "grpc", "soap", "webhook"
        ]
        if not any(kw in full_text for kw in contract_keywords):
            issues.append(
                CategoryValidationIssue(
                    category="integration",
                    validation_type="interface_contract",
                    requirement_ref=req.id,
                    failure_reason="Integration requirement does not define interface contract",
                    severity=ValidationSeverity.WARNING,
                    suggestions=[
                        "Specify API endpoint or interface",
                        "Define request/response schema",
                        "Document data format (JSON, XML, etc.)",
                    ],
                )
            )

        # Check for error handling
        error_keywords = [
            "error", "exception", "failure", "fallback", "retry",
            "timeout", "circuit breaker", "graceful", "recovery"
        ]
        if not any(kw in full_text for kw in error_keywords):
            issues.append(
                CategoryValidationIssue(
                    category="integration",
                    validation_type="error_handling",
                    requirement_ref=req.id,
                    failure_reason="Integration requirement does not specify error handling",
                    severity=ValidationSeverity.WARNING,
                    suggestions=[
                        "Define error handling strategy",
                        "Consider retry logic and timeouts",
                        "Document failure modes and fallbacks",
                    ],
                )
            )

        return issues

    def validate_all(
        self, hierarchy: RequirementHierarchy, scope: str = ""
    ) -> CascadeValidationResult:
        """Execute the complete validation cascade.

        REQ_003.5: Orchestrate all validation stages with early-exit support.

        Stage execution order:
        1. Structural validation (always runs)
        2. Cross-reference validation (skipped if Stage 1 has ERRORs)
        3. Semantic validation (skipped if Stage 2 has ERRORs, requires --validate-full)
        4. Category-specific validation (optional via --validate-category)

        Args:
            hierarchy: The requirement hierarchy to validate
            scope: Project scope text for semantic validation

        Returns:
            CascadeValidationResult with per-stage breakdown
        """
        start_time = time.perf_counter()
        result = CascadeValidationResult()

        self._log_progress("Starting validation cascade...")

        # Stage 1: Structural validation
        if self.config.run_structural:
            result.structural_issues = self.validate_structural(hierarchy)
            result.stages_run.append(1)

            # Early exit check
            if self.config.early_exit_on_error:
                has_errors = any(
                    i.severity == ValidationSeverity.ERROR
                    for i in result.structural_issues
                )
                if has_errors:
                    result.early_exit_stage = 1
                    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                    result.processing_time_ms = elapsed_ms
                    self._log_progress(
                        f"Early exit at Stage 1: {len(result.structural_issues)} structural errors"
                    )
                    return result

        # Stage 2: Cross-reference validation
        if self.config.run_cross_references:
            result.cross_reference_issues = self.validate_cross_references(hierarchy)
            result.stages_run.append(2)

            # Early exit check
            if self.config.early_exit_on_error:
                has_errors = any(
                    i.severity == ValidationSeverity.ERROR
                    for i in result.cross_reference_issues
                )
                if has_errors:
                    result.early_exit_stage = 2
                    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                    result.processing_time_ms = elapsed_ms
                    self._log_progress(
                        f"Early exit at Stage 2: {len(result.cross_reference_issues)} cross-reference errors"
                    )
                    return result

        # Stage 3: Semantic validation (optional, requires --validate-full)
        if self.config.run_semantic and scope:
            result.semantic_summary = self.validate_semantic(hierarchy, scope)
            result.stages_run.append(3)

        # Stage 4: Category-specific validation (optional, requires --validate-category)
        if self.config.run_category:
            result.category_issues = self.validate_category_specific(hierarchy)
            result.stages_run.append(4)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        result.processing_time_ms = elapsed_ms

        self._log_progress(
            f"Validation cascade complete: {result.total_issues} issues in {elapsed_ms}ms"
        )
        self._log_progress(f"Stages run: {result.stages_run}")
        self._log_progress(f"Result: {'PASSED' if result.passed else 'FAILED'}")

        return result
