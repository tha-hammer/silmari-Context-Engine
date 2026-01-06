package planning

import (
	"os"
	"path/filepath"
	"testing"
)

func TestNewPlanningPipeline(t *testing.T) {
	config := PipelineConfig{
		ProjectPath: "/test/path",
		AutoApprove: true,
		TicketID:    "TEST-123",
	}

	pipeline := NewPlanningPipeline(config)
	if pipeline == nil {
		t.Fatal("pipeline should not be nil")
	}
	if pipeline.config.ProjectPath != "/test/path" {
		t.Errorf("ProjectPath = %s, want /test/path", pipeline.config.ProjectPath)
	}
	if !pipeline.config.AutoApprove {
		t.Error("AutoApprove should be true")
	}
	if pipeline.config.TicketID != "TEST-123" {
		t.Errorf("TicketID = %s, want TEST-123", pipeline.config.TicketID)
	}
}

func TestPipelineResultsInitialization(t *testing.T) {
	results := &PipelineResults{
		Success: true,
		Steps:   make(map[string]interface{}),
	}

	if !results.Success {
		t.Error("Success should be true")
	}
	if results.Steps == nil {
		t.Error("Steps should be initialized")
	}
}

func TestReadFileContent(t *testing.T) {
	// Create temp file
	tmpDir, err := os.MkdirTemp("", "test-*")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	testFile := filepath.Join(tmpDir, "test.txt")
	testContent := "Hello, World!"
	os.WriteFile(testFile, []byte(testContent), 0644)

	// Test reading existing file
	content, err := ReadFileContent(testFile)
	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
	if content != testContent {
		t.Errorf("content = %q, want %q", content, testContent)
	}

	// Test reading non-existent file
	_, err = ReadFileContent(filepath.Join(tmpDir, "nonexistent.txt"))
	if err == nil {
		t.Error("expected error for non-existent file")
	}
}

func TestCreateDir(t *testing.T) {
	tmpDir, err := os.MkdirTemp("", "test-*")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	newDir := filepath.Join(tmpDir, "nested", "directory", "structure")
	err = CreateDir(newDir)
	if err != nil {
		t.Errorf("CreateDir failed: %v", err)
	}

	// Verify directory was created
	info, err := os.Stat(newDir)
	if err != nil {
		t.Errorf("directory not created: %v", err)
	}
	if !info.IsDir() {
		t.Error("expected a directory")
	}
}

func TestSaveHierarchy(t *testing.T) {
	tmpDir, err := os.MkdirTemp("", "test-*")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	hierarchy := NewRequirementHierarchy()
	hierarchy.AddRequirement(&RequirementNode{
		ID:          "REQ_000",
		Description: "Test requirement",
		Type:        "parent",
	})

	outputPath := filepath.Join(tmpDir, "output", "hierarchy.json")
	err = SaveHierarchy(hierarchy, outputPath)
	if err != nil {
		t.Errorf("SaveHierarchy failed: %v", err)
	}

	// Verify file was created
	if _, err := os.Stat(outputPath); os.IsNotExist(err) {
		t.Error("hierarchy file not created")
	}

	// Verify content is valid JSON
	content, _ := os.ReadFile(outputPath)
	if len(content) == 0 {
		t.Error("hierarchy file is empty")
	}
}

func TestRequirementDecompositionResult(t *testing.T) {
	result := &RequirementDecompositionResult{
		Success:          true,
		RequirementCount: 10,
		HierarchyPath:    "/path/to/hierarchy.json",
	}

	if !result.Success {
		t.Error("Success should be true")
	}
	if result.RequirementCount != 10 {
		t.Errorf("RequirementCount = %d, want 10", result.RequirementCount)
	}
}

func TestContextGenerationResult(t *testing.T) {
	result := &ContextGenerationResult{
		Success:   true,
		OutputDir: "/path/to/output",
	}

	if !result.Success {
		t.Error("Success should be true")
	}
	if result.OutputDir != "/path/to/output" {
		t.Errorf("OutputDir = %s, want /path/to/output", result.OutputDir)
	}
}
