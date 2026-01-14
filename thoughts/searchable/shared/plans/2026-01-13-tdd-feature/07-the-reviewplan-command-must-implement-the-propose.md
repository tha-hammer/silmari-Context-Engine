# Phase 07: The review_plan command must implement the propose...

## Requirements

### REQ_006: The review_plan command must implement the proposed loop arc

The review_plan command must implement the proposed loop architecture with outer phase iteration, middle review step iteration, and inner recursive requirement traversal

#### REQ_006.1: Implement outer loop iterating over phases sequentially usin

Implement outer loop iterating over phases sequentially using AllPhases(), checking dependency satisfaction before processing each phase and respecting autonomy mode settings for checkpointing

##### Testable Behaviors

1. Loop iterates through all 6 phases in correct order: Research → Decomposition → TDD_Planning → Multi_Doc → Beads_Sync → Implementation
2. areDependenciesMet(phase) is called before processing each phase and skips phases with unmet dependencies
3. Phase iteration uses AllPhases() method from models.go for consistent ordering
4. Loop tracks current phase index for checkpoint resume capability
5. When autonomyMode == AutonomyCheckpoint, saveCheckpoint() is called after each phase completes
6. When autonomyMode == AutonomyBatch, checkpoints occur only at group boundaries
7. When autonomyMode == AutonomyFullyAutonomous, no checkpoints interrupt execution
8. Phase transition follows valid state machine: pending → in_progress → complete/failed
9. Failed phases can be retried by transitioning from failed → in_progress
10. Loop terminates gracefully if any phase has critical blocking issues (❌ findings)
11. Phase results are accumulated and passed to next phase for dependency context

#### REQ_006.2: Implement middle loop iterating over 5 review steps (contrac

Implement middle loop iterating over 5 review steps (contracts, interfaces, promises, data_models, apis) for each phase, collecting findings with severity levels

##### Testable Behaviors

1. Loop iterates through exactly 5 review steps in order: contracts → interfaces → promises → data_models → apis
2. Each step executes runReviewStep(phase, step) and captures ReviewStepResult
3. Contract analysis checks: component boundaries, input/output contracts, error contracts, preconditions/postconditions/invariants
4. Interface analysis checks: public method definitions, naming conventions, extension points, visibility modifiers
5. Promise analysis checks: behavioral guarantees, async/concurrent operations, timeout/cancellation handling, resource cleanup
6. Data model analysis checks: field definitions with types, optional vs required, relationships (1:1, 1:N, N:M), migration compatibility
7. API analysis checks: endpoint definitions, request/response formats, error responses, versioning policies
8. Results categorized by severity: WellDefined (✅), Warnings (⚠️), Critical (❌)
9. Step results stored in results[phase][step] map structure
10. Claude invocation per step with specific prompt template for that analysis type
11. Step execution time tracked for performance metrics
12. Failed step does not block subsequent steps within same phase (collect all findings)

#### REQ_006.3: Implement inner recursive loop for requirement tree traversa

Implement inner recursive loop for requirement tree traversal using reviewRequirements(node, step) pattern, handling 3-tier hierarchy (parent → sub_process → implementation)

##### Testable Behaviors

1. Function signature: reviewRequirements(node *RequirementNode, step ReviewStep) []ReviewFinding
2. Base case: reviewNode(node, step) returns findings for current node
3. Recursive case: iterates over node.Children and recursively calls reviewRequirements
4. Findings from all recursive calls are aggregated into single slice
5. Handles 3-tier hierarchy: parent (REQ_000) → sub_process (REQ_000.1) → implementation (REQ_000.1.1)
6. Node type (parent/sub_process/implementation) influences which review criteria apply
7. AcceptanceCriteria field on each node is validated against review step requirements
8. TestableProperties field validated for completeness and specificity
9. Implementation.Components validated when present on implementation-level nodes
10. Circular dependency detection to prevent infinite loops in malformed trees
11. Maximum recursion depth limit (configurable, default 10) to prevent stack overflow
12. Empty Children slice terminates recursion at leaf nodes
13. Findings include node.ID for traceability back to specific requirement

#### REQ_006.4: Collect results in map structure indexed by phase and step, 

Collect results in map structure indexed by phase and step, supporting aggregation, filtering, and report generation

##### Testable Behaviors

1. Results stored in map[PhaseType]map[ReviewStep]*ReviewStepResult structure
2. Thread-safe map operations if parallel step execution is enabled
3. Aggregation functions: countBySeverity(results) returns map[SeverityLevel]int
4. Filter functions: filterBySeverity(results, severity) returns filtered results
5. Filter functions: filterByPhase(results, phase) returns phase-specific results
6. Filter functions: filterByStep(results, step) returns step-specific results
7. Overall summary calculation: hasBlockingIssues(results) returns true if any Critical findings
8. Results serializable to JSON for checkpoint persistence
9. Results exportable to REVIEW.md markdown format matching existing report structure
10. Results include metadata: timestamp, plan path, git commit, reviewer
11. Empty results map initialized before iteration begins
12. Results accessible during iteration for cross-phase dependency analysis

#### REQ_006.5: Implement loop termination with iteration limit and closure 

Implement loop termination with iteration limit and closure check pattern, handling blocking dependencies and critical findings

##### Testable Behaviors

1. Maximum iteration limit configurable (default from existing IMPL_TIMEOUT pattern)
2. Iteration counter tracked: result.Iterations = i + 1 for each loop cycle
3. Closure check: allClosed, closedIssues := checkAllIssuesClosed(projectPath, beadsIssueIDs)
4. Early termination if hasBlockingIssues(results) returns true and stopOnCritical flag set
5. Continue execution with warnings logged if critical findings exist but stopOnCritical is false
6. Blocking dependency detection: for each issue check if depends_on_id is in open_ids set
7. Blocked count tracked: blocked++ when dependency found in open issues
8. Success flag set only when: all steps complete AND no critical findings AND tests pass (if applicable)
9. Retry mechanism: failed phases can retry up to maxRetries before marking final failure
10. Timeout per overall review configurable, triggers graceful termination with partial results
11. Final result includes: iterations completed, phases reviewed, steps executed, findings summary
12. Termination reason logged: 'max_iterations', 'all_complete', 'critical_blocking', 'timeout', 'user_cancelled'


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed