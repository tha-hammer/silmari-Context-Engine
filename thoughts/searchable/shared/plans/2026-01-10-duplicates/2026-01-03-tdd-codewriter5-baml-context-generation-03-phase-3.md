# Phase 3: Context Persistence

## Overview
Implement the `save_context_to_disk()` function that saves generated TechStack and FileGroupAnalysis data to the output directory in JSON format with proper structure and sanitization.

## Dependencies
**Requires**:
- Phase 1 complete (TechStack generation)
- Phase 2 complete (FileGroupAnalysis generation)

**Blocks**: Phase 4 (step needs to persist context)

## Changes Required

### Update: `planning_pipeline/context_generation.py`
**Append after file group functions** (lines ~500-718)

New functions:
- `save_context_to_disk(project_name: str, tech_stack: TechStack, file_groups: FileGroupAnalysis, output_root: Path) -> Path` (lines ~652-691)
- `_save_json(file_path: Path, data: Dict[str, Any]) -> None` (lines ~694-699)
- `_sanitize_project_name(name: str) -> str` (lines ~702-717)

New imports:
- `import json`
- `import re`
- `from typing import Any, Dict`

### Update: `planning_pipeline/tests/test_context_generation.py`
**Append after file group tests** (lines ~334-576)

New test cases:
- `test_save_context_creates_output_directory`
- `test_save_context_overwrites_existing_files`
- `test_save_context_handles_special_characters_in_project_name`

### Update: `planning_pipeline/tests/conftest.py`
**Append after Phase 2 fixtures**

New fixtures:
- `sample_tech_stack()` - Sample TechStack object
- `sample_file_groups()` - Sample FileGroupAnalysis object (if not already added)

## Implementation Steps

### 1. 🔴 Red: Write Failing Tests
```bash
# Add tests to existing test file
pytest planning_pipeline/tests/test_context_generation.py::test_save_context_creates_output_directory -v
```

Expected: `AttributeError: module 'planning_pipeline.context_generation' has no attribute 'save_context_to_disk'`

### 2. 🟢 Green: Minimal Implementation
Add to `planning_pipeline/context_generation.py`:
- Basic `save_context_to_disk()` function
- Directory creation with `mkdir(parents=True, exist_ok=True)`
- JSON serialization with model_dump()
- Project name sanitization

```bash
pytest planning_pipeline/tests/test_context_generation.py -k save_context -v
```

Expected: All save_context tests pass

### 3. 🔵 Refactor: Improve Code
- Extract `_save_json()` helper
- Improve sanitization logic (lowercase, consecutive hyphens)
- Add UTF-8 encoding
- Add newline at end of JSON files
- Better error messages in ContextGenerationError

```bash
pytest planning_pipeline/tests/test_context_generation.py -v  # All tests
mypy planning_pipeline/context_generation.py
```

Expected: All tests pass, no type errors

## Success Criteria

### Automated Tests
- [x] `pytest ...::test_save_context_creates_output_files -v` ✅
- [x] `pytest ...::test_save_context_writes_valid_json -v` ✅
- [x] `pytest ...::test_save_context_creates_output_directory -v` ✅
- [x] `pytest ...::test_save_context_handles_special_characters -v` ✅
- [ ] `mypy planning_pipeline/context_generation.py` (not run)

**Phase Status: ✅ COMPLETE** (4/4 tests passing)

### Manual Human Test
**Testable Function**: `save_context_to_disk()`

```python
from pathlib import Path
from planning_pipeline.context_generation import (
    extract_tech_stack,
    analyze_file_groups,
    save_context_to_disk
)

# Generate context
project_path = Path.cwd()
tech_stack = extract_tech_stack(project_path)
file_groups = analyze_file_groups(project_path)

# Save to disk
output_root = Path("output")
groups_dir = save_context_to_disk(
    project_name=project_path.name,
    tech_stack=tech_stack,
    file_groups=file_groups,
    output_root=output_root
)

# Verify files exist
assert groups_dir.exists(), "Groups directory should exist"
assert (groups_dir / "tech_stack.json").exists(), "tech_stack.json should exist"
assert (groups_dir / "file_groups.json").exists(), "file_groups.json should exist"

# Verify JSON is valid
import json
tech_stack_data = json.loads((groups_dir / "tech_stack.json").read_text())
assert "languages" in tech_stack_data, "Should have languages field"
assert "frameworks" in tech_stack_data, "Should have frameworks field"

file_groups_data = json.loads((groups_dir / "file_groups.json").read_text())
assert "groups" in file_groups_data, "Should have groups field"

print(f"✅ Files saved to: {groups_dir}")
print(f"✅ tech_stack.json: {(groups_dir / 'tech_stack.json').stat().st_size} bytes")
print(f"✅ file_groups.json: {(groups_dir / 'file_groups.json').stat().st_size} bytes")
print(f"✅ Context persistence working!")
```

Expected output:
```
✅ Files saved to: output/silmari-Context-Engine/groups
✅ tech_stack.json: 287 bytes
✅ file_groups.json: 1543 bytes
✅ Context persistence working!
```

### Verify Directory Structure
```bash
tree output/
```

Expected:
```
output/
└── silmari-context-engine/
    └── groups/
        ├── tech_stack.json
        └── file_groups.json
```

### Verify JSON Format
```bash
cat output/silmari-context-engine/groups/tech_stack.json | jq .
```

Expected: Properly formatted, indented JSON with languages, frameworks, etc.

## Edge Cases Handled
1. **Output directory doesn't exist**: Creates with `parents=True`
2. **Duplicate runs**: Overwrites existing files
3. **Special characters in project name**: Sanitized to `my-project-name` format
4. **Empty project name**: Returns `unnamed-project`
5. **Unicode in data**: Handled with `ensure_ascii=False`
6. **Serialization errors**: Wrapped in ContextGenerationError

## Output Structure
```
output_root/
  {sanitized-project-name}/
    groups/
      tech_stack.json      # TechStack serialized
      file_groups.json     # FileGroupAnalysis serialized
```

## Files Modified
- 📝 UPDATE: `planning_pipeline/context_generation.py` (add persistence functions)
- 📝 UPDATE: `planning_pipeline/tests/test_context_generation.py` (add tests)
- 📝 UPDATE: `planning_pipeline/tests/conftest.py` (ensure fixtures exist)
