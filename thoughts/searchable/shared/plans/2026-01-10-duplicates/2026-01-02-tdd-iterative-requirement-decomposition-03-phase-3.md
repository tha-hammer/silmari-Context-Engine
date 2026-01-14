# Phase 3: Property Derivation from Acceptance Criteria

## Overview

Generate Hypothesis test skeletons from acceptance criteria strings. This phase creates a property generator that analyzes acceptance criteria and produces appropriate property-based tests.

## Dependencies

- **Requires**: Phase 1 (Data Models)
- **Blocks**: Phase 5 (Step Integration)

## Human-Testable Function

```python
# After implementation, verify with:
from planning_pipeline.property_generator import derive_properties, generate_test_skeleton

criteria = ["Must validate agent_id uniqueness", "Session data must be preserved after save/load"]
properties = derive_properties(criteria)

for prop in properties:
    skeleton = generate_test_skeleton(prop, class_name="SessionManager")
    print(skeleton)
# Should output valid Python test code with @given decorators
```

## Changes Required

### New Files

| File | Purpose |
|------|---------|
| `planning_pipeline/property_generator.py` | Property derivation and test generation |
| `planning_pipeline/tests/test_property_generator.py` | Tests for property generator |

### planning_pipeline/property_generator.py (new file)

```python
# planning_pipeline/property_generator.py:1-150

class PropertyType(Enum):
    INVARIANT = "invariant"       # Uniqueness, state validity
    ROUND_TRIP = "round_trip"     # Serialize/deserialize, encode/decode
    IDEMPOTENCE = "idempotence"   # Operation applied twice = once
    ORACLE = "oracle"             # Compare to reference implementation

# Pattern matching for criterion classification
PROPERTY_PATTERNS = [
    (r"unique|distinct|no duplicate", PropertyType.INVARIANT, "st.text(min_size=1)"),
    (r"not empty|non-empty|has content", PropertyType.INVARIANT, "st.text(min_size=1)"),
    (r"state|status|must be", PropertyType.INVARIANT, "st.sampled_from([])"),
    (r"save.*load|encode.*decode|serialize|round.?trip", PropertyType.ROUND_TRIP, "st.text()"),
    (r"preserved|unchanged|maintains", PropertyType.ROUND_TRIP, "st.text()"),
    (r"twice|multiple times|idempotent|same result", PropertyType.IDEMPOTENCE, "st.lists(st.integers())"),
    (r"sorted|ordered|stable", PropertyType.IDEMPOTENCE, "st.lists(st.integers())"),
    (r"reference|oracle|matches|equals", PropertyType.ORACLE, "st.text()"),
]

def derive_properties(criteria: List[str]) -> List[TestableProperty]:
    """Derive testable properties from acceptance criteria strings."""

def generate_test_skeleton(prop: TestableProperty, class_name: str) -> str:
    """Generate Hypothesis test skeleton for a single property."""

def generate_full_test_file(properties: List[TestableProperty], class_name: str, module_path: str) -> str:
    """Generate complete test file with imports and all property tests."""
```

### planning_pipeline/tests/test_property_generator.py (new file)

```python
# planning_pipeline/tests/test_property_generator.py:1-100

class TestDeriveProperties:
    # test_uniqueness_criterion_produces_invariant
    # test_state_criterion_produces_invariant
    # test_validation_criterion_produces_round_trip
    # test_empty_criteria_returns_empty

class TestGenerateTestSkeleton:
    # test_generates_valid_python (uses ast.parse)
    # test_includes_hypothesis_decorator
    # test_includes_class_under_test

class TestPropertyTypes:
    # Parametrized tests for criterion classification
    # @pytest.mark.parametrize("criterion,expected_type", [...])
```

## TDD Cycle

### Red Phase
```bash
pytest planning_pipeline/tests/test_property_generator.py -v
# Expected: ImportError (property_generator module doesn't exist)
```

### Green Phase
```bash
# Implement minimal property_generator.py
pytest planning_pipeline/tests/test_property_generator.py -v
# Expected: All tests pass
```

### Refactor Phase
```bash
# Add more pattern recognition, improve skeleton templates
pytest planning_pipeline/tests/test_property_generator.py -v
# Verify generated code parses: python -c "import ast; ast.parse('''...''')"
```

## Success Criteria

### Automated
- [x] `pytest planning_pipeline/tests/test_property_generator.py -v` passes
- [x] All `ast.parse()` tests pass (generated code is valid Python)
- [x] Generated test file can be imported without errors

### Manual
- [x] Run generated test skeleton against real implementation
- [x] Property types match criterion semantics (uniqueness → invariant, save/load → round_trip)
- [x] Strategies are appropriate for data types mentioned in criteria

## Property Type Classification

| Criterion Pattern | Property Type | Default Strategy |
|------------------|---------------|------------------|
| `unique`, `distinct`, `no duplicate` | invariant | `st.text(min_size=1)` |
| `not empty`, `non-empty`, `has content` | invariant | `st.text(min_size=1)` |
| `state`, `status`, `must be` | invariant | `st.sampled_from([])` |
| `save.*load`, `encode.*decode`, `serialize` | round_trip | `st.text()` |
| `preserved`, `unchanged`, `maintains` | round_trip | `st.text()` |
| `twice`, `multiple times`, `idempotent` | idempotence | `st.lists(st.integers())` |
| `sorted`, `ordered`, `stable` | idempotence | `st.lists(st.integers())` |
| `reference`, `oracle`, `matches` | oracle | `st.text()` |

## Generated Test Template

```python
@given(st.text(min_size=1))
def test_property_must_validate_agent_id_uniqu(self, value):
    """Property: Must validate agent_id uniqueness"""
    instance = SessionManager()
    # TODO: Implement invariant check
    # Given: instance with value
    # When: operation performed
    # Then: invariant holds
    assert True  # Replace with actual assertion
```

## Implementation Notes

1. Sanitize criterion text for method names (replace non-alphanumeric with `_`, limit to 30 chars)
2. Default to `invariant` type if no pattern matches
3. Each property type has a different skeleton template with appropriate structure
4. Generated skeletons include TODO comments guiding implementation
5. Full test file includes imports: `pytest`, `hypothesis`, and module under test
