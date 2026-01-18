---
title: "Behavior 6: Process Single Requirement (3-Session Loop)"
description: "Execute 3-session TDD planning loop for a single requirement"
plan_id: "2026-01-18-tdd-refactor-tdd-planning-phase-llm-driven"
behavior_number: 6
status: "complete"
related_behaviors: [3, 4, 5]
dependencies: [3, 4, 5]
---

# Behavior 6: Process Single Requirement (3-Session Loop)

## Summary

Orchestrate the 3-session TDD planning loop for a single requirement: generate initial plan, review plan, then enhance plan using review feedback. Handle failures gracefully at each stage.

## Beads Workflow Integration

Track this behavior in Beads with these commands:

```bash
# Create issue for this behavior (if not already created)
bd create --title="Behavior 6: Process Single Requirement (3-Session Loop)" --type=task --priority=2

# View all open issues related to the plan
bd list --status=open

# Mark this behavior as in-progress when starting
bd update <id> --status=in_progress

# When behavior is complete, close the issue
bd close <id>

# View details of specific behavior
bd show <id>

# Sync to remote when work is complete
bd sync
```

## Test Specification

**Given**: Single RequirementNode + research doc path
**When**: `_process_requirement(requirement, research_doc_path)` is called
**Then**: 3 sessions executed (generate → review → enhance), final plan path returned

### Edge Cases

- Session 1 fails (skip sessions 2 & 3, return None)
- Session 2 fails (skip session 3, return plan from session 1)
- Session 3 fails (return plan from session 1, log warning)
- All sessions succeed (return enhanced plan path)

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `silmari_rlm_act/tests/test_tdd_planning_phase.py`

```python
def test_process_requirement_full_success(tmp_path):
    """Test: Process requirement through all 3 sessions successfully."""
    # Arrange
    from planning_pipeline.models import RequirementNode

    requirement = RequirementNode(
        id="REQ_001",
        description="Test requirement",
        type="parent",
        acceptance_criteria=["Criterion 1"]
    )

    research_doc = tmp_path / "research.md"
    research_doc.write_text("# Research")

    cwa = CWAIntegration(project_path=tmp_path)
    phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

    # Mock all three Claude calls
    with patch.object(phase, '_generate_initial_plan') as mock_gen, \
         patch.object(phase, '_review_plan') as mock_rev, \
         patch.object(phase, '_enhance_plan') as mock_enh:

        plan_path = tmp_path / "plan.md"
        plan_path.write_text("Plan")
        review_path = tmp_path / "review.md"
        review_path.write_text("Review")

        mock_gen.return_value = plan_path
        mock_rev.return_value = review_path
        mock_enh.return_value = True

        # Act
        result_path = phase._process_requirement(requirement, str(research_doc))

    # Assert
    assert result_path == plan_path
    assert mock_gen.called
    assert mock_rev.called
    assert mock_enh.called


def test_process_requirement_session1_fails(tmp_path):
    """Test: If session 1 fails, skip sessions 2 & 3."""
    # Arrange
    from planning_pipeline.models import RequirementNode

    requirement = RequirementNode(
        id="REQ_002",
        description="Test",
        type="parent"
    )

    cwa = CWAIntegration(project_path=tmp_path)
    phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

    # Mock session 1 failure
    with patch.object(phase, '_generate_initial_plan', return_value=None) as mock_gen, \
         patch.object(phase, '_review_plan') as mock_rev, \
         patch.object(phase, '_enhance_plan') as mock_enh:

        # Act
        result = phase._process_requirement(requirement, None)

    # Assert
    assert result is None
    assert mock_gen.called
    assert not mock_rev.called  # Should skip
    assert not mock_enh.called  # Should skip


def test_process_requirement_session2_fails(tmp_path):
    """Test: If session 2 fails, skip session 3, return session 1 plan."""
    # Arrange
    from planning_pipeline.models import RequirementNode

    requirement = RequirementNode(
        id="REQ_003",
        description="Test",
        type="parent"
    )

    cwa = CWAIntegration(project_path=tmp_path)
    phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

    plan_path = tmp_path / "plan.md"
    plan_path.write_text("Plan")

    # Mock session 1 success, session 2 failure
    with patch.object(phase, '_generate_initial_plan', return_value=plan_path), \
         patch.object(phase, '_review_plan', return_value=None) as mock_rev, \
         patch.object(phase, '_enhance_plan') as mock_enh:

        # Act
        result = phase._process_requirement(requirement, None)

    # Assert
    assert result == plan_path  # Returns session 1 plan
    assert mock_rev.called
    assert not mock_enh.called  # Should skip


def test_process_requirement_session3_fails(tmp_path):
    """Test: If session 3 fails, return session 1 plan with warning."""
    # Arrange
    from planning_pipeline.models import RequirementNode

    requirement = RequirementNode(
        id="REQ_004",
        description="Test",
        type="parent"
    )

    cwa = CWAIntegration(project_path=tmp_path)
    phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

    plan_path = tmp_path / "plan.md"
    plan_path.write_text("Original plan")
    review_path = tmp_path / "review.md"
    review_path.write_text("Review")

    # Mock sessions 1 & 2 success, session 3 failure
    with patch.object(phase, '_generate_initial_plan', return_value=plan_path), \
         patch.object(phase, '_review_plan', return_value=review_path), \
         patch.object(phase, '_enhance_plan', return_value=False):

        # Act
        result = phase._process_requirement(requirement, None)

    # Assert
    assert result == plan_path  # Returns unenhanced plan
    assert plan_path.read_text() == "Original plan"  # Unchanged
```

### 🟢 Green: Minimal Implementation

**File**: `silmari_rlm_act/phases/tdd_planning.py`

```python
def _process_requirement(
    self,
    requirement: RequirementNode,
    research_doc_path: Optional[str] = None,
) -> Optional[Path]:
    """Process requirement through 3-session TDD planning loop.

    Sessions:
    1. Generate initial plan
    2. Review plan
    3. Enhance plan using review

    Args:
        requirement: Requirement to process
        research_doc_path: Optional research document path

    Returns:
        Path to final plan file, or None if session 1 failed
    """
    print(f"\n{'='*60}")
    print(f"Processing requirement: {requirement.id}")
    print(f"{'='*60}")

    # Session 1: Generate initial plan
    print(f"\n[Session 1/3] Generating initial plan...")
    plan_path = self._generate_initial_plan(requirement, research_doc_path)
    if not plan_path:
        print(f"❌ Session 1 failed for {requirement.id}")
        return None
    print(f"✓ Initial plan created: {plan_path}")

    # Session 2: Review plan
    print(f"\n[Session 2/3] Reviewing plan...")
    review_path = self._review_plan(plan_path)
    if not review_path:
        print(f"⚠️  Session 2 failed, keeping unreviewed plan")
        return plan_path
    print(f"✓ Review created: {review_path}")

    # Session 3: Enhance plan
    print(f"\n[Session 3/3] Enhancing plan with review feedback...")
    success = self._enhance_plan(plan_path, review_path)
    if not success:
        print(f"⚠️  Session 3 failed, keeping unenhanced plan")
        return plan_path
    print(f"✓ Plan enhanced: {plan_path}")

    return plan_path
```

### 🔵 Refactor: Improve Code

Extract session execution to make testing easier:

```python
def _execute_session(
    self,
    session_name: str,
    session_func: callable,
    *args,
    **kwargs
) -> tuple[bool, Any]:
    """Execute a session and return success status + result.

    Args:
        session_name: Display name for logging
        session_func: Function to execute
        *args, **kwargs: Arguments for session_func

    Returns:
        Tuple of (success: bool, result: Any)
    """
    print(f"\n[{session_name}]")
    result = session_func(*args, **kwargs)
    success = result is not None and result is not False

    if success:
        print(f"✓ {session_name} completed")
    else:
        print(f"⚠️  {session_name} failed")

    return success, result
```

## Success Criteria (Tracking Matrix)

### Automated Tests

- [x] Test fails for right reason (Red): Method doesn't exist
- [x] Tests pass (Green): All 4 tests pass
- [x] All tests pass: `pytest silmari_rlm_act/tests/test_tdd_planning_phase.py -v`
- [x] Type checking passes: `mypy silmari_rlm_act/phases/tdd_planning.py`

### Manual Verification

- [x] Three sessions execute in order
- [x] Failures handled gracefully at each stage
- [x] Progress printed to console for user feedback

### Beads Workflow Tracking

```bash
# When starting the behavior
bd update <id> --status=in_progress

# Once all tests pass and implementation is complete
bd update <id> --status=in_progress  # Keep in-progress while cleaning up

# After final verification and cleanup
bd close <id>

# Sync changes to remote
bd sync

# Verify issue is closed
bd show <id>
```

## Notes

- This is the core orchestration method for the 3-session workflow
- Failures cascade: if session 1 fails, sessions 2 & 3 are skipped
- Sessions 2 & 3 can fail independently without affecting the initial plan
- Console output provides clear progress visibility
