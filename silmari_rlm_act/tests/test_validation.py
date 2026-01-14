"""Tests for semantic validation module.

This module tests REQ_003: BAML-level validation for semantic checking
of requirements against research scope.
"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from silmari_rlm_act.validation.models import (
    SemanticValidationResult,
    ValidationSummary,
)
from silmari_rlm_act.validation.service import (
    SemanticValidationService,
    ValidationConfig,
    ValidationError,
)


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture
def temp_hierarchy(tmp_path: Path) -> Path:
    """Create a temporary hierarchy JSON file."""
    hierarchy = {
        "requirements": [
            {
                "id": "REQ_001",
                "description": "User authentication system",
                "type": "parent",
                "parent_id": None,
                "children": [
                    {
                        "id": "REQ_001.1",
                        "description": "Login functionality",
                        "type": "child",
                        "parent_id": "REQ_001",
                        "children": [],
                    }
                ],
                "acceptance_criteria": [],
                "implementation": None,
                "testable_properties": [],
                "function_id": None,
                "related_concepts": [],
                "category": "functional",
            }
        ],
        "metadata": {"source": "test"},
    }
    doc = tmp_path / "hierarchy.json"
    doc.write_text(json.dumps(hierarchy, indent=2))
    return doc


@pytest.fixture
def temp_research_doc(tmp_path: Path) -> Path:
    """Create a temporary research document."""
    doc = tmp_path / "research.md"
    doc.write_text(
        "# Research Document\n\n"
        "This project implements user authentication.\n"
        "The scope includes login, logout, and session management."
    )
    return doc


@pytest.fixture
def mock_baml_response() -> MagicMock:
    """Create a mock BAML validation response."""
    mock_result = MagicMock()
    mock_result.requirement_id = "REQ_001"
    mock_result.is_valid = True
    mock_result.validation_issues = []
    mock_result.suggestions = ["Consider adding rate limiting"]
    mock_result.confidence_score = 0.95
    mock_result.component_name = "auth"

    mock_response = MagicMock()
    mock_response.validation_results = [mock_result]
    mock_response.metadata = MagicMock()
    mock_response.metadata.llm_model = "test-model"
    mock_response.metadata.processing_time_ms = 1500

    return mock_response


# ===========================================================================
# REQ_003.2: ValidationResult Tests
# ===========================================================================


class TestSemanticValidationResult:
    """Tests for SemanticValidationResult model (REQ_003.2)."""

    def test_result_contains_requirement_id(self) -> None:
        """REQ_003.2.1: ValidationResult contains requirement_id string."""
        result = SemanticValidationResult(
            requirement_id="REQ_001",
            is_valid=True,
        )
        assert result.requirement_id == "REQ_001"
        assert isinstance(result.requirement_id, str)

    def test_result_contains_is_valid_boolean(self) -> None:
        """REQ_003.2.2: ValidationResult contains is_valid boolean."""
        result = SemanticValidationResult(
            requirement_id="REQ_001",
            is_valid=False,
        )
        assert result.is_valid is False
        assert isinstance(result.is_valid, bool)

    def test_result_contains_validation_issues_list(self) -> None:
        """REQ_003.2.3: ValidationResult contains validation_issues list."""
        issues = ["Missing acceptance criteria", "Scope unclear"]
        result = SemanticValidationResult(
            requirement_id="REQ_001",
            is_valid=False,
            validation_issues=issues,
        )
        assert result.validation_issues == issues
        assert isinstance(result.validation_issues, list)

    def test_result_contains_suggestions_list(self) -> None:
        """REQ_003.2.4: ValidationResult contains suggestions list."""
        suggestions = ["Add rate limiting", "Document edge cases"]
        result = SemanticValidationResult(
            requirement_id="REQ_001",
            is_valid=True,
            suggestions=suggestions,
        )
        assert result.suggestions == suggestions

    def test_result_contains_confidence_score(self) -> None:
        """REQ_003.2.5: ValidationResult contains confidence_score float 0.0-1.0."""
        result = SemanticValidationResult(
            requirement_id="REQ_001",
            is_valid=True,
            confidence_score=0.85,
        )
        assert result.confidence_score == 0.85
        assert 0.0 <= result.confidence_score <= 1.0

    def test_confidence_score_validation(self) -> None:
        """REQ_003.2.5: confidence_score must be between 0.0 and 1.0."""
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            SemanticValidationResult(
                requirement_id="REQ_001",
                is_valid=True,
                confidence_score=1.5,
            )

    def test_result_serializable_to_json(self) -> None:
        """REQ_003.2.6: All ValidationResult objects are serializable to JSON."""
        result = SemanticValidationResult(
            requirement_id="REQ_001",
            is_valid=True,
            validation_issues=["issue1"],
            suggestions=["suggestion1"],
            confidence_score=0.9,
            component_name="auth",
        )
        json_dict = result.to_dict()

        # Should be JSON serializable
        json_str = json.dumps(json_dict)
        assert json_str is not None

        # Should contain all fields
        assert json_dict["requirement_id"] == "REQ_001"
        assert json_dict["is_valid"] is True
        assert json_dict["confidence_score"] == 0.9

    def test_result_supports_comparison(self) -> None:
        """REQ_003.2.7: ValidationResult supports comparison for testing."""
        result1 = SemanticValidationResult(
            requirement_id="REQ_001",
            is_valid=True,
            confidence_score=0.9,
        )
        result2 = SemanticValidationResult(
            requirement_id="REQ_001",
            is_valid=True,
            confidence_score=0.9,
        )
        result3 = SemanticValidationResult(
            requirement_id="REQ_002",
            is_valid=True,
        )

        assert result1 == result2
        assert result1 != result3

    def test_empty_issues_implies_valid(self) -> None:
        """REQ_003.2.8: Empty validation_issues list is consistent with is_valid=True."""
        result = SemanticValidationResult(
            requirement_id="REQ_001",
            is_valid=True,
            validation_issues=[],
        )
        # No exception, valid state
        assert len(result.validation_issues) == 0
        assert result.is_valid is True

    def test_confidence_score_none_when_undetermined(self) -> None:
        """REQ_003.2.9: Confidence score is None when LLM cannot determine."""
        result = SemanticValidationResult(
            requirement_id="REQ_001",
            is_valid=True,
            confidence_score=None,
        )
        assert result.confidence_score is None

    def test_result_includes_timestamp(self) -> None:
        """REQ_003.2.10: ValidationResult includes timestamp of validation."""
        before = datetime.now()
        result = SemanticValidationResult(
            requirement_id="REQ_001",
            is_valid=True,
        )
        after = datetime.now()

        assert before <= result.validated_at <= after


# ===========================================================================
# REQ_003.1: BAML Function Invocation Tests
# ===========================================================================


class TestSemanticValidationService:
    """Tests for SemanticValidationService (REQ_003.1)."""

    def test_function_accepts_scope_and_requirements(
        self, temp_hierarchy: Path
    ) -> None:
        """REQ_003.1.1: Function accepts scope_text and current_requirements."""
        service = SemanticValidationService()

        # The service should accept these parameters
        # (actual BAML call will be mocked)
        with patch.object(
            service, "_invoke_baml_validation"
        ) as mock_invoke:
            mock_invoke.side_effect = ValidationError("BAML not available in tests")

            with pytest.raises(ValidationError):
                service.validate_sync(
                    scope_text="Test scope",
                    hierarchy_path=temp_hierarchy,
                )

    def test_service_handles_baml_unavailability(
        self, temp_hierarchy: Path
    ) -> None:
        """REQ_003.1.9: Function gracefully handles BAML service unavailability."""
        config = ValidationConfig(warning_only=True, max_retries=1)
        service = SemanticValidationService(config=config)

        with patch.object(
            service, "_invoke_baml_validation"
        ) as mock_invoke:
            mock_invoke.side_effect = ValidationError("BAML service unavailable")

            # Should not raise, should return degraded result
            summary = service.validate_sync(
                scope_text="Test scope",
                hierarchy_path=temp_hierarchy,
            )

            assert summary.total_requirements > 0
            assert len(summary.results) == 0  # No detailed results

    def test_service_returns_validation_response(
        self, temp_hierarchy: Path, mock_baml_response: MagicMock
    ) -> None:
        """REQ_003.1.6: Function returns RequirementValidationResponse."""
        service = SemanticValidationService()

        with patch.object(
            service, "_invoke_baml_validation"
        ) as mock_invoke:
            mock_invoke.return_value = mock_baml_response

            summary = service.validate_sync(
                scope_text="Test scope",
                hierarchy_path=temp_hierarchy,
            )

            assert isinstance(summary, ValidationSummary)
            assert summary.total_requirements > 0

    def test_service_logs_validation_request(
        self, temp_hierarchy: Path, mock_baml_response: MagicMock, caplog
    ) -> None:
        """REQ_003.1.7: Function logs validation request details."""
        import logging

        caplog.set_level(logging.DEBUG)
        service = SemanticValidationService()

        with patch.object(
            service, "_invoke_baml_validation"
        ) as mock_invoke:
            mock_invoke.return_value = mock_baml_response

            service.validate_sync(
                scope_text="Test scope",
                hierarchy_path=temp_hierarchy,
            )

            # Should log something about validation
            assert any("validation" in r.message.lower() for r in caplog.records)


# ===========================================================================
# REQ_003.4: Latency Handling Tests
# ===========================================================================


class TestValidationLatencyHandling:
    """Tests for validation latency handling (REQ_003.4)."""

    def test_configurable_timeout(self) -> None:
        """REQ_003.4.3: Configurable timeout (default 60 seconds)."""
        config = ValidationConfig(timeout_seconds=30)
        assert config.timeout_seconds == 30

        default_config = ValidationConfig()
        assert default_config.timeout_seconds == 60

    def test_retry_logic_configured(self) -> None:
        """REQ_003.4.10: Retry logic attempts validation up to 3 times."""
        config = ValidationConfig(max_retries=3)
        assert config.max_retries == 3

    def test_warning_only_mode(
        self, temp_hierarchy: Path
    ) -> None:
        """REQ_003.4.8: Failed LLM validation does not block (warning-only mode)."""
        config = ValidationConfig(warning_only=True, max_retries=1)
        service = SemanticValidationService(config=config)

        with patch.object(
            service, "_invoke_baml_validation"
        ) as mock_invoke:
            mock_invoke.side_effect = ValidationError("Validation failed")

            # Should not raise
            summary = service.validate_sync(
                scope_text="Test scope",
                hierarchy_path=temp_hierarchy,
            )

            # Should return a result even though validation failed
            assert summary is not None

    def test_progress_callback_called(
        self, temp_hierarchy: Path, mock_baml_response: MagicMock
    ) -> None:
        """REQ_003.4.2: User receives progress feedback during validation."""
        progress_messages: list[str] = []

        config = ValidationConfig(show_progress=True)
        service = SemanticValidationService(
            config=config,
            progress_callback=lambda msg: progress_messages.append(msg),
        )

        with patch.object(
            service, "_invoke_baml_validation"
        ) as mock_invoke:
            mock_invoke.return_value = mock_baml_response

            service.validate_sync(
                scope_text="Test scope",
                hierarchy_path=temp_hierarchy,
            )

            # Should have received progress updates
            assert len(progress_messages) > 0


# ===========================================================================
# ValidationSummary Tests
# ===========================================================================


class TestValidationSummary:
    """Tests for ValidationSummary model."""

    def test_all_valid_property(self) -> None:
        """all_valid returns True when all requirements are valid."""
        summary = ValidationSummary(
            total_requirements=3,
            valid_count=3,
            invalid_count=0,
        )
        assert summary.all_valid is True

    def test_all_valid_false_when_invalid(self) -> None:
        """all_valid returns False when some requirements are invalid."""
        summary = ValidationSummary(
            total_requirements=3,
            valid_count=2,
            invalid_count=1,
        )
        assert summary.all_valid is False

    def test_validity_rate_calculation(self) -> None:
        """validity_rate calculates correct proportion."""
        summary = ValidationSummary(
            total_requirements=4,
            valid_count=3,
            invalid_count=1,
        )
        assert summary.validity_rate == 0.75

    def test_validity_rate_empty(self) -> None:
        """validity_rate returns 1.0 for empty requirements."""
        summary = ValidationSummary(
            total_requirements=0,
            valid_count=0,
            invalid_count=0,
        )
        assert summary.validity_rate == 1.0

    def test_summary_to_dict(self) -> None:
        """Summary serializes correctly to dictionary."""
        summary = ValidationSummary(
            total_requirements=2,
            valid_count=1,
            invalid_count=1,
            llm_model="test-model",
        )
        data = summary.to_dict()

        assert data["total_requirements"] == 2
        assert data["valid_count"] == 1
        assert data["invalid_count"] == 1
        assert data["llm_model"] == "test-model"
        assert data["all_valid"] is False
        assert data["validity_rate"] == 0.5
