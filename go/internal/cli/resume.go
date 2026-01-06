package cli

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/spf13/cobra"
)

// Resume command flags
var (
	resumeResearchPrompt    string
	resumeResearchPath      string
	resumeAdditionalContext string
	resumePlanPath          string
	resumePhaseFiles        []string
	resumeEpicTitle         string
)

// Valid step names for resume
var validSteps = []string{"research", "planning", "decomposition", "beads"}

// resumeCmd represents the resume subcommand
var resumeCmd = &cobra.Command{
	Use:   "resume",
	Short: "Resume a pipeline from a specific step",
	Long: `Resume Planning Pipeline
========================
Resume a failed planning pipeline from a specific step.

Examples:
    context-engine resume planning --research-path /path/to/research.md
    context-engine resume decomposition --plan-path /path/to/plan.md
    context-engine resume beads --phase-files phase1.md,phase2.md --epic-title "My Epic"`,
}

// resumePlanningCmd resumes from planning step
var resumePlanningCmd = &cobra.Command{
	Use:     "planning",
	Aliases: []string{"plan"},
	Short:   "Resume from planning step",
	Long: `Resume from Planning Step
=========================
Resume the pipeline from the planning step.

Requires:
  --research-path: Path to the research document`,
	RunE: runResumePlanning,
}

// resumeDecompositionCmd resumes from decomposition step
var resumeDecompositionCmd = &cobra.Command{
	Use:     "decomposition",
	Aliases: []string{"decomp"},
	Short:   "Resume from decomposition step",
	Long: `Resume from Decomposition Step
==============================
Resume the pipeline from the decomposition step.

Requires:
  --plan-path: Path to the plan document`,
	RunE: runResumeDecomposition,
}

// resumeBeadsCmd resumes from beads integration step
var resumeBeadsCmd = &cobra.Command{
	Use:   "beads",
	Short: "Resume from beads integration step",
	Long: `Resume from Beads Integration Step
==================================
Resume the pipeline from the beads integration step.

Requires:
  --phase-files: List of phase file paths
  --epic-title: Title for the epic`,
	RunE: runResumeBeads,
}

func init() {
	// Add subcommands to resume
	resumeCmd.AddCommand(resumePlanningCmd)
	resumeCmd.AddCommand(resumeDecompositionCmd)
	resumeCmd.AddCommand(resumeBeadsCmd)

	// Resume planning flags
	resumePlanningCmd.Flags().StringVar(&resumeResearchPath, "research-path", "", "Path to research document (required)")
	resumePlanningCmd.Flags().StringVar(&resumeAdditionalContext, "additional-context", "", "Additional context for planning")
	resumePlanningCmd.MarkFlagRequired("research-path")

	// Resume decomposition flags
	resumeDecompositionCmd.Flags().StringVar(&resumePlanPath, "plan-path", "", "Path to plan document (required)")
	resumeDecompositionCmd.MarkFlagRequired("plan-path")

	// Resume beads flags
	resumeBeadsCmd.Flags().StringSliceVar(&resumePhaseFiles, "phase-files", nil, "List of phase file paths (required)")
	resumeBeadsCmd.Flags().StringVar(&resumeEpicTitle, "epic-title", "", "Title for the epic (required)")
	resumeBeadsCmd.MarkFlagRequired("phase-files")
	resumeBeadsCmd.MarkFlagRequired("epic-title")

	// Support underscored versions for backwards compatibility
	resumePlanningCmd.Flags().SetNormalizeFunc(normalizeUnderscoredFlags)
	resumeDecompositionCmd.Flags().SetNormalizeFunc(normalizeUnderscoredFlags)
	resumeBeadsCmd.Flags().SetNormalizeFunc(normalizeUnderscoredFlags)
}

// runResumePlanning handles the resume planning command
func runResumePlanning(cmd *cobra.Command, args []string) error {
	// Validate research path
	absPath, err := filepath.Abs(resumeResearchPath)
	if err != nil {
		return fmt.Errorf("invalid research path: %w", err)
	}
	if _, err := os.Stat(absPath); os.IsNotExist(err) {
		return fmt.Errorf("path does not exist: %s", resumeResearchPath)
	}

	if debug {
		fmt.Println("[DEBUG] Resume planning configuration:")
		fmt.Printf("  Research path: %s\n", absPath)
		fmt.Printf("  Additional context: %s\n", resumeAdditionalContext)
	}

	fmt.Println("Resuming from planning step...")
	fmt.Printf("Research document: %s\n", absPath)

	// TODO: Implement actual resume planning logic
	return nil
}

// runResumeDecomposition handles the resume decomposition command
func runResumeDecomposition(cmd *cobra.Command, args []string) error {
	// Validate plan path
	absPath, err := filepath.Abs(resumePlanPath)
	if err != nil {
		return fmt.Errorf("invalid plan path: %w", err)
	}
	if _, err := os.Stat(absPath); os.IsNotExist(err) {
		return fmt.Errorf("path does not exist: %s", resumePlanPath)
	}

	if debug {
		fmt.Println("[DEBUG] Resume decomposition configuration:")
		fmt.Printf("  Plan path: %s\n", absPath)
	}

	fmt.Println("Resuming from decomposition step...")
	fmt.Printf("Plan document: %s\n", absPath)

	// TODO: Implement actual resume decomposition logic
	return nil
}

// runResumeBeads handles the resume beads command
func runResumeBeads(cmd *cobra.Command, args []string) error {
	// Validate phase files
	var validPaths []string
	for _, path := range resumePhaseFiles {
		absPath, err := filepath.Abs(path)
		if err != nil {
			return fmt.Errorf("invalid phase file path %s: %w", path, err)
		}
		if _, err := os.Stat(absPath); os.IsNotExist(err) {
			return fmt.Errorf("path does not exist: %s", path)
		}
		validPaths = append(validPaths, absPath)
	}

	if debug {
		fmt.Println("[DEBUG] Resume beads configuration:")
		fmt.Printf("  Phase files: %v\n", validPaths)
		fmt.Printf("  Epic title: %s\n", resumeEpicTitle)
	}

	fmt.Println("Resuming from beads integration step...")
	fmt.Printf("Phase files: %v\n", validPaths)
	fmt.Printf("Epic title: %s\n", resumeEpicTitle)

	// TODO: Implement actual resume beads logic
	return nil
}
