# Phase 2: Add `related_concepts` Field to RequirementNode

**Beads ID**: `silmari-Context-Engine-aya3`
**Depends On**: None
**Blocks**: Phase 5

---

## Test Specification

**Given**: A `RequirementNode` is created with `related_concepts` list
**When**: The node is serialized and deserialized
**Then**: The `related_concepts` list is preserved

**Edge Cases**:
- Empty list (default)
- List with duplicates
- List with empty strings

---

## TDD Cycle

### Red: Write Failing Test

**File**: `planning_pipeline/tests/test_models.py`

```python
class TestRequirementNodeRelatedConcepts:
    """Tests for related_concepts field on RequirementNode."""

    def test_related_concepts_stored_on_creation(self):
        """Given related_concepts provided, when node created, then stored."""
        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
            related_concepts=["auth", "jwt", "session"],
        )
        assert node.related_concepts == ["auth", "jwt", "session"]

    def test_related_concepts_default_empty_list(self):
        """Given no related_concepts, when node created, then empty list."""
        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
        )
        assert node.related_concepts == []

    def test_related_concepts_serialized_to_dict(self):
        """Given node with related_concepts, when to_dict, then in output."""
        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
            related_concepts=["database", "caching"],
        )
        result = node.to_dict()
        assert result["related_concepts"] == ["database", "caching"]

    def test_related_concepts_deserialized_from_dict(self):
        """Given dict with related_concepts, when from_dict, then restored."""
        data = {
            "id": "REQ_001",
            "description": "Test requirement",
            "type": "parent",
            "parent_id": None,
            "children": [],
            "acceptance_criteria": [],
            "implementation": None,
            "testable_properties": [],
            "related_concepts": ["api", "rest"],
        }
        node = RequirementNode.from_dict(data)
        assert node.related_concepts == ["api", "rest"]

    @given(st.lists(st.text(min_size=1, max_size=50), max_size=10))
    def test_related_concepts_roundtrip_property(self, concepts: list[str]):
        """Property: related_concepts survives serialization roundtrip."""
        node = RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
            related_concepts=concepts,
        )
        restored = RequirementNode.from_dict(node.to_dict())
        assert restored.related_concepts == concepts
```

**Run**: `pytest planning_pipeline/tests/test_models.py::TestRequirementNodeRelatedConcepts -v`

---

### Green: Minimal Implementation

**File**: `planning_pipeline/models.py`

Add to `RequirementNode` dataclass:

```python
related_concepts: list[str] = field(default_factory=list)  # NEW FIELD
```

Update `to_dict()`:
```python
"related_concepts": self.related_concepts,  # NEW FIELD
```

Update `from_dict()`:
```python
related_concepts=data.get("related_concepts", []),  # NEW FIELD
```

---

### Refactor: Improve Code

No refactoring needed.

---

## Success Criteria

**Automated:**
- [x] Test fails for right reason: `pytest planning_pipeline/tests/test_models.py::TestRequirementNodeRelatedConcepts -v`
- [x] Test passes after implementation - 5 tests pass
- [x] All existing tests pass: `pytest planning_pipeline/tests/test_models.py -v` - 41 tests pass
