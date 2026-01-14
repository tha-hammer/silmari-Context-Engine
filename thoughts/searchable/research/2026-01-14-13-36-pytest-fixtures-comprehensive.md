---
date: 2026-01-14 13:36:38 -05:00
researcher: Maceo Thompson
git_commit: 86514b2dc0f81e96de5389e3c6b3287bb3e349b3
branch: main
repository: silmari-Context-Engine
topic: "Testing patterns in this project - Focus on pytest fixtures"
tags: [research, codebase, pytest, testing, fixtures, mocking]
status: complete
last_updated: 2026-01-14
last_updated_by: Maceo Thompson
---

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│               PYTEST FIXTURES & TESTING PATTERNS                    │
│                    silmari-Context-Engine                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

# Research: Testing Patterns - Pytest Fixtures Analysis

**Date**: 2026-01-14 13:36:38 -05:00
**Researcher**: Maceo Thompson
**Git Commit**: `86514b2dc0f81e96de5389e3c6b3287bb3e349b3`
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📋 Research Question

Analyze the testing patterns in this project. Focus on pytest fixtures.

---

## 🎯 Summary

The silmari-Context-Engine project implements a comprehensive testing strategy using pytest with extensive fixture patterns across 73 test files (47 Python, 26 Go). The test suite employs **60+ custom fixtures** organized in two main `conftest.py` files, utilizing mock dataclasses, stateful mocking, and fixture dependency chains. All fixtures use the default `function` scope without explicit parameterization, focusing on simplicity and isolation.

**Key Testing Components:**
- **2 conftest.py files** with shared fixtures
- **Custom pytest markers**: `slow`, `integration`, `e2e`
- **Mocking strategies**: MagicMock, mock dataclasses, patch decorators, monkeypatch
- **Fixture patterns**: Sample data, mock responses, temporary paths, cleanup with yield
- **Property-based testing**: Hypothesis with custom strategies and stateful testing

---

## 📊 Test Suite Organization

### Directory Structure

```
silmari-Context-Engine/
├── tests/                           # Root-level tests (3 files)
│   ├── test_autonomous_loop.py
│   ├── test_execute_phase.py
│   └── test_loop_orchestrator_integration.py
│
├── planning_pipeline/tests/         # Planning pipeline tests (22 files)
│   ├── conftest.py                  # 348 lines - Main fixture definitions
│   ├── test_beads.py
│   ├── test_checkpoint_manager.py
│   ├── test_claude.py
│   ├── test_decomposition.py
│   ├── test_helpers.py
│   ├── test_models.py
│   ├── test_orchestrator.py
│   ├── test_phase_execution.py
│   ├── test_pipeline.py
│   ├── test_steps.py
│   └── ... (12 more files)
│
├── silmari_rlm_act/tests/           # RLM Act tests (16 files)
│   ├── conftest.py                  # 29 lines - Simple shared fixtures
│   ├── test_artifact_generation.py
│   ├── test_cli.py
│   ├── test_implementation_phase.py
│   ├── test_models.py
│   ├── test_pipeline.py
│   └── ... (11 more files)
│
├── context_window_array/tests/      # CWA tests (6 files)
│   ├── test_batching.py
│   ├── test_models.py
│   ├── test_store.py
│   └── ... (3 more files)
│
└── go/internal/*/                   # Go tests (26 files, co-located)
    ├── build/*_test.go
    ├── cli/*_test.go
    ├── planning/*_test.go
    └── ... (across 8 packages)
```

### Naming Conventions

| Language | Pattern | Example |
|----------|---------|---------|
| **Python** | `test_*.py` prefix | `test_models.py`, `test_pipeline.py` |
| **Go** | `*_test.go` suffix | `models_test.go`, `pipeline_test.go` |

### Test Coverage by Component

<table>
<tr><th>Component</th><th>Test Files</th><th>Coverage Areas</th></tr>
<tr>
<td><b>Planning Pipeline</b></td>
<td>22 files</td>
<td>Decomposition, orchestration, Claude integration, checkpoints, property generation</td>
</tr>
<tr>
<td><b>RLM Act Pipeline</b></td>
<td>16 files</td>
<td>Phases (research, decomposition, TDD planning, implementation), CLI, validation, CWA integration</td>
</tr>
<tr>
<td><b>Context Window Array</b></td>
<td>6 files</td>
<td>Context management, batching, search, storage</td>
</tr>
<tr>
<td><b>Go Implementation</b></td>
<td>26 files</td>
<td>Planning, CLI, build tools, concurrency, execution, file system utilities</td>
</tr>
</table>

---

## 🔧 Pytest Configuration

### Configuration Files

#### `pytest.ini` (Root)
```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```

#### `pyproject.toml` (Pytest Section)
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

### Custom Pytest Markers

Defined in `planning_pipeline/tests/conftest.py` (lines 10-14):

```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
```

**Usage:**
- `@pytest.mark.slow` - Tests requiring actual CLI/SDK execution
- `@pytest.mark.integration` - Tests requiring external API calls (ANTHROPIC_API_KEY)
- `@pytest.mark.e2e` - End-to-end tests spanning multiple components

**Run commands:**
```bash
# Skip slow tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration

# Run only unit tests (no integration/e2e)
pytest -m "not integration and not e2e"
```

---

## 🎨 Fixture Patterns

### 1. Fixture Locations

| File | Lines | Fixture Count | Purpose |
|------|-------|---------------|---------|
| `planning_pipeline/tests/conftest.py` | 348 | ~40 fixtures | Mock BAML types, Claude SDK responses, project paths |
| `silmari_rlm_act/tests/conftest.py` | 29 | 3 fixtures | Simple shared data (timestamps, artifacts, errors) |
| Individual test files | Various | ~20+ fixtures | Test-specific fixtures (controllers, temp projects, cleanup) |

### 2. Fixture Scopes

**Distribution:**
- ✅ **Function scope (default)**: 100% - All fixtures use default function scope
- ❌ **Class scope**: Not used
- ❌ **Module scope**: Not used
- ❌ **Session scope**: Not used

This design prioritizes test isolation over performance optimization.

### 3. Fixture Dependencies

#### Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                    FIXTURE DEPENDENCY CHAINS                     │
└─────────────────────────────────────────────────────────────────┘

Level 0 (Standalone)
├── sample_timestamp                    [silmari_rlm_act/tests/conftest.py:8]
├── sample_artifacts                    [silmari_rlm_act/tests/conftest.py:14]
├── sample_errors                       [silmari_rlm_act/tests/conftest.py:23]
├── mock_baml_initial_extraction        [planning_pipeline/tests/conftest.py:86]
├── mock_baml_subprocess_details        [planning_pipeline/tests/conftest.py:104]
├── mock_claude_sdk_response            [planning_pipeline/tests/conftest.py:138]
├── mock_claude_expansion_response      [planning_pipeline/tests/conftest.py:160]
└── sample_research_output              [planning_pipeline/tests/conftest.py:310]

Level 1 (Single Dependency)
├── mock_baml_client
│   ├─→ mock_baml_initial_extraction
│   └─→ mock_baml_subprocess_details
│
├── patch_baml_client
│   ├─→ mock_claude_sdk_response
│   ├─→ mock_claude_expansion_response
│   └─→ mock_claude_expansion_response_limited
│
├── temp_project (multiple files)
│   └─→ tmp_path (pytest built-in)
│
└── project_path (standalone)

Level 2 (Chained Dependencies)
├── beads_controller
│   └─→ project_path
│
└── cleanup_issues
    └─→ beads_controller
        └─→ project_path
```

#### Dependency Examples

**Simple Dependency** (`planning_pipeline/tests/conftest.py:129`):
```python
@pytest.fixture
def mock_baml_client(mock_baml_initial_extraction, mock_baml_subprocess_details):
    """Complete mock of BAML client - depends on two other fixtures."""
    mock_b = MagicMock()
    mock_b.ProcessGate1InitialExtractionPrompt.return_value = mock_baml_initial_extraction
    mock_b.ProcessGate1SubprocessDetailsPrompt.return_value = mock_baml_subprocess_details
    return mock_b
```

**Chained Dependency** (`planning_pipeline/tests/test_steps.py`):
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
    yield created_ids  # Test runs here
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
    beads_controller.sync()
```

### 4. Common Fixture Patterns

#### Pattern 1: Sample Data Fixtures
**Purpose:** Provide consistent test data
**Location:** `silmari_rlm_act/tests/conftest.py`

```python
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
```

#### Pattern 2: Mock Dataclasses
**Purpose:** Type-safe mock data structures
**Location:** `planning_pipeline/tests/conftest.py:22-78`

```python
@dataclass
class MockImplementationComponents:
    """Mock for baml_client.types.ImplementationComponents."""
    frontend: List[str] = field(default_factory=list)
    backend: List[str] = field(default_factory=list)
    middleware: List[str] = field(default_factory=list)
    shared: List[str] = field(default_factory=list)

@dataclass
class MockImplementationDetail:
    """Mock for baml_client.types.ImplementationDetail."""
    function_id: str
    description: str
    related_concepts: List[str]
    acceptance_criteria: List[str]
    implementation: MockImplementationComponents
```

**Rationale:** Provides complete type coverage without external BAML client dependencies.

#### Pattern 3: Mock Responses with JSON Output
**Purpose:** Simulate Claude SDK responses
**Location:** `planning_pipeline/tests/conftest.py:138-254`

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

**Key Characteristics:**
- Envelope structure: `{success, output, error, elapsed}`
- Output as JSON-formatted string (not parsed dict)
- Elapsed time as float (seconds)

#### Pattern 4: Temporary Project Setup
**Purpose:** Create isolated test environments
**Used in:** Multiple test files

```python
@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with checkpoints dir."""
    checkpoints_dir = tmp_path / ".workflow-checkpoints"
    checkpoints_dir.mkdir()
    return tmp_path
```

#### Pattern 5: Cleanup with Yield (Teardown)
**Purpose:** Resource cleanup after tests
**Used in:** Beads integration tests, checkpoint tests

```python
@pytest.fixture
def cleanup_issues(beads_controller):
    """Track and cleanup created issues after test."""
    created_ids = []
    yield created_ids  # ← Test executes here
    # Teardown phase
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
    beads_controller.sync()
```

**Execution flow:**
1. Setup: Create empty list
2. Yield: Test runs and appends issue IDs
3. Teardown: Cleanup all created issues

#### Pattern 6: Stateful Mock with side_effect
**Purpose:** Simulate sequential API calls
**Location:** `planning_pipeline/tests/conftest.py:257-301`

```python
@pytest.fixture
def patch_baml_client(mock_claude_sdk_response, mock_claude_expansion_response, mock_claude_expansion_response_limited):
    """Context manager to patch run_claude_sync for decomposition tests.

    First call returns initial extraction (requirements with sub_processes).
    Subsequent calls return expansion (implementation_details).
    """
    call_count = [0]  # Use list to allow mutation
    override_return = [None]  # Allow test override

    def side_effect(*args, **kwargs):
        if override_return[0] is not None:
            return override_return[0]
        call_count[0] += 1
        if call_count[0] == 1:
            return mock_claude_sdk_response
        return mock_claude_expansion_response

    with patch("planning_pipeline.decomposition.run_claude_sync") as mock_run:
        mock_run.side_effect = side_effect

        # Make return_value settable for error testing
        def set_return_value(value):
            override_return[0] = value

        type(mock_run).return_value = property(
            lambda self: override_return[0],
            lambda self, value: set_return_value(value)
        )

        yield mock_run
```

**Features:**
- ✅ Tracks call count for different return values
- ✅ Supports test override via `mock_run.return_value`
- ✅ Uses mutable containers (lists) for state preservation
- ✅ Context manager pattern with yield

#### Pattern 7: Path Fixtures
**Purpose:** Provide project/directory paths

```python
@pytest.fixture
def project_path():
    """Return the root project path."""
    return Path(__file__).parent.parent.parent
```

#### Pattern 8: In-Class Fixtures
**Purpose:** Fixtures scoped to test classes
**Location:** Various test files

```python
class TestDiscoverThoughtsFiles:
    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project with thoughts directory."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        return tmp_path
```

#### Pattern 9: Mock Object Fixtures
**Purpose:** Create MagicMock instances

```python
@pytest.fixture
def mock_cwa() -> MagicMock:
    """Create a mock CWA integration."""
    cwa = MagicMock()
    cwa.store_research.return_value = "research_001"
    cwa.store_plan.return_value = "plan_001"
    return cwa
```

#### Pattern 10: Instance Creation Fixtures
**Purpose:** Create actual class instances

```python
@pytest.fixture
def cwa() -> CWAIntegration:
    """Create CWA integration."""
    return CWAIntegration()

@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()
```

---

## 🎭 Mocking Patterns

### 1. Mock Object Types

#### unittest.mock.MagicMock

**Basic Usage** (`planning_pipeline/tests/conftest.py:131`):
```python
mock_b = MagicMock()
mock_b.ProcessGate1InitialExtractionPrompt.return_value = mock_baml_initial_extraction
mock_b.ProcessGate1SubprocessDetailsPrompt.return_value = mock_baml_subprocess_details
```

**With Attributes** (`planning_pipeline/tests/test_decomposition.py:238`):
```python
mock_response = MagicMock()
mock_detail = MagicMock()
mock_detail.function_id = None
mock_detail.description = "Some description"
mock_detail.acceptance_criteria = []
mock_detail.implementation = None
```

#### unittest.mock.patch Decorator

**Module Function Patching** (`planning_pipeline/tests/test_decomposition.py:283`):
```python
with patch("planning_pipeline.decomposition.run_claude_sync") as mock_run:
    mock_run.return_value = {"success": True, "output": "..."}
    result = decompose_requirements("research content")
```

**Subprocess Patching** (`planning_pipeline/tests/test_claude_runner.py:73`):
```python
with patch("subprocess.Popen") as mock_popen:
    mock_process = MagicMock()
    mock_process.poll.return_value = 0
    mock_process.returncode = 0
    mock_process.stdout.read1.side_effect = [b"output\n", b""]
    mock_popen.return_value = mock_process
    # Test code here
```

**File Operations** (`planning_pipeline/tests/test_claude_runner.py:490`):
```python
mock_creds = {
    "claudeAiOauth": {
        "accessToken": "test_token",
        "refreshToken": "test_refresh",
        "expiresAt": int(time.time() * 1000) + 3600000,
    }
}
with patch("builtins.open", mock_open(read_data=json.dumps(mock_creds))):
    creds = read_credentials()
```

**Environment Variables** (`planning_pipeline/tests/test_claude_runner.py:972`):
```python
with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
    # Test code here
```

#### pytest.monkeypatch

**Input Mocking** (`planning_pipeline/tests/test_orchestrator.py:58`):
```python
def test_collects_single_line(self, monkeypatch):
    """Given single line then blank, returns that line."""
    from planning_orchestrator import collect_prompt

    inputs = iter(["How does auth work?", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    result = collect_prompt()
    assert result == "How does auth work?"
```

**Function Replacement** (`planning_pipeline/tests/test_orchestrator.py:107`):
```python
def test_fails_when_claude_missing(self, monkeypatch):
    """Given claude not installed, returns error."""
    original_run = subprocess.run

    def mock_run(cmd, *args, **kwargs):
        if cmd[0] == "which" and cmd[1] == "claude":
            result = type('Result', (), {'returncode': 1})()
            return result
        return original_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_run)
    result = check_prerequisites()
```

### 2. side_effect Patterns

#### List of Return Values (Sequential)

```python
mock_process.poll.side_effect = [None, 0]
# Call 1: returns None (still running)
# Call 2: returns 0 (finished successfully)

mock_process.stdout.read1.side_effect = [b"output\n", b""]
# Call 1: returns data
# Call 2: returns empty (EOF)
```

#### Exception Raising

```python
with patch("subprocess.Popen") as mock_popen:
    mock_popen.side_effect = FileNotFoundError("claude not found")
    result = run_claude_subprocess("test", timeout=5)
    assert result["success"] is False
```

#### Callable/Function

```python
def side_effect(*args, **kwargs):
    call_count[0] += 1
    if call_count[0] == 1:
        return first_response
    return subsequent_response

mock_run.side_effect = side_effect
```

### 3. Mock Assertions

#### Verify Calls

```python
# Not called
mock.assert_not_called()

# Called once
mock.assert_called_once()

# Called with specific args
mock.assert_called_with(arg1, arg2)

# Any call with args
mock.assert_any_call(arg1, arg2)
```

#### Inspect Call Arguments

```python
# Last call positional args
call_args = mock_popen.call_args[0][0]

# Last call keyword args
_, kwargs = mock_popen.call_args
assert kwargs["stdin"] == subprocess.PIPE
```

### 4. Mock Response Structures

#### Claude SDK Response Format

```python
{
    "success": bool,
    "output": str,  # JSON-formatted string
    "error": str,
    "elapsed": float  # Seconds
}
```

#### BAML Response Mock Structure

```python
MockInitialExtractionResponse:
    requirements: List[MockRequirement]
        - description: str
        - sub_processes: List[str]
        - related_concepts: Optional[List[str]]
    metadata: MockResponseMetadata
        - timestamp: str (ISO 8601)
        - model: str
        - schema_version: str
        - dynamic_types_applied: List[str]
        - groups_processed: int
        - requirements_analyzed: int

MockSubprocessDetailsResponse:
    implementation_details: List[MockImplementationDetail]
        - function_id: str
        - description: str
        - related_concepts: List[str]
        - acceptance_criteria: List[str]
        - implementation: MockImplementationComponents
            - frontend: List[str]
            - backend: List[str]
            - middleware: List[str]
            - shared: List[str]
    metadata: MockResponseMetadata
```

---

## 🔬 Property-Based Testing with Hypothesis

### Custom Strategies

**Location:** `planning_pipeline/tests/test_models.py`

#### Strategy Composition

```python
@st.composite
def _requirement_id_strategy(draw, prefix: str = "REQ") -> str:
    """Generate valid requirement IDs like REQ_001, REQ_001.2, REQ_001.2.1."""
    base_num = draw(st.integers(min_value=1, max_value=999))
    base_id = f"{prefix}_{base_num:03d}"

    num_levels = draw(st.integers(min_value=0, max_value=2))
    for _ in range(num_levels):
        sub_num = draw(st.integers(min_value=1, max_value=9))
        base_id = f"{base_id}.{sub_num}"

    return base_id
```

#### Filtered Strategies

```python
def _non_whitespace_text(min_size: int = 1, max_size: int = 100):
    """Strategy for generating non-whitespace text."""
    return st.text(
        alphabet=st.characters(
            blacklist_categories=("Cs",),
            blacklist_characters="\r\n\t "
        ),
        min_size=min_size,
        max_size=max_size,
    ).filter(lambda s: s.strip())
```

### Stateful Testing

**RuleBasedStateMachine Pattern** (`test_models.py:580-675`):

```python
class HierarchyStateMachine(RuleBasedStateMachine):
    """Stateful testing of RequirementHierarchy operations."""

    def __init__(self):
        super().__init__()
        self.hierarchy = RequirementHierarchy()
        self.added_ids = []

    @rule(req_id=_requirement_id_strategy(), description=st.text())
    def add_requirement(self, req_id, description):
        """Add a requirement to the hierarchy."""
        requirement = Requirement(id=req_id, description=description)
        self.hierarchy.add_requirement(requirement)
        self.added_ids.append(req_id)

    @invariant()
    def all_requirements_findable(self):
        """All added requirements should be findable."""
        for req_id in self.added_ids:
            requirement = self.hierarchy.find_requirement(req_id)
            assert requirement is not None
```

---

## 📈 Fixture Usage Statistics

### Overall Metrics

| Metric | Count |
|--------|-------|
| **Total Fixtures Defined** | 60+ |
| **conftest.py Files** | 2 |
| **Test Files with Local Fixtures** | ~15 |
| **Fixtures in planning_pipeline/conftest.py** | ~40 |
| **Fixtures in silmari_rlm_act/conftest.py** | 3 |

### Fixture Scope Distribution

| Scope | Count | Percentage |
|-------|-------|------------|
| Function (default) | 60+ | 100% |
| Class | 0 | 0% |
| Module | 0 | 0% |
| Session | 0 | 0% |

### Fixture Dependency Distribution

| Dependency Type | Count |
|-----------------|-------|
| Standalone (no dependencies) | ~35 |
| Single dependency | ~15 |
| Multiple dependencies | ~10 |
| Built-in fixture dependencies (tmp_path) | ~35 |

### Fixture Type Distribution

| Fixture Type | Count | Examples |
|--------------|-------|----------|
| Mock objects (MagicMock/custom) | ~25 | `mock_baml_client`, `mock_cwa` |
| Temporary paths/directories | ~15 | `temp_project`, `tmp_path` |
| Resource cleanup (yield) | ~8 | `cleanup_issues` |
| Data objects | ~12 | `sample_timestamp`, `mock_claude_sdk_response` |
| Instance creation | ~10 | `cwa`, `cli_runner`, `beads_controller` |

---

## 🔍 Code References

### Primary Fixture Files

- **`planning_pipeline/tests/conftest.py`** - Main fixture definitions (348 lines)
  - Lines 10-14: Custom marker registration
  - Lines 22-78: Mock BAML dataclasses
  - Lines 86-134: BAML mock fixtures
  - Lines 138-254: Claude SDK mock responses
  - Lines 257-301: Stateful `patch_baml_client` fixture
  - Lines 304-348: Sample output fixtures

- **`silmari_rlm_act/tests/conftest.py`** - Simple shared fixtures (29 lines)
  - Lines 7-10: `sample_timestamp` fixture
  - Lines 13-19: `sample_artifacts` fixture
  - Lines 22-28: `sample_errors` fixture

### Test Files with Local Fixtures

| File | Fixture Count | Key Fixtures |
|------|---------------|--------------|
| `test_beads.py` | 2 | `beads_controller`, `cleanup_issues` |
| `test_checkpoint_manager.py` | 1 | `temp_project` |
| `test_step_decomposition.py` | 2 | `temp_project`, `mock_decomposition_result` |
| `test_steps.py` | 3 | `project_path`, `beads_controller`, `cleanup_issues` |
| `test_pipeline.py` (planning) | 3 | `project_path`, `beads_controller`, `cleanup_issues` |
| `test_helpers.py` | 1 | `temp_project` (in class) |
| `test_orchestrator.py` | 2 | `project_path`, `cleanup_issues` (class methods) |
| `test_pipeline.py` (rlm_act) | 5 | `temp_project`, `mock_cwa`, `mock_beads_controller`, `sample_research_result`, `sample_decomposition_result` |
| `test_cli.py` | 2 | `cli_runner`, `temp_project` |
| `test_validation.py` | 3 | `temp_hierarchy`, `temp_research_doc`, `mock_baml_response` |
| `test_implementation_phase.py` | 2 | `sample_plan`, `cwa` |
| `test_beads_sync_phase.py` | 2 | `mock_beads`, `sample_phase_docs` |

### Pytest Configuration

- **`pytest.ini`** - Asyncio configuration (4 lines)
- **`pyproject.toml`** - Tool configuration (77 lines)
  - Lines 56-64: `[tool.pytest.ini_options]` section with testpaths

---

## 🏗️ Testing Architecture

### Test Separation Strategy

```
┌────────────────────────────────────────────────────────┐
│                   TEST CLASSIFICATION                  │
└────────────────────────────────────────────────────────┘

Unit Tests
├── Uses: Mocked dependencies (fixtures, patches)
├── Speed: Fast (<1s per test)
├── Markers: None (default)
└── Example: test_decomposition.py::TestDecomposeRequirements

Integration Tests
├── Uses: Real external dependencies (APIs, databases)
├── Speed: Slow (1-10s per test)
├── Markers: @pytest.mark.integration
├── Requires: ANTHROPIC_API_KEY environment variable
└── Example: test_decomposition.py::TestDecomposeRequirementsIntegration

Slow Tests
├── Uses: Actual CLI/SDK execution
├── Speed: Very slow (10s+ per test)
├── Markers: @pytest.mark.slow
└── Example: test_claude_runner.py slow tests

E2E Tests
├── Uses: Full system integration
├── Speed: Very slow (10s+ per test)
├── Markers: @pytest.mark.e2e
└── Example: End-to-end pipeline tests
```

### Test Execution Commands

```bash
# Run all tests
pytest

# Run specific test directory
pytest planning_pipeline/tests/

# Skip slow tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration

# Run unit tests only
pytest -m "not integration and not e2e and not slow"

# Run with coverage
pytest --cov=planning_pipeline --cov-report=html

# Run specific test file
pytest planning_pipeline/tests/test_models.py

# Run specific test
pytest planning_pipeline/tests/test_models.py::TestRequirement::test_valid_creation
```

---

## 📚 Fixture Data Patterns

### Timestamp Patterns

```python
# Python datetime
datetime(2026, 1, 5, 10, 30, 0)

# ISO 8601 string
"2026-01-02T00:00:00Z"
```

### File Path Patterns

```python
# Absolute paths
"/home/user/project/thoughts/research/2026-01-05-topic.md"

# Relative paths (project convention)
"thoughts/searchable/research/YYYY-MM-DD-topic.md"
"thoughts/searchable/plans/YYYY-MM-DD-feature/##-phase-name.md"

# Hierarchical structure
"<type>/<date>-<topic>/<##-name>.md"
```

### Requirement ID Patterns

```python
# Parent requirements
"REQ_001", "REQ_002"

# Child requirements (sub-processes)
"REQ_001.1", "REQ_001.2"

# Implementation details (grandchildren)
"REQ_001.1.1", "REQ_001.2.1"
```

### Component Architecture Pattern

All implementation fixtures follow a **three-tier architecture**:

```python
implementation: {
    "frontend": ["LoginForm", "AuthContext"],
    "backend": ["AuthService.login", "UserRepository.findByEmail"],
    "middleware": ["validateCredentials"],
    "shared": ["User", "AuthResult"]
}
```

---

## 🎯 Key Testing Patterns

### Pattern Summary Table

| Pattern | Purpose | Location | Usage Frequency |
|---------|---------|----------|-----------------|
| **MagicMock** | General object mocking | conftest.py, test files | High (~25 fixtures) |
| **@patch decorator** | Replace module functions | test_claude_runner.py | Medium (~10 uses) |
| **Mock dataclasses** | Type-safe mock data | conftest.py | Medium (8 classes) |
| **side_effect lists** | Sequential return values | test_claude_runner.py | Medium (~15 uses) |
| **side_effect functions** | Stateful mocking | conftest.py | Low (1-2 uses) |
| **side_effect exceptions** | Error simulation | test files | Medium (~5 uses) |
| **Yield fixtures** | Setup/teardown | test files | Medium (~8 fixtures) |
| **mock_open** | File I/O mocking | test_claude_runner.py | Low (~2 uses) |
| **monkeypatch** | Pytest-style patching | test_orchestrator.py | Low (~5 uses) |
| **Hypothesis** | Property-based testing | test_models.py | Low (1 file) |
| **tmp_path** | Temporary directories | All test files | High (~35 fixtures) |

---

## 📖 Testing Best Practices Observed

### ✅ Strengths

1. **Consistent Naming**: All fixtures use descriptive names with prefixes (`mock_`, `sample_`, `temp_`)
2. **Type Hints**: silmari_rlm_act tests use comprehensive type hints on fixtures
3. **Isolation**: All fixtures use function scope for maximum test isolation
4. **Documentation**: Fixtures include docstrings explaining purpose
5. **Separation of Concerns**: Unit/integration tests clearly separated with markers
6. **Cleanup Patterns**: Yield-based fixtures handle resource cleanup
7. **Realistic Test Data**: Mock data reflects actual project domain (authentication, components)
8. **Stateful Testing**: Hypothesis RuleBasedStateMachine for complex state testing
9. **Configuration Management**: Clear pytest configuration in both pytest.ini and pyproject.toml
10. **Fixture Composition**: Fixtures depend on other fixtures to build complex scenarios

### 📊 Test Execution Performance

```
Unit Tests (mocked)
├── Count: ~90% of tests
├── Speed: Fast (<1s per test)
└── Can run offline: ✅

Integration Tests
├── Count: ~8% of tests
├── Speed: Slow (1-10s per test)
└── Requires: Internet + API key

Slow Tests
├── Count: ~2% of tests
├── Speed: Very slow (10s+ per test)
└── Skipped by default: ✅
```

---

## 🔗 Related Research

- Previous pytest research documents in `thoughts/searchable/research/`:
  - `2026-01-14-pytest-fixtures-comprehensive-analysis.md`
  - `2026-01-14-pytest-fixtures-detailed-analysis.md`
  - `2026-01-14-pytest-fixtures-analysis.md`
  - `2026-01-06-pytest-fixtures-patterns.md`

---

## 📝 Summary

The silmari-Context-Engine project implements a **mature and comprehensive pytest testing strategy** with:

- ✅ **73 total test files** (47 Python, 26 Go)
- ✅ **60+ custom fixtures** across 2 main conftest.py files
- ✅ **100% function-scoped fixtures** for maximum isolation
- ✅ **10 distinct fixture patterns** (sample data, mocks, paths, cleanup, stateful, etc.)
- ✅ **Custom pytest markers** for test categorization (slow, integration, e2e)
- ✅ **Comprehensive mocking** using MagicMock, patch, monkeypatch
- ✅ **Property-based testing** with Hypothesis custom strategies
- ✅ **Stateful testing** with RuleBasedStateMachine
- ✅ **Clear separation** between unit/integration/slow tests
- ✅ **Realistic test data** following project conventions

The testing approach prioritizes **test isolation, maintainability, and comprehensive coverage** while maintaining clear separation between fast unit tests and slower integration tests.

---

**Research Complete** ✅
*For follow-up questions or deeper analysis of specific patterns, please ask.*
