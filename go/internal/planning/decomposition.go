package planning

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

// DecompositionConfig contains configuration for requirement decomposition.
type DecompositionConfig struct {
	MaxSubProcesses           int  `json:"max_sub_processes"`
	MinSubProcesses           int  `json:"min_sub_processes"`
	IncludeAcceptanceCriteria bool `json:"include_acceptance_criteria"`
	ExpandDimensions          bool `json:"expand_dimensions"`
}

// DefaultDecompositionConfig returns the default configuration.
func DefaultDecompositionConfig() *DecompositionConfig {
	return &DecompositionConfig{
		MaxSubProcesses:           15,
		MinSubProcesses:           2,
		IncludeAcceptanceCriteria: true,
		ExpandDimensions:          false,
	}
}

// ProgressCallback is called to report progress during decomposition.
type ProgressCallback func(message string)

// SaveCallback is called after each requirement is added to the hierarchy.
type SaveCallback func(hierarchy *RequirementHierarchy)

// DecompositionStats contains statistics from the decomposition process.
type DecompositionStats struct {
	RequirementsFound    int `json:"requirements_found"`
	SubprocessesExpanded int `json:"subprocesses_expanded"`
	TotalNodes           int `json:"total_nodes"`
	ExtractionTimeMs     int `json:"extraction_time_ms"`
	ExpansionTimeMs      int `json:"expansion_time_ms"`
}

// Summary returns a human-readable summary.
func (s *DecompositionStats) Summary() string {
	totalTime := float64(s.ExtractionTimeMs+s.ExpansionTimeMs) / 1000.0
	return fmt.Sprintf("  %d requirements, %d subprocesses (%.1fs)",
		s.RequirementsFound, s.SubprocessesExpanded, totalTime)
}

// DecomposeRequirements decomposes research content into a requirement hierarchy.
func DecomposeRequirements(
	researchContent string,
	projectPath string,
	config *DecompositionConfig,
	progress ProgressCallback,
	saveCallback SaveCallback,
) (*RequirementHierarchy, *DecompositionError) {
	if config == nil {
		config = DefaultDecompositionConfig()
	}

	// Default progress callback
	report := progress
	if report == nil {
		report = func(msg string) { fmt.Println(msg) }
	}

	// Validate input
	if strings.TrimSpace(researchContent) == "" {
		return nil, NewDecompositionError(
			ErrEmptyContent,
			"Research content cannot be empty",
			map[string]interface{}{"input_length": len(researchContent)},
		)
	}

	stats := &DecompositionStats{}

	// Step 1: Extract initial requirements using Claude
	report("  Analyzing research with Claude agent SDK...")
	extractionStart := time.Now()

	extractionPrompt := buildExtractionPrompt(researchContent)

	result := RunClaudeSync(extractionPrompt, 1300, true, projectPath)
	if !result.Success {
		return nil, NewDecompositionError(
			ErrBAMLAPIError,
			fmt.Sprintf("Claude agent SDK call failed: %s", result.Error),
			nil,
		)
	}

	// Parse JSON response
	jsonStr := extractJSON(result.Output)
	if jsonStr == "" {
		return nil, NewDecompositionError(
			ErrInvalidJSON,
			"No valid JSON found in Claude response",
			map[string]interface{}{"output_preview": truncateString(result.Output, 500)},
		)
	}

	var data struct {
		Requirements []struct {
			Description     string   `json:"description"`
			SubProcesses    []string `json:"sub_processes"`
			RelatedConcepts []string `json:"related_concepts"`
		} `json:"requirements"`
	}

	if err := json.Unmarshal([]byte(jsonStr), &data); err != nil {
		return nil, NewDecompositionError(
			ErrInvalidJSON,
			fmt.Sprintf("Invalid JSON in response: %v", err),
			map[string]interface{}{"json_str": truncateString(jsonStr, 500)},
		)
	}

	stats.ExtractionTimeMs = int(time.Since(extractionStart).Milliseconds())
	stats.RequirementsFound = len(data.Requirements)

	report(fmt.Sprintf("  ✓ Extracted %d top-level requirements", stats.RequirementsFound))

	// Step 2: Expand each requirement to get implementation details
	hierarchy := NewRequirementHierarchy()
	hierarchy.Metadata["source"] = "agent_sdk_decomposition"
	hierarchy.Metadata["research_length"] = len(researchContent)

	report(fmt.Sprintf("  Expanding %d requirements via LLM...", stats.RequirementsFound))
	expansionStart := time.Now()

	for reqIdx, requirement := range data.Requirements {
		parentID := fmt.Sprintf("REQ_%03d", reqIdx)
		subProcesses := requirement.SubProcesses
		if len(subProcesses) > config.MaxSubProcesses {
			subProcesses = subProcesses[:config.MaxSubProcesses]
		}

		report(fmt.Sprintf("    [%d/%d] Expanding: %s...",
			reqIdx+1, stats.RequirementsFound, truncateString(requirement.Description, 60)))

		// Create parent node
		parentNode := &RequirementNode{
			ID:          parentID,
			Description: requirement.Description,
			Type:        "parent",
		}

		// Call LLM to expand implementation details
		expansionPrompt := buildExpansionPrompt(researchContent, requirement.Description, subProcesses)
		expansionResult := RunClaudeSync(expansionPrompt, 90, true, projectPath)

		if expansionResult.Success {
			expansionJSON := extractJSON(expansionResult.Output)
			if expansionJSON != "" {
				var expansionData struct {
					ImplementationDetails []struct {
						FunctionID         string   `json:"function_id"`
						Description        string   `json:"description"`
						RelatedConcepts    []string `json:"related_concepts"`
						AcceptanceCriteria []string `json:"acceptance_criteria"`
						Implementation     struct {
							Frontend   []string `json:"frontend"`
							Backend    []string `json:"backend"`
							Middleware []string `json:"middleware"`
							Shared     []string `json:"shared"`
						} `json:"implementation"`
					} `json:"implementation_details"`
				}

				if err := json.Unmarshal([]byte(expansionJSON), &expansionData); err == nil {
					// Create child nodes from implementation details
					for implIdx, detail := range expansionData.ImplementationDetails {
						childID := fmt.Sprintf("%s.%d", parentID, implIdx+1)

						implComponents := &ImplementationComponents{
							Frontend:   detail.Implementation.Frontend,
							Backend:    detail.Implementation.Backend,
							Middleware: detail.Implementation.Middleware,
							Shared:     detail.Implementation.Shared,
						}

						functionID := detail.FunctionID
						if functionID == "" {
							functionID = GenerateFunctionID(detail.Description)
						}

						childNode := &RequirementNode{
							ID:                 childID,
							Description:        detail.Description,
							Type:               "sub_process",
							ParentID:           parentID,
							FunctionID:         functionID,
							RelatedConcepts:    detail.RelatedConcepts,
							AcceptanceCriteria: detail.AcceptanceCriteria,
							Implementation:     implComponents,
						}
						parentNode.Children = append(parentNode.Children, childNode)
						stats.SubprocessesExpanded++
					}
				} else {
					// JSON parse failed - create basic nodes
					createBasicChildNodes(parentNode, parentID, subProcesses, stats)
				}
			} else {
				createBasicChildNodes(parentNode, parentID, subProcesses, stats)
			}
		} else {
			// LLM call failed - create basic nodes
			createBasicChildNodes(parentNode, parentID, subProcesses, stats)
		}

		hierarchy.AddRequirement(parentNode)

		// Incremental save after each requirement
		if saveCallback != nil {
			saveCallback(hierarchy)
		}
	}

	stats.ExpansionTimeMs = int(time.Since(expansionStart).Milliseconds())
	stats.TotalNodes = stats.RequirementsFound + stats.SubprocessesExpanded

	report(fmt.Sprintf("  ✓ Expanded %d implementation details via LLM", stats.SubprocessesExpanded))
	report(stats.Summary())

	// Store stats in hierarchy metadata
	hierarchy.Metadata["decomposition_stats"] = map[string]interface{}{
		"requirements_found":    stats.RequirementsFound,
		"subprocesses_expanded": stats.SubprocessesExpanded,
		"total_nodes":           stats.TotalNodes,
		"extraction_time_ms":    stats.ExtractionTimeMs,
		"expansion_time_ms":     stats.ExpansionTimeMs,
	}

	return hierarchy, nil
}

// createBasicChildNodes creates basic child nodes from subprocess descriptions.
func createBasicChildNodes(parent *RequirementNode, parentID string, subProcesses []string, stats *DecompositionStats) {
	for subIdx, subProcess := range subProcesses {
		childID := fmt.Sprintf("%s.%d", parentID, subIdx+1)
		childNode := &RequirementNode{
			ID:          childID,
			Description: subProcess,
			Type:        "sub_process",
			ParentID:    parentID,
			FunctionID:  GenerateFunctionID(subProcess),
		}
		parent.Children = append(parent.Children, childNode)
		stats.SubprocessesExpanded++
	}
}

// buildExtractionPrompt builds the prompt for initial requirement extraction.
func buildExtractionPrompt(researchContent string) string {
	return fmt.Sprintf(`You are an expert software requirements analyst. Your task is to extract EVERY requirement from the scope text. DO NOT summarize. Extract individual requirements from EVERY section.

Research content:
%s

**MANDATORY REQUIREMENTS:**
1. Count all numbered sections in the document (e.g., '## 0.', '## 1.', '## 2.', etc.)
2. Extract AT LEAST 2-5 requirements from EACH numbered section
3. For a document with 15 sections, you MUST extract 30-75+ requirements total
4. DO NOT combine multiple requirements into one - each requirement must be separate
5. Process sections in order: Section 0, then Section 1, then Section 2, etc. - do not skip any

**EXTRACTION METHOD:**

For EACH numbered section (## 0, ## 1, ## 2, etc.):

1. Read the entire section content
2. Find ALL requirement statements (look for: "must", "should", "shall", "will", "needs to", "requires", "supports", "implements", "provides")
3. Extract EACH requirement as a separate item - do not combine them

Return ONLY valid JSON with this exact structure (no markdown, no explanation):
{
    "requirements": [
        {
            "description": "Clear description of the requirement",
            "sub_processes": ["subprocess 1", "subprocess 2", "subprocess 3"]
        }
    ]
}

Extract 3-7 top-level requirements, each with 2-5 sub-processes.
`, researchContent)
}

// buildExpansionPrompt builds the prompt for expanding a requirement.
func buildExpansionPrompt(researchContent, parentDescription string, subProcesses []string) string {
	subProcessJSON, _ := json.Marshal(subProcesses)
	return fmt.Sprintf(`        You are an expert software analyst. Expand each requirement into specific implementation requirements.
        The sofware developer needs to know what detailed requirements are needed to implement this requirement for this project.
        For each implementation requirement:


RESEARCH CONTEXT:
%s

PARENT REQUIREMENT:
%s

SUB-PROCESSES TO EXPAND:
%s

        1. Provide a clear, actionable description
        2. List ALL REQUIRED STEPS to implement the requirement
        3. For each step, provide specific acceptance criteria
        4. Consider technical and functional aspects
        5. If the requirement lists specific actions, questions or decisions, include them as acceptance criteria
        6. If the requirement is a decision, include the decision and the criteria for making that decision
        7. If the requirement is a question, include the question and the criteria for answering it
        8. Add any related or dependent concepts
        9. EACH AND EVERY STEP to implement the requirement must be included
        10. For each requirement, specify exactly what components are needed:
            - frontend: UI components, pages, forms, validation, user interactions
            - backend: API endpoints, services, data processing, business logic
            - middleware: authentication, authorization, request/response processing
            - shared: data models, utilities, constants, interfaces
        Assume sub-processes exist even if not stated. Propose granular steps. Imagine you are the user of the system and you are trying to implement the requirement. Think about the user's problem and how to solve it.
        

Return ONLY valid JSON in this exact format:
{
  "implementation_details": [
    {
      "function_id": "ServiceName.functionName",
      "description": "specific requirement description",
      "related_concepts": ["concept1", "concept2"],
      "acceptance_criteria": ["specific criterion 1", "specific criterion 2"],
      "implementation": {
        "frontend": ["UI components needed"],
        "backend": ["API endpoints needed"],
        "middleware": ["authentication requirements"],
        "shared": ["data models needed"]
      }
    }
  ]
}

Generate one implementation_detail for each sub-process. If no sub-processes provided, generate 2-3 implementation details based on the parent requirement.
`, researchContent, parentDescription, string(subProcessJSON))
}

// extractJSON extracts JSON object from text (first { to last }).
func extractJSON(text string) string {
	start := strings.Index(text, "{")
	end := strings.LastIndex(text, "}")
	if start != -1 && end != -1 && end > start {
		return text[start : end+1]
	}
	return ""
}

// truncateString truncates a string to maxLen characters.
func truncateString(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen]
}

// DecomposeRequirementsCLIFallback provides a fallback using Claude CLI.
func DecomposeRequirementsCLIFallback(
	researchContent string,
	projectPath string,
	config *DecompositionConfig,
) (*RequirementHierarchy, *DecompositionError) {
	if config == nil {
		config = DefaultDecompositionConfig()
	}

	// Validate input
	if strings.TrimSpace(researchContent) == "" {
		return nil, NewDecompositionError(
			ErrEmptyContent,
			"Research content cannot be empty",
			nil,
		)
	}

	prompt := fmt.Sprintf(`Analyze this research content and extract requirements.

Return ONLY valid JSON with this structure:
{
    "requirements": [
        {
            "description": "Requirement description",
            "sub_processes": ["subprocess 1", "subprocess 2"]
        }
    ]
}

Research content:
%s
`, researchContent)

	result := RunClaudeSync(prompt, 60, true, projectPath)
	if !result.Success {
		return nil, NewDecompositionError(
			ErrCLIFallbackError,
			fmt.Sprintf("Claude CLI failed: %s", result.Error),
			nil,
		)
	}

	// Extract and parse JSON
	jsonStr := extractJSON(result.Output)
	if jsonStr == "" {
		return nil, NewDecompositionError(
			ErrInvalidJSON,
			"No valid JSON found in CLI output",
			map[string]interface{}{"output_preview": truncateString(result.Output, 200)},
		)
	}

	var data struct {
		Requirements []struct {
			Description  string   `json:"description"`
			SubProcesses []string `json:"sub_processes"`
		} `json:"requirements"`
	}

	if err := json.Unmarshal([]byte(jsonStr), &data); err != nil {
		return nil, NewDecompositionError(
			ErrInvalidJSON,
			fmt.Sprintf("Invalid JSON: %v", err),
			nil,
		)
	}

	// Convert to hierarchy
	hierarchy := NewRequirementHierarchy()
	hierarchy.Metadata["source"] = "cli_fallback"

	for reqIdx, req := range data.Requirements {
		parentID := fmt.Sprintf("REQ_%03d", reqIdx)
		parentNode := &RequirementNode{
			ID:          parentID,
			Description: req.Description,
			Type:        "parent",
		}

		subProcesses := req.SubProcesses
		if len(subProcesses) > config.MaxSubProcesses {
			subProcesses = subProcesses[:config.MaxSubProcesses]
		}

		for subIdx, subProc := range subProcesses {
			childID := fmt.Sprintf("%s.%d", parentID, subIdx+1)
			childNode := &RequirementNode{
				ID:          childID,
				Description: subProc,
				Type:        "sub_process",
				ParentID:    parentID,
			}
			parentNode.Children = append(parentNode.Children, childNode)
		}

		hierarchy.AddRequirement(parentNode)
	}

	return hierarchy, nil
}
