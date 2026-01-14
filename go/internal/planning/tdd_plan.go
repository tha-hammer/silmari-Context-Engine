package planning

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// TDDPlanResult contains the result of creating a TDD plan from a requirement hierarchy.
type TDDPlanResult struct {
	Success   bool     `json:"success"`
	PlanPaths []string `json:"plan_paths"`
	Output    string   `json:"output"`
	Error     string   `json:"error,omitempty"`
}

// SerializeHierarchyForPrompt converts a RequirementHierarchy to a JSON string for prompt insertion.
func SerializeHierarchyForPrompt(hierarchy *RequirementHierarchy) string {
	data := serializeHierarchyToMap(hierarchy)
	jsonBytes, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return "{\"requirements\": []}"
	}
	return string(jsonBytes)
}

// serializeHierarchyToMap converts hierarchy to a map structure for JSON serialization.
func serializeHierarchyToMap(hierarchy *RequirementHierarchy) map[string]interface{} {
	requirements := make([]map[string]interface{}, 0)
	for _, req := range hierarchy.Requirements {
		requirements = append(requirements, serializeRequirementToMap(req))
	}
	return map[string]interface{}{
		"requirements": requirements,
	}
}

// serializeRequirementToMap converts a RequirementNode to a map for JSON serialization.
func serializeRequirementToMap(req *RequirementNode) map[string]interface{} {
	result := map[string]interface{}{
		"id":          req.ID,
		"description": req.Description,
		"type":        req.Type,
	}

	if req.ParentID != "" {
		result["parent_id"] = req.ParentID
	}

	if len(req.AcceptanceCriteria) > 0 {
		result["acceptance_criteria"] = req.AcceptanceCriteria
	}

	if req.FunctionID != "" {
		result["function_id"] = req.FunctionID
	}

	if len(req.RelatedConcepts) > 0 {
		result["related_concepts"] = req.RelatedConcepts
	}

	if req.Category != "" {
		result["category"] = req.Category
	}

	if req.Implementation != nil {
		impl := map[string]interface{}{}
		if len(req.Implementation.Frontend) > 0 {
			impl["frontend"] = req.Implementation.Frontend
		}
		if len(req.Implementation.Backend) > 0 {
			impl["backend"] = req.Implementation.Backend
		}
		if len(req.Implementation.Middleware) > 0 {
			impl["middleware"] = req.Implementation.Middleware
		}
		if len(req.Implementation.Shared) > 0 {
			impl["shared"] = req.Implementation.Shared
		}
		if len(impl) > 0 {
			result["implementation"] = impl
		}
	}

	if len(req.Children) > 0 {
		children := make([]map[string]interface{}, 0)
		for _, child := range req.Children {
			children = append(children, serializeRequirementToMap(child))
		}
		result["children"] = children
	}

	return result
}

// BuildTDDPlanPrompt constructs the full prompt for TDD plan generation.
func BuildTDDPlanPrompt(instructionContent string, hierarchy *RequirementHierarchy, planName string) string {
	hierarchyJSON := SerializeHierarchyForPrompt(hierarchy)

	var sb strings.Builder
	sb.WriteString(instructionContent)
	sb.WriteString("\n\n## Requirement Hierarchy\n\n")
	sb.WriteString("The following requirement hierarchy should be used to generate the TDD plan:\n\n")
	sb.WriteString("```json\n")
	sb.WriteString(hierarchyJSON)
	sb.WriteString("\n```\n\n")
	sb.WriteString(fmt.Sprintf("## Plan Name\n\nGenerate TDD plan with name: %s\n", planName))

	return sb.String()
}

// ExtractPlanPaths extracts TDD plan file paths from Claude output.
func ExtractPlanPaths(output string) []string {
	// Pattern to match plan file paths
	pattern := regexp.MustCompile(`(?:^|[\s\-:])?(thoughts/searchable/shared/plans/[^\s\n\r]+\.md)`)

	matches := pattern.FindAllStringSubmatch(output, -1)
	paths := make([]string, 0)
	seen := make(map[string]bool)

	for _, match := range matches {
		if len(match) > 1 {
			path := match[1]
			if !seen[path] {
				seen[path] = true
				paths = append(paths, path)
			}
		}
	}

	return paths
}

// CreateTDDPlanFromHierarchy creates TDD plan documents from a requirement hierarchy.
// It loads the create_tdd_plan.md instruction file, builds a prompt with the hierarchy,
// invokes Claude to generate the plan, and extracts the resulting plan file paths.
func CreateTDDPlanFromHierarchy(projectPath string, hierarchy *RequirementHierarchy, planName, additionalContext string) *TDDPlanResult {
	result := &TDDPlanResult{
		Success:   false,
		PlanPaths: []string{},
		Output:    "",
		Error:     "",
	}

	// Load instruction file
	instructionPath := filepath.Join(projectPath, ".claude", "commands", "create_tdd_plan.md")
	instructionContent, err := os.ReadFile(instructionPath)
	if err != nil {
		result.Error = fmt.Sprintf("Failed to load create_tdd_plan.md: %v", err)
		return result
	}

	// Build prompt
	prompt := BuildTDDPlanPrompt(string(instructionContent), hierarchy, planName)
	if additionalContext != "" {
		prompt += "\n\n## Additional Context\n\n" + additionalContext
	}

	// Invoke Claude (prompt, timeoutSecs, stream, cwd)
	claudeResult := RunClaudeSync(prompt, 600, false, projectPath)
	if !claudeResult.Success {
		result.Error = fmt.Sprintf("Claude invocation failed: %s", claudeResult.Error)
		return result
	}

	// Extract plan paths
	planPaths := ExtractPlanPaths(claudeResult.Output)

	result.Success = true
	result.Output = claudeResult.Output
	result.PlanPaths = planPaths
	return result
}
