package cli

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/spf13/cobra"
	"github.com/silmari/context-engine/go/internal/planning"
)

// Plan command flags
var (
	planProjectPath    string
	planTicket         string
	planAutoApprove    bool
	planPromptText     string
	planResume         bool
	planResumeStep     string
	planResearchPath   string
	planPlanPath       string
)

// Valid resume steps
var validResumeSteps = []string{"planning", "requirement_decomposition", "phase_decomposition"}

// planCmd represents the plan subcommand (maps to planning_orchestrator.py)
var planCmd = &cobra.Command{
	Use:     "plan",
	Aliases: []string{"p"},
	Short:   "Run the planning pipeline",
	Long: `Planning Pipeline Orchestrator
==============================
Run the planning pipeline to decompose requirements into phases.

Examples:
    context-engine plan --project ~/myapp
    context-engine plan --project ~/myapp --ticket PROJ-123
    context-engine plan --project ~/myapp --resume
    context-engine plan --project ~/myapp --resume-step planning`,
	RunE: runPlan,
}

func init() {
	// Plan-specific flags
	planCmd.Flags().StringVarP(&planProjectPath, "project", "p", "", "Project path (default: current directory)")
	planCmd.Flags().StringVarP(&planTicket, "ticket", "t", "", "Ticket ID for tracking")
	planCmd.Flags().BoolVarP(&planAutoApprove, "auto-approve", "y", false, "Skip interactive checkpoints")
	planCmd.Flags().StringVar(&planPromptText, "prompt-text", "", "Custom prompt text")

	// Resume flags
	planCmd.Flags().BoolVarP(&planResume, "resume", "r", false, "Resume from a previous step (auto-detects from checkpoints)")
	planCmd.Flags().StringVar(&planResumeStep, "resume-step", "", "Step to resume from: planning, requirement_decomposition, or phase_decomposition")
	planCmd.Flags().StringVar(&planResearchPath, "research-path", "", "Research .md file: full path, relative path, or just filename")
	planCmd.Flags().StringVar(&planPlanPath, "plan-path", "", "Plan .md file path for resume")

	// Support underscored versions for backwards compatibility
	planCmd.Flags().SetNormalizeFunc(normalizeUnderscoredFlags)
}

// runPlan is the plan command handler
func runPlan(cmd *cobra.Command, args []string) error {
	// Default to current directory if no project specified
	if planProjectPath == "" {
		cwd, err := os.Getwd()
		if err != nil {
			return fmt.Errorf("failed to get current directory: %w", err)
		}
		planProjectPath = cwd
	} else {
		absPath, err := filepath.Abs(planProjectPath)
		if err != nil {
			return fmt.Errorf("invalid project path: %w", err)
		}
		if _, err := os.Stat(absPath); os.IsNotExist(err) {
			return fmt.Errorf("path does not exist: %s", planProjectPath)
		}
		planProjectPath = absPath
	}

	// Validate resume step if provided
	if planResumeStep != "" {
		if err := validateChoice(planResumeStep, validResumeSteps, "resume-step"); err != nil {
			return err
		}
	}

	// Validate research path if provided
	if planResearchPath != "" {
		if err := validatePath(planResearchPath, "research-path"); err != nil {
			return err
		}
	}

	// Validate plan path if provided
	if planPlanPath != "" {
		if err := validatePath(planPlanPath, "plan-path"); err != nil {
			return err
		}
	}

	if debug {
		fmt.Println("[DEBUG] Plan configuration:")
		fmt.Printf("  Project: %s\n", planProjectPath)
		fmt.Printf("  Ticket: %s\n", planTicket)
		fmt.Printf("  Auto-approve: %v\n", planAutoApprove)
		fmt.Printf("  Prompt text: %s\n", planPromptText)
		fmt.Printf("  Resume: %v\n", planResume)
		fmt.Printf("  Resume step: %s\n", planResumeStep)
		fmt.Printf("  Research path: %s\n", planResearchPath)
		fmt.Printf("  Plan path: %s\n", planPlanPath)
	}

	fmt.Println("Planning Pipeline Orchestrator")
	fmt.Println("==============================")
	fmt.Printf("Project: %s\n", planProjectPath)

	if planResume {
		fmt.Println("Resuming from checkpoint...")
		if planResumeStep != "" {
			fmt.Printf("  Step: %s\n", planResumeStep)
		}
	}

	// Validate that prompt text is provided
	if planPromptText == "" {
		return fmt.Errorf("--prompt-text is required")
	}

	// Create and run the planning pipeline
	config := planning.PipelineConfig{
		ProjectPath: planProjectPath,
		AutoApprove: planAutoApprove,
		TicketID:    planTicket,
	}

	pipeline := planning.NewPlanningPipeline(config)
	results := pipeline.Run(planPromptText)

	// Display results
	if results.Success {
		fmt.Printf("\n✓ Pipeline completed successfully\n")
		if results.PlanDir != "" {
			fmt.Printf("  Plan directory: %s\n", results.PlanDir)
		}
		if results.EpicID != "" {
			fmt.Printf("  Epic ID: %s\n", results.EpicID)
		}
		return nil
	}

	// Pipeline failed
	fmt.Printf("\n✗ Pipeline failed at: %s\n", results.FailedAt)
	if results.Error != "" {
		fmt.Printf("  Error: %s\n", results.Error)
	}
	return fmt.Errorf("pipeline failed at step: %s", results.FailedAt)
}
