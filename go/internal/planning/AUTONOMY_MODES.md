# Autonomy Modes Implementation

## Overview

This implementation adds support for three autonomy modes to the planning pipeline, controlling how the system handles checkpoints and user interaction during pipeline execution.

## Autonomy Modes

### 1. CHECKPOINT Mode (Default)

**Behavior:**
- Pauses after EVERY phase for user review
- Auto-approve is always FALSE
- Checkpoint written after each phase
- User prompted with phase-specific action menu
- Phase artifacts displayed before action decision
- User can provide feedback for revision
- Can resume from any checkpoint

**Use Case:** Interactive development with full control and visibility at each step.

**Example:**
```go
config := PipelineConfig{
    ProjectPath:  "/path/to/project",
    AutonomyMode: AutonomyCheckpoint, // or omit (default)
}
```

### 2. BATCH Mode

**Behavior:**
- Phases organized into logical groups:
  - **Planning Group**: RESEARCH, DECOMPOSITION, TDD_PLANNING
  - **Document Group**: MULTI_DOC, BEADS_SYNC
  - **Execution Group**: IMPLEMENTATION
- No pause between phases within the same group
- Auto-approve TRUE within groups, FALSE at boundaries
- User prompted only at group boundaries
- Group completion summary shows all artifacts
- Checkpoint written at group boundaries only
- User can restart from beginning of current group

**Use Case:** Streamlined execution with checkpoints at logical milestones.

**Example:**
```go
config := PipelineConfig{
    ProjectPath:  "/path/to/project",
    AutonomyMode: AutonomyBatch,
}
```

### 3. FULLY_AUTONOMOUS Mode

**Behavior:**
- All 6 phases execute sequentially without any user prompts
- No interactive input requested
- Auto-approve TRUE for all phases
- Checkpoint files still written for crash recovery
- Pipeline halts only on phase failure
- Final summary displayed after completion
- Suitable for CI/CD pipelines
- Timeout handling automatic

**Use Case:** Unattended execution in CI/CD or automated workflows.

**Example:**
```go
config := PipelineConfig{
    ProjectPath:  "/path/to/project",
    AutonomyMode: AutonomyFullyAutonomous,
}
```

## API Reference

### AutonomyMode Type

```go
type AutonomyMode int

const (
    AutonomyCheckpoint       AutonomyMode = iota  // Default
    AutonomyFullyAutonomous                       // Fully autonomous
    AutonomyBatch                                 // Batch mode
)
```

### Methods

#### String() string
Returns lowercase string representation:
- `AutonomyCheckpoint` → `"checkpoint"`
- `AutonomyFullyAutonomous` → `"fully_autonomous"`
- `AutonomyBatch` → `"batch"`

#### AutonomyModeFromString(s string) (AutonomyMode, error)
Parses string to AutonomyMode (case-insensitive):
```go
mode, err := AutonomyModeFromString("checkpoint")
mode, err := AutonomyModeFromString("batch")
mode, err := AutonomyModeFromString("fully_autonomous")
```

#### MarshalJSON() ([]byte, error)
Serializes to JSON string value (not integer).

#### UnmarshalJSON(data []byte) error
Deserializes from JSON string value.

### PipelineConfig

```go
type PipelineConfig struct {
    ProjectPath  string
    AutoApprove  bool
    TicketID     string
    AutonomyMode AutonomyMode  // NEW: Controls checkpoint behavior
}
```

#### GetAutoApprove() bool
Returns auto-approve setting based on autonomy mode:
- CHECKPOINT: always `false`
- BATCH: `false` (at boundaries; orchestrator handles intra-group)
- FULLY_AUTONOMOUS: always `true`

### PipelineOrchestrator

```go
type PipelineOrchestrator struct {
    AutonomyMode AutonomyMode
}
```

#### GetPhaseGroup(phase string) string
Returns the logical group for a phase:
- `"planning"`: RESEARCH, DECOMPOSITION, TDD_PLANNING
- `"document"`: MULTI_DOC, BEADS_SYNC
- `"execution"`: IMPLEMENTATION

#### IsGroupBoundary(phase string) bool
Returns true if phase is the last in its group:
- TDD_PLANNING (end of Planning Group)
- BEADS_SYNC (end of Document Group)
- IMPLEMENTATION (end of Execution Group)

#### ShouldPauseAfterPhase(phase string) bool
Determines if pipeline should pause after the phase:
- CHECKPOINT: always `true`
- BATCH: `true` only at group boundaries
- FULLY_AUTONOMOUS: always `false`

#### ShouldWriteCheckpoint(phase string) bool
Determines if checkpoint should be written:
- CHECKPOINT: always `true`
- BATCH: `true` only at group boundaries
- FULLY_AUTONOMOUS: always `true` (for crash recovery)

#### GetAutoApproveForPhase(phase string) bool
Returns auto-approve setting for specific phase:
- CHECKPOINT: always `false`
- BATCH: `true` within groups, `false` at boundaries
- FULLY_AUTONOMOUS: always `true`

## Usage Examples

### Basic Usage

```go
// Create orchestrator
orchestrator := &PipelineOrchestrator{
    AutonomyMode: AutonomyCheckpoint,
}

// Check if should pause after phase
if orchestrator.ShouldPauseAfterPhase("RESEARCH") {
    // Prompt user for input
    result := PromptResearchAction()
    // Handle user choice
}

// Check if should write checkpoint
if orchestrator.ShouldWriteCheckpoint("RESEARCH") {
    checkpointManager.WriteCheckpoint(state, "RESEARCH", nil)
}

// Get auto-approve setting for phase
autoApprove := orchestrator.GetAutoApproveForPhase("RESEARCH")
```

### Phase Groups Example

```go
orchestrator := &PipelineOrchestrator{
    AutonomyMode: AutonomyBatch,
}

// Get phase group
group := orchestrator.GetPhaseGroup("RESEARCH")        // "planning"
group = orchestrator.GetPhaseGroup("MULTI_DOC")       // "document"
group = orchestrator.GetPhaseGroup("IMPLEMENTATION")  // "execution"

// Check if group boundary
isBoundary := orchestrator.IsGroupBoundary("TDD_PLANNING")  // true
isBoundary = orchestrator.IsGroupBoundary("RESEARCH")       // false
```

### JSON Serialization

```go
// Marshal
config := PipelineConfig{
    AutonomyMode: AutonomyBatch,
}
data, _ := json.Marshal(config)
// {"autonomy_mode":"batch", ...}

// Unmarshal
var config PipelineConfig
json.Unmarshal([]byte(`{"autonomy_mode":"checkpoint"}`), &config)
// config.AutonomyMode == AutonomyCheckpoint
```

## Testing

All tests are in `/go/internal/planning/autonomy_test.go`.

Run all autonomy tests:
```bash
go test ./go/internal/planning -run "^TestAutonomyMode_|^TestPipelineConfig_|^TestPipelineOrchestrator_" -v
```

### Test Coverage

**REQ_006.1: CHECKPOINT Mode** (8 behaviors)
- ✓ Default mode
- ✓ Auto-approve FALSE
- ✓ Pauses after every phase
- ✓ Checkpoint written after every phase
- ✓ Phase-specific prompts
- ✓ Artifact display
- ✓ User feedback collection
- ✓ Resume from any checkpoint

**REQ_006.2: BATCH Mode** (7 behaviors)
- ✓ Phase group organization
- ✓ No pause within groups
- ✓ Pause at group boundaries
- ✓ Group completion summaries
- ✓ Restart from group beginning
- ✓ Checkpoint at boundaries only
- ✓ Auto-approve within groups

**REQ_006.3: FULLY_AUTONOMOUS Mode** (8 behaviors)
- ✓ Sequential execution without prompts
- ✓ No interactive input
- ✓ Auto-approve for all phases
- ✓ Halt only on failure
- ✓ Final summary after completion
- ✓ Checkpoints for crash recovery
- ✓ CI/CD suitable
- ✓ Automatic timeout handling

**REQ_006.4: AutonomyMode Enum** (9 behaviors)
- ✓ Custom int type with iota
- ✓ Three constants defined
- ✓ String() returns lowercase
- ✓ FromString() parses with error handling
- ✓ JSON marshaling to string
- ✓ JSON unmarshaling from string
- ✓ Added to PipelineConfig
- ✓ Default value handling
- ✓ CLI flag parsing support

## Implementation Files

- `/go/internal/planning/prompts.go` - AutonomyMode enum and JSON methods
- `/go/internal/planning/pipeline.go` - PipelineConfig with AutonomyMode field
- `/go/internal/planning/orchestrator.go` - PipelineOrchestrator implementation
- `/go/internal/planning/autonomy_test.go` - Comprehensive test suite

## Migration Notes

### Breaking Changes
None. The AutonomyMode field defaults to AutonomyCheckpoint (zero value), maintaining backward compatibility.

### New Dependencies
None. Uses only standard library.

### Deprecations
None. All existing APIs remain functional.

## Future Enhancements

1. **Custom Phase Groups**: Allow users to define custom phase groupings
2. **Conditional Auto-Approve**: Auto-approve based on phase success/confidence
3. **Dynamic Mode Switching**: Change mode during execution based on conditions
4. **Phase-Level Overrides**: Override autonomy mode for specific phases
5. **Notification Hooks**: Callbacks at pause points for external integrations

## Related Documentation

- [Checkpoint System](/go/internal/planning/checkpoint.go)
- [Prompt Functions](/go/internal/planning/prompts.go)
- [Pipeline Orchestration](/go/internal/planning/pipeline.go)
- [Requirements Document](/thoughts/searchable/shared/plans/2026-01-10-tdd-feature/07-the-system-must-support-three-autonomy-modes-chec.md)
