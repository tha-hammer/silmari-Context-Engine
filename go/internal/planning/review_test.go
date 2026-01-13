package planning

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestReviewStepEnum(t *testing.T) {
	tests := []struct {
		name     string
		step     ReviewStep
		wantStr  string
	}{
		{"contracts", StepContracts, "contracts"},
		{"interfaces", StepInterfaces, "interfaces"},
		{"promises", StepPromises, "promises"},
		{"data_models", StepDataModels, "data_models"},
		{"apis", StepAPIs, "apis"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.step.String(); got != tt.wantStr {
				t.Errorf("ReviewStep.String() = %v, want %v", got, tt.wantStr)
			}
		})
	}
}

func TestReviewStepFromString(t *testing.T) {
	tests := []struct {
		input   string
		want    ReviewStep
		wantErr bool
	}{
		{"contracts", StepContracts, false},
		{"CONTRACTS", StepContracts, false},
		{"interfaces", StepInterfaces, false},
		{"promises", StepPromises, false},
		{"data_models", StepDataModels, false},
		{"apis", StepAPIs, false},
		{"invalid", StepContracts, true},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			got, err := ReviewStepFromString(tt.input)
			if (err != nil) != tt.wantErr {
				t.Errorf("ReviewStepFromString() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr && got != tt.want {
				t.Errorf("ReviewStepFromString() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestAllReviewSteps(t *testing.T) {
	steps := AllReviewSteps()
	if len(steps) != 5 {
		t.Errorf("AllReviewSteps() returned %d steps, want 5", len(steps))
	}

	expectedOrder := []ReviewStep{
		StepContracts,
		StepInterfaces,
		StepPromises,
		StepDataModels,
		StepAPIs,
	}

	for i, expected := range expectedOrder {
		if steps[i] != expected {
			t.Errorf("AllReviewSteps()[%d] = %v, want %v", i, steps[i], expected)
		}
	}
}

func TestReviewStepNavigation(t *testing.T) {
	// Test Next()
	step := StepContracts
	next, err := step.Next()
	if err != nil {
		t.Errorf("StepContracts.Next() unexpected error: %v", err)
	}
	if next != StepInterfaces {
		t.Errorf("StepContracts.Next() = %v, want StepInterfaces", next)
	}

	// Test Next() at end
	step = StepAPIs
	_, err = step.Next()
	if err == nil {
		t.Error("StepAPIs.Next() expected error, got nil")
	}

	// Test Previous()
	step = StepInterfaces
	prev, err := step.Previous()
	if err != nil {
		t.Errorf("StepInterfaces.Previous() unexpected error: %v", err)
	}
	if prev != StepContracts {
		t.Errorf("StepInterfaces.Previous() = %v, want StepContracts", prev)
	}

	// Test Previous() at start
	step = StepContracts
	_, err = step.Previous()
	if err == nil {
		t.Error("StepContracts.Previous() expected error, got nil")
	}
}

func TestSeverityEnum(t *testing.T) {
	tests := []struct {
		severity Severity
		wantStr  string
		wantEmoji string
	}{
		{SeverityWellDefined, "well_defined", "✅"},
		{SeverityWarning, "warning", "⚠️"},
		{SeverityCritical, "critical", "❌"},
	}

	for _, tt := range tests {
		t.Run(tt.wantStr, func(t *testing.T) {
			if got := tt.severity.String(); got != tt.wantStr {
				t.Errorf("Severity.String() = %v, want %v", got, tt.wantStr)
			}
			if got := tt.severity.Emoji(); got != tt.wantEmoji {
				t.Errorf("Severity.Emoji() = %v, want %v", got, tt.wantEmoji)
			}
		})
	}
}

func TestSeverityFromString(t *testing.T) {
	tests := []struct {
		input   string
		want    Severity
		wantErr bool
	}{
		{"well_defined", SeverityWellDefined, false},
		{"ok", SeverityWellDefined, false},
		{"good", SeverityWellDefined, false},
		{"warning", SeverityWarning, false},
		{"warn", SeverityWarning, false},
		{"critical", SeverityCritical, false},
		{"error", SeverityCritical, false},
		{"fail", SeverityCritical, false},
		{"invalid", SeverityWellDefined, true},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			got, err := SeverityFromString(tt.input)
			if (err != nil) != tt.wantErr {
				t.Errorf("SeverityFromString() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr && got != tt.want {
				t.Errorf("SeverityFromString() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestSeverityCounts(t *testing.T) {
	counts := SeverityCounts{
		WellDefined: 10,
		Warning:     5,
		Critical:    2,
	}

	if total := counts.Total(); total != 17 {
		t.Errorf("SeverityCounts.Total() = %v, want 17", total)
	}

	if !counts.HasCritical() {
		t.Error("SeverityCounts.HasCritical() = false, want true")
	}

	counts.Critical = 0
	if counts.HasCritical() {
		t.Error("SeverityCounts.HasCritical() = true, want false")
	}
}

func TestContractAnalysisResult(t *testing.T) {
	result := NewContractAnalysisResult()

	if result.Step != StepContracts {
		t.Errorf("NewContractAnalysisResult().Step = %v, want StepContracts", result.Step)
	}

	// Add findings and verify counts
	result.AddFinding(ContractFinding{
		ReviewFinding: ReviewFinding{Severity: SeverityWellDefined},
	})
	result.AddFinding(ContractFinding{
		ReviewFinding: ReviewFinding{Severity: SeverityWarning},
	})
	result.AddFinding(ContractFinding{
		ReviewFinding: ReviewFinding{Severity: SeverityCritical},
	})

	if result.Counts.WellDefined != 1 {
		t.Errorf("WellDefined count = %d, want 1", result.Counts.WellDefined)
	}
	if result.Counts.Warning != 1 {
		t.Errorf("Warning count = %d, want 1", result.Counts.Warning)
	}
	if result.Counts.Critical != 1 {
		t.Errorf("Critical count = %d, want 1", result.Counts.Critical)
	}
}

func TestContractAnalyzer(t *testing.T) {
	analyzer := &ContractAnalyzer{}

	req := &RequirementNode{
		ID:          "REQ_001",
		Description: "Test requirement",
		Type:        "parent",
		AcceptanceCriteria: []string{
			"Function accepts input string and returns processed result",
			"Must throw error on invalid input",
			"Ensures output is always valid",
		},
		TestableProperties: []*TestableProperty{
			{Criterion: "Test invariant", PropertyType: "invariant"},
		},
	}

	resultI, err := analyzer.Analyze(nil, PhaseImplementation, req)
	if err != nil {
		t.Fatalf("ContractAnalyzer.Analyze() error = %v", err)
	}

	result, ok := resultI.(*ContractAnalysisResult)
	if !ok {
		t.Fatalf("Expected *ContractAnalysisResult, got %T", resultI)
	}

	if result.RequirementID != "REQ_001" {
		t.Errorf("RequirementID = %v, want REQ_001", result.RequirementID)
	}

	// Should have findings for each criterion and property
	if len(result.Findings) < 4 {
		t.Errorf("Expected at least 4 findings, got %d", len(result.Findings))
	}

	// Verify contract types are detected
	contractTypes := make(map[string]bool)
	for _, f := range result.Findings {
		if f.ContractType != "" {
			contractTypes[f.ContractType] = true
		}
	}

	if !contractTypes["input"] && !contractTypes["output"] {
		// At least one of input/output should be detected
		t.Log("Warning: Expected to detect input or output contract types")
	}
}

func TestInterfaceAnalyzer(t *testing.T) {
	analyzer := &InterfaceAnalyzer{}

	req := &RequirementNode{
		ID:          "REQ_001",
		Description: "Implement user_handler with plugin interface",
		Type:        "parent",
		Implementation: &ImplementationComponents{
			Backend: []string{"UserHandler", "auth_provider"},
			Shared:  []string{"UserModel"},
		},
	}

	resultI, err := analyzer.Analyze(nil, PhaseImplementation, req)
	if err != nil {
		t.Fatalf("InterfaceAnalyzer.Analyze() error = %v", err)
	}

	result, ok := resultI.(*InterfaceAnalysisResult)
	if !ok {
		t.Fatalf("Expected *InterfaceAnalysisResult, got %T", resultI)
	}

	// Should detect public methods
	if result.PublicMethodCount < 3 {
		t.Errorf("PublicMethodCount = %d, want at least 3", result.PublicMethodCount)
	}

	// Should detect extension points (handler, provider)
	if result.ExtensionPoints == 0 {
		t.Error("Expected to detect extension points")
	}

	// Check naming convention detection
	hasSnakeCase := false
	hasPascalCase := false
	for _, f := range result.Findings {
		if f.NamingConvention == "snake_case" {
			hasSnakeCase = true
		}
		if f.NamingConvention == "PascalCase" {
			hasPascalCase = true
		}
	}

	if !hasSnakeCase {
		t.Error("Expected to detect snake_case naming convention")
	}
	if !hasPascalCase {
		t.Error("Expected to detect PascalCase naming convention")
	}
}

func TestPromiseAnalyzer(t *testing.T) {
	analyzer := &PromiseAnalyzer{}

	req := &RequirementNode{
		ID:          "REQ_001",
		Description: "Async operation with mutex synchronization",
		Type:        "parent",
		AcceptanceCriteria: []string{
			"Operation is idempotent and produces same result",
			"Async processing uses mutex for synchronization",
			"Network request has timeout handling",
			"Context cancellation is supported",
		},
		TestableProperties: []*TestableProperty{
			{Criterion: "Operation is idempotent", PropertyType: "idempotence"},
		},
	}

	resultI, err := analyzer.Analyze(nil, PhaseImplementation, req)
	if err != nil {
		t.Fatalf("PromiseAnalyzer.Analyze() error = %v", err)
	}

	result, ok := resultI.(*PromiseAnalysisResult)
	if !ok {
		t.Fatalf("Expected *PromiseAnalysisResult, got %T", resultI)
	}

	if result.IdempotentOperations == 0 {
		t.Error("Expected to detect idempotent operations")
	}

	// Check for promise type detection
	hasIdempotency := false
	hasCancellation := false
	hasTimeout := false
	for _, f := range result.Findings {
		if f.PromiseType == "idempotency" {
			hasIdempotency = true
		}
		if f.HasCancellation {
			hasCancellation = true
		}
		if f.HasTimeout {
			hasTimeout = true
		}
	}

	if !hasIdempotency {
		t.Error("Expected to detect idempotency promise")
	}
	if !hasCancellation {
		t.Error("Expected to detect cancellation handling")
	}
	if !hasTimeout {
		t.Error("Expected to detect timeout handling")
	}
}

func TestDataModelAnalyzer(t *testing.T) {
	analyzer := &DataModelAnalyzer{}

	req := &RequirementNode{
		ID:          "REQ_001",
		Description: "One-to-many relationship with required field validation",
		Type:        "parent",
		Implementation: &ImplementationComponents{
			Shared: []string{"UserList", "RoleMap"},
		},
	}

	resultI, err := analyzer.Analyze(nil, PhaseImplementation, req)
	if err != nil {
		t.Fatalf("DataModelAnalyzer.Analyze() error = %v", err)
	}

	result, ok := resultI.(*DataModelAnalysisResult)
	if !ok {
		t.Fatalf("Expected *DataModelAnalysisResult, got %T", resultI)
	}

	if result.StructCount < 2 {
		t.Errorf("StructCount = %d, want at least 2", result.StructCount)
	}

	// Check for relationship detection
	hasOneToMany := false
	hasNToM := false
	hasValidation := false
	for _, f := range result.Findings {
		if f.RelationshipType == "1:N" {
			hasOneToMany = true
		}
		if f.RelationshipType == "N:M" {
			hasNToM = true
		}
		if f.HasValidation {
			hasValidation = true
		}
	}

	if !hasOneToMany {
		t.Error("Expected to detect 1:N relationship")
	}
	if !hasNToM {
		t.Error("Expected to detect N:M relationship (from RoleMap)")
	}
	if !hasValidation {
		t.Error("Expected to detect validation rules")
	}
}

func TestAPIAnalyzer(t *testing.T) {
	analyzer := &APIAnalyzer{}

	req := &RequirementNode{
		ID:          "REQ_001",
		Description: "REST API endpoint",
		Type:        "parent",
		Implementation: &ImplementationComponents{
			Backend: []string{"GetUserHandler", "PostOrderEndpoint"},
		},
		AcceptanceCriteria: []string{
			"GET /api/v1/users returns 200 OK with JSON response",
			"POST /api/v1/orders returns 201 Created",
			"Deprecated /api/v1/legacy endpoint has sunset header",
		},
	}

	resultI, err := analyzer.Analyze(nil, PhaseImplementation, req)
	if err != nil {
		t.Fatalf("APIAnalyzer.Analyze() error = %v", err)
	}

	result, ok := resultI.(*APIAnalysisResult)
	if !ok {
		t.Fatalf("Expected *APIAnalysisResult, got %T", resultI)
	}

	if result.EndpointCount < 2 {
		t.Errorf("EndpointCount = %d, want at least 2", result.EndpointCount)
	}

	// Check for HTTP method and endpoint detection
	hasGET := false
	hasPOST := false
	hasEndpoint := false
	hasVersioning := false
	for _, f := range result.Findings {
		if f.HTTPMethod == "GET" {
			hasGET = true
		}
		if f.HTTPMethod == "POST" {
			hasPOST = true
		}
		if f.Endpoint != "" {
			hasEndpoint = true
		}
		if f.VersioningScheme == "url" {
			hasVersioning = true
		}
	}

	if !hasGET {
		t.Error("Expected to detect GET method")
	}
	if !hasPOST {
		t.Error("Expected to detect POST method")
	}
	if !hasEndpoint {
		t.Error("Expected to detect endpoint patterns")
	}
	if !hasVersioning {
		t.Error("Expected to detect URL versioning")
	}
}

func TestRunReviewWithPlanFile(t *testing.T) {
	// Create a temporary plan file
	tmpDir := t.TempDir()
	planPath := filepath.Join(tmpDir, "test-plan.md")

	planContent := `# Test Plan

## Overview
This is a test plan for the review functionality.

## Requirements
- Implement feature X
- Test feature X
`
	if err := os.WriteFile(planPath, []byte(planContent), 0644); err != nil {
		t.Fatalf("Failed to write test plan: %v", err)
	}

	config := ReviewConfig{
		ProjectPath: tmpDir,
		PlanPath:    planPath,
		AllPhases:   false,
		Phase:       "implementation",
		Step:        "contracts",
	}

	result := RunReview(config)

	if !result.Success {
		t.Errorf("RunReview() failed: %v", result.Error)
	}

	if len(result.ReviewedPhases) != 1 {
		t.Errorf("ReviewedPhases = %d, want 1", len(result.ReviewedPhases))
	}

	if len(result.ReviewedSteps) != 1 {
		t.Errorf("ReviewedSteps = %d, want 1", len(result.ReviewedSteps))
	}

	if result.Output == "" {
		t.Error("Expected non-empty output")
	}
}

func TestRunReviewAllPhasesAllSteps(t *testing.T) {
	// Create a temporary plan file
	tmpDir := t.TempDir()
	planPath := filepath.Join(tmpDir, "full-plan.md")

	planContent := `# Full Test Plan

## Overview
Comprehensive test plan.
`
	if err := os.WriteFile(planPath, []byte(planContent), 0644); err != nil {
		t.Fatalf("Failed to write test plan: %v", err)
	}

	config := ReviewConfig{
		ProjectPath: tmpDir,
		PlanPath:    planPath,
		AllPhases:   true,
	}

	result := RunReview(config)

	if !result.Success {
		t.Errorf("RunReview() failed: %v", result.Error)
	}

	// Should review all 6 phases
	if len(result.ReviewedPhases) != 6 {
		t.Errorf("ReviewedPhases = %d, want 6", len(result.ReviewedPhases))
	}

	// Should run all 5 steps
	if len(result.ReviewedSteps) != 5 {
		t.Errorf("ReviewedSteps = %d, want 5", len(result.ReviewedSteps))
	}
}

func TestRunReviewWithOutput(t *testing.T) {
	// Create temporary directories
	tmpDir := t.TempDir()
	planPath := filepath.Join(tmpDir, "plan.md")
	outputPath := filepath.Join(tmpDir, "review-output.json")

	planContent := `# Test Plan

## Requirement
Test requirement
`
	if err := os.WriteFile(planPath, []byte(planContent), 0644); err != nil {
		t.Fatalf("Failed to write test plan: %v", err)
	}

	config := ReviewConfig{
		ProjectPath: tmpDir,
		PlanPath:    planPath,
		OutputPath:  outputPath,
		Phase:       "research",
		Step:        "interfaces",
	}

	result := RunReview(config)

	if !result.Success {
		t.Errorf("RunReview() failed: %v", result.Error)
	}

	// Verify output file was created
	if _, err := os.Stat(outputPath); os.IsNotExist(err) {
		t.Error("Output file was not created")
	}

	// Read and verify output content
	content, err := os.ReadFile(outputPath)
	if err != nil {
		t.Fatalf("Failed to read output file: %v", err)
	}

	if !strings.Contains(string(content), "success") {
		t.Error("Output file should contain success field")
	}
}

func TestRunReviewInvalidPlanPath(t *testing.T) {
	config := ReviewConfig{
		ProjectPath: "/tmp",
		PlanPath:    "/nonexistent/plan.md",
	}

	result := RunReview(config)

	if result.Success {
		t.Error("RunReview() should fail with invalid plan path")
	}

	if result.FailedAt != "load_plan" {
		t.Errorf("FailedAt = %v, want load_plan", result.FailedAt)
	}
}

func TestRunReviewInvalidPhase(t *testing.T) {
	tmpDir := t.TempDir()
	planPath := filepath.Join(tmpDir, "plan.md")

	if err := os.WriteFile(planPath, []byte("# Test"), 0644); err != nil {
		t.Fatalf("Failed to write test plan: %v", err)
	}

	config := ReviewConfig{
		ProjectPath: tmpDir,
		PlanPath:    planPath,
		Phase:       "invalid_phase",
	}

	result := RunReview(config)

	if result.Success {
		t.Error("RunReview() should fail with invalid phase")
	}

	if result.FailedAt != "parse_phase" {
		t.Errorf("FailedAt = %v, want parse_phase", result.FailedAt)
	}
}

func TestRunReviewInvalidStep(t *testing.T) {
	tmpDir := t.TempDir()
	planPath := filepath.Join(tmpDir, "plan.md")

	if err := os.WriteFile(planPath, []byte("# Test"), 0644); err != nil {
		t.Fatalf("Failed to write test plan: %v", err)
	}

	config := ReviewConfig{
		ProjectPath: tmpDir,
		PlanPath:    planPath,
		Step:        "invalid_step",
	}

	result := RunReview(config)

	if result.Success {
		t.Error("RunReview() should fail with invalid step")
	}

	if result.FailedAt != "parse_step" {
		t.Errorf("FailedAt = %v, want parse_step", result.FailedAt)
	}
}

func TestStepAnalysisResultInterface(t *testing.T) {
	// Verify all result types implement the interface
	var _ StepAnalysisResult = &ContractAnalysisResult{}
	var _ StepAnalysisResult = &InterfaceAnalysisResult{}
	var _ StepAnalysisResult = &PromiseAnalysisResult{}
	var _ StepAnalysisResult = &DataModelAnalysisResult{}
	var _ StepAnalysisResult = &APIAnalysisResult{}

	// Test GetStep and GetCounts methods
	contractResult := NewContractAnalysisResult()
	contractResult.Counts.WellDefined = 5

	if contractResult.GetStep() != StepContracts {
		t.Error("ContractAnalysisResult.GetStep() wrong")
	}
	if contractResult.GetCounts().WellDefined != 5 {
		t.Error("ContractAnalysisResult.GetCounts() wrong")
	}
}

func TestReviewStepJSONMarshaling(t *testing.T) {
	step := StepInterfaces

	// Marshal
	data, err := step.MarshalJSON()
	if err != nil {
		t.Fatalf("MarshalJSON() error = %v", err)
	}

	expected := `"interfaces"`
	if string(data) != expected {
		t.Errorf("MarshalJSON() = %s, want %s", string(data), expected)
	}

	// Unmarshal
	var unmarshaled ReviewStep
	if err := unmarshaled.UnmarshalJSON(data); err != nil {
		t.Fatalf("UnmarshalJSON() error = %v", err)
	}

	if unmarshaled != StepInterfaces {
		t.Errorf("UnmarshalJSON() = %v, want StepInterfaces", unmarshaled)
	}
}

func TestSeverityJSONMarshaling(t *testing.T) {
	sev := SeverityWarning

	// Marshal
	data, err := sev.MarshalJSON()
	if err != nil {
		t.Fatalf("MarshalJSON() error = %v", err)
	}

	expected := `"warning"`
	if string(data) != expected {
		t.Errorf("MarshalJSON() = %s, want %s", string(data), expected)
	}

	// Unmarshal
	var unmarshaled Severity
	if err := unmarshaled.UnmarshalJSON(data); err != nil {
		t.Fatalf("UnmarshalJSON() error = %v", err)
	}

	if unmarshaled != SeverityWarning {
		t.Errorf("UnmarshalJSON() = %v, want SeverityWarning", unmarshaled)
	}
}

func TestReviewRequirementTree(t *testing.T) {
	parent := &RequirementNode{
		ID:          "REQ_001",
		Description: "Parent requirement",
		Type:        "parent",
		AcceptanceCriteria: []string{"Must work correctly"},
	}

	child := &RequirementNode{
		ID:          "REQ_001.1",
		Description: "Child requirement",
		Type:        "sub_process",
		ParentID:    "REQ_001",
		AcceptanceCriteria: []string{"Must integrate with parent"},
	}

	parent.Children = []*RequirementNode{child}

	analyzers := map[ReviewStep]Analyzer{
		StepContracts: &ContractAnalyzer{},
	}

	results, err := reviewRequirementTree(parent, PhaseImplementation, analyzers)
	if err != nil {
		t.Fatalf("reviewRequirementTree() error = %v", err)
	}

	if len(results) != 1 {
		t.Errorf("Expected 1 result, got %d", len(results))
	}

	if _, ok := results[StepContracts]; !ok {
		t.Error("Expected StepContracts result")
	}
}

func TestLoadPlanDocument(t *testing.T) {
	tmpDir := t.TempDir()
	planPath := filepath.Join(tmpDir, "test-plan.md")

	content := `# My Test Plan

## Overview
This is a test plan.

## Phase 1
Do something.
`
	if err := os.WriteFile(planPath, []byte(content), 0644); err != nil {
		t.Fatalf("Failed to write plan: %v", err)
	}

	doc, err := LoadPlanDocument(planPath)
	if err != nil {
		t.Fatalf("LoadPlanDocument() error = %v", err)
	}

	if doc.Title != "My Test Plan" {
		t.Errorf("Title = %v, want 'My Test Plan'", doc.Title)
	}

	if doc.Path != planPath {
		t.Errorf("Path = %v, want %v", doc.Path, planPath)
	}
}

func TestExtractEndpoint(t *testing.T) {
	tests := []struct {
		input string
		want  string
	}{
		{"GET /api/v1/users returns 200", "/api/v1/users"},
		{"POST /api/orders creates order", "/api/orders"},
		{"The /health endpoint returns OK", "/health"},
		{"No endpoint here", ""},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			got := extractEndpoint(tt.input)
			if got != tt.want {
				t.Errorf("extractEndpoint(%q) = %q, want %q", tt.input, got, tt.want)
			}
		})
	}
}
