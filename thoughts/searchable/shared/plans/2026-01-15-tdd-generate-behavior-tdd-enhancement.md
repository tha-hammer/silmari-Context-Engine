# _generate_behavior_tdd Enhancement TDD Implementation Plan

## Tracking

| Item | Beads ID | Status |
|------|----------|--------|
| **Epic** | `silmari-Context-Engine-84lvu` | in_progress |
| Behavior 1: Loop Over Requirements | `silmari-Context-Engine-ly806` | closed |
| Behavior 2: LLM Content Generation | `silmari-Context-Engine-t1gxv` | closed |
| Behavior 3: Review Plan Integration | `silmari-Context-Engine-f6dn2` | closed |

**Dependencies**: B1 → B2 → B3 (sequential implementation)

---

## Overview

This plan covers enhancing the `_generate_behavior_tdd()` function in `silmari_rlm_act/phases/tdd_planning.py` to:
1. Call an LLM (via Claude Agent SDK's `run_claude_sync()`) to generate actual test and implementation code instead of TODO placeholders
2. Generate one TDD plan file per RequirementNode
3. Loop over all requirements from the decomposition phase
4. Trigger a `review_plan` session after each plan is generated

## Current State Analysis

### Key Discoveries:
- Current implementation at `silmari_rlm_act/phases/tdd_planning.py:171-235` generates static templates with `assert False  # TODO: Implement`
- No LLM calls in `_generate_behavior_tdd()` - purely string templating
- Existing LLM patterns in `planning_pipeline/claude_runner.py:611-648` show how to call LLM via `run_claude_sync()`
- Test patterns in `silmari_rlm_act/tests/test_tdd_planning_phase.py` use pytest with tmp_path fixtures
- RequirementNode model at `planning_pipeline/models.py:109` has: id, description, type, acceptance_criteria, children

### Current Flow:
```
TDDPlanningPhase.execute()
    → _load_hierarchy() → RequirementHierarchy
    → _generate_plan_document() → single markdown string
        → for req in hierarchy.requirements:
            → _generate_requirement_section(req)
                → for criterion in acceptance_criteria:
                    → _generate_behavior_tdd(req_id, num, criterion)  # Returns list[str] of static template
    → _save_plan() → single file
```

## Desired End State

### Observable Behaviors:
1. Given a RequirementHierarchy with 5 requirements, when `execute()` is called, then 5 separate TDD plan files are generated
2. Given a RequirementNode, when `_generate_behavior_tdd()` is called, then actual test code is generated (not TODO placeholders)
3. Given a generated TDD plan file, when complete, then a review session is automatically initiated
4. Given Agent SDK unavailable, when `_generate_behavior_tdd()` is called, then graceful fallback to template behavior

### Proposed Flow:
```
TDDPlanningPhase.execute()
    → _load_hierarchy() → RequirementHierarchy
    → for req in hierarchy.requirements:
        → _generate_requirement_tdd_plan(req)  # NEW: calls LLM for one requirement
            → _call_llm_for_tdd_generation(req)  # NEW: run_claude_sync() call
            → _save_requirement_plan(req, content)  # NEW: writes individual file
            → _run_review_session(plan_path)  # NEW: fresh review session
    → Return list of all plan paths
```

## What We're NOT Doing

- Not modifying the RequirementNode or RequirementHierarchy models
- Not changing the decomposition phase
- Not creating a new phase (enhancing existing TDDPlanningPhase)
- Not adding codebase research step (that's a separate enhancement)

## Testing Strategy

- **Framework**: pytest
- **Test Types**: Unit tests for individual methods, integration tests for full flow
- **Mocking Strategy**: Mock `run_claude_sync` calls, mock file I/O for unit tests
- **Fixtures**: Use `tmp_path` for file operations, mock `CWAIntegration`

---

## Behavior 1: Loop Over Requirements to Generate Individual Plans
<!-- beads: silmari-Context-Engine-ly806 -->

### Test Specification
**Given**: A RequirementHierarchy with 3 RequirementNodes (REQ_001, REQ_002, REQ_003)
**When**: `execute()` is called
**Then**: 3 separate plan files are created, one for each requirement

**Edge Cases**:
- Empty hierarchy (0 requirements) → no files created
- Hierarchy with nested children → only top-level requirements get files
- Single requirement → exactly 1 file created

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `silmari_rlm_act/tests/test_tdd_planning_phase.py`
```python
class TestIndividualPlanGeneration:
    """Behavior 1: Generate individual plan files per requirement."""

    def test_generates_one_file_per_requirement(self, tmp_path: Path) -> None:
        """Given 3 requirements, when execute(), then 3 plan files created."""
        # Arrange
        hierarchy_data = {
            "requirements": [
                {"id": "REQ_001", "description": "User login", "type": "parent",
                 "children": [], "acceptance_criteria": ["Given creds, when login, then authenticated"]},
                {"id": "REQ_002", "description": "User logout", "type": "parent",
                 "children": [], "acceptance_criteria": ["Given session, when logout, then session ends"]},
                {"id": "REQ_003", "description": "Password reset", "type": "parent",
                 "children": [], "acceptance_criteria": ["Given email, when reset, then link sent"]},
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Act
        result = phase.execute(plan_name="test-plan", hierarchy_path=str(hierarchy_path))

        # Assert
        assert result.status == PhaseStatus.COMPLETE
        assert len(result.artifacts) == 3
        for artifact_path in result.artifacts:
            assert Path(artifact_path).exists()
            assert "REQ_" in artifact_path

    def test_handles_empty_hierarchy(self, tmp_path: Path) -> None:
        """Given 0 requirements, when execute(), then 0 files created."""
        hierarchy_data = {"requirements": [], "metadata": {}}
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test-plan", hierarchy_path=str(hierarchy_path))

        assert result.status == PhaseStatus.COMPLETE
        assert len(result.artifacts) == 0
```

#### 🟢 Green: Minimal Implementation
**File**: `silmari_rlm_act/phases/tdd_planning.py`
```python
def execute(
    self,
    plan_name: str,
    hierarchy_path: str,
) -> PhaseResult:
    """Execute TDD planning phase - generate one plan file per requirement."""
    started_at = datetime.now()

    try:
        hierarchy = self._load_hierarchy(hierarchy_path)
        artifacts = []

        # Generate individual plan for each requirement
        for req in hierarchy.requirements:
            plan_path = self._generate_requirement_tdd_plan(req, plan_name)
            if plan_path:
                artifacts.append(str(plan_path))

        completed_at = datetime.now()
        duration = (completed_at - started_at).total_seconds()

        return PhaseResult(
            phase_type=PhaseType.TDD_PLANNING,
            status=PhaseStatus.COMPLETE,
            artifacts=artifacts,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            metadata={
                "requirements_count": len(hierarchy.requirements),
                "plans_generated": len(artifacts),
            },
        )
    except Exception as e:
        # ... error handling
        pass


def _generate_requirement_tdd_plan(
    self,
    req: RequirementNode,
    plan_name: str,
) -> Optional[Path]:
    """Generate TDD plan file for a single requirement."""
    # Minimal: just create file structure
    date_str = datetime.now().strftime("%Y-%m-%d")
    plan_dir = self.project_path / "thoughts" / "searchable" / "shared" / "plans"
    plan_dir.mkdir(parents=True, exist_ok=True)

    plan_path = plan_dir / f"{date_str}-tdd-{plan_name}-{req.id.lower()}.md"

    # Generate content (will be enhanced in Behavior 2)
    content = self._generate_plan_content_for_requirement(req)
    plan_path.write_text(content, encoding="utf-8")

    return plan_path
```

#### 🔵 Refactor: Improve Code
**File**: `silmari_rlm_act/phases/tdd_planning.py`
```python
def execute(
    self,
    plan_name: str,
    hierarchy_path: str,
) -> PhaseResult:
    """Execute TDD planning phase - generate one plan file per requirement.

    For each RequirementNode in the hierarchy:
    1. Generate TDD plan content via LLM session
    2. Write individual plan file
    3. Run review session (post-generation)

    Args:
        plan_name: Base name for the plan files
        hierarchy_path: Path to hierarchy JSON file

    Returns:
        PhaseResult with list of generated plan file paths
    """
    started_at = datetime.now()
    artifacts: list[str] = []
    errors: list[str] = []

    try:
        hierarchy = self._load_hierarchy(hierarchy_path)

        for req in hierarchy.requirements:
            try:
                plan_path = self._generate_requirement_tdd_plan(req, plan_name)
                if plan_path:
                    artifacts.append(str(plan_path))
            except Exception as req_error:
                errors.append(f"Failed to generate plan for {req.id}: {req_error}")

        status = PhaseStatus.COMPLETE if not errors else PhaseStatus.PARTIAL
        completed_at = datetime.now()

        return PhaseResult(
            phase_type=PhaseType.TDD_PLANNING,
            status=status,
            artifacts=artifacts,
            errors=errors,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=(completed_at - started_at).total_seconds(),
            metadata={
                "requirements_count": len(hierarchy.requirements),
                "plans_generated": len(artifacts),
                "errors_count": len(errors),
            },
        )

    except FileNotFoundError as e:
        return self._create_failed_result(started_at, str(e))
    except json.JSONDecodeError as e:
        return self._create_failed_result(started_at, f"Invalid JSON: {e}")
```

### Success Criteria
**Automated:**
- [x] Test fails for right reason (Red): `pytest silmari_rlm_act/tests/test_tdd_planning_phase.py::TestIndividualPlanGeneration -v`
- [x] Test passes (Green): `pytest silmari_rlm_act/tests/test_tdd_planning_phase.py::TestIndividualPlanGeneration -v`
- [x] All existing tests still pass: `pytest silmari_rlm_act/tests/test_tdd_planning_phase.py -v`
- [x] Type checking passes: `mypy silmari_rlm_act/phases/tdd_planning.py`

**Manual:**
- [x] Running with sample hierarchy creates correct number of files
- [x] File names follow pattern: `YYYY-MM-DD-tdd-{plan_name}-{req_id}.md`

---

## Behavior 2: LLM Session for TDD Content Generation (Using Agent SDK)
<!-- beads: silmari-Context-Engine-t1gxv -->

### Test Specification
**Given**: A RequirementNode with acceptance_criteria
**When**: `_generate_behavior_tdd()` is called
**Then**: Actual test code is generated (not TODO placeholders)

**Edge Cases**:
- Agent SDK unavailable → fallback to template
- LLM returns invalid response → graceful error handling
- Empty acceptance_criteria → generates placeholder guidance

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `silmari_rlm_act/tests/test_tdd_planning_phase.py`
```python
class TestLLMContentGeneration:
    """Behavior 2: LLM generates actual TDD content via Agent SDK."""

    def test_generates_actual_test_code_not_todos(self, tmp_path: Path) -> None:
        """Given requirement, when _generate_behavior_tdd(), then no TODO placeholders."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        req = RequirementNode(
            id="REQ_001",
            description="User login feature",
            type="parent",
            acceptance_criteria=["Given valid credentials, when login, then user authenticated"],
        )

        # Act
        content = phase._generate_plan_content_for_requirement(req)

        # Assert
        assert "assert False  # TODO" not in content
        assert "# TODO: Implement" not in content
        assert "# TODO: Add minimal implementation" not in content
        # Should have actual assertions
        assert "assert" in content.lower()

    def test_includes_given_when_then_from_criteria(self, tmp_path: Path) -> None:
        """Given requirement with criteria, when generate, then Given/When/Then extracted."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        req = RequirementNode(
            id="REQ_001",
            description="User login",
            type="parent",
            acceptance_criteria=["Given valid credentials, when login submitted, then session created"],
        )

        content = phase._generate_plan_content_for_requirement(req)

        assert "**Given**:" in content or "Given:" in content
        assert "**When**:" in content or "When:" in content
        assert "**Then**:" in content or "Then:" in content

    @patch("silmari_rlm_act.phases.tdd_planning.HAS_CLAUDE_SDK", False)
    def test_fallback_when_sdk_unavailable(self, tmp_path: Path) -> None:
        """Given Agent SDK unavailable, when generate, then fallback to template."""
        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        req = RequirementNode(
            id="REQ_001",
            description="User login",
            type="parent",
            acceptance_criteria=["Given creds, when login, then authenticated"],
        )

        content = phase._generate_plan_content_for_requirement(req)

        # Fallback should still produce valid markdown
        assert "# " in content
        assert "REQ_001" in content
```

#### 🟢 Green: Minimal Implementation
**File**: `silmari_rlm_act/phases/tdd_planning.py`
```python
# At top of file - import the Agent SDK runner
from planning_pipeline.claude_runner import run_claude_sync, HAS_CLAUDE_SDK


def _generate_plan_content_for_requirement(
    self,
    req: RequirementNode,
) -> str:
    """Generate TDD plan content for a single requirement via LLM."""
    if not HAS_CLAUDE_SDK:
        return self._generate_fallback_content(req)

    try:
        # Call LLM to generate TDD content
        tdd_content = self._call_llm_for_tdd(req)
        return tdd_content
    except Exception:
        return self._generate_fallback_content(req)


def _call_llm_for_tdd(self, req: RequirementNode) -> str:
    """Call LLM via Agent SDK to generate TDD content.

    Uses run_claude_sync() from planning_pipeline/claude_runner.py
    which wraps the claude_agent_sdk for synchronous LLM calls.
    """
    # Build prompt from requirement
    criteria_text = "\n".join(f"- {c}" for c in req.acceptance_criteria)

    prompt = f"""You are an expert TDD practitioner. Generate a complete TDD implementation plan.

## Requirement
ID: {req.id}
Description: {req.description}

## Acceptance Criteria
{criteria_text}

For EACH acceptance criterion, generate:

1. **Test Specification** with Given/When/Then format
2. **Red Phase**: Complete failing test code (NOT placeholder with TODO)
3. **Green Phase**: Minimal implementation to pass test
4. **Refactor Phase**: Improved implementation
5. **Success Criteria**: Automated and manual verification steps

CRITICAL RULES:
- Generate ACTUAL working test code, not placeholder comments
- Test code must have real assertions (assert x == y, assert x in y)
- NEVER use `assert False` or `# TODO` placeholders
- Include proper imports, fixtures, and test setup

### Example of GOOD test code:
```python
import pytest
from src.auth import AuthService

def test_user_login_with_valid_credentials():
    # Arrange
    auth = AuthService()
    credentials = {{"username": "testuser", "password": "validpass123"}}

    # Act
    result = auth.login(credentials)

    # Assert
    assert result.success is True
    assert result.session_id is not None
```

### Example of BAD test code (DO NOT GENERATE):
```python
def test_user_login():
    # TODO: Implement
    assert False
```

Generate the TDD plan now.
"""

    # Call Agent SDK via run_claude_sync
    result = run_claude_sync(
        prompt=prompt,
        timeout=300,  # 5 minutes
        stream=False,  # Don't stream for content generation
    )

    if result["success"] and result["output"]:
        return self._format_tdd_response(result["output"], req)
    else:
        raise RuntimeError(f"LLM call failed: {result.get('error', 'Unknown error')}")


def _generate_fallback_content(self, req: RequirementNode) -> str:
    """Fallback content when LLM unavailable."""
    lines = [
        f"# {req.id}: {req.description}",
        "",
        "## Test Specification",
        "",
    ]

    for i, criterion in enumerate(req.acceptance_criteria, 1):
        given, when, then = self._parse_behavior(criterion)
        lines.extend([
            f"### Behavior {i}",
            f"**Given**: {given}",
            f"**When**: {when}",
            f"**Then**: {then}",
            "",
        ])

    lines.extend([
        "## TDD Cycles",
        "",
        "_LLM content generation unavailable. Manual implementation required._",
        "",
    ])

    return "\n".join(lines)
```

#### 🔵 Refactor: Improve Code
**File**: `silmari_rlm_act/phases/tdd_planning.py`
```python
from planning_pipeline.claude_runner import run_claude_sync, HAS_CLAUDE_SDK
from typing import Any

# TDD Prompt template - can be customized or loaded from file
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
"""


def _call_llm_for_tdd(self, req: RequirementNode) -> str:
    """Call LLM via Agent SDK to generate comprehensive TDD content.

    This uses run_claude_sync() from planning_pipeline/claude_runner.py
    which wraps the claude_agent_sdk. The SDK provides:
    - Async iteration over streaming messages
    - Tool use handling
    - Permission management

    For TDD generation, we use non-streaming mode to get the
    complete output at once for easier parsing.

    Args:
        req: RequirementNode to generate TDD plan for

    Returns:
        Formatted markdown string with complete TDD cycles

    Raises:
        RuntimeError: If LLM call fails (caught by caller for fallback)
    """
    # Prepare context for LLM
    criteria_text = "\n".join(f"- {c}" for c in req.acceptance_criteria)

    prompt = TDD_GENERATION_PROMPT.format(
        req_id=req.id,
        req_description=req.description,
        criteria_text=criteria_text,
    )

    # Call Agent SDK via synchronous wrapper
    result = run_claude_sync(
        prompt=prompt,
        timeout=300,
        stream=False,  # Get complete response
    )

    if not result["success"]:
        raise RuntimeError(f"LLM call failed: {result.get('error', 'Unknown error')}")

    if not result["output"]:
        raise RuntimeError("LLM returned empty response")

    # Format and return
    return self._format_tdd_response(result["output"], req)


def _format_tdd_response(
    self,
    llm_output: str,
    req: RequirementNode,
) -> str:
    """Format LLM response into TDD plan markdown.

    Args:
        llm_output: Raw output from LLM
        req: RequirementNode for context

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
        llm_output,  # Include LLM-generated content
    ]

    return "\n".join(lines)
```

### Success Criteria
**Automated:**
- [x] Test fails for right reason (Red): `pytest silmari_rlm_act/tests/test_tdd_planning_phase.py::TestLLMContentGeneration -v`
- [x] Test passes (Green): `pytest silmari_rlm_act/tests/test_tdd_planning_phase.py::TestLLMContentGeneration -v`
- [x] All tests pass after refactor: `pytest silmari_rlm_act/tests/ -v`
- [x] Type checking: `mypy silmari_rlm_act/phases/tdd_planning.py`

**Manual:**
- [x] Generated content has actual assertions (not `assert False`)
- [x] Test code is syntactically valid Python
- [x] Given/When/Then format properly extracted

---

## Behavior 3: Review Plan Integration After Generation
<!-- beads: silmari-Context-Engine-f6dn2 -->

### Test Specification
**Given**: A TDD plan file has been generated for a requirement
**When**: The plan generation completes
**Then**: A fresh review session is initiated for that plan

**Edge Cases**:
- Review session fails → plan still saved, error logged
- Review unavailable → plan generation succeeds without review
- Multiple plans → each gets its own review session

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `silmari_rlm_act/tests/test_tdd_planning_phase.py`
```python
class TestReviewPlanIntegration:
    """Behavior 3: Review plan runs after TDD generation."""

    @patch("silmari_rlm_act.phases.tdd_planning.run_review_session")
    def test_review_session_called_after_plan_generated(
        self, mock_review: MagicMock, tmp_path: Path
    ) -> None:
        """Given plan generated, when complete, then review session initiated."""
        hierarchy_data = {
            "requirements": [
                {"id": "REQ_001", "description": "Login", "type": "parent",
                 "children": [], "acceptance_criteria": ["Given creds, when login, then session"]}
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        # Act
        result = phase.execute(plan_name="test", hierarchy_path=str(hierarchy_path))

        # Assert
        assert result.status == PhaseStatus.COMPLETE
        mock_review.assert_called_once()
        # Verify it was called with the plan path
        call_args = mock_review.call_args
        assert "tdd-test-req_001" in call_args[0][0].lower()

    @patch("silmari_rlm_act.phases.tdd_planning.run_review_session")
    def test_multiple_plans_each_get_review(
        self, mock_review: MagicMock, tmp_path: Path
    ) -> None:
        """Given 3 plans generated, when complete, then 3 review sessions."""
        hierarchy_data = {
            "requirements": [
                {"id": "REQ_001", "description": "Login", "type": "parent",
                 "children": [], "acceptance_criteria": ["criterion1"]},
                {"id": "REQ_002", "description": "Logout", "type": "parent",
                 "children": [], "acceptance_criteria": ["criterion2"]},
                {"id": "REQ_003", "description": "Reset", "type": "parent",
                 "children": [], "acceptance_criteria": ["criterion3"]},
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test", hierarchy_path=str(hierarchy_path))

        assert result.status == PhaseStatus.COMPLETE
        assert mock_review.call_count == 3

    @patch("silmari_rlm_act.phases.tdd_planning.run_review_session")
    def test_plan_saved_even_if_review_fails(
        self, mock_review: MagicMock, tmp_path: Path
    ) -> None:
        """Given review fails, when plan generated, then plan still saved."""
        mock_review.side_effect = Exception("Review service unavailable")

        hierarchy_data = {
            "requirements": [
                {"id": "REQ_001", "description": "Login", "type": "parent",
                 "children": [], "acceptance_criteria": ["criterion"]}
            ],
            "metadata": {},
        }
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps(hierarchy_data))

        cwa = CWAIntegration()
        phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(plan_name="test", hierarchy_path=str(hierarchy_path))

        # Plan should still be saved even if review failed
        assert len(result.artifacts) == 1
        assert Path(result.artifacts[0]).exists()
        # But should note the review failure
        assert "review_failed" in result.metadata or result.status == PhaseStatus.PARTIAL
```

#### 🟢 Green: Minimal Implementation
**File**: `silmari_rlm_act/phases/tdd_planning.py`
```python
def run_review_session(plan_path: str) -> dict[str, Any]:
    """Run review_plan skill on generated plan.

    This creates a fresh session to review the TDD plan
    following the review_plan skill criteria.

    Uses run_claude_sync() from planning_pipeline/claude_runner.py
    to invoke the Agent SDK.

    Args:
        plan_path: Path to the generated TDD plan file

    Returns:
        Review results dict with findings and amendments
    """
    review_prompt = f"""Review the TDD plan at {plan_path} using the review_plan criteria:
1. Contract Analysis - Are interfaces well-defined?
2. Interface Analysis - Are boundaries clear?
3. Promise Analysis - Are assertions verifiable?
4. Data Model Analysis - Are types correct?
5. API Analysis - Are endpoints documented?

Return findings and any amendments needed.
"""

    return run_claude_sync(
        prompt=review_prompt,
        timeout=300,
        stream=False,
    )


class TDDPlanningPhase:
    # ... existing code ...

    def _generate_requirement_tdd_plan(
        self,
        req: RequirementNode,
        plan_name: str,
    ) -> Optional[Path]:
        """Generate TDD plan file and run review session."""
        # Generate plan file
        plan_path = self._write_plan_file(req, plan_name)

        # Run review session (in fresh context)
        try:
            review_result = run_review_session(str(plan_path))
            self._save_review_results(plan_path, review_result)
        except Exception as e:
            # Log but don't fail - plan is still saved
            import logging
            logging.warning(f"Review session failed for {req.id}: {e}")

        return plan_path
```

#### 🔵 Refactor: Improve Code
**File**: `silmari_rlm_act/phases/tdd_planning.py`
```python
import logging
from typing import Any, Optional
from pathlib import Path

from planning_pipeline.claude_runner import run_claude_sync, HAS_CLAUDE_SDK

logger = logging.getLogger(__name__)


def run_review_session(plan_path: str) -> dict[str, Any]:
    """Run review_plan skill on generated TDD plan in a fresh session.

    Creates an independent LLM session to review the generated plan
    using the 5-step discrete analysis from review_plan:
    1. Contract Analysis
    2. Interface Analysis
    3. Promise Analysis
    4. Data Model Analysis
    5. API Analysis

    Uses run_claude_sync() which wraps the claude_agent_sdk for
    synchronous LLM calls.

    Args:
        plan_path: Absolute path to the generated TDD plan file

    Returns:
        Review results with:
        - success: bool
        - output: review findings text
        - error: error message if failed
    """
    review_prompt = f"""You are reviewing a TDD implementation plan.

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

    return run_claude_sync(
        prompt=review_prompt,
        timeout=300,
        stream=False,
    )


class TDDPlanningPhase:
    """Execute TDD planning phase with individual plans and reviews."""

    def _generate_requirement_tdd_plan(
        self,
        req: RequirementNode,
        plan_name: str,
    ) -> tuple[Optional[Path], Optional[dict[str, Any]]]:
        """Generate TDD plan file and run review session.

        Args:
            req: RequirementNode to generate plan for
            plan_name: Base name for the plan

        Returns:
            Tuple of (plan_path, review_result)
            Plan path is None if generation failed
            Review result is None if review failed or skipped
        """
        # Step 1: Generate and write plan file
        plan_path = self._write_plan_file(req, plan_name)
        if not plan_path:
            return None, None

        # Step 2: Run review session (in fresh context)
        review_result = None
        try:
            logger.info(f"Running review session for {req.id}")
            review_result = run_review_session(str(plan_path))

            if review_result.get("success"):
                # Save review alongside plan
                review_path = plan_path.with_suffix(".review.md")
                self._write_review_file(review_path, review_result)
                logger.info(f"Review saved to {review_path}")
            else:
                logger.warning(f"Review returned error for {req.id}: {review_result.get('error')}")

        except Exception as e:
            logger.warning(f"Review session failed for {req.id}: {e}")
            # Don't fail - plan is still saved

        return plan_path, review_result

    def _write_review_file(
        self,
        review_path: Path,
        review_result: dict[str, Any],
    ) -> None:
        """Write review results to companion file."""
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
```

### Success Criteria
**Automated:**
- [x] Test fails for right reason (Red): `pytest silmari_rlm_act/tests/test_tdd_planning_phase.py::TestReviewPlanIntegration -v`
- [x] Test passes (Green): `pytest silmari_rlm_act/tests/test_tdd_planning_phase.py::TestReviewPlanIntegration -v`
- [x] All tests pass after refactor: `pytest silmari_rlm_act/tests/ -v`

**Manual:**
- [x] Review file created alongside plan file
- [x] Review contains 5-step analysis
- [x] Plan saved even when review fails

---

## Implementation Order

1. **Behavior 1: Loop Over Requirements** - Foundation for per-requirement processing
2. **Behavior 2: LLM Content Generation** - Integrate Agent SDK calls into phase
3. **Behavior 3: Review Integration** - Add post-generation review

## Dependencies

- `planning_pipeline/claude_runner.py` - `run_claude_sync()` function and `HAS_CLAUDE_SDK` flag
- `claude_agent_sdk` - Underlying SDK (imported by claude_runner.py)
- pytest for testing

## Key API Reference

### run_claude_sync() from planning_pipeline/claude_runner.py

```python
def run_claude_sync(
    prompt: str,
    tools: Optional[list[str]] = None,
    timeout: int = 300,
    stream: bool = True,
    output_format: OutputFormat = "text",
    cwd: Optional[Path] = None,
) -> dict[str, Any]:
    """Run Claude Code via Agent SDK and return structured result.

    Returns:
        Dictionary with keys:
        - success: bool indicating if command completed successfully
        - output: text output from Claude
        - error: error message if any
        - elapsed: time in seconds
    """
```

### HAS_CLAUDE_SDK Flag

```python
# At planning_pipeline/claude_runner.py:48-68
try:
    from claude_agent_sdk import query
    from claude_agent_sdk.types import (
        ClaudeAgentOptions,
        AssistantMessage,
        ResultMessage,
        TextBlock,
        ToolUseBlock,
        ToolResultBlock,
    )
    HAS_CLAUDE_SDK = True
except ImportError:
    HAS_CLAUDE_SDK = False
```

Use this flag for graceful fallback when SDK is unavailable.

## References

- Research: `thoughts/searchable/research/2026-01-15-plan-generation-quality-improvement.md`
- Current Implementation: `silmari_rlm_act/phases/tdd_planning.py:171-235`
- Gold Standard: `create_tdd_plan` skill at `.claude/commands/create_tdd_plan.md`
- Test Patterns: `silmari_rlm_act/tests/test_tdd_planning_phase.py`
- Agent SDK Wrapper: `planning_pipeline/claude_runner.py:611-648`
- SDK Usage Examples: `silmari_rlm_act/phases/research_sdk.py`, `silmari_rlm_act/phases/implementation_sdk.py`
- Models: `planning_pipeline/models.py:109` (RequirementNode)
