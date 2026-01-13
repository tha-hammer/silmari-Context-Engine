package planning

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
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

// ============================================================================
// Phase 5 Tests: Three-level severity classification (REQ_004)
// ============================================================================

// REQ_004.1 Tests: Well-Defined classification
func TestMarkWellDefined(t *testing.T) {
	f := &ReviewFinding{
		ID:          "TEST-001",
		Description: "Test finding",
		Severity:    SeverityWarning, // Start with different severity
	}

	// Test marking as well-defined
	result := f.MarkWellDefined()

	if result != f {
		t.Error("MarkWellDefined should return the same finding")
	}
	if f.Severity != SeverityWellDefined {
		t.Errorf("Severity = %v, want %v", f.Severity, SeverityWellDefined)
	}
	if f.Reason != "" {
		t.Error("MarkWellDefined should clear Reason")
	}
	if f.ResolutionNeeded != "" {
		t.Error("MarkWellDefined should clear ResolutionNeeded")
	}
}

func TestIsWellDefined(t *testing.T) {
	f := &ReviewFinding{ID: "TEST-001", Severity: SeverityWellDefined}
	if !f.IsWellDefined() {
		t.Error("IsWellDefined() = false, want true")
	}

	f.Severity = SeverityWarning
	if f.IsWellDefined() {
		t.Error("IsWellDefined() = true, want false")
	}
}

func TestWellDefinedStoredInSlice(t *testing.T) {
	cf := NewCategorizedFindings()

	f := &ReviewFinding{ID: "WELL-001", Severity: SeverityWellDefined}
	cf.AddFinding(f)

	if len(cf.WellDefined) != 1 {
		t.Errorf("WellDefined slice length = %d, want 1", len(cf.WellDefined))
	}
	if cf.WellDefined[0] != "WELL-001" {
		t.Errorf("WellDefined[0] = %v, want WELL-001", cf.WellDefined[0])
	}
}

func TestWellDefinedCountPerStep(t *testing.T) {
	result := NewReviewStepResult(StepContracts, PhaseImplementation)

	// Add well-defined findings
	result.AddFinding(ReviewFinding{ID: "WD-001", Severity: SeverityWellDefined})
	result.AddFinding(ReviewFinding{ID: "WD-002", Severity: SeverityWellDefined})
	result.AddFinding(ReviewFinding{ID: "WD-003", Severity: SeverityWellDefined})

	if result.Counts.WellDefined != 3 {
		t.Errorf("WellDefined count = %d, want 3", result.Counts.WellDefined)
	}
}

// REQ_004.2 Tests: Warning classification
func TestMarkWarning(t *testing.T) {
	f := &ReviewFinding{
		ID:          "TEST-001",
		Description: "Test finding",
		Severity:    SeverityWellDefined,
	}

	reason := "Missing type specification"
	result := f.MarkWarning(reason)

	if result != f {
		t.Error("MarkWarning should return the same finding")
	}
	if f.Severity != SeverityWarning {
		t.Errorf("Severity = %v, want %v", f.Severity, SeverityWarning)
	}
	if f.Reason != reason {
		t.Errorf("Reason = %v, want %v", f.Reason, reason)
	}
	if f.ResolutionNeeded != "" {
		t.Error("MarkWarning should clear ResolutionNeeded")
	}
}

func TestIsWarning(t *testing.T) {
	f := &ReviewFinding{ID: "TEST-001", Severity: SeverityWarning}
	if !f.IsWarning() {
		t.Error("IsWarning() = false, want true")
	}

	f.Severity = SeverityCritical
	if f.IsWarning() {
		t.Error("IsWarning() = true, want false")
	}
}

func TestWarningStoredInSlice(t *testing.T) {
	cf := NewCategorizedFindings()

	f := &ReviewFinding{ID: "WARN-001", Severity: SeverityWarning, Reason: "Test reason"}
	cf.AddFinding(f)

	if len(cf.Warnings) != 1 {
		t.Errorf("Warnings slice length = %d, want 1", len(cf.Warnings))
	}
	if cf.Warnings[0] != "WARN-001" {
		t.Errorf("Warnings[0] = %v, want WARN-001", cf.Warnings[0])
	}
}

func TestWarningDoesNotBlockProgression(t *testing.T) {
	result := NewReviewStepResult(StepContracts, PhaseImplementation)

	// Add warning findings
	result.AddFinding(ReviewFinding{ID: "WARN-001", Severity: SeverityWarning})
	result.AddFinding(ReviewFinding{ID: "WARN-002", Severity: SeverityWarning})

	// Warnings should NOT block progression
	if !result.CanProceed {
		t.Error("CanProceed = false, want true (warnings should not block)")
	}
}

// REQ_004.3 Tests: Critical classification
func TestMarkCritical(t *testing.T) {
	f := &ReviewFinding{
		ID:          "TEST-001",
		Description: "Test finding",
		Severity:    SeverityWellDefined,
	}

	resolution := "Define explicit input/output contracts"
	result := f.MarkCritical(resolution)

	if result != f {
		t.Error("MarkCritical should return the same finding")
	}
	if f.Severity != SeverityCritical {
		t.Errorf("Severity = %v, want %v", f.Severity, SeverityCritical)
	}
	if f.ResolutionNeeded != resolution {
		t.Errorf("ResolutionNeeded = %v, want %v", f.ResolutionNeeded, resolution)
	}
}

func TestIsCritical(t *testing.T) {
	f := &ReviewFinding{ID: "TEST-001", Severity: SeverityCritical}
	if !f.IsCritical() {
		t.Error("IsCritical() = false, want true")
	}

	f.Severity = SeverityWarning
	if f.IsCritical() {
		t.Error("IsCritical() = true, want false")
	}
}

func TestCriticalStoredInSlice(t *testing.T) {
	cf := NewCategorizedFindings()

	f := &ReviewFinding{ID: "CRIT-001", Severity: SeverityCritical, ResolutionNeeded: "Fix now"}
	cf.AddFinding(f)

	if len(cf.Critical) != 1 {
		t.Errorf("Critical slice length = %d, want 1", len(cf.Critical))
	}
	if cf.Critical[0] != "CRIT-001" {
		t.Errorf("Critical[0] = %v, want CRIT-001", cf.Critical[0])
	}
}

func TestCriticalBlocksProgression(t *testing.T) {
	result := NewReviewStepResult(StepContracts, PhaseImplementation)

	// Initially can proceed
	if !result.CanProceed {
		t.Error("Initial CanProceed should be true")
	}

	// Add a critical finding
	result.AddFinding(ReviewFinding{ID: "CRIT-001", Severity: SeverityCritical})

	// Critical should BLOCK progression (REQ_004.3)
	if result.CanProceed {
		t.Error("CanProceed = true, want false (critical should block)")
	}
}

func TestCannotCompleteWithCritical(t *testing.T) {
	cf := NewCategorizedFindings()
	cf.AddFinding(&ReviewFinding{ID: "CRIT-001", Severity: SeverityCritical})

	if cf.CanProceed() {
		t.Error("CanProceed() = true, want false (cannot complete with critical)")
	}
}

func TestCategorizedFindingsCanProceed(t *testing.T) {
	cf := NewCategorizedFindings()

	// No findings - can proceed
	if !cf.CanProceed() {
		t.Error("Empty CategorizedFindings should CanProceed")
	}

	// Add well-defined - can proceed
	cf.AddFinding(&ReviewFinding{ID: "WD-001", Severity: SeverityWellDefined})
	if !cf.CanProceed() {
		t.Error("WellDefined only should CanProceed")
	}

	// Add warning - still can proceed
	cf.AddFinding(&ReviewFinding{ID: "WARN-001", Severity: SeverityWarning})
	if !cf.CanProceed() {
		t.Error("Warnings should not block CanProceed")
	}

	// Add critical - cannot proceed
	cf.AddFinding(&ReviewFinding{ID: "CRIT-001", Severity: SeverityCritical})
	if cf.CanProceed() {
		t.Error("Critical should block CanProceed")
	}
}

// REQ_004.4 Tests: Recommendation generation
func TestGenerateRecommendations(t *testing.T) {
	findings := []ReviewFinding{
		{ID: "WD-001", Description: "Well defined", Severity: SeverityWellDefined},
		{ID: "WARN-001", Description: "Warning issue", Severity: SeverityWarning, Reason: "Partial spec"},
		{ID: "CRIT-001", Description: "Critical issue", Severity: SeverityCritical, ResolutionNeeded: "Fix contract"},
	}

	result := GenerateRecommendations(findings)

	// Should skip well-defined
	if result.SkippedCount != 1 {
		t.Errorf("SkippedCount = %d, want 1", result.SkippedCount)
	}

	// Should have recommendations for warning and critical
	if len(result.Recommendations) != 2 {
		t.Errorf("Recommendations count = %d, want 2", len(result.Recommendations))
	}

	if result.CriticalCount != 1 {
		t.Errorf("CriticalCount = %d, want 1", result.CriticalCount)
	}

	if result.WarningCount != 1 {
		t.Errorf("WarningCount = %d, want 1", result.WarningCount)
	}
}

func TestRecommendationsPrioritized(t *testing.T) {
	findings := []ReviewFinding{
		{ID: "WARN-001", Description: "Warning first", Severity: SeverityWarning},
		{ID: "CRIT-001", Description: "Critical second", Severity: SeverityCritical},
		{ID: "WARN-002", Description: "Warning third", Severity: SeverityWarning},
	}

	result := GenerateRecommendations(findings)

	// Critical should be first (REQ_004.4 - prioritized order)
	if len(result.Recommendations) < 1 {
		t.Fatal("Expected at least 1 recommendation")
	}

	if result.Recommendations[0].Severity != SeverityCritical {
		t.Error("First recommendation should be Critical")
	}

	// Remaining should be warnings
	for i := 1; i < len(result.Recommendations); i++ {
		if result.Recommendations[i].Severity != SeverityWarning {
			t.Errorf("Recommendation[%d] should be Warning", i)
		}
	}
}

func TestWellDefinedExcludedFromRecommendations(t *testing.T) {
	findings := []ReviewFinding{
		{ID: "WD-001", Description: "Well defined 1", Severity: SeverityWellDefined},
		{ID: "WD-002", Description: "Well defined 2", Severity: SeverityWellDefined},
	}

	result := GenerateRecommendations(findings)

	// No recommendations for well-defined
	if len(result.Recommendations) != 0 {
		t.Errorf("Should have 0 recommendations, got %d", len(result.Recommendations))
	}

	if result.SkippedCount != 2 {
		t.Errorf("SkippedCount = %d, want 2", result.SkippedCount)
	}
}

func TestWarningRecommendationContainsReason(t *testing.T) {
	findings := []ReviewFinding{
		{ID: "WARN-001", Description: "Missing types", Severity: SeverityWarning, Reason: "Partial specification"},
	}

	result := GenerateRecommendations(findings)

	if len(result.Recommendations) != 1 {
		t.Fatal("Expected 1 recommendation")
	}

	if !strings.Contains(result.Recommendations[0].Message, "Partial specification") {
		t.Error("Warning recommendation should contain reason")
	}
}

func TestCriticalRecommendationContainsResolution(t *testing.T) {
	findings := []ReviewFinding{
		{ID: "CRIT-001", Description: "Undefined contract", Severity: SeverityCritical, ResolutionNeeded: "Add input/output types"},
	}

	result := GenerateRecommendations(findings)

	if len(result.Recommendations) != 1 {
		t.Fatal("Expected 1 recommendation")
	}

	rec := result.Recommendations[0]
	if rec.SuggestedFix != "Add input/output types" {
		t.Errorf("SuggestedFix = %v, want 'Add input/output types'", rec.SuggestedFix)
	}
	if !rec.IsMandatory {
		t.Error("Critical recommendation should be mandatory")
	}
}

func TestCriticalRecommendationIsMandatory(t *testing.T) {
	findings := []ReviewFinding{
		{ID: "CRIT-001", Description: "Critical", Severity: SeverityCritical},
	}

	result := GenerateRecommendations(findings)

	if len(result.Recommendations) != 1 {
		t.Fatal("Expected 1 recommendation")
	}

	if !result.Recommendations[0].IsMandatory {
		t.Error("Critical recommendations must be mandatory")
	}
}

func TestWarningRecommendationNotMandatory(t *testing.T) {
	findings := []ReviewFinding{
		{ID: "WARN-001", Description: "Warning", Severity: SeverityWarning},
	}

	result := GenerateRecommendations(findings)

	if len(result.Recommendations) != 1 {
		t.Fatal("Expected 1 recommendation")
	}

	if result.Recommendations[0].IsMandatory {
		t.Error("Warning recommendations should not be mandatory")
	}
}

func TestEmptyRecommendationListValid(t *testing.T) {
	// Empty when no Warning or Critical
	findings := []ReviewFinding{
		{ID: "WD-001", Description: "Well defined", Severity: SeverityWellDefined},
	}

	result := GenerateRecommendations(findings)

	if result.Recommendations == nil {
		t.Error("Recommendations should not be nil")
	}
	if len(result.Recommendations) != 0 {
		t.Errorf("Expected empty recommendations, got %d", len(result.Recommendations))
	}
}

// SeverityClassifier tests
func TestSeverityClassifier(t *testing.T) {
	sc := NewSeverityClassifier()

	f1 := &ReviewFinding{ID: "F1", Description: "Test 1"}
	f2 := &ReviewFinding{ID: "F2", Description: "Test 2"}
	f3 := &ReviewFinding{ID: "F3", Description: "Test 3"}

	sc.ClassifyAsWellDefined(f1)
	sc.ClassifyAsWarning(f2, "Test reason")
	sc.ClassifyAsCritical(f3, "Fix this")

	counts := sc.GetCounts()
	if counts.WellDefined != 1 {
		t.Errorf("WellDefined = %d, want 1", counts.WellDefined)
	}
	if counts.Warning != 1 {
		t.Errorf("Warning = %d, want 1", counts.Warning)
	}
	if counts.Critical != 1 {
		t.Errorf("Critical = %d, want 1", counts.Critical)
	}

	// Should not proceed with critical
	if sc.CanProceed() {
		t.Error("CanProceed should be false with critical findings")
	}
}

func TestClassifyRequirementRecursive(t *testing.T) {
	parent := &RequirementNode{
		ID:          "REQ_001",
		Description: "Parent with input and output contracts",
		AcceptanceCriteria: []string{
			"Accepts input parameters",
			"Returns processed output",
		},
	}

	child := &RequirementNode{
		ID:          "REQ_001.1",
		Description: "Child requirement",
		ParentID:    "REQ_001",
		// No acceptance criteria - will be warning
	}

	parent.Children = []*RequirementNode{child}

	sc := NewSeverityClassifier()
	ClassifyRequirementRecursive(parent, sc)

	counts := sc.GetCounts()
	// Parent is well-defined (has contracts), child is warning (partial)
	if counts.WellDefined < 1 {
		t.Errorf("Expected at least 1 well-defined, got %d", counts.WellDefined)
	}
	if counts.Warning < 1 {
		t.Errorf("Expected at least 1 warning, got %d", counts.Warning)
	}
}

func TestIsRequirementWellDefined(t *testing.T) {
	tests := []struct {
		name string
		req  *RequirementNode
		want bool
	}{
		{
			name: "nil requirement",
			req:  nil,
			want: false,
		},
		{
			name: "empty description",
			req:  &RequirementNode{ID: "R1", Description: ""},
			want: false,
		},
		{
			name: "no criteria",
			req:  &RequirementNode{ID: "R1", Description: "Test"},
			want: false,
		},
		{
			name: "no contracts in criteria",
			req: &RequirementNode{
				ID:                 "R1",
				Description:        "Test",
				AcceptanceCriteria: []string{"Does something"},
			},
			want: false,
		},
		{
			name: "has input contract",
			req: &RequirementNode{
				ID:                 "R1",
				Description:        "Test",
				AcceptanceCriteria: []string{"Accepts input string"},
			},
			want: true,
		},
		{
			name: "has output contract",
			req: &RequirementNode{
				ID:                 "R1",
				Description:        "Test",
				AcceptanceCriteria: []string{"Returns processed result"},
			},
			want: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := isRequirementWellDefined(tt.req)
			if got != tt.want {
				t.Errorf("isRequirementWellDefined() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestHasRequirementCriticalIssues(t *testing.T) {
	tests := []struct {
		name string
		req  *RequirementNode
		want bool
	}{
		{
			name: "nil requirement",
			req:  nil,
			want: true,
		},
		{
			name: "empty description",
			req:  &RequirementNode{ID: "R1", Description: ""},
			want: true,
		},
		{
			name: "contradictory - always/never",
			req:  &RequirementNode{ID: "R1", Description: "Must always return and never fail"},
			want: true,
		},
		{
			name: "non-contradictory - must do different things",
			req:  &RequirementNode{ID: "R1", Description: "System requires input validation"},
			want: false, // Clear non-contradictory requirement
		},
		{
			name: "valid requirement",
			req:  &RequirementNode{ID: "R1", Description: "Process input data"},
			want: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := hasRequirementCriticalIssues(tt.req)
			if got != tt.want {
				t.Errorf("hasRequirementCriticalIssues() = %v, want %v", got, tt.want)
			}
		})
	}
}

// ReviewStepResult tests
func TestReviewStepResult(t *testing.T) {
	result := NewReviewStepResult(StepContracts, PhaseImplementation)

	if result.Step != StepContracts {
		t.Errorf("Step = %v, want StepContracts", result.Step)
	}
	if result.Phase != PhaseImplementation {
		t.Errorf("Phase = %v, want PhaseImplementation", result.Phase)
	}
	if !result.CanProceed {
		t.Error("Initial CanProceed should be true")
	}
	if result.Categorized == nil {
		t.Error("Categorized should be initialized")
	}
}

func TestReviewStepResultAddFinding(t *testing.T) {
	result := NewReviewStepResult(StepContracts, PhaseImplementation)

	result.AddFinding(ReviewFinding{ID: "WD-001", Severity: SeverityWellDefined})
	result.AddFinding(ReviewFinding{ID: "WARN-001", Severity: SeverityWarning})

	if result.Counts.WellDefined != 1 {
		t.Errorf("WellDefined count = %d, want 1", result.Counts.WellDefined)
	}
	if result.Counts.Warning != 1 {
		t.Errorf("Warning count = %d, want 1", result.Counts.Warning)
	}
	if len(result.Categorized.WellDefined) != 1 {
		t.Error("Categorized WellDefined should have 1 item")
	}
	if len(result.Categorized.Warnings) != 1 {
		t.Error("Categorized Warnings should have 1 item")
	}
}

func TestReviewStepResultGenerateRecommendations(t *testing.T) {
	result := NewReviewStepResult(StepContracts, PhaseImplementation)

	result.AddFinding(ReviewFinding{ID: "WD-001", Severity: SeverityWellDefined})
	result.AddFinding(ReviewFinding{ID: "WARN-001", Severity: SeverityWarning, Reason: "Test"})
	result.AddFinding(ReviewFinding{ID: "CRIT-001", Severity: SeverityCritical, ResolutionNeeded: "Fix"})

	result.GenerateRecommendationsForResult()

	if result.Recommendations == nil {
		t.Fatal("Recommendations should not be nil")
	}
	if len(result.Recommendations.Recommendations) != 2 {
		t.Errorf("Expected 2 recommendations, got %d", len(result.Recommendations.Recommendations))
	}
}

func TestFormatEmojiSummary(t *testing.T) {
	result := NewReviewStepResult(StepContracts, PhaseImplementation)
	result.AddFinding(ReviewFinding{ID: "WD-001", Severity: SeverityWellDefined})
	result.AddFinding(ReviewFinding{ID: "WARN-001", Severity: SeverityWarning})

	summary := result.FormatEmojiSummary()

	if !strings.Contains(summary, "✅") {
		t.Error("Summary should contain ✅ emoji")
	}
	if !strings.Contains(summary, "⚠️") {
		t.Error("Summary should contain ⚠️ emoji")
	}
	if !strings.Contains(summary, "contracts") {
		t.Error("Summary should contain step name")
	}
	if !strings.Contains(summary, "Can proceed") {
		t.Error("Summary should show can proceed status")
	}
}

func TestFormatEmojiSummaryBlocked(t *testing.T) {
	result := NewReviewStepResult(StepContracts, PhaseImplementation)
	result.AddFinding(ReviewFinding{ID: "CRIT-001", Severity: SeverityCritical})

	summary := result.FormatEmojiSummary()

	if !strings.Contains(summary, "BLOCKED") {
		t.Error("Summary should show BLOCKED status when critical")
	}
	if !strings.Contains(summary, "❌") {
		t.Error("Summary should contain ❌ emoji for critical")
	}
}

// JSON serialization tests for emoji output
func TestSeverityJSONWithEmoji(t *testing.T) {
	// Test that emoji symbols are available for display
	if SeverityWellDefined.Emoji() != "✅" {
		t.Errorf("WellDefined emoji = %v, want ✅", SeverityWellDefined.Emoji())
	}
	if SeverityWarning.Emoji() != "⚠️" {
		t.Errorf("Warning emoji = %v, want ⚠️", SeverityWarning.Emoji())
	}
	if SeverityCritical.Emoji() != "❌" {
		t.Errorf("Critical emoji = %v, want ❌", SeverityCritical.Emoji())
	}
}

// Integration tests
func TestSeverityClassificationIntegration(t *testing.T) {
	// Create a comprehensive test scenario
	result := NewReviewStepResult(StepContracts, PhaseImplementation)

	// Add various findings
	wellDefined := ReviewFinding{
		ID:          "WD-001",
		Component:   "AuthService",
		Description: "Authentication service with clear contracts",
		Severity:    SeverityWellDefined,
	}
	warning := ReviewFinding{
		ID:          "WARN-001",
		Component:   "UserService",
		Description: "User service missing type annotations",
		Severity:    SeverityWarning,
		Reason:      "Partial type specification",
	}
	critical := ReviewFinding{
		ID:               "CRIT-001",
		Component:        "PaymentService",
		Description:      "Payment service with undefined error handling",
		Severity:         SeverityCritical,
		ResolutionNeeded: "Define error contract for payment failures",
	}

	result.AddFinding(wellDefined)
	result.AddFinding(warning)
	result.AddFinding(critical)

	// Verify counts
	if result.Counts.WellDefined != 1 {
		t.Errorf("WellDefined = %d, want 1", result.Counts.WellDefined)
	}
	if result.Counts.Warning != 1 {
		t.Errorf("Warning = %d, want 1", result.Counts.Warning)
	}
	if result.Counts.Critical != 1 {
		t.Errorf("Critical = %d, want 1", result.Counts.Critical)
	}

	// Verify blocking behavior
	if result.CanProceed {
		t.Error("Should not proceed with critical finding")
	}

	// Generate and verify recommendations
	result.GenerateRecommendationsForResult()

	if result.Recommendations.SkippedCount != 1 {
		t.Errorf("SkippedCount = %d, want 1", result.Recommendations.SkippedCount)
	}
	if result.Recommendations.CriticalCount != 1 {
		t.Errorf("CriticalCount = %d, want 1", result.Recommendations.CriticalCount)
	}
	if result.Recommendations.WarningCount != 1 {
		t.Errorf("WarningCount = %d, want 1", result.Recommendations.WarningCount)
	}

	// Verify prioritization - critical first
	if result.Recommendations.Recommendations[0].Severity != SeverityCritical {
		t.Error("First recommendation should be critical")
	}
}

// =============================================================================
// REQ_005: Review Autonomy Modes Tests (Phase 6)
// =============================================================================

// TestReviewOrchestratorCheckpointMode tests checkpoint mode behavior.
// REQ_005.1: Checkpoint Mode - pause after each phase
func TestReviewOrchestratorCheckpointMode(t *testing.T) {
	ro := NewReviewOrchestrator(AutonomyCheckpoint, "/test/plan.md", "/test/project")

	phases := []PhaseType{
		PhaseResearch,
		PhaseDecomposition,
		PhaseTDDPlanning,
		PhaseMultiDoc,
		PhaseBeadsSync,
		PhaseImplementation,
	}

	// REQ_005.1: All 6 phases must be reviewed individually before pausing
	for _, phase := range phases {
		if !ro.ShouldPauseAfterPhase(phase) {
			t.Errorf("Checkpoint mode should pause after %s", phase.String())
		}
	}
}

// TestReviewOrchestratorCheckpointWritesAfterEachPhase tests checkpoint writes.
// REQ_005.1: Checkpoint must be saved after each phase completes
func TestReviewOrchestratorCheckpointWritesAfterEachPhase(t *testing.T) {
	ro := NewReviewOrchestrator(AutonomyCheckpoint, "/test/plan.md", "/test/project")

	phases := AllPhases()
	for _, phase := range phases {
		if !ro.ShouldWriteCheckpoint(phase) {
			t.Errorf("Checkpoint mode should write checkpoint after %s", phase.String())
		}
	}
}

// TestReviewOrchestratorBatchMode tests batch mode behavior.
// REQ_005.2: Batch Mode - group related phases together
func TestReviewOrchestratorBatchMode(t *testing.T) {
	ro := NewReviewOrchestrator(AutonomyBatch, "/test/plan.md", "/test/project")

	// REQ_005.2: Phases must be grouped into logical batches
	testCases := []struct {
		phase     PhaseType
		wantGroup string
	}{
		{PhaseResearch, ReviewBatchGroupPlanning},
		{PhaseDecomposition, ReviewBatchGroupPlanning},
		{PhaseTDDPlanning, ReviewBatchGroupTDD},
		{PhaseMultiDoc, ReviewBatchGroupTDD},
		{PhaseBeadsSync, ReviewBatchGroupExecution},
		{PhaseImplementation, ReviewBatchGroupExecution},
	}

	for _, tc := range testCases {
		if got := ro.GetReviewBatchGroup(tc.phase); got != tc.wantGroup {
			t.Errorf("GetReviewBatchGroup(%s) = %s, want %s", tc.phase.String(), got, tc.wantGroup)
		}
	}
}

// TestReviewOrchestratorBatchBoundaries tests batch boundary detection.
// REQ_005.2: Pause only at defined group boundaries
func TestReviewOrchestratorBatchBoundaries(t *testing.T) {
	ro := NewReviewOrchestrator(AutonomyBatch, "/test/plan.md", "/test/project")

	// REQ_005.2: System must not pause between phases within the same batch
	nonBoundaryPhases := []PhaseType{PhaseResearch, PhaseTDDPlanning, PhaseBeadsSync}
	for _, phase := range nonBoundaryPhases {
		if ro.ShouldPauseAfterPhase(phase) {
			t.Errorf("Batch mode should NOT pause after %s (within batch)", phase.String())
		}
	}

	// REQ_005.2: Pause only at defined group boundaries
	boundaryPhases := []PhaseType{PhaseDecomposition, PhaseMultiDoc, PhaseImplementation}
	for _, phase := range boundaryPhases {
		if !ro.ShouldPauseAfterPhase(phase) {
			t.Errorf("Batch mode should pause after %s (batch boundary)", phase.String())
		}
	}
}

// TestReviewOrchestratorBatchCheckpointBoundaries tests checkpoint writes at boundaries.
// REQ_005.2: Checkpoint is written at group boundaries, not at individual phase boundaries
func TestReviewOrchestratorBatchCheckpointBoundaries(t *testing.T) {
	ro := NewReviewOrchestrator(AutonomyBatch, "/test/plan.md", "/test/project")

	// No checkpoint within batches
	nonBoundaryPhases := []PhaseType{PhaseResearch, PhaseTDDPlanning, PhaseBeadsSync}
	for _, phase := range nonBoundaryPhases {
		if ro.ShouldWriteCheckpoint(phase) {
			t.Errorf("Batch mode should NOT write checkpoint after %s (within batch)", phase.String())
		}
	}

	// Checkpoint at batch boundaries
	boundaryPhases := []PhaseType{PhaseDecomposition, PhaseMultiDoc, PhaseImplementation}
	for _, phase := range boundaryPhases {
		if !ro.ShouldWriteCheckpoint(phase) {
			t.Errorf("Batch mode should write checkpoint after %s (batch boundary)", phase.String())
		}
	}
}

// TestReviewOrchestratorBatchGetPhasesInBatch tests batch phase grouping.
// REQ_005.2: Group 1 (Research, Decomposition), Group 2 (TDDPlanning, MultiDoc), Group 3 (BeadsSync, Implementation)
func TestReviewOrchestratorBatchGetPhasesInBatch(t *testing.T) {
	ro := NewReviewOrchestrator(AutonomyBatch, "/test/plan.md", "/test/project")

	// Planning batch
	planningBatch := ro.GetPhasesInBatch(PhaseResearch)
	if len(planningBatch) != 2 {
		t.Errorf("Planning batch should have 2 phases, got %d", len(planningBatch))
	}
	if planningBatch[0] != PhaseResearch || planningBatch[1] != PhaseDecomposition {
		t.Error("Planning batch should contain Research, Decomposition")
	}

	// TDD batch
	tddBatch := ro.GetPhasesInBatch(PhaseTDDPlanning)
	if len(tddBatch) != 2 {
		t.Errorf("TDD batch should have 2 phases, got %d", len(tddBatch))
	}
	if tddBatch[0] != PhaseTDDPlanning || tddBatch[1] != PhaseMultiDoc {
		t.Error("TDD batch should contain TDDPlanning, MultiDoc")
	}

	// Execution batch
	execBatch := ro.GetPhasesInBatch(PhaseImplementation)
	if len(execBatch) != 2 {
		t.Errorf("Execution batch should have 2 phases, got %d", len(execBatch))
	}
	if execBatch[0] != PhaseBeadsSync || execBatch[1] != PhaseImplementation {
		t.Error("Execution batch should contain BeadsSync, Implementation")
	}
}

// TestReviewOrchestratorFullyAutonomousMode tests fully autonomous mode behavior.
// REQ_005.3: Fully Autonomous Mode - no pauses
func TestReviewOrchestratorFullyAutonomousMode(t *testing.T) {
	ro := NewReviewOrchestrator(AutonomyFullyAutonomous, "/test/plan.md", "/test/project")

	phases := AllPhases()

	// REQ_005.3: All 6 phases must be reviewed sequentially without any pause
	for _, phase := range phases {
		if ro.ShouldPauseAfterPhase(phase) {
			t.Errorf("Fully autonomous mode should NOT pause after %s", phase.String())
		}
	}
}

// TestReviewOrchestratorFullyAutonomousWritesCheckpoints tests checkpoint writes for crash recovery.
// REQ_005.3: Checkpoint files are still written after each phase for crash recovery
func TestReviewOrchestratorFullyAutonomousWritesCheckpoints(t *testing.T) {
	ro := NewReviewOrchestrator(AutonomyFullyAutonomous, "/test/plan.md", "/test/project")

	phases := AllPhases()
	for _, phase := range phases {
		if !ro.ShouldWriteCheckpoint(phase) {
			t.Errorf("Fully autonomous mode should write checkpoint after %s for crash recovery", phase.String())
		}
	}
}

// TestReviewOrchestratorAccumulateResults tests result accumulation.
// REQ_005.2: Batch boundary checkpoint must aggregate all results
func TestReviewOrchestratorAccumulateResults(t *testing.T) {
	ro := NewReviewOrchestrator(AutonomyBatch, "/test/plan.md", "/test/project")

	// Add results for two phases
	result1 := PhaseReviewResult{
		Phase:  PhaseResearch,
		Counts: SeverityCounts{WellDefined: 5, Warning: 2, Critical: 0},
	}
	result2 := PhaseReviewResult{
		Phase:  PhaseDecomposition,
		Counts: SeverityCounts{WellDefined: 3, Warning: 1, Critical: 1},
	}

	ro.AccumulatePhaseResult(PhaseResearch, result1)
	ro.AccumulatePhaseResult(PhaseDecomposition, result2)

	accumulated := ro.GetAccumulatedResults()
	if len(accumulated) != 2 {
		t.Errorf("Should have 2 accumulated results, got %d", len(accumulated))
	}

	if accumulated[PhaseResearch].Counts.WellDefined != 5 {
		t.Error("Research result not properly accumulated")
	}
	if accumulated[PhaseDecomposition].Counts.Critical != 1 {
		t.Error("Decomposition result not properly accumulated")
	}

	// Test clearing
	ro.ClearAccumulatedResults()
	accumulated = ro.GetAccumulatedResults()
	if len(accumulated) != 0 {
		t.Errorf("Should have 0 accumulated results after clear, got %d", len(accumulated))
	}
}

// TestReviewCheckpointSaveAndLoad tests checkpoint persistence.
// REQ_005.4: Implement saveCheckpoint() function for review operations
func TestReviewCheckpointSaveAndLoad(t *testing.T) {
	// Create temp directory
	tmpDir, err := os.MkdirTemp("", "review-checkpoint-test")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	// Create a test plan file
	planPath := filepath.Join(tmpDir, "test-plan.md")
	if err := os.WriteFile(planPath, []byte("# Test Plan\n"), 0644); err != nil {
		t.Fatalf("Failed to create test plan: %v", err)
	}

	ro := NewReviewOrchestrator(AutonomyCheckpoint, planPath, tmpDir)

	// REQ_005.4: Save checkpoint with all required data
	completedPhases := []PhaseType{PhaseResearch, PhaseDecomposition}
	pendingPhases := []PhaseType{PhaseTDDPlanning, PhaseMultiDoc, PhaseBeadsSync, PhaseImplementation}
	phaseResults := map[PhaseType]PhaseReviewResult{
		PhaseResearch: {
			Phase:  PhaseResearch,
			Counts: SeverityCounts{WellDefined: 10, Warning: 3, Critical: 0},
		},
		PhaseDecomposition: {
			Phase:  PhaseDecomposition,
			Counts: SeverityCounts{WellDefined: 8, Warning: 1, Critical: 1},
		},
	}
	totalCounts := SeverityCounts{WellDefined: 18, Warning: 4, Critical: 1}

	checkpointPath, err := ro.SaveReviewCheckpoint(2, completedPhases, pendingPhases, phaseResults, totalCounts)
	if err != nil {
		t.Fatalf("SaveReviewCheckpoint failed: %v", err)
	}

	// REQ_005.4: Checkpoint file must exist
	if _, err := os.Stat(checkpointPath); os.IsNotExist(err) {
		t.Error("Checkpoint file was not created")
	}

	// REQ_005.4: Load and verify checkpoint
	loaded, err := LoadReviewCheckpoint(checkpointPath)
	if err != nil {
		t.Fatalf("LoadReviewCheckpoint failed: %v", err)
	}

	// Verify all fields
	if loaded.PlanPath != planPath {
		t.Errorf("PlanPath = %s, want %s", loaded.PlanPath, planPath)
	}
	if loaded.AutonomyMode != AutonomyCheckpoint {
		t.Errorf("AutonomyMode = %v, want checkpoint", loaded.AutonomyMode)
	}
	if loaded.CurrentPhaseIdx != 2 {
		t.Errorf("CurrentPhaseIdx = %d, want 2", loaded.CurrentPhaseIdx)
	}
	if len(loaded.CompletedPhases) != 2 {
		t.Errorf("CompletedPhases = %d, want 2", len(loaded.CompletedPhases))
	}
	if len(loaded.PendingPhases) != 4 {
		t.Errorf("PendingPhases = %d, want 4", len(loaded.PendingPhases))
	}
	if loaded.TotalCounts.Critical != 1 {
		t.Errorf("TotalCounts.Critical = %d, want 1", loaded.TotalCounts.Critical)
	}

	// REQ_005.4: Plan hash should be present
	if loaded.PlanHash == "" {
		t.Error("PlanHash should not be empty")
	}

	// REQ_005.4: Timestamps should be present
	if loaded.Timestamp == "" {
		t.Error("Timestamp should not be empty")
	}
	if loaded.StartedAt == "" {
		t.Error("StartedAt should not be empty")
	}
	if loaded.CumulativeSecs <= 0 {
		t.Error("CumulativeSecs should be positive")
	}
}

// TestReviewCheckpointPlanValidation tests plan hash validation.
// REQ_005.4: loadCheckpoint() must validate plan hash matches before allowing resume
func TestReviewCheckpointPlanValidation(t *testing.T) {
	// Create temp directory
	tmpDir, err := os.MkdirTemp("", "review-checkpoint-validation-test")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	// Create a test plan file
	planPath := filepath.Join(tmpDir, "test-plan.md")
	if err := os.WriteFile(planPath, []byte("# Test Plan\n"), 0644); err != nil {
		t.Fatalf("Failed to create test plan: %v", err)
	}

	ro := NewReviewOrchestrator(AutonomyCheckpoint, planPath, tmpDir)

	// Save checkpoint
	checkpointPath, err := ro.SaveReviewCheckpoint(0, nil, AllPhases(), nil, SeverityCounts{})
	if err != nil {
		t.Fatalf("SaveReviewCheckpoint failed: %v", err)
	}

	// Load checkpoint
	loaded, err := LoadReviewCheckpoint(checkpointPath)
	if err != nil {
		t.Fatalf("LoadReviewCheckpoint failed: %v", err)
	}

	// Validate without changes - should pass
	if err := ValidateCheckpointPlan(loaded); err != nil {
		t.Errorf("ValidateCheckpointPlan should pass for unchanged plan: %v", err)
	}

	// Modify the plan file
	if err := os.WriteFile(planPath, []byte("# Modified Test Plan\nNew content\n"), 0644); err != nil {
		t.Fatalf("Failed to modify test plan: %v", err)
	}

	// Validate after changes - should fail
	if err := ValidateCheckpointPlan(loaded); err == nil {
		t.Error("ValidateCheckpointPlan should fail for modified plan")
	}
}

// TestReviewCheckpointRotation tests checkpoint rotation.
// REQ_005.4: Old checkpoints must be rotated: keep last 5
func TestReviewCheckpointRotation(t *testing.T) {
	// Create temp directory
	tmpDir, err := os.MkdirTemp("", "review-checkpoint-rotation-test")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	// Create a test plan file
	planPath := filepath.Join(tmpDir, "test-plan.md")
	if err := os.WriteFile(planPath, []byte("# Test Plan\n"), 0644); err != nil {
		t.Fatalf("Failed to create test plan: %v", err)
	}

	// Create checkpoint directory and add 7 test checkpoint files manually
	// This avoids timing issues from fast consecutive saves
	checkpointDir := filepath.Join(tmpDir, ".context-engine", "checkpoints")
	if err := os.MkdirAll(checkpointDir, 0755); err != nil {
		t.Fatalf("Failed to create checkpoint dir: %v", err)
	}

	// Create 7 checkpoint files with different timestamps in filename
	for i := 0; i < 7; i++ {
		filename := filepath.Join(checkpointDir, "review-test-plan-2026010"+string(rune('0'+i))+"-120000.json")
		content := `{"id":"test-id","plan_path":"test","timestamp":"2026-01-0` + string(rune('0'+i)) + `T12:00:00Z"}`
		if err := os.WriteFile(filename, []byte(content), 0644); err != nil {
			t.Fatalf("Failed to create checkpoint file %d: %v", i, err)
		}
		// Set different mod times
		modTime := time.Now().Add(time.Duration(-7+i) * time.Hour)
		os.Chtimes(filename, modTime, modTime)
	}

	// Verify 7 files exist before rotation
	files, _ := filepath.Glob(filepath.Join(checkpointDir, "review-*.json"))
	if len(files) != 7 {
		t.Fatalf("Should have 7 checkpoints before rotation, got %d", len(files))
	}

	// Now save one more checkpoint which should trigger rotation
	ro := NewReviewOrchestrator(AutonomyCheckpoint, planPath, tmpDir)
	_, err = ro.SaveReviewCheckpoint(0, nil, AllPhases(), nil, SeverityCounts{})
	if err != nil {
		t.Fatalf("SaveReviewCheckpoint failed: %v", err)
	}

	// Count checkpoint files after rotation
	files, err = filepath.Glob(filepath.Join(checkpointDir, "review-*.json"))
	if err != nil {
		t.Fatalf("Failed to glob checkpoints: %v", err)
	}

	// REQ_005.4: Should keep only 5 checkpoints (rotated oldest ones)
	if len(files) != 5 {
		t.Errorf("Should have 5 checkpoints after rotation, got %d", len(files))
	}
}

// TestReviewCheckpointAtomicWrite tests atomic write pattern.
// REQ_005.4: Atomic write pattern must be used
func TestReviewCheckpointAtomicWrite(t *testing.T) {
	// Create temp directory
	tmpDir, err := os.MkdirTemp("", "review-checkpoint-atomic-test")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	// Create a test plan file
	planPath := filepath.Join(tmpDir, "test-plan.md")
	if err := os.WriteFile(planPath, []byte("# Test Plan\n"), 0644); err != nil {
		t.Fatalf("Failed to create test plan: %v", err)
	}

	ro := NewReviewOrchestrator(AutonomyCheckpoint, planPath, tmpDir)

	// Save checkpoint
	checkpointPath, err := ro.SaveReviewCheckpoint(0, nil, AllPhases(), nil, SeverityCounts{})
	if err != nil {
		t.Fatalf("SaveReviewCheckpoint failed: %v", err)
	}

	// Verify no temp files left behind
	checkpointDir := filepath.Join(tmpDir, ".context-engine", "checkpoints")
	tmpFiles, _ := filepath.Glob(filepath.Join(checkpointDir, "*.tmp"))
	if len(tmpFiles) > 0 {
		t.Error("Temp files should not be left behind after atomic write")
	}

	// REQ_005.4: Checkpoint file must be human-readable (pretty-printed JSON)
	data, err := os.ReadFile(checkpointPath)
	if err != nil {
		t.Fatalf("Failed to read checkpoint: %v", err)
	}

	// Pretty-printed JSON should have indentation
	if !strings.Contains(string(data), "\n  ") {
		t.Error("Checkpoint JSON should be pretty-printed with indentation")
	}
}

// TestReviewExitCode tests exit code determination.
// REQ_005.3: Exit code must reflect overall review health
func TestReviewExitCode(t *testing.T) {
	tests := []struct {
		name          string
		counts        SeverityCounts
		expectedCode  int
	}{
		{
			name:         "all pass",
			counts:       SeverityCounts{WellDefined: 10, Warning: 0, Critical: 0},
			expectedCode: 0,
		},
		{
			name:         "warnings only",
			counts:       SeverityCounts{WellDefined: 10, Warning: 3, Critical: 0},
			expectedCode: 1,
		},
		{
			name:         "critical issues",
			counts:       SeverityCounts{WellDefined: 10, Warning: 3, Critical: 1},
			expectedCode: 2,
		},
		{
			name:         "only critical",
			counts:       SeverityCounts{WellDefined: 0, Warning: 0, Critical: 5},
			expectedCode: 2,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := &ReviewResult{
				TotalCounts: tt.counts,
			}
			if got := GetReviewExitCode(result); got != tt.expectedCode {
				t.Errorf("GetReviewExitCode() = %d, want %d", got, tt.expectedCode)
			}
		})
	}
}

// TestReviewReportGeneration tests report generation.
// REQ_005.3: Final comprehensive report must include all findings
func TestReviewReportGeneration(t *testing.T) {
	result := &ReviewResult{
		Success:         true,
		TotalCounts:     SeverityCounts{WellDefined: 15, Warning: 5, Critical: 2},
		ReviewedPhases:  []PhaseType{PhaseResearch, PhaseDecomposition},
		ReviewedSteps:   AllReviewSteps(),
		DurationSeconds: 12.5,
		Timestamp:       time.Now(),
		PhaseResults: map[PhaseType]PhaseReviewResult{
			PhaseResearch: {
				Phase:  PhaseResearch,
				Counts: SeverityCounts{WellDefined: 10, Warning: 3, Critical: 1},
			},
			PhaseDecomposition: {
				Phase:  PhaseDecomposition,
				Counts: SeverityCounts{WellDefined: 5, Warning: 2, Critical: 1},
			},
		},
	}

	config := ReviewConfig{
		PlanPath:     "/test/plan.md",
		AutonomyMode: AutonomyFullyAutonomous,
	}

	report := GenerateReviewReport(result, config)

	// REQ_005.3: Report must include plan info
	if !strings.Contains(report, "/test/plan.md") {
		t.Error("Report should contain plan path")
	}

	// REQ_005.3: Report must include mode
	if !strings.Contains(report, "fully_autonomous") {
		t.Error("Report should contain autonomy mode")
	}

	// REQ_005.3: Report must include duration
	if !strings.Contains(report, "12.50 seconds") {
		t.Error("Report should contain duration")
	}

	// REQ_005.3: Critical findings must be prominently highlighted
	if !strings.Contains(report, "Critical Issues") {
		t.Error("Report should prominently highlight critical issues")
	}

	// REQ_005.3: Report must include phase results
	if !strings.Contains(report, "research") {
		t.Error("Report should contain phase results")
	}

	// REQ_005.3: Report must include steps executed
	if !strings.Contains(report, "contracts") {
		t.Error("Report should contain steps executed")
	}
}

// TestDetectReviewCheckpoint tests checkpoint detection.
func TestDetectReviewCheckpoint(t *testing.T) {
	// Create temp directory
	tmpDir, err := os.MkdirTemp("", "review-checkpoint-detect-test")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	// Create a test plan file
	planPath := filepath.Join(tmpDir, "test-plan.md")
	if err := os.WriteFile(planPath, []byte("# Test Plan\n"), 0644); err != nil {
		t.Fatalf("Failed to create test plan: %v", err)
	}

	// Initially no checkpoints should be found
	checkpoint, err := DetectReviewCheckpoint(tmpDir)
	if err != nil {
		t.Fatalf("DetectReviewCheckpoint should not error: %v", err)
	}
	if checkpoint != nil {
		t.Error("Should not find checkpoint when none exist")
	}

	// Create a checkpoint
	ro := NewReviewOrchestrator(AutonomyCheckpoint, planPath, tmpDir)
	_, err = ro.SaveReviewCheckpoint(1, []PhaseType{PhaseResearch}, AllPhases()[1:], nil, SeverityCounts{})
	if err != nil {
		t.Fatalf("SaveReviewCheckpoint failed: %v", err)
	}

	// Now should detect checkpoint
	checkpoint, err = DetectReviewCheckpoint(tmpDir)
	if err != nil {
		t.Fatalf("DetectReviewCheckpoint failed: %v", err)
	}
	if checkpoint == nil {
		t.Error("Should find checkpoint after creation")
	}
	if checkpoint.CurrentPhaseIdx != 1 {
		t.Errorf("Detected checkpoint should have phase index 1, got %d", checkpoint.CurrentPhaseIdx)
	}
}

// TestReviewOrchestratorIsReviewBatchBoundary tests batch boundary detection.
func TestReviewOrchestratorIsReviewBatchBoundary(t *testing.T) {
	ro := NewReviewOrchestrator(AutonomyBatch, "/test/plan.md", "/test/project")

	tests := []struct {
		phase      PhaseType
		isBoundary bool
	}{
		{PhaseResearch, false},
		{PhaseDecomposition, true},    // End of planning batch
		{PhaseTDDPlanning, false},
		{PhaseMultiDoc, true},         // End of TDD batch
		{PhaseBeadsSync, false},
		{PhaseImplementation, true},   // End of execution batch
	}

	for _, tt := range tests {
		t.Run(tt.phase.String(), func(t *testing.T) {
			if got := ro.IsReviewBatchBoundary(tt.phase); got != tt.isBoundary {
				t.Errorf("IsReviewBatchBoundary(%s) = %v, want %v", tt.phase.String(), got, tt.isBoundary)
			}
		})
	}
}

// TestNewReviewOrchestrator tests orchestrator creation.
func TestNewReviewOrchestrator(t *testing.T) {
	ro := NewReviewOrchestrator(AutonomyBatch, "/test/plan.md", "/test/project")

	if ro.AutonomyMode != AutonomyBatch {
		t.Errorf("AutonomyMode = %v, want AutonomyBatch", ro.AutonomyMode)
	}
	if ro.PlanPath != "/test/plan.md" {
		t.Errorf("PlanPath = %s, want /test/plan.md", ro.PlanPath)
	}
	if ro.ProjectPath != "/test/project" {
		t.Errorf("ProjectPath = %s, want /test/project", ro.ProjectPath)
	}
	if ro.checkpointMgr == nil {
		t.Error("checkpointMgr should not be nil")
	}
	if ro.accumulatedResults == nil {
		t.Error("accumulatedResults should not be nil")
	}
	if ro.startTime.IsZero() {
		t.Error("startTime should be set")
	}
}

// =============================================================================
// REQ_006: Review Loop Architecture Tests (Phase 7)
// =============================================================================

// TestNewReviewLoopConfig tests ReviewLoopConfig creation with defaults.
// REQ_006.1: Loop configuration for phase iteration
func TestNewReviewLoopConfig(t *testing.T) {
	config := NewReviewLoopConfig("/test/plan.md", "/test/project")

	// REQ_006.1: Verify default values
	if config.PlanPath != "/test/plan.md" {
		t.Errorf("PlanPath = %s, want /test/plan.md", config.PlanPath)
	}
	if config.ProjectPath != "/test/project" {
		t.Errorf("ProjectPath = %s, want /test/project", config.ProjectPath)
	}
	if config.AutonomyMode != AutonomyCheckpoint {
		t.Errorf("AutonomyMode = %v, want AutonomyCheckpoint", config.AutonomyMode)
	}
	if config.MaxIterations != DefaultMaxIterations {
		t.Errorf("MaxIterations = %d, want %d", config.MaxIterations, DefaultMaxIterations)
	}
	if config.MaxRetries != DefaultMaxRetries {
		t.Errorf("MaxRetries = %d, want %d", config.MaxRetries, DefaultMaxRetries)
	}
	if config.MaxRecursionDepth != DefaultMaxRecursionDepth {
		t.Errorf("MaxRecursionDepth = %d, want %d", config.MaxRecursionDepth, DefaultMaxRecursionDepth)
	}
	if config.Timeout != DefaultReviewTimeout {
		t.Errorf("Timeout = %v, want %v", config.Timeout, DefaultReviewTimeout)
	}
	if !config.StopOnCritical {
		t.Error("StopOnCritical should be true by default")
	}
	if len(config.StepsToRun) != 5 {
		t.Errorf("StepsToRun should have 5 steps, got %d", len(config.StepsToRun))
	}
	if len(config.PhasesToReview) != 6 {
		t.Errorf("PhasesToReview should have 6 phases, got %d", len(config.PhasesToReview))
	}
}

// TestNewReviewLoopResult tests ReviewLoopResult initialization.
// REQ_006.4: Results map structure for storing review findings
func TestNewReviewLoopResult(t *testing.T) {
	result := NewReviewLoopResult()

	// REQ_006.4: Empty results map initialized
	if result.Results == nil {
		t.Error("Results should be initialized")
	}
	if result.PhaseStates == nil {
		t.Error("PhaseStates should be initialized")
	}
	if result.PhaseCounts == nil {
		t.Error("PhaseCounts should be initialized")
	}
	if result.ReviewedPhases == nil {
		t.Error("ReviewedPhases should be initialized")
	}
	if result.ReviewedSteps == nil {
		t.Error("ReviewedSteps should be initialized")
	}
	if result.RetryCount == nil {
		t.Error("RetryCount should be initialized")
	}
	if !result.Success {
		t.Error("Success should be true initially")
	}
	if result.StartTime.IsZero() {
		t.Error("StartTime should be set")
	}
}

// TestReviewLoopResultHasBlockingIssues tests critical issue detection.
// REQ_006.4: hasBlockingIssues(results) returns true if any Critical findings
func TestReviewLoopResultHasBlockingIssues(t *testing.T) {
	tests := []struct {
		name       string
		counts     SeverityCounts
		hasBlocking bool
	}{
		{
			name:       "No critical issues",
			counts:     SeverityCounts{WellDefined: 5, Warning: 3, Critical: 0},
			hasBlocking: false,
		},
		{
			name:       "One critical issue",
			counts:     SeverityCounts{WellDefined: 5, Warning: 3, Critical: 1},
			hasBlocking: true,
		},
		{
			name:       "Multiple critical issues",
			counts:     SeverityCounts{WellDefined: 2, Warning: 1, Critical: 5},
			hasBlocking: true,
		},
		{
			name:       "Only well-defined",
			counts:     SeverityCounts{WellDefined: 10, Warning: 0, Critical: 0},
			hasBlocking: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := NewReviewLoopResult()
			result.TotalCounts = tt.counts

			if got := result.HasBlockingIssues(); got != tt.hasBlocking {
				t.Errorf("HasBlockingIssues() = %v, want %v", got, tt.hasBlocking)
			}
		})
	}
}

// TestReviewLoopResultCountBySeverity tests severity count aggregation.
// REQ_006.4: countBySeverity(results) returns map[SeverityLevel]int
func TestReviewLoopResultCountBySeverity(t *testing.T) {
	result := NewReviewLoopResult()
	result.TotalCounts = SeverityCounts{
		WellDefined: 10,
		Warning:     5,
		Critical:    2,
	}

	counts := result.CountBySeverity()

	if counts[SeverityWellDefined] != 10 {
		t.Errorf("WellDefined count = %d, want 10", counts[SeverityWellDefined])
	}
	if counts[SeverityWarning] != 5 {
		t.Errorf("Warning count = %d, want 5", counts[SeverityWarning])
	}
	if counts[SeverityCritical] != 2 {
		t.Errorf("Critical count = %d, want 2", counts[SeverityCritical])
	}
}

// TestReviewLoopResultFilterBySeverity tests severity filtering.
// REQ_006.4: filterBySeverity(results, severity) returns filtered results
func TestReviewLoopResultFilterBySeverity(t *testing.T) {
	result := NewReviewLoopResult()
	result.Results[PhaseResearch] = make(map[ReviewStep]*ReviewStepResult)

	stepResult := NewReviewStepResult(StepContracts, PhaseResearch)
	stepResult.AddFinding(ReviewFinding{ID: "f1", Severity: SeverityWellDefined})
	stepResult.AddFinding(ReviewFinding{ID: "f2", Severity: SeverityWarning})
	stepResult.AddFinding(ReviewFinding{ID: "f3", Severity: SeverityCritical})
	stepResult.AddFinding(ReviewFinding{ID: "f4", Severity: SeverityWarning})
	result.Results[PhaseResearch][StepContracts] = stepResult

	// Test filter by Warning
	warnings := result.FilterBySeverity(SeverityWarning)
	if len(warnings) != 2 {
		t.Errorf("FilterBySeverity(Warning) returned %d findings, want 2", len(warnings))
	}

	// Test filter by Critical
	criticals := result.FilterBySeverity(SeverityCritical)
	if len(criticals) != 1 {
		t.Errorf("FilterBySeverity(Critical) returned %d findings, want 1", len(criticals))
	}

	// Test filter by WellDefined
	wellDefined := result.FilterBySeverity(SeverityWellDefined)
	if len(wellDefined) != 1 {
		t.Errorf("FilterBySeverity(WellDefined) returned %d findings, want 1", len(wellDefined))
	}
}

// TestReviewLoopResultFilterByPhase tests phase-specific filtering.
// REQ_006.4: filterByPhase(results, phase) returns phase-specific results
func TestReviewLoopResultFilterByPhase(t *testing.T) {
	result := NewReviewLoopResult()
	result.Results[PhaseResearch] = make(map[ReviewStep]*ReviewStepResult)
	result.Results[PhaseDecomposition] = make(map[ReviewStep]*ReviewStepResult)

	stepResult1 := NewReviewStepResult(StepContracts, PhaseResearch)
	stepResult1.AddFinding(ReviewFinding{ID: "f1"})
	result.Results[PhaseResearch][StepContracts] = stepResult1

	stepResult2 := NewReviewStepResult(StepInterfaces, PhaseDecomposition)
	stepResult2.AddFinding(ReviewFinding{ID: "f2"})
	result.Results[PhaseDecomposition][StepInterfaces] = stepResult2

	// Test filter by Research phase
	researchResults := result.FilterByPhase(PhaseResearch)
	if researchResults == nil {
		t.Error("FilterByPhase(Research) returned nil")
	}
	if len(researchResults) != 1 {
		t.Errorf("FilterByPhase(Research) returned %d results, want 1", len(researchResults))
	}

	// Test filter by non-existent phase
	tddResults := result.FilterByPhase(PhaseTDDPlanning)
	if tddResults != nil {
		t.Error("FilterByPhase for non-existent phase should return nil")
	}
}

// TestReviewLoopResultFilterByStep tests step-specific filtering.
// REQ_006.4: filterByStep(results, step) returns step-specific results
func TestReviewLoopResultFilterByStep(t *testing.T) {
	result := NewReviewLoopResult()
	result.Results[PhaseResearch] = make(map[ReviewStep]*ReviewStepResult)
	result.Results[PhaseDecomposition] = make(map[ReviewStep]*ReviewStepResult)

	stepResult1 := NewReviewStepResult(StepContracts, PhaseResearch)
	result.Results[PhaseResearch][StepContracts] = stepResult1

	stepResult2 := NewReviewStepResult(StepContracts, PhaseDecomposition)
	result.Results[PhaseDecomposition][StepContracts] = stepResult2

	stepResult3 := NewReviewStepResult(StepInterfaces, PhaseResearch)
	result.Results[PhaseResearch][StepInterfaces] = stepResult3

	// Test filter by Contracts step
	contractResults := result.FilterByStep(StepContracts)
	if len(contractResults) != 2 {
		t.Errorf("FilterByStep(Contracts) returned %d results, want 2", len(contractResults))
	}

	// Test filter by Interfaces step
	interfaceResults := result.FilterByStep(StepInterfaces)
	if len(interfaceResults) != 1 {
		t.Errorf("FilterByStep(Interfaces) returned %d results, want 1", len(interfaceResults))
	}
}

// TestReviewLoopResultToJSON tests JSON serialization.
// REQ_006.4: Results serializable to JSON for checkpoint persistence
func TestReviewLoopResultToJSON(t *testing.T) {
	result := NewReviewLoopResult()
	result.Metadata.PlanPath = "/test/plan.md"
	result.Metadata.Reviewer = "test-reviewer"
	result.TotalCounts = SeverityCounts{WellDefined: 5, Warning: 2, Critical: 1}

	jsonData, err := result.ToJSON()
	if err != nil {
		t.Fatalf("ToJSON() error: %v", err)
	}

	// Verify JSON contains expected fields
	jsonStr := string(jsonData)
	if !strings.Contains(jsonStr, "plan_path") {
		t.Error("JSON should contain plan_path")
	}
	if !strings.Contains(jsonStr, "reviewer") {
		t.Error("JSON should contain reviewer")
	}
	if !strings.Contains(jsonStr, "well_defined") {
		t.Error("JSON should contain well_defined")
	}
}

// TestReviewLoopResultToMarkdown tests markdown export.
// REQ_006.4: Results exportable to REVIEW.md markdown format
func TestReviewLoopResultToMarkdown(t *testing.T) {
	result := NewReviewLoopResult()
	result.Metadata.PlanPath = "/test/plan.md"
	result.Metadata.Timestamp = time.Now()
	result.TotalCounts = SeverityCounts{WellDefined: 5, Warning: 2, Critical: 1}
	result.TerminationReason = TerminationAllComplete
	result.Iterations = 3
	result.DurationSeconds = 12.5

	markdown := result.ToMarkdown()

	// Verify markdown contains expected sections
	if !strings.Contains(markdown, "# Plan Review Report") {
		t.Error("Markdown should contain header")
	}
	if !strings.Contains(markdown, "## Summary") {
		t.Error("Markdown should contain Summary section")
	}
	if !strings.Contains(markdown, "Well-defined: 5") {
		t.Error("Markdown should contain well-defined count")
	}
	if !strings.Contains(markdown, "Warnings: 2") {
		t.Error("Markdown should contain warning count")
	}
	if !strings.Contains(markdown, "Critical: 1") {
		t.Error("Markdown should contain critical count")
	}
}

// TestReviewLoopExecutorAreDependenciesMet tests phase dependency checking.
// REQ_006.1: areDependenciesMet(phase) is called before processing each phase
func TestReviewLoopExecutorAreDependenciesMet(t *testing.T) {
	config := NewReviewLoopConfig("/test/plan.md", "/test/project")
	executor := NewReviewLoopExecutor(config)

	tests := []struct {
		name           string
		phase          PhaseType
		phaseStates    map[PhaseType]PhaseState
		expectedMet    bool
	}{
		{
			name:  "Research has no dependencies",
			phase: PhaseResearch,
			phaseStates: map[PhaseType]PhaseState{},
			expectedMet: true,
		},
		{
			name:  "Decomposition depends on Research - not complete",
			phase: PhaseDecomposition,
			phaseStates: map[PhaseType]PhaseState{
				PhaseResearch: PhaseStatePending,
			},
			expectedMet: false,
		},
		{
			name:  "Decomposition depends on Research - complete",
			phase: PhaseDecomposition,
			phaseStates: map[PhaseType]PhaseState{
				PhaseResearch: PhaseStateComplete,
			},
			expectedMet: true,
		},
		{
			name:  "TDDPlanning depends on Decomposition - not complete",
			phase: PhaseTDDPlanning,
			phaseStates: map[PhaseType]PhaseState{
				PhaseResearch:      PhaseStateComplete,
				PhaseDecomposition: PhaseStateInProgress,
			},
			expectedMet: false,
		},
		{
			name:  "Implementation depends on BeadsSync - complete",
			phase: PhaseImplementation,
			phaseStates: map[PhaseType]PhaseState{
				PhaseBeadsSync: PhaseStateComplete,
			},
			expectedMet: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := NewReviewLoopResult()
			result.PhaseStates = tt.phaseStates

			got := executor.AreDependenciesMet(tt.phase, result)
			if got != tt.expectedMet {
				t.Errorf("AreDependenciesMet(%s) = %v, want %v", tt.phase, got, tt.expectedMet)
			}
		})
	}
}

// TestReviewLoopExecutorTransitionPhaseState tests state machine transitions.
// REQ_006.1: Phase transition follows valid state machine
func TestReviewLoopExecutorTransitionPhaseState(t *testing.T) {
	config := NewReviewLoopConfig("/test/plan.md", "/test/project")
	executor := NewReviewLoopExecutor(config)

	tests := []struct {
		name         string
		initialState PhaseState
		newState     PhaseState
		wantErr      bool
	}{
		// Valid transitions
		{name: "Empty to Pending", initialState: "", newState: PhaseStatePending, wantErr: false},
		{name: "Pending to InProgress", initialState: PhaseStatePending, newState: PhaseStateInProgress, wantErr: false},
		{name: "InProgress to Complete", initialState: PhaseStateInProgress, newState: PhaseStateComplete, wantErr: false},
		{name: "InProgress to Failed", initialState: PhaseStateInProgress, newState: PhaseStateFailed, wantErr: false},
		{name: "Failed to InProgress (retry)", initialState: PhaseStateFailed, newState: PhaseStateInProgress, wantErr: false},

		// Invalid transitions
		{name: "Pending to Complete", initialState: PhaseStatePending, newState: PhaseStateComplete, wantErr: true},
		{name: "Pending to Failed", initialState: PhaseStatePending, newState: PhaseStateFailed, wantErr: true},
		{name: "Complete to any", initialState: PhaseStateComplete, newState: PhaseStateInProgress, wantErr: true},
		{name: "InProgress to Pending", initialState: PhaseStateInProgress, newState: PhaseStatePending, wantErr: true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := NewReviewLoopResult()
			if tt.initialState != "" {
				result.PhaseStates[PhaseResearch] = tt.initialState
			}

			err := executor.TransitionPhaseState(PhaseResearch, tt.newState, result)
			if (err != nil) != tt.wantErr {
				t.Errorf("TransitionPhaseState() error = %v, wantErr %v", err, tt.wantErr)
			}

			// Verify state was updated on success
			if err == nil {
				if result.PhaseStates[PhaseResearch] != tt.newState {
					t.Errorf("PhaseState = %v, want %v", result.PhaseStates[PhaseResearch], tt.newState)
				}
			}
		})
	}
}

// TestReviewLoopExecutorReviewRequirements tests recursive requirement traversal.
// REQ_006.3: reviewRequirements(node *RequirementNode, step ReviewStep) []ReviewFinding
func TestReviewLoopExecutorReviewRequirements(t *testing.T) {
	config := NewReviewLoopConfig("/test/plan.md", "/test/project")
	config.MaxRecursionDepth = 3
	executor := NewReviewLoopExecutor(config)

	t.Run("Nil node returns empty findings", func(t *testing.T) {
		findings := executor.ReviewRequirements(nil, StepContracts, 0)
		if len(findings) != 0 {
			t.Errorf("ReviewRequirements(nil) returned %d findings, want 0", len(findings))
		}
	})

	t.Run("Simple node produces findings", func(t *testing.T) {
		executor.visitedNodes = make(map[string]bool)
		node := &RequirementNode{
			ID:          "REQ-001",
			Type:        "implementation",
			Description: "Test requirement",
			AcceptanceCriteria: []string{
				"Input must be validated",
				"Output is JSON format",
			},
		}

		findings := executor.ReviewRequirements(node, StepContracts, 0)
		// Should have findings for I/O contracts
		if len(findings) == 0 {
			t.Error("Expected findings for contract analysis")
		}
	})

	t.Run("Max recursion depth produces warning", func(t *testing.T) {
		executor.visitedNodes = make(map[string]bool)
		node := &RequirementNode{
			ID:   "REQ-DEEP",
			Type: "parent",
		}

		findings := executor.ReviewRequirements(node, StepContracts, config.MaxRecursionDepth+1)

		hasDepthWarning := false
		for _, f := range findings {
			if strings.Contains(f.Description, "Maximum recursion depth exceeded") {
				hasDepthWarning = true
				break
			}
		}
		if !hasDepthWarning {
			t.Error("Expected depth exceeded warning")
		}
	})

	t.Run("Circular dependency detection", func(t *testing.T) {
		executor.visitedNodes = make(map[string]bool)
		// First visit marks node as visited
		executor.visitedNodes["REQ-CIRC"] = true

		node := &RequirementNode{
			ID:   "REQ-CIRC",
			Type: "parent",
		}

		findings := executor.ReviewRequirements(node, StepContracts, 0)

		hasCircularWarning := false
		for _, f := range findings {
			if strings.Contains(f.Description, "Circular dependency detected") {
				hasCircularWarning = true
				if f.Severity != SeverityCritical {
					t.Errorf("Circular dependency should be Critical, got %v", f.Severity)
				}
				break
			}
		}
		if !hasCircularWarning {
			t.Error("Expected circular dependency warning")
		}
	})

	t.Run("Recursive child traversal", func(t *testing.T) {
		executor.visitedNodes = make(map[string]bool)
		node := &RequirementNode{
			ID:   "REQ-PARENT",
			Type: "parent",
			Children: []*RequirementNode{
				{
					ID:          "REQ-CHILD-1",
					Type:        "implementation",
					Description: "Child requirement 1",
				},
				{
					ID:          "REQ-CHILD-2",
					Type:        "implementation",
					Description: "Child requirement 2",
				},
			},
		}

		findings := executor.ReviewRequirements(node, StepContracts, 0)

		// Should have findings from parent and children
		childFindings := 0
		for _, f := range findings {
			if strings.Contains(f.Component, "REQ-CHILD") {
				childFindings++
			}
		}
		if childFindings == 0 {
			t.Error("Expected findings from child nodes")
		}
	})

	t.Run("Three-tier hierarchy traversal", func(t *testing.T) {
		executor.visitedNodes = make(map[string]bool)
		// REQ_006.3: 3-tier hierarchy: parent → step → implementation
		node := &RequirementNode{
			ID:   "REQ-TOP",
			Type: "parent",
			Children: []*RequirementNode{
				{
					ID:   "REQ-MID",
					Type: "step",
					Children: []*RequirementNode{
						{
							ID:          "REQ-IMPL",
							Type:        "implementation",
							Description: "Implementation detail",
						},
					},
				},
			},
		}

		findings := executor.ReviewRequirements(node, StepContracts, 0)

		// Should traverse all three levels
		foundImpl := false
		for _, f := range findings {
			if strings.Contains(f.Component, "REQ-IMPL") {
				foundImpl = true
				break
			}
		}
		if !foundImpl {
			t.Error("Expected to traverse to implementation level")
		}
	})
}

// TestReviewLoopResultTerminationReasons tests termination reason constants.
// REQ_006.5: Loop termination with clear reasons
func TestReviewLoopResultTerminationReasons(t *testing.T) {
	tests := []struct {
		reason      TerminationReason
		description string
	}{
		{TerminationMaxIterations, "max_iterations"},
		{TerminationAllComplete, "all_complete"},
		{TerminationCriticalBlocking, "critical_blocking"},
		{TerminationTimeout, "timeout"},
		{TerminationUserCancelled, "user_cancelled"},
	}

	for _, tt := range tests {
		t.Run(string(tt.reason), func(t *testing.T) {
			if string(tt.reason) != tt.description {
				t.Errorf("TerminationReason = %s, want %s", tt.reason, tt.description)
			}
		})
	}
}

// TestPhaseStateConstants tests phase state constants.
// REQ_006.1: Phase transition follows pending → in_progress → complete/failed
func TestPhaseStateConstants(t *testing.T) {
	tests := []struct {
		state       PhaseState
		description string
	}{
		{PhaseStatePending, "pending"},
		{PhaseStateInProgress, "in_progress"},
		{PhaseStateComplete, "complete"},
		{PhaseStateFailed, "failed"},
	}

	for _, tt := range tests {
		t.Run(string(tt.state), func(t *testing.T) {
			if string(tt.state) != tt.description {
				t.Errorf("PhaseState = %s, want %s", tt.state, tt.description)
			}
		})
	}
}

// TestReviewLoopPhaseOrder tests that phases are processed in correct order.
// REQ_006.1: Outer loop iterates through 6 phases in order
func TestReviewLoopPhaseOrder(t *testing.T) {
	expectedOrder := []PhaseType{
		PhaseResearch,
		PhaseDecomposition,
		PhaseTDDPlanning,
		PhaseMultiDoc,
		PhaseBeadsSync,
		PhaseImplementation,
	}

	phases := AllPhases()

	if len(phases) != 6 {
		t.Errorf("AllPhases() returned %d phases, want 6", len(phases))
	}

	for i, expected := range expectedOrder {
		if phases[i] != expected {
			t.Errorf("Phase at index %d = %s, want %s", i, phases[i], expected)
		}
	}
}

// TestReviewStepOrder tests that review steps are processed in correct order.
// REQ_006.2: Middle loop iterates through 5 steps in order
func TestReviewStepOrder(t *testing.T) {
	expectedOrder := []ReviewStep{
		StepContracts,
		StepInterfaces,
		StepPromises,
		StepDataModels,
		StepAPIs,
	}

	steps := AllReviewSteps()

	if len(steps) != 5 {
		t.Errorf("AllReviewSteps() returned %d steps, want 5", len(steps))
	}

	for i, expected := range expectedOrder {
		if steps[i] != expected {
			t.Errorf("Step at index %d = %s, want %s", i, steps[i], expected)
		}
	}
}

// TestDefaultConstants tests default constant values.
// REQ_006.5: Configuration defaults
func TestDefaultConstants(t *testing.T) {
	if DefaultMaxRecursionDepth != 10 {
		t.Errorf("DefaultMaxRecursionDepth = %d, want 10", DefaultMaxRecursionDepth)
	}
	if DefaultMaxIterations != 100 {
		t.Errorf("DefaultMaxIterations = %d, want 100", DefaultMaxIterations)
	}
	if DefaultMaxRetries != 3 {
		t.Errorf("DefaultMaxRetries = %d, want 3", DefaultMaxRetries)
	}
	if DefaultReviewTimeout != 10*time.Minute {
		t.Errorf("DefaultReviewTimeout = %v, want 10 minutes", DefaultReviewTimeout)
	}
}

// TestNewReviewLoopExecutor tests executor initialization.
// REQ_006.1: Loop executor setup
func TestNewReviewLoopExecutor(t *testing.T) {
	config := NewReviewLoopConfig("/test/plan.md", "/test/project")
	executor := NewReviewLoopExecutor(config)

	if executor.config != config {
		t.Error("Executor config not set correctly")
	}
	if executor.orchestrator == nil {
		t.Error("Executor orchestrator should be initialized")
	}
	if len(executor.analyzers) != 5 {
		t.Errorf("Executor should have 5 analyzers, got %d", len(executor.analyzers))
	}
	if executor.visitedNodes == nil {
		t.Error("Executor visitedNodes should be initialized")
	}

	// Verify all step analyzers are present
	expectedSteps := []ReviewStep{StepContracts, StepInterfaces, StepPromises, StepDataModels, StepAPIs}
	for _, step := range expectedSteps {
		if _, ok := executor.analyzers[step]; !ok {
			t.Errorf("Executor missing analyzer for step: %s", step)
		}
	}
}

// TestReviewLoopResultAggregation tests result aggregation across phases and steps.
// REQ_006.4: Results stored in map[PhaseType]map[ReviewStep]*ReviewStepResult
func TestReviewLoopResultAggregation(t *testing.T) {
	result := NewReviewLoopResult()

	// Initialize results for multiple phases and steps
	phases := []PhaseType{PhaseResearch, PhaseDecomposition}
	steps := []ReviewStep{StepContracts, StepInterfaces}

	for _, phase := range phases {
		result.Results[phase] = make(map[ReviewStep]*ReviewStepResult)
		for _, step := range steps {
			stepResult := NewReviewStepResult(step, phase)
			stepResult.AddFinding(ReviewFinding{
				ID:       fmt.Sprintf("%s-%s-finding", phase, step),
				Severity: SeverityWarning,
			})
			result.Results[phase][step] = stepResult
		}
	}

	// Verify structure
	for _, phase := range phases {
		phaseResults := result.Results[phase]
		if phaseResults == nil {
			t.Errorf("Missing results for phase: %s", phase)
			continue
		}
		for _, step := range steps {
			stepResult := phaseResults[step]
			if stepResult == nil {
				t.Errorf("Missing results for %s-%s", phase, step)
			}
		}
	}
}

// TestReviewLoopMetadataFields tests metadata field population.
// REQ_006.4: Results include metadata: timestamp, plan path, git commit, reviewer
func TestReviewLoopMetadataFields(t *testing.T) {
	result := NewReviewLoopResult()
	now := time.Now()
	result.Metadata = ReviewLoopMetadata{
		Timestamp:   now,
		PlanPath:    "/test/plan.md",
		ProjectPath: "/test/project",
		GitCommit:   "abc123",
		Reviewer:    "test-reviewer",
	}

	if result.Metadata.Timestamp != now {
		t.Error("Metadata timestamp not set correctly")
	}
	if result.Metadata.PlanPath != "/test/plan.md" {
		t.Errorf("Metadata PlanPath = %s, want /test/plan.md", result.Metadata.PlanPath)
	}
	if result.Metadata.ProjectPath != "/test/project" {
		t.Errorf("Metadata ProjectPath = %s, want /test/project", result.Metadata.ProjectPath)
	}
	if result.Metadata.GitCommit != "abc123" {
		t.Errorf("Metadata GitCommit = %s, want abc123", result.Metadata.GitCommit)
	}
	if result.Metadata.Reviewer != "test-reviewer" {
		t.Errorf("Metadata Reviewer = %s, want test-reviewer", result.Metadata.Reviewer)
	}
}

// TestReviewLoopCheckAllIssuesClosed tests beads issue closure checking.
// REQ_006.5: Closure check for beads issues
func TestReviewLoopCheckAllIssuesClosed(t *testing.T) {
	// Create temp directory with beads structure
	tmpDir, err := os.MkdirTemp("", "review-closure-test")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	beadsDir := filepath.Join(tmpDir, ".beads")
	if err := os.MkdirAll(beadsDir, 0755); err != nil {
		t.Fatalf("Failed to create beads dir: %v", err)
	}

	// Create closed issue
	closedIssue := `{"status": "closed"}`
	if err := os.WriteFile(filepath.Join(beadsDir, "issue-1.json"), []byte(closedIssue), 0644); err != nil {
		t.Fatalf("Failed to create closed issue: %v", err)
	}

	// Create open issue
	openIssue := `{"status": "open"}`
	if err := os.WriteFile(filepath.Join(beadsDir, "issue-2.json"), []byte(openIssue), 0644); err != nil {
		t.Fatalf("Failed to create open issue: %v", err)
	}

	t.Run("Empty list returns all closed", func(t *testing.T) {
		allClosed, closed := CheckAllIssuesClosed(tmpDir, []string{})
		if !allClosed {
			t.Error("Empty list should return all closed")
		}
		if len(closed) != 0 {
			t.Errorf("Empty list should return empty closed list, got %d", len(closed))
		}
	})

	t.Run("All closed issues", func(t *testing.T) {
		allClosed, closed := CheckAllIssuesClosed(tmpDir, []string{"issue-1"})
		if !allClosed {
			t.Error("Should return all closed for closed issues only")
		}
		if len(closed) != 1 {
			t.Errorf("Should return 1 closed issue, got %d", len(closed))
		}
	})

	t.Run("Mixed open and closed", func(t *testing.T) {
		allClosed, closed := CheckAllIssuesClosed(tmpDir, []string{"issue-1", "issue-2"})
		if allClosed {
			t.Error("Should not return all closed when open issues exist")
		}
		if len(closed) != 1 {
			t.Errorf("Should return 1 closed issue, got %d", len(closed))
		}
	})

	t.Run("Non-existent issues are considered open", func(t *testing.T) {
		allClosed, _ := CheckAllIssuesClosed(tmpDir, []string{"non-existent"})
		if allClosed {
			t.Error("Non-existent issues should be considered open")
		}
	})
}

// TestCountBlockedIssues tests blocked issue counting.
// REQ_006.5: Blocking dependency detection
func TestCountBlockedIssues(t *testing.T) {
	// Create temp directory with beads structure
	tmpDir, err := os.MkdirTemp("", "review-blocked-test")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	beadsDir := filepath.Join(tmpDir, ".beads")
	if err := os.MkdirAll(beadsDir, 0755); err != nil {
		t.Fatalf("Failed to create beads dir: %v", err)
	}

	// Create closed issue (no blocker)
	closedIssue := `{"status": "closed"}`
	if err := os.WriteFile(filepath.Join(beadsDir, "issue-1.json"), []byte(closedIssue), 0644); err != nil {
		t.Fatalf("Failed to create closed issue: %v", err)
	}

	// Create open issue blocked by open dependency
	blockedIssue := `{"status": "open", "depends_on_id": "issue-3"}`
	if err := os.WriteFile(filepath.Join(beadsDir, "issue-2.json"), []byte(blockedIssue), 0644); err != nil {
		t.Fatalf("Failed to create blocked issue: %v", err)
	}

	// Create the blocking open issue
	blockingIssue := `{"status": "open"}`
	if err := os.WriteFile(filepath.Join(beadsDir, "issue-3.json"), []byte(blockingIssue), 0644); err != nil {
		t.Fatalf("Failed to create blocking issue: %v", err)
	}

	t.Run("Count blocked issues", func(t *testing.T) {
		blocked, blockedBy := CountBlockedIssues(tmpDir, []string{"issue-1", "issue-2", "issue-3"})

		if blocked != 1 {
			t.Errorf("Should have 1 blocked issue, got %d", blocked)
		}
		if blockedBy["issue-2"] != "issue-3" {
			t.Errorf("issue-2 should be blocked by issue-3, got %s", blockedBy["issue-2"])
		}
	})
}

// TestAnalyzeContracts tests contract analysis on requirement nodes.
// REQ_006.2: Contract analysis checks
func TestAnalyzeContracts(t *testing.T) {
	config := NewReviewLoopConfig("/test/plan.md", "/test/project")
	executor := NewReviewLoopExecutor(config)

	t.Run("Node with I/O contracts", func(t *testing.T) {
		node := &RequirementNode{
			ID:   "REQ-001",
			Type: "implementation",
			AcceptanceCriteria: []string{
				"Accepts JSON input",
				"Returns structured output",
			},
		}

		base := ReviewFinding{Component: node.ID}
		findings := executor.analyzeContracts(node, base)

		hasIOContract := false
		for _, f := range findings {
			if strings.Contains(f.ID, "contract-io") && f.Severity == SeverityWellDefined {
				hasIOContract = true
			}
		}
		if !hasIOContract {
			t.Error("Expected I/O contract to be well-defined")
		}
	})

	t.Run("Node missing I/O contracts", func(t *testing.T) {
		node := &RequirementNode{
			ID:   "REQ-002",
			Type: "implementation",
			AcceptanceCriteria: []string{
				"Does something",
			},
		}

		base := ReviewFinding{Component: node.ID}
		findings := executor.analyzeContracts(node, base)

		hasMissingIO := false
		for _, f := range findings {
			if strings.Contains(f.ID, "contract-io") && f.Severity == SeverityWarning {
				hasMissingIO = true
			}
		}
		if !hasMissingIO {
			t.Error("Expected warning for missing I/O contracts")
		}
	})
}

// TestAnalyzePromises tests promise analysis on requirement nodes.
// REQ_006.2: Promise analysis checks
func TestAnalyzePromises(t *testing.T) {
	config := NewReviewLoopConfig("/test/plan.md", "/test/project")
	executor := NewReviewLoopExecutor(config)

	t.Run("Async operation with timeout", func(t *testing.T) {
		node := &RequirementNode{
			ID:   "REQ-001",
			Type: "implementation",
			AcceptanceCriteria: []string{
				"Async operation with timeout handling",
				"Supports cancellation via context",
			},
		}

		base := ReviewFinding{Component: node.ID}
		findings := executor.analyzePromises(node, base)

		hasAsync := false
		for _, f := range findings {
			if strings.Contains(f.ID, "promise-async") && f.Severity == SeverityWellDefined {
				hasAsync = true
			}
		}
		if !hasAsync {
			t.Error("Expected async operation to be well-defined")
		}
	})

	t.Run("Async operation missing timeout", func(t *testing.T) {
		node := &RequirementNode{
			ID:   "REQ-002",
			Type: "implementation",
			AcceptanceCriteria: []string{
				"Runs async operation in goroutine",
			},
		}

		base := ReviewFinding{Component: node.ID}
		findings := executor.analyzePromises(node, base)

		hasMissingTimeout := false
		for _, f := range findings {
			if strings.Contains(f.ID, "promise-no-timeout") && f.Severity == SeverityWarning {
				hasMissingTimeout = true
			}
		}
		if !hasMissingTimeout {
			t.Error("Expected warning for missing timeout")
		}
	})
}

// TestAnalyzeAPIs tests API analysis on requirement nodes.
// REQ_006.2: API analysis checks
func TestAnalyzeAPIs(t *testing.T) {
	config := NewReviewLoopConfig("/test/plan.md", "/test/project")
	executor := NewReviewLoopExecutor(config)

	t.Run("API endpoint with versioning", func(t *testing.T) {
		node := &RequirementNode{
			ID:   "REQ-001",
			Type: "implementation",
			AcceptanceCriteria: []string{
				"GET /api/v1/users returns 200 OK",
				"Returns 404 for missing user",
			},
		}

		base := ReviewFinding{Component: node.ID}
		findings := executor.analyzeAPIs(node, base)

		hasEndpoint := false
		hasVersioning := false
		for _, f := range findings {
			if strings.Contains(f.ID, "api-endpoint") {
				hasEndpoint = true
			}
			if strings.Contains(f.ID, "api-version") {
				hasVersioning = true
			}
		}
		if !hasEndpoint {
			t.Error("Expected API endpoint finding")
		}
		if !hasVersioning {
			t.Error("Expected API versioning finding")
		}
	})

	t.Run("API endpoint missing error handling", func(t *testing.T) {
		node := &RequirementNode{
			ID:   "REQ-002",
			Type: "implementation",
			AcceptanceCriteria: []string{
				"POST /api/v1/items creates item",
			},
		}

		base := ReviewFinding{Component: node.ID}
		findings := executor.analyzeAPIs(node, base)

		hasMissingErrors := false
		for _, f := range findings {
			if strings.Contains(f.ID, "api-no-errors") && f.Severity == SeverityWarning {
				hasMissingErrors = true
			}
		}
		if !hasMissingErrors {
			t.Error("Expected warning for missing error definitions")
		}
	})
}

// TestContainsStep tests the helper function for checking step membership.
func TestContainsStep(t *testing.T) {
	steps := []ReviewStep{StepContracts, StepInterfaces, StepPromises}

	if !containsStep(steps, StepContracts) {
		t.Error("containsStep should find StepContracts")
	}
	if !containsStep(steps, StepInterfaces) {
		t.Error("containsStep should find StepInterfaces")
	}
	if containsStep(steps, StepAPIs) {
		t.Error("containsStep should not find StepAPIs")
	}
	if containsStep([]ReviewStep{}, StepContracts) {
		t.Error("containsStep should return false for empty slice")
	}
}
