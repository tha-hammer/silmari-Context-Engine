# Phase 4: Helper Integration

## Overview

Create `baml_helpers.py` module that wraps BAML client functions, providing a clean Python API for the pipeline to use.

## Dependencies

- **Requires**: Phase 3 (Parsing Functions) - BAML functions must be callable
- **Blocks**: Phase 5 (Steps Integration)

## Behaviors Covered

- Behavior 9: BAML Parser Integration in helpers.py

## Changes Required

### New Files

| File | Purpose |
|------|---------|
| `planning_pipeline/baml_helpers.py:1-30` | BAML parsing wrapper functions |
| `planning_pipeline/tests/test_baml_helpers.py` | Tests for helper integration |

### File Contents

**planning_pipeline/baml_helpers.py**
```python
"""BAML-powered parsing helpers for structured LLM output extraction."""

from typing import Optional
from baml_client import b
from baml_client.types import ResearchOutput, PlanOutput, PhaseDecompositionOutput


def parse_research_output(raw_output: str) -> ResearchOutput:
    """Parse research output using BAML for type-safe extraction.

    Args:
        raw_output: Raw text output from Claude research step

    Returns:
        Typed ResearchOutput with research_path, open_questions, summary
    """
    return b.ParseResearchOutput(raw_output=raw_output)


def parse_plan_output(raw_output: str) -> PlanOutput:
    """Parse plan output using BAML for type-safe extraction.

    Args:
        raw_output: Raw text output from Claude planning step

    Returns:
        Typed PlanOutput with plan_path, phases, estimated_complexity
    """
    return b.ParsePlanOutput(raw_output=raw_output)


def parse_phase_files(raw_output: str) -> PhaseDecompositionOutput:
    """Parse phase decomposition output using BAML.

    Args:
        raw_output: Raw text output from phase decomposition step

    Returns:
        Typed PhaseDecompositionOutput with phase_files, overview_file
    """
    return b.ParsePhaseFiles(raw_output=raw_output)
```

## TDD Cycle

### Red: Write Failing Tests

```bash
pytest planning_pipeline/tests/test_baml_helpers.py -v
```

Expected failures:
- `test_parse_research_output_exists` - module doesn't exist
- `test_parse_research_returns_typed_object` - function not implemented
- `test_parse_plan_output_exists` - function not implemented
- `test_parse_phase_files_exists` - function not implemented

### Green: Implement

1. Create `planning_pipeline/baml_helpers.py`
2. Import and wrap BAML client functions
3. Add type hints for IDE support

### Refactor

- Add docstrings
- Consider adding logging

## Success Criteria

### Automated
- [ ] `pytest planning_pipeline/tests/test_baml_helpers.py -v` passes
- [ ] All helper functions are callable
- [ ] Return types match BAML-generated types

### Manual
- [ ] `from planning_pipeline.baml_helpers import parse_research_output` works
- [ ] IDE autocomplete works for helper functions
- [ ] Return types show correct fields in IDE

## Testable Function

**End of Phase Test**: After this phase, the following should succeed:

```python
from planning_pipeline.baml_helpers import (
    parse_research_output,
    parse_plan_output,
    parse_phase_files
)
from baml_client.types import ResearchOutput, PlanOutput, PhaseDecompositionOutput

# Test 1: parse_research_output
sample_research = '''
Research complete!
Created: thoughts/shared/research/2026-01-01-test.md

## Open Questions
- Question 1?
- Question 2?
'''
result = parse_research_output(sample_research)
assert isinstance(result, ResearchOutput)
assert result.research_path is not None

# Test 2: parse_plan_output
sample_plan = '''
Plan created!
Path: thoughts/shared/plans/2026-01-01-test/00-overview.md

## Phase 1: Setup
Success Criteria: Tests pass

Complexity: low
'''
result = parse_plan_output(sample_plan)
assert isinstance(result, PlanOutput)

# Test 3: parse_phase_files
sample_files = '''
Created:
- thoughts/shared/plans/test/00-overview.md
- thoughts/shared/plans/test/01-setup.md
'''
result = parse_phase_files(sample_files)
assert isinstance(result, PhaseDecompositionOutput)
```
