# Phase 07: The system must support three Autonomy Modes: CHEC...

## Requirements

### REQ_006: The system must support three Autonomy Modes: CHECKPOINT, BA

The system must support three Autonomy Modes: CHECKPOINT, BATCH, and FULLY_AUTONOMOUS

#### REQ_006.1: CHECKPOINT mode pauses after each phase, allowing user revie

CHECKPOINT mode pauses after each phase, allowing user review and revision before proceeding to the next pipeline phase

##### Testable Behaviors

1. Pipeline execution pauses after EVERY phase (RESEARCH, DECOMPOSITION, TDD_PLANNING, MULTI_DOC, BEADS_SYNC, IMPLEMENTATION)
2. User is prompted with phase-specific action menu (continue/revise/restart/exit) after each phase completion
3. Phase artifacts are displayed to user before requesting action decision
4. User can provide feedback for revision if choosing 'revise' action
5. Checkpoint file is written to .rlm-act-checkpoints/ after each phase completes
6. Pipeline can resume from any checkpoint if user exits mid-pipeline
7. CHECKPOINT mode is the default mode when no mode is specified
8. Auto-approve flag is FALSE when autonomy_mode == AutonomyCheckpoint

#### REQ_006.2: BATCH mode groups related phases together and pauses only be

BATCH mode groups related phases together and pauses only between phase groups for streamlined execution

##### Testable Behaviors

1. Phases are organized into logical groups: Planning Group (RESEARCH, DECOMPOSITION, TDD_PLANNING), Document Group (MULTI_DOC, BEADS_SYNC), Execution Group (IMPLEMENTATION)
2. No pause occurs between phases within the same group
3. User is prompted only at group boundaries (after Planning, after Documents, after Implementation)
4. Group completion summary shows all artifacts produced by phases in that group
5. User can choose to restart from the beginning of the current group
6. Checkpoint is written at group boundaries, not at individual phase boundaries
7. BATCH mode uses auto_approve=true for intra-group phases, auto_approve=false at group boundaries

#### REQ_006.3: FULLY_AUTONOMOUS mode runs all phases without any user inter

FULLY_AUTONOMOUS mode runs all phases without any user interaction or pauses

##### Testable Behaviors

1. All 6 phases execute sequentially without any user prompts
2. No interactive input is requested at any point during execution
3. Auto-approve flag is TRUE for all phases when autonomy_mode == AutonomyFull
4. Pipeline halts only on phase failure (error condition)
5. Final summary is displayed only after all phases complete or pipeline fails
6. Checkpoint files are still written after each phase for crash recovery
7. Mode is suitable for CI/CD pipelines and unattended execution
8. Timeout handling is automatic without user intervention

#### REQ_006.4: Implement the AutonomyMode enum type in Go with three values

Implement the AutonomyMode enum type in Go with three values matching Python implementation

##### Testable Behaviors

1. AutonomyMode is defined as a custom int type with iota constants
2. Three constants defined: AutonomyCheckpoint (0), AutonomyBatch (1), AutonomyFull (2)
3. String() method returns lowercase string values matching Python: 'checkpoint', 'batch', 'fully_autonomous'
4. FromString() static function parses string to AutonomyMode with error handling for invalid values
5. JSON marshaling serializes to string value (not integer)
6. JSON unmarshaling parses from string value
7. AutonomyMode is added to PipelineConfig struct in pipeline.go
8. Default value is AutonomyCheckpoint when not specified
9. CLI parses --mode flag with values: checkpoint, batch, autonomous


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed