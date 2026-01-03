---
date: 2026-01-01T17:07:55-05:00
researcher: maceo
git_commit: 1593fb24780193e59665ef7ac57b1b79634bac68
branch: main
repository: silmari-Context-Engine
topic: "Pytest Fixture Patterns and Testing Infrastructure"
tags: [research, pytest, fixtures, testing, tdd, conftest]
status: complete
last_updated: 2026-01-01
last_updated_by: maceo
---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PYTEST FIXTURES & TESTING PATTERNS                       │
│                       silmari-Context-Engine Project                        │
│                              Research Report                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Date**: 2026-01-01T17:07:55-05:00
**Researcher**: maceo
**Git Commit**: 1593fb24780193e59665ef7ac57b1b79634bac68
**Branch**: main
**Repository**: silmari-Context-Engine

## Research Question

Analyze the testing patterns in this project, focusing on pytest fixtures.

---

## 📊 Summary

The project uses pytest with **20 custom fixtures** across **11 test files** (10 test files + 1 conftest.py). All fixtures use **function scope** (default). The codebase follows **BDD-style test organization** with Given-When-Then docstrings and behavior-driven test class naming. Key patterns include **yield fixtures for cleanup**, **fixture dependency chains**, and **shared fixtures via conftest.py**.

| Metric | Value |
|--------|-------|
| Total Test Files | 10 |
| Conftest Files | 1 |
| Custom Fixtures | 20 |
| Fixture Scopes Used | Function (100%) |
| Custom Markers | 3 (slow, integration, e2e) |
| Parametrized Tests | 0 |

---

## 📁 Test File Organization

### Directory Structure

All test files reside in a single directory:

```
planning_pipeline/tests/
├── conftest.py              # 4 shared fixtures
├── test_beads.py            # BeadsController CRUD tests
├── test_beads_controller.py # BeadsController unit tests
├── test_checkpoint_manager.py # Checkpoint detection tests
├── test_checkpoints.py      # Interactive checkpoint tests
├── test_claude.py           # Claude SDK integration tests
├── test_helpers.py          # Parser/helper function tests
├── test_integrated_orchestrator.py # Integrated orchestrator tests
├── test_orchestrator.py     # Main orchestrator tests
├── test_pipeline.py         # PlanningPipeline tests
└── test_steps.py            # Step execution tests
```

### Test File Contents

| File | Purpose | Key Fixtures Used |
|------|---------|-------------------|
| `conftest.py` | Shared fixtures & markers | Defines: `project_path`, `sample_*_output` |
| `test_beads.py` | BeadsController CRUD | `beads_controller`, `cleanup_issues` |
| `test_beads_controller.py` | Unit tests with mocks | `tmp_path` |
| `test_checkpoint_manager.py` | Checkpoint detection | `temp_project`, `tmp_path` |
| `test_checkpoints.py` | Interactive checkpoints | Mock `input` |
| `test_claude.py` | Claude SDK calls | None (slow tests) |
| `test_helpers.py` | Output parsers | `sample_research_output`, `temp_project` |
| `test_integrated_orchestrator.py` | Full orchestration | `tmp_path`, mocks |
| `test_orchestrator.py` | Pipeline execution | `project_path`, `cleanup_issues`, `monkeypatch` |
| `test_pipeline.py` | Pipeline initialization | `project_path`, `beads_controller`, `cleanup_issues` |
| `test_steps.py` | Step functions | `project_path`, `beads_controller`, `cleanup_issues` |

---

## 🎯 Fixture Definitions

### Pattern 1: Project Path Fixture

**Location**: `planning_pipeline/tests/conftest.py:14-17`

```python
@pytest.fixture
def project_path():
    """Return the root project path."""
    return Path(__file__).parent.parent.parent
```

| Property | Value |
|----------|-------|
| Scope | Function (default) |
| Dependencies | None |
| Returns | `Path` object |
| Usage | 7+ test files |

This fixture is **duplicated** in `test_pipeline.py:9-12`, `test_steps.py:14-17`, and multiple test classes in `test_orchestrator.py`.

---

### Pattern 2: BeadsController Fixture

**Location**: `planning_pipeline/tests/test_pipeline.py:15-18`

```python
@pytest.fixture
def beads_controller(project_path):
    """Create BeadsController with project path."""
    return BeadsController(project_path)
```

| Property | Value |
|----------|-------|
| Scope | Function (default) |
| Dependencies | `project_path` |
| Returns | `BeadsController` instance |
| Used In | `test_pipeline.py`, `test_steps.py`, `test_beads.py` |

**Dependency Chain**: `project_path` → `beads_controller`

---

### Pattern 3: Yield Fixtures for Cleanup

**Location**: `planning_pipeline/tests/test_pipeline.py:21-28`

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

| Property | Value |
|----------|-------|
| Scope | Function (default) |
| Dependencies | `beads_controller` |
| Pattern | Setup → Yield → Teardown |
| Teardown Actions | Close issues, sync |

**Dependency Chain**: `project_path` → `beads_controller` → `cleanup_issues`

This pattern appears in:
- `test_beads.py:15-22`
- `test_pipeline.py:21-28`
- `test_steps.py:26-33`
- `test_orchestrator.py:153-162` (class method variant)

---

### Pattern 4: Sample Data Fixtures

**Location**: `planning_pipeline/tests/conftest.py:20-58`

```python
@pytest.fixture
def sample_research_output():
    """Sample Claude output containing a research file path."""
    return """
    Research complete!
    I've analyzed the codebase and created a research document.
    Created: thoughts/shared/research/2025-01-01-test-research.md
    ...
    """

@pytest.fixture
def sample_plan_output():
    """Sample Claude output containing a plan file path."""
    return """
    Planning complete!
    Plan written to thoughts/shared/plans/2025-01-01-feature/00-overview.md
    ...
    """

@pytest.fixture
def sample_phase_output():
    """Sample Claude output containing phase file paths."""
    return """
    Created phase files:
    - thoughts/shared/plans/2025-01-01-feature/01-phase-1-setup.md
    - thoughts/shared/plans/2025-01-01-feature/02-phase-2-impl.md
    ...
    """
```

| Fixture | Returns | Used For |
|---------|---------|----------|
| `sample_research_output` | Multi-line string | Testing output parsers |
| `sample_plan_output` | Multi-line string | Testing plan extraction |
| `sample_phase_output` | Multi-line string | Testing phase file parsing |

---

### Pattern 5: Temp Directory Fixtures

**Location**: `planning_pipeline/tests/test_checkpoint_manager.py:19-24`

```python
@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with checkpoints dir."""
    checkpoints_dir = tmp_path / ".workflow-checkpoints"
    checkpoints_dir.mkdir()
    return tmp_path
```

**Location**: `planning_pipeline/tests/test_helpers.py:178-186`

```python
@pytest.fixture
def temp_project(self, tmp_path):
    """Create a temporary project with thoughts directory."""
    research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
    research_dir.mkdir(parents=True)
    plans_dir = tmp_path / "thoughts" / "searchable" / "shared" / "plans"
    plans_dir.mkdir(parents=True)
    return tmp_path
```

| Property | Value |
|----------|-------|
| Dependencies | `tmp_path` (pytest built-in) |
| Pattern | Create directory structure |
| Cleanup | Automatic via `tmp_path` |

---

## 📋 Fixture Inventory

### All 20 Custom Fixtures

| # | Fixture Name | Location | Scope | Dependencies | Pattern |
|---|--------------|----------|-------|--------------|---------|
| 1 | `project_path` | `conftest.py:14` | function | None | Path calculation |
| 2 | `sample_research_output` | `conftest.py:20` | function | None | Sample data |
| 3 | `sample_plan_output` | `conftest.py:38` | function | None | Sample data |
| 4 | `sample_phase_output` | `conftest.py:50` | function | None | Sample data |
| 5 | `project_path` | `test_pipeline.py:9` | function | None | Path (duplicate) |
| 6 | `beads_controller` | `test_pipeline.py:15` | function | `project_path` | Controller init |
| 7 | `cleanup_issues` | `test_pipeline.py:21` | function | `beads_controller` | Yield cleanup |
| 8 | `project_path` | `test_steps.py:14` | function | None | Path (duplicate) |
| 9 | `beads_controller` | `test_steps.py:20` | function | `project_path` | Controller init |
| 10 | `cleanup_issues` | `test_steps.py:26` | function | `beads_controller` | Yield cleanup |
| 11 | `beads_controller` | `test_beads.py:8` | function | None | Inline path |
| 12 | `cleanup_issues` | `test_beads.py:15` | function | `beads_controller` | Yield cleanup |
| 13 | `temp_project` | `test_checkpoint_manager.py:19` | function | `tmp_path` | Temp dir |
| 14 | `project_path` | `test_orchestrator.py:148` | function | None | Class method |
| 15 | `cleanup_issues` | `test_orchestrator.py:153` | function | `project_path` | Class method |
| 16 | `project_path` | `test_orchestrator.py:282` | function | None | Class method |
| 17 | `project_path` | `test_orchestrator.py:323` | function | None | Class method |
| 18 | `cleanup_issues` | `test_orchestrator.py:327` | function | `project_path` | Class method |
| 19 | `project_path` | `test_orchestrator.py:457` | function | None | Class method |
| 20 | `temp_project` | `test_helpers.py:178` | function | `tmp_path` | Class method |

---

## 🔗 Fixture Dependencies

### Dependency Chains

```
┌─────────────────────────────────────────────────────────────────┐
│                     FIXTURE DEPENDENCY GRAPH                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  (pytest built-in)          (custom fixtures)                    │
│                                                                  │
│      tmp_path ──────────────► temp_project                       │
│                                                                  │
│      project_path ──────────► beads_controller                   │
│                                      │                           │
│                                      ▼                           │
│                               cleanup_issues                     │
│                                                                  │
│      (no deps)              sample_research_output               │
│      (no deps)              sample_plan_output                   │
│      (no deps)              sample_phase_output                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Dependency Table

| Fixture | Depends On | Depended On By |
|---------|------------|----------------|
| `project_path` | - | `beads_controller`, `cleanup_issues` |
| `beads_controller` | `project_path` | `cleanup_issues` |
| `cleanup_issues` | `beads_controller` or `project_path` | - |
| `temp_project` | `tmp_path` | - |
| `sample_*_output` | - | - |

---

## 🏷️ Custom Markers

**Location**: `planning_pipeline/tests/conftest.py:7-11`

```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
```

### Marker Usage

| Marker | Purpose | Usage Example |
|--------|---------|---------------|
| `@pytest.mark.slow` | Tests calling Claude SDK | `test_claude.py:10` |
| `@pytest.mark.integration` | Integration tests | `test_orchestrator.py:319` |
| `@pytest.mark.e2e` | End-to-end tests | `test_orchestrator.py:318` |

**Running Tests by Marker**:
```bash
pytest -m "not slow"        # Skip slow tests
pytest -m "integration"     # Run only integration tests
pytest -m "not e2e"         # Skip e2e tests
```

---

## 🧪 Testing Patterns

### Pattern 1: Given-When-Then Docstrings (BDD Style)

**Location**: `planning_pipeline/tests/test_beads.py:28-40`

```python
def test_creates_task_issue(self, beads_controller, cleanup_issues):
    """Given valid title/type/priority, creates issue and returns success."""
    # WHEN
    result = beads_controller.create_issue(
        title="TDD Test Issue - Create",
        issue_type="task",
        priority=2
    )
    # THEN
    assert result["success"] is True
    assert "data" in result
```

All test docstrings follow `"""Given [precondition], [action] [expected result]."""` format.

---

### Pattern 2: Arrange-Act-Assert

**Location**: `planning_pipeline/tests/test_checkpoint_manager.py:38-64`

```python
def test_detect_resumable_checkpoint_finds_latest(temp_project):
    """Finds most recent checkpoint."""
    # ARRANGE
    checkpoints_dir = temp_project / ".workflow-checkpoints"
    old = {"id": "old-id", "phase": "research-failed", ...}
    (checkpoints_dir / "old.json").write_text(json.dumps(old))
    new = {"id": "new-id", "phase": "planning-failed", ...}
    (checkpoints_dir / "new.json").write_text(json.dumps(new))

    # ACT
    result = detect_resumable_checkpoint(temp_project)

    # ASSERT
    assert result["id"] == "new-id"
    assert result["phase"] == "planning-failed"
```

---

### Pattern 3: Behavior-Driven Test Classes

**Location**: `planning_pipeline/tests/test_beads.py:25-47`

```python
class TestBeadsControllerCreateIssue:
    """Behavior 4: BeadsController - Create Issue."""

    def test_creates_task_issue(self, beads_controller, cleanup_issues):
        ...

    def test_creates_epic_issue(self, beads_controller, cleanup_issues):
        ...
```

Test classes are named as `Test[Component][Behavior]` with behavior docstrings.

---

### Pattern 4: Mock Context Managers

**Location**: `planning_pipeline/tests/test_checkpoints.py:21-22`

```python
with patch('builtins.input', return_value='c'):
    result = interactive_checkpoint_research(research_result)
```

**Location**: `planning_pipeline/tests/test_integrated_orchestrator.py:300-305`

```python
with patch.object(BeadsController, 'create_issue', side_effect=mock_create):
    with patch.object(BeadsController, 'create_epic', return_value={...}):
        with patch.object(BeadsController, 'add_dependency', return_value={...}):
            orchestrator = IntegratedOrchestrator(tmp_path)
            result = orchestrator.create_phase_issues(...)
```

---

### Pattern 5: Iterator Pattern for Mock Input

**Location**: `planning_pipeline/tests/test_orchestrator.py:72-78`

```python
inputs = iter([
    "Research the authentication system.",
    "Focus on JWT token handling.",
    ""
])
monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
```

Provides sequential mock inputs for interactive functions.

---

### Pattern 6: Mock Factory Pattern

**Location**: `planning_pipeline/tests/test_integrated_orchestrator.py:295-310`

```python
created_issues = []

def mock_create(title, issue_type, priority):
    created_issues.append({"title": title, "priority": priority})
    return {"success": True, "data": {"id": f"issue-{len(created_issues)}"}}

with patch.object(BeadsController, 'create_issue', side_effect=mock_create):
    ...

assert len(created_issues) == 3
assert created_issues[0]["priority"] == 1
```

Factory function captures call arguments for later verification.

---

## 🔍 Pytest Built-in Fixtures Used

| Fixture | Purpose | Used In |
|---------|---------|---------|
| `tmp_path` | Temporary directory per test | `test_checkpoint_manager.py`, `test_helpers.py`, `test_orchestrator.py`, `test_beads_controller.py`, `test_integrated_orchestrator.py` |
| `monkeypatch` | Attribute/env patching | `test_orchestrator.py` |
| `capsys` | Capture stdout/stderr | `test_orchestrator.py` |

---

## 📚 Historical Context (from thoughts/)

The following documents contain related testing information:

### TDD Plans
- `thoughts/shared/plans/2025-12-31-tdd-python-deterministic-pipeline.md` - Complete TDD methodology with 14 behavior specifications
- `thoughts/shared/plans/2026-01-01-tdd-planning-orchestrator.md` - Test markers and organization
- `thoughts/shared/plans/2026-01-01-ENG-XXXX-tdd-integrated-orchestrator-02-feature-status.md` - Concrete pytest fixture examples

### Research Documents
- `thoughts/shared/research/2026-01-01-pipeline-research.md` - Test patterns section, pytest markers for Go port
- `thoughts/shared/research/2025-12-31-context-engine-codebase.md` - Test file organization mapping

### Testing Philosophy (from docs)
- **Minimal mocking** - Preference for real subprocess calls
- **BDD-style naming** - Descriptive behavior-based test names
- **Red-Green-Refactor** - TDD cycle consistently followed
- **Unit tests** for pure parser functions
- **Integration tests** for full workflows

---

## 📊 Patterns Summary

### What This Project Uses

| Feature | Status | Notes |
|---------|--------|-------|
| Function-scoped fixtures | ✅ Used | All 20 fixtures |
| Module/Session-scoped fixtures | ❌ Not used | All use default scope |
| Yield fixtures (teardown) | ✅ Used | 5 cleanup fixtures |
| Fixture dependencies | ✅ Used | Up to 3 levels deep |
| Shared fixtures (conftest.py) | ✅ Used | 4 shared fixtures |
| Custom markers | ✅ Used | slow, integration, e2e |
| autouse fixtures | ❌ Not used | No autouse=True found |
| pytest.mark.parametrize | ❌ Not used | No parametrized tests |
| Fixture factories | ✅ Used | Mock factory pattern |
| Built-in fixtures | ✅ Used | tmp_path, monkeypatch, capsys |

### Fixture Distribution

```
┌──────────────────────────────────────────────────────────────┐
│              FIXTURE DISTRIBUTION BY FILE                     │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  conftest.py          ████ 4 fixtures (shared)                │
│  test_orchestrator.py ██████ 6 fixtures (class methods)       │
│  test_pipeline.py     ███ 3 fixtures                          │
│  test_steps.py        ███ 3 fixtures                          │
│  test_beads.py        ██ 2 fixtures                           │
│  test_checkpoint_mgr  █ 1 fixture                             │
│  test_helpers.py      █ 1 fixture                             │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Code References

| File | Line | Description |
|------|------|-------------|
| `planning_pipeline/tests/conftest.py:7-11` | Marker registration |
| `planning_pipeline/tests/conftest.py:14-17` | Shared `project_path` fixture |
| `planning_pipeline/tests/conftest.py:20-58` | Sample data fixtures |
| `planning_pipeline/tests/test_pipeline.py:21-28` | Yield cleanup fixture |
| `planning_pipeline/tests/test_checkpoint_manager.py:19-24` | Temp directory fixture |
| `planning_pipeline/tests/test_orchestrator.py:148-162` | Class-scoped fixtures |
| `planning_pipeline/tests/test_integrated_orchestrator.py:295-310` | Mock factory pattern |

---

## Open Questions

- Should module/session-scoped fixtures be introduced for expensive setup (e.g., BeadsController)?
- Would parametrized tests reduce code duplication in similar test cases?
- Should the duplicated `project_path` fixtures be consolidated into conftest.py?

---

*Research completed: 2026-01-01T17:07:55-05:00*
