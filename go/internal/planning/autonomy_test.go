package planning

import (
	"testing"
)

// =========================================================================
// REQ_006.1: CHECKPOINT mode tests
// =========================================================================

// TestAutonomyMode_CheckpointIsDefault tests that CHECKPOINT is the default mode.
// REQ_006.1: CHECKPOINT is the default mode when no mode is specified
func TestAutonomyMode_CheckpointIsDefault(t *testing.T) {
	config := PipelineConfig{
		ProjectPath: "/test/path",
		AutoApprove: false,
		TicketID:    "TEST-123",
	}

	if config.AutonomyMode != AutonomyCheckpoint {
		t.Errorf("Default autonomy mode should be AutonomyCheckpoint, got %v", config.AutonomyMode)
	}
}

// TestAutonomyMode_CheckpointAutoApproveFalse tests auto-approve is FALSE in CHECKPOINT mode.
// REQ_006.1: Auto-approve flag is FALSE when autonomy_mode == AutonomyCheckpoint
func TestAutonomyMode_CheckpointAutoApproveFalse(t *testing.T) {
	config := PipelineConfig{
		ProjectPath:  "/test/path",
		AutonomyMode: AutonomyCheckpoint,
	}

	autoApprove := config.GetAutoApprove()
	if autoApprove {
		t.Error("Auto-approve should be FALSE in CHECKPOINT mode")
	}
}

// TestAutonomyMode_CheckpointPausesAfterEachPhase tests pipeline pauses after every phase.
// REQ_006.1: Pipeline execution pauses after EVERY phase
func TestAutonomyMode_CheckpointPausesAfterEachPhase(t *testing.T) {
	orchestrator := &PipelineOrchestrator{
		AutonomyMode: AutonomyCheckpoint,
	}

	phases := []string{"RESEARCH", "DECOMPOSITION", "TDD_PLANNING", "MULTI_DOC", "BEADS_SYNC", "IMPLEMENTATION"}

	for _, phase := range phases {
		shouldPause := orchestrator.ShouldPauseAfterPhase(phase)
		if !shouldPause {
			t.Errorf("CHECKPOINT mode should pause after %s phase", phase)
		}
	}
}

// TestAutonomyMode_CheckpointWritesAfterEachPhase tests checkpoint written after each phase.
// REQ_006.1: Checkpoint file is written to .rlm-act-checkpoints/ after each phase completes
func TestAutonomyMode_CheckpointWritesAfterEachPhase(t *testing.T) {
	orchestrator := &PipelineOrchestrator{
		AutonomyMode: AutonomyCheckpoint,
	}

	phases := []string{"RESEARCH", "DECOMPOSITION", "TDD_PLANNING", "MULTI_DOC", "BEADS_SYNC", "IMPLEMENTATION"}

	for _, phase := range phases {
		shouldWrite := orchestrator.ShouldWriteCheckpoint(phase)
		if !shouldWrite {
			t.Errorf("CHECKPOINT mode should write checkpoint after %s phase", phase)
		}
	}
}

// =========================================================================
// REQ_006.2: BATCH mode tests
// =========================================================================

// TestAutonomyMode_BatchAutoApproveWithinGroups tests auto-approve TRUE within groups.
// REQ_006.2: BATCH mode uses auto_approve=true for intra-group phases
func TestAutonomyMode_BatchAutoApproveWithinGroups(t *testing.T) {
	orchestrator := &PipelineOrchestrator{
		AutonomyMode: AutonomyBatch,
	}

	// Within Planning Group: no pause between phases
	if orchestrator.ShouldPauseAfterPhase("RESEARCH") {
		t.Error("BATCH mode should NOT pause after RESEARCH (within Planning Group)")
	}
	if orchestrator.ShouldPauseAfterPhase("DECOMPOSITION") {
		t.Error("BATCH mode should NOT pause after DECOMPOSITION (within Planning Group)")
	}
}

// TestAutonomyMode_BatchPausesAtGroupBoundaries tests pauses at group boundaries.
// REQ_006.2: User is prompted only at group boundaries
func TestAutonomyMode_BatchPausesAtGroupBoundaries(t *testing.T) {
	orchestrator := &PipelineOrchestrator{
		AutonomyMode: AutonomyBatch,
	}

	// Should pause after Planning Group (TDD_PLANNING is last in group)
	if !orchestrator.ShouldPauseAfterPhase("TDD_PLANNING") {
		t.Error("BATCH mode should pause after TDD_PLANNING (end of Planning Group)")
	}

	// Should pause after Document Group (BEADS_SYNC is last in group)
	if !orchestrator.ShouldPauseAfterPhase("BEADS_SYNC") {
		t.Error("BATCH mode should pause after BEADS_SYNC (end of Document Group)")
	}

	// Should pause after Execution Group (IMPLEMENTATION is last in group)
	if !orchestrator.ShouldPauseAfterPhase("IMPLEMENTATION") {
		t.Error("BATCH mode should pause after IMPLEMENTATION (end of Execution Group)")
	}
}

// TestAutonomyMode_BatchCheckpointsAtGroupBoundaries tests checkpoints at group boundaries.
// REQ_006.2: Checkpoint is written at group boundaries, not at individual phase boundaries
func TestAutonomyMode_BatchCheckpointsAtGroupBoundaries(t *testing.T) {
	orchestrator := &PipelineOrchestrator{
		AutonomyMode: AutonomyBatch,
	}

	// No checkpoint within groups
	if orchestrator.ShouldWriteCheckpoint("RESEARCH") {
		t.Error("BATCH mode should NOT write checkpoint after RESEARCH (within group)")
	}
	if orchestrator.ShouldWriteCheckpoint("DECOMPOSITION") {
		t.Error("BATCH mode should NOT write checkpoint after DECOMPOSITION (within group)")
	}
	if orchestrator.ShouldWriteCheckpoint("MULTI_DOC") {
		t.Error("BATCH mode should NOT write checkpoint after MULTI_DOC (within group)")
	}

	// Checkpoint at group boundaries
	if !orchestrator.ShouldWriteCheckpoint("TDD_PLANNING") {
		t.Error("BATCH mode should write checkpoint after TDD_PLANNING (group boundary)")
	}
	if !orchestrator.ShouldWriteCheckpoint("BEADS_SYNC") {
		t.Error("BATCH mode should write checkpoint after BEADS_SYNC (group boundary)")
	}
	if !orchestrator.ShouldWriteCheckpoint("IMPLEMENTATION") {
		t.Error("BATCH mode should write checkpoint after IMPLEMENTATION (group boundary)")
	}
}

// TestAutonomyMode_BatchPhaseGroups tests phase group organization.
// REQ_006.2: Phases are organized into logical groups
func TestAutonomyMode_BatchPhaseGroups(t *testing.T) {
	orchestrator := &PipelineOrchestrator{
		AutonomyMode: AutonomyBatch,
	}

	testCases := []struct {
		phase         string
		expectedGroup string
	}{
		{"RESEARCH", "planning"},
		{"DECOMPOSITION", "planning"},
		{"TDD_PLANNING", "planning"},
		{"MULTI_DOC", "document"},
		{"BEADS_SYNC", "document"},
		{"IMPLEMENTATION", "execution"},
	}

	for _, tc := range testCases {
		group := orchestrator.GetPhaseGroup(tc.phase)
		if group != tc.expectedGroup {
			t.Errorf("Phase %s should be in %s group, got %s", tc.phase, tc.expectedGroup, group)
		}
	}
}

// =========================================================================
// REQ_006.3: FULLY_AUTONOMOUS mode tests
// =========================================================================

// TestAutonomyMode_FullyAutonomousAutoApproveTrue tests auto-approve TRUE for all phases.
// REQ_006.3: Auto-approve flag is TRUE for all phases
func TestAutonomyMode_FullyAutonomousAutoApproveTrue(t *testing.T) {
	config := PipelineConfig{
		ProjectPath:  "/test/path",
		AutonomyMode: AutonomyFullyAutonomous,
	}

	autoApprove := config.GetAutoApprove()
	if !autoApprove {
		t.Error("Auto-approve should be TRUE in FULLY_AUTONOMOUS mode")
	}
}

// TestAutonomyMode_FullyAutonomousNoPauses tests no pauses in execution.
// REQ_006.3: All 6 phases execute sequentially without any user prompts
func TestAutonomyMode_FullyAutonomousNoPauses(t *testing.T) {
	orchestrator := &PipelineOrchestrator{
		AutonomyMode: AutonomyFullyAutonomous,
	}

	phases := []string{"RESEARCH", "DECOMPOSITION", "TDD_PLANNING", "MULTI_DOC", "BEADS_SYNC", "IMPLEMENTATION"}

	for _, phase := range phases {
		shouldPause := orchestrator.ShouldPauseAfterPhase(phase)
		if shouldPause {
			t.Errorf("FULLY_AUTONOMOUS mode should NOT pause after %s phase", phase)
		}
	}
}

// TestAutonomyMode_FullyAutonomousWritesCheckpoints tests checkpoints still written.
// REQ_006.3: Checkpoint files are still written after each phase for crash recovery
func TestAutonomyMode_FullyAutonomousWritesCheckpoints(t *testing.T) {
	orchestrator := &PipelineOrchestrator{
		AutonomyMode: AutonomyFullyAutonomous,
	}

	phases := []string{"RESEARCH", "DECOMPOSITION", "TDD_PLANNING", "MULTI_DOC", "BEADS_SYNC", "IMPLEMENTATION"}

	for _, phase := range phases {
		shouldWrite := orchestrator.ShouldWriteCheckpoint(phase)
		if !shouldWrite {
			t.Errorf("FULLY_AUTONOMOUS mode should write checkpoint after %s phase for crash recovery", phase)
		}
	}
}

// =========================================================================
// REQ_006.4: AutonomyMode enum tests
// =========================================================================

// TestAutonomyMode_FromString tests parsing string to AutonomyMode.
// REQ_006.4: FromString() static function parses string to AutonomyMode
func TestAutonomyMode_FromString(t *testing.T) {
	testCases := []struct {
		input       string
		expected    AutonomyMode
		shouldError bool
	}{
		{"checkpoint", AutonomyCheckpoint, false},
		{"batch", AutonomyBatch, false},
		{"fully_autonomous", AutonomyFullyAutonomous, false},
		{"CHECKPOINT", AutonomyCheckpoint, false}, // case-insensitive
		{"Batch", AutonomyBatch, false},
		{"invalid", AutonomyCheckpoint, true},
		{"", AutonomyCheckpoint, true},
	}

	for _, tc := range testCases {
		mode, err := AutonomyModeFromString(tc.input)
		if tc.shouldError {
			if err == nil {
				t.Errorf("AutonomyModeFromString(%q) should return error", tc.input)
			}
		} else {
			if err != nil {
				t.Errorf("AutonomyModeFromString(%q) unexpected error: %v", tc.input, err)
			}
			if mode != tc.expected {
				t.Errorf("AutonomyModeFromString(%q) = %v, want %v", tc.input, mode, tc.expected)
			}
		}
	}
}

// TestAutonomyMode_JSONMarshal tests JSON marshaling to string value.
// REQ_006.4: JSON marshaling serializes to string value (not integer)
func TestAutonomyMode_JSONMarshal(t *testing.T) {
	testCases := []struct {
		mode     AutonomyMode
		expected string
	}{
		{AutonomyCheckpoint, `"checkpoint"`},
		{AutonomyBatch, `"batch"`},
		{AutonomyFullyAutonomous, `"fully_autonomous"`},
	}

	for _, tc := range testCases {
		data, err := tc.mode.MarshalJSON()
		if err != nil {
			t.Errorf("AutonomyMode(%v).MarshalJSON() error: %v", tc.mode, err)
		}
		if string(data) != tc.expected {
			t.Errorf("AutonomyMode(%v).MarshalJSON() = %s, want %s", tc.mode, string(data), tc.expected)
		}
	}
}

// TestAutonomyMode_JSONUnmarshal tests JSON unmarshaling from string value.
// REQ_006.4: JSON unmarshaling parses from string value
func TestAutonomyMode_JSONUnmarshal(t *testing.T) {
	testCases := []struct {
		input       string
		expected    AutonomyMode
		shouldError bool
	}{
		{`"checkpoint"`, AutonomyCheckpoint, false},
		{`"batch"`, AutonomyBatch, false},
		{`"fully_autonomous"`, AutonomyFullyAutonomous, false},
		{`"invalid"`, AutonomyCheckpoint, true},
		{`123`, AutonomyCheckpoint, true}, // should reject integer
	}

	for _, tc := range testCases {
		var mode AutonomyMode
		err := mode.UnmarshalJSON([]byte(tc.input))
		if tc.shouldError {
			if err == nil {
				t.Errorf("UnmarshalJSON(%s) should return error", tc.input)
			}
		} else {
			if err != nil {
				t.Errorf("UnmarshalJSON(%s) unexpected error: %v", tc.input, err)
			}
			if mode != tc.expected {
				t.Errorf("UnmarshalJSON(%s) = %v, want %v", tc.input, mode, tc.expected)
			}
		}
	}
}

// TestPipelineConfig_AutonomyModeField tests AutonomyMode field in PipelineConfig.
// REQ_006.4: AutonomyMode is added to PipelineConfig struct
func TestPipelineConfig_AutonomyModeField(t *testing.T) {
	config := PipelineConfig{
		ProjectPath:  "/test/path",
		AutoApprove:  false,
		TicketID:     "TEST-123",
		AutonomyMode: AutonomyBatch,
	}

	if config.AutonomyMode != AutonomyBatch {
		t.Errorf("PipelineConfig.AutonomyMode = %v, want AutonomyBatch", config.AutonomyMode)
	}
}

// TestPipelineOrchestrator_RespectsAutonomyMode tests orchestrator respects mode.
// REQ_006.4: Update pipeline orchestration to respect the autonomy mode
func TestPipelineOrchestrator_RespectsAutonomyMode(t *testing.T) {
	testCases := []struct {
		mode                AutonomyMode
		phase               string
		shouldPause         bool
		shouldWriteCheckpoint bool
	}{
		// CHECKPOINT mode: pause and checkpoint after every phase
		{AutonomyCheckpoint, "RESEARCH", true, true},
		{AutonomyCheckpoint, "DECOMPOSITION", true, true},
		{AutonomyCheckpoint, "TDD_PLANNING", true, true},

		// BATCH mode: pause and checkpoint only at group boundaries
		{AutonomyBatch, "RESEARCH", false, false},
		{AutonomyBatch, "DECOMPOSITION", false, false},
		{AutonomyBatch, "TDD_PLANNING", true, true},
		{AutonomyBatch, "MULTI_DOC", false, false},
		{AutonomyBatch, "BEADS_SYNC", true, true},

		// FULLY_AUTONOMOUS mode: no pause but checkpoint after every phase
		{AutonomyFullyAutonomous, "RESEARCH", false, true},
		{AutonomyFullyAutonomous, "DECOMPOSITION", false, true},
		{AutonomyFullyAutonomous, "IMPLEMENTATION", false, true},
	}

	for _, tc := range testCases {
		orchestrator := &PipelineOrchestrator{
			AutonomyMode: tc.mode,
		}

		pause := orchestrator.ShouldPauseAfterPhase(tc.phase)
		if pause != tc.shouldPause {
			t.Errorf("Mode %v, Phase %s: ShouldPauseAfterPhase = %v, want %v",
				tc.mode, tc.phase, pause, tc.shouldPause)
		}

		checkpoint := orchestrator.ShouldWriteCheckpoint(tc.phase)
		if checkpoint != tc.shouldWriteCheckpoint {
			t.Errorf("Mode %v, Phase %s: ShouldWriteCheckpoint = %v, want %v",
				tc.mode, tc.phase, checkpoint, tc.shouldWriteCheckpoint)
		}
	}
}

// =========================================================================
// Integration tests
// =========================================================================

// TestPipelineConfig_GetAutoApprove tests GetAutoApprove method for all modes.
func TestPipelineConfig_GetAutoApprove(t *testing.T) {
	testCases := []struct {
		mode           AutonomyMode
		expectedResult bool
	}{
		{AutonomyCheckpoint, false},
		{AutonomyBatch, false}, // False at boundaries
		{AutonomyFullyAutonomous, true},
	}

	for _, tc := range testCases {
		config := PipelineConfig{
			AutonomyMode: tc.mode,
		}

		autoApprove := config.GetAutoApprove()
		if autoApprove != tc.expectedResult {
			t.Errorf("Mode %v: GetAutoApprove() = %v, want %v",
				tc.mode, autoApprove, tc.expectedResult)
		}
	}
}

// TestPipelineOrchestrator_GetAutoApproveForPhase tests per-phase auto-approve.
func TestPipelineOrchestrator_GetAutoApproveForPhase(t *testing.T) {
	testCases := []struct {
		mode           AutonomyMode
		phase          string
		expectedResult bool
	}{
		// CHECKPOINT: always false
		{AutonomyCheckpoint, "RESEARCH", false},
		{AutonomyCheckpoint, "TDD_PLANNING", false},

		// BATCH: true within groups, false at boundaries
		{AutonomyBatch, "RESEARCH", true},
		{AutonomyBatch, "DECOMPOSITION", true},
		{AutonomyBatch, "TDD_PLANNING", false}, // boundary
		{AutonomyBatch, "MULTI_DOC", true},
		{AutonomyBatch, "BEADS_SYNC", false}, // boundary

		// FULLY_AUTONOMOUS: always true
		{AutonomyFullyAutonomous, "RESEARCH", true},
		{AutonomyFullyAutonomous, "IMPLEMENTATION", true},
	}

	for _, tc := range testCases {
		orchestrator := &PipelineOrchestrator{
			AutonomyMode: tc.mode,
		}

		autoApprove := orchestrator.GetAutoApproveForPhase(tc.phase)
		if autoApprove != tc.expectedResult {
			t.Errorf("Mode %v, Phase %s: GetAutoApproveForPhase() = %v, want %v",
				tc.mode, tc.phase, autoApprove, tc.expectedResult)
		}
	}
}
