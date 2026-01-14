# Phase 7: 3-Tier Hierarchy (Implementation Details as Children)

**Beads ID**: `silmari-Context-Engine-usn7`
**Depends On**: Phase 4, Phase 5, Phase 6
**Blocks**: None (final integration phase)

---

## Test Specification

**Given**: BAML returns multiple `implementation_details` for a subprocess
**When**: Hierarchy is built
**Then**: Each implementation detail becomes a child of the sub_process node with type "implementation"

**Expected Structure**:
```
parent (type="parent")
  -> sub_process (type="sub_process")
      -> implementation_detail_1 (type="implementation")
      -> implementation_detail_2 (type="implementation")
```

---

## TDD Cycle

### Red: Write Failing Test

**File**: `planning_pipeline/tests/test_decomposition.py`

```python
class TestThreeTierHierarchy:
    """Tests for 3-tier hierarchy: parent -> sub_process -> implementation."""

    def test_implementation_details_become_children(self, patch_baml_client):
        """Given BAML returns multiple impl details, when decomposed, then 3-tier."""
        # Arrange: Mock BAML to return multiple implementation details
        mock_initial = MagicMock()
        mock_req = MagicMock()
        mock_req.description = "Parent requirement"
        mock_req.sub_processes = ["Sub process 1"]
        mock_req.related_concepts = []
        mock_initial.requirements = [mock_req]

        mock_subprocess = MagicMock()
        mock_detail1 = MagicMock()
        mock_detail1.function_id = "Impl.detail1"
        mock_detail1.description = "First implementation detail"
        mock_detail1.acceptance_criteria = ["AC1"]
        mock_detail1.implementation = None
        mock_detail1.related_concepts = ["concept1"]

        mock_detail2 = MagicMock()
        mock_detail2.function_id = "Impl.detail2"
        mock_detail2.description = "Second implementation detail"
        mock_detail2.acceptance_criteria = ["AC2"]
        mock_detail2.implementation = None
        mock_detail2.related_concepts = ["concept2"]

        mock_subprocess.implementation_details = [mock_detail1, mock_detail2]

        with patch_baml_client as mock_b:
            mock_b.ProcessGate1InitialExtractionPrompt.return_value = mock_initial
            mock_b.ProcessGate1SubprocessDetailsPrompt.return_value = mock_subprocess

            # Act
            result = decompose_requirements("Test research content")

            # Assert: 3-tier structure
            assert isinstance(result, RequirementHierarchy)
            assert len(result.requirements) == 1

            parent = result.requirements[0]
            assert parent.type == "parent"
            assert len(parent.children) == 1

            sub_process = parent.children[0]
            assert sub_process.type == "sub_process"
            assert len(sub_process.children) == 2  # Two implementation details

            impl1 = sub_process.children[0]
            assert impl1.type == "implementation"
            assert impl1.description == "First implementation detail"
            assert impl1.function_id == "Impl.detail1"

            impl2 = sub_process.children[1]
            assert impl2.type == "implementation"
            assert impl2.description == "Second implementation detail"

    def test_implementation_node_ids_follow_pattern(self, patch_baml_client):
        """Given 3-tier hierarchy, when built, then IDs are REQ_XXX.Y.Z."""
        # Similar setup as above...
        mock_initial = MagicMock()
        mock_req = MagicMock()
        mock_req.description = "Parent"
        mock_req.sub_processes = ["Sub 1"]
        mock_req.related_concepts = []
        mock_initial.requirements = [mock_req]

        mock_subprocess = MagicMock()
        mock_detail = MagicMock()
        mock_detail.function_id = "Impl.test"
        mock_detail.description = "Implementation"
        mock_detail.acceptance_criteria = []
        mock_detail.implementation = None
        mock_detail.related_concepts = []
        mock_subprocess.implementation_details = [mock_detail]

        with patch_baml_client as mock_b:
            mock_b.ProcessGate1InitialExtractionPrompt.return_value = mock_initial
            mock_b.ProcessGate1SubprocessDetailsPrompt.return_value = mock_subprocess

            result = decompose_requirements("Test")

            impl = result.requirements[0].children[0].children[0]
            assert impl.id == "REQ_000.1.1"  # REQ_XXX.Y.Z pattern
            assert impl.parent_id == "REQ_000.1"
```

**Run**: `pytest planning_pipeline/tests/test_decomposition.py::TestThreeTierHierarchy -v`

---

### Green: Minimal Implementation

**File**: `planning_pipeline/decomposition.py`

Refactor the decomposition loop to create 3-tier hierarchy:

```python
# Process each top-level requirement
for req_idx, requirement in enumerate(initial_response.requirements):
    parent_id = f"REQ_{req_idx:03d}"
    parent_node = RequirementNode(
        id=parent_id,
        description=requirement.description,
        type="parent",
    )

    sub_processes = requirement.sub_processes[: config.max_sub_processes]

    for sub_idx, sub_process in enumerate(sub_processes):
        sub_id = f"{parent_id}.{sub_idx + 1}"

        try:
            details_response = b.ProcessGate1SubprocessDetailsPrompt(
                sub_process=sub_process,
                parent_description=requirement.description,
                scope_text=research_content[:500],
                user_confirmation=True,
            )

            # Create sub_process node
            sub_node = RequirementNode(
                id=sub_id,
                description=sub_process,
                type="sub_process",
                parent_id=parent_id,
            )

            # Create implementation children from details
            for impl_idx, detail in enumerate(details_response.implementation_details):
                impl_id = f"{sub_id}.{impl_idx + 1}"
                impl_node = _create_implementation_node(
                    impl_id=impl_id,
                    detail=detail,
                    parent_id=sub_id,
                    config=config,
                )
                sub_node.children.append(impl_node)

            stats.subprocesses_expanded += 1

        except Exception:
            # Fallback: create basic sub_process node
            sub_node = RequirementNode(
                id=sub_id,
                description=sub_process,
                type="sub_process",
                parent_id=parent_id,
            )

        parent_node.children.append(sub_node)

    hierarchy.add_requirement(parent_node)
```

Add new helper:

```python
def _create_implementation_node(
    impl_id: str,
    detail: Any,
    parent_id: str,
    config: DecompositionConfig,
) -> RequirementNode:
    """Create an implementation-level RequirementNode from BAML detail."""
    # Extract or generate function_id
    function_id = None
    if hasattr(detail, "function_id") and detail.function_id:
        function_id = detail.function_id
    else:
        desc = detail.description if hasattr(detail, "description") else ""
        function_id = _generate_function_id(desc, parent_id)

    # Extract related_concepts
    related_concepts = []
    if hasattr(detail, "related_concepts") and detail.related_concepts:
        related_concepts = list(detail.related_concepts)

    # Extract implementation components
    impl = None
    if hasattr(detail, "implementation") and detail.implementation:
        impl = ImplementationComponents(
            frontend=list(detail.implementation.frontend or []),
            backend=list(detail.implementation.backend or []),
            middleware=list(detail.implementation.middleware or []),
            shared=list(detail.implementation.shared or []),
        )

    # Extract acceptance criteria
    acceptance_criteria = []
    if config.include_acceptance_criteria and hasattr(detail, "acceptance_criteria"):
        acceptance_criteria = list(detail.acceptance_criteria or [])

    return RequirementNode(
        id=impl_id,
        description=detail.description if hasattr(detail, "description") else "Implementation",
        type="implementation",
        parent_id=parent_id,
        acceptance_criteria=acceptance_criteria,
        implementation=impl,
        function_id=function_id,
        related_concepts=related_concepts,
    )
```

---

### Refactor: Improve Code

- Consider extracting BAML response parsing into a separate helper
- Add logging for debugging hierarchy construction
- Consider adding depth limit configuration

---

## Success Criteria

**Automated:**
- [x] Test fails for right reason
- [x] Test passes after implementation
- [x] All decomposition tests pass: `pytest planning_pipeline/tests/test_decomposition.py -v`
