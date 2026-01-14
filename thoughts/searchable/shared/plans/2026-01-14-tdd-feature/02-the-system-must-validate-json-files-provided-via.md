# Phase 02: The system must validate JSON files provided via -...

## Requirements

### REQ_001: The system must validate JSON files provided via --plan-path

The system must validate JSON files provided via --plan-path against the RequirementHierarchy schema

#### REQ_001.1: Load and parse JSON content using RequirementHierarchy.from_

Load and parse JSON content using RequirementHierarchy.from_dict() to deserialize the JSON file into the RequirementHierarchy domain model

##### Testable Behaviors

1. The function opens the file at hierarchy_path with UTF-8 encoding
2. The function uses json.load() to parse the file content into a Python dictionary
3. The function passes the parsed dictionary to RequirementHierarchy.from_dict() for deserialization
4. The function returns a tuple containing (RequirementHierarchy, None, metadata) on success
5. The function catches json.JSONDecodeError and returns (None, error_message, {}) with descriptive message 'Plan validation failed: Invalid JSON - {error details}'
6. The function catches FileNotFoundError and returns (None, 'Plan validation failed: File not found - {path}', {})
7. The function catches generic Exception and returns (None, 'Plan validation failed: {error}', {})
8. The function calculates total_nodes by counting parent requirements plus all children recursively
9. The function populates metadata dict with hierarchy_path, requirements_count, total_nodes, validated=True, and validation_timestamp

#### REQ_001.2: Trigger RequirementNode.__post_init__() validation for each 

Trigger RequirementNode.__post_init__() validation for each node in the hierarchy during deserialization

##### Testable Behaviors

1. The __post_init__ method is automatically called by Python dataclass after __init__ completes
2. Validation is triggered recursively for each RequirementNode when from_dict() reconstructs children
3. Each RequirementNode in the hierarchy is validated including nested children at all levels
4. Validation errors raised during from_dict() propagate up to the calling _validate_hierarchy_path method
5. The validation order proceeds depth-first through the requirement tree structure
6. Validation errors include the specific field and value that failed validation
7. ValueError exceptions contain actionable error messages for debugging

#### REQ_001.3: Validate requirement type is in VALID_REQUIREMENT_TYPES (par

Validate requirement type is in VALID_REQUIREMENT_TYPES (parent, sub_process, implementation)

##### Testable Behaviors

1. The validation checks 'self.type not in VALID_REQUIREMENT_TYPES'
2. VALID_REQUIREMENT_TYPES is defined as frozenset(['parent', 'sub_process', 'implementation'])
3. Valid type 'parent' passes validation without error
4. Valid type 'sub_process' passes validation without error
5. Valid type 'implementation' passes validation without error
6. Invalid type raises ValueError with message "Invalid type '{self.type}'. Must be one of: {', '.join(VALID_REQUIREMENT_TYPES)}"
7. Type validation is case-sensitive (e.g., 'Parent' is invalid, 'parent' is valid)
8. Type validation occurs before description and category validation in __post_init__

#### REQ_001.4: Validate requirement category is in VALID_CATEGORIES (functi

Validate requirement category is in VALID_CATEGORIES (functional, non_functional, security, performance, usability, integration)

##### Testable Behaviors

1. The validation checks 'self.category not in VALID_CATEGORIES'
2. VALID_CATEGORIES is defined as frozenset(['functional', 'non_functional', 'security', 'performance', 'usability', 'integration'])
3. Valid category 'functional' passes validation without error
4. Valid category 'non_functional' passes validation without error
5. Valid category 'security' passes validation without error
6. Valid category 'performance' passes validation without error
7. Valid category 'usability' passes validation without error
8. Valid category 'integration' passes validation without error
9. Invalid category raises ValueError with message "Invalid category '{self.category}'. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
10. Category has default value 'functional' if not specified in JSON
11. Category validation is case-sensitive (e.g., 'Functional' is invalid, 'functional' is valid)
12. Category validation occurs after type and description validation in __post_init__

#### REQ_001.5: Validate description field is non-empty for each requirement

Validate description field is non-empty for each requirement node

##### Testable Behaviors

1. The validation checks 'not self.description or not self.description.strip()'
2. Empty string '' raises ValueError with message 'Requirement description must not be empty'
3. None value raises ValueError with message 'Requirement description must not be empty'
4. Whitespace-only string '   ' raises ValueError with message 'Requirement description must not be empty'
5. Tab-only string '\t\t' raises ValueError with message 'Requirement description must not be empty'
6. Newline-only string '\n\n' raises ValueError with message 'Requirement description must not be empty'
7. Mixed whitespace string ' \t\n ' raises ValueError with message 'Requirement description must not be empty'
8. Description with leading/trailing whitespace but non-empty content passes validation
9. Description validation occurs after type validation but before category validation in __post_init__
10. Minimum valid description is a single non-whitespace character


## Success Criteria

- [x] All tests pass (54 model tests + 74 pipeline tests = 128 total)
- [x] All behaviors implemented
- [x] Code reviewed

## Implementation Notes

Phase 2 requirements were already implemented in:
- `planning_pipeline/models.py`: `VALID_REQUIREMENT_TYPES`, `VALID_CATEGORIES`, `RequirementNode.__post_init__()`, `from_dict()` methods
- `silmari_rlm_act/pipeline.py`: `_validate_hierarchy_path()` method

Additional tests added for completeness:
- `test_tab_only_description_raises_error` - REQ_001.5.5
- `test_newline_only_description_raises_error` - REQ_001.5.6
- `test_single_char_description_is_valid` - REQ_001.5.10
- `test_description_with_leading_trailing_whitespace_valid` - REQ_001.5.8
- `test_validation_order_type_before_description` - REQ_001.3.8
- `test_validation_order_description_before_category` - REQ_001.5.9