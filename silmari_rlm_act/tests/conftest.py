"""Shared fixtures for silmari_rlm_act tests."""

import pytest
from datetime import datetime


@pytest.fixture
def sample_timestamp() -> datetime:
    """Provide a consistent timestamp for tests."""
    return datetime(2026, 1, 5, 10, 30, 0)


@pytest.fixture
def sample_artifacts() -> list[str]:
    """Provide sample artifact paths for tests."""
    return [
        "/home/user/project/thoughts/research/2026-01-05-topic.md",
        "/home/user/project/thoughts/plans/2026-01-05-plan.md",
    ]


@pytest.fixture
def sample_errors() -> list[str]:
    """Provide sample error messages for tests."""
    return [
        "File not found: src/main.py",
        "Test failed: test_integration.py::test_login",
    ]
