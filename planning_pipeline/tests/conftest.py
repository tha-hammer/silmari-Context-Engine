"""Pytest configuration and fixtures for planning pipeline tests."""

import pytest
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from unittest.mock import MagicMock, patch


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")


# ==============================================================================
# MOCK BAML TYPES - Mirror baml_client/types.py structure
# ==============================================================================


@dataclass
class MockImplementationComponents:
    """Mock for baml_client.types.ImplementationComponents."""

    frontend: List[str] = field(default_factory=list)
    backend: List[str] = field(default_factory=list)
    middleware: List[str] = field(default_factory=list)
    shared: List[str] = field(default_factory=list)


@dataclass
class MockImplementationDetail:
    """Mock for baml_client.types.ImplementationDetail."""

    function_id: str
    description: str
    related_concepts: List[str]
    acceptance_criteria: List[str]
    implementation: MockImplementationComponents


@dataclass
class MockRequirement:
    """Mock for baml_client.types.Requirement."""

    description: str
    sub_processes: List[str]
    related_concepts: Optional[List[str]] = None


@dataclass
class MockResponseMetadata:
    """Mock for baml_client.types.ResponseMetadata."""

    timestamp: str = "2026-01-02T00:00:00Z"
    model: str = "test-model"
    schema_version: str = "1.0"
    dynamic_types_applied: List[str] = field(default_factory=list)
    groups_processed: int = 0
    requirements_analyzed: int = 0


@dataclass
class MockInitialExtractionResponse:
    """Mock for baml_client.types.InitialExtractionResponse."""

    requirements: List[MockRequirement]
    metadata: MockResponseMetadata = field(default_factory=MockResponseMetadata)


@dataclass
class MockSubprocessDetailsResponse:
    """Mock for baml_client.types.SubprocessDetailsResponse."""

    implementation_details: List[MockImplementationDetail]
    metadata: MockResponseMetadata = field(default_factory=MockResponseMetadata)


# ==============================================================================
# BAML MOCK FIXTURES
# ==============================================================================


@pytest.fixture
def mock_baml_initial_extraction():
    """Mock response for b.ProcessGate1InitialExtractionPrompt."""
    return MockInitialExtractionResponse(
        requirements=[
            MockRequirement(
                description="User Authentication System",
                sub_processes=[
                    "Login flow implementation",
                    "Session management",
                    "Password recovery",
                ],
                related_concepts=["security", "user-management"],
            )
        ]
    )


@pytest.fixture
def mock_baml_subprocess_details():
    """Mock response for b.ProcessGate1SubprocessDetailsPrompt."""
    return MockSubprocessDetailsResponse(
        implementation_details=[
            MockImplementationDetail(
                function_id="AUTH_001",
                description="Implement login form with email/password",
                related_concepts=["forms", "validation"],
                acceptance_criteria=[
                    "Form validates email format",
                    "Shows inline errors on invalid input",
                    "Submits to /api/auth/login",
                ],
                implementation=MockImplementationComponents(
                    frontend=["LoginForm", "AuthContext"],
                    backend=["AuthService.login", "UserRepository.findByEmail"],
                    middleware=["validateCredentials"],
                    shared=["User", "AuthResult"],
                ),
            )
        ]
    )


@pytest.fixture
def mock_baml_client(mock_baml_initial_extraction, mock_baml_subprocess_details):
    """Complete mock of BAML client for unit tests (legacy)."""
    mock_b = MagicMock()
    mock_b.ProcessGate1InitialExtractionPrompt.return_value = mock_baml_initial_extraction
    mock_b.ProcessGate1SubprocessDetailsPrompt.return_value = mock_baml_subprocess_details
    return mock_b


@pytest.fixture
def mock_claude_sdk_response():
    """Mock response from run_claude_sync for requirement extraction."""
    return {
        "success": True,
        "output": """{
    "requirements": [
        {
            "description": "User Authentication System",
            "sub_processes": [
                "Login flow implementation",
                "Session management",
                "Password recovery"
            ]
        }
    ]
}""",
        "error": "",
        "elapsed": 1.5
    }


@pytest.fixture
def mock_claude_expansion_response():
    """Mock response from run_claude_sync for requirement expansion (second call)."""
    return {
        "success": True,
        "output": """{
    "implementation_details": [
        {
            "function_id": "Auth.login",
            "description": "Implement login form with email/password",
            "related_concepts": ["forms", "validation"],
            "acceptance_criteria": [
                "Form validates email format",
                "Shows inline errors on invalid input",
                "Submits to /api/auth/login"
            ],
            "implementation": {
                "frontend": ["LoginForm", "AuthContext"],
                "backend": ["AuthService.login", "UserRepository.findByEmail"],
                "middleware": ["validateCredentials"],
                "shared": ["User", "AuthResult"]
            }
        },
        {
            "function_id": "Session.manage",
            "description": "Session management and token handling",
            "related_concepts": ["jwt", "cookies"],
            "acceptance_criteria": [
                "Sessions persist across page reloads",
                "Sessions expire after inactivity"
            ],
            "implementation": {
                "frontend": ["SessionProvider"],
                "backend": ["SessionService"],
                "middleware": [],
                "shared": ["Session"]
            }
        },
        {
            "function_id": "Auth.recover",
            "description": "Password recovery via email",
            "related_concepts": ["email", "security"],
            "acceptance_criteria": [
                "User can request password reset",
                "Reset link expires after 1 hour"
            ],
            "implementation": {
                "frontend": ["PasswordResetForm"],
                "backend": ["PasswordResetService", "EmailService"],
                "middleware": [],
                "shared": ["ResetToken"]
            }
        }
    ]
}""",
        "error": "",
        "elapsed": 2.0
    }


@pytest.fixture
def mock_claude_expansion_response_limited():
    """Mock response with only 2 implementation_details for max_sub_processes tests."""
    return {
        "success": True,
        "output": """{
    "implementation_details": [
        {
            "function_id": "Auth.login",
            "description": "Implement login form with email/password",
            "related_concepts": ["forms", "validation"],
            "acceptance_criteria": ["Form validates email format"],
            "implementation": {
                "frontend": ["LoginForm"],
                "backend": ["AuthService.login"],
                "middleware": [],
                "shared": []
            }
        },
        {
            "function_id": "Session.manage",
            "description": "Session management",
            "related_concepts": ["jwt"],
            "acceptance_criteria": ["Sessions persist"],
            "implementation": {
                "frontend": ["SessionProvider"],
                "backend": ["SessionService"],
                "middleware": [],
                "shared": []
            }
        }
    ]
}""",
        "error": "",
        "elapsed": 1.0
    }


@pytest.fixture
def patch_baml_client(mock_claude_sdk_response, mock_claude_expansion_response, mock_claude_expansion_response_limited):
    """Context manager to patch run_claude_sync for decomposition tests.

    First call returns initial extraction (requirements with sub_processes).
    Subsequent calls return expansion (implementation_details).

    The mock supports:
    - Setting return_value to override side_effect for error testing
    - Side effect that returns extraction first, then expansion

    Note: If a test sets mock_run.return_value after fixture setup, that value
    will be returned (side_effect checks for this override).
    """
    call_count = [0]  # Use list to allow mutation in nested function
    override_return = [None]  # Allow tests to override the return

    def side_effect(*args, **kwargs):
        # Check if a test has set an override return value
        if override_return[0] is not None:
            return override_return[0]
        call_count[0] += 1
        if call_count[0] == 1:
            return mock_claude_sdk_response
        return mock_claude_expansion_response

    with patch("planning_pipeline.decomposition.run_claude_sync") as mock_run:
        mock_run.side_effect = side_effect

        # Store the original return_value setter so tests can override
        original_return_value = None

        def set_return_value(value):
            nonlocal original_return_value
            original_return_value = value
            override_return[0] = value

        # Make return_value settable
        type(mock_run).return_value = property(
            lambda self: override_return[0],
            lambda self, value: set_return_value(value)
        )

        yield mock_run


@pytest.fixture
def project_path():
    """Return the root project path."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def sample_research_output():
    """Sample Claude output containing a research file path."""
    return """
    Research complete!

    I've analyzed the codebase and created a research document.

    Created: thoughts/searchable/research/2025-01-01-test-research.md

    The document contains findings about the project structure.

    ## Open Questions
    - What authentication method should we use?
    - Should we support multiple databases?
    """


@pytest.fixture
def sample_plan_output():
    """Sample Claude output containing a plan file path."""
    return """
    Planning complete!

    Plan written to thoughts/searchable/plans/2025-01-01-feature/00-overview.md

    The plan includes 3 phases for implementation.
    """


@pytest.fixture
def sample_phase_output():
    """Sample Claude output containing phase file paths."""
    return """
    Created phase files:
    - thoughts/searchable/plans/2025-01-01-feature/01-phase-1-setup.md
    - thoughts/searchable/plans/2025-01-01-feature/02-phase-2-impl.md
    - thoughts/searchable/plans/2025-01-01-feature/03-phase-3-test.md
    """
