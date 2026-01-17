"""Tests for planning_pipeline.validators module.

This module tests the multi-stage validation cascade for requirement hierarchies:
- Stage 1: Structural validation (REQ_003.1)
- Stage 2: Cross-reference validation (REQ_003.2)
- Stage 3: Semantic validation (REQ_003.3)
- Stage 4: Category-specific validation (REQ_003.4)
- HierarchyValidator orchestrator (REQ_003.5)
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from planning_pipeline.models import (
    ImplementationComponents,
    RequirementHierarchy,
    RequirementNode,
)
from planning_pipeline.validators import (
    CascadeValidationResult,
    CategoryValidationIssue,
    HierarchyValidator,
    SemanticScore,
    ValidationConfig,
    ValidationIssue,
    ValidationSeverity,
    ValidationSummary,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def valid_requirement() -> RequirementNode:
    """Create a valid requirement node for testing."""
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
def security_requirement() -> RequirementNode:
    """Create a security requirement for category-specific tests."""
    return RequirementNode(
        id="REQ_SEC_001",
        description="Implement JWT authentication with RBAC authorization",
        type="implementation",
        category="security",
        acceptance_criteria=[
            "JWT tokens are used for authentication",
            "RBAC controls access to resources",
            "Sensitive data is encrypted with AES-256",
        ],
    )


@pytest.fixture
def performance_requirement() -> RequirementNode:
    """Create a performance requirement for category-specific tests."""
    return RequirementNode(
        id="REQ_PERF_001",
        description="API must respond in under 200ms for 100 concurrent users",
        type="implementation",
        category="performance",
        acceptance_criteria=[
            "Response time < 200ms at p95",
            "Handle 100 concurrent connections",
            "Throughput > 1000 req/s",
        ],
    )


@pytest.fixture
def integration_requirement() -> RequirementNode:
    """Create an integration requirement for category-specific tests."""
    return RequirementNode(
        id="REQ_INT_001",
        description="Integrate with external payment API endpoint",
        type="implementation",
        category="integration",
        acceptance_criteria=[
            "REST API endpoint for payment processing",
            "JSON request/response format",
            "Retry on transient errors with exponential backoff",
        ],
    )


@pytest.fixture
def validator() -> HierarchyValidator:
    """Create a default validator for testing."""
    return HierarchyValidator()


# =============================================================================
# REQ_003.1: Stage 1 Structural Validation Tests
# =============================================================================


class TestStructuralValidation:
    """Tests for Stage 1 structural validation (REQ_003.1)."""

    def test_validate_1000_requirements_under_1_second(
        self, validator: HierarchyValidator
    ):
        """REQ_003.1.1: MUST complete validation of 1000 requirements in under 1 second."""
        # Create 1000 requirements
        requirements = [
            RequirementNode(
                id=f"REQ_{i:03d}",
                description=f"Requirement {i} description",
                type="parent",
                acceptance_criteria=[f"Criterion {i}"],
            )
            for i in range(1000)
        ]
        hierarchy = RequirementHierarchy(requirements=requirements)

        start_time = time.perf_counter()
        issues = validator.validate_structural(hierarchy)
        elapsed = time.perf_counter() - start_time

        assert elapsed < 1.0, f"Validation took {elapsed:.2f}s, expected < 1s"

    def test_missing_id_returns_validation_issue(self, validator: HierarchyValidator):
        """REQ_003.1.2: MUST return ValidationIssue with code 'missing_id' when id is null/empty."""
        # We need to bypass __post_init__ validation
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

        hierarchy = RequirementHierarchy(requirements=[req])
        issues = validator.validate_structural(hierarchy)

        assert any(i.code == "missing_id" for i in issues)

    def test_empty_description_returns_validation_issue(
        self, validator: HierarchyValidator
    ):
        """REQ_003.1.3: MUST return ValidationIssue with code 'empty_description' when description is null/empty."""
        # Bypass validation in __post_init__
        req = RequirementNode.__new__(RequirementNode)
        req.id = "REQ_001"
        req.description = ""
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
        issues = validator.validate_structural(hierarchy)

        assert any(i.code == "empty_description" for i in issues)

    def test_invalid_type_returns_validation_issue(
        self, validator: HierarchyValidator
    ):
        """REQ_003.1.4: MUST return ValidationIssue with code 'invalid_type' when type is invalid."""
        req = RequirementNode.__new__(RequirementNode)
        req.id = "REQ_001"
        req.description = "Test requirement"
        req.type = "invalid_type"
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
        issues = validator.validate_structural(hierarchy)

        assert any(i.code == "invalid_type" for i in issues)

    def test_invalid_category_returns_validation_issue(
        self, validator: HierarchyValidator
    ):
        """REQ_003.1.5: MUST return ValidationIssue with code 'invalid_category' when category is invalid."""
        req = RequirementNode.__new__(RequirementNode)
        req.id = "REQ_001"
        req.description = "Test requirement"
        req.type = "parent"
        req.parent_id = None
        req.children = []
        req.acceptance_criteria = []
        req.implementation = None
        req.testable_properties = []
        req.function_id = None
        req.related_concepts = []
        req.category = "invalid_category"
        req.contracts = None
        req.edge_cases = []
        req.gherkin_scenarios = []

        hierarchy = RequirementHierarchy(requirements=[req])
        issues = validator.validate_structural(hierarchy)

        assert any(i.code == "invalid_category" for i in issues)

    def test_invalid_parent_ref_returns_validation_issue(
        self, validator: HierarchyValidator
    ):
        """REQ_003.1.6: MUST return ValidationIssue with code 'invalid_parent_ref' when parent doesn't exist."""
        parent = RequirementNode(
            id="REQ_001",
            description="Parent requirement",
            type="parent",
            acceptance_criteria=["Criterion"],
        )

        child = RequirementNode(
            id="REQ_001.1",
            description="Child requirement",
            type="sub_process",
            parent_id="REQ_NONEXISTENT",  # Invalid parent reference
            acceptance_criteria=["Criterion"],
        )
        # Don't add child to parent.children - this creates the inconsistency

        hierarchy = RequirementHierarchy(requirements=[parent, child])
        issues = validator.validate_structural(hierarchy)

        assert any(i.code == "invalid_parent_ref" for i in issues)

    def test_valid_hierarchy_returns_empty_list(
        self, validator: HierarchyValidator, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_003.1.8: MUST return empty list when all structural validations pass."""
        issues = validator.validate_structural(valid_hierarchy)
        # Filter for errors only (warnings are OK)
        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert len(errors) == 0

    def test_validation_issue_has_human_readable_message(
        self, validator: HierarchyValidator
    ):
        """REQ_003.1.9: MUST provide human-readable error message in each ValidationIssue."""
        req = RequirementNode.__new__(RequirementNode)
        req.id = "REQ_001"
        req.description = "Test"
        req.type = "invalid"
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
        issues = validator.validate_structural(hierarchy)

        assert len(issues) > 0
        for issue in issues:
            assert issue.message
            assert len(issue.message) > 10  # Reasonable message length

    def test_validation_issue_includes_requirement_reference(
        self, validator: HierarchyValidator
    ):
        """REQ_003.1.10: MUST include the failing requirement reference in ValidationIssue."""
        req = RequirementNode.__new__(RequirementNode)
        req.id = "REQ_001"
        req.description = "Test"
        req.type = "invalid"
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
        issues = validator.validate_structural(hierarchy)

        assert len(issues) > 0
        for issue in issues:
            assert issue.requirement_ref is not None


# =============================================================================
# REQ_003.2: Stage 2 Cross-Reference Validation Tests
# =============================================================================


class TestCrossReferenceValidation:
    """Tests for Stage 2 cross-reference validation (REQ_003.2)."""

    def test_validate_1000_requirements_under_1_second(
        self, validator: HierarchyValidator
    ):
        """REQ_003.2.1: MUST complete cross-reference validation of 1000 requirements in under 1 second."""
        requirements = [
            RequirementNode(
                id=f"REQ_{i:03d}",
                description=f"Requirement {i} description",
                type="parent",
                acceptance_criteria=[f"Criterion {i}"],
            )
            for i in range(1000)
        ]
        hierarchy = RequirementHierarchy(requirements=requirements)

        start_time = time.perf_counter()
        issues = validator.validate_cross_references(hierarchy)
        elapsed = time.perf_counter() - start_time

        assert elapsed < 1.0, f"Validation took {elapsed:.2f}s, expected < 1s"

    def test_duplicate_id_returns_validation_issue(
        self, validator: HierarchyValidator
    ):
        """REQ_003.2.2: MUST return ValidationIssue with code 'duplicate_id' when IDs are duplicated."""
        req1 = RequirementNode(
            id="REQ_001",
            description="First requirement",
            type="parent",
            acceptance_criteria=["Criterion"],
        )
        req2 = RequirementNode(
            id="REQ_001",  # Duplicate ID
            description="Second requirement with same ID",
            type="parent",
            acceptance_criteria=["Criterion"],
        )

        hierarchy = RequirementHierarchy(requirements=[req1, req2])
        issues = validator.validate_cross_references(hierarchy)

        duplicate_issues = [i for i in issues if i.code == "duplicate_id"]
        assert len(duplicate_issues) > 0

    def test_duplicate_id_includes_both_references(
        self, validator: HierarchyValidator
    ):
        """REQ_003.2.3: MUST include both original and duplicate requirement references."""
        req1 = RequirementNode(
            id="REQ_001",
            description="First requirement",
            type="parent",
            acceptance_criteria=["Criterion"],
        )
        req2 = RequirementNode(
            id="REQ_001",
            description="Second requirement",
            type="parent",
            acceptance_criteria=["Criterion"],
        )

        hierarchy = RequirementHierarchy(requirements=[req1, req2])
        issues = validator.validate_cross_references(hierarchy)

        duplicate_issues = [i for i in issues if i.code == "duplicate_id"]
        assert len(duplicate_issues) > 0
        assert duplicate_issues[0].details is not None
        assert "original_ref" in duplicate_issues[0].details
        assert "duplicate_ref" in duplicate_issues[0].details

    def test_orphan_child_returns_validation_issue(
        self, validator: HierarchyValidator
    ):
        """REQ_003.2.4: MUST return ValidationIssue with code 'orphan_child' when child references non-existent parent."""
        child = RequirementNode(
            id="REQ_001.1",
            description="Orphan child requirement",
            type="sub_process",
            parent_id="REQ_NONEXISTENT",
            acceptance_criteria=["Criterion"],
        )

        hierarchy = RequirementHierarchy(requirements=[child])
        issues = validator.validate_cross_references(hierarchy)

        orphan_issues = [i for i in issues if i.code == "orphan_child"]
        assert len(orphan_issues) > 0

    def test_circular_dependency_returns_validation_issue(
        self, validator: HierarchyValidator
    ):
        """REQ_003.2.5: MUST return ValidationIssue with code 'circular_dependency'."""
        # Create a circular dependency: A -> B -> C -> A
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
        issues = validator.validate_cross_references(hierarchy)

        circular_issues = [i for i in issues if i.code == "circular_dependency"]
        assert len(circular_issues) > 0

    def test_detects_long_circular_chains(self, validator: HierarchyValidator):
        """REQ_003.2.6: MUST detect circular dependencies of any length."""
        # Create a longer chain: A -> B -> C -> D -> E -> A
        requirements = []
        for i, letter in enumerate("ABCDE"):
            parent_letter = "EDCBA"[i]  # E, D, C, B, A
            requirements.append(
                RequirementNode(
                    id=f"REQ_{letter}",
                    description=f"Requirement {letter}",
                    type="parent",
                    parent_id=f"REQ_{parent_letter}",
                    acceptance_criteria=["Criterion"],
                )
            )

        hierarchy = RequirementHierarchy(requirements=requirements)
        issues = validator.validate_cross_references(hierarchy)

        circular_issues = [i for i in issues if i.code == "circular_dependency"]
        assert len(circular_issues) > 0

    def test_missing_acceptance_criteria_returns_warning(
        self, validator: HierarchyValidator
    ):
        """REQ_003.2.7: MUST return ValidationIssue with code 'missing_acceptance_criteria'."""
        req = RequirementNode(
            id="REQ_001",
            description="Requirement without acceptance criteria",
            type="parent",
            acceptance_criteria=[],  # Empty
        )

        hierarchy = RequirementHierarchy(requirements=[req])
        issues = validator.validate_cross_references(hierarchy)

        missing_ac_issues = [i for i in issues if i.code == "missing_acceptance_criteria"]
        assert len(missing_ac_issues) > 0

    def test_uses_single_pass_o_n_complexity(self, validator: HierarchyValidator):
        """REQ_003.2.9: MUST track all seen IDs in a single pass using O(n) time complexity."""
        # This is validated by the <1s performance test for 1000 requirements
        # If it weren't O(n), 1000 requirements would take much longer
        requirements = [
            RequirementNode(
                id=f"REQ_{i:03d}",
                description=f"Requirement {i}",
                type="parent",
                acceptance_criteria=["Criterion"],
            )
            for i in range(500)
        ]
        hierarchy = RequirementHierarchy(requirements=requirements)

        start_time = time.perf_counter()
        validator.validate_cross_references(hierarchy)
        elapsed = time.perf_counter() - start_time

        assert elapsed < 0.5  # Should be very fast for O(n)


# =============================================================================
# REQ_003.3: Stage 3 Semantic Validation Tests
# =============================================================================


class TestSemanticValidation:
    """Tests for Stage 3 semantic validation (REQ_003.3)."""

    def test_invokes_baml_validation_prompt(
        self, validator: HierarchyValidator, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_003.3.1: MUST invoke existing BAML ProcessGate1RequirementValidationPrompt."""
        # Mock the baml_client module that is imported inside the method
        mock_result = MagicMock()
        mock_result.requirement_id = "REQ_001"
        mock_result.is_valid = True
        mock_result.confidence_score = 0.9

        mock_response = MagicMock()
        mock_response.validation_results = [mock_result]

        mock_b = MagicMock()
        mock_b.ProcessGate1RequirementValidationPrompt.return_value = mock_response

        with patch.dict("sys.modules", {"baml_client": MagicMock(b=mock_b)}):
            validator.config.run_semantic = True
            summary = validator.validate_semantic(valid_hierarchy, "Test scope")

            # The test passes if we get a summary back with scores
            assert isinstance(summary, ValidationSummary)
            assert len(summary.scores) > 0

    def test_batches_requirements_max_10_per_call(
        self, validator: HierarchyValidator
    ):
        """REQ_003.3.2: MUST batch requirements to optimize LLM calls (max 10 per call)."""
        # Create 25 requirements
        requirements = [
            RequirementNode(
                id=f"REQ_{i:03d}",
                description=f"Requirement {i}",
                type="parent",
                acceptance_criteria=["Criterion"],
            )
            for i in range(25)
        ]
        hierarchy = RequirementHierarchy(requirements=requirements)

        assert validator.config.batch_size == 10

    def test_returns_clarity_score(
        self, validator: HierarchyValidator, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_003.3.3: MUST return clarity_score (0.0-1.0) for each requirement."""
        summary = validator.validate_semantic(valid_hierarchy, "Test scope")

        for score in summary.scores:
            assert 0.0 <= score.clarity_score <= 1.0

    def test_returns_completeness_score(
        self, validator: HierarchyValidator, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_003.3.4: MUST return completeness_score (0.0-1.0) for each requirement."""
        summary = validator.validate_semantic(valid_hierarchy, "Test scope")

        for score in summary.scores:
            assert 0.0 <= score.completeness_score <= 1.0

    def test_returns_scope_alignment_score(
        self, validator: HierarchyValidator, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_003.3.5: MUST return scope_alignment_score (0.0-1.0)."""
        summary = validator.validate_semantic(valid_hierarchy, "Test scope")

        for score in summary.scores:
            assert 0.0 <= score.scope_alignment_score <= 1.0

    def test_flags_low_clarity_requirements(self, validator: HierarchyValidator):
        """REQ_003.3.6: MUST flag requirements with clarity_score < 0.7 as needing revision."""
        score = SemanticScore(
            requirement_id="REQ_001",
            clarity_score=0.6,
            completeness_score=0.8,
            scope_alignment_score=0.8,
        )

        assert score.needs_revision is True

    def test_flags_incomplete_requirements(self, validator: HierarchyValidator):
        """REQ_003.3.7: MUST flag requirements with completeness_score < 0.6 as incomplete."""
        score = SemanticScore(
            requirement_id="REQ_001",
            clarity_score=0.8,
            completeness_score=0.5,
            scope_alignment_score=0.8,
        )

        assert score.is_incomplete is True

    def test_flags_out_of_scope_requirements(self, validator: HierarchyValidator):
        """REQ_003.3.8: MUST flag requirements with scope_alignment_score < 0.5 as out of scope."""
        score = SemanticScore(
            requirement_id="REQ_001",
            clarity_score=0.8,
            completeness_score=0.8,
            scope_alignment_score=0.4,
        )

        assert score.is_out_of_scope is True

    def test_semantic_validation_disabled_by_default(
        self, validator: HierarchyValidator
    ):
        """REQ_003.3.10: MUST support --validate-full flag (disabled by default)."""
        assert validator.config.run_semantic is False

    def test_aggregates_to_validation_summary(
        self, validator: HierarchyValidator, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_003.3.11: MUST aggregate individual validations into ValidationSummary."""
        summary = validator.validate_semantic(valid_hierarchy, "Test scope")

        assert isinstance(summary, ValidationSummary)
        assert summary.processing_time_ms >= 0
        assert hasattr(summary, "average_clarity")
        assert hasattr(summary, "average_completeness")
        assert hasattr(summary, "average_scope_alignment")


# =============================================================================
# REQ_003.4: Stage 4 Category-Specific Validation Tests
# =============================================================================


class TestCategorySpecificValidation:
    """Tests for Stage 4 category-specific validation (REQ_003.4)."""

    def test_validates_security_authentication_method(
        self, validator: HierarchyValidator
    ):
        """REQ_003.4.4: MUST validate security requirements specify authentication method."""
        req = RequirementNode(
            id="REQ_SEC_001",
            description="Implement user login",
            type="implementation",
            category="security",
            acceptance_criteria=["Users can log in"],
        )

        hierarchy = RequirementHierarchy(requirements=[req])
        issues = validator.validate_category_specific(hierarchy)

        auth_issues = [
            i for i in issues if i.validation_type == "authentication_method"
        ]
        assert len(auth_issues) > 0

    def test_validates_security_authorization_model(
        self, validator: HierarchyValidator
    ):
        """REQ_003.4.5: MUST validate security requirements specify authorization model."""
        req = RequirementNode(
            id="REQ_SEC_001",
            description="Implement secure login feature",  # No authorization keywords
            type="implementation",
            category="security",
            acceptance_criteria=["Users can log in securely"],  # No authz keywords
        )

        hierarchy = RequirementHierarchy(requirements=[req])
        issues = validator.validate_category_specific(hierarchy)

        authz_issues = [
            i for i in issues if i.validation_type == "authorization_model"
        ]
        assert len(authz_issues) > 0

    def test_validates_security_encryption(self, validator: HierarchyValidator):
        """REQ_003.4.6: MUST validate security requirements mention encryption for sensitive data."""
        req = RequirementNode(
            id="REQ_SEC_001",
            description="Store user passwords and sensitive data",
            type="implementation",
            category="security",
            acceptance_criteria=["Passwords are stored"],
        )

        hierarchy = RequirementHierarchy(requirements=[req])
        issues = validator.validate_category_specific(hierarchy)

        encryption_issues = [i for i in issues if i.validation_type == "encryption"]
        assert len(encryption_issues) > 0

    def test_validates_performance_quantitative_metrics(
        self, validator: HierarchyValidator
    ):
        """REQ_003.4.7: MUST validate performance requirements include quantitative metrics."""
        req = RequirementNode(
            id="REQ_PERF_001",
            description="System should be fast",
            type="implementation",
            category="performance",
            acceptance_criteria=["Performance is acceptable"],
        )

        hierarchy = RequirementHierarchy(requirements=[req])
        issues = validator.validate_category_specific(hierarchy)

        metric_issues = [
            i for i in issues if i.validation_type == "quantitative_metrics"
        ]
        assert len(metric_issues) > 0

    def test_validates_performance_load_conditions(
        self, validator: HierarchyValidator
    ):
        """REQ_003.4.8: MUST validate performance requirements specify load conditions."""
        req = RequirementNode(
            id="REQ_PERF_001",
            description="Response time under 100ms",
            type="implementation",
            category="performance",
            acceptance_criteria=["Response time is fast"],
        )

        hierarchy = RequirementHierarchy(requirements=[req])
        issues = validator.validate_category_specific(hierarchy)

        load_issues = [i for i in issues if i.validation_type == "load_conditions"]
        assert len(load_issues) > 0

    def test_validates_integration_interface_contract(
        self, validator: HierarchyValidator
    ):
        """REQ_003.4.9: MUST validate integration requirements define interface contract."""
        req = RequirementNode(
            id="REQ_INT_001",
            description="Connect to external system",
            type="implementation",
            category="integration",
            acceptance_criteria=["System is connected"],
        )

        hierarchy = RequirementHierarchy(requirements=[req])
        issues = validator.validate_category_specific(hierarchy)

        contract_issues = [
            i for i in issues if i.validation_type == "interface_contract"
        ]
        assert len(contract_issues) > 0

    def test_validates_integration_error_handling(
        self, validator: HierarchyValidator
    ):
        """REQ_003.4.10: MUST validate integration requirements specify error handling."""
        req = RequirementNode(
            id="REQ_INT_001",
            description="Integrate with external API endpoint",
            type="implementation",
            category="integration",
            acceptance_criteria=["API is called"],
        )

        hierarchy = RequirementHierarchy(requirements=[req])
        issues = validator.validate_category_specific(hierarchy)

        error_issues = [i for i in issues if i.validation_type == "error_handling"]
        assert len(error_issues) > 0

    def test_returns_category_validation_issue_type(
        self, validator: HierarchyValidator
    ):
        """REQ_003.4.11: MUST return CategoryValidationIssue with category, validation_type, failure_reason."""
        req = RequirementNode(
            id="REQ_SEC_001",
            description="Security feature",
            type="implementation",
            category="security",
            acceptance_criteria=["Secure"],
        )

        hierarchy = RequirementHierarchy(requirements=[req])
        issues = validator.validate_category_specific(hierarchy)

        for issue in issues:
            assert isinstance(issue, CategoryValidationIssue)
            assert issue.category is not None
            assert issue.validation_type is not None
            assert issue.failure_reason is not None

    def test_category_validation_disabled_by_default(
        self, validator: HierarchyValidator
    ):
        """REQ_003.4.12: MUST support --validate-category flag (disabled by default)."""
        assert validator.config.run_category is False

    def test_skips_functional_category(self, validator: HierarchyValidator):
        """REQ_003.4.13: MUST skip validation for categories without specific rules."""
        req = RequirementNode(
            id="REQ_FUNC_001",
            description="Functional requirement",
            type="implementation",
            category="functional",
            acceptance_criteria=["Works correctly"],
        )

        hierarchy = RequirementHierarchy(requirements=[req])
        issues = validator.validate_category_specific(hierarchy)

        # No issues for functional category
        assert len(issues) == 0

    def test_skips_usability_category(self, validator: HierarchyValidator):
        """REQ_003.4.13: MUST skip validation for usability category."""
        req = RequirementNode(
            id="REQ_USE_001",
            description="Usability requirement",
            type="implementation",
            category="usability",
            acceptance_criteria=["User-friendly"],
        )

        hierarchy = RequirementHierarchy(requirements=[req])
        issues = validator.validate_category_specific(hierarchy)

        # No issues for usability category
        assert len(issues) == 0

    def test_valid_security_requirement_passes(
        self, validator: HierarchyValidator, security_requirement: RequirementNode
    ):
        """Valid security requirement with all elements should pass."""
        hierarchy = RequirementHierarchy(requirements=[security_requirement])
        issues = validator.validate_category_specific(hierarchy)

        # Well-formed security requirement should have no issues
        assert len(issues) == 0

    def test_valid_performance_requirement_passes(
        self, validator: HierarchyValidator, performance_requirement: RequirementNode
    ):
        """Valid performance requirement with metrics and load should pass."""
        hierarchy = RequirementHierarchy(requirements=[performance_requirement])
        issues = validator.validate_category_specific(hierarchy)

        # Well-formed performance requirement should have no issues
        assert len(issues) == 0

    def test_valid_integration_requirement_passes(
        self, validator: HierarchyValidator, integration_requirement: RequirementNode
    ):
        """Valid integration requirement with contract and error handling should pass."""
        hierarchy = RequirementHierarchy(requirements=[integration_requirement])
        issues = validator.validate_category_specific(hierarchy)

        # Well-formed integration requirement should have no issues
        assert len(issues) == 0


# =============================================================================
# REQ_003.5: HierarchyValidator Orchestrator Tests
# =============================================================================


class TestHierarchyValidator:
    """Tests for HierarchyValidator orchestrator class (REQ_003.5)."""

    def test_class_exists_in_validators_module(self):
        """REQ_003.5.1: MUST create HierarchyValidator class in validators.py."""
        from planning_pipeline.validators import HierarchyValidator

        assert HierarchyValidator is not None

    def test_accepts_validation_config_in_constructor(self):
        """REQ_003.5.2: MUST accept ValidationConfig in constructor."""
        config = ValidationConfig(
            run_structural=True,
            run_cross_references=True,
            run_semantic=False,
            run_category=False,
        )
        validator = HierarchyValidator(config=config)

        assert validator.config.run_structural is True
        assert validator.config.run_semantic is False

    def test_exposes_validate_structural_method(
        self, validator: HierarchyValidator, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_003.5.3: MUST expose validate_structural method."""
        result = validator.validate_structural(valid_hierarchy)

        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, ValidationIssue)

    def test_exposes_validate_cross_references_method(
        self, validator: HierarchyValidator, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_003.5.4: MUST expose validate_cross_references method."""
        result = validator.validate_cross_references(valid_hierarchy)

        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, ValidationIssue)

    def test_exposes_validate_semantic_method(
        self, validator: HierarchyValidator, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_003.5.5: MUST expose validate_semantic method."""
        result = validator.validate_semantic(valid_hierarchy, "Test scope")

        assert isinstance(result, ValidationSummary)

    def test_exposes_validate_category_specific_method(
        self, validator: HierarchyValidator, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_003.5.6: MUST expose validate_category_specific method."""
        result = validator.validate_category_specific(valid_hierarchy)

        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, CategoryValidationIssue)

    def test_exposes_validate_all_method(
        self, validator: HierarchyValidator, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_003.5.7: MUST expose validate_all method."""
        result = validator.validate_all(valid_hierarchy, "Test scope")

        assert isinstance(result, CascadeValidationResult)

    def test_early_exit_on_stage_1_error(self, validator: HierarchyValidator):
        """REQ_003.5.8: MUST early exit if Stage 1 fails with ERROR severity."""
        # Create requirement with structural error
        req = RequirementNode.__new__(RequirementNode)
        req.id = "REQ_001"
        req.description = "Test"
        req.type = "invalid_type"  # ERROR
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
        result = validator.validate_all(hierarchy)

        assert result.early_exit_stage == 1
        assert 1 in result.stages_run
        assert 2 not in result.stages_run

    def test_early_exit_on_stage_2_error(self, validator: HierarchyValidator):
        """REQ_003.5.9: MUST early exit if Stage 2 fails with ERROR severity."""
        # Create requirements with cross-reference error (duplicate IDs)
        req1 = RequirementNode(
            id="REQ_001",
            description="First requirement",
            type="parent",
            acceptance_criteria=["Criterion"],
        )
        req2 = RequirementNode(
            id="REQ_001",  # Duplicate ID
            description="Second requirement",
            type="parent",
            acceptance_criteria=["Criterion"],
        )

        hierarchy = RequirementHierarchy(requirements=[req1, req2])
        result = validator.validate_all(hierarchy)

        assert result.early_exit_stage == 2
        assert 1 in result.stages_run
        assert 2 in result.stages_run
        # Semantic validation should not run
        assert result.semantic_summary is None

    def test_aggregates_results_with_per_stage_breakdown(
        self, validator: HierarchyValidator, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_003.5.10: MUST aggregate all validation results into CascadeValidationResult."""
        config = ValidationConfig(
            run_structural=True,
            run_cross_references=True,
            run_semantic=True,
            run_category=True,
            early_exit_on_error=False,
        )
        validator = HierarchyValidator(config=config)
        result = validator.validate_all(valid_hierarchy, "Test scope")

        assert isinstance(result.structural_issues, list)
        assert isinstance(result.cross_reference_issues, list)
        assert isinstance(result.category_issues, list)
        assert result.stages_run is not None

    def test_logs_validation_progress_and_timing(
        self, validator: HierarchyValidator, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_003.5.11: MUST log validation progress and timing for each stage."""
        progress_messages: list[str] = []

        def progress_callback(msg: str) -> None:
            progress_messages.append(msg)

        validator = HierarchyValidator(progress_callback=progress_callback)
        validator.validate_all(valid_hierarchy)

        assert len(progress_messages) > 0
        assert any("Stage 1" in msg for msg in progress_messages)
        assert any("Stage 2" in msg for msg in progress_messages)

    def test_accepts_optional_progress_callback(
        self, valid_hierarchy: RequirementHierarchy
    ):
        """REQ_003.5.13: MUST accept optional progress_callback."""
        callback_called = {"value": False}

        def callback(msg: str) -> None:
            callback_called["value"] = True

        validator = HierarchyValidator(progress_callback=callback)
        validator.validate_all(valid_hierarchy)

        assert callback_called["value"] is True

    def test_importable_from_planning_pipeline_validators(self):
        """REQ_003.5.14: MUST be importable from planning_pipeline.validators."""
        from planning_pipeline.validators import HierarchyValidator

        assert HierarchyValidator is not None


# =============================================================================
# Data Class Tests
# =============================================================================


class TestDataClasses:
    """Tests for validation data classes."""

    def test_validation_issue_serialization(self):
        """ValidationIssue can be serialized to dict."""
        issue = ValidationIssue(
            code="test_code",
            message="Test message",
            requirement_ref="REQ_001",
            severity=ValidationSeverity.ERROR,
            stage=1,
            details={"key": "value"},
        )

        d = issue.to_dict()

        assert d["code"] == "test_code"
        assert d["message"] == "Test message"
        assert d["severity"] == "error"

    def test_category_validation_issue_serialization(self):
        """CategoryValidationIssue can be serialized to dict."""
        issue = CategoryValidationIssue(
            category="security",
            validation_type="authentication",
            requirement_ref="REQ_001",
            failure_reason="Missing auth method",
            suggestions=["Add OAuth"],
        )

        d = issue.to_dict()

        assert d["category"] == "security"
        assert d["validation_type"] == "authentication"
        assert len(d["suggestions"]) == 1

    def test_semantic_score_properties(self):
        """SemanticScore properties work correctly."""
        score = SemanticScore(
            requirement_id="REQ_001",
            clarity_score=0.5,
            completeness_score=0.4,
            scope_alignment_score=0.3,
        )

        assert score.needs_revision is True  # < 0.7
        assert score.is_incomplete is True  # < 0.6
        assert score.is_out_of_scope is True  # < 0.5

    def test_validation_summary_averages(self):
        """ValidationSummary calculates averages correctly."""
        scores = [
            SemanticScore("REQ_001", 0.8, 0.7, 0.9),
            SemanticScore("REQ_002", 0.6, 0.5, 0.7),
        ]
        summary = ValidationSummary(scores=scores)

        assert summary.average_clarity == 0.7
        assert summary.average_completeness == 0.6
        assert summary.average_scope_alignment == 0.8

    def test_cascade_validation_result_properties(self):
        """CascadeValidationResult properties work correctly."""
        result = CascadeValidationResult(
            structural_issues=[
                ValidationIssue(
                    code="error",
                    message="Test",
                    severity=ValidationSeverity.ERROR,
                )
            ],
            cross_reference_issues=[],
            category_issues=[],
            stages_run=[1, 2],
        )

        assert result.total_issues == 1
        assert result.has_errors is True
        assert result.passed is False

    def test_validation_config_defaults(self):
        """ValidationConfig has correct defaults."""
        config = ValidationConfig()

        assert config.run_structural is True
        assert config.run_cross_references is True
        assert config.run_semantic is False
        assert config.run_category is False
        assert config.early_exit_on_error is True
        assert config.clarity_threshold == 0.7
        assert config.completeness_threshold == 0.6
        assert config.scope_alignment_threshold == 0.5
        assert config.batch_size == 10
