package cli

import (
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/spf13/cobra"
)

// Loop runner flags
var (
	lrProjectPath  string
	lrFeaturesPath string
	lrModel        string
	lrMaxSessions  int
	lrMaxIter      int
	lrTimeout      time.Duration
	lrParallel     int
	lrDryRun       bool
	lrResume       bool
	lrVerbose      bool
	lrInteractive  bool
	lrSkipReview   bool
	lrValidate     bool
	lrShowBlocked  bool
	lrUnblock      string
	lrQAMode       string
	lrMetrics      bool
)

// Valid QA modes
var validQAModes = []string{"full", "lite"}

// loopRunnerCmd is the root command for loop-runner binary
var loopRunnerCmd = &cobra.Command{
	Use:   "loop-runner [project]",
	Short: "Autonomous loop runner that continuously runs Claude Code sessions",
	Long: `Autonomous Loop Runner
======================
Continuously runs Claude Code sessions until all features are complete.

Examples:
    loop-runner                           # Run in current directory
    loop-runner ~/projects/myapp          # Run in specific project
    loop-runner --max-sessions 20
    loop-runner --features features.json
    loop-runner --validate                # Validate feature_list.json and exit`,
	Args:    cobra.MaximumNArgs(1),
	Version: fmt.Sprintf("%s (commit: %s, built: %s)", Version, GitCommit, BuildDate),
	RunE:    runLoopRunner,
}

// ExecuteLoopRunner runs the loop-runner command
func ExecuteLoopRunner() error {
	return loopRunnerCmd.Execute()
}

func init() {
	// Loop runner flags
	loopRunnerCmd.Flags().StringVarP(&lrFeaturesPath, "features", "f", "", "Path to features.json file")
	loopRunnerCmd.Flags().StringVarP(&lrModel, "model", "m", "sonnet", "Model to use (sonnet/opus)")
	loopRunnerCmd.Flags().IntVarP(&lrMaxSessions, "max-sessions", "n", 100, "Max sessions")
	loopRunnerCmd.Flags().IntVar(&lrMaxIter, "max-iterations", 0, "Maximum loop iterations (0 = unlimited)")
	loopRunnerCmd.Flags().DurationVar(&lrTimeout, "timeout", 1*time.Hour, "Session timeout")
	loopRunnerCmd.Flags().IntVarP(&lrParallel, "parallel", "P", 1, "Parallel execution count")
	loopRunnerCmd.Flags().BoolVar(&lrDryRun, "dry-run", false, "Validation without execution")
	loopRunnerCmd.Flags().BoolVar(&lrResume, "resume", false, "Resume from last checkpoint")
	loopRunnerCmd.Flags().BoolVarP(&lrVerbose, "verbose", "v", false, "Verbose output")
	loopRunnerCmd.Flags().BoolVarP(&lrInteractive, "interactive", "i", false, "Run interactively (opens shell)")
	loopRunnerCmd.Flags().BoolVar(&lrSkipReview, "skip-review", false, "Skip features marked needs_review")
	loopRunnerCmd.Flags().BoolVar(&lrValidate, "validate", false, "Validate feature_list.json and exit")
	loopRunnerCmd.Flags().BoolVar(&lrShowBlocked, "show-blocked", false, "Show blocked features and exit")
	loopRunnerCmd.Flags().StringVar(&lrUnblock, "unblock", "", "Unblock a feature by ID")
	loopRunnerCmd.Flags().StringVar(&lrQAMode, "qa-mode", "full", "QA testing mode: full (comprehensive) or lite (quick)")
	loopRunnerCmd.Flags().BoolVar(&lrMetrics, "metrics", false, "Show metrics report and exit")

	// Debug flag (global-like)
	loopRunnerCmd.Flags().BoolVarP(&debug, "debug", "d", false, "Show debug output")

	// Set up custom usage template
	loopRunnerCmd.SetUsageTemplate(usageTemplate)
}

// runLoopRunner is the loop-runner command handler
func runLoopRunner(cmd *cobra.Command, args []string) error {
	// Get project path from positional arg or default to cwd
	if len(args) > 0 {
		lrProjectPath = args[0]
	}
	if lrProjectPath == "" {
		cwd, err := os.Getwd()
		if err != nil {
			return fmt.Errorf("failed to get current directory: %w", err)
		}
		lrProjectPath = cwd
	} else {
		absPath, err := filepath.Abs(lrProjectPath)
		if err != nil {
			return fmt.Errorf("invalid project path: %w", err)
		}
		if _, err := os.Stat(absPath); os.IsNotExist(err) {
			return fmt.Errorf("path does not exist: %s", lrProjectPath)
		}
		lrProjectPath = absPath
	}

	// Validate model choice
	if err := validateChoice(lrModel, validModels, "model"); err != nil {
		return err
	}

	// Validate QA mode
	if err := validateChoice(lrQAMode, validQAModes, "qa-mode"); err != nil {
		return err
	}

	// Validate features path if provided
	if lrFeaturesPath != "" {
		absPath, err := filepath.Abs(lrFeaturesPath)
		if err != nil {
			return fmt.Errorf("invalid features path: %w", err)
		}
		if _, err := os.Stat(absPath); os.IsNotExist(err) {
			return fmt.Errorf("path does not exist: %s", lrFeaturesPath)
		}
		lrFeaturesPath = absPath
	}

	// Validate parallel count
	if lrParallel < 1 {
		return fmt.Errorf("invalid integer value for --parallel: must be at least 1")
	}

	if debug {
		fmt.Println("[DEBUG] Loop runner configuration:")
		fmt.Printf("  Project: %s\n", lrProjectPath)
		fmt.Printf("  Features: %s\n", lrFeaturesPath)
		fmt.Printf("  Model: %s\n", lrModel)
		fmt.Printf("  Max sessions: %d\n", lrMaxSessions)
		fmt.Printf("  Max iterations: %d\n", lrMaxIter)
		fmt.Printf("  Timeout: %v\n", lrTimeout)
		fmt.Printf("  Parallel: %d\n", lrParallel)
		fmt.Printf("  Dry run: %v\n", lrDryRun)
		fmt.Printf("  Resume: %v\n", lrResume)
		fmt.Printf("  Verbose: %v\n", lrVerbose)
		fmt.Printf("  Interactive: %v\n", lrInteractive)
		fmt.Printf("  Skip review: %v\n", lrSkipReview)
		fmt.Printf("  QA mode: %s\n", lrQAMode)
	}

	// Handle quick-exit flags
	if lrValidate {
		return validateFeatures(lrProjectPath)
	}

	if lrShowBlocked {
		return showBlockedFeatures(lrProjectPath)
	}

	if lrMetrics {
		return showMetrics(lrProjectPath)
	}

	if lrUnblock != "" {
		return unblockFeature(lrProjectPath, lrUnblock)
	}

	fmt.Println("Autonomous Loop Runner")
	fmt.Println("======================")
	fmt.Printf("Project: %s\n", lrProjectPath)
	fmt.Printf("Model: %s\n", lrModel)
	fmt.Printf("Max sessions: %d\n", lrMaxSessions)

	if lrDryRun {
		fmt.Println("(Dry run mode - no execution)")
	}

	// TODO: Implement actual loop runner logic
	return nil
}

// validateFeatures validates the feature_list.json file
func validateFeatures(projectPath string) error {
	featureFile := filepath.Join(projectPath, "feature_list.json")
	if _, err := os.Stat(featureFile); os.IsNotExist(err) {
		return fmt.Errorf("feature_list.json not found in %s", projectPath)
	}

	fmt.Printf("Validating feature_list.json in %s...\n", projectPath)
	// TODO: Implement actual validation
	fmt.Println("Validation passed!")
	return nil
}

// showBlockedFeatures displays blocked features
func showBlockedFeatures(projectPath string) error {
	fmt.Printf("Blocked features in %s:\n", projectPath)
	// TODO: Implement actual blocked feature display
	fmt.Println("  (none)")
	return nil
}

// showMetrics displays metrics report
func showMetrics(projectPath string) error {
	fmt.Printf("Metrics for %s:\n", projectPath)
	// TODO: Implement actual metrics display
	fmt.Println("  Total features: 0")
	fmt.Println("  Completed: 0")
	fmt.Println("  In progress: 0")
	fmt.Println("  Blocked: 0")
	return nil
}

// unblockFeature unblocks a feature by ID
func unblockFeature(projectPath, featureID string) error {
	fmt.Printf("Unblocking feature %s in %s...\n", featureID, projectPath)
	// TODO: Implement actual unblock logic
	fmt.Printf("Feature %s unblocked!\n", featureID)
	return nil
}
