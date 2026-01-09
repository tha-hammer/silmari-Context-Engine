# Phase 02: The system must replace Python CLI framework patte...

## Requirements

### REQ_001: The system must replace Python CLI framework patterns with G

The system must replace Python CLI framework patterns with Go equivalents, converting argparse-based CLI tools to cobra-based commands with identical functionality

#### REQ_001.1: Port orchestrator.py CLI arguments including --project, --ne

Port orchestrator.py CLI arguments including --project, --new, --model, --max-sessions, --continue, --status, --mcp-preset, --with-qa, and --debug flags to cobra command structure

##### Testable Behaviors

1. Implement --project/-p flag accepting filesystem path to continue existing project
2. Implement --new flag accepting filesystem path for creating new project
3. Implement --model/-m flag with default value 'sonnet' and valid choices (sonnet/opus)
4. Implement --max-sessions flag with int type and default value 100
5. Implement --continue/-c boolean flag for continuing existing project
6. Implement --status/-s boolean flag to show status and exit
7. Implement --mcp-preset flag with valid choices (rust/python/node/docs)
8. Implement --with-qa boolean flag for generating E2E QA features
9. Implement --debug/-d boolean flag for debug output
10. All flags must produce identical help text to Python argparse version
11. Mutually exclusive flag combinations (--project vs --new) must be validated
12. Path flags must validate that paths exist when required
13. Unit tests verify all flag combinations work correctly
14. Help output matches format: 'context-engine [flags]' with description 'Context-Engineered Agent Orchestrator'

#### REQ_001.2: Port loop-runner.py CLI arguments to cobra command structure

Port loop-runner.py CLI arguments to cobra command structure maintaining feature list processing, dependency resolution, and session management functionality

##### Testable Behaviors

1. Implement --features/-f flag accepting path to features.json file
2. Implement --project/-p flag accepting filesystem path to project directory
3. Implement --model/-m flag with default value 'sonnet' and valid choices
4. Implement --max-iterations flag with int type for maximum loop iterations
5. Implement --timeout flag with duration type for session timeout
6. Implement --parallel/-P flag with int type for parallel execution count
7. Implement --dry-run boolean flag for validation without execution
8. Implement --resume boolean flag to resume from last checkpoint
9. Implement --verbose/-v boolean flag for verbose output
10. Help text describes loop-runner as 'Autonomous loop runner that continuously runs Claude Code sessions'
11. Features.json path must be validated for existence and valid JSON schema
12. Unit tests verify feature list loading and validation
13. Integration tests verify topological sort of feature dependencies works correctly

#### REQ_001.3: Implement flag validation and help text matching current Pyt

Implement flag validation and help text matching current Python behavior with consistent error messages and usage patterns

##### Testable Behaviors

1. All required flags produce 'required flag not set' error with flag name
2. Invalid enum values produce 'invalid value for --flag: must be one of [choices]' error
3. Invalid path values produce 'path does not exist: <path>' error
4. Invalid integer values produce 'invalid integer value for --flag' error
5. Help text (-h/--help) displays formatted usage with all flags and descriptions
6. Version flag (--version) displays binary version from build-time injection
7. Error messages match Python argparse style for user familiarity
8. Custom usage template matches Python argparse output format
9. All validation errors are wrapped with context using fmt.Errorf or errors package
10. Unit tests cover all validation error paths
11. Validation functions are reusable across all CLI commands

#### REQ_001.4: Support short and long flag forms (e.g., -p and --project) w

Support short and long flag forms (e.g., -p and --project) with cobra pflag integration ensuring all flag aliases work correctly

##### Testable Behaviors

1. -p is alias for --project in orchestrator command
2. -m is alias for --model in both orchestrator and loop-runner
3. -c is alias for --continue in orchestrator command
4. -s is alias for --status in orchestrator command
5. -d is alias for --debug in orchestrator command
6. -f is alias for --features in loop-runner command
7. -P is alias for --parallel in loop-runner command
8. -v is alias for --verbose in loop-runner command
9. Both short and long forms appear in help text
10. Short flags can be combined (e.g., -cd for --continue --debug)
11. Unit tests verify short and long flag equivalence
12. Help text format shows '-p, --project string' style

#### REQ_001.5: Implement subcommands for planning_orchestrator, mcp-setup, 

Implement subcommands for planning_orchestrator, mcp-setup, resume_planning, and resume_pipeline entry points as cobra subcommands under a unified CLI

##### Testable Behaviors

1. Main binary 'context-engine' supports subcommands: plan, mcp-setup, resume
2. 'context-engine plan' maps to planning_orchestrator.py functionality (596 lines)
3. 'context-engine mcp-setup' maps to mcp-setup.py functionality (634 lines)
4. 'context-engine resume planning' maps to resume_planning.py (23 lines)
5. 'context-engine resume pipeline' maps to resume_pipeline.py (175 lines)
6. Each subcommand has own flags inheriting from parent where appropriate
7. Global flags (--debug, --verbose) available to all subcommands
8. Help text for 'context-engine --help' lists all available subcommands
9. Help text for 'context-engine plan --help' shows plan-specific flags
10. Subcommand aliases supported (e.g., 'context-engine p' for 'context-engine plan')
11. Unknown subcommand produces helpful error with suggestions
12. Tab completion support for subcommands in bash/zsh


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed