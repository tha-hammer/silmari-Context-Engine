# Phase 06: The system must support Interactive Checkpoints wi...

## Requirements

### REQ_005: The system must support Interactive Checkpoints with user pr

The system must support Interactive Checkpoints with user prompts and input collection

#### REQ_005.1: Implement phase action prompts for research, decomposition, 

Implement phase action prompts for research, decomposition, and TDD planning phases with menu-driven user interaction in Go

##### Testable Behaviors

1. prompt_research_action() equivalent displays menu with Continue, Revise, Start over, Exit options
2. prompt_decomposition_action() equivalent displays menu with Continue, Revise, Start over, Exit options
3. prompt_tdd_planning_action() equivalent displays menu with Continue, Revise, Start over, Exit options
4. All prompt functions accept single-key input (c/r/s/e) case-insensitive
5. Empty input defaults to 'continue' action
6. Invalid input displays error message and re-prompts without exiting
7. Each function returns a PhaseAction enum or string: 'continue', 'revise', 'restart', 'exit'
8. Menu text matches phase context (e.g., 'Continue to decomposition' vs 'Continue to multi-doc generation')
9. prompt_phase_continue() displays completed phase name, artifacts list, and prompts Y/n to continue
10. When user answers 'n' to continue, prompts for multiline feedback and returns {continue: false, feedback: string}
11. prompt_use_checkpoint() displays timestamp, phase name, artifact list and prompts Y/n to resume
12. All prompts integrate with PipelineConfig.AutonomyMode to skip prompts when fully autonomous

#### REQ_005.2: Implement multiline input collection that reads lines until 

Implement multiline input collection that reads lines until an empty line is entered, with optional prompt prefix

##### Testable Behaviors

1. CollectMultilineInput(prompt string) string function reads from stdin using bufio.Scanner
2. Optional prompt string is displayed before each input line
3. Reading continues until user enters an empty line (just presses Enter)
4. All non-empty lines are joined with newline characters
5. Function returns the complete multiline string
6. Handles EOF gracefully without panic
7. Works correctly with terminal input including special characters
8. Empty first line returns empty string immediately
9. Leading/trailing whitespace on each line is preserved (not trimmed)
10. Integration with PromptPhaseContinue for feedback collection when user declines to continue

#### REQ_005.3: Implement interactive file selection menu that displays numb

Implement interactive file selection menu that displays numbered file list with search, custom path, and exit options

##### Testable Behaviors

1. PromptFileSelection(files []string, fileType string) (action string, selectedPath string) function signature
2. Displays header with fileType in uppercase (e.g., 'SELECT RESEARCH FILE')
3. Lists discovered files with 1-indexed numbers: [1] filename1.md, [2] filename2.md
4. Shows 'No {fileType} files found.' when files slice is empty
5. Displays menu options: [S] Search again, [O] Other (specify path), [E] Exit
6. Numeric input selects corresponding file and returns ('selected', filepath)
7. Input 's' or 'S' returns ('search', '') to trigger re-search with more days
8. Input 'o' or 'O' returns ('other', '') to trigger custom path prompt
9. Input 'e' or 'E' returns ('exit', '') to abort selection
10. Invalid number outside range displays 'Invalid number. Enter 1-N'
11. Invalid non-numeric input displays 'Invalid choice. Enter a number, S, O, or E.'
12. Empty file list with numeric input displays 'No files available to select.'
13. prompt_search_days(default int) int prompts 'Search how many days back? [N]:' and validates positive integer
14. prompt_custom_path(fileType string) (string, error) prompts for path and validates existence

#### REQ_005.4: Implement autonomy mode selection prompt that displays imple

Implement autonomy mode selection prompt that displays implementation readiness info and offers CHECKPOINT, BATCH, or FULLY_AUTONOMOUS modes

##### Testable Behaviors

1. PromptAutonomyMode(phaseCount int, epicID string) AutonomyMode function signature
2. Displays 60-character separator line with 'IMPLEMENTATION READY' header
3. Shows 'Plan phases: N' with phaseCount value
4. Shows 'Beads epic: {epicID}' with epic identifier
5. Displays mode options with descriptions: [C]heckpoint - pause at each phase for review (recommended), [F]ully autonomous - run all phases without stopping, [B]atch - run groups of phases, pause between groups
6. Input 'c' or 'C' or empty returns AutonomyCheckpoint (default)
7. Input 'f' or 'F' returns AutonomyFullyAutonomous
8. Input 'b' or 'B' returns AutonomyBatch
9. Invalid input displays 'Invalid choice: '{input}'. Please enter C, F, or B.' and re-prompts
10. AutonomyMode type defined as iota-based int with String() method returning 'checkpoint', 'fully_autonomous', 'batch'
11. Integration with PipelineConfig to set AutonomyMode field before implementation phase


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed