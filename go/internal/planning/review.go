package planning

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"
)

// ReviewStep represents the 5-step discrete analysis framework.
type ReviewStep int

const (
	StepContracts ReviewStep = iota
	StepInterfaces
	StepPromises
	StepDataModels
	StepAPIs
)

// String returns the string representation of ReviewStep.
func (rs ReviewStep) String() string {
	switch rs {
	case StepContracts:
		return "contracts"
	case StepInterfaces:
		return "interfaces"
	case StepPromises:
		return "promises"
	case StepDataModels:
		return "data_models"
	case StepAPIs:
		return "apis"
	default:
		return "unknown"
	}
}

// ReviewStepFromString parses a string into a ReviewStep.
func ReviewStepFromString(s string) (ReviewStep, error) {
	switch strings.ToLower(strings.TrimSpace(s)) {
	case "contracts":
		return StepContracts, nil
	case "interfaces":
		return StepInterfaces, nil
	case "promises":
		return StepPromises, nil
	case "data_models":
		return StepDataModels, nil
	case "apis":
		return StepAPIs, nil
	default:
		return StepContracts, fmt.Errorf("invalid review step: %s (valid: contracts, interfaces, promises, data_models, apis)", s)
	}
}

// AllReviewSteps returns all review steps in order.
func AllReviewSteps() []ReviewStep {
	return []ReviewStep{
		StepContracts,
		StepInterfaces,
		StepPromises,
		StepDataModels,
		StepAPIs,
	}
}

// Next returns the next review step in sequence.
func (rs ReviewStep) Next() (ReviewStep, error) {
	if rs == StepAPIs {
		return StepAPIs, fmt.Errorf("apis is the final step")
	}
	return rs + 1, nil
}

// Previous returns the previous review step in sequence.
func (rs ReviewStep) Previous() (ReviewStep, error) {
	if rs == StepContracts {
		return StepContracts, fmt.Errorf("contracts is the first step")
	}
	return rs - 1, nil
}

// MarshalJSON implements json.Marshaler for ReviewStep.
func (rs ReviewStep) MarshalJSON() ([]byte, error) {
	return json.Marshal(rs.String())
}

// UnmarshalJSON implements json.Unmarshaler for ReviewStep.
func (rs *ReviewStep) UnmarshalJSON(data []byte) error {
	var s string
	if err := json.Unmarshal(data, &s); err != nil {
		return fmt.Errorf("review step must be a string: %w", err)
	}
	step, err := ReviewStepFromString(s)
	if err != nil {
		return err
	}
	*rs = step
	return nil
}

// Severity represents the three-level severity classification.
type Severity int

const (
	SeverityWellDefined Severity = iota // ✅ Well-defined
	SeverityWarning                     // ⚠️ Warning
	SeverityCritical                    // ❌ Critical
)

// String returns the string representation of Severity.
func (s Severity) String() string {
	switch s {
	case SeverityWellDefined:
		return "well_defined"
	case SeverityWarning:
		return "warning"
	case SeverityCritical:
		return "critical"
	default:
		return "unknown"
	}
}

// Emoji returns the emoji for display.
func (s Severity) Emoji() string {
	switch s {
	case SeverityWellDefined:
		return "✅"
	case SeverityWarning:
		return "⚠️"
	case SeverityCritical:
		return "❌"
	default:
		return "❓"
	}
}

// SeverityFromString parses a string into a Severity.
func SeverityFromString(str string) (Severity, error) {
	switch strings.ToLower(strings.TrimSpace(str)) {
	case "well_defined", "ok", "good":
		return SeverityWellDefined, nil
	case "warning", "warn":
		return SeverityWarning, nil
	case "critical", "error", "fail":
		return SeverityCritical, nil
	default:
		return SeverityWellDefined, fmt.Errorf("invalid severity: %s", str)
	}
}

// MarshalJSON implements json.Marshaler for Severity.
func (s Severity) MarshalJSON() ([]byte, error) {
	return json.Marshal(s.String())
}

// UnmarshalJSON implements json.Unmarshaler for Severity.
func (s *Severity) UnmarshalJSON(data []byte) error {
	var str string
	if err := json.Unmarshal(data, &str); err != nil {
		return fmt.Errorf("severity must be a string: %w", err)
	}
	sev, err := SeverityFromString(str)
	if err != nil {
		return err
	}
	*s = sev
	return nil
}

// ReviewFinding represents a single finding from the review process.
type ReviewFinding struct {
	ID             string   `json:"id"`
	Component      string   `json:"component"`
	Description    string   `json:"description"`
	Severity       Severity `json:"severity"`
	Recommendation string   `json:"recommendation,omitempty"`
	Location       string   `json:"location,omitempty"` // file:line format
	RelatedIDs     []string `json:"related_ids,omitempty"`
}

// SeverityCounts tracks counts by severity level.
type SeverityCounts struct {
	WellDefined int `json:"well_defined"`
	Warning     int `json:"warning"`
	Critical    int `json:"critical"`
}

// Total returns the total count of all findings.
func (sc *SeverityCounts) Total() int {
	return sc.WellDefined + sc.Warning + sc.Critical
}

// HasCritical returns true if there are any critical findings.
func (sc *SeverityCounts) HasCritical() bool {
	return sc.Critical > 0
}

// ContractFinding represents a contract-specific finding.
type ContractFinding struct {
	ReviewFinding
	ContractType string `json:"contract_type"` // input, output, error, precondition, postcondition, invariant
}

// ContractAnalysisResult contains results from contract analysis.
type ContractAnalysisResult struct {
	Step           ReviewStep        `json:"step"`
	Phase          PhaseType         `json:"phase,omitempty"`
	RequirementID  string            `json:"requirement_id,omitempty"`
	Findings       []ContractFinding `json:"findings"`
	Counts         SeverityCounts    `json:"counts"`
	ComponentCount int               `json:"component_count"`
	Timestamp      time.Time         `json:"timestamp"`
}

// NewContractAnalysisResult creates a new contract analysis result.
func NewContractAnalysisResult() *ContractAnalysisResult {
	return &ContractAnalysisResult{
		Step:      StepContracts,
		Findings:  make([]ContractFinding, 0),
		Timestamp: time.Now(),
	}
}

// AddFinding adds a finding and updates counts.
func (r *ContractAnalysisResult) AddFinding(f ContractFinding) {
	r.Findings = append(r.Findings, f)
	switch f.Severity {
	case SeverityWellDefined:
		r.Counts.WellDefined++
	case SeverityWarning:
		r.Counts.Warning++
	case SeverityCritical:
		r.Counts.Critical++
	}
}

// InterfaceFinding represents an interface-specific finding.
type InterfaceFinding struct {
	ReviewFinding
	MethodName        string `json:"method_name,omitempty"`
	NamingConvention  string `json:"naming_convention,omitempty"` // camelCase, PascalCase, snake_case
	Visibility        string `json:"visibility,omitempty"`        // public, private, protected
	IsBreakingChange  bool   `json:"is_breaking_change,omitempty"`
	ExtensionPoint    bool   `json:"extension_point,omitempty"`
}

// InterfaceAnalysisResult contains results from interface analysis.
type InterfaceAnalysisResult struct {
	Step               ReviewStep         `json:"step"`
	Phase              PhaseType          `json:"phase,omitempty"`
	RequirementID      string             `json:"requirement_id,omitempty"`
	Findings           []InterfaceFinding `json:"findings"`
	Counts             SeverityCounts     `json:"counts"`
	PublicMethodCount  int                `json:"public_method_count"`
	ExtensionPoints    int                `json:"extension_points"`
	BreakingChanges    int                `json:"breaking_changes"`
	Timestamp          time.Time          `json:"timestamp"`
}

// NewInterfaceAnalysisResult creates a new interface analysis result.
func NewInterfaceAnalysisResult() *InterfaceAnalysisResult {
	return &InterfaceAnalysisResult{
		Step:      StepInterfaces,
		Findings:  make([]InterfaceFinding, 0),
		Timestamp: time.Now(),
	}
}

// AddFinding adds a finding and updates counts.
func (r *InterfaceAnalysisResult) AddFinding(f InterfaceFinding) {
	r.Findings = append(r.Findings, f)
	switch f.Severity {
	case SeverityWellDefined:
		r.Counts.WellDefined++
	case SeverityWarning:
		r.Counts.Warning++
	case SeverityCritical:
		r.Counts.Critical++
	}
	if f.IsBreakingChange {
		r.BreakingChanges++
	}
	if f.ExtensionPoint {
		r.ExtensionPoints++
	}
}

// PromiseFinding represents a promise-specific finding.
type PromiseFinding struct {
	ReviewFinding
	PromiseType       string `json:"promise_type,omitempty"` // idempotency, ordering, determinism
	PropertyType      string `json:"property_type,omitempty"` // maps to ValidPropertyTypes
	ConcurrencyType   string `json:"concurrency_type,omitempty"` // mutex, channel, semaphore
	HasTimeout        bool   `json:"has_timeout,omitempty"`
	HasCancellation   bool   `json:"has_cancellation,omitempty"`
	HasResourceCleanup bool   `json:"has_resource_cleanup,omitempty"`
}

// PromiseAnalysisResult contains results from promise analysis.
type PromiseAnalysisResult struct {
	Step                    ReviewStep       `json:"step"`
	Phase                   PhaseType        `json:"phase,omitempty"`
	RequirementID           string           `json:"requirement_id,omitempty"`
	Findings                []PromiseFinding `json:"findings"`
	Counts                  SeverityCounts   `json:"counts"`
	IdempotentOperations    int              `json:"idempotent_operations"`
	OrderedOperations       int              `json:"ordered_operations"`
	AsyncOperations         int              `json:"async_operations"`
	MissingTimeouts         int              `json:"missing_timeouts"`
	MissingCancellation     int              `json:"missing_cancellation"`
	PotentialRaceConditions int              `json:"potential_race_conditions"`
	Timestamp               time.Time        `json:"timestamp"`
}

// NewPromiseAnalysisResult creates a new promise analysis result.
func NewPromiseAnalysisResult() *PromiseAnalysisResult {
	return &PromiseAnalysisResult{
		Step:      StepPromises,
		Findings:  make([]PromiseFinding, 0),
		Timestamp: time.Now(),
	}
}

// AddFinding adds a finding and updates counts.
func (r *PromiseAnalysisResult) AddFinding(f PromiseFinding) {
	r.Findings = append(r.Findings, f)
	switch f.Severity {
	case SeverityWellDefined:
		r.Counts.WellDefined++
	case SeverityWarning:
		r.Counts.Warning++
	case SeverityCritical:
		r.Counts.Critical++
	}
	if !f.HasTimeout {
		r.MissingTimeouts++
	}
	if !f.HasCancellation {
		r.MissingCancellation++
	}
}

// DataModelFinding represents a data model-specific finding.
type DataModelFinding struct {
	ReviewFinding
	FieldName       string `json:"field_name,omitempty"`
	FieldType       string `json:"field_type,omitempty"`
	IsRequired      bool   `json:"is_required,omitempty"`
	RelationshipType string `json:"relationship_type,omitempty"` // 1:1, 1:N, N:M
	IsBreakingChange bool   `json:"is_breaking_change,omitempty"`
	HasValidation   bool   `json:"has_validation,omitempty"`
}

// DataModelAnalysisResult contains results from data model analysis.
type DataModelAnalysisResult struct {
	Step              ReviewStep         `json:"step"`
	Phase             PhaseType          `json:"phase,omitempty"`
	RequirementID     string             `json:"requirement_id,omitempty"`
	Findings          []DataModelFinding `json:"findings"`
	Counts            SeverityCounts     `json:"counts"`
	StructCount       int                `json:"struct_count"`
	FieldCount        int                `json:"field_count"`
	RelationshipCount int                `json:"relationship_count"`
	BreakingChanges   int                `json:"breaking_changes"`
	MissingValidation int                `json:"missing_validation"`
	Timestamp         time.Time          `json:"timestamp"`
}

// NewDataModelAnalysisResult creates a new data model analysis result.
func NewDataModelAnalysisResult() *DataModelAnalysisResult {
	return &DataModelAnalysisResult{
		Step:      StepDataModels,
		Findings:  make([]DataModelFinding, 0),
		Timestamp: time.Now(),
	}
}

// AddFinding adds a finding and updates counts.
func (r *DataModelAnalysisResult) AddFinding(f DataModelFinding) {
	r.Findings = append(r.Findings, f)
	switch f.Severity {
	case SeverityWellDefined:
		r.Counts.WellDefined++
	case SeverityWarning:
		r.Counts.Warning++
	case SeverityCritical:
		r.Counts.Critical++
	}
	if f.IsBreakingChange {
		r.BreakingChanges++
	}
	if !f.HasValidation {
		r.MissingValidation++
	}
}

// APIFinding represents an API-specific finding.
type APIFinding struct {
	ReviewFinding
	Endpoint          string   `json:"endpoint,omitempty"`
	HTTPMethod        string   `json:"http_method,omitempty"`
	StatusCodes       []int    `json:"status_codes,omitempty"`
	ContentType       string   `json:"content_type,omitempty"`
	VersioningScheme  string   `json:"versioning_scheme,omitempty"` // url, header, query
	IsDeprecated      bool     `json:"is_deprecated,omitempty"`
	MissingErrorCases []string `json:"missing_error_cases,omitempty"`
}

// APIAnalysisResult contains results from API analysis.
type APIAnalysisResult struct {
	Step               ReviewStep   `json:"step"`
	Phase              PhaseType    `json:"phase,omitempty"`
	RequirementID      string       `json:"requirement_id,omitempty"`
	Findings           []APIFinding `json:"findings"`
	Counts             SeverityCounts `json:"counts"`
	EndpointCount      int          `json:"endpoint_count"`
	DeprecatedCount    int          `json:"deprecated_count"`
	MissingErrorCount  int          `json:"missing_error_count"`
	Timestamp          time.Time    `json:"timestamp"`
}

// NewAPIAnalysisResult creates a new API analysis result.
func NewAPIAnalysisResult() *APIAnalysisResult {
	return &APIAnalysisResult{
		Step:      StepAPIs,
		Findings:  make([]APIFinding, 0),
		Timestamp: time.Now(),
	}
}

// AddFinding adds a finding and updates counts.
func (r *APIAnalysisResult) AddFinding(f APIFinding) {
	r.Findings = append(r.Findings, f)
	switch f.Severity {
	case SeverityWellDefined:
		r.Counts.WellDefined++
	case SeverityWarning:
		r.Counts.Warning++
	case SeverityCritical:
		r.Counts.Critical++
	}
	if f.IsDeprecated {
		r.DeprecatedCount++
	}
	if len(f.MissingErrorCases) > 0 {
		r.MissingErrorCount += len(f.MissingErrorCases)
	}
}

// StepAnalysisResult is an interface for all analysis result types.
type StepAnalysisResult interface {
	GetStep() ReviewStep
	GetCounts() SeverityCounts
}

// Implement interface for all result types
func (r *ContractAnalysisResult) GetStep() ReviewStep     { return r.Step }
func (r *ContractAnalysisResult) GetCounts() SeverityCounts { return r.Counts }

func (r *InterfaceAnalysisResult) GetStep() ReviewStep     { return r.Step }
func (r *InterfaceAnalysisResult) GetCounts() SeverityCounts { return r.Counts }

func (r *PromiseAnalysisResult) GetStep() ReviewStep     { return r.Step }
func (r *PromiseAnalysisResult) GetCounts() SeverityCounts { return r.Counts }

func (r *DataModelAnalysisResult) GetStep() ReviewStep     { return r.Step }
func (r *DataModelAnalysisResult) GetCounts() SeverityCounts { return r.Counts }

func (r *APIAnalysisResult) GetStep() ReviewStep     { return r.Step }
func (r *APIAnalysisResult) GetCounts() SeverityCounts { return r.Counts }

// ReviewConfig holds configuration for plan review.
type ReviewConfig struct {
	ProjectPath  string       `json:"project_path"`
	PlanPath     string       `json:"plan_path"`
	Phase        string       `json:"phase,omitempty"`
	Step         string       `json:"step,omitempty"`
	OutputPath   string       `json:"output_path,omitempty"`
	AutonomyMode AutonomyMode `json:"autonomy_mode"`
	AllPhases    bool         `json:"all_phases"`
}

// ReviewResult holds the result of a plan review.
type ReviewResult struct {
	Success          bool                         `json:"success"`
	Output           string                       `json:"output,omitempty"`
	Error            string                       `json:"error,omitempty"`
	FailedAt         string                       `json:"failed_at,omitempty"`
	StepResults      map[ReviewStep]interface{}   `json:"step_results,omitempty"`
	PhaseResults     map[PhaseType]PhaseReviewResult `json:"phase_results,omitempty"`
	TotalCounts      SeverityCounts               `json:"total_counts"`
	ReviewedPhases   []PhaseType                  `json:"reviewed_phases,omitempty"`
	ReviewedSteps    []ReviewStep                 `json:"reviewed_steps,omitempty"`
	Timestamp        time.Time                    `json:"timestamp"`
	DurationSeconds  float64                      `json:"duration_seconds,omitempty"`
}

// PhaseReviewResult contains review results for a single phase.
type PhaseReviewResult struct {
	Phase       PhaseType                     `json:"phase"`
	StepResults map[ReviewStep]interface{}    `json:"step_results"`
	Counts      SeverityCounts                `json:"counts"`
	Timestamp   time.Time                     `json:"timestamp"`
}

// NewReviewResult creates a new review result.
func NewReviewResult() *ReviewResult {
	return &ReviewResult{
		Success:      true,
		StepResults:  make(map[ReviewStep]interface{}),
		PhaseResults: make(map[PhaseType]PhaseReviewResult),
		Timestamp:    time.Now(),
	}
}

// Analyzer is the interface for all step analyzers.
type Analyzer interface {
	Analyze(plan *PlanDocument, phase PhaseType, req *RequirementNode) (interface{}, error)
}

// ContractAnalyzer analyzes contracts in a plan.
type ContractAnalyzer struct{}

// Analyze performs contract analysis on a plan/phase/requirement.
func (a *ContractAnalyzer) Analyze(plan *PlanDocument, phase PhaseType, req *RequirementNode) (interface{}, error) {
	result := NewContractAnalysisResult()
	result.Phase = phase
	if req != nil {
		result.RequirementID = req.ID
	}

	// Analyze component boundaries
	if req != nil && req.Implementation != nil {
		result.ComponentCount = len(req.Implementation.Frontend) +
			len(req.Implementation.Backend) +
			len(req.Implementation.Middleware) +
			len(req.Implementation.Shared)
	}

	// Analyze acceptance criteria for contract definitions
	if req != nil {
		for i, criterion := range req.AcceptanceCriteria {
			finding := a.analyzeCriterion(req.ID, i, criterion)
			result.AddFinding(finding)
		}
	}

	// Analyze testable properties for contract patterns
	if req != nil {
		for _, prop := range req.TestableProperties {
			finding := a.analyzeTestableProperty(req.ID, prop)
			result.AddFinding(finding)
		}
	}

	return result, nil
}

// analyzeCriterion analyzes a single acceptance criterion for contract patterns.
func (a *ContractAnalyzer) analyzeCriterion(reqID string, index int, criterion string) ContractFinding {
	finding := ContractFinding{
		ReviewFinding: ReviewFinding{
			ID:          fmt.Sprintf("%s-contract-%d", reqID, index),
			Component:   reqID,
			Description: criterion,
			Severity:    SeverityWellDefined,
		},
	}

	criterionLower := strings.ToLower(criterion)

	// Check for input contract patterns
	if strings.Contains(criterionLower, "input") || strings.Contains(criterionLower, "accepts") ||
		strings.Contains(criterionLower, "receives") || strings.Contains(criterionLower, "takes") {
		finding.ContractType = "input"
		// Check if it specifies types
		if !strings.Contains(criterionLower, "type") && !strings.Contains(criterionLower, "string") &&
			!strings.Contains(criterionLower, "int") && !strings.Contains(criterionLower, "bool") {
			finding.Severity = SeverityWarning
			finding.Recommendation = "Consider specifying input types and constraints"
		}
	}

	// Check for output contract patterns
	if strings.Contains(criterionLower, "returns") || strings.Contains(criterionLower, "outputs") ||
		strings.Contains(criterionLower, "produces") {
		finding.ContractType = "output"
	}

	// Check for error contract patterns
	if strings.Contains(criterionLower, "error") || strings.Contains(criterionLower, "exception") ||
		strings.Contains(criterionLower, "fails") || strings.Contains(criterionLower, "throws") {
		finding.ContractType = "error"
	}

	// Check for precondition patterns
	if strings.Contains(criterionLower, "must be") || strings.Contains(criterionLower, "requires") ||
		strings.Contains(criterionLower, "prerequisite") || strings.Contains(criterionLower, "before") {
		finding.ContractType = "precondition"
	}

	// Check for postcondition patterns
	if strings.Contains(criterionLower, "ensures") || strings.Contains(criterionLower, "guarantees") ||
		strings.Contains(criterionLower, "after") || strings.Contains(criterionLower, "will be") {
		finding.ContractType = "postcondition"
	}

	// Check for invariant patterns
	if strings.Contains(criterionLower, "always") || strings.Contains(criterionLower, "invariant") ||
		strings.Contains(criterionLower, "never") || strings.Contains(criterionLower, "must remain") {
		finding.ContractType = "invariant"
	}

	// No contract type identified - might be ambiguous
	if finding.ContractType == "" {
		finding.Severity = SeverityWarning
		finding.Recommendation = "Criterion does not clearly indicate contract type (input/output/error/precondition/postcondition/invariant)"
	}

	return finding
}

// analyzeTestableProperty analyzes a testable property for contract patterns.
func (a *ContractAnalyzer) analyzeTestableProperty(reqID string, prop *TestableProperty) ContractFinding {
	finding := ContractFinding{
		ReviewFinding: ReviewFinding{
			ID:          fmt.Sprintf("%s-prop-%s", reqID, prop.PropertyType),
			Component:   reqID,
			Description: prop.Criterion,
			Severity:    SeverityWellDefined,
		},
	}

	// Map property types to contract types
	switch prop.PropertyType {
	case "invariant":
		finding.ContractType = "invariant"
	case "round_trip":
		finding.ContractType = "postcondition"
	case "idempotence":
		finding.ContractType = "postcondition"
	case "oracle":
		finding.ContractType = "output"
	}

	// Check for test skeleton
	if prop.TestSkeleton == "" {
		finding.Severity = SeverityWarning
		finding.Recommendation = "Consider adding a test skeleton for this property"
	}

	return finding
}

// InterfaceAnalyzer analyzes interfaces in a plan.
type InterfaceAnalyzer struct{}

// Analyze performs interface analysis on a plan/phase/requirement.
func (a *InterfaceAnalyzer) Analyze(plan *PlanDocument, phase PhaseType, req *RequirementNode) (interface{}, error) {
	result := NewInterfaceAnalysisResult()
	result.Phase = phase
	if req != nil {
		result.RequirementID = req.ID
	}

	// Analyze implementation components for interface patterns
	if req != nil && req.Implementation != nil {
		a.analyzeComponents(result, req)
	}

	// Analyze description for interface indicators
	if req != nil {
		finding := a.analyzeDescription(req)
		result.AddFinding(finding)
	}

	return result, nil
}

// analyzeComponents analyzes implementation components for interface patterns.
func (a *InterfaceAnalyzer) analyzeComponents(result *InterfaceAnalysisResult, req *RequirementNode) {
	impl := req.Implementation

	// Analyze backend components
	for i, component := range impl.Backend {
		finding := InterfaceFinding{
			ReviewFinding: ReviewFinding{
				ID:          fmt.Sprintf("%s-interface-backend-%d", req.ID, i),
				Component:   component,
				Description: fmt.Sprintf("Backend component: %s", component),
				Severity:    SeverityWellDefined,
			},
			Visibility: "public",
		}

		// Check naming convention
		if strings.Contains(component, "_") {
			finding.NamingConvention = "snake_case"
		} else if len(component) > 0 && component[0] >= 'A' && component[0] <= 'Z' {
			finding.NamingConvention = "PascalCase"
		} else {
			finding.NamingConvention = "camelCase"
		}

		// Check for extension points
		if strings.Contains(strings.ToLower(component), "handler") ||
			strings.Contains(strings.ToLower(component), "provider") ||
			strings.Contains(strings.ToLower(component), "factory") {
			finding.ExtensionPoint = true
		}

		result.AddFinding(finding)
		result.PublicMethodCount++
	}

	// Analyze shared components (typically public)
	for i, component := range impl.Shared {
		finding := InterfaceFinding{
			ReviewFinding: ReviewFinding{
				ID:          fmt.Sprintf("%s-interface-shared-%d", req.ID, i),
				Component:   component,
				Description: fmt.Sprintf("Shared component: %s", component),
				Severity:    SeverityWellDefined,
			},
			Visibility: "public",
		}
		result.AddFinding(finding)
		result.PublicMethodCount++
	}
}

// analyzeDescription analyzes a requirement description for interface patterns.
func (a *InterfaceAnalyzer) analyzeDescription(req *RequirementNode) InterfaceFinding {
	finding := InterfaceFinding{
		ReviewFinding: ReviewFinding{
			ID:          fmt.Sprintf("%s-interface-desc", req.ID),
			Component:   req.ID,
			Description: req.Description,
			Severity:    SeverityWellDefined,
		},
	}

	descLower := strings.ToLower(req.Description)

	// Check for breaking change indicators
	if strings.Contains(descLower, "breaking") || strings.Contains(descLower, "deprecated") ||
		strings.Contains(descLower, "removed") || strings.Contains(descLower, "renamed") {
		finding.IsBreakingChange = true
		finding.Severity = SeverityWarning
		finding.Recommendation = "This change may break existing consumers - ensure proper deprecation notices"
	}

	// Check for extension point indicators
	if strings.Contains(descLower, "extensible") || strings.Contains(descLower, "plugin") ||
		strings.Contains(descLower, "hook") || strings.Contains(descLower, "interface") {
		finding.ExtensionPoint = true
	}

	return finding
}

// PromiseAnalyzer analyzes behavioral promises in a plan.
type PromiseAnalyzer struct{}

// Analyze performs promise analysis on a plan/phase/requirement.
func (a *PromiseAnalyzer) Analyze(plan *PlanDocument, phase PhaseType, req *RequirementNode) (interface{}, error) {
	result := NewPromiseAnalysisResult()
	result.Phase = phase
	if req != nil {
		result.RequirementID = req.ID
	}

	// Analyze testable properties for promise patterns
	if req != nil {
		for _, prop := range req.TestableProperties {
			finding := a.analyzeTestableProperty(req.ID, prop)
			result.AddFinding(finding)

			// Count property types
			switch prop.PropertyType {
			case "idempotence":
				result.IdempotentOperations++
			}
		}

		// Analyze acceptance criteria for promise patterns
		for i, criterion := range req.AcceptanceCriteria {
			finding := a.analyzeCriterion(req.ID, i, criterion)
			result.AddFinding(finding)
		}
	}

	return result, nil
}

// analyzeTestableProperty analyzes a testable property for promise patterns.
func (a *PromiseAnalyzer) analyzeTestableProperty(reqID string, prop *TestableProperty) PromiseFinding {
	finding := PromiseFinding{
		ReviewFinding: ReviewFinding{
			ID:          fmt.Sprintf("%s-promise-%s", reqID, prop.PropertyType),
			Component:   reqID,
			Description: prop.Criterion,
			Severity:    SeverityWellDefined,
		},
		PropertyType: prop.PropertyType,
	}

	// Map property types to promise types
	switch prop.PropertyType {
	case "idempotence":
		finding.PromiseType = "idempotency"
	case "invariant":
		finding.PromiseType = "determinism"
	case "round_trip":
		finding.PromiseType = "ordering"
	}

	return finding
}

// analyzeCriterion analyzes a criterion for promise patterns.
func (a *PromiseAnalyzer) analyzeCriterion(reqID string, index int, criterion string) PromiseFinding {
	finding := PromiseFinding{
		ReviewFinding: ReviewFinding{
			ID:          fmt.Sprintf("%s-promise-crit-%d", reqID, index),
			Component:   reqID,
			Description: criterion,
			Severity:    SeverityWellDefined,
		},
	}

	criterionLower := strings.ToLower(criterion)

	// Check for async/concurrent patterns
	if strings.Contains(criterionLower, "async") || strings.Contains(criterionLower, "concurrent") ||
		strings.Contains(criterionLower, "parallel") || strings.Contains(criterionLower, "goroutine") {
		finding.PromiseType = "async"

		// Check for synchronization
		if strings.Contains(criterionLower, "mutex") {
			finding.ConcurrencyType = "mutex"
		} else if strings.Contains(criterionLower, "channel") {
			finding.ConcurrencyType = "channel"
		} else if strings.Contains(criterionLower, "semaphore") {
			finding.ConcurrencyType = "semaphore"
		} else {
			finding.Severity = SeverityWarning
			finding.Recommendation = "Async operation should specify synchronization mechanism"
		}
	}

	// Check for timeout
	if strings.Contains(criterionLower, "timeout") {
		finding.HasTimeout = true
	} else if strings.Contains(criterionLower, "network") || strings.Contains(criterionLower, "http") ||
		strings.Contains(criterionLower, "api") || strings.Contains(criterionLower, "request") {
		// Network operations should have timeouts
		if !strings.Contains(criterionLower, "timeout") {
			finding.Severity = SeverityWarning
			finding.Recommendation = "Network operation should specify timeout handling"
		}
	}

	// Check for cancellation
	if strings.Contains(criterionLower, "cancel") || strings.Contains(criterionLower, "context") {
		finding.HasCancellation = true
	}

	// Check for resource cleanup
	if strings.Contains(criterionLower, "cleanup") || strings.Contains(criterionLower, "defer") ||
		strings.Contains(criterionLower, "close") || strings.Contains(criterionLower, "release") {
		finding.HasResourceCleanup = true
	}

	// Check for idempotency
	if strings.Contains(criterionLower, "idempotent") || strings.Contains(criterionLower, "same result") {
		finding.PromiseType = "idempotency"
	}

	// Check for ordering
	if strings.Contains(criterionLower, "order") || strings.Contains(criterionLower, "sequence") ||
		strings.Contains(criterionLower, "before") || strings.Contains(criterionLower, "after") {
		finding.PromiseType = "ordering"
	}

	return finding
}

// DataModelAnalyzer analyzes data models in a plan.
type DataModelAnalyzer struct{}

// Analyze performs data model analysis on a plan/phase/requirement.
func (a *DataModelAnalyzer) Analyze(plan *PlanDocument, phase PhaseType, req *RequirementNode) (interface{}, error) {
	result := NewDataModelAnalysisResult()
	result.Phase = phase
	if req != nil {
		result.RequirementID = req.ID
	}

	// Analyze shared components for data model patterns
	if req != nil && req.Implementation != nil {
		for i, component := range req.Implementation.Shared {
			finding := a.analyzeComponent(req.ID, i, component)
			result.AddFinding(finding)
			result.StructCount++
		}
	}

	// Analyze description for data model patterns
	if req != nil {
		findings := a.analyzeDescription(req)
		for _, finding := range findings {
			result.AddFinding(finding)
		}
	}

	return result, nil
}

// analyzeComponent analyzes a component for data model patterns.
func (a *DataModelAnalyzer) analyzeComponent(reqID string, index int, component string) DataModelFinding {
	finding := DataModelFinding{
		ReviewFinding: ReviewFinding{
			ID:          fmt.Sprintf("%s-datamodel-%d", reqID, index),
			Component:   component,
			Description: fmt.Sprintf("Data structure: %s", component),
			Severity:    SeverityWellDefined,
		},
	}

	componentLower := strings.ToLower(component)

	// Check for relationship indicators
	if strings.Contains(componentLower, "list") || strings.Contains(componentLower, "array") ||
		strings.Contains(componentLower, "slice") {
		finding.RelationshipType = "1:N"
	} else if strings.Contains(componentLower, "map") || strings.Contains(componentLower, "many") {
		finding.RelationshipType = "N:M"
	}

	return finding
}

// analyzeDescription analyzes a requirement description for data model patterns.
func (a *DataModelAnalyzer) analyzeDescription(req *RequirementNode) []DataModelFinding {
	var findings []DataModelFinding

	descLower := strings.ToLower(req.Description)

	// Check for relationship patterns
	if strings.Contains(descLower, "one-to-one") || strings.Contains(descLower, "1:1") {
		findings = append(findings, DataModelFinding{
			ReviewFinding: ReviewFinding{
				ID:          fmt.Sprintf("%s-rel-1to1", req.ID),
				Component:   req.ID,
				Description: "One-to-one relationship identified",
				Severity:    SeverityWellDefined,
			},
			RelationshipType: "1:1",
		})
	}

	if strings.Contains(descLower, "one-to-many") || strings.Contains(descLower, "1:n") {
		findings = append(findings, DataModelFinding{
			ReviewFinding: ReviewFinding{
				ID:          fmt.Sprintf("%s-rel-1toN", req.ID),
				Component:   req.ID,
				Description: "One-to-many relationship identified",
				Severity:    SeverityWellDefined,
			},
			RelationshipType: "1:N",
		})
	}

	if strings.Contains(descLower, "many-to-many") || strings.Contains(descLower, "n:m") {
		findings = append(findings, DataModelFinding{
			ReviewFinding: ReviewFinding{
				ID:          fmt.Sprintf("%s-rel-NtoM", req.ID),
				Component:   req.ID,
				Description: "Many-to-many relationship identified",
				Severity:    SeverityWellDefined,
			},
			RelationshipType: "N:M",
		})
	}

	// Check for breaking change indicators
	if strings.Contains(descLower, "remove field") || strings.Contains(descLower, "change type") ||
		strings.Contains(descLower, "rename") {
		findings = append(findings, DataModelFinding{
			ReviewFinding: ReviewFinding{
				ID:             fmt.Sprintf("%s-breaking", req.ID),
				Component:     req.ID,
				Description:   "Potential breaking schema change",
				Severity:      SeverityWarning,
				Recommendation: "Ensure backward compatibility or migration strategy",
			},
			IsBreakingChange: true,
		})
	}

	// Check for validation patterns
	if strings.Contains(descLower, "validate") || strings.Contains(descLower, "constraint") ||
		strings.Contains(descLower, "required") || strings.Contains(descLower, "optional") {
		findings = append(findings, DataModelFinding{
			ReviewFinding: ReviewFinding{
				ID:          fmt.Sprintf("%s-validation", req.ID),
				Component:   req.ID,
				Description: "Validation rules identified",
				Severity:    SeverityWellDefined,
			},
			HasValidation: true,
		})
	}

	// If no specific patterns found, add a general finding
	if len(findings) == 0 {
		findings = append(findings, DataModelFinding{
			ReviewFinding: ReviewFinding{
				ID:          fmt.Sprintf("%s-datamodel-general", req.ID),
				Component:   req.ID,
				Description: req.Description,
				Severity:    SeverityWellDefined,
			},
		})
	}

	return findings
}

// APIAnalyzer analyzes APIs in a plan.
type APIAnalyzer struct{}

// Analyze performs API analysis on a plan/phase/requirement.
func (a *APIAnalyzer) Analyze(plan *PlanDocument, phase PhaseType, req *RequirementNode) (interface{}, error) {
	result := NewAPIAnalysisResult()
	result.Phase = phase
	if req != nil {
		result.RequirementID = req.ID
	}

	// Analyze backend components for API patterns
	if req != nil && req.Implementation != nil {
		for i, component := range req.Implementation.Backend {
			finding := a.analyzeComponent(req.ID, i, component)
			result.AddFinding(finding)
			result.EndpointCount++
		}
	}

	// Analyze acceptance criteria for API patterns
	if req != nil {
		for i, criterion := range req.AcceptanceCriteria {
			finding := a.analyzeCriterion(req.ID, i, criterion)
			if finding.Endpoint != "" || finding.HTTPMethod != "" {
				result.AddFinding(finding)
			}
		}
	}

	return result, nil
}

// analyzeComponent analyzes a component for API patterns.
func (a *APIAnalyzer) analyzeComponent(reqID string, index int, component string) APIFinding {
	finding := APIFinding{
		ReviewFinding: ReviewFinding{
			ID:          fmt.Sprintf("%s-api-%d", reqID, index),
			Component:   component,
			Description: fmt.Sprintf("API component: %s", component),
			Severity:    SeverityWellDefined,
		},
	}

	componentLower := strings.ToLower(component)

	// Detect HTTP method patterns
	if strings.Contains(componentLower, "handler") || strings.Contains(componentLower, "endpoint") ||
		strings.Contains(componentLower, "route") || strings.Contains(componentLower, "api") {

		// Try to detect HTTP method
		if strings.Contains(componentLower, "get") {
			finding.HTTPMethod = "GET"
		} else if strings.Contains(componentLower, "post") {
			finding.HTTPMethod = "POST"
		} else if strings.Contains(componentLower, "put") {
			finding.HTTPMethod = "PUT"
		} else if strings.Contains(componentLower, "delete") {
			finding.HTTPMethod = "DELETE"
		} else if strings.Contains(componentLower, "patch") {
			finding.HTTPMethod = "PATCH"
		}
	}

	return finding
}

// analyzeCriterion analyzes a criterion for API patterns.
func (a *APIAnalyzer) analyzeCriterion(reqID string, index int, criterion string) APIFinding {
	finding := APIFinding{
		ReviewFinding: ReviewFinding{
			ID:          fmt.Sprintf("%s-api-crit-%d", reqID, index),
			Component:   reqID,
			Description: criterion,
			Severity:    SeverityWellDefined,
		},
	}

	criterionLower := strings.ToLower(criterion)

	// Check for HTTP method patterns
	httpMethods := []string{"GET", "POST", "PUT", "DELETE", "PATCH"}
	for _, method := range httpMethods {
		if strings.Contains(strings.ToUpper(criterion), method) {
			finding.HTTPMethod = method
			break
		}
	}

	// Check for endpoint patterns
	if strings.Contains(criterionLower, "/api/") || strings.Contains(criterionLower, "/v1/") ||
		strings.Contains(criterionLower, "/v2/") || strings.Contains(criterion, "/{") {
		finding.Endpoint = extractEndpoint(criterion)
	}

	// Check for status codes
	statusCodePatterns := map[string]int{
		"200": 200, "201": 201, "204": 204,
		"400": 400, "401": 401, "403": 403, "404": 404,
		"500": 500,
	}
	for pattern, code := range statusCodePatterns {
		if strings.Contains(criterion, pattern) {
			finding.StatusCodes = append(finding.StatusCodes, code)
		}
	}

	// Check for content type
	if strings.Contains(criterionLower, "json") {
		finding.ContentType = "application/json"
	} else if strings.Contains(criterionLower, "xml") {
		finding.ContentType = "application/xml"
	}

	// Check for versioning
	if strings.Contains(criterionLower, "/v1/") || strings.Contains(criterionLower, "/v2/") {
		finding.VersioningScheme = "url"
	} else if strings.Contains(criterionLower, "api-version") {
		finding.VersioningScheme = "header"
	}

	// Check for deprecation
	if strings.Contains(criterionLower, "deprecated") || strings.Contains(criterionLower, "sunset") {
		finding.IsDeprecated = true
		finding.Severity = SeverityWarning
		finding.Recommendation = "Document deprecation timeline and migration path"
	}

	// Check for missing error handling
	expectedErrors := []string{"validation", "auth", "not found", "conflict", "rate limit"}
	for _, errCase := range expectedErrors {
		if strings.Contains(criterionLower, "error") && !strings.Contains(criterionLower, errCase) {
			// Note: This is a simplified check
		}
	}

	return finding
}

// extractEndpoint extracts an endpoint pattern from a criterion string.
func extractEndpoint(criterion string) string {
	// Simple extraction - find patterns like /api/... or /v1/...
	words := strings.Fields(criterion)
	for _, word := range words {
		if strings.HasPrefix(word, "/") && len(word) > 1 {
			// Clean up trailing punctuation
			return strings.TrimRight(word, ".,;:)")
		}
	}
	return ""
}

// PlanDocument represents a parsed plan file structure.
type PlanDocument struct {
	Path         string                 `json:"path"`
	Title        string                 `json:"title"`
	Phases       []PhaseType            `json:"phases"`
	Requirements *RequirementHierarchy  `json:"requirements,omitempty"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// LoadPlanDocument loads and parses a plan document from a file path.
func LoadPlanDocument(path string) (*PlanDocument, error) {
	content, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read plan file: %w", err)
	}

	doc := &PlanDocument{
		Path:     path,
		Phases:   make([]PhaseType, 0),
		Metadata: make(map[string]interface{}),
	}

	// Parse markdown content
	lines := strings.Split(string(content), "\n")
	for _, line := range lines {
		trimmed := strings.TrimSpace(line)

		// Extract title
		if strings.HasPrefix(trimmed, "# ") && doc.Title == "" {
			doc.Title = strings.TrimPrefix(trimmed, "# ")
		}
	}

	return doc, nil
}

// reviewRequirementTree recursively reviews a requirement node and its children.
func reviewRequirementTree(req *RequirementNode, phase PhaseType, analyzers map[ReviewStep]Analyzer) (map[ReviewStep]interface{}, error) {
	results := make(map[ReviewStep]interface{})

	// Run all analyzers on this requirement
	for step, analyzer := range analyzers {
		var result interface{}
		var err error

		switch a := analyzer.(type) {
		case *ContractAnalyzer:
			result, err = a.Analyze(nil, phase, req)
		case *InterfaceAnalyzer:
			result, err = a.Analyze(nil, phase, req)
		case *PromiseAnalyzer:
			result, err = a.Analyze(nil, phase, req)
		case *DataModelAnalyzer:
			result, err = a.Analyze(nil, phase, req)
		case *APIAnalyzer:
			result, err = a.Analyze(nil, phase, req)
		}

		if err != nil {
			return nil, fmt.Errorf("analyzer %s failed: %w", step.String(), err)
		}
		results[step] = result
	}

	// Recursively analyze children
	for _, child := range req.Children {
		childResults, err := reviewRequirementTree(child, phase, analyzers)
		if err != nil {
			return nil, err
		}
		// Merge child results (in a real implementation, you'd aggregate these)
		_ = childResults
	}

	return results, nil
}

// RunReview executes a plan review with the given configuration.
func RunReview(config ReviewConfig) *ReviewResult {
	startTime := time.Now()
	result := NewReviewResult()

	// Load the plan document
	plan, err := LoadPlanDocument(config.PlanPath)
	if err != nil {
		result.Success = false
		result.Error = err.Error()
		result.FailedAt = "load_plan"
		return result
	}

	// Initialize analyzers
	analyzers := map[ReviewStep]Analyzer{
		StepContracts:   &ContractAnalyzer{},
		StepInterfaces:  &InterfaceAnalyzer{},
		StepPromises:    &PromiseAnalyzer{},
		StepDataModels:  &DataModelAnalyzer{},
		StepAPIs:        &APIAnalyzer{},
	}

	// Determine which phases to review
	var phasesToReview []PhaseType
	if config.AllPhases {
		phasesToReview = AllPhases()
	} else if config.Phase != "" {
		phase, err := PhaseTypeFromString(config.Phase)
		if err != nil {
			result.Success = false
			result.Error = err.Error()
			result.FailedAt = "parse_phase"
			return result
		}
		phasesToReview = []PhaseType{phase}
	} else {
		// Default to all phases
		phasesToReview = AllPhases()
	}

	// Determine which steps to run
	var stepsToRun []ReviewStep
	if config.Step != "" {
		step, err := ReviewStepFromString(config.Step)
		if err != nil {
			result.Success = false
			result.Error = err.Error()
			result.FailedAt = "parse_step"
			return result
		}
		stepsToRun = []ReviewStep{step}
	} else {
		stepsToRun = AllReviewSteps()
	}

	// Run the review
	for _, phase := range phasesToReview {
		phaseResult := PhaseReviewResult{
			Phase:       phase,
			StepResults: make(map[ReviewStep]interface{}),
			Timestamp:   time.Now(),
		}

		for _, step := range stepsToRun {
			analyzer := analyzers[step]

			var stepResult interface{}
			var err error

			// If we have requirements, analyze them
			if plan.Requirements != nil && len(plan.Requirements.Requirements) > 0 {
				// Analyze each top-level requirement
				for _, req := range plan.Requirements.Requirements {
					results, err := reviewRequirementTree(req, phase, map[ReviewStep]Analyzer{step: analyzer})
					if err != nil {
						result.Success = false
						result.Error = err.Error()
						result.FailedAt = fmt.Sprintf("%s/%s", phase.String(), step.String())
						return result
					}
					stepResult = results[step]
				}
			} else {
				// No requirements - run analyzer with nil requirement
				switch a := analyzer.(type) {
				case *ContractAnalyzer:
					stepResult, err = a.Analyze(plan, phase, nil)
				case *InterfaceAnalyzer:
					stepResult, err = a.Analyze(plan, phase, nil)
				case *PromiseAnalyzer:
					stepResult, err = a.Analyze(plan, phase, nil)
				case *DataModelAnalyzer:
					stepResult, err = a.Analyze(plan, phase, nil)
				case *APIAnalyzer:
					stepResult, err = a.Analyze(plan, phase, nil)
				}
			}

			if err != nil {
				result.Success = false
				result.Error = err.Error()
				result.FailedAt = fmt.Sprintf("%s/%s", phase.String(), step.String())
				return result
			}

			phaseResult.StepResults[step] = stepResult
			result.StepResults[step] = stepResult

			// Aggregate counts
			if sr, ok := stepResult.(StepAnalysisResult); ok {
				counts := sr.GetCounts()
				phaseResult.Counts.WellDefined += counts.WellDefined
				phaseResult.Counts.Warning += counts.Warning
				phaseResult.Counts.Critical += counts.Critical
			}
		}

		result.PhaseResults[phase] = phaseResult
		result.ReviewedPhases = append(result.ReviewedPhases, phase)

		// Aggregate total counts
		result.TotalCounts.WellDefined += phaseResult.Counts.WellDefined
		result.TotalCounts.Warning += phaseResult.Counts.Warning
		result.TotalCounts.Critical += phaseResult.Counts.Critical
	}

	result.ReviewedSteps = stepsToRun
	result.DurationSeconds = time.Since(startTime).Seconds()

	// Generate output summary
	var summary strings.Builder
	summary.WriteString(fmt.Sprintf("Review completed in %.2f seconds\n", result.DurationSeconds))
	summary.WriteString(fmt.Sprintf("Phases reviewed: %d\n", len(result.ReviewedPhases)))
	summary.WriteString(fmt.Sprintf("Steps executed: %d\n", len(result.ReviewedSteps)))
	summary.WriteString(fmt.Sprintf("\nFindings Summary:\n"))
	summary.WriteString(fmt.Sprintf("  ✅ Well-defined: %d\n", result.TotalCounts.WellDefined))
	summary.WriteString(fmt.Sprintf("  ⚠️  Warnings: %d\n", result.TotalCounts.Warning))
	summary.WriteString(fmt.Sprintf("  ❌ Critical: %d\n", result.TotalCounts.Critical))

	result.Output = summary.String()

	// Write output file if specified
	if config.OutputPath != "" {
		outputData, err := json.MarshalIndent(result, "", "  ")
		if err == nil {
			os.WriteFile(config.OutputPath, outputData, 0644)
		}
	}

	// Check for critical issues
	if result.TotalCounts.Critical > 0 {
		result.Success = false
		result.Error = fmt.Sprintf("%d critical issues found", result.TotalCounts.Critical)
	}

	return result
}
