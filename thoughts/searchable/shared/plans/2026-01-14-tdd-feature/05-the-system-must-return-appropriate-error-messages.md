# Phase 05: The system must return appropriate error messages ...

## Requirements

### REQ_004: The system must return appropriate error messages and phase 

The system must return appropriate error messages and phase results when JSON validation fails

#### REQ_004.1: Return PhaseResult with status=FAILED when JSON parsing fail

Return PhaseResult with status=FAILED when JSON parsing fails

##### Testable Behaviors

1. When json.load() raises JSONDecodeError, the method returns (None, error_message, {}) tuple
2. The error message contains 'Invalid JSON' prefix followed by the specific parse error details
3. The returned tuple format is (hierarchy: None, error: str, metadata: empty dict)
4. The calling code in run() method creates PhaseResult with status=PhaseStatus.FAILED
5. The PhaseResult.phase_type is set to PhaseType.DECOMPOSITION
6. The PhaseResult.errors array contains exactly one error string from the validation
7. The PhaseResult.metadata includes 'validation_failed': True
8. The PhaseResult.metadata includes 'validated': False per REQ_004.4.9
9. The PhaseResult.metadata includes 'error_count': 1 per REQ_004.4.10
10. The PhaseResult includes timing information (started_at, completed_at, duration_seconds)

#### REQ_004.2: Include specific validation errors in the errors array of Ph

Include specific validation errors in the errors array of PhaseResult

##### Testable Behaviors

1. PhaseResult.errors is a list[str] containing all validation error messages
2. Each error message is descriptive and actionable for the user
3. Error messages include the file path that failed validation
4. Error messages include the specific validation rule that was violated
5. For JSON parse errors, message includes line/column information if available
6. For schema validation errors, message includes the field name that failed
7. For type/category errors, message includes the invalid value and valid options
8. Multiple errors can be accumulated if validation produces multiple failures
9. Errors are accessible via result.errors after pipeline.run() returns

#### REQ_004.3: Validate invalid JSON produces clear error message (test_pla

Validate invalid JSON produces clear error message (test_plan_path_validates_json_format)

##### Testable Behaviors

1. Test creates a temporary file containing invalid JSON syntax (e.g., 'not valid json {{{')
2. Test invokes pipeline.run() with hierarchy_path pointing to invalid JSON file
3. Test asserts result.status == PhaseStatus.FAILED
4. Test asserts result.errors contains at least one error with 'json' or 'valid' keyword (case-insensitive)
5. Test verifies the pipeline does not proceed to TDD_PLANNING phase
6. Test fixture uses tmp_path to create temporary files
7. Test uses mock_cwa and mock_beads_controller fixtures
8. Test uses AutonomyMode.FULLY_AUTONOMOUS to avoid user interaction

#### REQ_004.4: Validate incorrect requirement type produces error (test_pla

Validate incorrect requirement type produces error (test_plan_path_validates_requirement_type)

##### Testable Behaviors

1. Test creates JSON with requirement having type='invalid_type' (not in VALID_REQUIREMENT_TYPES)
2. VALID_REQUIREMENT_TYPES = frozenset(['parent', 'sub_process', 'implementation'])
3. Test verifies result.status == PhaseStatus.FAILED when invalid type is used
4. Test verifies error message contains 'type' or 'invalid' keyword
5. Test JSON structure includes all required fields: id, description, type, parent_id, children, acceptance_criteria, category
6. Test uses valid category='functional' to isolate type validation failure
7. RequirementNode.__post_init__() raises ValueError for invalid type

#### REQ_004.5: Validate incorrect category produces error (test_plan_path_v

Validate incorrect category produces error (test_plan_path_validates_requirement_category)

##### Testable Behaviors

1. Test creates JSON with requirement having category='invalid_category' (not in VALID_CATEGORIES)
2. VALID_CATEGORIES = frozenset(['functional', 'non_functional', 'security', 'performance', 'usability', 'integration'])
3. Test verifies result.status == PhaseStatus.FAILED when invalid category is used
4. Test verifies error message contains 'category' or 'invalid' keyword
5. Test JSON structure includes all required fields with valid type='parent'
6. Test uses valid type to isolate category validation failure
7. RequirementNode.__post_init__() raises ValueError for invalid category


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed