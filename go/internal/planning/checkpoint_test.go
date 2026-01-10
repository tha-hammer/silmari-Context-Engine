package planning

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/google/uuid"
)

// TestWriteCheckpoint_CreatesDirectory tests that checkpoint directory is created.
// REQ_003.1: Checkpoint files are created in `.rlm-act-checkpoints/` directory
func TestWriteCheckpoint_CreatesDirectory(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	state := map[string]interface{}{"phase": "test", "data": "value"}
	_, err := cm.WriteCheckpoint(state, "test-phase", nil)
	if err != nil {
		t.Fatalf("WriteCheckpoint failed: %v", err)
	}

	// Verify directory was created
	checkpointsDir := filepath.Join(tmpDir, ".rlm-act-checkpoints")
	if _, err := os.Stat(checkpointsDir); os.IsNotExist(err) {
		t.Errorf("Checkpoints directory was not created")
	}
}

// TestWriteCheckpoint_UUIDFilename tests that checkpoint files use UUID v4 format.
// REQ_003.1: Each checkpoint file is named with a UUID v4 format: `{uuid}.json`
func TestWriteCheckpoint_UUIDFilename(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	state := map[string]interface{}{"test": "data"}
	checkpointPath, err := cm.WriteCheckpoint(state, "test-phase", nil)
	if err != nil {
		t.Fatalf("WriteCheckpoint failed: %v", err)
	}

	// Extract filename and verify UUID format
	filename := filepath.Base(checkpointPath)
	uuidStr := filename[:len(filename)-5] // Remove .json extension

	_, err = uuid.Parse(uuidStr)
	if err != nil {
		t.Errorf("Checkpoint filename is not a valid UUID: %s", uuidStr)
	}
}

// TestWriteCheckpoint_RequiredFields tests that checkpoint JSON contains required fields.
// REQ_003.1: Checkpoint JSON contains required fields: id, phase, timestamp, state, errors, git_commit
func TestWriteCheckpoint_RequiredFields(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	state := map[string]interface{}{"data": "test"}
	errors := []string{"error1", "error2"}

	checkpointPath, err := cm.WriteCheckpoint(state, "test-phase", errors)
	if err != nil {
		t.Fatalf("WriteCheckpoint failed: %v", err)
	}

	// Read and parse checkpoint
	data, err := os.ReadFile(checkpointPath)
	if err != nil {
		t.Fatalf("Failed to read checkpoint: %v", err)
	}

	var cp Checkpoint
	if err := json.Unmarshal(data, &cp); err != nil {
		t.Fatalf("Failed to unmarshal checkpoint: %v", err)
	}

	// Verify required fields
	if cp.ID == "" {
		t.Errorf("Checkpoint missing 'id' field")
	}
	if cp.Phase != "test-phase" {
		t.Errorf("Expected phase 'test-phase', got '%s'", cp.Phase)
	}
	if cp.Timestamp == "" {
		t.Errorf("Checkpoint missing 'timestamp' field")
	}
	if cp.State == nil {
		t.Errorf("Checkpoint missing 'state' field")
	}
	if cp.Errors == nil {
		t.Errorf("Checkpoint 'errors' field is nil (should be array)")
	}
	if len(cp.Errors) != 2 {
		t.Errorf("Expected 2 errors, got %d", len(cp.Errors))
	}
	// git_commit can be empty string if not in repo, just verify field exists
	if _, ok := map[string]interface{}{"git_commit": cp.GitCommit}["git_commit"]; !ok {
		t.Errorf("Checkpoint missing 'git_commit' field")
	}
}

// TestWriteCheckpoint_TimestampFormat tests timestamp is in RFC3339/ISO8601 format.
// REQ_003.1: Timestamp is in RFC3339/ISO8601 format with timezone suffix
func TestWriteCheckpoint_TimestampFormat(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	state := map[string]interface{}{"test": "data"}
	checkpointPath, err := cm.WriteCheckpoint(state, "test-phase", nil)
	if err != nil {
		t.Fatalf("WriteCheckpoint failed: %v", err)
	}

	// Read checkpoint
	data, err := os.ReadFile(checkpointPath)
	if err != nil {
		t.Fatalf("Failed to read checkpoint: %v", err)
	}

	var cp Checkpoint
	if err := json.Unmarshal(data, &cp); err != nil {
		t.Fatalf("Failed to unmarshal checkpoint: %v", err)
	}

	// Parse timestamp to verify RFC3339 format
	_, err = time.Parse(time.RFC3339, cp.Timestamp)
	if err != nil {
		t.Errorf("Timestamp not in RFC3339 format: %s, error: %v", cp.Timestamp, err)
	}
}

// TestWriteCheckpoint_EmptyErrors tests that empty errors is an array, not null.
// REQ_003.1: Errors field is an array of error message strings (empty array if no errors)
func TestWriteCheckpoint_EmptyErrors(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	state := map[string]interface{}{"test": "data"}
	checkpointPath, err := cm.WriteCheckpoint(state, "test-phase", nil)
	if err != nil {
		t.Fatalf("WriteCheckpoint failed: %v", err)
	}

	// Read checkpoint
	data, err := os.ReadFile(checkpointPath)
	if err != nil {
		t.Fatalf("Failed to read checkpoint: %v", err)
	}

	var cp Checkpoint
	if err := json.Unmarshal(data, &cp); err != nil {
		t.Fatalf("Failed to unmarshal checkpoint: %v", err)
	}

	// Verify errors is an empty array, not nil
	if cp.Errors == nil {
		t.Errorf("Errors field is nil, expected empty array")
	}
	if len(cp.Errors) != 0 {
		t.Errorf("Expected empty errors array, got %d items", len(cp.Errors))
	}
}

// TestWriteCheckpoint_ReturnsAbsolutePath tests that absolute path is returned.
// REQ_003.1: Function returns absolute path to created checkpoint file
func TestWriteCheckpoint_ReturnsAbsolutePath(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	state := map[string]interface{}{"test": "data"}
	checkpointPath, err := cm.WriteCheckpoint(state, "test-phase", nil)
	if err != nil {
		t.Fatalf("WriteCheckpoint failed: %v", err)
	}

	// Verify it's an absolute path
	if !filepath.IsAbs(checkpointPath) {
		t.Errorf("Expected absolute path, got relative: %s", checkpointPath)
	}
}

// TestWriteCheckpoint_FilePermissions tests file permissions are 0644.
// REQ_003.1: Checkpoint files are written with mode 0644
func TestWriteCheckpoint_FilePermissions(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	state := map[string]interface{}{"test": "data"}
	checkpointPath, err := cm.WriteCheckpoint(state, "test-phase", nil)
	if err != nil {
		t.Fatalf("WriteCheckpoint failed: %v", err)
	}

	// Check file permissions
	info, err := os.Stat(checkpointPath)
	if err != nil {
		t.Fatalf("Failed to stat checkpoint file: %v", err)
	}

	mode := info.Mode().Perm()
	if mode != 0644 {
		t.Errorf("Expected file mode 0644, got %o", mode)
	}
}

// TestDetectResumableCheckpoint_NoDirectory tests return nil when directory doesn't exist.
// REQ_003.3: Returns nil/empty if no checkpoints exist or directory doesn't exist
func TestDetectResumableCheckpoint_NoDirectory(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	checkpoint, err := cm.DetectResumableCheckpoint()
	if err != nil {
		t.Fatalf("DetectResumableCheckpoint failed: %v", err)
	}

	if checkpoint != nil {
		t.Errorf("Expected nil checkpoint when directory doesn't exist, got %v", checkpoint)
	}
}

// TestDetectResumableCheckpoint_EmptyDirectory tests return nil when no checkpoints exist.
// REQ_003.3: Returns nil/empty if no checkpoints exist
func TestDetectResumableCheckpoint_EmptyDirectory(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	// Create empty checkpoints directory
	os.MkdirAll(cm.checkpointsDir, 0755)

	checkpoint, err := cm.DetectResumableCheckpoint()
	if err != nil {
		t.Fatalf("DetectResumableCheckpoint failed: %v", err)
	}

	if checkpoint != nil {
		t.Errorf("Expected nil checkpoint when directory is empty, got %v", checkpoint)
	}
}

// TestDetectResumableCheckpoint_MostRecent tests return most recent by timestamp.
// REQ_003.3: DetectResumableCheckpoint() returns most recent checkpoint based on timestamp field
func TestDetectResumableCheckpoint_MostRecent(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	// Create checkpoints with different timestamps
	old := time.Now().Add(-2 * time.Hour).UTC().Format(time.RFC3339)
	recent := time.Now().UTC().Format(time.RFC3339)

	os.MkdirAll(cm.checkpointsDir, 0755)

	// Write old checkpoint
	oldCP := Checkpoint{
		ID:        uuid.New().String(),
		Phase:     "old-phase",
		Timestamp: old,
		State:     map[string]interface{}{},
		Errors:    []string{},
		GitCommit: "",
	}
	oldData, _ := json.Marshal(oldCP)
	os.WriteFile(filepath.Join(cm.checkpointsDir, oldCP.ID+".json"), oldData, 0644)

	// Write recent checkpoint
	recentCP := Checkpoint{
		ID:        uuid.New().String(),
		Phase:     "recent-phase",
		Timestamp: recent,
		State:     map[string]interface{}{},
		Errors:    []string{},
		GitCommit: "",
	}
	recentData, _ := json.Marshal(recentCP)
	os.WriteFile(filepath.Join(cm.checkpointsDir, recentCP.ID+".json"), recentData, 0644)

	// Detect should return most recent
	checkpoint, err := cm.DetectResumableCheckpoint()
	if err != nil {
		t.Fatalf("DetectResumableCheckpoint failed: %v", err)
	}

	if checkpoint == nil {
		t.Fatalf("Expected checkpoint, got nil")
	}

	if checkpoint.Phase != "recent-phase" {
		t.Errorf("Expected recent checkpoint, got phase: %s", checkpoint.Phase)
	}
}

// TestLoadCheckpoint_FileNotExist tests error when file doesn't exist.
// REQ_003.3: LoadCheckpoint returns error if file doesn't exist
func TestLoadCheckpoint_FileNotExist(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	_, err := cm.LoadCheckpoint(filepath.Join(tmpDir, "nonexistent.json"))
	if err == nil {
		t.Errorf("Expected error when file doesn't exist")
	}
}

// TestLoadCheckpoint_InvalidJSON tests error when JSON is invalid.
// REQ_003.3: LoadCheckpoint returns error if invalid JSON
func TestLoadCheckpoint_InvalidJSON(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	// Write invalid JSON
	invalidFile := filepath.Join(tmpDir, "invalid.json")
	os.WriteFile(invalidFile, []byte("not valid json"), 0644)

	_, err := cm.LoadCheckpoint(invalidFile)
	if err == nil {
		t.Errorf("Expected error when JSON is invalid")
	}
}

// TestLoadCheckpoint_MissingRequiredFields tests error when required fields missing.
// REQ_003.3: LoadCheckpoint returns error if missing required fields
func TestLoadCheckpoint_MissingRequiredFields(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	// Write checkpoint with missing fields
	invalidFile := filepath.Join(tmpDir, "missing.json")
	data := []byte(`{"id": "", "phase": "test"}`)
	os.WriteFile(invalidFile, data, 0644)

	_, err := cm.LoadCheckpoint(invalidFile)
	if err == nil {
		t.Errorf("Expected error when required fields are missing")
	}
}

// TestLoadCheckpoint_ValidCheckpoint tests successful loading.
// REQ_003.3: LoadCheckpoint deserializes JSON and returns checkpoint
func TestLoadCheckpoint_ValidCheckpoint(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	// Write valid checkpoint
	checkpointFile := filepath.Join(tmpDir, "valid.json")
	cp := Checkpoint{
		ID:        uuid.New().String(),
		Phase:     "test-phase",
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		State:     map[string]interface{}{"data": "value"},
		Errors:    []string{},
		GitCommit: "abc123",
	}
	data, _ := json.Marshal(cp)
	os.WriteFile(checkpointFile, data, 0644)

	// Load checkpoint
	loaded, err := cm.LoadCheckpoint(checkpointFile)
	if err != nil {
		t.Fatalf("LoadCheckpoint failed: %v", err)
	}

	if loaded.ID != cp.ID {
		t.Errorf("Expected ID %s, got %s", cp.ID, loaded.ID)
	}
	if loaded.Phase != cp.Phase {
		t.Errorf("Expected phase %s, got %s", cp.Phase, loaded.Phase)
	}
}

// TestGetCheckpointAgeDays_EmptyTimestamp tests return 0 for empty timestamp.
// REQ_003.3: GetCheckpointAgeDays handles missing timestamps
func TestGetCheckpointAgeDays_EmptyTimestamp(t *testing.T) {
	cm := NewCheckpointManager(t.TempDir())

	cp := &Checkpoint{Timestamp: ""}
	age := cm.GetCheckpointAgeDays(cp)

	if age != 0 {
		t.Errorf("Expected age 0 for empty timestamp, got %d", age)
	}
}

// TestGetCheckpointAgeDays_ValidTimestamp tests age calculation.
// REQ_003.3: GetCheckpointAgeDays calculates age from timestamp field
func TestGetCheckpointAgeDays_ValidTimestamp(t *testing.T) {
	cm := NewCheckpointManager(t.TempDir())

	// Create checkpoint from 2 days ago
	twoDaysAgo := time.Now().Add(-48 * time.Hour).UTC().Format(time.RFC3339)
	cp := &Checkpoint{Timestamp: twoDaysAgo}

	age := cm.GetCheckpointAgeDays(cp)

	// Age should be 2 days (with some tolerance for test execution time)
	if age < 1 || age > 3 {
		t.Errorf("Expected age around 2 days, got %d", age)
	}
}

// TestCleanupByAge_NoDirectory tests return 0,0 when directory doesn't exist.
// REQ_003.4: Gracefully handles missing/empty checkpoints directory
func TestCleanupByAge_NoDirectory(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	deleted, failed := cm.CleanupByAge(30)

	if deleted != 0 || failed != 0 {
		t.Errorf("Expected (0, 0) when directory doesn't exist, got (%d, %d)", deleted, failed)
	}
}

// TestCleanupByAge_DeletesOldCheckpoints tests deletion of old checkpoints.
// REQ_003.4: CleanupByAge(days int) deletes all checkpoints with age >= days
func TestCleanupByAge_DeletesOldCheckpoints(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	os.MkdirAll(cm.checkpointsDir, 0755)

	// Create old checkpoint (3 days ago)
	old := time.Now().Add(-72 * time.Hour).UTC().Format(time.RFC3339)
	oldCP := Checkpoint{
		ID:        uuid.New().String(),
		Phase:     "old",
		Timestamp: old,
		State:     map[string]interface{}{},
		Errors:    []string{},
	}
	oldData, _ := json.Marshal(oldCP)
	os.WriteFile(filepath.Join(cm.checkpointsDir, oldCP.ID+".json"), oldData, 0644)

	// Create recent checkpoint (1 day ago)
	recent := time.Now().Add(-24 * time.Hour).UTC().Format(time.RFC3339)
	recentCP := Checkpoint{
		ID:        uuid.New().String(),
		Phase:     "recent",
		Timestamp: recent,
		State:     map[string]interface{}{},
		Errors:    []string{},
	}
	recentData, _ := json.Marshal(recentCP)
	os.WriteFile(filepath.Join(cm.checkpointsDir, recentCP.ID+".json"), recentData, 0644)

	// Delete checkpoints older than 2 days
	deleted, failed := cm.CleanupByAge(2)

	if deleted != 1 {
		t.Errorf("Expected 1 deleted, got %d", deleted)
	}
	if failed != 0 {
		t.Errorf("Expected 0 failed, got %d", failed)
	}

	// Verify old checkpoint was deleted and recent remains
	if _, err := os.Stat(filepath.Join(cm.checkpointsDir, oldCP.ID+".json")); !os.IsNotExist(err) {
		t.Errorf("Old checkpoint should be deleted")
	}
	if _, err := os.Stat(filepath.Join(cm.checkpointsDir, recentCP.ID+".json")); os.IsNotExist(err) {
		t.Errorf("Recent checkpoint should remain")
	}
}

// TestCleanupByAge_InvalidJSON tests handling of invalid JSON.
// REQ_003.4: Skips files with invalid JSON (counts in failed)
func TestCleanupByAge_InvalidJSON(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	os.MkdirAll(cm.checkpointsDir, 0755)

	// Write invalid JSON file
	os.WriteFile(filepath.Join(cm.checkpointsDir, "invalid.json"), []byte("not json"), 0644)

	deleted, failed := cm.CleanupByAge(0)

	// Should count as failed
	if failed != 1 {
		t.Errorf("Expected 1 failed for invalid JSON, got %d", failed)
	}
	if deleted != 0 {
		t.Errorf("Expected 0 deleted, got %d", deleted)
	}
}

// TestCleanupByAge_NegativeDays tests handling of negative days.
// REQ_003.4: Negative days parameter is treated as 0
func TestCleanupByAge_NegativeDays(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	os.MkdirAll(cm.checkpointsDir, 0755)

	// Create checkpoint
	cp := Checkpoint{
		ID:        uuid.New().String(),
		Phase:     "test",
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		State:     map[string]interface{}{},
		Errors:    []string{},
	}
	data, _ := json.Marshal(cp)
	os.WriteFile(filepath.Join(cm.checkpointsDir, cp.ID+".json"), data, 0644)

	// Call with negative days (should be treated as 0, deleting all)
	deleted, failed := cm.CleanupByAge(-5)

	// Should delete the checkpoint
	if deleted != 1 {
		t.Errorf("Expected 1 deleted with negative days, got %d", deleted)
	}
	if failed != 0 {
		t.Errorf("Expected 0 failed, got %d", failed)
	}
}

// TestCleanupAll_NoDirectory tests return 0,0 when directory doesn't exist.
// REQ_003.5: Gracefully handles missing checkpoints directory
func TestCleanupAll_NoDirectory(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	deleted, failed := cm.CleanupAll()

	if deleted != 0 || failed != 0 {
		t.Errorf("Expected (0, 0) when directory doesn't exist, got (%d, %d)", deleted, failed)
	}
}

// TestCleanupAll_DeletesAllCheckpoints tests deletion of all checkpoints.
// REQ_003.5: CleanupAll() deletes all *.json files
func TestCleanupAll_DeletesAllCheckpoints(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	os.MkdirAll(cm.checkpointsDir, 0755)

	// Create multiple checkpoints
	for i := 0; i < 3; i++ {
		cp := Checkpoint{
			ID:        uuid.New().String(),
			Phase:     "test",
			Timestamp: time.Now().UTC().Format(time.RFC3339),
			State:     map[string]interface{}{},
			Errors:    []string{},
		}
		data, _ := json.Marshal(cp)
		os.WriteFile(filepath.Join(cm.checkpointsDir, cp.ID+".json"), data, 0644)
	}

	deleted, failed := cm.CleanupAll()

	if deleted != 3 {
		t.Errorf("Expected 3 deleted, got %d", deleted)
	}
	if failed != 0 {
		t.Errorf("Expected 0 failed, got %d", failed)
	}

	// Verify all files deleted
	files, _ := filepath.Glob(filepath.Join(cm.checkpointsDir, "*.json"))
	if len(files) != 0 {
		t.Errorf("Expected no checkpoint files remaining, got %d", len(files))
	}
}

// TestCleanupAll_DoesNotDeleteDirectory tests directory is not deleted.
// REQ_003.5: Does NOT delete the checkpoints directory itself
func TestCleanupAll_DoesNotDeleteDirectory(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	os.MkdirAll(cm.checkpointsDir, 0755)

	// Create checkpoint
	cp := Checkpoint{
		ID:        uuid.New().String(),
		Phase:     "test",
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		State:     map[string]interface{}{},
		Errors:    []string{},
	}
	data, _ := json.Marshal(cp)
	os.WriteFile(filepath.Join(cm.checkpointsDir, cp.ID+".json"), data, 0644)

	cm.CleanupAll()

	// Verify directory still exists
	if _, err := os.Stat(cm.checkpointsDir); os.IsNotExist(err) {
		t.Errorf("Checkpoints directory should not be deleted")
	}
}

// TestCleanupAll_DoesNotDeleteNonJSON tests non-JSON files are not deleted.
// REQ_003.5: Does NOT delete non-JSON files in the directory
func TestCleanupAll_DoesNotDeleteNonJSON(t *testing.T) {
	tmpDir := t.TempDir()
	cm := NewCheckpointManager(tmpDir)

	os.MkdirAll(cm.checkpointsDir, 0755)

	// Create non-JSON file
	txtFile := filepath.Join(cm.checkpointsDir, "readme.txt")
	os.WriteFile(txtFile, []byte("readme"), 0644)

	// Create JSON checkpoint
	cp := Checkpoint{
		ID:        uuid.New().String(),
		Phase:     "test",
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		State:     map[string]interface{}{},
		Errors:    []string{},
	}
	data, _ := json.Marshal(cp)
	os.WriteFile(filepath.Join(cm.checkpointsDir, cp.ID+".json"), data, 0644)

	deleted, _ := cm.CleanupAll()

	// Should only delete JSON file
	if deleted != 1 {
		t.Errorf("Expected 1 deleted (JSON only), got %d", deleted)
	}

	// Verify txt file still exists
	if _, err := os.Stat(txtFile); os.IsNotExist(err) {
		t.Errorf("Non-JSON file should not be deleted")
	}
}
