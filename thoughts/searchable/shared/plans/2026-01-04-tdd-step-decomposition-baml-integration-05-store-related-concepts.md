# Phase 5: Store `related_concepts` from BAML Response

**Beads ID**: `silmari-Context-Engine-mn41`
**Depends On**: Phase 2
**Blocks**: Phase 7

---

## Test Specification

**Given**: BAML response contains `related_concepts` array
**When**: `_create_child_from_details()` is called
**Then**: `related_concepts` is stored in the `RequirementNode`

**Edge Cases**:
- `related_concepts` is None
- `related_concepts` is empty array
- `related_concepts` contains duplicates

---

## TDD Cycle

### Red: Write Failing Test

**File**: `planning_pipeline/tests/test_decomposition.py`

```python
class TestCreateChildFromDetailsRelatedConcepts:
    """Tests for related_concepts extraction in _create_child_from_details."""

    def test_related_concepts_extracted_from_baml_response(self):
        """Given BAML returns related_concepts, when child created, then stored."""
        mock_response = MagicMock()
        mock_detail = MagicMock()
        mock_detail.function_id = None
        mock_detail.description = "Implement authentication"
        mock_detail.acceptance_criteria = []
        mock_detail.implementation = None
        mock_detail.related_concepts = ["jwt", "oauth", "session"]
        mock_response.implementation_details = [mock_detail]

        config = DecompositionConfig()

        from planning_pipeline.decomposition import _create_child_from_details
        child = _create_child_from_details(
            child_id="REQ_001.1",
            sub_process="Auth",
            details_response=mock_response,
            parent_id="REQ_001",
            config=config,
        )

        assert child.related_concepts == ["jwt", "oauth", "session"]

    def test_related_concepts_empty_when_not_in_response(self):
        """Given no related_concepts in response, when child created, then empty list."""
        mock_response = MagicMock()
        mock_detail = MagicMock()
        mock_detail.function_id = None
        mock_detail.description = "Some description"
        mock_detail.acceptance_criteria = []
        mock_detail.implementation = None
        mock_detail.related_concepts = None
        mock_response.implementation_details = [mock_detail]

        config = DecompositionConfig()

        from planning_pipeline.decomposition import _create_child_from_details
        child = _create_child_from_details(
            child_id="REQ_001.1",
            sub_process="Process",
            details_response=mock_response,
            parent_id="REQ_001",
            config=config,
        )

        assert child.related_concepts == []
```

**Run**: `pytest planning_pipeline/tests/test_decomposition.py::TestCreateChildFromDetailsRelatedConcepts -v`

---

### Green: Minimal Implementation

**File**: `planning_pipeline/decomposition.py`

Update `_create_child_from_details()`:

```python
# Extract related_concepts from BAML response
related_concepts = []
if hasattr(detail, "related_concepts") and detail.related_concepts:
    related_concepts = list(detail.related_concepts)

return RequirementNode(
    id=child_id,
    description=detail.description if hasattr(detail, "description") else sub_process,
    type="sub_process",
    parent_id=parent_id,
    acceptance_criteria=acceptance_criteria,
    implementation=impl,
    function_id=function_id,
    related_concepts=related_concepts,  # NEW: Store related_concepts
)
```

---

### Refactor: Improve Code

No refactoring needed.

---

## Success Criteria

**Automated:**
- [x] Test fails for right reason
- [x] Test passes after implementation - 6 related_concepts tests pass
- [x] All decomposition tests pass - 34 passed, 2 skipped
