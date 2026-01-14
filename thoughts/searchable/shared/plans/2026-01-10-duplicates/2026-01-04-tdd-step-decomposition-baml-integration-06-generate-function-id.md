# Phase 6: Generate Semantic `function_id` When Not Provided

**Beads ID**: `silmari-Context-Engine-t6uj`
**Depends On**: Phase 1
**Blocks**: Phase 7

---

## Test Specification

**Given**: BAML response has no `function_id` (None or empty)
**When**: `_create_child_from_details()` is called
**Then**: A semantic `function_id` is generated from the description

**Examples**:
- "Authenticate user credentials" -> "Auth.authenticate"
- "Render dashboard UI" -> "Dashboard.render"
- "Validate input data" -> "Validator.validate"

---

## TDD Cycle

### Red: Write Failing Test

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

**Run**: `pytest planning_pipeline/tests/test_decomposition.py::TestGenerateFunctionIdFromDescription -v`

---

### Green: Minimal Implementation

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

---

### Refactor: Improve Code

Consider extracting the action/subject mappings to module-level constants for easier maintenance.

---

## Success Criteria

**Automated:**
- [x] Test fails for right reason
- [x] Test passes after implementation
- [x] All decomposition tests pass
