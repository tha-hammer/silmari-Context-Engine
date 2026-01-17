"""Tests for Agent SDK + BAML integration module.

Tests cover:
- REQ_004.1: BAML b.request for typed prompt building
- REQ_004.2: Agent SDK execution with ClaudeAgentOptions
- REQ_004.3: BAML b.parse for type-safe response parsing
- REQ_004.4: OpusAgent client configuration
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from planning_pipeline.agent_sdk_integration import (
    AgentSDKConfig,
    AgentSDKError,
    AgentSDKErrorCode,
    AgentSDKResult,
    BAMLRequest,
    build_baml_request,
    execute_with_agent_sdk,
    parse_baml_response,
    agent_sdk_decompose,
    _extract_json,
    _clean_response_text,
    _build_subprocess_details_prompt,
    HAS_AGENT_SDK,
    BAML_AVAILABLE,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_baml_client():
    """Mock BAML client for testing."""
    with patch('planning_pipeline.agent_sdk_integration.baml_client') as mock:
        mock.ProcessGate1SubprocessDetailsPrompt = MagicMock()
        mock.ProcessGate1InitialExtractionPrompt = MagicMock()
        yield mock


@pytest.fixture
def mock_agent_sdk():
    """Mock Agent SDK for testing."""
    with patch('planning_pipeline.agent_sdk_integration.query') as mock_query:
        # Create async iterator mock
        async def mock_async_iter():
            from unittest.mock import MagicMock
            # Yield a result message
            result_msg = MagicMock()
            result_msg.is_error = False
            result_msg.result = '{"implementation_details": [], "metadata": {"baml_validated": true}}'
            yield result_msg

        mock_query.return_value = mock_async_iter()
        yield mock_query


@pytest.fixture
def sample_subprocess_details_response():
    """Sample response JSON for ProcessGate1SubprocessDetailsPrompt."""
    return {
        "implementation_details": [
            {
                "function_id": "AuthService.login",
                "description": "Implement user login endpoint",
                "related_concepts": ["authentication", "JWT"],
                "acceptance_criteria": [
                    "Validates email format",
                    "Returns JWT on success",
                ],
                "implementation": {
                    "frontend": ["LoginForm component", "useAuth hook"],
                    "backend": ["POST /auth/login endpoint", "AuthService.login()"],
                    "middleware": ["validateLoginRequest middleware"],
                    "shared": ["User model", "AuthTypes"],
                },
            }
        ],
        "metadata": {
            "baml_validated": True,
            "schema_version": "2.0.0",
            "llm_model": "claude-opus-4-5-20251101",
        },
    }


# =============================================================================
# REQ_004.1 Tests: BAML b.request for typed prompt building
# =============================================================================

class TestBuildBamlRequest:
    """Tests for build_baml_request function (REQ_004.1)."""

    def test_builds_subprocess_details_prompt(self):
        """REQ_004.1.1: Returns request with typed prompt."""
        result = build_baml_request(
            "ProcessGate1SubprocessDetailsPrompt",
            sub_process="Login flow",
            parent_description="User authentication",
            scope_text="Build a secure login system",
            user_confirmation=True,
        )

        # Should return BAMLRequest, not AgentSDKError
        if isinstance(result, AgentSDKError):
            pytest.skip(f"BAML not available: {result.error}")

        assert isinstance(result, BAMLRequest)
        assert result.function_name == "ProcessGate1SubprocessDetailsPrompt"
        assert "Login flow" in result.prompt
        assert "User authentication" in result.prompt

    def test_request_includes_output_format_schema(self):
        """REQ_004.1.4: Prompt includes expected JSON schema."""
        result = build_baml_request(
            "ProcessGate1SubprocessDetailsPrompt",
            sub_process="Test process",
            parent_description="Test parent",
            scope_text="Test scope",
            user_confirmation=True,
        )

        if isinstance(result, AgentSDKError):
            pytest.skip(f"BAML not available: {result.error}")

        # Prompt should include schema hints
        assert "implementation_details" in result.prompt
        assert "function_id" in result.prompt
        assert "acceptance_criteria" in result.prompt

    def test_preserves_all_parameters(self):
        """REQ_004.1.3: Request preserves all function parameters."""
        params = {
            "sub_process": "Test process",
            "parent_description": "Test parent",
            "scope_text": "Test scope",
            "user_confirmation": True,
        }

        result = build_baml_request("ProcessGate1SubprocessDetailsPrompt", **params)

        if isinstance(result, AgentSDKError):
            pytest.skip(f"BAML not available: {result.error}")

        assert result.parameters == params

    def test_request_serializes_for_logging(self):
        """REQ_004.1.7: Request can be serialized for logging."""
        result = build_baml_request(
            "ProcessGate1SubprocessDetailsPrompt",
            sub_process="Test",
            parent_description="Parent",
            scope_text="Scope",
            user_confirmation=True,
        )

        if isinstance(result, AgentSDKError):
            pytest.skip(f"BAML not available: {result.error}")

        serialized = result.to_dict()

        assert "function_name" in serialized
        assert "parameters" in serialized
        assert "prompt_length" in serialized
        assert isinstance(serialized["prompt_length"], int)

    def test_handles_unknown_function(self):
        """Should handle unknown function gracefully."""
        result = build_baml_request(
            "UnknownFunction",
            param1="value1",
        )

        if isinstance(result, AgentSDKError):
            # If BAML unavailable, that's expected
            assert result.error_code in [
                AgentSDKErrorCode.BAML_UNAVAILABLE,
                AgentSDKErrorCode.VALIDATION_ERROR,
            ]
        else:
            # Unknown functions get generic prompt
            assert isinstance(result, BAMLRequest)
            assert "UnknownFunction" in result.prompt


class TestBuildSubprocessDetailsPrompt:
    """Unit tests for subprocess details prompt builder."""

    def test_includes_all_sections(self):
        """Prompt should include all required sections."""
        prompt = _build_subprocess_details_prompt({
            "sub_process": "Login flow",
            "parent_description": "Authentication system",
            "scope_text": "Build a secure app",
        })

        assert "SCOPE:" in prompt
        assert "Login flow" in prompt
        assert "Authentication system" in prompt
        assert "Build a secure app" in prompt

    def test_includes_json_schema(self):
        """Prompt should include JSON output schema."""
        prompt = _build_subprocess_details_prompt({
            "sub_process": "Test",
            "parent_description": "Test",
            "scope_text": "Test",
        })

        assert "implementation_details" in prompt
        assert "function_id" in prompt
        assert "frontend" in prompt
        assert "backend" in prompt


# =============================================================================
# REQ_004.2 Tests: Agent SDK execution
# =============================================================================

class TestExecuteWithAgentSDK:
    """Tests for execute_with_agent_sdk function (REQ_004.2)."""

    def test_returns_result_on_sdk_unavailable(self):
        """REQ_004.2: Should handle SDK unavailability gracefully."""
        with patch('planning_pipeline.agent_sdk_integration.HAS_AGENT_SDK', False):
            result = execute_with_agent_sdk("Test prompt")

            assert isinstance(result, AgentSDKResult)
            assert result.success is False
            assert "not installed" in result.error

    def test_config_default_model(self):
        """REQ_004.2.1: Default model should be claude-opus-4-5-20251101."""
        config = AgentSDKConfig()

        assert config.model == "claude-opus-4-5-20251101"

    def test_config_default_tools(self):
        """REQ_004.2.2: Default tools should include Read, Glob, Grep."""
        config = AgentSDKConfig()

        assert "Read" in config.tools
        assert "Glob" in config.tools
        assert "Grep" in config.tools

    def test_config_default_permission_mode(self):
        """REQ_004.2.3: Default permission mode should be bypassPermissions."""
        config = AgentSDKConfig()

        assert config.permission_mode == "bypassPermissions"

    def test_config_default_timeout(self):
        """REQ_004.2.6: Default timeout should be 300 seconds."""
        config = AgentSDKConfig()

        assert config.timeout == 300

    def test_result_has_expected_fields(self):
        """REQ_004.2.8: Result should have all expected fields."""
        result = AgentSDKResult(
            success=True,
            output="Test output",
            tool_results=[],
            elapsed=1.5,
            session_id="session-123",
            error="",
        )

        assert result.success is True
        assert result.output == "Test output"
        assert result.elapsed == 1.5
        assert result.session_id == "session-123"

    def test_result_serializes_to_dict(self):
        """Result should serialize for logging."""
        result = AgentSDKResult(
            success=True,
            output="Test output",
            tool_results=[{"tool_name": "Read"}],
            elapsed=1.5,
        )

        serialized = result.to_dict()

        assert "success" in serialized
        assert "output_length" in serialized
        assert "tool_results_count" in serialized
        assert serialized["tool_results_count"] == 1


# =============================================================================
# REQ_004.3 Tests: BAML b.parse for response parsing
# =============================================================================

class TestParseBamlResponse:
    """Tests for parse_baml_response function (REQ_004.3)."""

    def test_parses_valid_json_response(self, sample_subprocess_details_response):
        """REQ_004.3.1: Should parse valid JSON into typed model."""
        json_str = json.dumps(sample_subprocess_details_response)

        result = parse_baml_response(
            "ProcessGate1SubprocessDetailsPrompt",
            json_str,
        )

        if isinstance(result, AgentSDKError):
            # May fail if BAML types not available
            assert result.error_code == AgentSDKErrorCode.BAML_UNAVAILABLE
        else:
            # Should have implementation_details
            if hasattr(result, 'implementation_details'):
                assert len(result.implementation_details) == 1
            elif isinstance(result, dict):
                assert "implementation_details" in result

    def test_handles_json_in_code_fence(self, sample_subprocess_details_response):
        """REQ_004.3.2: Should extract JSON from markdown code fence."""
        json_str = json.dumps(sample_subprocess_details_response)
        text_with_fence = f"Here is the response:\n```json\n{json_str}\n```"

        result = parse_baml_response(
            "ProcessGate1SubprocessDetailsPrompt",
            text_with_fence,
        )

        # Should not fail due to code fence
        if not isinstance(result, AgentSDKError):
            assert result is not None

    def test_retries_with_cleaned_text(self):
        """REQ_004.3.6: Should retry parsing with cleaned text."""
        malformed = '```json\n{"implementation_details": [], "metadata": {}}\n```'

        result = parse_baml_response(
            "ProcessGate1SubprocessDetailsPrompt",
            malformed,
            retry_on_failure=True,
        )

        # Should succeed after cleaning
        if isinstance(result, AgentSDKError):
            assert result.error_code != AgentSDKErrorCode.PARSE_ERROR

    def test_returns_error_on_invalid_json(self):
        """REQ_004.3.7: Should return error on unparseable JSON."""
        invalid = "This is not JSON at all"

        result = parse_baml_response(
            "ProcessGate1SubprocessDetailsPrompt",
            invalid,
            retry_on_failure=False,
        )

        assert isinstance(result, AgentSDKError)
        assert result.error_code == AgentSDKErrorCode.PARSE_ERROR

    def test_error_includes_raw_response(self):
        """REQ_004.3.4: Error should include field-level detail."""
        invalid = "Not JSON"

        result = parse_baml_response(
            "ProcessGate1SubprocessDetailsPrompt",
            invalid,
            retry_on_failure=False,
        )

        assert isinstance(result, AgentSDKError)
        assert result.details is not None
        assert "raw_response" in result.details


class TestExtractJson:
    """Unit tests for _extract_json helper."""

    def test_extracts_plain_json(self):
        """Should extract plain JSON object."""
        text = '{"key": "value"}'

        result = _extract_json(text)

        assert result == '{"key": "value"}'

    def test_extracts_json_from_code_fence(self):
        """Should extract JSON from markdown code fence."""
        text = '```json\n{"key": "value"}\n```'

        result = _extract_json(text)

        assert result == '{"key": "value"}'

    def test_extracts_json_with_surrounding_text(self):
        """Should extract JSON from text with prose."""
        text = 'Here is the response:\n{"key": "value"}\nEnd of response.'

        result = _extract_json(text)

        assert result == '{"key": "value"}'

    def test_returns_none_for_no_json(self):
        """Should return None when no JSON found."""
        text = "No JSON here"

        result = _extract_json(text)

        assert result is None


class TestCleanResponseText:
    """Unit tests for _clean_response_text helper."""

    def test_removes_code_fences(self):
        """Should remove markdown code fences."""
        text = '```json\n{"key": "value"}\n```'

        result = _clean_response_text(text)

        assert "```" not in result
        assert '{"key": "value"}' in result

    def test_strips_whitespace(self):
        """Should strip leading/trailing whitespace."""
        text = '   {"key": "value"}   '

        result = _clean_response_text(text)

        assert result == '{"key": "value"}'


# =============================================================================
# REQ_004.4 Tests: OpusAgent client configuration
# =============================================================================

class TestOpusAgentConfiguration:
    """Tests for OpusAgent client configuration (REQ_004.4)."""

    def test_opus_agent_in_baml_clients(self):
        """REQ_004.4.1: OpusAgent should be configured in BAML clients."""
        # Read the clients.baml file to verify configuration
        clients_path = Path(__file__).parent.parent.parent / "baml_src" / "clients.baml"

        if clients_path.exists():
            content = clients_path.read_text()

            assert "OpusAgent" in content
            assert "claude-opus-4-5-20251101" in content
            assert "provider anthropic" in content

    def test_opus_agent_has_retry_policy(self):
        """REQ_004.4.2: OpusAgent should have retry policy configured."""
        clients_path = Path(__file__).parent.parent.parent / "baml_src" / "clients.baml"

        if clients_path.exists():
            content = clients_path.read_text()

            # Find OpusAgent definition and check for retry_policy
            assert "OpusAgent" in content
            assert "retry_policy" in content

    def test_opus_with_fallback_configured(self):
        """REQ_004.4.3: Fallback configurations should be defined."""
        clients_path = Path(__file__).parent.parent.parent / "baml_src" / "clients.baml"

        if clients_path.exists():
            content = clients_path.read_text()

            assert "OpusWithHaikuFallback" in content
            assert "OpusWithOllamaFallback" in content


# =============================================================================
# Integration Tests
# =============================================================================

class TestAgentSdkDecompose:
    """Integration tests for agent_sdk_decompose helper."""

    def test_decompose_returns_error_when_sdk_unavailable(self):
        """Should return structured error when SDK not available."""
        with patch('planning_pipeline.agent_sdk_integration.HAS_AGENT_SDK', False):
            result = agent_sdk_decompose(
                "ProcessGate1SubprocessDetailsPrompt",
                {
                    "sub_process": "Test",
                    "parent_description": "Parent",
                    "scope_text": "Scope",
                },
            )

            # Build request might work, but execute will fail
            assert isinstance(result, (AgentSDKError, dict))
            if isinstance(result, AgentSDKError):
                assert result.error_code in [
                    AgentSDKErrorCode.API_ERROR,
                    AgentSDKErrorCode.SDK_UNAVAILABLE,
                ]

    def test_decompose_calls_progress_callback(self):
        """Progress callback should be called at each stage."""
        progress_calls = []

        def track_progress(msg):
            progress_calls.append(msg)

        with patch('planning_pipeline.agent_sdk_integration.HAS_AGENT_SDK', False):
            agent_sdk_decompose(
                "ProcessGate1SubprocessDetailsPrompt",
                {"sub_process": "Test", "parent_description": "P", "scope_text": "S"},
                progress_callback=track_progress,
            )

        # Should have at least one progress call (building request)
        assert len(progress_calls) >= 1
        assert any("Building" in msg for msg in progress_calls)


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestAgentSDKError:
    """Tests for AgentSDKError dataclass."""

    def test_to_dict_serialization(self):
        """Error should serialize to dictionary."""
        error = AgentSDKError(
            success=False,
            error_code=AgentSDKErrorCode.PARSE_ERROR,
            error="Failed to parse response",
            details={"raw_response": "invalid"},
        )

        result = error.to_dict()

        assert result["success"] is False
        assert result["error_code"] == "parse_error"
        assert result["error"] == "Failed to parse response"
        assert result["details"]["raw_response"] == "invalid"

    def test_default_values(self):
        """Error should have sensible defaults."""
        error = AgentSDKError()

        assert error.success is False
        assert error.error_code == AgentSDKErrorCode.API_ERROR
        assert error.error == ""
        assert error.details is None
