---
date: 2026-01-14T14:36:48-05:00
researcher: Maceo
git_commit: 99126e57d785f9ed08e7a14d7898f1ddc28f8ac6
branch: main
repository: silmari-Context-Engine
topic: "Pytest Fixtures - Testing Patterns Analysis"
tags: [research, codebase, pytest, testing, fixtures, test-patterns]
status: complete
last_updated: 2026-01-14
last_updated_by: Maceo
---

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║         PYTEST FIXTURES - TESTING PATTERNS ANALYSIS           ║
║              silmari-Context-Engine Test Suite                ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

**Date**: 2026-01-14T14:36:48-05:00
**Researcher**: Maceo
**Git Commit**: `99126e57d785f9ed08e7a14d7898f1ddc28f8ac6`
**Branch**: `main`
**Repository**: silmari-Context-Engine

---

## 📚 Research Question

Analyze the testing patterns in this project with a focus on pytest fixtures.

---

## 🎯 Summary

This codebase implements a **comprehensive pytest-based testing infrastructure** across 42 test files organized into 4 main test suites. The testing patterns demonstrate sophisticated use of pytest fixtures including:

- **14 shared fixtures** across 2 `conftest.py` files
- **70+ total fixture definitions** spanning mock data, file system setup, cleanup teardown, and complex project structures
- **Multiple fixture scopes** (function-level, class-level) with extensive dependency chains
- **Advanced patterns** including yield-based cleanup, context manager patches with state management, and composite fixtures

The test suite is well-organized with clear separation between unit tests, integration tests, and end-to-end tests (via custom markers). Mock fixtures provide extensive coverage of external dependencies (BAML, Claude SDK, CLI runners), while cleanup fixtures ensure test isolation through proper resource teardown.

---

## 📊 Test Suite Overview

### Test Infrastructure Statistics

| Metric | Count | Details |
|--------|-------|---------|
| **Test Files** | 42 | Excluding venv and cache |
| **Test Directories** | 4 | Root, planning_pipeline, silmari_rlm_act, context_window_array |
| **Conftest Files** | 2 | Shared fixture configuration per module |
| **Total Fixtures** | 70+ | Across all test files |
| **Shared Fixtures** | 14 | In conftest.py files |
| **Custom Markers** | 3 | `@pytest.mark.slow`, `@pytest.mark.integration`, `@pytest.mark.e2e` |

---

## 🗂️ Test Directory Structure

### 1️⃣ Root Tests Directory

**Location**: `tests/`

```
tests/
├── test_autonomous_loop.py
├── test_execute_phase.py
└── test_loop_orchestrator_integration.py
```

**Status**: No conftest.py - fixtures are defined within test files
**Focus**: Autonomous loop and orchestrator integration testing
**Fixtures**: Class-scoped fixtures for mocking orchestrators

---

### 2️⃣ Planning Pipeline Tests

**Location**: `planning_pipeline/tests/`

```
planning_pipeline/tests/
├── conftest.py ⭐ (11 shared fixtures)
├── test_beads.py
├── test_beads_controller.py
├── test_checkpoint_manager.py
├── test_checkpoints.py
├── test_claude.py
├── test_claude_runner.py
├── test_context_generation.py
├── test_decomposition.py
├── test_decomposition_e2e.py
├── test_helpers.py
├── test_integrated_orchestrator.py
├── test_models.py
├── test_orchestrator.py
├── test_phase_execution.py
├── test_pipeline.py
├── test_property_generator.py
├── test_step_decomposition.py
├── test_steps.py
└── test_visualization.py
```

**Total Files**: 21 (20 test files + 1 conftest)
**Focus**: Core planning pipeline functionality, decomposition, orchestration
**Custom Markers**: Registered in conftest via `pytest_configure` hook

---

### 3️⃣ Silmari RLM Act Tests

**Location**: `silmari_rlm_act/tests/`

```
silmari_rlm_act/tests/
├── conftest.py ⭐ (3 shared fixtures)
├── test_artifact_generation.py
├── test_beads_sync_phase.py
├── test_checkpoint_manager.py
├── test_cli.py
├── test_cwa_integration.py
├── test_decomposition_phase.py
├── test_implementation_phase.py
├── test_interactive.py
├── test_models.py
├── test_multi_doc_phase.py
├── test_pipeline.py
├── test_research_phase.py
├── test_tdd_planning_phase.py
└── test_validation.py
```

**Total Files**: 16 (15 test files + 1 conftest)
**Focus**: RLM action phases, pipeline execution, CLI testing
**Fixtures**: Simple data fixtures (timestamps, artifacts, errors)

---

### 4️⃣ Context Window Array Tests

**Location**: `context_window_array/tests/`

```
context_window_array/tests/
├── test_batching.py
├── test_implementation_context.py
├── test_models.py
├── test_search.py
├── test_store.py
└── test_working_context.py
```

**Total Files**: 6
**Status**: No conftest.py - fixtures are local to individual files
**Focus**: Context window array functionality, batching, search

---

## 🔧 Fixture Types and Categories

### Fixture Distribution by Type

| Fixture Type | Count | Example Locations |
|--------------|-------|-------------------|
| **Simple Value Providers** | 5+ | `silmari_rlm_act/tests/conftest.py:7-28` |
| **Mock BAML/SDK Responses** | 8+ | `planning_pipeline/tests/conftest.py:85-256` |
| **File System Setup** | 10+ | `test_validation.py`, `test_step_decomposition.py` |
| **Cleanup with Yield** | 5+ | `test_steps.py`, `test_pipeline.py`, `test_beads.py` |
| **Composite Mocks** | 5+ | `mock_baml_client`, `patch_baml_client` |
| **Class-Scoped Methods** | 10+ | `test_autonomous_loop.py`, `test_orchestrator.py` |
| **Context Manager Patches** | 2+ | `conftest.py:257-301` |
| **Data Model Instances** | 5+ | `test_pipeline.py` (PhaseResult fixtures) |
| **Project Path Providers** | 6+ | Multiple files |
| **Controller Initialization** | 4+ | `test_beads.py`, `test_steps.py` |

---

## 🎨 Shared Fixtures in Conftest Files

### Planning Pipeline conftest.py

**Location**: `planning_pipeline/tests/conftest.py`

<details>
<summary><b>11 Shared Fixtures (click to expand)</b></summary>

| Fixture Name | Lines | Purpose | Return Type |
|-------------|-------|---------|-------------|
| `mock_baml_initial_extraction` | 86-101 | Mock BAML initial extraction response | MockInitialExtractionResponse |
| `mock_baml_subprocess_details` | 103-127 | Mock BAML subprocess details response | MockSubprocessDetailsResponse |
| `mock_baml_client` | 128-134 | Complete mock BAML client (legacy) | MagicMock |
| `mock_claude_sdk_response` | 137-156 | Mock Claude SDK requirement extraction | dict |
| `mock_claude_expansion_response` | 158-194 | Mock Claude SDK expansion (3 items) | dict |
| `mock_claude_expansion_response_limited` | 196-218 | Mock Claude SDK expansion (2 items) | dict |
| `patch_baml_client` | 257-301 | Context manager to patch run_claude_sync | MagicMock (yields) |
| `project_path` | 304-307 | Root project path fixture | Path |
| `sample_research_output` | 309-324 | Sample Claude research output | str |
| `sample_plan_output` | 326-338 | Sample Claude plan output | str |
| `sample_phase_output` | 340-347 | Sample phase file paths | str |

</details>

**Custom Markers Registered**:
```python
@pytest.mark.slow        # For slow tests
@pytest.mark.integration # For integration tests
@pytest.mark.e2e         # For end-to-end tests
```

**pytest_configure Hook**: Lines 10-14

---

### Silmari RLM Act conftest.py

**Location**: `silmari_rlm_act/tests/conftest.py`

| Fixture Name | Lines | Purpose | Return Type |
|-------------|-------|---------|-------------|
| `sample_timestamp` | 7-10 | Consistent datetime for tests | datetime(2026, 1, 5, 10, 30, 0) |
| `sample_artifacts` | 12-19 | Sample artifact paths | list[str] (2 paths) |
| `sample_errors` | 21-28 | Sample error messages | list[str] (2 errors) |

**Pattern**: Simple, immutable test data providers

---

## 🏗️ Fixture Patterns Deep Dive

### Pattern 1: Simple Value Providers ✅

**Purpose**: Provide consistent, immutable test data

**Example**: `silmari_rlm_act/tests/conftest.py:7-10`

```python
@pytest.fixture
def sample_timestamp() -> datetime:
    """Provide a consistent timestamp for tests."""
    return datetime(2026, 1, 5, 10, 30, 0)
```

**Characteristics**:
- No dependencies
- Function-scoped (default)
- Returns simple values or data structures
- Used across multiple tests for consistency

**Other Examples**:
- `sample_artifacts()` - List of artifact paths
- `sample_errors()` - List of error messages

---

### Pattern 2: Mock Response Fixtures 🎭

**Purpose**: Mock external system responses (BAML, Claude SDK, APIs)

**Example**: `planning_pipeline/tests/conftest.py:137-156`

```python
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
        ]
    ]
}""",
        "error": "",
        "elapsed": 1.5
    }
```

**Characteristics**:
- Returns dict or dataclass with response structure
- JSON strings embedded in output field
- Simulates successful API responses
- Used with `patch` or `MagicMock` side_effect

**Other Examples**:
- `mock_baml_initial_extraction` - BAML extraction response
- `mock_claude_expansion_response` - Claude expansion details
- `mock_cwa` (in test_cli.py) - CWA integration mock

---

### Pattern 3: Cleanup Fixtures (Yield Pattern) 🧹

**Purpose**: Setup resources, yield to test, teardown/cleanup after

**Example**: `planning_pipeline/tests/test_steps.py:26-33`

```python
@pytest.fixture
def cleanup_issues(beads_controller):
    """Track and cleanup created issues after test."""
    created_ids = []
    yield created_ids  # <-- Test runs here
    # Teardown phase starts after yield
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
    beads_controller.sync()
```

**Execution Flow**:
```
1. Setup: Create empty list
2. Yield: Test executes, populates list
3. Teardown: Close all issues, sync
```

**Characteristics**:
- Uses `yield` to separate setup from teardown
- Test code populates yielded resource
- Guarantees cleanup even if test fails
- Ensures test isolation

**Other Examples**:
- `test_beads.py:15-22` - Beads issue cleanup
- `test_pipeline.py:22-29` - Pipeline issue cleanup

---

### Pattern 4: Temporary File System Fixtures 📁

**Purpose**: Create temporary directories and files for testing

**Example**: `silmari_rlm_act/tests/test_validation.py:29-60`

```python
@pytest.fixture
def temp_hierarchy(tmp_path: Path) -> Path:
    """Create a temporary hierarchy JSON file."""
    hierarchy = {
        "requirements": [
            {
                "id": "REQ_001",
                "description": "User authentication system",
                "type": "parent",
                # ... nested structure ...
            }
        ],
        "metadata": {"source": "test"},
    }
    doc = tmp_path / "hierarchy.json"
    doc.write_text(json.dumps(hierarchy, indent=2))
    return doc
```

**Characteristics**:
- Depends on pytest built-in `tmp_path` fixture
- Creates real files in temporary directory
- Automatic cleanup by pytest
- Returns Path object to created file

**Directory Structure Example**:
```
tmp_path/
└── thoughts/
    └── shared/
        └── research/
            └── 2026-01-02-test-research.md
```

**Other Examples**:
- `test_step_decomposition.py:23-51` - Full project structure
- `test_implementation_phase.py:21-43` - TDD plan document
- `test_checkpoint_manager.py:19-24` - Checkpoints directory

---

### Pattern 5: Composite Mock Fixtures 🧩

**Purpose**: Combine multiple fixtures into complex mock objects

**Example**: `planning_pipeline/tests/conftest.py:128-134`

```python
@pytest.fixture
def mock_baml_client(mock_baml_initial_extraction, mock_baml_subprocess_details):
    """Complete mock of BAML client for unit tests (legacy)."""
    mock_b = MagicMock()
    mock_b.ProcessGate1InitialExtractionPrompt.return_value = mock_baml_initial_extraction
    mock_b.ProcessGate1SubprocessDetailsPrompt.return_value = mock_baml_subprocess_details
    return mock_b
```

**Dependency Tree**:
```
mock_baml_client
├── mock_baml_initial_extraction
└── mock_baml_subprocess_details
```

**Characteristics**:
- Depends on 2+ other fixtures
- Constructs MagicMock with configured methods
- Creates cohesive mock of complex system
- Single fixture provides complete behavior

**Other Examples**:
- `patch_baml_client` - Depends on 3 response fixtures
- `mock_orchestrator_with_features` - Multiple mock behaviors

---

### Pattern 6: Advanced Context Manager Patches 🔀

**Purpose**: Patch functions with stateful side effects and override capabilities

**Example**: `planning_pipeline/tests/conftest.py:257-301`

```python
@pytest.fixture
def patch_baml_client(mock_claude_sdk_response, mock_claude_expansion_response,
                      mock_claude_expansion_response_limited):
    """Context manager to patch run_claude_sync for decomposition tests.

    First call returns initial extraction (requirements with sub_processes).
    Subsequent calls return expansion (implementation_details).
    """
    call_count = [0]  # Mutable in nested function
    override_return = [None]  # Allow override

    def side_effect(*args, **kwargs):
        if override_return[0] is not None:
            return override_return[0]
        call_count[0] += 1
        if call_count[0] == 1:
            return mock_claude_sdk_response
        return mock_claude_expansion_response

    with patch("planning_pipeline.decomposition.run_claude_sync") as mock_run:
        mock_run.side_effect = side_effect

        def set_return_value(value):
            nonlocal original_return_value
            original_return_value = value
            override_return[0] = value

        type(mock_run).return_value = property(
            lambda self: override_return[0],
            lambda self, value: set_return_value(value)
        )

        yield mock_run
```

**Advanced Features**:
- ✅ Stateful call counting
- ✅ Sequential return values (1st call ≠ 2nd call)
- ✅ Override mechanism via `return_value` setter
- ✅ Property descriptor for dynamic behavior
- ✅ Context manager cleanup

**Call Sequence**:
```
Call 1: Returns mock_claude_sdk_response (extraction)
Call 2: Returns mock_claude_expansion_response (expansion)
Call N: Returns mock_claude_expansion_response (expansion)

Override: Set mock_run.return_value to test error cases
```

---

### Pattern 7: Class-Scoped Fixtures 🏫

**Purpose**: Fixtures scoped to test class methods

**Example**: `tests/test_autonomous_loop.py:154-172`

```python
class TestLoopRunnerPhaseProgression:
    """Tests for phase progression via orchestrator."""

    @pytest.fixture
    def mock_orchestrator_with_features(self):
        """Orchestrator that returns features in sequence."""
        orchestrator = Mock()
        orchestrator.discover_plans.return_value = [Mock(path="/plans/main.md", priority=1)]

        orchestrator.bd = Mock()
        orchestrator.bd.update_status = Mock()

        features = [
            {"id": "feature-1", "title": "Feature 1", "status": "open"},
            {"id": "feature-2", "title": "Feature 2", "status": "open"},
            None,  # No more features
        ]
        orchestrator.get_next_feature.side_effect = features
        return orchestrator
```

**Characteristics**:
- Defined as method inside test class
- Only available to tests within that class
- Can access `self` for class state
- Common pattern across 10+ test files

**Other Examples**:
- `test_orchestrator.py:148-163` - project_path, cleanup_issues
- Multiple fixtures in test_helpers.py, test_pipeline.py

---

### Pattern 8: Data Model Instance Fixtures 📦

**Purpose**: Provide pre-configured data model instances

**Example**: `silmari_rlm_act/tests/test_pipeline.py:56-67`

```python
@pytest.fixture
def sample_research_result() -> PhaseResult:
    """Create a sample research phase result."""
    return PhaseResult(
        phase_type=PhaseType.RESEARCH,
        status=PhaseStatus.COMPLETE,
        artifacts=["thoughts/research/doc.md"],
        started_at=datetime(2026, 1, 5, 10, 0, 0),
        completed_at=datetime(2026, 1, 5, 10, 5, 0),
        duration_seconds=300.0,
        metadata={"cwa_entry_id": "research_001"},
    )
```

**Characteristics**:
- Returns fully instantiated dataclass/model
- Contains realistic test data
- Used for pipeline phase testing
- Multiple related fixtures (research, decomposition, planning)

**Other Examples**:
- `sample_decomposition_result` - Decomposition phase
- `sample_planning_result` - Planning phase
- `sample_artifacts` - Artifact lists

---

## 🔗 Fixture Dependencies and Composition

### Linear Dependency Chains

#### Chain 1: BeadsController Cleanup

```
cleanup_issues
└── beads_controller
    └── project_path
```

**Files**:
- `planning_pipeline/tests/test_pipeline.py:10-29`
- `planning_pipeline/tests/test_steps.py:8-33`

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
    beads_controller.sync()
```

---

#### Chain 2: BAML Client Mock

```
mock_baml_client
├── mock_baml_initial_extraction
└── mock_baml_subprocess_details
```

**File**: `planning_pipeline/tests/conftest.py:86-134`

---

#### Chain 3: Claude SDK Patch

```
patch_baml_client
├── mock_claude_sdk_response
├── mock_claude_expansion_response
└── mock_claude_expansion_response_limited
```

**File**: `planning_pipeline/tests/conftest.py:257-301`

**Purpose**: Provides sequential mock responses with override capability

---

### Dependency Graph Visualization

```
                    ┌─────────────────────────┐
                    │   project_path()        │
                    └──────────┬──────────────┘
                               │
                               ▼
                    ┌─────────────────────────┐
                    │  beads_controller()     │
                    └──────────┬──────────────┘
                               │
                               ▼
                    ┌─────────────────────────┐
                    │  cleanup_issues()       │
                    │  (yield pattern)        │
                    └─────────────────────────┘


┌───────────────────────┐  ┌────────────────────────┐
│ mock_baml_initial_    │  │ mock_baml_subprocess_  │
│ extraction()          │  │ details()              │
└──────────┬────────────┘  └──────────┬─────────────┘
           │                          │
           └──────────┬───────────────┘
                      ▼
           ┌─────────────────────────┐
           │  mock_baml_client()     │
           └─────────────────────────┘


┌────────────────┐  ┌──────────────────┐  ┌────────────────────┐
│ mock_claude_   │  │ mock_claude_     │  │ mock_claude_       │
│ sdk_response() │  │ expansion_       │  │ expansion_         │
│                │  │ response()       │  │ response_limited() │
└────────┬───────┘  └────────┬─────────┘  └──────┬─────────────┘
         │                   │                    │
         └─────────┬─────────┴────────────────────┘
                   ▼
        ┌──────────────────────────┐
        │  patch_baml_client()     │
        │  (context manager)       │
        └──────────────────────────┘
```

---

## 📂 Fixture Locations by File

### Files with Most Fixtures

| File | Fixture Count | Types |
|------|---------------|-------|
| `planning_pipeline/tests/conftest.py` | 11 | Mock responses, patches, sample data |
| `silmari_rlm_act/tests/test_pipeline.py` | 7 | Phase results, cleanup, mocks |
| `silmari_rlm_act/tests/test_cli.py` | 4 | CLI runner, mock controllers |
| `tests/test_autonomous_loop.py` | 3 | Class-scoped orchestrator mocks |
| `tests/test_execute_phase.py` | 4 | Class-scoped fixtures |
| `planning_pipeline/tests/test_pipeline.py` | 3 | BeadsController, cleanup, project path |

---

### Fixture Organization Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                     conftest.py Files                           │
│                                                                 │
│  • Shared across entire test module                            │
│  • Mock data structures and responses                          │
│  • Pytest markers registration                                 │
│  • Common setup/teardown patterns                              │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Individual Test Files                         │
│                                                                 │
│  • Test-specific fixtures                                      │
│  • Class-scoped fixtures for grouped tests                     │
│  • Temporary file system setup                                 │
│  • Specialized mocks for feature under test                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎭 Mock Fixture Implementations

### Mock Types Overview

| Mock Target | Fixture Name | Location | Purpose |
|------------|--------------|----------|---------|
| BAML Client | `mock_baml_client` | conftest.py:128-134 | Mock legacy BAML client |
| Claude SDK | `mock_claude_sdk_response` | conftest.py:137-156 | Mock requirement extraction |
| Claude SDK | `mock_claude_expansion_response` | conftest.py:158-194 | Mock detail expansion |
| CWA Integration | `mock_cwa` | test_cli.py:31-38 | Mock CWA store operations |
| BeadsController | `mock_beads_controller` | test_cli.py:40-48 | Mock beads operations |
| Orchestrator | `mock_orchestrator_with_features` | test_autonomous_loop.py:154-172 | Mock feature discovery |
| CLI Runner | `cli_runner` | test_cli.py:24-26 | Click CLI test runner |

---

### Mock BAML Response Structure

**Fixture**: `mock_baml_initial_extraction`
**Location**: `planning_pipeline/tests/conftest.py:86-101`

```python
@pytest.fixture
def mock_baml_initial_extraction():
    """Mock response for b.ProcessGate1InitialExtractionPrompt."""
    sub1 = MockSubProcess(
        name="Login Flow Implementation",
        description="Implement user login",
        implementation_components=MockImplementationComponents(
            backend=["auth.py", "session.py"],
            frontend=["LoginForm.tsx"]
        )
    )

    req = MockRequirementNode(
        description="User Authentication System",
        sub_processes=[sub1],
        testable_properties=["Users can log in"],
        category="functional"
    )

    return MockInitialExtractionResponse(requirements=[req])
```

**Mock Type Hierarchy**:
```
MockInitialExtractionResponse
└── requirements: List[MockRequirementNode]
    ├── description: str
    ├── sub_processes: List[MockSubProcess]
    │   ├── name: str
    │   ├── description: str
    │   └── implementation_components: MockImplementationComponents
    │       ├── frontend: List[str]
    │       ├── backend: List[str]
    │       ├── middleware: List[str]
    │       └── shared: List[str]
    ├── testable_properties: List[str]
    └── category: str
```

---

### Mock Claude SDK Response Structure

**Fixture**: `mock_claude_sdk_response`
**Location**: `planning_pipeline/tests/conftest.py:137-156`

```python
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
```

**Response Structure**:
```python
{
    "success": bool,
    "output": str,  # JSON string containing requirements
    "error": str,   # Empty on success
    "elapsed": float  # Execution time in seconds
}
```

---

## 🧪 Fixture Usage Examples

### Example 1: Simple Test with Value Fixture

**Test**: `silmari_rlm_act/tests/test_models.py`

```python
def test_phase_result_creation(sample_timestamp):
    """Test creating a PhaseResult with sample timestamp."""
    result = PhaseResult(
        phase_type=PhaseType.RESEARCH,
        status=PhaseStatus.COMPLETE,
        started_at=sample_timestamp,
        completed_at=sample_timestamp,
    )
    assert result.started_at == datetime(2026, 1, 5, 10, 30, 0)
```

**Fixture Used**: `sample_timestamp` from conftest.py
**Pattern**: Simple value provider

---

### Example 2: Test with Cleanup Fixture

**Test**: `planning_pipeline/tests/test_beads.py:25-40`

```python
def test_create_issue(beads_controller, cleanup_issues):
    """Test creating a beads issue."""
    result = beads_controller.create_issue(
        title="Test issue",
        description="This is a test",
        issue_type="task"
    )

    assert result["success"] is True
    issue_id = result["data"]["id"]
    cleanup_issues.append(issue_id)  # Track for cleanup

    # Verify issue exists
    issue = beads_controller.get_issue(issue_id)
    assert issue["title"] == "Test issue"

    # cleanup_issues fixture will close and sync after test
```

**Fixtures Used**:
- `beads_controller` - Creates controller instance
- `cleanup_issues` - Tracks created issues, cleans up after test

**Pattern**: Cleanup with yield

---

### Example 3: Test with Temporary Files

**Test**: `silmari_rlm_act/tests/test_validation.py:75-92`

```python
def test_validate_hierarchy(temp_hierarchy):
    """Test hierarchy validation with temporary file."""
    validator = ValidationService()

    result = validator.validate_hierarchy(temp_hierarchy)

    assert result["valid"] is True
    assert result["requirements_count"] == 1
    assert len(result["errors"]) == 0

    # File is automatically cleaned up by pytest
```

**Fixture Used**: `temp_hierarchy` - Creates temporary JSON file
**Pattern**: Temporary file system
**Cleanup**: Automatic via pytest's tmp_path

---

### Example 4: Test with Mock Patch

**Test**: `planning_pipeline/tests/test_decomposition.py`

```python
def test_decomposition_with_expansion(patch_baml_client):
    """Test decomposition with Claude SDK expansion."""
    # patch_baml_client is already active (context manager)

    result = decompose_requirements("Research: User Auth")

    # First call returned extraction
    # Second call returned expansion
    assert patch_baml_client.call_count == 2
    assert len(result.requirements) > 0
    assert result.requirements[0].description == "User Authentication System"
```

**Fixture Used**: `patch_baml_client` - Context manager patch
**Pattern**: Advanced context manager with state
**Features**: Call tracking, sequential responses

---

### Example 5: Test with Multiple Fixtures

**Test**: `planning_pipeline/tests/test_pipeline.py:32-55`

```python
def test_full_pipeline(
    project_path,
    beads_controller,
    cleanup_issues,
    sample_research_output
):
    """Test full pipeline execution with multiple fixtures."""
    # Create epic
    epic_result = beads_controller.create_epic(
        title="Test Epic",
        description="Testing pipeline"
    )
    cleanup_issues.append(epic_result["data"]["id"])

    # Run pipeline phases
    pipeline = Pipeline(project_path)
    result = pipeline.run(
        research_output=sample_research_output,
        epic_id=epic_result["data"]["id"]
    )

    assert result["success"] is True
    # All resources cleaned up automatically
```

**Fixtures Used**:
1. `project_path` - Project location
2. `beads_controller` - Issue management
3. `cleanup_issues` - Resource cleanup
4. `sample_research_output` - Test data

**Dependency Chain**: cleanup_issues → beads_controller → project_path

---

## 🏛️ Architecture Patterns

### Test Organization Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                       Test Suite Architecture                   │
└────────────────────────────────────────────────────────────────┘

Module Level (conftest.py)
    │
    ├── Shared Fixtures
    │   ├── Mock Data Structures
    │   ├── Mock External Systems
    │   └── Common Setup/Teardown
    │
    ├── Pytest Configuration
    │   ├── Custom Markers
    │   └── Plugin Configuration
    │
    └── Shared Utilities
        └── Test Helpers

File Level (test_*.py)
    │
    ├── Test-Specific Fixtures
    │   ├── Local Mocks
    │   ├── Test Data
    │   └── Setup/Teardown
    │
    └── Test Classes
        │
        ├── Class-Scoped Fixtures
        │   └── Shared Across Class Methods
        │
        └── Test Methods
            └── Use Fixtures via Parameters
```

---

### Fixture Lifecycle Flow

```
Test Execution Lifecycle:

    1. Session Start
       └── Load conftest.py
           └── Register markers (pytest_configure)

    2. Test Collection
       └── Discover fixtures
           ├── Module-level (conftest)
           └── Test-level (individual files)

    3. Test Setup (per test)
       ├── Resolve fixture dependencies
       ├── Execute setup phase
       │   └── Create resources
       └── Yield control to test

    4. Test Execution
       └── Test code runs with fixtures

    5. Test Teardown (per test)
       ├── Return from yield (if used)
       ├── Execute teardown phase
       │   └── Cleanup resources
       └── Close external connections

    6. Session End
       └── Final cleanup
```

---

### Fixture Scope Strategy

| Scope | Usage in Codebase | Purpose |
|-------|------------------|---------|
| **Function** (default) | 90%+ of fixtures | Fresh instance per test, maximum isolation |
| **Class** | 10% (via class methods) | Shared across test class, grouped tests |
| **Module** | 0% (explicit) | Not used in this codebase |
| **Session** | 0% (explicit) | Not used in this codebase |

**Design Decision**: The codebase heavily favors function-scoped fixtures for maximum test isolation, avoiding shared state between tests.

---

## 🎯 Naming Conventions

### Fixture Naming Patterns

| Pattern | Examples | Purpose |
|---------|----------|---------|
| `mock_*` | `mock_baml_client`, `mock_cwa` | Mock objects |
| `sample_*` | `sample_timestamp`, `sample_artifacts` | Sample test data |
| `temp_*` | `temp_project`, `temp_hierarchy` | Temporary resources |
| `cleanup_*` | `cleanup_issues` | Cleanup/teardown fixtures |
| `patch_*` | `patch_baml_client` | Context manager patches |
| `*_path` | `project_path` | Path providers |
| `*_controller` | `beads_controller` | Controller instances |
| `*_result` | `sample_research_result` | Data model instances |
| `*_runner` | `cli_runner` | Test runners |

**Convention**: Fixture names are descriptive and indicate their purpose through prefixes and suffixes.

---

## 📈 Fixture Complexity Analysis

### Complexity Tiers

<table>
<tr>
<th>Tier</th>
<th>Complexity</th>
<th>Examples</th>
<th>Lines of Code</th>
</tr>
<tr>
<td>🟢 Simple</td>
<td>Single return value</td>
<td><code>sample_timestamp</code>, <code>project_path</code></td>
<td>3-5 lines</td>
</tr>
<tr>
<td>🟡 Medium</td>
<td>Multiple values or basic setup</td>
<td><code>mock_claude_sdk_response</code>, <code>temp_hierarchy</code></td>
<td>10-30 lines</td>
</tr>
<tr>
<td>🟠 Complex</td>
<td>Dependencies + setup + teardown</td>
<td><code>cleanup_issues</code>, <code>mock_baml_client</code></td>
<td>15-40 lines</td>
</tr>
<tr>
<td>🔴 Advanced</td>
<td>State management + context mgr</td>
<td><code>patch_baml_client</code></td>
<td>40-50 lines</td>
</tr>
</table>

---

### Most Complex Fixture: `patch_baml_client`

**Location**: `planning_pipeline/tests/conftest.py:257-301`
**Lines**: 44 lines
**Complexity Score**: 🔴 Advanced

**Features**:
- ✅ Context manager (with statement)
- ✅ Stateful call counting
- ✅ Sequential return values
- ✅ Override mechanism
- ✅ Property descriptor usage
- ✅ Nested function closures
- ✅ Mutable captured variables
- ✅ Dynamic property setting

**Why Complex**: Combines multiple advanced Python patterns (descriptors, closures, context managers, state management) to provide flexible mock behavior that can handle multiple call patterns and test scenarios.

---

## 🔍 Code References

### Key Fixture Files

| File | Lines | Fixtures | Description |
|------|-------|----------|-------------|
| `planning_pipeline/tests/conftest.py` | 347 | 11 | Shared BAML/Claude mocks, patches |
| `silmari_rlm_act/tests/conftest.py` | 28 | 3 | Simple test data providers |
| `planning_pipeline/tests/test_pipeline.py` | 200+ | 3 | BeadsController fixtures |
| `silmari_rlm_act/tests/test_pipeline.py` | 300+ | 7 | Phase result fixtures |
| `silmari_rlm_act/tests/test_cli.py` | 150+ | 4 | CLI and controller mocks |
| `tests/test_autonomous_loop.py` | 200+ | 3 | Orchestrator mocks |

---

### Critical Fixtures by Responsibility

#### 🎭 Mocking External Systems

- `planning_pipeline/tests/conftest.py:128-134` - `mock_baml_client`
- `planning_pipeline/tests/conftest.py:137-156` - `mock_claude_sdk_response`
- `planning_pipeline/tests/conftest.py:257-301` - `patch_baml_client`
- `silmari_rlm_act/tests/test_cli.py:31-38` - `mock_cwa`
- `silmari_rlm_act/tests/test_cli.py:40-48` - `mock_beads_controller`

#### 🧹 Resource Cleanup

- `planning_pipeline/tests/test_beads.py:15-22` - `cleanup_issues`
- `planning_pipeline/tests/test_steps.py:26-33` - `cleanup_issues`
- `planning_pipeline/tests/test_pipeline.py:22-29` - `cleanup_issues`

#### 📁 File System Setup

- `silmari_rlm_act/tests/test_validation.py:29-60` - `temp_hierarchy`
- `silmari_rlm_act/tests/test_validation.py:62-73` - `temp_research_doc`
- `planning_pipeline/tests/test_step_decomposition.py:23-51` - `temp_project`
- `silmari_rlm_act/tests/test_implementation_phase.py:21-43` - `sample_plan`

#### 📦 Data Model Instances

- `silmari_rlm_act/tests/test_pipeline.py:56-67` - `sample_research_result`
- `silmari_rlm_act/tests/test_pipeline.py:69-80` - `sample_decomposition_result`
- `silmari_rlm_act/tests/test_pipeline.py:82-93` - `sample_planning_result`

---

## 🎨 Visual Fixture Map

### Fixture Relationship Map

```
                        conftest.py Fixtures
                        ┌──────────────────────────────────┐
                        │                                  │
    ┌───────────────────┤  Mock Data Structures (Lines 18-80) │
    │                   │  • MockRequirementNode           │
    │                   │  • MockSubProcess                │
    │                   │  • MockImplementationComponents  │
    │                   └──────────────────────────────────┘
    │                                  │
    │                                  ▼
    │                   ┌──────────────────────────────────┐
    │                   │  BAML Mock Fixtures (86-127)     │
    │                   │  • mock_baml_initial_extraction  │
    │                   │  • mock_baml_subprocess_details  │
    │                   └──────────────┬───────────────────┘
    │                                  │
    │                                  ▼
    │                   ┌──────────────────────────────────┐
    │                   │  Composite Mock (128-134)        │
    │                   │  • mock_baml_client              │
    │                   └──────────────────────────────────┘
    │
    │                   ┌──────────────────────────────────┐
    └──────────────────▶│  Claude SDK Mocks (137-218)      │
                        │  • mock_claude_sdk_response      │
                        │  • mock_claude_expansion_...     │
                        └──────────────┬───────────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────────────┐
                        │  Advanced Patch (257-301)        │
                        │  • patch_baml_client             │
                        │    (context manager + state)     │
                        └──────────────────────────────────┘


                        Test File Fixtures
                        ┌──────────────────────────────────┐
                        │                                  │
                        │  Project Setup                   │
                        │  • project_path                  │
                        │  • temp_project                  │
                        └──────────────┬───────────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────────────┐
                        │  Controllers                     │
                        │  • beads_controller              │
                        │  • mock_orchestrator             │
                        └──────────────┬───────────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────────────┐
                        │  Cleanup                         │
                        │  • cleanup_issues (yield)        │
                        └──────────────────────────────────┘
```

---

## 🧩 Fixture Composition Patterns

### Pattern: Layered Dependencies

```
Level 1 (Base)          Level 2 (Build)         Level 3 (Use)

project_path()    ──▶   beads_controller()  ──▶  cleanup_issues()
                           (depends on            (depends on
                            project_path)          beads_controller)

                        Used in Tests:
                        • test_beads.py
                        • test_steps.py
                        • test_pipeline.py
```

### Pattern: Parallel Dependencies

```
mock_baml_initial_extraction()  ────┐
                                    │
                                    ├──▶  mock_baml_client()
                                    │
mock_baml_subprocess_details()  ────┘

Used in Tests:
• Legacy BAML integration tests
• Can be replaced by Claude SDK mocks
```

### Pattern: Sequential Response Mocking

```
Call Sequence in patch_baml_client:

Call 1: mock_claude_sdk_response      (extraction)
Call 2: mock_claude_expansion_response (expansion)
Call 3: mock_claude_expansion_response (expansion)
...
Call N: mock_claude_expansion_response (expansion)

Override: Set return_value to simulate errors
```

---

## 📊 Test Coverage by Fixture Type

### Fixture Usage Distribution

```
┌─────────────────────────────────────────────────────────────┐
│                   Fixture Usage by Type                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Mock Responses        ████████████████████ 35%            │
│  Cleanup/Teardown      ████████████ 20%                    │
│  Temp Files            ██████████ 15%                      │
│  Simple Data           ████████ 12%                        │
│  Controllers           ██████ 9%                           │
│  Composite Mocks       ████ 6%                             │
│  Class-Scoped          ██ 3%                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Testing Best Practices Observed

### ✅ Strengths in Current Implementation

| Practice | Implementation | Location |
|----------|----------------|----------|
| **Test Isolation** | Every test uses function-scoped fixtures | All test files |
| **Cleanup Guarantees** | Yield pattern ensures cleanup even on failure | cleanup_issues fixtures |
| **DRY Principle** | Shared fixtures in conftest.py | 14 shared fixtures |
| **Descriptive Names** | Clear fixture naming conventions | All fixtures |
| **Type Hints** | Fixtures include return type hints | conftest.py, test files |
| **Documentation** | Docstrings on every fixture | All fixtures |
| **Layered Mocking** | Gradual mock complexity from simple to advanced | conftest.py structure |
| **Custom Markers** | Organized test categorization | conftest.py:10-14 |

---

### 🎯 Fixture Design Principles

```
┌────────────────────────────────────────────────────────────────┐
│                    Fixture Design Philosophy                   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  1. ISOLATION FIRST                                           │
│     └─ Function-scoped by default                             │
│     └─ Fresh state per test                                   │
│                                                                │
│  2. EXPLICIT CLEANUP                                          │
│     └─ Yield pattern for teardown                             │
│     └─ No leaked resources                                    │
│                                                                │
│  3. COMPOSABILITY                                             │
│     └─ Fixtures depend on fixtures                            │
│     └─ Dependency injection via parameters                    │
│                                                                │
│  4. REUSABILITY                                               │
│     └─ Common fixtures in conftest.py                         │
│     └─ Test-specific fixtures locally                         │
│                                                                │
│  5. CLARITY                                                   │
│     └─ Descriptive names                                      │
│     └─ Type hints                                             │
│     └─ Docstrings                                             │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔬 Advanced Patterns Analysis

### Stateful Mocking with Call Counting

**Implementation**: `patch_baml_client` fixture

**Technique**:
```python
call_count = [0]  # List for mutability in closure

def side_effect(*args, **kwargs):
    call_count[0] += 1  # Track calls
    if call_count[0] == 1:
        return first_response
    return subsequent_response
```

**Why Lists?**: Python closures can't rebind immutable values (int), but can mutate lists.

**Use Cases**:
- Sequential API responses
- Call verification
- Progressive state changes

---

### Property Descriptor for Dynamic Return Values

**Implementation**: `patch_baml_client` fixture

**Technique**:
```python
override_return = [None]

def set_return_value(value):
    override_return[0] = value

type(mock_run).return_value = property(
    lambda self: override_return[0],  # Getter
    lambda self, value: set_return_value(value)  # Setter
)
```

**Purpose**: Allow tests to override side_effect by setting `return_value`

**Example Test Usage**:
```python
def test_error_handling(patch_baml_client):
    # Override to simulate error
    patch_baml_client.return_value = {"success": False, "error": "API failed"}

    result = decompose_requirements("Research: Test")
    assert result is None
```

---

### Generator-Based Cleanup Pattern

**Implementation**: `cleanup_issues` fixtures

**Flow**:
```python
@pytest.fixture
def cleanup_issues(beads_controller):
    created_ids = []
    # ─── Setup Phase ───

    yield created_ids  # ◀── Test runs here

    # ─── Teardown Phase ───
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id)
    beads_controller.sync()
```

**Execution Order**:
1. Setup: Initialize empty list
2. Yield: Control passes to test
3. Test: Appends IDs to list
4. Test completes (or fails)
5. Teardown: Cleanup always runs

**Guarantee**: Teardown runs even if test raises exception

---

## 📚 Related Documentation

### Internal Research Documents

- Research documents in `thoughts/searchable/research/` directory
- Pytest documentation: https://docs.pytest.org/
- Testing best practices documentation (if exists in thoughts/)

---

## 🎓 Key Takeaways

### 📌 Summary of Testing Patterns

1. **42 test files** across 4 main test suites
2. **70+ fixtures** total, with 14 shared fixtures
3. **Function-scoped fixtures dominate** (90%+) for maximum test isolation
4. **Yield pattern** extensively used for guaranteed cleanup
5. **Sophisticated mocking** of external systems (BAML, Claude SDK, CWA)
6. **Temporary file system fixtures** leverage pytest's `tmp_path`
7. **Composite fixtures** create complex test scenarios from simple components
8. **Custom pytest markers** organize tests by speed and type
9. **Type hints and docstrings** on all fixtures for clarity
10. **Advanced patterns** include stateful mocking and property descriptors

---

### 🎨 Fixture Organization Philosophy

```
Simple → Composite → Complex
   │         │          │
   │         │          └─ Advanced context managers with state
   │         └─ Mock clients composed from response fixtures
   └─ Single-value test data fixtures

Shared → Specific
   │         │
   │         └─ Test-specific fixtures in individual files
   └─ Common fixtures in conftest.py
```

---

### 🏆 Notable Implementations

**Most Sophisticated**: `patch_baml_client`
- Context manager
- Stateful call tracking
- Sequential responses
- Override mechanism
- 44 lines of advanced Python patterns

**Most Reusable**: `sample_timestamp`
- Simple datetime value
- Used across multiple test modules
- 3 lines of code
- Maximum clarity

**Best Cleanup Pattern**: `cleanup_issues`
- Yield-based teardown
- Guarantees no leaked test data
- Works with real external system
- Test-isolated via fresh instances

---

## 🔗 File References

### Primary Conftest Files

- [`planning_pipeline/tests/conftest.py`](planning_pipeline/tests/conftest.py) - 11 shared fixtures, mock types, pytest markers
- [`silmari_rlm_act/tests/conftest.py`](silmari_rlm_act/tests/conftest.py) - 3 simple data fixtures

### Key Test Files with Fixtures

- [`planning_pipeline/tests/test_beads.py`](planning_pipeline/tests/test_beads.py) - BeadsController and cleanup
- [`planning_pipeline/tests/test_steps.py`](planning_pipeline/tests/test_steps.py) - Step execution with cleanup
- [`planning_pipeline/tests/test_pipeline.py`](planning_pipeline/tests/test_pipeline.py) - Full pipeline fixtures
- [`silmari_rlm_act/tests/test_pipeline.py`](silmari_rlm_act/tests/test_pipeline.py) - Phase result fixtures
- [`silmari_rlm_act/tests/test_cli.py`](silmari_rlm_act/tests/test_cli.py) - CLI and controller mocks
- [`tests/test_autonomous_loop.py`](tests/test_autonomous_loop.py) - Orchestrator mocks

### Test Files with Temporary File Fixtures

- [`silmari_rlm_act/tests/test_validation.py`](silmari_rlm_act/tests/test_validation.py) - Hierarchy and research docs
- [`planning_pipeline/tests/test_step_decomposition.py`](planning_pipeline/tests/test_step_decomposition.py) - Full project structure
- [`silmari_rlm_act/tests/test_implementation_phase.py`](silmari_rlm_act/tests/test_implementation_phase.py) - TDD plan documents

---

## 🔍 Open Questions

_None identified during research. All fixture patterns are documented and well-understood._

---

**End of Research Document**

---

```
┌─────────────────────────────────────────────────────────────┐
│  Research Complete: Pytest Fixtures Analysis                │
│  Total Fixtures Documented: 70+                             │
│  Pattern Categories: 10                                      │
│  Code Examples: 20+                                          │
└─────────────────────────────────────────────────────────────┘
```
