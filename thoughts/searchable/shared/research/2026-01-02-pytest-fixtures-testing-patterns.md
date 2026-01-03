---
date: 2026-01-02T13:42:20-05:00
researcher: maceo
git_commit: 82132f774a983fc906bbf9ec15279ccb69d1ee6f
branch: main
repository: silmari-Context-Engine
topic: "Pytest Fixtures and Testing Patterns Analysis"
tags: [research, testing, pytest, fixtures, codebase]
status: complete
last_updated: 2026-01-02
last_updated_by: maceo
---

```
┌─────────────────────────────────────────────────────────────────────┐
│                PYTEST FIXTURES TESTING PATTERNS                     │
│                    silmari-Context-Engine                           │
│                      Research Document                              │
└─────────────────────────────────────────────────────────────────────┘
```

**Date**: 2026-01-02T13:42:20-05:00
**Researcher**: maceo
**Git Commit**: `82132f774a983fc906bbf9ec15279ccb69d1ee6f`
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📚 Research Question

Analyze the testing patterns in this project. Focus on pytest fixtures.

---

## 📊 Summary

This project uses **pytest** as its primary testing framework with a **minimalist conftest.py approach**. The codebase contains **15 test files** across **2 test directories**, with **one centralized conftest.py** providing shared fixtures. Key patterns include:

| Aspect | Finding |
|--------|---------|
| **Framework** | pytest (all 15 test files) |
| **Fixture Count** | 20+ custom fixtures across 11 test files |
| **Fixture Scope** | All function-scoped (default) |
| **Custom Markers** | `slow`, `integration`, `e2e` |
| **Property Testing** | Hypothesis with custom strategies |
| **Test Style** | BDD-style Given-When-Then docstrings |

---

## 🎯 Detailed Findings

### Test Directory Structure

```
/home/maceo/Dev/silmari-Context-Engine/
├── tests/                              # Root-level tests (2 files)
│   ├── __init__.py
│   ├── test_autonomous_loop.py
│   └── test_loop_orchestrator_integration.py
│
├── planning_pipeline/tests/            # Module tests (13 files)
│   ├── __init__.py
│   ├── conftest.py                     # Shared fixtures
│   ├── test_beads.py
│   ├── test_beads_controller.py
│   ├── test_checkpoint_manager.py
│   ├── test_checkpoints.py
│   ├── test_claude.py
│   ├── test_helpers.py
│   ├── test_integrated_orchestrator.py
│   ├── test_models.py
│   ├── test_orchestrator.py
│   ├── test_pipeline.py
│   ├── test_property_generator.py
│   ├── test_steps.py
│   └── test_visualization.py
│
└── .hypothesis/                        # Hypothesis test database
    ├── examples/                       # Cached test examples
    └── constants/                      # Cached constants
```

---

### Conftest.py Configuration

**Location**: `planning_pipeline/tests/conftest.py`

#### Pytest Hooks

| Hook | Lines | Purpose |
|------|-------|---------|
| `pytest_configure` | 7-11 | Registers custom markers |

#### Custom Markers Registered

| Marker | Purpose | Deselect With |
|--------|---------|---------------|
| `@pytest.mark.slow` | Tests with LLM API calls | `-m "not slow"` |
| `@pytest.mark.integration` | Integration tests | `-m "not integration"` |
| `@pytest.mark.e2e` | End-to-end tests | `-m "not e2e"` |

#### Global Fixtures in conftest.py

| Fixture | Lines | Returns | Purpose |
|---------|-------|---------|---------|
| `project_path` | 14-17 | `Path` | Root project directory |
| `sample_research_output` | 20-35 | `str` | Mock Claude research output |
| `sample_plan_output` | 38-47 | `str` | Mock Claude plan output |
| `sample_phase_output` | 50-58 | `str` | Mock Claude phase file list |

---

### 🔧 Fixture Patterns

#### Pattern 1: Basic Fixture Definition

```python
# conftest.py:14-17
@pytest.fixture
def project_path():
    """Return the root project path."""
    return Path(__file__).parent.parent.parent
```

**Usage**:
```python
def test_creates_pipeline_with_project_path(self, project_path):
    pipeline = PlanningPipeline(project_path)
    assert pipeline.project_path == project_path.resolve()
```

---

#### Pattern 2: Fixture Composition (Dependency Chains)

```
project_path (fixture)
    ↓
beads_controller (fixture, depends on project_path)
    ↓
cleanup_issues (fixture, depends on beads_controller)
```

```python
# test_steps.py:20-23
@pytest.fixture
def beads_controller(project_path):
    """Create BeadsController with project path."""
    return BeadsController(project_path)
```

---

#### Pattern 3: Yield Fixtures (Setup/Teardown)

```python
# test_beads.py:15-22
@pytest.fixture
def cleanup_issues(beads_controller):
    """Track and cleanup created issues after test."""
    created_ids = []
    yield created_ids  # Test runs here
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
    beads_controller.sync()
```

**Key aspects**:
- Code before `yield` = setup
- Code after `yield` = teardown (always runs, even on failure)
- Returns mutable object for test to populate

---

#### Pattern 4: Built-in Fixtures Usage

| Fixture | Source | Usage Location |
|---------|--------|----------------|
| `tmp_path` | pytest built-in | `test_checkpoint_manager.py:19-24` |
| `monkeypatch` | pytest built-in | `test_orchestrator.py:58-66` |
| `capsys` | pytest built-in | `test_orchestrator.py:204-219` |

**Example - tmp_path**:
```python
# test_checkpoint_manager.py:19-24
@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with checkpoints dir."""
    checkpoints_dir = tmp_path / ".workflow-checkpoints"
    checkpoints_dir.mkdir()
    return tmp_path
```

**Example - monkeypatch**:
```python
# test_orchestrator.py:58-66
def test_collects_single_line(self, monkeypatch):
    inputs = iter(["How does auth work?", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    result = collect_prompt()
    assert result == "How does auth work?"
```

**Example - capsys**:
```python
# test_orchestrator.py:204-219
def test_displays_success_result(self, capsys):
    display_result(result)
    captured = capsys.readouterr()
    assert "SUCCESS" in captured.out
```

---

#### Pattern 5: Class-Scoped Fixtures

```python
# test_helpers.py:178-186
class TestDiscoverThoughtsFiles:

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project with thoughts directory."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        return tmp_path

    def test_discovers_today_files(self, temp_project):
        # Uses the class-level fixture
        ...
```

---

#### Pattern 6: @pytest.mark.parametrize

```python
# test_property_generator.py:432-476
@pytest.mark.parametrize(
    "criterion,expected_type",
    [
        ("Must validate unique IDs", "invariant"),
        ("All values distinct", "invariant"),
        ("Save and load preserves data", "round_trip"),
        ("Applying twice gives same result", "idempotence"),
        ("Matches reference implementation", "oracle"),
    ],
)
def test_criterion_classified_correctly(self, criterion, expected_type):
    result = derive_properties([criterion])
    assert result[0].property_type == expected_type
```

---

### 🧪 Hypothesis Property-Based Testing

**Location**: `planning_pipeline/tests/test_property_generator.py`

#### Custom Strategy Example

```python
# test_property_generator.py:18-24
@st.composite
def _criterion_with_keyword(draw, keywords: list[str]) -> str:
    """Generate a criterion containing one of the keywords."""
    keyword = draw(st.sampled_from(keywords))
    prefix = draw(st.text(min_size=0, max_size=30, alphabet=...))
    suffix = draw(st.text(min_size=0, max_size=30, alphabet=...))
    return f"{prefix} {keyword} {suffix}".strip()
```

**Usage**:
```python
@given(_criterion_with_keyword(["invariant", "must", "always"]))
@settings(max_examples=50)
def test_invariant_keywords_detected(self, criterion):
    ...
```

---

### 📋 Complete Fixture Inventory

<details>
<summary>Click to expand full fixture table</summary>

| Fixture | File | Lines | Scope | Dependencies |
|---------|------|-------|-------|--------------|
| `project_path` | `conftest.py` | 14-17 | function | None |
| `sample_research_output` | `conftest.py` | 20-35 | function | None |
| `sample_plan_output` | `conftest.py` | 38-47 | function | None |
| `sample_phase_output` | `conftest.py` | 50-58 | function | None |
| `temp_project` | `test_helpers.py` | 178-186 | function | `tmp_path` |
| `temp_project` | `test_checkpoint_manager.py` | 19-24 | function | `tmp_path` |
| `beads_controller` | `test_steps.py` | 20-23 | function | `project_path` |
| `cleanup_issues` | `test_steps.py` | 26-33 | function | `beads_controller` |
| `beads_controller` | `test_pipeline.py` | 15-18 | function | `project_path` |
| `cleanup_issues` | `test_pipeline.py` | 21-28 | function | `beads_controller` |
| `beads_controller` | `test_beads.py` | 10-13 | function | `project_path` |
| `cleanup_issues` | `test_beads.py` | 15-22 | function | `beads_controller` |
| `project_path` | `test_orchestrator.py` | 148-151 | function | None |
| `cleanup_issues` | `test_orchestrator.py` | 153-162 | function | `project_path` |
| `project_path` | `test_orchestrator.py` | 282-284 | function | None |
| `project_path` | `test_orchestrator.py` | 323-326 | function | None |
| `cleanup_issues` | `test_orchestrator.py` | 328-337 | function | `project_path` |

</details>

---

### 🚫 Patterns NOT Used

| Pattern | Status |
|---------|--------|
| `autouse=True` fixtures | Not used |
| `scope="session"` or `scope="module"` | Not used |
| Parameterized fixtures (`params=`) | Not used |
| pytest.ini / pyproject.toml config | Not present |

---

## 💡 Code References

### Key Files

| File | Purpose |
|------|---------|
| `planning_pipeline/tests/conftest.py` | Central fixture configuration |
| `planning_pipeline/tests/test_property_generator.py` | Hypothesis strategies |
| `planning_pipeline/tests/test_orchestrator.py` | Most comprehensive fixture usage |

### Fixture Definition Locations

- `conftest.py:14-17` - `project_path` fixture
- `conftest.py:20-35` - `sample_research_output` fixture
- `test_steps.py:20-33` - `beads_controller` and `cleanup_issues` chain
- `test_checkpoint_manager.py:19-24` - `temp_project` with tmp_path
- `test_property_generator.py:18-24` - Hypothesis custom strategy

---

## 📖 Historical Context (from thoughts/)

| Document | Key Content |
|----------|-------------|
| `thoughts/shared/research/2026-01-01-pytest-fixtures-testing-patterns.md` | Prior fixture analysis (20 fixtures documented) |
| `thoughts/shared/plans/2025-12-31-tdd-python-deterministic-pipeline.md` | Original TDD strategy: "pytest with Unit/Integration/E2E" |
| `thoughts/shared/plans/2026-01-01-tdd-planning-orchestrator.md` | Cleanup requirements for beads issues |
| `thoughts/shared/research/2026-01-01-rust-pipeline-port.md` | Comparison: Python monkeypatching vs Rust trait-based DI |

---

## 🔗 Related Research

- `thoughts/shared/research/2026-01-01-pytest-fixtures-testing-patterns.md` - Earlier fixture analysis
- `thoughts/shared/research/2026-01-01-pipeline-research.md` - "pytest with BDD-style organization"
- `thoughts/shared/research/2026-01-02-iterative-requirement-decomposition-with-visualization.md` - Hypothesis custom strategies

---

## ❓ Open Questions

None - this is a documentation of existing patterns.

---

```
┌─────────────────────────────────────────────────────────────────────┐
│                         END OF DOCUMENT                             │
└─────────────────────────────────────────────────────────────────────┘
```
