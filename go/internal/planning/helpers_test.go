package planning

import (
	"os"
	"path/filepath"
	"testing"
)

func TestExtractFilePath(t *testing.T) {
	tests := []struct {
		name     string
		text     string
		fileType string
		want     string
	}{
		{
			name:     "research file",
			text:     "Created file at thoughts/searchable/shared/research/2026-01-01-test.md",
			fileType: "research",
			want:     "thoughts/searchable/shared/research/2026-01-01-test.md",
		},
		{
			name:     "plans file",
			text:     "Plan saved to thoughts/searchable/plans/2026-01-01-feature/00-overview.md successfully",
			fileType: "plans",
			want:     "thoughts/searchable/plans/2026-01-01-feature/00-overview.md",
		},
		{
			name:     "no match",
			text:     "No file path here",
			fileType: "research",
			want:     "",
		},
		{
			name:     "multiple paths - first match",
			text:     "thoughts/searchable/shared/research/first.md and thoughts/searchable/shared/research/second.md",
			fileType: "research",
			want:     "thoughts/searchable/shared/research/first.md",
		},
		{
			name:     "path in backticks",
			text:     "Created file: `thoughts/searchable/shared/research/2026-01-09-test.md`",
			fileType: "research",
			want:     "thoughts/searchable/shared/research/2026-01-09-test.md",
		},
		{
			name:     "path in double quotes",
			text:     "The file is located at \"thoughts/searchable/shared/research/2026-01-09-test.md\"",
			fileType: "research",
			want:     "thoughts/searchable/shared/research/2026-01-09-test.md",
		},
		{
			name:     "path in single quotes",
			text:     "Output saved to 'thoughts/searchable/plans/2026-01-09-feature.md'",
			fileType: "plans",
			want:     "thoughts/searchable/plans/2026-01-09-feature.md",
		},
		{
			name:     "path with surrounding text",
			text:     "I've created the research file at thoughts/searchable/research/2026-01-09-pipeline-research.md for your review.",
			fileType: "research",
			want:     "thoughts/searchable/research/2026-01-09-pipeline-research.md",
		},
		{
			name:     "path in markdown code block",
			text:     "File created:\n```\nthoughts/searchable/shared/research/test.md\n```",
			fileType: "research",
			want:     "thoughts/searchable/shared/research/test.md",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := ExtractFilePath(tt.text, tt.fileType)
			if got != tt.want {
				t.Errorf("ExtractFilePath() = %q, want %q", got, tt.want)
			}
		})
	}
}

func TestExtractOpenQuestions(t *testing.T) {
	text := `# Research Summary

Some content here.

## Open Questions

- What is the best approach?
- How should we handle errors?
* Third question here

## Next Section

This should not be included.
`

	questions := ExtractOpenQuestions(text)

	if len(questions) != 3 {
		t.Errorf("expected 3 questions, got %d", len(questions))
	}

	if len(questions) > 0 && questions[0] != "What is the best approach?" {
		t.Errorf("first question wrong: %q", questions[0])
	}
}

func TestExtractOpenQuestionsNumbered(t *testing.T) {
	text := `## Open Questions

1. First question
2. Second question
3. Third question
`

	questions := ExtractOpenQuestions(text)

	if len(questions) != 3 {
		t.Errorf("expected 3 questions, got %d", len(questions))
	}
}

func TestExtractOpenQuestionsEmpty(t *testing.T) {
	text := `# Research
Just some content without questions section.
`

	questions := ExtractOpenQuestions(text)

	if len(questions) != 0 {
		t.Errorf("expected 0 questions, got %d", len(questions))
	}
}

func TestExtractPhaseFiles(t *testing.T) {
	text := `Created the following phase files:
- thoughts/searchable/shared/plans/2026-01-01-feature/00-overview.md
- thoughts/searchable/shared/plans/2026-01-01-feature/01-phase-1.md
- thoughts/searchable/shared/plans/2026-01-01-feature/02-phase-2.md
`

	files := ExtractPhaseFiles(text)

	if len(files) != 3 {
		t.Errorf("expected 3 files, got %d", len(files))
	}

	// Check deduplication
	text2 := `thoughts/searchable/plans/test/01-phase.md appears twice: thoughts/searchable/plans/test/01-phase.md`
	files2 := ExtractPhaseFiles(text2)
	if len(files2) != 1 {
		t.Errorf("expected 1 file after dedup, got %d", len(files2))
	}
}

func TestResolveFilePath(t *testing.T) {
	// Create temp directory structure
	tempDir, err := os.MkdirTemp("", "test-resolve-*")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Create test file
	testFile := filepath.Join(tempDir, "thoughts", "searchable", "shared", "research", "test.md")
	os.MkdirAll(filepath.Dir(testFile), 0755)
	os.WriteFile(testFile, []byte("test"), 0644)

	// Test absolute path
	resolved := ResolveFilePath(testFile, tempDir)
	if resolved != testFile {
		t.Errorf("absolute path: got %q, want %q", resolved, testFile)
	}

	// Test relative path
	relPath := "thoughts/searchable/shared/research/test.md"
	resolved = ResolveFilePath(relPath, tempDir)
	if resolved != testFile {
		t.Errorf("relative path: got %q, want %q", resolved, testFile)
	}

	// Test filename only (should find via search)
	resolved = ResolveFilePath("test.md", tempDir)
	if resolved != testFile {
		t.Errorf("filename search: got %q, want %q", resolved, testFile)
	}

	// Test non-existent
	resolved = ResolveFilePath("nonexistent.md", tempDir)
	if resolved != "" {
		t.Errorf("non-existent should return empty: got %q", resolved)
	}
}

func TestExtractResearchSummary(t *testing.T) {
	content := `# Research: Test Topic

This is the first line of the summary.
This is the second line.
This is the third line.
This is the fourth line.

## Details
More content here.
`

	summary := ExtractResearchSummary(content, 3)
	if summary == "" {
		t.Error("summary should not be empty")
	}

	// Should contain first 3 lines
	if len(summary) < 20 {
		t.Error("summary seems too short")
	}
}

func TestDetectQuestionIndicators(t *testing.T) {
	tests := []struct {
		text     string
		expected bool
	}{
		{"Could you clarify the requirements?", true},
		{"Can you provide more details?", true},
		{"What is the expected behavior?", true},
		{"How should we implement this?", true},
		{"This is a statement.", false},
		{"Please clarify the scope.", true},
		{"Does this work?", true},
		{"Implementation complete", false},
	}

	for _, tt := range tests {
		got := DetectQuestionIndicators(tt.text)
		if got != tt.expected {
			t.Errorf("DetectQuestionIndicators(%q) = %v, want %v", tt.text, got, tt.expected)
		}
	}
}

func TestGenerateFunctionID(t *testing.T) {
	tests := []struct {
		description string
		want        string
	}{
		{"authenticate user credentials", "Auth.authenticate"},
		{"validator validates input data", "Validator.validate"},
		{"create new user account", "User.create"},
		{"fetch API data", "API.fetch"},
		{"store to database", "Database.store"},
		{"process incoming message", "MessageHandler.process"},
		{"handle error condition", "ErrorHandler.handle"},
		{"some generic implementation", "Implementation.perform"},
		{"UserService create", "User.create"},
	}

	for _, tt := range tests {
		got := GenerateFunctionID(tt.description)
		if got != tt.want {
			t.Errorf("GenerateFunctionID(%q) = %q, want %q", tt.description, got, tt.want)
		}
	}
}
