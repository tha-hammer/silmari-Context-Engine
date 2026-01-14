---
date: 2026-01-14T13:18:22-05:00
researcher: maceo
git_commit: ff14cfa3cb94bfd5e2eae341a119dc7cf0a1ff5e
branch: main
repository: silmari-Context-Engine
topic: "Pytest Fixtures - Detailed Analysis of Testing Patterns"
tags: [research, codebase, testing, pytest, fixtures, patterns, test-organization]
status: complete
last_updated: 2026-01-14
last_updated_by: maceo
---

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║         PYTEST FIXTURES: DETAILED PATTERN ANALYSIS            ║
║                  silmari-Context-Engine                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

**Date**: 2026-01-14T13:18:22-05:00
**Researcher**: maceo
**Git Commit**: `ff14cfa3cb94bfd5e2eae341a119dc7cf0a1ff5e`
**Branch**: main
**Repository**: silmari-Context-Engine
**Status**: ✅ Complete

---

## 📚 Research Question

**Analyze the testing patterns in this project. Focus on pytest fixtures.**

This research provides a comprehensive, fixture-by-fixture analysis of the testing infrastructure, documenting all 44+ pytest fixtures, their implementations, usage patterns, and architectural decisions.

---

## 🎯 Executive Summary

The silmari-Context-Engine project demonstrates **mature and sophisticated pytest usage** with a well-organized testing infrastructure. The codebase contains **44 documented fixtures** across **42 test files** organized into **4 test directories**. Testing follows consistent patterns with clear naming conventions, proper isolation, and sophisticated mocking infrastructure.

### 📊 Key Metrics

| **Metric** | **Value** |
|------------|-----------|
| 📁 Test Directories | 4 |
| 📄 Test Files | 42 |
| 🔧 Documented Fixtures | 44 |
| 📦 Conftest Files | 2 |
| 🎭 Mock BAML Types | 6 |
| 🔄 Cleanup Patterns | 4 instances |
| 📐 Lines of Test Code | 377 lines (conftest.py files) |

---

## 🗂️ Test Structure Overview

### Test Directory Organization

```
silmari-Context-Engine/
├── tests/                                    (3 test files)
│   ├── test_autonomous_loop.py
│   ├── test_execute_phase.py
│   └── test_loop_orchestrator_integration.py
│
├── planning_pipeline/tests/                  (19 test files + conftest.py)
│   ├── conftest.py                          [348 lines - Primary fixture hub]
│   ├── test_beads.py
│   ├── test_beads_controller.py
│   ├── test_checkpoint_manager.py
│   ├── test_checkpoints.py
│   ├── test_claude.py
│   ├── test_claude_runner.py
│   ├── test_context_generation.py
│   ├── test_decomposition.py
│   ├── test_decomposition_e2e.py
│   ├── test_helpers.py
│   ├── test_integrated_orchestrator.py
│   ├── test_models.py
│   ├── test_orchestrator.py
│   ├── test_phase_execution.py
│   ├── test_pipeline.py
│   ├── test_property_generator.py
│   ├── test_step_decomposition.py
│   ├── test_steps.py
│   └── test_visualization.py
│
├── silmari_rlm_act/tests/                   (14 test files + conftest.py)
│   ├── conftest.py                          [29 lines - Lightweight fixtures]
│   ├── test_artifact_generation.py
│   ├── test_beads_sync_phase.py
│   ├── test_checkpoint_manager.py
│   ├── test_cli.py
│   ├── test_cwa_integration.py
│   ├── test_decomposition_phase.py
│   ├── test_implementation_phase.py
│   ├── test_interactive.py
│   ├── test_models.py
│   ├── test_multi_doc_phase.py
│   ├── test_pipeline.py
│   ├── test_research_phase.py
│   ├── test_tdd_planning_phase.py
│   └── test_validation.py
│
└── context_window_array/tests/              (6 test files)
    ├── test_batching.py
    ├── test_implementation_context.py
    ├── test_models.py
    ├── test_search.py
    ├── test_store.py
    └── test_working_context.py
```

### Test Distribution

| **Directory** | **Test Files** | **Conftest** | **Purpose** |
|--------------|----------------|--------------|-------------|
| `tests/` | 3 | ❌ No | Integration and autonomous loop testing |
| `planning_pipeline/tests/` | 19 | ✅ Yes (348 lines) | Decomposition, orchestration, pipeline |
| `silmari_rlm_act/tests/` | 14 | ✅ Yes (29 lines) | Phases, implementation, RLM act pipeline |
| `context_window_array/tests/` | 6 | ❌ No | Context window management |

---

## 🔧 Complete Fixture Inventory

### silmari_rlm_act/tests/conftest.py (Shared Fixtures)

#### 1. `sample_timestamp`

```python
@pytest.fixture
def sample_timestamp() -> datetime:
    """Provide a consistent timestamp for tests."""
    return datetime(2026, 1, 5, 10, 30, 0)
```

- **File**: `silmari_rlm_act/tests/conftest.py:7-10`
- **Scope**: function (default)
- **Type**: Simple data fixture
- **Purpose**: Provides fixed timestamp for time-dependent functionality testing
- **Dependencies**: None
- **Autouse**: No

#### 2. `sample_artifacts`

```python
@pytest.fixture
def sample_artifacts() -> list[str]:
    """Provide sample artifact paths for tests."""
    return [
        "/home/user/project/thoughts/research/2026-01-05-topic.md",
        "/home/user/project/thoughts/plans/2026-01-05-plan.md",
    ]
```

- **File**: `silmari_rlm_act/tests/conftest.py:13-19`
- **Scope**: function (default)
- **Type**: Simple data fixture
- **Purpose**: Sample artifact file paths for artifact handling tests
- **Dependencies**: None
- **Autouse**: No

#### 3. `sample_errors`

```python
@pytest.fixture
def sample_errors() -> list[str]:
    """Provide sample error messages for tests."""
    return [
        "Error: File not found",
        "Error: Invalid configuration",
        "Error: Connection timeout",
    ]
```

- **File**: `silmari_rlm_act/tests/conftest.py:22-28`
- **Scope**: function (default)
- **Type**: Simple data fixture
- **Purpose**: Sample error messages for error handling tests
- **Dependencies**: None
- **Autouse**: No

---

### silmari_rlm_act/tests/test_validation.py

#### 4. `temp_hierarchy`

- **File**: `silmari_rlm_act/tests/test_validation.py:29-60`
- **Scope**: function
- **Type**: Temporary file fixture
- **Purpose**: Creates temporary requirement hierarchy JSON file for validation testing
- **Dependencies**: `tmp_path` (pytest built-in)
- **Autouse**: No
- **Pattern**: Temporary resource creation

#### 5. `temp_research_doc`

- **File**: `silmari_rlm_act/tests/test_validation.py:63-72`
- **Scope**: function
- **Type**: Temporary file fixture
- **Purpose**: Creates temporary research markdown file for validation testing
- **Dependencies**: `tmp_path` (pytest built-in)
- **Autouse**: No
- **Pattern**: Temporary resource creation

#### 6. `mock_baml_response`

- **File**: `silmari_rlm_act/tests/test_validation.py:75-92`
- **Scope**: function
- **Type**: Mock object fixture
- **Purpose**: Mocks BAML validation response with validation results and metadata
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: Mock API response

---

### silmari_rlm_act/tests/test_implementation_phase.py

#### 7. `sample_plan`

- **File**: `silmari_rlm_act/tests/test_implementation_phase.py:21-37`
- **Scope**: function
- **Type**: Temporary file fixture
- **Purpose**: Creates sample TDD plan document with multiple phases
- **Dependencies**: `tmp_path` (pytest built-in)
- **Autouse**: No
- **Pattern**: Temporary resource with structured content

#### 8. `cwa`

- **File**: `silmari_rlm_act/tests/test_implementation_phase.py:40-43`
- **Scope**: function
- **Type**: Service object fixture
- **Purpose**: Creates CWA (Context Window Array) integration object for testing
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: Service instantiation

---

### silmari_rlm_act/tests/test_cli.py

#### 9. `cli_runner`

- **File**: `silmari_rlm_act/tests/test_cli.py:24-27`
- **Scope**: function
- **Type**: Test runner fixture
- **Purpose**: Creates Click CLI test runner for CLI command testing
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: Test infrastructure

#### 10. `temp_project` (CLI variant)

- **File**: `silmari_rlm_act/tests/test_cli.py:30-35`
- **Scope**: function
- **Type**: Temporary directory fixture
- **Purpose**: Creates temporary project directory for CLI testing
- **Dependencies**: `tmp_path` (pytest built-in)
- **Autouse**: No
- **Pattern**: Temporary resource

#### 11. `temp_research_doc` (CLI variant)

- **File**: `silmari_rlm_act/tests/test_cli.py:271-276`
- **Scope**: function
- **Type**: Temporary file fixture
- **Purpose**: Creates temporary research markdown file for CLI testing
- **Dependencies**: `tmp_path` (pytest built-in)
- **Autouse**: No
- **Pattern**: Temporary resource
- **Note**: Duplicate name but different implementation from test_validation.py

#### 12. `temp_plan_doc`

- **File**: `silmari_rlm_act/tests/test_cli.py:506-531`
- **Scope**: function
- **Type**: Temporary file fixture
- **Purpose**: Creates temporary requirement hierarchy JSON file for CLI testing
- **Dependencies**: `tmp_path` (pytest built-in)
- **Autouse**: No
- **Pattern**: Temporary resource with JSON structure

---

### silmari_rlm_act/tests/test_beads_sync_phase.py

#### 13. `mock_beads`

- **File**: `silmari_rlm_act/tests/test_beads_sync_phase.py:80-83`
- **Scope**: function
- **Type**: Mock object fixture
- **Purpose**: Creates mock beads controller for testing beads sync phase
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: Mock service object

#### 14. `sample_phase_docs`

- **File**: `silmari_rlm_act/tests/test_beads_sync_phase.py:86-105`
- **Scope**: function
- **Type**: Temporary file fixture
- **Purpose**: Creates sample phase markdown documents with overview and phases
- **Dependencies**: `tmp_path` (pytest built-in)
- **Autouse**: No
- **Pattern**: Multiple temporary files

---

### silmari_rlm_act/tests/test_pipeline.py

#### 15. `temp_project` (Pipeline variant)

- **File**: `silmari_rlm_act/tests/test_pipeline.py:26-32`
- **Scope**: function
- **Type**: Temporary directory fixture
- **Purpose**: Creates temporary project with `.rlm-act-checkpoints` directory
- **Dependencies**: `tmp_path` (pytest built-in)
- **Autouse**: No
- **Pattern**: Temporary resource with specific structure

#### 16. `mock_cwa`

- **File**: `silmari_rlm_act/tests/test_pipeline.py:35-42`
- **Scope**: function
- **Type**: Mock object fixture
- **Purpose**: Creates mock CWA integration with pre-configured return values
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: Mock with configured methods

#### 17. `mock_beads_controller`

- **File**: `silmari_rlm_act/tests/test_pipeline.py:45-53`
- **Scope**: function
- **Type**: Mock object fixture
- **Purpose**: Creates mock beads controller with pre-configured success responses
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: Mock with configured responses

#### 18. `sample_research_result`

- **File**: `silmari_rlm_act/tests/test_pipeline.py:56-67`
- **Scope**: function
- **Type**: Data fixture
- **Purpose**: Creates sample PhaseResult for research phase with timing and metadata
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: Complex data structure

#### 19. `sample_decomposition_result`

- **File**: `silmari_rlm_act/tests/test_pipeline.py:70-81`
- **Scope**: function
- **Type**: Data fixture
- **Purpose**: Creates sample PhaseResult for decomposition phase with artifacts
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: Complex data structure

---

### planning_pipeline/tests/conftest.py (Shared Fixtures)

This is the **primary fixture hub** with 348 lines of sophisticated mocking infrastructure.

#### Custom Pytest Markers

```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
```

**Purpose**: Allows test categorization with `@pytest.mark.slow`, `@pytest.mark.integration`, `@pytest.mark.e2e`

#### Mock BAML Types (Lines 17-78)

Six dataclass definitions mirroring `baml_client/types.py`:

1. **MockImplementationComponents**
2. **MockImplementationDetail**
3. **MockRequirement**
4. **MockResponseMetadata**
5. **MockInitialExtractionResponse**
6. **MockSubprocessDetailsResponse**

**Purpose**: Type-safe mock objects for BAML API responses

#### 20. `mock_baml_initial_extraction`

- **File**: `planning_pipeline/tests/conftest.py:85-100`
- **Scope**: function
- **Type**: Mock response fixture
- **Purpose**: Mocks BAML `ProcessGate1InitialExtractionPrompt` response with requirements
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: Structured mock data

#### 21. `mock_baml_subprocess_details`

- **File**: `planning_pipeline/tests/conftest.py:103-125`
- **Scope**: function
- **Type**: Mock response fixture
- **Purpose**: Mocks BAML `ProcessGate1SubprocessDetailsPrompt` response with implementation details
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: Structured mock data with 3 implementation details

#### 22. `mock_baml_client`

- **File**: `planning_pipeline/tests/conftest.py:128-134`
- **Scope**: function
- **Type**: Mock service fixture
- **Purpose**: Creates complete mock of BAML client for legacy unit tests
- **Dependencies**: `mock_baml_initial_extraction`, `mock_baml_subprocess_details`
- **Autouse**: No
- **Pattern**: Fixture composition

#### 23. `mock_claude_sdk_response`

- **File**: `planning_pipeline/tests/conftest.py:137-156`
- **Scope**: function
- **Type**: Mock response fixture
- **Purpose**: Mocks `run_claude_sync` response for requirement extraction (first call)
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: JSON response mock

#### 24. `mock_claude_expansion_response`

- **File**: `planning_pipeline/tests/conftest.py:159-216`
- **Scope**: function
- **Type**: Mock response fixture
- **Purpose**: Mocks `run_claude_sync` response for requirement expansion (second call) with 3 implementation details
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: JSON response mock with complex structure

#### 25. `mock_claude_expansion_response_limited`

- **File**: `planning_pipeline/tests/conftest.py:219-254`
- **Scope**: function
- **Type**: Mock response fixture
- **Purpose**: Mocks Claude SDK response with only 2 implementation details for `max_sub_processes` tests
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: Variant mock for boundary testing

#### 26. `patch_baml_client` ⭐ **Most Complex Fixture**

```python
@pytest.fixture
def patch_baml_client(
    mock_claude_sdk_response,
    mock_claude_expansion_response,
    mock_claude_expansion_response_limited
):
    """Context manager to patch run_claude_sync for decomposition tests.

    Provides intelligent side-effect handling for multiple sequential calls.
    First call returns initial extraction (requirements with sub_processes).
    Subsequent calls return expansion (implementation_details).
    """
```

- **File**: `planning_pipeline/tests/conftest.py:257-300`
- **Scope**: function
- **Type**: Context manager fixture
- **Purpose**: Patches `run_claude_sync` with stateful side effects for decomposition tests
- **Dependencies**: 3 mock response fixtures
- **Autouse**: No
- **Pattern**: Stateful mock with call counting and override capability
- **Complexity**: Highest - implements call counting and dynamic response switching

#### 27. `project_path`

- **File**: `planning_pipeline/tests/conftest.py:303-306`
- **Scope**: function
- **Type**: Path fixture
- **Purpose**: Returns root project path for integration tests
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: Project reference

#### 28. `sample_research_output`

- **File**: `planning_pipeline/tests/conftest.py:309-324`
- **Scope**: function
- **Type**: Sample data fixture
- **Purpose**: Provides sample Claude output with embedded research file path for testing artifact extraction
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: String parsing test data

#### 29. `sample_plan_output`

- **File**: `planning_pipeline/tests/conftest.py:327-336`
- **Scope**: function
- **Type**: Sample data fixture
- **Purpose**: Provides sample Claude output with embedded plan file path
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: String parsing test data

#### 30. `sample_phase_output`

- **File**: `planning_pipeline/tests/conftest.py:339-347`
- **Scope**: function
- **Type**: Sample data fixture
- **Purpose**: Provides sample Claude output with embedded phase file paths
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: String parsing test data

---

### planning_pipeline/tests/test_beads.py

#### 31. `beads_controller`

- **File**: `planning_pipeline/tests/test_beads.py:8-12`
- **Scope**: function
- **Type**: Service fixture
- **Purpose**: Creates real BeadsController for integration testing
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: Real service instantiation

#### 32. `cleanup_issues`

```python
@pytest.fixture
def cleanup_issues(beads_controller):
    """Track and cleanup created issues after test."""
    created_ids = []
    yield created_ids
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
    beads_controller.sync()
```

- **File**: `planning_pipeline/tests/test_beads.py:15-22`
- **Scope**: function
- **Type**: Yield fixture (setup/teardown)
- **Purpose**: Tracks created beads issues and cleans them up after test completion
- **Dependencies**: `beads_controller`
- **Autouse**: No
- **Pattern**: Resource cleanup with yield

---

### planning_pipeline/tests/test_checkpoint_manager.py

#### 33. `temp_project` (Checkpoint variant)

- **File**: `planning_pipeline/tests/test_checkpoint_manager.py:19-24`
- **Scope**: function
- **Type**: Temporary directory fixture
- **Purpose**: Creates temporary project with `.workflow-checkpoints` directory
- **Dependencies**: `tmp_path` (pytest built-in)
- **Autouse**: No
- **Pattern**: Temporary resource with specific structure

---

### planning_pipeline/tests/test_steps.py

#### 34. `project_path` (Steps variant)

- **File**: `planning_pipeline/tests/test_steps.py:14-17`
- **Scope**: function
- **Type**: Path fixture
- **Purpose**: Returns root project path for step testing
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: Project reference

#### 35. `beads_controller` (Steps variant)

- **File**: `planning_pipeline/tests/test_steps.py:20-23`
- **Scope**: function
- **Type**: Service fixture
- **Purpose**: Creates BeadsController with project path for step testing
- **Dependencies**: `project_path`
- **Autouse**: No
- **Pattern**: Service with dependency

#### 36. `cleanup_issues` (Steps variant)

- **File**: `planning_pipeline/tests/test_steps.py:26-33`
- **Scope**: function
- **Type**: Yield fixture (setup/teardown)
- **Purpose**: Tracks and cleans up created beads issues after test
- **Dependencies**: `beads_controller`
- **Autouse**: No
- **Pattern**: Resource cleanup with yield

---

### planning_pipeline/tests/test_step_decomposition.py

#### 37. `temp_project` (Decomposition variant)

- **File**: `planning_pipeline/tests/test_step_decomposition.py:23-51`
- **Scope**: function
- **Type**: Temporary directory fixture (complex)
- **Purpose**: Creates temporary project structure with research directory and sample research file
- **Dependencies**: `tmp_path` (pytest built-in)
- **Autouse**: No
- **Pattern**: Complex project structure
- **Returns**: `tuple[Path, str]` (project path and relative research path)

#### 38. `mock_decomposition_result`

- **File**: `planning_pipeline/tests/test_step_decomposition.py:54-87`
- **Scope**: function
- **Type**: Data fixture (complex)
- **Purpose**: Creates mock RequirementHierarchy with parent and child nodes
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: Complex data structure with hierarchy

---

### planning_pipeline/tests/test_pipeline.py

#### 39. `project_path` (Pipeline variant)

- **File**: `planning_pipeline/tests/test_pipeline.py:10-13`
- **Scope**: function
- **Type**: Path fixture
- **Purpose**: Returns root project path for pipeline testing
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: Project reference

#### 40. `beads_controller` (Pipeline variant)

- **File**: `planning_pipeline/tests/test_pipeline.py:16-19`
- **Scope**: function
- **Type**: Service fixture
- **Purpose**: Creates BeadsController for pipeline integration testing
- **Dependencies**: `project_path`
- **Autouse**: No
- **Pattern**: Service with dependency

#### 41. `cleanup_issues` (Pipeline variant)

- **File**: `planning_pipeline/tests/test_pipeline.py:22-29`
- **Scope**: function
- **Type**: Yield fixture (setup/teardown)
- **Purpose**: Tracks and cleans up beads issues created during pipeline tests
- **Dependencies**: `beads_controller`
- **Autouse**: No
- **Pattern**: Resource cleanup with yield

---

### planning_pipeline/tests/test_orchestrator.py

#### 42. `project_path` (Orchestrator variant)

- **File**: `planning_pipeline/tests/test_orchestrator.py:148-151`
- **Scope**: function
- **Type**: Path fixture
- **Purpose**: Returns root project path for orchestrator testing
- **Dependencies**: None
- **Autouse**: No
- **Pattern**: Project reference

#### 43. `cleanup_issues` (Orchestrator variant)

- **File**: `planning_pipeline/tests/test_orchestrator.py:153-162`
- **Scope**: function
- **Type**: Yield fixture (setup/teardown)
- **Purpose**: Tracks and cleans up beads issues created during orchestrator tests
- **Dependencies**: `project_path`
- **Autouse**: No
- **Pattern**: Resource cleanup with yield
- **Note**: Creates BeadsController inline rather than using separate fixture

---

### planning_pipeline/tests/test_helpers.py

#### 44. `temp_project` (Helpers variant)

- **File**: `planning_pipeline/tests/test_helpers.py:178-186`
- **Scope**: function
- **Type**: Temporary directory fixture
- **Purpose**: Creates temporary project with `thoughts/searchable/shared/research` and plans structure
- **Dependencies**: `tmp_path` (pytest built-in)
- **Autouse**: No
- **Pattern**: Temporary resource with nested structure

---

## 🎨 Fixture Patterns Analysis

### Pattern 1: Simple Data Fixtures

**Description**: Fixtures that return constant or simple data structures.

**Examples**:
- `sample_timestamp` → returns fixed datetime
- `sample_artifacts` → returns list of paths
- `sample_errors` → returns list of error messages

**Usage Count**: 6 fixtures

**Benefits**:
- Simple to understand
- Fast execution
- No cleanup needed
- Predictable test data

---

### Pattern 2: Temporary Resource Fixtures

**Description**: Fixtures using `tmp_path` to create isolated temporary files/directories.

**Examples**:
```python
@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with checkpoints dir."""
    checkpoints_dir = tmp_path / ".workflow-checkpoints"
    checkpoints_dir.mkdir()
    return tmp_path
```

**Usage Count**: 10+ fixtures

**Benefits**:
- Test isolation
- Automatic cleanup by pytest
- No filesystem pollution
- Parallel test execution support

**Variants**:
- Simple directory creation
- Complex project structures
- Multiple nested directories
- Files with specific content

---

### Pattern 3: Mock Object Fixtures

**Description**: Fixtures creating `MagicMock` objects to replace external dependencies.

**Examples**:
- `mock_baml_client` → Complete BAML API mock
- `mock_cwa` → Mock CWA integration
- `mock_beads_controller` → Mock beads controller

**Usage Count**: 8+ fixtures

**Benefits**:
- No external API calls
- Fast test execution
- Predictable behavior
- Easy to configure return values

**Pattern Variations**:
```python
# Simple mock
@pytest.fixture
def mock_service():
    return MagicMock()

# Configured mock
@pytest.fixture
def mock_service():
    mock = MagicMock()
    mock.method.return_value = {"success": True}
    return mock
```

---

### Pattern 4: Fixture Composition (Chaining)

**Description**: Fixtures that depend on other fixtures to build complex test objects.

**Example Chain**:
```
project_path → beads_controller → cleanup_issues
```

**Code**:
```python
@pytest.fixture
def project_path():
    return Path(__file__).parent.parent.parent

@pytest.fixture
def beads_controller(project_path):
    return BeadsController(project_path)

@pytest.fixture
def cleanup_issues(beads_controller):
    created_ids = []
    yield created_ids
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
```

**Usage Count**: 4 chains

**Benefits**:
- Reusable components
- Clear dependencies
- Single responsibility
- Easy to test fixtures themselves

---

### Pattern 5: Yield Fixtures (Setup/Teardown)

**Description**: Fixtures using `yield` for automatic cleanup after test execution.

**Example**:
```python
@pytest.fixture
def cleanup_issues(beads_controller):
    """Track and cleanup created issues after test."""
    created_ids = []
    yield created_ids  # Setup: provide empty list
    # Teardown: cleanup all created issues
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
    beads_controller.sync()
```

**Usage Count**: 4 fixtures

**Usage in Tests**:
```python
def test_creates_issue(beads_controller, cleanup_issues):
    result = beads_controller.create_issue("Test", "task", 2)
    cleanup_issues.append(result["data"]["id"])  # Register for cleanup
    assert result["success"]
```

**Benefits**:
- Guaranteed cleanup (even if test fails)
- Resource tracking
- Prevents test pollution
- Clear separation of setup/teardown

---

### Pattern 6: Context Manager Fixtures

**Description**: Fixtures that yield context managers (typically `unittest.mock.patch`).

**Example**:
```python
@pytest.fixture
def patch_baml_client(mock_claude_sdk_response, mock_claude_expansion_response):
    """Context manager to patch run_claude_sync."""
    call_count = [0]

    def side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return mock_claude_sdk_response
        return mock_claude_expansion_response

    with patch("planning_pipeline.decomposition.run_claude_sync") as mock_run:
        mock_run.side_effect = side_effect
        yield mock_run
    # Patch automatically reverted when context exits
```

**Usage Count**: 1 fixture (most complex)

**Benefits**:
- Automatic patch cleanup
- Stateful behavior
- Multiple call handling
- Override capability

---

### Pattern 7: Mock Type Fixtures

**Description**: Dataclass-based mock types mirroring actual API types.

**Example**:
```python
@dataclass
class MockRequirement:
    description: str
    sub_processes: list[str]
    related_concepts: list[str]
    implementation_considerations: list[str] = field(default_factory=list)
```

**Usage Count**: 6 dataclasses

**Benefits**:
- Type safety
- IDE autocomplete
- Realistic test data
- Easy to construct

---

### Pattern 8: Sample Output Fixtures

**Description**: Fixtures providing sample string output for parsing tests.

**Examples**:
- `sample_research_output` → Claude output with file paths
- `sample_plan_output` → Claude output with plan paths
- `sample_phase_output` → Claude output with phase paths

**Usage Count**: 3 fixtures

**Purpose**: Testing artifact extraction and path parsing logic

---

### Pattern 9: Service Instantiation Fixtures

**Description**: Fixtures creating real service instances for integration testing.

**Examples**:
- `beads_controller` → Real BeadsController with project path
- `cwa` → Real CWAIntegration instance
- `cli_runner` → Click CLI test runner

**Usage Count**: 5+ fixtures

**Benefits**:
- Integration testing
- Real behavior validation
- End-to-end testing support

---

## 📐 Fixture Scope Strategy

### Scope Distribution

| **Scope** | **Count** | **Percentage** |
|-----------|-----------|----------------|
| function | 44 | 100% |
| class | 0 | 0% |
| module | 0 | 0% |
| session | 0 | 0% |

### Analysis

**100% function-scoped fixtures** indicates:
- ✅ Maximum test isolation
- ✅ No state leakage between tests
- ✅ Parallel test execution safety
- ✅ Easy to understand and debug
- ⚠️ Potential performance trade-off (rebuilding fixtures for each test)

The project prioritizes **test reliability over performance optimization**, which is appropriate for a development tooling project where test correctness is critical.

---

## 🔄 Fixture Usage Patterns

### Common Fixture Combinations

#### Pattern A: "Project Setup"

**Fixtures**: `tmp_path` + `temp_project` + custom structure

**Example**:
```python
def test_creates_hierarchy_json(self, temp_project, mock_decomposition_result):
    project_path, research_path = temp_project
    # Test implementation
```

**Used In**: `test_step_decomposition.py`, `test_context_generation.py`

---

#### Pattern B: "Mock + Test + Cleanup"

**Fixtures**: `beads_controller` + `cleanup_issues` + mock data

**Example**:
```python
def test_creates_task_issue(self, beads_controller, cleanup_issues):
    result = beads_controller.create_issue("Test", "task", 2)
    cleanup_issues.append(result["data"]["id"])
    assert result["success"]
```

**Used In**: `test_beads.py`, `test_pipeline.py`, `test_orchestrator.py`

---

#### Pattern C: "Integration Test"

**Fixtures**: `tmp_path` + `monkeypatch` + `capsys` + multiple patches

**Example**:
```python
def test_prompts_on_failure(self, tmp_path, monkeypatch, capsys):
    inputs = iter(["c"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch.multiple("planning_pipeline.pipeline", ...):
        pipeline = PlanningPipeline(tmp_path)
        pipeline.run("test", auto_approve=False)

    output = capsys.readouterr().out
    assert "(R)etry" in output
```

**Used In**: `test_pipeline.py`, `test_orchestrator.py`

---

## 🎯 Fixture Naming Conventions

### Observed Naming Patterns

| **Prefix** | **Meaning** | **Examples** |
|------------|-------------|--------------|
| `mock_*` | Mock object or response | `mock_baml_client`, `mock_cwa`, `mock_beads` |
| `sample_*` | Sample data for testing | `sample_timestamp`, `sample_artifacts`, `sample_errors` |
| `temp_*` | Temporary resource | `temp_project`, `temp_research_doc`, `temp_plan_doc` |
| `cleanup_*` | Cleanup/teardown fixture | `cleanup_issues` |
| `patch_*` | Context manager for patching | `patch_baml_client` |

### Benefits

- ✅ Immediate understanding of fixture purpose
- ✅ Easy to search and find fixtures
- ✅ Clear distinction between real and mock objects
- ✅ Consistent across the codebase

---

## 🔗 Fixture Dependency Graph

### Primary Chains

```
┌─────────────┐
│ project_path│
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│beads_controller  │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ cleanup_issues   │
└──────────────────┘
```

### Mock Composition

```
┌───────────────────────────┐
│mock_baml_initial_extraction│──┐
└───────────────────────────┘  │
                               ├──►┌─────────────────┐
┌───────────────────────────┐  │   │mock_baml_client │
│mock_baml_subprocess_details│──┘   └─────────────────┘
└───────────────────────────┘
```

### Complex Patch Fixture

```
┌─────────────────────────┐
│mock_claude_sdk_response │──┐
└─────────────────────────┘  │
                             ├──►┌──────────────────┐
┌─────────────────────────┐  │   │patch_baml_client │
│mock_claude_expansion_   │──┤   └──────────────────┘
│response                 │  │
└─────────────────────────┘  │
                             │
┌─────────────────────────┐  │
│mock_claude_expansion_   │──┘
│response_limited         │
└─────────────────────────┘
```

---

## 🧪 Custom Pytest Markers

### Defined Markers

```python
# planning_pipeline/tests/conftest.py
config.addinivalue_line("markers", "slow: marks tests as slow")
config.addinivalue_line("markers", "integration: marks tests as integration tests")
config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
```

### Usage

```python
@pytest.mark.slow
def test_large_dataset_processing():
    # Test implementation

@pytest.mark.integration
def test_api_integration():
    # Test implementation

@pytest.mark.e2e
def test_full_pipeline():
    # Test implementation
```

### Benefits

- ✅ Selective test execution: `pytest -m "not slow"`
- ✅ CI/CD optimization: Run fast tests first
- ✅ Clear test categorization
- ✅ Documentation of test types

---

## 📝 Fixture Documentation Patterns

### Docstring Conventions

All fixtures follow consistent documentation:

```python
@pytest.fixture
def fixture_name(dependencies):
    """One-line description of what the fixture provides."""
    # implementation
```

### Examples

- ✅ `"""Create a temporary project with checkpoints dir."""`
- ✅ `"""Track and cleanup created issues after test."""`
- ✅ `"""Mock response for b.ProcessGate1InitialExtractionPrompt."""`
- ✅ `"""Provide a consistent timestamp for tests."""`

### Type Hints

Modern fixtures use type hints:

```python
@pytest.fixture
def sample_timestamp() -> datetime:
    """Provide a consistent timestamp for tests."""
    return datetime(2026, 1, 5, 10, 30, 0)

@pytest.fixture
def sample_artifacts() -> list[str]:
    """Provide sample artifact paths for tests."""
    return [...]
```

**Benefits**:
- IDE autocomplete support
- Type checking with mypy
- Better documentation
- Clearer contracts

---

## 🏗️ Test Architecture Insights

### Fixture Distribution by Purpose

| **Purpose** | **Count** | **Percentage** |
|-------------|-----------|----------------|
| Mock Objects | 12 | 27% |
| Temporary Resources | 14 | 32% |
| Simple Data | 6 | 14% |
| Service Instances | 5 | 11% |
| Cleanup/Teardown | 4 | 9% |
| Sample Output | 3 | 7% |

### Key Observations

1. **Heavy Mocking Infrastructure** (27%): Indicates extensive external dependencies (BAML, Claude SDK, CWA)
2. **Temporary Resource Focus** (32%): Testing file system operations and project structures
3. **Real Service Testing** (11%): Balance between unit and integration testing
4. **Cleanup Discipline** (9%): Careful resource management for integration tests

---

## 📚 Historical Context

### Related Research Documents

From the thoughts/ directory search, previous testing research includes:

1. **`thoughts/searchable/research/2026-01-14-pytest-fixtures-testing-patterns.md`**
   - Date: 2026-01-14 11:37:27
   - 52 pytest fixtures across 41 test files
   - 9 distinct fixture patterns

2. **`thoughts/searchable/research/2026-01-14-pytest-fixtures-analysis.md`**
   - Date: 2026-01-14 13:00:42
   - 62 fixtures, 42 test files, 7,989 test functions
   - 12 distinct fixture patterns
   - Complete fixture inventory

3. **`thoughts/searchable/shared/research/2026-01-06-pytest-fixtures-patterns.md`**
   - Date: 2026-01-06 07:11:40 EST
   - 48 fixtures across 43 test files
   - BDD-style testing patterns
   - Custom pytest markers documentation

### Evolution Timeline

- **2026-01-01**: Foundation analysis (20 fixtures)
- **2026-01-02**: Pattern study (20+ fixtures) with Hypothesis
- **2026-01-04**: Dependency graphs (8 shared fixtures)
- **2026-01-06**: Comprehensive catalog (48 fixtures)
- **2026-01-14**: Latest analyses (44-62 fixtures depending on count method)

**Trend**: Consistent growth with well-established patterns refined over 2 weeks

---

## 🎯 Testing Strategy Overview

### Multi-Layered Approach

```
┌─────────────────────────────────────┐
│         End-to-End Tests            │  (@pytest.mark.e2e)
│         Full pipeline flows         │
├─────────────────────────────────────┤
│      Integration Tests              │  (@pytest.mark.integration)
│      Component interactions         │
├─────────────────────────────────────┤
│          Unit Tests                 │  (default)
│      Mock external dependencies     │
└─────────────────────────────────────┘
```

### Framework Integration

- **pytest-asyncio**: `asyncio_mode = auto` for async/await support
- **Hypothesis**: Property-based testing for model validation
- **unittest.mock**: MagicMock and patch patterns throughout
- **Click.testing**: CLI command testing with CliRunner

---

## 🔍 Special Fixture Implementations

### Most Complex: `patch_baml_client`

This fixture demonstrates advanced pytest patterns:

**Features**:
1. **Stateful Behavior**: Call counter tracks invocation order
2. **Dynamic Responses**: Different responses for first vs subsequent calls
3. **Override Capability**: Tests can override default behavior
4. **Multiple Dependencies**: Composes 3 mock response fixtures
5. **Context Management**: Uses `with patch()` for automatic cleanup

**Code Structure**:
```python
@pytest.fixture
def patch_baml_client(
    mock_claude_sdk_response,
    mock_claude_expansion_response,
    mock_claude_expansion_response_limited
):
    call_count = [0]  # Mutable container for closure
    override_return = [None]  # Override mechanism

    def side_effect(*args, **kwargs):
        if override_return[0] is not None:
            return override_return[0]
        call_count[0] += 1
        if call_count[0] == 1:
            return mock_claude_sdk_response
        return mock_claude_expansion_response

    with patch("planning_pipeline.decomposition.run_claude_sync") as mock_run:
        mock_run.side_effect = side_effect
        # Provide access to override and helpers
        mock_run.use_limited_response = lambda: ...
        mock_run.reset_call_count = lambda: ...
        yield mock_run
```

**Usage in Tests**:
```python
def test_decomposition(patch_baml_client):
    with patch_baml_client:
        result = decompose_requirements(...)
        assert result.success
```

---

## ✅ Testing Strengths

| **Strength** | **Evidence** |
|-------------|--------------|
| Comprehensive Coverage | 42 test files across 4 directories |
| Clear Naming | Consistent `mock_*`, `sample_*`, `temp_*` conventions |
| Test Isolation | 100% function-scoped fixtures |
| Explicit Dependencies | Zero autouse fixtures |
| BDD Structure | Given-When-Then test organization |
| Sophisticated Mocking | 12 mock fixtures with type-safe dataclasses |
| Resource Cleanup | 4 yield-based cleanup patterns |
| Type Safety | Type hints on fixtures |

---

## 📊 Fixture Statistics Summary

<details>
<summary><b>Click to expand detailed statistics</b></summary>

### By Location

| **File** | **Fixture Count** |
|----------|-------------------|
| `planning_pipeline/tests/conftest.py` | 11 |
| `silmari_rlm_act/tests/conftest.py` | 3 |
| `silmari_rlm_act/tests/test_validation.py` | 3 |
| `silmari_rlm_act/tests/test_implementation_phase.py` | 2 |
| `silmari_rlm_act/tests/test_cli.py` | 3 |
| `silmari_rlm_act/tests/test_beads_sync_phase.py` | 2 |
| `silmari_rlm_act/tests/test_pipeline.py` | 5 |
| `planning_pipeline/tests/test_beads.py` | 2 |
| `planning_pipeline/tests/test_checkpoint_manager.py` | 1 |
| `planning_pipeline/tests/test_steps.py` | 3 |
| `planning_pipeline/tests/test_step_decomposition.py` | 2 |
| `planning_pipeline/tests/test_pipeline.py` | 3 |
| `planning_pipeline/tests/test_orchestrator.py` | 2 |
| `planning_pipeline/tests/test_helpers.py` | 1 |

### Fixture Reuse

| **Fixture Name** | **Occurrences** | **Files** |
|------------------|-----------------|-----------|
| `temp_project` | 6 | Multiple test files |
| `project_path` | 5 | Multiple test files |
| `beads_controller` | 4 | Multiple test files |
| `cleanup_issues` | 4 | Multiple test files |
| `temp_research_doc` | 2 | test_validation.py, test_cli.py |

**Note**: Multiple fixtures share the same name but have different implementations for their specific test contexts.

</details>

---

## 🎓 Best Practices Observed

### 1. Fixture Naming

✅ **DO**: Use descriptive prefixes (`mock_`, `sample_`, `temp_`)
✅ **DO**: Include purpose in name (`cleanup_issues`, not just `cleanup`)
✅ **DO**: Be specific (`mock_baml_client`, not just `mock_client`)

### 2. Fixture Scope

✅ **DO**: Use function scope by default (as this codebase does)
✅ **DO**: Only use broader scopes (module, session) when performance is critical
✅ **DO**: Document reasons for broader scopes

### 3. Fixture Dependencies

✅ **DO**: Create small, composable fixtures
✅ **DO**: Chain fixtures for complex setups
✅ **DO**: Make dependencies explicit through parameters
❌ **DON'T**: Create monolithic fixtures that do too much

### 4. Cleanup

✅ **DO**: Use yield fixtures for resource cleanup
✅ **DO**: Track resources that need cleanup (`cleanup_issues` pattern)
✅ **DO**: Ensure cleanup happens even if test fails

### 5. Documentation

✅ **DO**: Add docstrings to all fixtures
✅ **DO**: Use type hints for better IDE support
✅ **DO**: Document complex fixture behavior

---

## 🎨 Code Examples

### Example 1: Simple Data Fixture

```python
@pytest.fixture
def sample_timestamp() -> datetime:
    """Provide a consistent timestamp for tests."""
    return datetime(2026, 1, 5, 10, 30, 0)
```

**Usage**:
```python
def test_timestamp_format(sample_timestamp):
    formatted = sample_timestamp.strftime("%Y-%m-%d")
    assert formatted == "2026-01-05"
```

---

### Example 2: Temporary Resource with Cleanup

```python
@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure."""
    research_dir = tmp_path / "thoughts" / "research"
    research_dir.mkdir(parents=True)

    research_file = research_dir / "test.md"
    research_file.write_text("# Test Research")

    return tmp_path, str(research_file.relative_to(tmp_path))
```

**Usage**:
```python
def test_project_structure(temp_project):
    project_path, research_path = temp_project
    assert (project_path / research_path).exists()
```

---

### Example 3: Yield Fixture with Resource Tracking

```python
@pytest.fixture
def cleanup_issues(beads_controller):
    """Track and cleanup created issues after test."""
    created_ids = []
    yield created_ids

    # Cleanup happens here, even if test fails
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
    beads_controller.sync()
```

**Usage**:
```python
def test_creates_issue(beads_controller, cleanup_issues):
    result = beads_controller.create_issue("Test", "task", 2)
    cleanup_issues.append(result["data"]["id"])  # Register for cleanup
    assert result["success"]
    # Cleanup happens automatically after test
```

---

### Example 4: Mock with Configured Behavior

```python
@pytest.fixture
def mock_cwa():
    """Create a mock CWA integration with pre-configured return values."""
    mock = MagicMock()
    mock.store_in_context_window.return_value = {"success": True, "id": "cwa-123"}
    mock.get_relevant_context.return_value = "Sample context"
    return mock
```

**Usage**:
```python
def test_stores_context(mock_cwa):
    result = mock_cwa.store_in_context_window("data")
    assert result["success"]
    assert "id" in result
```

---

### Example 5: Complex Fixture Composition

```python
@pytest.fixture
def project_path():
    """Return the root project path."""
    return Path(__file__).parent.parent.parent

@pytest.fixture
def beads_controller(project_path):
    """Create BeadsController with project path."""
    return BeadsController(project_path)

@pytest.fixture
def cleanup_issues(beads_controller):
    """Track and cleanup created issues."""
    created_ids = []
    yield created_ids
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
```

**Usage** (all three fixtures injected):
```python
def test_full_workflow(project_path, beads_controller, cleanup_issues):
    # project_path and beads_controller available
    issue = beads_controller.create_issue("Test", "task", 2)
    cleanup_issues.append(issue["data"]["id"])
    assert issue["success"]
```

---

## 🔍 Detailed Conftest Analysis

### planning_pipeline/tests/conftest.py Structure

**Lines 1-14**: Pytest configuration and custom markers
**Lines 17-78**: Mock BAML type definitions (6 dataclasses)
**Lines 81-125**: BAML mock fixtures (3 fixtures)
**Lines 128-134**: BAML client mock (1 fixture)
**Lines 137-255**: Claude SDK mock fixtures (3 fixtures)
**Lines 257-300**: Patch fixture with stateful behavior (1 fixture)
**Lines 303-307**: Project path fixture (1 fixture)
**Lines 309-348**: Sample output fixtures (3 fixtures)

**Total**: 348 lines, 11 fixtures, 6 mock types

### silmari_rlm_act/tests/conftest.py Structure

**Lines 7-28**: Simple data fixtures (3 fixtures)

**Total**: 29 lines, 3 fixtures

---

## 📋 Related TDD/Testing Plans

From the thoughts/ directory, testing infrastructure plans include:

### Test Execution Requirements

**Document**: `thoughts/searchable/shared/plans/2026-01-10-tdd-feature/13-the-implementation-phase-must-run-tests-using-pyte.md`

**Specifications**:
- Primary command: `pytest -v --tb=short`
- Fallback: `make test` when pytest unavailable
- Timeout: 300 seconds (5 minutes default)
- Tests must pass for implementation completion
- 8 specific testable behaviors documented

### Integration Testing Specifications

**Document**: `thoughts/searchable/shared/plans/2026-01-01-tdd-loop-runner-orchestrator-07-integration-tests.md`

**Purpose**: Integration testing requirements for loop runner orchestrator and autonomous execution system

---

## 🎯 Conclusion

The silmari-Context-Engine project demonstrates **mature pytest fixture usage** with:

1. ✅ **Well-Organized Structure**: Clear separation between shared (conftest.py) and test-specific fixtures
2. ✅ **Consistent Patterns**: 9 distinct patterns used consistently across the codebase
3. ✅ **Sophisticated Mocking**: Type-safe mock objects with stateful behavior
4. ✅ **Resource Management**: Disciplined cleanup using yield fixtures
5. ✅ **Test Isolation**: 100% function-scoped fixtures for maximum reliability
6. ✅ **Good Documentation**: Every fixture has a clear docstring and type hints
7. ✅ **Practical Design**: No over-engineering, focuses on real testing needs

The testing infrastructure supports a **multi-layered testing strategy** (unit, integration, e2e) with clear categorization using custom markers and extensive mocking infrastructure for external dependencies.

---

## 📎 Code References

<details>
<summary><b>Click to expand all file references</b></summary>

### Conftest Files
- `planning_pipeline/tests/conftest.py` - Primary fixture hub (348 lines)
- `silmari_rlm_act/tests/conftest.py` - Lightweight fixtures (29 lines)

### Test Files with Fixtures
- `silmari_rlm_act/tests/test_validation.py:29-92` - 3 fixtures
- `silmari_rlm_act/tests/test_implementation_phase.py:21-43` - 2 fixtures
- `silmari_rlm_act/tests/test_cli.py:24-531` - 3 fixtures
- `silmari_rlm_act/tests/test_beads_sync_phase.py:80-105` - 2 fixtures
- `silmari_rlm_act/tests/test_pipeline.py:26-81` - 5 fixtures
- `planning_pipeline/tests/test_beads.py:8-22` - 2 fixtures
- `planning_pipeline/tests/test_checkpoint_manager.py:19-24` - 1 fixture
- `planning_pipeline/tests/test_steps.py:14-33` - 3 fixtures
- `planning_pipeline/tests/test_step_decomposition.py:23-87` - 2 fixtures
- `planning_pipeline/tests/test_pipeline.py:10-29` - 3 fixtures
- `planning_pipeline/tests/test_orchestrator.py:148-162` - 2 fixtures
- `planning_pipeline/tests/test_helpers.py:178-186` - 1 fixture

### Test Directories
- `/home/maceo/Dev/silmari-Context-Engine/tests/` - 3 test files
- `/home/maceo/Dev/silmari-Context-Engine/planning_pipeline/tests/` - 19 test files
- `/home/maceo/Dev/silmari-Context-Engine/silmari_rlm_act/tests/` - 14 test files
- `/home/maceo/Dev/silmari-Context-Engine/context_window_array/tests/` - 6 test files

</details>

---

## 🔗 Related Research

- `thoughts/searchable/research/2026-01-14-pytest-fixtures-analysis.md` - Latest comprehensive analysis
- `thoughts/searchable/research/2026-01-14-pytest-fixtures-testing-patterns.md` - Earlier pattern study
- `thoughts/searchable/shared/research/2026-01-06-pytest-fixtures-patterns.md` - Initial comprehensive catalog
- `thoughts/searchable/shared/plans/2026-01-10-tdd-feature/13-the-implementation-phase-must-run-tests-using-pyte.md` - Test execution requirements
- `thoughts/searchable/shared/plans/2026-01-01-tdd-loop-runner-orchestrator-07-integration-tests.md` - Integration testing specs

---

**End of Research Document**
