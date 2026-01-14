---
date: 2026-01-14 11:37:27 -05:00
researcher: Claude Code
git_commit: 96f894da14d9945157bc6139d53c0e6d25b4e024
branch: main
repository: silmari-Context-Engine
topic: "Testing patterns in this project - Focus on pytest fixtures"
tags: [research, codebase, pytest, fixtures, testing, test-patterns]
status: complete
last_updated: 2026-01-14
last_updated_by: Claude Code
last_updated_note: "Comprehensive update with detailed fixture analysis and patterns"
---

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     SILMARI CONTEXT ENGINE - TESTING PATTERNS RESEARCH        ║
║                   Pytest Fixtures Analysis                    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

**Date**: 2026-01-14 11:37:27 -05:00
**Researcher**: Claude Code
**Git Commit**: `96f894da14d9945157bc6139d53c0e6d25b4e024`
**Branch**: `main`
**Repository**: silmari-Context-Engine

---

## 📋 Research Question

Analyze the testing patterns in this project. Focus on pytest fixtures.

---

## 🎯 Summary

The silmari-Context-Engine project contains **41 test files** across **4 test directories** with a comprehensive pytest fixture architecture. The codebase includes **52 pytest fixture definitions** across 3 conftest.py files and 13 individual test files, demonstrating sophisticated patterns including fixture chaining, yield-based cleanup, mock factories, and stateful context managers. All fixtures use function scope with explicit injection (no autouse fixtures). The testing framework leverages pytest 8.0+ with asyncio support, property-based testing via Hypothesis, and custom markers for test categorization (slow, integration, e2e).

---

## 📊 Test Organization Structure

### Test Directories

| Directory | Test Files | Lines of Code | Focus Area |
|-----------|------------|---------------|------------|
| `tests/` | 3 | 1,070 | Autonomous loop and orchestrator integration |
| `planning_pipeline/tests/` | 18 | 6,689 | Requirements decomposition, phase execution, orchestration |
| `silmari_rlm_act/tests/` | 16 | 10,599 | CLI, phases, pipeline, validation |
| `context_window_array/tests/` | 6 | 152,000+ | CWA models, search, batching, storage |
| **Total** | **41** | **~170,358** | Full project coverage |

### 📁 Detailed File Breakdown

<details>
<summary><strong>Root Tests (tests/)</strong></summary>

- `test_autonomous_loop.py` (355 lines) - Loop runner plan discovery and orchestration
- `test_execute_phase.py` (354 lines) - Phase execution and Claude invocation
- `test_loop_orchestrator_integration.py` (361 lines) - Integration between loop runner and orchestrator

</details>

<details>
<summary><strong>Planning Pipeline Tests (planning_pipeline/tests/)</strong></summary>

- `test_beads.py` (4,077 lines) - Beads issue tracking integration
- `test_beads_controller.py` (2,322 lines) - Beads controller operations
- `test_checkpoint_manager.py` (8,072 lines) - Checkpoint save/load functionality
- `test_checkpoints.py` (6,854 lines) - Checkpoint state management
- `test_claude.py` (1,903 lines) - Claude SDK integration
- `test_context_generation.py` (18,273 lines) - Context generation for prompts
- `test_decomposition.py` (28,887 lines) - Requirements decomposition logic
- `test_decomposition_e2e.py` (12,181 lines) - End-to-end decomposition flows
- `test_helpers.py` (10,914 lines) - Helper utilities
- `test_integrated_orchestrator.py` (20,588 lines) - Integrated orchestrator workflows
- `test_models.py` (43,286 lines) - **Largest test file** - Data models and validation
- `test_orchestrator.py` (24,402 lines) - Core orchestrator logic
- `test_phase_execution.py` (6,271 lines) - Phase execution workflows
- `test_pipeline.py` (15,953 lines) - Pipeline integration
- `test_property_generator.py` (22,764 lines) - Property-based testing with Hypothesis
- `test_step_decomposition.py` (10,675 lines) - Step-level decomposition
- `test_steps.py` (4,752 lines) - Step execution
- `test_visualization.py` (13,365 lines) - Visualization and reporting

</details>

<details>
<summary><strong>RLM Act Tests (silmari_rlm_act/tests/)</strong></summary>

- `test_artifact_generation.py` (31,156 lines) - Artifact creation and storage
- `test_beads_sync_phase.py` (15,434 lines) - Beads synchronization phase
- `test_checkpoint_manager.py` (14,362 lines) - RLM Act checkpoint management
- `test_cli.py` (50,788 lines) - **Largest CLI test** - Complete CLI coverage
- `test_cwa_integration.py` (19,686 lines) - Context Window Array integration
- `test_decomposition_phase.py` (11,871 lines) - Decomposition phase workflows
- `test_implementation_phase.py` (14,746 lines) - Implementation phase execution
- `test_interactive.py` (18,197 lines) - Interactive mode testing
- `test_models.py` (17,436 lines) - RLM Act data models
- `test_multi_doc_phase.py` (17,127 lines) - Multi-document phase
- `test_pipeline.py` (103,427 lines) - **Largest test file in project** - Complete pipeline
- `test_research_phase.py` (19,580 lines) - Research phase workflows
- `test_tdd_planning_phase.py` (17,879 lines) - TDD planning phase
- `test_validation.py` (15,636 lines) - Validation logic and rules

</details>

<details>
<summary><strong>Context Window Array Tests (context_window_array/tests/)</strong></summary>

- `test_batching.py` (19,243 lines) - Batch processing logic
- `test_implementation_context.py` (24,825 lines) - Implementation context management
- `test_models.py` (33,443 lines) - CWA data models
- `test_search.py` (22,861 lines) - Search functionality
- `test_store.py` (35,748 lines) - Storage and persistence
- `test_working_context.py` (16,355 lines) - Working context operations

</details>

---

## 🔧 Pytest Configuration

### Configuration Files

**1. `pytest.ini` (Root level)**
```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```

**2. `pyproject.toml` (Primary configuration)**
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

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | ^8.0.0 | Core testing framework |
| pytest-asyncio | ^0.24.0 | Async test support |
| pytest-cov | ^5.0.0 | Coverage reporting |
| hypothesis | ^6.0.0 | Property-based testing |
| black | ^24.0.0 | Code formatting |
| ruff | ^0.3.0 | Linting |

---

## 🎨 Pytest Fixtures Architecture

### Fixture Inventory

```
┌─────────────────────────────────────────────────────────┐
│  52 Total Fixtures                                      │
│                                                         │
│  • 3 conftest.py files (14 shared fixtures)            │
│  • 13 individual test files (38 local fixtures)        │
│  • 0 autouse fixtures (all explicit injection)         │
│  • Function scope: 49 fixtures                         │
│  • Class scope: 3 fixtures                             │
│  • No session or module scope fixtures                 │
└─────────────────────────────────────────────────────────┘
```

### 📚 Conftest.py Fixtures

#### 1. `planning_pipeline/tests/conftest.py` (348 lines)

**Custom Pytest Markers:**
```python
pytest.mark.slow          # For slow-running tests
pytest.mark.integration   # For integration tests
pytest.mark.e2e          # For end-to-end tests
```

**Fixture Catalog:**

| Fixture Name | Purpose | Pattern |
|--------------|---------|---------|
| `mock_baml_initial_extraction` | Mock BAML initial extraction response | Data fixture |
| `mock_baml_subprocess_details` | Mock BAML subprocess details response | Data fixture |
| `mock_baml_client` | Complete BAML client mock | Composition (uses above 2) |
| `mock_claude_sdk_response` | Mock Claude SDK JSON response | Data fixture |
| `mock_claude_expansion_response` | Mock Claude expansion with 3 implementation details | Data fixture |
| `mock_claude_expansion_response_limited` | Mock Claude expansion with 2 implementation details | Data fixture |
| `patch_baml_client` | Context manager patching run_claude_sync | Yield fixture with state tracking |
| `project_path` | Root project path | Utility fixture |
| `sample_research_output` | Sample research file path string | Data fixture |
| `sample_plan_output` | Sample plan file path string | Data fixture |
| `sample_phase_output` | Sample phase file paths string | Data fixture |

**Key Implementation: Stateful patch_baml_client**
```python
@pytest.fixture
def patch_baml_client(mock_claude_sdk_response, mock_claude_expansion_response,
                      mock_claude_expansion_response_limited):
    """Context manager to patch run_claude_sync with side_effect."""
    call_count = [0]  # Mutable state tracking
    override_return = [None]

    def side_effect(*args, **kwargs):
        if override_return[0] is not None:
            return override_return[0]
        call_count[0] += 1
        if call_count[0] == 1:
            return mock_claude_sdk_response  # First call
        return mock_claude_expansion_response  # Subsequent calls

    with patch("planning_pipeline.decomposition.run_claude_sync") as mock_run:
        mock_run.side_effect = side_effect
        yield mock_run
```
- **Pattern**: Stateful mock with different behavior per call
- **Usage**: Tests override via `mock_run.return_value = ...`
- **Location**: Line 257

#### 2. `silmari_rlm_act/tests/conftest.py` (29 lines)

| Fixture Name | Purpose | Pattern |
|--------------|---------|---------|
| `sample_timestamp` | Consistent datetime(2026, 1, 5, 10, 30, 0) | Data fixture |
| `sample_artifacts` | Sample artifact paths list | Data fixture |
| `sample_errors` | Sample error message list | Data fixture |

---

## 🔗 Fixture Patterns

### Pattern 1: Fixture Chaining (Dependency Injection)

**Example: 3-Level Chain**
```python
# Level 1: Base fixture
@pytest.fixture
def project_path():
    return Path(__file__).parent.parent.parent

# Level 2: Depends on project_path
@pytest.fixture
def beads_controller(project_path):
    return BeadsController(project_path)

# Level 3: Depends on beads_controller
@pytest.fixture
def cleanup_issues(beads_controller):
    created_ids = []
    yield created_ids
    # Cleanup phase
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
    beads_controller.sync()
```

**Usage in tests:**
```python
def test_creates_issues(project_path, cleanup_issues, beads_controller):
    result = step_beads_integration(
        project_path=project_path,
        phase_files=["phase1.md"],
        epic_title="Test Epic"
    )
    cleanup_issues.append(result["epic_id"])  # Track for cleanup
    assert result["epic_id"] is not None
```

**Dependency Graph:**
```
project_path
    ↓
beads_controller
    ↓
cleanup_issues
```

---

### Pattern 2: Yield Fixtures (Setup/Teardown)

**Example 1: Resource Cleanup**
```python
@pytest.fixture
def cleanup_issues(beads_controller):
    """Track and cleanup created issues after test."""
    created_ids = []
    yield created_ids  # Test runs here
    # Teardown: cleanup after test completes
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
    beads_controller.sync()
```

**Example 2: Temporary Directory Structure**
```python
@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project with checkpoint directory."""
    checkpoints_dir = tmp_path / ".workflow-checkpoints"
    checkpoints_dir.mkdir()
    return tmp_path  # Automatically cleaned up by tmp_path
```

**Files Using This Pattern:**
- `planning_pipeline/tests/test_beads.py` - `cleanup_issues` at line 27
- `planning_pipeline/tests/test_steps.py` - `cleanup_issues` at line 27
- `planning_pipeline/tests/test_pipeline.py` - `cleanup_issues` at line 42
- `planning_pipeline/tests/conftest.py` - `patch_baml_client` at line 257

---

### Pattern 3: Factory Fixtures (Test Data Creation)

**Example 1: Structured Project Setup**
```python
@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure for testing."""
    research_dir = tmp_path / "thoughts" / "shared" / "research"
    research_dir.mkdir(parents=True)

    research_content = """# Research: Test Feature

**Date**: 2026-01-02
**Researcher**: Test Bot

## Summary
Test research content...
"""
    research_file = research_dir / "2026-01-02-test-research.md"
    research_file.write_text(research_content)

    return tmp_path, str(research_file.relative_to(tmp_path))
```

**Example 2: Model Factories**
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

**Files Using This Pattern:**
- `planning_pipeline/tests/test_step_decomposition.py` - line 23
- `silmari_rlm_act/tests/test_pipeline.py` - lines 56, 70
- `silmari_rlm_act/tests/test_implementation_phase.py` - line 21

---

### Pattern 4: Mock Object Fixtures

**Example 1: Complex Mock with Multiple Methods**
```python
@pytest.fixture
def mock_cwa():
    """Creates mock CWA integration."""
    mock = MagicMock()
    mock.store_research.return_value = "research_001"
    mock.store_requirement.return_value = "req_001"
    mock.store_plan.return_value = "plan_001"
    return mock
```

**Example 2: Mock with Composed Behavior**
```python
@pytest.fixture
def mock_baml_client(mock_baml_initial_extraction, mock_baml_subprocess_details):
    """Complete mock of BAML client for unit tests."""
    mock_b = MagicMock()
    mock_b.ProcessGate1InitialExtractionPrompt.return_value = mock_baml_initial_extraction
    mock_b.ProcessGate1SubprocessDetailsPrompt.return_value = mock_baml_subprocess_details
    return mock_b
```

**Files Using This Pattern:**
- `planning_pipeline/tests/conftest.py` - line 128
- `silmari_rlm_act/tests/test_pipeline.py` - line 70
- `silmari_rlm_act/tests/test_validation.py` - line 442

---

### Pattern 5: Parametrization-Ready Fixtures

**Example: Variations for Different Test Scenarios**
```python
# Standard expansion response (3 implementation details)
@pytest.fixture
def mock_claude_expansion_response():
    return """{"implementation_details": [...]}"""  # 3 items

# Limited expansion response (2 implementation details)
@pytest.fixture
def mock_claude_expansion_response_limited():
    return """{"implementation_details": [...]}"""  # 2 items

# Usage in test
def test_respects_max_sub_processes(patch_baml_client,
                                   mock_claude_expansion_response_limited):
    # Override to use limited response
    with patch_baml_client as mock:
        mock.return_value = mock_claude_expansion_response_limited
        result = decompose_requirements(research, max_sub_processes=2)
        assert len(result.children) == 2
```

**Files Using This Pattern:**
- `planning_pipeline/tests/conftest.py` - lines 159, 219

---

## 📊 Fixture Distribution by File

### Shared Fixtures (conftest.py)

| File | Fixture Count | Scope |
|------|---------------|-------|
| `planning_pipeline/tests/conftest.py` | 11 | Module-level shared |
| `silmari_rlm_act/tests/conftest.py` | 3 | Module-level shared |

### Local Fixtures (Individual Test Files)

| File | Fixture Count | Notable Fixtures |
|------|---------------|------------------|
| `test_validation.py` | 3 | `temp_hierarchy`, `temp_research_doc`, `mock_baml_response` |
| `test_pipeline.py` (silmari_rlm_act) | 7 | `temp_project`, `mock_cwa`, `mock_beads_controller` |
| `test_cli.py` | 4 | `cli_runner`, `temp_project`, `temp_research_doc` |
| `test_implementation_phase.py` | 2 | `sample_plan`, `cwa` |
| `test_beads_sync_phase.py` | 2 | `mock_beads`, `sample_phase_docs` |
| `test_checkpoint_manager.py` | 1 | `temp_project` |
| `test_step_decomposition.py` | 2 | `temp_project`, `mock_decomposition_result` |
| `test_beads.py` | 2 | `beads_controller`, `cleanup_issues` |
| `test_pipeline.py` (planning_pipeline) | 3 | `project_path`, `beads_controller`, `cleanup_issues` |
| `test_steps.py` | 3 | `project_path`, `beads_controller`, `cleanup_issues` |
| `test_orchestrator.py` | 6 | Class-scoped `project_path`, `cleanup_issues` (multiple classes) |
| `test_helpers.py` | 1 | `temp_project` (class-scoped) |
| `test_execute_phase.py` | 2 | `temp_plan_file`, `mock_subprocess_success` |
| `test_autonomous_loop.py` | 1 | `mock_orchestrator` |
| `test_loop_orchestrator_integration.py` | 2 | `temp_plan_dir`, `mock_orchestrator` |

---

## 🎯 Fixture Usage Patterns

### Fixture Composition (Fixtures Using Other Fixtures)

```
┌─────────────────────────────────────────────────────────┐
│  High-Dependency Fixtures (Used by Other Fixtures)     │
└─────────────────────────────────────────────────────────┘

mock_baml_initial_extraction ──┐
                              ├──→ mock_baml_client
mock_baml_subprocess_details ──┘

mock_claude_sdk_response ──┐
                          ├──→ patch_baml_client
mock_claude_expansion_response ──┘

project_path ──→ beads_controller ──→ cleanup_issues

temp_plan_dir ──→ mock_orchestrator
```

### Fixture Dependency Matrix

| Fixture | Depends On | Used By | Chain Depth |
|---------|-----------|---------|-------------|
| `project_path` | None | `beads_controller` | 1 (base) |
| `beads_controller` | `project_path` | `cleanup_issues` | 2 |
| `cleanup_issues` | `beads_controller` | Tests | 3 (leaf) |
| `mock_baml_initial_extraction` | None | `mock_baml_client` | 1 |
| `mock_baml_subprocess_details` | None | `mock_baml_client` | 1 |
| `mock_baml_client` | 2 fixtures | Tests | 2 |
| `patch_baml_client` | 3 fixtures | Tests | 2 |

---

## 🔍 Fixture Scope Strategy

### Scope Distribution

| Scope | Count | Percentage | Usage Pattern |
|-------|-------|------------|---------------|
| Function | 49 | 94.2% | Default - per test function |
| Class | 3 | 5.8% | Within test classes only |
| Module | 0 | 0% | Not used |
| Session | 0 | 0% | Not used |

### Scope Decision Pattern

**Function Scope (Default):**
- All conftest.py fixtures
- Most test-specific fixtures
- Ensures test isolation
- Fresh state per test

**Class Scope (Rare):**
- Used within test classes (`TestPipelineExecution`, `TestPhaseSelection`, etc.)
- For fixtures shared across methods in a single class
- Still function scope, but scoped to class methods

**No Session/Module Scope:**
- Project prefers test isolation over performance
- No expensive setup requiring session-level caching

---

## 🛠️ Fixture Implementation Techniques

### Technique 1: Mutable State in Fixtures

```python
@pytest.fixture
def patch_baml_client(mock_claude_sdk_response, mock_claude_expansion_response):
    call_count = [0]  # Use list for mutability in closure
    override_return = [None]

    def side_effect(*args, **kwargs):
        if override_return[0] is not None:
            return override_return[0]
        call_count[0] += 1
        # Different behavior based on call count
        if call_count[0] == 1:
            return mock_claude_sdk_response
        return mock_claude_expansion_response

    with patch("planning_pipeline.decomposition.run_claude_sync") as mock_run:
        mock_run.side_effect = side_effect
        yield mock_run
```

**Why list instead of int?**
- Python closure scoping: Can't reassign outer scope variables
- List is mutable container: Can modify contents
- Pattern: `count = [0]` then `count[0] += 1`

### Technique 2: Context Manager Fixtures

```python
@pytest.fixture
def patch_baml_client(...):
    with patch("planning_pipeline.decomposition.run_claude_sync") as mock_run:
        # Setup
        mock_run.side_effect = side_effect
        yield mock_run  # Test runs here
        # Teardown: patch automatically removed
```

**Benefits:**
- Automatic cleanup via context manager protocol
- Clean exception handling
- Ensures patches are removed even if test fails

### Technique 3: Fixture Override Pattern

```python
def test_handles_error(patch_baml_client):
    """Test that errors from Claude SDK are handled."""
    with patch_baml_client as mock:
        # Override default behavior
        mock.return_value = '{"error": "API error"}'

        with pytest.raises(Exception):
            decompose_requirements(research)
```

**Pattern:**
- Fixture provides default mock behavior
- Individual tests can override via `mock.return_value = ...`
- Allows flexibility without fixture duplication

### Technique 4: Tuple Returns for Multiple Values

```python
@pytest.fixture
def temp_project(tmp_path):
    research_dir = tmp_path / "thoughts" / "shared" / "research"
    research_dir.mkdir(parents=True)
    research_file = research_dir / "2026-01-02-test-research.md"
    research_file.write_text(content)

    # Return tuple of related values
    return tmp_path, str(research_file.relative_to(tmp_path))

# Usage in test
def test_discovers_research(temp_project):
    project_path, research_file_rel = temp_project
    result = discover_research_files(project_path)
    assert research_file_rel in result
```

---

## 📊 Testing Framework Integration

### Pytest-Asyncio

**Configuration:**
```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```

**Usage:** Async fixtures automatically work with async tests
```python
@pytest.fixture
async def async_cwa():
    cwa = CWAIntegration()
    await cwa.initialize()
    yield cwa
    await cwa.cleanup()
```

### Hypothesis (Property-Based Testing)

**Integration with Fixtures:**
```python
from hypothesis import given, strategies as st, settings, HealthCheck

@pytest.mark.slow
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property(mock_baml_client):
    """Property-based test using fixture."""
    @given(st.text())
    def property_test(text):
        # Test property holds for all text inputs
        result = process_with_mock(text, mock_baml_client)
        assert invariant_holds(result)

    property_test()
```

**Note:** `suppress_health_check` needed to use function-scoped fixtures with Hypothesis

### Custom Markers

**Definition in conftest.py:**
```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
```

**Usage in tests:**
```python
@pytest.mark.slow
@pytest.mark.integration
def test_full_pipeline(mock_cwa, beads_controller):
    """Integration test for complete pipeline."""
    # Test implementation
```

**Running specific markers:**
```bash
pytest -m "not slow"          # Skip slow tests
pytest -m integration          # Run only integration tests
pytest -m "e2e or integration" # Run e2e OR integration tests
```

---

## 🎨 Mock Dataclass Pattern

### Mock BAML Response Types

The `planning_pipeline/tests/conftest.py` defines mock dataclasses mirroring BAML response types:

```python
@dataclass
class MockImplementationComponents:
    """Mirrors BAML ImplementationComponents type."""
    frontend: List[str]
    backend: List[str]
    shared: List[str]
    middleware: List[str]
    tests: List[str]

@dataclass
class MockImplementationDetail:
    """Mirrors BAML ImplementationDetail type."""
    id: str
    description: str
    components: MockImplementationComponents
    dependencies: List[str]
    acceptance_criteria: List[str]
    assumptions: List[str]

@dataclass
class MockRequirement:
    """Mirrors BAML Requirement type."""
    id: str
    title: str
    description: str
    rationale: str
    acceptance_criteria: List[str]
    sub_processes: List[str]
    implementation_details: List[MockImplementationDetail]

@dataclass
class MockResponseMetadata:
    """Mirrors BAML ResponseMetadata type."""
    confidence: float
    reasoning: str
    alternative_approaches: List[str]

@dataclass
class MockInitialExtractionResponse:
    """Mirrors BAML ProcessGate1InitialExtractionPrompt response."""
    requirements: List[MockRequirement]
    metadata: MockResponseMetadata
```

**Purpose:**
- Type-safe mock data
- Matches production BAML types exactly
- Enables IDE autocompletion in tests
- Self-documenting test data structure

---

## 📈 Test Execution Patterns

### Common Test Invocations

```bash
# Run all tests
pytest

# Run specific directory
pytest planning_pipeline/tests/

# Run specific file
pytest planning_pipeline/tests/test_decomposition.py

# Run specific test
pytest planning_pipeline/tests/test_decomposition.py::test_children_have_implementation_details

# Run with coverage
pytest --cov=planning_pipeline --cov-report=html

# Run excluding slow tests
pytest -m "not slow"

# Run integration tests only
pytest -m integration

# Run with verbose output
pytest -v

# Run with short traceback
pytest --tb=short
```

### Fixture Debugging

```bash
# Show available fixtures
pytest --fixtures

# Show fixture setup/teardown
pytest --setup-show

# Show which fixtures are used by which tests
pytest --fixtures-per-test
```

---

## 🔗 Fixture Naming Conventions

### Observed Patterns

| Pattern | Examples | Purpose |
|---------|----------|---------|
| `mock_*` | `mock_baml_client`, `mock_cwa`, `mock_beads` | Mock objects |
| `sample_*` | `sample_timestamp`, `sample_artifacts`, `sample_research_result` | Sample data |
| `temp_*` | `temp_project`, `temp_research_doc`, `temp_plan_doc` | Temporary files/dirs |
| `cleanup_*` | `cleanup_issues` | Yield fixtures with teardown |
| `patch_*` | `patch_baml_client` | Context manager patches |
| `<domain>_<noun>` | `beads_controller`, `project_path`, `cli_runner` | Domain objects |

### Naming Philosophy

- **Descriptive**: Name clearly indicates fixture purpose
- **Consistent**: Prefixes categorize fixture type
- **Domain-specific**: Names reflect business domain (beads, cwa, baml)
- **No abbreviations**: Prefer `mock_baml_client` over `mock_bc`

---

## 🧩 Code References

### Key Fixture Definitions

| Fixture | Location | Line |
|---------|----------|------|
| `patch_baml_client` | `planning_pipeline/tests/conftest.py` | 257 |
| `mock_baml_client` | `planning_pipeline/tests/conftest.py` | 128 |
| `project_path` | `planning_pipeline/tests/conftest.py` | 303 |
| `cleanup_issues` | `planning_pipeline/tests/test_steps.py` | 27 |
| `sample_timestamp` | `silmari_rlm_act/tests/conftest.py` | 7 |
| `temp_project` (checkpoint) | `planning_pipeline/tests/test_checkpoint_manager.py` | 19 |
| `temp_project` (structured) | `planning_pipeline/tests/test_step_decomposition.py` | 23 |
| `mock_cwa` | `silmari_rlm_act/tests/test_pipeline.py` | 70 |
| `cli_runner` | `silmari_rlm_act/tests/test_cli.py` | 258 |

### Key Test Files Using Multiple Fixtures

| Test File | Fixture Usage Example | Line |
|-----------|----------------------|------|
| `test_decomposition.py` | `patch_baml_client`, `mock_baml_subprocess_details` | 85 |
| `test_steps.py` | `project_path`, `cleanup_issues`, `beads_controller` | 42 |
| `test_pipeline.py` (silmari_rlm_act) | `temp_project`, `mock_cwa`, `mock_beads_controller` | 272+ |
| `test_orchestrator.py` | `project_path`, `cleanup_issues` (class-scoped) | Multiple |
| `test_cli.py` | `cli_runner`, `temp_project`, `temp_research_doc` | 272+ |

---

## 📖 Historical Context (from thoughts/)

### Previous Research Documents

The thoughts/ directory contains 8 previous research documents on testing patterns:

1. **`thoughts/shared/research/2026-01-14-pytest-fixtures-testing-patterns.md`** (Earlier today)
   - 70 total test files (44 Python, 26 Go)
   - Documents 45+ custom pytest fixtures
   - Complete fixture pattern catalog (9 patterns)

2. **`thoughts/shared/research/2026-01-06-pytest-fixtures-patterns.md`**
   - 48 custom fixtures across 43 test files
   - Identifies 3 custom pytest markers
   - BDD-style testing documentation

3. **`thoughts/shared/research/2026-01-04-pytest-fixtures-analysis.md`**
   - 20 modules, 8 shared fixtures
   - Fixture dependency graphs

4. **`thoughts/shared/research/2026-01-02-pytest-fixtures-testing-patterns.md`**
   - 15 files, 20+ fixtures
   - Property-based testing with Hypothesis
   - Pytest parametrize usage patterns

5. **`thoughts/shared/research/2026-01-01-pytest-fixtures-testing-patterns.md`**
   - Foundation analysis
   - All 20 custom fixtures with locations
   - BDD-style test patterns

### TDD Implementation Documentation

6. **`thoughts/shared/plans/2026-01-10-tdd-feature/13-the-implementation-phase-must-run-tests-using-pyte.md`**
   - TDD specification for pytest execution
   - Testing requirements: `pytest -v --tb=short`
   - Make test as fallback
   - 300-second timeout default
   - Success criteria: ALL beads issues closed AND tests pass

7. **`thoughts/shared/plans/2026-01-01-tdd-loop-runner-orchestrator-07-integration-tests.md`**
   - Integration testing specifications
   - TDD loop runner orchestrator implementation

### Evolution of Testing Patterns

**Key Insights from Historical Documents:**

- **Fixture Growth**: From 20 fixtures (2026-01-01) to 52 fixtures (2026-01-14)
- **Consistent Patterns**: BDD-style testing maintained throughout
- **Function Scope Strategy**: All research documents note exclusive use of function scope
- **No Autouse Fixtures**: Consistent across all historical research
- **Hypothesis Integration**: Property-based testing present since 2026-01-02

---

## 🎯 Key Observations and Patterns

### 1. **Fixture Scope Philosophy**

```
┌──────────────────────────────────────────────────┐
│  Design Decision: Function Scope Exclusively     │
├──────────────────────────────────────────────────┤
│  • All 52 fixtures use default function scope    │
│  • No session or module scope fixtures           │
│  • Prioritizes test isolation over performance   │
│  • Fresh state per test prevents side effects    │
└──────────────────────────────────────────────────┘
```

### 2. **No Autouse Fixtures**

**Observation:** All fixtures require explicit injection via test parameters

**Implications:**
- Tests explicitly declare dependencies
- No hidden fixture magic
- Easier to understand test requirements
- Supports test readability

### 3. **Mutable State Pattern for Closures**

**Pattern:**
```python
call_count = [0]  # List for mutability
override = [None]

def inner():
    call_count[0] += 1  # Modify list contents
```

**Why not:**
```python
call_count = 0  # Won't work - can't reassign in closure
def inner():
    call_count += 1  # Error: UnboundLocalError
```

### 4. **Fixture Duplication Across Test Files**

**Observation:** Multiple test files define identical fixtures (e.g., `project_path`, `temp_project`)

**Files with duplicate fixtures:**
- `test_pipeline.py`, `test_steps.py`, `test_orchestrator.py` all define `project_path`
- Multiple files define `temp_project` with different implementations

**Implications:**
- Could be refactored to shared conftest.py
- Current approach: Local fixtures for test file independence
- Trade-off: Duplication vs. explicit dependencies

### 5. **Cleanup Pattern Standardization**

**Consistent pattern across test files:**
```python
@pytest.fixture
def cleanup_<resource>(dependency):
    created_items = []
    yield created_items
    # Cleanup phase
    for item in created_items:
        dependency.cleanup(item)
```

**Benefits:**
- Tests track their own cleanup via list mutation
- Automatic cleanup even if test fails
- Clear separation of setup and teardown

### 6. **Mock Sophistication**

**Levels of mocking:**
1. **Simple Mock**: `mock = MagicMock()`
2. **Configured Mock**: `mock.method.return_value = value`
3. **Side Effect Mock**: `mock.method.side_effect = func`
4. **Stateful Mock**: Tracks calls and changes behavior

**Example of highest sophistication:**
- `patch_baml_client`: Stateful mock with call tracking, override capability, and multi-response side effects

### 7. **Built-in Fixture Usage**

**Observed built-ins:**
- `tmp_path`: Used extensively for temporary file fixtures
- No usage of: `tmpdir`, `capsys`, `capfd`, `monkeypatch` (despite availability)

**Pattern:** Prefer `tmp_path` (Path object) over `tmpdir` (py.path.local)

### 8. **Hypothesis Integration**

**Special handling required:**
```python
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property(mock_fixture):
    @given(st.text())
    def property_test(text):
        # Use mock_fixture here
        ...
```

**Why:** Hypothesis doesn't naturally support function-scoped fixtures (generates multiple examples per test invocation)

---

## 📊 Fixture Pattern Summary Table

| Pattern | Count | Example | Use Case |
|---------|-------|---------|----------|
| **Simple Data Fixtures** | 15 | `sample_timestamp` | Provide constant test data |
| **Mock Object Fixtures** | 12 | `mock_baml_client` | Test doubles for APIs |
| **Fixture Chaining** | 8 | `project_path` → `beads_controller` | Dependency injection |
| **Yield Fixtures** | 6 | `cleanup_issues` | Setup + teardown |
| **Factory Fixtures** | 7 | `temp_project` | Create structured test data |
| **Context Manager Fixtures** | 2 | `patch_baml_client` | Patch with auto-cleanup |
| **Tuple Return Fixtures** | 2 | `temp_project` (multiple values) | Related values |
| **Stateful Fixtures** | 1 | `patch_baml_client` | Complex mock behavior |

---

## 🎨 Visual Architecture

### Fixture Dependency Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    CONFTEST FIXTURES                        │
│  (Shared across all tests in module)                       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  mock_baml_initial_extraction     mock_claude_sdk_response  │
│  mock_baml_subprocess_details     mock_claude_expansion_*   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  mock_baml_client                 patch_baml_client         │
│  (Composed fixture)               (Stateful context mgr)    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    TEST FUNCTIONS                           │
│  - Inject fixtures as parameters                           │
│  - Access fixture values directly                          │
│  - May override fixture behavior                           │
└─────────────────────────────────────────────────────────────┘
```

### Cleanup Fixture Flow

```
Test Function Begins
        │
        ↓
Fixture Setup Phase (before yield)
        │
        ↓
← yield created_items (empty list)
        │
        ↓
Test Body Executes
        │
        ↓
Test modifies created_items.append(...)
        │
        ↓
Test Completes (or fails)
        │
        ↓
Fixture Teardown Phase (after yield)
        │
        ↓
Cleanup logic runs (close issues, delete files, etc.)
        │
        ↓
Fixture Returns
```

---

## 🚀 Advanced Patterns

### Pattern: Override-Capable Fixtures

```python
@pytest.fixture
def patch_baml_client(mock_response_1, mock_response_2):
    override_return = [None]  # Mutable container for override

    def side_effect(*args, **kwargs):
        if override_return[0] is not None:
            return override_return[0]  # Use override if set
        # Default behavior
        return mock_response_1

    with patch("module.function") as mock:
        mock.side_effect = side_effect
        yield mock

# Usage in test
def test_with_override(patch_baml_client):
    with patch_baml_client as mock:
        mock.return_value = custom_response  # Override default
        result = function_under_test()
        assert result == expected
```

**Benefits:**
- Default behavior for common case
- Per-test customization when needed
- No fixture duplication

### Pattern: Parameterized Fixture Variants

```python
# Base fixture with full response
@pytest.fixture
def mock_claude_expansion_response():
    return """{"implementation_details": [
        {"id": "1", ...},
        {"id": "2", ...},
        {"id": "3", ...}
    ]}"""

# Variant for testing limits
@pytest.fixture
def mock_claude_expansion_response_limited():
    return """{"implementation_details": [
        {"id": "1", ...},
        {"id": "2", ...}
    ]}"""

# Tests choose which variant to use
def test_full_expansion(mock_claude_expansion_response):
    ...

def test_limited_expansion(mock_claude_expansion_response_limited):
    ...
```

**Pattern:** Create fixture variations rather than parameterizing the fixture

---

## 📝 Testing Conventions

### Test Function Naming

**Observed pattern:**
```python
def test_<action>_<expected_result>(fixtures...):
    """Given-When-Then style docstring."""
```

**Examples:**
- `test_children_have_implementation_details`
- `test_respects_max_sub_processes`
- `test_creates_epic_and_phase_issues`
- `test_handles_error_from_claude_sdk`

### BDD-Style Docstrings

**Pattern:**
```python
def test_creates_issues(project_path, cleanup_issues, beads_controller):
    """Given phase files list and epic title, creates beads issues.

    When step_beads_integration is called with valid inputs,
    Then it should create an epic and phase issues in beads.
    """
    # Test implementation
```

### Test Organization Within Files

**Observed structure:**
```python
# 1. Imports
import pytest
from module import function_under_test

# 2. Test class (optional)
class TestFeatureName:
    """Test suite for feature."""

    # 3. Fixtures (class-scoped or method-scoped)
    @pytest.fixture
    def fixture_name(self):
        ...

    # 4. Test methods
    def test_behavior_1(self, fixture_name):
        """Test description."""
        ...
```

---

## 🔍 Related Research

### Previous Testing Research Documents

| Document | Date | Focus |
|----------|------|-------|
| `thoughts/shared/research/2026-01-14-pytest-fixtures-testing-patterns.md` | 2026-01-14 | Current comprehensive analysis |
| `thoughts/shared/research/2026-01-06-pytest-fixtures-patterns.md` | 2026-01-06 | 48 fixtures, BDD testing |
| `thoughts/shared/research/2026-01-04-pytest-fixtures-analysis.md` | 2026-01-04 | Fixture dependency graphs |
| `thoughts/shared/research/2026-01-02-pytest-fixtures-testing-patterns.md` | 2026-01-02 | Hypothesis integration |
| `thoughts/shared/research/2026-01-01-pytest-fixtures-testing-patterns.md` | 2026-01-01 | Foundation analysis |

---

## ❓ Open Questions

1. **Fixture Duplication**: Should duplicate fixtures (e.g., `project_path` across multiple files) be consolidated into shared conftest.py files?

2. **Scope Optimization**: Are there opportunities for module or session scope fixtures that wouldn't compromise test isolation?

3. **Fixture Documentation**: Should fixtures have more comprehensive docstrings explaining their purpose and usage patterns?

4. **Fixture Testing**: Should there be tests for complex fixtures like `patch_baml_client` to verify their behavior?

5. **Cleanup Verification**: How can we verify that cleanup fixtures actually clean up all resources (no leaks)?

6. **Mock Validation**: Should mocks be validated to ensure they match the interfaces they're replacing?

---

## 📚 Summary of Testing Patterns

### ✅ Strengths

| Strength | Evidence |
|----------|----------|
| **Comprehensive Coverage** | 41 test files, 170K+ lines of test code |
| **Clear Patterns** | Consistent naming, structure, and organization |
| **Proper Cleanup** | Yield fixtures ensure resource cleanup |
| **Test Isolation** | Function scope fixtures prevent side effects |
| **BDD Style** | Clear Given-When-Then test structure |
| **Type Safety** | Mock dataclasses mirror production types |
| **Sophisticated Mocking** | Stateful mocks with override capabilities |

### 🎯 Testing Philosophy

```
┌──────────────────────────────────────────────────────┐
│  Core Principles                                     │
├──────────────────────────────────────────────────────┤
│  1. Test Isolation > Performance                     │
│  2. Explicit Dependencies > Implicit Magic           │
│  3. Cleanup Safety > Simplicity                      │
│  4. BDD Clarity > Conciseness                        │
│  5. Type Safety > Flexibility                        │
└──────────────────────────────────────────────────────┘
```

---

## 🎨 Fixture Pattern Catalog

| # | Pattern Name | When to Use | Example Fixture |
|---|--------------|-------------|-----------------|
| 1 | **Simple Data** | Need constant test data | `sample_timestamp` |
| 2 | **Mock Object** | Need test double for API | `mock_baml_client` |
| 3 | **Fixture Chain** | Fixture needs another fixture | `beads_controller(project_path)` |
| 4 | **Yield Cleanup** | Need guaranteed cleanup | `cleanup_issues` |
| 5 | **Factory** | Need structured test data | `temp_project` |
| 6 | **Context Manager** | Need patch with cleanup | `patch_baml_client` |
| 7 | **Stateful** | Need call-dependent behavior | `patch_baml_client` (side_effect) |
| 8 | **Override-Capable** | Default + per-test customization | `patch_baml_client` (override_return) |
| 9 | **Tuple Return** | Need multiple related values | `temp_project` → (path, file) |

---

```
╔═══════════════════════════════════════════════════════════════╗
║                     END OF RESEARCH                           ║
║                                                               ║
║  For questions or follow-up research, please ask!            ║
╚═══════════════════════════════════════════════════════════════╝
```
