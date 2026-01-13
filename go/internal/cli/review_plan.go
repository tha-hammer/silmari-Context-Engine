package cli

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/spf13/cobra"
	"github.com/silmari/context-engine/go/internal/planning"
)

// Review plan command flags
var (
	reviewPlanPath     string
	reviewPhase        string
	reviewStep         string
	reviewOutputPath   string
	reviewAutonomyMode string
	reviewAllPhases    bool
)

// Valid phase choices for review (matches PhaseType enum)
var validReviewPhases = []string{
	"research",
	"decomposition",
	"tdd_planning",
	"multi_doc",
	"beads_sync",
	"implementation",
}

// Valid step choices for the 5-step review framework
var validReviewSteps = []string{
	"contracts",
	"interfaces",
	"promises",
	"data_models",
	"apis",
}

// Valid autonomy mode choices
var validAutonomyModes = []string{
	"checkpoint",
	"batch",
	"fully_autonomous",
}

// reviewPlanCmd represents the review-plan subcommand
var reviewPlanCmd = &cobra.Command{
	Use:     "review-plan",
	Aliases: []string{"rp", "review"},
	Short:   "Review an implementation plan before execution",
	Long: `Plan Review
===========
Review a generated plan document and validate its implementation readiness.

The review process uses a 5-step framework:
  1. Contracts - Analyze contract definitions and guarantees
  2. Interfaces - Review public API surfaces and boundaries
  3. Promises - Validate behavioral commitments and invariants
  4. Data Models - Check field definitions and relationships
  5. APIs - Verify endpoint signatures and specifications

Examples:
    context-engine review-plan --plan-path ./thoughts/plans/myplan.md
    context-engine review-plan --plan-path ./plan.md --phase decomposition
    context-engine review-plan --plan-path ./plan.md --step contracts
    context-engine review-plan --plan-path ./plan.md --all-phases
    context-engine rp -p ./plan.md --autonomy-mode batch`,
	RunE: runReviewPlan,
}

func init() {
	// Review plan specific flags
	reviewPlanCmd.Flags().StringVarP(&reviewPlanPath, "plan-path", "p", "", "Path to plan document (searches thoughts/plans/ if empty)")
	reviewPlanCmd.Flags().StringVar(&reviewPhase, "phase", "", "Phase to review: research, decomposition, tdd_planning, multi_doc, beads_sync, implementation")
	reviewPlanCmd.Flags().StringVar(&reviewStep, "step", "", "Review step: contracts, interfaces, promises, data_models, apis")
	reviewPlanCmd.Flags().StringVarP(&reviewOutputPath, "output", "o", "", "Output path for review results")
	reviewPlanCmd.Flags().StringVar(&reviewAutonomyMode, "autonomy-mode", "checkpoint", "Autonomy mode: checkpoint (default), batch, fully_autonomous")
	reviewPlanCmd.Flags().BoolVar(&reviewAllPhases, "all-phases", false, "Review all phases sequentially")

	// Support underscored versions for backwards compatibility
	reviewPlanCmd.Flags().SetNormalizeFunc(normalizeUnderscoredFlags)
}

// runReviewPlan is the review-plan command handler
func runReviewPlan(cmd *cobra.Command, args []string) error {
	var projectPath string

	// Default project path to current directory
	cwd, err := os.Getwd()
	if err != nil {
		return fmt.Errorf("failed to get current directory: %w", err)
	}
	projectPath = cwd

	// Handle plan path
	if reviewPlanPath == "" {
		// Search for recent plans in thoughts/searchable/shared/plans/
		planDir := filepath.Join(projectPath, "thoughts", "searchable", "shared", "plans")
		if _, err := os.Stat(planDir); err == nil {
			// Find most recent plan directory or file
			entries, err := os.ReadDir(planDir)
			if err == nil && len(entries) > 0 {
				// Find the most recent entry (they are typically dated)
				var recentPlan string
				for i := len(entries) - 1; i >= 0; i-- {
					entry := entries[i]
					if strings.HasSuffix(entry.Name(), ".md") || entry.IsDir() {
						recentPlan = filepath.Join(planDir, entry.Name())
						break
					}
				}
				if recentPlan != "" {
					reviewPlanPath = recentPlan
				}
			}
		}

		if reviewPlanPath == "" {
			return fmt.Errorf("--plan-path is required (no plans found in thoughts/searchable/shared/plans/)")
		}
	}

	// Validate and normalize plan path
	absPath, err := filepath.Abs(reviewPlanPath)
	if err != nil {
		return fmt.Errorf("invalid plan path: %w", err)
	}
	if _, err := os.Stat(absPath); os.IsNotExist(err) {
		return fmt.Errorf("plan path does not exist: %s", reviewPlanPath)
	}
	reviewPlanPath = absPath

	// Validate phase if provided
	if reviewPhase != "" {
		if err := validateChoice(reviewPhase, validReviewPhases, "phase"); err != nil {
			return err
		}
	}

	// Validate step if provided
	if reviewStep != "" {
		if err := validateChoice(reviewStep, validReviewSteps, "step"); err != nil {
			return err
		}
	}

	// Validate autonomy mode
	if err := validateChoice(reviewAutonomyMode, validAutonomyModes, "autonomy-mode"); err != nil {
		return err
	}

	// Validate output path if provided
	if reviewOutputPath != "" {
		absOutputPath, err := filepath.Abs(reviewOutputPath)
		if err != nil {
			return fmt.Errorf("invalid output path: %w", err)
		}
		// Ensure parent directory exists
		parentDir := filepath.Dir(absOutputPath)
		if _, err := os.Stat(parentDir); os.IsNotExist(err) {
			return fmt.Errorf("output directory does not exist: %s", parentDir)
		}
		reviewOutputPath = absOutputPath
	}

	// Debug output
	if debug {
		fmt.Println("[DEBUG] Review plan configuration:")
		fmt.Printf("  Project: %s\n", projectPath)
		fmt.Printf("  Plan path: %s\n", reviewPlanPath)
		fmt.Printf("  Phase: %s\n", reviewPhase)
		fmt.Printf("  Step: %s\n", reviewStep)
		fmt.Printf("  Output: %s\n", reviewOutputPath)
		fmt.Printf("  Autonomy mode: %s\n", reviewAutonomyMode)
		fmt.Printf("  All phases: %v\n", reviewAllPhases)
	}

	// Header output
	fmt.Println("Plan Review")
	fmt.Println("===========")
	fmt.Printf("Project: %s\n", projectPath)
	fmt.Printf("Plan: %s\n", filepath.Base(reviewPlanPath))

	if reviewPhase != "" {
		fmt.Printf("Phase: %s\n", reviewPhase)
	}
	if reviewStep != "" {
		fmt.Printf("Step: %s\n", reviewStep)
	}
	fmt.Printf("Mode: %s\n", reviewAutonomyMode)

	// Parse autonomy mode
	autonomyMode, err := planning.AutonomyModeFromString(reviewAutonomyMode)
	if err != nil {
		return fmt.Errorf("invalid autonomy mode: %w", err)
	}

	// Create review config
	config := planning.ReviewConfig{
		ProjectPath:  projectPath,
		PlanPath:     reviewPlanPath,
		Phase:        reviewPhase,
		Step:         reviewStep,
		OutputPath:   reviewOutputPath,
		AutonomyMode: autonomyMode,
		AllPhases:    reviewAllPhases,
	}

	// Run the review
	result := planning.RunReview(config)

	// Handle results
	if result.Success {
		fmt.Printf("\n✅ Plan review complete\n")
		if result.Output != "" {
			fmt.Printf("  Output: %s\n", result.Output)
		}
		if reviewOutputPath != "" {
			fmt.Printf("  Results saved to: %s\n", reviewOutputPath)
		}
		return nil
	}

	// Review failed
	fmt.Printf("\n❌ Review failed\n")
	if result.FailedAt != "" {
		fmt.Printf("  Failed at: %s\n", result.FailedAt)
	}
	if result.Error != "" {
		fmt.Printf("  Error: %s\n", result.Error)
	}
	return fmt.Errorf("review failed: %s", result.Error)
}
