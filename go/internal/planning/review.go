package planning

// ReviewConfig holds configuration for plan review.
type ReviewConfig struct {
	ProjectPath  string       `json:"project_path"`
	PlanPath     string       `json:"plan_path"`
	Phase        string       `json:"phase,omitempty"`
	Step         string       `json:"step,omitempty"`
	OutputPath   string       `json:"output_path,omitempty"`
	AutonomyMode AutonomyMode `json:"autonomy_mode"`
	AllPhases    bool         `json:"all_phases"`
}

// ReviewResult holds the result of a plan review.
type ReviewResult struct {
	Success  bool   `json:"success"`
	Output   string `json:"output,omitempty"`
	Error    string `json:"error,omitempty"`
	FailedAt string `json:"failed_at,omitempty"`
}

// RunReview executes a plan review with the given configuration.
func RunReview(config ReviewConfig) *ReviewResult {
	// TODO: Implement actual review logic in later phases
	// This is a stub for Phase 1 (CLI integration)
	return &ReviewResult{
		Success: true,
		Output:  "Review completed (stub implementation)",
	}
}
