package cli

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/spf13/cobra"
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
