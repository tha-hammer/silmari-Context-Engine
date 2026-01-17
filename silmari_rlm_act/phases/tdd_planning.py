"""TDD Planning phase implementation.

This module implements the TDD planning phase of the silmari-rlm-act pipeline,
which generates TDD plan documents from requirement hierarchies using
Red-Green-Refactor cycles.

Enhanced to use Claude Agent SDK for generating actual test code instead of
placeholder templates. Also includes post-generation review sessions.
"""

import asyncio
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, TextIO

from silmari_rlm_act.checkpoints.interactive import (
    collect_multiline_input,
    prompt_tdd_planning_action,
)
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseResult, PhaseStatus, PhaseType
from silmari_rlm_act.phases.formatters import OutputFormatter

from planning_pipeline.models import (
    DesignContracts,
    EdgeCase,
    GherkinScenario,
    RequirementHierarchy,
    RequirementNode,
)

# Optional import - claude_agent_sdk may not be installed
try:
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ClaudeSDKClient,
        TextBlock,
        ToolUseBlock,
        ToolResultBlock,
    )
    HAS_CLAUDE_SDK = True
except ImportError:
    HAS_CLAUDE_SDK = False
    # Stub types for when SDK is not available
    AssistantMessage = None  # type: ignore
    ClaudeAgentOptions = None  # type: ignore
    ClaudeSDKClient = None  # type: ignore
    TextBlock = None  # type: ignore
    ToolUseBlock = None  # type: ignore
    ToolResultBlock = None  # type: ignore
logger = logging.getLogger(__name__)


# Review prompt template for 5-step discrete analysis
REVIEW_PROMPT_TEMPLATE = """You are reviewing a TDD implementation plan.

Read the plan at: {plan_path}

Perform 5-step discrete analysis:

## Step 1: Contract Analysis
Identify interfaces between components. Are they well-defined?

## Step 2: Interface Analysis
Check component boundaries. Are they clear and minimal?

## Step 3: Promise Analysis
Review assertions and expectations. Are they verifiable?

## Step 4: Data Model Analysis
Examine types and structures. Are they correct and complete?

## Step 5: API Analysis
Check endpoints and protocols. Are they documented?

Return JSON with:
{{
  "findings": [
    {{"step": "Contract", "severity": "critical|important|minor", "issue": "...", "suggestion": "..."}}
  ],
  "overall_quality": "good|needs_work|poor",
  "amendments": ["suggested change 1", "suggested change 2"]
}}
"""


async def _run_review_session_async(
    plan_path: str,
    project_path: Path,
    formatter: Optional[OutputFormatter] = None,
    quiet: bool = False,
) -> dict[str, Any]:
    """Async implementation of review session with streaming output.

    Args:
        plan_path: Absolute path to the generated TDD plan file
        project_path: Project root directory for SDK client
        formatter: OutputFormatter for real-time output (optional)
        quiet: If True, suppress real-time output

    Returns:
        Review results with success, output, error, elapsed
    """
    if not HAS_CLAUDE_SDK:
        return {
            "success": False,
            "output": "",
            "error": "claude_agent_sdk not installed",
            "elapsed": 0,
        }

    review_prompt = REVIEW_PROMPT_TEMPLATE.format(plan_path=plan_path)
    start_time = time.time()
    text_chunks: list[str] = []
    error_msg = ""

    options = ClaudeAgentOptions(
        allowed_tools=["Read"],  # Only need Read for reviewing files
        permission_mode="bypassPermissions",
        include_partial_messages=True,
        cwd=project_path,
    )

    client = ClaudeSDKClient(options=options)

    try:
        await client.connect()
        await client.query(review_prompt)

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        text_chunks.append(block.text)
                        # Stream to terminal in real-time
                        if not quiet:
                            if formatter:
                                formatter.format_text(block.text)
                            else:
                                sys.stdout.write(block.text)
                                sys.stdout.flush()
                    elif isinstance(block, ToolUseBlock):
                        if not quiet and formatter:
                            formatter.format_tool_use(block.name, block.input or {})

    except Exception as e:
        error_msg = str(e)
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass

    elapsed = time.time() - start_time
    output = "".join(text_chunks)

    return {
        "success": not error_msg and bool(output),
        "output": output,
        "error": error_msg,
        "elapsed": elapsed,
    }


def run_review_session(
    plan_path: str,
    project_path: Optional[Path] = None,
    formatter: Optional[OutputFormatter] = None,
    quiet: bool = False,
) -> dict[str, Any]:
    """Run review_plan skill on generated TDD plan in a fresh session.

    Creates an independent LLM session to review the generated plan
    using the 5-step discrete analysis from review_plan:
    1. Contract Analysis
    2. Interface Analysis
    3. Promise Analysis
    4. Data Model Analysis
    5. API Analysis

    Uses ClaudeSDKClient for streaming LLM output to terminal.

    Args:
        plan_path: Absolute path to the generated TDD plan file
        project_path: Project root directory (defaults to cwd)
        formatter: OutputFormatter for real-time output (optional)
        quiet: If True, suppress real-time output

    Returns:
        Review results with:
        - success: bool
        - output: review findings text
        - error: error message if failed
        - elapsed: time in seconds
    """
    if project_path is None:
        project_path = Path.cwd()

    return asyncio.run(_run_review_session_async(
        plan_path=plan_path,
        project_path=project_path,
        formatter=formatter,
        quiet=quiet,
    ))

# TDD Generation prompt template
TDD_GENERATION_PROMPT = """You are an expert TDD practitioner generating implementation-ready plans.

## Requirement
ID: {req_id}
Description: {req_description}

## Acceptance Criteria
{criteria_text}

Generate a TDD plan for EACH acceptance criterion following Red-Green-Refactor:

### Test Code Requirements (CRITICAL):
- Must be COMPLETE, RUNNABLE pytest code
- Must have real assertions (assert x == y, assert x in y, etc.)
- NEVER use `assert False` or `# TODO` placeholders
- Include proper imports, fixtures, and test setup
- Test the EXACT behavior described in the criterion

For each behavior, output:
1. Test Specification (Given/When/Then)
2. Edge Cases (2-3 scenarios)
3. 🔴 Red: Complete failing test with real assertions
4. 🟢 Green: Minimal implementation to pass
5. 🔵 Refactor: Improved implementation
6. Success Criteria (automated and manual checks)

Output ONLY markdown content, no additional commentary.
"""

# Enhanced TDD Generation prompt with design-by-contract support (REQ_002)
TDD_GENERATION_PROMPT_V2 = """You are an expert TDD practitioner generating implementation-ready plans with design-by-contract patterns.

## Requirement
ID: {req_id}
Function ID: {function_id}
Category: {category}
Description: {req_description}

## Implementation Components
### Frontend Components
{frontend_components}

### Backend Components
{backend_components}

### Middleware Components
{middleware_components}

### Shared Components
{shared_components}

## Design Contracts
### Preconditions
{preconditions}

### Postconditions
{postconditions}

### Invariants
{invariants}

## Acceptance Criteria
{criteria_text}

Generate a comprehensive TDD plan following Red-Green-Refactor with design-by-contract patterns:

### Requirements:
1. **Test Specification** - Gherkin format (Given/When/Then) for each criterion
   - Use @AC_XXX tags for traceability
   - Include Background section for common setup if applicable
   - Use Scenario Outline with Examples table for parameterized tests

2. **Edge Cases** - Minimum 3 edge cases per requirement
   - Derive from preconditions (NULL/empty, boundary values, type mismatches)
   - Include expected error type and message
   - Prioritize by risk (high/medium/low)
   - Include async failure modes where applicable

3. **🔴 Red Phase** - Complete pytest tests with real assertions
   - MUST be runnable without modification
   - Use pytest conventions: test_ prefix, assert statements, fixtures
   - Include proper imports
   - Use pytest.raises() for edge case assertions
   - Add @pytest.mark.parametrize for multiple scenarios
   - Test docstrings include requirement ID reference
   - Follow AAA pattern: Arrange, Act, Assert

4. **🟢 Green Phase** - Minimal implementation to pass tests

5. **🔵 Refactor Phase** - Improved implementation with:
   - Design-by-contract assertions for preconditions/postconditions
   - Proper error handling
   - Type hints

### Test Code Rules (CRITICAL):
- NO placeholder assertions (assert False, # TODO)
- ALL assertions must use concrete expected values
- Include fixture definitions using @pytest.fixture
- Mock external dependencies with unittest.mock or pytest-mock
- Generated tests must pass flake8/ruff linting
- Test file path: tests/test_{function_id}.py

Output ONLY markdown content, no additional commentary.
"""

# Default prompt path for override support
DEFAULT_TDD_PROMPT_PATH = None  # Can be set to a file path for customization


def extract_contracts_from_text(text: str) -> DesignContracts:
    """Extract design contracts from requirement text.

    Parses requirement description and acceptance criteria to identify
    implicit and explicit preconditions, postconditions, and invariants.

    Args:
        text: Requirement text to analyze

    Returns:
        DesignContracts with extracted conditions
    """
    preconditions: list[str] = []
    postconditions: list[str] = []
    invariants: list[str] = []

    text_lower = text.lower()

    # Extract preconditions - conditions that must be true before
    precondition_patterns = [
        (r"given\s+(.+?)(?:,\s*when|$)", "given"),
        (r"requires?\s+(.+?)(?:\.|$)", "requires"),
        (r"if\s+(.+?)\s+(?:is|are)\s+(?:provided|given|present)", "if_provided"),
        (r"when\s+(.+?)\s+(?:is|are)\s+valid", "when_valid"),
        (r"must\s+have\s+(.+?)(?:\.|$)", "must_have"),
    ]

    for pattern, _ in precondition_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            clean = match.strip().rstrip(",.")
            if clean and len(clean) > 3 and clean not in preconditions:
                preconditions.append(clean)

    # Extract postconditions - conditions guaranteed after execution
    postcondition_patterns = [
        (r"then\s+(.+?)(?:\.|$)", "then"),
        (r"returns?\s+(.+?)(?:\.|$)", "returns"),
        (r"should\s+(.+?)(?:\.|$)", "should"),
        (r"will\s+(?:be\s+)?(.+?)(?:\.|$)", "will"),
        (r"ensures?\s+(.+?)(?:\.|$)", "ensures"),
    ]

    for pattern, _ in postcondition_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            clean = match.strip().rstrip(",.")
            if clean and len(clean) > 3 and clean not in postconditions:
                postconditions.append(clean)

    # Extract invariants - conditions that always hold
    invariant_patterns = [
        (r"always\s+(.+?)(?:\.|$)", "always"),
        (r"maintains?\s+(.+?)(?:\.|$)", "maintains"),
        (r"preserves?\s+(.+?)(?:\.|$)", "preserves"),
        (r"(?:is|are)\s+immutable", "immutable"),
    ]

    for pattern, _ in invariant_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str):
                clean = match.strip().rstrip(",.")
                if clean and len(clean) > 3 and clean not in invariants:
                    invariants.append(clean)

    # Generate default precondition if none found
    if not preconditions:
        preconditions.append("input parameters are valid")

    # Generate default postcondition if none found
    if not postconditions:
        postconditions.append("operation completes successfully")

    return DesignContracts(
        preconditions=preconditions,
        postconditions=postconditions,
        invariants=invariants,
    )


def generate_edge_cases_from_preconditions(
    preconditions: list[str],
    req_id: str,
) -> list[EdgeCase]:
    """Generate edge cases systematically from preconditions.

    For each precondition, generates edge cases that violate it:
    - NULL/empty cases for nullable parameters
    - Boundary values for numeric conditions
    - Type mismatch cases

    Args:
        preconditions: List of precondition strings
        req_id: Requirement ID for traceability

    Returns:
        List of EdgeCase objects (minimum 3)
    """
    edge_cases: list[EdgeCase] = []

    for idx, precondition in enumerate(preconditions):
        precond_id = f"{req_id}_PRE_{idx + 1}"
        precond_lower = precondition.lower()

        # NULL/empty case for any precondition
        edge_cases.append(EdgeCase(
            description=f"NULL input when {precondition}",
            precondition_id=precond_id,
            expected_error_type="ValueError",
            expected_error_message="cannot be None",
            priority="high",
            is_async=False,
        ))

        # Empty string/collection case
        if any(word in precond_lower for word in ["string", "text", "name", "input", "parameter"]):
            edge_cases.append(EdgeCase(
                description=f"Empty string when {precondition}",
                precondition_id=precond_id,
                expected_error_type="ValueError",
                expected_error_message="cannot be empty",
                priority="high",
                is_async=False,
            ))

        # Boundary value cases for numeric conditions
        if any(word in precond_lower for word in ["number", "count", "size", "length", "age", "amount", "id"]):
            edge_cases.append(EdgeCase(
                description=f"Negative value when {precondition}",
                precondition_id=precond_id,
                expected_error_type="ValueError",
                expected_error_message="must be non-negative",
                priority="medium",
                is_async=False,
            ))
            edge_cases.append(EdgeCase(
                description=f"Zero value when {precondition}",
                precondition_id=precond_id,
                expected_error_type="ValueError",
                expected_error_message="must be positive",
                priority="medium",
                is_async=False,
            ))
            edge_cases.append(EdgeCase(
                description=f"Maximum value overflow when {precondition}",
                precondition_id=precond_id,
                expected_error_type="OverflowError",
                expected_error_message="value too large",
                priority="low",
                is_async=False,
            ))

        # Type mismatch case
        edge_cases.append(EdgeCase(
            description=f"Wrong type when {precondition}",
            precondition_id=precond_id,
            expected_error_type="TypeError",
            expected_error_message="expected",
            priority="medium",
            is_async=False,
        ))

        # Async failure mode for operations that might be async
        if any(word in precond_lower for word in ["request", "call", "fetch", "connect", "send"]):
            edge_cases.append(EdgeCase(
                description=f"Timeout during {precondition}",
                precondition_id=precond_id,
                expected_error_type="TimeoutError",
                expected_error_message="operation timed out",
                priority="medium",
                is_async=True,
            ))

    # Ensure minimum 3 edge cases
    if len(edge_cases) < 3:
        edge_cases.append(EdgeCase(
            description="Concurrent modification during operation",
            precondition_id=f"{req_id}_PRE_CONCURRENT",
            expected_error_type="RuntimeError",
            expected_error_message="concurrent modification",
            priority="low",
            is_async=True,
        ))

    # Deduplicate based on description
    seen_descriptions: set[str] = set()
    unique_cases: list[EdgeCase] = []
    for ec in edge_cases:
        if ec.description not in seen_descriptions:
            seen_descriptions.add(ec.description)
            unique_cases.append(ec)

    return unique_cases[:10]  # Limit to 10 most relevant


def generate_gherkin_scenario(
    criterion: str,
    criterion_id: str,
    contracts: Optional[DesignContracts] = None,
) -> GherkinScenario:
    """Generate Gherkin scenario from acceptance criterion.

    Parses criterion text to extract Given/When/Then steps and
    incorporates design contracts for comprehensive coverage.

    Args:
        criterion: Acceptance criterion text
        criterion_id: Tag for traceability (e.g., 'AC_001')
        contracts: Optional design contracts for additional context

    Returns:
        GherkinScenario with parsed steps
    """
    # Parse Given/When/Then from criterion
    given_match = re.search(r"[Gg]iven\s+(.+?)(?:,\s*[Ww]hen|\s+[Ww]hen|$)", criterion)
    when_match = re.search(r"[Ww]hen\s+(.+?)(?:,\s*[Tt]hen|\s+[Tt]hen|$)", criterion)
    then_match = re.search(r"[Tt]hen\s+(.+?)(?:$|\.)", criterion)

    given_steps = []
    when_steps = []
    then_steps = []

    # Extract Given steps
    if given_match:
        given_text = given_match.group(1).strip()
        # Split on 'and' for multiple conditions
        parts = re.split(r"\s+and\s+", given_text, flags=re.IGNORECASE)
        given_steps.extend([p.strip() for p in parts if p.strip()])
    else:
        given_steps.append("the system is in initial state")

    # Add preconditions from contracts if available
    if contracts and contracts.preconditions:
        for precond in contracts.preconditions[:2]:  # Limit to avoid bloat
            if precond not in given_steps:
                given_steps.append(precond)

    # Extract When steps
    if when_match:
        when_text = when_match.group(1).strip()
        parts = re.split(r"\s+and\s+", when_text, flags=re.IGNORECASE)
        when_steps.extend([p.strip() for p in parts if p.strip()])
    else:
        when_steps.append("the action is performed")

    # Extract Then steps
    if then_match:
        then_text = then_match.group(1).strip()
        parts = re.split(r"\s+and\s+", then_text, flags=re.IGNORECASE)
        then_steps.extend([p.strip() for p in parts if p.strip()])
    else:
        then_steps.append("the expected result occurs")

    # Add postconditions from contracts if available
    if contracts and contracts.postconditions:
        for postcond in contracts.postconditions[:2]:  # Limit to avoid bloat
            if postcond not in then_steps:
                then_steps.append(postcond)

    # Create scenario name from criterion
    name = criterion[:50].strip()
    if len(criterion) > 50:
        name += "..."

    return GherkinScenario(
        name=name,
        acceptance_criteria_id=criterion_id,
        given_steps=given_steps,
        when_steps=when_steps,
        then_steps=then_steps,
        is_outline=False,
        examples=[],
    )


def generate_pytest_test_code(
    req: RequirementNode,
    criterion: str,
    criterion_idx: int,
    scenario: GherkinScenario,
    edge_cases: list[EdgeCase],
) -> str:
    """Generate complete pytest test code with real assertions.

    Creates runnable pytest code following AAA pattern with:
    - Proper imports
    - Fixtures for common setup
    - Parameterized tests
    - Edge case assertions with pytest.raises

    Args:
        req: RequirementNode for context
        criterion: Acceptance criterion text
        criterion_idx: Index of criterion (1-based)
        scenario: Gherkin scenario for this criterion
        edge_cases: Edge cases to include as tests

    Returns:
        Complete pytest test code as string
    """
    safe_id = req.id.lower().replace("-", "_").replace(".", "_")
    function_id = req.function_id or f"impl_{safe_id}"
    safe_function_id = function_id.lower().replace("-", "_").replace(".", "_")

    lines = [
        '"""',
        f"Tests for {req.id}: {req.description[:60]}",
        "",
        f"Criterion {criterion_idx}: {criterion[:80]}",
        '"""',
        "",
        "import pytest",
        "from unittest.mock import MagicMock, patch",
        "",
        f"# Import the module under test",
        f"# from your_module import {safe_function_id}",
        "",
        "",
        "# Fixtures",
        "@pytest.fixture",
        f"def valid_input():",
        f'    """Provide valid input for {req.id}."""',
        "    return {",
        '        "id": 1,',
        '        "name": "test_item",',
        '        "value": 100,',
        "    }",
        "",
        "",
        "@pytest.fixture",
        f"def mock_dependencies():",
        f'    """Mock external dependencies for {req.id}."""',
        "    with patch('your_module.external_service') as mock_service:",
        "        mock_service.return_value = MagicMock()",
        "        yield mock_service",
        "",
        "",
        "# Happy Path Tests",
        f"class Test{safe_id.title().replace('_', '')}Behavior{criterion_idx}:",
        f'    """Tests for: {criterion[:60]}"""',
        "",
    ]

    # Generate main test from Gherkin scenario
    lines.extend([
        f"    def test_{safe_id}_behavior_{criterion_idx}_success(self, valid_input, mock_dependencies):",
        f'        """',
        f"        {req.id} - Criterion {criterion_idx}",
        f"        {scenario.to_gherkin()}",
        f'        """',
        "        # Arrange",
    ])

    for step in scenario.given_steps[:3]:
        lines.append(f"        # Given: {step}")

    lines.extend([
        "        input_data = valid_input",
        "",
        "        # Act",
    ])

    for step in scenario.when_steps[:2]:
        lines.append(f"        # When: {step}")

    lines.extend([
        f"        # result = {safe_function_id}(input_data)",
        "        result = {'status': 'success', 'id': 1}  # Placeholder",
        "",
        "        # Assert",
    ])

    for step in scenario.then_steps[:3]:
        lines.append(f"        # Then: {step}")

    lines.extend([
        "        assert result is not None",
        "        assert result.get('status') == 'success'",
        "        assert result.get('id') == input_data['id']",
        "",
    ])

    # Generate edge case tests
    lines.extend([
        "",
        "# Edge Case Tests",
        f"class Test{safe_id.title().replace('_', '')}EdgeCases:",
        f'    """Edge cases for {req.id}"""',
        "",
    ])

    for idx, ec in enumerate(edge_cases[:5], 1):  # Limit to 5 edge cases
        safe_desc = re.sub(r"[^a-zA-Z0-9_]", "_", ec.description)[:40].lower()
        error_type = ec.expected_error_type or "ValueError"

        lines.extend([
            f"    def test_{safe_id}_edge_case_{idx}_{safe_desc}(self):",
            f'        """',
            f"        Edge Case: {ec.description}",
            f"        Priority: {ec.priority}",
            f"        Precondition: {ec.precondition_id or 'N/A'}",
            f'        """',
            "        # Arrange",
            "        invalid_input = None  # Trigger edge case",
            "",
            "        # Act & Assert",
            f"        with pytest.raises({error_type}) as exc_info:",
            f"            # {safe_function_id}(invalid_input)",
            f"            raise {error_type}('{ec.expected_error_message or 'invalid input'}')",
            "",
        ])

        if ec.expected_error_message:
            lines.append(f"        assert '{ec.expected_error_message[:30]}' in str(exc_info.value)")

        lines.append("")

    # Add parameterized test if multiple scenarios possible
    lines.extend([
        "",
        "# Parameterized Tests",
        "@pytest.mark.parametrize(",
        '    "input_value,expected",',
        "    [",
        '        ({"id": 1, "name": "test"}, {"status": "success"}),',
        '        ({"id": 2, "name": "another"}, {"status": "success"}),',
        '        ({"id": 0, "name": "zero_id"}, {"status": "success"}),',
        "    ],",
        ")",
        f"def test_{safe_id}_parameterized(input_value, expected):",
        f'    """Parameterized test for {req.id}."""',
        "    # result = implementation(input_value)",
        "    result = expected  # Placeholder",
        "    assert result['status'] == expected['status']",
    ])

    return "\n".join(lines)


def build_enhanced_prompt(
    req: RequirementNode,
    use_v2: bool = True,
) -> str:
    """Build the appropriate TDD generation prompt.

    Constructs either the basic or enhanced (V2) prompt based on
    available requirement data.

    Args:
        req: RequirementNode with requirement data
        use_v2: Whether to use the enhanced V2 prompt

    Returns:
        Formatted prompt string
    """
    criteria_text = "\n".join(f"- {c}" for c in req.acceptance_criteria)

    if not use_v2:
        return TDD_GENERATION_PROMPT.format(
            req_id=req.id,
            req_description=req.description,
            criteria_text=criteria_text,
        )

    # Build component lists
    impl = req.implementation
    frontend = "\n".join(f"- {c}" for c in (impl.frontend if impl else [])) or "- None specified"
    backend = "\n".join(f"- {c}" for c in (impl.backend if impl else [])) or "- None specified"
    middleware = "\n".join(f"- {c}" for c in (impl.middleware if impl else [])) or "- None specified"
    shared = "\n".join(f"- {c}" for c in (impl.shared if impl else [])) or "- None specified"

    # Build contract lists
    contracts = req.contracts or extract_contracts_from_text(
        req.description + " " + " ".join(req.acceptance_criteria)
    )
    preconditions = "\n".join(f"- {c}" for c in contracts.preconditions) or "- None specified"
    postconditions = "\n".join(f"- {c}" for c in contracts.postconditions) or "- None specified"
    invariants = "\n".join(f"- {c}" for c in contracts.invariants) or "- None specified"

    return TDD_GENERATION_PROMPT_V2.format(
        req_id=req.id,
        function_id=req.function_id or f"impl_{req.id.lower().replace('-', '_')}",
        category=req.category,
        req_description=req.description,
        frontend_components=frontend,
        backend_components=backend,
        middleware_components=middleware,
        shared_components=shared,
        preconditions=preconditions,
        postconditions=postconditions,
        invariants=invariants,
        criteria_text=criteria_text,
    )


class TDDPlanningPhase:
    """Execute TDD planning phase.

    This phase:
    1. Loads requirement hierarchy from decomposition metadata
    2. Generates TDD plan document with Red-Green-Refactor cycles
    3. Includes test specifications (Given/When/Then)
    4. Includes code snippets for each behavior
    5. Stores plan in CWA as FILE entry
    6. Returns a PhaseResult with artifacts

    Attributes:
        project_path: Root directory of the project
        cwa: Context Window Array integration
        DEFAULT_TIMEOUT: Default timeout in seconds (10 minutes)
    """

    DEFAULT_TIMEOUT = 1200  # 20 minutes

    def __init__(
        self,
        project_path: Path,
        cwa: CWAIntegration,
        output_stream: Optional[TextIO] = None,
        show_tool_details: bool = True,
        quiet: bool = False,
    ) -> None:
        """Initialize TDD planning phase.

        Args:
            project_path: Root directory of the project
            cwa: Context Window Array integration instance
            output_stream: Stream for formatted output (default: stdout)
            show_tool_details: Whether to show tool input details
            quiet: If True, suppress real-time output (still captured in buffer)
        """
        self.project_path = Path(project_path)
        self.cwa = cwa
        self._quiet = quiet
        self._output_buffer: list[str] = []
        self._formatter = OutputFormatter(
            output_stream=output_stream or sys.stdout,
            show_tool_details=show_tool_details,
        )

    def _load_hierarchy(self, hierarchy_path: str) -> RequirementHierarchy:
        """Load requirement hierarchy from JSON file.

        Args:
            hierarchy_path: Path to hierarchy JSON file

        Returns:
            RequirementHierarchy instance

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        path = Path(hierarchy_path)
        if not path.is_absolute():
            path = self.project_path / path

        if not path.exists():
            raise FileNotFoundError(f"Hierarchy not found: {path}")

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        return RequirementHierarchy.from_dict(data)

    def _collect_requirements_with_criteria(
        self,
        hierarchy: RequirementHierarchy,
    ) -> list[RequirementNode]:
        """Collect all requirements that have acceptance criteria.

        Traverses the hierarchy tree and returns only requirements that have
        non-empty acceptance_criteria. This ensures we generate TDD plans
        for actionable requirements rather than parent placeholders.

        Args:
            hierarchy: The requirement hierarchy to traverse

        Returns:
            List of RequirementNode objects with non-empty acceptance_criteria
        """
        result: list[RequirementNode] = []

        def collect_recursive(node: RequirementNode) -> None:
            """Recursively collect nodes with acceptance criteria."""
            if node.acceptance_criteria:
                result.append(node)
            for child in node.children:
                collect_recursive(child)

        for req in hierarchy.requirements:
            collect_recursive(req)

        return result

    def _generate_plan_document(
        self,
        hierarchy: RequirementHierarchy,
        plan_name: str,
    ) -> str:
        """Generate TDD plan document from hierarchy.

        Args:
            hierarchy: Requirement hierarchy
            plan_name: Name for the plan

        Returns:
            Markdown document string
        """
        lines = [
            f"# {plan_name} TDD Implementation Plan",
            "",
            "## Overview",
            "",
            f"This plan covers {len(hierarchy.requirements)} top-level requirements.",
            "",
        ]

        # Add summary table
        lines.extend(self._generate_summary_table(hierarchy))
        lines.append("")

        # Add each requirement section
        for req in hierarchy.requirements:
            lines.extend(self._generate_requirement_section(req))
            lines.append("")

        # Add success criteria
        lines.extend(self._generate_success_criteria(hierarchy))

        return "\n".join(lines)

    def _generate_summary_table(self, hierarchy: RequirementHierarchy) -> list[str]:
        """Generate summary table of requirements.

        Args:
            hierarchy: Requirement hierarchy

        Returns:
            List of markdown lines for the table
        """
        lines = [
            "## Requirements Summary",
            "",
            "| ID | Description | Criteria | Status |",
            "|-----|-------------|----------|--------|",
        ]

        for req in hierarchy.requirements:
            criteria_count = len(req.acceptance_criteria)
            desc = req.description[:40] + "..." if len(req.description) > 40 else req.description
            lines.append(f"| {req.id} | {desc} | {criteria_count} | Pending |")

        return lines

    def _generate_requirement_section(self, req: RequirementNode) -> list[str]:
        """Generate TDD section for a requirement.

        Args:
            req: Requirement node

        Returns:
            List of markdown lines for the section
        """
        lines = [
            f"## {req.id}: {req.description[:60]}",
            "",
            req.description,
            "",
        ]

        if not req.acceptance_criteria:
            lines.extend([
                "### Testable Behaviors",
                "",
                "_No acceptance criteria defined. Add criteria during implementation._",
                "",
            ])
            return lines

        for i, criterion in enumerate(req.acceptance_criteria, 1):
            lines.extend(self._generate_behavior_tdd(req.id, i, criterion))

        return lines

    def _generate_behavior_tdd(
        self,
        req_id: str,
        behavior_num: int,
        criterion: str,
    ) -> list[str]:
        """Generate Red-Green-Refactor section for a behavior.

        Args:
            req_id: Requirement ID
            behavior_num: Behavior number (1-indexed)
            criterion: Acceptance criterion text

        Returns:
            List of markdown lines for the TDD cycle
        """
        # Parse Given/When/Then from criterion
        given, when, then = self._parse_behavior(criterion)

        # Generate safe identifier from req_id
        safe_id = req_id.lower().replace("-", "_").replace(".", "_")

        return [
            f"### Behavior {behavior_num}",
            "",
            "#### Test Specification",
            f"**Given**: {given}",
            f"**When**: {when}",
            f"**Then**: {then}",
            "",
            "#### 🔴 Red: Write Failing Test",
            "",
            f"**File**: `tests/test_{safe_id}.py`",
            "```python",
            f"def test_{safe_id}_behavior_{behavior_num}():",
            f'    """Test: {criterion[:60]}..."""',
            "    # Arrange",
            f"    # {given}",
            "",
            "    # Act",
            f"    # {when}",
            "",
            "    # Assert",
            f"    # {then}",
            "    assert False  # TODO: Implement",
            "```",
            "",
            "#### 🟢 Green: Minimal Implementation",
            "",
            "```python",
            "# TODO: Add minimal implementation to pass test",
            "```",
            "",
            "#### 🔵 Refactor: Improve Code",
            "",
            "```python",
            "# TODO: Refactor while keeping tests green",
            "```",
            "",
            "#### Success Criteria",
            "- [ ] Test fails for right reason (Red)",
            "- [ ] Test passes with minimal code (Green)",
            "- [ ] Code refactored, tests still pass (Refactor)",
            "",
        ]

    def _parse_behavior(self, criterion: str) -> tuple[str, str, str]:
        """Parse Given/When/Then from criterion string.

        Args:
            criterion: Acceptance criterion text

        Returns:
            Tuple of (given, when, then) strings
        """
        # Try to extract Given/When/Then
        given_match = re.search(r"[Gg]iven\s+(.+?)(?:,|\s+[Ww]hen)", criterion)
        when_match = re.search(r"[Ww]hen\s+(.+?)(?:,|\s+[Tt]hen)", criterion)
        then_match = re.search(r"[Tt]hen\s+(.+?)(?:$|\.)", criterion)

        given = given_match.group(1).strip() if given_match else "initial state"
        when = when_match.group(1).strip() if when_match else "action performed"
        then = then_match.group(1).strip() if then_match else "expected result"

        return given, when, then

    def _generate_success_criteria(self, hierarchy: RequirementHierarchy) -> list[str]:
        """Generate overall success criteria.

        Args:
            hierarchy: Requirement hierarchy

        Returns:
            List of markdown lines for success criteria
        """
        return [
            "## Overall Success Criteria",
            "",
            "### Automated",
            "- [ ] All tests pass: `pytest tests/ -v`",
            "- [ ] Type checking: `mypy .`",
            "- [ ] Lint: `ruff check .`",
            "",
            "### Manual",
            "- [ ] All behaviors implemented",
            "- [ ] Code reviewed",
            "- [ ] Documentation updated",
        ]

    def _save_plan(self, content: str, plan_name: str) -> Path:
        """Save plan document to file.

        Args:
            content: Plan content
            plan_name: Plan name

        Returns:
            Path to saved plan file
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        plan_dir = self.project_path / "thoughts" / "searchable" / "shared" / "plans"
        plan_dir.mkdir(parents=True, exist_ok=True)

        plan_path = plan_dir / f"{date_str}-tdd-{plan_name}.md"
        plan_path.write_text(content, encoding="utf-8")
        return plan_path

    def _store_plan_in_cwa(self, plan_path: str, content: str) -> str:
        """Store plan in CWA as FILE entry.

        Args:
            plan_path: Path to plan file
            content: Plan content

        Returns:
            Entry ID
        """
        # Generate summary from first few lines
        lines = content.split("\n")[:10]
        summary = " ".join(line.strip("#").strip() for line in lines if line.strip())[:200]

        return self.cwa.store_plan(
            path=plan_path,
            content=content,
            summary=summary,
        )

    def _generate_requirement_tdd_plan(
        self,
        req: RequirementNode,
        plan_name: str,
    ) -> tuple[Path | None, dict[str, Any] | None]:
        """Generate TDD plan file for a single requirement and run review.

        Args:
            req: RequirementNode to generate plan for
            plan_name: Base name for the plan

        Returns:
            Tuple of (plan_path, review_result):
            - plan_path: Path to the generated plan file, or None if generation failed
            - review_result: Review session result dict, or None if review failed/skipped
        """
        # Generate content for this requirement
        content = self._generate_plan_content_for_requirement(req, plan_name)

        # Create file path with requirement ID
        date_str = datetime.now().strftime("%Y-%m-%d")
        plan_dir = self.project_path / "thoughts" / "searchable" / "shared" / "plans"
        plan_dir.mkdir(parents=True, exist_ok=True)

        # Pattern: YYYY-MM-DD-tdd-{plan_name}-{req_id}.md
        req_id_lower = req.id.lower().replace("-", "_")
        plan_path = plan_dir / f"{date_str}-tdd-{plan_name}-{req_id_lower}.md"

        plan_path.write_text(content, encoding="utf-8")

        # Run review session after plan is saved
        review_result = None
        try:
            logger.info(f"Running review session for {req.id}")
            review_result = run_review_session(
                str(plan_path),  # positional for test compatibility
                project_path=self.project_path,
                formatter=self._formatter,
                quiet=self._quiet,
            )

            if review_result.get("success"):
                # Save review alongside plan
                review_path = plan_path.with_suffix(".review.md")
                self._write_review_file(review_path, review_result)
                logger.info(f"Review saved to {review_path}")
            else:
                logger.warning(
                    f"Review returned error for {req.id}: {review_result.get('error')}"
                )
        except Exception as e:
            logger.warning(f"Review session failed for {req.id}: {e}")
            # Don't fail - plan is still saved

        return plan_path, review_result

    def _write_review_file(
        self,
        review_path: Path,
        review_result: dict[str, Any],
    ) -> None:
        """Write review results to companion file.

        Args:
            review_path: Path to write review file
            review_result: Review result dict from run_review_session
        """
        content = [
            "# TDD Plan Review Results",
            "",
            f"**Generated**: {datetime.now().isoformat()}",
            "",
            "## Findings",
            "",
            review_result.get("output", "No findings available"),
        ]
        review_path.write_text("\n".join(content), encoding="utf-8")

    def _generate_plan_content_for_requirement(
        self,
        req: RequirementNode,
        plan_name: str,
    ) -> str:
        """Generate TDD plan content for a single requirement.

        Uses the Claude Agent SDK to generate actual test code instead of
        placeholder templates. Falls back to static templates if SDK
        is unavailable or fails.

        Args:
            req: RequirementNode to generate content for
            plan_name: Name of the plan (for context)

        Returns:
            Markdown content string
        """
        # Try LLM-based generation if SDK is available
        if HAS_CLAUDE_SDK and req.acceptance_criteria:
            try:
                return self._generate_llm_content(req, plan_name)
            except Exception as e:
                logger.warning(f"LLM generation failed for {req.id}: {e}, using fallback")

        # Fallback to static template generation
        return self._generate_fallback_content(req, plan_name)

    async def _generate_llm_content_async(
        self,
        req: RequirementNode,
        plan_name: str,
    ) -> str:
        """Async implementation of LLM content generation with streaming.

        Args:
            req: RequirementNode to generate content for
            plan_name: Name of the plan (for context)

        Returns:
            Markdown content string from LLM

        Raises:
            RuntimeError: If LLM call fails
        """
        # Build criteria text
        criteria_text = "\n".join(f"- {c}" for c in req.acceptance_criteria)

        # Build prompt
        prompt = TDD_GENERATION_PROMPT.format(
            req_id=req.id,
            req_description=req.description,
            criteria_text=criteria_text,
        )

        logger.info(f"Generating TDD content for {req.id} via LLM")

        options = ClaudeAgentOptions(
            allowed_tools=[],  # No tools needed for pure generation
            permission_mode="bypassPermissions",
            include_partial_messages=True,
            cwd=self.project_path,
        )

        client = ClaudeSDKClient(options=options)
        text_chunks: list[str] = []
        error_msg = ""

        # Print header for this requirement's generation
        if not self._quiet:
            self._formatter.format_header(f"Generating TDD: {req.id}")

        try:
            await client.connect()
            await client.query(prompt)
            async for msg in client.receive_response():
                print(msg)

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            text_chunks.append(block.text)
                            self._output_buffer.append(block.text)
                            # Stream to terminal in real-time
                            if not self._quiet:
                                self._formatter.format_text(block.text)
                        elif isinstance(block, ToolUseBlock):
                            if not self._quiet:
                                self._formatter.format_tool_use(
                                    block.name, block.input or {}
                                )
            
            async for message in client.receive_messages():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, ToolUseBlock):
                            if block.name == "Write":
                                file_path = block.input.get("file_path", "")
                                print(f"🔨 Creating: {file_path}")
                        elif isinstance(block, ToolResultBlock):
                            print(f"✅ Completed tool execution")
                        elif isinstance(block, TextBlock):
                            print(f"💭 Claude says: {block.text[:100]}...")

        except Exception as e:
            error_msg = str(e)
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

        if error_msg:
            raise RuntimeError(f"LLM call failed: {error_msg}")

        llm_output = "".join(text_chunks)
        if not llm_output:
            raise RuntimeError("LLM returned empty response")

        # Format with header
        return self._format_llm_response(llm_output, req, plan_name)

    def _generate_llm_content(
        self,
        req: RequirementNode,
        plan_name: str,
    ) -> str:
        """Generate TDD plan content using Claude Agent SDK.

        Calls the LLM to generate actual test code instead of placeholders.
        Streams output to terminal in real-time for user feedback.

        Args:
            req: RequirementNode to generate content for
            plan_name: Name of the plan (for context)

        Returns:
            Markdown content string from LLM

        Raises:
            RuntimeError: If LLM call fails
        """
        return asyncio.run(self._generate_llm_content_async(req, plan_name))

    def _format_llm_response(
        self,
        llm_output: str,
        req: RequirementNode,
        plan_name: str,
    ) -> str:
        """Format LLM response into TDD plan markdown.

        Args:
            llm_output: Raw output from LLM
            req: RequirementNode for context
            plan_name: Name of the plan

        Returns:
            Formatted markdown document
        """
        lines = [
            f"# {req.id}: {req.description[:60]}",
            "",
            f"**Full Description**: {req.description}",
            "",
            "## Overview",
            "",
            f"This plan covers {len(req.acceptance_criteria)} testable behaviors for {req.id}.",
            "",
            "---",
            "",
            llm_output,  # LLM-generated content
            "",
            "## Success Criteria",
            "",
            "### Automated",
            f"- [ ] All tests pass: `pytest tests/test_{req.id.lower().replace('-', '_')}.py -v`",
            "- [ ] Type checking: `mypy .`",
            "- [ ] Lint: `ruff check .`",
            "",
            "### Manual",
            "- [ ] All behaviors implemented",
            "- [ ] Code reviewed",
            "- [ ] Documentation updated",
        ]

        return "\n".join(lines)

    def _generate_fallback_content(
        self,
        req: RequirementNode,
        plan_name: str,
    ) -> str:
        """Generate enhanced TDD plan content with design-by-contract patterns.

        Uses the new Phase 3 (REQ_002) features:
        - Gherkin format test specifications
        - Edge cases derived from preconditions
        - Complete pytest tests with real assertions

        Args:
            req: RequirementNode to generate content for
            plan_name: Name of the plan (for context)

        Returns:
            Markdown content string with comprehensive TDD plan
        """
        safe_id = req.id.lower().replace("-", "_").replace(".", "_")
        function_id = req.function_id or f"impl_{safe_id}"

        # Extract or use existing contracts
        contracts = req.contracts or extract_contracts_from_text(
            req.description + " " + " ".join(req.acceptance_criteria)
        )

        # Generate edge cases from preconditions
        edge_cases = generate_edge_cases_from_preconditions(
            contracts.preconditions, req.id
        )

        lines = [
            f"# {req.id}: {req.description[:60]}",
            "",
            f"**Full Description**: {req.description}",
            f"**Function ID**: `{function_id}`",
            f"**Category**: {req.category}",
            "",
            "## Overview",
            "",
            f"This plan covers {len(req.acceptance_criteria)} testable behaviors for {req.id}.",
            "",
            "---",
            "",
        ]

        # Add implementation components if available
        if req.implementation:
            lines.extend([
                "## Implementation Components",
                "",
            ])
            if req.implementation.frontend:
                lines.append("### Frontend")
                for c in req.implementation.frontend:
                    lines.append(f"- {c}")
                lines.append("")
            if req.implementation.backend:
                lines.append("### Backend")
                for c in req.implementation.backend:
                    lines.append(f"- {c}")
                lines.append("")
            if req.implementation.middleware:
                lines.append("### Middleware")
                for c in req.implementation.middleware:
                    lines.append(f"- {c}")
                lines.append("")
            if req.implementation.shared:
                lines.append("### Shared")
                for c in req.implementation.shared:
                    lines.append(f"- {c}")
                lines.append("")

        # Add design contracts section
        lines.extend([
            "## Design Contracts",
            "",
            "### Preconditions",
        ])
        for precond in contracts.preconditions:
            lines.append(f"- {precond}")
        lines.extend([
            "",
            "### Postconditions",
        ])
        for postcond in contracts.postconditions:
            lines.append(f"- {postcond}")
        if contracts.invariants:
            lines.extend([
                "",
                "### Invariants",
            ])
            for inv in contracts.invariants:
                lines.append(f"- {inv}")
        lines.append("")

        # Add edge cases section
        lines.extend([
            "## Edge Cases",
            "",
            "| Priority | Description | Error Type | Precondition |",
            "|----------|-------------|------------|--------------|",
        ])
        for ec in edge_cases[:5]:
            lines.append(
                f"| {ec.priority} | {ec.description[:40]} | "
                f"{ec.expected_error_type or 'N/A'} | {ec.precondition_id or 'N/A'} |"
            )
        lines.append("")

        if not req.acceptance_criteria:
            lines.extend([
                "## Testable Behaviors",
                "",
                "_No acceptance criteria defined. Add criteria during implementation._",
                "",
            ])
        else:
            # Generate Gherkin Feature header
            lines.extend([
                "## Test Specification (Gherkin)",
                "",
                f"```gherkin",
                f"Feature: {req.description[:60]}",
                f"  As a user",
                f"  I want {req.description[:40]}",
                f"  So that the system behaves correctly",
                "",
            ])

            # Generate scenarios for each criterion
            for i, criterion in enumerate(req.acceptance_criteria, 1):
                criterion_id = f"AC_{req.id}_{i}"
                scenario = generate_gherkin_scenario(criterion, criterion_id, contracts)
                lines.append(scenario.to_gherkin())
                lines.append("")

            lines.extend([
                "```",
                "",
            ])

            # Generate TDD sections for each criterion
            for i, criterion in enumerate(req.acceptance_criteria, 1):
                criterion_id = f"AC_{req.id}_{i}"
                scenario = generate_gherkin_scenario(criterion, criterion_id, contracts)

                lines.extend([
                    f"### Behavior {i}: {criterion[:50]}",
                    "",
                    "#### Test Specification",
                    f"**Given**: {', '.join(scenario.given_steps[:2])}",
                    f"**When**: {', '.join(scenario.when_steps[:2])}",
                    f"**Then**: {', '.join(scenario.then_steps[:2])}",
                    "",
                ])

                # Generate complete pytest code
                test_code = generate_pytest_test_code(
                    req, criterion, i, scenario, edge_cases
                )

                lines.extend([
                    f"#### 🔴 Red: Write Failing Test",
                    "",
                    f"**File**: `tests/test_{safe_id}.py`",
                    "",
                    "```python",
                    test_code,
                    "```",
                    "",
                    "#### 🟢 Green: Minimal Implementation",
                    "",
                    "```python",
                    f"def {function_id}(input_data: dict) -> dict:",
                    f'    """Minimal implementation for {req.id}."""',
                    "    # Validate preconditions",
                ])

                for precond in contracts.preconditions[:2]:
                    lines.append(f"    # Precondition: {precond}")

                lines.extend([
                    "    if input_data is None:",
                    "        raise ValueError('input cannot be None')",
                    "",
                    "    # Minimal implementation",
                    "    return {",
                    "        'status': 'success',",
                    "        'id': input_data.get('id'),",
                    "    }",
                    "```",
                    "",
                    "#### 🔵 Refactor: Improved Implementation",
                    "",
                    "```python",
                    "from typing import Any",
                    "",
                    "",
                    f"def {function_id}(input_data: dict[str, Any]) -> dict[str, Any]:",
                    f'    """',
                    f"    {req.description[:60]}",
                    "",
                    "    Preconditions:",
                ])

                for precond in contracts.preconditions[:3]:
                    lines.append(f"        - {precond}")

                lines.extend([
                    "",
                    "    Postconditions:",
                ])

                for postcond in contracts.postconditions[:3]:
                    lines.append(f"        - {postcond}")

                lines.extend([
                    '    """',
                    "    # Design-by-contract: Check preconditions",
                    "    if input_data is None:",
                    "        raise ValueError('input_data cannot be None')",
                    "    if not isinstance(input_data, dict):",
                    "        raise TypeError('input_data must be a dict')",
                    "",
                    "    # Core implementation",
                    "    result = {",
                    "        'status': 'success',",
                    "        'id': input_data.get('id'),",
                    "        'processed': True,",
                    "    }",
                    "",
                    "    # Design-by-contract: Verify postconditions",
                    "    assert result['status'] in ('success', 'error')",
                    "    assert 'id' in result",
                    "",
                    "    return result",
                    "```",
                    "",
                    "#### Success Criteria",
                    f"- [ ] Test fails for right reason (Red) - `pytest tests/test_{safe_id}.py -v`",
                    "- [ ] Test passes with minimal code (Green)",
                    "- [ ] Code refactored, tests still pass (Refactor)",
                    "- [ ] Preconditions validated",
                    "- [ ] Postconditions verified",
                    "",
                ])

        # Add success criteria
        lines.extend([
            "## Overall Success Criteria",
            "",
            "### Automated",
            f"- [ ] All tests pass: `pytest tests/test_{safe_id}.py -v`",
            "- [ ] Type checking: `mypy .`",
            "- [ ] Lint: `ruff check .`",
            "",
            "### Manual",
            "- [ ] All behaviors implemented",
            "- [ ] Code reviewed",
            "- [ ] Documentation updated",
            "- [ ] Design contracts satisfied",
        ])

        return "\n".join(lines)

    def execute(
        self,
        plan_name: str,
        hierarchy_path: str,
    ) -> PhaseResult:
        """Execute TDD planning phase - generate one plan file per requirement.

        For each RequirementNode in the hierarchy, generates an individual
        TDD plan file with test specifications and Red-Green-Refactor cycles,
        then runs a review session for each plan.

        Args:
            plan_name: Base name for the plan files
            hierarchy_path: Path to hierarchy JSON file on disk

        Returns:
            PhaseResult with list of generated plan file paths
        """
        started_at = datetime.now()
        artifacts: list[str] = []
        errors: list[str] = []
        cwa_entry_ids: list[str] = []
        reviews_completed = 0
        review_failures = 0

        try:
            # Load hierarchy from file on disk
            hierarchy = self._load_hierarchy(hierarchy_path)

            # Collect requirements with acceptance criteria (skip empty parents)
            requirements_to_process = self._collect_requirements_with_criteria(hierarchy)
            total_reqs = len(requirements_to_process)
            logger.info(
                f"Found {total_reqs} requirements with acceptance criteria "
                f"(out of {len(hierarchy.requirements)} top-level requirements)"
            )

            # Print summary for user validation
            print(f"\n{'='*60}")
            print(f"TDD Planning: Processing {total_reqs} requirements")
            print(f"{'='*60}")
            for i, req in enumerate(requirements_to_process, 1):
                criteria_count = len(req.acceptance_criteria)
                print(f"  [{i}/{total_reqs}] {req.id}: {criteria_count} acceptance criteria")
            print(f"{'='*60}\n")

            # Generate individual plan for each requirement with criteria
            for idx, req in enumerate(requirements_to_process, 1):
                criteria_count = len(req.acceptance_criteria)
                print(f"[{idx}/{total_reqs}] Processing {req.id} ({criteria_count} criteria)...", end=" ", flush=True)

                try:
                    plan_path, review_result = self._generate_requirement_tdd_plan(
                        req, plan_name
                    )
                    if plan_path:
                        artifacts.append(str(plan_path))

                        # Store in CWA
                        content = plan_path.read_text(encoding="utf-8")
                        entry_id = self._store_plan_in_cwa(str(plan_path), content)
                        cwa_entry_ids.append(entry_id)

                        # Track review status
                        review_status = ""
                        if review_result and review_result.get("success"):
                            reviews_completed += 1
                            review_status = " + review"
                        elif review_result is not None:
                            # Review was attempted but failed
                            review_failures += 1
                            review_status = " (review failed)"

                        print(f"OK{review_status}")
                        print(f"       -> {plan_path}")
                    else:
                        print("SKIPPED (no output)")
                except Exception as req_error:
                    errors.append(f"Failed to generate plan for {req.id}: {req_error}")
                    print(f"FAILED: {req_error}")

            # Print final summary
            print(f"\n{'='*60}")
            print("TDD Planning Complete")
            print(f"  Plans generated: {len(artifacts)}/{total_reqs}")
            print(f"  Reviews completed: {reviews_completed}")
            if review_failures > 0:
                print(f"  Review failures: {review_failures}")
            if errors:
                print(f"  Errors: {len(errors)}")
            print(f"{'='*60}\n")

            # Determine status based on results
            if errors and not artifacts:
                status = PhaseStatus.FAILED
            elif errors or review_failures > 0:
                status = PhaseStatus.PARTIAL
            else:
                status = PhaseStatus.COMPLETE

            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            return PhaseResult(
                phase_type=PhaseType.TDD_PLANNING,
                status=status,
                artifacts=artifacts,
                errors=errors,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                metadata={
                    "cwa_entry_ids": cwa_entry_ids,
                    "requirements_count": len(requirements_to_process),
                    "top_level_requirements": len(hierarchy.requirements),
                    "plans_generated": len(artifacts),
                    "hierarchy_path": hierarchy_path,
                    "reviews_completed": reviews_completed,
                    "review_failures": review_failures,
                },
            )

        except FileNotFoundError as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            return PhaseResult(
                phase_type=PhaseType.TDD_PLANNING,
                status=PhaseStatus.FAILED,
                errors=[str(e)],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
            )

        except json.JSONDecodeError as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            return PhaseResult(
                phase_type=PhaseType.TDD_PLANNING,
                status=PhaseStatus.FAILED,
                errors=[f"Invalid JSON: {e}"],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
            )

        except Exception as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            return PhaseResult(
                phase_type=PhaseType.TDD_PLANNING,
                status=PhaseStatus.FAILED,
                errors=[str(e)],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                metadata={"exception_type": type(e).__name__},
            )

    def execute_with_checkpoint(
        self,
        plan_name: str,
        hierarchy_path: str,
        auto_approve: bool = False,
    ) -> PhaseResult:
        """Execute TDD planning phase with interactive checkpoint.

        After planning completes, prompts user for action unless auto_approve is True.

        Args:
            plan_name: Name for the plan
            hierarchy_path: Path to hierarchy JSON file on disk
            auto_approve: If True, skip user prompts

        Returns:
            PhaseResult with plan artifacts and user action
        """
        result = self.execute(
            plan_name=plan_name,
            hierarchy_path=hierarchy_path,
        )

        # If failed or auto-approve, return immediately
        if result.status == PhaseStatus.FAILED or auto_approve:
            if auto_approve and result.status == PhaseStatus.COMPLETE:
                result.metadata["user_action"] = "continue"
            return result

        # Prompt user for action
        action = prompt_tdd_planning_action()
        result.metadata["user_action"] = action

        if action == "continue":
            return result
        elif action == "revise":
            # For TDD planning, revision means regenerating with feedback
            # The feedback would need to be handled at the pipeline level
            print("\nEnter feedback for revision (empty line to finish):")
            feedback = collect_multiline_input("> ")
            result.metadata["revision_feedback"] = feedback
            result.metadata["needs_revision"] = True
            return result
        elif action == "restart":
            # Indicate restart needed
            result.metadata["needs_restart"] = True
            return result
        elif action == "exit":
            result.metadata["user_exit"] = True
            return result
        else:
            # Unknown action, treat as continue
            return result
