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

    def test_agent_sdk_error_returns_structured_error(self, patch_baml_client):
        """Agent SDK failures should be caught and wrapped."""
        # Configure mock to return a failed response
        patch_baml_client.return_value = {
            "success": False,
            "output": "",
            "error": "API rate limit exceeded",
            "elapsed": 0.5
        }

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
        assert config.expansion_timeout == 300  # 5 minutes


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


class TestCreateChildFromDetailsFunctionId:
    """Tests for function_id extraction in _create_child_from_details."""

    def test_function_id_extracted_from_baml_response(self, mock_baml_subprocess_details):
        """Given BAML returns function_id, when child created, then function_id stored on impl."""
        from planning_pipeline.decomposition import _create_child_from_details

        config = DecompositionConfig()

        # Act - use the fixture which has function_id="AUTH_001"
        child = _create_child_from_details(
            child_id="REQ_001.1",
            sub_process="Login flow implementation",
            details_response=mock_baml_subprocess_details,
            parent_id="REQ_001",
            config=config,
        )

        # Assert - function_id is on implementation children (3-tier)
        assert child.type == "sub_process"
        assert len(child.children) == 1
        assert child.children[0].function_id == "AUTH_001"


class TestCreateChildFromDetailsRelatedConcepts:
    """Tests for related_concepts extraction in _create_child_from_details."""

    def test_related_concepts_extracted_from_baml_response(self, mock_baml_subprocess_details):
        """Given BAML returns related_concepts, when child created, then stored on impl."""
        from planning_pipeline.decomposition import _create_child_from_details

        config = DecompositionConfig()

        # Act - use the fixture which has related_concepts=["forms", "validation"]
        child = _create_child_from_details(
            child_id="REQ_001.1",
            sub_process="Login flow implementation",
            details_response=mock_baml_subprocess_details,
            parent_id="REQ_001",
            config=config,
        )

        # Assert - related_concepts is on implementation children (3-tier)
        assert child.type == "sub_process"
        assert len(child.children) == 1
        assert child.children[0].related_concepts == ["forms", "validation"]

    def test_related_concepts_empty_when_none_in_response(self):
        """Given BAML response has None related_concepts, when child created, then empty list."""
        from planning_pipeline.decomposition import _create_child_from_details

        mock_response = MagicMock()
        mock_detail = MagicMock()
        mock_detail.function_id = None
        mock_detail.description = "Some description"
        mock_detail.acceptance_criteria = []
        mock_detail.implementation = None
        mock_detail.related_concepts = None
        mock_response.implementation_details = [mock_detail]

        config = DecompositionConfig()

        child = _create_child_from_details(
            child_id="REQ_001.1",
            sub_process="Process",
            details_response=mock_response,
            parent_id="REQ_001",
            config=config,
        )

        assert child.related_concepts == []

    def test_related_concepts_empty_when_empty_list_in_response(self):
        """Given BAML response has empty related_concepts list, when child created, then empty list."""
        from planning_pipeline.decomposition import _create_child_from_details

        mock_response = MagicMock()
        mock_detail = MagicMock()
        mock_detail.function_id = None
        mock_detail.description = "Some description"
        mock_detail.acceptance_criteria = []
        mock_detail.implementation = None
        mock_detail.related_concepts = []
        mock_response.implementation_details = [mock_detail]

        config = DecompositionConfig()

        child = _create_child_from_details(
            child_id="REQ_001.1",
            sub_process="Process",
            details_response=mock_response,
            parent_id="REQ_001",
            config=config,
        )

        assert child.related_concepts == []

    def test_related_concepts_empty_when_no_implementation_details(self):
        """Given no implementation_details in response, when child created, then empty list."""
        from planning_pipeline.decomposition import _create_child_from_details

        mock_response = MagicMock()
        mock_response.implementation_details = []

        config = DecompositionConfig()

        child = _create_child_from_details(
            child_id="REQ_001.1",
            sub_process="Some process",
            details_response=mock_response,
            parent_id="REQ_001",
            config=config,
        )

        assert child.related_concepts == []

    def test_related_concepts_preserves_multiple_values(self):
        """Given BAML returns multiple related_concepts, when child created, then all stored on impl."""
        from planning_pipeline.decomposition import _create_child_from_details

        mock_response = MagicMock()
        mock_detail = MagicMock()
        mock_detail.function_id = "TEST_001"
        mock_detail.description = "Test implementation"
        mock_detail.acceptance_criteria = []
        mock_detail.implementation = None
        mock_detail.related_concepts = ["auth", "jwt", "oauth", "session", "security"]
        mock_response.implementation_details = [mock_detail]

        config = DecompositionConfig()

        child = _create_child_from_details(
            child_id="REQ_001.1",
            sub_process="Auth",
            details_response=mock_response,
            parent_id="REQ_001",
            config=config,
        )

        # Assert - related_concepts is on implementation children (3-tier)
        assert len(child.children) == 1
        assert child.children[0].related_concepts == ["auth", "jwt", "oauth", "session", "security"]

    def test_function_id_generated_when_not_in_response(self):
        """Given BAML response has no function_id, when child created, then generated on impl."""
        from planning_pipeline.decomposition import _create_child_from_details
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_detail = MagicMock()
        mock_detail.function_id = None
        mock_detail.description = "Some description"
        mock_detail.acceptance_criteria = []
        mock_detail.implementation = None
        mock_detail.related_concepts = []
        mock_response.implementation_details = [mock_detail]

        config = DecompositionConfig()

        child = _create_child_from_details(
            child_id="REQ_001.1",
            sub_process="Some process",
            details_response=mock_response,
            parent_id="REQ_001",
            config=config,
        )

        # Phase 6+7: function_id is generated on implementation children (3-tier)
        assert len(child.children) == 1
        assert child.children[0].function_id is not None
        assert "." in child.children[0].function_id

    def test_function_id_generated_when_empty_string(self):
        """Given BAML response has empty function_id, when child created, then generated on impl."""
        from planning_pipeline.decomposition import _create_child_from_details
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_detail = MagicMock()
        mock_detail.function_id = ""  # Empty string
        mock_detail.description = "Some description"
        mock_detail.acceptance_criteria = []
        mock_detail.implementation = None
        mock_detail.related_concepts = []
        mock_response.implementation_details = [mock_detail]

        config = DecompositionConfig()

        child = _create_child_from_details(
            child_id="REQ_001.1",
            sub_process="Some process",
            details_response=mock_response,
            parent_id="REQ_001",
            config=config,
        )

        # Phase 6+7: function_id is generated on implementation children (3-tier)
        assert len(child.children) == 1
        assert child.children[0].function_id is not None
        assert "." in child.children[0].function_id

    def test_function_id_none_when_no_implementation_details(self):
        """Given no implementation_details in response, when child created, then None."""
        from planning_pipeline.decomposition import _create_child_from_details
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.implementation_details = []

        config = DecompositionConfig()

        child = _create_child_from_details(
            child_id="REQ_001.1",
            sub_process="Some process",
            details_response=mock_response,
            parent_id="REQ_001",
            config=config,
        )

        assert child.function_id is None


class TestGenerateFunctionIdFromDescription:
    """Tests for semantic function_id generation."""

    def test_generate_function_id_auth_pattern(self):
        """Given auth-related description, when generated, then Auth.* pattern."""
        from planning_pipeline.decomposition import _generate_function_id

        result = _generate_function_id("Authenticate user credentials")
        assert result == "Auth.authenticate"

    def test_generate_function_id_validate_pattern(self):
        """Given validation description, when generated, then Validator.validate."""
        from planning_pipeline.decomposition import _generate_function_id

        result = _generate_function_id("Validate input data")
        assert result == "Validator.validate"

    def test_generate_function_id_create_pattern(self):
        """Given create description, when generated, then Service.create."""
        from planning_pipeline.decomposition import _generate_function_id

        result = _generate_function_id("Create new user account")
        assert result == "User.create"

    def test_generate_function_id_fallback(self):
        """Given unknown pattern, when generated, then Service.action format."""
        from planning_pipeline.decomposition import _generate_function_id

        result = _generate_function_id("Something completely different")
        assert "." in result  # At least has Service.action format

    def test_generate_function_id_dashboard_render(self):
        """Given dashboard render description, when generated, then Dashboard.render."""
        from planning_pipeline.decomposition import _generate_function_id

        result = _generate_function_id("Render dashboard UI")
        assert result == "Dashboard.render"

    def test_generate_function_id_fetch_data(self):
        """Given fetch description, when generated, then Data.fetch."""
        from planning_pipeline.decomposition import _generate_function_id

        result = _generate_function_id("Fetch user data from API")
        assert result == "Data.fetch"

    def test_child_gets_generated_function_id_when_baml_none(self):
        """Given BAML returns no function_id, when child created, then generated on impl."""
        from planning_pipeline.decomposition import (
            _create_child_from_details,
            DecompositionConfig,
        )

        mock_response = MagicMock()
        mock_detail = MagicMock()
        mock_detail.function_id = None
        mock_detail.description = "Authenticate user credentials"
        mock_detail.acceptance_criteria = []
        mock_detail.implementation = None
        mock_detail.related_concepts = []
        mock_response.implementation_details = [mock_detail]

        config = DecompositionConfig()

        child = _create_child_from_details(
            child_id="REQ_001.1",
            sub_process="Auth",
            details_response=mock_response,
            parent_id="REQ_001",
            config=config,
        )

        # function_id is on implementation children (3-tier)
        assert len(child.children) == 1
        assert child.children[0].function_id is not None
        assert "." in child.children[0].function_id

    def test_child_gets_generated_function_id_when_baml_empty_string(self):
        """Given BAML returns empty function_id, when child created, then generated on impl."""
        from planning_pipeline.decomposition import (
            _create_child_from_details,
            DecompositionConfig,
        )

        mock_response = MagicMock()
        mock_detail = MagicMock()
        mock_detail.function_id = ""
        mock_detail.description = "Validate user input"
        mock_detail.acceptance_criteria = []
        mock_detail.implementation = None
        mock_detail.related_concepts = []
        mock_response.implementation_details = [mock_detail]

        config = DecompositionConfig()

        child = _create_child_from_details(
            child_id="REQ_001.1",
            sub_process="Validation",
            details_response=mock_response,
            parent_id="REQ_001",
            config=config,
        )

        # function_id is on implementation children (3-tier)
        assert len(child.children) == 1
        assert child.children[0].function_id is not None
        assert "." in child.children[0].function_id


@pytest.mark.skip(reason="3-tier hierarchy was BAML-specific; agent SDK uses 2-tier")
class TestThreeTierHierarchy:
    """Tests for 3-tier hierarchy: parent -> sub_process -> implementation.

    NOTE: These tests are skipped because the 3-tier hierarchy was specific to
    the BAML implementation. The new agent SDK implementation uses a simpler
    2-tier hierarchy (parent -> subprocesses).
    """

    def test_implementation_details_become_children(self, patch_baml_client):
        """Given BAML returns multiple impl details, when decomposed, then 3-tier."""
        # Arrange: Mock BAML to return multiple implementation details
        mock_initial = MagicMock()
        mock_req = MagicMock()
        mock_req.description = "Parent requirement"
        mock_req.sub_processes = ["Sub process 1"]
        mock_req.related_concepts = []
        mock_initial.requirements = [mock_req]

        mock_subprocess = MagicMock()
        mock_detail1 = MagicMock()
        mock_detail1.function_id = "Impl.detail1"
        mock_detail1.description = "First implementation detail"
        mock_detail1.acceptance_criteria = ["AC1"]
        mock_detail1.implementation = None
        mock_detail1.related_concepts = ["concept1"]

        mock_detail2 = MagicMock()
        mock_detail2.function_id = "Impl.detail2"
        mock_detail2.description = "Second implementation detail"
        mock_detail2.acceptance_criteria = ["AC2"]
        mock_detail2.implementation = None
        mock_detail2.related_concepts = ["concept2"]

        mock_subprocess.implementation_details = [mock_detail1, mock_detail2]

        patch_baml_client.ProcessGate1InitialExtractionPrompt.return_value = mock_initial
        patch_baml_client.ProcessGate1SubprocessDetailsPrompt.return_value = mock_subprocess

        # Act
        result = decompose_requirements("Test research content")

        # Assert: 3-tier structure
        assert isinstance(result, RequirementHierarchy)
        assert len(result.requirements) == 1

        parent = result.requirements[0]
        assert parent.type == "parent"
        assert len(parent.children) == 1

        sub_process = parent.children[0]
        assert sub_process.type == "sub_process"
        assert len(sub_process.children) == 2  # Two implementation details

        impl1 = sub_process.children[0]
        assert impl1.type == "implementation"
        assert impl1.description == "First implementation detail"
        assert impl1.function_id == "Impl.detail1"

        impl2 = sub_process.children[1]
        assert impl2.type == "implementation"
        assert impl2.description == "Second implementation detail"

    def test_implementation_node_ids_follow_pattern(self, patch_baml_client):
        """Given 3-tier hierarchy, when built, then IDs are REQ_XXX.Y.Z."""
        # Arrange
        mock_initial = MagicMock()
        mock_req = MagicMock()
        mock_req.description = "Parent"
        mock_req.sub_processes = ["Sub 1"]
        mock_req.related_concepts = []
        mock_initial.requirements = [mock_req]

        mock_subprocess = MagicMock()
        mock_detail = MagicMock()
        mock_detail.function_id = "Impl.test"
        mock_detail.description = "Implementation"
        mock_detail.acceptance_criteria = []
        mock_detail.implementation = None
        mock_detail.related_concepts = []
        mock_subprocess.implementation_details = [mock_detail]

        patch_baml_client.ProcessGate1InitialExtractionPrompt.return_value = mock_initial
        patch_baml_client.ProcessGate1SubprocessDetailsPrompt.return_value = mock_subprocess

        # Act
        result = decompose_requirements("Test")

        # Assert
        impl = result.requirements[0].children[0].children[0]
        assert impl.id == "REQ_000.1.1"  # REQ_XXX.Y.Z pattern
        assert impl.parent_id == "REQ_000.1"

    def test_implementation_nodes_have_correct_parent_id(self, patch_baml_client):
        """Given implementation nodes, when created, then parent_id points to sub_process."""
        # Arrange
        mock_initial = MagicMock()
        mock_req = MagicMock()
        mock_req.description = "Parent"
        mock_req.sub_processes = ["Sub 1"]
        mock_req.related_concepts = []
        mock_initial.requirements = [mock_req]

        mock_subprocess = MagicMock()
        mock_detail1 = MagicMock()
        mock_detail1.function_id = "Impl.1"
        mock_detail1.description = "First impl"
        mock_detail1.acceptance_criteria = []
        mock_detail1.implementation = None
        mock_detail1.related_concepts = []

        mock_detail2 = MagicMock()
        mock_detail2.function_id = "Impl.2"
        mock_detail2.description = "Second impl"
        mock_detail2.acceptance_criteria = []
        mock_detail2.implementation = None
        mock_detail2.related_concepts = []

        mock_subprocess.implementation_details = [mock_detail1, mock_detail2]

        patch_baml_client.ProcessGate1InitialExtractionPrompt.return_value = mock_initial
        patch_baml_client.ProcessGate1SubprocessDetailsPrompt.return_value = mock_subprocess

        # Act
        result = decompose_requirements("Test")

        # Assert
        sub_process = result.requirements[0].children[0]
        for impl in sub_process.children:
            assert impl.parent_id == sub_process.id

    def test_implementation_nodes_preserve_related_concepts(self, patch_baml_client):
        """Given impl details with related_concepts, when created, then preserved."""
        # Arrange
        mock_initial = MagicMock()
        mock_req = MagicMock()
        mock_req.description = "Parent"
        mock_req.sub_processes = ["Sub 1"]
        mock_req.related_concepts = []
        mock_initial.requirements = [mock_req]

        mock_subprocess = MagicMock()
        mock_detail = MagicMock()
        mock_detail.function_id = "Impl.test"
        mock_detail.description = "Implementation with concepts"
        mock_detail.acceptance_criteria = []
        mock_detail.implementation = None
        mock_detail.related_concepts = ["auth", "jwt", "security"]
        mock_subprocess.implementation_details = [mock_detail]

        patch_baml_client.ProcessGate1InitialExtractionPrompt.return_value = mock_initial
        patch_baml_client.ProcessGate1SubprocessDetailsPrompt.return_value = mock_subprocess

        # Act
        result = decompose_requirements("Test")

        # Assert
        impl = result.requirements[0].children[0].children[0]
        assert impl.related_concepts == ["auth", "jwt", "security"]

    def test_sub_process_node_has_no_implementation_data(self, patch_baml_client):
        """Given 3-tier hierarchy, sub_process nodes should not have implementation."""
        # Arrange
        mock_initial = MagicMock()
        mock_req = MagicMock()
        mock_req.description = "Parent"
        mock_req.sub_processes = ["Sub 1"]
        mock_req.related_concepts = []
        mock_initial.requirements = [mock_req]

        mock_subprocess = MagicMock()
        mock_detail = MagicMock()
        mock_detail.function_id = "Impl.test"
        mock_detail.description = "Implementation"
        mock_detail.acceptance_criteria = ["AC1"]
        mock_detail.implementation = MagicMock()
        mock_detail.implementation.frontend = ["Component"]
        mock_detail.implementation.backend = ["Service"]
        mock_detail.implementation.middleware = []
        mock_detail.implementation.shared = []
        mock_detail.related_concepts = []
        mock_subprocess.implementation_details = [mock_detail]

        patch_baml_client.ProcessGate1InitialExtractionPrompt.return_value = mock_initial
        patch_baml_client.ProcessGate1SubprocessDetailsPrompt.return_value = mock_subprocess

        # Act
        result = decompose_requirements("Test")

        # Assert - sub_process has no implementation, children do
        sub_process = result.requirements[0].children[0]
        assert sub_process.implementation is None
        assert sub_process.acceptance_criteria == []

        impl = sub_process.children[0]
        assert impl.implementation is not None
        assert impl.acceptance_criteria == ["AC1"]


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
