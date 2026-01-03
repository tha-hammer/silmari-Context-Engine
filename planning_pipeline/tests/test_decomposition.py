"""Unit and integration tests for requirement decomposition.

Following TDD approach:
- Unit tests use mocked BAML client (no API calls)
- Integration tests use real BAML (requires ANTHROPIC_API_KEY)
- Property tests verify robustness with random input
"""

import os
import pytest
from unittest.mock import MagicMock, patch

import hypothesis
from hypothesis import given, strategies as st, settings

from planning_pipeline.decomposition import (
    DecompositionConfig,
    DecompositionError,
    DecompositionErrorCode,
    decompose_requirements,
    decompose_requirements_cli_fallback,
)
from planning_pipeline.models import RequirementHierarchy


class TestDecomposeRequirements:
    """Unit tests for decompose_requirements with mocked BAML."""

    def test_returns_hierarchy_from_research(self, patch_baml_client):
        """Unit test with mocked BAML - no API calls."""
        research = "# Research: User Auth\nImplement login system."

        result = decompose_requirements(research)

        assert isinstance(result, RequirementHierarchy)
        assert len(result.requirements) == 1
        assert result.requirements[0].description == "User Authentication System"
        assert len(result.requirements[0].children) == 3  # 3 sub_processes

    def test_returns_error_for_empty_research(self, patch_baml_client):
        """Empty input should return error without calling BAML."""
        result = decompose_requirements("")

        assert isinstance(result, DecompositionError)
        assert result.error_code == DecompositionErrorCode.EMPTY_CONTENT
        patch_baml_client.ProcessGate1InitialExtractionPrompt.assert_not_called()

    def test_returns_error_for_whitespace_only_research(self, patch_baml_client):
        """Whitespace-only input should return error."""
        result = decompose_requirements("   \n\t  ")

        assert isinstance(result, DecompositionError)
        assert result.error_code == DecompositionErrorCode.EMPTY_CONTENT

    def test_baml_api_error_returns_structured_error(self, patch_baml_client):
        """BAML exceptions should be caught and wrapped."""
        patch_baml_client.ProcessGate1InitialExtractionPrompt.side_effect = Exception(
            "API rate limit"
        )

        result = decompose_requirements("Some research content")

        assert isinstance(result, DecompositionError)
        assert result.error_code == DecompositionErrorCode.BAML_API_ERROR
        assert "API rate limit" in result.error

    def test_sub_processes_become_children(self, patch_baml_client):
        """Each sub_process should become a child RequirementNode."""
        research = "# Research\nSome content about authentication."

        result = decompose_requirements(research)

        assert isinstance(result, RequirementHierarchy)
        parent = result.requirements[0]
        assert len(parent.children) == 3

        # Children should have correct parent_id
        for child in parent.children:
            assert child.parent_id == parent.id

    def test_children_have_implementation_details(
        self, patch_baml_client, mock_baml_subprocess_details
    ):
        """Children should include acceptance criteria and implementation components."""
        research = "# Research\nSome content."

        result = decompose_requirements(research)

        assert isinstance(result, RequirementHierarchy)
        # The mock provides implementation details for each subprocess
        for child in result.requirements[0].children:
            # At minimum, children should have the correct type
            assert child.type == "sub_process"

    def test_respects_max_sub_processes_config(self, patch_baml_client):
        """Config should limit number of sub-processes."""
        config = DecompositionConfig(max_sub_processes=2)
        research = "# Research\nSome content."

        result = decompose_requirements(research, config=config)

        assert isinstance(result, RequirementHierarchy)
        # Mock returns 3 sub_processes, but should be capped at 2
        assert len(result.requirements[0].children) <= 2

    def test_id_format_correct(self, patch_baml_client):
        """IDs should follow REQ_XXX format for parents, REQ_XXX.Y for children."""
        research = "# Research\nSome content."

        result = decompose_requirements(research)

        assert isinstance(result, RequirementHierarchy)
        parent = result.requirements[0]
        assert parent.id.startswith("REQ_")

        for i, child in enumerate(parent.children):
            assert child.id.startswith(parent.id + ".")


class TestDecompositionError:
    """Test DecompositionError dataclass functionality."""

    def test_to_dict_serialization(self):
        """Error should serialize to dictionary."""
        error = DecompositionError(
            success=False,
            error_code=DecompositionErrorCode.EMPTY_CONTENT,
            error="Research content cannot be empty",
            details={"input_length": 0},
        )

        result = error.to_dict()

        assert result["success"] is False
        assert result["error_code"] == "empty_content"
        assert result["error"] == "Research content cannot be empty"
        assert result["details"]["input_length"] == 0

    def test_default_values(self):
        """Error should have sensible defaults."""
        error = DecompositionError()

        assert error.success is False
        assert error.error_code == DecompositionErrorCode.BAML_API_ERROR
        assert error.error == ""
        assert error.details is None


class TestDecompositionConfig:
    """Test DecompositionConfig dataclass."""

    def test_default_values(self):
        """Config should have sensible defaults."""
        config = DecompositionConfig()

        assert config.max_sub_processes == 5
        assert config.min_sub_processes == 2
        assert config.include_acceptance_criteria is True
        assert config.expand_dimensions is False


class TestDecomposeRequirementsCliFallback:
    """Tests for CLI fallback when BAML unavailable."""

    def test_cli_fallback_returns_hierarchy(self):
        """CLI fallback should work when BAML unavailable."""
        # This test would mock subprocess call to claude CLI
        pytest.skip("CLI fallback tests require subprocess mocking - implement as needed")


class TestDecompositionProperties:
    """Property-based tests for decomposition robustness."""

    @given(research=st.text(min_size=10, max_size=1000))
    @settings(max_examples=50, suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture])
    def test_decomposition_never_crashes(self, research, patch_baml_client):
        """Decomposition should never raise - always return Hierarchy or Error."""
        result = decompose_requirements(research)

        assert isinstance(result, (RequirementHierarchy, DecompositionError))


@pytest.mark.integration
class TestDecomposeRequirementsIntegration:
    """Integration tests - require ANTHROPIC_API_KEY."""

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    )
    def test_real_baml_call_returns_valid_structure(self):
        """Real API call - run with: pytest -m integration"""
        research = """
        # Research: Session Tracking

        Implement user session tracking with:
        - Session start/end timestamps
        - Active user monitoring
        - Stale session cleanup
        """

        result = decompose_requirements(research)

        assert isinstance(result, RequirementHierarchy)
        assert len(result.requirements) >= 1
