# Phase 8: Integration Testing

## Overview

Create integration tests that verify the full orchestration workflow: get_project_info → get_feature_status → get_next_feature → sync_features_with_git. Also includes E2E manual test scenarios.

## Dependencies

**Requires**: All phases (1-7)
**Blocks**: None (final phase)

## Changes Required

### Modify: `planning_pipeline/tests/test_integrated_orchestrator.py`

Add `TestIntegratedOrchestratorFlow` class.

```python
# planning_pipeline/tests/test_integrated_orchestrator.py:370-450
class TestIntegratedOrchestratorFlow:
    """Integration tests for full orchestration workflow."""
    # Test methods here...
```

## Test Specification

**Given**: All orchestrator methods are implemented
**When**: Full workflow is executed
**Then**: Operations chain together correctly

### Test Cases

1. `test_full_workflow_with_mocked_beads` - Complete workflow with mocked external calls

### Integration Test Flow

1. Get project info from overview
2. Get feature status from beads
3. Get next ready feature
4. Sync features with git

## Implementation

### Integration Test Code

```python
class TestIntegratedOrchestratorFlow:
    """Integration tests for full orchestration workflow."""

    def test_full_workflow_with_mocked_beads(self, tmp_path):
        """Test complete workflow: get_project_info -> get_status -> get_next -> sync."""
        # Setup mock overview file
        plans_dir = tmp_path / "thoughts" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        overview = plans_dir / "2026-01-01-00-overview.md"
        overview.write_text("# Test Plan\n\n## Tech Stack\nPython, pytest")

        # Mock all external calls
        with patch('planning_pipeline.integrated_orchestrator.run_claude_sync') as mock_claude:
            mock_claude.return_value = {
                "success": True,
                "output": '{"name": "Test", "stack": "Python", "description": "Test project"}'
            }

            with patch.object(BeadsController, '_run_bd') as mock_bd:
                # Mock responses for different commands
                def bd_side_effect(*args, **kwargs):
                    cmd = args[0] if args else ""
                    if cmd == "list":
                        return {"success": True, "data": [
                            {"id": "p1", "status": "open", "dependencies": []},
                            {"id": "p2", "status": "open", "dependencies": [{"depends_on_id": "p1"}]}
                        ]}
                    elif cmd == "ready":
                        return {"success": True, "data": [{"id": "p1", "priority": 1}]}
                    elif cmd == "sync":
                        return {"success": True, "output": "Synced"}
                    return {"success": True, "data": {}}

                mock_bd.side_effect = bd_side_effect

                orchestrator = IntegratedOrchestrator(tmp_path)

                # Execute workflow
                info = orchestrator.get_project_info()
                assert info["name"] == "Test"

                status = orchestrator.get_feature_status()
                assert status["total"] == 2

                feature = orchestrator.get_next_feature()
                assert feature["id"] == "p1"

                sync_result = orchestrator.sync_features_with_git()
                assert sync_result == 0

    def test_workflow_with_session_logging(self, tmp_path):
        """Test workflow logs each step to session file."""
        with patch('planning_pipeline.integrated_orchestrator.run_claude_sync') as mock_claude:
            mock_claude.return_value = {
                "success": True,
                "output": '{"name": "Test", "stack": "Python", "description": "Test"}'
            }

            with patch.object(BeadsController, '_run_bd') as mock_bd:
                mock_bd.return_value = {"success": True, "data": []}

                orchestrator = IntegratedOrchestrator(tmp_path)
                session_id = "integration-test-001"

                # Execute workflow with logging
                info = orchestrator.get_project_info()
                orchestrator.log_session(session_id, "get_project_info", info)

                status = orchestrator.get_feature_status()
                orchestrator.log_session(session_id, "get_feature_status", status)

                feature = orchestrator.get_next_feature()
                orchestrator.log_session(session_id, "get_next_feature", {"feature": feature})

                sync_result = orchestrator.sync_features_with_git()
                orchestrator.log_session(session_id, "sync_features_with_git", {"result": sync_result})

        # Verify session log
        session_file = tmp_path / ".agent" / "sessions" / f"{session_id}.json"
        assert session_file.exists()

        import json
        logs = json.loads(session_file.read_text())
        assert len(logs) == 4
        assert logs[0]["action"] == "get_project_info"
        assert logs[1]["action"] == "get_feature_status"
        assert logs[2]["action"] == "get_next_feature"
        assert logs[3]["action"] == "sync_features_with_git"
```

## E2E Test Scenario (Manual)

### Prerequisites

1. Initialize beads: `bd init`
2. Create phase files in `thoughts/shared/plans/`

### Test Script

```bash
#!/bin/bash
# E2E test for IntegratedOrchestrator

# Step 1: Initialize project
echo "=== Step 1: Initialize project ==="
bd init --force

# Step 2: Create test phase files
echo "=== Step 2: Create test phase files ==="
mkdir -p thoughts/shared/plans
cat > thoughts/shared/plans/2026-01-01-test-00-overview.md << 'EOF'
# Test Feature

## Tech Stack
- Python 3.11
- pytest
- Click CLI
EOF

cat > thoughts/shared/plans/2026-01-01-test-01-setup.md << 'EOF'
# Phase 1: Setup

Create project structure.
EOF

cat > thoughts/shared/plans/2026-01-01-test-02-core.md << 'EOF'
# Phase 2: Core

Implement core functionality.
EOF

# Step 3: Run orchestrator workflow
echo "=== Step 3: Run orchestrator workflow ==="
python -c "
from pathlib import Path
from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

orchestrator = IntegratedOrchestrator(Path('.'))

# Get project info
print('Getting project info...')
info = orchestrator.get_project_info()
print(f'  Project: {info[\"name\"]}')
print(f'  Stack: {info[\"stack\"]}')

# Create phase issues
print('\\nCreating phase issues...')
phase_files = [
    'thoughts/shared/plans/2026-01-01-test-01-setup.md',
    'thoughts/shared/plans/2026-01-01-test-02-core.md',
]
result = orchestrator.create_phase_issues(phase_files, 'Test Feature')
print(f'  Created {len(result[\"phase_issues\"])} issues')

# Get feature status
print('\\nGetting feature status...')
status = orchestrator.get_feature_status()
print(f'  Total: {status[\"total\"]}')
print(f'  Remaining: {status[\"remaining\"]}')
print(f'  Blocked: {status[\"blocked\"]}')

# Get next feature
print('\\nGetting next feature...')
feature = orchestrator.get_next_feature()
if feature:
    print(f'  Next: {feature[\"id\"]} - {feature.get(\"title\", \"N/A\")}')
else:
    print('  No ready features')

# Sync
print('\\nSyncing...')
sync_result = orchestrator.sync_features_with_git()
print(f'  Result: {\"Success\" if sync_result == 0 else \"Failed\"}')

# Log session
print('\\nLogging session...')
orchestrator.log_session('e2e-test', 'full_workflow', {
    'info': info,
    'status': status,
    'next_feature': feature,
    'sync_result': sync_result
})
print('  Session logged')
"

# Step 4: Verify results
echo "=== Step 4: Verify results ==="
echo "Issues:"
bd list
echo ""
echo "Session log:"
cat .agent/sessions/e2e-test.json 2>/dev/null || echo "No session log found"

# Cleanup
echo "=== Cleanup ==="
rm -rf thoughts/shared/plans/2026-01-01-test-*.md
```

### Expected Results

1. Project info extracted from overview.md
2. Phase issues created with correct priorities (1, 2)
3. Dependencies linked (phase 2 depends on phase 1)
4. Feature status shows correct counts
5. Next feature returns phase 1 (not blocked)
6. Sync completes successfully
7. Session log contains all actions

## Success Criteria

### Automated

- [ ] Integration test passes: `pytest planning_pipeline/tests/test_integrated_orchestrator.py::TestIntegratedOrchestratorFlow -v`
- [ ] All unit tests still pass: `pytest planning_pipeline/tests/`

### Manual (Human-Testable)

Run the E2E test script above and verify:

1. [ ] No errors during execution
2. [ ] Issues visible in `bd list`
3. [ ] Session log contains all 4 actions
4. [ ] Feature priorities match phase order

## References

- All phase files (01-07)
- `planning_pipeline/integrated_orchestrator.py` - Complete implementation
- `planning_pipeline/beads_controller.py` - Extended BeadsController
