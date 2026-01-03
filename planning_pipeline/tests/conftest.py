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
    """Complete mock of BAML client for unit tests."""
    mock_b = MagicMock()
    mock_b.ProcessGate1InitialExtractionPrompt.return_value = mock_baml_initial_extraction
    mock_b.ProcessGate1SubprocessDetailsPrompt.return_value = mock_baml_subprocess_details
    return mock_b


@pytest.fixture
def patch_baml_client(mock_baml_client):
    """Context manager to patch BAML client import."""
    with patch.dict("sys.modules", {"baml_client": MagicMock(b=mock_baml_client)}):
        with patch("planning_pipeline.decomposition.b", mock_baml_client):
            with patch("planning_pipeline.decomposition.BAML_AVAILABLE", True):
                yield mock_baml_client


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

    Created: thoughts/shared/research/2025-01-01-test-research.md

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

    Plan written to thoughts/shared/plans/2025-01-01-feature/00-overview.md

    The plan includes 3 phases for implementation.
    """


@pytest.fixture
def sample_phase_output():
    """Sample Claude output containing phase file paths."""
    return """
    Created phase files:
    - thoughts/shared/plans/2025-01-01-feature/01-phase-1-setup.md
    - thoughts/shared/plans/2025-01-01-feature/02-phase-2-impl.md
    - thoughts/shared/plans/2025-01-01-feature/03-phase-3-test.md
    """
