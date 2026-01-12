package planning

import (
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

// ExtractFilePath extracts a file path matching a specific type from text.
// Pattern: thoughts/...{file_type}...*.md
// Handles various formats: backticks, quotes, bare paths
func ExtractFilePath(text, fileType string) string {
	// Build patterns dynamically with fileType
	quotedFileType := regexp.QuoteMeta(fileType)

	patterns := []string{
		// Pattern 1: Path in backticks with fileType
		"`(thoughts/[^`]+" + quotedFileType + "[^`]*\\.md)`",
		// Pattern 2: Path in double quotes with fileType
		`"(thoughts/[^"]+` + quotedFileType + `[^"]*\.md)"`,
		// Pattern 3: Path in single quotes with fileType
		`'(thoughts/[^']+` + quotedFileType + `[^']*\.md)'`,
		// Pattern 4: Bare path with fileType (original pattern)
		`(thoughts/[^\s]+` + quotedFileType + `[^\s]*\.md)`,
		// Pattern 5: Any thoughts path containing fileType (more lenient)
		`(thoughts/[^\s\)\]"'` + "`" + `]*` + quotedFileType + `[^\s\)\]"'` + "`" + `]*\.md)`,
	}

	for _, pattern := range patterns {
		re := regexp.MustCompile(pattern)
		matches := re.FindStringSubmatch(text)
		if len(matches) > 1 {
			// Return the captured group (without quotes/backticks)
			return matches[1]
		}
	}

	return ""
}

// ExtractOpenQuestions extracts bullet/numbered items from an "Open Questions" section.
func ExtractOpenQuestions(text string) []string {
	var questions []string
	lines := strings.Split(text, "\n")
	inSection := false

	for _, line := range lines {
		trimmed := strings.TrimSpace(line)

		// Check for Open Questions section header
		if strings.Contains(strings.ToLower(trimmed), "open questions") {
			inSection = true
			continue
		}

		// Check for next section header (exit)
		if inSection && strings.HasPrefix(trimmed, "#") {
			break
		}

		// Extract bullet or numbered items
		if inSection {
			if strings.HasPrefix(trimmed, "- ") {
				questions = append(questions, strings.TrimPrefix(trimmed, "- "))
			} else if strings.HasPrefix(trimmed, "* ") {
				questions = append(questions, strings.TrimPrefix(trimmed, "* "))
			} else if len(trimmed) > 2 && trimmed[0] >= '0' && trimmed[0] <= '9' && trimmed[1] == '.' {
				questions = append(questions, strings.TrimSpace(trimmed[2:]))
			}
		}
	}

	return questions
}

// ExtractPhaseFiles extracts phase file paths from text.
// Pattern: thoughts/.../NN-*.md
func ExtractPhaseFiles(text string) []string {
	pattern := `(thoughts/[^\s]+/\d{2}-[^\s]+\.md)`
	re := regexp.MustCompile(pattern)
	matches := re.FindAllString(text, -1)

	// Deduplicate
	seen := make(map[string]bool)
	var result []string
	for _, m := range matches {
		if !seen[m] {
			seen[m] = true
			result = append(result, m)
		}
	}

	return result
}

// ResolveFilePath tries to resolve a file path to an existing file.
// Tries: absolute path, relative from project, filename search.
func ResolveFilePath(path, projectPath string) string {
	// Try as absolute path
	if filepath.IsAbs(path) {
		if _, err := os.Stat(path); err == nil {
			return path
		}
	}

	// Try relative from project path
	relPath := filepath.Join(projectPath, path)
	if _, err := os.Stat(relPath); err == nil {
		return relPath
	}

	// Try searching in thoughts directories
	searchDirs := []string{
		filepath.Join(projectPath, "thoughts", "searchable", "shared"),
		filepath.Join(projectPath, "thoughts", "shared"),
	}

	basename := filepath.Base(path)
	for _, dir := range searchDirs {
		var found string
		filepath.Walk(dir, func(p string, info os.FileInfo, err error) error {
			if err != nil || found != "" {
				return nil
			}
			if info.IsDir() {
				return nil
			}
			// Exact match
			if filepath.Base(p) == basename {
				found = p
				return filepath.SkipAll
			}
			// Suffix match
			if strings.HasSuffix(p, basename) {
				found = p
				return filepath.SkipAll
			}
			return nil
		})
		if found != "" {
			return found
		}
	}

	return ""
}

// DiscoverThoughtsFiles finds files in thoughts directories matching a file type.
// Filters by date cutoff if provided.
func DiscoverThoughtsFiles(projectPath, fileType string, dateCutoff time.Time) []string {
	var files []string

	searchDirs := []string{
		filepath.Join(projectPath, "thoughts", "searchable", "shared", fileType),
		filepath.Join(projectPath, "thoughts", "shared", fileType),
	}

	for _, dir := range searchDirs {
		if _, err := os.Stat(dir); os.IsNotExist(err) {
			continue
		}

		entries, err := os.ReadDir(dir)
		if err != nil {
			continue
		}

		for _, entry := range entries {
			if entry.IsDir() {
				continue
			}
			if !strings.HasSuffix(entry.Name(), ".md") {
				continue
			}

			// Check date in filename if cutoff provided
			if !dateCutoff.IsZero() {
				// Pattern: YYYY-MM-DD in filename
				dateRe := regexp.MustCompile(`(\d{4}-\d{2}-\d{2})`)
				if match := dateRe.FindString(entry.Name()); match != "" {
					fileDate, err := time.Parse("2006-01-02", match)
					if err == nil && fileDate.Before(dateCutoff) {
						continue
					}
				}
			}

			files = append(files, filepath.Join(dir, entry.Name()))
		}
	}

	// Sort by name (which typically includes date)
	sort.Strings(files)

	return files
}

// ExtractResearchSummary extracts the first few lines after the title from research content.
func ExtractResearchSummary(content string, maxLines int) string {
	lines := strings.Split(content, "\n")
	var summaryLines []string
	foundTitle := false

	for _, line := range lines {
		trimmed := strings.TrimSpace(line)

		// Skip title line
		if strings.HasPrefix(trimmed, "# ") {
			foundTitle = true
			continue
		}

		// Skip empty lines immediately after title
		if foundTitle && trimmed == "" {
			continue
		}

		// Collect non-empty lines
		if foundTitle && trimmed != "" {
			summaryLines = append(summaryLines, trimmed)
			if len(summaryLines) >= maxLines {
				break
			}
		}
	}

	return strings.Join(summaryLines, " ")
}

// DetectQuestionIndicators checks if text contains question indicators.
func DetectQuestionIndicators(text string) bool {
	lower := strings.ToLower(text)
	indicators := []string{
		"could you",
		"can you",
		"would you",
		"do you",
		"what ",
		"how ",
		"which ",
		"please clarify",
		"please provide",
		"please specify",
	}

	for _, indicator := range indicators {
		if strings.Contains(lower, indicator) {
			return true
		}
	}

	// Check for question marks
	return strings.Contains(text, "?")
}

// GenerateFunctionID generates a semantic function ID from a description.
// Format: Subject.action (e.g., "Auth.authenticate", "Validator.validate")
func GenerateFunctionID(description string) string {
	lower := strings.ToLower(description)

	// Action mapping
	actionMap := map[string]string{
		"authenticate": "authenticate",
		"create":       "create",
		"validate":     "validate",
		"parse":        "parse",
		"transform":    "transform",
		"fetch":        "fetch",
		"store":        "store",
		"delete":       "delete",
		"update":       "update",
		"render":       "render",
		"process":      "process",
		"handle":       "handle",
		"generate":     "generate",
		"compute":      "compute",
		"calculate":    "calculate",
	}

	// Subject mapping (priority-ordered)
	subjectMap := []struct {
		pattern string
		subject string
	}{
		{"auth", "Auth"},
		{"login", "Auth"},
		{"user", "User"},
		{"validation", "Validator"},
		{"validator", "Validator"},
		{"api", "API"},
		{"endpoint", "API"},
		{"database", "Database"},
		{"db", "Database"},
		{"cache", "Cache"},
		{"file", "FileSystem"},
		{"config", "Config"},
		{"setting", "Config"},
		{"error", "ErrorHandler"},
		{"log", "Logger"},
		{"event", "EventHandler"},
		{"message", "MessageHandler"},
		{"service", "Service"},
	}

	// Find action
	action := "perform"
	for keyword, act := range actionMap {
		if strings.Contains(lower, keyword) {
			action = act
			break
		}
	}

	// Find subject
	subject := "Implementation"
	for _, sm := range subjectMap {
		if strings.Contains(lower, sm.pattern) {
			subject = sm.subject
			break
		}
	}

	// Fallback: use first word as subject if capitalized
	words := strings.Fields(description)
	if len(words) > 0 && subject == "Implementation" {
		firstWord := words[0]
		if len(firstWord) > 0 && firstWord[0] >= 'A' && firstWord[0] <= 'Z' {
			subject = firstWord
		}
	}

	return subject + "." + action
}
