# Phase 5: WorkflowContext Extension

## Overview
Extend the `WorkflowContext` dataclass to support BAML-generated context fields (tech_stack and file_groups) with proper serialization/deserialization for checkpoint persistence.

## Dependencies
**Requires**:
- BAML types (`TechStack`, `FileGroupAnalysis`) available
- Existing `WorkflowContext` in `planning_pipeline/pipeline.py`

**Blocks**: Phase 6 (pipeline needs extended context)

## Changes Required

### Update: `planning_pipeline/pipeline.py`
**Modify WorkflowContext dataclass** (lines vary by existing implementation)

Changes to `WorkflowContext`:
- Add import: `from baml_client.types import TechStack, FileGroupAnalysis`
- Add fields: `tech_stack: Optional[TechStack] = None`
- Add fields: `file_groups: Optional[FileGroupAnalysis] = None`
- Update `to_dict()` method to serialize BAML types
- Update `from_dict()` classmethod to deserialize BAML types
- Add docstring explaining BAML fields

### New File: `planning_pipeline/tests/test_pipeline.py` OR update existing
**Lines**: Depends on if file exists

New test cases:
- `test_workflow_context_supports_tech_stack_field`
- `test_workflow_context_supports_file_groups_field`
- `test_workflow_context_serializes_with_baml_types`
- `test_workflow_context_handles_none_baml_fields`

## Implementation Steps

### 1. 🔴 Red: Write Failing Tests
```bash
# Create or update test_pipeline.py
pytest planning_pipeline/tests/test_pipeline.py::test_workflow_context_supports_tech_stack_field -v
```

Expected: `TypeError: __init__() got an unexpected keyword argument 'tech_stack'`

### 2. 🟢 Green: Minimal Implementation
Update `planning_pipeline/pipeline.py`:
- Add BAML type imports
- Add optional tech_stack and file_groups fields
- Update to_dict() to handle BAML types
- Update from_dict() to reconstruct BAML types

```bash
pytest planning_pipeline/tests/test_pipeline.py -k workflow_context -v
```

Expected: All workflow_context tests pass

### 3. 🔵 Refactor: Improve Code
- Add comprehensive docstrings
- Improve serialization with better None handling
- Add type hints to methods
- Document backward compatibility behavior
- Clean up from_dict() logic

```bash
pytest planning_pipeline/tests/test_pipeline.py -v
mypy planning_pipeline/pipeline.py
```

Expected: All tests pass, no type errors

## Success Criteria

**Phase Status: ⏭️ SKIPPED (N/A)**

This phase was designed for a class-based architecture with `WorkflowContext` dataclass,
but the actual implementation uses:
- Function-based steps (`step_context_generation()`) returning dicts
- No `WorkflowContext` dataclass exists in the codebase
- Results are stored in `results["steps"]["context_generation"]` dict

The `step_context_generation()` function already returns a dict with `tech_stack` and
`file_groups` keys, which serves the same purpose as extending WorkflowContext.

### Original Tests (Not Applicable)
- [ ] `pytest planning_pipeline/tests/test_pipeline.py::test_workflow_context_supports_tech_stack_field -v`
- [ ] `pytest planning_pipeline/tests/test_pipeline.py::test_workflow_context_supports_file_groups_field -v`
- [ ] `pytest planning_pipeline/tests/test_pipeline.py::test_workflow_context_serializes_with_baml_types -v`
- [ ] `pytest planning_pipeline/tests/test_pipeline.py::test_workflow_context_handles_none_baml_fields -v`

### Manual Human Test
**Testable Function**: `WorkflowContext.to_dict()` / `WorkflowContext.from_dict()`

```python
from pathlib import Path
import json
from planning_pipeline.pipeline import WorkflowContext
from planning_pipeline.context_generation import extract_tech_stack, analyze_file_groups

# Create context with BAML data
project_path = Path.cwd()
tech_stack = extract_tech_stack(project_path)
file_groups = analyze_file_groups(project_path)

context = WorkflowContext(
    checkpoint_id="test-serialization",
    project_path=project_path,
    requirement="Test serialization",
    decomposed_requirements=["req1", "req2"],
    tech_stack=tech_stack,
    file_groups=file_groups
)

# Test serialization
serialized = context.to_dict()
assert serialized["tech_stack"] is not None, "Should serialize tech_stack"
assert serialized["file_groups"] is not None, "Should serialize file_groups"
assert "languages" in serialized["tech_stack"], "Should have languages"

# Test JSON round-trip
json_str = json.dumps(serialized, indent=2)
print(f"✅ Serialized to {len(json_str)} bytes of JSON")

# Test deserialization
loaded_dict = json.loads(json_str)
loaded_context = WorkflowContext.from_dict(loaded_dict)

assert loaded_context.tech_stack is not None, "Should deserialize tech_stack"
assert loaded_context.file_groups is not None, "Should deserialize file_groups"
assert loaded_context.tech_stack.languages == tech_stack.languages, "Languages should match"
assert len(loaded_context.file_groups.groups) == len(file_groups.groups), "Groups should match"

print(f"✅ Deserialized successfully")
print(f"✅ Tech stack: {loaded_context.tech_stack.languages}")
print(f"✅ File groups: {len(loaded_context.file_groups.groups)} groups")
print(f"✅ Serialization working!")
```

Expected output:
```
✅ Serialized to 2847 bytes of JSON
✅ Deserialized successfully
✅ Tech stack: ['Python']
✅ File groups: 3 groups
✅ Serialization working!
```

### Test Backward Compatibility
```python
# Test loading old checkpoint without BAML fields
old_checkpoint = {
    "checkpoint_id": "old-checkpoint",
    "project_path": str(Path.cwd()),
    "requirement": "Old requirement",
    "decomposed_requirements": []
    # No tech_stack or file_groups
}

loaded = WorkflowContext.from_dict(old_checkpoint)
assert loaded.tech_stack is None, "Should handle missing tech_stack"
assert loaded.file_groups is None, "Should handle missing file_groups"
assert loaded.checkpoint_id == "old-checkpoint", "Should load other fields"

print(f"✅ Backward compatibility verified")
```

### Test None Values
```python
# Test with explicit None
context_none = WorkflowContext(
    checkpoint_id="none-test",
    project_path=Path.cwd(),
    requirement="Test None",
    decomposed_requirements=[],
    tech_stack=None,
    file_groups=None
)

serialized_none = context_none.to_dict()
assert serialized_none["tech_stack"] is None
assert serialized_none["file_groups"] is None

loaded_none = WorkflowContext.from_dict(serialized_none)
assert loaded_none.tech_stack is None
assert loaded_none.file_groups is None

print(f"✅ None values handled correctly")
```

## Edge Cases Handled
1. **None values**: Serialized as null, deserialized as None
2. **Missing fields in dict**: from_dict() handles with .get()
3. **Backward compatibility**: Old checkpoints without BAML fields load successfully
4. **Type reconstruction**: BAML Pydantic models reconstructed from dicts
5. **Nested objects**: FileGroup objects within FileGroupAnalysis handled

## Serialization Format
```json
{
  "checkpoint_id": "test",
  "project_path": "/path/to/project",
  "requirement": "Build feature",
  "decomposed_requirements": ["req1", "req2"],
  "tech_stack": {
    "languages": ["Python"],
    "frameworks": ["pytest"],
    "testing_frameworks": ["pytest"],
    "build_systems": ["pip"]
  },
  "file_groups": {
    "groups": [
      {
        "name": "planning_pipeline",
        "files": ["planning_pipeline/pipeline.py"],
        "purpose": "Core pipeline orchestration"
      }
    ]
  }
}
```

## Files Modified
- 📝 UPDATE: `planning_pipeline/pipeline.py` (extend WorkflowContext)
- ✨ NEW or 📝 UPDATE: `planning_pipeline/tests/test_pipeline.py` (add context tests)
