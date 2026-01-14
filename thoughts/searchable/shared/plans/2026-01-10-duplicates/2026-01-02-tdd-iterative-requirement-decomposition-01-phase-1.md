# Phase 1: RequirementNode Data Model with Invariants

## Overview

Implement core data models for requirement hierarchy with property-based tests ensuring structural invariants are maintained.

## Dependencies

- **Requires**: None (foundation phase)
- **Blocks**: Phase 2 (Visualization), Phase 3 (Property Generator), Phase 4 (BAML Decomposition)

## Human-Testable Function

```python
# After implementation, verify with:
from planning_pipeline.models import RequirementNode, RequirementHierarchy

node = RequirementNode(id="REQ_001", description="Test requirement", type="parent")
as_dict = node.to_dict()
restored = RequirementNode.from_dict(as_dict)
assert node.description == restored.description  # Should pass
```

## Changes Required

### New Files

| File | Purpose |
|------|---------|
| `planning_pipeline/models.py` | Core data models |
| `planning_pipeline/tests/test_models.py` | Property-based tests |

### planning_pipeline/models.py (new file)

Create dataclasses with serialization:

```python
# planning_pipeline/models.py:1-100
@dataclass
class ImplementationComponents:
    frontend: List[str]
    backend: List[str]
    middleware: List[str]
    shared: List[str]
    # to_dict(), from_dict() methods

@dataclass
class TestableProperty:
    criterion: str
    property_type: str  # "invariant", "round_trip", "idempotence", "oracle"
    hypothesis_strategy: str
    test_skeleton: str
    # to_dict(), from_dict() methods

@dataclass
class RequirementNode:
    id: str  # Format: REQ_\d{3}(\.\d+)*
    description: str
    type: str  # "parent", "sub_process", "implementation"
    parent_id: Optional[str] = None
    children: List["RequirementNode"] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    implementation: Optional[ImplementationComponents] = None
    testable_properties: List[TestableProperty] = field(default_factory=list)
    # to_dict(), from_dict(), __post_init__ validation

@dataclass
class RequirementHierarchy:
    requirements: List[RequirementNode]
    metadata: Dict[str, Any] = field(default_factory=dict)
    # add_requirement(), add_child(), get_by_id(), to_dict(), from_dict()
```

### planning_pipeline/tests/test_models.py (new file)

```python
# planning_pipeline/tests/test_models.py:1-100
# Property-based tests using Hypothesis:
# - TestRequirementNodeProperties: description_preserved, type_and_description_valid, acceptance_criteria_round_trip
# - RequirementHierarchyStateMachine: stateful tests for add/remove operations
# - Invariants: ids_are_unique, parent_child_consistency, hierarchy_depth_max_three
```

## TDD Cycle

### Red Phase
```bash
# Create test file first, run to see failures
pytest planning_pipeline/tests/test_models.py -v
# Expected: ImportError (models module doesn't exist)
```

### Green Phase
```bash
# Implement minimal models.py
pytest planning_pipeline/tests/test_models.py -v
# Expected: All tests pass
```

### Refactor Phase
```bash
# Add validation in __post_init__, run all tests
pytest planning_pipeline/tests/test_models.py -v --hypothesis-show-statistics
# Expected: All tests pass with Hypothesis statistics
```

## Success Criteria

### Automated
- [x] `pytest planning_pipeline/tests/test_models.py -v` passes
- [x] `pytest --hypothesis-show-statistics` shows no counterexamples
- [ ] `mypy planning_pipeline/models.py` type checks (if mypy installed)

### Manual
- [x] `RequirementNode` round-trips through JSON: Create node → to_dict() → from_dict() → compare
- [x] `RequirementHierarchy` maintains parent-child consistency after add_child()
- [x] Invalid types raise `ValueError` (e.g., `type="invalid"`)

## Test Properties to Verify

| Property | Test Method | Strategy |
|----------|-------------|----------|
| Description preserved | `test_description_preserved` | `st.text(min_size=1)` |
| Type validation | `test_type_and_description_valid` | `st.sampled_from(["parent", "sub_process", "implementation"])` |
| Serialization round-trip | `test_acceptance_criteria_round_trip` | `st.lists(st.text())` |
| Unique IDs | `invariant: ids_are_unique` | Stateful machine |
| Max depth 3 | `invariant: hierarchy_depth_max_three` | Stateful machine |

## Design Decisions

### Why Python Dataclasses (Not BAML-Generated Types)

BAML defines similar types in `baml_src/Gate1SharedClasses.baml` (e.g., `ImplementationComponents`, `Requirement`). We intentionally create **separate Python dataclasses** because:

1. **Decoupling**: Pipeline models shouldn't depend on BAML client regeneration
2. **Extended functionality**: We add `to_dict()`, `from_dict()`, validation, and hierarchy methods
3. **Testing**: Pure Python dataclasses are easier to test without BAML runtime
4. **Flexibility**: Can evolve independently of BAML schema changes

Phase 4 handles conversion between BAML response types and these models.

### Sub-Processes Representation

The BAML `Requirement` type has `sub_processes: string[]` (raw text descriptions). Our `RequirementNode` represents these as **child nodes** instead:

- BAML: `Requirement.sub_processes = ["Login flow", "Session management"]`
- Python: `RequirementNode.children = [RequirementNode(id="REQ_001.1", ...), ...]`

This allows recursive hierarchy with typed children rather than flat strings.

## JSON Schema Specification

### RequirementNode JSON Structure

```json
{
  "id": "REQ_001",
  "description": "User authentication system",
  "type": "parent",
  "parent_id": null,
  "children": [
    {
      "id": "REQ_001.1",
      "description": "Login flow implementation",
      "type": "sub_process",
      "parent_id": "REQ_001",
      "children": [],
      "acceptance_criteria": ["Form validates email format"],
      "implementation": {
        "frontend": ["LoginForm", "AuthContext"],
        "backend": ["AuthService.login"],
        "middleware": ["validateToken"],
        "shared": ["User"]
      },
      "testable_properties": []
    }
  ],
  "acceptance_criteria": [],
  "implementation": null,
  "testable_properties": []
}
```

### ImplementationComponents JSON Structure

```json
{
  "frontend": ["ComponentName", "PageName"],
  "backend": ["ServiceName.method", "RepositoryName"],
  "middleware": ["middlewareName"],
  "shared": ["ModelName", "UtilityName"]
}
```

### TestableProperty JSON Structure

```json
{
  "criterion": "Must validate agent_id uniqueness",
  "property_type": "invariant",
  "hypothesis_strategy": "st.text(min_size=1)",
  "test_skeleton": "@given(st.text(min_size=1))\ndef test_..."
}
```

### RequirementHierarchy JSON Structure

```json
{
  "requirements": [/* array of RequirementNode */],
  "metadata": {
    "source_research": "path/to/research.md",
    "created_at": "2026-01-02T10:00:00Z",
    "version": "1.0"
  }
}
```

## Implementation Notes

1. Use `dataclasses.dataclass` with `field(default_factory=...)` for mutable defaults
2. ID pattern: `REQ_\d{3}(\.\d+)*` (e.g., REQ_001, REQ_001.2, REQ_001.2.1)
3. Type hierarchy: parent → sub_process → implementation (3 levels max)
4. Non-empty description required (validate in `__post_init__`)
5. `to_dict()` must handle recursive children serialization
6. `from_dict()` must reconstruct parent_id references
