# Phase 03: The system must handle sequential phase dependenci...

## Requirements

### REQ_002: The system must handle sequential phase dependencies where e

The system must handle sequential phase dependencies where each phase (Research → Decomposition → TDD_Planning → Multi_Doc → Beads_Sync → Implementation) depends on the previous phase completing successfully

#### REQ_002.1: Implement phase iteration using AllPhases() enumeration retu

Implement phase iteration using AllPhases() enumeration returning all PhaseType values in sequential order from Research to Implementation

##### Testable Behaviors

1. AllPhases() returns a slice of all 6 PhaseType values in exact order: PhaseResearch, PhaseDecomposition, PhaseTDDPlanning, PhaseMultiDoc, PhaseBeadsSync, PhaseImplementation
2. PhaseIterator exposes a ForEach(callback func(PhaseType) error) method that iterates through phases in order and stops on first error
3. PhaseIterator exposes a GetPhaseAtIndex(index int) (PhaseType, error) method that returns the phase at a given index or error if out of bounds
4. PhaseIterator exposes a GetPhaseCount() int method that returns 6 (total number of phases)
5. Phase iteration maintains consistent ordering across multiple calls (idempotent)
6. PhaseIterator can be reset to start iteration from the beginning
7. Unit tests verify iteration order matches the defined sequence exactly
8. Integration test confirms all 6 phases are visited exactly once during full pipeline execution

#### REQ_002.2: Implement dependency checking that verifies all prerequisite

Implement dependency checking that verifies all prerequisite phases have completed successfully before allowing a phase to be processed

##### Testable Behaviors

1. AreDependenciesMet(phase PhaseType) returns true only if ALL phases preceding the target phase have StatusComplete
2. AreDependenciesMet(PhaseResearch) always returns true since Research has no dependencies
3. AreDependenciesMet(PhaseDecomposition) returns true only if PhaseResearch has StatusComplete
4. AreDependenciesMet returns false if any preceding phase has StatusPending, StatusInProgress, or StatusFailed
5. Function provides detailed error information indicating which specific phase(s) are blocking
6. GetBlockingPhases(phase PhaseType) returns a slice of PhaseType values that are not yet complete
7. Method handles nil or uninitialized PhaseResults map gracefully (treats as all pending)
8. Unit tests verify correct dependency check for each of the 6 phases
9. Unit tests verify false is returned when any upstream phase has failed status
10. Edge case: calling AreDependenciesMet on a phase with StatusComplete or StatusFailed still checks dependencies correctly

#### REQ_002.3: Support Next() and Previous() navigation methods for bidirec

Support Next() and Previous() navigation methods for bidirectional phase traversal with proper boundary handling

##### Testable Behaviors

1. Next() returns the subsequent phase for all phases except PhaseImplementation
2. Next() on PhaseImplementation returns error 'implementation is the final phase'
3. Previous() returns the preceding phase for all phases except PhaseResearch
4. Previous() on PhaseResearch returns error 'research is the first phase'
5. Navigation chain is consistent: phase.Next().Previous() equals original phase (where applicable)
6. IsFirstPhase() method returns true only for PhaseResearch
7. IsLastPhase() method returns true only for PhaseImplementation
8. HasNext() method returns false only for PhaseImplementation
9. HasPrevious() method returns false only for PhaseResearch
10. GetDistanceFromStart() returns 0 for PhaseResearch, 5 for PhaseImplementation
11. GetDistanceToEnd() returns 5 for PhaseResearch, 0 for PhaseImplementation
12. Unit tests verify all phase transitions for both Next() and Previous()
13. Unit tests verify error messages match expected text exactly

#### REQ_002.4: Implement PhaseStatus state machine with valid transitions e

Implement PhaseStatus state machine with valid transitions enforcing proper lifecycle: pending→in_progress→complete/failed with retry support from failed state

##### Testable Behaviors

1. CanTransitionTo() returns true for pending→in_progress transition
2. CanTransitionTo() returns true for in_progress→complete transition
3. CanTransitionTo() returns true for in_progress→failed transition
4. CanTransitionTo() returns true for failed→in_progress transition (retry)
5. CanTransitionTo() returns false for complete→any transition (terminal state)
6. CanTransitionTo() returns false for pending→complete (must go through in_progress)
7. CanTransitionTo() returns false for pending→failed (must go through in_progress)
8. TransitionTo() method performs transition and returns error if invalid
9. IsTerminal() returns true for StatusComplete and StatusFailed
10. IsPending() returns true only for StatusPending
11. IsActive() returns true only for StatusInProgress
12. GetValidTransitions() returns slice of valid next states for current state
13. State transition events are logged for debugging/audit
14. Unit tests cover all valid transitions returning true
15. Unit tests cover all invalid transitions returning false
16. Integration test verifies phase cannot be marked complete without going through in_progress


## Success Criteria

- [x] All tests pass
- [x] All behaviors implemented
- [ ] Code reviewed

## Implementation Summary

**Completed on 2026-01-13**

### Files Modified
- `go/internal/planning/models.go`: Added PhaseIterator, PhaseDependencyChecker, and additional navigation/status methods
- `go/internal/planning/models_test.go`: Added comprehensive tests for all new functionality

### Implementation Details

#### REQ_002.1: PhaseIterator
- `NewPhaseIterator()` creates an iterator over all phases
- `ForEach(callback)` iterates with error stopping
- `GetPhaseAtIndex(index)` returns phase at index with bounds checking
- `GetPhaseCount()` returns 6
- `Reset()` resets iterator to beginning
- `Current()`, `Next()`, `HasMore()` for manual iteration

#### REQ_002.2: Dependency Checking
- `NewPhaseDependencyChecker(results)` creates a checker
- `AreDependenciesMet(phase)` returns true if all preceding phases complete
- `GetBlockingPhases(phase)` returns slice of blocking phases
- `GetBlockingPhasesDetailed(phase)` returns detailed status info

#### REQ_002.3: Navigation Methods
- `IsFirstPhase()`, `IsLastPhase()` for boundary detection
- `HasNext()`, `HasPrevious()` for navigation availability
- `GetDistanceFromStart()`, `GetDistanceToEnd()` for position info

#### REQ_002.4: PhaseStatus State Machine
- `IsPending()`, `IsActive()` for status checking
- `GetValidTransitions()` returns valid next states
- `TransitionTo(next)` attempts transition with error on invalid

### Test Coverage
- 40+ tests covering all new functionality
- All tests passing