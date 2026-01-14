---
date: 2026-01-14T14:52:32-05:00
researcher: Maceo Finkenwirth
git_commit: bc8bc90f3f2888a21597c6e4739250e41548ef78
branch: main
repository: silmari-Context-Engine
topic: "Pytest Fixtures and Testing Patterns Analysis"
tags: [research, testing, pytest, fixtures, test-organization]
status: complete
last_updated: 2026-01-14
last_updated_by: Maceo Finkenwirth
---

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║         PYTEST FIXTURES & TESTING PATTERNS ANALYSIS           ║
║              silmari-Context-Engine Project                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

**Date**: 2026-01-14T14:52:32-05:00
**Researcher**: Maceo Finkenwirth
**Git Commit**: `bc8bc90f3f2888a21597c6e4739250e41548ef78`
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📋 Research Question

Analyze the testing patterns in this project with a focus on pytest fixtures.

---

## 🎯 Summary

The silmari-Context-Engine project has a comprehensive test suite with **46 test files** totaling **25,070 lines of test code** organized across 4 test directories. The project uses **30+ custom pytest fixtures** following distinct patterns:

- **Fixture Organization**: 2 conftest.py files (shared fixtures) + local test file fixtures
- **Fixture Scopes**: Primarily function-scoped (default), with sophisticated cleanup patterns
- **Testing Frameworks**: pytest + pytest-asyncio + Hypothesis (property-based testing)
- **Mock Strategy**: Multi-layered mocking for BAML client, Claude SDK, and external services
- **Key Patterns**: Cleanup/teardown fixtures, context manager fixtures, state tracking via closure variables

The testing infrastructure supports unit tests, integration tests, end-to-end tests, and property-based tests with markers (`@slow`, `@integration`, `@e2e`).

---

## 📚 Detailed Findings

### 1. Test Organization & Structure

#### Test Directory Layout

\`\`\`
silmari-Context-Engine/
├── pytest.ini                                   # Root pytest config
├── pyproject.toml                               # Defines testpaths and dev dependencies
│
├── tests/                                       # Root integration tests (3 files, ~600 lines)
│   ├── __init__.py
│   ├── test_autonomous_loop.py
│   ├── test_execute_phase.py
│   └── test_loop_orchestrator_integration.py
│
├── planning_pipeline/tests/                     # Pipeline tests (17 files, 8,425 lines)
│   ├── __init__.py
│   ├── conftest.py                              # ⭐ Extended fixtures & mocks (11,275 lines)
│   ├── test_beads.py
│   ├── test_claude_runner.py (1,139 lines)
│   ├── test_decomposition.py (738 lines)
│   ├── test_models.py (1,168 lines)
│   ├── test_orchestrator.py (789 lines)
│   └── [12 more test files]
│
├── silmari_rlm_act/tests/                       # RLM Act tests (13 files, 10,979 lines)
│   ├── __init__.py
│   ├── conftest.py                              # Minimal fixtures (717 lines)
│   ├── test_pipeline.py (3,203 lines)          # ⭐ Largest test file
│   ├── test_cli.py (1,669 lines)
│   ├── test_cwa_integration.py (638 lines)
│   └── [10 more test files]
│
└── context_window_array/tests/                  # CWA tests (6 files, 4,596 lines)
    ├── __init__.py
    ├── test_store.py (1,169 lines)
    ├── test_models.py (995 lines)
    ├── test_implementation_context.py (715 lines)
    └── [3 more test files]
\`\`\`

#### Configuration Files

**pytest.ini** (Root):
\`\`\`ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
\`\`\`

**pyproject.toml** \`[tool.pytest.ini_options]\`:
\`\`\`toml
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = [
    "silmari_rlm_act/tests",
    "context_window_array/tests",
    "planning_pipeline/tests",
    "tests",
]
\`\`\`

**Dev Dependencies**:
- pytest (^8.0.0)
- pytest-asyncio (^0.24.0) - Async test support
- pytest-cov (^5.0.0) - Coverage reporting
- hypothesis (^6.0.0) - Property-based testing

#### Test Statistics

| Directory | Test Files | Total Lines | Notable Features |
|-----------|-----------|-------------|------------------|
| \`planning_pipeline/tests/\` | 17 | 8,425 | Extensive conftest (11,275 lines), BAML mocking |
| \`silmari_rlm_act/tests/\` | 13 | 10,979 | Largest test file (3,203 lines), CLI tests |
| \`context_window_array/tests/\` | 6 | 4,596 | Focused test suite, no conftest |
| \`tests/\` (root) | 3 | ~600 | Integration & orchestration tests |
| **TOTAL** | **46** | **25,070** | |

---

### 2. Pytest Fixtures - Complete Inventory

#### 📁 Shared Fixtures (conftest.py Files)

##### \`/planning_pipeline/tests/conftest.py\` (12 fixtures)

**🔧 Mock BAML & Claude SDK Fixtures (7 fixtures)**

**1. \`mock_baml_initial_extraction\`** (Line 85)
- **Scope**: Function (default)
- **Returns**: \`MockInitialExtractionResponse\`
- **Purpose**: Mock response for BAML ProcessGate1InitialExtractionPrompt
- **Content**: User Authentication System with 3 sub-processes, related concepts
- **Dependencies**: None

**2. \`mock_baml_subprocess_details\`** (Line 103)
- **Scope**: Function (default)
- **Returns**: \`MockSubprocessDetailsResponse\`
- **Purpose**: Mock response for BAML ProcessGate1SubprocessDetailsPrompt
- **Content**: Login form implementation with components (frontend, backend, middleware, shared)
- **Dependencies**: None

**3. \`mock_baml_client\`** (Line 128)
- **Scope**: Function (default)
- **Returns**: MagicMock
- **Purpose**: Complete mock of BAML client for unit tests (legacy)
- **Dependencies**: \`mock_baml_initial_extraction\`, \`mock_baml_subprocess_details\`
- **Pattern**: Composite mock fixture

**4. \`mock_claude_sdk_response\`** (Line 137)
- **Scope**: Function (default)
- **Returns**: Dict with keys: \`success\`, \`output\`, \`error\`, \`elapsed\`
- **Purpose**: Mock response for requirement extraction via Claude SDK
- **Content**: JSON with requirements array containing sub_processes

**5. \`mock_claude_expansion_response\`** (Line 159)
- **Scope**: Function (default)
- **Returns**: Dict with implementation details JSON (3 items)
- **Purpose**: Mock response for requirement expansion (second call)
- **Content**: Auth.login, Session.manage, Auth.recover with full component details

**6. \`mock_claude_expansion_response_limited\`** (Line 219)
- **Scope**: Function (default)
- **Returns**: Dict with limited implementation details (2 items)
- **Purpose**: Mock response with limited details for max_sub_processes tests

**7. \`patch_baml_client\`** (Line 257) ⭐
- **Scope**: Function (default)
- **Returns**: Yields mock patched function
- **Dependencies**: \`mock_claude_sdk_response\`, \`mock_claude_expansion_response\`, \`mock_claude_expansion_response_limited\`
- **Pattern**: Context manager fixture with yield + closure variables
- **Advanced Features**:
  - Uses \`side_effect\` callable for sequential returns
  - First call returns \`mock_claude_sdk_response\` (initial extraction)
  - Subsequent calls return \`mock_claude_expansion_response\` (expansion)
  - Supports override via \`mock_run.return_value\` assignment
  - Uses closure variables: \`call_count[0]\`, \`override_return[0]\` (lists for mutation)
  - Patches: \`planning_pipeline.decomposition.run_claude_sync\`
- **Cleanup**: Patch automatically unpatches on context exit

\`\`\`python
# Advanced pattern example from patch_baml_client:
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
    yield mock_run
\`\`\`

**📂 Project Path & Sample Output Fixtures (5 fixtures)**

**8. \`project_path\`** (Line 303)
- **Scope**: Function (default)
- **Returns**: \`Path(__file__).parent.parent.parent\` (project root)
- **Purpose**: Return the root project path for file system operations

**9. \`sample_research_output\`** (Line 309)
- **Scope**: Function (default)
- **Returns**: String with research report format
- **Purpose**: Sample Claude output containing a research file path
- **Content**: Mock path \`thoughts/searchable/research/2025-01-01-test-research.md\`

**10. \`sample_plan_output\`** (Line 327)
- **Scope**: Function (default)
- **Returns**: String with plan report format
- **Purpose**: Sample Claude output containing a plan file path
- **Content**: Mock path \`thoughts/searchable/plans/2025-01-01-feature/00-overview.md\`

**11. \`sample_phase_output\`** (Line 339)
- **Scope**: Function (default)
- **Returns**: String with phase file list
- **Purpose**: Sample Claude output containing phase file paths
- **Content**: Multiple phase files (01, 02, 03)

**12. Pytest Configuration Hook**: \`pytest_configure(config)\`
- Registers custom markers:
  - \`@pytest.mark.slow\` - Performance-sensitive tests
  - \`@pytest.mark.integration\` - Integration tests
  - \`@pytest.mark.e2e\` - End-to-end tests

##### \`/silmari_rlm_act/tests/conftest.py\` (3 fixtures)

**1. \`sample_timestamp\`** (Line 7)
- **Scope**: Function (default)
- **Returns**: \`datetime(2026, 1, 5, 10, 30, 0)\`
- **Purpose**: Provide a consistent timestamp for tests

**2. \`sample_artifacts\`** (Line 13)
- **Scope**: Function (default)
- **Returns**: List of two artifact paths (research and plan files)
- **Purpose**: Provide sample artifact paths for tests

**3. \`sample_errors\`** (Line 22)
- **Scope**: Function (default)
- **Returns**: List of sample error messages
- **Purpose**: Provide sample error messages for tests

---

#### 📄 Local Fixtures Summary (Test Files)

**test_pipeline.py** (3 fixtures): \`project_path\`, \`beads_controller\`, \`cleanup_issues\`

**test_execute_phase.py** (4 fixtures): \`temp_plan_file\`, \`mock_subprocess_success\`, \`temp_git_repo\`, \`runner_with_plan\`

**test_checkpoint_manager.py** (1 fixture): \`temp_project\`

**test_helpers.py** (2 fixtures): \`temp_project\`, \`temp_project_with_plans\`

**test_step_decomposition.py** (2 fixtures): \`temp_project\`, \`mock_decomposition_result\`

**test_orchestrator.py** (Multiple fixtures): \`project_path\` (4 duplicates), \`cleanup_issues\` (2 instances)

**test_beads.py** (2 fixtures): \`beads_controller\`, \`cleanup_issues\`

**test_steps.py** (3 fixtures): \`project_path\`, \`beads_controller\`, \`cleanup_issues\`

**test_cli.py** (4 fixtures): \`cli_runner\`, \`temp_project\`, \`temp_research_doc\`, \`temp_plan_doc\`

**test_implementation_phase.py** (2 fixtures): \`sample_plan\`, \`cwa\`

**test_validation.py** (3 fixtures): \`temp_hierarchy\`, \`temp_research_doc\`, \`mock_baml_response\`

**test_autonomous_loop.py** (3 fixtures): \`mock_orchestrator\`, \`mock_orchestrator_with_features\`, \`mock_orchestrator_with_status\`

**test_loop_orchestrator_integration.py** (4 fixtures): \`temp_plan_dir\`, \`mock_orchestrator\`, \`temp_project_with_plans\`, \`full_setup\`

**Additional silmari_rlm_act/test_pipeline.py** (7 fixtures): \`temp_project\`, \`mock_cwa\`, \`mock_beads_controller\`, \`sample_research_result\`, \`sample_decomposition_result\`, \`sample_epic_and_issues\`, \`sample_plan_hierarchy\`

**test_beads_sync_phase.py** (2 fixtures): \`mock_beads\`, \`sample_phase_docs\`

---

### 3. Fixture Dependency Graph

\`\`\`
Built-in Fixtures (pytest)
├── tmp_path (built-in) ──────────┐
│   ├── temp_project               │
│   │   └── temp_project_with_plans│
│   ├── sample_plan                │
│   ├── temp_hierarchy             │
│   ├── temp_research_doc          │
│   └── temp_plan_file             │
│                                  │
├── capsys (built-in)              │
├── monkeypatch (built-in)         │
└── caplog (built-in)              │

Custom Fixtures                    │
├── project_path (standalone) ─────┤
│   ├── beads_controller           │
│   │   └── cleanup_issues ⭐      │
│   └── Used directly in tests     │
│                                  │
├── Mock Fixtures                  │
│   ├── mock_baml_initial_extraction
│   ├── mock_baml_subprocess_details
│   │   └── mock_baml_client       │
│   │                              │
│   ├── mock_claude_sdk_response   │
│   ├── mock_claude_expansion_response
│   ├── mock_claude_expansion_response_limited
│   │   └── patch_baml_client ⭐   │
│   │                              │
│   └── mock_baml_response         │
│                                  │
└── Sample Data Fixtures           │
    ├── sample_timestamp           │
    ├── sample_artifacts           │
    ├── sample_errors              │
    ├── sample_research_output     │
    ├── sample_plan_output         │
    └── sample_phase_output        │
\`\`\`

**Legend:**
- ⭐ Advanced fixtures (yield, cleanup, or complex logic)
- → Dependency relationship

---

### 4. Fixture Patterns & Best Practices

#### Pattern 1: Cleanup/Teardown Fixtures ⭐

The most common advanced pattern in the codebase:

\`\`\`python
@pytest.fixture
def cleanup_issues(beads_controller):
    """Track and cleanup created issues after test."""
    created_ids = []
    yield created_ids  # Test receives this list and appends IDs

    # Teardown phase (runs after test completes)
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
    beads_controller.sync()
\`\`\`

**Usage in Tests:**
\`\`\`python
def test_create_issue(cleanup_issues, beads_controller):
    issue_id = beads_controller.create_issue(title="Test Issue")
    cleanup_issues.append(issue_id)  # Will be cleaned up automatically
    assert issue_id is not None
\`\`\`

**Found in**: 8 locations across test files

---

#### Pattern 2: Context Manager Fixtures

\`\`\`python
@pytest.fixture
def patch_baml_client(mock_claude_sdk_response, mock_claude_expansion_response):
    """Context manager to patch run_claude_sync."""
    with patch("planning_pipeline.decomposition.run_claude_sync") as mock_run:
        mock_run.side_effect = side_effect
        yield mock_run
    # Cleanup automatic via context manager exit
\`\`\`

**Found in**: \`patch_baml_client\` fixture

---

#### Pattern 3: Closure Variables for State Tracking

\`\`\`python
@pytest.fixture
def patch_baml_client(...):
    call_count = [0]  # List to allow mutation in nested function
    override_return = [None]

    def side_effect(*args, **kwargs):
        if override_return[0] is not None:
            return override_return[0]
        call_count[0] += 1
        if call_count[0] == 1:
            return mock_claude_sdk_response
        return mock_claude_expansion_response

    with patch(...) as mock_run:
        mock_run.side_effect = side_effect
        # Allow test to override return value
        mock_run.override_return = override_return
        yield mock_run
\`\`\`

**Advanced Feature**: Tests can override behavior at runtime:
\`\`\`python
def test_custom_behavior(patch_baml_client):
    patch_baml_client.return_value = custom_response
    # This overrides the side_effect
\`\`\`

**Found in**: \`patch_baml_client\` fixture

---

#### Pattern 4: Temporary Directory with Structure

\`\`\`python
@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with directory structure."""
    thoughts_dir = tmp_path / "thoughts" / "searchable" / "shared"
    research_dir = thoughts_dir / "research"
    plans_dir = thoughts_dir / "plans"

    research_dir.mkdir(parents=True)
    plans_dir.mkdir(parents=True)

    return tmp_path
\`\`\`

**Found in**: Multiple locations (test_helpers.py, test_checkpoint_manager.py, etc.)

---

#### Pattern 5: Composite Mock Fixtures

\`\`\`python
@pytest.fixture
def mock_baml_client(mock_baml_initial_extraction, mock_baml_subprocess_details):
    """Complete mock of BAML client combining multiple mock fixtures."""
    mock_b = MagicMock()
    mock_b.ProcessGate1InitialExtractionPrompt.return_value = mock_baml_initial_extraction
    mock_b.ProcessGate1SubprocessDetailsPrompt.return_value = mock_baml_subprocess_details
    return mock_b
\`\`\`

**Found in**: \`mock_baml_client\` fixture

---

### 5. Fixture Usage Patterns in Tests

#### How Fixtures Are Injected

Fixtures are passed as function parameters. Pytest automatically resolves dependencies based on parameter names:

\`\`\`python
# Single fixture
def test_creates_pipeline(project_path):
    pipeline = PlanningPipeline(project_path)
    assert pipeline.project_path == project_path.resolve()

# Multiple fixtures
def test_with_cleanup(beads_controller, cleanup_issues):
    issue_id = beads_controller.create_issue(title="Test")
    cleanup_issues.append(issue_id)
    # Test code...

# Class methods with fixtures
class TestPipelineInit:
    def test_creates_pipeline(self, project_path):
        # 'self' (class context) + 'project_path' fixture
        pass
\`\`\`

#### Built-in Pytest Fixtures Used

| Fixture | Usage Count | Purpose |
|---------|-------------|---------|
| \`tmp_path\` | 73 | Temporary directory creation |
| \`capsys\` | 14 | Capture stdout/stderr |
| \`monkeypatch\` | 11 | Patch builtins/modules |
| \`caplog\` | ~5 | Capture log output |

#### Custom Fixture Usage Frequency

| Fixture | Usage Count | Category |
|---------|-------------|----------|
| \`tmp_path\` | 73 | Built-in |
| \`temp_project\` | 23 | Temporary files |
| \`capsys\` | 14 | Built-in |
| \`project_path\` | 13 | Project paths |
| \`patch_baml_client\` | 13 | Mocking |
| \`monkeypatch\` | 11 | Built-in |
| \`beads_controller\` | 9 | Domain objects |
| \`cleanup_issues\` | 8 | Cleanup |
| \`temp_project_with_plans\` | 7 | Temporary files |
| \`mock_decomposition_result\` | 5 | Mocking |

---

### 6. Mock and External Service Patterns

#### External Services Mocked

**1. BAML Client (Code Generation Service)**
\`\`\`python
# Fixtures: mock_baml_client, mock_baml_initial_extraction, mock_baml_subprocess_details
# Mocks: ProcessGate1InitialExtractionPrompt, ProcessGate1SubprocessDetailsPrompt
\`\`\`

**2. Claude SDK (LLM API Calls)**
\`\`\`python
# Fixtures: mock_claude_sdk_response, mock_claude_expansion_response
# Patches: planning_pipeline.decomposition.run_claude_sync
\`\`\`

**3. Beads Issue Tracker (Git-based Issue Management)**
\`\`\`python
# Fixtures: beads_controller (real instance), cleanup_issues
# Also patched in tests: patch.object(BeadsController, '_run_bd', ...)
\`\`\`

**4. Subprocess/CLI Calls**
\`\`\`python
# Fixtures: mock_subprocess_success
# Patches: subprocess.run() for Claude CLI, git, bd commands
\`\`\`

**5. Context Window Array (CWA Integration)**
\`\`\`python
# Fixtures: mock_cwa, cwa
# Mocks: CWAIntegration instance
\`\`\`

#### Mock Usage Statistics

- **Total mock/patch references**: 317+ in planning_pipeline/tests
- **Common assertion patterns**:
  - \`assert_called_once()\`
  - \`assert_called_with()\`
  - \`call_args\`, \`call_args_list\`
  - \`call_count\`

---

### 7. Fixture Scopes & Lifecycle

#### Scope Distribution

| Scope | Count | Details |
|-------|-------|---------|
| **Function** (default) | 68 | Recreated for each test function |
| **Class** | 3 | Instance methods in test classes |
| **Module** | 0 | None found |
| **Session** | 0 | None found |

#### Fixture Parameters

- **None use \`autouse=True\`** (no automatic fixtures)
- **None use \`params\`** (no parametrized fixtures)
- **All use default \`scope="function"\`**

#### Async Fixture Support

Configuration exists but no async fixtures found:
\`\`\`ini
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
\`\`\`

Tests do use \`@pytest.mark.asyncio\` for async test functions.

---

### 8. Testing Frameworks & Tools Integration

#### Pytest Markers

Defined in \`planning_pipeline/tests/conftest.py\`:

\`\`\`python
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
\`\`\`

**Usage**:
\`\`\`python
@pytest.mark.slow
@pytest.mark.integration
def test_full_pipeline_integration(...):
    pass
\`\`\`

#### Hypothesis Integration

Property-based testing with fixtures:

\`\`\`python
from hypothesis import given, strategies as st, suppress_health_check, HealthCheck

@given(research=st.text(min_size=10, max_size=1000))
@pytest.mark.parametrize("max_sub_processes", [None, 2])
def test_decomposition_never_crashes(research, max_sub_processes, patch_baml_client):
    # Test with random inputs + mocked external calls
    pass
\`\`\`

**Health Check Suppression**:
\`\`\`python
settings=Settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
\`\`\`

Allows Hypothesis to work with function-scoped fixtures.

---

### 9. Test Categories & Usage Patterns

#### Unit Tests

**Characteristics**:
- Use mock fixtures extensively
- No file system access (except via \`tmp_path\`)
- Fast execution
- Test individual functions/methods

**Fixtures Used**:
- \`patch_baml_client\`
- \`mock_baml_*\`
- \`sample_*\` data fixtures

**Example**:
\`\`\`python
def test_parses_claude_response(mock_claude_sdk_response):
    result = parse_response(mock_claude_sdk_response)
    assert result.success
\`\`\`

---

#### Integration Tests

**Characteristics**:
- Marked with \`@pytest.mark.integration\` or \`@pytest.mark.slow\`
- Use real service instances
- File system access via \`project_path\` or \`tmp_path\`
- May have cleanup requirements

**Fixtures Used**:
- \`project_path\`
- \`beads_controller\`
- \`cleanup_issues\`
- \`temp_project\`

**Example**:
\`\`\`python
@pytest.mark.integration
def test_creates_beads_issue(beads_controller, cleanup_issues):
    issue_id = beads_controller.create_issue(title="Test Issue")
    cleanup_issues.append(issue_id)
    assert beads_controller.get_issue(issue_id) is not None
\`\`\`

---

#### End-to-End Tests

**Characteristics**:
- Marked with \`@pytest.mark.e2e\`
- Test complete workflows
- Multiple services/components involved
- Longer execution time

**Fixtures Used**:
- \`runner_with_plan\`
- \`full_setup\`
- \`temp_project_with_plans\`
- Multiple mock fixtures

---

#### Property-Based Tests

**Characteristics**:
- Use Hypothesis \`@given\` decorator
- Test with random/generated inputs
- Verify properties hold across input space
- Combined with fixtures for mocking

**Example**:
\`\`\`python
@given(research=st.text(min_size=10, max_size=1000))
def test_decomposition_never_crashes(research, patch_baml_client):
    # Test should never crash regardless of input
    result = decompose_requirements(research)
    assert result is not None
\`\`\`

---

### 10. Data Models & Type Hints

#### Mock Data Classes

Defined in \`planning_pipeline/tests/conftest.py\`:

\`\`\`python
@dataclass
class MockImplementationComponents:
    frontend: List[str] = field(default_factory=list)
    backend: List[str] = field(default_factory=list)
    middleware: List[str] = field(default_factory=list)
    shared: List[str] = field(default_factory=list)

@dataclass
class MockImplementationDetail:
    function_id: str
    description: str
    related_concepts: List[str]
    acceptance_criteria: List[str]
    implementation: MockImplementationComponents

@dataclass
class MockRequirement:
    description: str
    sub_processes: List[str]
    related_concepts: List[str]

@dataclass
class MockResponseMetadata:
    prompt_tokens: int
    output_tokens: int
    total_tokens: int

@dataclass
class MockInitialExtractionResponse:
    requirements: List[MockRequirement]
    metadata: MockResponseMetadata = field(default_factory=lambda: MockResponseMetadata(0, 0, 0))

@dataclass
class MockSubprocessDetailsResponse:
    implementation_details: List[MockImplementationDetail]
    metadata: MockResponseMetadata = field(default_factory=lambda: MockResponseMetadata(0, 0, 0))
\`\`\`

These dataclasses mirror the structure of BAML client responses for testing without external API calls.

#### Fixture Type Hints

Some fixtures include return type hints:

\`\`\`python
@pytest.fixture
def sample_timestamp() -> datetime:
    return datetime(2026, 1, 5, 10, 30, 0)

@pytest.fixture
def sample_artifacts() -> list[str]:
    return [...]

@pytest.fixture
def temp_hierarchy(tmp_path: Path) -> Path:
    doc = tmp_path / "hierarchy.json"
    doc.write_text(json.dumps(hierarchy, indent=2))
    return doc

@pytest.fixture
def mock_baml_response() -> MagicMock:
    return mock_response
\`\`\`

---

## 🔍 Code References

<table>
<tr>
<th>Location</th>
<th>Description</th>
</tr>
<tr>
<td><code>pytest.ini:1-3</code></td>
<td>Root pytest configuration with asyncio settings</td>
</tr>
<tr>
<td><code>pyproject.toml:[tool.pytest.ini_options]</code></td>
<td>Alternative pytest config with testpaths definition</td>
</tr>
<tr>
<td><code>planning_pipeline/tests/conftest.py:85-128</code></td>
<td>BAML mock fixtures (initial extraction & subprocess details)</td>
</tr>
<tr>
<td><code>planning_pipeline/tests/conftest.py:137-256</code></td>
<td>Claude SDK mock fixtures and responses</td>
</tr>
<tr>
<td><code>planning_pipeline/tests/conftest.py:257-301</code></td>
<td>⭐ <code>patch_baml_client</code> - Advanced context manager fixture</td>
</tr>
<tr>
<td><code>silmari_rlm_act/tests/conftest.py:7-29</code></td>
<td>Simple sample data fixtures (timestamp, artifacts, errors)</td>
</tr>
<tr>
<td><code>planning_pipeline/tests/test_pipeline.py:22-29</code></td>
<td>⭐ <code>cleanup_issues</code> - Yield fixture with teardown</td>
</tr>
<tr>
<td><code>planning_pipeline/tests/test_helpers.py:178-186</code></td>
<td><code>temp_project</code> - Creates full directory structure</td>
</tr>
<tr>
<td><code>tests/test_execute_phase.py:75-84</code></td>
<td><code>mock_subprocess_success</code> - Subprocess mocking</td>
</tr>
<tr>
<td><code>tests/test_execute_phase.py:148-157</code></td>
<td><code>temp_git_repo</code> - Temporary git repository</td>
</tr>
</table>

---

## 🏗️ Architecture Documentation

### Testing Architecture Layers

\`\`\`
┌─────────────────────────────────────────────────────────┐
│              Test Layer 1: Unit Tests                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Mock Fixtures (patch_baml_client, mock_*)        │   │
│  │ ↓                                                 │   │
│  │ Business Logic (decomposition, orchestration)    │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│         Test Layer 2: Integration Tests                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Real Instances (beads_controller, CWA)           │   │
│  │ ↓                                                 │   │
│  │ Service Integration (issue tracking, context)    │   │
│  │ ↓                                                 │   │
│  │ Cleanup Fixtures (cleanup_issues)                │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│           Test Layer 3: E2E Tests                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Full Pipeline (runner_with_plan, full_setup)     │   │
│  │ ↓                                                 │   │
│  │ Orchestrator → Claude → Beads → File System     │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│      Test Layer 4: Property-Based Tests                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Hypothesis @given + Fixtures                     │   │
│  │ ↓                                                 │   │
│  │ Property Verification across Input Space         │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
\`\`\`

### Fixture Composition Strategy

The project uses a **layered fixture composition** strategy:

**Layer 1: Built-in Pytest Fixtures**
- Foundation: \`tmp_path\`, \`capsys\`, \`monkeypatch\`, \`caplog\`
- Provide base test infrastructure

**Layer 2: Domain Fixtures**
- Examples: \`project_path\`, \`beads_controller\`, \`cwa\`
- Provide domain-specific context
- May depend on Layer 1 fixtures

**Layer 3: Mock Fixtures**
- Examples: \`mock_baml_client\`, \`mock_claude_sdk_response\`
- Mock external services and APIs
- Independent of Layers 1 and 2

**Layer 4: Composite Fixtures**
- Examples: \`patch_baml_client\`, \`runner_with_plan\`, \`temp_project_with_plans\`
- Combine multiple fixtures from Layers 1-3
- Provide complete test scenarios
- Most complex fixtures with multiple dependencies

**Layer 5: Cleanup Fixtures**
- Examples: \`cleanup_issues\`
- Depend on Layer 2 fixtures
- Ensure test isolation via teardown

This architecture allows:
- ✅ **Test composition**: Combine fixtures at different layers
- ✅ **Reusability**: Share fixtures across test files via conftest.py
- ✅ **Clear separation**: Mock vs real services
- ✅ **Maintainability**: Update fixtures independently

---

## 📊 Summary Statistics

### Fixture Statistics

| Category | Count |
|----------|-------|
| **Total Custom Fixtures** | 68 |
| **Shared Fixtures (conftest.py)** | 15 |
| **Local Test File Fixtures** | 53 |
| **Fixtures with Dependencies** | 12 |
| **Fixtures with Cleanup (yield)** | 4 |
| **Mock Fixtures** | 18 |
| **Temporary File/Directory Fixtures** | 14 |
| **Sample Data Fixtures** | 12 |
| **Integration Fixtures** | 9 |

### Test Statistics

| Metric | Value |
|--------|-------|
| **Total Test Files** | 46 |
| **Total Test Code Lines** | 25,070 |
| **Test Directories** | 4 |
| **Conftest Files** | 2 |
| **Largest Test File** | test_pipeline.py (3,203 lines) |
| **Largest Conftest** | planning_pipeline/tests/conftest.py (11,275 lines) |
| **Most Fixtures in One Directory** | planning_pipeline/tests (12 conftest fixtures) |

### Fixture Usage Frequency

| Built-in Fixture | Usage Count |
|------------------|-------------|
| \`tmp_path\` | 73 |
| \`capsys\` | 14 |
| \`monkeypatch\` | 11 |
| \`caplog\` | ~5 |

| Custom Fixture | Usage Count |
|----------------|-------------|
| \`temp_project\` | 23 |
| \`patch_baml_client\` | 13 |
| \`project_path\` | 13 |
| \`beads_controller\` | 9 |
| \`cleanup_issues\` | 8 |

### Mock/Patch Statistics

- **Total mock/patch references**: 317+ in planning_pipeline/tests
- **Mock fixtures**: 18
- **Services mocked**: 5 (BAML, Claude SDK, Beads, Subprocess, CWA)

---

## 🎨 Testing Patterns & Conventions

### Pattern Summary Table

| Pattern | Usage | Complexity | Examples |
|---------|-------|------------|----------|
| **Simple Return Fixtures** | ⭐⭐⭐⭐⭐ Very Common | Low | \`sample_timestamp\`, \`project_path\` |
| **Cleanup/Teardown (Yield)** | ⭐⭐⭐ Common | Medium | \`cleanup_issues\`, \`temp_plan_dir\` |
| **Context Manager Fixtures** | ⭐ Rare | Medium | \`patch_baml_client\` |
| **Closure State Tracking** | ⭐ Rare | High | \`patch_baml_client\` with call_count |
| **Composite Mock Fixtures** | ⭐⭐⭐ Common | Medium | \`mock_baml_client\` |
| **Temporary Directory + Structure** | ⭐⭐⭐⭐ Very Common | Low-Medium | \`temp_project\`, \`temp_git_repo\` |

### Naming Conventions

**Observed Patterns**:
- \`mock_*\` - Mock objects/responses (18 fixtures)
- \`sample_*\` - Sample data for tests (12 fixtures)
- \`temp_*\` - Temporary files/directories (14 fixtures)
- \`cleanup_*\` - Cleanup/teardown fixtures (4 fixtures)
- \`*_controller\` - Service controllers (beads_controller)

### Test Organization Conventions

**Directory Structure**:
- Tests mirror source code structure (\`planning_pipeline/\` → \`planning_pipeline/tests/\`)
- Conftest at test directory root for shared fixtures
- Test files named \`test_*.py\`

**Test Function Naming**:
\`\`\`python
def test_<action>_<expected_behavior>(fixtures):
    """Docstring: <Scenario> <Expected Outcome>"""
    # Arrange
    # Act
    # Assert
\`\`\`

**Examples**:
\`\`\`python
def test_creates_pipeline_with_project_path(self, project_path):
    """Should create pipeline with provided project path."""

def test_calls_requirement_decomposition_after_memory_sync(self, tmp_path):
    """Given memory sync, should call requirement decomposition."""
\`\`\`

---

## 💡 Key Insights

### 1. Sophisticated Cleanup Patterns

The codebase uses yield fixtures extensively for cleanup, particularly for integration tests that create external resources (Beads issues). This ensures test isolation even when tests fail.

### 2. Multi-Layer Mocking Strategy

The project employs a multi-layer approach to mocking:
- **Layer 1**: Simple mock responses (\`mock_claude_sdk_response\`)
- **Layer 2**: Composite mocks combining Layer 1 (\`mock_baml_client\`)
- **Layer 3**: Context managers with dynamic behavior (\`patch_baml_client\`)

This allows tests to choose the appropriate level of mocking complexity.

### 3. Extensive Conftest in planning_pipeline

The \`planning_pipeline/tests/conftest.py\` file (11,275 lines) contains extensive mock infrastructure, suggesting this is a complex subsystem with significant external dependencies that need mocking.

### 4. Temporary Directory Usage

Heavy reliance on \`tmp_path\` (73 usages) indicates the test suite emphasizes file system isolation and doesn't pollute the working directory.

### 5. No Parametrized Fixtures

The codebase doesn't use \`@pytest.mark.parametrize\` at the fixture level, instead opting for:
- Multiple fixture variants (e.g., \`mock_claude_expansion_response\` vs \`_limited\`)
- Hypothesis for property-based testing with random inputs

### 6. Function-Scoped Everything

All fixtures use function scope (default), indicating a preference for test isolation over performance. Each test gets fresh fixture instances.

### 7. Marker-Based Test Selection

The custom markers (\`@slow\`, \`@integration\`, \`@e2e\`) allow selective test execution:
\`\`\`bash
pytest -m "not slow"              # Skip slow tests
pytest -m "integration"           # Only integration tests
pytest -m "not (integration or e2e)"  # Only unit tests
\`\`\`

### 8. Hypothesis Integration

The combination of Hypothesis with pytest fixtures (with health check suppression) enables property-based testing with mocked external dependencies—a sophisticated testing approach.

---

## 🏁 Conclusion

The silmari-Context-Engine project demonstrates a mature and sophisticated testing infrastructure with pytest. The fixture architecture follows best practices including:

✅ Clear separation between unit, integration, and E2E tests
✅ Comprehensive mocking of external services
✅ Robust cleanup/teardown patterns for test isolation
✅ Property-based testing integration
✅ Extensive test coverage (25,070 lines)
✅ Well-organized conftest files for fixture sharing
✅ Marker-based test categorization for selective execution

The testing patterns documented here serve as a reference for understanding and extending the test suite.
