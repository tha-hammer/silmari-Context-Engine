"""Pytest configuration and fixtures for planning pipeline tests."""

import pytest
from pathlib import Path


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")


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
