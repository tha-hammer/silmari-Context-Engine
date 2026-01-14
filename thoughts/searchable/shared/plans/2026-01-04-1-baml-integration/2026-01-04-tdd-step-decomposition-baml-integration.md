# Step Decomposition BAML Integration - TDD Implementation Plan

## Overview

Enhance `step_decomposition.py` and `decomposition.py` to produce 3+ tier requirement hierarchies matching the CodeWriter5 expected output format (`test-002-alpha.02.json`). This includes adding `function_id`, `related_concepts`, and `category` fields, plus supporting arbitrary depth nesting.

**Related Research**: `thoughts/searchable/shared/research/2026-01-04-step-decomposition-baml-integration.md`
**Related Beads**: `silmari-Context-Engine-4hi`

## Current State Analysis

### What Exists

| Component | Location | Status |
|-----------|----------|--------|
| `RequirementNode` | `planning_pipeline/models.py:103-185` | 2-level, missing `function_id`, `related_concepts`, `category` |
| `decompose_requirements()` | `planning_pipeline/decomposition.py:133-291` | Only creates 2 levels |
| `_create_child_from_details()` | `planning_pipeline/decomposition.py:294-347` | Discards `function_id` and `related_concepts` |
| Test suite | `planning_pipeline/tests/test_*.py` | Good coverage, uses Hypothesis |

### Key Discoveries

- BAML `ImplementationDetail` already returns `function_id` but it's not stored (`decomposition.py:323`)
- BAML `ImplementationDetail` returns `related_concepts` but it's discarded (`decomposition.py:294-347`)
- `RequirementNode` has hardcoded `VALID_REQUIREMENT_TYPES = frozenset(["parent", "sub_process", "implementation"])` (`models.py:16`)
- CodeWriter5 `requirements_processor.py:51-144` has `_generate_function_id_from_description()` for semantic ID generation
- Existing tests use Hypothesis extensively (`test_models.py:27-115` for strategies)

### Gaps to Address

1. **Missing Fields**: `function_id`, `related_concepts` on `RequirementNode`
2. **Missing Category**: No category field on nodes
3. **Shallow Hierarchy**: Only 2 levels, need 3+ with arbitrary depth
4. **Discarded BAML Data**: `function_id` and `related_concepts` from BAML response ignored
5. **ID Format**: Current format limited, need arbitrary depth support

## Desired End State

### Observable Behaviors

1. **Given** BAML returns `function_id`, **when** child node is created, **then** `function_id` is stored in node
2. **Given** BAML returns `related_concepts`, **when** child node is created, **then** `related_concepts` is stored
3. **Given** subprocess has multiple `implementation_details`, **when** hierarchy built, **then** each detail becomes child of sub_process (3-tier)
4. **Given** no `function_id` from BAML, **when** child created, **then** semantic ID generated from description
5. **Given** category specified, **when** node created, **then** category is stored and serialized
6. **Given** deep nesting needed, **when** `add_child()` called recursively, **then** IDs follow `REQ_XXX.Y.Z.W` pattern

### Expected Output Structure

```json
{
  "requirements": [
    {
      "id": "REQ_001",
      "description": "Parent requirement",
      "type": "parent",
      "category": "functional",
      "function_id": "Feature.initialize",
      "parent_id": null,
      "children": [
        {
          "id": "REQ_001.2",
          "description": "Sub-process requirement",
          "type": "sub_process",
          "category": "functional",
          "function_id": "SubProcess.execute",
          "parent_id": "REQ_001",
          "related_concepts": ["auth", "validation"],
          "children": [
            {
              "id": "REQ_001.2.1",
              "description": "Implementation detail",
              "type": "implementation",
              "category": "functional",
              "function_id": "AuthService.login",
              "parent_id": "REQ_001.2",
              "related_concepts": ["jwt", "session"],
              "acceptance_criteria": ["Must validate credentials"],
              "implementation": {
                "frontend": ["LoginForm"],
                "backend": ["AuthController"],
                "middleware": ["AuthMiddleware"],
                "shared": ["UserModel"]
              }
            }
          ]
        }
      ]
    }
  ]
}
```

## What We're NOT Doing

- Changing BAML schema (already has required fields)
- Modifying `step_research()` or `step_planning()` pipeline steps
- Changing the Mermaid visualization logic (will auto-adapt)
- Backward compatibility shims for old JSON format

## Testing Strategy

- **Framework**: pytest with Hypothesis for property-based testing
- **Test Types**:
  - Unit: Model field storage, serialization, ID generation
  - Integration: Full decomposition flow with mocked BAML
  - E2E: Real BAML calls (marked `@pytest.mark.e2e`)
- **Mocking**: Use existing `conftest.py` fixtures (`mock_baml_*`, `patch_baml_client`)
- **Patterns**: Follow existing class-based test organization

---

## Behavior 1: Add `function_id` Field to RequirementNode

### Test Specification

**Given**: A `RequirementNode` is created with a `function_id` value
**When**: The node is serialized via `to_dict()` and deserialized via `from_dict()`
**Then**: The `function_id` is preserved in both directions

**Edge Cases**:
- `function_id` is None (optional field)
- `function_id` contains special characters
- `function_id` is empty string

### TDD Cycle

#### 🔴 Red: Write Failing Test

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

#### 🟢 Green: Minimal Implementation

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

#### 🔵 Refactor: Improve Code

No refactoring needed for this behavior - implementation is minimal and clean.

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (AttributeError: function_id): `pytest planning_pipeline/tests/test_models.py::TestRequirementNodeFunctionId -v`
- [ ] Test passes after implementation: `pytest planning_pipeline/tests/test_models.py::TestRequirementNodeFunctionId -v`
- [ ] All existing model tests still pass: `pytest planning_pipeline/tests/test_models.py -v`
- [ ] Type check passes: `mypy planning_pipeline/models.py`

**Manual:**
- [ ] JSON output includes `function_id` field

---

## Behavior 2: Add `related_concepts` Field to RequirementNode

### Test Specification

**Given**: A `RequirementNode` is created with `related_concepts` list
**When**: The node is serialized and deserialized
**Then**: The `related_concepts` list is preserved

**Edge Cases**:
- Empty list (default)
- List with duplicates
- List with empty strings

### TDD Cycle

#### 🔴 Red: Write Failing Test

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

#### 🟢 Green: Minimal Implementation

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

#### 🔵 Refactor: Improve Code

No refactoring needed.

### Success Criteria

**Automated:**
- [ ] Test fails for right reason: `pytest planning_pipeline/tests/test_models.py::TestRequirementNodeRelatedConcepts -v`
- [ ] Test passes after implementation
- [ ] All existing tests pass: `pytest planning_pipeline/tests/test_models.py -v`

---

## Behavior 3: Add `category` Field to RequirementNode

### Test Specification

**Given**: A `RequirementNode` is created with a `category` value
**When**: The node is serialized and deserialized
**Then**: The `category` is preserved

**Valid Categories**: `functional`, `non_functional`, `security`, `performance`, `usability`, `integration`

**Edge Cases**:
- Category is None (defaults to "functional")
- Invalid category (should raise ValueError)

### TDD Cycle

#### 🔴 Red: Write Failing Test

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

#### 🟢 Green: Minimal Implementation

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

Update `to_dict()` and `from_dict()` accordingly.

#### 🔵 Refactor: Improve Code

No refactoring needed.

### Success Criteria

**Automated:**
- [ ] Test fails for right reason: `pytest planning_pipeline/tests/test_models.py::TestRequirementNodeCategory -v`
- [ ] Test passes after implementation
- [ ] All existing tests pass

---

## Behavior 4: Store `function_id` from BAML Response

### Test Specification

**Given**: BAML `ProcessGate1SubprocessDetailsPrompt` returns `implementation_details` with `function_id`
**When**: `_create_child_from_details()` is called
**Then**: The `function_id` is stored in the resulting `RequirementNode`

**Edge Cases**:
- `function_id` is empty string
- `function_id` is None
- No `implementation_details` in response

### TDD Cycle

#### 🔴 Red: Write Failing Test

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

#### 🟢 Green: Minimal Implementation

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

#### 🔵 Refactor: Improve Code

No refactoring needed.

### Success Criteria

**Automated:**
- [ ] Test fails for right reason: `pytest planning_pipeline/tests/test_decomposition.py::TestCreateChildFromDetailsFunctionId -v`
- [ ] Test passes after implementation
- [ ] All decomposition tests pass: `pytest planning_pipeline/tests/test_decomposition.py -v`

---

## Behavior 5: Store `related_concepts` from BAML Response

### Test Specification

**Given**: BAML response contains `related_concepts` array
**When**: `_create_child_from_details()` is called
**Then**: `related_concepts` is stored in the `RequirementNode`

### TDD Cycle

#### 🔴 Red: Write Failing Test

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

#### 🟢 Green: Minimal Implementation

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

### Success Criteria

**Automated:**
- [ ] Test fails for right reason
- [ ] Test passes after implementation
- [ ] All decomposition tests pass

---

## Behavior 6: Generate Semantic `function_id` When Not Provided

### Test Specification

**Given**: BAML response has no `function_id` (None or empty)
**When**: `_create_child_from_details()` is called
**Then**: A semantic `function_id` is generated from the description

**Examples**:
- "Authenticate user credentials" → "Auth.authenticate"
- "Render dashboard UI" → "Dashboard.render"
- "Validate input data" → "Validator.validate"

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `planning_pipeline/tests/test_decomposition.py`

```python
class TestGenerateFunctionIdFromDescription:
    """Tests for semantic function_id generation."""

    def test_generate_function_id_auth_pattern(self):
        """Given auth-related description, when generated, then Auth.* pattern."""
        from planning_pipeline.decomposition import _generate_function_id
        result = _generate_function_id("Authenticate user credentials")
        assert result == "Auth.authenticate"

    def test_generate_function_id_validate_pattern(self):
        """Given validation description, when generated, then Validator.validate."""
        from planning_pipeline.decomposition import _generate_function_id
        result = _generate_function_id("Validate input data")
        assert result == "Validator.validate"

    def test_generate_function_id_create_pattern(self):
        """Given create description, when generated, then Service.create."""
        from planning_pipeline.decomposition import _generate_function_id
        result = _generate_function_id("Create new user account")
        assert result == "User.create"

    def test_generate_function_id_fallback(self):
        """Given unknown pattern, when generated, then Service.perform."""
        from planning_pipeline.decomposition import _generate_function_id
        result = _generate_function_id("Something completely different")
        assert "." in result  # At least has Service.action format

    def test_child_gets_generated_function_id_when_baml_none(self):
        """Given BAML returns no function_id, when child created, then generated."""
        mock_response = MagicMock()
        mock_detail = MagicMock()
        mock_detail.function_id = None
        mock_detail.description = "Authenticate user credentials"
        mock_detail.acceptance_criteria = []
        mock_detail.implementation = None
        mock_detail.related_concepts = []
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

        assert child.function_id is not None
        assert "." in child.function_id
```

#### 🟢 Green: Minimal Implementation

**File**: `planning_pipeline/decomposition.py`

Add helper function (adapted from CodeWriter5 `requirements_processor.py:51-144`):

```python
def _generate_function_id(description: str, parent_id: Optional[str] = None) -> str:
    """Generate a semantic function_id from requirement description.

    Examples:
    - "Authenticate user credentials" -> "Auth.authenticate"
    - "Render dashboard UI" -> "Dashboard.render"
    - "Validate input data" -> "Validator.validate"
    """
    desc_lower = description.lower()

    # Action verb mappings
    action_map = {
        'authenticate': 'authenticate', 'login': 'login', 'logout': 'logout',
        'register': 'register', 'create': 'create', 'update': 'update',
        'delete': 'delete', 'get': 'get', 'fetch': 'fetch', 'retrieve': 'retrieve',
        'validate': 'validate', 'verify': 'verify', 'render': 'render',
        'display': 'display', 'show': 'show', 'process': 'process',
        'transform': 'transform', 'calculate': 'calculate', 'send': 'send',
        'receive': 'receive', 'store': 'store', 'save': 'save', 'load': 'load',
    }

    # Find action verb
    action = None
    for verb, mapped in action_map.items():
        if verb in desc_lower:
            action = mapped
            break
    if not action:
        words = description.split()
        action = words[0].lower() if words else "perform"

    # Subject mappings
    subject_map = {
        'user': 'User', 'auth': 'Auth', 'authentication': 'Auth',
        'data': 'Data', 'dashboard': 'Dashboard', 'report': 'Report',
        'validation': 'Validator', 'validator': 'Validator',
        'service': 'Service', 'api': 'API', 'endpoint': 'Endpoint',
    }

    subject = None
    for noun, mapped in subject_map.items():
        if noun in desc_lower:
            subject = mapped
            break
    if not subject:
        subject = "Implementation" if parent_id and '.' in parent_id else "Service"

    return f"{subject}.{action}"
```

Update `_create_child_from_details()`:

```python
# Extract or generate function_id
function_id = None
if hasattr(detail, "function_id") and detail.function_id:
    function_id = detail.function_id
else:
    # Generate from description
    desc = detail.description if hasattr(detail, "description") else sub_process
    function_id = _generate_function_id(desc, parent_id)
```

### Success Criteria

**Automated:**
- [ ] Test fails for right reason
- [ ] Test passes after implementation
- [ ] All decomposition tests pass

---

## Behavior 7: 3-Tier Hierarchy (Implementation Details as Children)

### Test Specification

**Given**: BAML returns multiple `implementation_details` for a subprocess
**When**: Hierarchy is built
**Then**: Each implementation detail becomes a child of the sub_process node with type "implementation"

### TDD Cycle

#### 🔴 Red: Write Failing Test

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
        # Assert: ID pattern
        # impl1.id == "REQ_000.1.1"
        # impl2.id == "REQ_000.1.2"
```

#### 🟢 Green: Minimal Implementation

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

### Success Criteria

**Automated:**
- [ ] Test fails for right reason
- [ ] Test passes after implementation
- [ ] All decomposition tests pass: `pytest planning_pipeline/tests/test_decomposition.py -v`

---

## Behavior 8: Arbitrary Depth ID Generation

### Test Specification

**Given**: Hierarchy needs 4+ levels
**When**: `add_child()` is called recursively
**Then**: IDs follow `REQ_XXX.Y.Z.W...` pattern

### TDD Cycle

#### 🔴 Red: Write Failing Test

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
```

#### 🟢 Green: Minimal Implementation

The existing `RequirementHierarchy.add_child()` and `get_by_id()` already support arbitrary depth through recursion. The test should pass without changes.

If not, ensure:
1. `add_child()` properly sets `parent_id` and appends to parent's `children`
2. `get_by_id()` recursively searches all levels

### Success Criteria

**Automated:**
- [ ] Test fails (if implementation missing)
- [ ] Test passes
- [ ] All model tests pass

---

## Integration & E2E Testing

### Integration Test: Full Decomposition Flow

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

### E2E Test: Real BAML Calls

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

---

## Implementation Order

Execute behaviors in this order (each builds on previous):

1. **Behavior 1**: Add `function_id` field to `RequirementNode`
2. **Behavior 2**: Add `related_concepts` field to `RequirementNode`
3. **Behavior 3**: Add `category` field to `RequirementNode`
4. **Behavior 4**: Store `function_id` from BAML response
5. **Behavior 5**: Store `related_concepts` from BAML response
6. **Behavior 6**: Generate semantic `function_id` when not provided
7. **Behavior 7**: 3-tier hierarchy (implementation details as children)
8. **Behavior 8**: Arbitrary depth ID generation

---

## References

- **Research**: `thoughts/searchable/shared/research/2026-01-04-step-decomposition-baml-integration.md`
- **Current Implementation**: `planning_pipeline/decomposition.py:133-347`
- **Model Definition**: `planning_pipeline/models.py:103-185`
- **Reference Pattern**: `/home/maceo/Dev/CodeWriter5/code-writer/src2/scope/requirements_processor.py:146-205`
- **BAML Schema**: `baml_src/Gate1SharedClasses.baml:17-31`
- **Test Fixtures**: `planning_pipeline/tests/conftest.py:85-137`
- **Beads Issue**: `silmari-Context-Engine-4hi`
