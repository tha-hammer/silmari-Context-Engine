package planning

// PipelineOrchestrator manages pipeline execution flow based on autonomy mode.
type PipelineOrchestrator struct {
	AutonomyMode AutonomyMode
}

// PhaseGroup represents a logical group of pipeline phases.
const (
	PhaseGroupPlanning  = "planning"
	PhaseGroupDocument  = "document"
	PhaseGroupExecution = "execution"
)

// GetPhaseGroup returns the phase group name for a given phase.
func (po *PipelineOrchestrator) GetPhaseGroup(phase string) string {
	switch phase {
	case "RESEARCH", "DECOMPOSITION", "TDD_PLANNING":
		return PhaseGroupPlanning
	case "MULTI_DOC", "BEADS_SYNC":
		return PhaseGroupDocument
	case "IMPLEMENTATION":
		return PhaseGroupExecution
	default:
		return ""
	}
}

// IsGroupBoundary returns true if the phase is the last phase in its group.
func (po *PipelineOrchestrator) IsGroupBoundary(phase string) bool {
	switch phase {
	case "TDD_PLANNING", "BEADS_SYNC", "IMPLEMENTATION":
		return true
	default:
		return false
	}
}

// ShouldPauseAfterPhase returns true if the pipeline should pause for user input after the phase.
func (po *PipelineOrchestrator) ShouldPauseAfterPhase(phase string) bool {
	switch po.AutonomyMode {
	case AutonomyCheckpoint:
		// Pause after every phase
		return true
	case AutonomyBatch:
		// Pause only at group boundaries
		return po.IsGroupBoundary(phase)
	case AutonomyFullyAutonomous:
		// Never pause
		return false
	default:
		// Default to checkpoint behavior
		return true
	}
}

// ShouldWriteCheckpoint returns true if a checkpoint should be written after the phase.
func (po *PipelineOrchestrator) ShouldWriteCheckpoint(phase string) bool {
	switch po.AutonomyMode {
	case AutonomyCheckpoint:
		// Write checkpoint after every phase
		return true
	case AutonomyBatch:
		// Write checkpoint only at group boundaries
		return po.IsGroupBoundary(phase)
	case AutonomyFullyAutonomous:
		// Write checkpoint after every phase for crash recovery
		return true
	default:
		// Default to checkpoint behavior
		return true
	}
}

// GetAutoApproveForPhase returns whether auto-approve should be enabled for a specific phase.
func (po *PipelineOrchestrator) GetAutoApproveForPhase(phase string) bool {
	switch po.AutonomyMode {
	case AutonomyCheckpoint:
		// Never auto-approve in checkpoint mode
		return false
	case AutonomyBatch:
		// Auto-approve within groups, not at boundaries
		return !po.IsGroupBoundary(phase)
	case AutonomyFullyAutonomous:
		// Always auto-approve in fully autonomous mode
		return true
	default:
		// Default to no auto-approve
		return false
	}
}
