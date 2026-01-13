package planning

import (
	"testing"
)

func TestDefaultDecompositionConfig(t *testing.T) {
	config := DefaultDecompositionConfig()

	if config.MaxSubProcesses != 15 {
		t.Errorf("MaxSubProcesses = %d, want 15", config.MaxSubProcesses)
	}
	if config.MinSubProcesses != 2 {
		t.Errorf("MinSubProcesses = %d, want 2", config.MinSubProcesses)
	}
	if !config.IncludeAcceptanceCriteria {
		t.Error("IncludeAcceptanceCriteria should be true by default")
	}
	if config.ExpandDimensions {
		t.Error("ExpandDimensions should be false by default")
	}
}

func TestDecompositionStatsSummary(t *testing.T) {
	stats := &DecompositionStats{
		RequirementsFound:    5,
		SubprocessesExpanded: 15,
		TotalNodes:          20,
		ExtractionTimeMs:    1000,
		ExpansionTimeMs:     2000,
	}

	summary := stats.Summary()
	if summary == "" {
		t.Error("summary should not be empty")
	}
	// Should contain requirement count
	if !contains(summary, "5 requirements") {
		t.Error("summary should contain requirement count")
	}
	// Should contain subprocess count
	if !contains(summary, "15 subprocesses") {
		t.Error("summary should contain subprocess count")
	}
	// Should contain time
	if !contains(summary, "3.0s") {
		t.Error("summary should contain total time")
	}
}

func TestExtractJSON(t *testing.T) {
	tests := []struct {
		name string
		text string
		want string
	}{
		{
			name: "simple json",
			text: `{"key": "value"}`,
			want: `{"key": "value"}`,
		},
		{
			name: "json with surrounding text",
			text: `Here is the result: {"data": 123} and more text`,
			want: `{"data": 123}`,
		},
		{
			name: "nested json",
			text: `{"outer": {"inner": "value"}}`,
			want: `{"outer": {"inner": "value"}}`,
		},
		{
			name: "no json",
			text: "No JSON here",
			want: "",
		},
		{
			name: "malformed - only opening brace",
			text: "{ no closing",
			want: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := extractJSON(tt.text)
			if got != tt.want {
				t.Errorf("extractJSON(%q) = %q, want %q", tt.text, got, tt.want)
			}
		})
	}
}

func TestTruncateString(t *testing.T) {
	tests := []struct {
		s      string
		maxLen int
		want   string
	}{
		{"hello", 10, "hello"},
		{"hello world", 5, "hello"},
		{"", 5, ""},
		{"test", 4, "test"},
	}

	for _, tt := range tests {
		got := truncateString(tt.s, tt.maxLen)
		if got != tt.want {
			t.Errorf("truncateString(%q, %d) = %q, want %q", tt.s, tt.maxLen, got, tt.want)
		}
	}
}

func TestDecomposeRequirementsEmptyContent(t *testing.T) {
	_, err := DecomposeRequirements("", ".", nil, nil, nil)
	if err == nil {
		t.Error("expected error for empty content")
	}
	if err.Code != ErrEmptyContent {
		t.Errorf("expected ErrEmptyContent, got %s", err.Code)
	}
}

func TestDecomposeRequirementsWhitespaceContent(t *testing.T) {
	_, err := DecomposeRequirements("   \n\t  ", ".", nil, nil, nil)
	if err == nil {
		t.Error("expected error for whitespace-only content")
	}
	if err.Code != ErrEmptyContent {
		t.Errorf("expected ErrEmptyContent, got %s", err.Code)
	}
}

func TestCreateBasicChildNodes(t *testing.T) {
	parent := &RequirementNode{
		ID:          "REQ_000",
		Description: "Parent",
		Type:        "parent",
	}
	stats := &DecompositionStats{}

	subProcesses := []string{"subprocess 1", "subprocess 2"}
	createBasicChildNodes(parent, "REQ_000", subProcesses, stats)

	if len(parent.Children) != 2 {
		t.Errorf("expected 2 children, got %d", len(parent.Children))
	}
	if stats.SubprocessesExpanded != 2 {
		t.Errorf("expected 2 subprocesses expanded, got %d", stats.SubprocessesExpanded)
	}

	// Check child IDs
	if parent.Children[0].ID != "REQ_000.1" {
		t.Errorf("first child ID = %s, want REQ_000.1", parent.Children[0].ID)
	}
	if parent.Children[1].ID != "REQ_000.2" {
		t.Errorf("second child ID = %s, want REQ_000.2", parent.Children[1].ID)
	}
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > 0 && containsAt(s, substr, 0))
}

func containsAt(s, substr string, start int) bool {
	for i := start; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
