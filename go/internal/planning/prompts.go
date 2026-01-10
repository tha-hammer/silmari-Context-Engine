// Package planning provides planning pipeline data structures and logic.
package planning

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"strings"
)

// AutonomyMode defines how the pipeline handles checkpoints.
type AutonomyMode int

const (
	// AutonomyCheckpoint pauses after each phase for user review (default).
	AutonomyCheckpoint AutonomyMode = iota
	// AutonomyFullyAutonomous runs all phases without stopping.
	AutonomyFullyAutonomous
	// AutonomyBatch runs groups of phases, pausing between groups.
	AutonomyBatch
)

// String returns the string representation of the AutonomyMode.
func (am AutonomyMode) String() string {
	switch am {
	case AutonomyCheckpoint:
		return "checkpoint"
	case AutonomyFullyAutonomous:
		return "fully_autonomous"
	case AutonomyBatch:
		return "batch"
	default:
		return "unknown"
	}
}

// AutonomyModeFromString parses a string into an AutonomyMode.
func AutonomyModeFromString(s string) (AutonomyMode, error) {
	switch strings.ToLower(strings.TrimSpace(s)) {
	case "checkpoint":
		return AutonomyCheckpoint, nil
	case "fully_autonomous", "autonomous":
		return AutonomyFullyAutonomous, nil
	case "batch":
		return AutonomyBatch, nil
	default:
		return AutonomyCheckpoint, fmt.Errorf("invalid autonomy mode: %s", s)
	}
}

// MarshalJSON implements json.Marshaler for AutonomyMode.
func (am AutonomyMode) MarshalJSON() ([]byte, error) {
	return json.Marshal(am.String())
}

// UnmarshalJSON implements json.Unmarshaler for AutonomyMode.
func (am *AutonomyMode) UnmarshalJSON(data []byte) error {
	var s string
	if err := json.Unmarshal(data, &s); err != nil {
		return fmt.Errorf("autonomy mode must be a string: %w", err)
	}

	mode, err := AutonomyModeFromString(s)
	if err != nil {
		return err
	}

	*am = mode
	return nil
}

// PhaseAction represents user decisions at phase checkpoints.
type PhaseAction string

const (
	ActionContinue PhaseAction = "continue"
	ActionRevise   PhaseAction = "revise"
	ActionRestart  PhaseAction = "restart"
	ActionExit     PhaseAction = "exit"
)

// PhaseContinueResult represents the result of prompting to continue a phase.
type PhaseContinueResult struct {
	Continue bool
	Feedback string
}

// CollectMultilineInput reads lines from stdin until an empty line is entered.
// The prompt string is displayed before each input line.
func CollectMultilineInput(prompt string) string {
	scanner := bufio.NewScanner(os.Stdin)
	var lines []string

	for {
		if prompt != "" {
			fmt.Print(prompt)
		}

		if !scanner.Scan() {
			// EOF or error
			break
		}

		line := scanner.Text()
		if line == "" {
			break
		}

		lines = append(lines, line)
	}

	return strings.Join(lines, "\n")
}

// PromptResearchAction displays menu for research phase with Continue, Revise, Start over, Exit options.
func PromptResearchAction() PhaseAction {
	fmt.Println("\n=== Research Phase Complete ===")
	fmt.Println("[C] Continue to decomposition")
	fmt.Println("[R] Revise research")
	fmt.Println("[S] Start over")
	fmt.Println("[E] Exit")
	fmt.Print("Choice: ")

	return readPhaseAction()
}

// PromptDecompositionAction displays menu for decomposition phase with Continue, Revise, Start over, Exit options.
func PromptDecompositionAction() PhaseAction {
	fmt.Println("\n=== Decomposition Phase Complete ===")
	fmt.Println("[C] Continue to TDD planning")
	fmt.Println("[R] Revise decomposition")
	fmt.Println("[S] Start over")
	fmt.Println("[E] Exit")
	fmt.Print("Choice: ")

	return readPhaseAction()
}

// PromptTDDPlanningAction displays menu for TDD planning phase with Continue, Revise, Start over, Exit options.
func PromptTDDPlanningAction() PhaseAction {
	fmt.Println("\n=== TDD Planning Phase Complete ===")
	fmt.Println("[C] Continue to multi-doc generation")
	fmt.Println("[R] Revise TDD plan")
	fmt.Println("[S] Start over")
	fmt.Println("[E] Exit")
	fmt.Print("Choice: ")

	return readPhaseAction()
}

// readPhaseAction reads a single character action from stdin and returns the corresponding PhaseAction.
// Accepts c/r/s/e (case-insensitive). Empty input defaults to 'continue'.
// Invalid input displays error and re-prompts.
func readPhaseAction() PhaseAction {
	scanner := bufio.NewScanner(os.Stdin)

	for {
		if !scanner.Scan() {
			// EOF - default to continue
			return ActionContinue
		}

		input := strings.TrimSpace(strings.ToLower(scanner.Text()))

		// Empty input defaults to continue
		if input == "" {
			return ActionContinue
		}

		switch input {
		case "c":
			return ActionContinue
		case "r":
			return ActionRevise
		case "s":
			return ActionRestart
		case "e":
			return ActionExit
		default:
			fmt.Printf("Invalid choice: '%s'. Please enter C, R, S, or E.\nChoice: ", input)
		}
	}
}

// PromptPhaseContinue displays completed phase info and prompts Y/n to continue.
// If user answers 'n', prompts for multiline feedback.
func PromptPhaseContinue(phaseName string, artifacts []string) PhaseContinueResult {
	fmt.Printf("\n=== Phase Complete: %s ===\n", phaseName)
	if len(artifacts) > 0 {
		fmt.Println("Artifacts:")
		for _, artifact := range artifacts {
			fmt.Printf("  - %s\n", artifact)
		}
	}
	fmt.Print("Continue? [Y/n]: ")

	scanner := bufio.NewScanner(os.Stdin)
	if !scanner.Scan() {
		// EOF - default to yes
		return PhaseContinueResult{Continue: true}
	}

	input := strings.TrimSpace(strings.ToLower(scanner.Text()))

	// Empty or 'y' means continue
	if input == "" || input == "y" {
		return PhaseContinueResult{Continue: true}
	}

	// 'n' means don't continue, collect feedback
	if input == "n" {
		fmt.Println("\nPlease provide feedback (enter empty line when done):")
		feedback := CollectMultilineInput("> ")
		return PhaseContinueResult{
			Continue: false,
			Feedback: feedback,
		}
	}

	// Any other input defaults to yes
	return PhaseContinueResult{Continue: true}
}

// PromptUseCheckpoint displays checkpoint info and prompts Y/n to resume from it.
func PromptUseCheckpoint(timestamp, phaseName string, artifacts []string) bool {
	fmt.Println("\n=== Resumable Checkpoint Found ===")
	fmt.Printf("Timestamp: %s\n", timestamp)
	fmt.Printf("Phase: %s\n", phaseName)
	if len(artifacts) > 0 {
		fmt.Println("Artifacts:")
		for _, artifact := range artifacts {
			fmt.Printf("  - %s\n", artifact)
		}
	}
	fmt.Print("Resume from this checkpoint? [Y/n]: ")

	scanner := bufio.NewScanner(os.Stdin)
	if !scanner.Scan() {
		// EOF - default to yes
		return true
	}

	input := strings.TrimSpace(strings.ToLower(scanner.Text()))

	// Empty or 'y' means yes
	if input == "" || input == "y" {
		return true
	}

	// 'n' means no
	return input != "n"
}

// PromptFileSelection displays numbered file list with search, custom path, and exit options.
// Returns action ("selected", "search", "other", "exit") and selected file path (if action is "selected").
func PromptFileSelection(files []string, fileType string) (action string, selectedPath string) {
	fmt.Printf("\n=== SELECT %s FILE ===\n", strings.ToUpper(fileType))

	if len(files) == 0 {
		fmt.Printf("No %s files found.\n", fileType)
	} else {
		for i, file := range files {
			fmt.Printf("[%d] %s\n", i+1, file)
		}
	}

	fmt.Println("\n[S] Search again")
	fmt.Println("[O] Other (specify path)")
	fmt.Println("[E] Exit")
	fmt.Print("Choice: ")

	scanner := bufio.NewScanner(os.Stdin)
	for {
		if !scanner.Scan() {
			// EOF - treat as exit
			return "exit", ""
		}

		input := strings.TrimSpace(scanner.Text())
		inputLower := strings.ToLower(input)

		// Handle single-letter choices
		if inputLower == "s" {
			return "search", ""
		}
		if inputLower == "o" {
			return "other", ""
		}
		if inputLower == "e" {
			return "exit", ""
		}

		// Try to parse as number
		if num, err := strconv.Atoi(input); err == nil {
			// Check if number is in range
			if len(files) == 0 {
				fmt.Print("No files available to select.\nChoice: ")
				continue
			}
			if num < 1 || num > len(files) {
				fmt.Printf("Invalid number. Enter 1-%d\nChoice: ", len(files))
				continue
			}
			return "selected", files[num-1]
		}

		// Invalid input
		fmt.Print("Invalid choice. Enter a number, S, O, or E.\nChoice: ")
	}
}

// PromptSearchDays prompts for the number of days to search back, with a default value.
// Returns the number of days (validated as positive integer).
func PromptSearchDays(defaultDays int) int {
	fmt.Printf("Search how many days back? [%d]: ", defaultDays)

	scanner := bufio.NewScanner(os.Stdin)
	if !scanner.Scan() {
		// EOF - use default
		return defaultDays
	}

	input := strings.TrimSpace(scanner.Text())

	// Empty input - use default
	if input == "" {
		return defaultDays
	}

	// Try to parse as integer
	days, err := strconv.Atoi(input)
	if err != nil || days <= 0 {
		fmt.Println("Invalid input. Using default.")
		return defaultDays
	}

	return days
}

// PromptCustomPath prompts for a custom file path and validates it exists.
func PromptCustomPath(fileType string) (string, error) {
	fmt.Printf("Enter path to %s file: ", fileType)

	scanner := bufio.NewScanner(os.Stdin)
	if !scanner.Scan() {
		return "", fmt.Errorf("no input provided")
	}

	path := strings.TrimSpace(scanner.Text())
	if path == "" {
		return "", fmt.Errorf("empty path provided")
	}

	// Check if file exists
	if _, err := os.Stat(path); err != nil {
		return "", fmt.Errorf("file not found: %s", path)
	}

	return path, nil
}

// PromptAutonomyMode displays implementation readiness info and prompts for autonomy mode.
// Returns the selected AutonomyMode (default is AutonomyCheckpoint).
func PromptAutonomyMode(phaseCount int, epicID string) AutonomyMode {
	fmt.Println("\n============================================================")
	fmt.Println("                   IMPLEMENTATION READY")
	fmt.Println("============================================================")
	fmt.Printf("Plan phases: %d\n", phaseCount)
	fmt.Printf("Beads epic: %s\n", epicID)
	fmt.Println()
	fmt.Println("Select autonomy mode:")
	fmt.Println("[C] Checkpoint - pause at each phase for review (recommended)")
	fmt.Println("[F] Fully autonomous - run all phases without stopping")
	fmt.Println("[B] Batch - run groups of phases, pause between groups")
	fmt.Print("Choice [C]: ")

	scanner := bufio.NewScanner(os.Stdin)
	for {
		if !scanner.Scan() {
			// EOF - default to checkpoint
			return AutonomyCheckpoint
		}

		input := strings.TrimSpace(strings.ToLower(scanner.Text()))

		// Empty input defaults to checkpoint
		if input == "" || input == "c" {
			return AutonomyCheckpoint
		}

		switch input {
		case "f":
			return AutonomyFullyAutonomous
		case "b":
			return AutonomyBatch
		default:
			fmt.Printf("Invalid choice: '%s'. Please enter C, F, or B.\nChoice [C]: ", input)
		}
	}
}
