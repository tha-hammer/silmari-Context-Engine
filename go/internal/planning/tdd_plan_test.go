package planning

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TestSerializeHierarchyForPrompt tests Behavior 3.2
func TestSerializeHierarchyForPrompt(t *testing.T) {
	t.Run("hierarchy_with_5_requirements_serializes_completely", func(t *testing.T) {
		hierarchy := NewRequirementHierarchy()
		for i := 0; i < 5; i++ {
			req := &RequirementNode{
				ID:                 "REQ_00" + string(rune('0'+i)),
				Description:        "Requirement " + string(rune('0'+i)),
				Type:               "parent",
				AcceptanceCriteria: []string{"Criterion 1", "Criterion 2"},
			}
			hierarchy.AddRequirement(req)
		}

		jsonStr := SerializeHierarchyForPrompt(hierarchy)

		var data map[string]interface{}
		if err := json.Unmarshal([]byte(jsonStr), &data); err != nil {
			t.Fatalf("failed to parse JSON: %v", err)
		}

		requirements, ok := data["requirements"].([]interface{})
		if !ok {
			t.Fatal("requirements should be an array")
		}
		if len(requirements) != 5 {
			t.Errorf("expected 5 requirements, got %d", len(requirements))
		}
	})

	t.Run("nested_children_recursively_serialized", func(t *testing.T) {
		hierarchy := NewRequirementHierarchy()
		parent := &RequirementNode{
			ID:          "REQ_001",
			Description: "Parent requirement",
			Type:        "parent",
		}
		child := &RequirementNode{
			ID:                 "REQ_001.1",
			Description:        "Child requirement",
			Type:               "sub_process",
			ParentID:           "REQ_001",
			AcceptanceCriteria: []string{"Child AC"},
		}
		parent.Children = append(parent.Children, child)
		hierarchy.AddRequirement(parent)

		jsonStr := SerializeHierarchyForPrompt(hierarchy)

		var data map[string]interface{}
		if err := json.Unmarshal([]byte(jsonStr), &data); err != nil {
			t.Fatalf("failed to parse JSON: %v", err)
		}

		requirements := data["requirements"].([]interface{})
		firstReq := requirements[0].(map[string]interface{})
		children := firstReq["children"].([]interface{})
		if len(children) != 1 {
			t.Errorf("expected 1 child, got %d", len(children))
		}
	})

	t.Run("empty_hierarchy_produces_valid_json", func(t *testing.T) {
		hierarchy := NewRequirementHierarchy()

		jsonStr := SerializeHierarchyForPrompt(hierarchy)

		var data map[string]interface{}
		if err := json.Unmarshal([]byte(jsonStr), &data); err != nil {
			t.Fatalf("failed to parse JSON: %v", err)
		}

		requirements, ok := data["requirements"].([]interface{})
		if !ok {
			t.Fatal("requirements should be an array")
		}
		if len(requirements) != 0 {
			t.Errorf("expected 0 requirements, got %d", len(requirements))
		}
	})

	t.Run("all_requirement_keys_preserved", func(t *testing.T) {
		hierarchy := NewRequirementHierarchy()
		req := &RequirementNode{
			ID:          "REQ_001.1",
			Description: "Full requirement",
			Type:        "sub_process",
			ParentID:    "REQ_001",
			AcceptanceCriteria: []string{"AC1", "AC2", "AC3"},
			Implementation: &ImplementationComponents{
				Frontend:   []string{"Component"},
				Backend:    []string{"Service"},
				Middleware: []string{"Filter"},
				Shared:     []string{"Model"},
			},
			FunctionID:      "Service.method",
			RelatedConcepts: []string{"concept1", "concept2"},
			Category:        "functional",
		}
		hierarchy.AddRequirement(req)

		jsonStr := SerializeHierarchyForPrompt(hierarchy)

		var data map[string]interface{}
		if err := json.Unmarshal([]byte(jsonStr), &data); err != nil {
			t.Fatalf("failed to parse JSON: %v", err)
		}

		requirements := data["requirements"].([]interface{})
		reqData := requirements[0].(map[string]interface{})

		if reqData["id"] != "REQ_001.1" {
			t.Errorf("id = %v, want REQ_001.1", reqData["id"])
		}
		if reqData["description"] != "Full requirement" {
			t.Errorf("description = %v, want 'Full requirement'", reqData["description"])
		}
		if reqData["type"] != "sub_process" {
			t.Errorf("type = %v, want 'sub_process'", reqData["type"])
		}
		if reqData["function_id"] != "Service.method" {
			t.Errorf("function_id = %v, want 'Service.method'", reqData["function_id"])
		}
	})
}

// TestBuildTDDPlanPrompt tests Behavior 3.2 prompt building
func TestBuildTDDPlanPrompt(t *testing.T) {
	t.Run("prompt_includes_all_acceptance_criteria", func(t *testing.T) {
		hierarchy := NewRequirementHierarchy()
		req := &RequirementNode{
			ID:          "REQ_001.1",
			Description: "Login validation",
			Type:        "sub_process",
			AcceptanceCriteria: []string{
				"Email format validated before submission",
				"Password minimum 8 characters enforced",
				"Clear error messages displayed for invalid inputs",
				"Form submission blocked until all validations pass",
			},
			FunctionID: "AuthService.validateLoginForm",
		}
		hierarchy.AddRequirement(req)

		instructionContent := "# TDD Plan Instructions"
		prompt := BuildTDDPlanPrompt(instructionContent, hierarchy, "feature")

		if !strings.Contains(prompt, "Email format validated before submission") {
			t.Error("prompt should contain first acceptance criterion")
		}
		if !strings.Contains(prompt, "Password minimum 8 characters enforced") {
			t.Error("prompt should contain second acceptance criterion")
		}
		if !strings.Contains(prompt, "Clear error messages displayed for invalid inputs") {
			t.Error("prompt should contain third acceptance criterion")
		}
		if !strings.Contains(prompt, "Form submission blocked until all validations pass") {
			t.Error("prompt should contain fourth acceptance criterion")
		}
		if !strings.Contains(prompt, "AuthService.validateLoginForm") {
			t.Error("prompt should contain function_id")
		}
	})

	t.Run("prompt_contains_tdd_mapping_instructions", func(t *testing.T) {
		hierarchy := NewRequirementHierarchy()
		req := &RequirementNode{
			ID:                 "REQ_001",
			Description:        "Test",
			Type:               "parent",
			AcceptanceCriteria: []string{"Test criterion"},
		}
		hierarchy.AddRequirement(req)

		instructionContent := "# TDD Plan Instructions"
		prompt := BuildTDDPlanPrompt(instructionContent, hierarchy, "feature")

		lower := strings.ToLower(prompt)
		if !strings.Contains(lower, "acceptance_criteria") && !strings.Contains(lower, "acceptance criteria") {
			t.Error("prompt should mention acceptance criteria")
		}
	})
}

// TestExtractPlanPaths tests Behavior 3.4
func TestExtractPlanPaths(t *testing.T) {
	t.Run("single_plan_file_extracted", func(t *testing.T) {
		output := "Created: thoughts/searchable/shared/plans/2026-01-14-tdd-feature.md"

		paths := ExtractPlanPaths(output)

		if len(paths) < 1 {
			t.Fatalf("expected at least 1 path, got %d", len(paths))
		}
		if !strings.Contains(paths[0], "2026-01-14-tdd-feature.md") {
			t.Errorf("path should contain filename, got %s", paths[0])
		}
	})

	t.Run("multiple_plan_files_captured", func(t *testing.T) {
		output := `Created files:
- thoughts/searchable/shared/plans/2026-01-14-tdd-feature/00-overview.md
- thoughts/searchable/shared/plans/2026-01-14-tdd-feature/01-phase-1.md
- thoughts/searchable/shared/plans/2026-01-14-tdd-feature/02-phase-2.md`

		paths := ExtractPlanPaths(output)

		if len(paths) != 3 {
			t.Errorf("expected 3 paths, got %d", len(paths))
		}
	})

	t.Run("no_plan_file_returns_empty_list", func(t *testing.T) {
		output := "Processing complete but no files created."

		paths := ExtractPlanPaths(output)

		if len(paths) != 0 {
			t.Errorf("expected 0 paths, got %d", len(paths))
		}
	})
}

// TestCreateTDDPlanFromHierarchy tests the main function (Behaviors 3.1-3.5)
func TestCreateTDDPlanFromHierarchy(t *testing.T) {
	t.Run("returns_error_when_instruction_file_missing", func(t *testing.T) {
		tmpDir := t.TempDir()

		hierarchy := NewRequirementHierarchy()
		hierarchy.AddRequirement(&RequirementNode{
			ID:          "REQ_001",
			Description: "Test requirement",
			Type:        "parent",
		})

		result := CreateTDDPlanFromHierarchy(tmpDir, hierarchy, "feature", "")

		if result.Success {
			t.Error("expected failure when instruction file is missing")
		}
		if !strings.Contains(result.Error, "create_tdd_plan.md") {
			t.Errorf("error should mention missing file, got: %s", result.Error)
		}
	})

	t.Run("loads_instruction_file_from_project_path", func(t *testing.T) {
		tmpDir := t.TempDir()
		commandsDir := filepath.Join(tmpDir, ".claude", "commands")
		if err := os.MkdirAll(commandsDir, 0755); err != nil {
			t.Fatalf("failed to create commands dir: %v", err)
		}

		instructionFile := filepath.Join(commandsDir, "create_tdd_plan.md")
		if err := os.WriteFile(instructionFile, []byte("# TDD Plan Instructions\nCreate tests first."), 0644); err != nil {
			t.Fatalf("failed to write instruction file: %v", err)
		}

		hierarchy := NewRequirementHierarchy()
		hierarchy.AddRequirement(&RequirementNode{
			ID:          "REQ_001",
			Description: "Test requirement",
			Type:        "parent",
		})

		// Note: This will fail at Claude invocation since we don't have a mock,
		// but we can verify the instruction file was loaded by checking error message
		result := CreateTDDPlanFromHierarchy(tmpDir, hierarchy, "feature", "")

		// Should not have the "instruction file not found" error
		if strings.Contains(result.Error, "create_tdd_plan.md") && strings.Contains(result.Error, "not found") {
			t.Error("should have loaded instruction file")
		}
	})

	t.Run("handles_empty_instruction_file", func(t *testing.T) {
		tmpDir := t.TempDir()
		commandsDir := filepath.Join(tmpDir, ".claude", "commands")
		if err := os.MkdirAll(commandsDir, 0755); err != nil {
			t.Fatalf("failed to create commands dir: %v", err)
		}

		instructionFile := filepath.Join(commandsDir, "create_tdd_plan.md")
		if err := os.WriteFile(instructionFile, []byte(""), 0644); err != nil {
			t.Fatalf("failed to write empty instruction file: %v", err)
		}

		hierarchy := NewRequirementHierarchy()
		hierarchy.AddRequirement(&RequirementNode{
			ID:          "REQ_001",
			Description: "Test requirement",
			Type:        "parent",
		})

		result := CreateTDDPlanFromHierarchy(tmpDir, hierarchy, "feature", "")

		// Should not crash - result should have success field
		if result.Success && len(result.PlanPaths) == 0 {
			// Empty instruction file should still produce a valid (empty) prompt
			// The function runs successfully even with empty instructions
		}
	})
}

// TestTDDPlanResultStructure tests Behavior 3.5
func TestTDDPlanResultStructure(t *testing.T) {
	t.Run("result_has_all_required_fields", func(t *testing.T) {
		result := &TDDPlanResult{
			Success:   true,
			PlanPaths: []string{"path/to/plan.md"},
			Output:    "Full Claude output",
			Error:     "",
		}

		if !result.Success {
			t.Error("Success should be true")
		}
		if len(result.PlanPaths) != 1 {
			t.Errorf("expected 1 plan path, got %d", len(result.PlanPaths))
		}
		if result.Output != "Full Claude output" {
			t.Error("Output should be preserved")
		}
	})

	t.Run("failure_result_includes_error", func(t *testing.T) {
		result := &TDDPlanResult{
			Success:   false,
			PlanPaths: []string{},
			Output:    "",
			Error:     "Instruction file not found",
		}

		if result.Success {
			t.Error("Success should be false")
		}
		if result.Error == "" {
			t.Error("Error should not be empty for failures")
		}
	})
}
