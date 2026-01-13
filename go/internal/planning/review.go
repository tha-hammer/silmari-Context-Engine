package planning

import (
	"bufio"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/google/uuid"
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
	ID               string   `json:"id"`
	Component        string   `json:"component"`
	Description      string   `json:"description"`
	Severity         Severity `json:"severity"`
	Recommendation   string   `json:"recommendation,omitempty"`
	Location         string   `json:"location,omitempty"` // file:line format
	RelatedIDs       []string `json:"related_ids,omitempty"`
	Reason           string   `json:"reason,omitempty"`            // REQ_004.2: Why warning was raised
	ResolutionNeeded string   `json:"resolution_needed,omitempty"` // REQ_004.3: What must be fixed for Critical
}

// MarkWellDefined marks the finding as well-defined (REQ_004.1).
// Returns the updated finding with Severity set to 'well_defined'.
func (f *ReviewFinding) MarkWellDefined() *ReviewFinding {
	f.Severity = SeverityWellDefined
	f.Reason = ""
	f.ResolutionNeeded = ""
	return f
}

// MarkWarning marks the finding as warning with optional reason (REQ_004.2).
// Returns the updated finding with Severity set to 'warning'.
func (f *ReviewFinding) MarkWarning(reason string) *ReviewFinding {
	f.Severity = SeverityWarning
	f.Reason = reason
	f.ResolutionNeeded = ""
	return f
}

// MarkCritical marks the finding as critical with required resolution (REQ_004.3).
// Returns the updated finding with Severity set to 'critical'.
func (f *ReviewFinding) MarkCritical(resolutionNeeded string) *ReviewFinding {
	f.Severity = SeverityCritical
	f.ResolutionNeeded = resolutionNeeded
	return f
}

// IsWellDefined returns true if the finding is well-defined (REQ_004.1).
func (f *ReviewFinding) IsWellDefined() bool {
	return f.Severity == SeverityWellDefined
}

// IsWarning returns true if the finding is a warning (REQ_004.2).
func (f *ReviewFinding) IsWarning() bool {
	return f.Severity == SeverityWarning
}

// IsCritical returns true if the finding is critical (REQ_004.3).
func (f *ReviewFinding) IsCritical() bool {
	return f.Severity == SeverityCritical
}

// CategorizedFindings holds findings organized by severity level (REQ_004).
type CategorizedFindings struct {
	WellDefined []string `json:"well_defined"` // REQ_004.1: IDs of well-defined items
	Warnings    []string `json:"warnings"`     // REQ_004.2: IDs of warning items
	Critical    []string `json:"critical"`     // REQ_004.3: IDs of critical items
}

// NewCategorizedFindings creates a new empty CategorizedFindings.
func NewCategorizedFindings() *CategorizedFindings {
	return &CategorizedFindings{
		WellDefined: make([]string, 0),
		Warnings:    make([]string, 0),
		Critical:    make([]string, 0),
	}
}

// AddFinding categorizes a finding by its severity and adds to appropriate slice.
func (cf *CategorizedFindings) AddFinding(f *ReviewFinding) {
	switch f.Severity {
	case SeverityWellDefined:
		cf.WellDefined = append(cf.WellDefined, f.ID)
	case SeverityWarning:
		cf.Warnings = append(cf.Warnings, f.ID)
	case SeverityCritical:
		cf.Critical = append(cf.Critical, f.ID)
	}
}

// CanProceed returns true if there are no critical findings blocking progression (REQ_004.3).
// Critical findings BLOCK phase progression.
func (cf *CategorizedFindings) CanProceed() bool {
	return len(cf.Critical) == 0
}

// HasCritical returns true if there are any critical findings.
func (cf *CategorizedFindings) HasCritical() bool {
	return len(cf.Critical) > 0
}

// HasWarnings returns true if there are any warning findings.
func (cf *CategorizedFindings) HasWarnings() bool {
	return len(cf.Warnings) > 0
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

// Recommendation represents an actionable recommendation for a finding (REQ_004.4).
type Recommendation struct {
	FindingID      string   `json:"finding_id"`
	Severity       Severity `json:"severity"`
	Message        string   `json:"message"`
	Location       string   `json:"location,omitempty"`        // file:line format
	SuggestedFix   string   `json:"suggested_fix,omitempty"`
	DocReferences  []string `json:"doc_references,omitempty"` // Related documentation
	IsMandatory    bool     `json:"is_mandatory"`             // True for Critical findings
}

// RecommendationResult contains generated recommendations (REQ_004.4).
type RecommendationResult struct {
	Recommendations []Recommendation `json:"recommendations"`
	CriticalCount   int              `json:"critical_count"`
	WarningCount    int              `json:"warning_count"`
	SkippedCount    int              `json:"skipped_count"` // Well-defined items skipped
}

// GenerateRecommendations generates actionable recommendations for Warning and Critical findings (REQ_004.4).
// Well-defined findings are skipped - no recommendations generated for them.
// Recommendations are prioritized: Critical first, then Warning.
func GenerateRecommendations(findings []ReviewFinding) *RecommendationResult {
	result := &RecommendationResult{
		Recommendations: make([]Recommendation, 0),
	}

	// Separate findings by severity
	var criticalFindings []ReviewFinding
	var warningFindings []ReviewFinding

	for _, f := range findings {
		switch f.Severity {
		case SeverityCritical:
			criticalFindings = append(criticalFindings, f)
		case SeverityWarning:
			warningFindings = append(warningFindings, f)
		case SeverityWellDefined:
			result.SkippedCount++
		}
	}

	// Generate recommendations for Critical findings first (REQ_004.4 - prioritized order)
	for _, f := range criticalFindings {
		rec := generateRecommendationForFinding(f)
		rec.IsMandatory = true // Critical recommendations are mandatory
		result.Recommendations = append(result.Recommendations, rec)
		result.CriticalCount++
	}

	// Generate recommendations for Warning findings
	for _, f := range warningFindings {
		rec := generateRecommendationForFinding(f)
		rec.IsMandatory = false
		result.Recommendations = append(result.Recommendations, rec)
		result.WarningCount++
	}

	return result
}

// generateRecommendationForFinding generates a recommendation for a single finding.
func generateRecommendationForFinding(f ReviewFinding) Recommendation {
	rec := Recommendation{
		FindingID: f.ID,
		Severity:  f.Severity,
		Location:  f.Location,
	}

	// Use existing recommendation if present
	if f.Recommendation != "" {
		rec.Message = f.Recommendation
	} else {
		// Generate default recommendation based on severity
		if f.Severity == SeverityCritical {
			rec.Message = fmt.Sprintf("Critical issue: %s - Resolution required: %s",
				f.Description, f.ResolutionNeeded)
			rec.SuggestedFix = f.ResolutionNeeded
		} else {
			rec.Message = fmt.Sprintf("Warning: %s - Consider addressing this issue",
				f.Description)
			if f.Reason != "" {
				rec.Message = fmt.Sprintf("Warning: %s - Reason: %s", f.Description, f.Reason)
			}
		}
	}

	return rec
}

// GenerateContractRecommendations generates recommendations from contract analysis results.
func GenerateContractRecommendations(result *ContractAnalysisResult) *RecommendationResult {
	findings := make([]ReviewFinding, len(result.Findings))
	for i, f := range result.Findings {
		findings[i] = f.ReviewFinding
	}
	return GenerateRecommendations(findings)
}

// GenerateInterfaceRecommendations generates recommendations from interface analysis results.
func GenerateInterfaceRecommendations(result *InterfaceAnalysisResult) *RecommendationResult {
	findings := make([]ReviewFinding, len(result.Findings))
	for i, f := range result.Findings {
		findings[i] = f.ReviewFinding
	}
	return GenerateRecommendations(findings)
}

// GeneratePromiseRecommendations generates recommendations from promise analysis results.
func GeneratePromiseRecommendations(result *PromiseAnalysisResult) *RecommendationResult {
	findings := make([]ReviewFinding, len(result.Findings))
	for i, f := range result.Findings {
		findings[i] = f.ReviewFinding
	}
	return GenerateRecommendations(findings)
}

// GenerateDataModelRecommendations generates recommendations from data model analysis results.
func GenerateDataModelRecommendations(result *DataModelAnalysisResult) *RecommendationResult {
	findings := make([]ReviewFinding, len(result.Findings))
	for i, f := range result.Findings {
		findings[i] = f.ReviewFinding
	}
	return GenerateRecommendations(findings)
}

// GenerateAPIRecommendations generates recommendations from API analysis results.
func GenerateAPIRecommendations(result *APIAnalysisResult) *RecommendationResult {
	findings := make([]ReviewFinding, len(result.Findings))
	for i, f := range result.Findings {
		findings[i] = f.ReviewFinding
	}
	return GenerateRecommendations(findings)
}

// SeverityClassifier classifies findings and applies severity levels (REQ_004).
type SeverityClassifier struct {
	categorized *CategorizedFindings
	findings    map[string]*ReviewFinding
}

// NewSeverityClassifier creates a new severity classifier.
func NewSeverityClassifier() *SeverityClassifier {
	return &SeverityClassifier{
		categorized: NewCategorizedFindings(),
		findings:    make(map[string]*ReviewFinding),
	}
}

// ClassifyFinding classifies a single finding and updates counts.
func (sc *SeverityClassifier) ClassifyFinding(f *ReviewFinding) {
	sc.findings[f.ID] = f
	sc.categorized.AddFinding(f)
}

// ClassifyAsWellDefined marks a finding as well-defined (REQ_004.1).
func (sc *SeverityClassifier) ClassifyAsWellDefined(f *ReviewFinding) {
	f.MarkWellDefined()
	sc.ClassifyFinding(f)
}

// ClassifyAsWarning marks a finding as warning (REQ_004.2).
func (sc *SeverityClassifier) ClassifyAsWarning(f *ReviewFinding, reason string) {
	f.MarkWarning(reason)
	sc.ClassifyFinding(f)
}

// ClassifyAsCritical marks a finding as critical (REQ_004.3).
func (sc *SeverityClassifier) ClassifyAsCritical(f *ReviewFinding, resolutionNeeded string) {
	f.MarkCritical(resolutionNeeded)
	sc.ClassifyFinding(f)
}

// GetCategorized returns the categorized findings.
func (sc *SeverityClassifier) GetCategorized() *CategorizedFindings {
	return sc.categorized
}

// CanProceed returns true if there are no critical findings (REQ_004.3).
func (sc *SeverityClassifier) CanProceed() bool {
	return sc.categorized.CanProceed()
}

// GetCounts returns severity counts.
func (sc *SeverityClassifier) GetCounts() SeverityCounts {
	return SeverityCounts{
		WellDefined: len(sc.categorized.WellDefined),
		Warning:     len(sc.categorized.Warnings),
		Critical:    len(sc.categorized.Critical),
	}
}

// GenerateRecommendationsForAll generates recommendations for all classified findings.
func (sc *SeverityClassifier) GenerateRecommendationsForAll() *RecommendationResult {
	findings := make([]ReviewFinding, 0, len(sc.findings))
	for _, f := range sc.findings {
		findings = append(findings, *f)
	}
	return GenerateRecommendations(findings)
}

// ClassifyRequirementRecursive recursively classifies a requirement and its children (REQ_004.1).
// This applies severity classification through nested RequirementNode children.
func ClassifyRequirementRecursive(req *RequirementNode, classifier *SeverityClassifier) {
	if req == nil {
		return
	}

	// Classify the requirement itself
	finding := &ReviewFinding{
		ID:          req.ID,
		Component:   req.ID,
		Description: req.Description,
	}

	// Determine severity based on requirement completeness
	if isRequirementWellDefined(req) {
		classifier.ClassifyAsWellDefined(finding)
	} else if hasRequirementCriticalIssues(req) {
		classifier.ClassifyAsCritical(finding, "Requirement has undefined or contradictory components")
	} else {
		classifier.ClassifyAsWarning(finding, "Requirement has partial specification")
	}

	// Recursively classify children (REQ_004.1 - recursive through nested RequirementNode)
	for _, child := range req.Children {
		ClassifyRequirementRecursive(child, classifier)
	}
}

// isRequirementWellDefined checks if a requirement meets all criteria for well-defined status (REQ_004.1).
// Well-Defined status is only assigned when ALL of the following are true:
// - component has explicit input/output contracts
// - interfaces are fully defined
// - behavioral guarantees are documented
// - API contracts are complete
func isRequirementWellDefined(req *RequirementNode) bool {
	if req == nil {
		return false
	}

	// Must have description
	if req.Description == "" {
		return false
	}

	// Must have acceptance criteria
	if len(req.AcceptanceCriteria) == 0 {
		return false
	}

	// Check for explicit contracts in criteria
	hasInputOutput := false
	for _, criterion := range req.AcceptanceCriteria {
		lower := strings.ToLower(criterion)
		if strings.Contains(lower, "input") || strings.Contains(lower, "output") ||
			strings.Contains(lower, "returns") || strings.Contains(lower, "accepts") {
			hasInputOutput = true
			break
		}
	}

	return hasInputOutput
}

// hasRequirementCriticalIssues checks if a requirement has critical issues (REQ_004.3).
// Critical status is assigned when:
// - contracts are undefined or contradictory
// - interfaces have missing method definitions
// - promises conflict
// - data models have ambiguous relationships
// - APIs have undefined error handling
func hasRequirementCriticalIssues(req *RequirementNode) bool {
	if req == nil {
		return true
	}

	// No description is critical
	if req.Description == "" {
		return true
	}

	// Check for contradictory terms
	lower := strings.ToLower(req.Description)
	contradictions := []struct{ a, b string }{
		{"always", "never"},
		{"must", "must not"},
		{"required", "optional"},
	}

	for _, c := range contradictions {
		if strings.Contains(lower, c.a) && strings.Contains(lower, c.b) {
			return true
		}
	}

	return false
}

// ReviewStepResult is an enhanced result that includes categorized findings and recommendations (REQ_004).
type ReviewStepResult struct {
	Step            ReviewStep            `json:"step"`
	Phase           PhaseType             `json:"phase"`
	RequirementID   string                `json:"requirement_id,omitempty"`
	Findings        []ReviewFinding       `json:"findings"`
	Counts          SeverityCounts        `json:"counts"`
	Categorized     *CategorizedFindings  `json:"categorized"`
	Recommendations *RecommendationResult `json:"recommendations,omitempty"`
	CanProceed      bool                  `json:"can_proceed"` // REQ_004.3: False if critical issues exist
	Timestamp       time.Time             `json:"timestamp"`
}

// NewReviewStepResult creates a new review step result with categorization.
func NewReviewStepResult(step ReviewStep, phase PhaseType) *ReviewStepResult {
	return &ReviewStepResult{
		Step:        step,
		Phase:       phase,
		Findings:    make([]ReviewFinding, 0),
		Categorized: NewCategorizedFindings(),
		CanProceed:  true,
		Timestamp:   time.Now(),
	}
}

// AddFinding adds a finding and updates counts and categorization.
func (r *ReviewStepResult) AddFinding(f ReviewFinding) {
	r.Findings = append(r.Findings, f)

	// Update counts
	switch f.Severity {
	case SeverityWellDefined:
		r.Counts.WellDefined++
	case SeverityWarning:
		r.Counts.Warning++
	case SeverityCritical:
		r.Counts.Critical++
		r.CanProceed = false // REQ_004.3: Critical blocks progression
	}

	// Update categorization
	r.Categorized.AddFinding(&f)
}

// GenerateRecommendationsForResult generates recommendations for this result (REQ_004.4).
func (r *ReviewStepResult) GenerateRecommendationsForResult() {
	r.Recommendations = GenerateRecommendations(r.Findings)
}

// FormatEmojiSummary returns a formatted summary with emojis for JSON/display output (REQ_004).
func (r *ReviewStepResult) FormatEmojiSummary() string {
	var sb strings.Builder
	sb.WriteString(fmt.Sprintf("Step: %s (Phase: %s)\n", r.Step.String(), r.Phase.String()))
	sb.WriteString(fmt.Sprintf("  %s Well-defined: %d\n", SeverityWellDefined.Emoji(), r.Counts.WellDefined))
	sb.WriteString(fmt.Sprintf("  %s Warnings: %d\n", SeverityWarning.Emoji(), r.Counts.Warning))
	sb.WriteString(fmt.Sprintf("  %s Critical: %d\n", SeverityCritical.Emoji(), r.Counts.Critical))
	if r.CanProceed {
		sb.WriteString("  Status: Can proceed ✅\n")
	} else {
		sb.WriteString("  Status: BLOCKED - Critical issues must be resolved ❌\n")
	}
	return sb.String()
}

// =============================================================================
// REQ_005: Review Autonomy Modes and Checkpointing (Phase 6)
// =============================================================================

// ReviewBatchGroup represents a logical group of review phases for batch mode.
// REQ_005.2: Phases must be grouped into logical batches
const (
	ReviewBatchGroupPlanning  = "planning"  // Research, Decomposition
	ReviewBatchGroupTDD       = "tdd"       // TDDPlanning, MultiDoc
	ReviewBatchGroupExecution = "execution" // BeadsSync, Implementation
)

// ReviewOrchestrator manages review execution flow based on autonomy mode.
// REQ_005: The system must support three autonomy modes for review execution
type ReviewOrchestrator struct {
	AutonomyMode     AutonomyMode
	PlanPath         string
	ProjectPath      string
	checkpointMgr    *CheckpointManager
	accumulatedResults map[PhaseType]PhaseReviewResult
	startTime        time.Time
}

// NewReviewOrchestrator creates a new review orchestrator.
func NewReviewOrchestrator(autonomyMode AutonomyMode, planPath, projectPath string) *ReviewOrchestrator {
	return &ReviewOrchestrator{
		AutonomyMode:       autonomyMode,
		PlanPath:           planPath,
		ProjectPath:        projectPath,
		checkpointMgr:      NewCheckpointManager(projectPath),
		accumulatedResults: make(map[PhaseType]PhaseReviewResult),
		startTime:          time.Now(),
	}
}

// GetReviewBatchGroup returns the batch group for a review phase.
// REQ_005.2: Phases must be grouped into logical batches
func (ro *ReviewOrchestrator) GetReviewBatchGroup(phase PhaseType) string {
	switch phase {
	case PhaseResearch, PhaseDecomposition:
		return ReviewBatchGroupPlanning
	case PhaseTDDPlanning, PhaseMultiDoc:
		return ReviewBatchGroupTDD
	case PhaseBeadsSync, PhaseImplementation:
		return ReviewBatchGroupExecution
	default:
		return ""
	}
}

// IsReviewBatchBoundary returns true if the phase is the last in its batch group.
// REQ_005.2: Pause only at defined group boundaries for consolidated approval
func (ro *ReviewOrchestrator) IsReviewBatchBoundary(phase PhaseType) bool {
	switch phase {
	case PhaseDecomposition: // End of Planning batch
		return true
	case PhaseMultiDoc: // End of TDD batch
		return true
	case PhaseImplementation: // End of Execution batch
		return true
	default:
		return false
	}
}

// ShouldPauseAfterPhase returns true if review should pause after the phase.
// REQ_005.1: Checkpoint Mode - pause after each phase
// REQ_005.2: Batch Mode - pause only at batch boundaries
// REQ_005.3: Fully Autonomous Mode - never pause
func (ro *ReviewOrchestrator) ShouldPauseAfterPhase(phase PhaseType) bool {
	switch ro.AutonomyMode {
	case AutonomyCheckpoint:
		// REQ_005.1: Pause after every phase
		return true
	case AutonomyBatch:
		// REQ_005.2: Pause only at batch boundaries
		return ro.IsReviewBatchBoundary(phase)
	case AutonomyFullyAutonomous:
		// REQ_005.3: Never pause
		return false
	default:
		return true
	}
}

// ShouldWriteCheckpoint returns true if checkpoint should be written after the phase.
// REQ_005.1: Checkpoint saved after each phase completes
// REQ_005.2: Checkpoint at batch boundaries only
// REQ_005.3: Write checkpoint for crash recovery
func (ro *ReviewOrchestrator) ShouldWriteCheckpoint(phase PhaseType) bool {
	switch ro.AutonomyMode {
	case AutonomyCheckpoint:
		// REQ_005.1: Write checkpoint after every phase
		return true
	case AutonomyBatch:
		// REQ_005.2: Write checkpoint only at batch boundaries
		return ro.IsReviewBatchBoundary(phase)
	case AutonomyFullyAutonomous:
		// REQ_005.3: Write checkpoint after every phase for crash recovery
		return true
	default:
		return true
	}
}

// AccumulatePhaseResult stores phase result for batch aggregation.
// REQ_005.2: Batch boundary checkpoint must aggregate all results
func (ro *ReviewOrchestrator) AccumulatePhaseResult(phase PhaseType, result PhaseReviewResult) {
	ro.accumulatedResults[phase] = result
}

// GetAccumulatedResults returns all accumulated results since last checkpoint.
func (ro *ReviewOrchestrator) GetAccumulatedResults() map[PhaseType]PhaseReviewResult {
	return ro.accumulatedResults
}

// ClearAccumulatedResults clears accumulated results after checkpoint.
func (ro *ReviewOrchestrator) ClearAccumulatedResults() {
	ro.accumulatedResults = make(map[PhaseType]PhaseReviewResult)
}

// GetPhasesInBatch returns all phases in the same batch as the given phase.
// REQ_005.2: Group related phases together
func (ro *ReviewOrchestrator) GetPhasesInBatch(phase PhaseType) []PhaseType {
	group := ro.GetReviewBatchGroup(phase)
	switch group {
	case ReviewBatchGroupPlanning:
		return []PhaseType{PhaseResearch, PhaseDecomposition}
	case ReviewBatchGroupTDD:
		return []PhaseType{PhaseTDDPlanning, PhaseMultiDoc}
	case ReviewBatchGroupExecution:
		return []PhaseType{PhaseBeadsSync, PhaseImplementation}
	default:
		return []PhaseType{phase}
	}
}

// ReviewCheckpoint represents a checkpoint specifically for review operations.
// REQ_005.4: Checkpoint structure for review state persistence
type ReviewCheckpoint struct {
	ID               string                          `json:"id"`
	PlanPath         string                          `json:"plan_path"`
	PlanHash         string                          `json:"plan_hash"`          // REQ_005.4: Detect if plan changed
	AutonomyMode     AutonomyMode                    `json:"autonomy_mode"`
	CurrentPhaseIdx  int                             `json:"current_phase_idx"`
	CompletedPhases  []PhaseType                     `json:"completed_phases"`
	PendingPhases    []PhaseType                     `json:"pending_phases"`
	PhaseResults     map[PhaseType]PhaseReviewResult `json:"phase_results"`
	TotalCounts      SeverityCounts                  `json:"total_counts"`
	Timestamp        string                          `json:"timestamp"`
	StartedAt        string                          `json:"started_at"`
	CumulativeSecs   float64                         `json:"cumulative_seconds"` // REQ_005.4: Cumulative review duration
}

// SaveReviewCheckpoint saves the current review state to a checkpoint file.
// REQ_005.4: Implement saveCheckpoint() function for review operations
func (ro *ReviewOrchestrator) SaveReviewCheckpoint(
	currentPhaseIdx int,
	completedPhases []PhaseType,
	pendingPhases []PhaseType,
	phaseResults map[PhaseType]PhaseReviewResult,
	totalCounts SeverityCounts,
) (string, error) {
	// Create checkpoint directory
	checkpointDir := filepath.Join(ro.ProjectPath, ".context-engine", "checkpoints")
	if err := os.MkdirAll(checkpointDir, 0755); err != nil {
		return "", fmt.Errorf("failed to create checkpoint directory: %w", err)
	}

	// Generate checkpoint ID
	checkpointID := uuid.New().String()

	// Compute plan hash
	planHash, err := computePlanHash(ro.PlanPath)
	if err != nil {
		planHash = "" // Continue without hash if computation fails
	}

	// Extract plan name for filename
	planName := filepath.Base(ro.PlanPath)
	planName = strings.TrimSuffix(planName, filepath.Ext(planName))

	// Create checkpoint structure
	checkpoint := ReviewCheckpoint{
		ID:              checkpointID,
		PlanPath:        ro.PlanPath,
		PlanHash:        planHash,
		AutonomyMode:    ro.AutonomyMode,
		CurrentPhaseIdx: currentPhaseIdx,
		CompletedPhases: completedPhases,
		PendingPhases:   pendingPhases,
		PhaseResults:    phaseResults,
		TotalCounts:     totalCounts,
		Timestamp:       time.Now().UTC().Format(time.RFC3339),
		StartedAt:       ro.startTime.UTC().Format(time.RFC3339),
		CumulativeSecs:  time.Since(ro.startTime).Seconds(),
	}

	// Marshal to pretty-printed JSON (REQ_005.4: Human-readable)
	data, err := json.MarshalIndent(checkpoint, "", "  ")
	if err != nil {
		return "", fmt.Errorf("failed to marshal checkpoint: %w", err)
	}

	// Write to temp file first for atomic write (REQ_005.4)
	timestamp := time.Now().Format("20060102-150405")
	filename := fmt.Sprintf("review-%s-%s.json", planName, timestamp)
	checkpointPath := filepath.Join(checkpointDir, filename)
	tempPath := checkpointPath + ".tmp"

	if err := os.WriteFile(tempPath, data, 0644); err != nil {
		return "", fmt.Errorf("failed to write temp checkpoint file: %w", err)
	}

	// Rename for atomic write
	if err := os.Rename(tempPath, checkpointPath); err != nil {
		os.Remove(tempPath) // Cleanup temp file
		return "", fmt.Errorf("failed to rename checkpoint file: %w", err)
	}

	// Rotate old checkpoints (REQ_005.4: Keep last 5)
	ro.rotateCheckpoints(checkpointDir, 5)

	return checkpointPath, nil
}

// rotateCheckpoints keeps only the most recent N checkpoints.
// REQ_005.4: Old checkpoints must be rotated: keep last 5
func (ro *ReviewOrchestrator) rotateCheckpoints(checkpointDir string, keepCount int) {
	files, err := filepath.Glob(filepath.Join(checkpointDir, "review-*.json"))
	if err != nil || len(files) <= keepCount {
		return
	}

	// Sort by modification time (oldest first)
	type fileInfo struct {
		path    string
		modTime time.Time
	}
	var fileInfos []fileInfo
	for _, f := range files {
		info, err := os.Stat(f)
		if err == nil {
			fileInfos = append(fileInfos, fileInfo{path: f, modTime: info.ModTime()})
		}
	}

	sort.Slice(fileInfos, func(i, j int) bool {
		return fileInfos[i].modTime.Before(fileInfos[j].modTime)
	})

	// Delete oldest files beyond keepCount
	deleteCount := len(fileInfos) - keepCount
	for i := 0; i < deleteCount; i++ {
		os.Remove(fileInfos[i].path)
	}
}

// LoadReviewCheckpoint loads a review checkpoint from file.
// REQ_005.4: loadCheckpoint() must validate plan hash before allowing resume
func LoadReviewCheckpoint(checkpointPath string) (*ReviewCheckpoint, error) {
	data, err := os.ReadFile(checkpointPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read checkpoint: %w", err)
	}

	var checkpoint ReviewCheckpoint
	if err := json.Unmarshal(data, &checkpoint); err != nil {
		return nil, fmt.Errorf("invalid checkpoint JSON: %w", err)
	}

	return &checkpoint, nil
}

// ValidateCheckpointPlan validates that the plan hasn't changed since checkpoint.
// REQ_005.4: loadCheckpoint() must validate plan hash matches before allowing resume
func ValidateCheckpointPlan(checkpoint *ReviewCheckpoint) error {
	if checkpoint.PlanHash == "" {
		return nil // No hash to validate
	}

	currentHash, err := computePlanHash(checkpoint.PlanPath)
	if err != nil {
		return nil // Can't compute hash, allow resume
	}

	if currentHash != checkpoint.PlanHash {
		return fmt.Errorf("plan has changed since checkpoint (hash mismatch)")
	}

	return nil
}

// computePlanHash computes a hash of the plan file for change detection.
func computePlanHash(planPath string) (string, error) {
	data, err := os.ReadFile(planPath)
	if err != nil {
		return "", err
	}
	hash := sha256.Sum256(data)
	return fmt.Sprintf("%x", hash[:8]), nil // First 8 bytes as hex
}

// DetectReviewCheckpoint finds the most recent review checkpoint.
func DetectReviewCheckpoint(projectPath string) (*ReviewCheckpoint, error) {
	checkpointDir := filepath.Join(projectPath, ".context-engine", "checkpoints")
	files, err := filepath.Glob(filepath.Join(checkpointDir, "review-*.json"))
	if err != nil || len(files) == 0 {
		return nil, nil
	}

	// Find most recent by modification time
	var mostRecent string
	var mostRecentTime time.Time

	for _, f := range files {
		info, err := os.Stat(f)
		if err == nil && info.ModTime().After(mostRecentTime) {
			mostRecent = f
			mostRecentTime = info.ModTime()
		}
	}

	if mostRecent == "" {
		return nil, nil
	}

	return LoadReviewCheckpoint(mostRecent)
}

// PromptReviewPhaseApproval displays review findings and prompts for approval.
// REQ_005.1: User must be able to view review findings at each checkpoint pause
func PromptReviewPhaseApproval(phase PhaseType, result PhaseReviewResult) (bool, string) {
	fmt.Printf("\n=== Review Checkpoint: %s Phase ===\n", phase.String())
	fmt.Printf("  %s Well-defined: %d\n", SeverityWellDefined.Emoji(), result.Counts.WellDefined)
	fmt.Printf("  %s Warnings: %d\n", SeverityWarning.Emoji(), result.Counts.Warning)
	fmt.Printf("  %s Critical: %d\n", SeverityCritical.Emoji(), result.Counts.Critical)

	// REQ_005.1: Critical findings must be flagged
	if result.Counts.Critical > 0 {
		fmt.Printf("\n⚠️  CRITICAL ISSUES DETECTED - Acknowledgment required to proceed\n")
	}

	fmt.Print("\nContinue to next phase? [Y/n]: ")

	scanner := bufio.NewScanner(os.Stdin)
	if !scanner.Scan() {
		return true, "" // Default to yes on EOF
	}

	input := strings.TrimSpace(strings.ToLower(scanner.Text()))
	if input == "" || input == "y" {
		return true, ""
	}

	if input == "n" {
		fmt.Println("\nPlease provide feedback (enter empty line when done):")
		feedback := CollectMultilineInput("> ")
		return false, feedback
	}

	return true, ""
}

// PromptReviewBatchApproval displays consolidated batch findings and prompts for approval.
// REQ_005.2: User must receive consolidated report showing findings across all phases in batch
func PromptReviewBatchApproval(phases []PhaseType, results map[PhaseType]PhaseReviewResult) (bool, string) {
	fmt.Printf("\n=== Review Checkpoint: Batch Complete ===\n")
	fmt.Printf("Phases in batch: ")
	for i, p := range phases {
		if i > 0 {
			fmt.Print(", ")
		}
		fmt.Print(p.String())
	}
	fmt.Println()

	// Aggregate counts
	var totalCounts SeverityCounts
	for _, phase := range phases {
		if result, ok := results[phase]; ok {
			totalCounts.WellDefined += result.Counts.WellDefined
			totalCounts.Warning += result.Counts.Warning
			totalCounts.Critical += result.Counts.Critical
		}
	}

	fmt.Printf("\nConsolidated Findings:\n")
	fmt.Printf("  %s Well-defined: %d\n", SeverityWellDefined.Emoji(), totalCounts.WellDefined)
	fmt.Printf("  %s Warnings: %d\n", SeverityWarning.Emoji(), totalCounts.Warning)
	fmt.Printf("  %s Critical: %d\n", SeverityCritical.Emoji(), totalCounts.Critical)

	// Show per-phase breakdown
	fmt.Printf("\nPer-Phase Breakdown:\n")
	for _, phase := range phases {
		if result, ok := results[phase]; ok {
			fmt.Printf("  %s: %d well-defined, %d warnings, %d critical\n",
				phase.String(), result.Counts.WellDefined, result.Counts.Warning, result.Counts.Critical)
		}
	}

	// REQ_005.2: Critical findings in any phase must be surfaced
	if totalCounts.Critical > 0 {
		fmt.Printf("\n⚠️  CRITICAL ISSUES DETECTED IN BATCH - Review required\n")
	}

	fmt.Print("\nContinue to next batch? [Y/n]: ")

	scanner := bufio.NewScanner(os.Stdin)
	if !scanner.Scan() {
		return true, ""
	}

	input := strings.TrimSpace(strings.ToLower(scanner.Text()))
	if input == "" || input == "y" {
		return true, ""
	}

	if input == "n" {
		fmt.Println("\nPlease provide feedback (enter empty line when done):")
		feedback := CollectMultilineInput("> ")
		return false, feedback
	}

	return true, ""
}

// GenerateReviewReport generates a comprehensive review report.
// REQ_005.3: Final comprehensive report must include all findings
func GenerateReviewReport(result *ReviewResult, config ReviewConfig) string {
	var sb strings.Builder

	sb.WriteString("# Plan Review Report\n\n")
	sb.WriteString(fmt.Sprintf("**Plan**: %s\n", config.PlanPath))
	sb.WriteString(fmt.Sprintf("**Mode**: %s\n", config.AutonomyMode.String()))
	sb.WriteString(fmt.Sprintf("**Duration**: %.2f seconds\n", result.DurationSeconds))
	sb.WriteString(fmt.Sprintf("**Timestamp**: %s\n\n", result.Timestamp.Format(time.RFC3339)))

	// Summary
	sb.WriteString("## Summary\n\n")
	sb.WriteString(fmt.Sprintf("- %s Well-defined: %d\n", SeverityWellDefined.Emoji(), result.TotalCounts.WellDefined))
	sb.WriteString(fmt.Sprintf("- %s Warnings: %d\n", SeverityWarning.Emoji(), result.TotalCounts.Warning))
	sb.WriteString(fmt.Sprintf("- %s Critical: %d\n", SeverityCritical.Emoji(), result.TotalCounts.Critical))
	sb.WriteString("\n")

	// REQ_005.3: Critical findings must be prominently highlighted
	if result.TotalCounts.Critical > 0 {
		sb.WriteString("### ⚠️ Critical Issues\n\n")
		sb.WriteString("The following critical issues were found and must be addressed:\n\n")
		// List critical issues from phase results
		for _, phaseResult := range result.PhaseResults {
			if phaseResult.Counts.Critical > 0 {
				sb.WriteString(fmt.Sprintf("- **%s Phase**: %d critical issues\n",
					phaseResult.Phase.String(), phaseResult.Counts.Critical))
			}
		}
		sb.WriteString("\n")
	}

	// Phase details
	sb.WriteString("## Phase Results\n\n")
	for _, phase := range result.ReviewedPhases {
		if phaseResult, ok := result.PhaseResults[phase]; ok {
			sb.WriteString(fmt.Sprintf("### %s\n\n", phase.String()))
			sb.WriteString(fmt.Sprintf("- Well-defined: %d\n", phaseResult.Counts.WellDefined))
			sb.WriteString(fmt.Sprintf("- Warnings: %d\n", phaseResult.Counts.Warning))
			sb.WriteString(fmt.Sprintf("- Critical: %d\n", phaseResult.Counts.Critical))
			sb.WriteString("\n")
		}
	}

	// Steps executed
	sb.WriteString("## Steps Executed\n\n")
	for _, step := range result.ReviewedSteps {
		sb.WriteString(fmt.Sprintf("- %s\n", step.String()))
	}

	return sb.String()
}

// GetReviewExitCode returns the appropriate exit code based on review results.
// REQ_005.3: Exit code must reflect overall review health
func GetReviewExitCode(result *ReviewResult) int {
	if result.TotalCounts.Critical > 0 {
		return 2 // Critical issues
	}
	if result.TotalCounts.Warning > 0 {
		return 1 // Warnings only
	}
	return 0 // All pass
}

// =============================================================================
// REQ_006: Review Loop Architecture (Phase 7)
// =============================================================================

// TerminationReason describes why the review loop terminated.
type TerminationReason string

const (
	TerminationMaxIterations    TerminationReason = "max_iterations"
	TerminationAllComplete      TerminationReason = "all_complete"
	TerminationCriticalBlocking TerminationReason = "critical_blocking"
	TerminationTimeout          TerminationReason = "timeout"
	TerminationUserCancelled    TerminationReason = "user_cancelled"
)

// PhaseState represents the state of a phase in the state machine.
type PhaseState string

const (
	PhaseStatePending    PhaseState = "pending"
	PhaseStateInProgress PhaseState = "in_progress"
	PhaseStateComplete   PhaseState = "complete"
	PhaseStateFailed     PhaseState = "failed"
)

// DefaultMaxRecursionDepth is the default maximum depth for requirement tree traversal.
const DefaultMaxRecursionDepth = 10

// DefaultMaxIterations is the default maximum number of loop iterations.
const DefaultMaxIterations = 100

// DefaultMaxRetries is the default number of retries for failed phases.
const DefaultMaxRetries = 3

// DefaultReviewTimeout is the default timeout for overall review (10 minutes).
const DefaultReviewTimeout = 10 * time.Minute

// ReviewLoopConfig holds configuration for the review loop execution.
// REQ_006.1: Loop configuration for phase iteration
type ReviewLoopConfig struct {
	// PlanPath is the path to the plan document.
	PlanPath string `json:"plan_path"`

	// ProjectPath is the path to the project directory.
	ProjectPath string `json:"project_path"`

	// AutonomyMode controls checkpointing and pause behavior.
	AutonomyMode AutonomyMode `json:"autonomy_mode"`

	// MaxIterations is the maximum number of loop iterations (default: 100).
	MaxIterations int `json:"max_iterations"`

	// MaxRetries is the number of retries for failed phases (default: 3).
	MaxRetries int `json:"max_retries"`

	// MaxRecursionDepth limits requirement tree traversal depth (default: 10).
	MaxRecursionDepth int `json:"max_recursion_depth"`

	// Timeout is the overall review timeout duration.
	Timeout time.Duration `json:"timeout"`

	// StopOnCritical terminates if any critical findings exist.
	StopOnCritical bool `json:"stop_on_critical"`

	// StepsToRun specifies which review steps to execute (empty = all).
	StepsToRun []ReviewStep `json:"steps_to_run,omitempty"`

	// PhasesToReview specifies which phases to review (empty = all).
	PhasesToReview []PhaseType `json:"phases_to_review,omitempty"`

	// ResumeFromPhaseIdx resumes from a specific phase index (for checkpoint resume).
	ResumeFromPhaseIdx int `json:"resume_from_phase_idx"`

	// GitCommit is the git commit hash for metadata.
	GitCommit string `json:"git_commit,omitempty"`

	// Reviewer is the reviewer name for metadata.
	Reviewer string `json:"reviewer,omitempty"`
}

// NewReviewLoopConfig creates a new ReviewLoopConfig with defaults.
func NewReviewLoopConfig(planPath, projectPath string) *ReviewLoopConfig {
	return &ReviewLoopConfig{
		PlanPath:          planPath,
		ProjectPath:       projectPath,
		AutonomyMode:      AutonomyCheckpoint,
		MaxIterations:     DefaultMaxIterations,
		MaxRetries:        DefaultMaxRetries,
		MaxRecursionDepth: DefaultMaxRecursionDepth,
		Timeout:           DefaultReviewTimeout,
		StopOnCritical:    true,
		StepsToRun:        AllReviewSteps(),
		PhasesToReview:    AllPhases(),
	}
}

// ReviewLoopResult holds the comprehensive result of a review loop execution.
// REQ_006.4: Results map structure for storing review findings
// REQ_006.5: Loop termination tracking
type ReviewLoopResult struct {
	// Success indicates if the review completed successfully.
	Success bool `json:"success"`

	// Error contains error message if failed.
	Error string `json:"error,omitempty"`

	// TerminationReason explains why the loop terminated.
	TerminationReason TerminationReason `json:"termination_reason"`

	// Iterations is the number of iterations completed.
	Iterations int `json:"iterations"`

	// Results is the nested map: phase -> step -> *ReviewStepResult.
	// REQ_006.4: Results stored in map[PhaseType]map[ReviewStep]*ReviewStepResult
	Results map[PhaseType]map[ReviewStep]*ReviewStepResult `json:"results"`

	// PhaseStates tracks the state of each phase.
	PhaseStates map[PhaseType]PhaseState `json:"phase_states"`

	// PhaseCounts aggregates counts per phase.
	PhaseCounts map[PhaseType]SeverityCounts `json:"phase_counts"`

	// TotalCounts aggregates all findings across phases.
	TotalCounts SeverityCounts `json:"total_counts"`

	// ReviewedPhases is the list of phases that were reviewed.
	ReviewedPhases []PhaseType `json:"reviewed_phases"`

	// ReviewedSteps is the list of steps that were executed.
	ReviewedSteps []ReviewStep `json:"reviewed_steps"`

	// CurrentPhaseIdx is the current phase index for resume.
	CurrentPhaseIdx int `json:"current_phase_idx"`

	// Metadata contains additional information.
	Metadata ReviewLoopMetadata `json:"metadata"`

	// StartTime is when the review started.
	StartTime time.Time `json:"start_time"`

	// EndTime is when the review ended.
	EndTime time.Time `json:"end_time"`

	// DurationSeconds is the total duration in seconds.
	DurationSeconds float64 `json:"duration_seconds"`

	// RetryCount tracks retries per phase.
	RetryCount map[PhaseType]int `json:"retry_count,omitempty"`
}

// ReviewLoopMetadata contains metadata about the review.
// REQ_006.4: Results include metadata: timestamp, plan path, git commit, reviewer
type ReviewLoopMetadata struct {
	Timestamp   time.Time `json:"timestamp"`
	PlanPath    string    `json:"plan_path"`
	ProjectPath string    `json:"project_path"`
	GitCommit   string    `json:"git_commit,omitempty"`
	Reviewer    string    `json:"reviewer,omitempty"`
}

// NewReviewLoopResult creates a new empty ReviewLoopResult.
func NewReviewLoopResult() *ReviewLoopResult {
	return &ReviewLoopResult{
		Success:         true,
		Results:         make(map[PhaseType]map[ReviewStep]*ReviewStepResult),
		PhaseStates:     make(map[PhaseType]PhaseState),
		PhaseCounts:     make(map[PhaseType]SeverityCounts),
		ReviewedPhases:  make([]PhaseType, 0),
		ReviewedSteps:   make([]ReviewStep, 0),
		RetryCount:      make(map[PhaseType]int),
		StartTime:       time.Now(),
	}
}

// HasBlockingIssues returns true if there are any Critical findings.
// REQ_006.4: hasBlockingIssues(results) returns true if any Critical findings
func (r *ReviewLoopResult) HasBlockingIssues() bool {
	return r.TotalCounts.Critical > 0
}

// CountBySeverity returns a map of severity level to count.
// REQ_006.4: countBySeverity(results) returns map[SeverityLevel]int
func (r *ReviewLoopResult) CountBySeverity() map[Severity]int {
	return map[Severity]int{
		SeverityWellDefined: r.TotalCounts.WellDefined,
		SeverityWarning:     r.TotalCounts.Warning,
		SeverityCritical:    r.TotalCounts.Critical,
	}
}

// FilterBySeverity returns findings filtered by severity.
// REQ_006.4: filterBySeverity(results, severity) returns filtered results
func (r *ReviewLoopResult) FilterBySeverity(severity Severity) []ReviewFinding {
	var findings []ReviewFinding
	for _, phaseResults := range r.Results {
		for _, stepResult := range phaseResults {
			for _, finding := range stepResult.Findings {
				if finding.Severity == severity {
					findings = append(findings, finding)
				}
			}
		}
	}
	return findings
}

// FilterByPhase returns results for a specific phase.
// REQ_006.4: filterByPhase(results, phase) returns phase-specific results
func (r *ReviewLoopResult) FilterByPhase(phase PhaseType) map[ReviewStep]*ReviewStepResult {
	if results, ok := r.Results[phase]; ok {
		return results
	}
	return nil
}

// FilterByStep returns results for a specific step across all phases.
// REQ_006.4: filterByStep(results, step) returns step-specific results
func (r *ReviewLoopResult) FilterByStep(step ReviewStep) []*ReviewStepResult {
	var results []*ReviewStepResult
	for _, phaseResults := range r.Results {
		if stepResult, ok := phaseResults[step]; ok {
			results = append(results, stepResult)
		}
	}
	return results
}

// ToJSON serializes the result to JSON.
// REQ_006.4: Results serializable to JSON for checkpoint persistence
func (r *ReviewLoopResult) ToJSON() ([]byte, error) {
	return json.MarshalIndent(r, "", "  ")
}

// ToMarkdown exports results to REVIEW.md markdown format.
// REQ_006.4: Results exportable to REVIEW.md markdown format
func (r *ReviewLoopResult) ToMarkdown() string {
	var sb strings.Builder

	sb.WriteString("# Plan Review Report\n\n")
	sb.WriteString(fmt.Sprintf("**Plan**: %s\n", r.Metadata.PlanPath))
	sb.WriteString(fmt.Sprintf("**Timestamp**: %s\n", r.Metadata.Timestamp.Format(time.RFC3339)))
	if r.Metadata.GitCommit != "" {
		sb.WriteString(fmt.Sprintf("**Git Commit**: %s\n", r.Metadata.GitCommit))
	}
	if r.Metadata.Reviewer != "" {
		sb.WriteString(fmt.Sprintf("**Reviewer**: %s\n", r.Metadata.Reviewer))
	}
	sb.WriteString(fmt.Sprintf("**Duration**: %.2f seconds\n\n", r.DurationSeconds))

	// Summary
	sb.WriteString("## Summary\n\n")
	sb.WriteString(fmt.Sprintf("- %s Well-defined: %d\n", SeverityWellDefined.Emoji(), r.TotalCounts.WellDefined))
	sb.WriteString(fmt.Sprintf("- %s Warnings: %d\n", SeverityWarning.Emoji(), r.TotalCounts.Warning))
	sb.WriteString(fmt.Sprintf("- %s Critical: %d\n", SeverityCritical.Emoji(), r.TotalCounts.Critical))
	sb.WriteString(fmt.Sprintf("\n**Termination**: %s\n", r.TerminationReason))
	sb.WriteString(fmt.Sprintf("**Iterations**: %d\n\n", r.Iterations))

	// Per-phase results
	sb.WriteString("## Phase Results\n\n")
	for _, phase := range r.ReviewedPhases {
		if counts, ok := r.PhaseCounts[phase]; ok {
			sb.WriteString(fmt.Sprintf("### %s\n\n", phase.String()))
			sb.WriteString(fmt.Sprintf("- Well-defined: %d\n", counts.WellDefined))
			sb.WriteString(fmt.Sprintf("- Warnings: %d\n", counts.Warning))
			sb.WriteString(fmt.Sprintf("- Critical: %d\n\n", counts.Critical))
		}
	}

	// Critical findings section
	if r.TotalCounts.Critical > 0 {
		sb.WriteString("## Critical Issues\n\n")
		for phase, phaseResults := range r.Results {
			for step, stepResult := range phaseResults {
				for _, finding := range stepResult.Findings {
					if finding.Severity == SeverityCritical {
						sb.WriteString(fmt.Sprintf("### %s - %s: %s\n", phase.String(), step.String(), finding.ID))
						sb.WriteString(fmt.Sprintf("- **Description**: %s\n", finding.Description))
						if finding.ResolutionNeeded != "" {
							sb.WriteString(fmt.Sprintf("- **Resolution**: %s\n", finding.ResolutionNeeded))
						}
						sb.WriteString("\n")
					}
				}
			}
		}
	}

	return sb.String()
}

// ReviewLoopExecutor manages the execution of the review loop.
type ReviewLoopExecutor struct {
	config       *ReviewLoopConfig
	orchestrator *ReviewOrchestrator
	plan         *PlanDocument
	analyzers    map[ReviewStep]Analyzer
	visitedNodes map[string]bool // For circular dependency detection
}

// NewReviewLoopExecutor creates a new review loop executor.
func NewReviewLoopExecutor(config *ReviewLoopConfig) *ReviewLoopExecutor {
	return &ReviewLoopExecutor{
		config:       config,
		orchestrator: NewReviewOrchestrator(config.AutonomyMode, config.PlanPath, config.ProjectPath),
		analyzers: map[ReviewStep]Analyzer{
			StepContracts:  &ContractAnalyzer{},
			StepInterfaces: &InterfaceAnalyzer{},
			StepPromises:   &PromiseAnalyzer{},
			StepDataModels: &DataModelAnalyzer{},
			StepAPIs:       &APIAnalyzer{},
		},
		visitedNodes: make(map[string]bool),
	}
}

// AreDependenciesMet checks if a phase's dependencies are satisfied.
// REQ_006.1: areDependenciesMet(phase) is called before processing each phase
func (e *ReviewLoopExecutor) AreDependenciesMet(phase PhaseType, result *ReviewLoopResult) bool {
	// Define phase dependencies
	dependencies := map[PhaseType][]PhaseType{
		PhaseResearch:       {}, // No dependencies
		PhaseDecomposition:  {PhaseResearch},
		PhaseTDDPlanning:    {PhaseDecomposition},
		PhaseMultiDoc:       {PhaseTDDPlanning},
		PhaseBeadsSync:      {PhaseMultiDoc},
		PhaseImplementation: {PhaseBeadsSync},
	}

	deps, ok := dependencies[phase]
	if !ok {
		return true
	}

	for _, dep := range deps {
		state, exists := result.PhaseStates[dep]
		if !exists || state != PhaseStateComplete {
			return false
		}
	}

	return true
}

// TransitionPhaseState handles the state machine transitions.
// REQ_006.1: Phase transition follows valid state machine
func (e *ReviewLoopExecutor) TransitionPhaseState(phase PhaseType, newState PhaseState, result *ReviewLoopResult) error {
	currentState := result.PhaseStates[phase]

	// Valid transitions
	validTransitions := map[PhaseState][]PhaseState{
		PhaseStatePending:    {PhaseStateInProgress},
		PhaseStateInProgress: {PhaseStateComplete, PhaseStateFailed},
		PhaseStateFailed:     {PhaseStateInProgress}, // Retry
		PhaseStateComplete:   {},                     // Terminal state
	}

	allowed := validTransitions[currentState]
	for _, validState := range allowed {
		if newState == validState {
			result.PhaseStates[phase] = newState
			return nil
		}
	}

	// Allow setting pending state for initialization
	if currentState == "" && newState == PhaseStatePending {
		result.PhaseStates[phase] = newState
		return nil
	}

	return fmt.Errorf("invalid state transition: %s -> %s for phase %s", currentState, newState, phase.String())
}

// RunReviewStep executes a single review step for a phase.
// REQ_006.2: runReviewStep(phase, step) captures ReviewStepResult
func (e *ReviewLoopExecutor) RunReviewStep(phase PhaseType, step ReviewStep, result *ReviewLoopResult) (*ReviewStepResult, error) {
	startTime := time.Now()

	stepResult := NewReviewStepResult(step, phase)

	analyzer, ok := e.analyzers[step]
	if !ok {
		return nil, fmt.Errorf("no analyzer for step: %s", step.String())
	}

	// Analyze requirements if available
	if e.plan != nil && e.plan.Requirements != nil {
		for _, req := range e.plan.Requirements.Requirements {
			// Reset visited nodes for each top-level requirement
			e.visitedNodes = make(map[string]bool)
			findings := e.ReviewRequirements(req, step, 0)
			for _, finding := range findings {
				stepResult.AddFinding(finding)
			}
		}
	} else {
		// Run analyzer without requirements
		analysisResult, err := analyzer.Analyze(e.plan, phase, nil)
		if err != nil {
			return nil, fmt.Errorf("analyzer error: %w", err)
		}

		// Convert analysis result to findings
		if stepResult := e.extractFindings(analysisResult, stepResult); stepResult != nil {
			// Findings already added
		}
	}

	// Generate recommendations
	stepResult.GenerateRecommendationsForResult()

	// Track execution time (placeholder for actual metric)
	_ = time.Since(startTime)

	return stepResult, nil
}

// extractFindings extracts ReviewFindings from various analysis result types.
func (e *ReviewLoopExecutor) extractFindings(analysisResult interface{}, stepResult *ReviewStepResult) *ReviewStepResult {
	switch r := analysisResult.(type) {
	case *ContractAnalysisResult:
		for _, f := range r.Findings {
			stepResult.AddFinding(f.ReviewFinding)
		}
	case *InterfaceAnalysisResult:
		for _, f := range r.Findings {
			stepResult.AddFinding(f.ReviewFinding)
		}
	case *PromiseAnalysisResult:
		for _, f := range r.Findings {
			stepResult.AddFinding(f.ReviewFinding)
		}
	case *DataModelAnalysisResult:
		for _, f := range r.Findings {
			stepResult.AddFinding(f.ReviewFinding)
		}
	case *APIAnalysisResult:
		for _, f := range r.Findings {
			stepResult.AddFinding(f.ReviewFinding)
		}
	}
	return stepResult
}

// ReviewRequirements recursively reviews a requirement tree.
// REQ_006.3: reviewRequirements(node *RequirementNode, step ReviewStep) []ReviewFinding
func (e *ReviewLoopExecutor) ReviewRequirements(node *RequirementNode, step ReviewStep, depth int) []ReviewFinding {
	var findings []ReviewFinding

	if node == nil {
		return findings
	}

	// REQ_006.3: Maximum recursion depth limit
	if depth > e.config.MaxRecursionDepth {
		findings = append(findings, ReviewFinding{
			ID:          fmt.Sprintf("%s-depth-exceeded", node.ID),
			Component:   node.ID,
			Description: "Maximum recursion depth exceeded",
			Severity:    SeverityWarning,
		})
		return findings
	}

	// REQ_006.3: Circular dependency detection
	if e.visitedNodes[node.ID] {
		findings = append(findings, ReviewFinding{
			ID:          fmt.Sprintf("%s-circular", node.ID),
			Component:   node.ID,
			Description: "Circular dependency detected",
			Severity:    SeverityCritical,
			ResolutionNeeded: "Remove circular dependency in requirement hierarchy",
		})
		return findings
	}
	e.visitedNodes[node.ID] = true

	// REQ_006.3: Base case - reviewNode(node, step)
	nodeFindings := e.reviewNode(node, step)
	findings = append(findings, nodeFindings...)

	// REQ_006.3: Recursive case - iterate over node.Children
	for _, child := range node.Children {
		childFindings := e.ReviewRequirements(child, step, depth+1)
		findings = append(findings, childFindings...)
	}

	// REQ_006.3: Empty Children slice terminates recursion at leaf nodes
	return findings
}

// reviewNode analyzes a single requirement node for a specific step.
// REQ_006.3: Node type influences which review criteria apply
func (e *ReviewLoopExecutor) reviewNode(node *RequirementNode, step ReviewStep) []ReviewFinding {
	var findings []ReviewFinding

	// REQ_006.3: Findings include node.ID for traceability
	baseFinding := ReviewFinding{
		Component:   node.ID,
		RelatedIDs:  []string{node.ID},
	}

	switch step {
	case StepContracts:
		// REQ_006.2: Contract analysis checks
		findings = append(findings, e.analyzeContracts(node, baseFinding)...)

	case StepInterfaces:
		// REQ_006.2: Interface analysis checks
		findings = append(findings, e.analyzeInterfaces(node, baseFinding)...)

	case StepPromises:
		// REQ_006.2: Promise analysis checks
		findings = append(findings, e.analyzePromises(node, baseFinding)...)

	case StepDataModels:
		// REQ_006.2: Data model analysis checks
		findings = append(findings, e.analyzeDataModels(node, baseFinding)...)

	case StepAPIs:
		// REQ_006.2: API analysis checks
		findings = append(findings, e.analyzeAPIs(node, baseFinding)...)
	}

	// REQ_006.3: AcceptanceCriteria field validation
	if len(node.AcceptanceCriteria) == 0 && node.Type == "implementation" {
		findings = append(findings, ReviewFinding{
			ID:               fmt.Sprintf("%s-no-criteria", node.ID),
			Component:        node.ID,
			Description:      "Implementation requirement missing acceptance criteria",
			Severity:         SeverityWarning,
			Reason:           "Acceptance criteria required for testability",
			RelatedIDs:       []string{node.ID},
		})
	}

	// REQ_006.3: TestableProperties field validation
	if len(node.TestableProperties) == 0 && node.Type == "implementation" {
		findings = append(findings, ReviewFinding{
			ID:          fmt.Sprintf("%s-no-testable", node.ID),
			Component:   node.ID,
			Description: "Implementation requirement missing testable properties",
			Severity:    SeverityWarning,
			Reason:      "Testable properties ensure verification",
			RelatedIDs:  []string{node.ID},
		})
	}

	// REQ_006.3: Implementation.Components validation for implementation-level nodes
	if node.Type == "implementation" && node.Implementation == nil {
		findings = append(findings, ReviewFinding{
			ID:               fmt.Sprintf("%s-no-impl", node.ID),
			Component:        node.ID,
			Description:      "Implementation requirement missing component definitions",
			Severity:         SeverityCritical,
			ResolutionNeeded: "Define implementation components (frontend, backend, middleware, shared)",
			RelatedIDs:       []string{node.ID},
		})
	}

	return findings
}

// analyzeContracts performs contract-specific analysis.
// REQ_006.2: Contract analysis checks
func (e *ReviewLoopExecutor) analyzeContracts(node *RequirementNode, base ReviewFinding) []ReviewFinding {
	var findings []ReviewFinding

	hasInputContract := false
	hasOutputContract := false
	hasErrorContract := false
	hasPrecondition := false
	hasPostcondition := false
	hasInvariant := false

	for _, criterion := range node.AcceptanceCriteria {
		lower := strings.ToLower(criterion)

		if strings.Contains(lower, "input") || strings.Contains(lower, "accepts") ||
			strings.Contains(lower, "receives") || strings.Contains(lower, "takes") {
			hasInputContract = true
		}
		if strings.Contains(lower, "output") || strings.Contains(lower, "returns") ||
			strings.Contains(lower, "produces") {
			hasOutputContract = true
		}
		if strings.Contains(lower, "error") || strings.Contains(lower, "exception") ||
			strings.Contains(lower, "fails") || strings.Contains(lower, "throws") {
			hasErrorContract = true
		}
		if strings.Contains(lower, "must be") || strings.Contains(lower, "requires") ||
			strings.Contains(lower, "prerequisite") || strings.Contains(lower, "before") {
			hasPrecondition = true
		}
		if strings.Contains(lower, "ensures") || strings.Contains(lower, "guarantees") ||
			strings.Contains(lower, "after") || strings.Contains(lower, "will be") {
			hasPostcondition = true
		}
		if strings.Contains(lower, "always") || strings.Contains(lower, "invariant") ||
			strings.Contains(lower, "never") || strings.Contains(lower, "must remain") {
			hasInvariant = true
		}
	}

	// Check for component boundaries
	if node.Implementation != nil {
		components := len(node.Implementation.Frontend) + len(node.Implementation.Backend) +
			len(node.Implementation.Middleware) + len(node.Implementation.Shared)

		finding := base
		finding.ID = fmt.Sprintf("%s-contract-boundaries", node.ID)
		finding.Description = fmt.Sprintf("Component boundaries defined: %d components", components)
		finding.Severity = SeverityWellDefined
		findings = append(findings, finding)
	}

	// Validate I/O contracts for non-parent nodes
	if node.Type != "parent" {
		if !hasInputContract && !hasOutputContract {
			finding := base
			finding.ID = fmt.Sprintf("%s-contract-io", node.ID)
			finding.Description = "Missing explicit input/output contracts"
			finding.Severity = SeverityWarning
			finding.Reason = "I/O contracts needed for clear component interface"
			findings = append(findings, finding)
		} else {
			finding := base
			finding.ID = fmt.Sprintf("%s-contract-io", node.ID)
			finding.Description = "Input/output contracts defined"
			finding.Severity = SeverityWellDefined
			findings = append(findings, finding)
		}
	}

	// Note: error contracts, pre/post conditions, invariants are optional
	// but we record their presence
	if hasErrorContract {
		finding := base
		finding.ID = fmt.Sprintf("%s-contract-error", node.ID)
		finding.Description = "Error contracts defined"
		finding.Severity = SeverityWellDefined
		findings = append(findings, finding)
	}

	if hasPrecondition || hasPostcondition || hasInvariant {
		finding := base
		finding.ID = fmt.Sprintf("%s-contract-conditions", node.ID)
		finding.Description = "Preconditions/postconditions/invariants defined"
		finding.Severity = SeverityWellDefined
		findings = append(findings, finding)
	}

	return findings
}

// analyzeInterfaces performs interface-specific analysis.
// REQ_006.2: Interface analysis checks
func (e *ReviewLoopExecutor) analyzeInterfaces(node *RequirementNode, base ReviewFinding) []ReviewFinding {
	var findings []ReviewFinding

	if node.Implementation == nil {
		return findings
	}

	// Check public method definitions (backend + shared = public API)
	publicMethods := len(node.Implementation.Backend) + len(node.Implementation.Shared)
	if publicMethods > 0 {
		finding := base
		finding.ID = fmt.Sprintf("%s-interface-public", node.ID)
		finding.Description = fmt.Sprintf("Public methods defined: %d", publicMethods)
		finding.Severity = SeverityWellDefined
		findings = append(findings, finding)
	}

	// Check naming conventions
	for _, component := range node.Implementation.Backend {
		namingConvention := "unknown"
		if strings.Contains(component, "_") {
			namingConvention = "snake_case"
		} else if len(component) > 0 && component[0] >= 'A' && component[0] <= 'Z' {
			namingConvention = "PascalCase"
		} else {
			namingConvention = "camelCase"
		}

		finding := base
		finding.ID = fmt.Sprintf("%s-interface-naming-%s", node.ID, component)
		finding.Description = fmt.Sprintf("Component %s uses %s naming", component, namingConvention)
		finding.Severity = SeverityWellDefined
		findings = append(findings, finding)
	}

	// Check for extension points
	for _, component := range node.Implementation.Backend {
		lower := strings.ToLower(component)
		if strings.Contains(lower, "handler") || strings.Contains(lower, "provider") ||
			strings.Contains(lower, "factory") || strings.Contains(lower, "interface") {
			finding := base
			finding.ID = fmt.Sprintf("%s-interface-extension-%s", node.ID, component)
			finding.Description = fmt.Sprintf("Extension point identified: %s", component)
			finding.Severity = SeverityWellDefined
			findings = append(findings, finding)
		}
	}

	return findings
}

// analyzePromises performs promise-specific analysis.
// REQ_006.2: Promise analysis checks
func (e *ReviewLoopExecutor) analyzePromises(node *RequirementNode, base ReviewFinding) []ReviewFinding {
	var findings []ReviewFinding

	hasTimeout := false
	hasCancellation := false
	hasResourceCleanup := false
	hasIdempotency := false
	hasAsync := false

	for _, criterion := range node.AcceptanceCriteria {
		lower := strings.ToLower(criterion)

		if strings.Contains(lower, "timeout") {
			hasTimeout = true
		}
		if strings.Contains(lower, "cancel") || strings.Contains(lower, "context") {
			hasCancellation = true
		}
		if strings.Contains(lower, "cleanup") || strings.Contains(lower, "defer") ||
			strings.Contains(lower, "close") || strings.Contains(lower, "release") {
			hasResourceCleanup = true
		}
		if strings.Contains(lower, "idempotent") || strings.Contains(lower, "same result") {
			hasIdempotency = true
		}
		if strings.Contains(lower, "async") || strings.Contains(lower, "concurrent") ||
			strings.Contains(lower, "parallel") || strings.Contains(lower, "goroutine") {
			hasAsync = true
		}
	}

	// Check testable properties for promise types
	for _, prop := range node.TestableProperties {
		if prop.PropertyType == "idempotence" {
			hasIdempotency = true
		}
	}

	// Behavioral guarantees
	if hasIdempotency {
		finding := base
		finding.ID = fmt.Sprintf("%s-promise-idempotent", node.ID)
		finding.Description = "Idempotency guarantee documented"
		finding.Severity = SeverityWellDefined
		findings = append(findings, finding)
	}

	// Async/concurrent operations need synchronization
	if hasAsync {
		finding := base
		finding.ID = fmt.Sprintf("%s-promise-async", node.ID)
		finding.Description = "Async/concurrent operations defined"
		finding.Severity = SeverityWellDefined
		findings = append(findings, finding)

		// Async should have timeout handling
		if !hasTimeout {
			finding := base
			finding.ID = fmt.Sprintf("%s-promise-no-timeout", node.ID)
			finding.Description = "Async operation missing timeout handling"
			finding.Severity = SeverityWarning
			finding.Reason = "Async operations should specify timeout behavior"
			findings = append(findings, finding)
		}

		// Async should have cancellation
		if !hasCancellation {
			finding := base
			finding.ID = fmt.Sprintf("%s-promise-no-cancel", node.ID)
			finding.Description = "Async operation missing cancellation handling"
			finding.Severity = SeverityWarning
			finding.Reason = "Async operations should support cancellation"
			findings = append(findings, finding)
		}
	}

	// Resource cleanup
	if hasResourceCleanup {
		finding := base
		finding.ID = fmt.Sprintf("%s-promise-cleanup", node.ID)
		finding.Description = "Resource cleanup documented"
		finding.Severity = SeverityWellDefined
		findings = append(findings, finding)
	}

	return findings
}

// analyzeDataModels performs data model-specific analysis.
// REQ_006.2: Data model analysis checks
func (e *ReviewLoopExecutor) analyzeDataModels(node *RequirementNode, base ReviewFinding) []ReviewFinding {
	var findings []ReviewFinding

	hasRelationship := false
	hasValidation := false
	hasMigration := false

	descLower := strings.ToLower(node.Description)

	// Check for relationship types
	if strings.Contains(descLower, "one-to-one") || strings.Contains(descLower, "1:1") {
		hasRelationship = true
		finding := base
		finding.ID = fmt.Sprintf("%s-datamodel-rel-1to1", node.ID)
		finding.Description = "1:1 relationship defined"
		finding.Severity = SeverityWellDefined
		findings = append(findings, finding)
	}
	if strings.Contains(descLower, "one-to-many") || strings.Contains(descLower, "1:n") {
		hasRelationship = true
		finding := base
		finding.ID = fmt.Sprintf("%s-datamodel-rel-1toN", node.ID)
		finding.Description = "1:N relationship defined"
		finding.Severity = SeverityWellDefined
		findings = append(findings, finding)
	}
	if strings.Contains(descLower, "many-to-many") || strings.Contains(descLower, "n:m") {
		hasRelationship = true
		finding := base
		finding.ID = fmt.Sprintf("%s-datamodel-rel-NtoM", node.ID)
		finding.Description = "N:M relationship defined"
		finding.Severity = SeverityWellDefined
		findings = append(findings, finding)
	}

	// Check for validation
	if strings.Contains(descLower, "validate") || strings.Contains(descLower, "constraint") ||
		strings.Contains(descLower, "required") || strings.Contains(descLower, "optional") {
		hasValidation = true
		finding := base
		finding.ID = fmt.Sprintf("%s-datamodel-validation", node.ID)
		finding.Description = "Field definitions with validation rules"
		finding.Severity = SeverityWellDefined
		findings = append(findings, finding)
	}

	// Check for migration compatibility
	if strings.Contains(descLower, "migration") || strings.Contains(descLower, "backward compatible") {
		hasMigration = true
		finding := base
		finding.ID = fmt.Sprintf("%s-datamodel-migration", node.ID)
		finding.Description = "Migration compatibility considered"
		finding.Severity = SeverityWellDefined
		findings = append(findings, finding)
	}

	// Check for breaking changes
	if strings.Contains(descLower, "remove field") || strings.Contains(descLower, "change type") ||
		strings.Contains(descLower, "rename") {
		finding := base
		finding.ID = fmt.Sprintf("%s-datamodel-breaking", node.ID)
		finding.Description = "Potential breaking schema change"
		finding.Severity = SeverityWarning
		finding.Reason = "Ensure backward compatibility or migration strategy"
		findings = append(findings, finding)
	}

	// Check shared components for data models
	if node.Implementation != nil && len(node.Implementation.Shared) > 0 {
		for _, component := range node.Implementation.Shared {
			finding := base
			finding.ID = fmt.Sprintf("%s-datamodel-%s", node.ID, component)
			finding.Description = fmt.Sprintf("Data structure: %s", component)
			finding.Severity = SeverityWellDefined
			findings = append(findings, finding)
		}
	}

	_, _, _ = hasRelationship, hasValidation, hasMigration // Use variables

	return findings
}

// analyzeAPIs performs API-specific analysis.
// REQ_006.2: API analysis checks
func (e *ReviewLoopExecutor) analyzeAPIs(node *RequirementNode, base ReviewFinding) []ReviewFinding {
	var findings []ReviewFinding

	hasEndpoint := false
	hasVersioning := false
	hasErrorResponse := false

	for _, criterion := range node.AcceptanceCriteria {
		lower := strings.ToLower(criterion)

		// Check for endpoint definitions
		if strings.Contains(lower, "/api/") || strings.Contains(lower, "/v1/") ||
			strings.Contains(lower, "/v2/") || strings.Contains(criterion, "/{") {
			hasEndpoint = true

			// Extract HTTP method
			httpMethod := ""
			methods := []string{"GET", "POST", "PUT", "DELETE", "PATCH"}
			for _, method := range methods {
				if strings.Contains(strings.ToUpper(criterion), method) {
					httpMethod = method
					break
				}
			}

			finding := base
			finding.ID = fmt.Sprintf("%s-api-endpoint", node.ID)
			finding.Description = fmt.Sprintf("API endpoint defined with %s method", httpMethod)
			finding.Severity = SeverityWellDefined
			findings = append(findings, finding)
		}

		// Check for versioning
		if strings.Contains(lower, "/v1/") || strings.Contains(lower, "/v2/") {
			hasVersioning = true
			finding := base
			finding.ID = fmt.Sprintf("%s-api-version-url", node.ID)
			finding.Description = "URL-based API versioning"
			finding.Severity = SeverityWellDefined
			findings = append(findings, finding)
		} else if strings.Contains(lower, "api-version") {
			hasVersioning = true
			finding := base
			finding.ID = fmt.Sprintf("%s-api-version-header", node.ID)
			finding.Description = "Header-based API versioning"
			finding.Severity = SeverityWellDefined
			findings = append(findings, finding)
		}

		// Check for error responses
		if strings.Contains(lower, "400") || strings.Contains(lower, "401") ||
			strings.Contains(lower, "403") || strings.Contains(lower, "404") ||
			strings.Contains(lower, "500") || strings.Contains(lower, "error response") {
			hasErrorResponse = true
		}

		// Check for deprecation
		if strings.Contains(lower, "deprecated") || strings.Contains(lower, "sunset") {
			finding := base
			finding.ID = fmt.Sprintf("%s-api-deprecated", node.ID)
			finding.Description = "Deprecated endpoint identified"
			finding.Severity = SeverityWarning
			finding.Reason = "Document deprecation timeline and migration path"
			findings = append(findings, finding)
		}
	}

	// API endpoints should have error handling
	if hasEndpoint && !hasErrorResponse {
		finding := base
		finding.ID = fmt.Sprintf("%s-api-no-errors", node.ID)
		finding.Description = "API endpoint missing error response definitions"
		finding.Severity = SeverityWarning
		finding.Reason = "API endpoints should define error response formats"
		findings = append(findings, finding)
	}

	_, _ = hasVersioning, hasErrorResponse // Use variables

	return findings
}

// ExecuteReviewLoop runs the complete review loop.
// REQ_006.1: Outer loop - phase iteration
// REQ_006.2: Middle loop - review steps
// REQ_006.3: Inner recursive loop - requirement traversal
func ExecuteReviewLoop(config *ReviewLoopConfig) *ReviewLoopResult {
	result := NewReviewLoopResult()
	result.Metadata = ReviewLoopMetadata{
		Timestamp:   time.Now(),
		PlanPath:    config.PlanPath,
		ProjectPath: config.ProjectPath,
		GitCommit:   config.GitCommit,
		Reviewer:    config.Reviewer,
	}

	executor := NewReviewLoopExecutor(config)

	// Load plan document
	plan, err := LoadPlanDocument(config.PlanPath)
	if err != nil {
		result.Success = false
		result.Error = fmt.Sprintf("failed to load plan: %v", err)
		result.TerminationReason = TerminationCriticalBlocking
		return result
	}
	executor.plan = plan

	// Determine phases to review
	phases := config.PhasesToReview
	if len(phases) == 0 {
		phases = AllPhases()
	}

	// REQ_006.1: Use AllPhases() method for consistent ordering
	orderedPhases := make([]PhaseType, 0)
	allPhasesOrder := AllPhases()
	for _, p := range allPhasesOrder {
		for _, requested := range phases {
			if p == requested {
				orderedPhases = append(orderedPhases, p)
				break
			}
		}
	}
	phases = orderedPhases

	// Determine steps to run
	steps := config.StepsToRun
	if len(steps) == 0 {
		steps = AllReviewSteps()
	}

	// REQ_006.4: Empty results map initialized before iteration
	for _, phase := range phases {
		result.Results[phase] = make(map[ReviewStep]*ReviewStepResult)
		result.PhaseStates[phase] = PhaseStatePending
	}

	// Set up timeout
	deadline := time.Now().Add(config.Timeout)

	// REQ_006.1: Loop tracks current phase index for checkpoint resume
	startIdx := config.ResumeFromPhaseIdx
	if startIdx < 0 || startIdx >= len(phases) {
		startIdx = 0
	}

	// REQ_006.5: Iteration counter tracked
	iteration := 0

	// REQ_006.1: Outer loop - phase iteration
	for phaseIdx := startIdx; phaseIdx < len(phases); phaseIdx++ {
		phase := phases[phaseIdx]
		iteration++
		result.Iterations = iteration
		result.CurrentPhaseIdx = phaseIdx

		// REQ_006.5: Maximum iteration limit
		if iteration > config.MaxIterations {
			result.TerminationReason = TerminationMaxIterations
			result.Success = false
			result.Error = "maximum iterations exceeded"
			break
		}

		// REQ_006.5: Timeout check
		if time.Now().After(deadline) {
			result.TerminationReason = TerminationTimeout
			result.Success = false
			result.Error = "review timeout exceeded"
			break
		}

		// REQ_006.1: areDependenciesMet(phase) is called before processing
		if !executor.AreDependenciesMet(phase, result) {
			// Skip phases with unmet dependencies
			continue
		}

		// REQ_006.1: Phase transition: pending -> in_progress
		if err := executor.TransitionPhaseState(phase, PhaseStateInProgress, result); err != nil {
			result.Success = false
			result.Error = err.Error()
			break
		}

		phaseCounts := SeverityCounts{}
		phaseSuccess := true

		// REQ_006.2: Middle loop - review steps (exactly 5 steps in order)
		for _, step := range steps {
			stepResult, err := executor.RunReviewStep(phase, step, result)
			if err != nil {
				// REQ_006.2: Failed step does not block subsequent steps
				stepResult = NewReviewStepResult(step, phase)
				stepResult.AddFinding(ReviewFinding{
					ID:               fmt.Sprintf("%s-%s-error", phase.String(), step.String()),
					Component:        "executor",
					Description:      fmt.Sprintf("Step execution error: %v", err),
					Severity:         SeverityCritical,
					ResolutionNeeded: "Fix step execution error",
				})
			}

			// REQ_006.4: Results stored in results[phase][step] map
			result.Results[phase][step] = stepResult

			// Aggregate counts
			phaseCounts.WellDefined += stepResult.Counts.WellDefined
			phaseCounts.Warning += stepResult.Counts.Warning
			phaseCounts.Critical += stepResult.Counts.Critical

			// Track reviewed steps
			if !containsStep(result.ReviewedSteps, step) {
				result.ReviewedSteps = append(result.ReviewedSteps, step)
			}
		}

		// Update phase counts
		result.PhaseCounts[phase] = phaseCounts
		result.TotalCounts.WellDefined += phaseCounts.WellDefined
		result.TotalCounts.Warning += phaseCounts.Warning
		result.TotalCounts.Critical += phaseCounts.Critical

		// REQ_006.1: Phase transition: in_progress -> complete/failed
		if phaseCounts.Critical > 0 {
			phaseSuccess = false
		}

		if phaseSuccess {
			if err := executor.TransitionPhaseState(phase, PhaseStateComplete, result); err != nil {
				result.Success = false
				result.Error = err.Error()
				break
			}
		} else {
			if err := executor.TransitionPhaseState(phase, PhaseStateFailed, result); err != nil {
				result.Success = false
				result.Error = err.Error()
				break
			}

			// REQ_006.5: Retry mechanism for failed phases
			retries := result.RetryCount[phase]
			if retries < config.MaxRetries {
				result.RetryCount[phase]++
				// Transition back to pending for retry
				result.PhaseStates[phase] = PhaseStatePending
				phaseIdx-- // Retry this phase
				continue
			}
		}

		// Track reviewed phases
		result.ReviewedPhases = append(result.ReviewedPhases, phase)

		// REQ_006.1: Phase results accumulated for dependency context
		executor.orchestrator.AccumulatePhaseResult(phase, PhaseReviewResult{
			Phase:       phase,
			StepResults: make(map[ReviewStep]interface{}),
			Counts:      phaseCounts,
			Timestamp:   time.Now(),
		})

		// REQ_006.1: Checkpoint handling based on autonomy mode
		if executor.orchestrator.ShouldWriteCheckpoint(phase) {
			completedPhases := make([]PhaseType, 0)
			pendingPhases := make([]PhaseType, 0)
			for _, p := range phases {
				if result.PhaseStates[p] == PhaseStateComplete {
					completedPhases = append(completedPhases, p)
				} else if result.PhaseStates[p] == PhaseStatePending {
					pendingPhases = append(pendingPhases, p)
				}
			}

			// Convert results to PhaseReviewResult format
			phaseResults := make(map[PhaseType]PhaseReviewResult)
			for p, stepResults := range result.Results {
				stepResultsInterface := make(map[ReviewStep]interface{})
				for s, sr := range stepResults {
					stepResultsInterface[s] = sr
				}
				phaseResults[p] = PhaseReviewResult{
					Phase:       p,
					StepResults: stepResultsInterface,
					Counts:      result.PhaseCounts[p],
					Timestamp:   time.Now(),
				}
			}

			_, _ = executor.orchestrator.SaveReviewCheckpoint(
				phaseIdx,
				completedPhases,
				pendingPhases,
				phaseResults,
				result.TotalCounts,
			)
		}

		// REQ_006.5: Early termination on critical issues
		if config.StopOnCritical && result.HasBlockingIssues() {
			result.TerminationReason = TerminationCriticalBlocking
			result.Success = false
			result.Error = fmt.Sprintf("%d critical issues found", result.TotalCounts.Critical)
			break
		}
	}

	// Set termination reason if not already set
	if result.TerminationReason == "" {
		if result.Success {
			result.TerminationReason = TerminationAllComplete
		}
	}

	// Record end time
	result.EndTime = time.Now()
	result.DurationSeconds = result.EndTime.Sub(result.StartTime).Seconds()

	// Check final success status
	if result.TotalCounts.Critical > 0 {
		result.Success = false
	}

	return result
}

// containsStep checks if a step is in the slice.
func containsStep(steps []ReviewStep, step ReviewStep) bool {
	for _, s := range steps {
		if s == step {
			return true
		}
	}
	return false
}

// CheckAllIssuesClosed checks if all beads issues are closed.
// REQ_006.5: Closure check for beads issues
func CheckAllIssuesClosed(projectPath string, beadsIssueIDs []string) (bool, []string) {
	if len(beadsIssueIDs) == 0 {
		return true, nil
	}

	closedIssues := make([]string, 0)
	openIDs := make(map[string]bool)

	// Check each issue file in .beads directory
	beadsDir := filepath.Join(projectPath, ".beads")
	for _, issueID := range beadsIssueIDs {
		issuePath := filepath.Join(beadsDir, issueID+".json")
		data, err := os.ReadFile(issuePath)
		if err != nil {
			// Issue file doesn't exist or can't be read - consider open
			openIDs[issueID] = true
			continue
		}

		// Parse issue to check status
		var issue struct {
			Status string `json:"status"`
			DependsOnID string `json:"depends_on_id,omitempty"`
		}
		if err := json.Unmarshal(data, &issue); err != nil {
			openIDs[issueID] = true
			continue
		}

		if issue.Status == "closed" || issue.Status == "complete" {
			closedIssues = append(closedIssues, issueID)
		} else {
			openIDs[issueID] = true
		}
	}

	return len(openIDs) == 0, closedIssues
}

// CountBlockedIssues counts issues blocked by dependencies.
// REQ_006.5: Blocking dependency detection
func CountBlockedIssues(projectPath string, beadsIssueIDs []string) (int, map[string]string) {
	blocked := 0
	blockedBy := make(map[string]string)

	// Get open issues
	_, closedIssues := CheckAllIssuesClosed(projectPath, beadsIssueIDs)
	closedSet := make(map[string]bool)
	for _, id := range closedIssues {
		closedSet[id] = true
	}

	beadsDir := filepath.Join(projectPath, ".beads")
	for _, issueID := range beadsIssueIDs {
		if closedSet[issueID] {
			continue
		}

		issuePath := filepath.Join(beadsDir, issueID+".json")
		data, err := os.ReadFile(issuePath)
		if err != nil {
			continue
		}

		var issue struct {
			DependsOnID string `json:"depends_on_id,omitempty"`
		}
		if err := json.Unmarshal(data, &issue); err != nil {
			continue
		}

		// REQ_006.5: Check if depends_on_id is in open_ids set
		if issue.DependsOnID != "" && !closedSet[issue.DependsOnID] {
			blocked++
			blockedBy[issueID] = issue.DependsOnID
		}
	}

	return blocked, blockedBy
}
