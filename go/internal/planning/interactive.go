package planning

import (
	"fmt"
)

// Note: PromptResearchAction and CollectMultilineInput are now in prompts.go
// This file keeps PromptPlanningAction for backward compatibility

// PromptPlanningAction prompts user for planning checkpoint action.
//
// Displays a menu for the user to choose what to do after
// the planning phase completes.
//
// Returns a PhaseAction: ActionContinue, ActionRevise, ActionRestart, or ActionExit
func PromptPlanningAction() PhaseAction {
	fmt.Println("\n=== Planning Phase Complete ===")
	fmt.Println("[C] Continue to phase decomposition")
	fmt.Println("[R] Revise planning with additional context")
	fmt.Println("[S] Start over from research")
	fmt.Println("[E] Exit pipeline")
	fmt.Print("Choice: ")

	return readPhaseAction()
}
