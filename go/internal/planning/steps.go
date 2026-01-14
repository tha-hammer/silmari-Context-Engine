package planning

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// StepResult represents the result of a pipeline step.
type StepResult struct {
	Success       bool                   `json:"success"`
	Error         string                 `json:"error,omitempty"`
	Output        string                 `json:"output,omitempty"`
	ResearchPath  string                 `json:"research_path,omitempty"`
	PlanPath      string                 `json:"plan_path,omitempty"`  // Single plan path (first found, for backward compatibility)
	PlanPaths     []string               `json:"plan_paths,omitempty"` // All plan paths when multiple files are created
	PhaseFiles    []string               `json:"phase_files,omitempty"`
	OpenQuestions []string               `json:"open_questions,omitempty"`
	Data          map[string]interface{} `json:"data,omitempty"`
}

// NewStepResult creates a new successful StepResult.
func NewStepResult() *StepResult {
	return &StepResult{
		Success: true,
		Data:    make(map[string]interface{}),
	}
}

// SetError marks the result as failed with an error message.
func (r *StepResult) SetError(err error) {
	r.Success = false
	if err != nil {
		r.Error = err.Error()
	}
}

// StepResearch executes the research phase of the pipeline.
func StepResearch(projectPath, researchPrompt string) *StepResult {
	result := NewStepResult()
	dateStr := time.Now().Format("2006-01-02")

	// Load research instructions from markdown file
	instructionsPath := filepath.Join(projectPath, ".claude", "commands", "research_codebase.md")
	instructionsBytes, err := os.ReadFile(instructionsPath)
	if err != nil {
		result.SetError(fmt.Errorf("failed to read research instructions: %w", err))
		return result
	}

	instructions := string(instructionsBytes)

	// Process instructions: insert research question after "# Research Codebase"
	lines := strings.Split(instructions, "\n")
	var processedLines []string
	insertIdx := 1

	for i, line := range lines {
		if strings.TrimSpace(line) == "# Research Codebase" {
			insertIdx = i + 1
			break
		}
	}

	// Insert research question section
	processedLines = append(processedLines, lines[:insertIdx]...)
	processedLines = append(processedLines, "")
	processedLines = append(processedLines, "## Research Question")
	processedLines = append(processedLines, researchPrompt)
	processedLines = append(processedLines, "")
	processedLines = append(processedLines, lines[insertIdx:]...)

	// Remove "Initial Setup" section
	var finalLines []string
	skipSection := false
	for _, line := range processedLines {
		if strings.Contains(line, "## Initial Setup:") {
			skipSection = true
			continue
		}
		if skipSection && strings.Contains(line, "Then wait for the user's research query.") {
			skipSection = false
			continue
		}
		if !skipSection {
			finalLines = append(finalLines, line)
		}
	}

	// Replace date placeholder
	instructions = strings.Join(finalLines, "\n")
	instructions = strings.Replace(instructions,
		"Filename: `thoughts/searchable/shared/research/YYYY-MM-DD-description.md`",
		fmt.Sprintf("Filename: `thoughts/searchable/shared/research/%s-pipeline-research.md`", dateStr),
		1,
	)

	prompt := instructions + "\n\nAfter creating the document, output the path.\n"

	// Run Claude
	claudeResult := RunClaudeSync(prompt, 1200, true, projectPath)
	if !claudeResult.Success {
		result.SetError(fmt.Errorf("research failed: %s", claudeResult.Error))
		return result
	}

	result.Output = claudeResult.Output
	result.ResearchPath = ExtractFilePath(claudeResult.Output, "research")
	result.OpenQuestions = ExtractOpenQuestions(claudeResult.Output)

	if result.ResearchPath == "" {
		result.SetError(fmt.Errorf("research completed but no research file path found in output"))
		return result
	}

	return result
}

// StepPlanning executes the planning phase of the pipeline.
func StepPlanning(projectPath, researchPath, additionalContext string) *StepResult {
	result := NewStepResult()
	dateStr := time.Now().Format("2006-01-02")

	// Load planning instructions
	instructionsPath := filepath.Join(projectPath, ".claude", "commands", "create_tdd_plan.md")
	instructionsBytes, err := os.ReadFile(instructionsPath)
	if err != nil {
		result.SetError(fmt.Errorf("failed to read planning instructions: %w", err))
		return result
	}

	instructions := string(instructionsBytes)

	// Process instructions: insert research document reference
	lines := strings.Split(instructions, "\n")
	var processedLines []string
	insertIdx := 1

	for i, line := range lines {
		if strings.TrimSpace(line) == "# TDD Implementation Plan" {
			insertIdx = i + 1
			break
		}
	}

	// Insert research document and context sections
	processedLines = append(processedLines, lines[:insertIdx]...)
	processedLines = append(processedLines, "")
	processedLines = append(processedLines, "## Research Document")
	processedLines = append(processedLines, fmt.Sprintf("Read the research at: %s", researchPath))
	processedLines = append(processedLines, "")

	if additionalContext != "" {
		processedLines = append(processedLines, "## Additional Context")
		processedLines = append(processedLines, additionalContext)
		processedLines = append(processedLines, "")
	}

	processedLines = append(processedLines, lines[insertIdx:]...)

	// Remove "Initial Response" section
	var finalLines []string
	skipSection := false
	for _, line := range processedLines {
		if strings.Contains(line, "## Initial Response") {
			skipSection = true
			continue
		}
		if skipSection && strings.Contains(line, "## Process Steps") {
			skipSection = false
		}
		if !skipSection {
			finalLines = append(finalLines, line)
		}
	}

	// Replace date placeholders
	instructions = strings.Join(finalLines, "\n")
	instructions = strings.Replace(instructions,
		"`thoughts/searchable/plans/YYYY-MM-DD-tdd-description.md`",
		fmt.Sprintf("`thoughts/searchable/plans/%s-plan.md`", dateStr),
		1,
	)

	prompt := instructions + "\n\nOutput the plan file path when complete.\n"

	// Retry loop with question detection (max 3 attempts)
	maxRetries := 3
	fmt.Printf("\n[DEBUG] Starting planning retry loop (max %d attempts)\n", maxRetries)
	for attempt := 0; attempt < maxRetries; attempt++ {
		fmt.Printf("[DEBUG] Planning attempt %d/%d\n", attempt+1, maxRetries)
		// Run Claude
		claudeResult := RunClaudeSync(prompt, 1200, true, projectPath)
		if !claudeResult.Success {
			result.SetError(fmt.Errorf("planning failed: %s", claudeResult.Error))
			return result
		}

		result.Output = claudeResult.Output
		result.PlanPaths = ExtractAllFilePaths(claudeResult.Output, "plan")
		if len(result.PlanPaths) > 0 {
			result.PlanPath = result.PlanPaths[0] // First path for backward compatibility
		}

		fmt.Printf("[DEBUG] Extracted plan paths: %v\n", result.PlanPaths)

		// Success - plan file(s) found
		if len(result.PlanPaths) > 0 {
			fmt.Printf("[DEBUG] Found %d plan file(s), returning success\n", len(result.PlanPaths))
			return result
		}

		// Check if output contains questions and we have retries left
		hasQuestion := isQuestion(claudeResult.Output)
		fmt.Printf("[DEBUG] Question detected: %v, Retries left: %v\n", hasQuestion, attempt < maxRetries-1)

		if hasQuestion && attempt < maxRetries-1 {
			fmt.Println("\n" + strings.Repeat("=", 60))
			fmt.Println("CLAUDE NEEDS CLARIFICATION")
			fmt.Println(strings.Repeat("=", 60))
			fmt.Println("\nClaude's response did not produce a plan file.")
			fmt.Println("Please provide additional context or answers:")

			// Collect user input
			fmt.Print("> ")
			userResponse := collectMultilineInput()

			fmt.Printf("[DEBUG] User response length: %d\n", len(userResponse))

			if userResponse != "" {
				// Augment prompt with user clarification and retry
				prompt = fmt.Sprintf(`%s

## User Clarification (Attempt %d)
%s

Now create the plan file. Output the plan file path when complete.
`, prompt, attempt+2, userResponse)
				fmt.Print("\nSending additional context to Claude...")
				continue
			}
			fmt.Println("[DEBUG] No user response provided, continuing loop")
		}

		// No question detected or no user input - fail after last attempt
		if attempt == maxRetries-1 {
			fmt.Println("[DEBUG] Last attempt reached, failing")
			result.SetError(fmt.Errorf("failed to generate plan after %d attempts", maxRetries))
			return result
		}
		fmt.Printf("[DEBUG] Continuing to next attempt (attempt %d < maxRetries-1 %d)\n", attempt, maxRetries-1)
	}

	// Should not reach here, but just in case
	result.SetError(fmt.Errorf("failed to generate plan"))
	return result
}

// StepPhaseDecomposition decomposes a plan into separate phase files.
// planPath can be a single path (backward compatible) or the first of multiple paths.
// Use StepPhaseDecompositionMulti for explicit multi-plan support.
func StepPhaseDecomposition(projectPath, planPath string) *StepResult {
	return StepPhaseDecompositionMulti(projectPath, []string{planPath})
}

// StepPhaseDecompositionMulti decomposes multiple plan files into separate phase files.
func StepPhaseDecompositionMulti(projectPath string, planPaths []string) *StepResult {
	result := NewStepResult()

	// Filter out empty paths
	var validPaths []string
	for _, p := range planPaths {
		if p != "" {
			validPaths = append(validPaths, p)
		}
	}

	if len(validPaths) == 0 {
		result.SetError(fmt.Errorf("plan_paths is required but was empty"))
		return result
	}

	// Use the directory of the first plan file for output
	planDir := filepath.Dir(validPaths[0])

	// Build the plan files section of the prompt
	var planFilesSection string
	if len(validPaths) == 1 {
		planFilesSection = fmt.Sprintf("Read the plan file at: %s", validPaths[0])
	} else {
		planFilesSection = "Read all the following plan files:\n"
		for i, path := range validPaths {
			planFilesSection += fmt.Sprintf("%d. %s\n", i+1, path)
		}
		planFilesSection += "\nCombine the phases from ALL plan files into a unified set of phase files."
	}

	prompt := fmt.Sprintf(`# Phase Decomposition Task

%s

## Instructions
Create distinct phase files based on the plan(s). Each phase should end with 1 human-testable function.

## Output Structure
Create files at: %s/YYYY-MM-DD-tdd-description/
Append YYYY-MM-DD-tdd-description to the filename of each file.
- YYYY-MM-DD-tdd-description-00-overview.md (links to all phases)
- YYYY-MM-DD-tdd-description-01-phase-1.md
- YYYY-MM-DD-tdd-description-02-phase-2.md
- etc.

## Phase File Template
Each phase file must contain:
- Overview
- Dependencies (requires/blocks)
- Changes Required with file:line
- Success Criteria

After creating all files, list the created file paths.
`, planFilesSection, planDir)

	claudeResult := RunClaudeSync(prompt, 1200, true, projectPath)
	if !claudeResult.Success {
		result.SetError(fmt.Errorf("phase decomposition failed: %s", claudeResult.Error))
		return result
	}

	result.Output = claudeResult.Output
	result.PhaseFiles = ExtractPhaseFiles(claudeResult.Output)

	return result
}

// StepMemorySync syncs 4-layer memory and clears Claude context between phases.
func StepMemorySync(projectPath, researchPath, sessionID string) *StepResult {
	result := NewStepResult()
	result.Data["episode_recorded"] = false
	result.Data["context_compiled"] = false
	result.Data["context_cleared"] = false

	// Read research summary for episodic memory
	summary := fmt.Sprintf("Research session %s", sessionID)
	researchFile := researchPath
	if !filepath.IsAbs(researchPath) {
		researchFile = filepath.Join(projectPath, researchPath)
	}

	if content, err := os.ReadFile(researchFile); err == nil {
		lines := strings.Split(string(content), "\n")
		var summaryLines []string
		inContent := false
		for _, line := range lines {
			if strings.HasPrefix(line, "# ") {
				inContent = true
				continue
			}
			if inContent && strings.TrimSpace(line) != "" {
				summaryLines = append(summaryLines, strings.TrimSpace(line))
				if len(summaryLines) >= 3 {
					break
				}
			}
		}
		if len(summaryLines) > 0 {
			summary = strings.Join(summaryLines, " ")
			if len(summary) > 500 {
				summary = summary[:500]
			}
		}
	}

	// 1. Record episodic memory
	cmd := exec.Command("silmari-oracle", "memory", "episode", sessionID, summary)
	cmd.Dir = projectPath
	if err := cmd.Run(); err == nil {
		result.Data["episode_recorded"] = true
	}

	// 2. Compile working context
	cmd = exec.Command("silmari-oracle", "memory", "compile")
	cmd.Dir = projectPath
	if err := cmd.Run(); err == nil {
		result.Data["context_compiled"] = true
	}

	// 3. Clear Claude context
	cmd = exec.Command("claude", "--print", "-p", "/clear")
	if err := cmd.Run(); err == nil {
		result.Data["context_cleared"] = true
	}

	// Memory sync is best-effort, don't fail pipeline
	return result
}

// BeadsIntegrationResult contains results from beads integration step.
type BeadsIntegrationResult struct {
	Success        bool
	Error          string
	EpicID         string
	PhaseIssues    []PhaseIssue
	FilesAnnotated []string
}

// PhaseIssue represents a phase issue created in beads.
type PhaseIssue struct {
	Phase   int
	File    string
	IssueID string
}

// ensureBeadsDatabase checks for .beads directory and initializes if needed.
// Returns the path to the .beads directory or an error.
func ensureBeadsDatabase(projectPath string) (string, error) {
	beadsDir := filepath.Join(projectPath, ".beads")

	// Check if .beads directory exists
	if info, err := os.Stat(beadsDir); err == nil && info.IsDir() {
		// Verify db.sqlite exists
		dbPath := filepath.Join(beadsDir, "db.sqlite")
		if _, err := os.Stat(dbPath); err == nil {
			return beadsDir, nil
		}
	}

	// .beads not found or incomplete - initialize it
	fmt.Println("\n⚠️  No beads database found. Initializing...")
	fmt.Printf("Running: bd init in %s\n\n", projectPath)

	cmd := exec.Command("bd", "init")
	cmd.Dir = projectPath
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return "", fmt.Errorf("failed to initialize beads: %w", err)
	}

	// Run bd doctor --fix with automatic "Y" response
	fmt.Println("\n🔧 Running bd doctor --fix...")
	cmd = exec.Command("bd", "doctor", "--fix")
	cmd.Dir = projectPath
	cmd.Env = append(os.Environ(), fmt.Sprintf("BEADS_DIR=%s", beadsDir))

	// Create a pipe to send "Y" to stdin
	stdin, err := cmd.StdinPipe()
	if err != nil {
		return "", fmt.Errorf("failed to create stdin pipe: %w", err)
	}

	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Start(); err != nil {
		return "", fmt.Errorf("failed to start bd doctor: %w", err)
	}

	// Send "Y" to confirm fixes
	if _, err := stdin.Write([]byte("Y\n")); err != nil {
		fmt.Fprintf(os.Stderr, "Warning: failed to send Y to bd doctor: %v\n", err)
	}
	stdin.Close()

	if err := cmd.Wait(); err != nil {
		// bd doctor may exit non-zero even on success, so just log warning
		fmt.Fprintf(os.Stderr, "Warning: bd doctor exited with: %v\n", err)
	}

	// Run bd ready to show available work
	fmt.Println("\n📋 Checking for ready work...")
	cmd = exec.Command("bd", "ready")
	cmd.Dir = projectPath
	cmd.Env = append(os.Environ(), fmt.Sprintf("BEADS_DIR=%s", beadsDir))
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Run() // Ignore error, this is informational

	fmt.Println("\n✓ Beads database initialized successfully")
	return beadsDir, nil
}

// StepBeadsIntegration creates beads issues for plan phases.
func StepBeadsIntegration(projectPath string, phaseFiles []string, epicTitle string) *BeadsIntegrationResult {
	result := &BeadsIntegrationResult{Success: true}

	// Ensure beads database exists
	beadsDir, err := ensureBeadsDatabase(projectPath)
	if err != nil {
		result.Success = false
		result.Error = fmt.Sprintf("failed to ensure beads database: %v", err)
		return result
	}

	// Create epic with BEADS_DIR set
	cmd := exec.Command("bd", "create", "--title", epicTitle, "--type", "epic")
	cmd.Dir = projectPath
	cmd.Env = append(os.Environ(), fmt.Sprintf("BEADS_DIR=%s", beadsDir))
	output, err := cmd.CombinedOutput()
	if err != nil {
		result.Success = false
		result.Error = fmt.Sprintf("failed to create epic: %v\nOutput: %s", err, string(output))
		return result
	}

	// Parse epic ID from output (format: "Created beads-xxxx")
	epicID := extractBeadsID(string(output))
	result.EpicID = epicID

	// Separate overview from phase files
	var overviewFile string
	var actualPhaseFiles []string
	for _, f := range phaseFiles {
		lower := strings.ToLower(f)
		if strings.Contains(lower, "overview") || strings.HasSuffix(f, "00-overview.md") {
			overviewFile = f
		} else {
			actualPhaseFiles = append(actualPhaseFiles, f)
		}
	}

	// Create issues for each phase
	var prevIssueID string
	for i, phaseFile := range actualPhaseFiles {
		phaseName := extractPhaseName(phaseFile)
		title := fmt.Sprintf("Phase %d: %s", i+1, phaseName)

		cmd := exec.Command("bd", "create", "--title", title, "--type", "task", "--priority", "2")
		cmd.Dir = projectPath
		cmd.Env = append(os.Environ(), fmt.Sprintf("BEADS_DIR=%s", beadsDir))
		output, err := cmd.CombinedOutput()

		var issueID string
		if err == nil {
			issueID = extractBeadsID(string(output))
		} else {
			// Log the error but continue with other phases
			fmt.Fprintf(os.Stderr, "Warning: failed to create phase issue: %v\nOutput: %s\n", err, string(output))
		}

		result.PhaseIssues = append(result.PhaseIssues, PhaseIssue{
			Phase:   i + 1,
			File:    phaseFile,
			IssueID: issueID,
		})

		// Link dependency to previous phase
		if prevIssueID != "" && issueID != "" {
			cmd = exec.Command("bd", "dep", "add", issueID, prevIssueID)
			cmd.Dir = projectPath
			cmd.Env = append(os.Environ(), fmt.Sprintf("BEADS_DIR=%s", beadsDir))
			cmd.Run()
		}
		prevIssueID = issueID
	}

	// Sync beads
	cmd = exec.Command("bd", "sync")
	cmd.Dir = projectPath
	cmd.Env = append(os.Environ(), fmt.Sprintf("BEADS_DIR=%s", beadsDir))
	cmd.Run()

	// Annotate files with bd commands using Claude
	if overviewFile != "" {
		if annotateOverviewFile(projectPath, overviewFile, epicID, result.PhaseIssues) {
			result.FilesAnnotated = append(result.FilesAnnotated, overviewFile)
		}
	}

	for _, pi := range result.PhaseIssues {
		if annotatePhaseFile(projectPath, pi.File, pi.IssueID, pi.Phase) {
			result.FilesAnnotated = append(result.FilesAnnotated, pi.File)
		}
	}

	return result
}

// extractBeadsID extracts beads issue ID from bd create output.
func extractBeadsID(output string) string {
	// Look for pattern "beads-xxxx" or "Created beads-xxxx"
	lines := strings.Split(output, "\n")
	for _, line := range lines {
		if idx := strings.Index(line, "beads-"); idx != -1 {
			end := idx + 6 // "beads-" length
			for end < len(line) && (line[end] >= 'a' && line[end] <= 'z' || line[end] >= '0' && line[end] <= '9') {
				end++
			}
			return line[idx:end]
		}
	}
	return ""
}

// extractPhaseName extracts phase name from filename.
func extractPhaseName(filename string) string {
	base := filepath.Base(filename)
	base = strings.TrimSuffix(base, filepath.Ext(base))

	// Split on "-" and take everything after the phase number
	parts := strings.SplitN(base, "-", 3)
	if len(parts) >= 3 {
		return strings.Title(strings.ReplaceAll(parts[2], "-", " "))
	}
	return base
}

// annotateOverviewFile adds beads tracking info to overview file.
func annotateOverviewFile(projectPath, overviewFile, epicID string, phases []PhaseIssue) bool {
	filePath := overviewFile
	if !filepath.IsAbs(overviewFile) {
		filePath = filepath.Join(projectPath, overviewFile)
	}

	content, err := os.ReadFile(filePath)
	if err != nil {
		return false
	}

	// Build phase list for prompt
	var phaseList strings.Builder
	for _, p := range phases {
		basename := filepath.Base(p.File)
		phaseList.WriteString(fmt.Sprintf("- Phase %d: %s -> Issue ID: %s\n", p.Phase, basename, p.IssueID))
	}

	prompt := fmt.Sprintf(`# Task: Add Beads Tracking Information to Plan Overview File

## Context: Understanding the Work Hierarchy

This overview file describes an entire project/feature. The work is organized in a 3-level hierarchy:

1. **Epic** (This overview) - The entire project/feature
   - Epic ID: %s
   - Contains multiple phases that must be completed sequentially

2. **Phases** (Individual phase files) - Sequential steps in the epic
   - Each phase has its own beads issue ID
   - Phase 2 depends on Phase 1, Phase 3 depends on Phase 2, etc.
   - Each phase contains multiple behaviors

3. **Behaviors** (Within phase files) - Testable units within a phase
   - NOT tracked individually in beads
   - All behaviors in a phase share that phase's issue ID
   - Example: "Behavior 1.1", "Behavior 1.2", etc.

## Your Task

Add comprehensive beads tracking information to the overview file so developers can:
1. See the epic issue ID
2. Find all phase issue IDs
3. Understand the sequential workflow

## File to Edit
Path: %s

## Current Content
%s

## Tracking Information

**Epic Issue ID**: %s

**Phase Issues** (%d phases total):
%s

## Instructions

Add a "Beads Tracking" section near the top of the file (after the main title/description).

The section should include:

1. **Epic Issue subsection**: Show the epic ID (%s) with bd commands:
   - bd show %s (to view the epic)
   - bd list --status=open (to view all issues)
   - bd ready (to see ready work)

2. **Phase Issues subsection**: List all %d phases with their issue IDs:
%s

3. **Workflow Commands subsection**: Include these command examples in a bash code block:
   - bd show <phase-issue-id> (review phase details)
   - bd update <phase-issue-id> --status=in_progress (start work)
   - bd close <phase-issue-id> (mark complete)
   - bd ready (see ready phases)
   - bd list --status=in_progress (see active work)
   - bd blocked (see blocked work)

4. **Important Note**: Clarify that all behaviors within a phase (e.g., Behavior 1.1, 1.2) are tracked under that phase's single issue ID.

### Important Guidelines

1. **Placement**: Add tracking section AFTER the main title and high-level description, but BEFORE detailed phase descriptions
2. **Preserve Content**: Do NOT modify existing content - only add the tracking section
3. **Use Actual IDs**: Use the actual issue IDs provided above in the tracking section
4. **Format Phase List**: In the "Phase Issues" subsection, list each phase with its issue ID in a clear, scannable format

Now edit the file at %s to add this comprehensive tracking section.
`, epicID, overviewFile, string(content), epicID, len(phases), phaseList.String(), epicID, epicID, len(phases), phaseList.String(), overviewFile)

	claudeResult := RunClaudeSync(prompt, 120, true, projectPath)
	return claudeResult.Success
}

// annotatePhaseFile adds beads tracking info to a phase file.
func annotatePhaseFile(projectPath, phaseFile, issueID string, phaseNum int) bool {
	filePath := phaseFile
	if !filepath.IsAbs(phaseFile) {
		filePath = filepath.Join(projectPath, phaseFile)
	}

	content, err := os.ReadFile(filePath)
	if err != nil {
		return false
	}

	prompt := fmt.Sprintf(`# Task: Add Beads Issue Tracking to Phase File

## Context: Understanding the Work Hierarchy

This project uses a 3-level hierarchy for tracking work:

1. **Epic** (Top level) - The entire project/feature being built
   - Tracked with a single beads issue ID (e.g., beads-abc1)
   - Contains multiple sequential phases

2. **Phase** (Middle level) - A sequential step in the epic
   - Each phase is tracked with its own beads issue ID (e.g., beads-xyz2)
   - Phases depend on previous phases (Phase 2 depends on Phase 1, etc.)
   - Each phase contains multiple behaviors

3. **Behavior** (Bottom level) - A testable unit within a phase
   - NOT tracked individually in beads (tracked as part of the phase)
   - Each behavior ends with 1 human-testable function
   - Example: "Behavior 7.1: Complete User Flow Works"

## Your Task

Add beads tracking information to a phase file so developers know how to track their work.

## File to Edit
Path: %s

## Current Content
%s

## This Phase's Tracking Information
- Phase Number: %d
- Phase Issue ID: %s
- All behaviors in this phase are tracked under issue: %s

## Instructions

Add a "Tracking" section at the top of the file (right after the phase title and metadata).

The tracking section should include:

1. **Phase Issue**: Display the issue ID (%s)

2. **Quick Commands**: List these bd commands:
   - View: bd show %s
   - Start work: bd update %s --status=in_progress
   - Complete phase: bd close %s

3. **Note**: Clarify that all behaviors in this phase (e.g., Behavior %d.1, %d.2, etc.) are tracked under this single phase issue.

### Important Guidelines

1. **Placement**: Add the tracking section AFTER the phase title and metadata (dependencies, effort) but BEFORE the "Overview" section
2. **Preserve Content**: Do NOT modify any existing content - only add the tracking section
3. **Reference Behaviors**: Make it clear that all behaviors in this phase share the same tracking issue

Now edit the file at %s to add this tracking section.
`, phaseFile, string(content), phaseNum, issueID, issueID, issueID, issueID, issueID, issueID, phaseNum, phaseNum, phaseFile)

	claudeResult := RunClaudeSync(prompt, 120, true, projectPath)
	return claudeResult.Success
}

// isQuestion checks if Claude's output contains question indicators.
func isQuestion(output string) bool {
	outputLower := strings.ToLower(output)
	questionIndicators := []string{
		"could you", "can you", "would you", "what is", "which",
		"clarify", "specify", "more information", "more details",
		"please provide", "i need to understand", "?",
	}
	for _, q := range questionIndicators {
		if strings.Contains(outputLower, q) {
			return true
		}
	}
	return false
}

// collectMultilineInput prompts the user for multi-line input.
// Returns the collected input as a single string, or empty string if no input.
func collectMultilineInput() string {
	fmt.Println("(Enter your response, blank line to finish)")
	var lines []string

	// Use bufio.Scanner for line-by-line reading
	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			break
		}
		lines = append(lines, line)
		fmt.Print("> ")
	}

	return strings.Join(lines, "\n")
}
