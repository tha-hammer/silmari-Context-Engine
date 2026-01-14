# Phase 02: The CLI must support a --plan-path option that acc...

## Requirements

### REQ_001: The CLI must support a --plan-path option that accepts a pat

The CLI must support a --plan-path option that accepts a path to an existing TDD plan/hierarchy JSON document and skips decomposition phase when provided

#### REQ_001.1: Add --plan-path option to the CLI using Click framework with

Add --plan-path option to the CLI using Click framework with proper path validation to accept existing TDD plan/hierarchy JSON files

##### Testable Behaviors

1. The --plan-path option is added to the run command in silmari_rlm_act/cli.py
2. Option uses click.Path(exists=True, file_okay=True, dir_okay=False) type
3. Option has default=None to make it optional
4. Option includes help text: 'Path to existing TDD plan/hierarchy JSON (skips decomposition phase)'
5. CLI raises appropriate error when --plan-path points to non-existent file
6. CLI raises appropriate error when --plan-path points to a directory instead of a file
7. The plan_path parameter is added to the run() function signature as Optional[str]
8. Option follows existing naming convention pattern (kebab-case for CLI, snake_case for Python)

#### REQ_001.2: Pass the hierarchy_path from CLI --plan-path argument throug

Pass the hierarchy_path from CLI --plan-path argument through to pipeline kwargs so downstream phases can consume it

##### Testable Behaviors

1. When --plan-path is provided, it is passed as kwargs['hierarchy_path'] to pipeline.run()
2. The existing pipeline.py integration point at lines 174-201 receives hierarchy_path via kwargs
3. The hierarchy_path is available in self.state for phase result tracking
4. Pipeline logs which hierarchy_path is being used when provided via CLI
5. The kwargs passthrough does not break existing functionality when --plan-path is not provided
6. The hierarchy_path value is stored in PipelineState for downstream phase access

#### REQ_001.3: Skip DecompositionPhase execution when --plan-path is provid

Skip DecompositionPhase execution when --plan-path is provided since the hierarchy already exists

##### Testable Behaviors

1. When hierarchy_path is provided via kwargs, DecompositionPhase.execute() is NOT called
2. Pipeline state is updated to mark DECOMPOSITION phase as SKIPPED (not COMPLETE)
3. PhaseResult for DECOMPOSITION includes metadata indicating it was skipped due to --plan-path
4. The skipped phase does not produce artifacts but passes hierarchy_path to next phase
5. Pipeline logs 'Skipping DecompositionPhase: using existing hierarchy from {path}'
6. Subsequent phases (TDDPlanningPhase) still receive the hierarchy_path correctly
7. Phase ordering and dependencies are maintained despite skip

#### REQ_001.4: Skip ResearchPhase execution when --plan-path is provided si

Skip ResearchPhase execution when --plan-path is provided since the hierarchy already contains decomposed requirements

##### Testable Behaviors

1. When hierarchy_path is provided via kwargs, ResearchPhase.execute() is NOT called
2. Pipeline state is updated to mark RESEARCH phase as SKIPPED
3. PhaseResult for RESEARCH includes metadata indicating it was skipped due to --plan-path
4. The --question argument is NOT required when --plan-path is provided
5. CLI validation is updated: --question required unless --research-path OR --plan-path OR --resume
6. Pipeline logs 'Skipping ResearchPhase: using existing hierarchy from {path}'
7. No research artifacts are produced when skipped

#### REQ_001.5: Support and validate the JSON hierarchy format produced by D

Support and validate the JSON hierarchy format produced by DecompositionPhase output when loading from --plan-path

##### Testable Behaviors

1. JSON file from --plan-path is loaded and parsed using json.load()
2. Parsed JSON is validated by deserializing to RequirementHierarchy.from_dict()
3. Each RequirementNode in hierarchy triggers __post_init__ validation
4. Validation checks: type in VALID_REQUIREMENT_TYPES ('parent', 'sub_process', 'implementation')
5. Validation checks: category in VALID_CATEGORIES ('functional', 'non_functional', 'security', etc.)
6. Validation checks: description is non-empty string
7. Clear error message returned if JSON is malformed: 'Plan validation failed: {specific_error}'
8. Clear error message returned if RequirementNode validation fails with field name and invalid value
9. PhaseResult with status=FAILED and errors list is returned on validation failure
10. Successful validation returns PhaseResult with metadata including requirements_count and total_nodes


## Success Criteria

- [x] All tests pass
- [x] All behaviors implemented
- [ ] Code reviewed

## Implementation Notes

**Completed 2026-01-14**

### Changes Made:

1. **cli.py**:
   - Added `--plan-path` option with `click.Path(exists=True, file_okay=True, dir_okay=False)`
   - Updated argument validation to allow `--plan-path` as alternative to `--question`
   - Added warning when both `--question` and `--plan-path` are provided
   - Added warning when both `--research-path` and `--plan-path` are provided
   - Updated console output to show plan document path when skipping phases
   - Passes `hierarchy_path` kwarg to `pipeline.run()`

2. **pipeline.py**:
   - Added import for `RequirementHierarchy` from `planning_pipeline.models`
   - Added `_validate_hierarchy_path()` method for JSON validation
   - Added logic in `run()` to detect `hierarchy_path` kwarg
   - Creates synthetic `PhaseResult` for RESEARCH phase when hierarchy_path provided
   - Creates synthetic `PhaseResult` for DECOMPOSITION phase with validation metadata
   - Sets `metadata={'skipped': True, 'reason': 'hierarchy_path provided'}`
   - Creates checkpoints with `phase='research-skipped'` and `phase='decomposition-skipped'`
   - Validates JSON format, RequirementHierarchy structure, type, and category
   - Returns FAILED status with appropriate error messages on validation failure
   - Includes `requirements_count` and `total_nodes` in metadata on success

### Tests Added:

- `test_cli.py::TestPlanPathOption` - 8 tests covering all CLI behaviors
- `test_pipeline.py::TestPlanPathSkip` - 12 tests covering pipeline skipping and validation

All 336 tests pass.