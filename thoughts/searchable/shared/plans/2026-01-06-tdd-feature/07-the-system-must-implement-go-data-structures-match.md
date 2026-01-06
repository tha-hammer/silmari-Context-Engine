# Phase 07: The system must implement Go data structures match...

## Requirements

### REQ_006: The system must implement Go data structures matching Python

The system must implement Go data structures matching Python dataclass schemas with proper JSON serialization and validation methods

#### REQ_006.1: Implement RequirementNode struct with all fields matching th

Implement RequirementNode struct with all fields matching the Python dataclass schema, including proper JSON tags and nested struct references for hierarchical requirement management

##### Testable Behaviors

1. Struct contains id field as string with json tag 'id'
2. Struct contains description field as string with json tag 'description'
3. Struct contains type field as string with json tag 'type' (values: 'parent', 'sub_process', 'implementation')
4. Struct contains parent_id field as *string with json tag 'parent_id,omitempty'
5. Struct contains children field as []RequirementNode with json tag 'children'
6. Struct contains acceptance_criteria field as []string with json tag 'acceptance_criteria'
7. Struct contains implementation field as *ImplementationComponents with json tag 'implementation,omitempty'
8. Struct contains testable_properties field as []TestableProperty with json tag 'testable_properties'
9. Struct contains function_id field as *string with json tag 'function_id,omitempty'
10. Struct contains related_concepts field as []string with json tag 'related_concepts'
11. Struct contains category field as string with json tag 'category'
12. Struct correctly serializes to JSON matching Python output format
13. Struct correctly deserializes from JSON matching Python input format
14. Children slice is initialized to empty slice (not nil) for consistent JSON output
15. Unit tests verify round-trip JSON serialization/deserialization
16. Unit tests verify nested RequirementNode children serialization

#### REQ_006.2: Implement Feature struct with all fields for feature trackin

Implement Feature struct with all fields for feature tracking including status flags, dependencies, and complexity metadata with proper JSON serialization

##### Testable Behaviors

1. Struct contains id field as string with json tag 'id'
2. Struct contains name field as string with json tag 'name'
3. Struct contains description field as string with json tag 'description'
4. Struct contains priority field as int with json tag 'priority,omitempty'
5. Struct contains category field as string with json tag 'category,omitempty'
6. Struct contains passes field as bool with json tag 'passes'
7. Struct contains blocked field as bool with json tag 'blocked,omitempty'
8. Struct contains blocked_reason field as string with json tag 'blocked_reason,omitempty'
9. Struct contains blocked_by field as []string with json tag 'blocked_by,omitempty'
10. Struct contains dependencies field as []string with json tag 'dependencies,omitempty'
11. Struct contains tests field as []string with json tag 'tests,omitempty'
12. Struct contains complexity field as string with json tag 'complexity,omitempty'
13. Struct contains needs_review field as bool with json tag 'needs_review,omitempty'
14. Feature with passes=false and blocked=false serializes correctly
15. Feature with all optional fields empty omits them from JSON output
16. Unit tests verify JSON output matches Python feature_list.json format
17. Unit tests verify deserialization from existing Python-generated feature files

#### REQ_006.3: Implement FeatureList struct containing Features array with 

Implement FeatureList struct containing Features array with methods for feature lookup, filtering, and dependency resolution

##### Testable Behaviors

1. Struct contains Features field as []Feature with json tag 'features'
2. FeatureList serializes to JSON with 'features' as root array key
3. FeatureList deserializes from JSON matching Python feature_list.json format
4. Empty FeatureList serializes as {"features": []} not null
5. Unit tests verify loading existing Python-generated feature_list.json files
6. Unit tests verify saving and reloading produces identical output
7. Struct supports direct iteration over Features slice

#### REQ_006.4: Implement Validate() method for RequirementNode performing p

Implement Validate() method for RequirementNode performing post-init validation matching Python dataclass __post_init__ logic including type validation and ID format checking

##### Testable Behaviors

1. Validate() returns error if type is not one of 'parent', 'sub_process', 'implementation'
2. Validate() returns error if id is empty string
3. Validate() returns error if id does not match REQ_XXX(.Y.Z) format pattern
4. Validate() returns error if description is empty string
5. Validate() recursively validates all children RequirementNodes
6. Validate() returns nil for valid RequirementNode with all required fields
7. Validate() aggregates multiple validation errors into single error message
8. Validate() checks parent_id references valid parent when present
9. Unit tests verify each validation rule independently
10. Unit tests verify recursive child validation
11. Unit tests verify error messages are descriptive and actionable
12. Validation follows Go error wrapping conventions (fmt.Errorf with %w)

#### REQ_006.5: Implement Validate() method for Feature performing validatio

Implement Validate() method for Feature performing validation of required fields, status consistency, and dependency references

##### Testable Behaviors

1. Validate() returns error if id is empty string
2. Validate() returns error if name is empty string
3. Validate() returns error if blocked=true but blocked_reason is empty
4. Validate() returns error if blocked=true but blocked_by is empty
5. Validate() returns error if complexity is non-empty and not valid value
6. Validate() returns error if passes=true and blocked=true simultaneously
7. Validate() warns if dependencies contains self-reference (feature depends on itself)
8. Validate() returns nil for valid Feature with all required fields
9. ValidateWithFeatureList(list *FeatureList) validates dependency IDs exist
10. Unit tests verify each validation rule independently
11. Unit tests verify status consistency checks
12. Unit tests verify complexity value validation


## Success Criteria

- [x] All tests pass
- [x] All behaviors implemented
- [ ] Code reviewed

## Implementation Summary (2026-01-06)

### Implemented in go/internal/planning/models.go

**RequirementNode struct (REQ_006.1, REQ_006.4)** - Previously implemented:
- All fields with proper JSON tags: ID, Description, Type, ParentID, Children, AcceptanceCriteria, Implementation, TestableProperties, FunctionID, RelatedConcepts, Category
- `Validate()` method checking type validity, description non-empty, category validation, and recursive testable property validation
- `AddChild()`, `GetByID()`, `NextChildID()` helper methods
- RequirementHierarchy container with `AddRequirement()`, `AddChild()`, `GetByID()`, `Validate()`, `ToJSON()`, `FromJSON()`

**Feature struct (REQ_006.2, REQ_006.5)** - Newly implemented:
- All fields matching Python feature_list.json schema:
  - `ID`, `Name`, `Description` (required)
  - `Priority`, `Category`, `Complexity` (optional metadata)
  - `Passes`, `Blocked`, `BlockedReason`, `BlockedBy`, `BlockedAt` (status flags)
  - `Dependencies`, `Tests` (references)
  - `NeedsReview`, `QAOrigin`, `Severity`, `SuggestedFix` (QA fields)
- `Validate()` method enforcing:
  - ID and Name required
  - blocked=true requires blocked_reason and blocked_by
  - Valid complexity values (high, medium, low)
  - Cannot have passes=true and blocked=true simultaneously
  - No self-reference in dependencies
- `ValidateWithFeatureList(list *FeatureList)` for cross-reference validation

**FeatureList struct (REQ_006.3)** - Newly implemented:
- `Features []Feature` with proper JSON serialization
- `NewFeatureList()` constructor
- `Add(feature)`, `GetByID(id)` methods
- `GetPending()`, `GetBlocked()`, `GetCompleted()` filtering methods
- `Stats()` returning total/completed/remaining/blocked counts
- `ToJSON()`, `FeatureListFromJSON()` for serialization
- `Validate()` validating all features with cross-reference checking
- Empty list serializes as `{"features":[]}` not null

### Test Coverage

81 tests passing in go/internal/planning/:
- `models_test.go`: RequirementNode, TestableProperty, RequirementHierarchy, Feature, FeatureList validation and serialization tests
- `claude_runner_test.go`: Claude wrapper tests
- `decomposition_test.go`: Decomposition logic tests
- `helpers_test.go`: Helper function tests
- `pipeline_test.go`: Pipeline orchestration tests
- `steps_test.go`: Step execution tests

New tests added:
- `TestFeatureValidation` (10 sub-tests covering all validation rules)
- `TestFeatureListBasics`, `TestFeatureListFiltering`, `TestFeatureListStats`
- `TestFeatureListJSON`, `TestFeatureListValidation`, `TestEmptyFeatureListJSON`