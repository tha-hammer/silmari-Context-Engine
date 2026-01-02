# Phase 5: Pipeline Step Integration

## Overview

Create the pipeline step function that orchestrates all components: reads research file, runs decomposition, generates visualization, creates property test skeletons, and writes all outputs to disk.

## Dependencies

- **Requires**: Phase 1 (Data Models), Phase 2 (Visualization), Phase 3 (Property Generator), Phase 4 (BAML Decomposition)
- **Blocks**: None (final phase)

## Human-Testable Function

```python
# After implementation, verify with:
from pathlib import Path
from planning_pipeline.step_decomposition import step_requirement_decomposition

# Use existing research file
project_path = Path.cwd()
research_path = "thoughts/searchable/shared/research/2026-01-02-iterative-requirement-decomposition-with-visualization.md"

result = step_requirement_decomposition(
    project_path=project_path,
    research_path=research_path
)

if result["success"]:
    print(f"Hierarchy: {result['hierarchy_path']}")
    print(f"Diagram: {result['diagram_path']}")
    print(f"Tests: {result.get('tests_path', 'None')}")
else:
    print(f"Error: {result['error']}")
```

## Changes Required

### New Files

| File | Purpose |
|------|---------|
| `planning_pipeline/step_decomposition.py` | Pipeline step function |
| `planning_pipeline/tests/test_step_decomposition.py` | Integration tests |
| `planning_pipeline/tests/test_decomposition_e2e.py` | End-to-end tests |

### planning_pipeline/step_decomposition.py (new file)

```python
# planning_pipeline/step_decomposition.py:1-100

def step_requirement_decomposition(
    project_path: Path,
    research_path: str,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Execute requirement decomposition step.

    Pipeline position: step_research() → [this] → step_planning()

    Args:
        project_path: Root project path.
        research_path: Path to research document.
        output_dir: Optional custom output directory.

    Returns:
        Dict with:
        - success: bool
        - hierarchy_path: str (path to requirements_hierarchy.json)
        - diagram_path: str (path to requirements_diagram.mmd)
        - tests_path: str | None (path to property_tests_skeleton.py)
        - requirement_count: int
        - output_dir: str
        - error: str (if success=False)
    """

def _collect_acceptance_criteria(hierarchy: RequirementHierarchy) -> list:
    """Collect all acceptance criteria from hierarchy recursively."""
```

### planning_pipeline/tests/test_step_decomposition.py (new file)

```python
# planning_pipeline/tests/test_step_decomposition.py:1-100

class TestStepRequirementDecomposition:
    # Fixtures: temp_project, mock_decomposition

    # test_creates_hierarchy_json
    # test_creates_mermaid_diagram
    # test_creates_property_tests_skeleton
    # test_returns_error_for_missing_research
    # test_returns_error_when_decomposition_fails
```

### planning_pipeline/tests/test_decomposition_e2e.py (new file)

```python
# planning_pipeline/tests/test_decomposition_e2e.py:1-50

@pytest.mark.e2e
@pytest.mark.slow
class TestDecompositionE2E:
    # test_full_flow_with_real_research
```

## TDD Cycle

### Red Phase
```bash
pytest planning_pipeline/tests/test_step_decomposition.py -v
# Expected: ImportError (step_decomposition module doesn't exist)
```

### Green Phase
```bash
# Implement step_decomposition.py
pytest planning_pipeline/tests/test_step_decomposition.py -v
# Expected: All tests pass
```

### E2E Phase
```bash
# Run end-to-end tests with real files
pytest planning_pipeline/tests/test_decomposition_e2e.py -v -m e2e
# Expected: E2E tests pass
```

## Success Criteria

### Automated
- [x] `pytest planning_pipeline/tests/test_step_decomposition.py -v` passes
- [x] All output files created in correct locations
- [x] `python -c "import json; json.load(open('requirements_hierarchy.json'))"` succeeds
- [x] Mermaid file starts with `flowchart`

### Manual
- [x] Open `requirements_diagram.mmd` in Mermaid Live Editor - renders correctly
- [x] Open `property_tests_skeleton.py` - syntactically valid Python
- [x] Run step with real research file - produces meaningful output

## Output Structure

```
thoughts/shared/plans/2026-01-02-requirements/
├── requirements_hierarchy.json   # Full hierarchy with all metadata
├── requirements_diagram.mmd      # Mermaid flowchart
└── property_tests_skeleton.py    # Hypothesis test stubs (if acceptance criteria exist)
```

## Pipeline Integration

### Current Pipeline (planning_pipeline/steps.py)

```python
def step_research(project_path, feature_description):
    """Step 1: Research the codebase."""
    ...
    return {"success": True, "research_path": str(output_file)}

# NEW: Insert between research and planning
def step_requirement_decomposition(project_path, research_path):
    """Step 1.5: Decompose research into requirements."""
    ...
    return {"success": True, "hierarchy_path": ..., "diagram_path": ...}

def step_planning(project_path, research_path):
    """Step 2: Create implementation plan."""
    ...
```

### Optional: Modify steps.py

```python
# planning_pipeline/steps.py:640 (optional addition)
# from planning_pipeline.step_decomposition import step_requirement_decomposition
# Export for pipeline use
```

## Error Handling

| Error Condition | Response |
|----------------|----------|
| Research file not found | `{"success": False, "error": "Research file not found: {path}"}` |
| Read error | `{"success": False, "error": "Failed to read research file: {exception}"}` |
| Decomposition failure | Pass through error from `decompose_requirements()` |
| Write error | `{"success": False, "error": "Failed to write output: {exception}"}` |

## Implementation Notes

1. Default output dir: `{project}/thoughts/shared/plans/{date}-requirements/`
2. Create output directory with `mkdir(parents=True, exist_ok=True)`
3. Only generate property tests if acceptance criteria exist
4. Use generic class name "Implementation" for test skeleton
5. Include `requirement_count` in result for quick visibility
6. Preserve original research path in hierarchy metadata
