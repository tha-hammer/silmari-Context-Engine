# Phase 07: The system must implement CLI commands matching ex...

## Requirements

### REQ_006: The system must implement CLI commands matching existing Pyt

The system must implement CLI commands matching existing Python orchestrator and loop-runner interfaces

#### REQ_006.1: Implement --project/-p flag for project path to continue an 

Implement --project/-p flag for project path to continue an existing project session

##### Testable Behaviors

1. Flag accepts both --project and -p short form
2. Flag value is parsed as a file path string
3. Path is validated to exist on the filesystem
4. Path is validated to be a directory (not a file)
5. Path is converted to absolute path if relative path provided
6. Error message displayed if path does not exist
7. Error message displayed if path is not a valid project directory
8. Project directory must contain .context-engine/ state directory to be valid
9. Flag is mutually exclusive with --new flag
10. Help text clearly describes the flag purpose

#### REQ_006.2: Implement --new flag for creating a new project at the speci

Implement --new flag for creating a new project at the specified path

##### Testable Behaviors

1. Flag accepts --new with a path argument
2. Path is validated to not already exist OR be an empty directory
3. Parent directory of path must exist and be writable
4. Creates project directory if it does not exist
5. Initializes .context-engine/ state directory structure
6. Creates initial feature-list.json with empty features array
7. Creates initial session-log.json for tracking
8. Error message displayed if path already contains a project
9. Error message displayed if parent directory is not writable
10. Flag is mutually exclusive with --project/-p flag
11. Flag is mutually exclusive with --continue/-c flag
12. Help text clearly describes the flag purpose

#### REQ_006.3: Implement --model/-m flag defaulting to 'sonnet' for Claude 

Implement --model/-m flag defaulting to 'sonnet' for Claude model selection

##### Testable Behaviors

1. Flag accepts both --model and -m short form
2. Flag defaults to 'sonnet' when not specified
3. Accepts valid model values: sonnet, opus, haiku
4. Rejects invalid model names with clear error message
5. Model value is case-insensitive (Sonnet, SONNET, sonnet all valid)
6. Model value is passed to Claude CLI subprocess calls
7. Help text lists all valid model options
8. Help text indicates the default value

#### REQ_006.4: Implement --max-sessions flag with default of 100 to limit a

Implement --max-sessions flag with default of 100 to limit autonomous execution cycles

##### Testable Behaviors

1. Flag accepts --max-sessions with integer argument
2. Flag defaults to 100 when not specified
3. Accepts positive integer values only
4. Rejects zero or negative values with clear error message
5. Rejects non-integer values with clear error message
6. Maximum value capped at 10000 to prevent runaway execution
7. Value is used to limit loop iterations in orchestrator main loop
8. Help text describes the purpose and default value
9. Help text indicates valid range (1-10000)

#### REQ_006.5: Implement --continue/-c flag for continuing an existing proj

Implement --continue/-c flag for continuing an existing project from last checkpoint

##### Testable Behaviors

1. Flag accepts both --continue and -c short form
2. Flag is a boolean flag (no argument required)
3. When set, orchestrator resumes from last saved checkpoint
4. Requires --project/-p flag to be set (continue needs a project)
5. Error if project has no checkpoint state to continue from
6. Loads feature-list.json and resumes from first non-passing feature
7. Loads session-log.json and appends new session entries
8. Restores any in-progress phase state from checkpoint
9. Flag is mutually exclusive with --new flag
10. Help text clearly describes resume behavior


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed