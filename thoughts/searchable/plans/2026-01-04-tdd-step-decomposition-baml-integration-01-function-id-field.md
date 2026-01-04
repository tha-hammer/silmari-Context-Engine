# Phase 1: Add `function_id` Field to RequirementNode

**Beads ID**: `silmari-Context-Engine-219c`
**Depends On**: None
**Blocks**: Phase 4, Phase 6

---

## Test Specification

**Given**: A `RequirementNode` is created with a `function_id` value
**When**: The node is serialized via `to_dict()` and deserialized via `from_dict()`
**Then**: The `function_id` is preserved in both directions

**Edge Cases**:
- `function_id` is None (optional field)
- `function_id` contains special characters
- `function_id` is empty string

---

## TDD Cycle

### Red: Write Failing Test

**File**: `planning_pipeline/tests/test_models.py`

```python
class TestRequirementNodeFunctionId:
    """Tests for function_id field on RequirementNode."""

    def test_function_id_stored_on_creation(self):
        """Given function_id provided, when node created, then function_id is stored."""
        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
            function_id="AuthService.login",
        )
        assert node.function_id == "AuthService.login"

    def test_function_id_serialized_to_dict(self):
        """Given node with function_id, when to_dict called, then function_id in output."""
        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
            function_id="DataValidator.validate",
        )
        result = node.to_dict()
        assert result["function_id"] == "DataValidator.validate"

    def test_function_id_deserialized_from_dict(self):
        """Given dict with function_id, when from_dict called, then function_id restored."""
        data = {
            "id": "REQ_001",
            "description": "Test requirement",
            "type": "parent",
            "function_id": "UserService.create",
            "parent_id": None,
            "children": [],
            "acceptance_criteria": [],
            "implementation": None,
            "testable_properties": [],
        }
        node = RequirementNode.from_dict(data)
        assert node.function_id == "UserService.create"

    def test_function_id_none_when_not_provided(self):
        """Given no function_id, when node created, then function_id is None."""
        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
        )
        assert node.function_id is None

    @given(st.text(min_size=1, max_size=100).filter(lambda x: x.strip()))
    def test_function_id_roundtrip_property(self, function_id: str):
        """Property: function_id survives serialization roundtrip."""
        node = RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
            function_id=function_id,
        )
        restored = RequirementNode.from_dict(node.to_dict())
        assert restored.function_id == function_id
```

**Run**: `pytest planning_pipeline/tests/test_models.py::TestRequirementNodeFunctionId -v`

---

### Green: Minimal Implementation

**File**: `planning_pipeline/models.py`

```python
@dataclass
class RequirementNode:
    """Single node in the requirement hierarchy."""

    id: str
    description: str
    type: str
    parent_id: Optional[str] = None
    children: list["RequirementNode"] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    implementation: Optional[ImplementationComponents] = None
    testable_properties: list[TestableProperty] = field(default_factory=list)
    function_id: Optional[str] = None  # NEW FIELD

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary with recursive children."""
        return {
            "id": self.id,
            "description": self.description,
            "type": self.type,
            "parent_id": self.parent_id,
            "children": [child.to_dict() for child in self.children],
            "acceptance_criteria": self.acceptance_criteria,
            "implementation": self.implementation.to_dict() if self.implementation else None,
            "testable_properties": [prop.to_dict() for prop in self.testable_properties],
            "function_id": self.function_id,  # NEW FIELD
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RequirementNode":
        """Deserialize from dictionary with recursive children reconstruction."""
        impl = None
        if data.get("implementation"):
            impl = ImplementationComponents.from_dict(data["implementation"])

        props = [
            TestableProperty.from_dict(p) for p in data.get("testable_properties", [])
        ]

        children = [cls.from_dict(c) for c in data.get("children", [])]

        return cls(
            id=data["id"],
            description=data["description"],
            type=data["type"],
            parent_id=data.get("parent_id"),
            children=children,
            acceptance_criteria=data.get("acceptance_criteria", []),
            implementation=impl,
            testable_properties=props,
            function_id=data.get("function_id"),  # NEW FIELD
        )
```

---

### Refactor: Improve Code

No refactoring needed for this behavior - implementation is minimal and clean.

---

## Success Criteria

**Automated:**
- [x] Test fails for right reason (AttributeError: function_id): `pytest planning_pipeline/tests/test_models.py::TestRequirementNodeFunctionId -v`
- [x] Test passes after implementation: `pytest planning_pipeline/tests/test_models.py::TestRequirementNodeFunctionId -v`
- [x] All existing model tests still pass: `pytest planning_pipeline/tests/test_models.py -v` (24 passed)
- [x] Type check passes: `mypy planning_pipeline/models.py` (no errors in models.py)

**Manual:**
- [x] JSON output includes `function_id` field
