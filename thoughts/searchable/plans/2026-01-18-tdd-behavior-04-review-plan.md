---
title: "Behavior 4: Review Plan via Claude Session"
description: "Invoke Claude with review_plan template to review and provide feedback on TDD plan"
plan_id: "2026-01-18-tdd-refactor-tdd-planning-phase-llm-driven"
behavior_number: 4
status: "complete"
related_behaviors: [3, 5, 6]
dependencies: [3]
---

# Behavior 4: Review Plan via Claude Session

## Summary

Invoke Claude with the review_plan.md template to review the generated TDD plan and provide feedback. Create a review file with -REVIEW suffix containing Claude's analysis.

## Beads Workflow Integration

Track this behavior in Beads with these commands:

```bash
# Create issue for this behavior (if not already created)
bd create --title="Behavior 4: Review Plan via Claude Session" --type=task --priority=2

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

**Given**: Generated TDD plan file path
**When**: `_review_plan(plan_path)` is called
**Then**: Claude session invoked with review_plan.md + plan content, review file created with -REVIEW suffix, review file path returned

### Edge Cases

- Plan file doesn't exist (return None)
- Claude returns error (handle gracefully)
- Review file already exists (overwrite)

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `silmari_rlm_act/tests/test_tdd_planning_phase.py`

```python
def test_review_plan_success(tmp_path):
    """Test: Review plan via Claude with successful response."""
    # Arrange
    plan_content = """# Test TDD Plan
## Behavior 1
Some test specification
"""
    plan_path = tmp_path / "thoughts" / "searchable" / "plans" / "2026-01-18-tdd-test.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(plan_content)

    mock_result = {
        "success": True,
        "output": "# Plan Review\nLooks good with minor suggestions",
        "error": "",
        "elapsed": 8.0
    }

    cwa = CWAIntegration(project_path=tmp_path)
    phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

    # Act
    with patch('silmari_rlm_act.phases.tdd_planning.run_claude_sync', return_value=mock_result):
        review_path = phase._review_plan(plan_path)

    # Assert
    assert review_path is not None
    assert review_path.exists()
    assert "-REVIEW.md" in str(review_path)
    assert "2026-01-18-tdd-test-REVIEW.md" in str(review_path)

    review_content = review_path.read_text()
    assert "Plan Review" in review_content


def test_review_plan_missing_file(tmp_path):
    """Test: Handle missing plan file gracefully."""
    # Arrange
    cwa = CWAIntegration(project_path=tmp_path)
    phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

    nonexistent_path = tmp_path / "nonexistent.md"

    # Act
    review_path = phase._review_plan(nonexistent_path)

    # Assert
    assert review_path is None


def test_review_plan_prompt_structure(tmp_path):
    """Test: Verify review prompt contains instruction + plan content."""
    # Arrange
    plan_content = "# TDD Plan\nTest behaviors"
    plan_path = tmp_path / "plan.md"
    plan_path.write_text(plan_content)

    # Create review_plan.md template
    template_dir = tmp_path / ".claude" / "commands"
    template_dir.mkdir(parents=True, exist_ok=True)
    template_path = template_dir / "review_plan.md"
    template_path.write_text("# Review Plan\nInstructions for reviewing")

    cwa = CWAIntegration(project_path=tmp_path)
    phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

    mock_result = {"success": True, "output": "Review", "error": "", "elapsed": 5.0}

    # Act
    with patch('silmari_rlm_act.phases.tdd_planning.run_claude_sync', return_value=mock_result) as mock_claude:
        phase._review_plan(plan_path)

    # Assert
    assert mock_claude.called
    prompt = mock_claude.call_args[0][0]

    assert "review_plan" in prompt.lower() or "review" in prompt.lower()
    assert str(plan_path) in prompt
    assert "TDD Plan" in prompt or plan_content in prompt
```

### 🟢 Green: Minimal Implementation

**File**: `silmari_rlm_act/phases/tdd_planning.py`

```python
def _review_plan(self, plan_path: Path) -> Optional[Path]:
    """Review TDD plan using Claude.

    Args:
        plan_path: Path to plan file to review

    Returns:
        Path to review file, or None on error
    """
    if not plan_path.exists():
        print(f"Error: Plan file not found: {plan_path}")
        return None

    # Load review instruction template
    instruction = self._load_instruction_template("review_plan")
    if not instruction:
        return None

    # Read plan content
    plan_content = plan_path.read_text(encoding="utf-8")

    # Build prompt
    prompt = (
        f"Using the instruction template below, review the TDD implementation plan.\n\n"
        f"# Instruction Template\n{instruction}\n\n---\n\n"
        f"# Plan to Review\n**File**: `{plan_path}`\n\n{plan_content}\n\n"
        f"Please provide a comprehensive review following the template structure."
    )

    # Invoke Claude
    result = run_claude_sync(
        prompt=prompt,
        timeout=600,  # 10 minutes for review
        stream=True,
        cwd=self.project_path,
    )

    if not result["success"]:
        print(f"Error reviewing plan: {result['error']}")
        return None

    # Generate review file path (same name with -REVIEW suffix)
    review_path = plan_path.parent / plan_path.name.replace(".md", "-REVIEW.md")

    # Save review content
    review_path.write_text(result["output"], encoding="utf-8")

    return review_path
```

### 🔵 Refactor: Improve Code

No significant refactoring needed - implementation is clean.

## Success Criteria (Tracking Matrix)

### Automated Tests

- [x] Test fails for right reason (Red): Method doesn't exist
- [x] Tests pass (Green): All 5 tests pass
- [x] All tests pass: `pytest silmari_rlm_act/tests/test_tdd_planning_phase.py -v`
- [x] Type checking passes: `mypy silmari_rlm_act/phases/tdd_planning.py`

### Manual Verification

- [x] Review file created with -REVIEW suffix
- [x] Prompt contains review instruction + plan content
- [x] Missing files handled gracefully

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

- Uses 600s timeout for review
- Review file created with -REVIEW suffix before .md extension
- Reviews are separate files for manual inspection
