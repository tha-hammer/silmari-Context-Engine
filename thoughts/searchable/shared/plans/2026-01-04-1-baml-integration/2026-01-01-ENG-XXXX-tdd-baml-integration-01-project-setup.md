# Phase 1: Project Setup

## Overview

Configure Python project with BAML dependencies and initialize BAML code generation. This phase establishes the foundation for all subsequent BAML integration work.

**Behaviors Covered**: 1, 2
**Human-Testable Function**: `baml-cli --version` outputs version info; `pip install -e .` completes successfully

## Dependencies

- **Requires**: None (first phase)
- **Blocks**: Phase 2 (Schema Definitions)

## Changes Required

### Behavior 1: pyproject.toml with baml-py

| File | Line | Change Description |
|------|------|-------------------|
| `pyproject.toml` | NEW | Create Python project config with baml-py dependency |

**Test File**: `planning_pipeline/tests/test_baml_setup.py`

```python
class TestBAMLSetup:
    """Behavior 1: BAML project configuration."""

    def test_baml_cli_available(self):
        """Given baml-py installed, baml-cli is available."""
        # Runs: sys.executable -m baml_cli --version
        # Expects: returncode == 0, "baml" or "version" in stdout

    def test_pyproject_exists(self):
        """Given project root, pyproject.toml exists."""
        # Checks: project_root / "pyproject.toml" exists

    def test_baml_dependency_in_pyproject(self):
        """Given pyproject.toml, baml-py is listed as dependency."""
        # Checks: "baml-py" in pyproject content
```

**Implementation**: `pyproject.toml`
```toml
[project]
name = "silmari-context-engine"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "baml-py>=0.80.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-mock>=3.14.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

### Behavior 2: BAML Generator Configuration

| File | Line | Change Description |
|------|------|-------------------|
| `baml_src/main.baml` | NEW | Generator config for Python output |
| `baml_src/clients.baml` | NEW | Claude Sonnet client definition |

**Test File**: `planning_pipeline/tests/test_baml_setup.py`

```python
class TestBAMLGeneration:
    """Behavior 2: BAML code generation."""

    def test_baml_src_directory_exists(self):
        """Given project, baml_src/ directory exists."""
        # Checks: project_root / "baml_src" is directory

    def test_main_baml_exists(self):
        """Given baml_src/, main.baml with generator config exists."""
        # Checks: "generator" in main.baml content

    def test_baml_client_generated(self):
        """Given baml-cli generate ran, baml_client/ exists."""
        # Checks: project_root / "baml_client" exists

    def test_baml_client_importable(self):
        """Given generated client, it can be imported."""
        # Imports: from baml_client import b
```

**Implementation**: `baml_src/main.baml`
```baml
generator lang_python {
  output_type "python/pydantic"
  output_dir "../baml_client"
  version "0.80.0"
  default_client_mode "sync"
}
```

**Implementation**: `baml_src/clients.baml`
```baml
client<llm> ClaudeSonnet {
  provider anthropic
  options {
    model "claude-3-5-sonnet-20241022"
    api_key env.ANTHROPIC_API_KEY
  }
}
```

## Success Criteria

### Automated Tests
```bash
# Red phase - tests should fail
pytest planning_pipeline/tests/test_baml_setup.py -v

# Green phase - after implementation
pip install -e .
baml-cli generate
pytest planning_pipeline/tests/test_baml_setup.py -v
```

### Manual Verification
- [ ] `baml-cli --version` outputs version info
- [ ] `pip install -e .` completes without errors
- [ ] `baml_client/` directory contains Python files
- [ ] `from baml_client import b` works in Python REPL

## Implementation Steps

1. Create `pyproject.toml` in project root
2. Run `pip install -e .` to install dependencies
3. Create `baml_src/` directory
4. Create `baml_src/main.baml` with generator config
5. Create `baml_src/clients.baml` with Claude client
6. Run `baml-cli generate` to create `baml_client/`
7. Verify all tests pass

## Rollback Plan

If issues arise:
1. Remove `baml_client/` directory
2. Remove `baml_src/` directory
3. Remove `pyproject.toml` (if created new)
4. Run `pip uninstall baml-py`
