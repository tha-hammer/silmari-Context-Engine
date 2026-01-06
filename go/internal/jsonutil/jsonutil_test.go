package jsonutil

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

type testStruct struct {
	Name  string `json:"name"`
	Value int    `json:"value"`
}

func TestReadWriteFile(t *testing.T) {
	dir, err := os.MkdirTemp("", "jsonutil-test")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(dir)

	path := filepath.Join(dir, "test.json")
	original := testStruct{Name: "test", Value: 42}

	// Write
	if err := WriteFile(path, original, false); err != nil {
		t.Fatalf("WriteFile failed: %v", err)
	}

	// Read
	var result testStruct
	if err := ReadFile(path, &result); err != nil {
		t.Fatalf("ReadFile failed: %v", err)
	}

	if result.Name != original.Name || result.Value != original.Value {
		t.Errorf("Read got %+v, want %+v", result, original)
	}
}

func TestWriteFileIndented(t *testing.T) {
	dir, err := os.MkdirTemp("", "jsonutil-test")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(dir)

	path := filepath.Join(dir, "test.json")
	original := testStruct{Name: "test", Value: 42}

	// Write with indent
	if err := WriteFile(path, original, true); err != nil {
		t.Fatalf("WriteFile failed: %v", err)
	}

	// Check content has newlines (indented)
	data, _ := os.ReadFile(path)
	if !strings.Contains(string(data), "\n") {
		t.Error("Expected indented output with newlines")
	}
}

func TestWriteFileAtomic(t *testing.T) {
	dir, err := os.MkdirTemp("", "jsonutil-test")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(dir)

	// Test with nested directory that doesn't exist
	path := filepath.Join(dir, "nested", "dir", "test.json")
	data := []byte(`{"test": true}`)

	if err := WriteFileAtomic(path, data); err != nil {
		t.Fatalf("WriteFileAtomic failed: %v", err)
	}

	// Verify content
	content, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("ReadFile failed: %v", err)
	}
	if !bytes.Equal(content, data) {
		t.Errorf("Content = %s, want %s", content, data)
	}
}

func TestPrettyPrint(t *testing.T) {
	obj := map[string]any{"name": "test", "value": 42}

	result, err := PrettyPrint(obj)
	if err != nil {
		t.Fatalf("PrettyPrint failed: %v", err)
	}

	if !strings.Contains(result, "\n") {
		t.Error("Expected indented output with newlines")
	}

	// Should be valid JSON
	if !json.Valid([]byte(result)) {
		t.Error("Result is not valid JSON")
	}
}

func TestCompact(t *testing.T) {
	obj := map[string]any{"name": "test", "value": 42}

	result, err := Compact(obj)
	if err != nil {
		t.Fatalf("Compact failed: %v", err)
	}

	if strings.Contains(result, "\n") {
		t.Error("Expected compact output without newlines")
	}

	// Should be valid JSON
	if !json.Valid([]byte(result)) {
		t.Error("Result is not valid JSON")
	}
}

func TestStreamReader(t *testing.T) {
	data := `{"name":"a"}
{"name":"b"}
{"name":"c"}`

	reader := NewStreamReader(strings.NewReader(data))

	var items []testStruct
	for {
		var item testStruct
		err := reader.Decode(&item)
		if err != nil {
			break
		}
		items = append(items, item)
	}

	if len(items) != 3 {
		t.Errorf("Got %d items, want 3", len(items))
	}

	expected := []string{"a", "b", "c"}
	for i, item := range items {
		if item.Name != expected[i] {
			t.Errorf("Item %d name = %s, want %s", i, item.Name, expected[i])
		}
	}
}

func TestStreamWriter(t *testing.T) {
	var buf bytes.Buffer
	writer := NewStreamWriter(&buf)

	items := []testStruct{
		{Name: "a", Value: 1},
		{Name: "b", Value: 2},
	}

	for _, item := range items {
		if err := writer.Encode(item); err != nil {
			t.Fatalf("Encode failed: %v", err)
		}
	}

	// Each item should be on its own line
	lines := strings.Split(strings.TrimSpace(buf.String()), "\n")
	if len(lines) != 2 {
		t.Errorf("Got %d lines, want 2", len(lines))
	}
}

func TestExtractJSON(t *testing.T) {
	tests := []struct {
		name    string
		input   string
		want    string
		wantErr bool
	}{
		{
			name:  "simple object",
			input: `Here is some text {"key": "value"} and more text`,
			want:  `{"key": "value"}`,
		},
		{
			name:  "nested object",
			input: `prefix {"outer": {"inner": 42}} suffix`,
			want:  `{"outer": {"inner": 42}}`,
		},
		{
			name:  "array",
			input: `data: [1, 2, 3] end`,
			want:  `[1, 2, 3]`,
		},
		{
			name:  "object with array",
			input: `result: {"items": [1, 2]} done`,
			want:  `{"items": [1, 2]}`,
		},
		{
			name:  "string with brackets",
			input: `{"text": "hello {world}"} `,
			want:  `{"text": "hello {world}"}`,
		},
		{
			name:    "no json",
			input:   "just some plain text",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := ExtractJSON(tt.input)
			if (err != nil) != tt.wantErr {
				t.Errorf("ExtractJSON() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr && got != tt.want {
				t.Errorf("ExtractJSON() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestExtractJSONAs(t *testing.T) {
	input := `Here is the result: {"name": "test", "value": 42} done`

	var result testStruct
	if err := ExtractJSONAs(input, &result); err != nil {
		t.Fatalf("ExtractJSONAs failed: %v", err)
	}

	if result.Name != "test" || result.Value != 42 {
		t.Errorf("Got %+v, want {Name:test Value:42}", result)
	}
}

func TestExtractAllJSON(t *testing.T) {
	input := `First: {"a": 1} Second: {"b": 2} Array: [1, 2, 3]`

	results := ExtractAllJSON(input)
	if len(results) != 3 {
		t.Errorf("Got %d results, want 3", len(results))
	}
}

func TestExtractJSONFromCodeBlock(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  string
	}{
		{
			name: "json code block",
			input: "Here is the output:\n```json\n{\"key\": \"value\"}\n```\nDone",
			want: `{"key": "value"}`,
		},
		{
			name: "plain code block",
			input: "Result:\n```\n{\"test\": true}\n```",
			want: `{"test": true}`,
		},
		{
			name:  "no code block",
			input: `Just JSON: {"plain": true}`,
			want:  `{"plain": true}`,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := ExtractJSONFromCodeBlock(tt.input)
			if err != nil {
				t.Fatalf("ExtractJSONFromCodeBlock failed: %v", err)
			}
			if got != tt.want {
				t.Errorf("Got %q, want %q", got, tt.want)
			}
		})
	}
}

func TestClone(t *testing.T) {
	original := testStruct{Name: "test", Value: 42}

	cloned, err := Clone(original)
	if err != nil {
		t.Fatalf("Clone failed: %v", err)
	}

	if cloned.Name != original.Name || cloned.Value != original.Value {
		t.Errorf("Clone got %+v, want %+v", cloned, original)
	}

	// Modify original, clone should be unaffected
	original.Name = "modified"
	if cloned.Name == "modified" {
		t.Error("Clone was affected by modifying original")
	}
}

func TestMerge(t *testing.T) {
	obj1 := map[string]any{"a": 1, "b": 2}
	obj2 := map[string]any{"b": 3, "c": 4}

	result := Merge(obj1, obj2)

	if result["a"] != 1 {
		t.Errorf("result[a] = %v, want 1", result["a"])
	}
	if result["b"] != 3 {
		t.Errorf("result[b] = %v, want 3 (from obj2)", result["b"])
	}
	if result["c"] != 4 {
		t.Errorf("result[c] = %v, want 4", result["c"])
	}
}

func TestGetPath(t *testing.T) {
	obj := map[string]any{
		"user": map[string]any{
			"name": "Alice",
			"address": map[string]any{
				"city": "NYC",
			},
		},
	}

	tests := []struct {
		path  string
		want  any
		found bool
	}{
		{"user.name", "Alice", true},
		{"user.address.city", "NYC", true},
		{"user.missing", nil, false},
		{"missing", nil, false},
	}

	for _, tt := range tests {
		got, found := GetPath(obj, tt.path)
		if found != tt.found {
			t.Errorf("GetPath(%q) found = %v, want %v", tt.path, found, tt.found)
		}
		if found && got != tt.want {
			t.Errorf("GetPath(%q) = %v, want %v", tt.path, got, tt.want)
		}
	}
}

func TestSetPath(t *testing.T) {
	obj := make(map[string]any)

	SetPath(obj, "user.address.city", "NYC")

	city, found := GetPath(obj, "user.address.city")
	if !found {
		t.Error("SetPath did not create nested path")
	}
	if city != "NYC" {
		t.Errorf("city = %v, want NYC", city)
	}

	// Overwrite existing
	SetPath(obj, "user.address.city", "LA")
	city, _ = GetPath(obj, "user.address.city")
	if city != "LA" {
		t.Errorf("city = %v, want LA after overwrite", city)
	}
}

func TestMustMarshal(t *testing.T) {
	// Should not panic
	data := MustMarshal(testStruct{Name: "test", Value: 42})
	if !json.Valid(data) {
		t.Error("MustMarshal produced invalid JSON")
	}
}

func TestMustUnmarshal(t *testing.T) {
	data := []byte(`{"name":"test","value":42}`)

	var result testStruct
	MustUnmarshal(data, &result)

	if result.Name != "test" || result.Value != 42 {
		t.Errorf("Got %+v, want {Name:test Value:42}", result)
	}
}
