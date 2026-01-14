# Phase 01: The CLI must support a --plan-path option that acc...

## Requirements

### REQ_000: The CLI must support a --plan-path option that accepts a pat

The CLI must support a --plan-path option that accepts a path to an existing TDD plan/hierarchy JSON document

#### REQ_000.1: Implement click.Path validation with exists=True, file_okay=

Implement click.Path validation with exists=True, file_okay=True, dir_okay=False for the --plan-path CLI option

##### Testable Behaviors

1. The --plan-path option uses click.Path type with exists=True parameter
2. The --plan-path option uses click.Path type with file_okay=True parameter
3. The --plan-path option uses click.Path type with dir_okay=False parameter
4. The --plan-path option has default=None for optional usage
5. CLI returns error exit code when --plan-path file does not exist
6. CLI returns error exit code when --plan-path points to a directory instead of a file
7. CLI accepts valid file paths that exist on the filesystem
8. The option is accessible via '--plan-path' command line argument
9. Running 'silmari-rlm-act run --help' shows --plan-path in the output

#### REQ_000.2: Pass the plan_path CLI parameter to pipeline.run() as hierar

Pass the plan_path CLI parameter to pipeline.run() as hierarchy_path parameter to maintain correct internal naming

##### Testable Behaviors

1. The plan_path value from CLI is passed to pipeline.run() as hierarchy_path keyword argument
2. When plan_path is None, hierarchy_path is not passed or is passed as None
3. The pipeline.run() method signature accepts hierarchy_path as Optional[str]
4. The mapping preserves the exact file path string without modification
5. Integration test confirms plan_path='path/to/file.json' results in hierarchy_path='path/to/file.json' in pipeline
6. The pipeline receives hierarchy_path in its kwargs dictionary

#### REQ_000.3: Skip ResearchPhase execution when --plan-path is provided si

Skip ResearchPhase execution when --plan-path is provided since hierarchy JSON contains pre-decomposed requirements

##### Testable Behaviors

1. When hierarchy_path is provided, ResearchPhase.execute() is NOT called
2. When hierarchy_path is provided, no research document (.md) is generated
3. Pipeline state shows ResearchPhase as skipped (not failed, not complete)
4. Synthetic PhaseResult is created for skipped ResearchPhase with appropriate status
5. Pipeline proceeds directly to TDDPlanningPhase after skipping Research and Decomposition
6. No Claude API calls are made for research when hierarchy_path is provided
7. Pipeline metadata includes 'research_skipped': True flag
8. The skipped phase result includes hierarchy_path in its metadata for traceability

#### REQ_000.4: Skip DecompositionPhase execution when --plan-path is provid

Skip DecompositionPhase execution when --plan-path is provided since the JSON already contains decomposed requirements

##### Testable Behaviors

1. When hierarchy_path is provided, DecompositionPhase.execute() is NOT called
2. When hierarchy_path is provided, no new requirement_hierarchy.json is generated
3. The provided hierarchy JSON is loaded and validated via _validate_hierarchy_path()
4. JSON is validated against RequirementHierarchy schema using from_dict()
5. Each RequirementNode triggers __post_init__() validation for type and category
6. Validation confirms type is in VALID_REQUIREMENT_TYPES frozenset
7. Validation confirms category is in VALID_CATEGORIES frozenset
8. Validation confirms description is non-empty string
9. Synthetic PhaseResult is created for skipped DecompositionPhase
10. Metadata includes 'hierarchy_path', 'requirements_count', 'total_nodes', 'validated': True
11. On validation failure, PhaseResult has status=FAILED with specific error message
12. Invalid JSON format returns error: 'Plan validation failed: Invalid JSON - {details}'
13. Invalid requirement type returns error: 'Plan validation failed: {validation_error}'
14. Pipeline state is updated with the synthetic decomposition result

#### REQ_000.5: Provide descriptive help text explaining the option accepts 

Provide descriptive help text explaining the option accepts TDD plan/hierarchy JSON and skips research and decomposition phases

##### Testable Behaviors

1. Help text is provided via help= parameter in @click.option decorator
2. Help text mentions 'TDD plan/hierarchy JSON' to indicate expected file format
3. Help text explains that research phase is skipped when option is used
4. Help text explains that decomposition phase is skipped when option is used
5. Running 'silmari-rlm-act run --help' displays the help text for --plan-path
6. Help text is concise but informative (under 100 characters ideal)
7. Help text matches the actual behavior of the option


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed