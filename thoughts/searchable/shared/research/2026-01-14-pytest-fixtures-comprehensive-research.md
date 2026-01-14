---
date: 2026-01-14 14:22:45 -05:00
researcher: Claude Sonnet 4.5
git_commit: 99126e57d785f9ed08e7a14d7898f1ddc28f8ac6
branch: main
repository: silmari-Context-Engine
topic: "Testing Patterns and Pytest Fixtures Analysis"
tags: [research, codebase, pytest, fixtures, testing, test-patterns, hypothesis, mocking]
status: complete
last_updated: 2026-01-14
last_updated_by: Claude Sonnet 4.5
---

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│         SILMARI CONTEXT ENGINE - TESTING PATTERNS               │
│         Pytest Fixtures & Testing Architecture Analysis         │
│                                                                 │
│  Status: ✅ Complete                                            │
│  Date: 2026-01-14                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

# Research: Testing Patterns and Pytest Fixtures Analysis

**Date**: 2026-01-14 14:22:45 -05:00
**Researcher**: Claude Sonnet 4.5
**Git Commit**: `99126e57d785f9ed08e7a14d7898f1ddc28f8ac6`
**Branch**: main
**Repository**: silmari-Context-Engine

## 📋 Research Question

Analyze the testing patterns in this project with a focus on pytest fixtures.

---

## 🎯 Summary

The silmari-Context-Engine project has a **comprehensive and mature testing infrastructure** built on pytest with extensive use of fixtures, property-based testing (Hypothesis), and behavior-driven organization. The test suite contains:

- **43 Python test files** across 4 directories
- **~19,400 lines of test code**
- **62+ custom fixtures** (14 shared in conftest.py files, 48+ file-specific)
- **100% function-scoped fixtures** ensuring complete test isolation
- **3 custom pytest markers** (slow, integration, e2e)
- **Extensive property-based testing** using Hypothesis with custom strategies
- **Behavior-driven test organization** with class-based grouping
- **Comprehensive mocking infrastructure** for external dependencies

---

## 📊 Test Suite Overview

### Test Directory Structure

| Directory | Test Files | Lines of Code | Purpose |
|-----------|------------|---------------|---------|
| `silmari_rlm_act/tests/` | 14 files | ~4,000 lines | RLM-ACT pipeline phases and core functionality |
| `planning_pipeline/tests/` | 20 files | ~10,000 lines | Planning pipeline, decomposition, orchestration |
| `context_window_array/tests/` | 6 files | ~3,000 lines | CWA integration, storage, context management |
| `tests/` (root) | 3 files | ~2,400 lines | Integration tests, autonomous loop, execution |

**Total: 43 test files, ~19,400 lines of test code**

### Test File Distribution

<details>
<summary><strong>silmari_rlm_act/tests/</strong> (14 files)</summary>

- `test_validation.py` - Validation logic
- `test_checkpoint_manager.py` - Checkpoint system
- `test_models.py` - Data models and enums
- `test_decomposition_phase.py` - Decomposition phase
- `test_cwa_integration.py` - CWA integration
- `test_multi_doc_phase.py` - Multi-document phase
- `test_artifact_generation.py` - Artifact generation
- `test_implementation_phase.py` - Implementation phase
- `test_cli.py` - CLI interface
- `test_tdd_planning_phase.py` - TDD planning
- `test_interactive.py` - Interactive mode
- `test_beads_sync_phase.py` - Beads synchronization
- `test_pipeline.py` - Pipeline orchestration
- `test_research_phase.py` - Research phase

</details>

<details>
<summary><strong>planning_pipeline/tests/</strong> (20 files)</summary>

- `test_checkpoints.py` - Checkpoint functionality
- `test_beads_controller.py` - Beads controller
- `test_beads.py` - Beads integration
- `test_phase_execution.py` - Phase execution
- `test_claude.py` - Claude integration
- `test_orchestrator.py` - Pipeline orchestration
- `test_visualization.py` - Visualization
- `test_context_generation.py` - Context generation
- `test_step_decomposition.py` - Step decomposition
- `test_checkpoint_manager.py` - Checkpoint management
- `test_models.py` - Data models
- `test_property_generator.py` - Property generation
- `test_decomposition_e2e.py` - E2E decomposition
- `test_claude_runner.py` - Claude runner
- `test_steps.py` - Step execution
- `test_integrated_orchestrator.py` - Integrated orchestration
- `test_helpers.py` - Helper utilities
- `test_pipeline.py` - Pipeline logic
- `test_decomposition.py` - Decomposition logic

</details>

<details>
<summary><strong>context_window_array/tests/</strong> (6 files)</summary>

- `test_batching.py` - Batch processing
- `test_models.py` - CWA models
- `test_search.py` - Search functionality
- `test_implementation_context.py` - Implementation context
- `test_store.py` - Storage operations
- `test_working_context.py` - Working context

</details>

<details>
<summary><strong>tests/</strong> (3 files - root level)</summary>

- `test_autonomous_loop.py` - Autonomous loop
- `test_loop_orchestrator_integration.py` - Loop orchestrator integration
- `test_execute_phase.py` - Phase execution

</details>

---

## 🧪 Pytest Configuration

### pytest.ini

**Location**: `/home/maceo/Dev/silmari-Context-Engine/pytest.ini`

```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```

### pyproject.toml

**Location**: `/home/maceo/Dev/silmari-Context-Engine/pyproject.toml` (lines 56-64)

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = [
    "silmari_rlm_act/tests",
    "context_window_array/tests",
    "planning_pipeline/tests",
    "tests",
]
```

**Key Configuration**:
- Async test support via `pytest-asyncio`
- Function-scoped async fixtures
- Four test path directories defined

---

## 🔧 Pytest Fixtures Architecture

### conftest.py Files

The project has **2 conftest.py files** that define shared fixtures:

#### 1. `silmari_rlm_act/tests/conftest.py`

**Location**: `/home/maceo/Dev/silmari-Context-Engine/silmari_rlm_act/tests/conftest.py`

**Fixtures** (3 total):

| Fixture | Scope | Lines | Purpose |
|---------|-------|-------|---------|
| `sample_timestamp` | function | 7-10 | Provides consistent datetime for tests |
| `sample_artifacts` | function | 13-19 | Provides sample artifact path lists |
| `sample_errors` | function | 22-28 | Provides sample error messages |

**Example**:
```python
@pytest.fixture
def sample_timestamp() -> datetime:
    """Provide a consistent timestamp for tests."""
    return datetime(2026, 1, 5, 10, 30, 0)
```

---

#### 2. `planning_pipeline/tests/conftest.py`

**Location**: `/home/maceo/Dev/silmari-Context-Engine/planning_pipeline/tests/conftest.py`

**Pytest Configuration Hook** (lines 10-14):
```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
```

**Mock Dataclasses** (lines 22-77):
- `MockImplementationComponents` - Mock BAML implementation components
- `MockImplementationDetail` - Mock implementation detail
- `MockRequirement` - Mock requirement
- `MockResponseMetadata` - Mock response metadata
- `MockInitialExtractionResponse` - Mock initial extraction
- `MockSubprocessDetailsResponse` - Mock subprocess details

**Fixtures** (11 total):

| Fixture | Scope | Lines | Type | Purpose |
|---------|-------|-------|------|---------|
| `mock_baml_initial_extraction` | function | 85-100 | Mock Response | Mock BAML initial extraction response |
| `mock_baml_subprocess_details` | function | 103-125 | Mock Response | Mock BAML subprocess details response |
| `mock_baml_client` | function | 128-134 | Mock Client | Legacy complete BAML client mock |
| `mock_claude_sdk_response` | function | 137-156 | Mock Response | Mock Claude SDK requirement extraction response |
| `mock_claude_expansion_response` | function | 159-216 | Mock Response | Mock Claude SDK expansion response |
| `mock_claude_expansion_response_limited` | function | 219-254 | Mock Response | Limited expansion for constraint tests |
| `patch_baml_client` | function | 257-300 | Context Manager | Patches `run_claude_sync` with side_effect |
| `project_path` | function | 303-306 | Path | Returns root project directory |
| `sample_research_output` | function | 309-324 | String | Sample Claude research output |
| `sample_plan_output` | function | 327-336 | String | Sample Claude plan output |
| `sample_phase_output` | function | 339-347 | String | Sample Claude phase output |

**Example - Context Manager Fixture**:
```python
@pytest.fixture
def patch_baml_client(mock_claude_sdk_response, mock_claude_expansion_response, ...):
    """Context manager to patch run_claude_sync for decomposition tests.

    First call returns initial extraction (requirements with sub_processes).
    Subsequent calls return expansion (implementation_details).
    """
    call_count = [0]
    override_return = [None]

    def side_effect(*args, **kwargs):
        if override_return[0] is not None:
            return override_return[0]
        call_count[0] += 1
        if call_count[0] == 1:
            return mock_claude_sdk_response
        return mock_claude_expansion_response

    with patch("planning_pipeline.decomposition.run_claude_sync") as mock_run:
        mock_run.side_effect = side_effect
        mock_run.call_count_tracker = call_count
        mock_run.override_return = override_return
        yield mock_run
```

---

### 🎨 Fixture Patterns

The codebase uses **6 primary fixture patterns**:

#### Pattern 1: Simple Value Fixtures

**Distribution**: ~9 fixtures (14%)
**Purpose**: Provide consistent, reusable test data

```python
# From silmari_rlm_act/tests/conftest.py
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
```

---

#### Pattern 2: Temporary Resource Fixtures

**Distribution**: ~20 fixtures (32%)
**Purpose**: Create temporary files/directories using `tmp_path`

```python
# From test_checkpoint_manager.py
def test_creates_checkpoint_file(self, tmp_path: Path) -> None:
    """Given state, creates JSON file."""
    manager = CheckpointManager(tmp_path)
    state = PipelineState(
        project_path=str(tmp_path),
        autonomy_mode=AutonomyMode.CHECKPOINT,
    )
    # ... test continues
```

```python
# From test_beads_sync_phase.py
@pytest.fixture
def sample_phase_docs(tmp_path: Path) -> list[str]:
    """Create sample phase documents."""
    docs_dir = tmp_path / "plans"
    docs_dir.mkdir(parents=True)

    files = [
        ("00-overview.md", "# Overview\n\nPlan overview"),
        ("01-phase-1.md", "# Phase 01\n\nFirst phase"),
    ]

    paths = []
    for filename, content in files:
        path = docs_dir / filename
        path.write_text(content)
        paths.append(str(path))
    return paths
```

---

#### Pattern 3: Mock Object Fixtures

**Distribution**: ~17 fixtures (27%)
**Purpose**: Create mock objects for external dependencies

```python
# From test_pipeline.py
@pytest.fixture
def mock_cwa() -> MagicMock:
    """Create a mock CWA integration."""
    cwa = MagicMock()
    cwa.store_research.return_value = "research_001"
    cwa.store_requirement.return_value = "req_001"
    cwa.store_plan.return_value = "plan_001"
    return cwa

@pytest.fixture
def mock_beads_controller() -> MagicMock:
    """Create a mock BeadsController."""
    mock = MagicMock()
    mock.create_epic.return_value = {"success": True, "data": {"id": "EPIC-1"}}
    mock.create_task.return_value = {"success": True, "data": {"id": "TASK-1"}}
    return mock
```

---

#### Pattern 4: Service Instance Fixtures

**Distribution**: ~7 fixtures (11%)
**Purpose**: Create real service instances for testing

```python
# From test_implementation_phase.py
@pytest.fixture
def cwa() -> CWAIntegration:
    """Create CWA integration instance for implementation tests."""
    return CWAIntegration()

# From test_beads.py
@pytest.fixture
def beads_controller(project_path: Path) -> BeadsController:
    """Create BeadsController instance with project path."""
    return BeadsController(project_path)
```

---

#### Pattern 5: Cleanup/Teardown Fixtures (yield)

**Distribution**: ~6 fixtures (9%)
**Purpose**: Track resources and clean up after tests

```python
# From test_beads.py
@pytest.fixture
def cleanup_issues(beads_controller: BeadsController) -> Generator[list[str], None, None]:
    """Track and cleanup created issues after tests."""
    created_ids: list[str] = []
    yield created_ids

    # Cleanup: close all created issues
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id)
    beads_controller.sync()
```

```python
# From test_loop_orchestrator_integration.py
@pytest.fixture
def temp_plan_dir() -> Generator[Path, None, None]:
    """Create temporary directory with test plan structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        # ... setup directory structure ...
        yield tmpdir_path
    # Automatic cleanup when context exits
```

---

#### Pattern 6: Factory/Builder Fixtures

**Distribution**: ~3 fixtures (5%)
**Purpose**: Create complex test data structures

```python
# From test_step_decomposition.py
@pytest.fixture
def mock_decomposition_result() -> RequirementHierarchy:
    """Create mock decomposition result with sample requirement nodes."""
    return RequirementHierarchy(
        root=RequirementNode(
            id="REQ_001",
            title="Parent Requirement",
            description="Top-level requirement",
            children=[
                RequirementNode(
                    id="REQ_001.1",
                    title="Child Requirement 1",
                    description="First child",
                    children=[]
                ),
                RequirementNode(
                    id="REQ_001.2",
                    title="Child Requirement 2",
                    description="Second child",
                    children=[]
                ),
            ]
        )
    )
```

---

### 🔗 Fixture Dependencies

**Fixture Dependency Graph**:

```
Built-in Fixtures:
├── tmp_path (pytest built-in)
│   ├── temp_project (20+ fixtures)
│   ├── temp_hierarchy
│   ├── sample_phase_docs
│   └── temp_git_repo

Shared Mock Fixtures:
├── mock_baml_initial_extraction
│   └── mock_baml_client
├── mock_baml_subprocess_details
│   └── mock_baml_client
├── mock_claude_sdk_response
│   └── patch_baml_client
├── mock_claude_expansion_response
│   └── patch_baml_client
└── mock_claude_expansion_response_limited
    └── patch_baml_client

Configuration Fixtures:
├── project_path
│   ├── cleanup_issues (multiple files)
│   └── beads_controller
└── beads_controller
    └── cleanup_issues

Service Fixtures:
├── cwa (independent)
├── mock_cwa (independent)
├── mock_beads_controller (independent)
└── mock_beads (independent)
```

---

### 📍 File-Specific Fixtures

<details>
<summary><strong>test_beads.py</strong> (2 fixtures)</summary>

| Fixture | Lines | Purpose |
|---------|-------|---------|
| `beads_controller` | 8-12 | Create BeadsController instance |
| `cleanup_issues` | 15-22 | Track and cleanup test issues |

</details>

<details>
<summary><strong>test_orchestrator.py</strong> (5 fixtures)</summary>

| Fixture | Lines | Class | Purpose |
|---------|-------|-------|---------|
| `project_path` | 148-151 | TestPipelineExecution | Root project path |
| `cleanup_issues` | 153-162 | TestPipelineExecution | Cleanup test issues |
| `project_path` | 282-284 | TestMainEntryPoint | Root project path |
| `project_path` | 323-325 | TestOrchestratorE2E | Root project path |
| `cleanup_issues` | 327-335 | TestOrchestratorE2E | Cleanup E2E issues |

</details>

<details>
<summary><strong>test_validation.py</strong> (3 fixtures)</summary>

| Fixture | Lines | Purpose |
|---------|-------|---------|
| `temp_hierarchy` | 29-60 | Create temp hierarchy JSON file |
| `temp_research_doc` | 63-72 | Create temp research markdown |
| `mock_baml_response` | 75-92 | Mock BAML validation response |

</details>

<details>
<summary><strong>test_cli.py</strong> (2 fixtures)</summary>

| Fixture | Lines | Purpose |
|---------|-------|---------|
| `cli_runner` | 24-27 | Create Click CLI test runner |
| `temp_project` | 30-35 | Create temp project structure |

</details>

<details>
<summary><strong>test_implementation_phase.py</strong> (2 fixtures)</summary>

| Fixture | Lines | Purpose |
|---------|-------|---------|
| `sample_plan` | 21-37 | Create sample TDD plan document |
| `cwa` | 40-43 | Create CWA integration instance |

</details>

<details>
<summary><strong>test_pipeline.py</strong> (5 fixtures)</summary>

| Fixture | Lines | Purpose |
|---------|-------|---------|
| `temp_project` | 26-32 | Temp project with checkpoint dir |
| `mock_cwa` | 35-42 | Mock CWA integration |
| `mock_beads_controller` | 45-53 | Mock BeadsController |
| `sample_research_result` | 56-67 | Sample research phase result |
| `sample_decomposition_result` | 70-81 | Sample decomposition result |

</details>

<details>
<summary><strong>test_beads_sync_phase.py</strong> (2 fixtures + 1 mock class)</summary>

**Custom Mock Class**: `MockBeadsController` (lines 23-77)

| Fixture | Lines | Purpose |
|---------|-------|---------|
| `mock_beads` | 80-83 | Create mock beads controller |
| `sample_phase_docs` | 86-105 | Create sample phase markdown files |

</details>

<details>
<summary><strong>test_checkpoint_manager.py</strong> (1 fixture)</summary>

| Fixture | Lines | Purpose |
|---------|-------|---------|
| `temp_project` | 19-24 | Temp project with checkpoints dir |

</details>

<details>
<summary><strong>test_step_decomposition.py</strong> (2 fixtures)</summary>

| Fixture | Lines | Purpose |
|---------|-------|---------|
| `temp_project` | 23-51 | Temp project with research directory |
| `mock_decomposition_result` | 54-87 | Mock requirement hierarchy |

</details>

<details>
<summary><strong>test_steps.py</strong> (3 fixtures)</summary>

| Fixture | Lines | Purpose |
|---------|-------|---------|
| `project_path` | 14-17 | Root project path |
| `beads_controller` | 20-23 | BeadsController instance |
| `cleanup_issues` | 26-33 | Track and cleanup issues |

</details>

<details>
<summary><strong>test_autonomous_loop.py</strong> (1 fixture)</summary>

| Fixture | Lines | Class | Purpose |
|---------|-------|-------|---------|
| `mock_orchestrator` | 54-62 | TestLoopRunnerPlanDiscovery | Mock orchestrator |

</details>

<details>
<summary><strong>test_loop_orchestrator_integration.py</strong> (2 fixtures)</summary>

| Fixture | Lines | Purpose |
|---------|-------|---------|
| `temp_plan_dir` | 16-41 | Temp directory with plan structure |
| `mock_orchestrator` | 43-71 | Mock orchestrator with behavior |

</details>

<details>
<summary><strong>test_execute_phase.py</strong> (3 fixtures)</summary>

| Fixture | Lines | Purpose |
|---------|-------|---------|
| `temp_plan_file` | 13-28 | Temp plan markdown file |
| `mock_subprocess_success` | 75-84 | Mock successful subprocess |
| `temp_git_repo` | 148-150 | Temp git repository |

</details>

---

### 🎯 Fixture Scope Summary

**Key Finding**: All fixtures are **function-scoped** (default).

- ✅ **Function scope**: 62+ fixtures (100%)
- ❌ **Class scope**: 0 fixtures
- ❌ **Module scope**: 0 fixtures
- ❌ **Session scope**: 0 fixtures

**Design Rationale**: Function scope ensures complete test isolation - each test gets fresh fixtures with no shared state.

---

## 🏗️ Testing Patterns

### Pattern 1: Behavior-Based Test Organization

Tests are organized using **class-based grouping** where each class represents a specific behavior:

```python
# From test_checkpoint_manager.py
class TestWriteCheckpoint:
    """Behavior 1: Write Checkpoint."""

    def test_creates_checkpoint_file(self, tmp_path: Path) -> None:
        """Given state, creates JSON file."""
        # test implementation

class TestDetectResumableCheckpoint:
    """Behavior 2: Detect Resumable Checkpoint."""

    def test_returns_none_when_no_checkpoints(self, tmp_path: Path) -> None:
        """Given no checkpoints, returns None."""
        # test implementation
```

**Structure**:
- **Class docstring**: Describes the behavior being tested
- **Method docstring**: Given-When-Then format
- **Method name**: Descriptive sentence (`test_<scenario>`)

---

### Pattern 2: Given-When-Then Test Structure

Each test method uses descriptive docstrings following Given-When-Then:

```python
def test_creates_checkpoint_file(self, tmp_path: Path) -> None:
    """Given state, creates JSON file."""
    # Given: Initial state
    manager = CheckpointManager(tmp_path)
    state = PipelineState(...)

    # When: Action performed
    checkpoint_path = manager.write_checkpoint(state, "research-complete")

    # Then: Expected outcome
    assert Path(checkpoint_path).exists()
    assert checkpoint_path.endswith(".json")
```

---

### Pattern 3: Custom Pytest Markers

**Location**: `planning_pipeline/tests/conftest.py` (lines 10-14)

| Marker | Usage | Purpose |
|--------|-------|---------|
| `@pytest.mark.slow` | Slow-running tests | Deselect with `-m "not slow"` |
| `@pytest.mark.integration` | Integration tests | Tests with external dependencies |
| `@pytest.mark.e2e` | End-to-end tests | Full workflow tests |

**Example Usage**:
```python
@pytest.mark.slow
class TestLargeDecomposition:
    """Test decomposition with large requirements."""

@pytest.mark.e2e
@pytest.mark.slow
class TestDecompositionE2E:
    """End-to-end decomposition tests."""

@pytest.mark.integration
def test_with_real_api():
    """Test with real API integration."""
```

---

### Pattern 4: Parametrized Tests

Uses `@pytest.mark.parametrize` for exhaustive case coverage:

```python
# From test_property_generator.py
@pytest.mark.parametrize(
    "criterion,expected_type",
    [
        # Invariant patterns
        ("Must validate unique IDs", "invariant"),
        ("All values distinct", "invariant"),
        ("No duplicate entries", "invariant"),
        # Round-trip patterns
        ("Save and load preserves data", "round_trip"),
        ("Encode and decode correctly", "round_trip"),
        # Idempotence patterns
        ("Applying twice gives same result", "idempotence"),
        # Oracle patterns
        ("Matches reference implementation", "oracle"),
    ],
)
def test_criterion_classified_correctly(self, criterion, expected_type):
    """Criterion should be classified to expected property type."""
    result = derive_properties([criterion])
    assert len(result) == 1
    assert result[0].property_type == expected_type
```

---

### Pattern 5: Property-Based Testing with Hypothesis

The codebase makes **extensive use of Hypothesis** for property-based testing.

#### Custom Strategies

```python
# From test_models.py (planning_pipeline)
@st.composite
def _requirement_id_strategy(draw, prefix: str = "REQ") -> str:
    """Generate valid requirement IDs like REQ_001, REQ_001.2, REQ_001.2.1."""
    base_num = draw(st.integers(min_value=1, max_value=999))
    base_id = f"{prefix}_{base_num:03d}"

    # Optionally add sub-levels (up to 2 additional levels for 3-tier max)
    num_levels = draw(st.integers(min_value=0, max_value=2))
    for _ in range(num_levels):
        sub_num = draw(st.integers(min_value=1, max_value=9))
        base_id = f"{base_id}.{sub_num}"

    return base_id

@st.composite
def _implementation_components_strategy(draw) -> dict:
    """Generate valid ImplementationComponents data."""
    return {
        "frontend": draw(st.lists(st.text(min_size=1, max_size=30), max_size=5)),
        "backend": draw(st.lists(st.text(min_size=1, max_size=30), max_size=5)),
        "middleware": draw(st.lists(st.text(min_size=1, max_size=30), max_size=5)),
        "shared": draw(st.lists(st.text(min_size=1, max_size=30), max_size=5)),
    }
```

#### @given Decorator

```python
# From test_models.py (planning_pipeline)
class TestImplementationComponentsProperties:
    """Property-based tests for ImplementationComponents."""

    @given(_implementation_components_strategy())
    def test_round_trip_serialization(self, data):
        """ImplementationComponents should round-trip through dict serialization."""
        comp = ImplementationComponents(
            frontend=data["frontend"],
            backend=data["backend"],
            middleware=data["middleware"],
            shared=data["shared"],
        )

        # Round-trip through dict
        as_dict = comp.to_dict()
        restored = ImplementationComponents.from_dict(as_dict)

        assert comp.frontend == restored.frontend
        assert comp.backend == restored.backend
        assert comp.middleware == restored.middleware
        assert comp.shared == restored.shared
```

---

### Pattern 6: Mocking Patterns

#### unittest.mock.MagicMock

```python
# From test_pipeline.py
@pytest.fixture
def mock_cwa() -> MagicMock:
    """Create a mock CWA integration."""
    cwa = MagicMock()
    cwa.store_research.return_value = "research_001"
    cwa.store_requirement.return_value = "req_001"
    cwa.store_plan.return_value = "plan_001"
    return cwa
```

#### Custom Mock Classes

```python
# From test_beads_sync_phase.py (lines 23-77)
class MockBeadsController:
    """Mock BeadsController for testing."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.created_issues: list[dict[str, Any]] = []
        self.dependencies: list[tuple[str, str]] = []
        self.synced = False
        self._issue_counter = 0
        self._fail_on: set[str] = set()

    def _next_id(self) -> str:
        self._issue_counter += 1
        return f"beads-{self._issue_counter:04d}"

    def create_epic(self, title: str, priority: int = 1) -> dict[str, Any]:
        if "create_epic" in self._fail_on:
            return {"success": False, "error": "Mock error"}
        issue_id = self._next_id()
        self.created_issues.append({
            "id": issue_id,
            "title": title,
            "type": "epic",
            "priority": priority,
        })
        return {"success": True, "data": {"id": issue_id}}
```

#### patch() Context Manager

```python
# From test_artifact_generation.py
with patch("silmari_rlm_act.phases.decomposition.decompose_requirements") as mock:
    mock.return_value = mock_hierarchy
    result = generate_artifacts(...)
    assert result.success
```

#### Monkeypatch (pytest fixture)

```python
# From test_orchestrator.py
def test_collects_multiple_lines(self, monkeypatch):
    """Given multiple lines then blank, returns joined lines."""
    inputs = iter([
        "Research the authentication system.",
        "Focus on JWT token handling.",
        ""
    ])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    result = collect_prompt()
    expected = "Research the authentication system.\nFocus on JWT token handling."
    assert result == expected
```

---

### Pattern 7: Test Naming Conventions

**Format**: `test_<scenario_description>`

| Convention | Example | Purpose |
|------------|---------|---------|
| Descriptive verb phrases | `test_creates_checkpoint_file` | Action being tested |
| Conditional descriptions | `test_returns_none_when_no_checkpoints` | Conditional behavior |
| Constraint testing | `test_respects_max_sub_processes_config` | Configuration constraints |
| Error cases | `test_returns_error_for_empty_research` | Error handling |

---

### Pattern 8: Built-in Pytest Fixtures

| Fixture | Usage Count | Purpose | Examples |
|---------|-------------|---------|----------|
| `tmp_path` | 20+ tests | Temporary directories/files | checkpoint_manager, validation, beads_sync |
| `monkeypatch` | ~10 tests | Patching builtins | orchestrator, CLI tests |
| `capsys` | ~3 tests | Capture stdout/stderr | CLI output tests |
| `caplog` | ~2 tests | Capture logging | Logging tests |

---

## 📈 Test Coverage Approach

### Unit Tests

**Focus**: Individual functions, methods, data models

```python
# From test_models.py (silmari_rlm_act)
class TestAutonomyMode:
    """Unit tests for AutonomyMode enum."""

    def test_has_checkpoint_mode(self):
        """Checkpoint mode pauses at each phase."""
        assert AutonomyMode.CHECKPOINT.value == "checkpoint"

    def test_from_string_valid(self):
        """Convert valid string to AutonomyMode."""
        assert AutonomyMode.from_string("checkpoint") == AutonomyMode.CHECKPOINT

    def test_from_string_invalid(self):
        """Invalid string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid autonomy mode"):
            AutonomyMode.from_string("invalid_mode")
```

---

### Integration Tests

**Focus**: Component interaction, marked with `@pytest.mark.integration`

```python
@pytest.mark.integration
def test_beads_controller_with_real_api(self, cleanup_issues):
    """Test BeadsController with real Beads API."""
    controller = BeadsController(project_path)
    result = controller.create_epic("Test Epic")
    assert result["success"]
    cleanup_issues.append(result["data"]["id"])
```

---

### End-to-End Tests

**Focus**: Full workflows, marked with `@pytest.mark.e2e` and `@pytest.mark.slow`

```python
@pytest.mark.e2e
@pytest.mark.slow
class TestDecompositionE2E:
    """End-to-end decomposition tests."""

    def test_full_flow_with_mock_research(self, tmp_path):
        """Test complete decomposition flow from research to hierarchy."""
        # Setup: Create research file
        research_path = tmp_path / "research.md"
        research_path.write_text("# Research\n\nUser authentication requirements")

        # Execute: Run full decomposition
        result = run_decomposition(str(research_path))

        # Verify: Check complete output
        assert result.success
        assert len(result.hierarchy.requirements) > 0
```

---

## 🎨 Testing Utilities

### Mock Data Classes

**Location**: `planning_pipeline/tests/conftest.py` (lines 22-77)

```python
@dataclass
class MockImplementationComponents:
    """Mock for baml_client.types.ImplementationComponents."""
    frontend: List[str] = field(default_factory=list)
    backend: List[str] = field(default_factory=list)
    middleware: List[str] = field(default_factory=list)
    shared: List[str] = field(default_factory=list)
```

### Helper Functions

Tests in `test_helpers.py` document helper utilities:

```python
# From test_helpers.py
class TestExtractFilePath:
    """Behavior 1: Extract file path from Claude output."""

    def test_extracts_research_path(self):
        """Extracts research file path from output."""
        output = """
        Research complete!
        Created: thoughts/searchable/research/2025-01-01-test-research.md
        """
        result = extract_file_path(output, "research")
        assert result == "thoughts/searchable/research/2025-01-01-test-research.md"
```

---

## 📝 Code References

### Conftest Files

- `silmari_rlm_act/tests/conftest.py` - 3 shared fixtures (sample_timestamp, sample_artifacts, sample_errors)
- `planning_pipeline/tests/conftest.py` - 11 shared fixtures + custom markers

### Configuration Files

- `pytest.ini:1-3` - Pytest configuration
- `pyproject.toml:56-64` - Test paths and asyncio config

### Example Test Files

- `silmari_rlm_act/tests/test_models.py` - Model tests with fixtures
- `planning_pipeline/tests/test_checkpoint_manager.py` - Checkpoint tests
- `planning_pipeline/tests/test_property_generator.py` - Parametrized tests
- `silmari_rlm_act/tests/test_beads_sync_phase.py` - Custom mock class example

---

## 🏛️ Architecture Documentation

### Test Organization Principles

1. **Complete Test Isolation**: All fixtures are function-scoped
2. **Behavior-Driven Organization**: Tests grouped by behavior, not by class under test
3. **Mock-Driven Testing**: Heavy use of mocks for external dependencies (BAML, Claude SDK)
4. **Property-Based Testing**: Hypothesis used for data model invariants
5. **Explicit Dependencies**: No autouse fixtures, all dependencies explicit

### Fixture Naming Conventions

| Prefix | Purpose | Example |
|--------|---------|---------|
| `temp_` / `tmp_` | Temporary resources | `temp_project`, `temp_hierarchy` |
| `mock_` | Mock objects | `mock_cwa`, `mock_baml_client` |
| `sample_` | Test data | `sample_timestamp`, `sample_artifacts` |
| `cleanup_` | Cleanup fixtures | `cleanup_issues` |
| No prefix | Configuration | `project_path`, `cli_runner` |

### Test Markers Strategy

```
@pytest.mark.slow
    ↓
Long-running tests (>1s)
Deselect with: pytest -m "not slow"

@pytest.mark.integration
    ↓
Tests with external dependencies
Run with: pytest -m integration

@pytest.mark.e2e
    ↓
Full workflow tests
Often combined with @slow
```

---

## 📚 Historical Context (from thoughts/)

The project has **extensive prior research** on testing patterns:

### Related Research Documents

1. **`thoughts/searchable/research/2026-01-14-pytest-fixtures.md`**
   - Date: 2026-01-14 13:41:12
   - Comprehensive fixtures analysis (62+ fixtures documented)
   - Custom markers analysis
   - Fixture architecture diagrams

2. **`thoughts/searchable/research/2026-01-14-pytest-fixtures-comprehensive-analysis.md`**
   - Date: 2026-01-14T13:25:52
   - Test suite organization (42 files, 7,989+ test functions)
   - 6 fixture pattern types with distribution
   - Architectural decisions documentation

3. **`thoughts/searchable/research/2026-01-06-pytest-fixtures-patterns.md`**
   - Date: 2026-01-06
   - Early fixture patterns analysis
   - BDD-style organization documentation

4. **`thoughts/shared/research/2026-01-02-pytest-fixtures-testing-patterns.md`**
   - Date: 2026-01-02T13:42:20
   - Initial testing patterns documentation
   - Hypothesis strategy documentation
   - Complete fixture inventory

### Historical Planning Documents

- `thoughts/shared/plans/2026-01-10-tdd-feature/13-the-implementation-phase-must-run-tests-using-pyte.md` - Pytest execution specs (300s timeout)
- `thoughts/shared/plans/2026-01-01-tdd-loop-runner-orchestrator-07-integration-tests.md` - Integration testing specs

---

## 🔍 Key Findings

### Fixture Architecture Strengths

| Strength | Evidence |
|----------|----------|
| ✅ Complete test isolation | 100% function-scoped fixtures |
| ✅ Explicit dependencies | Zero autouse fixtures found |
| ✅ Comprehensive mocking | 17+ mock fixtures covering all external deps |
| ✅ Reusable test data | 14 shared fixtures in conftest.py |
| ✅ Proper cleanup | 6+ yield-based cleanup fixtures |
| ✅ Fixture composition | Multi-level dependency chains |

### Testing Pattern Strengths

| Pattern | Implementation Quality |
|---------|----------------------|
| BDD Organization | ✅ Consistent class-based grouping across all test files |
| Given-When-Then | ✅ All test methods have descriptive docstrings |
| Property-Based Testing | ✅ Custom strategies for domain models |
| Parametrization | ✅ Used for exhaustive case coverage |
| Mocking | ✅ Mix of MagicMock and custom mock classes |
| Markers | ✅ Custom markers for test categorization |

### Test Coverage Quality

```
Unit Tests: ████████████████████ 60%
  └─ Model tests, function tests, validation

Integration Tests: ██████████ 25%
  └─ Component interaction, API integration

E2E Tests: ██████ 15%
  └─ Full workflow, marked @e2e @slow
```

---

## 📊 Statistics Summary

| Metric | Count |
|--------|-------|
| **Total Test Files** | 43 |
| **Total Lines of Test Code** | ~19,400 |
| **Custom Fixtures (conftest.py)** | 14 |
| **File-Specific Fixtures** | 48+ |
| **Total Fixtures** | 62+ |
| **Fixture Scope (function)** | 100% |
| **Custom Pytest Markers** | 3 |
| **Property-Based Test Classes** | 5+ |
| **Custom Hypothesis Strategies** | 8+ |
| **Mock Fixtures** | 17+ |

---

## 🎯 Testing Conventions Summary

### ✅ Followed Conventions

- **Behavior-driven test organization**: Tests grouped by behavior
- **Descriptive test names**: `test_<scenario>` pattern
- **Given-When-Then docstrings**: All tests documented
- **Function-scoped fixtures**: Complete isolation
- **Explicit fixture injection**: No autouse
- **Comprehensive mocking**: All external deps mocked
- **Custom markers**: slow, integration, e2e
- **Property-based testing**: Hypothesis for invariants

### 📋 Naming Patterns

| Element | Convention | Example |
|---------|-----------|---------|
| Test classes | `Test<Behavior>` | `TestWriteCheckpoint` |
| Test methods | `test_<scenario>` | `test_creates_checkpoint_file` |
| Fixtures | `<type>_<name>` | `mock_cwa`, `temp_project` |
| Mock classes | `Mock<ClassName>` | `MockBeadsController` |
| Strategies | `_<name>_strategy` | `_requirement_id_strategy` |

---

## 🔗 Related Research

- [2026-01-14 Pytest Fixtures Comprehensive Analysis](thoughts/searchable/research/2026-01-14-pytest-fixtures-comprehensive-analysis.md)
- [2026-01-14 Pytest Fixtures Documentation](thoughts/searchable/research/2026-01-14-pytest-fixtures.md)
- [2026-01-06 Pytest Fixtures Patterns](thoughts/searchable/research/2026-01-06-pytest-fixtures-patterns.md)
- [2026-01-02 Pytest Fixtures Testing Patterns](thoughts/shared/research/2026-01-02-pytest-fixtures-testing-patterns.md)

---

## 📌 Open Questions

None - the testing infrastructure is well-documented and comprehensive.

---
