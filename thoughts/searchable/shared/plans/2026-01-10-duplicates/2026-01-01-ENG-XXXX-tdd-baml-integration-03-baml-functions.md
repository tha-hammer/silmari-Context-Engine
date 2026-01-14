# Phase 3: BAML Parse Functions

## Overview

Define BAML functions that use Claude to parse raw text output into typed schemas. These functions bridge the gap between Claude CLI text output and strongly-typed Pydantic models.

**Behaviors Covered**: 6, 7, 8
**Human-Testable Function**: `b.ParseResearchOutput(raw_output="...")` returns typed `ResearchOutput` with correctly extracted data

## Dependencies

- **Requires**: Phase 2 (Schema Definitions) - schemas must exist for function return types
- **Blocks**: Phase 4 (Helper Integration)

## Changes Required

### Behavior 6: ParseResearchOutput Function

| File | Line | Change Description |
|------|------|-------------------|
| `baml_src/functions.baml` | NEW:1-20 | Define ParseResearchOutput function |

**Test File**: `planning_pipeline/tests/test_baml_functions.py`

```python
class TestParseResearchOutput:
    """Behavior 6: ParseResearchOutput BAML function."""

    @pytest.fixture
    def sample_research_output(self):
        """Sample Claude output from research step."""
        # Returns multi-line string with research output format

    def test_parse_research_function_exists(self):
        """Given generated client, ParseResearchOutput function exists."""
        # Checks: hasattr(b, 'ParseResearchOutput')

    def test_parse_research_extracts_path(self, sample_research_output):
        """Given output with path, extracts research_path."""
        # Calls: b.ParseResearchOutput(raw_output=sample_research_output)
        # Verifies: result.research_path matches expected path

    def test_parse_research_extracts_questions(self, sample_research_output):
        """Given output with open questions, extracts them."""
        # Verifies: len(result.open_questions) == 3

    def test_parse_research_extracts_summary(self, sample_research_output):
        """Given output with summary, extracts it."""
        # Verifies: "authentication" in result.summary.lower()

    def test_parse_research_handles_no_questions(self):
        """Given output without open questions, returns empty list."""
        # Verifies: result.open_questions == []
```

**Implementation**: `baml_src/functions.baml`
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
```

---

### Behavior 7: ParsePlanOutput Function

| File | Line | Change Description |
|------|------|-------------------|
| `baml_src/functions.baml` | NEW:22-45 | Define ParsePlanOutput function |

**Test File**: `planning_pipeline/tests/test_baml_functions.py`

```python
class TestParsePlanOutput:
    """Behavior 7: ParsePlanOutput BAML function."""

    @pytest.fixture
    def sample_plan_output(self):
        """Sample Claude output from planning step."""
        # Returns multi-line string with plan format including phases

    def test_parse_plan_function_exists(self):
        """Given generated client, ParsePlanOutput function exists."""
        # Checks: hasattr(b, 'ParsePlanOutput')

    def test_parse_plan_extracts_path(self, sample_plan_output):
        """Given output with path, extracts plan_path."""
        # Verifies: "thoughts/shared/plans/" in result.plan_path

    def test_parse_plan_extracts_phases(self, sample_plan_output):
        """Given output with phases, extracts Phase list."""
        # Verifies: len(result.phases) == 3
        # Verifies: result.phases[0].number == 1
        # Verifies: result.phases[0].name == "Setup"

    def test_parse_plan_extracts_complexity(self, sample_plan_output):
        """Given output with complexity, extracts it."""
        # Verifies: result.estimated_complexity.lower() == "medium"
```

**Implementation**: `baml_src/functions.baml` (append)
```baml
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
```

---

### Behavior 8: ParsePhaseFiles Function

| File | Line | Change Description |
|------|------|-------------------|
| `baml_src/functions.baml` | NEW:47-65 | Define ParsePhaseFiles function |

**Test File**: `planning_pipeline/tests/test_baml_functions.py`

```python
class TestParsePhaseFiles:
    """Behavior 8: ParsePhaseFiles BAML function."""

    @pytest.fixture
    def sample_decomposition_output(self):
        """Sample Claude output from phase decomposition."""
        # Returns multi-line string with file list

    def test_parse_phase_files_function_exists(self):
        """Given generated client, ParsePhaseFiles function exists."""
        # Checks: hasattr(b, 'ParsePhaseFiles')

    def test_parse_phase_files_extracts_all(self, sample_decomposition_output):
        """Given output with file list, extracts all paths."""
        # Verifies: len(result.phase_files) == 4
        # Verifies: "00-overview.md" in result.phase_files[0]

    def test_parse_phase_files_identifies_overview(self, sample_decomposition_output):
        """Given output, identifies overview file."""
        # Verifies: "00-overview.md" in result.overview_file
```

**Implementation**: `baml_src/functions.baml` (append)
```baml
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

## Success Criteria

### Automated Tests
```bash
# Red phase - tests should fail
pytest planning_pipeline/tests/test_baml_functions.py -v

# Green phase - after implementation
baml-cli generate
pytest planning_pipeline/tests/test_baml_functions.py -v
```

### Manual Verification
- [ ] In Python REPL, `b.ParseResearchOutput(raw_output="...")` returns typed data
- [ ] In Python REPL, `b.ParsePlanOutput(raw_output="...")` returns typed data
- [ ] In Python REPL, `b.ParsePhaseFiles(raw_output="...")` returns typed data
- [ ] IDE shows correct return types for all functions
- [ ] Results have proper field access (result.research_path, result.phases[0].name)

## Implementation Steps

1. Create `baml_src/functions.baml` with ParseResearchOutput
2. Run `baml-cli generate`
3. Run Behavior 6 tests (should pass)
4. Add ParsePlanOutput to functions.baml
5. Run `baml-cli generate`
6. Run Behavior 7 tests (should pass)
7. Add ParsePhaseFiles to functions.baml
8. Run `baml-cli generate`
9. Run all Phase 3 tests (should all pass)

## Complete functions.baml File

```baml
// functions.baml - BAML parsing functions for Claude output

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

## API Cost Consideration

These functions make real API calls to Claude Sonnet. For testing:
- Use `pytest.mark.slow` and `pytest.mark.integration` markers
- Consider mocking for unit tests (covered in Phase 5)
- Set reasonable rate limiting in test fixtures

## Rollback Plan

If issues arise:
1. Remove `baml_src/functions.baml`
2. Run `baml-cli generate` to regenerate client without functions
3. Remove test file `planning_pipeline/tests/test_baml_functions.py`
