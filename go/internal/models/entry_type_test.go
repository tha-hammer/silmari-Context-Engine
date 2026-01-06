package models

import (
	"encoding/json"
	"testing"
)

func TestEntryType_IsValid(t *testing.T) {
	tests := []struct {
		name     string
		et       EntryType
		expected bool
	}{
		// Valid entry types
		{"file is valid", EntryTypeFile, true},
		{"command is valid", EntryTypeCommand, true},
		{"command_result is valid", EntryTypeCommandResult, true},
		{"task is valid", EntryTypeTask, true},
		{"task_result is valid", EntryTypeTaskResult, true},
		{"search_result is valid", EntryTypeSearchResult, true},
		{"summary is valid", EntryTypeSummary, true},
		{"context_request is valid", EntryTypeContextRequest, true},

		// Invalid entry types
		{"empty string is invalid", EntryType(""), false},
		{"unknown type is invalid", EntryType("unknown"), false},
		{"uppercase FILE is invalid", EntryType("FILE"), false},
		{"mixed case File is invalid", EntryType("File"), false},
		{"typo is invalid", EntryType("filee"), false},
		{"whitespace only is invalid", EntryType("   "), false},
		{"special chars is invalid", EntryType("file!"), false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.et.IsValid(); got != tt.expected {
				t.Errorf("EntryType(%q).IsValid() = %v, want %v", tt.et, got, tt.expected)
			}
		})
	}
}

func TestEntryType_String(t *testing.T) {
	tests := []struct {
		name     string
		et       EntryType
		expected string
	}{
		{"file type", EntryTypeFile, "file"},
		{"command type", EntryTypeCommand, "command"},
		{"command_result type", EntryTypeCommandResult, "command_result"},
		{"task type", EntryTypeTask, "task"},
		{"task_result type", EntryTypeTaskResult, "task_result"},
		{"search_result type", EntryTypeSearchResult, "search_result"},
		{"summary type", EntryTypeSummary, "summary"},
		{"context_request type", EntryTypeContextRequest, "context_request"},
		{"empty type", EntryType(""), ""},
		{"arbitrary type", EntryType("arbitrary"), "arbitrary"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.et.String(); got != tt.expected {
				t.Errorf("EntryType(%q).String() = %q, want %q", tt.et, got, tt.expected)
			}
		})
	}
}

func TestParseEntryType(t *testing.T) {
	tests := []struct {
		name        string
		input       string
		expected    EntryType
		expectError bool
	}{
		// Valid inputs
		{"file lowercase", "file", EntryTypeFile, false},
		{"command lowercase", "command", EntryTypeCommand, false},
		{"command_result lowercase", "command_result", EntryTypeCommandResult, false},
		{"task lowercase", "task", EntryTypeTask, false},
		{"task_result lowercase", "task_result", EntryTypeTaskResult, false},
		{"search_result lowercase", "search_result", EntryTypeSearchResult, false},
		{"summary lowercase", "summary", EntryTypeSummary, false},
		{"context_request lowercase", "context_request", EntryTypeContextRequest, false},

		// Case insensitive
		{"FILE uppercase", "FILE", EntryTypeFile, false},
		{"File mixed case", "File", EntryTypeFile, false},
		{"COMMAND uppercase", "COMMAND", EntryTypeCommand, false},
		{"Task_Result mixed case", "Task_Result", EntryTypeTaskResult, false},

		// Whitespace trimming
		{"file with leading space", " file", EntryTypeFile, false},
		{"file with trailing space", "file ", EntryTypeFile, false},
		{"file with surrounding spaces", "  file  ", EntryTypeFile, false},
		{"file with tabs", "\tfile\t", EntryTypeFile, false},

		// Invalid inputs
		{"empty string", "", EntryType(""), true},
		{"whitespace only", "   ", EntryType(""), true},
		{"unknown type", "unknown", EntryType(""), true},
		{"typo", "filee", EntryType(""), true},
		{"partial match", "fil", EntryType(""), true},
		{"with special chars", "file!", EntryType(""), true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := ParseEntryType(tt.input)

			if tt.expectError {
				if err == nil {
					t.Errorf("ParseEntryType(%q) expected error, got nil", tt.input)
				}
				return
			}

			if err != nil {
				t.Errorf("ParseEntryType(%q) unexpected error: %v", tt.input, err)
				return
			}

			if got != tt.expected {
				t.Errorf("ParseEntryType(%q) = %q, want %q", tt.input, got, tt.expected)
			}
		})
	}
}

func TestParseEntryType_ErrorMessage(t *testing.T) {
	_, err := ParseEntryType("invalid_type")
	if err == nil {
		t.Fatal("ParseEntryType(\"invalid_type\") expected error, got nil")
	}

	// Check that error message contains the invalid type
	errMsg := err.Error()
	if !contains(errMsg, "invalid_type") {
		t.Errorf("error message should contain the invalid type, got: %s", errMsg)
	}

	// Check that error message mentions some valid types
	if !contains(errMsg, "file") && !contains(errMsg, "command") {
		t.Errorf("error message should list valid types, got: %s", errMsg)
	}
}

func TestEntryType_MarshalJSON(t *testing.T) {
	tests := []struct {
		name     string
		et       EntryType
		expected string
	}{
		{"file type", EntryTypeFile, `"file"`},
		{"command type", EntryTypeCommand, `"command"`},
		{"command_result type", EntryTypeCommandResult, `"command_result"`},
		{"task type", EntryTypeTask, `"task"`},
		{"task_result type", EntryTypeTaskResult, `"task_result"`},
		{"search_result type", EntryTypeSearchResult, `"search_result"`},
		{"summary type", EntryTypeSummary, `"summary"`},
		{"context_request type", EntryTypeContextRequest, `"context_request"`},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := json.Marshal(tt.et)
			if err != nil {
				t.Fatalf("json.Marshal(%q) error: %v", tt.et, err)
			}

			if string(got) != tt.expected {
				t.Errorf("json.Marshal(%q) = %s, want %s", tt.et, got, tt.expected)
			}
		})
	}
}

func TestEntryType_UnmarshalJSON(t *testing.T) {
	tests := []struct {
		name        string
		input       string
		expected    EntryType
		expectError bool
	}{
		// Valid inputs
		{"file type", `"file"`, EntryTypeFile, false},
		{"command type", `"command"`, EntryTypeCommand, false},
		{"command_result type", `"command_result"`, EntryTypeCommandResult, false},
		{"task type", `"task"`, EntryTypeTask, false},
		{"task_result type", `"task_result"`, EntryTypeTaskResult, false},
		{"search_result type", `"search_result"`, EntryTypeSearchResult, false},
		{"summary type", `"summary"`, EntryTypeSummary, false},
		{"context_request type", `"context_request"`, EntryTypeContextRequest, false},

		// Case insensitive via ParseEntryType
		{"FILE uppercase", `"FILE"`, EntryTypeFile, false},
		{"File mixed case", `"File"`, EntryTypeFile, false},

		// Invalid inputs
		{"empty string", `""`, EntryType(""), true},
		{"invalid type", `"invalid"`, EntryType(""), true},
		{"number", `123`, EntryType(""), true},
		{"null", `null`, EntryType(""), true},
		{"array", `["file"]`, EntryType(""), true},
		{"object", `{"type":"file"}`, EntryType(""), true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var got EntryType
			err := json.Unmarshal([]byte(tt.input), &got)

			if tt.expectError {
				if err == nil {
					t.Errorf("json.Unmarshal(%s) expected error, got nil", tt.input)
				}
				return
			}

			if err != nil {
				t.Errorf("json.Unmarshal(%s) unexpected error: %v", tt.input, err)
				return
			}

			if got != tt.expected {
				t.Errorf("json.Unmarshal(%s) = %q, want %q", tt.input, got, tt.expected)
			}
		})
	}
}

func TestEntryType_JSON_RoundTrip(t *testing.T) {
	for _, et := range AllEntryTypes() {
		t.Run(et.String(), func(t *testing.T) {
			// Marshal
			data, err := json.Marshal(et)
			if err != nil {
				t.Fatalf("json.Marshal(%q) error: %v", et, err)
			}

			// Unmarshal
			var got EntryType
			if err := json.Unmarshal(data, &got); err != nil {
				t.Fatalf("json.Unmarshal(%s) error: %v", data, err)
			}

			// Compare
			if got != et {
				t.Errorf("round-trip failed: got %q, want %q", got, et)
			}
		})
	}
}

func TestEntryType_InStruct_JSON(t *testing.T) {
	type TestStruct struct {
		Name string    `json:"name"`
		Type EntryType `json:"type"`
	}

	tests := []struct {
		name        string
		input       string
		expected    TestStruct
		expectError bool
	}{
		{
			name:     "valid struct with file type",
			input:    `{"name":"test","type":"file"}`,
			expected: TestStruct{Name: "test", Type: EntryTypeFile},
		},
		{
			name:     "valid struct with command type",
			input:    `{"name":"test","type":"command"}`,
			expected: TestStruct{Name: "test", Type: EntryTypeCommand},
		},
		{
			name:        "invalid entry type in struct",
			input:       `{"name":"test","type":"invalid"}`,
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var got TestStruct
			err := json.Unmarshal([]byte(tt.input), &got)

			if tt.expectError {
				if err == nil {
					t.Error("expected error, got nil")
				}
				return
			}

			if err != nil {
				t.Errorf("unexpected error: %v", err)
				return
			}

			if got != tt.expected {
				t.Errorf("got %+v, want %+v", got, tt.expected)
			}
		})
	}
}

func TestAllEntryTypes(t *testing.T) {
	allTypes := AllEntryTypes()

	// Check count
	expectedCount := 8
	if len(allTypes) != expectedCount {
		t.Errorf("AllEntryTypes() returned %d types, want %d", len(allTypes), expectedCount)
	}

	// Check all types are valid
	for _, et := range allTypes {
		if !et.IsValid() {
			t.Errorf("AllEntryTypes() contains invalid type: %q", et)
		}
	}

	// Check for expected types
	expectedTypes := map[EntryType]bool{
		EntryTypeFile:           false,
		EntryTypeCommand:        false,
		EntryTypeCommandResult:  false,
		EntryTypeTask:           false,
		EntryTypeTaskResult:     false,
		EntryTypeSearchResult:   false,
		EntryTypeSummary:        false,
		EntryTypeContextRequest: false,
	}

	for _, et := range allTypes {
		if _, ok := expectedTypes[et]; !ok {
			t.Errorf("AllEntryTypes() contains unexpected type: %q", et)
		}
		expectedTypes[et] = true
	}

	for et, found := range expectedTypes {
		if !found {
			t.Errorf("AllEntryTypes() missing expected type: %q", et)
		}
	}
}

func TestEntryType_Constants(t *testing.T) {
	// Verify constant values match expected strings
	tests := []struct {
		constant EntryType
		expected string
	}{
		{EntryTypeFile, "file"},
		{EntryTypeCommand, "command"},
		{EntryTypeCommandResult, "command_result"},
		{EntryTypeTask, "task"},
		{EntryTypeTaskResult, "task_result"},
		{EntryTypeSearchResult, "search_result"},
		{EntryTypeSummary, "summary"},
		{EntryTypeContextRequest, "context_request"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			if string(tt.constant) != tt.expected {
				t.Errorf("constant value = %q, want %q", tt.constant, tt.expected)
			}
		})
	}
}

// Helper function
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > 0 && containsHelper(s, substr))
}

func containsHelper(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
