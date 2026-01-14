# Phase 3: Parsing Functions

## Overview

Define BAML functions that use Claude to parse raw text output into typed schemas: `ParseResearchOutput`, `ParsePlanOutput`, and `ParsePhaseFiles`.

## Dependencies

- **Requires**: Phase 2 (Schema Definitions) - schemas must exist
- **Blocks**: Phase 4 (Helper Integration)

## Behaviors Covered

- Behavior 6: ParseResearchOutput Function Definition
- Behavior 7: ParsePlanOutput Function Definition
- Behavior 8: ParsePhaseFiles Function Definition

## Changes Required

### New Files

| File | Purpose |
|------|---------|
| `baml_src/functions.baml` | BAML function definitions |
| `planning_pipeline/tests/test_baml_functions.py` | Tests for function behaviors |

### File Contents

**baml_src/functions.baml**
```baml
function ParseResearchOutput(raw_output: string) -> ResearchOutput {
  client ClaudeSonnet
  prompt #"
    Parse the following research output from Claude and extract structured information.

    Raw output:
    ---
    {{ raw_output }}
    ---

    Extract:
    1. research_path: The file path mentioned (starts with 'thoughts/')
    2. open_questions: Any questions listed under "Open Questions" section
    3. summary: A brief summary of the research findings

    If no open questions section exists, return an empty array.
    If no clear summary, extract the first 1-2 sentences after "Summary" or the main findings.

    {{ ctx.output_format }}
  "#
}

function ParsePlanOutput(raw_output: string) -> PlanOutput {
  client ClaudeSonnet
  prompt #"
    Parse the following plan output from Claude and extract structured information.

    Raw output:
    ---
    {{ raw_output }}
    ---

    Extract:
    1. plan_path: The file path mentioned (starts with 'thoughts/')
    2. phases: Each phase with number, name, dependencies, and success_criteria
    3. estimated_complexity: low, medium, or high

    For each phase, extract:
    - number: Sequential 1-indexed number
    - name: Phase name (e.g., "Setup", "Implementation")
    - dependencies: List of phase names this depends on
    - success_criteria: List of verification criteria

    {{ ctx.output_format }}
  "#
}

function ParsePhaseFiles(raw_output: string) -> PhaseDecompositionOutput {
  client ClaudeSonnet
  prompt #"
    Parse the following phase decomposition output and extract file paths.

    Raw output:
    ---
    {{ raw_output }}
    ---

    Extract:
    1. phase_files: All file paths mentioned (starting with 'thoughts/')
    2. overview_file: The file ending with '00-overview.md'

    Return paths in the order they appear. Include all .md files in the plan directory.

    {{ ctx.output_format }}
  "#
}
```

## TDD Cycle

### Red: Write Failing Tests

```bash
pytest planning_pipeline/tests/test_baml_functions.py -v
```

Expected failures:
- `test_parse_research_function_exists` - function not defined
- `test_parse_research_extracts_path` - can't parse
- `test_parse_research_extracts_questions` - can't extract questions
- `test_parse_research_extracts_summary` - can't extract summary
- `test_parse_research_handles_no_questions` - fails on empty
- `test_parse_plan_function_exists` - function not defined
- `test_parse_plan_extracts_path` - can't parse
- `test_parse_plan_extracts_phases` - can't extract phases
- `test_parse_plan_extracts_complexity` - can't extract complexity
- `test_parse_phase_files_function_exists` - function not defined
- `test_parse_phase_files_extracts_all` - can't extract files
- `test_parse_phase_files_identifies_overview` - can't identify overview

### Green: Implement

1. Create `baml_src/functions.baml` with all function definitions
2. Run `baml-cli generate`
3. Verify functions available via `from baml_client import b`

### Refactor

- Improve prompts for better extraction accuracy
- Add retry logic in prompts if needed

## Success Criteria

### Automated
- [ ] `pytest planning_pipeline/tests/test_baml_functions.py::TestParseResearchOutput -v` passes
- [ ] `pytest planning_pipeline/tests/test_baml_functions.py::TestParsePlanOutput -v` passes
- [ ] `pytest planning_pipeline/tests/test_baml_functions.py::TestParsePhaseFiles -v` passes

### Manual
- [ ] Functions return correct types in Python REPL
- [ ] IDE shows correct return type for `b.ParseResearchOutput`
- [ ] Parsing handles edge cases gracefully

## Testable Function

**End of Phase Test**: After this phase, the following should succeed:

```python
from baml_client import b
from baml_client.types import ResearchOutput, PlanOutput, PhaseDecompositionOutput

# Test 1: ParseResearchOutput
research_text = '''
Research complete!
Created: thoughts/shared/research/2026-01-01-test.md

## Open Questions
- What auth method?
- Which database?

## Summary
Analyzed authentication options.
'''
result = b.ParseResearchOutput(raw_output=research_text)
assert isinstance(result, ResearchOutput)
assert "thoughts/" in result.research_path
assert len(result.open_questions) >= 1

# Test 2: ParsePlanOutput
plan_text = '''
Plan created at: thoughts/shared/plans/2026-01-01-test/00-overview.md

## Phase 1: Setup
Dependencies: None
Success Criteria: Tests pass

Complexity: low
'''
result = b.ParsePlanOutput(raw_output=plan_text)
assert isinstance(result, PlanOutput)
assert len(result.phases) >= 1

# Test 3: ParsePhaseFiles
files_text = '''
Created files:
- thoughts/shared/plans/test/00-overview.md
- thoughts/shared/plans/test/01-setup.md
'''
result = b.ParsePhaseFiles(raw_output=files_text)
assert isinstance(result, PhaseDecompositionOutput)
assert "00-overview.md" in result.overview_file
```
