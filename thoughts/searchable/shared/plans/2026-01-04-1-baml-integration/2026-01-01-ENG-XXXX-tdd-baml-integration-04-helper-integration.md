# Phase 4: Helper Integration

## Overview

Create Python wrapper functions in `baml_helpers.py` that expose BAML parsing functions with a clean interface. This layer provides the API that step functions will call.

**Behaviors Covered**: 9
**Human-Testable Function**: `from planning_pipeline.baml_helpers import parse_research_output` works and `parse_research_output(text)` returns a typed `ResearchOutput`

## Dependencies

- **Requires**: Phase 3 (BAML Functions) - BAML functions must exist in generated client
- **Blocks**: Phase 5 (Steps Integration)

## Changes Required

### Behavior 9: BAML Helper Functions

| File | Line | Change Description |
|------|------|-------------------|
| `planning_pipeline/baml_helpers.py` | NEW:1-35 | Create helper wrapper module |

**Test File**: `planning_pipeline/tests/test_baml_helpers.py`

```python
class TestBAMLHelperIntegration:
    """Behavior 9: BAML parsing in helpers module."""

    @pytest.fixture
    def sample_research_output(self):
        """Sample Claude output from research step."""
        return '''
Research complete!
Created: thoughts/shared/research/2026-01-01-test.md

## Open Questions
- Question 1?
- Question 2?
'''

    def test_parse_research_output_exists(self):
        """Given helpers module, parse_research_output function exists."""
        # Imports: from planning_pipeline.baml_helpers import parse_research_output
        # Checks: callable(parse_research_output)

    def test_parse_research_returns_typed_object(self, sample_research_output):
        """Given Claude output, returns ResearchOutput object."""
        # Imports: from baml_client.types import ResearchOutput
        # Calls: parse_research_output(sample_research_output)
        # Verifies: isinstance(result, ResearchOutput)

    def test_parse_plan_output_exists(self):
        """Given helpers module, parse_plan_output function exists."""
        # Imports: from planning_pipeline.baml_helpers import parse_plan_output

    def test_parse_phase_files_exists(self):
        """Given helpers module, parse_phase_files function exists."""
        # Imports: from planning_pipeline.baml_helpers import parse_phase_files
```

**Implementation**: `planning_pipeline/baml_helpers.py`

```python
"""BAML-powered parsing helpers for structured LLM output extraction."""

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

## Success Criteria

### Automated Tests
```bash
# Red phase - tests should fail (module doesn't exist)
pytest planning_pipeline/tests/test_baml_helpers.py -v

# Green phase - after implementation
pytest planning_pipeline/tests/test_baml_helpers.py -v
```

### Manual Verification
- [ ] `from planning_pipeline.baml_helpers import parse_research_output` works in REPL
- [ ] `parse_research_output("sample text")` returns `ResearchOutput` instance
- [ ] `parse_plan_output("sample text")` returns `PlanOutput` instance
- [ ] `parse_phase_files("sample text")` returns `PhaseDecompositionOutput` instance
- [ ] IDE shows correct type hints for function parameters and return values

## Implementation Steps

1. Create `planning_pipeline/baml_helpers.py`
2. Add `parse_research_output` function
3. Add `parse_plan_output` function
4. Add `parse_phase_files` function
5. Run tests to verify all functions work

## Module Structure

```
planning_pipeline/
├── __init__.py
├── helpers.py           # Original regex helpers (unchanged)
├── baml_helpers.py      # NEW: BAML wrapper functions
└── tests/
    ├── test_helpers.py       # Original tests (unchanged)
    └── test_baml_helpers.py  # NEW: Behavior 9 tests
```

## Comparison with Original helpers.py

| Original Function | BAML Equivalent | Key Difference |
|------------------|-----------------|----------------|
| `extract_file_path(text)` | `parse_research_output(text).research_path` | Typed return |
| `extract_list(text, section)` | `parse_research_output(text).open_questions` | Typed list |
| Multiple regex calls | Single BAML call | Atomic parsing |

## Rollback Plan

If issues arise:
1. Remove `planning_pipeline/baml_helpers.py`
2. Remove `planning_pipeline/tests/test_baml_helpers.py`
3. Existing code continues using `helpers.py`
