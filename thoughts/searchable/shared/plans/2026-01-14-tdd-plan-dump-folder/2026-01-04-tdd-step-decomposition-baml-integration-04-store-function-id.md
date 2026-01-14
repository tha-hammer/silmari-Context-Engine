# Phase 4: Store `function_id` from BAML Response

**Beads ID**: `silmari-Context-Engine-iz7d`
**Depends On**: Phase 1
**Blocks**: Phase 7

---

## Test Specification

**Given**: BAML `ProcessGate1SubprocessDetailsPrompt` returns `implementation_details` with `function_id`
**When**: `_create_child_from_details()` is called
**Then**: The `function_id` is stored in the resulting `RequirementNode`

**Edge Cases**:
- `function_id` is empty string
- `function_id` is None
- No `implementation_details` in response

---

## TDD Cycle

### Red: Write Failing Test

**File**: `planning_pipeline/tests/test_decomposition.py`

```python
class TestCreateChildFromDetailsFunctionId:
    """Tests for function_id extraction in _create_child_from_details."""

    def test_function_id_extracted_from_baml_response(self, mock_baml_subprocess_details):
        """Given BAML returns function_id, when child created, then function_id stored."""
        # Arrange: Mock response with function_id
        mock_response = MagicMock()
        mock_detail = MagicMock()
        mock_detail.function_id = "AuthService.validateCredentials"
        mock_detail.description = "Validate user credentials"
        mock_detail.acceptance_criteria = []
        mock_detail.implementation = None
        mock_detail.related_concepts = []
        mock_response.implementation_details = [mock_detail]

        config = DecompositionConfig()

        # Act
        from planning_pipeline.decomposition import _create_child_from_details
        child = _create_child_from_details(
            child_id="REQ_001.1",
            sub_process="Validate credentials",
            details_response=mock_response,
            parent_id="REQ_001",
            config=config,
        )

        # Assert
        assert child.function_id == "AuthService.validateCredentials"

    def test_function_id_none_when_not_in_response(self):
        """Given BAML response has no function_id, when child created, then None."""
        mock_response = MagicMock()
        mock_detail = MagicMock()
        mock_detail.function_id = None
        mock_detail.description = "Some description"
        mock_detail.acceptance_criteria = []
        mock_detail.implementation = None
        mock_detail.related_concepts = []
        mock_response.implementation_details = [mock_detail]

        config = DecompositionConfig()

        from planning_pipeline.decomposition import _create_child_from_details
        child = _create_child_from_details(
            child_id="REQ_001.1",
            sub_process="Some process",
            details_response=mock_response,
            parent_id="REQ_001",
            config=config,
        )

        assert child.function_id is None
```

**Run**: `pytest planning_pipeline/tests/test_decomposition.py::TestCreateChildFromDetailsFunctionId -v`

---

### Green: Minimal Implementation

**File**: `planning_pipeline/decomposition.py`

Update `_create_child_from_details()`:

```python
def _create_child_from_details(
    child_id: str,
    sub_process: str,
    details_response: Any,
    parent_id: str,
    config: DecompositionConfig,
) -> RequirementNode:
    """Create a child RequirementNode from BAML subprocess details response."""
    if not details_response.implementation_details:
        return RequirementNode(
            id=child_id,
            description=sub_process,
            type="sub_process",
            parent_id=parent_id,
        )

    detail = details_response.implementation_details[0]

    # Extract function_id from BAML response
    function_id = None
    if hasattr(detail, "function_id") and detail.function_id:
        function_id = detail.function_id

    # Build implementation components
    impl = None
    if hasattr(detail, "implementation") and detail.implementation:
        impl = ImplementationComponents(
            frontend=list(detail.implementation.frontend or []),
            backend=list(detail.implementation.backend or []),
            middleware=list(detail.implementation.middleware or []),
            shared=list(detail.implementation.shared or []),
        )

    acceptance_criteria = []
    if config.include_acceptance_criteria and hasattr(detail, "acceptance_criteria"):
        acceptance_criteria = list(detail.acceptance_criteria or [])

    return RequirementNode(
        id=child_id,
        description=detail.description if hasattr(detail, "description") else sub_process,
        type="sub_process",
        parent_id=parent_id,
        acceptance_criteria=acceptance_criteria,
        implementation=impl,
        function_id=function_id,  # NEW: Store function_id
    )
```

---

### Refactor: Improve Code

No refactoring needed.

---

## Success Criteria

**Automated:**
- [x] Test fails for right reason: `pytest planning_pipeline/tests/test_decomposition.py::TestCreateChildFromDetailsFunctionId -v`
- [x] Test passes after implementation
- [x] All decomposition tests pass: `pytest planning_pipeline/tests/test_decomposition.py -v`
