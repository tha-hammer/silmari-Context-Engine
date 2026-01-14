# Phase 06: The system must support three autonomy modes for r...

## Requirements

### REQ_005: The system must support three autonomy modes for review exec

The system must support three autonomy modes for review execution: Checkpoint, Batch, and Fully Autonomous

#### REQ_005.1: Implement Checkpoint Mode to review each phase individually,

Implement Checkpoint Mode to review each phase individually, execute all 5 review steps (contracts, interfaces, promises, data models, APIs) for each phase, persist state after completion, and pause for user approval before proceeding to the next phase

##### Testable Behaviors

1. Each of the 6 phases (Research, Decomposition, TDDPlanning, MultiDoc, BeadsSync, Implementation) must be reviewed individually before pausing
2. All 5 review steps (contracts, interfaces, promises, data_models, apis) must execute sequentially for each phase before checkpoint
3. Phase dependencies must be validated using areDependenciesMet(phase) before starting review of any phase
4. Checkpoint must be saved with phase identifier, all ReviewStepResult data, and timestamp after each phase completes
5. System must block execution and wait for explicit user approval signal before proceeding to next phase
6. User must be able to view review findings (WellDefined ✅, Warnings ⚠️, Critical ❌) at each checkpoint pause
7. Critical findings (❌) in a phase must be flagged and require explicit acknowledgment to proceed
8. Resume capability must restore exact checkpoint state including phase index and accumulated results
9. Checkpoint JSON file must follow existing checkpoint.go structure with phase-specific review data in Data map

#### REQ_005.2: Implement Batch Mode to group related phases together, execu

Implement Batch Mode to group related phases together, execute all reviews within each group without pausing, and pause only at defined group boundaries for consolidated approval

##### Testable Behaviors

1. Phases must be grouped into logical batches: Group 1 (Research, Decomposition), Group 2 (TDDPlanning, MultiDoc), Group 3 (BeadsSync, Implementation)
2. All phases within a batch must complete their full review (all 5 steps each) before checkpoint pause
3. Batch boundary checkpoint must aggregate all ReviewStepResult data from all phases in the batch
4. User must receive consolidated report showing findings across all phases in the completed batch
5. Critical findings in any phase within a batch must be surfaced in the consolidated batch report
6. System must not pause between phases within the same batch
7. Resume from batch checkpoint must restart from the beginning of the current batch, not mid-batch
8. Batch grouping configuration must be customizable via --batch-groups flag or config file

#### REQ_005.3: Implement Fully Autonomous Mode to execute the complete revi

Implement Fully Autonomous Mode to execute the complete review pipeline across all phases and all review steps without any user intervention, producing a final comprehensive report upon completion

##### Testable Behaviors

1. All 6 phases must be reviewed sequentially without any pause for user input
2. All 5 review steps must execute for each phase (30 total review operations)
3. Phase dependencies must still be validated but failures should be logged and continued, not blocked
4. Final comprehensive report must include all findings from all phases and steps
5. Total execution time must be tracked and reported
6. Any critical findings (❌) must be prominently highlighted in final report but not block execution
7. Exit code must reflect overall review health: 0 for all pass, 1 for warnings only, 2 for critical issues
8. Report must be written to specified --output path in REVIEW.md format matching existing examples
9. Execution must be suitable for CI/CD pipeline integration with machine-readable output option

#### REQ_005.4: Implement the saveCheckpoint() function specifically for rev

Implement the saveCheckpoint() function specifically for review operations to persist review state after phase completion in checkpoint mode, enabling resume capability with full context restoration

##### Testable Behaviors

1. Checkpoint must be saved as JSON file to .context-engine/checkpoints/review-{plan-name}-{timestamp}.json
2. Checkpoint must include: current phase index, autonomy mode, all completed phase results, pending phases list
3. Each ReviewStepResult must be fully serialized including WellDefined, Warnings, Critical arrays
4. Checkpoint must include original plan path and plan hash to detect if plan changed since checkpoint
5. Atomic write pattern must be used: write to temp file, then rename to prevent corruption
6. Checkpoint file must be human-readable for debugging (pretty-printed JSON with indentation)
7. loadCheckpoint() must validate plan hash matches before allowing resume
8. Checkpoint must store timestamp of last save and cumulative review duration
9. Old checkpoints must be rotated: keep last 5, delete older ones automatically


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed