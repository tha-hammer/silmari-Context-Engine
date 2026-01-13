package cli

import (
	"strings"

	"github.com/spf13/pflag"
)

// normalizeUnderscoredFlags allows both --flag-name and --flag_name
// for backwards compatibility with Python argparse
func normalizeUnderscoredFlags(f *pflag.FlagSet, name string) pflag.NormalizedName {
	// Convert underscores to dashes
	if strings.Contains(name, "_") {
		name = strings.ReplaceAll(name, "_", "-")
	}
	return pflag.NormalizedName(name)
}

// Flag name constants for consistent reference
const (
	FlagProject       = "project"
	FlagModel         = "model"
	FlagMaxSessions   = "max-sessions"
	FlagContinue      = "continue"
	FlagStatus        = "status"
	FlagMCPPreset     = "mcp-preset"
	FlagWithQA        = "with-qa"
	FlagInteractive   = "interactive"
	FlagDebug         = "debug"
	FlagVerbose       = "verbose"
	FlagNew           = "new"
	FlagTicket        = "ticket"
	FlagAutoApprove   = "auto-approve"
	FlagPromptText    = "prompt-text"
	FlagResume        = "resume"
	FlagResumeStep    = "resume-step"
	FlagResearchPath  = "research-path"
	FlagPlanPath      = "plan-path"
	FlagFeatures      = "features"
	FlagMaxIterations = "max-iterations"
	FlagTimeout       = "timeout"
	FlagParallel      = "parallel"
	FlagDryRun        = "dry-run"
	FlagSkipReview    = "skip-review"
	FlagValidate      = "validate"
	FlagShowBlocked   = "show-blocked"
	FlagUnblock       = "unblock"
	FlagQAMode        = "qa-mode"
	FlagMetrics       = "metrics"
	FlagPreset        = "preset"
	FlagAdd           = "add"
	FlagList          = "list"
	FlagSmart         = "smart"
	FlagOutput        = "output"
	FlagPhaseFiles    = "phase-files"
	FlagEpicTitle     = "epic-title"
	FlagPhase         = "phase"
	FlagStep          = "step"
	FlagAutonomyMode  = "autonomy-mode"
	FlagAllPhases     = "all-phases"
)

// Short flag mappings for documentation
var shortFlags = map[string]string{
	FlagProject:     "p",
	FlagModel:       "m",
	FlagContinue:    "c",
	FlagStatus:      "s",
	FlagInteractive: "i",
	FlagDebug:       "d",
	FlagVerbose:     "v",
	FlagTicket:      "t",
	FlagAutoApprove: "y",
	FlagResume:      "r",
	FlagFeatures:    "f",
	FlagMaxSessions: "n",
	FlagParallel:    "P",
	FlagList:        "l",
	FlagSmart:       "s",
	FlagOutput:      "o",
}

// GetShortFlag returns the short flag for a given long flag name
func GetShortFlag(longFlag string) string {
	return shortFlags[longFlag]
}
