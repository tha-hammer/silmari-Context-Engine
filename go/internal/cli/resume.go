package cli

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/silmari/context-engine/go/internal/planning"
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

// findProjectRoot determines the project root directory.
// If in a Git repository, returns the repository root.
// If not in a Git repository, returns the current working directory.
// Beads is always locked to the project directory - it does NOT search parent directories.
func findProjectRoot() (string, error) {
	dir, err := os.Getwd()
	if err != nil {
		return "", err
	}

	// Try to find Git repository root
	gitRoot, err := findGitRoot(dir)
	if err == nil {
		// In a Git repository - use the Git root
		return gitRoot, nil
	}

	// Not in a Git repository - use current working directory (local mode)
	return dir, nil
}

// findGitRoot finds the root of the Git repository
func findGitRoot(startDir string) (string, error) {
	dir := startDir
	for {
		gitPath := filepath.Join(dir, ".git")
		if info, err := os.Stat(gitPath); err == nil && info.IsDir() {
			return dir, nil
		}

		// Check if we've reached the root
		parent := filepath.Dir(dir)
		if parent == dir {
			return "", fmt.Errorf("not in a git repository")
		}
		dir = parent
	}
}

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
	// Find project root
	projectPath, err := findProjectRoot()
	if err != nil {
		return fmt.Errorf("failed to find project root: %w (hint: run from a directory containing .beads/)", err)
	}

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
		fmt.Printf("  Project path: %s\n", projectPath)
		fmt.Printf("  Research path: %s\n", absPath)
		fmt.Printf("  Additional context: %s\n", resumeAdditionalContext)
	}

	fmt.Println("Resuming from planning step...")
	fmt.Printf("Project: %s\n", projectPath)
	fmt.Printf("Research document: %s\n", absPath)

	// TODO: Implement actual resume planning logic
	return nil
}

// runResumeDecomposition handles the resume decomposition command
func runResumeDecomposition(cmd *cobra.Command, args []string) error {
	// Find project root
	projectPath, err := findProjectRoot()
	if err != nil {
		return fmt.Errorf("failed to find project root: %w (hint: run from a directory containing .beads/)", err)
	}

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
		fmt.Printf("  Project path: %s\n", projectPath)
		fmt.Printf("  Plan path: %s\n", absPath)
	}

	fmt.Println("Resuming from decomposition step...")
	fmt.Printf("Project: %s\n", projectPath)
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

	// Get project path - find the directory containing .beads
	projectPath, err := findProjectRoot()
	if err != nil {
		return fmt.Errorf("failed to find project root: %w (hint: run from a directory containing .beads/)", err)
	}

	if debug {
		fmt.Println("[DEBUG] Resume beads configuration:")
		fmt.Printf("  Project path: %s\n", projectPath)
		fmt.Printf("  Phase files: %v\n", validPaths)
		fmt.Printf("  Epic title: %s\n", resumeEpicTitle)
	}

	fmt.Println("\n============================================================")
	fmt.Println("RESUMING: BEADS INTEGRATION")
	fmt.Println("============================================================")
	fmt.Printf("Epic title: %s\n", resumeEpicTitle)
	fmt.Printf("Phase files: %d\n", len(validPaths))

	// Run beads integration
	result := planning.StepBeadsIntegration(projectPath, validPaths, resumeEpicTitle)

	if !result.Success {
		fmt.Printf("\n❌ Beads integration failed: %s\n", result.Error)
		return fmt.Errorf("beads integration failed: %s", result.Error)
	}

	fmt.Printf("\n✅ Beads integration complete\n")
	fmt.Printf("Epic ID: %s\n", result.EpicID)
	fmt.Printf("Phase issues created: %d\n", len(result.PhaseIssues))

	if len(result.FilesAnnotated) > 0 {
		fmt.Printf("Files annotated: %d\n", len(result.FilesAnnotated))
	}

	// Print phase details
	fmt.Println("\nPhase Issues:")
	for _, pi := range result.PhaseIssues {
		if pi.IssueID != "" {
			fmt.Printf("  Phase %d: %s → %s\n", pi.Phase, filepath.Base(pi.File), pi.IssueID)
		} else {
			fmt.Printf("  Phase %d: %s → (failed to create)\n", pi.Phase, filepath.Base(pi.File))
		}
	}

	fmt.Println("\n💡 Next steps:")
	fmt.Println("  1. Run 'bd list --status=open' to see created issues")
	fmt.Printf("  2. Run 'bd show %s' to see the epic\n", result.EpicID)
	fmt.Println("  3. Use 'bd update <issue-id> --status=in_progress' to start work")

	return nil
}
