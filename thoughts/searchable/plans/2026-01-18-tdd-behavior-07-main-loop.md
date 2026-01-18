---
title: "Behavior 7: Process All Requirements (Main Loop)"
description: "Execute main loop to process all requirements in hierarchy"
plan_id: "2026-01-18-tdd-refactor-tdd-planning-phase-llm-driven"
beads_id: "silmari-Context-Engine-xqztn"
behavior_number: 7
status: "completed"
related_behaviors: [1, 6]
dependencies: [1, 6]
---

# Behavior 7: Process All Requirements (Main Loop)

## Summary

Process all top-level requirements in the hierarchy through the 3-session TDD planning loop. Collect plan artifacts, store in CWA, return PhaseResult with complete metadata.

## Test Specification

**Given**: RequirementHierarchy with N top-level requirements + research doc
**When**: New `execute()` method called
**Then**: Each requirement processed via `_process_requirement()`, all plan paths collected, PhaseResult returned with artifacts

### Edge Cases

- Empty hierarchy (0 requirements) - return success with empty artifacts
- Some requirements fail - continue processing others, return partial success
- All requirements fail - return failed status
- Research doc optional (None passed)

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `silmari_rlm_act/tests/test_tdd_planning_phase.py`

```python
def test_execute_multiple_requirements(tmp_path):
    """Test: Process multiple requirements, collect all plan paths."""
    # Arrange
    from planning_pipeline.models import RequirementNode, RequirementHierarchy

    req1 = RequirementNode(id="REQ_001", description="First", type="parent")
    req2 = RequirementNode(id="REQ_002", description="Second", type="parent")
    req3 = RequirementNode(id="REQ_003", description="Third", type="parent")

    hierarchy = RequirementHierarchy(requirements=[req1, req2, req3])
    hierarchy_file = tmp_path / "hierarchy.json"
    hierarchy_file.write_text(json.dumps(hierarchy.to_dict()))

    research_doc = tmp_path / "research.md"
    research_doc.write_text("# Research")

    cwa = CWAIntegration(project_path=tmp_path)
    phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

    # Mock _process_requirement to return paths
    plan_paths = [
        tmp_path / "plan1.md",
        tmp_path / "plan2.md",
        tmp_path / "plan3.md"
    ]
    for p in plan_paths:
        p.write_text("Plan")

    with patch.object(phase, '_process_requirement', side_effect=plan_paths):
        # Act
        result = phase.execute(
            hierarchy_path=str(hierarchy_file),
            research_doc_path=str(research_doc)
        )

    # Assert
    assert result.status == PhaseStatus.COMPLETE
    assert len(result.artifacts) == 3
    assert all(str(p) in result.artifacts for p in plan_paths)
    assert result.metadata["requirements_count"] == 3
    assert result.metadata["successful_plans"] == 3


def test_execute_partial_failure(tmp_path):
    """Test: Some requirements fail, continue with others."""
    # Arrange
    from planning_pipeline.models import RequirementNode, RequirementHierarchy

    req1 = RequirementNode(id="REQ_001", description="First", type="parent")
    req2 = RequirementNode(id="REQ_002", description="Second", type="parent")
    req3 = RequirementNode(id="REQ_003", description="Third", type="parent")

    hierarchy = RequirementHierarchy(requirements=[req1, req2, req3])
    hierarchy_file = tmp_path / "hierarchy.json"
    hierarchy_file.write_text(json.dumps(hierarchy.to_dict()))

    cwa = CWAIntegration(project_path=tmp_path)
    phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

    # Mock: req1 succeeds, req2 fails, req3 succeeds
    plan1 = tmp_path / "plan1.md"
    plan1.write_text("Plan 1")
    plan3 = tmp_path / "plan3.md"
    plan3.write_text("Plan 3")

    with patch.object(phase, '_process_requirement', side_effect=[plan1, None, plan3]):
        # Act
        result = phase.execute(hierarchy_path=str(hierarchy_file))

    # Assert
    assert result.status == PhaseStatus.COMPLETE  # Partial success still complete
    assert len(result.artifacts) == 2  # Only successful plans
    assert result.metadata["requirements_count"] == 3
    assert result.metadata["successful_plans"] == 2
    assert result.metadata["failed_plans"] == 1


def test_execute_empty_hierarchy(tmp_path):
    """Test: Empty hierarchy returns success with no artifacts."""
    # Arrange
    from planning_pipeline.models import RequirementHierarchy

    hierarchy = RequirementHierarchy(requirements=[])
    hierarchy_file = tmp_path / "hierarchy.json"
    hierarchy_file.write_text(json.dumps(hierarchy.to_dict()))

    cwa = CWAIntegration(project_path=tmp_path)
    phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

    # Act
    result = phase.execute(hierarchy_path=str(hierarchy_file))

    # Assert
    assert result.status == PhaseStatus.COMPLETE
    assert len(result.artifacts) == 0
    assert result.metadata["requirements_count"] == 0


def test_execute_stores_plans_in_cwa(tmp_path):
    """Test: Each successful plan stored in CWA."""
    # Arrange
    from planning_pipeline.models import RequirementNode, RequirementHierarchy

    req1 = RequirementNode(id="REQ_001", description="Test", type="parent")
    hierarchy = RequirementHierarchy(requirements=[req1])
    hierarchy_file = tmp_path / "hierarchy.json"
    hierarchy_file.write_text(json.dumps(hierarchy.to_dict()))

    cwa = CWAIntegration(project_path=tmp_path)
    phase = TDDPlanningPhase(project_path=tmp_path, cwa=cwa)

    plan_path = tmp_path / "plan.md"
    plan_path.write_text("# Plan Content")

    with patch.object(phase, '_process_requirement', return_value=plan_path), \
         patch.object(cwa, 'store_plan', return_value="cwa_entry_123") as mock_store:

        # Act
        result = phase.execute(hierarchy_path=str(hierarchy_file))

    # Assert
    assert mock_store.called
    call_args = mock_store.call_args[1]  # kwargs
    assert call_args["path"] == str(plan_path)
    assert "# Plan Content" in call_args["content"]
    assert "cwa_entry_ids" in result.metadata
```

### 🟢 Green: Minimal Implementation

**File**: `silmari_rlm_act/phases/tdd_planning.py`

Replace the entire `execute()` method (lines 318-400):

```python
def execute(
    self,
    hierarchy_path: str,
    research_doc_path: Optional[str] = None,
) -> PhaseResult:
    """Execute TDD planning phase with LLM-driven multi-session approach.

    For each top-level requirement in hierarchy:
    1. Generate initial plan using Claude + create_tdd_plan.md
    2. Review plan using Claude + review_plan.md
    3. Enhance plan using Claude + review feedback

    Args:
        hierarchy_path: Path to requirement hierarchy JSON file
        research_doc_path: Optional path to research document

    Returns:
        PhaseResult with plan artifacts and metadata
    """
    started_at = datetime.now()
    plan_paths: list[Path] = []
    cwa_entry_ids: list[str] = []
    failed_requirements: list[str] = []

    try:
        # Load hierarchy
        hierarchy = self._load_hierarchy(hierarchy_path)

        print(f"\n{'='*70}")
        print(f"TDD Planning Phase: Processing {len(hierarchy.requirements)} requirements")
        print(f"{'='*70}")

        # Process each top-level requirement
        for i, requirement in enumerate(hierarchy.requirements, 1):
            print(f"\n\n[Requirement {i}/{len(hierarchy.requirements)}]")

            # Process through 3-session loop
            plan_path = self._process_requirement(requirement, research_doc_path)

            if plan_path:
                plan_paths.append(plan_path)

                # Store in CWA
                plan_content = plan_path.read_text(encoding="utf-8")
                summary = f"TDD plan for {requirement.id}: {requirement.description[:100]}"
                entry_id = self.cwa.store_plan(
                    path=str(plan_path),
                    content=plan_content,
                    summary=summary,
                )
                cwa_entry_ids.append(entry_id)
                print(f"✓ Plan stored in CWA: {entry_id}")
            else:
                failed_requirements.append(requirement.id)
                print(f"❌ Failed to create plan for {requirement.id}")

        # Calculate results
        completed_at = datetime.now()
        duration = (completed_at - started_at).total_seconds()

        successful_count = len(plan_paths)
        failed_count = len(failed_requirements)

        print(f"\n{'='*70}")
        print(f"TDD Planning Complete:")
        print(f"  ✓ Successful: {successful_count}/{len(hierarchy.requirements)}")
        if failed_count > 0:
            print(f"  ❌ Failed: {failed_count}")
            print(f"     {', '.join(failed_requirements)}")
        print(f"  Duration: {duration:.1f}s")
        print(f"{'='*70}\n")

        return PhaseResult(
            phase_type=PhaseType.TDD_PLANNING,
            status=PhaseStatus.COMPLETE,
            artifacts=[str(p) for p in plan_paths],
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            metadata={
                "hierarchy_path": hierarchy_path,
                "research_doc_path": research_doc_path,
                "requirements_count": len(hierarchy.requirements),
                "successful_plans": successful_count,
                "failed_plans": failed_count,
                "failed_requirements": failed_requirements,  # List of requirement IDs that failed
                "cwa_entry_ids": cwa_entry_ids,
                "intermediate_files_policy": "preserved_on_failure",  # Review files and unenhanced plans kept for debugging
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
            errors=[f"Invalid hierarchy JSON: {e}"],
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
```

### 🔵 Refactor: Improve Code

Remove all old manual methods that are no longer used:
- `_generate_plan_document()` (lines 81-116)
- `_generate_summary_table()` (lines 118-139)
- `_generate_requirement_section()` (lines 141-169)
- `_generate_behavior_tdd()` (lines 171-235)
- `_parse_behavior()` (lines 237-255)
- `_generate_success_criteria()` (lines 257-278)
- `_save_plan()` (lines 280-296)
- `_store_plan_in_cwa()` (lines 298-316)

These are replaced by the new LLM-driven methods.

## Success Criteria (Tracking Matrix)

### Automated Tests

- [x] Test fails for right reason (Red): Method signature changed
- [x] Tests pass (Green): All 4 tests pass
- [x] All tests pass: `pytest silmari_rlm_act/tests/test_tdd_planning_phase.py -v`
- [x] Type checking passes: `mypy silmari_rlm_act/phases/tdd_planning.py`
- [x] Integration test: `pytest silmari_rlm_act/tests/ -v -k tdd`

### Manual Verification

- [x] Multiple requirements processed sequentially
- [x] Partial failures handled gracefully
- [x] Progress printed to console
- [x] All successful plans stored in CWA

## Notes

- This is the main entry point for the TDD planning phase
- Replace the entire existing execute() method
- Remove 8 old helper methods that are no longer needed
- Partial success (some requirements failed) still returns COMPLETE status
- All metadata collected for debugging and progress tracking
