# Phase 1: LLM-Powered Techstack Detection

## Overview

Implement `IntegratedOrchestrator.get_project_info()` method that uses Claude SDK to analyze overview.md files and extract project name, tech stack, and description.

## Dependencies

**Requires**: None (first phase)
**Blocks**: Phase 6 (Session Logging), Phase 8 (Integration)

## Changes Required

### New File: `planning_pipeline/integrated_orchestrator.py`

Create the base `IntegratedOrchestrator` class with `get_project_info()` method.

```python
# planning_pipeline/integrated_orchestrator.py:1-60
"""Integrated orchestrator using beads for state and Claude for LLM calls."""

import json
from pathlib import Path
from typing import Any

from .beads_controller import BeadsController
from .claude_runner import run_claude_sync


class IntegratedOrchestrator:
    """Orchestrator using planning_pipeline and beads for state management."""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self.bd = BeadsController(project_path)

    def get_project_info(self) -> dict[str, Any]:
        """Detect project info from overview.md via LLM."""
        # Implementation here...

    def _default_project_info(self) -> dict[str, Any]:
        """Return default project info when detection fails."""
        # Implementation here...
```

### New File: `planning_pipeline/tests/test_integrated_orchestrator.py`

Create test file with `TestGetProjectInfo` class.

```python
# planning_pipeline/tests/test_integrated_orchestrator.py:1-80
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator


class TestGetProjectInfo:
    """Tests for LLM-powered project info detection."""
    # Test methods here...
```

## Test Specification

**Given**: An overview.md file exists at `thoughts/shared/plans/*-overview.md`
**When**: `get_project_info()` is called with a project path
**Then**: Returns dict with name, stack, description from LLM analysis

### Test Cases

1. `test_extracts_techstack_from_overview_file` - Happy path with overview.md
2. `test_fallback_to_readme_when_no_overview` - Falls back to README.md
3. `test_returns_defaults_when_no_files_found` - No files, return defaults
4. `test_handles_invalid_json_from_llm` - LLM returns invalid JSON

### Edge Cases

- No overview file found → fallback to README.md
- No files found → return defaults with project directory name
- LLM returns invalid JSON → return defaults
- Empty overview content → return defaults

## Implementation

### Red Phase Test Code

```python
def test_extracts_techstack_from_overview_file(self, tmp_path):
    """Given overview.md exists, returns techstack from LLM analysis."""
    plans_dir = tmp_path / "thoughts" / "shared" / "plans"
    plans_dir.mkdir(parents=True)
    overview = plans_dir / "2026-01-01-feature-00-overview.md"
    overview.write_text("""# Feature Implementation

## Tech Stack
- Python 3.11
- FastAPI
- PostgreSQL
""")

    mock_result = {
        "success": True,
        "output": '{"name": "Feature", "stack": "Python FastAPI PostgreSQL", "description": "A feature implementation"}'
    }

    with patch('planning_pipeline.integrated_orchestrator.run_claude_sync', return_value=mock_result):
        orchestrator = IntegratedOrchestrator(tmp_path)
        info = orchestrator.get_project_info()

        assert info["name"] == "Feature"
        assert "Python" in info["stack"]
        assert "FastAPI" in info["stack"]
        assert info["path"] == tmp_path
        assert info["model"] == "sonnet"
```

### Green Phase Implementation

```python
def get_project_info(self) -> dict[str, Any]:
    """Detect project info from overview.md via LLM."""
    search_patterns = [
        "thoughts/**/plans/*-overview.md",
        "thoughts/**/plans/*-00-overview.md",
        "thoughts/**/plans/*.md",
        "README.md",
    ]

    content = ""
    for pattern in search_patterns:
        files = list(self.project_path.glob(pattern))
        if files:
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            content = files[0].read_text()[:5000]
            break

    if not content:
        return self._default_project_info()

    prompt = f"""Analyze this project documentation and extract:
1. Project name
2. Tech stack (language, framework, database)
3. Brief description (1-2 sentences)

Documentation:
{content}

Return ONLY valid JSON: {{"name": "...", "stack": "...", "description": "..."}}"""

    result = run_claude_sync(prompt=prompt, timeout=60, stream=False)

    if not result["success"]:
        return self._default_project_info()

    try:
        info = json.loads(result["output"])
        info["path"] = self.project_path
        info["model"] = "sonnet"
        return info
    except json.JSONDecodeError:
        return self._default_project_info()

def _default_project_info(self) -> dict[str, Any]:
    """Return default project info when detection fails."""
    return {
        "name": self.project_path.name,
        "path": self.project_path,
        "stack": "Unknown",
        "description": "",
        "model": "sonnet"
    }
```

## Success Criteria

### Automated

- [ ] Test fails for right reason (Red): `pytest planning_pipeline/tests/test_integrated_orchestrator.py::TestGetProjectInfo -v`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_integrated_orchestrator.py::TestGetProjectInfo -v`
- [ ] All tests pass after refactor: `pytest planning_pipeline/tests/`
- [ ] Type check passes: `mypy planning_pipeline/integrated_orchestrator.py`

### Manual (Human-Testable)

Run from project root:

```bash
python -c "
from pathlib import Path
from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

orchestrator = IntegratedOrchestrator(Path('.'))
info = orchestrator.get_project_info()
print(f'Project: {info[\"name\"]}')
print(f'Stack: {info[\"stack\"]}')
print(f'Description: {info[\"description\"]}')
"
```

**Expected**: Returns project info extracted from overview.md or README.md

## References

- `planning_pipeline/claude_runner.py:23-81` - run_claude_sync function
- `orchestrator.py:322-407` - Original get_project_info_interactive function
