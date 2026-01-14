# Phase 6: Error Handling

## Overview

Add safe wrapper functions in `baml_helpers.py` that handle BAML parsing failures gracefully, returning structured error results instead of raising exceptions.

## Dependencies

- **Requires**: Phase 5 (Steps Integration) - basic parsing must work
- **Blocks**: Phase 7 (Pipeline Integration)

## Behaviors Covered

- Behavior 11: Error Handling for BAML Parsing Failures

## Changes Required

### Modified Files

| File | Line Range | Changes |
|------|------------|---------|
| `planning_pipeline/baml_helpers.py:35-70` | Add `ParseResult` dataclass and `*_safe` functions |
| `planning_pipeline/tests/test_baml_errors.py` | New test file for error handling |

### File Contents

**planning_pipeline/baml_helpers.py** (additions)
```python
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class ParseResult:
    """Generic result wrapper for BAML parsing."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


def parse_research_output_safe(raw_output: str) -> ParseResult:
    """Parse research output with error handling.

    Returns ParseResult with success=False on any error.
    """
    if not raw_output or not raw_output.strip():
        return ParseResult(
            success=False,
            error="Empty output provided"
        )

    try:
        result = b.ParseResearchOutput(raw_output=raw_output)
        return ParseResult(success=True, data=result)
    except Exception as e:
        return ParseResult(
            success=False,
            error=f"BAML parsing error: {str(e)}"
        )


def parse_plan_output_safe(raw_output: str) -> ParseResult:
    """Parse plan output with error handling.

    Returns ParseResult with success=False on any error.
    """
    if not raw_output or not raw_output.strip():
        return ParseResult(
            success=False,
            error="Empty output provided"
        )

    try:
        result = b.ParsePlanOutput(raw_output=raw_output)
        return ParseResult(success=True, data=result)
    except Exception as e:
        return ParseResult(
            success=False,
            error=f"BAML parsing error: {str(e)}"
        )


def parse_phase_files_safe(raw_output: str) -> ParseResult:
    """Parse phase files output with error handling.

    Returns ParseResult with success=False on any error.
    """
    if not raw_output or not raw_output.strip():
        return ParseResult(
            success=False,
            error="Empty output provided"
        )

    try:
        result = b.ParsePhaseFiles(raw_output=raw_output)
        return ParseResult(success=True, data=result)
    except Exception as e:
        return ParseResult(
            success=False,
            error=f"BAML parsing error: {str(e)}"
        )
```

## TDD Cycle

### Red: Write Failing Tests

```bash
pytest planning_pipeline/tests/test_baml_errors.py -v
```

Expected failures:
- `test_parse_research_handles_empty_output` - safe function doesn't exist
- `test_parse_research_handles_no_path` - not handling gracefully
- `test_baml_api_error_handled` - exceptions not caught

### Green: Implement

1. Add `ParseResult` dataclass to `baml_helpers.py`
2. Add `parse_research_output_safe` function
3. Add `parse_plan_output_safe` function
4. Add `parse_phase_files_safe` function
5. Handle empty input, API errors, and parsing failures

### Refactor

- Improve error message clarity
- Add specific error types if needed

## Success Criteria

### Automated
- [ ] `pytest planning_pipeline/tests/test_baml_errors.py -v` passes
- [ ] Empty input returns `ParseResult(success=False)`
- [ ] API errors are caught and returned in `ParseResult.error`
- [ ] No uncaught exceptions during parsing

### Manual
- [ ] Error messages are descriptive and actionable
- [ ] IDE shows `ParseResult` type hints correctly
- [ ] Errors include context about what failed

## Testable Function

**End of Phase Test**: After this phase, the following should succeed:

```python
from planning_pipeline.baml_helpers import (
    parse_research_output_safe,
    parse_plan_output_safe,
    parse_phase_files_safe,
    ParseResult
)

# Test 1: Empty input handling
result = parse_research_output_safe("")
assert result.success is False
assert result.error is not None
assert "empty" in result.error.lower()

# Test 2: Valid input returns data
valid_input = '''
Research complete!
Created: thoughts/shared/research/2026-01-01-test.md
Summary: Test research.
'''
result = parse_research_output_safe(valid_input)
assert result.success is True
assert result.data is not None
assert result.data.research_path is not None

# Test 3: Error contains details
result = parse_plan_output_safe("   ")  # Whitespace only
assert result.success is False
assert "empty" in result.error.lower()
```
