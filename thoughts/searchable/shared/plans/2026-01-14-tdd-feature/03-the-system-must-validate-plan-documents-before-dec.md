# Phase 03: The system must validate plan documents before dec...

## Requirements

### REQ_002: The system must validate plan documents before decomposition

The system must validate plan documents before decomposition using the three-tier validation architecture

#### REQ_002.1: Validate JSON structure and file format ensuring the plan do

Validate JSON structure and file format ensuring the plan document is well-formed JSON with expected schema (Tier 1 validation)

##### Testable Behaviors

1. File must exist at the provided path (click.Path(exists=True) enforces this)
2. File must have .json extension or be parseable as valid JSON
3. JSON.loads() must succeed without JSONDecodeError
4. JSON structure must contain required top-level keys: 'requirements' (list) and 'metadata' (dict)
5. Must return descriptive error message with line number and character position on parse failure
6. Must handle empty files gracefully with specific error message
7. Must handle files with invalid UTF-8 encoding with appropriate error
8. Must validate file size is within acceptable limits (e.g., < 10MB) before parsing

#### REQ_002.2: Deserialize JSON to RequirementHierarchy triggering __post_i

Deserialize JSON to RequirementHierarchy triggering __post_init__ validation on all RequirementNode instances (Tier 2 validation)

##### Testable Behaviors

1. Must successfully deserialize valid JSON into RequirementHierarchy instance
2. Must recursively construct all RequirementNode children at any depth level
3. Must trigger RequirementNode.__post_init__() for every node (parent, sub_process, implementation)
4. Must reconstruct ImplementationComponents for implementation nodes via ImplementationComponents.from_dict()
5. Must reconstruct TestableProperty list for nodes with testable_properties via TestableProperty.from_dict()
6. Must preserve parent_id relationships throughout hierarchy
7. Must raise ValueError with descriptive message if any node fails validation
8. Must capture all validation errors (not fail-fast) and report complete list of issues
9. Must handle missing optional fields with sensible defaults (function_id=None, related_concepts=[], category='functional')

#### REQ_002.3: Validate requirement type is in VALID_REQUIREMENT_TYPES set 

Validate requirement type is in VALID_REQUIREMENT_TYPES set (parent, sub_process, implementation)

##### Testable Behaviors

1. Must accept exactly these type values: 'parent', 'sub_process', 'implementation'
2. Must reject any type value not in VALID_REQUIREMENT_TYPES frozenset
3. Must raise ValueError with message format: "Invalid type '{type}'. Must be one of: parent, sub_process, implementation"
4. Must be case-sensitive (e.g., 'Parent' is invalid)
5. Must reject None, empty string, and whitespace-only strings
6. Validation must occur during __post_init__ before object is fully constructed
7. Error message must list all valid options for user guidance
8. Type validation must precede other validations (fail fast on invalid type)

#### REQ_002.4: Validate requirement category is in VALID_CATEGORIES set (fu

Validate requirement category is in VALID_CATEGORIES set (functional, non_functional, security, performance, usability, integration)

##### Testable Behaviors

1. Must accept exactly these category values: 'functional', 'non_functional', 'security', 'performance', 'usability', 'integration'
2. Must reject any category value not in VALID_CATEGORIES frozenset
3. Must raise ValueError with message format: "Invalid category '{category}'. Must be one of: functional, integration, non_functional, performance, security, usability"
4. Must default to 'functional' when category field is not provided in input JSON
5. Must be case-sensitive (e.g., 'Functional' is invalid)
6. Must sort valid options alphabetically in error message for consistency
7. Category validation must occur after type validation in __post_init__
8. Must handle None value by using default 'functional' during from_dict() deserialization

#### REQ_002.5: Validate requirement description is not empty, null, or whit

Validate requirement description is not empty, null, or whitespace-only

##### Testable Behaviors

1. Must reject None value for description field
2. Must reject empty string '' for description field
3. Must reject whitespace-only strings (e.g., '   ', '\t\n') after stripping
4. Must raise ValueError with message: 'Requirement description must not be empty'
5. Description validation must occur after type validation in __post_init__ sequence
6. Must preserve original description value (no auto-stripping of valid descriptions)
7. Must handle description containing only unicode whitespace characters
8. Validation applies to all requirement types (parent, sub_process, implementation)
9. Must not truncate or modify valid descriptions - validation only, not normalization


## Success Criteria

- [x] All tests pass
- [x] All behaviors implemented
- [x] Code reviewed

## Implementation Notes

### Tests Added (2026-01-14)

**planning_pipeline/tests/test_models.py** (8 new tests):
- `test_whitespace_only_description_raises_error` - REQ_002.5
- `test_type_validation_case_sensitive` - REQ_002.3
- `test_type_validation_rejects_empty_string` - REQ_002.3
- `test_category_validation_case_sensitive` - REQ_002.4
- `test_type_error_message_lists_valid_options` - REQ_002.3
- `test_category_error_message_lists_valid_options_sorted` - REQ_002.4
- `test_description_not_modified_after_validation` - REQ_002.5

**silmari_rlm_act/tests/test_pipeline.py** (18 new tests in TestPlanDocumentValidation):
- REQ_002.1: `test_empty_file_produces_error`, `test_json_structure_requires_requirements_key`, `test_json_error_includes_position_info`, `test_utf8_encoding_error_handled`
- REQ_002.2: `test_recursive_children_reconstruction`, `test_implementation_components_reconstruction`, `test_testable_properties_reconstruction`, `test_missing_optional_fields_use_defaults`
- REQ_002.3: `test_type_validation_case_sensitive`, `test_type_validation_rejects_empty_string`, `test_valid_types_accepted`
- REQ_002.4: `test_category_validation_case_sensitive`, `test_category_defaults_when_missing_from_json`, `test_all_valid_categories_accepted`
- REQ_002.5: `test_description_whitespace_only_rejected`, `test_description_empty_string_rejected`, `test_description_validation_applies_to_all_types`, `test_valid_description_preserved`

### Existing Implementation

The core validation was already implemented in:
- `planning_pipeline/models.py`: `VALID_REQUIREMENT_TYPES`, `VALID_CATEGORIES`, `RequirementNode.__post_init__()`, `from_dict()` methods
- `silmari_rlm_act/pipeline.py`: `_validate_hierarchy_path()` method

### Test Results

- 48 tests in planning_pipeline/tests/test_models.py - ALL PASS
- 52 tests in silmari_rlm_act/tests/test_pipeline.py - ALL PASS
- 25 tests in silmari_rlm_act/tests/test_cli.py - ALL PASS

Total: 167+ tests passing