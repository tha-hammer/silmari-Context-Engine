# Phase 4: BAML-Based Requirement Decomposition

## Overview

Implement the core decomposition logic that takes research content and produces a structured `RequirementHierarchy` using BAML functions for LLM-powered analysis. Includes CLI fallback for environments without BAML.

## Dependencies

- **Requires**: Phase 1 (Data Models), BAML client (`baml_client/`)
- **Blocks**: Phase 5 (Step Integration)

## Human-Testable Function

```python
# After implementation, verify with:
from planning_pipeline.decomposition import decompose_requirements

research_content = """
# Research: User Session Tracking

We need to implement session tracking for the dashboard.
Key features:
- Track session start/end times
- Monitor active users
- Cleanup stale sessions
"""

result = decompose_requirements(research_content)
if isinstance(result, dict):
    print(f"Error: {result.get('error')}")
else:
    print(f"Found {len(result.requirements)} requirements")
    for req in result.requirements:
        print(f"  - {req.id}: {req.description}")
```

## Changes Required

### New Files

| File | Purpose |
|------|---------|
| `planning_pipeline/decomposition.py` | BAML-based decomposition logic |
| `planning_pipeline/tests/test_decomposition.py` | Unit and integration tests |

### planning_pipeline/decomposition.py (new file)

```python
# planning_pipeline/decomposition.py:1-150
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Union, Dict, Any

class DecompositionErrorCode(Enum):
    """Error codes for decomposition failures."""
    EMPTY_CONTENT = "empty_content"
    BAML_UNAVAILABLE = "baml_unavailable"
    BAML_API_ERROR = "baml_api_error"
    INVALID_JSON = "invalid_json"
    CONVERSION_ERROR = "conversion_error"
    CLI_FALLBACK_ERROR = "cli_fallback_error"

@dataclass
class DecompositionError:
    """Structured error response from decomposition."""
    success: bool = False
    error_code: DecompositionErrorCode = DecompositionErrorCode.BAML_API_ERROR
    error: str = ""
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "error_code": self.error_code.value,
            "error": self.error,
            "details": self.details
        }

@dataclass
class DecompositionConfig:
    max_sub_processes: int = 5
    min_sub_processes: int = 2
    include_acceptance_criteria: bool = True
    expand_dimensions: bool = False

def decompose_requirements(
    research_content: str,
    config: Optional[DecompositionConfig] = None
) -> Union[RequirementHierarchy, DecompositionError]:
    """Decompose research content into requirement hierarchy using BAML.

    Steps:
    1. Validate input (non-empty)
    2. Call b.ProcessGate1InitialExtractionPrompt for top-level requirements
    3. For each requirement, call b.ProcessGate1SubprocessDetailsPrompt
    4. Build RequirementHierarchy from responses
    5. Return hierarchy or DecompositionError
    """

def decompose_requirements_cli_fallback(
    research_content: str,
    config: Optional[DecompositionConfig] = None
) -> Union[RequirementHierarchy, DecompositionError]:
    """Fallback using Claude CLI when BAML unavailable."""

def _convert_json_to_hierarchy(data: dict) -> RequirementHierarchy:
    """Convert raw JSON response to RequirementHierarchy."""
```

### planning_pipeline/tests/test_decomposition.py (new file)

```python
# planning_pipeline/tests/test_decomposition.py:1-100

class TestDecomposeRequirements:
    # test_returns_hierarchy_from_research (mocked BAML)
    # test_returns_error_for_empty_research
    # test_sub_processes_become_children
    # @pytest.mark.integration: test_real_baml_call_returns_valid_structure

class TestDecompositionProperties:
    # test_decomposition_never_crashes (property-based with mocked BAML)
```

## TDD Cycle

### Red Phase
```bash
pytest planning_pipeline/tests/test_decomposition.py -v
# Expected: ImportError (decomposition module doesn't exist)
```

### Green Phase
```bash
# Implement minimal decomposition.py with mocked BAML
pytest planning_pipeline/tests/test_decomposition.py -v -k "not integration"
# Expected: Unit tests pass
```

### Integration Phase
```bash
# Test with real BAML (requires API key)
pytest planning_pipeline/tests/test_decomposition.py -v -m integration
# Expected: Integration tests pass
```

### Refactor Phase
```bash
# Add CLI fallback, run all tests
pytest planning_pipeline/tests/test_decomposition.py -v
```

## Success Criteria

### Automated
- [x] `pytest planning_pipeline/tests/test_decomposition.py -v -k "not integration"` passes (unit tests)
- [x] Mocked tests complete in < 1 second: `pytest --durations=10`
- [x] Property test finds no crashes with random input

### Manual (requires ANTHROPIC_API_KEY)
- [ ] Real BAML call produces valid hierarchy with 1+ requirements
- [x] CLI fallback works when BAML unavailable
- [x] Error messages are informative for invalid input

## BAML Functions Used

| Function | Purpose | Location |
|----------|---------|----------|
| `b.ProcessGate1InitialExtractionPrompt` | Extract top-level requirements | `baml_src/functions.baml:408` |
| `b.ProcessGate1SubprocessDetailsPrompt` | Get subprocess implementation details | `baml_src/functions.baml:500` |

## Mock Response Structure

```python
# Initial extraction response
{
    "requirements": [
        {
            "description": "User Authentication System",
            "sub_processes": [
                "Login flow implementation",
                "Session management",
                "Password recovery",
            ]
        }
    ]
}

# Subprocess details response
{
    "implementation_details": [
        {
            "description": "Implement login form",
            "acceptance_criteria": ["Form validates email", "Shows errors"],
            "implementation": {
                "frontend": ["LoginForm"],
                "backend": ["AuthService.login"],
                "middleware": [],
                "shared": ["User"]
            }
        }
    ]
}
```

## Error Handling

| Error Condition | Error Code | Response |
|----------------|------------|----------|
| Empty research content | `EMPTY_CONTENT` | `DecompositionError(error_code=EMPTY_CONTENT, error="Research content cannot be empty")` |
| BAML client not importable | `BAML_UNAVAILABLE` | `DecompositionError(error_code=BAML_UNAVAILABLE, error="BAML client not available")` |
| BAML API exception | `BAML_API_ERROR` | `DecompositionError(error_code=BAML_API_ERROR, error="<exception message>")` |
| Invalid JSON from CLI fallback | `INVALID_JSON` | `DecompositionError(error_code=INVALID_JSON, error="Invalid JSON: <parse error>")` |
| Failed to convert response to hierarchy | `CONVERSION_ERROR` | `DecompositionError(error_code=CONVERSION_ERROR, error="<details>")` |
| CLI fallback subprocess failed | `CLI_FALLBACK_ERROR` | `DecompositionError(error_code=CLI_FALLBACK_ERROR, error="<details>")` |

## Mock Strategy for Unit Tests

### Fixture: mock_baml_client

```python
# planning_pipeline/tests/conftest.py

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import List

# Mock BAML response types (mirrors baml_client/types.py structure)
@dataclass
class MockRequirement:
    description: str
    sub_processes: List[str]
    related_concepts: List[str] = None

@dataclass
class MockImplementationComponents:
    frontend: List[str]
    backend: List[str]
    middleware: List[str]
    shared: List[str]

@dataclass
class MockImplementationDetail:
    function_id: str
    description: str
    related_concepts: List[str]
    acceptance_criteria: List[str]
    implementation: MockImplementationComponents

@dataclass
class MockInitialExtractionResponse:
    requirements: List[MockRequirement]

@dataclass
class MockSubprocessDetailsResponse:
    implementation_details: List[MockImplementationDetail]


@pytest.fixture
def mock_baml_initial_extraction():
    """Mock for b.ProcessGate1InitialExtractionPrompt."""
    return MockInitialExtractionResponse(
        requirements=[
            MockRequirement(
                description="User Authentication System",
                sub_processes=[
                    "Login flow implementation",
                    "Session management",
                    "Password recovery",
                ],
                related_concepts=["security", "user-management"]
            )
        ]
    )


@pytest.fixture
def mock_baml_subprocess_details():
    """Mock for b.ProcessGate1SubprocessDetailsPrompt."""
    return MockSubprocessDetailsResponse(
        implementation_details=[
            MockImplementationDetail(
                function_id="AUTH_001",
                description="Implement login form with email/password",
                related_concepts=["forms", "validation"],
                acceptance_criteria=[
                    "Form validates email format",
                    "Shows inline errors on invalid input",
                    "Submits to /api/auth/login"
                ],
                implementation=MockImplementationComponents(
                    frontend=["LoginForm", "AuthContext"],
                    backend=["AuthService.login", "UserRepository.findByEmail"],
                    middleware=["validateCredentials"],
                    shared=["User", "AuthResult"]
                )
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
    with patch.dict('sys.modules', {'baml_client': MagicMock(b=mock_baml_client)}):
        with patch('planning_pipeline.decomposition.b', mock_baml_client):
            with patch('planning_pipeline.decomposition.BAML_AVAILABLE', True):
                yield mock_baml_client
```

### Using Mocks in Tests

```python
# planning_pipeline/tests/test_decomposition.py

import pytest
from planning_pipeline.decomposition import decompose_requirements, DecompositionErrorCode
from planning_pipeline.models import RequirementHierarchy

class TestDecomposeRequirements:

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

        assert result.error_code == DecompositionErrorCode.EMPTY_CONTENT
        patch_baml_client.ProcessGate1InitialExtractionPrompt.assert_not_called()

    def test_baml_api_error_returns_structured_error(self, patch_baml_client):
        """BAML exceptions should be caught and wrapped."""
        patch_baml_client.ProcessGate1InitialExtractionPrompt.side_effect = Exception("API rate limit")

        result = decompose_requirements("Some research content")

        assert result.error_code == DecompositionErrorCode.BAML_API_ERROR
        assert "API rate limit" in result.error


@pytest.mark.integration
class TestDecomposeRequirementsIntegration:
    """Integration tests - require ANTHROPIC_API_KEY."""

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
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
```

### Property-Based Test with Mocks

```python
from hypothesis import given, strategies as st, settings

class TestDecompositionProperties:

    @given(research=st.text(min_size=10, max_size=1000))
    @settings(max_examples=50)
    def test_decomposition_never_crashes(self, research, patch_baml_client):
        """Decomposition should never raise - always return Hierarchy or Error."""
        result = decompose_requirements(research)

        assert isinstance(result, (RequirementHierarchy, DecompositionError))
```

## Implementation Notes

1. Import BAML client conditionally with try/except
2. Set `BAML_AVAILABLE = False` if import fails
3. Truncate research context to 500 chars for subprocess detail calls
4. Use `config.max_sub_processes` to limit children (default 5)
5. CLI fallback extracts JSON from Claude output (find first `{` to last `}`)
6. ID format: `REQ_{idx:03d}` for parents, `REQ_{idx:03d}.{sub_idx}` for children
7. Use `DecompositionError` dataclass instead of raw dicts for type safety
8. All unit tests should use `patch_baml_client` fixture - no real API calls
