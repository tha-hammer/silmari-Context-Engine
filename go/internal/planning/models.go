// Package planning provides planning pipeline data structures and logic.
package planning

import (
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"
)

// Valid requirement types for RequirementNode.
var ValidRequirementTypes = map[string]bool{
	"parent":         true,
	"sub_process":    true,
	"implementation": true,
}

// Valid property types for TestableProperty.
var ValidPropertyTypes = map[string]bool{
	"invariant":   true,
	"round_trip":  true,
	"idempotence": true,
	"oracle":      true,
}

// Valid categories for RequirementNode.
var ValidCategories = map[string]bool{
	"functional":     true,
	"non_functional": true,
	"security":       true,
	"performance":    true,
	"usability":      true,
	"integration":    true,
}

// ImplementationComponents categorizes implementation work into architectural layers.
type ImplementationComponents struct {
	Frontend   []string `json:"frontend,omitempty"`
	Backend    []string `json:"backend,omitempty"`
	Middleware []string `json:"middleware,omitempty"`
	Shared     []string `json:"shared,omitempty"`
}

// TestableProperty maps acceptance criteria to property-based tests.
type TestableProperty struct {
	Criterion          string `json:"criterion"`
	PropertyType       string `json:"property_type"`
	HypothesisStrategy string `json:"hypothesis_strategy,omitempty"`
	TestSkeleton       string `json:"test_skeleton,omitempty"`
}

// Validate checks that the TestableProperty has valid values.
func (tp *TestableProperty) Validate() error {
	if !ValidPropertyTypes[tp.PropertyType] {
		return fmt.Errorf("invalid property type: %s", tp.PropertyType)
	}
	return nil
}

// RequirementNode represents a hierarchical requirement (3-tier structure).
// Format: parent → sub_process → implementation
type RequirementNode struct {
	ID                 string                    `json:"id"`
	Description        string                    `json:"description"`
	Type               string                    `json:"type"`
	ParentID           string                    `json:"parent_id,omitempty"`
	Children           []*RequirementNode        `json:"children,omitempty"`
	AcceptanceCriteria []string                  `json:"acceptance_criteria,omitempty"`
	Implementation     *ImplementationComponents `json:"implementation,omitempty"`
	TestableProperties []*TestableProperty       `json:"testable_properties,omitempty"`
	FunctionID         string                    `json:"function_id,omitempty"`
	RelatedConcepts    []string                  `json:"related_concepts,omitempty"`
	Category           string                    `json:"category,omitempty"`
}

// Validate checks that the RequirementNode has valid values.
func (r *RequirementNode) Validate() error {
	if !ValidRequirementTypes[r.Type] {
		return fmt.Errorf("invalid requirement type: %s (valid: parent, sub_process, implementation)", r.Type)
	}
	if strings.TrimSpace(r.Description) == "" {
		return errors.New("description cannot be empty")
	}
	if r.Category != "" && !ValidCategories[r.Category] {
		return fmt.Errorf("invalid category: %s", r.Category)
	}
	// Validate testable properties
	for _, tp := range r.TestableProperties {
		if err := tp.Validate(); err != nil {
			return fmt.Errorf("testable property error: %w", err)
		}
	}
	return nil
}

// AddChild adds a child requirement node and sets parent_id.
func (r *RequirementNode) AddChild(child *RequirementNode) {
	child.ParentID = r.ID
	r.Children = append(r.Children, child)
}

// GetByID searches recursively for a requirement by ID.
func (r *RequirementNode) GetByID(id string) *RequirementNode {
	if r.ID == id {
		return r
	}
	for _, child := range r.Children {
		if found := child.GetByID(id); found != nil {
			return found
		}
	}
	return nil
}

// NextChildID generates the next child ID for this node.
// Pattern: parent_id.N where N is the next sequential number.
func (r *RequirementNode) NextChildID() string {
	nextNum := len(r.Children) + 1
	return fmt.Sprintf("%s.%d", r.ID, nextNum)
}

// RequirementHierarchy is a container for top-level requirements with metadata.
type RequirementHierarchy struct {
	Requirements []*RequirementNode     `json:"requirements"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// NewRequirementHierarchy creates a new empty hierarchy.
func NewRequirementHierarchy() *RequirementHierarchy {
	return &RequirementHierarchy{
		Requirements: make([]*RequirementNode, 0),
		Metadata:     make(map[string]interface{}),
	}
}

// AddRequirement adds a top-level requirement.
func (h *RequirementHierarchy) AddRequirement(req *RequirementNode) {
	h.Requirements = append(h.Requirements, req)
}

// AddChild adds a child requirement to a parent by ID.
func (h *RequirementHierarchy) AddChild(parentID string, child *RequirementNode) error {
	parent := h.GetByID(parentID)
	if parent == nil {
		return fmt.Errorf("parent requirement not found: %s", parentID)
	}
	parent.AddChild(child)
	return nil
}

// GetByID searches recursively for a requirement by ID.
func (h *RequirementHierarchy) GetByID(id string) *RequirementNode {
	for _, req := range h.Requirements {
		if found := req.GetByID(id); found != nil {
			return found
		}
	}
	return nil
}

// NextChildID generates the next child ID for a given parent.
func (h *RequirementHierarchy) NextChildID(parentID string) (string, error) {
	parent := h.GetByID(parentID)
	if parent == nil {
		return "", fmt.Errorf("parent requirement not found: %s", parentID)
	}
	return parent.NextChildID(), nil
}

// NextTopLevelID generates the next top-level requirement ID.
// Pattern: REQ_XXX where XXX is a zero-padded number.
func (h *RequirementHierarchy) NextTopLevelID() string {
	return fmt.Sprintf("REQ_%03d", len(h.Requirements))
}

// Validate validates all requirements in the hierarchy.
func (h *RequirementHierarchy) Validate() error {
	for _, req := range h.Requirements {
		if err := h.validateNode(req); err != nil {
			return err
		}
	}
	return nil
}

func (h *RequirementHierarchy) validateNode(node *RequirementNode) error {
	if err := node.Validate(); err != nil {
		return fmt.Errorf("requirement %s: %w", node.ID, err)
	}
	for _, child := range node.Children {
		if err := h.validateNode(child); err != nil {
			return err
		}
	}
	return nil
}

// ToJSON serializes the hierarchy to JSON.
func (h *RequirementHierarchy) ToJSON() ([]byte, error) {
	return json.MarshalIndent(h, "", "  ")
}

// FromJSON deserializes a hierarchy from JSON.
func FromJSON(data []byte) (*RequirementHierarchy, error) {
	h := &RequirementHierarchy{}
	if err := json.Unmarshal(data, h); err != nil {
		return nil, fmt.Errorf("failed to parse hierarchy JSON: %w", err)
	}
	return h, nil
}

// DecompositionErrorCode represents types of decomposition errors.
type DecompositionErrorCode string

const (
	ErrEmptyContent      DecompositionErrorCode = "EMPTY_CONTENT"
	ErrBAMLUnavailable   DecompositionErrorCode = "BAML_UNAVAILABLE"
	ErrBAMLAPIError      DecompositionErrorCode = "BAML_API_ERROR"
	ErrInvalidJSON       DecompositionErrorCode = "INVALID_JSON"
	ErrConversionError   DecompositionErrorCode = "CONVERSION_ERROR"
	ErrCLIFallbackError  DecompositionErrorCode = "CLI_FALLBACK_ERROR"
)

// DecompositionError represents an error during requirement decomposition.
type DecompositionError struct {
	Code    DecompositionErrorCode `json:"error_code"`
	Message string                 `json:"error"`
	Details map[string]interface{} `json:"details,omitempty"`
}

// Error implements the error interface.
func (e *DecompositionError) Error() string {
	if e.Details != nil {
		return fmt.Sprintf("%s: %s (details: %v)", e.Code, e.Message, e.Details)
	}
	return fmt.Sprintf("%s: %s", e.Code, e.Message)
}

// NewDecompositionError creates a new decomposition error.
func NewDecompositionError(code DecompositionErrorCode, message string, details map[string]interface{}) *DecompositionError {
	return &DecompositionError{
		Code:    code,
		Message: message,
		Details: details,
	}
}

// TechStackResult contains detected technology stack information.
type TechStackResult struct {
	Languages         []string `json:"languages"`
	Frameworks        []string `json:"frameworks"`
	TestingFrameworks []string `json:"testing_frameworks"`
	BuildSystems      []string `json:"build_systems"`
}

// FileGroup represents a group of related files.
type FileGroup struct {
	Name    string   `json:"name"`
	Path    string   `json:"path"`
	Files   []string `json:"files"`
	Purpose string   `json:"purpose,omitempty"`
}

// FileGroupAnalysis contains analysis results for file grouping.
type FileGroupAnalysis struct {
	Groups     []*FileGroup `json:"groups"`
	TotalFiles int          `json:"total_files"`
}

// PipelineResult represents the result of a pipeline step.
type PipelineResult struct {
	Success     bool                   `json:"success"`
	Output      string                 `json:"output,omitempty"`
	Error       string                 `json:"error,omitempty"`
	Data        map[string]interface{} `json:"data,omitempty"`
	Elapsed     float64                `json:"elapsed,omitempty"`
	FailedAt    string                 `json:"failed_at,omitempty"`
}

// NewPipelineResult creates a successful result.
func NewPipelineResult() *PipelineResult {
	return &PipelineResult{
		Success: true,
		Data:    make(map[string]interface{}),
	}
}

// SetError marks the result as failed with an error.
func (r *PipelineResult) SetError(err error) {
	r.Success = false
	r.Error = err.Error()
}

// SetData sets a data field on the result.
func (r *PipelineResult) SetData(key string, value interface{}) {
	if r.Data == nil {
		r.Data = make(map[string]interface{})
	}
	r.Data[key] = value
}

// GetString retrieves a string value from data.
func (r *PipelineResult) GetString(key string) string {
	if v, ok := r.Data[key]; ok {
		if s, ok := v.(string); ok {
			return s
		}
	}
	return ""
}

// GetStringSlice retrieves a string slice from data.
func (r *PipelineResult) GetStringSlice(key string) []string {
	if v, ok := r.Data[key]; ok {
		if s, ok := v.([]string); ok {
			return s
		}
	}
	return nil
}

// ValidComplexities for Feature.
var ValidComplexities = map[string]bool{
	"high":   true,
	"medium": true,
	"low":    true,
}

// Feature represents a feature/issue for tracking in feature_list.json.
// This matches the Python feature_list.json schema used by loop-runner.py and orchestrator.py.
type Feature struct {
	ID            string   `json:"id"`
	Name          string   `json:"name"`
	Description   string   `json:"description,omitempty"`
	Priority      int      `json:"priority,omitempty"`
	Category      string   `json:"category,omitempty"`
	Passes        bool     `json:"passes"`
	Blocked       bool     `json:"blocked,omitempty"`
	BlockedReason string   `json:"blocked_reason,omitempty"`
	BlockedBy     []string `json:"blocked_by,omitempty"`
	BlockedAt     string   `json:"blocked_at,omitempty"`
	Dependencies  []string `json:"dependencies,omitempty"`
	Tests         []string `json:"tests,omitempty"`
	Complexity    string   `json:"complexity,omitempty"`
	NeedsReview   bool     `json:"needs_review,omitempty"`
	QAOrigin      string   `json:"qa_origin,omitempty"`
	Severity      string   `json:"severity,omitempty"`
	SuggestedFix  string   `json:"suggested_fix,omitempty"`
}

// Validate checks that the Feature has valid values.
func (f *Feature) Validate() error {
	if f.ID == "" {
		return errors.New("feature id cannot be empty")
	}
	if f.Name == "" {
		return errors.New("feature name cannot be empty")
	}
	if f.Blocked && f.BlockedReason == "" {
		return errors.New("blocked feature must have blocked_reason")
	}
	if f.Blocked && len(f.BlockedBy) == 0 {
		return errors.New("blocked feature must have blocked_by")
	}
	if f.Complexity != "" && !ValidComplexities[f.Complexity] {
		return fmt.Errorf("invalid complexity: %s (valid: high, medium, low)", f.Complexity)
	}
	if f.Passes && f.Blocked {
		return errors.New("feature cannot be both passes=true and blocked=true")
	}
	// Check for self-reference in dependencies
	for _, dep := range f.Dependencies {
		if dep == f.ID {
			return fmt.Errorf("feature %s cannot depend on itself", f.ID)
		}
	}
	return nil
}

// ValidateWithFeatureList validates the feature and checks that dependency IDs exist.
func (f *Feature) ValidateWithFeatureList(list *FeatureList) error {
	if err := f.Validate(); err != nil {
		return err
	}
	if list == nil {
		return nil
	}
	// Check dependencies exist
	for _, depID := range f.Dependencies {
		if list.GetByID(depID) == nil {
			return fmt.Errorf("dependency %s not found in feature list", depID)
		}
	}
	// Check blocked_by references exist
	for _, blockerID := range f.BlockedBy {
		if list.GetByID(blockerID) == nil {
			return fmt.Errorf("blocked_by reference %s not found in feature list", blockerID)
		}
	}
	return nil
}

// FeatureList is a container for features from feature_list.json.
type FeatureList struct {
	Features []Feature `json:"features"`
}

// NewFeatureList creates a new empty feature list.
func NewFeatureList() *FeatureList {
	return &FeatureList{
		Features: make([]Feature, 0),
	}
}

// Add adds a feature to the list.
func (fl *FeatureList) Add(feature Feature) {
	fl.Features = append(fl.Features, feature)
}

// GetByID finds a feature by ID.
func (fl *FeatureList) GetByID(id string) *Feature {
	for i := range fl.Features {
		if fl.Features[i].ID == id {
			return &fl.Features[i]
		}
	}
	return nil
}

// GetPending returns features that are not passes and not blocked.
func (fl *FeatureList) GetPending() []Feature {
	var pending []Feature
	for _, f := range fl.Features {
		if !f.Passes && !f.Blocked {
			pending = append(pending, f)
		}
	}
	return pending
}

// GetBlocked returns all blocked features.
func (fl *FeatureList) GetBlocked() []Feature {
	var blocked []Feature
	for _, f := range fl.Features {
		if f.Blocked {
			blocked = append(blocked, f)
		}
	}
	return blocked
}

// GetCompleted returns all completed (passes=true) features.
func (fl *FeatureList) GetCompleted() []Feature {
	var completed []Feature
	for _, f := range fl.Features {
		if f.Passes {
			completed = append(completed, f)
		}
	}
	return completed
}

// Stats returns feature list statistics.
func (fl *FeatureList) Stats() map[string]int {
	total := len(fl.Features)
	completed := 0
	blocked := 0
	for _, f := range fl.Features {
		if f.Passes {
			completed++
		}
		if f.Blocked {
			blocked++
		}
	}
	return map[string]int{
		"total":     total,
		"completed": completed,
		"remaining": total - completed,
		"blocked":   blocked,
	}
}

// ToJSON serializes the feature list to JSON.
func (fl *FeatureList) ToJSON() ([]byte, error) {
	return json.MarshalIndent(fl, "", "  ")
}

// FeatureListFromJSON deserializes a feature list from JSON.
func FeatureListFromJSON(data []byte) (*FeatureList, error) {
	fl := &FeatureList{}
	if err := json.Unmarshal(data, fl); err != nil {
		return nil, fmt.Errorf("failed to parse feature list JSON: %w", err)
	}
	return fl, nil
}

// Validate validates all features in the list.
func (fl *FeatureList) Validate() error {
	for i := range fl.Features {
		if err := fl.Features[i].ValidateWithFeatureList(fl); err != nil {
			return fmt.Errorf("feature %s: %w", fl.Features[i].ID, err)
		}
	}
	return nil
}

// PhaseType represents the 6 pipeline phases with execution ordering.
type PhaseType int

const (
	PhaseResearch PhaseType = iota
	PhaseDecomposition
	PhaseTDDPlanning
	PhaseMultiDoc
	PhaseBeadsSync
	PhaseImplementation
)

// String returns the string representation of PhaseType.
func (pt PhaseType) String() string {
	switch pt {
	case PhaseResearch:
		return "research"
	case PhaseDecomposition:
		return "decomposition"
	case PhaseTDDPlanning:
		return "tdd_planning"
	case PhaseMultiDoc:
		return "multi_doc"
	case PhaseBeadsSync:
		return "beads_sync"
	case PhaseImplementation:
		return "implementation"
	default:
		return "unknown"
	}
}

// PhaseTypeFromString parses a string into a PhaseType.
func PhaseTypeFromString(s string) (PhaseType, error) {
	switch strings.ToLower(strings.TrimSpace(s)) {
	case "research":
		return PhaseResearch, nil
	case "decomposition":
		return PhaseDecomposition, nil
	case "tdd_planning":
		return PhaseTDDPlanning, nil
	case "multi_doc":
		return PhaseMultiDoc, nil
	case "beads_sync":
		return PhaseBeadsSync, nil
	case "implementation":
		return PhaseImplementation, nil
	default:
		return PhaseResearch, fmt.Errorf("invalid phase type: %s (valid: research, decomposition, tdd_planning, multi_doc, beads_sync, implementation)", s)
	}
}

// Next returns the next phase in the sequence.
func (pt PhaseType) Next() (PhaseType, error) {
	if pt == PhaseImplementation {
		return PhaseImplementation, errors.New("implementation is the final phase")
	}
	return pt + 1, nil
}

// Previous returns the previous phase in the sequence.
func (pt PhaseType) Previous() (PhaseType, error) {
	if pt == PhaseResearch {
		return PhaseResearch, errors.New("research is the first phase")
	}
	return pt - 1, nil
}

// MarshalJSON implements json.Marshaler for PhaseType.
func (pt PhaseType) MarshalJSON() ([]byte, error) {
	return json.Marshal(pt.String())
}

// UnmarshalJSON implements json.Unmarshaler for PhaseType.
func (pt *PhaseType) UnmarshalJSON(data []byte) error {
	var s string
	if err := json.Unmarshal(data, &s); err != nil {
		return fmt.Errorf("phase type must be a string: %w", err)
	}

	phase, err := PhaseTypeFromString(s)
	if err != nil {
		return err
	}

	*pt = phase
	return nil
}

// AllPhases returns a slice of all phases in order.
func AllPhases() []PhaseType {
	return []PhaseType{
		PhaseResearch,
		PhaseDecomposition,
		PhaseTDDPlanning,
		PhaseMultiDoc,
		PhaseBeadsSync,
		PhaseImplementation,
	}
}

// PhaseStatus represents phase execution state.
type PhaseStatus int

const (
	StatusPending PhaseStatus = iota
	StatusInProgress
	StatusComplete
	StatusFailed
)

// String returns the string representation of PhaseStatus.
func (ps PhaseStatus) String() string {
	switch ps {
	case StatusPending:
		return "pending"
	case StatusInProgress:
		return "in_progress"
	case StatusComplete:
		return "complete"
	case StatusFailed:
		return "failed"
	default:
		return "unknown"
	}
}

// PhaseStatusFromString parses a string into a PhaseStatus.
func PhaseStatusFromString(s string) (PhaseStatus, error) {
	switch strings.ToLower(strings.TrimSpace(s)) {
	case "pending":
		return StatusPending, nil
	case "in_progress":
		return StatusInProgress, nil
	case "complete":
		return StatusComplete, nil
	case "failed":
		return StatusFailed, nil
	default:
		return StatusPending, fmt.Errorf("invalid phase status: %s (valid: pending, in_progress, complete, failed)", s)
	}
}

// IsTerminal returns true if the status is terminal (complete or failed).
func (ps PhaseStatus) IsTerminal() bool {
	return ps == StatusComplete || ps == StatusFailed
}

// CanTransitionTo checks if a transition to another status is valid.
func (ps PhaseStatus) CanTransitionTo(next PhaseStatus) bool {
	switch ps {
	case StatusPending:
		return next == StatusInProgress
	case StatusInProgress:
		return next == StatusComplete || next == StatusFailed
	case StatusFailed:
		return next == StatusInProgress // Allow retry
	case StatusComplete:
		return false // Complete is terminal, no transitions
	default:
		return false
	}
}

// MarshalJSON implements json.Marshaler for PhaseStatus.
func (ps PhaseStatus) MarshalJSON() ([]byte, error) {
	return json.Marshal(ps.String())
}

// UnmarshalJSON implements json.Unmarshaler for PhaseStatus.
func (ps *PhaseStatus) UnmarshalJSON(data []byte) error {
	var s string
	if err := json.Unmarshal(data, &s); err != nil {
		return fmt.Errorf("phase status must be a string: %w", err)
	}

	status, err := PhaseStatusFromString(s)
	if err != nil {
		return err
	}

	*ps = status
	return nil
}

// PhaseResult represents the result of executing a single phase.
type PhaseResult struct {
	Phase            PhaseType              `json:"phase"`
	Status           PhaseStatus            `json:"status"`
	Artifacts        []string               `json:"artifacts,omitempty"`
	Errors           []string               `json:"errors,omitempty"`
	StartedAt        *time.Time             `json:"started_at,omitempty"`
	CompletedAt      *time.Time             `json:"completed_at,omitempty"`
	DurationSeconds  float64                `json:"duration_seconds,omitempty"`
	Metadata         map[string]interface{} `json:"metadata,omitempty"`
}

// NewPhaseResult creates a new phase result with the given phase type.
func NewPhaseResult(phase PhaseType) *PhaseResult {
	now := time.Now()
	return &PhaseResult{
		Phase:     phase,
		Status:    StatusPending,
		Artifacts: make([]string, 0),
		Errors:    make([]string, 0),
		StartedAt: &now,
		Metadata:  make(map[string]interface{}),
	}
}

// IsComplete returns true if the phase is complete.
func (pr *PhaseResult) IsComplete() bool {
	return pr.Status == StatusComplete
}

// IsFailed returns true if the phase has failed.
func (pr *PhaseResult) IsFailed() bool {
	return pr.Status == StatusFailed
}

// Complete marks the phase as complete and sets completion time.
func (pr *PhaseResult) Complete() {
	now := time.Now()
	pr.Status = StatusComplete
	pr.CompletedAt = &now
	if pr.StartedAt != nil {
		pr.DurationSeconds = now.Sub(*pr.StartedAt).Seconds()
	}
}

// Fail marks the phase as failed and sets completion time.
func (pr *PhaseResult) Fail(err error) {
	now := time.Now()
	pr.Status = StatusFailed
	pr.CompletedAt = &now
	if pr.StartedAt != nil {
		pr.DurationSeconds = now.Sub(*pr.StartedAt).Seconds()
	}
	if err != nil {
		pr.Errors = append(pr.Errors, err.Error())
	}
}

// AddArtifact adds an artifact file path to the result.
func (pr *PhaseResult) AddArtifact(path string) {
	pr.Artifacts = append(pr.Artifacts, path)
}

// AddError adds an error message to the result.
func (pr *PhaseResult) AddError(err string) {
	pr.Errors = append(pr.Errors, err)
}

// SetMetadata sets a metadata value.
func (pr *PhaseResult) SetMetadata(key string, value interface{}) {
	if pr.Metadata == nil {
		pr.Metadata = make(map[string]interface{})
	}
	pr.Metadata[key] = value
}

// ToDict converts the phase result to a map for checkpoint serialization.
func (pr *PhaseResult) ToDict() map[string]interface{} {
	result := map[string]interface{}{
		"phase":  pr.Phase.String(),
		"status": pr.Status.String(),
	}

	if len(pr.Artifacts) > 0 {
		result["artifacts"] = pr.Artifacts
	}
	if len(pr.Errors) > 0 {
		result["errors"] = pr.Errors
	}
	if pr.StartedAt != nil {
		result["started_at"] = pr.StartedAt.Format(time.RFC3339)
	}
	if pr.CompletedAt != nil {
		result["completed_at"] = pr.CompletedAt.Format(time.RFC3339)
	}
	if pr.DurationSeconds > 0 {
		result["duration_seconds"] = pr.DurationSeconds
	}
	if len(pr.Metadata) > 0 {
		result["metadata"] = pr.Metadata
	}

	return result
}

// FromDict creates a PhaseResult from a map (checkpoint deserialization).
func PhaseResultFromDict(data map[string]interface{}) (*PhaseResult, error) {
	result := &PhaseResult{
		Artifacts: make([]string, 0),
		Errors:    make([]string, 0),
		Metadata:  make(map[string]interface{}),
	}

	// Parse phase
	if phaseStr, ok := data["phase"].(string); ok {
		phase, err := PhaseTypeFromString(phaseStr)
		if err != nil {
			return nil, fmt.Errorf("invalid phase: %w", err)
		}
		result.Phase = phase
	}

	// Parse status
	if statusStr, ok := data["status"].(string); ok {
		status, err := PhaseStatusFromString(statusStr)
		if err != nil {
			return nil, fmt.Errorf("invalid status: %w", err)
		}
		result.Status = status
	}

	// Parse artifacts
	if artifacts, ok := data["artifacts"].([]interface{}); ok {
		for _, a := range artifacts {
			if s, ok := a.(string); ok {
				result.Artifacts = append(result.Artifacts, s)
			}
		}
	}

	// Parse errors
	if errors, ok := data["errors"].([]interface{}); ok {
		for _, e := range errors {
			if s, ok := e.(string); ok {
				result.Errors = append(result.Errors, s)
			}
		}
	}

	// Parse timestamps
	if startedStr, ok := data["started_at"].(string); ok {
		if t, err := time.Parse(time.RFC3339, startedStr); err == nil {
			result.StartedAt = &t
		}
	}
	if completedStr, ok := data["completed_at"].(string); ok {
		if t, err := time.Parse(time.RFC3339, completedStr); err == nil {
			result.CompletedAt = &t
		}
	}

	// Parse duration
	if duration, ok := data["duration_seconds"].(float64); ok {
		result.DurationSeconds = duration
	}

	// Parse metadata
	if metadata, ok := data["metadata"].(map[string]interface{}); ok {
		result.Metadata = metadata
	}

	return result, nil
}

// PipelineState represents the complete state of the pipeline execution.
type PipelineState struct {
	ProjectPath     string                    `json:"project_path"`
	AutonomyMode    AutonomyMode              `json:"autonomy_mode"`
	CurrentPhase    *PhaseType                `json:"current_phase,omitempty"`
	PhaseResults    map[PhaseType]*PhaseResult `json:"phase_results"`
	ContextEntryIDs map[PhaseType][]string    `json:"context_entry_ids,omitempty"`
	StartedAt       *time.Time                `json:"started_at,omitempty"`
	CheckpointID    string                    `json:"checkpoint_id,omitempty"`
	BeadsEpicID     string                    `json:"beads_epic_id,omitempty"`
	Metadata        map[string]interface{}    `json:"metadata,omitempty"`
}

// NewPipelineState creates a new pipeline state.
func NewPipelineState(projectPath string, autonomyMode AutonomyMode) (*PipelineState, error) {
	if strings.TrimSpace(projectPath) == "" {
		return nil, errors.New("project path cannot be empty")
	}

	now := time.Now()
	return &PipelineState{
		ProjectPath:     projectPath,
		AutonomyMode:    autonomyMode,
		PhaseResults:    make(map[PhaseType]*PhaseResult),
		ContextEntryIDs: make(map[PhaseType][]string),
		StartedAt:       &now,
		Metadata:        make(map[string]interface{}),
	}, nil
}

// SetProjectPath sets the project path with validation.
func (ps *PipelineState) SetProjectPath(path string) error {
	if strings.TrimSpace(path) == "" {
		return errors.New("project path cannot be empty")
	}
	ps.ProjectPath = path
	return nil
}

// GetPhaseResult returns the result for a given phase.
func (ps *PipelineState) GetPhaseResult(phase PhaseType) *PhaseResult {
	return ps.PhaseResults[phase]
}

// SetPhaseResult sets the result for a given phase.
func (ps *PipelineState) SetPhaseResult(phase PhaseType, result *PhaseResult) {
	if ps.PhaseResults == nil {
		ps.PhaseResults = make(map[PhaseType]*PhaseResult)
	}
	ps.PhaseResults[phase] = result
}

// IsPhaseComplete checks if a given phase is complete.
func (ps *PipelineState) IsPhaseComplete(phase PhaseType) bool {
	result := ps.PhaseResults[phase]
	return result != nil && result.IsComplete()
}

// AllPhasesComplete checks if all 6 phases are complete.
func (ps *PipelineState) AllPhasesComplete() bool {
	allPhases := AllPhases()
	for _, phase := range allPhases {
		if !ps.IsPhaseComplete(phase) {
			return false
		}
	}
	return true
}

// TrackContextEntry adds a context entry ID for a phase.
func (ps *PipelineState) TrackContextEntry(phase PhaseType, entryID string) {
	if ps.ContextEntryIDs == nil {
		ps.ContextEntryIDs = make(map[PhaseType][]string)
	}
	ps.ContextEntryIDs[phase] = append(ps.ContextEntryIDs[phase], entryID)
}

// GetContextEntries returns all context entry IDs for a phase.
func (ps *PipelineState) GetContextEntries(phase PhaseType) []string {
	if ps.ContextEntryIDs == nil {
		return []string{}
	}
	return ps.ContextEntryIDs[phase]
}

// ToDict converts the pipeline state to a map for checkpoint serialization.
func (ps *PipelineState) ToDict() map[string]interface{} {
	result := map[string]interface{}{
		"project_path":  ps.ProjectPath,
		"autonomy_mode": ps.AutonomyMode.String(),
	}

	if ps.CurrentPhase != nil {
		result["current_phase"] = ps.CurrentPhase.String()
	}

	// Convert phase results
	if len(ps.PhaseResults) > 0 {
		phaseResults := make(map[string]interface{})
		for phase, phaseResult := range ps.PhaseResults {
			phaseResults[phase.String()] = phaseResult.ToDict()
		}
		result["phase_results"] = phaseResults
	}

	// Convert context entry IDs
	if len(ps.ContextEntryIDs) > 0 {
		contextEntries := make(map[string][]string)
		for phase, entries := range ps.ContextEntryIDs {
			contextEntries[phase.String()] = entries
		}
		result["context_entry_ids"] = contextEntries
	}

	if ps.StartedAt != nil {
		result["started_at"] = ps.StartedAt.Format(time.RFC3339)
	}
	if ps.CheckpointID != "" {
		result["checkpoint_id"] = ps.CheckpointID
	}
	if ps.BeadsEpicID != "" {
		result["beads_epic_id"] = ps.BeadsEpicID
	}
	if len(ps.Metadata) > 0 {
		result["metadata"] = ps.Metadata
	}

	return result
}

// ToCheckpointDict is an alias for ToDict for semantic clarity.
func (ps *PipelineState) ToCheckpointDict() map[string]interface{} {
	return ps.ToDict()
}

// PipelineStateFromDict creates a PipelineState from a map.
func PipelineStateFromDict(data map[string]interface{}) (*PipelineState, error) {
	state := &PipelineState{
		PhaseResults:    make(map[PhaseType]*PhaseResult),
		ContextEntryIDs: make(map[PhaseType][]string),
		Metadata:        make(map[string]interface{}),
	}

	// Parse project path
	if projectPath, ok := data["project_path"].(string); ok {
		state.ProjectPath = projectPath
	}

	// Parse autonomy mode
	if modeStr, ok := data["autonomy_mode"].(string); ok {
		mode, err := AutonomyModeFromString(modeStr)
		if err != nil {
			return nil, fmt.Errorf("invalid autonomy mode: %w", err)
		}
		state.AutonomyMode = mode
	}

	// Parse current phase
	if phaseStr, ok := data["current_phase"].(string); ok {
		phase, err := PhaseTypeFromString(phaseStr)
		if err != nil {
			return nil, fmt.Errorf("invalid current phase: %w", err)
		}
		state.CurrentPhase = &phase
	}

	// Parse phase results
	if phaseResults, ok := data["phase_results"].(map[string]interface{}); ok {
		for phaseStr, resultData := range phaseResults {
			phase, err := PhaseTypeFromString(phaseStr)
			if err != nil {
				continue // Skip invalid phases
			}

			if resultMap, ok := resultData.(map[string]interface{}); ok {
				result, err := PhaseResultFromDict(resultMap)
				if err == nil {
					state.PhaseResults[phase] = result
				}
			}
		}
	}

	// Parse context entry IDs - handle both map[string]interface{} and map[string][]string
	if contextEntriesRaw, ok := data["context_entry_ids"]; ok {
		switch contextEntries := contextEntriesRaw.(type) {
		case map[string]interface{}:
			for phaseStr, entriesData := range contextEntries {
				phase, err := PhaseTypeFromString(phaseStr)
				if err != nil {
					continue // Skip invalid phases
				}

				// Handle both []interface{} and []string
				switch v := entriesData.(type) {
				case []interface{}:
					for _, entry := range v {
						if s, ok := entry.(string); ok {
							state.ContextEntryIDs[phase] = append(state.ContextEntryIDs[phase], s)
						}
					}
				case []string:
					state.ContextEntryIDs[phase] = v
				}
			}
		case map[string][]string:
			for phaseStr, entries := range contextEntries {
				phase, err := PhaseTypeFromString(phaseStr)
				if err != nil {
					continue // Skip invalid phases
				}
				state.ContextEntryIDs[phase] = entries
			}
		}
	}

	// Parse timestamps
	if startedStr, ok := data["started_at"].(string); ok {
		if t, err := time.Parse(time.RFC3339, startedStr); err == nil {
			state.StartedAt = &t
		}
	}

	// Parse checkpoint ID
	if checkpointID, ok := data["checkpoint_id"].(string); ok {
		state.CheckpointID = checkpointID
	}

	// Parse beads epic ID
	if beadsEpicID, ok := data["beads_epic_id"].(string); ok {
		state.BeadsEpicID = beadsEpicID
	}

	// Parse metadata
	if metadata, ok := data["metadata"].(map[string]interface{}); ok {
		state.Metadata = metadata
	}

	return state, nil
}

// FromCheckpointDict is an alias for PipelineStateFromDict for semantic clarity.
func FromCheckpointDict(data map[string]interface{}) (*PipelineState, error) {
	return PipelineStateFromDict(data)
}
