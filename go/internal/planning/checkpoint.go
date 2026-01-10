// Package planning provides checkpoint management for pipeline resume functionality.
package planning

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/google/uuid"
)

// Checkpoint represents a pipeline state checkpoint.
type Checkpoint struct {
	ID        string                 `json:"id"`
	Phase     string                 `json:"phase"`
	Timestamp string                 `json:"timestamp"`
	State     map[string]interface{} `json:"state"`
	Errors    []string               `json:"errors"`
	GitCommit string                 `json:"git_commit"`
}

// CheckpointManager handles checkpoint creation, detection, and cleanup.
type CheckpointManager struct {
	projectPath     string
	checkpointsDir  string
	checkpointsDirName string
}

// NewCheckpointManager creates a new checkpoint manager for the given project path.
func NewCheckpointManager(projectPath string) *CheckpointManager {
	checkpointsDirName := ".rlm-act-checkpoints"
	return &CheckpointManager{
		projectPath:     projectPath,
		checkpointsDir:  filepath.Join(projectPath, checkpointsDirName),
		checkpointsDirName: checkpointsDirName,
	}
}

// WriteCheckpoint creates a UUID-based checkpoint file in .rlm-act-checkpoints/*.json
// that captures complete pipeline state after each phase.
//
// REQ_003.1: Create UUID-based checkpoint files in .rlm-act-checkpoints/*
func (cm *CheckpointManager) WriteCheckpoint(state map[string]interface{}, phase string, errors []string) (string, error) {
	// Create checkpoints directory if it doesn't exist (mode 0755)
	if err := os.MkdirAll(cm.checkpointsDir, 0755); err != nil {
		return "", fmt.Errorf("failed to create checkpoints directory: %w", err)
	}

	// Generate UUID v4 for checkpoint filename
	checkpointID := uuid.New().String()
	checkpointFile := filepath.Join(cm.checkpointsDir, checkpointID+".json")

	// Get current git commit hash (40-character SHA-1) or empty string if not in git repo
	gitCommit := cm.getGitCommit()

	// Initialize errors array (empty array if no errors, not null)
	if errors == nil {
		errors = []string{}
	}

	// Create checkpoint structure
	checkpoint := Checkpoint{
		ID:        checkpointID,
		Phase:     phase,
		Timestamp: time.Now().UTC().Format(time.RFC3339), // RFC3339/ISO8601 format with Z suffix
		State:     state,
		Errors:    errors,
		GitCommit: gitCommit,
	}

	// Marshal to JSON
	data, err := json.MarshalIndent(checkpoint, "", "  ")
	if err != nil {
		return "", fmt.Errorf("failed to marshal checkpoint: %w", err)
	}

	// Write checkpoint file with mode 0644
	if err := os.WriteFile(checkpointFile, data, 0644); err != nil {
		return "", fmt.Errorf("failed to write checkpoint file: %w", err)
	}

	// Return absolute path to created checkpoint file
	absPath, err := filepath.Abs(checkpointFile)
	if err != nil {
		return checkpointFile, nil // Return relative path if abs fails
	}
	return absPath, nil
}

// getGitCommit retrieves the current git commit hash or returns empty string.
func (cm *CheckpointManager) getGitCommit() string {
	cmd := exec.Command("git", "rev-parse", "HEAD")
	cmd.Dir = cm.projectPath
	output, err := cmd.Output()
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(output))
}

// DetectResumableCheckpoint finds the most recent checkpoint based on timestamp field.
//
// REQ_003.3: Load and restore pipeline state from any checkpoint file
func (cm *CheckpointManager) DetectResumableCheckpoint() (*Checkpoint, error) {
	// Return nil if checkpoints directory doesn't exist
	if _, err := os.Stat(cm.checkpointsDir); os.IsNotExist(err) {
		return nil, nil
	}

	// Read all checkpoint files
	files, err := filepath.Glob(filepath.Join(cm.checkpointsDir, "*.json"))
	if err != nil {
		return nil, fmt.Errorf("failed to glob checkpoints: %w", err)
	}

	if len(files) == 0 {
		return nil, nil
	}

	var checkpoints []Checkpoint
	for _, file := range files {
		data, err := os.ReadFile(file)
		if err != nil {
			continue // Skip files that can't be read
		}

		var cp Checkpoint
		if err := json.Unmarshal(data, &cp); err != nil {
			continue // Skip invalid JSON files
		}

		checkpoints = append(checkpoints, cp)
	}

	if len(checkpoints) == 0 {
		return nil, nil
	}

	// Sort by timestamp descending (most recent first)
	sort.Slice(checkpoints, func(i, j int) bool {
		return checkpoints[i].Timestamp > checkpoints[j].Timestamp
	})

	return &checkpoints[0], nil
}

// LoadCheckpoint deserializes a checkpoint JSON file and returns the checkpoint.
//
// REQ_003.3: Load and restore pipeline state from any checkpoint file
func (cm *CheckpointManager) LoadCheckpoint(checkpointPath string) (*Checkpoint, error) {
	// Check if file exists
	if _, err := os.Stat(checkpointPath); os.IsNotExist(err) {
		return nil, fmt.Errorf("checkpoint file does not exist: %s", checkpointPath)
	}

	// Read file
	data, err := os.ReadFile(checkpointPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read checkpoint file: %w", err)
	}

	// Parse JSON
	var cp Checkpoint
	if err := json.Unmarshal(data, &cp); err != nil {
		return nil, fmt.Errorf("invalid checkpoint JSON: %w", err)
	}

	// Validate required fields
	if cp.ID == "" || cp.Phase == "" || cp.Timestamp == "" {
		return nil, fmt.Errorf("checkpoint missing required fields (id, phase, or timestamp)")
	}

	return &cp, nil
}

// GetCheckpointAgeDays calculates age of checkpoint in days from timestamp field.
//
// REQ_003.3: Load and restore pipeline state from any checkpoint file
func (cm *CheckpointManager) GetCheckpointAgeDays(checkpoint *Checkpoint) int {
	if checkpoint.Timestamp == "" {
		return 0
	}

	// Parse timestamp (handles ISO8601 with Z suffix)
	timestamp, err := time.Parse(time.RFC3339, checkpoint.Timestamp)
	if err != nil {
		return 0
	}

	// Calculate age in days
	age := time.Since(timestamp)
	return int(age.Hours() / 24)
}

// CleanupByAge deletes all checkpoints with age >= specified days.
//
// REQ_003.4: Delete checkpoint files older than a specified number of days
func (cm *CheckpointManager) CleanupByAge(days int) (deletedCount int, failedCount int) {
	// Handle negative days parameter
	if days < 0 {
		days = 0
	}

	// Return 0, 0 if checkpoints directory doesn't exist
	if _, err := os.Stat(cm.checkpointsDir); os.IsNotExist(err) {
		return 0, 0
	}

	// Read all checkpoint files
	files, err := filepath.Glob(filepath.Join(cm.checkpointsDir, "*.json"))
	if err != nil {
		return 0, 0
	}

	for _, file := range files {
		data, err := os.ReadFile(file)
		if err != nil {
			failedCount++
			continue
		}

		var cp Checkpoint
		if err := json.Unmarshal(data, &cp); err != nil {
			failedCount++
			continue // Skip files with invalid JSON
		}

		// Skip files with missing or unparseable timestamps
		if cp.Timestamp == "" {
			continue
		}

		age := cm.GetCheckpointAgeDays(&cp)
		if age >= days {
			if err := os.Remove(file); err != nil {
				failedCount++
			} else {
				deletedCount++
			}
		}
	}

	return deletedCount, failedCount
}

// CleanupAll deletes all *.json files in .rlm-act-checkpoints/ directory.
//
// REQ_003.5: Delete all checkpoint files in the checkpoints directory
func (cm *CheckpointManager) CleanupAll() (deletedCount int, failedCount int) {
	// Return 0, 0 if checkpoints directory doesn't exist
	if _, err := os.Stat(cm.checkpointsDir); os.IsNotExist(err) {
		return 0, 0
	}

	// Read all *.json files
	files, err := filepath.Glob(filepath.Join(cm.checkpointsDir, "*.json"))
	if err != nil {
		return 0, 0
	}

	// Delete each file
	for _, file := range files {
		if err := os.Remove(file); err != nil {
			failedCount++
		} else {
			deletedCount++
		}
	}

	// Note: We do NOT delete the checkpoints directory itself

	return deletedCount, failedCount
}
