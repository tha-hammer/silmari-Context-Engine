# BAML Integration TDD Implementation Plan

## Overview

Integrate BAML (Boundary AI Markup Language) into the Context Engine to replace regex-based output parsing with type-safe, schema-driven LLM function calls. Using **Approach A (Hybrid)**: Keep Claude CLI subprocess for execution, use BAML for structured parsing of text output.

## Current State Analysis

### What Exists
- `planning_pipeline/helpers.py:9-70` - Three regex-based extraction functions
- `planning_pipeline/tests/test_helpers.py` - 16 test cases for helpers
- `planning_pipeline/steps.py:12-358` - Five pipeline steps returning `dict[str, Any]`
- `planning_pipeline/claude_runner.py:9-66` - Subprocess execution wrapper
- No pyproject.toml or requirements.txt
- No existing BAML configuration

### Key Discoveries
- Regex extraction is fragile and lacks type safety (`helpers.py:21-23`)
- Steps return untyped dictionaries (`steps.py:85-90`, `185-189`)
- Claude CLI provides tool access (Read, Write, Bash) that BAML direct API lacks
- Existing tests use pytest with fixtures (`tests/conftest.py`)

### What's Missing
- BAML project structure (`baml_src/`)
- Generated Python client (`baml_client/`)
- Pydantic models for structured outputs
- pyproject.toml with `baml-py` dependency
- BAML function definitions for parsing

## Desired End State

A hybrid system where:
1. Claude CLI subprocess executes prompts with full tool access
2. BAML parses text output into strongly-typed Pydantic models
3. Type-safe returns replace `dict[str, Any]` throughout pipeline
4. IDE autocomplete and type checking for all LLM outputs

### Observable Behaviors
- Given Claude text output, when BAML parser runs, then typed Pydantic model is returned
- Given invalid output format, when BAML parser runs, then structured error with details is returned
- Given pipeline step, when executed, then returns typed dataclass instead of dict
- Given BAML schema change, when `baml-cli generate` runs, then Python client updates

## What We're NOT Doing

- Replacing Claude CLI with BAML direct API (keeps tool access)
- Migrating to async/await patterns (codebase uses sync)
- Implementing BAML streaming (keeping subprocess model)
- Adding new LLM providers (keeping Anthropic via CLI)

## Testing Strategy

- **Framework**: pytest (existing)
- **Test Types**:
  - Unit: BAML parsing functions (pure, fast, mock LLM output)
  - Integration: BAML client generation, real parsing
  - E2E: Full pipeline with BAML parsing
- **Mocking**: Mock Claude output text, test BAML parsing independently
- **Fixtures**: Sample Claude outputs for each output type

---

## Behavior 1: Project Setup with pyproject.toml

### Test Specification
**Given**: A project without Python dependency configuration
**When**: pyproject.toml is created with baml-py dependency
**Then**: `pip install -e .` succeeds and baml-cli is available

**Edge Cases**:
- Invalid Python version
- baml-py version incompatibility

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_baml_setup.py`
```python
import subprocess
import sys
import pytest


class TestBAMLSetup:
    """Behavior 1: BAML project configuration."""

    def test_baml_cli_available(self):
        """Given baml-py installed, baml-cli is available."""
        result = subprocess.run(
            [sys.executable, "-m", "baml_cli", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "baml" in result.stdout.lower() or "version" in result.stdout.lower()

    def test_pyproject_exists(self):
        """Given project root, pyproject.toml exists."""
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        pyproject = project_root / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml must exist"

    def test_baml_dependency_in_pyproject(self):
        """Given pyproject.toml, baml-py is listed as dependency."""
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        pyproject = project_root / "pyproject.toml"
        content = pyproject.read_text()
        assert "baml-py" in content, "baml-py must be in dependencies"
```

#### 🟢 Green: Minimal Implementation
**File**: `pyproject.toml`
```toml
[project]
name = "silmari-context-engine"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "baml-py>=0.80.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-mock>=3.14.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### 🔵 Refactor: Improve Code
Add existing project dependencies and improve structure.

### Success Criteria
**Automated:**
- [ ] Test fails for right reason (Red): `pytest planning_pipeline/tests/test_baml_setup.py -v`
- [ ] Test passes (Green): `pip install -e . && pytest planning_pipeline/tests/test_baml_setup.py -v`
- [ ] All tests pass after refactor: `pytest planning_pipeline/tests/ -v`

**Manual:**
- [ ] `baml-cli --version` outputs version info
- [ ] `pip install -e .` completes without errors

---

## Behavior 2: BAML Generator Configuration

### Test Specification
**Given**: baml_src/ directory with main.baml
**When**: `baml-cli generate` runs
**Then**: baml_client/ Python code is generated

**Edge Cases**:
- Invalid baml syntax
- Missing generator config
- Output directory doesn't exist

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_baml_setup.py`
```python
class TestBAMLGeneration:
    """Behavior 2: BAML code generation."""

    def test_baml_src_directory_exists(self):
        """Given project, baml_src/ directory exists."""
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        baml_src = project_root / "baml_src"
        assert baml_src.exists(), "baml_src/ directory must exist"
        assert baml_src.is_dir(), "baml_src must be a directory"

    def test_main_baml_exists(self):
        """Given baml_src/, main.baml with generator config exists."""
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        main_baml = project_root / "baml_src" / "main.baml"
        assert main_baml.exists(), "baml_src/main.baml must exist"
        content = main_baml.read_text()
        assert "generator" in content, "main.baml must have generator config"

    def test_baml_client_generated(self):
        """Given baml-cli generate ran, baml_client/ exists with Python code."""
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        baml_client = project_root / "baml_client"
        assert baml_client.exists(), "baml_client/ must exist (run baml-cli generate)"

    def test_baml_client_importable(self):
        """Given generated client, it can be imported."""
        try:
            from baml_client import b
            assert b is not None
        except ImportError as e:
            pytest.fail(f"baml_client not importable: {e}")
```

#### 🟢 Green: Minimal Implementation
**File**: `baml_src/main.baml`
```baml
generator lang_python {
  output_type "python/pydantic"
  output_dir "../baml_client"
  version "0.80.0"
  default_client_mode "sync"
}
```

**File**: `baml_src/clients.baml`
```baml
client<llm> ClaudeSonnet {
  provider anthropic
  options {
    model "claude-3-5-sonnet-20241022"
    api_key env.ANTHROPIC_API_KEY
  }
}
```

**Run**: `baml-cli generate`

### Success Criteria
**Automated:**
- [ ] Test fails for right reason (Red): `pytest planning_pipeline/tests/test_baml_setup.py::TestBAMLGeneration -v`
- [ ] Test passes (Green): `baml-cli generate && pytest planning_pipeline/tests/test_baml_setup.py::TestBAMLGeneration -v`

**Manual:**
- [ ] `baml_client/` directory contains Python files
- [ ] `from baml_client import b` works in Python REPL

---

## Behavior 3: ResearchOutput Schema Definition

### Test Specification
**Given**: BAML schema for ResearchOutput
**When**: Client is generated
**Then**: `ResearchOutput` Pydantic model is available with typed fields

**Edge Cases**:
- Optional fields (open_questions may be empty)
- Invalid field types

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_baml_schemas.py`
```python
import pytest


class TestResearchOutputSchema:
    """Behavior 3: ResearchOutput schema definition."""

    def test_research_output_model_exists(self):
        """Given generated client, ResearchOutput model exists."""
        from baml_client.types import ResearchOutput
        assert ResearchOutput is not None

    def test_research_output_has_required_fields(self):
        """Given ResearchOutput, it has research_path, open_questions, summary fields."""
        from baml_client.types import ResearchOutput
        import inspect

        # Get field names from model
        if hasattr(ResearchOutput, 'model_fields'):
            fields = ResearchOutput.model_fields.keys()
        else:
            fields = [name for name, _ in inspect.getmembers(ResearchOutput)
                     if not name.startswith('_')]

        assert 'research_path' in fields, "research_path field required"
        assert 'open_questions' in fields, "open_questions field required"
        assert 'summary' in fields, "summary field required"

    def test_research_output_instantiation(self):
        """Given valid data, ResearchOutput can be instantiated."""
        from baml_client.types import ResearchOutput

        output = ResearchOutput(
            research_path="thoughts/shared/research/2026-01-01-test.md",
            open_questions=["What auth method?", "Which database?"],
            summary="Research on authentication options"
        )

        assert output.research_path == "thoughts/shared/research/2026-01-01-test.md"
        assert len(output.open_questions) == 2
        assert output.summary == "Research on authentication options"

    def test_research_output_empty_questions(self):
        """Given no open questions, open_questions can be empty list."""
        from baml_client.types import ResearchOutput

        output = ResearchOutput(
            research_path="thoughts/shared/research/2026-01-01-test.md",
            open_questions=[],
            summary="No questions"
        )

        assert output.open_questions == []
```

#### 🟢 Green: Minimal Implementation
**File**: `baml_src/schemas.baml`
```baml
class ResearchOutput {
  research_path string @description("Path to created research document, e.g. thoughts/shared/research/2026-01-01-topic.md")
  open_questions string[] @description("List of unanswered questions discovered during research")
  summary string @description("Brief summary of research findings")
}
```

**Run**: `baml-cli generate`

### Success Criteria
**Automated:**
- [ ] Test fails (Red): `pytest planning_pipeline/tests/test_baml_schemas.py::TestResearchOutputSchema -v`
- [ ] Test passes (Green): `baml-cli generate && pytest planning_pipeline/tests/test_baml_schemas.py::TestResearchOutputSchema -v`

**Manual:**
- [ ] IDE shows autocomplete for ResearchOutput fields
- [ ] Type checker validates field types

---

## Behavior 4: PlanOutput Schema Definition

### Test Specification
**Given**: BAML schema for PlanOutput
**When**: Client is generated
**Then**: `PlanOutput` and `Phase` Pydantic models are available

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_baml_schemas.py`
```python
class TestPlanOutputSchema:
    """Behavior 4: PlanOutput schema definition."""

    def test_plan_output_model_exists(self):
        """Given generated client, PlanOutput model exists."""
        from baml_client.types import PlanOutput
        assert PlanOutput is not None

    def test_phase_model_exists(self):
        """Given generated client, Phase model exists."""
        from baml_client.types import Phase
        assert Phase is not None

    def test_plan_output_has_phases(self):
        """Given PlanOutput, it has phases field as list of Phase."""
        from baml_client.types import PlanOutput, Phase

        phase = Phase(
            number=1,
            name="Setup",
            dependencies=[],
            success_criteria=["Tests pass"]
        )

        output = PlanOutput(
            plan_path="thoughts/shared/plans/2026-01-01-feature/00-overview.md",
            phases=[phase],
            estimated_complexity="medium"
        )

        assert len(output.phases) == 1
        assert output.phases[0].name == "Setup"

    def test_phase_fields(self):
        """Given Phase, it has number, name, dependencies, success_criteria."""
        from baml_client.types import Phase

        phase = Phase(
            number=2,
            name="Implementation",
            dependencies=["Phase 1: Setup"],
            success_criteria=["All tests pass", "No type errors"]
        )

        assert phase.number == 2
        assert phase.name == "Implementation"
        assert len(phase.dependencies) == 1
        assert len(phase.success_criteria) == 2
```

#### 🟢 Green: Minimal Implementation
**File**: `baml_src/schemas.baml` (append)
```baml
class Phase {
  number int @description("1-indexed phase number")
  name string @description("Phase name, e.g. 'Setup', 'Implementation', 'Testing'")
  dependencies string[] @description("List of phase names this depends on")
  success_criteria string[] @description("Automated and manual verification criteria")
}

class PlanOutput {
  plan_path string @description("Path to plan document, e.g. thoughts/shared/plans/2026-01-01-feature/00-overview.md")
  phases Phase[] @description("List of implementation phases")
  estimated_complexity string @description("low, medium, or high")
}
```

### Success Criteria
**Automated:**
- [ ] Test fails (Red): `pytest planning_pipeline/tests/test_baml_schemas.py::TestPlanOutputSchema -v`
- [ ] Test passes (Green): `baml-cli generate && pytest planning_pipeline/tests/test_baml_schemas.py::TestPlanOutputSchema -v`

---

## Behavior 5: PhaseDecompositionOutput Schema Definition

### Test Specification
**Given**: BAML schema for PhaseDecompositionOutput
**When**: Client is generated
**Then**: `PhaseDecompositionOutput` model is available with phase_files list

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_baml_schemas.py`
```python
class TestPhaseDecompositionOutputSchema:
    """Behavior 5: PhaseDecompositionOutput schema definition."""

    def test_phase_decomposition_output_exists(self):
        """Given generated client, PhaseDecompositionOutput model exists."""
        from baml_client.types import PhaseDecompositionOutput
        assert PhaseDecompositionOutput is not None

    def test_phase_decomposition_has_files(self):
        """Given PhaseDecompositionOutput, it has phase_files field."""
        from baml_client.types import PhaseDecompositionOutput

        output = PhaseDecompositionOutput(
            phase_files=[
                "thoughts/shared/plans/2026-01-01-feat/00-overview.md",
                "thoughts/shared/plans/2026-01-01-feat/01-phase-1-setup.md",
                "thoughts/shared/plans/2026-01-01-feat/02-phase-2-impl.md"
            ],
            overview_file="thoughts/shared/plans/2026-01-01-feat/00-overview.md"
        )

        assert len(output.phase_files) == 3
        assert "00-overview.md" in output.overview_file
```

#### 🟢 Green: Minimal Implementation
**File**: `baml_src/schemas.baml` (append)
```baml
class PhaseDecompositionOutput {
  phase_files string[] @description("List of created phase file paths in order")
  overview_file string @description("Path to the 00-overview.md file")
}
```

### Success Criteria
**Automated:**
- [ ] Test fails (Red): `pytest planning_pipeline/tests/test_baml_schemas.py::TestPhaseDecompositionOutputSchema -v`
- [ ] Test passes (Green): `baml-cli generate && pytest -v`

---

## Behavior 6: ParseResearchOutput Function Definition

### Test Specification
**Given**: Raw Claude text output from research step
**When**: `ParseResearchOutput(raw_text)` BAML function is called
**Then**: Returns typed `ResearchOutput` with extracted data

**Edge Cases**:
- Output missing research path
- No open questions section
- Malformed markdown

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_baml_functions.py`
```python
import pytest


class TestParseResearchOutput:
    """Behavior 6: ParseResearchOutput BAML function."""

    @pytest.fixture
    def sample_research_output(self):
        """Sample Claude output from research step."""
        return '''
Research complete!

I've created a research document at: thoughts/shared/research/2026-01-01-auth-options.md

## Summary
Analyzed authentication options for the project. Found existing patterns in auth/ directory.

## Key Findings
- JWT tokens used in auth/jwt.py:45
- Session management in auth/session.py:12

## Open Questions
- What authentication method should we use for the API?
- Should we support multiple databases for session storage?
- How should we handle token refresh?

## Next Steps
Begin implementation based on findings.
'''

    def test_parse_research_function_exists(self):
        """Given generated client, ParseResearchOutput function exists."""
        from baml_client import b
        assert hasattr(b, 'ParseResearchOutput')

    def test_parse_research_extracts_path(self, sample_research_output):
        """Given output with path, extracts research_path."""
        from baml_client import b

        result = b.ParseResearchOutput(raw_output=sample_research_output)

        assert result.research_path == "thoughts/shared/research/2026-01-01-auth-options.md"

    def test_parse_research_extracts_questions(self, sample_research_output):
        """Given output with open questions, extracts them."""
        from baml_client import b

        result = b.ParseResearchOutput(raw_output=sample_research_output)

        assert len(result.open_questions) == 3
        assert "authentication method" in result.open_questions[0].lower()

    def test_parse_research_extracts_summary(self, sample_research_output):
        """Given output with summary, extracts it."""
        from baml_client import b

        result = b.ParseResearchOutput(raw_output=sample_research_output)

        assert "authentication" in result.summary.lower()

    def test_parse_research_handles_no_questions(self):
        """Given output without open questions, returns empty list."""
        from baml_client import b

        output = '''
Research complete!
Created: thoughts/shared/research/2026-01-01-simple.md
Simple research with no open questions.
'''
        result = b.ParseResearchOutput(raw_output=output)

        assert result.open_questions == [] or len(result.open_questions) == 0
```

#### 🟢 Green: Minimal Implementation
**File**: `baml_src/functions.baml`
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

### Success Criteria
**Automated:**
- [ ] Test fails (Red): `pytest planning_pipeline/tests/test_baml_functions.py::TestParseResearchOutput -v`
- [ ] Test passes (Green): `baml-cli generate && pytest planning_pipeline/tests/test_baml_functions.py::TestParseResearchOutput -v`

**Manual:**
- [ ] Function returns correct types in REPL
- [ ] IDE shows correct return type for ParseResearchOutput

---

## Behavior 7: ParsePlanOutput Function Definition

### Test Specification
**Given**: Raw Claude text output from planning step
**When**: `ParsePlanOutput(raw_text)` BAML function is called
**Then**: Returns typed `PlanOutput` with phases extracted

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_baml_functions.py`
```python
class TestParsePlanOutput:
    """Behavior 7: ParsePlanOutput BAML function."""

    @pytest.fixture
    def sample_plan_output(self):
        """Sample Claude output from planning step."""
        return '''
Plan created!

I've written the plan to: thoughts/shared/plans/2026-01-01-auth-impl/00-overview.md

## Plan Overview
This plan implements authentication with 3 phases.

## Phase 1: Setup
- Configure dependencies
- Set up database schema
Dependencies: None
Success Criteria:
- pytest passes
- Schema migrations complete

## Phase 2: Implementation
- Implement JWT handler
- Add session middleware
Dependencies: Phase 1
Success Criteria:
- All auth tests pass
- No type errors

## Phase 3: Integration Testing
- E2E authentication tests
Dependencies: Phase 2
Success Criteria:
- All E2E tests pass
- Performance benchmarks met

Complexity: Medium
'''

    def test_parse_plan_function_exists(self):
        """Given generated client, ParsePlanOutput function exists."""
        from baml_client import b
        assert hasattr(b, 'ParsePlanOutput')

    def test_parse_plan_extracts_path(self, sample_plan_output):
        """Given output with path, extracts plan_path."""
        from baml_client import b

        result = b.ParsePlanOutput(raw_output=sample_plan_output)

        assert "thoughts/shared/plans/2026-01-01-auth-impl" in result.plan_path

    def test_parse_plan_extracts_phases(self, sample_plan_output):
        """Given output with phases, extracts Phase list."""
        from baml_client import b

        result = b.ParsePlanOutput(raw_output=sample_plan_output)

        assert len(result.phases) == 3
        assert result.phases[0].number == 1
        assert result.phases[0].name == "Setup"
        assert result.phases[1].name == "Implementation"

    def test_parse_plan_extracts_complexity(self, sample_plan_output):
        """Given output with complexity, extracts it."""
        from baml_client import b

        result = b.ParsePlanOutput(raw_output=sample_plan_output)

        assert result.estimated_complexity.lower() == "medium"
```

#### 🟢 Green: Minimal Implementation
**File**: `baml_src/functions.baml` (append)
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

### Success Criteria
**Automated:**
- [ ] Test fails (Red): `pytest planning_pipeline/tests/test_baml_functions.py::TestParsePlanOutput -v`
- [ ] Test passes (Green): `baml-cli generate && pytest -v`

---

## Behavior 8: ParsePhaseFiles Function Definition

### Test Specification
**Given**: Raw Claude text output from phase decomposition
**When**: `ParsePhaseFiles(raw_text)` BAML function is called
**Then**: Returns typed `PhaseDecompositionOutput` with file paths

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_baml_functions.py`
```python
class TestParsePhaseFiles:
    """Behavior 8: ParsePhaseFiles BAML function."""

    @pytest.fixture
    def sample_decomposition_output(self):
        """Sample Claude output from phase decomposition."""
        return '''
Phase decomposition complete!

Created the following phase files:
- thoughts/shared/plans/2026-01-01-auth/00-overview.md (Overview linking all phases)
- thoughts/shared/plans/2026-01-01-auth/01-phase-1-setup.md
- thoughts/shared/plans/2026-01-01-auth/02-phase-2-implementation.md
- thoughts/shared/plans/2026-01-01-auth/03-phase-3-testing.md

Each phase file contains detailed implementation steps with success criteria.
'''

    def test_parse_phase_files_function_exists(self):
        """Given generated client, ParsePhaseFiles function exists."""
        from baml_client import b
        assert hasattr(b, 'ParsePhaseFiles')

    def test_parse_phase_files_extracts_all(self, sample_decomposition_output):
        """Given output with file list, extracts all paths."""
        from baml_client import b

        result = b.ParsePhaseFiles(raw_output=sample_decomposition_output)

        assert len(result.phase_files) == 4
        assert "00-overview.md" in result.phase_files[0]
        assert "01-phase-1-setup.md" in result.phase_files[1]

    def test_parse_phase_files_identifies_overview(self, sample_decomposition_output):
        """Given output, identifies overview file."""
        from baml_client import b

        result = b.ParsePhaseFiles(raw_output=sample_decomposition_output)

        assert "00-overview.md" in result.overview_file
```

#### 🟢 Green: Minimal Implementation
**File**: `baml_src/functions.baml` (append)
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

### Success Criteria
**Automated:**
- [ ] Test fails (Red): `pytest planning_pipeline/tests/test_baml_functions.py::TestParsePhaseFiles -v`
- [ ] Test passes (Green): `baml-cli generate && pytest -v`

---

## Behavior 9: BAML Parser Integration in helpers.py

### Test Specification
**Given**: helpers.py with existing regex functions
**When**: BAML parsing functions are added
**Then**: New functions use BAML client, return typed objects

**Edge Cases**:
- BAML client not available (graceful fallback)
- API error during parsing

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_baml_helpers.py`
```python
import pytest


class TestBAMLHelperIntegration:
    """Behavior 9: BAML parsing in helpers module."""

    @pytest.fixture
    def sample_research_output(self):
        return '''
Research complete!
Created: thoughts/shared/research/2026-01-01-test.md

## Open Questions
- Question 1?
- Question 2?
'''

    def test_parse_research_output_exists(self):
        """Given helpers module, parse_research_output function exists."""
        from planning_pipeline.baml_helpers import parse_research_output
        assert callable(parse_research_output)

    def test_parse_research_returns_typed_object(self, sample_research_output):
        """Given Claude output, returns ResearchOutput object."""
        from planning_pipeline.baml_helpers import parse_research_output
        from baml_client.types import ResearchOutput

        result = parse_research_output(sample_research_output)

        assert isinstance(result, ResearchOutput)
        assert result.research_path is not None

    def test_parse_plan_output_exists(self):
        """Given helpers module, parse_plan_output function exists."""
        from planning_pipeline.baml_helpers import parse_plan_output
        assert callable(parse_plan_output)

    def test_parse_phase_files_exists(self):
        """Given helpers module, parse_phase_files function exists."""
        from planning_pipeline.baml_helpers import parse_phase_files
        assert callable(parse_phase_files)
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/baml_helpers.py`
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

### Success Criteria
**Automated:**
- [ ] Test fails (Red): `pytest planning_pipeline/tests/test_baml_helpers.py -v`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_baml_helpers.py -v`

**Manual:**
- [ ] Import works: `from planning_pipeline.baml_helpers import parse_research_output`
- [ ] Returns correct types in REPL

---

## Behavior 10: Step Functions Use BAML Parsing

### Test Specification
**Given**: steps.py using regex helpers
**When**: Updated to use BAML parsing
**Then**: Returns typed dataclasses instead of dicts

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_baml_steps.py`
```python
import pytest
from pathlib import Path
from dataclasses import dataclass


class TestBAMLStepsIntegration:
    """Behavior 10: Steps using BAML parsing."""

    def test_step_research_returns_typed_result(self, monkeypatch):
        """Given research step, returns typed ResearchStepResult."""
        from planning_pipeline.baml_steps import step_research, ResearchStepResult

        # Mock Claude runner to return sample output
        sample_output = '''
Research complete!
Created: thoughts/shared/research/2026-01-01-test.md

## Open Questions
- Test question?
'''
        def mock_run(*args, **kwargs):
            return {"success": True, "output": sample_output}

        monkeypatch.setattr("planning_pipeline.baml_steps.run_claude_sync", mock_run)

        result = step_research(Path("."), "Test research")

        assert isinstance(result, ResearchStepResult)
        assert result.success is True
        assert result.research_path is not None

    def test_step_planning_returns_typed_result(self, monkeypatch):
        """Given planning step, returns typed PlanStepResult."""
        from planning_pipeline.baml_steps import step_planning, PlanStepResult

        sample_output = '''
Plan created!
Path: thoughts/shared/plans/2026-01-01-test/00-overview.md

## Phase 1: Setup
Success Criteria: Tests pass

Complexity: low
'''
        def mock_run(*args, **kwargs):
            return {"success": True, "output": sample_output}

        monkeypatch.setattr("planning_pipeline.baml_steps.run_claude_sync", mock_run)

        result = step_planning(Path("."), "test-research.md")

        assert isinstance(result, PlanStepResult)
        assert result.success is True
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/baml_steps.py`
```python
"""Pipeline steps with BAML-powered typed outputs."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

from .claude_runner import run_claude_sync
from .baml_helpers import parse_research_output, parse_plan_output, parse_phase_files
from baml_client.types import Phase


@dataclass
class ResearchStepResult:
    """Typed result from research step."""
    success: bool
    research_path: Optional[str] = None
    open_questions: List[str] = None
    summary: Optional[str] = None
    raw_output: Optional[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.open_questions is None:
            self.open_questions = []


@dataclass
class PlanStepResult:
    """Typed result from planning step."""
    success: bool
    plan_path: Optional[str] = None
    phases: List[Phase] = None
    estimated_complexity: Optional[str] = None
    raw_output: Optional[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.phases is None:
            self.phases = []


@dataclass
class PhaseDecompositionResult:
    """Typed result from phase decomposition step."""
    success: bool
    phase_files: List[str] = None
    overview_file: Optional[str] = None
    raw_output: Optional[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.phase_files is None:
            self.phase_files = []


def step_research(project_path: Path, research_prompt: str) -> ResearchStepResult:
    """Execute research phase with BAML-typed output."""
    from datetime import datetime

    # ... (prompt construction same as original)
    prompt = f"Research: {research_prompt}"  # Simplified for test

    result = run_claude_sync(prompt=prompt, timeout=300)

    if not result["success"]:
        return ResearchStepResult(
            success=False,
            error=result.get("error", "Research failed")
        )

    try:
        parsed = parse_research_output(result["output"])
        return ResearchStepResult(
            success=True,
            research_path=parsed.research_path,
            open_questions=parsed.open_questions,
            summary=parsed.summary,
            raw_output=result["output"]
        )
    except Exception as e:
        return ResearchStepResult(
            success=False,
            error=f"BAML parsing failed: {e}",
            raw_output=result["output"]
        )


def step_planning(
    project_path: Path,
    research_path: str,
    additional_context: str = ""
) -> PlanStepResult:
    """Execute planning phase with BAML-typed output."""

    prompt = f"Create plan based on: {research_path}"  # Simplified

    result = run_claude_sync(prompt=prompt, timeout=300)

    if not result["success"]:
        return PlanStepResult(
            success=False,
            error=result.get("error", "Planning failed")
        )

    try:
        parsed = parse_plan_output(result["output"])
        return PlanStepResult(
            success=True,
            plan_path=parsed.plan_path,
            phases=parsed.phases,
            estimated_complexity=parsed.estimated_complexity,
            raw_output=result["output"]
        )
    except Exception as e:
        return PlanStepResult(
            success=False,
            error=f"BAML parsing failed: {e}",
            raw_output=result["output"]
        )
```

### Success Criteria
**Automated:**
- [ ] Test fails (Red): `pytest planning_pipeline/tests/test_baml_steps.py -v`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_baml_steps.py -v`
- [ ] All tests pass: `pytest planning_pipeline/tests/ -v`

**Manual:**
- [ ] IDE shows correct types for step results
- [ ] Autocomplete works for result.research_path, result.phases, etc.

---

## Behavior 11: Error Handling for BAML Parsing Failures

### Test Specification
**Given**: Malformed Claude output
**When**: BAML parsing runs
**Then**: Graceful error with details, not crash

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_baml_errors.py`
```python
import pytest


class TestBAMLErrorHandling:
    """Behavior 11: BAML parsing error handling."""

    def test_parse_research_handles_empty_output(self):
        """Given empty output, returns error result."""
        from planning_pipeline.baml_helpers import parse_research_output_safe

        result = parse_research_output_safe("")

        assert result.success is False
        assert result.error is not None

    def test_parse_research_handles_no_path(self):
        """Given output without path, returns error with details."""
        from planning_pipeline.baml_helpers import parse_research_output_safe

        result = parse_research_output_safe("Just some text without a file path")

        # BAML may still try to parse, but research_path might be None
        # or an error might occur
        assert result is not None

    def test_baml_api_error_handled(self, monkeypatch):
        """Given API error, returns graceful error."""
        from planning_pipeline.baml_helpers import parse_research_output_safe
        from baml_client import b

        def mock_parse(*args, **kwargs):
            raise Exception("API rate limit exceeded")

        monkeypatch.setattr(b, "ParseResearchOutput", mock_parse)

        result = parse_research_output_safe("Valid output")

        assert result.success is False
        assert "rate limit" in result.error.lower() or "API" in result.error
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/baml_helpers.py` (add to existing)
```python
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ParseResult:
    """Generic result wrapper for BAML parsing."""
    success: bool
    data: Optional[any] = None
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
```

### Success Criteria
**Automated:**
- [ ] Test fails (Red): `pytest planning_pipeline/tests/test_baml_errors.py -v`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_baml_errors.py -v`

**Manual:**
- [ ] No uncaught exceptions during parsing
- [ ] Error messages are descriptive

---

## Behavior 12: Full Pipeline with BAML Parsing

### Test Specification
**Given**: Pipeline configured with BAML parsing
**When**: Full pipeline runs
**Then**: All outputs are typed, IDE autocomplete works

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_baml_pipeline.py`
```python
import pytest
from pathlib import Path


class TestBAMLPipeline:
    """Behavior 12: Full pipeline with BAML."""

    @pytest.mark.slow
    @pytest.mark.integration
    def test_pipeline_returns_typed_results(self, monkeypatch, cleanup_issues):
        """Given pipeline with BAML, all results are typed."""
        from planning_pipeline.baml_pipeline import BAMLPlanningPipeline

        project_path = Path(__file__).parent.parent.parent
        pipeline = BAMLPlanningPipeline(project_path)

        result = pipeline.run(
            research_prompt="Brief project structure",
            auto_approve=True
        )

        # Result is a typed dataclass, not dict
        assert hasattr(result, 'success')
        assert hasattr(result, 'research')
        assert hasattr(result, 'planning')

        # Nested results are also typed
        if result.research:
            assert hasattr(result.research, 'research_path')
            assert hasattr(result.research, 'open_questions')

        # Cleanup
        if result.epic_id:
            cleanup_issues.append(result.epic_id)
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/baml_pipeline.py`
```python
"""Planning pipeline with BAML-powered typed outputs."""

from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from .beads_controller import BeadsController
from .baml_steps import (
    step_research,
    step_planning,
    ResearchStepResult,
    PlanStepResult,
    PhaseDecompositionResult
)


@dataclass
class PipelineResult:
    """Typed result from full pipeline execution."""
    success: bool
    started: str
    completed: Optional[str] = None
    research: Optional[ResearchStepResult] = None
    planning: Optional[PlanStepResult] = None
    decomposition: Optional[PhaseDecompositionResult] = None
    epic_id: Optional[str] = None
    plan_dir: Optional[str] = None
    failed_at: Optional[str] = None
    stopped_at: Optional[str] = None


class BAMLPlanningPipeline:
    """Interactive planning pipeline with BAML-powered type safety."""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self.beads = BeadsController(project_path)

    def run(
        self,
        research_prompt: str,
        ticket_id: Optional[str] = None,
        auto_approve: bool = False
    ) -> PipelineResult:
        """Run the complete planning pipeline with typed outputs."""

        result = PipelineResult(
            success=False,
            started=datetime.now().isoformat()
        )

        # Step 1: Research
        research = step_research(self.project_path, research_prompt)
        result.research = research

        if not research.success:
            result.failed_at = "research"
            return result

        # Step 2: Planning
        planning = step_planning(
            self.project_path,
            research.research_path or ""
        )
        result.planning = planning

        if not planning.success:
            result.failed_at = "planning"
            return result

        # ... rest of pipeline

        result.success = True
        result.completed = datetime.now().isoformat()
        return result
```

### Success Criteria
**Automated:**
- [ ] Test fails (Red): `pytest planning_pipeline/tests/test_baml_pipeline.py -v -m integration`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_baml_pipeline.py -v -m integration`
- [ ] All tests pass: `pytest planning_pipeline/tests/ -v`

**Manual:**
- [ ] IDE shows correct types throughout pipeline
- [ ] Type checker passes on pipeline code

---

## Project Structure After Implementation

```
silmari-Context-Engine/
├── pyproject.toml                    # NEW: Python deps with baml-py
├── baml_src/                         # NEW: BAML source definitions
│   ├── main.baml                     # Generator config
│   ├── clients.baml                  # LLM client definitions
│   ├── schemas.baml                  # ResearchOutput, PlanOutput, etc.
│   └── functions.baml                # ParseResearchOutput, etc.
├── baml_client/                      # GENERATED: Python client
│   └── (auto-generated by baml-cli)
├── planning_pipeline/
│   ├── __init__.py
│   ├── helpers.py                    # Original regex helpers (deprecated)
│   ├── baml_helpers.py               # NEW: BAML parsing wrappers
│   ├── steps.py                      # Original steps (dict returns)
│   ├── baml_steps.py                 # NEW: Steps with typed returns
│   ├── pipeline.py                   # Original pipeline
│   ├── baml_pipeline.py              # NEW: Pipeline with typed results
│   ├── beads_controller.py
│   ├── claude_runner.py
│   ├── checkpoints.py
│   └── tests/
│       ├── test_helpers.py           # Original tests
│       ├── test_baml_setup.py        # NEW: Behavior 1-2
│       ├── test_baml_schemas.py      # NEW: Behavior 3-5
│       ├── test_baml_functions.py    # NEW: Behavior 6-8
│       ├── test_baml_helpers.py      # NEW: Behavior 9
│       ├── test_baml_steps.py        # NEW: Behavior 10
│       ├── test_baml_errors.py       # NEW: Behavior 11
│       └── test_baml_pipeline.py     # NEW: Behavior 12
```

---

## Implementation Order

1. **Behavior 1-2**: Project setup (pyproject.toml, baml_src/, code generation)
2. **Behavior 3-5**: Schema definitions (ResearchOutput, PlanOutput, PhaseDecompositionOutput)
3. **Behavior 6-8**: BAML function definitions (ParseResearchOutput, etc.)
4. **Behavior 9**: Helper integration (baml_helpers.py)
5. **Behavior 10**: Steps integration (baml_steps.py)
6. **Behavior 11**: Error handling
7. **Behavior 12**: Full pipeline integration (baml_pipeline.py)

---

## References

- Research: `thoughts/shared/research/2026-01-01-baml-integration-research.md`
- Existing Pipeline Plan: `thoughts/shared/plans/2025-12-31-tdd-python-deterministic-pipeline.md`
- BAML Documentation: https://docs.boundaryml.com/home
- Python FastAPI Starter: https://github.com/BoundaryML/baml-examples/tree/main/python-fastapi-starter
