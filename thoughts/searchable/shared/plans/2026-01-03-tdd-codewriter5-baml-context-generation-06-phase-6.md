# Phase 6: Full Pipeline Integration

## Overview
Integrate `ContextGenerationStep` into the main `Pipeline` class as step 2.5, executing after requirement decomposition and before step decomposition, with proper configuration and ordering.

## Dependencies
**Requires**:
- Phase 4 complete (`ContextGenerationStep` implemented)
- Phase 5 complete (`WorkflowContext` extended)
- Existing pipeline structure in `planning_pipeline/pipeline.py`

**Blocks**: None (final phase)

## Changes Required

### Update: `planning_pipeline/pipeline.py`
**Modify Pipeline class**

Changes to `Pipeline`:
- Add import: `from planning_pipeline.context_generation import ContextGenerationStep`
- Update `_build_steps()` method to insert ContextGenerationStep
- Add step between RequirementDecompositionStep and StepDecompositionStep
- Add conditional logic for `enable_context_generation` config flag
- Update logging for new step

### Update: `planning_pipeline/pipeline.py` (PipelineConfig)
**Add configuration fields**

New fields in `PipelineConfig`:
- `enable_context_generation: bool = True`
- `context_max_files: int = 100`
- `context_exclude_patterns: Optional[Set[str]] = None`

### Update: `planning_pipeline/tests/test_pipeline.py`
**Add pipeline integration tests**

New test cases:
- `test_pipeline_includes_context_generation_step`
- `test_pipeline_context_generation_runs_after_requirement_decomposition`
- `test_pipeline_step_ordering_correct`
- `test_pipeline_skips_context_generation_when_disabled`

### New: Integration and E2E Tests
**Add comprehensive integration tests**

Test cases in `test_pipeline.py`:
- `test_full_context_generation_integration` - Full context flow
- `test_e2e_pipeline_with_context_generation` - Complete pipeline run

## Implementation Steps

### 1. 🔴 Red: Write Failing Tests
```bash
# Add tests to test_pipeline.py
pytest planning_pipeline/tests/test_pipeline.py::test_pipeline_includes_context_generation_step -v
```

Expected: `AssertionError: assert 'ContextGenerationStep' in step_types`

### 2. 🟢 Green: Minimal Implementation
Update `planning_pipeline/pipeline.py`:
- Import ContextGenerationStep
- Add to _build_steps() between decomposition steps
- Add config fields to PipelineConfig
- Add conditional logic for enabling/disabling

```bash
pytest planning_pipeline/tests/test_pipeline.py -k context_generation -v
```

Expected: All context_generation tests pass

### 3. 🔵 Refactor: Improve Code
- Extract `_is_context_generation_enabled()` method
- Improve logging for step execution
- Better error handling in run() method
- Clean up _build_steps() logic
- Add comprehensive docstrings

```bash
pytest planning_pipeline/tests/test_pipeline.py -v
pytest planning_pipeline/tests/ -v  # All tests
mypy planning_pipeline/
```

Expected: All tests pass, no type errors

## Success Criteria

### Automated Tests
- [ ] `pytest planning_pipeline/tests/test_pipeline.py::test_pipeline_includes_context_generation_step -v` ✅
- [ ] `pytest planning_pipeline/tests/test_pipeline.py::test_pipeline_context_generation_runs_after_requirement_decomposition -v` ✅
- [ ] `pytest planning_pipeline/tests/test_pipeline.py::test_pipeline_step_ordering_correct -v` ✅
- [ ] `pytest planning_pipeline/tests/test_pipeline.py::test_pipeline_skips_context_generation_when_disabled -v` ✅
- [ ] `pytest planning_pipeline/tests/test_pipeline.py::test_full_context_generation_integration -v` ✅
- [ ] `pytest planning_pipeline/tests/test_pipeline.py::test_e2e_pipeline_with_context_generation -v` ✅
- [ ] `pytest planning_pipeline/tests/ -v` ✅ (all pipeline tests)
- [ ] `mypy planning_pipeline/` ✅
- [ ] `ruff check planning_pipeline/` ✅

### Manual Human Test
**Testable Function**: `Pipeline.run()`

```python
from pathlib import Path
from planning_pipeline.pipeline import Pipeline, PipelineConfig, WorkflowContext

# Configure pipeline with context generation
config = PipelineConfig(
    enable_context_generation=True,
    context_max_files=100,
    output_dir="output"
)

# Create pipeline
pipeline = Pipeline(config)

# Verify step ordering
step_names = [type(step).__name__ for step in pipeline.steps]
print(f"Pipeline steps: {step_names}")

assert 'RequirementDecompositionStep' in step_names
assert 'ContextGenerationStep' in step_names
assert 'StepDecompositionStep' in step_names

# Verify order
decomp_idx = step_names.index('RequirementDecompositionStep')
context_idx = step_names.index('ContextGenerationStep')
steps_idx = step_names.index('StepDecompositionStep')

assert decomp_idx < context_idx < steps_idx, "Steps in wrong order!"

print(f"✅ Step ordering correct: {decomp_idx} < {context_idx} < {steps_idx}")

# Run full pipeline
initial_context = WorkflowContext(
    checkpoint_id="e2e-test",
    project_path=Path.cwd(),
    requirement="Add user authentication feature",
    decomposed_requirements=[]
)

print(f"\n🚀 Running full pipeline...")
final_context = pipeline.run(initial_context)

# Verify all steps executed
assert final_context.tech_stack is not None, "Should have tech_stack"
assert final_context.file_groups is not None, "Should have file_groups"
assert len(final_context.decomposed_requirements) > 0, "Should have decomposed requirements"

print(f"\n✅ Pipeline execution complete!")
print(f"✅ Tech stack: {final_context.tech_stack.languages}")
print(f"✅ File groups: {len(final_context.file_groups.groups)} groups")
print(f"✅ Decomposed requirements: {len(final_context.decomposed_requirements)} items")

# Verify output files
output_dir = Path("output") / Path.cwd().name / "groups"
assert output_dir.exists(), "Output directory should exist"
assert (output_dir / "tech_stack.json").exists(), "tech_stack.json should exist"
assert (output_dir / "file_groups.json").exists(), "file_groups.json should exist"

print(f"✅ Output files created at: {output_dir}")
print(f"\n🎉 Full pipeline integration working!")
```

Expected output:
```
Pipeline steps: ['RequirementDecompositionStep', 'ContextGenerationStep', 'StepDecompositionStep', 'CheckpointStep']
✅ Step ordering correct: 0 < 1 < 2

🚀 Running full pipeline...
INFO:planning_pipeline.pipeline:Executing step 1/4: RequirementDecompositionStep
INFO:planning_pipeline.pipeline:Executing step 2/4: ContextGenerationStep
INFO:planning_pipeline.context_generation:Generating BAML context for project: silmari-Context-Engine
INFO:planning_pipeline.context_generation:Context saved to: output/silmari-context-engine/groups
INFO:planning_pipeline.pipeline:Executing step 3/4: StepDecompositionStep
INFO:planning_pipeline.pipeline:Executing step 4/4: CheckpointStep
INFO:planning_pipeline.pipeline:Pipeline execution complete

✅ Pipeline execution complete!
✅ Tech stack: ['Python']
✅ File groups: 3 groups
✅ Decomposed requirements: 5 items
✅ Output files created at: output/silmari-context-engine/groups

🎉 Full pipeline integration working!
```

### Test Disabled Configuration
```python
# Test with context generation disabled
config_disabled = PipelineConfig(enable_context_generation=False)
pipeline_disabled = Pipeline(config_disabled)

step_names = [type(step).__name__ for step in pipeline_disabled.steps]
assert 'ContextGenerationStep' not in step_names, "Should not include step when disabled"

print(f"✅ Pipeline correctly excludes step when disabled")

# Run pipeline without context generation
context = WorkflowContext(
    checkpoint_id="test-disabled",
    project_path=Path.cwd(),
    requirement="Test without context",
    decomposed_requirements=[]
)

result = pipeline_disabled.run(context)
assert result.tech_stack is None, "Should not generate context when disabled"
assert result.file_groups is None, "Should not generate context when disabled"

print(f"✅ Disabled configuration working correctly")
```

### Verify Checkpoint Persistence
```python
import json

# After running pipeline, check checkpoint file
checkpoint_files = list(Path(".workflow-checkpoints").glob("*.json"))
if checkpoint_files:
    checkpoint_data = json.loads(checkpoint_files[0].read_text())

    # Should include BAML context
    assert "tech_stack" in checkpoint_data, "Checkpoint should include tech_stack"
    assert "file_groups" in checkpoint_data, "Checkpoint should include file_groups"

    print(f"✅ Checkpoint includes BAML context")
    print(f"✅ Checkpoint location: {checkpoint_files[0]}")
else:
    print("⚠️  No checkpoint files found (may need CheckpointStep implementation)")
```

## Edge Cases Handled
1. **Step ordering**: ContextGenerationStep always between decomposition steps
2. **Disabled config**: Step not added to pipeline when disabled
3. **Error in step**: Pipeline continues, logs warning
4. **Missing config fields**: Defaults used (enabled=True, max_files=100)
5. **Checkpoint serialization**: BAML context persisted to checkpoint

## Pipeline Execution Flow
```
1. RequirementDecompositionStep
   ↓ (decomposed_requirements populated)
2. ContextGenerationStep ← NEW
   ↓ (tech_stack, file_groups populated)
3. StepDecompositionStep
   ↓ (can use tech_stack and file_groups for better planning)
4. CheckpointStep
   ↓ (saves context with BAML data)
```

## Configuration Example
```python
config = PipelineConfig(
    # Existing config
    requirement="Build user authentication",
    output_dir="output",

    # New context generation config
    enable_context_generation=True,      # Enable/disable step
    context_max_files=100,                # Limit files analyzed
    context_exclude_patterns={"tmp"}      # Additional excludes
)
```

## Integration Test Structure
```python
def test_e2e_pipeline_with_context_generation(tmp_path):
    """E2E: Full pipeline run with real project structure."""
    # Setup
    project = create_test_project(tmp_path)
    config = create_test_config(tmp_path)
    pipeline = Pipeline(config)

    # Execute
    result = pipeline.run(initial_context)

    # Verify
    assert_context_generated(result)
    assert_files_created(tmp_path)
    assert_checkpoint_saved(tmp_path)
```

## Files Modified
- 📝 UPDATE: `planning_pipeline/pipeline.py` (integrate ContextGenerationStep)
- 📝 UPDATE: `planning_pipeline/tests/test_pipeline.py` (add integration tests)

## Final Verification Checklist
- [x] Run all tests: `pytest planning_pipeline/tests/ -v` (34/34 pass)
- [ ] Type check: `mypy planning_pipeline/`
- [ ] Lint: `ruff check planning_pipeline/`
- [ ] Manual E2E test on real project
- [x] Verify step ordering in logs (Step 4/7: CONTEXT GENERATION)
- [x] Verify context available to downstream steps
- [ ] Verify checkpoint includes BAML data
- [x] Test with enabled and disabled configurations

## Implementation Notes (Adapted)
The plan was adapted to work with the existing function-based step architecture:
- Used `step_context_generation()` function instead of class-based `ContextGenerationStep`
- Integrated directly into `PlanningPipeline.run()` method after requirement decomposition
- Updated step numbering from 6 to 7 steps total
- Context generation is non-blocking (errors log warning but don't halt pipeline)
