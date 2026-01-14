# Phase 05: The pipeline must support kwargs passthrough for r...

## Requirements

### REQ_004: The pipeline must support kwargs passthrough for research_pa

The pipeline must support kwargs passthrough for research_path and hierarchy_path to enable phase skipping

#### REQ_004.1: Pipeline must pass research_path kwarg to DecompositionPhase

Pipeline must pass research_path kwarg to DecompositionPhase when ResearchPhase is skipped. When a user provides --research-path CLI argument, the pipeline should bypass the ResearchPhase entirely and pass the provided path directly to the DecompositionPhase via kwargs.

##### Testable Behaviors

1. When research_path kwarg is provided, ResearchPhase.execute() is NOT invoked
2. DecompositionPhase receives research_path from kwargs when no ResearchPhase result exists
3. The research_path file must exist and be a valid markdown file (validated by click.Path before pipeline)
4. Pipeline state correctly reflects that ResearchPhase was skipped (status=SKIPPED or equivalent)
5. DecompositionPhase can read and parse the provided research document successfully
6. Pipeline logs indicate research phase was skipped due to --research-path argument
7. If research_path is invalid or unreadable, pipeline fails with descriptive error before DecompositionPhase starts

#### REQ_004.2: Pipeline must pass hierarchy_path kwarg to TDDPlanningPhase 

Pipeline must pass hierarchy_path kwarg to TDDPlanningPhase when DecompositionPhase is skipped. When a user provides --plan-path CLI argument pointing to a valid requirement hierarchy JSON, the pipeline should bypass both ResearchPhase and DecompositionPhase, passing the hierarchy directly to TDDPlanningPhase.

##### Testable Behaviors

1. When hierarchy_path (plan-path) kwarg is provided, both ResearchPhase and DecompositionPhase are NOT invoked
2. TDDPlanningPhase receives hierarchy_path from kwargs when no DecompositionPhase result exists
3. The hierarchy_path file must exist and be valid JSON conforming to RequirementHierarchy schema
4. Pipeline state correctly reflects that ResearchPhase and DecompositionPhase were skipped
5. TDDPlanningPhase can deserialize the provided JSON into RequirementHierarchy successfully
6. Pipeline logs indicate which phases were skipped due to --plan-path argument
7. If hierarchy_path JSON is malformed or schema-invalid, pipeline fails with descriptive error before TDDPlanningPhase starts
8. Metadata from the provided hierarchy JSON is preserved and passed through to TDDPlanningPhase

#### REQ_004.3: Return PhaseResult with status=COMPLETE and metadata for val

Return PhaseResult with status=COMPLETE and metadata for validated plans. When an existing plan document is provided via --plan-path, the pipeline must validate the document structure and content, then return a PhaseResult indicating successful validation with comprehensive metadata about the validated hierarchy.

##### Testable Behaviors

1. PhaseResult returned has status=PhaseStatus.COMPLETE when validation succeeds
2. PhaseResult.metadata contains 'validated': True flag
3. PhaseResult.metadata contains 'requirements_count' with count of top-level requirements
4. PhaseResult.metadata contains 'total_nodes' with recursive count of all requirement nodes including children
5. PhaseResult.metadata contains 'hierarchy_path' pointing to the validated file
6. PhaseResult.metadata contains 'validation_timestamp' with ISO format timestamp
7. PhaseResult.artifacts list contains the hierarchy_path as first element
8. All RequirementNode objects pass __post_init__ validation (type in VALID_REQUIREMENT_TYPES, non-empty description, category in VALID_CATEGORIES)
9. JSON structure conforms to RequirementHierarchy schema with 'requirements' array and optional 'metadata' object
10. If --validate-full flag provided, BAML ProcessGate1RequirementValidationPrompt() is invoked and results included in metadata

#### REQ_004.4: Return PhaseResult with status=FAILED and errors array for i

Return PhaseResult with status=FAILED and errors array for invalid plans. When an existing plan document provided via --plan-path fails validation (malformed JSON, missing required fields, invalid requirement types, empty descriptions, or invalid categories), return a PhaseResult indicating failure with detailed error messages.

##### Testable Behaviors

1. PhaseResult returned has status=PhaseStatus.FAILED when any validation fails
2. PhaseResult.errors array contains at least one descriptive error message
3. JSON parsing errors (JSONDecodeError) produce error message: 'Plan validation failed: Invalid JSON - {specific_error}'
4. Missing file errors (FileNotFoundError) produce error message: 'Plan validation failed: File not found - {path}'
5. RequirementNode type validation errors include the invalid type and valid options: 'Invalid requirement type '{type}'. Must be one of: parent, sub_process, implementation'
6. Empty description errors identify the requirement: 'Requirement {id} has empty description'
7. Invalid category errors include the invalid category and valid options: 'Invalid category '{category}' for requirement {id}. Must be one of: functional, non_functional, security, performance, usability, integration'
8. Multiple validation errors are collected and all reported in errors array (not fail-fast)
9. PhaseResult.metadata contains 'validated': False flag
10. PhaseResult.metadata contains 'error_count' with total number of validation errors
11. Pipeline execution halts gracefully after returning FAILED PhaseResult
12. Error messages are actionable and help user fix the plan document


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed