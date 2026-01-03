# Phase 2: File Group Analysis

## Overview
Implement the `analyze_file_groups()` function that uses BAML to organize project files into logical groups based on feature/responsibility, with configurable file limits and exclusion patterns.

## Dependencies
**Requires**:
- Phase 1 complete (shares same module)
- BAML client with `AnalyzeFileGroups` function

**Blocks**: Phase 3 (needs file groups data to save)

## Changes Required

### Update: `planning_pipeline/context_generation.py`
**Append after tech stack functions** (lines ~264-500)

New functions:
- `analyze_file_groups(project_path: Path, max_files: int, exclude_patterns: Set[str] | None) -> FileGroupAnalysis` (lines ~428-461)
- `_collect_file_structure(project_path: Path, config: FileCollectionConfig) -> str` (lines ~464-499)
- `FileCollectionConfig` dataclass (lines ~408-413)
- Constants: `DEFAULT_EXCLUDE_PATTERNS`, `DEFAULT_SOURCE_EXTENSIONS` (lines ~416-425)

### Update: `planning_pipeline/tests/test_context_generation.py`
**Append after tech stack tests** (lines ~122-333)

New test cases:
- `test_analyze_file_groups_identifies_feature_modules`
- `test_analyze_file_groups_handles_flat_structure`
- `test_analyze_file_groups_respects_file_limits`

### Update: `planning_pipeline/tests/conftest.py`
**Append after Phase 1 fixtures**

New fixtures:
- `sample_file_groups()` - Sample FileGroupAnalysis for testing

## Implementation Steps

### 1. 🔴 Red: Write Failing Tests
```bash
# Add tests to existing test file
pytest planning_pipeline/tests/test_context_generation.py::test_analyze_file_groups_identifies_feature_modules -v
```

Expected: `AttributeError: module 'planning_pipeline.context_generation' has no attribute 'analyze_file_groups'`

### 2. 🟢 Green: Minimal Implementation
Add to `planning_pipeline/context_generation.py`:
- Basic `analyze_file_groups()` function
- File collection with max_files limit
- Exclude pattern filtering

```bash
pytest planning_pipeline/tests/test_context_generation.py -k file_groups -v
```

Expected: All file group tests pass

### 3. 🔵 Refactor: Improve Code
- Extract configuration dataclass
- Add default constants
- Improve file filtering logic
- Better tree structure generation
- Add custom exclude pattern support

```bash
pytest planning_pipeline/tests/test_context_generation.py -v  # All tests
mypy planning_pipeline/context_generation.py
```

Expected: All tests pass, no type errors

## Success Criteria

### Automated Tests
- [x] `pytest planning_pipeline/tests/test_context_generation.py::test_analyze_file_groups_identifies_feature_modules -v` ✅
- [x] `pytest planning_pipeline/tests/test_context_generation.py::test_analyze_file_groups_handles_flat_structure -v` ✅
- [x] `pytest planning_pipeline/tests/test_context_generation.py::test_analyze_file_groups_respects_file_limits -v` ✅
- [x] `pytest ...::test_analyze_file_groups_excludes_common_dirs -v` ✅
- [x] `pytest ...::test_analyze_file_groups_with_custom_excludes -v` ✅
- [ ] `mypy planning_pipeline/context_generation.py` (not run)

**Phase Status: ✅ COMPLETE** (5/5 tests passing)

### Manual Human Test
**Testable Function**: `analyze_file_groups(Path.cwd())`

```python
from pathlib import Path
from planning_pipeline.context_generation import analyze_file_groups

# Run on silmari-Context-Engine
result = analyze_file_groups(Path.cwd(), max_files=100)

# Verify:
assert len(result.groups) > 0, "Should identify at least one file group"

# Look for planning_pipeline group
pipeline_group = next((g for g in result.groups if "pipeline" in g.name.lower()), None)
assert pipeline_group is not None, "Should identify planning_pipeline as a group"
assert len(pipeline_group.files) > 0, "Group should contain files"
assert pipeline_group.purpose, "Group should have purpose description"

print(f"✅ Identified {len(result.groups)} file groups:")
for group in result.groups:
    print(f"  - {group.name}: {len(group.files)} files - {group.purpose[:50]}...")
print(f"✅ File group analysis working!")
```

Expected output:
```
✅ Identified 3 file groups:
  - planning_pipeline: 8 files - Core pipeline orchestration and workflow...
  - tests: 4 files - Test suite for pipeline functionality...
  - file_discovery: 2 files - Service for discovering project files...
✅ File group analysis working!
```

## Edge Cases Handled
1. **Single file project**: Returns single group
2. **Flat structure (no directories)**: Groups all files together
3. **Large file count**: Respects max_files limit
4. **Excluded directories**: Skips __pycache__, node_modules, .git, etc.
5. **Non-source files**: Filters to only source extensions
6. **Deep nesting**: Handles arbitrary directory depth
7. **Custom exclude patterns**: Merges with defaults

## Configuration Options
```python
analyze_file_groups(
    project_path=Path("/path/to/project"),
    max_files=100,  # Limit analyzed files
    exclude_patterns={"custom_dir", "tmp"}  # Additional excludes
)
```

## Files Modified
- 📝 UPDATE: `planning_pipeline/context_generation.py` (add file group functions)
- 📝 UPDATE: `planning_pipeline/tests/test_context_generation.py` (add tests)
- 📝 UPDATE: `planning_pipeline/tests/conftest.py` (add fixture)
