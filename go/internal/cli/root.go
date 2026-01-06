// Package cli provides the cobra-based CLI for the context engine.
package cli

import (
	"fmt"

	"github.com/spf13/cobra"
)

// Version information (set at build time via ldflags)
var (
	Version   = "dev"
	GitCommit = "unknown"
	BuildDate = "unknown"
)

// Global flags
var (
	debug   bool
	verbose bool
)

// rootCmd is the base command for context-engine
var rootCmd = &cobra.Command{
	Use:   "context-engine",
	Short: "Context-Engineered Agent Orchestrator",
	Long: `Context-Engineered Agent Orchestrator
=====================================
Autonomous project builder using Claude Code with context engineering principles.

Examples:
    context-engine                        # Interactive mode
    context-engine --project ~/myapp      # Specify project
    context-engine --continue             # Continue existing project
    context-engine plan --project ~/myapp # Run planning pipeline
    context-engine mcp-setup --preset web # Configure MCP`,
	Version: fmt.Sprintf("%s (commit: %s, built: %s)", Version, GitCommit, BuildDate),
	RunE:    runOrchestrator,
}

// Execute runs the root command
func Execute() error {
	return rootCmd.Execute()
}

func init() {
	// Global persistent flags available to all subcommands
	rootCmd.PersistentFlags().BoolVarP(&debug, "debug", "d", false, "Show debug output")
	rootCmd.PersistentFlags().BoolVarP(&verbose, "verbose", "v", false, "Verbose output")

	// Add subcommands
	rootCmd.AddCommand(planCmd)
	rootCmd.AddCommand(mcpSetupCmd)
	rootCmd.AddCommand(resumeCmd)

	// Set up custom usage template matching Python argparse style
	rootCmd.SetUsageTemplate(usageTemplate)
}

// usageTemplate provides argparse-style help output
const usageTemplate = `Usage:
  {{.CommandPath}} [flags]
  {{.CommandPath}} [command]{{if gt (len .Aliases) 0}}

Aliases:
  {{.NameAndAliases}}{{end}}{{if .HasExample}}

Examples:
{{.Example}}{{end}}{{if .HasAvailableSubCommands}}

Available Commands:{{range .Commands}}{{if (or .IsAvailableCommand (eq .Name "help"))}}
  {{rpad .Name .NamePadding }} {{.Short}}{{end}}{{end}}{{end}}{{if .HasAvailableLocalFlags}}

Flags:
{{.LocalFlags.FlagUsages | trimTrailingWhitespaces}}{{end}}{{if .HasAvailableInheritedFlags}}

Global Flags:
{{.InheritedFlags.FlagUsages | trimTrailingWhitespaces}}{{end}}{{if .HasHelpSubCommands}}

Additional help topics:{{range .Commands}}{{if .IsAdditionalHelpTopicCommand}}
  {{rpad .CommandPath .CommandPathPadding}} {{.Short}}{{end}}{{end}}{{end}}{{if .HasAvailableSubCommands}}

Use "{{.CommandPath}} [command] --help" for more information about a command.{{end}}
`
