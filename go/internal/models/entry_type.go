// Package models provides core data models for the context window array architecture.
// It includes types for context entries, requirements, and their hierarchies.
package models

import (
	"encoding/json"
	"fmt"
	"strings"
)

// EntryType represents the type of a context entry in the store.
// Each type represents a different category of context:
//   - File: File content from codebase
//   - Command: Command invocation (can be removed after execution)
//   - CommandResult: Result of command execution (retained)
//   - Task: Task description for implementation LLM
//   - TaskResult: Result from task execution
//   - SearchResult: Result from search/grep operations
//   - Summary: Compressed summary of other entries
//   - ContextRequest: Worker request for additional context
type EntryType string

const (
	EntryTypeFile           EntryType = "file"
	EntryTypeCommand        EntryType = "command"
	EntryTypeCommandResult  EntryType = "command_result"
	EntryTypeTask           EntryType = "task"
	EntryTypeTaskResult     EntryType = "task_result"
	EntryTypeSearchResult   EntryType = "search_result"
	EntryTypeSummary        EntryType = "summary"
	EntryTypeContextRequest EntryType = "context_request"
)

// validEntryTypes contains all valid entry type values for validation.
var validEntryTypes = map[EntryType]bool{
	EntryTypeFile:           true,
	EntryTypeCommand:        true,
	EntryTypeCommandResult:  true,
	EntryTypeTask:           true,
	EntryTypeTaskResult:     true,
	EntryTypeSearchResult:   true,
	EntryTypeSummary:        true,
	EntryTypeContextRequest: true,
}

// AllEntryTypes returns a slice of all valid entry types.
func AllEntryTypes() []EntryType {
	return []EntryType{
		EntryTypeFile,
		EntryTypeCommand,
		EntryTypeCommandResult,
		EntryTypeTask,
		EntryTypeTaskResult,
		EntryTypeSearchResult,
		EntryTypeSummary,
		EntryTypeContextRequest,
	}
}

// IsValid returns true if the entry type is a valid value.
func (et EntryType) IsValid() bool {
	return validEntryTypes[et]
}

// String returns the string representation of the entry type.
func (et EntryType) String() string {
	return string(et)
}

// ParseEntryType converts a string to an EntryType.
// Returns an error if the string is not a valid entry type.
func ParseEntryType(s string) (EntryType, error) {
	et := EntryType(strings.ToLower(strings.TrimSpace(s)))
	if !et.IsValid() {
		validTypes := make([]string, 0, len(validEntryTypes))
		for t := range validEntryTypes {
			validTypes = append(validTypes, string(t))
		}
		return "", fmt.Errorf("invalid entry type '%s': must be one of: %s", s, strings.Join(validTypes, ", "))
	}
	return et, nil
}

// MarshalJSON implements json.Marshaler for EntryType.
func (et EntryType) MarshalJSON() ([]byte, error) {
	return json.Marshal(string(et))
}

// UnmarshalJSON implements json.Unmarshaler for EntryType.
func (et *EntryType) UnmarshalJSON(data []byte) error {
	var s string
	if err := json.Unmarshal(data, &s); err != nil {
		return fmt.Errorf("failed to unmarshal EntryType: %w", err)
	}

	parsed, err := ParseEntryType(s)
	if err != nil {
		return err
	}

	*et = parsed
	return nil
}
