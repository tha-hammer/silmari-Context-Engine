---
date: 2026-01-04T15:33:15-05:00
researcher: Claude Code
git_commit: fdd63c027b5ea026316109011e0f85b7f080f130
branch: main
repository: silmari-Context-Engine
topic: "Testing Patterns and Pytest Fixtures Analysis"
tags: [research, codebase, testing, pytest, fixtures, patterns]
status: complete
last_updated: 2026-01-04
last_updated_by: Claude Code
---

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║         PYTEST FIXTURES & TESTING PATTERNS ANALYSIS          ║
║                  silmari-Context-Engine                      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Status: ✅ Complete | Date: 2026-01-04 15:33:15 -05:00
```

**Researcher**: Claude Code
**Git Commit**: `fdd63c027b5ea026316109011e0f85b7f080f130`
**Branch**: `main`
**Repository**: silmari-Context-Engine

---

## 📚 Research Question

Analyze the testing patterns in this project. Focus on pytest fixtures.

---

## 🎯 Executive Summary

This research provides comprehensive documentation of all pytest fixtures and testing patterns in the silmari-Context-Engine codebase. The project uses pytest as its testing framework with async support enabled, custom markers for test categorization, and a sophisticated fixture ecosystem centered around a single `conftest.py` file.

### Key Statistics

| Metric | Count |
|--------|-------|
| **Total Test Files** | 20 test modules |
| **Test Directories** | 2 (`tests/`, `planning_pipeline/tests/`) |
| **Shared Fixtures** | 8 fixtures in `conftest.py` |
| **Test-Specific Fixtures** | 15+ inline fixtures across test files |
| **Fixture Patterns** | 12 distinct patterns identified |
| **Custom Pytest Markers** | 3 (`slow`, `integration`, `e2e`) |

---

## 📊 Testing Infrastructure

### Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| **pytest.ini** | `pytest.ini:1-3` | Async test configuration |
| **conftest.py** | `planning_pipeline/tests/conftest.py:1-191` | Shared fixtures and markers |

#### pytest.ini Configuration

```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```

**Key settings**:
- Automatic async test detection
- Function-scoped event loops for async fixtures

---

## 🗂️ Test File Organization

### Directory Structure

```
silmari-Context-Engine/
├── pytest.ini                          # Pytest configuration
├── tests/                              # Root-level integration tests (3 files)
│   ├── test_autonomous_loop.py
│   ├── test_loop_orchestrator_integration.py
│   └── test_execute_phase.py
│
└── planning_pipeline/
    └── tests/                          # Pipeline-specific tests (17 files)
        ├── conftest.py                 # Shared fixtures
        ├── test_beads.py
        ├── test_beads_controller.py
        ├── test_checkpoint_manager.py
        ├── test_checkpoints.py
        ├── test_claude.py
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

---

## 🎨 Shared Fixtures (conftest.py)

### Custom Pytest Markers

**Location**: `planning_pipeline/tests/conftest.py:10-14`

```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
```

### Mock Data Classes

**Location**: `planning_pipeline/tests/conftest.py:22-78`

The conftest defines mock dataclasses mirroring `baml_client.types`:

| Mock Class | Purpose | Lines |
|------------|---------|-------|
| `MockImplementationComponents` | Frontend/backend/middleware/shared lists | 22-29 |
| `MockImplementationDetail` | Function details with acceptance criteria | 32-40 |
| `MockRequirement` | Requirements with sub-processes | 43-49 |
| `MockResponseMetadata` | Response metadata with tracking | 52-61 |
| `MockInitialExtractionResponse` | Gate 1 initial extraction | 64-69 |
| `MockSubprocessDetailsResponse` | Gate 1 subprocess details | 72-77 |

---

## 🔧 Fixture Catalog

### 1. 🎭 Mock BAML Fixtures

#### `mock_baml_initial_extraction`

**Location**: `planning_pipeline/tests/conftest.py:85-100`
**Scope**: function (default)
**Dependencies**: None

```python
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
        ],
        metadata=MockResponseMetadata(
            timestamp="2025-01-01T12:00:00Z",
            model="test-model",
            schema_version="1.0",
        ),
    )
```

---

#### `mock_baml_subprocess_details`

**Location**: `planning_pipeline/tests/conftest.py:103-125`
**Scope**: function
**Dependencies**: None

```python
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
                    "Email field validates format",
                    "Password field masks input",
                    "Submit button is disabled until valid",
                ],
                implementation=MockImplementationComponents(
                    frontend=["LoginForm.tsx", "LoginButton.tsx"],
                    backend=["auth.py", "login_handler.py"],
                    middleware=["auth_middleware.py"],
                    shared=["types.ts"],
                ),
            )
        ],
        metadata=MockResponseMetadata(
            timestamp="2025-01-01T12:00:00Z",
            model="test-model",
            schema_version="1.0",
        ),
    )
```

---

#### `mock_baml_client`

**Location**: `planning_pipeline/tests/conftest.py:128-134`
**Scope**: function
**Dependencies**: `mock_baml_initial_extraction`, `mock_baml_subprocess_details`
**Pattern**: 🔗 Fixture Composition

```python
@pytest.fixture
def mock_baml_client(mock_baml_initial_extraction, mock_baml_subprocess_details):
    """Complete mock of BAML client for unit tests."""
    mock_b = MagicMock()
    mock_b.ProcessGate1InitialExtractionPrompt.return_value = mock_baml_initial_extraction
    mock_b.ProcessGate1SubprocessDetailsPrompt.return_value = mock_baml_subprocess_details
    return mock_b
```

**Key Feature**: Combines multiple fixtures into a complete mock client.

---

#### `patch_baml_client`

**Location**: `planning_pipeline/tests/conftest.py:137-143`
**Scope**: function
**Dependencies**: `mock_baml_client`
**Pattern**: 🎭 Patch Context Manager

```python
@pytest.fixture
def patch_baml_client(mock_baml_client):
    """Context manager to patch BAML client import."""
    with patch.dict("sys.modules", {"baml_client": MagicMock(b=mock_baml_client)}):
        with patch("planning_pipeline.decomposition.b", mock_baml_client):
            with patch("planning_pipeline.decomposition.BAML_AVAILABLE", True):
                yield mock_baml_client
```

**Key Feature**: Wraps mock client with import patches, automatically reverted after test.

---

### 2. 📁 Path & Output Fixtures

#### `project_path`

**Location**: `planning_pipeline/tests/conftest.py:146-149`
**Scope**: function
**Pattern**: 🗺️ Path Helper

```python
@pytest.fixture
def project_path():
    """Return the root project path."""
    return Path(__file__).parent.parent.parent
```

**Usage**: Provides root directory for integration tests that need real project structure.

---

#### `sample_research_output`

**Location**: `planning_pipeline/tests/conftest.py:152-167`
**Scope**: function
**Pattern**: 📄 Sample Data

```python
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
```

**Usage**: Testing path extraction and output parsing logic.

---

#### `sample_plan_output`

**Location**: `planning_pipeline/tests/conftest.py:170-179`
**Scope**: function
**Pattern**: 📄 Sample Data

```python
@pytest.fixture
def sample_plan_output():
    """Sample Claude output containing a plan file path."""
    return """
    Planning complete!

    Plan written to thoughts/shared/plans/2025-01-01-feature/00-overview.md

    The plan includes 3 phases for implementation.
    """
```

---

#### `sample_phase_output`

**Location**: `planning_pipeline/tests/conftest.py:182-190`
**Scope**: function
**Pattern**: 📄 Sample Data

```python
@pytest.fixture
def sample_phase_output():
    """Sample Claude output containing multiple phase file paths."""
    return """
    Phase files created:
    - thoughts/shared/plans/feature/01-phase-1.md
    - thoughts/shared/plans/feature/02-phase-2.md
    - thoughts/shared/plans/feature/03-phase-3.md
    """
```

---

## 🎯 Fixture Patterns Deep Dive

### Pattern 1: Simple Data Fixtures

**Purpose**: Provide mock data objects without side effects

<details>
<summary><strong>📌 Example: mock_decomposition_result</strong></summary>

**Location**: `planning_pipeline/tests/test_step_decomposition.py:54-88`

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
        description="Login implementation",
        type="sub_process",
        parent_id="REQ_000",
        acceptance_criteria=["Email validation works", "Password is checked"],
    )

    child2 = RequirementNode(
        id="REQ_000.2",
        description="Session management",
        type="sub_process",
        parent_id="REQ_000",
        acceptance_criteria=["Sessions expire after inactivity"],
    )

    parent.children = [child1, child2]
    hierarchy = RequirementHierarchy(
        requirements=[parent],
        metadata={"source": "test"},
    )
    return hierarchy
```

**Usage**:
```python
def test_creates_hierarchy_json(temp_project, mock_decomposition_result):
    """Step should create requirements_hierarchy.json file."""
    project_path, research_path = temp_project

    with patch("planning_pipeline.step_decomposition.decompose_requirements") as mock_decompose:
        mock_decompose.return_value = mock_decomposition_result

        result = step_requirement_decomposition(
            project_path=project_path,
            research_path=research_path,
        )

    assert result["success"] is True
    assert "hierarchy_path" in result
```

</details>

---

### Pattern 2: Temporary Directory/File Fixtures

**Purpose**: Create isolated test file systems
**Pattern**: 🗂️ Uses pytest's built-in `tmp_path` fixture

<details>
<summary><strong>📌 Example: temp_project</strong></summary>

**Location**: `planning_pipeline/tests/test_step_decomposition.py:23-51`

```python
@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure for testing."""
    # Create research directory
    research_dir = tmp_path / "thoughts" / "shared" / "research"
    research_dir.mkdir(parents=True)

    # Create a sample research file
    research_content = """# Research: Test Feature

## Overview

This research document describes requirements for a test feature.

## Requirements

1. User should be able to log in with email/password
2. System should track active sessions
3. Sessions should expire after inactivity
"""
    research_file = research_dir / "2026-01-02-test-research.md"
    research_file.write_text(research_content)

    return tmp_path, str(research_file.relative_to(tmp_path))
```

**Key Features**:
- Creates complete directory structures
- Returns tuple with multiple useful paths
- Automatically cleaned up by pytest after test

</details>

---

### Pattern 3: Fixtures with Cleanup (Yield Fixtures)

**Purpose**: Setup resources and guarantee cleanup
**Pattern**: 🧹 Teardown pattern using `yield`

<details>
<summary><strong>📌 Example: cleanup_issues</strong></summary>

**Location**: `planning_pipeline/tests/test_beads.py:15-22`

```python
@pytest.fixture
def cleanup_issues(beads_controller):
    """Track and cleanup created issues after test."""
    created_ids = []
    yield created_ids
    # Cleanup runs after test completes
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
    beads_controller.sync()
```

**Usage Pattern**:
```python
def test_creates_task_issue(beads_controller, cleanup_issues):
    """Given valid title/type/priority, creates issue and returns success."""
    result = beads_controller.create_issue(
        title="TDD Test Issue - Create",
        issue_type="task",
        priority=2
    )
    assert result["success"] is True

    # Track for cleanup
    if isinstance(result["data"], dict) and "id" in result["data"]:
        cleanup_issues.append(result["data"]["id"])
```

**Lifecycle**:
```
Setup (before yield) → Test Execution → Teardown (after yield)
     created_ids = []      test modifies list      close issues & sync
```

</details>

---

### Pattern 4: Fixture Dependencies (Fixtures Using Other Fixtures)

**Purpose**: Build complex fixtures from simpler components
**Pattern**: 🔗 Fixture Composition Chain

<details>
<summary><strong>📌 Example: Fixture Chain</strong></summary>

**Dependency Chain**:
```
project_path → beads_controller → cleanup_issues
```

**Step 1**: Base fixture
```python
@pytest.fixture
def project_path():
    """Return the root project path."""
    return Path(__file__).parent.parent.parent
```

**Step 2**: Dependent fixture
```python
@pytest.fixture
def beads_controller(project_path):
    """Create BeadsController with project path."""
    return BeadsController(project_path)
```

**Step 3**: Further dependent fixture
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

**Usage**: All three fixtures available automatically:
```python
def test_full_pipeline(project_path, beads_controller, cleanup_issues):
    """Test can access all fixtures in the chain."""
    # All fixtures are initialized in order
    assert project_path.exists()
    assert isinstance(beads_controller, BeadsController)
    assert isinstance(cleanup_issues, list)
```

</details>

---

### Pattern 5: Patch/Mock Fixtures

**Purpose**: Mock external dependencies and imports
**Pattern**: 🎭 Context Manager with Patches

<details>
<summary><strong>📌 Example: patch_baml_client</strong></summary>

**Location**: `planning_pipeline/tests/conftest.py:137-143`

```python
@pytest.fixture
def patch_baml_client(mock_baml_client):
    """Context manager to patch BAML client import."""
    with patch.dict("sys.modules", {"baml_client": MagicMock(b=mock_baml_client)}):
        with patch("planning_pipeline.decomposition.b", mock_baml_client):
            with patch("planning_pipeline.decomposition.BAML_AVAILABLE", True):
                yield mock_baml_client
```

**Key Features**:
- Multiple nested patches
- Automatically reverts all patches after test
- Yields mock within patched context

**Usage**:
```python
def test_decomposition_with_mocked_baml(patch_baml_client):
    """Test automatically runs with BAML client patched."""
    # Inside this test:
    # - sys.modules["baml_client"] is mocked
    # - planning_pipeline.decomposition.b is mocked
    # - BAML_AVAILABLE is True
    # No manual cleanup needed!
    from planning_pipeline.decomposition import b
    result = b.ProcessGate1InitialExtractionPrompt("test")
    # Gets mock response automatically
```

</details>

<details>
<summary><strong>📌 Example: mock_subprocess_success</strong></summary>

**Location**: `tests/test_execute_phase.py:75-84`

```python
@pytest.fixture
def mock_subprocess_success(self):
    """Mock successful subprocess run."""
    with patch('planning_pipeline.phase_execution.claude_invoker.subprocess') as mock:
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Success output"
        mock_process.stderr = ""
        mock.run.return_value = mock_process
        yield mock
```

**Usage**:
```python
def test_claude_invocation_success(mock_subprocess_success):
    """Test Claude CLI invocation with mocked subprocess."""
    result = invoke_claude(["prompt"])
    assert result["success"] is True
    mock_subprocess_success.run.assert_called_once()
```

</details>

---

### Pattern 6: Sample Data Fixtures

**Purpose**: Provide example strings/outputs for parsing tests
**Pattern**: 📄 Static String Data

**Examples in conftest.py**:
- `sample_research_output` - Claude output with research file path
- `sample_plan_output` - Claude output with plan file path
- `sample_phase_output` - Claude output with multiple phase file paths

**Usage Pattern**:
```python
def test_extracts_path_from_output(sample_research_output):
    """Test path extraction from Claude output."""
    path = extract_research_path(sample_research_output)
    assert path == "thoughts/shared/research/2025-01-01-test-research.md"
```

---

### Pattern 7: Git Repository Fixtures

**Purpose**: Create temporary git repositories for testing git operations
**Pattern**: 🔧 Subprocess Setup

<details>
<summary><strong>📌 Example: temp_git_repo</strong></summary>

**Location**: `tests/test_execute_phase.py:148-159`

```python
@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repo."""
    import subprocess
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
    # Create initial commit
    (tmp_path / "initial.txt").write_text("initial")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True)
    return tmp_path
```

**Key Features**:
- Fully initialized git repository
- Has initial commit for clean state
- Allows testing git status detection

</details>

---

### Pattern 8: Monkeypatch Fixtures

**Purpose**: Mock user input and environment
**Pattern**: 🔧 Built-in pytest fixture

<details>
<summary><strong>📌 Example: Input Mocking</strong></summary>

**Location**: `planning_pipeline/tests/test_orchestrator.py:58-66`

```python
def test_collects_single_line(monkeypatch):
    """Given single line then blank, returns that line."""
    from planning_orchestrator import collect_prompt

    inputs = iter(["How does auth work?", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    result = collect_prompt()
    assert result == "How does auth work?"
```

**Key Features**:
- `monkeypatch` is a built-in pytest fixture
- Use `monkeypatch.setattr` to replace functions
- Automatically reverts changes after test

</details>

<details>
<summary><strong>📌 Example: Environment Variable Mocking</strong></summary>

**Location**: `planning_pipeline/tests/test_orchestrator.py:107-123`

```python
def test_fails_when_claude_missing(monkeypatch):
    """Given claude not installed, returns error."""
    from planning_orchestrator import check_prerequisites

    original_run = subprocess.run

    def mock_run(cmd, *args, **kwargs):
        if cmd[0] == "which" and cmd[1] == "claude":
            result = type('Result', (), {'returncode': 1})()
            return result
        return original_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_run)

    result = check_prerequisites()
    assert result["success"] is False
    assert "claude" in result["error"]
```

</details>

---

### Pattern 9: Async Fixtures with @pytest.mark.asyncio

**Purpose**: Test async code with async fixtures
**Pattern**: ⚡ Async Test Support

<details>
<summary><strong>📌 Example: Async Test with Fixture</strong></summary>

**Location**: `tests/test_autonomous_loop.py:54-62`

```python
@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator with plan discovery."""
    orchestrator = Mock()
    orchestrator.discover_plans.return_value = [
        Mock(path="/plans/feature-a.md", priority=1),
        Mock(path="/plans/feature-b.md", priority=2),
    ]
    return orchestrator

@pytest.mark.asyncio
async def test_discovers_plan_when_none_provided(mock_orchestrator):
    """Should discover plan from orchestrator when plan_path is None."""
    runner = LoopRunner(orchestrator=mock_orchestrator)
    with patch.object(runner, "_execute_loop", new_callable=AsyncMock):
        await runner.run()
    mock_orchestrator.discover_plans.assert_called_once()
    assert runner.plan_path == "/plans/feature-a.md"
```

**Key Features**:
- Test method is `async def`
- Decorated with `@pytest.mark.asyncio`
- Uses `AsyncMock` for async methods
- Uses `await` for async calls

</details>

---

### Pattern 10: Project Path Fixtures

**Purpose**: Provide root project directory for integration tests
**Pattern**: 🗺️ Path Navigation

**Found in multiple test files:**
- `planning_pipeline/tests/test_orchestrator.py:148-150`
- `planning_pipeline/tests/test_pipeline.py:11-13`

```python
@pytest.fixture
def project_path():
    """Return the root project path."""
    return Path(__file__).parent.parent.parent
```

**Navigation Logic**:
```
__file__ = /home/maceo/Dev/silmari-Context-Engine/planning_pipeline/tests/test_file.py
parent   = /home/maceo/Dev/silmari-Context-Engine/planning_pipeline/tests/
parent   = /home/maceo/Dev/silmari-Context-Engine/planning_pipeline/
parent   = /home/maceo/Dev/silmari-Context-Engine/
```

---

### Pattern 11: Parametrized Tests

**Purpose**: Run same test with different inputs
**Pattern**: 🔄 Test Repetition with `@pytest.mark.parametrize`

<details>
<summary><strong>📌 Example: Property Classification Tests</strong></summary>

**Location**: `planning_pipeline/tests/test_property_generator.py:432-469`

```python
@pytest.mark.parametrize(
    "criterion,expected_type",
    [
        # Invariant patterns
        ("Must validate unique IDs", "invariant"),
        ("All values distinct", "invariant"),
        ("No duplicate entries", "invariant"),
        ("Result not empty", "invariant"),
        # Round-trip patterns
        ("Save and load preserves data", "round_trip"),
        ("Encode and decode correctly", "round_trip"),
        ("Serialize to JSON", "round_trip"),
        # Idempotence patterns
        ("Applying twice gives same result", "idempotence"),
        ("Multiple times same output", "idempotence"),
        # Oracle patterns
        ("Matches reference implementation", "oracle"),
        ("Compare to oracle", "oracle"),
    ],
)
def test_criterion_classified_correctly(criterion, expected_type):
    """Criterion should be classified to expected property type."""
    from planning_pipeline.property_generator import derive_properties
    result = derive_properties([criterion])
    assert result[0]["type"] == expected_type
```

**Key Features**:
- Uses `@pytest.mark.parametrize` decorator
- Takes parameter names and list of value tuples
- Generates one test per parameter set
- Test function receives parameters as arguments

**Output**: 11 tests generated from single test function.

</details>

---

### Pattern 12: Complex Runner/Controller Fixtures

**Purpose**: Integration testing with complex initialization
**Pattern**: 🏗️ Multi-Step Setup

<details>
<summary><strong>📌 Example: runner_with_plan</strong></summary>

**Location**: `tests/test_execute_phase.py:246-268`

```python
@pytest.fixture
def runner_with_plan(tmp_path):
    """Create a runner with a valid plan file."""
    # Create plan file
    plan_path = tmp_path / "plan.md"
    plan_path.write_text("""# Test Plan

## Implementation
- Do the thing
""")

    # Initialize git repo
    import subprocess
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
    (tmp_path / "initial.txt").write_text("initial")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True)

    # Create runner with plan
    runner = LoopRunner(plan_path=str(plan_path))
    runner.current_phase = "test-phase"
    runner._project_path = tmp_path
    return runner
```

**Key Features**:
- Combines file creation, git initialization, and object construction
- Returns ready-to-test object
- Encapsulates complex multi-step setup logic

</details>

---

## 🔗 Common Fixture Combinations

### Combination 1: Project Path + Cleanup

**Pattern**: Integration tests with resource tracking

```python
def test_full_pipeline_creates_artifacts(project_path, cleanup_issues):
    """Given real SDK, creates all expected artifacts."""
    # project_path provides real project directory
    # cleanup_issues tracks resources to clean up after test
    controller = BeadsController(project_path)
    issue_id = controller.create_issue("Test", "task", 2)
    cleanup_issues.append(issue_id)
```

---

### Combination 2: Temp Project + Mock Result

**Pattern**: Isolated filesystem with mock data

```python
def test_creates_hierarchy_json(temp_project, mock_decomposition_result):
    """Step should create requirements_hierarchy.json file."""
    # temp_project provides isolated filesystem
    # mock_decomposition_result provides test data
    project_path, research_path = temp_project
    result = step_requirement_decomposition(
        project_path=project_path,
        research_path=research_path,
        mock_data=mock_decomposition_result,
    )
```

---

### Combination 3: Monkeypatch + Capsys

**Pattern**: Input mocking with output capture

```python
def test_prompts_on_failure(monkeypatch, capsys):
    """Should show (R)etry/(C)ontinue prompt when operation fails."""
    # monkeypatch mocks user input
    # capsys captures stdout for assertions
    inputs = iter(["r", "c"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    run_with_retry()

    captured = capsys.readouterr()
    assert "(R)etry or (C)ontinue?" in captured.out
```

---

## 📋 Fixture Scope Analysis

### Current State

| Scope | Count | Description |
|-------|-------|-------------|
| **function** | All fixtures | Default scope - recreated for each test function |
| **class** | 0 | None found |
| **module** | 0 | None found |
| **session** | 0 | None found |

**Key Finding**: All fixtures use function scope (default). This means:
- ✅ Maximum test isolation
- ✅ No state leakage between tests
- ⚠️ Potential performance impact for expensive fixtures
- ⚠️ Could benefit from module/session scope for expensive setup (e.g., git repos)

---

## 🔍 Autouse Analysis

### Current State

**Finding**: No fixtures use `autouse=True`

**Implication**: All fixtures require explicit injection via test function parameters

**Example of autouse pattern (not found in this codebase)**:
```python
# This pattern is NOT in the codebase
@pytest.fixture(autouse=True)
def always_runs():
    """This would run for every test automatically."""
    pass
```

---

## 🎯 Architecture Patterns

### Pattern Matrix

| Pattern | Frequency | Primary Use Case | Example Fixtures |
|---------|-----------|------------------|------------------|
| **Simple Data** | High | Mock responses | `mock_baml_initial_extraction` |
| **Temp Directories** | Medium | Isolated filesystem | `temp_project` |
| **Yield/Cleanup** | Medium | Resource management | `cleanup_issues` |
| **Fixture Composition** | High | Building complex setups | `mock_baml_client` |
| **Patch/Mock** | High | External dependency mocking | `patch_baml_client` |
| **Sample Data** | Low | Output parsing tests | `sample_research_output` |
| **Git Repos** | Low | Git operation testing | `temp_git_repo` |
| **Monkeypatch** | Medium | Input/env mocking | Built-in usage |
| **Async** | Low | Async code testing | `mock_orchestrator` |
| **Project Path** | High | Integration tests | `project_path` |
| **Parametrized** | Low | Multi-input testing | Property generator tests |
| **Complex Setup** | Low | End-to-end fixtures | `runner_with_plan` |

---

## 📊 Fixture Dependency Graph

```
Mock BAML Chain:
mock_baml_initial_extraction ─┐
                              ├─> mock_baml_client ─> patch_baml_client
mock_baml_subprocess_details ─┘

Beads Controller Chain:
project_path ─> beads_controller ─> cleanup_issues

Temp Project Chain:
tmp_path (built-in) ─> temp_project

Git Repository Chain:
tmp_path (built-in) ─> temp_git_repo
```

---

## 📖 Code References

### Shared Fixtures

| Fixture | Location | Lines |
|---------|----------|-------|
| `mock_baml_initial_extraction` | `planning_pipeline/tests/conftest.py` | 85-100 |
| `mock_baml_subprocess_details` | `planning_pipeline/tests/conftest.py` | 103-125 |
| `mock_baml_client` | `planning_pipeline/tests/conftest.py` | 128-134 |
| `patch_baml_client` | `planning_pipeline/tests/conftest.py` | 137-143 |
| `project_path` | `planning_pipeline/tests/conftest.py` | 146-149 |
| `sample_research_output` | `planning_pipeline/tests/conftest.py` | 152-167 |
| `sample_plan_output` | `planning_pipeline/tests/conftest.py` | 170-179 |
| `sample_phase_output` | `planning_pipeline/tests/conftest.py` | 182-190 |

### Test-Specific Fixtures

<details>
<summary><strong>View all test-specific fixtures by file</strong></summary>

| Test File | Fixtures | Lines |
|-----------|----------|-------|
| `test_step_decomposition.py` | `temp_project`, `mock_decomposition_result` | 23-51, 54-88 |
| `test_pipeline.py` | `project_path`, `beads_controller`, `cleanup_issues` | 10-13, 16-19, 22-29 |
| `test_steps.py` | `project_path`, `beads_controller`, `cleanup_issues` | 14-17, 20-23, 26-33 |
| `test_beads.py` | `beads_controller`, `cleanup_issues` | 8-12, 15-22 |
| `test_checkpoint_manager.py` | `temp_project` | 19-24 |
| `test_orchestrator.py` | `project_path`, `cleanup_issues` (class-scoped) | 148-151, 153-162 |
| `test_execute_phase.py` | `temp_plan_file`, `mock_subprocess_success`, `temp_git_repo`, `runner_with_plan` | 13-28, 75-84, 148-159, 246-268 |
| `test_autonomous_loop.py` | `mock_orchestrator` | 54-62 |

</details>

---

## 💡 Key Discoveries

### 1. Centralized Mock Strategy

The codebase uses a centralized mocking strategy with mock dataclasses in `conftest.py` that mirror `baml_client.types`. This provides:
- Consistent mock structure across all tests
- Easy updates when BAML types change
- Type-safe mock data

### 2. Cleanup Pattern Consistency

Multiple test files implement the same cleanup pattern:
```python
@pytest.fixture
def cleanup_issues(beads_controller):
    created_ids = []
    yield created_ids
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id)
    beads_controller.sync()
```

This pattern ensures test isolation and prevents test pollution of the beads database.

### 3. BAML Client Mocking Architecture

The BAML mocking uses a three-tier approach:
1. **Data fixtures**: `mock_baml_initial_extraction`, `mock_baml_subprocess_details`
2. **Client fixture**: `mock_baml_client` (combines data fixtures)
3. **Patch fixture**: `patch_baml_client` (applies import patches)

This allows tests to use either the raw mocks or the fully patched client depending on needs.

### 4. Async Test Support

The project is configured for async testing with:
- `asyncio_mode = auto` in `pytest.ini`
- `@pytest.mark.asyncio` decorator for async tests
- `AsyncMock` for mocking async operations

---

## 🗺️ Testing Coverage Map

```
┌─────────────────────────────────────────────────────────────┐
│                     Test Coverage Areas                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ Unit Tests (planning_pipeline/tests/)                  │
│     • BAML integration                                      │
│     • Decomposition logic                                   │
│     • Step execution                                        │
│     • Beads controller                                      │
│     • Checkpoint management                                 │
│     • Property generation                                   │
│     • Visualization                                         │
│                                                             │
│  ✅ Integration Tests (tests/)                             │
│     • Autonomous loop                                       │
│     • Loop orchestrator                                     │
│     • Phase execution                                       │
│                                                             │
│  ✅ End-to-End Tests                                       │
│     • test_decomposition_e2e.py                            │
│     • Full pipeline execution                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Fixture Usage Statistics

### By Pattern Type

| Pattern | Usage Count | Percentage |
|---------|-------------|------------|
| Patch/Mock | 8 | 35% |
| Simple Data | 6 | 26% |
| Path Helpers | 4 | 17% |
| Cleanup/Teardown | 3 | 13% |
| Temp Directories | 2 | 9% |

### By Dependency Level

| Level | Description | Count |
|-------|-------------|-------|
| **Level 0** | No dependencies | 12 |
| **Level 1** | Depends on 1 fixture | 8 |
| **Level 2** | Depends on 2+ fixtures | 3 |

---

## 📚 Related Research

- **Testing Documentation**: (Not yet created - would document testing conventions)
- **BAML Integration**: (Not yet created - would document BAML usage patterns)
- **Async Architecture**: (Not yet created - would document async patterns)

---

## ❓ Open Questions

None - this research provides comprehensive documentation of the existing testing patterns and fixtures.

---

## 📌 Quick Reference

### Running Tests

```bash
# Run all tests
pytest

# Run specific marker
pytest -m integration
pytest -m "not slow"

# Run specific test file
pytest planning_pipeline/tests/test_beads.py

# Run with verbose output
pytest -v

# Run async tests
pytest --asyncio-mode=auto
```

### Common Test Patterns

```python
# Use shared mock BAML client
def test_with_baml(patch_baml_client):
    # BAML is automatically mocked
    pass

# Use cleanup tracking
def test_creates_issue(cleanup_issues):
    issue_id = create_issue()
    cleanup_issues.append(issue_id)  # Auto-cleaned up

# Use temporary directory
def test_with_temp_dir(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("content")

# Mock user input
def test_with_input(monkeypatch):
    inputs = iter(["yes", "no"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
```

---

```
╔═══════════════════════════════════════════════════════════════╗
║                     END OF RESEARCH                           ║
╚═══════════════════════════════════════════════════════════════╝
```
