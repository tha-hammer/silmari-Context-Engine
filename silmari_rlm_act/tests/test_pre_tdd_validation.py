"""Tests for pre-TDD validation module.

This module tests REQ_006: Run validation BEFORE TDD planning to catch
invalid requirements early and reduce wasted LLM calls on bad inputs.

Test coverage:
- REQ_006.1: Structural validation (Stage 1-2) with blocking
- REQ_006.2: Semantic validation (Stage 3) on --validate-full flag
- REQ_006.3: Category validation (Stage 4) on --validate-category flag
- REQ_006.4: Filter invalid requirements before TDD planning
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from planning_pipeline.models import RequirementHierarchy, RequirementNode
from planning_pipeline.validators import (
    CascadeValidationResult,
    ValidationConfig,
    ValidationIssue,
    ValidationSeverity,
)
from silmari_rlm_act.validation.pre_tdd_validation import (
    FilteredHierarchy,
    PreTDDValidationConfig,
    PreTDDValidationResult,
    PreTDDValidator,
    run_pre_tdd_validation,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def valid_requirement() -> RequirementNode:
    """Create a valid requirement node."""
    return RequirementNode(
        id="REQ_001",
        description="Implement user authentication system",
        type="parent",
        acceptance_criteria=["Users can log in", "Sessions are managed"],
    )


@pytest.fixture
def valid_hierarchy() -> RequirementHierarchy:
    """Create a valid hierarchy with nested requirements."""
    parent = RequirementNode(
        id="REQ_001",
        description="Implement user authentication system with OAuth support",
        type="parent",
        acceptance_criteria=["Users can log in with OAuth", "Sessions are managed"],
    )
    child1 = RequirementNode(
        id="REQ_001.1",
        description="Implement OAuth login flow for users",
        type="sub_process",
        parent_id="REQ_001",
        acceptance_criteria=["OAuth tokens are validated"],
    )
    child2 = RequirementNode(
        id="REQ_001.2",
        description="Implement session management",
        type="sub_process",
        parent_id="REQ_001",
        acceptance_criteria=["Sessions expire after timeout"],
    )
    parent.children = [child1, child2]

    return RequirementHierarchy(requirements=[parent])


@pytest.fixture
def invalid_hierarchy_missing_id() -> RequirementHierarchy:
    """Create a hierarchy with a requirement missing an ID."""
    req = RequirementNode.__new__(RequirementNode)
    req.id = ""
    req.description = "Test requirement"
    req.type = "parent"
    req.parent_id = None
    req.children = []
    req.acceptance_criteria = []
    req.implementation = None
    req.testable_properties = []
    req.function_id = None
    req.related_concepts = []
    req.category = "functional"
    req.contracts = None
    req.edge_cases = []
    req.gherkin_scenarios = []

    return RequirementHierarchy(requirements=[req])


@pytest.fixture
def hierarchy_with_duplicate_ids() -> RequirementHierarchy:
    """Create a hierarchy with duplicate requirement IDs."""
    req1 = RequirementNode(
        id="REQ_001",
        description="First requirement",
        type="parent",
        acceptance_criteria=["Criterion 1"],
    )
    req2 = RequirementNode(
        id="REQ_001",  # Duplicate ID
        description="Second requirement with duplicate ID",
        type="parent",
        acceptance_criteria=["Criterion 2"],
    )

    return RequirementHierarchy(requirements=[req1, req2])


@pytest.fixture
def mixed_validity_hierarchy() -> RequirementHierarchy:
    """Create a hierarchy with some valid and some invalid requirements."""
    valid_req = RequirementNode(
        id="REQ_001",
        description="Valid requirement",
        type="parent",
        acceptance_criteria=["Criterion"],
    )

    # Invalid requirement (bad type)
    invalid_req = RequirementNode.__new__(RequirementNode)
    invalid_req.id = "REQ_002"
    invalid_req.description = "Invalid requirement"
    invalid_req.type = "invalid_type"  # Invalid type
    invalid_req.parent_id = None
    invalid_req.children = []
    invalid_req.acceptance_criteria = []
    invalid_req.implementation = None
    invalid_req.testable_properties = []
    invalid_req.function_id = None
    invalid_req.related_concepts = []
    invalid_req.category = "functional"
    invalid_req.contracts = None
    invalid_req.edge_cases = []
    invalid_req.gherkin_scenarios = []

    return RequirementHierarchy(requirements=[valid_req, invalid_req])


# =============================================================================
# REQ_006.1: Structural Validation Tests
# =============================================================================


class TestStructuralValidation:
    """Tests for REQ_006.1: Structural validation (Stage 1-2) with blocking."""

    def test_executes_automatically_after_decomposition(
        self, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_006.1.1: MUST execute automatically (before any TDD planning)."""
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(valid_hierarchy)

        # Structural validation should have run
        assert 1 in result.structural_validation.stages_run
        assert 2 in result.structural_validation.stages_run

    def test_validates_non_empty_id(
        self, invalid_hierarchy_missing_id: RequirementHierarchy
    ):
        """REQ_006.1.2: MUST validate all RequirementNode objects have non-empty 'id'."""
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(invalid_hierarchy_missing_id)

        # Should find missing_id error
        assert any(
            i.code == "missing_id"
            for i in result.structural_validation.structural_issues
        )

    def test_validates_non_empty_description(self):
        """REQ_006.1.3: MUST validate all RequirementNode objects have non-empty 'description'."""
        req = RequirementNode.__new__(RequirementNode)
        req.id = "REQ_001"
        req.description = ""  # Empty description
        req.type = "parent"
        req.parent_id = None
        req.children = []
        req.acceptance_criteria = []
        req.implementation = None
        req.testable_properties = []
        req.function_id = None
        req.related_concepts = []
        req.category = "functional"
        req.contracts = None
        req.edge_cases = []
        req.gherkin_scenarios = []

        hierarchy = RequirementHierarchy(requirements=[req])
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(hierarchy)

        assert any(
            i.code == "empty_description"
            for i in result.structural_validation.structural_issues
        )

    def test_validates_type_in_valid_types(self):
        """REQ_006.1.4: MUST validate RequirementNode.type is in VALID_REQUIREMENT_TYPES."""
        req = RequirementNode.__new__(RequirementNode)
        req.id = "REQ_001"
        req.description = "Test"
        req.type = "invalid_type"  # Invalid type
        req.parent_id = None
        req.children = []
        req.acceptance_criteria = []
        req.implementation = None
        req.testable_properties = []
        req.function_id = None
        req.related_concepts = []
        req.category = "functional"
        req.contracts = None
        req.edge_cases = []
        req.gherkin_scenarios = []

        hierarchy = RequirementHierarchy(requirements=[req])
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(hierarchy)

        assert any(
            i.code == "invalid_type"
            for i in result.structural_validation.structural_issues
        )

    def test_validates_category_in_valid_categories(self):
        """REQ_006.1.5: MUST validate RequirementNode.category is in VALID_CATEGORIES."""
        req = RequirementNode.__new__(RequirementNode)
        req.id = "REQ_001"
        req.description = "Test"
        req.type = "parent"
        req.parent_id = None
        req.children = []
        req.acceptance_criteria = []
        req.implementation = None
        req.testable_properties = []
        req.function_id = None
        req.related_concepts = []
        req.category = "invalid_category"  # Invalid category
        req.contracts = None
        req.edge_cases = []
        req.gherkin_scenarios = []

        hierarchy = RequirementHierarchy(requirements=[req])
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(hierarchy)

        assert any(
            i.code == "invalid_category"
            for i in result.structural_validation.structural_issues
        )

    def test_detects_duplicate_ids(
        self, hierarchy_with_duplicate_ids: RequirementHierarchy
    ):
        """REQ_006.1.6: MUST detect and report duplicate requirement IDs."""
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(hierarchy_with_duplicate_ids)

        assert any(
            i.code == "duplicate_id"
            for i in result.structural_validation.cross_reference_issues
        )

    def test_validates_parent_child_relationships(self):
        """REQ_006.1.7: MUST validate parent-child relationships."""
        child = RequirementNode(
            id="REQ_001.1",
            description="Orphan child",
            type="sub_process",
            parent_id="REQ_NONEXISTENT",  # Invalid parent
            acceptance_criteria=["Criterion"],
        )

        hierarchy = RequirementHierarchy(requirements=[child])
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(hierarchy)

        assert any(
            i.code in ["invalid_parent_ref", "orphan_child"]
            for i in result.structural_validation.structural_issues
            + result.structural_validation.cross_reference_issues
        )

    def test_detects_circular_dependencies(self):
        """REQ_006.1.9: MUST detect circular dependency chains."""
        req_a = RequirementNode(
            id="REQ_A",
            description="Requirement A",
            type="parent",
            parent_id="REQ_C",
            acceptance_criteria=["Criterion"],
        )
        req_b = RequirementNode(
            id="REQ_B",
            description="Requirement B",
            type="parent",
            parent_id="REQ_A",
            acceptance_criteria=["Criterion"],
        )
        req_c = RequirementNode(
            id="REQ_C",
            description="Requirement C",
            type="parent",
            parent_id="REQ_B",
            acceptance_criteria=["Criterion"],
        )

        hierarchy = RequirementHierarchy(requirements=[req_a, req_b, req_c])
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(hierarchy)

        assert any(
            i.code == "circular_dependency"
            for i in result.structural_validation.cross_reference_issues
        )

    def test_returns_validation_issue_objects(
        self, invalid_hierarchy_missing_id: RequirementHierarchy
    ):
        """REQ_006.1.11: MUST return list of ValidationIssue objects."""
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(invalid_hierarchy_missing_id)

        for issue in result.structural_validation.structural_issues:
            assert hasattr(issue, "code")
            assert hasattr(issue, "message")
            assert hasattr(issue, "requirement_ref")
            assert hasattr(issue, "severity")

    def test_blocks_pipeline_on_structural_errors(
        self, invalid_hierarchy_missing_id: RequirementHierarchy
    ):
        """REQ_006.1.12: MUST BLOCK pipeline if ANY structural validation issues found."""
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(invalid_hierarchy_missing_id)

        assert result.should_proceed is False
        assert result.failure_reason is not None
        assert "structural" in result.failure_reason.lower()

    def test_completes_under_1_second_for_1000_requirements(self):
        """REQ_006.1.13: MUST complete validation in under 1 second for 1000 requirements."""
        requirements = [
            RequirementNode(
                id=f"REQ_{i:04d}",
                description=f"Requirement {i} description",
                type="parent",
                acceptance_criteria=[f"Criterion {i}"],
            )
            for i in range(1000)
        ]
        hierarchy = RequirementHierarchy(requirements=requirements)
        validator = PreTDDValidator()

        start_time = time.perf_counter()
        result = validator.validate_before_tdd(hierarchy)
        elapsed = time.perf_counter() - start_time

        assert elapsed < 1.0, f"Validation took {elapsed:.2f}s, expected < 1s"

    def test_includes_structural_validation_in_metadata(
        self, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_006.1.16: MUST include validation results in PhaseResult.metadata."""
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(valid_hierarchy)
        metadata = result.to_metadata()

        assert "structural_validation" in metadata
        assert "validation_passed" in metadata


# =============================================================================
# REQ_006.2: Semantic Validation Tests
# =============================================================================


class TestSemanticValidation:
    """Tests for REQ_006.2: Semantic validation (Stage 3) on --validate-full flag."""

    def test_only_executes_with_validate_full_flag(
        self, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_006.2.1: MUST only execute when --validate-full flag is provided."""
        # Without flag
        config = PreTDDValidationConfig(validate_full=False)
        validator = PreTDDValidator(config)
        result = validator.validate_before_tdd(valid_hierarchy, "Test scope")

        assert result.semantic_validation is None

        # With flag
        config_full = PreTDDValidationConfig(validate_full=True)
        validator_full = PreTDDValidator(config_full)
        result_full = validator_full.validate_before_tdd(valid_hierarchy, "Test scope")

        assert result_full.semantic_validation is not None

    def test_executes_after_structural_passes(
        self, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_006.2.2: MUST execute AFTER structural validation passes."""
        config = PreTDDValidationConfig(validate_full=True)
        validator = PreTDDValidator(config)
        result = validator.validate_before_tdd(valid_hierarchy, "Test scope")

        # Both structural and semantic should have run
        assert 1 in result.structural_validation.stages_run
        assert 2 in result.structural_validation.stages_run
        assert 3 in result.structural_validation.stages_run

    def test_does_not_block_pipeline_on_semantic_failures(
        self, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_006.2.9: MUST NOT block pipeline on semantic validation failures."""
        config = PreTDDValidationConfig(validate_full=True)
        validator = PreTDDValidator(config)
        result = validator.validate_before_tdd(valid_hierarchy, "Test scope")

        # Semantic validation may have warnings, but should not block
        assert result.should_proceed is True

    def test_includes_semantic_validation_in_metadata(
        self, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_006.2.12: MUST include semantic validation results in metadata."""
        config = PreTDDValidationConfig(validate_full=True)
        validator = PreTDDValidator(config)
        result = validator.validate_before_tdd(valid_hierarchy, "Test scope")
        metadata = result.to_metadata()

        assert "semantic_validation" in metadata


# =============================================================================
# REQ_006.3: Category Validation Tests
# =============================================================================


class TestCategoryValidation:
    """Tests for REQ_006.3: Category validation (Stage 4) on --validate-category flag."""

    def test_only_executes_with_validate_category_flag(
        self, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_006.3.1: MUST only execute when --validate-category flag is provided."""
        # Without flag
        config = PreTDDValidationConfig(validate_category=False)
        validator = PreTDDValidator(config)
        issues = validator.validate_category_after_tdd(valid_hierarchy)

        assert len(issues) == 0

    def test_validates_security_requirements(self):
        """REQ_006.3.4: MUST validate security requirements include required elements."""
        req = RequirementNode(
            id="REQ_SEC_001",
            description="Implement user login",  # Missing auth method
            type="implementation",
            category="security",
            acceptance_criteria=["Users can log in"],
        )

        hierarchy = RequirementHierarchy(requirements=[req])
        config = PreTDDValidationConfig(validate_category=True)
        validator = PreTDDValidator(config)
        issues = validator.validate_category_after_tdd(hierarchy)

        # Should find issues for missing security elements
        assert any(i.validation_type == "authentication_method" for i in issues)

    def test_validates_performance_requirements(self):
        """REQ_006.3.5: MUST validate performance requirements include metrics."""
        req = RequirementNode(
            id="REQ_PERF_001",
            description="System should be fast",  # No quantitative metrics
            type="implementation",
            category="performance",
            acceptance_criteria=["Performance is acceptable"],
        )

        hierarchy = RequirementHierarchy(requirements=[req])
        config = PreTDDValidationConfig(validate_category=True)
        validator = PreTDDValidator(config)
        issues = validator.validate_category_after_tdd(hierarchy)

        # Should find issues for missing metrics
        assert any(i.validation_type == "quantitative_metrics" for i in issues)

    def test_validates_integration_requirements(self):
        """REQ_006.3.6: MUST validate integration requirements include contracts."""
        req = RequirementNode(
            id="REQ_INT_001",
            description="Connect to external system",  # No interface details
            type="implementation",
            category="integration",
            acceptance_criteria=["System is connected"],
        )

        hierarchy = RequirementHierarchy(requirements=[req])
        config = PreTDDValidationConfig(validate_category=True)
        validator = PreTDDValidator(config)
        issues = validator.validate_category_after_tdd(hierarchy)

        # Should find issues for missing contract
        assert any(i.validation_type == "interface_contract" for i in issues)

    def test_skips_functional_and_usability_categories(self):
        """REQ_006.3.7: MUST skip validation for functional/usability categories."""
        func_req = RequirementNode(
            id="REQ_FUNC_001",
            description="Functional requirement",
            type="implementation",
            category="functional",
            acceptance_criteria=["Works correctly"],
        )
        usability_req = RequirementNode(
            id="REQ_USE_001",
            description="Usability requirement",
            type="implementation",
            category="usability",
            acceptance_criteria=["User-friendly"],
        )

        hierarchy = RequirementHierarchy(requirements=[func_req, usability_req])
        config = PreTDDValidationConfig(validate_category=True)
        validator = PreTDDValidator(config)
        issues = validator.validate_category_after_tdd(hierarchy)

        # No issues for functional/usability
        assert len(issues) == 0

    def test_does_not_block_pipeline_on_category_failures(self):
        """REQ_006.3.9: MUST NOT block pipeline on category validation failures."""
        # This is enforced by the API - category validation returns issues,
        # but doesn't affect should_proceed
        req = RequirementNode(
            id="REQ_SEC_001",
            description="Implement login",
            type="implementation",
            category="security",
            acceptance_criteria=["Users can log in"],
        )

        hierarchy = RequirementHierarchy(requirements=[req])
        config = PreTDDValidationConfig(validate_category=True)
        validator = PreTDDValidator(config)

        # Pre-TDD validation still passes
        result = validator.validate_before_tdd(hierarchy)
        assert result.should_proceed is True

        # Category validation returns issues but doesn't throw
        issues = validator.validate_category_after_tdd(hierarchy)
        assert len(issues) > 0


# =============================================================================
# REQ_006.4: Filter Invalid Requirements Tests
# =============================================================================


class TestFilterInvalidRequirements:
    """Tests for REQ_006.4: Filter invalid requirements before TDD planning."""

    def test_filters_out_structural_failures(
        self, mixed_validity_hierarchy: RequirementHierarchy
    ):
        """REQ_006.4.1: MUST filter out requirements that failed structural validation."""
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(mixed_validity_hierarchy)

        # Should proceed with partial success
        assert result.should_proceed is True
        assert result.filtered_hierarchy is not None
        assert result.filtered_hierarchy.skipped_count > 0

    def test_includes_skipped_count_in_metadata(
        self, mixed_validity_hierarchy: RequirementHierarchy
    ):
        """REQ_006.4.4: MUST include count of skipped requirements in metadata."""
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(mixed_validity_hierarchy)
        metadata = result.to_metadata()

        assert "skipped_requirements_count" in metadata
        assert metadata["skipped_requirements_count"] > 0

    def test_includes_skipped_ids_in_metadata(
        self, mixed_validity_hierarchy: RequirementHierarchy
    ):
        """REQ_006.4.5: MUST include list of skipped requirement IDs in metadata."""
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(mixed_validity_hierarchy)
        metadata = result.to_metadata()

        assert "skipped_requirement_ids" in metadata
        assert len(metadata["skipped_requirement_ids"]) > 0

    def test_continues_processing_valid_requirements(
        self, mixed_validity_hierarchy: RequirementHierarchy
    ):
        """REQ_006.4.7: MUST continue processing valid requirements (partial success)."""
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(mixed_validity_hierarchy)

        assert result.should_proceed is True
        assert result.filtered_hierarchy is not None
        assert result.filtered_hierarchy.valid_count > 0

    def test_fails_if_all_requirements_invalid(
        self, invalid_hierarchy_missing_id: RequirementHierarchy
    ):
        """REQ_006.4.9: MUST return FAILED if ALL requirements fail validation."""
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(invalid_hierarchy_missing_id)

        assert result.should_proceed is False

    def test_preserves_parent_child_relationships_when_filtering(self):
        """REQ_006.4.11: MUST preserve parent-child relationships when filtering."""
        parent = RequirementNode(
            id="REQ_001",
            description="Valid parent",
            type="parent",
            acceptance_criteria=["Criterion"],
        )
        valid_child = RequirementNode(
            id="REQ_001.1",
            description="Valid child",
            type="sub_process",
            parent_id="REQ_001",
            acceptance_criteria=["Criterion"],
        )
        parent.children = [valid_child]

        hierarchy = RequirementHierarchy(requirements=[parent])
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(hierarchy)

        # Parent-child structure should be preserved
        assert result.filtered_hierarchy is not None
        filtered = result.filtered_hierarchy.hierarchy
        assert len(filtered.requirements) == 1
        assert len(filtered.requirements[0].children) == 1

    def test_skips_children_when_parent_invalid(self):
        """REQ_006.4.11: If parent is invalid, children are also skipped."""
        # Create invalid parent
        parent = RequirementNode.__new__(RequirementNode)
        parent.id = "REQ_001"
        parent.description = "Invalid parent"
        parent.type = "invalid_type"  # Invalid
        parent.parent_id = None
        parent.children = []
        parent.acceptance_criteria = []
        parent.implementation = None
        parent.testable_properties = []
        parent.function_id = None
        parent.related_concepts = []
        parent.category = "functional"
        parent.contracts = None
        parent.edge_cases = []
        parent.gherkin_scenarios = []

        # Create valid child
        child = RequirementNode(
            id="REQ_001.1",
            description="Valid child",
            type="sub_process",
            parent_id="REQ_001",
            acceptance_criteria=["Criterion"],
        )
        parent.children = [child]

        hierarchy = RequirementHierarchy(requirements=[parent])
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(hierarchy)

        # Both parent and child should be skipped
        assert result.filtered_hierarchy is not None
        assert "REQ_001" in result.filtered_hierarchy.skipped_requirement_ids
        assert "REQ_001.1" in result.filtered_hierarchy.skipped_requirement_ids

    def test_force_all_bypasses_filtering(
        self, mixed_validity_hierarchy: RequirementHierarchy
    ):
        """REQ_006.4.13: MUST allow --force-all to bypass filtering."""
        config = PreTDDValidationConfig(force_all=True)
        validator = PreTDDValidator(config)
        result = validator.validate_before_tdd(mixed_validity_hierarchy)

        # Should proceed without filtering
        assert result.should_proceed is True
        assert result.filtered_hierarchy is not None
        assert result.filtered_hierarchy.skipped_count == 0


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestConvenienceFunction:
    """Tests for run_pre_tdd_validation convenience function."""

    def test_runs_with_defaults(self, valid_hierarchy: RequirementHierarchy):
        """Convenience function works with default parameters."""
        result = run_pre_tdd_validation(valid_hierarchy)

        assert result.should_proceed is True
        assert result.structural_validation is not None

    def test_accepts_validate_full_flag(self, valid_hierarchy: RequirementHierarchy):
        """Convenience function accepts validate_full parameter."""
        result = run_pre_tdd_validation(
            valid_hierarchy,
            scope_text="Test scope",
            validate_full=True,
        )

        assert result.semantic_validation is not None

    def test_accepts_force_all_flag(
        self, mixed_validity_hierarchy: RequirementHierarchy
    ):
        """Convenience function accepts force_all parameter."""
        result = run_pre_tdd_validation(
            mixed_validity_hierarchy,
            force_all=True,
        )

        assert result.filtered_hierarchy is not None
        assert result.filtered_hierarchy.skipped_count == 0

    def test_accepts_progress_callback(self, valid_hierarchy: RequirementHierarchy):
        """Convenience function accepts progress callback."""
        messages: list[str] = []

        def callback(msg: str) -> None:
            messages.append(msg)

        run_pre_tdd_validation(
            valid_hierarchy,
            progress_callback=callback,
        )

        assert len(messages) > 0


# =============================================================================
# Data Class Tests
# =============================================================================


class TestDataClasses:
    """Tests for validation data classes."""

    def test_filtered_hierarchy_properties(self):
        """FilteredHierarchy properties work correctly."""
        hierarchy = RequirementHierarchy(requirements=[])
        filtered = FilteredHierarchy(
            hierarchy=hierarchy,
            skipped_requirement_ids=["REQ_001", "REQ_002"],
            skipped_reasons={"REQ_001": "Error", "REQ_002": "Error"},
            original_count=5,
            valid_count=3,
        )

        assert filtered.skipped_count == 2
        assert filtered.all_filtered is False

    def test_filtered_hierarchy_all_filtered(self):
        """FilteredHierarchy.all_filtered is True when all filtered."""
        hierarchy = RequirementHierarchy(requirements=[])
        filtered = FilteredHierarchy(
            hierarchy=hierarchy,
            skipped_requirement_ids=["REQ_001", "REQ_002"],
            original_count=2,
            valid_count=0,
        )

        assert filtered.all_filtered is True

    def test_pre_tdd_validation_config_defaults(self):
        """PreTDDValidationConfig has correct defaults."""
        config = PreTDDValidationConfig()

        assert config.validate_full is False
        assert config.validate_category is False
        assert config.force_all is False
        assert config.early_exit_on_error is True
        assert config.timeout_seconds == 60
        assert config.max_retries == 3

    def test_pre_tdd_validation_result_to_metadata(
        self, valid_hierarchy: RequirementHierarchy
    ):
        """PreTDDValidationResult.to_metadata returns valid dict."""
        validator = PreTDDValidator()
        result = validator.validate_before_tdd(valid_hierarchy)
        metadata = result.to_metadata()

        assert isinstance(metadata, dict)
        assert "structural_validation" in metadata
        assert "validation_passed" in metadata
        assert "processing_time_ms" in metadata
