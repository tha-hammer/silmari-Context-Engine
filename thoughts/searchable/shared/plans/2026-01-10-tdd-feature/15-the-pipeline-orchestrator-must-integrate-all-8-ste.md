# Phase 15: The Pipeline Orchestrator must integrate all 8 ste...

## Requirements

### REQ_014: The Pipeline Orchestrator must integrate all 8 steps includi

The Pipeline Orchestrator must integrate all 8 steps including the new Implementation phase

#### REQ_014.1: Execute existing pipeline steps 1-7 (Research, Memory Sync, 

Execute existing pipeline steps 1-7 (Research, Memory Sync, Requirement Decomposition, Context Generation, Planning, Phase Decomposition, Beads Integration)

##### Testable Behaviors

1. All 7 existing steps execute in sequence: Research → Memory Sync → Requirement Decomposition → Context Generation → Planning → Phase Decomposition → Beads Integration
2. Each step result is stored in results.Steps map with appropriate key names
3. Pipeline returns early with results.Success=false and results.FailedAt set if any critical step fails
4. Non-critical steps (memory_sync, context_generation) continue on failure without blocking pipeline
5. Step execution timing is captured in results.Started and results.Completed
6. Pipeline correctly passes outputs between steps (research.ResearchPath → decomposition, planning.PlanPath → phase_decomposition, etc.)
7. BeadsIntegrationResult contains EpicID and PhaseIssues array for handoff to implementation phase

#### REQ_014.2: Add Step 8: Implementation Phase - autonomous TDD loop that 

Add Step 8: Implementation Phase - autonomous TDD loop that invokes Claude, checks beads issue status, and runs tests until complete

##### Testable Behaviors

1. New StepImplementation() function is created in go/internal/planning/implementation.go
2. Function accepts: projectPath string, phasePaths []string, beadsIssueIDs []string, beadsEpicID string, maxIterations int
3. Loop iterates up to maxIterations (default 100) times
4. Each iteration: (1) invokes Claude with implementation prompt, (2) sleeps IMPL_LOOP_SLEEP (10s), (3) checks if all beads issues are closed
5. When all issues closed: runs tests using runTests(), breaks loop if tests pass, continues if tests fail
6. Returns ImplementationResult struct with Success, Error, Iterations, TestsPassed, PhasesClosed fields
7. Implementation prompt includes TDD plan path, beads epic ID, phase issue IDs, and implementation instructions
8. Claude invocation uses RunClaudeSync() with IMPL_TIMEOUT (3600s) and streaming enabled

#### REQ_014.3: Call StepImplementation with project path, phase paths, issu

Call StepImplementation with project path, phase paths, issue IDs, epic ID, max iterations and integrate into main pipeline flow

##### Testable Behaviors

1. Pipeline Run() method updated to include Step 8 after Step 7 (Beads Integration)
2. Step 8 header printed: 'STEP 8/8: IMPLEMENTATION PHASE'
3. Phase paths extracted from decomposition.PhaseFiles
4. Issue IDs extracted from beads.PhaseIssues array using helper function getIssueIDsFromBeads()
5. Epic ID extracted from beads.EpicID
6. MaxIterations taken from pipeline config or defaults to IMPL_MAX_ITERATIONS
7. StepImplementation() called with all extracted parameters

#### REQ_014.4: Store implementation result in results.Steps map with proper

Store implementation result in results.Steps map with proper success/failure handling

##### Testable Behaviors

1. Implementation result stored in results.Steps['implementation']
2. If implementation fails (impl.Success=false), pipeline sets results.Success=false
3. If implementation fails, results.FailedAt set to 'implementation'
4. If implementation fails, results.Error set to impl.Error message
5. On failure, pipeline returns immediately with current results
6. On success, pipeline continues to completion logic

#### REQ_014.5: Handle implementation failure with proper error reporting in

Handle implementation failure with proper error reporting including iteration count, test output, and phase status

##### Testable Behaviors

1. On max iterations reached, error message includes iteration count: 'Max iterations (N) reached'
2. On test failure after issues closed, error includes truncated test output (first 500 chars)
3. Implementation result includes iterations count for debugging
4. Implementation result includes TestsPassed boolean flag
5. Implementation result includes PhasesClosed array showing which phases completed
6. Pipeline logs clear error message to stdout before returning
7. Error message includes suggestion to check beads status: 'Run bd ready to see remaining work'

#### REQ_014.6: Port Context Window Array integration from Python to Go for 

Port Context Window Array integration from Python to Go for managing context entries throughout pipeline phases

##### Testable Behaviors

1. Create go/internal/context/ package with CWA implementation
2. CentralContextStore implemented with in-memory entry storage and TF-IDF search
3. ContextEntry struct matches Python: id, entry_type, source, content, summary, ttl fields
4. EntryType enum includes: FILE, TASK, COMMAND types
5. WorkingLLMContext builds summaries-only context for orchestrator
6. ImplementationLLMContext builds full-content context with entry limits
7. TaskBatcher creates batches respecting max_entries_per_batch limit
8. Store supports search(), add(), get(), remove(), compress_multiple() operations
9. TTL management: process_turn() decrements TTL and removes expired entries
10. Integration with StepImplementation for context-aware prompts


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed