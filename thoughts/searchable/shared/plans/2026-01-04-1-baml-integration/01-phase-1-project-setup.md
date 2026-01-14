# Phase 1: Project Setup

## Overview

Configure Python project with BAML dependency and set up BAML generator configuration.

## Dependencies

- **Requires**: None (first phase)
- **Blocks**: Phase 2 (Schema Definitions)

## Behaviors Covered

- Behavior 1: Project Setup with pyproject.toml
- Behavior 2: BAML Generator Configuration

## Changes Required

### New Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python project configuration with baml-py dependency |
| `baml_src/main.baml` | BAML generator configuration |
| `baml_src/clients.baml` | LLM client definitions |
| `planning_pipeline/tests/test_baml_setup.py` | Tests for setup behaviors |

### File Contents

**pyproject.toml**
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

**baml_src/main.baml**
```baml
generator lang_python {
  output_type "python/pydantic"
  output_dir "../baml_client"
  version "0.80.0"
  default_client_mode "sync"
}
```

**baml_src/clients.baml**
```baml
client<llm> ClaudeSonnet {
  provider anthropic
  options {
    model "claude-3-5-sonnet-20241022"
    api_key env.ANTHROPIC_API_KEY
  }
}
```

## TDD Cycle

### Red: Write Failing Tests

```bash
pytest planning_pipeline/tests/test_baml_setup.py -v
```

Expected failures:
- `test_pyproject_exists` - pyproject.toml doesn't exist
- `test_baml_dependency_in_pyproject` - no baml-py in dependencies
- `test_baml_cli_available` - baml-cli not installed
- `test_baml_src_directory_exists` - baml_src/ doesn't exist
- `test_main_baml_exists` - main.baml doesn't exist
- `test_baml_client_generated` - baml_client/ doesn't exist
- `test_baml_client_importable` - can't import baml_client

### Green: Implement

1. Create `pyproject.toml`
2. Run `pip install -e .`
3. Create `baml_src/main.baml`
4. Create `baml_src/clients.baml`
5. Run `baml-cli generate`

### Refactor

- Add existing project dependencies to pyproject.toml
- Improve generator configuration if needed

## Success Criteria

### Automated
- [ ] `pytest planning_pipeline/tests/test_baml_setup.py::TestBAMLSetup -v` passes
- [ ] `pytest planning_pipeline/tests/test_baml_setup.py::TestBAMLGeneration -v` passes

### Manual
- [ ] `baml-cli --version` outputs version info
- [ ] `pip install -e .` completes without errors
- [ ] `baml_client/` directory contains Python files
- [ ] `from baml_client import b` works in Python REPL

## Testable Function

**End of Phase Test**: After this phase, the following should succeed:

```python
import subprocess
import sys

# Test 1: baml-cli is available
result = subprocess.run(
    [sys.executable, "-m", "baml_cli", "--version"],
    capture_output=True,
    text=True
)
assert result.returncode == 0

# Test 2: baml_client is importable
from baml_client import b
assert b is not None
```
