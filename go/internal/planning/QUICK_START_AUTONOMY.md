# Quick Start: Autonomy Modes

## TL;DR

Three modes control how the pipeline handles user interaction:

```go
AutonomyCheckpoint       // Pause after every phase (default)
AutonomyBatch           // Pause only at group boundaries
AutonomyFullyAutonomous // Never pause, run everything
```

## 30-Second Setup

```go
// 1. Create config with desired mode
config := PipelineConfig{
    ProjectPath:  "/path/to/project",
    AutonomyMode: AutonomyBatch, // or omit for default
}

// 2. Create orchestrator
orchestrator := &PipelineOrchestrator{
    AutonomyMode: config.AutonomyMode,
}

// 3. Use in pipeline
for _, phase := range phases {
    executePhase(phase)

    if orchestrator.ShouldWriteCheckpoint(phase) {
        writeCheckpoint(phase)
    }

    if orchestrator.ShouldPauseAfterPhase(phase) {
        promptUser(phase)
    }
}
```

## When to Use Each Mode

| Mode | Use When | Example |
|------|----------|---------|
| **CHECKPOINT** | Interactive development, want control at every step | Local feature development |
| **BATCH** | Want to review logical groups, not every phase | Code review workflow |
| **FULLY_AUTONOMOUS** | Unattended execution, CI/CD | GitHub Actions, Jenkins |

## API Cheat Sheet

### Check Pause Behavior
```go
orchestrator.ShouldPauseAfterPhase("RESEARCH")     // true/false based on mode
orchestrator.ShouldWriteCheckpoint("RESEARCH")     // true/false based on mode
orchestrator.GetAutoApproveForPhase("RESEARCH")    // true/false based on mode
```

### Phase Groups
```go
orchestrator.GetPhaseGroup("RESEARCH")        // "planning"
orchestrator.GetPhaseGroup("MULTI_DOC")       // "document"
orchestrator.GetPhaseGroup("IMPLEMENTATION")  // "execution"

orchestrator.IsGroupBoundary("TDD_PLANNING")  // true (end of planning)
orchestrator.IsGroupBoundary("RESEARCH")      // false (within planning)
```

### Parse from String
```go
mode, err := AutonomyModeFromString("checkpoint")
mode, err := AutonomyModeFromString("batch")
mode, err := AutonomyModeFromString("fully_autonomous")
```

### Convert to String
```go
mode := AutonomyBatch
mode.String() // "batch"
```

## Mode Comparison Matrix

| Behavior | CHECKPOINT | BATCH | FULLY_AUTONOMOUS |
|----------|-----------|-------|------------------|
| Pause after RESEARCH | ✅ | ❌ | ❌ |
| Pause after TDD_PLANNING | ✅ | ✅ (group boundary) | ❌ |
| Pause after IMPLEMENTATION | ✅ | ✅ (group boundary) | ❌ |
| Write checkpoint after RESEARCH | ✅ | ❌ | ✅ |
| Write checkpoint after TDD_PLANNING | ✅ | ✅ | ✅ |
| Auto-approve RESEARCH | ❌ | ✅ | ✅ |
| Auto-approve TDD_PLANNING | ❌ | ❌ (boundary) | ✅ |

## Phase Groups Reference

```
Planning Group (3 phases):
├─ RESEARCH
├─ DECOMPOSITION
└─ TDD_PLANNING ← pause point in BATCH mode

Document Group (2 phases):
├─ MULTI_DOC
└─ BEADS_SYNC ← pause point in BATCH mode

Execution Group (1 phase):
└─ IMPLEMENTATION ← pause point in BATCH mode
```

## Common Patterns

### Pattern 1: Standard Pipeline
```go
config := PipelineConfig{AutonomyMode: AutonomyCheckpoint}
orchestrator := &PipelineOrchestrator{AutonomyMode: config.AutonomyMode}

for _, phase := range []string{"RESEARCH", "DECOMPOSITION", "TDD_PLANNING"} {
    runPhase(phase)

    if orchestrator.ShouldWriteCheckpoint(phase) {
        cm.WriteCheckpoint(state, phase, nil)
    }

    if orchestrator.ShouldPauseAfterPhase(phase) {
        action := promptUser(phase)
        if action == ActionRevise {
            revisePhase(phase)
        }
    }
}
```

### Pattern 2: CI/CD Pipeline
```go
config := PipelineConfig{AutonomyMode: AutonomyFullyAutonomous}
orchestrator := &PipelineOrchestrator{AutonomyMode: config.AutonomyMode}

// No prompts, runs straight through
for _, phase := range allPhases {
    if err := runPhase(phase); err != nil {
        log.Fatal(err) // Only stops on error
    }
    cm.WriteCheckpoint(state, phase, nil) // Always writes for recovery
}
```

### Pattern 3: Group-Based Review
```go
config := PipelineConfig{AutonomyMode: AutonomyBatch}
orchestrator := &PipelineOrchestrator{AutonomyMode: config.AutonomyMode}

var groupArtifacts []string
for _, phase := range allPhases {
    artifacts := runPhase(phase)
    groupArtifacts = append(groupArtifacts, artifacts...)

    if orchestrator.ShouldPauseAfterPhase(phase) {
        // Review entire group at once
        group := orchestrator.GetPhaseGroup(phase)
        action := promptGroupReview(group, groupArtifacts)
        groupArtifacts = nil // Reset for next group
    }
}
```

## Testing Your Integration

```go
// Test that your code respects autonomy mode
func TestMyPipeline_RespectsAutonomyMode(t *testing.T) {
    orchestrator := &PipelineOrchestrator{
        AutonomyMode: AutonomyCheckpoint,
    }

    // Run pipeline...

    // Verify it paused when expected
    if !paused {
        t.Error("Should have paused in CHECKPOINT mode")
    }
}
```

## JSON Config Example

```json
{
  "project_path": "/path/to/project",
  "ticket_id": "PROJ-123",
  "autonomy_mode": "batch"
}
```

Parse it:
```go
var config PipelineConfig
json.Unmarshal(data, &config)
// config.AutonomyMode == AutonomyBatch
```

## Troubleshooting

**Q: Pipeline not pausing in CHECKPOINT mode?**
```go
// Check you're calling ShouldPauseAfterPhase
if orchestrator.ShouldPauseAfterPhase(phase) {
    // Must call prompt here!
}
```

**Q: Checkpoints not written in BATCH mode?**
```go
// Only written at boundaries. Check:
orchestrator.IsGroupBoundary(phase) // true = checkpoint written
```

**Q: Pipeline pausing in FULLY_AUTONOMOUS mode?**
```go
// Verify mode is set correctly
fmt.Println(config.AutonomyMode) // Should print "fully_autonomous"
```

## See Also

- [Full Documentation](AUTONOMY_MODES.md)
- [Implementation Summary](../../PHASE_7_IMPLEMENTATION_SUMMARY.md)
- [Test Suite](autonomy_test.go)
