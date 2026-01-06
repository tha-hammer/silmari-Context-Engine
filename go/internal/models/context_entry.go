package models

import (
	"errors"
	"fmt"
	"strings"
	"time"
)

// ContextCompressedError is returned when attempting to access content of a compressed entry.
type ContextCompressedError struct {
	EntryID string
}

func (e *ContextCompressedError) Error() string {
	return fmt.Sprintf("entry '%s' is compressed; content is unavailable", e.EntryID)
}

// ContextEntry represents a single addressable entry in the context store.
// It represents a piece of context that can be stored, searched, compressed,
// and referenced by ID. Follows the Context Entry Schema from RLM research.
type ContextEntry struct {
	// ID is the unique identifier (format: ctx_XXX)
	ID string `json:"id"`

	// EntryType is the type of context entry
	EntryType EntryType `json:"entry_type"`

	// Source is the origin (file path, command, task_id)
	Source string `json:"source"`

	// Content is the full content (can be nil if compressed)
	Content *string `json:"content,omitempty"`

	// Summary is the compressed summary (always present after creation)
	Summary *string `json:"summary,omitempty"`

	// CreatedAt is the creation timestamp
	CreatedAt time.Time `json:"created_at"`

	// References is the list of referenced entry IDs
	References []string `json:"references,omitempty"`

	// Searchable indicates whether to include in search index
	Searchable bool `json:"searchable"`

	// Compressed is true if content has been removed
	Compressed bool `json:"compressed"`

	// TTL is time-to-live in conversation turns (nil = no expiry)
	TTL *int `json:"ttl,omitempty"`

	// ParentID is the ID of parent entry if derived
	ParentID *string `json:"parent_id,omitempty"`

	// DerivedFrom is the list of entry IDs this was derived from
	DerivedFrom []string `json:"derived_from,omitempty"`

	// Priority is the priority level for the entry
	Priority int `json:"priority"`
}

// ContextEntryOption is a functional option for configuring a ContextEntry.
type ContextEntryOption func(*ContextEntry)

// WithContent sets the content of the entry.
func WithContent(content string) ContextEntryOption {
	return func(ce *ContextEntry) {
		ce.Content = &content
	}
}

// WithSummary sets the summary of the entry.
func WithSummary(summary string) ContextEntryOption {
	return func(ce *ContextEntry) {
		ce.Summary = &summary
	}
}

// WithCreatedAt sets the creation timestamp of the entry.
func WithCreatedAt(t time.Time) ContextEntryOption {
	return func(ce *ContextEntry) {
		ce.CreatedAt = t
	}
}

// WithReferences sets the references of the entry.
func WithReferences(refs []string) ContextEntryOption {
	return func(ce *ContextEntry) {
		ce.References = refs
	}
}

// WithSearchable sets whether the entry is searchable.
func WithSearchable(searchable bool) ContextEntryOption {
	return func(ce *ContextEntry) {
		ce.Searchable = searchable
	}
}

// WithTTL sets the TTL of the entry.
func WithTTL(ttl int) ContextEntryOption {
	return func(ce *ContextEntry) {
		ce.TTL = &ttl
	}
}

// WithParentID sets the parent ID of the entry.
func WithParentID(parentID string) ContextEntryOption {
	return func(ce *ContextEntry) {
		ce.ParentID = &parentID
	}
}

// WithDerivedFrom sets the derived from list of the entry.
func WithDerivedFrom(derivedFrom []string) ContextEntryOption {
	return func(ce *ContextEntry) {
		ce.DerivedFrom = derivedFrom
	}
}

// WithPriority sets the priority of the entry.
func WithPriority(priority int) ContextEntryOption {
	return func(ce *ContextEntry) {
		ce.Priority = priority
	}
}

// NewContextEntry creates a new ContextEntry with the given required fields and options.
// At least one of content or summary must be provided via options.
func NewContextEntry(id string, entryType EntryType, source string, opts ...ContextEntryOption) (*ContextEntry, error) {
	ce := &ContextEntry{
		ID:         id,
		EntryType:  entryType,
		Source:     source,
		CreatedAt:  time.Now(),
		References: []string{},
		Searchable: true,
		Compressed: false,
		DerivedFrom: []string{},
		Priority:   0,
	}

	// Apply options
	for _, opt := range opts {
		opt(ce)
	}

	// Validate the entry
	if err := ce.Validate(); err != nil {
		return nil, err
	}

	return ce, nil
}

// Validate checks if the ContextEntry is valid.
func (ce *ContextEntry) Validate() error {
	if err := ce.validateID(); err != nil {
		return err
	}
	if err := ce.validateEntryType(); err != nil {
		return err
	}
	if err := ce.validateSource(); err != nil {
		return err
	}
	if err := ce.validateContentOrSummary(); err != nil {
		return err
	}
	if err := ce.validateTTL(); err != nil {
		return err
	}
	if err := ce.validateParentID(); err != nil {
		return err
	}
	if err := ce.validateStringLists(); err != nil {
		return err
	}
	return nil
}

func (ce *ContextEntry) validateID() error {
	if ce.ID == "" || strings.TrimSpace(ce.ID) == "" {
		return errors.New("id must not be empty")
	}
	return nil
}

func (ce *ContextEntry) validateEntryType() error {
	if !ce.EntryType.IsValid() {
		return fmt.Errorf("invalid entry type '%s'", ce.EntryType)
	}
	return nil
}

func (ce *ContextEntry) validateSource() error {
	if ce.Source == "" || strings.TrimSpace(ce.Source) == "" {
		return errors.New("source must not be empty")
	}
	return nil
}

func (ce *ContextEntry) validateContentOrSummary() error {
	if ce.Content == nil && ce.Summary == nil {
		return errors.New("at least one of content or summary must be provided")
	}
	return nil
}

func (ce *ContextEntry) validateTTL() error {
	if ce.TTL != nil && *ce.TTL < 0 {
		return errors.New("ttl must be non-negative")
	}
	return nil
}

func (ce *ContextEntry) validateParentID() error {
	if ce.ParentID != nil && strings.TrimSpace(*ce.ParentID) == "" {
		// Normalize empty string to nil
		ce.ParentID = nil
	}
	return nil
}

func (ce *ContextEntry) validateStringLists() error {
	// References and DerivedFrom are already typed as []string,
	// so we just ensure they are not nil
	if ce.References == nil {
		ce.References = []string{}
	}
	if ce.DerivedFrom == nil {
		ce.DerivedFrom = []string{}
	}
	return nil
}

// ToDict converts the ContextEntry to a map for serialization.
func (ce *ContextEntry) ToDict() map[string]any {
	result := map[string]any{
		"id":           ce.ID,
		"entry_type":   ce.EntryType.String(),
		"source":       ce.Source,
		"created_at":   ce.CreatedAt.Format(time.RFC3339Nano),
		"references":   ce.References,
		"searchable":   ce.Searchable,
		"compressed":   ce.Compressed,
		"derived_from": ce.DerivedFrom,
		"priority":     ce.Priority,
	}

	if ce.Content != nil {
		result["content"] = *ce.Content
	} else {
		result["content"] = nil
	}

	if ce.Summary != nil {
		result["summary"] = *ce.Summary
	} else {
		result["summary"] = nil
	}

	if ce.TTL != nil {
		result["ttl"] = *ce.TTL
	} else {
		result["ttl"] = nil
	}

	if ce.ParentID != nil {
		result["parent_id"] = *ce.ParentID
	} else {
		result["parent_id"] = nil
	}

	return result
}

// FromDict creates a ContextEntry from a map representation.
func FromDict(data map[string]any) (*ContextEntry, error) {
	ce := &ContextEntry{
		References:  []string{},
		DerivedFrom: []string{},
	}

	// Required fields
	id, ok := data["id"].(string)
	if !ok {
		return nil, errors.New("id is required and must be a string")
	}
	ce.ID = id

	entryTypeStr, ok := data["entry_type"].(string)
	if !ok {
		return nil, errors.New("entry_type is required and must be a string")
	}
	entryType, err := ParseEntryType(entryTypeStr)
	if err != nil {
		return nil, err
	}
	ce.EntryType = entryType

	source, ok := data["source"].(string)
	if !ok {
		return nil, errors.New("source is required and must be a string")
	}
	ce.Source = source

	// Optional string fields
	if content, ok := data["content"].(string); ok {
		ce.Content = &content
	}

	if summary, ok := data["summary"].(string); ok {
		ce.Summary = &summary
	}

	// Created at
	if createdAtStr, ok := data["created_at"].(string); ok {
		createdAt, err := time.Parse(time.RFC3339Nano, createdAtStr)
		if err != nil {
			// Try ISO format as fallback
			createdAt, err = time.Parse("2006-01-02T15:04:05.999999", createdAtStr)
			if err != nil {
				return nil, fmt.Errorf("failed to parse created_at: %w", err)
			}
		}
		ce.CreatedAt = createdAt
	} else {
		ce.CreatedAt = time.Now()
	}

	// References
	if refs, ok := data["references"].([]any); ok {
		for _, ref := range refs {
			if refStr, ok := ref.(string); ok {
				ce.References = append(ce.References, refStr)
			}
		}
	}

	// Searchable
	if searchable, ok := data["searchable"].(bool); ok {
		ce.Searchable = searchable
	} else {
		ce.Searchable = true
	}

	// Compressed
	if compressed, ok := data["compressed"].(bool); ok {
		ce.Compressed = compressed
	}

	// TTL
	if ttl, ok := data["ttl"].(float64); ok {
		ttlInt := int(ttl)
		ce.TTL = &ttlInt
	} else if ttl, ok := data["ttl"].(int); ok {
		ce.TTL = &ttl
	}

	// Parent ID
	if parentID, ok := data["parent_id"].(string); ok && parentID != "" {
		ce.ParentID = &parentID
	}

	// Derived from
	if derivedFrom, ok := data["derived_from"].([]any); ok {
		for _, df := range derivedFrom {
			if dfStr, ok := df.(string); ok {
				ce.DerivedFrom = append(ce.DerivedFrom, dfStr)
			}
		}
	}

	// Priority
	if priority, ok := data["priority"].(float64); ok {
		ce.Priority = int(priority)
	} else if priority, ok := data["priority"].(int); ok {
		ce.Priority = priority
	}

	// Validate
	if err := ce.Validate(); err != nil {
		return nil, err
	}

	return ce, nil
}

// Compress removes the content and retains only the summary.
func (ce *ContextEntry) Compress() error {
	if ce.Compressed {
		return nil // Already compressed, no-op
	}

	if ce.Summary == nil {
		return errors.New("cannot compress entry without summary")
	}

	ce.Content = nil
	ce.Compressed = true
	return nil
}

// IsCompressed returns true if the entry is compressed.
func (ce *ContextEntry) IsCompressed() bool {
	return ce.Compressed
}

// GetContent returns the full content of the entry.
// Returns an error if the entry is compressed.
func (ce *ContextEntry) GetContent() (string, error) {
	if ce.Compressed {
		return "", &ContextCompressedError{EntryID: ce.ID}
	}
	if ce.Content == nil {
		return "", nil
	}
	return *ce.Content, nil
}

// GetContentOrSummary returns content if available, otherwise summary.
func (ce *ContextEntry) GetContentOrSummary() string {
	if ce.Content != nil {
		return *ce.Content
	}
	if ce.Summary != nil {
		return *ce.Summary
	}
	return ""
}

// CanCompress returns true if the entry can be compressed.
func (ce *ContextEntry) CanCompress() bool {
	return !ce.Compressed && ce.Content != nil && ce.Summary != nil
}

// DecrementTTL decrements TTL by 1 if set and positive.
// If TTL is nil, does nothing (no expiry).
// If TTL is 0, stays at 0.
func (ce *ContextEntry) DecrementTTL() {
	if ce.TTL != nil && *ce.TTL > 0 {
		newTTL := *ce.TTL - 1
		ce.TTL = &newTTL
	}
}

// IsExpired returns true if TTL is 0.
// Returns false if TTL is nil or positive.
func (ce *ContextEntry) IsExpired() bool {
	return ce.TTL != nil && *ce.TTL == 0
}

// HasTTL returns true if TTL is set (not nil).
func (ce *ContextEntry) HasTTL() bool {
	return ce.TTL != nil
}

// SetTTL sets the TTL value.
// Pass nil for no expiry.
func (ce *ContextEntry) SetTTL(ttl *int) error {
	if ttl != nil && *ttl < 0 {
		return errors.New("ttl must be non-negative")
	}
	ce.TTL = ttl
	return nil
}

// SetSummary sets the summary value.
// Returns an error if summary is empty.
func (ce *ContextEntry) SetSummary(summary string) error {
	if summary == "" || strings.TrimSpace(summary) == "" {
		return errors.New("summary must not be empty")
	}
	ce.Summary = &summary
	return nil
}
