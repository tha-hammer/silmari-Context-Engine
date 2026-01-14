# Phase 3: Add `category` Field to RequirementNode

**Beads ID**: `silmari-Context-Engine-t4yq`
**Depends On**: None
**Blocks**: Phase 7

---

## Test Specification

**Given**: A `RequirementNode` is created with a `category` value
**When**: The node is serialized and deserialized
**Then**: The `category` is preserved

**Valid Categories**: `functional`, `non_functional`, `security`, `performance`, `usability`, `integration`

**Edge Cases**:
- Category is None (defaults to "functional")
- Invalid category (should raise ValueError)

---

## TDD Cycle

### Red: Write Failing Test

**File**: `planning_pipeline/tests/test_models.py`

```python
VALID_CATEGORIES = frozenset([
    "functional", "non_functional", "security",
    "performance", "usability", "integration"
])


class TestRequirementNodeCategory:
    """Tests for category field on RequirementNode."""

    def test_category_stored_on_creation(self):
        """Given category provided, when node created, then stored."""
        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
            category="security",
        )
        assert node.category == "security"

    def test_category_default_functional(self):
        """Given no category, when node created, then defaults to functional."""
        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
        )
        assert node.category == "functional"

    def test_category_serialized_to_dict(self):
        """Given node with category, when to_dict, then in output."""
        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
            category="performance",
        )
        result = node.to_dict()
        assert result["category"] == "performance"

    def test_category_deserialized_from_dict(self):
        """Given dict with category, when from_dict, then restored."""
        data = {
            "id": "REQ_001",
            "description": "Test requirement",
            "type": "parent",
            "category": "usability",
            "parent_id": None,
            "children": [],
            "acceptance_criteria": [],
            "implementation": None,
            "testable_properties": [],
        }
        node = RequirementNode.from_dict(data)
        assert node.category == "usability"

    def test_invalid_category_raises_error(self):
        """Given invalid category, when node created, then ValueError."""
        with pytest.raises(ValueError, match="Invalid category"):
            RequirementNode(
                id="REQ_001",
                description="Test requirement",
                type="parent",
                category="invalid_category",
            )

    @given(st.sampled_from(list(VALID_CATEGORIES)))
    def test_valid_categories_accepted(self, category: str):
        """Property: all valid categories are accepted."""
        node = RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
            category=category,
        )
        assert node.category == category
```

**Run**: `pytest planning_pipeline/tests/test_models.py::TestRequirementNodeCategory -v`

---

### Green: Minimal Implementation

**File**: `planning_pipeline/models.py`

Add constant:
```python
VALID_CATEGORIES = frozenset([
    "functional", "non_functional", "security",
    "performance", "usability", "integration"
])
```

Add to `RequirementNode` dataclass:
```python
category: str = "functional"  # NEW FIELD
```

Add to `__post_init__`:
```python
if self.category not in VALID_CATEGORIES:
    raise ValueError(
        f"Invalid category '{self.category}'. Must be one of: {', '.join(VALID_CATEGORIES)}"
    )
```

Update `to_dict()`:
```python
"category": self.category,  # NEW FIELD
```

Update `from_dict()`:
```python
category=data.get("category", "functional"),  # NEW FIELD
```

---

### Refactor: Improve Code

No refactoring needed.

---

## Success Criteria

**Automated:**
- [x] Test fails for right reason: `pytest planning_pipeline/tests/test_models.py::TestRequirementNodeCategory -v`
- [x] Test passes after implementation
- [x] All existing tests pass
