// Package jsonutil provides JSON utilities for reading, writing, and streaming JSON data.
package jsonutil

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// ReadFile reads a JSON file and unmarshals it into the given value.
func ReadFile(path string, v any) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("failed to read file: %w", err)
	}
	if err := json.Unmarshal(data, v); err != nil {
		return fmt.Errorf("failed to unmarshal JSON: %w", err)
	}
	return nil
}

// WriteFile writes the given value as JSON to a file.
// Uses atomic write (temp file + rename) to prevent corruption.
func WriteFile(path string, v any, indent ...bool) error {
	var data []byte
	var err error

	if len(indent) > 0 && indent[0] {
		data, err = json.MarshalIndent(v, "", "  ")
	} else {
		data, err = json.Marshal(v)
	}
	if err != nil {
		return fmt.Errorf("failed to marshal JSON: %w", err)
	}

	return WriteFileAtomic(path, data)
}

// WriteFileAtomic writes data to a file using atomic write pattern.
// It writes to a temp file first, then renames to the target path.
func WriteFileAtomic(path string, data []byte) error {
	dir := filepath.Dir(path)

	// Create parent directory if needed
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create directory: %w", err)
	}

	// Create temp file in same directory (for atomic rename on same filesystem)
	tempFile, err := os.CreateTemp(dir, ".tmp-*")
	if err != nil {
		return fmt.Errorf("failed to create temp file: %w", err)
	}
	tempPath := tempFile.Name()

	// Clean up temp file on error
	defer func() {
		if tempPath != "" {
			os.Remove(tempPath)
		}
	}()

	// Write data to temp file
	if _, err := tempFile.Write(data); err != nil {
		tempFile.Close()
		return fmt.Errorf("failed to write temp file: %w", err)
	}

	if err := tempFile.Close(); err != nil {
		return fmt.Errorf("failed to close temp file: %w", err)
	}

	// Rename temp file to target path (atomic on same filesystem)
	if err := os.Rename(tempPath, path); err != nil {
		return fmt.Errorf("failed to rename temp file: %w", err)
	}

	// Clear tempPath so defer doesn't remove the successfully renamed file
	tempPath = ""
	return nil
}

// PrettyPrint returns a pretty-printed JSON string.
func PrettyPrint(v any) (string, error) {
	data, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return "", err
	}
	return string(data), nil
}

// Compact returns a compact JSON string (no whitespace).
func Compact(v any) (string, error) {
	data, err := json.Marshal(v)
	if err != nil {
		return "", err
	}
	return string(data), nil
}

// StreamReader reads JSON objects from a stream one at a time.
type StreamReader struct {
	decoder *json.Decoder
}

// NewStreamReader creates a new StreamReader from an io.Reader.
func NewStreamReader(r io.Reader) *StreamReader {
	return &StreamReader{
		decoder: json.NewDecoder(r),
	}
}

// Decode reads the next JSON value from the stream into v.
// Returns io.EOF when there are no more values.
func (sr *StreamReader) Decode(v any) error {
	return sr.decoder.Decode(v)
}

// More returns true if there are more values to read.
func (sr *StreamReader) More() bool {
	return sr.decoder.More()
}

// Token returns the next JSON token in the stream.
func (sr *StreamReader) Token() (json.Token, error) {
	return sr.decoder.Token()
}

// StreamWriter writes JSON objects to a stream one at a time.
type StreamWriter struct {
	encoder *json.Encoder
}

// NewStreamWriter creates a new StreamWriter to an io.Writer.
func NewStreamWriter(w io.Writer) *StreamWriter {
	return &StreamWriter{
		encoder: json.NewEncoder(w),
	}
}

// Encode writes a JSON value to the stream.
func (sw *StreamWriter) Encode(v any) error {
	return sw.encoder.Encode(v)
}

// SetIndent sets the indentation for subsequent writes.
func (sw *StreamWriter) SetIndent(prefix, indent string) {
	sw.encoder.SetIndent(prefix, indent)
}

// SetEscapeHTML enables or disables HTML escaping.
func (sw *StreamWriter) SetEscapeHTML(escape bool) {
	sw.encoder.SetEscapeHTML(escape)
}

// ExtractJSON extracts JSON from mixed text content.
// This is useful for parsing Claude CLI output that may contain
// text before or after JSON objects.
func ExtractJSON(text string) (string, error) {
	// Try to find JSON object
	if json, found := findJSONObject(text); found {
		return json, nil
	}

	// Try to find JSON array
	if json, found := findJSONArray(text); found {
		return json, nil
	}

	return "", errors.New("no JSON found in text")
}

// ExtractJSONAs extracts JSON from text and unmarshals it into v.
func ExtractJSONAs(text string, v any) error {
	jsonStr, err := ExtractJSON(text)
	if err != nil {
		return err
	}
	return json.Unmarshal([]byte(jsonStr), v)
}

// findJSONObject finds the first complete JSON object in text.
func findJSONObject(text string) (string, bool) {
	return findBalanced(text, '{', '}')
}

// findJSONArray finds the first complete JSON array in text.
func findJSONArray(text string) (string, bool) {
	return findBalanced(text, '[', ']')
}

// findBalanced finds a balanced bracket structure in text.
func findBalanced(text string, open, close rune) (string, bool) {
	start := -1
	depth := 0
	inString := false
	escape := false

	runes := []rune(text)
	for i, r := range runes {
		if escape {
			escape = false
			continue
		}

		if r == '\\' && inString {
			escape = true
			continue
		}

		if r == '"' && !escape {
			inString = !inString
			continue
		}

		if inString {
			continue
		}

		if r == open {
			if depth == 0 {
				start = i
			}
			depth++
		} else if r == close {
			depth--
			if depth == 0 && start >= 0 {
				result := string(runes[start : i+1])
				// Validate it's actually valid JSON
				if json.Valid([]byte(result)) {
					return result, true
				}
				// If not valid, continue searching
				start = -1
			}
		}
	}

	return "", false
}

// ExtractAllJSON extracts all JSON objects and arrays from text.
func ExtractAllJSON(text string) []string {
	var results []string

	// Find all JSON objects
	remaining := text
	for {
		if json, found := findJSONObject(remaining); found {
			results = append(results, json)
			idx := strings.Index(remaining, json)
			remaining = remaining[idx+len(json):]
		} else {
			break
		}
	}

	// Find all JSON arrays
	remaining = text
	for {
		if json, found := findJSONArray(remaining); found {
			results = append(results, json)
			idx := strings.Index(remaining, json)
			remaining = remaining[idx+len(json):]
		} else {
			break
		}
	}

	return results
}

// ExtractJSONFromCodeBlock extracts JSON from markdown code blocks.
// Handles ```json and ``` blocks.
func ExtractJSONFromCodeBlock(text string) (string, error) {
	// Pattern for ```json ... ``` or ``` ... ```
	re := regexp.MustCompile("(?s)```(?:json)?\\s*\n?(.*?)```")
	matches := re.FindStringSubmatch(text)
	if len(matches) >= 2 {
		content := strings.TrimSpace(matches[1])
		if json.Valid([]byte(content)) {
			return content, nil
		}
	}

	// Fall back to ExtractJSON
	return ExtractJSON(text)
}

// MustMarshal marshals v to JSON and panics on error.
// Use only when you're certain the value can be marshaled.
func MustMarshal(v any) []byte {
	data, err := json.Marshal(v)
	if err != nil {
		panic(fmt.Sprintf("json.Marshal failed: %v", err))
	}
	return data
}

// MustUnmarshal unmarshals JSON data into v and panics on error.
func MustUnmarshal(data []byte, v any) {
	if err := json.Unmarshal(data, v); err != nil {
		panic(fmt.Sprintf("json.Unmarshal failed: %v", err))
	}
}

// Clone creates a deep copy of v by marshaling and unmarshaling.
// This is not the most efficient method but works for any JSON-serializable type.
func Clone[T any](v T) (T, error) {
	var result T
	data, err := json.Marshal(v)
	if err != nil {
		return result, err
	}
	err = json.Unmarshal(data, &result)
	return result, err
}

// Merge merges multiple JSON objects into one.
// Later objects override earlier ones for conflicting keys.
func Merge(objects ...map[string]any) map[string]any {
	result := make(map[string]any)
	for _, obj := range objects {
		for k, v := range obj {
			result[k] = v
		}
	}
	return result
}

// GetPath retrieves a value from a nested JSON structure using a dot-separated path.
// Example: GetPath(obj, "user.address.city")
func GetPath(obj map[string]any, path string) (any, bool) {
	parts := strings.Split(path, ".")
	current := any(obj)

	for _, part := range parts {
		switch v := current.(type) {
		case map[string]any:
			val, ok := v[part]
			if !ok {
				return nil, false
			}
			current = val
		default:
			return nil, false
		}
	}

	return current, true
}

// SetPath sets a value in a nested JSON structure using a dot-separated path.
// Creates intermediate maps as needed.
func SetPath(obj map[string]any, path string, value any) {
	parts := strings.Split(path, ".")
	current := obj

	for i, part := range parts[:len(parts)-1] {
		if next, ok := current[part].(map[string]any); ok {
			current = next
		} else {
			// Create intermediate map
			newMap := make(map[string]any)
			current[part] = newMap
			current = newMap
			_ = i
		}
	}

	current[parts[len(parts)-1]] = value
}
