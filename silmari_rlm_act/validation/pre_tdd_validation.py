"""Pre-TDD validation integration module.

This module implements REQ_006: Run validation BEFORE TDD planning to catch
invalid requirements early and reduce wasted LLM calls on bad inputs.

Key features:
- REQ_006.1: Structural validation (Stage 1-2) with blocking on errors
- REQ_006.2: Semantic validation (Stage 3) on --validate-full flag
- REQ_006.3: Category validation (Stage 4) on --validate-category flag
- REQ_006.4: Filter invalid requirements before TDD planning
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from planning_pipeline.models import RequirementHierarchy, RequirementNode
from planning_pipeline.validators import (
    CascadeValidationResult,
    CategoryValidationIssue,
    HierarchyValidator,
    ValidationConfig,
    ValidationIssue,
    ValidationSeverity,
    ValidationSummary,
)

logger = logging.getLogger(__name__)


@dataclass
class PreTDDValidationConfig:
    """Configuration for pre-TDD validation.

    REQ_006: Controls which validation stages run and behavior.

    Attributes:
        validate_full: Enable Stage 3 semantic validation (--validate-full/-vf)
        validate_category: Enable Stage 4 category validation (--validate-category/-vc)
        force_all: Bypass requirement filtering and process all (--force-all)
        early_exit_on_error: Stop cascade on first ERROR severity issue
        timeout_seconds: Timeout for LLM operations (semantic validation)
        max_retries: Max retry attempts for LLM calls
    """

    validate_full: bool = False
    validate_category: bool = False
    force_all: bool = False
    early_exit_on_error: bool = True
    timeout_seconds: int = 60
    max_retries: int = 3


@dataclass
class FilteredHierarchy:
    """Result of filtering a hierarchy based on validation.

    REQ_006.4: Contains valid requirements and tracking of skipped ones.

    Attributes:
        hierarchy: Filtered hierarchy with only valid requirements
        skipped_requirement_ids: IDs of requirements that failed validation
        skipped_reasons: Map of requirement ID to skip reason
        original_count: Total requirements before filtering
        valid_count: Requirements remaining after filtering
    """

    hierarchy: RequirementHierarchy
    skipped_requirement_ids: list[str] = field(default_factory=list)
    skipped_reasons: dict[str, str] = field(default_factory=dict)
    original_count: int = 0
    valid_count: int = 0

    @property
    def skipped_count(self) -> int:
        """Count of skipped requirements."""
        return len(self.skipped_requirement_ids)

    @property
    def all_filtered(self) -> bool:
        """True if ALL requirements were filtered out."""
        return self.valid_count == 0 and self.original_count > 0


@dataclass
class PreTDDValidationResult:
    """Complete result from pre-TDD validation.

    REQ_006: Contains validation results and filtered hierarchy.

    Attributes:
        structural_validation: Stage 1-2 validation result
        semantic_validation: Stage 3 validation result (if enabled)
        category_validation: Stage 4 issues (populated after TDD planning)
        filtered_hierarchy: Hierarchy with invalid requirements removed
        should_proceed: True if pipeline should continue to TDD planning
        failure_reason: If should_proceed is False, explains why
        processing_time_ms: Total validation time
    """

    structural_validation: CascadeValidationResult
    semantic_validation: Optional[ValidationSummary] = None
    category_validation: Optional[list[CategoryValidationIssue]] = None
    filtered_hierarchy: Optional[FilteredHierarchy] = None
    should_proceed: bool = True
    failure_reason: Optional[str] = None
    processing_time_ms: int = 0

    def to_metadata(self) -> dict[str, Any]:
        """Convert to metadata dict for PhaseResult.

        REQ_006.1: Include validation results in PhaseResult.metadata.

        Returns:
            Dictionary suitable for PhaseResult.metadata
        """
        metadata: dict[str, Any] = {
            "structural_validation": self.structural_validation.to_dict(),
            "validation_passed": self.should_proceed,
            "processing_time_ms": self.processing_time_ms,
        }

        if self.semantic_validation:
            metadata["semantic_validation"] = self.semantic_validation.to_dict()

        if self.category_validation:
            metadata["category_validation"] = [
                i.to_dict() for i in self.category_validation
            ]

        if self.filtered_hierarchy:
            metadata["skipped_requirements_count"] = self.filtered_hierarchy.skipped_count
            metadata["skipped_requirement_ids"] = self.filtered_hierarchy.skipped_requirement_ids

        if self.failure_reason:
            metadata["failure_reason"] = self.failure_reason

        return metadata


class PreTDDValidator:
    """Validates requirement hierarchies before TDD planning.

    REQ_006: Orchestrates validation BEFORE TDD planning to catch invalid
    requirements early and reduce wasted LLM calls.

    This validator:
    1. Runs structural validation (Stage 1-2) - ALWAYS, blocking on errors
    2. Runs semantic validation (Stage 3) - on --validate-full flag
    3. Filters invalid requirements from the hierarchy
    4. Supports category validation (Stage 4) after TDD planning

    Example:
        >>> config = PreTDDValidationConfig(validate_full=True)
        >>> validator = PreTDDValidator(config)
        >>> result = validator.validate_before_tdd(hierarchy, scope_text)
        >>> if result.should_proceed:
        ...     # Use result.filtered_hierarchy.hierarchy for TDD planning
        ...     tdd_phase.execute(result.filtered_hierarchy.hierarchy)
    """

    def __init__(
        self,
        config: Optional[PreTDDValidationConfig] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Initialize the pre-TDD validator.

        Args:
            config: Validation configuration
            progress_callback: Optional callback for progress updates
        """
        self.config = config or PreTDDValidationConfig()
        self.progress_callback = progress_callback or (lambda msg: None)

        # Initialize HierarchyValidator with appropriate config
        # NOTE: We disable early_exit_on_error to collect all validation issues
        # so we can filter and continue with valid requirements (REQ_006.4.7)
        validator_config = ValidationConfig(
            run_structural=True,
            run_cross_references=True,
            run_semantic=self.config.validate_full,
            run_category=False,  # Category validation happens AFTER TDD planning
            early_exit_on_error=False,  # Collect all issues for filtering
            max_retries=self.config.max_retries,
            timeout_seconds=self.config.timeout_seconds,
        )
        self._validator = HierarchyValidator(
            config=validator_config,
            progress_callback=progress_callback,
        )

    def _log_progress(self, message: str) -> None:
        """Log progress and notify callback."""
        logger.info(message)
        self.progress_callback(message)

    def validate_before_tdd(
        self,
        hierarchy: RequirementHierarchy,
        scope_text: str = "",
    ) -> PreTDDValidationResult:
        """Run validation cascade before TDD planning.

        REQ_006.1: Run structural validation (Stage 1-2) immediately after
        decomposition with blocking behavior on validation failure.

        REQ_006.2: Run semantic validation (Stage 3) before TDD planning
        on --validate-full flag.

        REQ_006.4: Filter out requirements that failed structural validation
        before passing to TDD planning phase.

        Args:
            hierarchy: Requirement hierarchy from decomposition
            scope_text: Project scope text for semantic validation

        Returns:
            PreTDDValidationResult with validation results and filtered hierarchy
        """
        start_time = time.perf_counter()

        self._log_progress("Starting pre-TDD validation cascade...")

        # Run structural and cross-reference validation (Stage 1-2)
        # Semantic validation runs if validate_full is True
        cascade_result = self._validator.validate_all(hierarchy, scope_text)

        # Log validation issues at WARNING level (REQ_006.1.15)
        self._log_validation_issues(cascade_result)

        # Check if structural validation passed
        structural_errors = self._get_structural_errors(cascade_result)

        # Build result
        result = PreTDDValidationResult(
            structural_validation=cascade_result,
        )

        # REQ_006.2: Semantic validation (if enabled via --validate-full)
        if self.config.validate_full:
            result.semantic_validation = cascade_result.semantic_summary
            # REQ_006.2.9: MUST NOT block pipeline on semantic validation failures
            self._log_semantic_warnings(cascade_result.semantic_summary)

        # REQ_006.4: Filter invalid requirements
        # Filter BEFORE deciding whether to block - this allows partial success
        if self.config.force_all:
            # --force-all bypasses filtering
            result.filtered_hierarchy = FilteredHierarchy(
                hierarchy=hierarchy,
                original_count=self._count_all_requirements(hierarchy),
                valid_count=self._count_all_requirements(hierarchy),
            )
        else:
            result.filtered_hierarchy = self._filter_hierarchy(
                hierarchy, cascade_result
            )

        # REQ_006.4.9: Return FAILED only if ALL requirements fail validation
        # REQ_006.4.7: Continue processing valid requirements (partial success)
        if result.filtered_hierarchy.all_filtered:
            result.should_proceed = False
            result.failure_reason = (
                f"All requirements failed structural validation ({len(structural_errors)} error(s)). "
                "No valid requirements to process. Fix validation issues or use --force-all."
            )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        result.processing_time_ms = elapsed_ms

        status = "PASSED" if result.should_proceed else "BLOCKED"
        self._log_progress(
            f"Pre-TDD validation {status}: {result.filtered_hierarchy.valid_count}/"
            f"{result.filtered_hierarchy.original_count} requirements valid"
        )

        return result

    def validate_category_after_tdd(
        self,
        hierarchy: RequirementHierarchy,
    ) -> list[CategoryValidationIssue]:
        """Run category validation (Stage 4) after TDD planning.

        REQ_006.3: Run category validation optionally after TDD planning
        on --validate-category flag.

        Args:
            hierarchy: Requirement hierarchy (after TDD planning)

        Returns:
            List of CategoryValidationIssue for category-specific problems
        """
        if not self.config.validate_category:
            return []

        self._log_progress("Running Stage 4: Category-specific validation...")

        # Use the underlying validator's category validation
        issues = self._validator.validate_category_specific(hierarchy)

        # REQ_006.3.9: Log category validation warnings at WARNING level
        for issue in issues:
            logger.warning(
                f"Category validation [{issue.category}] {issue.requirement_ref}: "
                f"{issue.failure_reason}"
            )

        # REQ_006.3.9: MUST NOT block pipeline on category validation failures
        self._log_progress(
            f"Category validation complete: {len(issues)} issues found"
        )

        return issues

    def _get_structural_errors(
        self, cascade_result: CascadeValidationResult
    ) -> list[ValidationIssue]:
        """Get ERROR severity issues from structural validation stages.

        Args:
            cascade_result: Validation cascade result

        Returns:
            List of ERROR severity issues from Stage 1-2
        """
        errors: list[ValidationIssue] = []

        for issue in cascade_result.structural_issues:
            if issue.severity == ValidationSeverity.ERROR:
                errors.append(issue)

        for issue in cascade_result.cross_reference_issues:
            if issue.severity == ValidationSeverity.ERROR:
                errors.append(issue)

        return errors

    def _log_validation_issues(
        self, cascade_result: CascadeValidationResult
    ) -> None:
        """Log all validation issues at WARNING level.

        REQ_006.1.15: MUST log all validation issues at WARNING level.

        Args:
            cascade_result: Validation cascade result
        """
        for issue in cascade_result.structural_issues:
            logger.warning(
                f"Structural validation [{issue.code}] {issue.requirement_ref}: "
                f"{issue.message}"
            )

        for issue in cascade_result.cross_reference_issues:
            logger.warning(
                f"Cross-reference validation [{issue.code}] {issue.requirement_ref}: "
                f"{issue.message}"
            )

    def _log_semantic_warnings(
        self, summary: Optional[ValidationSummary]
    ) -> None:
        """Log semantic validation warnings.

        REQ_006.2.10: Log validation warnings at WARNING level.

        Args:
            summary: Semantic validation summary
        """
        if not summary:
            return

        for score in summary.scores:
            if score.is_incomplete:
                logger.warning(
                    f"Semantic validation {score.requirement_id}: "
                    f"completeness_score={score.completeness_score:.2f} < 0.6 (incomplete)"
                )
            if score.is_out_of_scope:
                logger.warning(
                    f"Semantic validation {score.requirement_id}: "
                    f"scope_alignment_score={score.scope_alignment_score:.2f} < 0.5 (out of scope)"
                )

    def _count_all_requirements(self, hierarchy: RequirementHierarchy) -> int:
        """Count total requirements in hierarchy.

        Args:
            hierarchy: Requirement hierarchy

        Returns:
            Total count of all requirements
        """
        count = 0
        stack: list[RequirementNode] = list(hierarchy.requirements)

        while stack:
            node = stack.pop()
            count += 1
            stack.extend(node.children)

        return count

    def _filter_hierarchy(
        self,
        hierarchy: RequirementHierarchy,
        cascade_result: CascadeValidationResult,
    ) -> FilteredHierarchy:
        """Filter invalid requirements from hierarchy.

        REQ_006.4: Only pass structurally valid requirements to TDD planning.

        REQ_006.4.11: Preserve parent-child relationships - if parent is
        invalid, children are also skipped.

        Args:
            hierarchy: Original requirement hierarchy
            cascade_result: Validation result with issues

        Returns:
            FilteredHierarchy with invalid requirements removed
        """
        # Collect IDs of requirements with structural errors
        invalid_ids: set[str] = set()
        skip_reasons: dict[str, str] = {}

        # Structural errors (Stage 1)
        for issue in cascade_result.structural_issues:
            if issue.severity == ValidationSeverity.ERROR and issue.requirement_ref:
                invalid_ids.add(issue.requirement_ref)
                skip_reasons[issue.requirement_ref] = f"Structural error: {issue.code}"

        # Cross-reference errors (Stage 2)
        for issue in cascade_result.cross_reference_issues:
            if issue.severity == ValidationSeverity.ERROR and issue.requirement_ref:
                invalid_ids.add(issue.requirement_ref)
                skip_reasons[issue.requirement_ref] = f"Cross-reference error: {issue.code}"

        # Build filtered hierarchy
        original_count = self._count_all_requirements(hierarchy)

        if not invalid_ids:
            # No filtering needed
            return FilteredHierarchy(
                hierarchy=hierarchy,
                skipped_requirement_ids=[],
                skipped_reasons={},
                original_count=original_count,
                valid_count=original_count,
            )

        # REQ_006.4.11: If parent is invalid, children are also skipped
        # Build set of all IDs to skip (including children of invalid parents)
        all_skip_ids = self._propagate_skip_to_children(hierarchy, invalid_ids, skip_reasons)

        # Filter the hierarchy
        filtered_requirements = self._filter_requirements(
            hierarchy.requirements, all_skip_ids
        )

        filtered_hierarchy = RequirementHierarchy(requirements=filtered_requirements)
        valid_count = self._count_all_requirements(filtered_hierarchy)

        # Log which requirements were skipped (REQ_006.4.6)
        for req_id in sorted(all_skip_ids):
            reason = skip_reasons.get(req_id, "Parent was invalid")
            logger.info(f"Skipping requirement {req_id}: {reason}")

        return FilteredHierarchy(
            hierarchy=filtered_hierarchy,
            skipped_requirement_ids=sorted(all_skip_ids),
            skipped_reasons=skip_reasons,
            original_count=original_count,
            valid_count=valid_count,
        )

    def _propagate_skip_to_children(
        self,
        hierarchy: RequirementHierarchy,
        invalid_ids: set[str],
        skip_reasons: dict[str, str],
    ) -> set[str]:
        """Propagate skip status to children of invalid parents.

        REQ_006.4.11: If parent is invalid, children are also skipped.

        Args:
            hierarchy: Requirement hierarchy
            invalid_ids: IDs of directly invalid requirements
            skip_reasons: Map to update with skip reasons

        Returns:
            Complete set of IDs to skip (including children)
        """
        all_skip_ids = set(invalid_ids)

        def mark_children(node: RequirementNode, parent_invalid: bool) -> None:
            """Recursively mark children if parent is invalid."""
            is_invalid = node.id in invalid_ids or parent_invalid

            if is_invalid and node.id not in invalid_ids:
                # Child being skipped because parent was invalid
                all_skip_ids.add(node.id)
                skip_reasons[node.id] = f"Parent {node.parent_id} was invalid"

            for child in node.children:
                mark_children(child, is_invalid)

        for req in hierarchy.requirements:
            mark_children(req, req.id in invalid_ids)

        return all_skip_ids

    def _filter_requirements(
        self,
        requirements: list[RequirementNode],
        skip_ids: set[str],
    ) -> list[RequirementNode]:
        """Filter requirements recursively.

        REQ_006.4.2: Maintain original hierarchy structure but mark invalid
        requirements as 'skipped'.

        Args:
            requirements: List of requirement nodes
            skip_ids: Set of IDs to skip (may contain description if ID was empty)

        Returns:
            Filtered list of requirements
        """
        result: list[RequirementNode] = []

        for req in requirements:
            # Check both ID and description since validator uses description
            # as requirement_ref when ID is empty/null
            if req.id in skip_ids or req.description in skip_ids:
                continue

            # Create copy with filtered children
            filtered_children = self._filter_requirements(req.children, skip_ids)

            # Only include if requirement or its children are valid
            filtered_req = RequirementNode(
                id=req.id,
                description=req.description,
                type=req.type,
                parent_id=req.parent_id,
                children=filtered_children,
                acceptance_criteria=req.acceptance_criteria,
                implementation=req.implementation,
                testable_properties=req.testable_properties,
                function_id=req.function_id,
                related_concepts=req.related_concepts,
                category=req.category,
                contracts=req.contracts,
                edge_cases=req.edge_cases,
                gherkin_scenarios=req.gherkin_scenarios,
            )
            result.append(filtered_req)

        return result


def run_pre_tdd_validation(
    hierarchy: RequirementHierarchy,
    scope_text: str = "",
    validate_full: bool = False,
    validate_category: bool = False,
    force_all: bool = False,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> PreTDDValidationResult:
    """Convenience function to run pre-TDD validation.

    REQ_006: Validates requirement hierarchy before TDD planning.

    Args:
        hierarchy: Requirement hierarchy from decomposition
        scope_text: Project scope text for semantic validation
        validate_full: Enable semantic validation (--validate-full)
        validate_category: Enable category validation (--validate-category)
        force_all: Bypass filtering (--force-all)
        progress_callback: Optional progress callback

    Returns:
        PreTDDValidationResult with validation status and filtered hierarchy
    """
    config = PreTDDValidationConfig(
        validate_full=validate_full,
        validate_category=validate_category,
        force_all=force_all,
    )

    validator = PreTDDValidator(config, progress_callback)
    return validator.validate_before_tdd(hierarchy, scope_text)
