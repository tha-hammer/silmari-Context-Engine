# Phase 5: Phase Priority from Order

## Overview

Implement `IntegratedOrchestrator.create_phase_issues()` method that creates beads issues for phases with priority matching phase order (phase 1 = priority 1, phase 2 = priority 2, etc.).

## Dependencies

**Requires**: Phase 2, 3, 4 (needs working BeadsController with create_issue, add_dependency, sync)
**Blocks**: Phase 6 (Session Logging), Phase 8 (Integration)

## Changes Required

### Modify: `planning_pipeline/integrated_orchestrator.py`

Add `create_phase_issues()` method.

```python
# planning_pipeline/integrated_orchestrator.py:145-200
def create_phase_issues(
    self,
    phase_files: list[str],
    epic_title: str
) -> dict[str, Any]:
    """Create beads issues for phases with priority by order."""
    # Implementation here...
```

### Modify: `planning_pipeline/tests/test_integrated_orchestrator.py`

Add `TestPhaseIssueCreation` class.

```python
# planning_pipeline/tests/test_integrated_orchestrator.py:230-300
class TestPhaseIssueCreation:
    """Tests for phase issue creation with priority by order."""
    # Test methods here...
```

## Test Specification

**Given**: Phase files are created from a plan
**When**: Issues are created for phases
**Then**: Priority equals phase order (phase 1 = priority 1, phase 2 = priority 2)

### Test Cases

1. `test_creates_issues_with_priority_matching_phase_order` - Priority matches phase number
2. `test_skips_overview_file` - Overview (phase 00) is not created as issue

### Edge Cases

- Phase 0 (overview) → not created as issue
- Phase numbers extracted from filename pattern
- Dependencies linked in order (phase 2 depends on phase 1, etc.)

## Implementation

### Red Phase Test Code

```python
class TestPhaseIssueCreation:
    """Tests for phase issue creation with priority by order."""

    def test_creates_issues_with_priority_matching_phase_order(self, tmp_path):
        """Given phase files, creates issues with priority = phase number."""
        phase_files = [
            "thoughts/shared/plans/2026-01-01-feature-01-setup.md",
            "thoughts/shared/plans/2026-01-01-feature-02-core.md",
            "thoughts/shared/plans/2026-01-01-feature-03-ui.md",
        ]

        created_issues = []

        def mock_create(title, issue_type, priority):
            created_issues.append({"title": title, "priority": priority})
            return {"success": True, "data": {"id": f"issue-{len(created_issues)}"}}

        with patch.object(BeadsController, 'create_issue', side_effect=mock_create):
            with patch.object(BeadsController, 'add_dependency', return_value={"success": True}):
                with patch.object(BeadsController, 'sync', return_value={"success": True}):
                    orchestrator = IntegratedOrchestrator(tmp_path)
                    result = orchestrator.create_phase_issues(phase_files, "Epic Title")

        assert len(created_issues) == 3
        assert created_issues[0]["priority"] == 1
        assert created_issues[1]["priority"] == 2
        assert created_issues[2]["priority"] == 3

    def test_skips_overview_file(self, tmp_path):
        """Given overview file in list, skips it."""
        phase_files = [
            "thoughts/shared/plans/2026-01-01-feature-00-overview.md",
            "thoughts/shared/plans/2026-01-01-feature-01-setup.md",
        ]

        created_issues = []

        def mock_create(title, issue_type, priority):
            created_issues.append({"title": title, "priority": priority})
            return {"success": True, "data": {"id": f"issue-{len(created_issues)}"}}

        with patch.object(BeadsController, 'create_issue', side_effect=mock_create):
            with patch.object(BeadsController, 'add_dependency', return_value={"success": True}):
                with patch.object(BeadsController, 'sync', return_value={"success": True}):
                    orchestrator = IntegratedOrchestrator(tmp_path)
                    result = orchestrator.create_phase_issues(phase_files, "Epic Title")

        # Only 1 issue created (overview skipped)
        assert len(created_issues) == 1
        assert created_issues[0]["priority"] == 1
```

### Green Phase Implementation

```python
def create_phase_issues(
    self,
    phase_files: list[str],
    epic_title: str
) -> dict[str, Any]:
    """Create beads issues for phases with priority by order.

    Args:
        phase_files: List of phase file paths
        epic_title: Title for the epic issue

    Returns:
        Dictionary with epic_id and phase_issues list
    """
    # Separate overview from phase files
    actual_phases = []
    for f in phase_files:
        if "overview" not in f.lower() and "-00-" not in f:
            actual_phases.append(f)

    # Create epic
    epic_result = self.bd.create_epic(epic_title)
    epic_id = None
    if epic_result["success"] and isinstance(epic_result["data"], dict):
        epic_id = epic_result["data"].get("id")

    # Create issues with priority = phase order
    phase_issues = []
    for i, phase_file in enumerate(actual_phases, start=1):
        phase_name = Path(phase_file).stem.split('-', 2)[-1].replace('-', ' ').title()

        result = self.bd.create_issue(
            title=f"Phase {i}: {phase_name}",
            issue_type="task",
            priority=i  # Priority matches phase order
        )

        if result["success"] and isinstance(result["data"], dict):
            issue_id = result["data"].get("id")
            phase_issues.append({
                "phase": i,
                "file": phase_file,
                "issue_id": issue_id,
                "priority": i
            })

    # Link dependencies (each phase depends on previous)
    for i in range(1, len(phase_issues)):
        curr_id = phase_issues[i].get("issue_id")
        prev_id = phase_issues[i - 1].get("issue_id")
        if curr_id and prev_id:
            self.bd.add_dependency(curr_id, prev_id)

    self.bd.sync()

    return {
        "success": True,
        "epic_id": epic_id,
        "phase_issues": phase_issues
    }
```

## Success Criteria

### Automated

- [ ] Test fails for right reason (Red): `pytest planning_pipeline/tests/test_integrated_orchestrator.py::TestPhaseIssueCreation -v`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_integrated_orchestrator.py::TestPhaseIssueCreation -v`
- [ ] All tests pass: `pytest planning_pipeline/tests/`

### Manual (Human-Testable)

Run from project root with phase files:

```bash
python -c "
from pathlib import Path
from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

phase_files = [
    'thoughts/shared/plans/2026-01-01-feature-01-setup.md',
    'thoughts/shared/plans/2026-01-01-feature-02-core.md',
]
orchestrator = IntegratedOrchestrator(Path('.'))
result = orchestrator.create_phase_issues(phase_files, 'Test Epic')
print(f'Created {len(result[\"phase_issues\"])} phase issues')
for phase in result['phase_issues']:
    print(f'  Phase {phase[\"phase\"]}: {phase[\"issue_id\"]} (priority {phase[\"priority\"]})')
"
```

Then verify:
```bash
bd list --status=open
```

**Expected**: Issues created with correct priorities (1, 2, 3, etc.) and dependencies

## References

- `planning_pipeline/beads_controller.py:66-79` - create_issue, add_dependency methods
- Phase file naming pattern: `YYYY-MM-DD-feature-NN-description.md`
