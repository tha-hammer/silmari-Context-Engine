package cli

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/spf13/cobra"
	"github.com/silmari/context-engine/go/internal/planning"
)

// Orchestrator flags
var (
	projectPath string
	newPath     string
	model       string
	maxSessions int
	cont        bool // --continue flag (cont because continue is a keyword)
	status      bool
	mcpPreset   string
	withQA      bool
	interactive bool
)

// Model choices for validation
var validModels = []string{"sonnet", "opus"}

// MCP preset choices for validation
var validMCPPresets = []string{"web", "fullstack", "data", "devops", "minimal", "rust", "python", "node", "docs"}

func init() {
	// Orchestrator-specific flags on root command
	rootCmd.Flags().StringVarP(&projectPath, "project", "p", "", "Project path to continue")
	rootCmd.Flags().StringVar(&newPath, "new", "", "Create new project at path")
	rootCmd.Flags().StringVarP(&model, "model", "m", "sonnet", "Model to use (sonnet/opus)")
	rootCmd.Flags().IntVar(&maxSessions, "max-sessions", 100, "Max sessions (default: 100)")
	rootCmd.Flags().BoolVarP(&cont, "continue", "c", false, "Continue existing project")
	rootCmd.Flags().BoolVarP(&status, "status", "s", false, "Show project status and exit")
	rootCmd.Flags().StringVar(&mcpPreset, "mcp-preset", "", "Use MCP preset (web/fullstack/data/devops/minimal/rust/python/node/docs)")
	rootCmd.Flags().BoolVar(&withQA, "with-qa", false, "Generate E2E QA features using Playwright")
	rootCmd.Flags().BoolVarP(&interactive, "interactive", "i", true, "Run sessions interactively (default)")

	// Mark mutually exclusive flags
	rootCmd.MarkFlagsMutuallyExclusive("project", "new")
}

// runOrchestrator is the main orchestrator command handler
func runOrchestrator(cmd *cobra.Command, args []string) error {
	// Validate model choice
	if err := validateChoice(model, validModels, "model"); err != nil {
		return err
	}

	// Validate MCP preset if provided
	if mcpPreset != "" {
		if err := validateChoice(mcpPreset, validMCPPresets, "mcp-preset"); err != nil {
			return err
		}
	}

	// Validate project path if provided
	if projectPath != "" {
		absPath, err := filepath.Abs(projectPath)
		if err != nil {
			return fmt.Errorf("invalid project path: %w", err)
		}
		if _, err := os.Stat(absPath); os.IsNotExist(err) {
			return fmt.Errorf("path does not exist: %s", projectPath)
		}
		projectPath = absPath
	}

	// Validate new path doesn't already exist
	if newPath != "" {
		absPath, err := filepath.Abs(newPath)
		if err != nil {
			return fmt.Errorf("invalid new project path: %w", err)
		}
		if _, err := os.Stat(absPath); err == nil {
			return fmt.Errorf("path already exists: %s", newPath)
		}
		newPath = absPath
	}

	// Show status and exit if requested
	if status {
		return showStatus()
	}

	if debug {
		fmt.Println("[DEBUG] Orchestrator configuration:")
		fmt.Printf("  Project: %s\n", projectPath)
		fmt.Printf("  New: %s\n", newPath)
		fmt.Printf("  Model: %s\n", model)
		fmt.Printf("  Max Sessions: %d\n", maxSessions)
		fmt.Printf("  Continue: %v\n", cont)
		fmt.Printf("  MCP Preset: %s\n", mcpPreset)
		fmt.Printf("  With QA: %v\n", withQA)
		fmt.Printf("  Interactive: %v\n", interactive)
	}

	// Handle --continue flag
	if cont {
		if projectPath == "" {
			projectPath, _ = os.Getwd()
		}
		return handleContinue(projectPath)
	}

	// TODO: Implement actual orchestrator logic
	fmt.Println("Context-Engineered Agent Orchestrator")
	fmt.Println("=====================================")
	if projectPath != "" {
		fmt.Printf("Project: %s\n", projectPath)
	} else if newPath != "" {
		fmt.Printf("Creating new project: %s\n", newPath)
	} else {
		fmt.Println("Running in interactive mode...")
	}

	return nil
}

// showStatus displays project status and exits
func showStatus() error {
	if projectPath == "" {
		return fmt.Errorf("--status requires --project to be specified")
	}

	fmt.Printf("Status for project: %s\n", projectPath)
	// TODO: Implement actual status display
	return nil
}

// validateChoice validates that a value is one of the valid choices
func validateChoice(value string, choices []string, flagName string) error {
	for _, choice := range choices {
		if value == choice {
			return nil
		}
	}
	return fmt.Errorf("invalid value for --%s: must be one of %v", flagName, choices)
}

// validatePath validates that a path exists
func validatePath(path string, flagName string) error {
	if path == "" {
		return nil
	}
	absPath, err := filepath.Abs(path)
	if err != nil {
		return fmt.Errorf("invalid path for --%s: %w", flagName, err)
	}
	if _, err := os.Stat(absPath); os.IsNotExist(err) {
		return fmt.Errorf("path does not exist: %s", path)
	}
	return nil
}

// validatePathNotExists validates that a path does NOT exist (for new projects)
func validatePathNotExists(path string, flagName string) error {
	if path == "" {
		return nil
	}
	absPath, err := filepath.Abs(path)
	if err != nil {
		return fmt.Errorf("invalid path for --%s: %w", flagName, err)
	}
	if _, err := os.Stat(absPath); err == nil {
		return fmt.Errorf("path already exists: %s", path)
	}
	return nil
}

// validateInteger validates integer flags (already handled by cobra, but for custom ranges)
func validateInteger(value int, min, max int, flagName string) error {
	if value < min || value > max {
		return fmt.Errorf("invalid integer value for --%s: must be between %d and %d", flagName, min, max)
	}
	return nil
}

// handleContinue handles the --continue flag by detecting and resuming from checkpoints.
func handleContinue(projectPath string) error {
	fmt.Println("\nAttempting to resume from checkpoint...")
	fmt.Println(strings.Repeat("=", 60))

	// Create checkpoint manager
	checkpointMgr := planning.NewCheckpointManager(projectPath)

	// Detect most recent checkpoint
	checkpoint, err := checkpointMgr.DetectResumableCheckpoint()
	if err != nil {
		return fmt.Errorf("failed to detect checkpoint: %w", err)
	}

	if checkpoint == nil {
		fmt.Println("\n❌ No checkpoint found. Cannot continue.")
		fmt.Println("\nTo resume a failed pipeline:")
		fmt.Println("  1. Ensure the pipeline failed and created a checkpoint")
		fmt.Println("  2. Run: context-engine orchestrator --continue")
		fmt.Println("\nCheckpoints are stored in: .rlm-act-checkpoints/")
		return fmt.Errorf("no checkpoint found")
	}

	// Display checkpoint information
	fmt.Printf("\n✓ Found checkpoint from %s\n", checkpoint.Timestamp[:19])
	fmt.Printf("  Phase: %s\n", checkpoint.Phase)
	fmt.Printf("  Checkpoint ID: %s\n", checkpoint.ID)

	if len(checkpoint.Errors) > 0 {
		fmt.Printf("  Errors: %d error(s) recorded\n", len(checkpoint.Errors))
	}

	// Extract artifacts from state
	var researchPath, planPath string

	// Try to extract from phase_results (RLM-Act format)
	if phaseResults, ok := checkpoint.State["phase_results"].(map[string]interface{}); ok {
		// Extract research path from research phase
		if researchPhase, ok := phaseResults["research"].(map[string]interface{}); ok {
			if artifacts, ok := researchPhase["artifacts"].([]interface{}); ok && len(artifacts) > 0 {
				if path, ok := artifacts[0].(string); ok {
					researchPath = path
					fmt.Printf("  Research: %s\n", filepath.Base(path))
				}
			}
		}

		// Extract plan path from planning phase
		if planningPhase, ok := phaseResults["planning"].(map[string]interface{}); ok {
			if artifacts, ok := planningPhase["artifacts"].([]interface{}); ok && len(artifacts) > 0 {
				if path, ok := artifacts[0].(string); ok {
					planPath = path
					fmt.Printf("  Plan: %s\n", filepath.Base(path))
				}
			}
		}
	}

	// Fallback: Try to extract from artifacts array (planning_orchestrator format)
	if researchPath == "" || planPath == "" {
		if artifacts, ok := checkpoint.State["artifacts"].([]interface{}); ok {
			for _, artifact := range artifacts {
				if artifactStr, ok := artifact.(string); ok {
					// Determine if it's a research or plan file
					if filepath.Base(filepath.Dir(artifactStr)) == "research" {
						researchPath = artifactStr
						fmt.Printf("  Research: %s\n", filepath.Base(artifactStr))
					} else if filepath.Base(filepath.Dir(artifactStr)) == "plans" {
						planPath = artifactStr
						fmt.Printf("  Plan: %s\n", filepath.Base(artifactStr))
					}
				}
			}
		}
	}

	// Determine resume phase based on checkpoint phase
	var resumePhase string
	phaseLower := strings.ToLower(checkpoint.Phase)

	// Handle RLM-Act phase names (e.g., "beads_sync-complete")
	if strings.Contains(phaseLower, "research") && strings.Contains(phaseLower, "complete") {
		// Research complete - resume from planning
		resumePhase = "planning"
	} else if strings.Contains(phaseLower, "multi_doc") || strings.Contains(phaseLower, "planning") {
		// Planning phase - resume from planning
		resumePhase = "planning"
	} else if strings.Contains(phaseLower, "decomposition") {
		// Decomposition phase - resume from decomposition
		resumePhase = "decomposition"
	} else if strings.Contains(phaseLower, "beads") {
		// Beads sync complete - all phases done, nothing to resume
		fmt.Println("\n✓ All pipeline phases complete (beads sync done)")
		fmt.Println("  No resume needed - pipeline already finished")
		return nil
	} else if strings.Contains(phaseLower, "implementation") {
		resumePhase = "implementation"
	} else if strings.Contains(phaseLower, "research") {
		// Research in progress or failed - resume from research
		resumePhase = "research"
	} else {
		// Default: Try to determine from available artifacts
		if planPath != "" {
			resumePhase = "decomposition"
		} else if researchPath != "" {
			resumePhase = "planning"
		} else {
			fmt.Println("\n❌ Cannot determine resume phase from checkpoint")
			fmt.Printf("  Checkpoint phase: %s\n", checkpoint.Phase)
			fmt.Println("  No artifacts found in checkpoint state")
			return fmt.Errorf("cannot determine resume phase")
		}
	}

	fmt.Printf("\n→ Resuming from: %s phase\n", resumePhase)
	fmt.Println(strings.Repeat("=", 60))

	// Create pipeline config
	config := planning.PipelineConfig{
		ProjectPath:  projectPath,
		AutoApprove:  false, // Default to checkpoint mode
		ResearchPath: researchPath,
		AutonomyMode: planning.AutonomyCheckpoint,
	}

	// Create pipeline
	pipeline := planning.NewPlanningPipeline(config)

	// Resume from checkpoint
	results := pipeline.ResumeFromCheckpoint(checkpoint, resumePhase, planPath)

	// Display results
	fmt.Println("\n" + strings.Repeat("=", 60))
	if results.Success {
		fmt.Println("✅ Pipeline resumed and completed successfully")
		fmt.Printf("  Epic ID: %s\n", results.EpicID)
		if results.PlanDir != "" {
			fmt.Printf("  Plan directory: %s\n", results.PlanDir)
		}

		// Cleanup checkpoint on success
		checkpointPath := filepath.Join(projectPath, ".rlm-act-checkpoints", checkpoint.ID+".json")
		if err := os.Remove(checkpointPath); err == nil {
			fmt.Println("\n✓ Checkpoint cleaned up")
		}
	} else {
		fmt.Println("❌ Pipeline failed")
		fmt.Printf("  Failed at: %s\n", results.FailedAt)
		if results.Error != "" {
			fmt.Printf("  Error: %s\n", results.Error)
		}
		fmt.Println("\n💡 Run 'context-engine orchestrator --continue' to retry")
	}
	fmt.Println(strings.Repeat("=", 60))

	if !results.Success {
		return fmt.Errorf("pipeline failed at %s", results.FailedAt)
	}

	return nil
}
