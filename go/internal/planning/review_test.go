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
