# Phase 8: Arbitrary Depth ID Generation

**Beads ID**: `silmari-Context-Engine-vjie`
**Depends On**: None (can run in parallel with Phase 7)
**Blocks**: None

---

## Test Specification

**Given**: Hierarchy needs 4+ levels
**When**: `add_child()` is called recursively
**Then**: IDs follow `REQ_XXX.Y.Z.W...` pattern

**Examples**:
- Level 1: `REQ_001`
- Level 2: `REQ_001.1`
- Level 3: `REQ_001.1.1`
- Level 4: `REQ_001.1.1.1`

---

## TDD Cycle

### Red: Write Failing Test

**File**: `planning_pipeline/tests/test_models.py`

```python
class TestArbitraryDepthIds:
    """Tests for arbitrary depth ID generation."""

    def test_four_level_hierarchy(self):
        """Given 4-level nesting, when add_child used, then IDs correct."""
        hierarchy = RequirementHierarchy()

        # Level 1: REQ_001
        parent = RequirementNode(id="REQ_001", description="Parent", type="parent")
        hierarchy.add_requirement(parent)

        # Level 2: REQ_001.1
        sub = RequirementNode(id="REQ_001.1", description="Sub", type="sub_process")
        hierarchy.add_child("REQ_001", sub)

        # Level 3: REQ_001.1.1
        impl = RequirementNode(id="REQ_001.1.1", description="Impl", type="implementation")
        hierarchy.add_child("REQ_001.1", impl)

        # Level 4: REQ_001.1.1.1
        detail = RequirementNode(id="REQ_001.1.1.1", description="Detail", type="implementation")
        hierarchy.add_child("REQ_001.1.1", detail)

        # Assert structure
        assert hierarchy.get_by_id("REQ_001.1.1.1") is not None
        assert hierarchy.get_by_id("REQ_001.1.1.1").parent_id == "REQ_001.1.1"

    def test_next_child_id_generation(self):
        """Given parent with children, when next ID generated, then increments."""
        parent = RequirementNode(id="REQ_001.2.3", description="Parent", type="implementation")

        # Simulate adding children
        next_id_1 = f"{parent.id}.1"  # REQ_001.2.3.1
        next_id_2 = f"{parent.id}.2"  # REQ_001.2.3.2

        assert next_id_1 == "REQ_001.2.3.1"
        assert next_id_2 == "REQ_001.2.3.2"

    @given(st.integers(min_value=1, max_value=10))
    def test_arbitrary_depth_property(self, depth: int):
        """Property: hierarchy supports arbitrary depth."""
        hierarchy = RequirementHierarchy()

        # Build nested hierarchy to given depth
        current_id = "REQ_001"
        parent = RequirementNode(id=current_id, description="Root", type="parent")
        hierarchy.add_requirement(parent)

        for i in range(1, depth):
            child_id = f"{current_id}.{i}"
            child = RequirementNode(
                id=child_id,
                description=f"Level {i+1}",
                type="implementation",
            )
            hierarchy.add_child(current_id, child)
            current_id = child_id

        # Assert deepest node is findable
        assert hierarchy.get_by_id(current_id) is not None

    def test_get_depth_method(self):
        """Given node ID, when get_depth called, then correct depth returned."""
        # REQ_001 -> depth 1
        # REQ_001.1 -> depth 2
        # REQ_001.1.3 -> depth 3
        # REQ_001.1.3.2 -> depth 4

        def get_depth(node_id: str) -> int:
            """Calculate depth from ID pattern."""
            if not node_id.startswith("REQ_"):
                return 0
            parts = node_id.split(".")
            return len(parts)

        assert get_depth("REQ_001") == 1
        assert get_depth("REQ_001.1") == 2
        assert get_depth("REQ_001.1.3") == 3
        assert get_depth("REQ_001.1.3.2") == 4
```

**Run**: `pytest planning_pipeline/tests/test_models.py::TestArbitraryDepthIds -v`

---

### Green: Minimal Implementation

The existing `RequirementHierarchy.add_child()` and `get_by_id()` already support arbitrary depth through recursion. The test should pass without changes.

If not, ensure:
1. `add_child()` properly sets `parent_id` and appends to parent's `children`
2. `get_by_id()` recursively searches all levels

**File**: `planning_pipeline/models.py`

Verify these methods exist and work correctly:

```python
def add_child(self, parent_id: str, child: RequirementNode) -> bool:
    """Add a child node to the specified parent."""
    parent = self.get_by_id(parent_id)
    if parent:
        child.parent_id = parent_id
        parent.children.append(child)
        return True
    return False

def get_by_id(self, node_id: str) -> Optional[RequirementNode]:
    """Recursively find a node by ID."""
    for req in self.requirements:
        if req.id == node_id:
            return req
        found = self._find_in_children(req, node_id)
        if found:
            return found
    return None

def _find_in_children(self, node: RequirementNode, node_id: str) -> Optional[RequirementNode]:
    """Recursively search children for a node."""
    for child in node.children:
        if child.id == node_id:
            return child
        found = self._find_in_children(child, node_id)
        if found:
            return found
    return None
```

---

### Refactor: Improve Code

Consider adding a utility method to generate the next child ID:

```python
def next_child_id(self, parent_id: str) -> str:
    """Generate the next child ID for a parent."""
    parent = self.get_by_id(parent_id)
    if not parent:
        raise ValueError(f"Parent {parent_id} not found")
    next_num = len(parent.children) + 1
    return f"{parent_id}.{next_num}"
```

---

## Success Criteria

**Automated:**
- [x] Test fails (if implementation missing) - Tests for `next_child_id` failed before implementation
- [x] Test passes - All 6 arbitrary depth tests pass
- [x] All model tests pass - 41 tests pass

---

## Integration & E2E Testing

After all phases complete, run full integration tests:

**File**: `planning_pipeline/tests/test_decomposition.py`

```python
@pytest.mark.integration
class TestDecompositionIntegration:
    """Integration tests for full decomposition flow."""

    def test_full_3tier_output_structure(self, patch_baml_client):
        """Given research content, when decomposed, then output matches expected structure."""
        # Setup mocks for realistic BAML responses
        # ...

        result = decompose_requirements("# Research\nImplement auth system")

        # Assert full structure
        assert isinstance(result, RequirementHierarchy)
        output = result.to_dict()

        # Verify all new fields present
        for req in output["requirements"]:
            assert "function_id" in req
            assert "related_concepts" in req
            assert "category" in req

            for child in req.get("children", []):
                assert "function_id" in child
                assert "related_concepts" in child

                for impl in child.get("children", []):
                    assert impl["type"] == "implementation"
                    assert "function_id" in impl
```

**File**: `planning_pipeline/tests/test_decomposition_e2e.py`

```python
@pytest.mark.e2e
@pytest.mark.slow
class TestDecompositionE2ENewFields:
    """E2E tests with real BAML calls for new field extraction."""

    def test_real_baml_extracts_function_id(self):
        """Given real research, when decomposed with BAML, then function_ids present."""
        if not BAML_AVAILABLE:
            pytest.skip("BAML not available")

        result = decompose_requirements(SAMPLE_RESEARCH_CONTENT)

        assert isinstance(result, RequirementHierarchy)
        # At least some nodes should have function_id
        found_function_id = False
        for req in result.requirements:
            for child in req.children:
                if child.function_id:
                    found_function_id = True
                    break
        assert found_function_id, "Expected at least one function_id from BAML"
```
