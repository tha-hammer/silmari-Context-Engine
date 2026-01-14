# Phase 01: The CLI must support a --research-path option that...

## Requirements

### REQ_000: The CLI must support a --research-path option that accepts a

The CLI must support a --research-path option that accepts a path to an existing research document and skips the research phase when provided

#### REQ_000.1: Add --research-path CLI option using click.Path with file ex

Add --research-path CLI option using click.Path with file existence validation

##### Testable Behaviors

1. Option is defined with type click.Path(exists=True, file_okay=True, dir_okay=False)
2. Option has both long form --research-path and is accessible via parameter name research_path
3. Help text clearly indicates the option accepts a path to an existing research document
4. Help text states that providing this option skips the research phase
5. Option default is None to indicate optional usage
6. Invalid file paths produce clear error messages from click's built-in validation
7. Option appears in silmari-rlm-act run --help output

#### REQ_000.2: Pass research_path to pipeline.run() kwargs when the --resea

Pass research_path to pipeline.run() kwargs when the --research-path option is provided

##### Testable Behaviors

1. When research_path is provided (not None), it is passed to pipeline.run() as a keyword argument
2. The research_path value is passed as-is without modification to preserve the original path
3. Existing pipeline.run() call in non-resume mode includes research_path=research_path in kwargs
4. The research_path kwarg is propagated to phase_kwargs in pipeline.py lines 360-374
5. DecompositionPhase receives research_path via kwargs.get('research_path') at pipeline.py line 167
6. Path is converted to Path object in pipeline._execute_phase() if needed

#### REQ_000.3: Skip ResearchPhase execution when --research-path is provide

Skip ResearchPhase execution when --research-path is provided with valid document

##### Testable Behaviors

1. When research_path kwarg is provided, ResearchPhase.execute_with_checkpoint() is NOT called
2. A synthetic PhaseResult is created for RESEARCH phase with status=COMPLETE when skipped
3. The synthetic PhaseResult includes the research_path in artifacts list
4. The synthetic PhaseResult includes metadata indicating phase was skipped: {'skipped': True, 'reason': 'research_path provided'}
5. Pipeline state is updated to mark RESEARCH phase as complete via state.set_phase_result()
6. DecompositionPhase receives the research_path and proceeds normally
7. Checkpoint is created for skipped research phase with phase name 'research-skipped'
8. Console output indicates research phase is being skipped with provided document path

#### REQ_000.4: Validate that the research document file exists before proce

Validate that the research document file exists before processing pipeline

##### Testable Behaviors

1. click.Path(exists=True) automatically validates file existence at CLI parsing time
2. Invalid paths produce error message: 'Error: Invalid value for --research-path: Path X does not exist'
3. Empty string paths are rejected with appropriate error
4. Paths to directories are rejected with error: 'Error: Invalid value for --research-path: Path X is a directory'
5. Symbolic links to valid files are accepted
6. Both absolute and relative paths are accepted (resolved to absolute internally)
7. File permissions are not checked at CLI level (handled by read operations later)
8. Path validation occurs before any pipeline initialization

#### REQ_000.5: Update argument validation to make --question optional when 

Update argument validation to make --question optional when --research-path is provided

##### Testable Behaviors

1. Command succeeds with --research-path alone (no --question required)
2. Command succeeds with --question alone (original behavior preserved)
3. Command succeeds with both --question and --research-path (research_path takes precedence)
4. Command fails without --question, --research-path, or --resume with error: '--question is required unless using --resume or --research-path'
5. Validation occurs after Click parses all arguments but before pipeline execution
6. Error message is clear and actionable for the user
7. Help text for --question is updated to reflect new optional conditions
8. When both --question and --research-path provided, log warning that question will be ignored


## Success Criteria

- [x] All tests pass
- [x] All behaviors implemented
- [ ] Code reviewed

## Implementation Notes

**Completed 2026-01-14**

### Changes Made:

1. **cli.py**:
   - Added `--research-path` option with `click.Path(exists=True, file_okay=True, dir_okay=False)`
   - Updated argument validation to allow `--research-path` as alternative to `--question`
   - Added warning when both `--question` and `--research-path` are provided
   - Updated console output to show research document path when skipping research phase
   - Passes `research_path` kwarg to `pipeline.run()`

2. **pipeline.py**:
   - Added logic in `run()` to detect `research_path` kwarg
   - Creates synthetic `PhaseResult` for RESEARCH phase with `status=COMPLETE`
   - Sets `metadata={'skipped': True, 'reason': 'research_path provided'}`
   - Creates checkpoint with `phase='research-skipped'`
   - Marks RESEARCH phase complete via `state.set_phase_result()`
   - Skips actual ResearchPhase execution when research_path provided

### Tests Added:

- `test_cli.py::TestResearchPathOption` - 9 tests covering all CLI behaviors
- `test_pipeline.py::TestResearchPathSkip` - 6 tests covering pipeline skipping behavior

All 316 tests pass.