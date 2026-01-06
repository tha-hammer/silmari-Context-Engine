// Package planning provides planning pipeline data structures and logic.
package planning

import (
	"encoding/json"
	"errors"
	"fmt"
	"strings"
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
