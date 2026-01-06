package planning

import (
	"testing"
)

func TestNewStepResult(t *testing.T) {
	result := NewStepResult()

	if !result.Success {
		t.Error("new step result should be successful")
	}
	if result.Data == nil {
		t.Error("data map should be initialized")
	}
}

func TestStepResultSetError(t *testing.T) {
	result := NewStepResult()
	result.SetError(nil)

	// nil error should set Success to false but not set Error string
	if result.Success {
		t.Error("SetError should mark result as failed")
	}
	if result.Error != "" {
		t.Error("nil error should not set error string")
	}
}

func TestExtractBeadsID(t *testing.T) {
	tests := []struct {
		name   string
		output string
		want   string
	}{
		{
			name:   "standard output",
			output: "Created beads-abc123",
			want:   "beads-abc123",
		},
		{
			name:   "output with newlines",
			output: "Creating issue...\nCreated beads-xyz789\nDone",
			want:   "beads-xyz789",
		},
		{
			name:   "no beads id",
			output: "No beads here",
			want:   "",
		},
		{
			name:   "beads with numbers",
			output: "beads-12ab34cd",
			want:   "beads-12ab34cd",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := extractBeadsID(tt.output)
			if got != tt.want {
				t.Errorf("extractBeadsID(%q) = %q, want %q", tt.output, got, tt.want)
			}
		})
	}
}

func TestExtractPhaseName(t *testing.T) {
	tests := []struct {
		filename string
		want     string
	}{
		{"01-phase-1-setup.md", "1 Setup"},
		{"02-implement-feature.md", "Feature"},
		{"simple.md", "simple"},
	}

	for _, tt := range tests {
		got := extractPhaseName(tt.filename)
		if got != tt.want {
			t.Errorf("extractPhaseName(%q) = %q, want %q", tt.filename, got, tt.want)
		}
	}
}
