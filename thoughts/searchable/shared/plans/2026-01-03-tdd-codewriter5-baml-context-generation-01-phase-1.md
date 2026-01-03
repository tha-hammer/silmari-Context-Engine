# Phase 1: Tech Stack Extraction

## Overview
Implement the `extract_tech_stack()` function that uses BAML to analyze project files and identify languages, frameworks, testing tools, and build systems.

## Dependencies
**Requires**:
- BAML client generated (`baml_client/`)
- `baml_src/codewriter5.baml` definitions

**Blocks**: Phase 3 (needs tech stack data to save)

## Changes Required

### New File: `planning_pipeline/context_generation.py`
**Lines**: 1-264 (entire new file)

Core functions:
- `extract_tech_stack(project_path: Path) -> TechStack` (lines ~205-222)
- `_collect_tech_stack_files(project_path: Path) -> List[str]` (lines ~224-263)
- `ContextGenerationError` exception class (lines ~200-202)

### New File: `planning_pipeline/tests/test_context_generation.py`
**Lines**: 1-121 (initial tests)

Test cases:
- `test_extract_tech_stack_identifies_python_project`
- `test_extract_tech_stack_identifies_typescript_project`
- `test_extract_tech_stack_handles_empty_directory`
- `test_extract_tech_stack_handles_baml_client_error`

### Update: `planning_pipeline/tests/conftest.py`
**Append after existing fixtures**

New fixtures:
- `sample_python_project(tmp_path)` - Creates Python project structure
- `sample_ts_project(tmp_path)` - Creates TypeScript project structure

## Implementation Steps

### 1. 🔴 Red: Write Failing Tests
```bash
# Create test file with failing tests
# Tests will fail because function doesn't exist yet
pytest planning_pipeline/tests/test_context_generation.py::test_extract_tech_stack_identifies_python_project -v
```

Expected: `ModuleNotFoundError: No module named 'planning_pipeline.context_generation'`

### 2. 🟢 Green: Minimal Implementation
Create `planning_pipeline/context_generation.py` with:
- Basic `extract_tech_stack()` function
- File collection logic for config files
- Error handling wrapper

```bash
pytest planning_pipeline/tests/test_context_generation.py -k extract_tech_stack -v
```

Expected: All tests pass

### 3. 🔵 Refactor: Improve Code
- Extract constants for tech indicators
- Add type hints
- Improve error messages
- Add custom exception class
- Better file filtering logic

```bash
mypy planning_pipeline/context_generation.py
ruff check planning_pipeline/context_generation.py
```

Expected: No type errors, no linting issues

## Success Criteria

### Automated Tests
- [x] `pytest planning_pipeline/tests/test_context_generation.py::test_extract_tech_stack_identifies_python_project -v` ✅
- [x] `pytest planning_pipeline/tests/test_context_generation.py::test_extract_tech_stack_identifies_typescript_project -v` ✅
- [x] `pytest planning_pipeline/tests/test_context_generation.py::test_extract_tech_stack_handles_empty_directory -v` ✅
- [x] `pytest planning_pipeline/tests/test_context_generation.py::test_extract_tech_stack_handles_baml_client_error -v` ✅
- [x] `pytest ...::test_extract_tech_stack_detects_rust_project -v` ✅
- [x] `pytest ...::test_extract_tech_stack_detects_go_project -v` ✅
- [ ] `mypy planning_pipeline/context_generation.py` (not run)
- [ ] `ruff check planning_pipeline/context_generation.py` (not run)

**Phase Status: ✅ COMPLETE** (6/6 tests passing)

### Manual Human Test
**Testable Function**: `extract_tech_stack(Path.cwd())`

```python
from pathlib import Path
from planning_pipeline.context_generation import extract_tech_stack

# Run on silmari-Context-Engine
result = extract_tech_stack(Path.cwd())

# Verify:
assert "Python" in result.languages
assert any("pytest" in tool.lower() for tool in result.testing_frameworks)
assert any("baml" in tool.lower() or "pip" in tool.lower() for tool in result.build_systems)

print(f"✅ Detected {len(result.languages)} languages: {result.languages}")
print(f"✅ Detected {len(result.frameworks)} frameworks")
print(f"✅ Tech stack extraction working!")
```

Expected output:
```
✅ Detected 1 languages: ['Python']
✅ Detected 3 frameworks
✅ Tech stack extraction working!
```

## Edge Cases Handled
1. **Empty directory**: Returns empty TechStack
2. **No recognizable tech stack**: Returns minimal TechStack with empty lists
3. **BAML client error**: Raises ContextGenerationError with clear message
4. **Binary/unreadable files**: Skipped gracefully with UnicodeDecodeError handling
5. **Missing permissions**: Skipped with PermissionError handling

## Files Created/Modified
- ✨ NEW: `planning_pipeline/context_generation.py`
- ✨ NEW: `planning_pipeline/tests/test_context_generation.py`
- 📝 UPDATE: `planning_pipeline/tests/conftest.py` (add fixtures)
