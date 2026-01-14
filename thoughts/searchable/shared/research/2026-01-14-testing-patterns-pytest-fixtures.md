---
date: 2026-01-14T15:20:28-05:00
researcher: Claude Sonnet 4.5
git_commit: 2fedd728165afad597235632281e98191712e06a
branch: main
repository: silmari-Context-Engine
topic: "Testing Patterns in Project - Focus on Pytest Fixtures"
tags: [research, codebase, testing, pytest, fixtures, test-patterns]
status: complete
last_updated: 2026-01-14
last_updated_by: Claude Sonnet 4.5
---

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║       PYTEST FIXTURES & TESTING PATTERNS RESEARCH             ║
║              Silmari Context Engine Project                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

# Research: Testing Patterns in Project - Focus on Pytest Fixtures

**Date**: 2026-01-14T15:20:28-05:00
**Researcher**: Claude Sonnet 4.5
**Git Commit**: `2fedd728165afad597235632281e98191712e06a`
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📚 Research Question

Analyze the testing patterns in this project with a focus on pytest fixtures - their organization, patterns, usage, and integration across the test suite.

---

## 🎯 Summary

The project implements a comprehensive testing infrastructure built around pytest with **46 Python test files**, **2 centralized conftest.py files**, and **30+ custom fixtures**. The testing strategy emphasizes **behavior-driven organization**, **property-based testing with Hypothesis**, and **extensive mocking** of external services (BAML, Claude SDK, Beads, subprocess calls, and CWA integration).

### Key Characteristics

| Aspect | Details |
|--------|---------|
| **Total Python Test Files** | 46 files (~1 MB of test code) |
| **Total Go Test Files** | 26 files (colocated with source) |
| **Conftest Files** | 2 (planning_pipeline, silmari_rlm_act) |
| **Custom Fixtures** | 30+ shared, 48+ file-specific |
| **Fixture Scope** | 100% function-scoped (complete isolation) |
| **Primary Patterns** | Mock objects, temporary resources, cleanup/teardown, factory patterns |
| **Testing Frameworks** | pytest + pytest-asyncio + Hypothesis |
| **Custom Markers** | `@slow`, `@integration`, `@e2e` |

---

## 📊 Detailed Findings

### 1. Test Directory Structure

```
silmari-Context-Engine/
├── tests/                              (3 files - Root integration tests)
│   ├── test_autonomous_loop.py
│   ├── test_execute_phase.py
│   └── test_loop_orchestrator_integration.py
│
├── planning_pipeline/tests/            (21 files + conftest.py)
│   ├── conftest.py                     (348 lines - Main fixture hub)
│   ├── test_beads.py
│   ├── test_beads_controller.py
│   ├── test_checkpoint_manager.py
│   ├── test_checkpoints.py
│   ├── test_claude.py
│   ├── test_claude_runner.py           (46KB - largest)
│   ├── test_context_generation.py
│   ├── test_decomposition.py           (29KB)
│   ├── test_decomposition_e2e.py       (13KB)
│   ├── test_helpers.py                 (29KB)
│   ├── test_integrated_orchestrator.py (21KB)
│   ├── test_models.py                  (43KB - second largest)
│   ├── test_orchestrator.py            (29KB)
│   ├── test_phase_execution.py
│   ├── test_pipeline.py                (16KB)
│   ├── test_property_generator.py      (23KB)
│   ├── test_step_decomposition.py      (11KB)
│   ├── test_steps.py
│   └── test_visualization.py           (13KB)
│
├── silmari_rlm_act/tests/              (16 files + conftest.py)
│   ├── conftest.py                     (29 lines - minimal)
│   ├── test_artifact_generation.py     (31KB)
│   ├── test_beads_sync_phase.py        (15KB)
│   ├── test_checkpoint_manager.py      (14KB)
│   ├── test_cli.py                     (55KB)
│   ├── test_cwa_integration.py         (20KB)
│   ├── test_decomposition_phase.py     (12KB)
│   ├── test_implementation_phase.py    (15KB)
│   ├── test_interactive.py             (18KB)
│   ├── test_models.py                  (17KB)
│   ├── test_multi_doc_phase.py         (17KB)
│   ├── test_pipeline.py                (113KB - largest overall)
│   ├── test_research_phase.py          (20KB)
│   ├── test_tdd_planning_phase.py      (18KB)
│   └── test_validation.py              (16KB)
│
├── context_window_array/tests/         (6 files - no conftest)
│   ├── test_batching.py                (19KB)
│   ├── test_implementation_context.py  (25KB)
│   ├── test_models.py                  (33KB)
│   ├── test_search.py                  (23KB)
│   ├── test_store.py                   (36KB)
│   └── test_working_context.py         (16KB)
│
└── go/internal/                        (26 Go test files - colocated)
    ├── build/*_test.go
    ├── cli/*_test.go
    ├── concurrent/*_test.go
    ├── exec/*_test.go
    ├── planning/*_test.go
    └── ...
```

---

### 2. 🔧 Core Fixture Locations

#### `/home/maceo/Dev/silmari-Context-Engine/planning_pipeline/tests/conftest.py`

**Purpose**: Central fixture hub for decomposition and planning pipeline tests (348 lines)

<details>
<summary><b>📦 Fixture Inventory</b></summary>

| Fixture Name | Lines | Dependencies | Purpose |
|--------------|-------|--------------|---------|
| `mock_baml_initial_extraction` | 85-100 | None | Returns MockInitialExtractionResponse with sample requirements |
| `mock_baml_subprocess_details` | 103-125 | None | Returns MockSubprocessDetailsResponse with implementation details |
| `mock_baml_client` | 128-134 | Above 2 fixtures | Complete BAML client mock for unit tests |
| `mock_claude_sdk_response` | 137-156 | None | Mock first call to run_claude_sync (extraction) |
| `mock_claude_expansion_response` | 159-216 | None | Mock second call to run_claude_sync (expansion) |
| `mock_claude_expansion_response_limited` | 219-254 | None | Mock response with limited data (max_sub_processes tests) |
| `patch_baml_client` | 257-300 | Above 3 mock responses | Context manager with side_effect for multi-call mocking |
| `project_path` | 303-306 | None | Returns root project path (Path object) |
| `sample_research_output` | 309-324 | None | Sample Claude output with research file path |
| `sample_plan_output` | 327-336 | None | Sample Claude output with plan file path |
| `sample_phase_output` | 339-347 | None | Sample Claude output with phase file paths |

</details>

**Mock Types (Dataclasses)**:
- `MockImplementationComponents` (lines 22-27)
- `MockImplementationDetail` (lines 30-40)
- `MockRequirement` (lines 43-48)
- `MockResponseMetadata` (lines 51-53)
- `MockInitialExtractionResponse` (lines 56-66)
- `MockSubprocessDetailsResponse` (lines 69-78)

**Custom Markers** (lines 8-19):
```python
pytest_configure():
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
```

#### `/home/maceo/Dev/silmari-Context-Engine/silmari_rlm_act/tests/conftest.py`

**Purpose**: Simple fixtures for RLM Act pipeline tests (29 lines)

| Fixture Name | Returns | Purpose |
|--------------|---------|---------|
| `sample_timestamp` | `datetime` | Consistent timestamp: `datetime(2026, 1, 5, 10, 30, 0)` |
| `sample_artifacts` | `list[str]` | Sample artifact paths (2 files) |
| `sample_errors` | `list[str]` | Sample error messages (2 errors) |

---

### 3. 🎨 Fixture Patterns

#### Pattern 1: **Simple Value Fixtures**

Fixtures that return static test data for consistent testing.

**Example:** `sample_timestamp` fixture
**File:** `silmari_rlm_act/tests/conftest.py:7-10`

```python
@pytest.fixture
def sample_timestamp() -> datetime:
    """Provide a consistent timestamp for tests."""
    return datetime(2026, 1, 5, 10, 30, 0)
```

#### Pattern 2: **Temporary Resource Fixtures**

Fixtures that create temporary directories/files for test isolation.

**Example:** `temp_project` fixture
**File:** `planning_pipeline/tests/test_step_decomposition.py:24-51`

```python
@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure for testing."""
    research_dir = tmp_path / "thoughts" / "shared" / "research"
    research_dir.mkdir(parents=True)
    research_file = research_dir / "2026-01-02-test-research.md"
    research_file.write_text("""
# Research: User Authentication System
## Key Findings
- System supports JWT tokens
- Session management required
    """)
    return tmp_path, str(research_file.relative_to(tmp_path))
```

#### Pattern 3: **Mock Object Fixtures**

Fixtures that return configured MagicMock objects for dependency injection.

**Example:** `mock_baml_client` fixture
**File:** `planning_pipeline/tests/conftest.py:128-134`

```python
@pytest.fixture
def mock_baml_client(mock_baml_initial_extraction, mock_baml_subprocess_details):
    """Complete mock of BAML client for unit tests (legacy)."""
    mock_b = MagicMock()
    mock_b.ProcessGate1InitialExtractionPrompt.return_value = mock_baml_initial_extraction
    mock_b.ProcessGate1SubprocessDetailsPrompt.return_value = mock_baml_subprocess_details
    return mock_b
```

#### Pattern 4: **Cleanup/Teardown Fixtures**

Fixtures that use `yield` to provide setup/teardown behavior.

**Example:** `cleanup_issues` fixture
**File:** `planning_pipeline/tests/test_pipeline.py:22-29`

```python
@pytest.fixture
def cleanup_issues(beads_controller):
    """Track and cleanup created issues after test."""
    created_ids = []
    yield created_ids  # Fixture value provided to test
    # Cleanup code runs after test completes
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
    beads_controller.sync()
```

**Usage:**
```python
def test_runs_pipeline_with_auto_approve(self, project_path, cleanup_issues):
    """Given valid prompt with auto-approve, executes full pipeline."""
    result = run_pipeline(...)
    if result.get("epic_id"):
        cleanup_issues.append(result["epic_id"])  # Register for cleanup
    # After test, cleanup fixture automatically runs
```

#### Pattern 5: **Context Manager Fixtures (Patch Fixtures)**

Fixtures that provide patching behavior using context managers.

**Example:** `patch_baml_client` fixture
**File:** `planning_pipeline/tests/conftest.py:257-301`

```python
@pytest.fixture
def patch_baml_client(mock_claude_sdk_response, mock_claude_expansion_response,
                      mock_claude_expansion_response_limited):
    """Context manager to patch run_claude_sync for decomposition tests.

    First call returns initial extraction (requirements with sub_processes).
    Subsequent calls return expansion (implementation_details).
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
        mock_run.override_return = override_return  # Allow test override
        yield mock_run
```

#### Pattern 6: **Factory/Builder Fixtures**

Fixtures that depend on other fixtures to build complex objects.

**Example:** `mock_decomposition_result` fixture
**File:** `planning_pipeline/tests/test_step_decomposition.py:54-87`

```python
@pytest.fixture
def mock_decomposition_result():
    """Create a mock RequirementHierarchy for testing."""
    parent = RequirementNode(
        id="REQ_000",
        description="User Authentication System",
        type="parent",
        acceptance_criteria=["Users can log in", "Sessions are tracked"],
    )
    child1 = RequirementNode(
        id="REQ_000.1",
        description="JWT Token Generation",
        type="child",
        acceptance_criteria=["Tokens expire after 24h"],
    )
    child2 = RequirementNode(
        id="REQ_000.2",
        description="Session Management",
        type="child",
        acceptance_criteria=["Sessions persist across page refreshes"],
    )
    parent.children = [child1, child2]
    hierarchy = RequirementHierarchy(requirements=[parent])
    return hierarchy
```

---

### 4. 🔗 Fixture Dependency Chains

Fixtures often depend on other fixtures, creating dependency graphs:

#### Chain 1: Project → Controller → Cleanup
```
project_path
    ↓
beads_controller (depends on project_path)
    ↓
cleanup_issues (depends on beads_controller)
```

**File:** `planning_pipeline/tests/test_pipeline.py:10-29`

#### Chain 2: Mock Responses → Patch
```
mock_claude_sdk_response
mock_claude_expansion_response        →  patch_baml_client
mock_claude_expansion_response_limited
```

**File:** `planning_pipeline/tests/conftest.py:257-301`

#### Chain 3: Temp Path → Project Structure
```
tmp_path (pytest built-in)
    ↓
temp_project (creates directory structure)
```

**File:** `planning_pipeline/tests/test_step_decomposition.py:24-51`

#### Chain 4: Mock Components → Mock Client
```
mock_baml_initial_extraction
    ↓
mock_baml_subprocess_details  →  mock_baml_client
```

**File:** `planning_pipeline/tests/conftest.py:85-134`

---

### 5. 🧪 Property-Based Testing with Hypothesis

The project extensively uses Hypothesis for property-based testing with custom strategies.

#### Hypothesis Strategies

| Strategy | File | Purpose |
|----------|------|---------|
| `_requirement_id_strategy` | test_visualization.py:26-37 | Generates valid requirement IDs (REQ_001, REQ_001.2) |
| `_non_whitespace_text` | test_visualization.py:40-48 | Generates non-whitespace text strings |
| `_simple_requirement_node_strategy` | test_visualization.py:51-82 | Generates RequirementNode with optional children |
| `_hierarchy_strategy` | test_visualization.py:85-93 | Generates RequirementHierarchy (0-5 requirements) |
| `_criterion_with_keyword` | test_property_generator.py:18-24 | Generates criteria containing keywords |
| `_requirement_id_strategy` | test_models.py:32-44 | Generates requirement IDs with sub-levels |
| `_implementation_components_strategy` | test_models.py:47-55 | Generates ImplementationComponents dict |
| `_testable_property_strategy` | test_models.py:67-76 | Generates TestableProperty dict |
| `_requirement_node_strategy` | test_models.py:79-115 | Generates RequirementNode dict |

**Example Strategy:**
**File:** `planning_pipeline/tests/test_visualization.py:26-37`

```python
@st.composite
def _requirement_id_strategy(draw):
    """Strategy for generating valid requirement IDs."""
    prefix = "REQ"
    num = draw(st.integers(min_value=0, max_value=999))
    base_id = f"{prefix}_{num:03d}"

    # Optionally add sub-levels (REQ_001.2.1)
    num_sublevels = draw(st.integers(min_value=0, max_value=2))
    for _ in range(num_sublevels):
        sublevel = draw(st.integers(min_value=1, max_value=9))
        base_id += f".{sublevel}"

    return base_id
```

#### Stateful Testing

**File:** `planning_pipeline/tests/test_models.py:580-675`

```python
class RequirementHierarchyStateMachine(RuleBasedStateMachine):
    """Stateful testing for RequirementHierarchy invariants."""

    parents = Bundle("parents")
    children = Bundle("children")

    def __init__(self):
        super().__init__()
        self.hierarchy = RequirementHierarchy(requirements=[])

    @rule(target=parents, requirement_data=_requirement_node_strategy())
    def add_parent_requirement(self, requirement_data):
        """Add a parent requirement to hierarchy."""
        req = RequirementNode(**requirement_data)
        self.hierarchy.requirements.append(req)
        return req

    @rule(parent=parents, child_data=_requirement_node_strategy())
    def add_child_to_parent(self, parent, child_data):
        """Add a child to an existing parent."""
        child = RequirementNode(**child_data)
        if not parent.children:
            parent.children = []
        parent.children.append(child)
        return child

    @invariant()
    def ids_are_unique(self):
        """All requirement IDs should be unique."""
        all_ids = [req.id for req in self.hierarchy.requirements]
        assert len(all_ids) == len(set(all_ids))

    @invariant()
    def parent_child_consistency(self):
        """Parent-child relationships should be consistent."""
        for req in self.hierarchy.requirements:
            if req.children:
                for child in req.children:
                    assert child.id.startswith(req.id)
```

---

### 6. 🎭 Mocking Strategies

#### External Service Mocking

| Service | Mock Location | Purpose |
|---------|---------------|---------|
| **BAML Client** | `conftest.py:85-134` | Mock LLM extraction/expansion calls |
| **Claude SDK** | `conftest.py:137-254` | Mock `run_claude_sync` responses |
| **Beads Tracker** | Test-specific | Mock issue creation/tracking |
| **Subprocess** | Test-specific | Mock git/shell commands |
| **CWA Integration** | `silmari_rlm_act/tests/test_pipeline.py` | Mock context window array storage |

#### Multi-Call Mocking Pattern

The `patch_baml_client` fixture demonstrates advanced multi-call mocking:

```python
def side_effect(*args, **kwargs):
    """Returns different values for first vs subsequent calls."""
    if override_return[0] is not None:
        return override_return[0]  # Allow test override
    call_count[0] += 1
    if call_count[0] == 1:
        return mock_claude_sdk_response  # First call: extraction
    return mock_claude_expansion_response  # Subsequent: expansion
```

---

### 7. 📝 Naming Conventions

| Prefix | Purpose | Examples |
|--------|---------|----------|
| `mock_` | Mock objects/responses | `mock_baml_client`, `mock_claude_sdk_response` |
| `patch_` | Context manager patches | `patch_baml_client` |
| `temp_` | Temporary resources | `temp_project`, `temp_plan_file` |
| `sample_` | Static test data | `sample_timestamp`, `sample_artifacts`, `sample_errors` |
| `cleanup_` | Cleanup fixtures | `cleanup_issues` |
| `_strategy` | Hypothesis strategies | `_requirement_id_strategy`, `_hierarchy_strategy` |

---

### 8. 🔄 Fixture Usage Examples

#### Example 1: Simple Fixture Passing

**File:** `planning_pipeline/tests/test_beads.py:28-39`

```python
def test_creates_task_issue(self, beads_controller, cleanup_issues):
    """Given valid title/type/priority, creates issue and returns success."""
    result = beads_controller.create_issue(
        title="TDD Test Issue - Create",
        issue_type="task",
        priority=2
    )
    assert result["success"] is True
    assert "data" in result
    # Track for cleanup
    if isinstance(result["data"], dict) and "id" in result["data"]:
        cleanup_issues.append(result["data"]["id"])
```

#### Example 2: Multiple Fixtures with Dependencies

**File:** `planning_pipeline/tests/test_step_decomposition.py:93-119`

```python
def test_creates_hierarchy_json(self, temp_project, mock_decomposition_result):
    """Step should create requirements_hierarchy.json file."""
    project_path, research_path = temp_project

    with patch(
        "planning_pipeline.step_decomposition.decompose_requirements"
    ) as mock_decompose:
        mock_decompose.return_value = mock_decomposition_result
        result = step_requirement_decomposition(
            project_path=project_path,
            research_path=research_path,
        )

        assert result["success"] is True
        hierarchy_path = Path(result["hierarchy_path"])
        assert hierarchy_path.exists()
```

#### Example 3: Monkeypatch for Input Mocking

**File:** `planning_pipeline/tests/test_pipeline.py:193-216`

```python
def test_prompts_on_decomposition_failure(self, tmp_path, monkeypatch, capsys):
    """Should show (R)etry/(C)ontinue prompt when decomposition fails."""
    inputs = iter(["c"])  # User chooses "continue"
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch.multiple(
        "planning_pipeline.pipeline",
        step_research=lambda *a, **kw: {"success": True, "research_path": "r.md", "output": ""},
        step_memory_sync=lambda *a, **kw: {"success": True},
        step_requirement_decomposition=lambda *a, **kw: {"success": False, "error": "failed"},
        # ... other patches
    ):
        pipeline = PlanningPipeline(tmp_path)
        result = pipeline.run("test", auto_approve=False)

    output = capsys.readouterr().out
    assert "(R)etry" in output or "(C)ontinue" in output
```

#### Example 4: Fixture with Complex Mock Setup

**File:** `planning_pipeline/tests/test_pipeline.py:101-150`

```python
def test_calls_requirement_decomposition_after_memory_sync(self, tmp_path):
    """Pipeline should call step_requirement_decomposition after memory sync."""
    call_order = []

    def track_research(*args, **kwargs):
        call_order.append("research")
        return {"success": True, "research_path": "test/research.md", "output": ""}

    def track_memory_sync(*args, **kwargs):
        call_order.append("memory_sync")
        return {"success": True}

    def track_requirement_decomposition(*args, **kwargs):
        call_order.append("requirement_decomposition")
        return {
            "success": True,
            "hierarchy_path": str(tmp_path / "hierarchy.json"),
            "diagram_path": str(tmp_path / "diagram.mmd"),
            "tests_path": None,
            "requirement_count": 3,
            "output_dir": str(tmp_path),
        }

    with patch.multiple(
        "planning_pipeline.pipeline",
        step_research=track_research,
        step_memory_sync=track_memory_sync,
        step_requirement_decomposition=track_requirement_decomposition,
        step_planning=lambda *a, **kw: {"success": True, "plan_path": "p.md", "output": ""},
        step_phase_decomposition=lambda *a, **kw: {"success": True, "phases": [], "output": ""},
        step_beads_integration=lambda *a, **kw: {"success": True, "epic_id": None},
        interactive_checkpoint_research=lambda x: {"action": "continue", "modifications": {}},
        interactive_checkpoint_plan=lambda x: {"continue": True},
    ):
        pipeline = PlanningPipeline(tmp_path)
        result = pipeline.run("test prompt", auto_approve=True)

    assert result["success"] is True
    assert call_order.index("memory_sync") < call_order.index("requirement_decomposition")
```

---

### 9. 🏗️ Test Organization Patterns

#### Behavior-Driven Organization (BDD-style)

Tests are organized into classes grouping related behaviors:

**File:** `planning_pipeline/tests/test_beads.py:25-90`

```python
class TestBeadsController:
    """Tests for BeadsController CRUD operations."""

    def test_creates_task_issue(self, beads_controller, cleanup_issues):
        """Given valid title/type/priority, creates issue and returns success."""
        # Test implementation

    def test_lists_issues(self, beads_controller):
        """Given existing issues, returns list with expected fields."""
        # Test implementation

    def test_updates_issue(self, beads_controller, cleanup_issues):
        """Given valid issue_id and updates, modifies issue successfully."""
        # Test implementation
```

#### Given-When-Then Docstrings

Test docstrings follow Given-When-Then pattern:

```python
def test_retry_reruns_decomposition(self, tmp_path, monkeypatch):
    """Choosing (R)etry should re-run step_requirement_decomposition."""
    # Given: decomposition fails initially
    # When: user chooses retry
    # Then: decomposition runs again
```

---

### 10. 🛠️ Pytest Configuration

#### Custom Markers

**File:** `planning_pipeline/tests/conftest.py:8-19`

```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
```

**Usage:**
```python
@pytest.mark.slow
def test_large_decomposition(self):
    """Test with large input that takes time."""
    pass

@pytest.mark.integration
def test_full_pipeline_integration(self):
    """Test complete pipeline flow."""
    pass
```

---

## 📂 Code References

### Core Conftest Files

- [`planning_pipeline/tests/conftest.py`](planning_pipeline/tests/conftest.py) - Main fixture hub (348 lines)
  - Lines 8-19: Custom pytest markers
  - Lines 22-78: Mock BAML types
  - Lines 85-134: BAML mock fixtures
  - Lines 137-254: Claude SDK response mocks
  - Lines 257-301: Patch fixtures with side effects
  - Lines 303-347: Utility fixtures

- [`silmari_rlm_act/tests/conftest.py`](silmari_rlm_act/tests/conftest.py) - RLM Act fixtures (29 lines)
  - Lines 7-10: `sample_timestamp` fixture
  - Lines 13-19: `sample_artifacts` fixture
  - Lines 22-28: `sample_errors` fixture

### File-Specific Fixtures

- [`planning_pipeline/tests/test_pipeline.py:10-29`](planning_pipeline/tests/test_pipeline.py#L10-L29) - Project path, beads controller, cleanup fixtures
- [`planning_pipeline/tests/test_beads.py:8-22`](planning_pipeline/tests/test_beads.py#L8-L22) - Beads controller and cleanup fixtures
- [`planning_pipeline/tests/test_step_decomposition.py:24-87`](planning_pipeline/tests/test_step_decomposition.py#L24-L87) - Temp project and mock decomposition fixtures
- [`planning_pipeline/tests/test_checkpoint_manager.py:20-24`](planning_pipeline/tests/test_checkpoint_manager.py#L20-L24) - Temp project fixture

### Hypothesis Strategies

- [`planning_pipeline/tests/test_visualization.py:26-93`](planning_pipeline/tests/test_visualization.py#L26-L93) - Requirement ID, text, node, and hierarchy strategies
- [`planning_pipeline/tests/test_property_generator.py:18-24`](planning_pipeline/tests/test_property_generator.py#L18-L24) - Criterion with keyword strategy
- [`planning_pipeline/tests/test_models.py:32-115`](planning_pipeline/tests/test_models.py#L32-L115) - Multiple strategies for model testing
- [`planning_pipeline/tests/test_models.py:580-675`](planning_pipeline/tests/test_models.py#L580-L675) - Stateful testing machine

### Example Test Files

- [`planning_pipeline/tests/test_beads.py:28-39`](planning_pipeline/tests/test_beads.py#L28-L39) - Example of fixture usage in tests
- [`planning_pipeline/tests/test_pipeline.py:193-216`](planning_pipeline/tests/test_pipeline.py#L193-L216) - Monkeypatch and capsys usage
- [`tests/test_execute_phase.py:246-307`](tests/test_execute_phase.py#L246-L307) - Async test with fixtures

---

## 🏛️ Architecture Documentation

### Fixture Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Fixture Hierarchy                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Level 1: Built-in Fixtures                                 │
│  └─ tmp_path, monkeypatch, capsys, caplog                   │
│                                                              │
│  Level 2: Project Fixtures (conftest.py)                    │
│  ├─ project_path                                            │
│  ├─ Mock BAML types (dataclasses)                           │
│  ├─ mock_baml_initial_extraction                            │
│  ├─ mock_baml_subprocess_details                            │
│  ├─ mock_claude_sdk_response                                │
│  └─ sample_* fixtures                                       │
│                                                              │
│  Level 3: Composite Fixtures (depend on Level 2)            │
│  ├─ mock_baml_client (depends on BAML fixtures)             │
│  ├─ patch_baml_client (depends on mock responses)           │
│  └─ beads_controller (depends on project_path)              │
│                                                              │
│  Level 4: Application Fixtures (depend on Level 3)          │
│  ├─ cleanup_issues (depends on beads_controller)            │
│  ├─ temp_project (depends on tmp_path)                      │
│  └─ mock_decomposition_result (standalone)                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Test Execution Flow

```
Test Discovery
    ↓
Fixture Resolution (dependency graph)
    ↓
Setup Phase (fixture creation, yield before)
    ↓
Test Execution (test function runs)
    ↓
Teardown Phase (yield after, cleanup)
    ↓
Results & Reporting
```

### Mocking Strategy Layers

```
┌───────────────────────────────────────────────────────────┐
│  Layer 1: External Services                               │
│  ├─ BAML Client (LLM calls)                               │
│  ├─ Claude SDK (run_claude_sync)                          │
│  ├─ Beads Issue Tracker                                   │
│  ├─ CWA Integration                                       │
│  └─ Subprocess (git, shell commands)                      │
│                                                            │
│  Layer 2: Mock Fixtures (conftest.py)                     │
│  ├─ Mock objects with MagicMock                           │
│  ├─ Side effects for multi-call scenarios                 │
│  ├─ Return values with sample data                        │
│  └─ Override capabilities for test-specific behavior      │
│                                                            │
│  Layer 3: Test-Specific Patches                           │
│  ├─ @patch decorator                                      │
│  ├─ patch.multiple for multiple patches                   │
│  ├─ monkeypatch for input/attribute mocking               │
│  └─ Context managers (with patch(...))                    │
└───────────────────────────────────────────────────────────┘
```

### Property-Based Testing Architecture

```
Hypothesis Strategies
    ├─ @st.composite decorators
    ├─ Custom data generators
    └─ Constraint definitions
         ↓
@given decorator (applies strategies to test)
    ↓
Test execution with generated inputs
    ↓
Invariant checking (stateful testing)
    ↓
Shrinking on failure (minimal failing case)
```

---

## 📜 Historical Context (from thoughts/)

The codebase has **extensive prior research** on testing patterns:

### Recent Testing Documentation

1. **`thoughts/searchable/research/2026-01-14-pytest-fixtures-patterns-complete.md`**
   - Date: 2026-01-14 14:52:32
   - Comprehensive analysis with:
     - 46 test files, 25,070 lines of test code
     - 30+ custom pytest fixtures
     - 5 advanced fixture patterns
     - Fixture dependency graphs
     - Usage frequency statistics

2. **`thoughts/searchable/research/2026-01-14-pytest-fixtures-comprehensive-research.md`**
   - Date: 2026-01-14 14:22:45
   - Focus on:
     - 43 Python test files, ~19,400 lines
     - 62+ custom fixtures (14 shared, 48+ file-specific)
     - 6 primary fixture patterns
     - Behavior-driven organization
     - Hypothesis integration

3. **`thoughts/searchable/research/2026-01-14-pytest-fixtures-detailed-analysis.md`**
   - Date: 2026-01-14 13:18:22
   - Fixture-by-fixture detailed analysis
   - conftest.py structure documentation
   - Mock BAML types breakdown
   - Cleanup patterns (4 instances)

4. **`thoughts/searchable/research/2026-01-14-pytest-fixtures.md`**
   - Date: 2026-01-14 13:41:12
   - Statistics:
     - 42 test files, 7,989+ test functions
     - 100% function-scoped fixtures
     - Zero autouse fixtures
     - Explicit dependency injection pattern

### Earlier Testing Documentation

5. **`thoughts/searchable/research/2026-01-06-pytest-fixtures-patterns.md`**
   - Early fixture pattern analysis
   - BDD-style organization documentation

6. **`thoughts/searchable/shared/research/2026-01-02-pytest-fixtures-testing-patterns.md`**
   - Initial testing patterns with Hypothesis documentation

### Planning Documents

7. **`thoughts/searchable/shared/plans/2026-01-10-tdd-feature/13-the-implementation-phase-must-run-tests-using-pyte.md`**
   - Specifications for running tests using pytest
   - Test command: `pytest -v --tb=short`
   - Fallback: `make test`
   - 300-second timeout configuration
   - Test failure handling logic

---

## 🔍 Key Architectural Decisions

### 1. **Function-Scoped Fixtures Only**

All fixtures use default function scope (no session/module/class scope). This ensures:
- ✅ Complete test isolation
- ✅ No state leakage between tests
- ✅ Parallel test execution safety
- ⚠️ Trade-off: Slightly slower test execution

### 2. **No Autouse Fixtures**

Zero autouse fixtures means:
- ✅ Explicit dependencies in test signatures
- ✅ Clear fixture usage (no hidden setup)
- ✅ Better test readability

### 3. **Centralized vs Distributed Fixtures**

| Location | Purpose | Complexity |
|----------|---------|-----------|
| `conftest.py` | Shared across all tests in directory | Complex (BAML, Claude mocks) |
| Test files | Specific to test module | Simple (temp paths, sample data) |

### 4. **Mock-Heavy vs Integration Testing**

- **Unit tests**: Heavy mocking (BAML, Claude SDK, Beads)
- **Integration tests**: Minimal mocking, marked with `@pytest.mark.integration`
- **E2E tests**: Full pipeline execution, marked with `@pytest.mark.e2e`

### 5. **Hypothesis Integration Strategy**

- Custom `@st.composite` strategies for domain objects
- Stateful testing with `RuleBasedStateMachine` for invariants
- Property-based testing for validation logic

### 6. **Cleanup Pattern**

Fixtures that create external resources (Beads issues, git repos) use:
```python
@pytest.fixture
def cleanup_resource():
    resources = []
    yield resources  # Test runs
    # Cleanup code after test
    for resource in resources:
        cleanup(resource)
```

---

## 🔗 Related Research

- `thoughts/searchable/research/2026-01-14-pytest-fixtures-patterns-complete.md` - Most recent comprehensive analysis
- `thoughts/searchable/research/2026-01-06-pytest-fixtures-patterns.md` - Earlier fixture patterns
- `thoughts/searchable/shared/plans/2026-01-10-tdd-feature/13-the-implementation-phase-must-run-tests-using-pyte.md` - Test execution specs

---

## ❓ Open Questions

1. **Fixture Scope Optimization**: Could some fixtures (e.g., `project_path`) use module/session scope for performance?
2. **Conftest Organization**: Should `context_window_array/tests/` have its own conftest.py?
3. **Go Test Integration**: How do Go tests and Python tests share fixtures/utilities?
4. **Async Testing**: Are there patterns for async fixtures beyond pytest-asyncio?
5. **Fixture Discovery**: How are test-specific fixtures discovered vs conftest fixtures?

---

## 📊 Statistics Summary

<table>
<tr>
<th>Metric</th>
<th>Count</th>
<th>Details</th>
</tr>
<tr>
<td><b>Python Test Files</b></td>
<td>46</td>
<td>~1 MB of test code</td>
</tr>
<tr>
<td><b>Go Test Files</b></td>
<td>26</td>
<td>Colocated with source</td>
</tr>
<tr>
<td><b>Conftest Files</b></td>
<td>2</td>
<td>planning_pipeline (348 lines), silmari_rlm_act (29 lines)</td>
</tr>
<tr>
<td><b>Shared Fixtures</b></td>
<td>30+</td>
<td>Defined in conftest.py files</td>
</tr>
<tr>
<td><b>File-Specific Fixtures</b></td>
<td>48+</td>
<td>Defined within test files</td>
</tr>
<tr>
<td><b>Hypothesis Strategies</b></td>
<td>9+</td>
<td>Custom @st.composite strategies</td>
</tr>
<tr>
<td><b>Custom Markers</b></td>
<td>3</td>
<td>@slow, @integration, @e2e</td>
</tr>
<tr>
<td><b>Mock Types</b></td>
<td>6</td>
<td>Custom dataclasses for BAML</td>
</tr>
<tr>
<td><b>Fixture Patterns</b></td>
<td>6</td>
<td>Value, temp, mock, cleanup, patch, factory</td>
</tr>
</table>

---

```
╔═══════════════════════════════════════════════════════════════╗
║                       END OF RESEARCH                         ║
║                                                               ║
║  This document represents the current state of testing       ║
║  patterns and pytest fixtures as they exist in the codebase. ║
╚═══════════════════════════════════════════════════════════════╝
```
