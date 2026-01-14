# Phase 17: The PipelineConfig must be extended to support Aut...

## Requirements

### REQ_017: The PipelineConfig must be extended to support AutonomyMode 

The PipelineConfig must be extended to support AutonomyMode and MaxIterations

#### REQ_017.1: Add AutonomyMode field to PipelineConfig struct to support t

Add AutonomyMode field to PipelineConfig struct to support three autonomy modes (checkpoint, batch, fully_autonomous) instead of the current binary AutoApprove flag

##### Testable Behaviors

1. AutonomyMode type is defined as an integer enum with three values: AutonomyCheckpoint (0), AutonomyBatch (1), AutonomyFull (2)
2. AutonomyMode has a String() method returning 'checkpoint', 'batch', or 'fully_autonomous'
3. PipelineConfig struct includes AutonomyMode field of type AutonomyMode
4. Default value of AutonomyMode is AutonomyCheckpoint (pause after each phase)
5. AutonomyCheckpoint mode pauses pipeline after each phase for user review
6. AutonomyBatch mode pauses pipeline between phase groups (research+decomposition, planning+phase_decomposition, beads+implementation)
7. AutonomyFull mode runs all phases without pauses
8. Existing AutoApprove bool field is preserved for backward compatibility but deprecated
9. Pipeline Run() method respects AutonomyMode for determining when to pause
10. Unit tests verify all three autonomy modes behave correctly

#### REQ_017.2: Add MaxIterations field to PipelineConfig struct to control 

Add MaxIterations field to PipelineConfig struct to control the maximum number of implementation loop iterations before timeout

##### Testable Behaviors

1. PipelineConfig struct includes MaxIterations field of type int
2. Default value of MaxIterations is 100 (matching Python IMPL_MAX_ITERATIONS constant)
3. MaxIterations value of 0 is treated as 'use default' (100 iterations)
4. MaxIterations is passed to StepImplementation() function when implementation phase is invoked
5. Implementation loop terminates after MaxIterations if all beads issues are not closed
6. ImplementationResult includes actual iteration count when loop completes
7. CLI accepts --max-iterations flag to override default value
8. Validation ensures MaxIterations is non-negative (negative values return error)
9. MaxIterations is persisted in checkpoint state for resume capability
10. Unit tests verify iteration limit is respected and loop terminates correctly

#### REQ_017.3: Ensure existing ProjectPath, AutoApprove, and TicketID field

Ensure existing ProjectPath, AutoApprove, and TicketID fields remain functional and backward compatible while integrating new fields

##### Testable Behaviors

1. ProjectPath string field remains unchanged and required
2. AutoApprove bool field is preserved with deprecation notice in godoc comment
3. TicketID string field remains unchanged and optional
4. AutoApprove=true maps to AutonomyMode=AutonomyFull when AutonomyMode is not explicitly set
5. AutoApprove=false maps to AutonomyMode=AutonomyCheckpoint when AutonomyMode is not explicitly set
6. Explicit AutonomyMode setting takes precedence over AutoApprove
7. All existing callers of NewPlanningPipeline() continue to work without modification
8. CLI --auto-approve flag continues to work but sets AutonomyMode=AutonomyFull
9. Warning log emitted when AutoApprove is used instead of AutonomyMode
10. Existing test cases pass without modification


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed