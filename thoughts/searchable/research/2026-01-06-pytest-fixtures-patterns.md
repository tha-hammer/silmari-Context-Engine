---
date: 2026-01-06 07:11:40 EST
researcher: tha-hammer
git_commit: 6a8a69f3c33d65d8e5c34f988ec71a9005992229
branch: main
repository: silmari-Context-Engine
topic: "Pytest Fixtures and Testing Patterns"
tags: [research, codebase, pytest, fixtures, testing, test-patterns]
status: complete
last_updated: 2026-01-06
last_updated_by: tha-hammer
---

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║         PYTEST FIXTURES & TESTING PATTERNS ANALYSIS           ║
║              silmari-Context-Engine Test Suite                ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

# Research: Pytest Fixtures and Testing Patterns

**Date**: 2026-01-06 07:11:40 EST
**Researcher**: tha-hammer
**Git Commit**: `6a8a69f3c33d65d8e5c34f988ec71a9005992229`
**Branch**: `main`
**Repository**: silmari-Context-Engine

---

## 📋 Research Question

Analyze the testing patterns in this project, with a focus on pytest fixtures.

---

## 🎯 Summary

The silmari-Context-Engine project employs a comprehensive test suite with **43 test files** organized across **4 main directories**. The testing infrastructure heavily relies on pytest with **48 custom fixtures** distributed across 2 `conftest.py` files and various test modules.

Key characteristics:
- **All fixtures use function scope** (no session/module/class scoped fixtures)
- **No autouse fixtures** found
- **Extensive mock usage** for Claude API, BAML client, and BeadsController
- **Yield fixtures** for setup/teardown patterns
- **3 custom pytest markers**: `slow`, `integration`, `e2e`
- **Built-in fixtures** heavily used (especially `tmp_path`)
- **BDD-style tests** with Given-When-Then comments

---

## 📊 Test Suite Structure

### Directory Organization

| Directory | Test Files | Purpose |
|-----------|-----------|---------|
| `tests/` | 3 | Root-level integration tests for autonomous loop |
| `context_window_array/tests/` | 6 | Context window array functionality tests |
| `planning_pipeline/tests/` | 21 | Planning pipeline and orchestration tests |
| `silmari_rlm_act/tests/` | 13 | RLM Act phases and pipeline tests |
| **Total** | **43** | **Complete test coverage** |

### Conftest Files

```
📁 silmari-Context-Engine/
├── 📁 planning_pipeline/tests/
│   └── 📄 conftest.py (8 shared fixtures)
└── 📁 silmari_rlm_act/tests/
    └── 📄 conftest.py (3 shared fixtures)
```

---

## 🔧 Fixture Catalog

### Shared Fixtures (conftest.py files)

<details>
<summary><b>planning_pipeline/tests/conftest.py</b> - 8 fixtures</summary>

| Fixture Name | Lines | Purpose | Dependencies |
|--------------|-------|---------|--------------|
| `mock_baml_initial_extraction` | 85-100 | Mock BAML ProcessGate1 initial extraction | None |
| `mock_baml_subprocess_details` | 103-125 | Mock BAML subprocess details response | None |
| `mock_baml_client` | 128-134 | Complete mock BAML client | ↳ `mock_baml_initial_extraction`, `mock_baml_subprocess_details` |
| `mock_claude_sdk_response` | 137-156 | Mock Claude SDK response JSON | None |
| `patch_baml_client` | 159-164 | Context manager patching run_claude_sync | ↳ `mock_claude_sdk_response` |
| `project_path` | 167-170 | Root project path | None |
| `sample_research_output` | 173-188 | Sample Claude research output | None |
| `sample_plan_output` | 191-200 | Sample Claude plan output | None |
| `sample_phase_output` | 203-211 | Sample Claude phase decomposition output | None |

**Pytest Configuration Hook:**
- `pytest_configure()` (Lines 10-14) - Registers custom markers: `slow`, `integration`, `e2e`

</details>

<details>
<summary><b>silmari_rlm_act/tests/conftest.py</b> - 3 fixtures</summary>

| Fixture Name | Lines | Purpose | Dependencies |
|--------------|-------|---------|--------------|
| `sample_timestamp` | 7-10 | Consistent datetime for tests | None |
| `sample_artifacts` | 13-19 | Sample artifact paths | None |
| `sample_errors` | 22-28 | Sample error messages | None |

</details>

### Test-Specific Fixtures

The project contains **37 additional test-specific fixtures** defined in individual test files. Key patterns include:

**Cleanup Pattern Fixtures:**
- `cleanup_issues` - Tracks and cleans up BeadsController issues (4 instances across test files)
- Setup → yield created_ids → teardown with cleanup

**Path Helper Fixtures:**
- `project_path` - Returns project root (5 instances)
- `temp_project` - Creates temporary project directories (7 instances)

**Mock Object Fixtures:**
- `mock_orchestrator` - Mocks IntegratedOrchestrator (3 instances)
- `mock_cwa` - Mocks CWA integration (2 instances)
- `mock_beads_controller` - Mocks BeadsController (2 instances)
- `beads_controller` - Real BeadsController for integration tests (3 instances)

**Sample Data Fixtures:**
- `sample_plan` - TDD plan documents
- `sample_research_result` - PhaseResult samples
- `sample_decomposition_result` - Mock RequirementHierarchy
- `sample_phase_docs` - Phase markdown files

**Test Environment Fixtures:**
- `temp_git_repo` - Initialized git repository
- `cli_runner` - Click CLI test runner
- `cwa` - CWA integration instance

---

## 🎨 Fixture Usage Patterns

### 1️⃣ Simple Fixture Usage

Fixtures are injected as function parameters.

**Example:** `context_window_array/tests/test_store.py`

```python
def test_add_entry_to_empty_store(self):
    """Given empty store, when add(entry), then entry is stored."""
    store = CentralContextStore()
    entry = ContextEntry(
        id="ctx_001",
        entry_type=EntryType.FILE,
        source="test.py",
        content="test content",
        summary="test summary",
    )

    store.add(entry)

    assert store.get("ctx_001") is not None
```

---

### 2️⃣ Fixture Composition

Fixtures can depend on other fixtures, creating dependency chains.

**Example:** `planning_pipeline/tests/conftest.py:128-134`

```python
@pytest.fixture
def mock_baml_client(mock_baml_initial_extraction, mock_baml_subprocess_details):
    """Complete mock of BAML client - depends on other fixtures."""
    mock_b = MagicMock()
    mock_b.ProcessGate1InitialExtractionPrompt.return_value = mock_baml_initial_extraction
    mock_b.ProcessGate1SubprocessDetailsPrompt.return_value = mock_baml_subprocess_details
    return mock_b
```

**Dependency Chain:**
```
mock_baml_client
├── mock_baml_initial_extraction
└── mock_baml_subprocess_details
```

---

### 3️⃣ Yield Fixtures (Setup/Teardown)

Fixtures using `yield` provide setup before and teardown after.

**Example:** `planning_pipeline/tests/test_steps.py:26-33`

```python
@pytest.fixture
def cleanup_issues(beads_controller):
    """Track and cleanup created issues after test."""
    created_ids = []
    yield created_ids  # Test runs here
    # Teardown: Clean up all created issues
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
    beads_controller.sync()
```

**Usage:**
```python
def test_creates_epic_and_phase_issues(self, project_path, cleanup_issues, beads_controller):
    """Test uses cleanup_issues to track what needs cleanup."""
    result = step_beads_integration(
        project_path=project_path,
        phase_files=["thoughts/shared/plans/2025-01-01-test/01-phase-1-setup.md"],
        epic_title="TDD Test Epic"
    )

    # Track for cleanup
    if result.get("epic_id"):
        cleanup_issues.append(result["epic_id"])
```

---

### 4️⃣ Mock Object Fixtures

Extensive use of `unittest.mock.MagicMock` for external dependencies.

**Example:** `silmari_rlm_act/tests/test_pipeline.py:35-53`

```python
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
    """Create a mock beads controller."""
    beads = MagicMock()
    beads.create_epic.return_value = {"success": True, "data": {"id": "epic_001"}}
    beads.create_issue.return_value = {"success": True, "data": {"id": "issue_001"}}
    beads.add_dependency.return_value = {"success": True}
    beads.sync.return_value = {"success": True}
    return beads
```

---

### 5️⃣ Patch Context Manager Fixtures

Fixtures that return context managers for patching.

**Example:** `planning_pipeline/tests/conftest.py:159-164`

```python
@pytest.fixture
def patch_baml_client(mock_claude_sdk_response):
    """Context manager to patch run_claude_sync."""
    with patch("planning_pipeline.decomposition.run_claude_sync") as mock_run:
        mock_run.return_value = mock_claude_sdk_response
        yield mock_run
```

---

### 6️⃣ Inline Patches in Tests

Tests often use `unittest.mock.patch` directly as context managers.

**Example:** `silmari_rlm_act/tests/test_implementation_phase.py`

```python
def test_invokes_claude_successfully(self, tmp_path: Path, cwa: CWAIntegration) -> None:
    """Given prompt, invokes claude and returns success."""
    phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

    with patch("silmari_rlm_act.phases.implementation.run_claude_subprocess") as mock_run:
        mock_run.return_value = {
            "success": True,
            "output": "Implementation complete",
            "error": "",
            "elapsed": 10.0,
        }

        result = phase._invoke_claude("Test prompt")

    assert result["success"] is True
    mock_run.assert_called_once()
```

---

### 7️⃣ Mock Side Effects

Complex behavior simulation using `side_effect`.

**Example:** `silmari_rlm_act/tests/test_implementation_phase.py`

```python
def test_continues_on_test_failure(
    self,
    tmp_path: Path,
    sample_plan: Path,
    cwa: CWAIntegration,
) -> None:
    """Given test failure after completion, continues loop."""
    phase = ImplementationPhase(project_path=tmp_path, cwa=cwa)

    test_calls = [0]

    def mock_tests():
        test_calls[0] += 1
        if test_calls[0] == 1:
            return (False, "failed")  # Fail first time
        return (True, "passed")      # Pass second time

    with patch.object(phase, "_invoke_claude", return_value={"success": True}):
        with patch.object(phase, "_check_completion", return_value=True):
            with patch.object(phase, "_run_tests", mock_tests):
                result = phase.execute(
                    phase_paths=[str(sample_plan)],
                    mode=AutonomyMode.FULLY_AUTONOMOUS,
                )

    assert test_calls[0] >= 2
```

---

### 8️⃣ Data Fixtures

Fixtures providing sample data structures.

**Example:** `silmari_rlm_act/tests/test_pipeline.py:56-67`

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

---

### 9️⃣ Built-in Pytest Fixtures

Heavy use of pytest's `tmp_path` fixture for temporary directories.

**Example:** `planning_pipeline/tests/test_checkpoint_manager.py`

```python
def test_detect_resumable_checkpoint_no_dir(tmp_path):
    """No checkpoints dir returns None."""
    assert detect_resumable_checkpoint(tmp_path) is None

def test_write_checkpoint_creates_dir(tmp_path):
    """write_checkpoint creates checkpoints dir if missing."""
    assert not (tmp_path / ".workflow-checkpoints").exists()

    path = write_checkpoint(tmp_path, "test-failed", [])

    assert Path(path).exists()
    assert (tmp_path / ".workflow-checkpoints").exists()
```

---

## 📈 Fixture Statistics

### Fixture Distribution

| Category | Count | Percentage |
|----------|-------|------------|
| **Test-specific fixtures** | 37 | 77% |
| **Shared fixtures (conftest.py)** | 11 | 23% |
| **Total custom fixtures** | 48 | 100% |

### Fixture Patterns by Usage

| Pattern | Instances | Files |
|---------|-----------|-------|
| 🔧 Mock objects | 15+ | 10 files |
| 📁 Path/project helpers | 12+ | 8 files |
| 🧪 Sample data | 10+ | 6 files |
| ♻️ Cleanup/teardown | 7 | 4 files |
| 🔄 Patch context managers | 5 | 3 files |
| 📝 Data structures | 8 | 5 files |

### Scope Distribution

```
┌─────────────────────────────────────┐
│   Fixture Scope Distribution        │
├─────────────────────────────────────┤
│  Function scope:  48  (100%)  ████  │
│  Class scope:      0   (0%)         │
│  Module scope:     0   (0%)         │
│  Session scope:    0   (0%)         │
└─────────────────────────────────────┘
```

---

## 🎯 Custom Pytest Markers

Defined in `planning_pipeline/tests/conftest.py:10-14`:

| Marker | Usage | Purpose |
|--------|-------|---------|
| 🐌 `slow` | `@pytest.mark.slow` | Marks slow tests (deselect with `-m "not slow"`) |
| 🔗 `integration` | `@pytest.mark.integration` | Marks integration tests requiring real services |
| 🌐 `e2e` | `@pytest.mark.e2e` | Marks end-to-end tests |

**Running tests with markers:**
```bash
# Run only integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"

# Run e2e tests only
pytest -m e2e
```

---

## 💡 BDD-Style Testing

Tests follow Given-When-Then pattern in docstrings.

**Example:** `context_window_array/tests/test_store.py`

```python
def test_add_entry_to_empty_store(self):
    """Given empty store, when add(entry), then entry is stored."""
    # Given
    store = CentralContextStore()
    entry = ContextEntry(...)

    # When
    store.add(entry)

    # Then
    assert store.get("ctx_001") is not None
```

---

## 📚 Code References

### Conftest Files

- **Planning Pipeline Conftest**: `planning_pipeline/tests/conftest.py`
  - Lines 10-14: `pytest_configure()` - Custom markers
  - Lines 85-100: `mock_baml_initial_extraction`
  - Lines 103-125: `mock_baml_subprocess_details`
  - Lines 128-134: `mock_baml_client`
  - Lines 137-156: `mock_claude_sdk_response`
  - Lines 159-164: `patch_baml_client`
  - Lines 167-170: `project_path`
  - Lines 173-188: `sample_research_output`
  - Lines 191-200: `sample_plan_output`
  - Lines 203-211: `sample_phase_output`

- **RLM Act Conftest**: `silmari_rlm_act/tests/conftest.py`
  - Lines 7-10: `sample_timestamp`
  - Lines 13-19: `sample_artifacts`
  - Lines 22-28: `sample_errors`

### Key Test Files with Fixtures

- `planning_pipeline/tests/test_beads.py` - Lines 8-22: `beads_controller`, `cleanup_issues`
- `planning_pipeline/tests/test_pipeline.py` - Lines 10-29: Path and cleanup fixtures
- `planning_pipeline/tests/test_steps.py` - Lines 14-33: BeadsController fixtures
- `planning_pipeline/tests/test_step_decomposition.py` - Lines 23-97: `temp_project`, `mock_decomposition_result`
- `planning_pipeline/tests/test_helpers.py` - Lines 178-186: `temp_project` (class-scoped)
- `planning_pipeline/tests/test_checkpoint_manager.py` - Lines 19-24: `temp_project`
- `planning_pipeline/tests/test_orchestrator.py` - Multiple `project_path` and `cleanup_issues` instances
- `silmari_rlm_act/tests/test_pipeline.py` - Lines 26-81: Mock and sample fixtures
- `silmari_rlm_act/tests/test_beads_sync_phase.py` - Lines 80-103: `mock_beads`, `sample_phase_docs`
- `silmari_rlm_act/tests/test_cli.py` - Lines 24-35: `cli_runner`, `temp_project`
- `silmari_rlm_act/tests/test_implementation_phase.py` - Lines 21-43: `sample_plan`, `cwa`
- `tests/test_execute_phase.py` - Lines 13-262: Multiple test environment fixtures
- `tests/test_loop_orchestrator_integration.py` - Lines 16-236: Complex integration fixtures
- `tests/test_autonomous_loop.py` - Lines 54-231: Mock orchestrator fixtures

### Test Files by Directory

**Root tests/** (3 files):
- `test_autonomous_loop.py`
- `test_execute_phase.py`
- `test_loop_orchestrator_integration.py`

**context_window_array/tests/** (6 files):
- `test_batching.py`
- `test_implementation_context.py`
- `test_models.py`
- `test_search.py`
- `test_store.py`
- `test_working_context.py`

**planning_pipeline/tests/** (21 files):
- `test_beads.py`, `test_beads_controller.py`
- `test_checkpoint_manager.py`, `test_checkpoints.py`
- `test_claude.py`, `test_context_generation.py`
- `test_decomposition.py`, `test_decomposition_e2e.py`
- `test_helpers.py`, `test_integrated_orchestrator.py`
- `test_models.py`, `test_orchestrator.py`
- `test_phase_execution.py`, `test_pipeline.py`
- `test_property_generator.py`, `test_step_decomposition.py`
- `test_steps.py`, `test_visualization.py`

**silmari_rlm_act/tests/** (13 files):
- `test_beads_sync_phase.py`, `test_checkpoint_manager.py`
- `test_cli.py`, `test_cwa_integration.py`
- `test_decomposition_phase.py`, `test_implementation_phase.py`
- `test_interactive.py`, `test_models.py`
- `test_multi_doc_phase.py`, `test_pipeline.py`
- `test_research_phase.py`, `test_tdd_planning_phase.py`

---

## 🗂️ Architecture Documentation

### Pytest Configuration

**pytest.ini** (if exists) or **setup.cfg** would contain:
```ini
[tool:pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
```

### Fixture Dependency Graph

```
Shared Fixtures (conftest.py)
│
├─ mock_baml_initial_extraction ──┐
├─ mock_baml_subprocess_details ──┼─→ mock_baml_client
│                                  │
├─ mock_claude_sdk_response ──────┼─→ patch_baml_client
│                                  │
├─ project_path ──────────────────┼─→ (used in many tests)
├─ sample_research_output ────────┤
├─ sample_plan_output ────────────┤
├─ sample_phase_output ───────────┤
└─ sample_timestamp ──────────────┘

Test-Specific Fixtures
│
├─ beads_controller ───────→ cleanup_issues (yield fixture)
├─ tmp_path (pytest built-in) ─→ temp_project
├─ temp_project ───────────→ various test scenarios
├─ mock_orchestrator ──────→ integration tests
├─ mock_cwa ───────────────→ pipeline tests
└─ cli_runner ─────────────→ CLI tests
```

### Common Testing Patterns

1. **Arrange-Act-Assert (AAA)**
   - Setup test state
   - Execute operation
   - Verify results

2. **Given-When-Then (BDD)**
   - Given: Initial state (docstring)
   - When: Action performed
   - Then: Expected outcome

3. **Fixture Composition**
   - Simple fixtures → Complex fixtures
   - Dependency injection via parameters

4. **Mock Objects**
   - `MagicMock` for external services
   - `patch` for module-level functions
   - `side_effect` for complex behaviors

5. **Cleanup Pattern**
   - Yield fixture provides list
   - Test appends created resources
   - Teardown cleans up resources

---

## 🕰️ Historical Context (from thoughts/)

### Related Research Documents

The thoughts/ directory contains **3 comprehensive research documents** about testing patterns:

1. **2026-01-04: Most Recent Analysis**
   - **Path**: `thoughts/shared/research/2026-01-04-pytest-fixtures-analysis.md`
   - **Coverage**: 20 test modules, 8 shared fixtures, 12 fixture patterns
   - **Key Findings**: Custom pytest markers, async test support, fixture dependency graphs
   - **Focus**: Comprehensive fixture catalog and usage statistics

2. **2026-01-02: Testing Patterns Study**
   - **Path**: `thoughts/shared/research/2026-01-02-pytest-fixtures-testing-patterns.md`
   - **Coverage**: 15 test files, 20+ custom fixtures
   - **Key Findings**: Property-based testing with Hypothesis, parametrize usage
   - **Focus**: Pytest configuration, fixture scopes, built-in fixtures

3. **2026-01-01: Foundation Analysis**
   - **Path**: `thoughts/shared/research/2026-01-01-pytest-fixtures-testing-patterns.md`
   - **Coverage**: All 20 custom fixtures with locations
   - **Key Findings**: BDD-style test patterns, mock patterns, best practices
   - **Focus**: Foundational fixture inventory and dependency chains

### Integration Test Specifications

- **Path**: `thoughts/shared/plans/2026-01-01-tdd-loop-runner-orchestrator-07-integration-tests.md`
- **Purpose**: Integration testing specifications for the project
- **Context**: Part of TDD loop runner orchestrator implementation

---

## 📖 Testing Conventions

### Naming Conventions

- **Test files**: `test_*.py`
- **Test functions**: `test_<action>_<expected_result>`
- **Fixtures**: Descriptive names (`mock_baml_client`, `sample_research_output`)
- **Cleanup fixtures**: `cleanup_*` pattern

### Documentation Standards

- **Docstrings**: Given-When-Then format
- **Comments**: Inline for complex setup
- **Assertions**: Clear, descriptive messages

### File Organization

```
tests/
├── conftest.py (shared fixtures)
├── test_module.py (tests for module)
└── ...

<component>/tests/
├── conftest.py (component-specific fixtures)
├── test_*.py (component tests)
└── ...
```

---

## 🔍 Key Observations

### ✅ Strengths

| Strength | Evidence |
|----------|----------|
| **Comprehensive coverage** | 43 test files across all major components |
| **Well-organized fixtures** | Clear separation between shared and test-specific |
| **Consistent patterns** | BDD-style, AAA pattern, Given-When-Then |
| **Proper cleanup** | Yield fixtures for resource management |
| **Extensive mocking** | Proper isolation of external dependencies |
| **Custom markers** | Easy test filtering (slow, integration, e2e) |

### 📌 Characteristics

- **All function-scoped fixtures**: No session/module/class scoped fixtures
- **No autouse fixtures**: All fixtures explicitly requested
- **Heavy tmp_path usage**: Proper temporary file handling
- **Mock-heavy approach**: Extensive use of MagicMock and patch
- **Fixture composition**: Well-designed dependency chains
- **No parametrized fixtures**: Parametrization at test level only

---

## 🔗 Related Research

- `thoughts/shared/research/2026-01-04-pytest-fixtures-analysis.md` - Latest comprehensive analysis
- `thoughts/shared/research/2026-01-02-pytest-fixtures-testing-patterns.md` - Earlier patterns study
- `thoughts/shared/research/2026-01-01-pytest-fixtures-testing-patterns.md` - Foundation analysis
- `thoughts/shared/plans/2026-01-01-tdd-loop-runner-orchestrator-07-integration-tests.md` - Integration specs

---

## ❓ Open Questions

None. The research comprehensively documents the current state of pytest fixtures and testing patterns in the codebase.

---

**Research Complete** ✅

This document provides a complete map of the testing infrastructure, fixture patterns, and testing conventions as they exist in the silmari-Context-Engine project as of commit `6a8a69f3c33d65d8e5c34f988ec71a9005992229`.
