---
date: 2026-01-14T03:37:14-05:00
researcher: claude
git_commit: cca392fe288684aec34a4c0bca7bd427586b4045
branch: main
repository: silmari-Context-Engine
topic: "Packaging silmari_rlm_act Python Pipeline with Poetry"
tags: [research, packaging, poetry, python, silmari_rlm_act, dependencies]
status: complete
last_updated: 2026-01-14
last_updated_by: claude
---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│           SILMARI_RLM_ACT POETRY PACKAGING RESEARCH                         │
│                        Complete Dependency Analysis                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Research: Packaging silmari_rlm_act Python Pipeline with Poetry

**Date**: 2026-01-14T03:37:14-05:00
**Researcher**: claude
**Git Commit**: `cca392fe288684aec34a4c0bca7bd427586b4045`
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📚 Research Question

How to package the `/silmari_rlm_act` Python pipeline using Poetry, with complete dependency tracing?

---

## 📊 Summary

The `silmari_rlm_act` module is an autonomous TDD pipeline that requires:
- **2 internal workspace dependencies**: `context_window_array` and `planning_pipeline`
- **1 external runtime dependency**: `click>=8.1.0`
- **4 external test dependencies**: `pytest>=9.0.0`, `hypothesis>=6.0.0`, `pytest-asyncio>=1.0.0`, `pytest-cov>=7.0.0`

The project currently has **no packaging configuration** (no `pyproject.toml`, `setup.py`, or `requirements.txt`). Poetry can package this as a **monorepo with workspace dependencies**.

---

## 🎯 Detailed Findings

### Package Structure Overview

```
silmari_rlm_act/
├── __init__.py              # Package root - exports main classes
├── cli.py                   # Click CLI entry point (main())
├── models.py                # Core data models (dataclasses)
├── pipeline.py              # RLMActPipeline orchestrator
├── agents/                  # Agent configs (6 markdown files)
├── checkpoints/             # Checkpoint management
│   ├── __init__.py
│   ├── interactive.py       # Interactive prompts
│   └── manager.py           # CheckpointManager
├── context/                 # CWA integration
│   ├── __init__.py
│   └── cwa_integration.py   # CWAIntegration class
├── phases/                  # Phase implementations
│   ├── __init__.py
│   ├── beads_sync.py
│   ├── decomposition.py
│   ├── implementation.py
│   ├── multi_doc.py
│   ├── research.py
│   └── tdd_planning.py
├── commands/                # Command docs (21 markdown files)
└── tests/                   # Test suite (14 Python files)
    ├── __init__.py
    ├── conftest.py
    └── test_*.py
```

| Category | Count |
|----------|-------|
| Python Source Files | 16 |
| Test Files | 14 |
| Markdown Files | 27 |
| Total | 57 |

---

### Complete Dependency Map

#### 🔴 Internal Dependencies (Workspace)

| Package | Used By | Import Pattern |
|---------|---------|----------------|
| `context_window_array` | `silmari_rlm_act.context.cwa_integration` | Direct imports |
| `planning_pipeline` | `silmari_rlm_act.cli`, `silmari_rlm_act.phases.decomposition` | Direct imports |

<details>
<summary>📁 Imports from context_window_array</summary>

```python
# From silmari_rlm_act/context/cwa_integration.py:11-25
from context_window_array import (
    CentralContextStore,
    ContextEntry,
    EntryType,
    StoreSearchResult,
    TaskBatch,
    TaskBatcher,
    TaskSpec,
)
from context_window_array.batching import BatchExecutor, BatchHandler, BatchResult
from context_window_array.implementation_context import (
    ImplementationContext,
    ImplementationLLMContext,
)
from context_window_array.working_context import WorkingContext, WorkingLLMContext
```
</details>

<details>
<summary>📁 Imports from planning_pipeline</summary>

```python
# From silmari_rlm_act/cli.py:17
from planning_pipeline.beads_controller import BeadsController

# From silmari_rlm_act/phases/decomposition.py:21-27
from planning_pipeline.decomposition import (
    DecompositionConfig,
    DecompositionError,
    SaveCallback,
    decompose_requirements,
)
from planning_pipeline.models import RequirementHierarchy, RequirementNode
```
</details>

---

#### 🟡 External Runtime Dependencies

| Package | Version | Used In | Purpose |
|---------|---------|---------|---------|
| `click` | `>=8.1.0` | `silmari_rlm_act/cli.py` | CLI framework |

```python
# silmari_rlm_act/cli.py:12
import click
```

---

#### 🟢 External Test Dependencies

| Package | Version | Used In | Purpose |
|---------|---------|---------|---------|
| `pytest` | `>=9.0.0` | All test files | Testing framework |
| `hypothesis` | `>=6.0.0` | `test_models.py` | Property-based testing |
| `pytest-asyncio` | `>=1.0.0` | `pytest.ini` config | Async test support |
| `pytest-cov` | `>=7.0.0` | Test runs | Coverage reporting |

---

#### 🔵 Standard Library Dependencies (No Installation Required)

| Module | Used In |
|--------|---------|
| `dataclasses` | `models.py` |
| `datetime` | `models.py`, `phases/*.py` |
| `enum` | `models.py` |
| `json` | `phases/decomposition.py`, `phases/multi_doc.py` |
| `pathlib` | Most files |
| `sys` | `cli.py` |
| `typing` | All files |
| `contextlib` | `context/cwa_integration.py` |
| `unittest.mock` | Test files |

---

### Currently Installed Versions (in .venv)

| Package | Installed Version |
|---------|-------------------|
| Python | 3.12.3 |
| click | 8.3.1 |
| pytest | 9.0.2 |
| hypothesis | 6.148.9 |
| pytest-asyncio | 1.3.0 |
| pytest-cov | 7.0.0 |
| numpy | 2.4.0 |
| baml-py | 0.216.0 |

---

## 🚀 Poetry Packaging Approach

### Option 1: Monorepo with Workspace Dependencies (Recommended)

Poetry supports path dependencies for local packages. Create a `pyproject.toml` at the repository root:

```toml
# /home/maceo/Dev/silmari-Context-Engine/pyproject.toml
[tool.poetry]
name = "silmari-context-engine"
version = "0.1.0"
description = "Silmari Context Engine - Autonomous TDD Pipeline"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"
packages = [
    { include = "silmari_rlm_act" },
    { include = "context_window_array" },
    { include = "planning_pipeline" },
]

[tool.poetry.dependencies]
python = "^3.12"
click = "^8.1.0"

[tool.poetry.group.dev.dependencies]
pytest = "^9.0.0"
hypothesis = "^6.0.0"
pytest-asyncio = "^1.0.0"
pytest-cov = "^7.0.0"
mypy = "^1.9.0"

[tool.poetry.scripts]
silmari-rlm-act = "silmari_rlm_act.cli:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

### Option 2: Separate Packages with Path Dependencies

If you want each package to be independently installable:

**Create `/silmari_rlm_act/pyproject.toml`:**

```toml
[tool.poetry]
name = "silmari-rlm-act"
version = "0.1.0"
description = "Autonomous TDD Pipeline"
authors = ["Your Name <your.email@example.com>"]
packages = [{ include = "silmari_rlm_act", from = ".." }]

[tool.poetry.dependencies]
python = "^3.12"
click = "^8.1.0"
context-window-array = { path = "../context_window_array", develop = true }
planning-pipeline = { path = "../planning_pipeline", develop = true }

[tool.poetry.group.dev.dependencies]
pytest = "^9.0.0"
hypothesis = "^6.0.0"
pytest-asyncio = "^1.0.0"
pytest-cov = "^7.0.0"

[tool.poetry.scripts]
silmari-rlm-act = "silmari_rlm_act.cli:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

---

### Dependency Chain

```
╔═══════════════════════════════════════════════════════════════╗
║                    DEPENDENCY HIERARCHY                        ║
╠═══════════════════════════════════════════════════════════════╣
║                                                                ║
║   silmari_rlm_act                                             ║
║        │                                                       ║
║        ├──► context_window_array (internal)                   ║
║        │         └──► numpy (external, optional for search)   ║
║        │                                                       ║
║        ├──► planning_pipeline (internal)                      ║
║        │         └──► baml-py (external, for decomposition)   ║
║        │                                                       ║
║        └──► click (external, for CLI)                         ║
║                                                                ║
╚═══════════════════════════════════════════════════════════════╝
```

---

### Additional Dependencies from Workspace Packages

**From `context_window_array`:**
- `numpy>=2.0.0` - Used for vector search operations (optional)

**From `planning_pipeline`:**
- `baml-py>=0.216.0` - Used for LLM-based decomposition

---

## Complete pyproject.toml for Monorepo

```toml
# /home/maceo/Dev/silmari-Context-Engine/pyproject.toml

[tool.poetry]
name = "silmari-context-engine"
version = "0.1.0"
description = "Silmari Context Engine - Autonomous TDD Pipeline with Context Window Array"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"
license = "MIT"
packages = [
    { include = "silmari_rlm_act" },
    { include = "context_window_array" },
    { include = "planning_pipeline" },
]

[tool.poetry.dependencies]
python = "^3.12"
# CLI framework
click = "^8.1.0"
# BAML for LLM integration
baml-py = "^0.216.0"
# Optional: Vector search (can be made optional with extras)
numpy = "^2.0.0"

[tool.poetry.group.dev.dependencies]
# Testing
pytest = "^9.0.0"
hypothesis = "^6.0.0"
pytest-asyncio = "^1.0.0"
pytest-cov = "^7.0.0"
# Type checking
mypy = "^1.9.0"
# BAML CLI for code generation
# Note: baml-cli is typically installed globally or via npm

[tool.poetry.extras]
# Optional dependencies
search = ["numpy"]

[tool.poetry.scripts]
# CLI entry points
silmari-rlm-act = "silmari_rlm_act.cli:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = [
    "silmari_rlm_act/tests",
    "context_window_array/tests",
    "planning_pipeline/tests",
    "tests",
]

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

---

## 🛡️ Installation Steps

```bash
# 1. Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# 2. Navigate to project root
cd /home/maceo/Dev/silmari-Context-Engine

# 3. Create pyproject.toml (use content above)

# 4. Install dependencies
poetry install

# 5. Activate virtual environment
poetry shell

# 6. Run CLI
silmari-rlm-act --help

# 7. Run tests
poetry run pytest

# 8. Build package (for distribution)
poetry build
```

---

## Code References

| File | Line | Description |
|------|------|-------------|
| `silmari_rlm_act/__init__.py:1-23` | Package exports |
| `silmari_rlm_act/cli.py:12` | Click import |
| `silmari_rlm_act/cli.py:17` | planning_pipeline import |
| `silmari_rlm_act/context/cwa_integration.py:11-25` | context_window_array imports |
| `silmari_rlm_act/phases/decomposition.py:21-27` | planning_pipeline imports |
| `silmari_rlm_act/models.py:1-413` | Core data models (stdlib only) |
| `planning_pipeline/__init__.py:1-55` | planning_pipeline exports |
| `context_window_array/__init__.py:1-37` | context_window_array exports |

---

## Open Questions

1. **BAML client handling**: The `baml_client/` is generated code - should it be included in the package or generated at install time?

2. **Go port relationship**: The `go/` directory contains a Go port - how should this relate to the Python package?

3. **Version synchronization**: Should `silmari_rlm_act`, `context_window_array`, and `planning_pipeline` share a version number?

4. **Distribution strategy**:
   - PyPI publishing (requires unique package names)?
   - Private package registry?
   - Git-based installation only?

---

## Related Research

- No prior research documents found on this topic in `thoughts/searchable/research/`
