# Phase 06: The CLI argument validation must follow establishe...

## Requirements

### REQ_005: The CLI argument validation must follow established Click fr

The CLI argument validation must follow established Click framework patterns for file path validation and mutual exclusivity

#### REQ_005.1: Implement 'required unless' pattern for --question argument 

Implement 'required unless' pattern for --question argument that makes it required unless --research-path or --resume flags are provided

##### Testable Behaviors

1. --question is required when neither --research-path nor --resume is provided
2. CLI exits with error code and descriptive message when --question is missing and no alternative is provided
3. Error message clearly states: 'Error: --question is required unless --research-path or --resume is provided'
4. --question becomes optional when --research-path is provided
5. --question becomes optional when --resume flag is set
6. --question can still be provided alongside --research-path or --resume without error
7. Validation occurs in callback function before command execution
8. Unit tests cover all permutations: question-only, research-path-only, resume-only, question+research-path, none-provided

#### REQ_005.2: Implement click.Path validation for --research-path argument

Implement click.Path validation for --research-path argument ensuring file exists and is a valid file (not directory)

##### Testable Behaviors

1. --research-path uses click.Path(exists=True, file_okay=True, dir_okay=False) type specification
2. CLI exits with error when provided path does not exist
3. CLI exits with error when provided path is a directory instead of file
4. Error message from Click clearly indicates 'Path does not exist' for missing files
5. Error message from Click clearly indicates 'is a directory' for directory paths
6. Argument accepts both absolute and relative paths
7. Path is resolved to absolute path before passing to pipeline
8. Default value is None when argument not provided
9. Help text states: 'Path to existing research document (skips research phase)'

#### REQ_005.3: Support default values for optional arguments following esta

Support default values for optional arguments following established patterns in existing CLI options

##### Testable Behaviors

1. --research-path defaults to None when not provided (not empty string)
2. --plan-path defaults to None when not provided (not empty string)
3. Existing --project default='.' pattern is preserved
4. Existing --plan-name default='feature' pattern is preserved
5. None default allows truthiness check in run() function: 'if research_path:'
6. Type annotations match default values: Optional[str] for None defaults, str for string defaults
7. Help text for each option documents default behavior where applicable
8. Default values are documented in CLI --help output

#### REQ_005.4: Follow existing flag argument patterns using is_flag=True fo

Follow existing flag argument patterns using is_flag=True for boolean options consistent with --autonomous and --resume flags

##### Testable Behaviors

1. Any new boolean options use is_flag=True pattern
2. Flag options default to False when not provided
3. Flag options become True when flag is present on command line
4. Flag naming follows existing convention: --flag-name with hyphen separator
5. Short form aliases follow existing pattern: -a for --autonomous, -r for --resume
6. Function signature uses bool type annotation for flag parameters
7. Flags do not require values: 'silmari run -a' not 'silmari run -a=True'
8. Help text uses imperative verb form: 'Enable autonomous mode' not 'Autonomous mode flag'


## Success Criteria

- [x] All tests pass (60 CLI tests, 423 total tests)
- [x] All behaviors implemented
- [x] Code reviewed

## Completion Notes

Phase 6 REQ_005 completed: CLI argument validation patterns fully tested.

All testable behaviors verified through comprehensive test coverage:
- REQ_005.1: 7 tests for 'required unless' pattern
- REQ_005.2: 7 tests for click.Path validation
- REQ_005.3: 6 tests for default values
- REQ_005.4: 8 tests for flag patterns

Implementation was already complete in cli.py; this phase added exhaustive test coverage.