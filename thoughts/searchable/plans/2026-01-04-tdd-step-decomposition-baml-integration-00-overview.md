# Step Decomposition BAML Integration - TDD Implementation Plan

## Overview

Enhance `step_decomposition.py` and `decomposition.py` to produce 3+ tier requirement hierarchies matching the CodeWriter5 expected output format (`test-002-alpha.02.json`). This includes adding `function_id`, `related_concepts`, and `category` fields, plus supporting arbitrary depth nesting.

**Related Research**: `thoughts/searchable/shared/research/2026-01-04-step-decomposition-baml-integration.md`
**Related Beads**: `silmari-Context-Engine-4hi`

---

## Phase Files

| Phase | File | Beads ID | Description |
|-------|------|----------|-------------|
| 1 | `...-01-function-id-field.md` | `219c` | Add `function_id` field to RequirementNode |
| 2 | `...-02-related-concepts-field.md` | `aya3` | Add `related_concepts` field to RequirementNode |
| 3 | `...-03-category-field.md` | `t4yq` | Add `category` field to RequirementNode |
| 4 | `...-04-store-function-id.md` | `iz7d` | Store `function_id` from BAML response |
| 5 | `...-05-store-related-concepts.md` | `mn41` | Store `related_concepts` from BAML response |
| 6 | `...-06-generate-function-id.md` | `t6uj` | Generate semantic `function_id` when not provided |
| 7 | `...-07-three-tier-hierarchy.md` | `usn7` | 3-tier hierarchy (implementation details as children) |
| 8 | `...-08-arbitrary-depth.md` | `vjie` | Arbitrary depth ID generation |

**Epic**: `silmari-Context-Engine-ec54`

---

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

---

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

---

## What We're NOT Doing

- Changing BAML schema (already has required fields)
- Modifying `step_research()` or `step_planning()` pipeline steps
- Changing the Mermaid visualization logic (will auto-adapt)
- Backward compatibility shims for old JSON format

---

## Testing Strategy

- **Framework**: pytest with Hypothesis for property-based testing
- **Test Types**:
  - Unit: Model field storage, serialization, ID generation
  - Integration: Full decomposition flow with mocked BAML
  - E2E: Real BAML calls (marked `@pytest.mark.e2e`)
- **Mocking**: Use existing `conftest.py` fixtures (`mock_baml_*`, `patch_baml_client`)
- **Patterns**: Follow existing class-based test organization

---

## Implementation Order

Execute phases in this order (each builds on previous):

1. **Phase 1**: Add `function_id` field to `RequirementNode`
2. **Phase 2**: Add `related_concepts` field to `RequirementNode`
3. **Phase 3**: Add `category` field to `RequirementNode`
4. **Phase 4**: Store `function_id` from BAML response
5. **Phase 5**: Store `related_concepts` from BAML response
6. **Phase 6**: Generate semantic `function_id` when not provided
7. **Phase 7**: 3-tier hierarchy (implementation details as children)
8. **Phase 8**: Arbitrary depth ID generation

**Dependencies**:
- Phases 1-3 can be done in parallel (model changes)
- Phases 4-6 depend on Phases 1-2 (uses new fields)
- Phase 7 depends on Phases 4-6 (full BAML extraction)
- Phase 8 can be done in parallel with Phase 7 (ID generation is independent)

---

## References

- **Research**: `thoughts/searchable/shared/research/2026-01-04-step-decomposition-baml-integration.md`
- **Current Implementation**: `planning_pipeline/decomposition.py:133-347`
- **Model Definition**: `planning_pipeline/models.py:103-185`
- **Reference Pattern**: `/home/maceo/Dev/CodeWriter5/code-writer/src2/scope/requirements_processor.py:146-205`
- **BAML Schema**: `baml_src/Gate1SharedClasses.baml:17-31`
- **Test Fixtures**: `planning_pipeline/tests/conftest.py:85-137`
- **Beads Issue**: `silmari-Context-Engine-4hi`
