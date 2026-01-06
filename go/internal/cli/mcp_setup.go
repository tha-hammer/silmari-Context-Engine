package cli

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/spf13/cobra"
)

// MCP setup command flags
var (
	mcpProjectPath string
	mcpPresetFlag  string
	mcpAdd         []string
	mcpList        bool
	mcpSmart       bool
	mcpOutput      string
)

// Valid MCP presets
var validPresets = []string{"web", "fullstack", "data", "devops", "minimal", "rust", "python", "node", "docs"}

// mcpSetupCmd represents the mcp-setup subcommand
var mcpSetupCmd = &cobra.Command{
	Use:     "mcp-setup",
	Aliases: []string{"mcp"},
	Short:   "Configure MCP servers",
	Long: `Smart MCP Configurator
=====================
Configure MCP servers for your project.

Examples:
    context-engine mcp-setup --project ~/myapp
    context-engine mcp-setup --preset web
    context-engine mcp-setup --add github:owner/repo
    context-engine mcp-setup --list
    context-engine mcp-setup --smart`,
	RunE: runMCPSetup,
}

func init() {
	// MCP setup specific flags
	mcpSetupCmd.Flags().StringVarP(&mcpProjectPath, "project", "p", "", "Project path (default: current directory)")
	mcpSetupCmd.Flags().StringVar(&mcpPresetFlag, "preset", "", "Use a preset configuration")
	mcpSetupCmd.Flags().StringArrayVar(&mcpAdd, "add", nil, "Add MCP (ID, GitHub URL, or claude command)")
	mcpSetupCmd.Flags().BoolVarP(&mcpList, "list", "l", false, "List available MCPs")
	mcpSetupCmd.Flags().BoolVarP(&mcpSmart, "smart", "s", false, "Use Claude to recommend MCPs")
	mcpSetupCmd.Flags().StringVarP(&mcpOutput, "output", "o", "", "Output config file path")
}

// runMCPSetup is the mcp-setup command handler
func runMCPSetup(cmd *cobra.Command, args []string) error {
	// Default to current directory if no project specified
	if mcpProjectPath == "" {
		cwd, err := os.Getwd()
		if err != nil {
			return fmt.Errorf("failed to get current directory: %w", err)
		}
		mcpProjectPath = cwd
	} else {
		absPath, err := filepath.Abs(mcpProjectPath)
		if err != nil {
			return fmt.Errorf("invalid project path: %w", err)
		}
		if _, err := os.Stat(absPath); os.IsNotExist(err) {
			return fmt.Errorf("path does not exist: %s", mcpProjectPath)
		}
		mcpProjectPath = absPath
	}

	// Validate preset if provided
	if mcpPresetFlag != "" {
		if err := validateChoice(mcpPresetFlag, validPresets, "preset"); err != nil {
			return err
		}
	}

	// Validate output path if provided
	if mcpOutput != "" {
		absPath, err := filepath.Abs(mcpOutput)
		if err != nil {
			return fmt.Errorf("invalid output path: %w", err)
		}
		mcpOutput = absPath
	}

	if debug {
		fmt.Println("[DEBUG] MCP setup configuration:")
		fmt.Printf("  Project: %s\n", mcpProjectPath)
		fmt.Printf("  Preset: %s\n", mcpPresetFlag)
		fmt.Printf("  Add: %v\n", mcpAdd)
		fmt.Printf("  List: %v\n", mcpList)
		fmt.Printf("  Smart: %v\n", mcpSmart)
		fmt.Printf("  Output: %s\n", mcpOutput)
	}

	// List available MCPs and exit
	if mcpList {
		return listMCPs()
	}

	fmt.Println("Smart MCP Configurator")
	fmt.Println("=====================")
	fmt.Printf("Project: %s\n", mcpProjectPath)

	if mcpPresetFlag != "" {
		fmt.Printf("Applying preset: %s\n", mcpPresetFlag)
	}

	if mcpSmart {
		fmt.Println("Using Claude to recommend MCPs...")
	}

	// TODO: Implement actual MCP setup logic
	return nil
}

// listMCPs displays available MCP servers
func listMCPs() error {
	fmt.Println("Available MCP Presets:")
	fmt.Println("----------------------")
	for _, preset := range validPresets {
		fmt.Printf("  %s\n", preset)
	}
	// TODO: List individual MCPs from registry
	return nil
}
