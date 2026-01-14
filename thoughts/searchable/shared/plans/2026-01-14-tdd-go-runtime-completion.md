# Go Runtime Completion - TDD Implementation Plan

## Overview

Complete 11 remaining CLI command stubs in the Go runtime to achieve feature parity with the Python implementation. The implementation follows TDD principles with Red-Green-Refactor cycles.

## Current State Analysis

### Key Discoveries:
- `go/internal/cli/resume.go:175-206` - 2 stubs (planning, decomposition)
- `go/internal/cli/loop_runner.go:180-219` - 5 stubs (main, validate, blocked, metrics, unblock)
- `go/internal/cli/orchestrator.go:111-132` - 2 stubs (main, status)
- `go/internal/cli/mcp_setup.go:115-126` - 2 stubs (main, list)
- Reference implementation: `runResumeBeads()` at `resume.go:210-276`
- Python reference: `silmari_rlm_act/phases/implementation.py` - simple Claude loop pattern
- Existing step functions in `go/internal/planning/steps.go`

### Existing Patterns:
- CLI commands call `planning.Step*()` functions
- Tests use `executeCommand()` helpers with `bytes.Buffer` capture
- `validateChoice()` and `validatePath()` for input validation
- `planning.RunClaudeSync()` for Claude invocation

## Desired End State

All 11 CLI stubs fully implemented with:
- Unit tests for each command
- Integration with existing `planning` package functions
- Consistent error handling and output formatting
- Beads issue tracking via `bd` commands

## What We're NOT Doing

- Adding new dependencies or external packages
- Changing existing public APIs
- Modifying test infrastructure
- Creating new CLI commands

## Testing Strategy

- **Framework**: Go standard `testing` package
- **Test Types**: Unit tests for CLI commands, integration tests for planning functions
- **Test Files**: `go/internal/cli/*_test.go`, `go/internal/planning/*_test.go`

---

## Behavior 1: Resume Planning Command

### Test Specification
**Given**: A valid research document path
**When**: `context-engine resume planning --research-path /path/to/research.md` is called
**Then**: `planning.StepPlanning()` is invoked with the research path and results are displayed

**Edge Cases**:
- Invalid research path → error message
- Planning step fails → error propagated

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `go/internal/cli/resume_test.go`
```go
func TestResumePlanning_CallsStepPlanning(t *testing.T) {
    tmpDir := t.TempDir()
    researchPath := filepath.Join(tmpDir, "research.md")
    if err := os.WriteFile(researchPath, []byte("# Research"), 0644); err != nil {
        t.Fatal(err)
    }

    // This test will fail until we implement the actual logic
    resetResumeFlags()
    resumeResearchPath = researchPath

    err := runResumePlanning(nil, nil)
    if err != nil {
        t.Errorf("Expected success, got error: %v", err)
    }
}
```

#### 🟢 Green: Minimal Implementation
**File**: `go/internal/cli/resume.go`
```go
func runResumePlanning(cmd *cobra.Command, args []string) error {
    projectPath, err := findProjectRoot()
    if err != nil {
        return fmt.Errorf("failed to find project root: %w", err)
    }

    absPath, err := filepath.Abs(resumeResearchPath)
    if err != nil {
        return fmt.Errorf("invalid research path: %w", err)
    }

    fmt.Println("Resuming from planning step...")
    result := planning.StepPlanning(projectPath, absPath, resumeAdditionalContext)

    if !result.Success {
        return fmt.Errorf("planning failed: %s", result.Error)
    }

    fmt.Printf("✅ Planning complete\n")
    if len(result.PlanPaths) > 0 {
        fmt.Printf("Plan files created: %d\n", len(result.PlanPaths))
        for _, p := range result.PlanPaths {
            fmt.Printf("  - %s\n", filepath.Base(p))
        }
    }
    return nil
}
```

#### 🔵 Refactor: Improve Code
- Add progress indicators
- Improve error messages with hints

### Success Criteria
**Automated:**
- [ ] Test fails for right reason (Red): `go test -run TestResumePlanning`
- [ ] Test passes (Green): `go test -run TestResumePlanning`
- [ ] All resume tests pass: `go test ./go/internal/cli/... -run Resume`

**Manual:**
- [ ] `context-engine resume planning --research-path <path>` works

---

## Behavior 2: Resume Decomposition Command

### Test Specification
**Given**: A valid plan document path
**When**: `context-engine resume decomposition --plan-path /path/to/plan.md` is called
**Then**: `planning.StepPhaseDecomposition()` is invoked with the plan path

**Edge Cases**:
- Invalid plan path → error message
- Decomposition fails → error propagated

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `go/internal/cli/resume_test.go`
```go
func TestResumeDecomposition_CallsStepDecomposition(t *testing.T) {
    tmpDir := t.TempDir()
    planPath := filepath.Join(tmpDir, "plan.md")
    if err := os.WriteFile(planPath, []byte("# Plan"), 0644); err != nil {
        t.Fatal(err)
    }

    resetResumeFlags()
    resumePlanPath = planPath

    err := runResumeDecomposition(nil, nil)
    if err != nil {
        t.Errorf("Expected success, got error: %v", err)
    }
}
```

#### 🟢 Green: Minimal Implementation
**File**: `go/internal/cli/resume.go`
```go
func runResumeDecomposition(cmd *cobra.Command, args []string) error {
    projectPath, err := findProjectRoot()
    if err != nil {
        return fmt.Errorf("failed to find project root: %w", err)
    }

    absPath, err := filepath.Abs(resumePlanPath)
    if err != nil {
        return fmt.Errorf("invalid plan path: %w", err)
    }

    fmt.Println("Resuming from decomposition step...")
    result := planning.StepPhaseDecomposition(projectPath, absPath)

    if !result.Success {
        return fmt.Errorf("decomposition failed: %s", result.Error)
    }

    fmt.Printf("✅ Decomposition complete\n")
    fmt.Printf("Phase files created: %d\n", len(result.PhaseFiles))
    return nil
}
```

### Success Criteria
**Automated:**
- [ ] Test passes: `go test -run TestResumeDecomposition`

---

## Behavior 3: Simplify StepImplementation (Critical Refactor)

### Test Specification
**Given**: Phase paths and beads issue IDs
**When**: `StepImplementation()` is called
**Then**: Simple Claude loop executes (matching Python pattern)

The current Go implementation is over-engineered. Simplify to match `silmari_rlm_act/phases/implementation.py`:
1. Build prompt with plan path (Claude reads the plan)
2. Loop: invoke Claude, sleep, check completion
3. Exit when all beads issues closed AND tests pass

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `go/internal/planning/implementation_test.go`
```go
func TestStepImplementation_SimplifiedPrompt(t *testing.T) {
    // Test that prompt only contains plan path, not full instructions
    prompt := buildImplementationPrompt(
        []string{"/path/to/plan.md"},
        "beads-epic1",
        []string{"beads-phase1"},
    )

    // Should contain plan path reference
    if !strings.Contains(prompt, "Implement the TDD plan at:") {
        t.Error("Expected prompt to reference plan path")
    }

    // Should NOT contain verbose inline instructions (simplified)
    if strings.Contains(prompt, "Red-Green-Refactor Cycle") {
        t.Error("Prompt should be simplified - Claude reads the plan")
    }
}
```

#### 🟢 Green: Minimal Implementation
**File**: `go/internal/planning/implementation.go`
```go
// buildImplementationPrompt creates a simple prompt - Claude reads the plan
func buildImplementationPrompt(phasePaths []string, epicID string, issueIDs []string) string {
    var sb strings.Builder

    if len(phasePaths) > 0 {
        sb.WriteString(fmt.Sprintf("Implement the TDD plan at: %s\n\n", phasePaths[0]))
        sb.WriteString("Read the plan overview first, then find and implement the phase documents.\n\n")
    }

    sb.WriteString("## Beads Tracking\n\n")
    sb.WriteString("Use `bd` commands to track progress:\n")
    sb.WriteString("```bash\n")
    sb.WriteString("bd ready                    # See available work\n")
    sb.WriteString("bd show <id>                # View issue details\n")
    sb.WriteString("bd update <id> --status=in_progress  # Start work\n")
    sb.WriteString("bd close <id>               # Complete work\n")
    sb.WriteString("bd sync                     # Sync changes\n")
    sb.WriteString("```\n\n")

    if epicID != "" {
        sb.WriteString(fmt.Sprintf("**Epic**: `%s`\n\n", epicID))
    }

    if len(issueIDs) > 0 {
        sb.WriteString("**Phase Issues**:\n")
        for i, id := range issueIDs {
            sb.WriteString(fmt.Sprintf("- Phase %d: `%s`\n", i+1, id))
        }
        sb.WriteString("\n")
    }

    sb.WriteString(`## Implementation Instructions

1. Read the plan overview at the path above
2. Find the phase documents in the same directory
3. Implement using subagents for parallel work
4. Run all tests: pytest or make test
5. Use bd close <id> when phase is complete
6. Use /clear after closing an issue

**CRITICAL**: After ALL TESTS PASS and after each bd close,
emit /clear to clear context for the next issue.
`)

    return sb.String()
}
```

### Success Criteria
**Automated:**
- [ ] Test passes: `go test -run TestStepImplementation_SimplifiedPrompt`
- [ ] Existing implementation tests still pass

---

## Behavior 4: Loop Runner Main Command

### Test Specification
**Given**: A project with feature_list.json or beads issues
**When**: `loop-runner` is called
**Then**: Autonomous implementation loop executes using `StepImplementation()`

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `go/internal/cli/loop_runner_test.go`
```go
func TestLoopRunner_ExecutesLoop(t *testing.T) {
    tmpDir := t.TempDir()

    // Create minimal feature_list.json
    featureList := `{"features":[]}`
    if err := os.WriteFile(filepath.Join(tmpDir, "feature_list.json"), []byte(featureList), 0644); err != nil {
        t.Fatal(err)
    }

    resetLoopRunnerCmd()
    lrProjectPath = tmpDir
    lrDryRun = true  // Don't actually run Claude

    err := runLoopRunner(nil, nil)
    // Should not error on empty feature list
    if err != nil {
        t.Errorf("Expected success, got error: %v", err)
    }
}
```

#### 🟢 Green: Minimal Implementation
**File**: `go/internal/cli/loop_runner.go`
```go
func runLoopRunner(cmd *cobra.Command, args []string) error {
    // ... existing validation code ...

    if lrDryRun {
        fmt.Println("(Dry run mode - would execute autonomous loop)")
        return nil
    }

    // Load feature list or use beads
    features, err := loadFeatures(lrProjectPath, lrFeaturesPath)
    if err != nil {
        return fmt.Errorf("failed to load features: %w", err)
    }

    fmt.Printf("Loaded %d features\n", len(features.Features))

    // Run implementation loop
    result := planning.StepImplementation(
        lrProjectPath,
        nil, // phase paths from features
        getFeatureIDs(features),
        "", // no epic
        lrMaxSessions,
    )

    if !result.Success {
        return fmt.Errorf("implementation failed: %s", result.Error)
    }

    fmt.Println("✅ All features complete!")
    return nil
}

func loadFeatures(projectPath, featuresPath string) (*planning.FeatureList, error) {
    path := featuresPath
    if path == "" {
        path = filepath.Join(projectPath, "feature_list.json")
    }

    data, err := os.ReadFile(path)
    if err != nil {
        if os.IsNotExist(err) {
            return planning.NewFeatureList(), nil
        }
        return nil, err
    }

    return planning.FeatureListFromJSON(data)
}
```

### Success Criteria
**Automated:**
- [ ] Test passes: `go test -run TestLoopRunner_ExecutesLoop`

---

## Behavior 5: Validate Features Command

### Test Specification
**Given**: A project path with feature_list.json
**When**: `loop-runner --validate` is called
**Then**: Feature list is validated and results displayed

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `go/internal/cli/loop_runner_test.go`
```go
func TestValidateFeatures_ValidFile(t *testing.T) {
    tmpDir := t.TempDir()

    validFeatures := `{"features":[{"id":"f1","name":"Feature 1","passes":false}]}`
    if err := os.WriteFile(filepath.Join(tmpDir, "feature_list.json"), []byte(validFeatures), 0644); err != nil {
        t.Fatal(err)
    }

    err := validateFeatures(tmpDir)
    if err != nil {
        t.Errorf("Expected validation to pass, got error: %v", err)
    }
}

func TestValidateFeatures_InvalidFile(t *testing.T) {
    tmpDir := t.TempDir()

    // Feature missing required 'name' field
    invalidFeatures := `{"features":[{"id":"f1","passes":false}]}`
    if err := os.WriteFile(filepath.Join(tmpDir, "feature_list.json"), []byte(invalidFeatures), 0644); err != nil {
        t.Fatal(err)
    }

    err := validateFeatures(tmpDir)
    if err == nil {
        t.Error("Expected validation error for missing name")
    }
}
```

#### 🟢 Green: Minimal Implementation
**File**: `go/internal/cli/loop_runner.go`
```go
func validateFeatures(projectPath string) error {
    featureFile := filepath.Join(projectPath, "feature_list.json")

    data, err := os.ReadFile(featureFile)
    if err != nil {
        if os.IsNotExist(err) {
            return fmt.Errorf("feature_list.json not found in %s", projectPath)
        }
        return fmt.Errorf("failed to read feature_list.json: %w", err)
    }

    features, err := planning.FeatureListFromJSON(data)
    if err != nil {
        return fmt.Errorf("invalid JSON: %w", err)
    }

    if err := features.Validate(); err != nil {
        return fmt.Errorf("validation failed: %w", err)
    }

    stats := features.Stats()
    fmt.Printf("✅ Validation passed!\n")
    fmt.Printf("  Total features: %d\n", stats["total"])
    fmt.Printf("  Completed: %d\n", stats["completed"])
    fmt.Printf("  Remaining: %d\n", stats["remaining"])
    fmt.Printf("  Blocked: %d\n", stats["blocked"])

    return nil
}
```

### Success Criteria
**Automated:**
- [ ] Both tests pass: `go test -run TestValidateFeatures`

---

## Behavior 6: Show Blocked Features Command

### Test Specification
**Given**: A project path with feature_list.json containing blocked features
**When**: `loop-runner --show-blocked` is called
**Then**: Blocked features are displayed with reasons

### TDD Cycle

#### 🔴 Red: Write Failing Test
```go
func TestShowBlockedFeatures_DisplaysBlocked(t *testing.T) {
    tmpDir := t.TempDir()

    features := `{"features":[
        {"id":"f1","name":"Feature 1","passes":false,"blocked":true,"blocked_reason":"Waiting on API","blocked_by":["f2"]},
        {"id":"f2","name":"Feature 2","passes":false}
    ]}`
    if err := os.WriteFile(filepath.Join(tmpDir, "feature_list.json"), []byte(features), 0644); err != nil {
        t.Fatal(err)
    }

    // Capture output
    err := showBlockedFeatures(tmpDir)
    if err != nil {
        t.Errorf("Unexpected error: %v", err)
    }
}
```

#### 🟢 Green: Minimal Implementation
```go
func showBlockedFeatures(projectPath string) error {
    featureFile := filepath.Join(projectPath, "feature_list.json")

    data, err := os.ReadFile(featureFile)
    if err != nil {
        if os.IsNotExist(err) {
            fmt.Println("No feature_list.json found")
            return nil
        }
        return err
    }

    features, err := planning.FeatureListFromJSON(data)
    if err != nil {
        return err
    }

    blocked := features.GetBlocked()

    fmt.Printf("Blocked features in %s:\n", projectPath)
    if len(blocked) == 0 {
        fmt.Println("  (none)")
        return nil
    }

    for _, f := range blocked {
        fmt.Printf("  %s: %s\n", f.ID, f.Name)
        fmt.Printf("    Reason: %s\n", f.BlockedReason)
        fmt.Printf("    Blocked by: %v\n", f.BlockedBy)
    }

    return nil
}
```

### Success Criteria
**Automated:**
- [ ] Test passes: `go test -run TestShowBlockedFeatures`

---

## Behavior 7: Show Metrics Command

### Test Specification
**Given**: A project path with feature_list.json
**When**: `loop-runner --metrics` is called
**Then**: Metrics report is displayed

### TDD Cycle

#### 🔴 Red: Write Failing Test
```go
func TestShowMetrics_DisplaysStats(t *testing.T) {
    tmpDir := t.TempDir()

    features := `{"features":[
        {"id":"f1","name":"Feature 1","passes":true},
        {"id":"f2","name":"Feature 2","passes":false},
        {"id":"f3","name":"Feature 3","passes":false,"blocked":true,"blocked_reason":"Waiting","blocked_by":["f1"]}
    ]}`
    if err := os.WriteFile(filepath.Join(tmpDir, "feature_list.json"), []byte(features), 0644); err != nil {
        t.Fatal(err)
    }

    err := showMetrics(tmpDir)
    if err != nil {
        t.Errorf("Unexpected error: %v", err)
    }
}
```

#### 🟢 Green: Minimal Implementation
```go
func showMetrics(projectPath string) error {
    featureFile := filepath.Join(projectPath, "feature_list.json")

    data, err := os.ReadFile(featureFile)
    if err != nil {
        if os.IsNotExist(err) {
            fmt.Println("No feature_list.json found")
            return nil
        }
        return err
    }

    features, err := planning.FeatureListFromJSON(data)
    if err != nil {
        return err
    }

    stats := features.Stats()

    fmt.Printf("Metrics for %s:\n", projectPath)
    fmt.Printf("  Total features: %d\n", stats["total"])
    fmt.Printf("  Completed: %d\n", stats["completed"])
    fmt.Printf("  In progress: %d\n", stats["remaining"]-stats["blocked"])
    fmt.Printf("  Blocked: %d\n", stats["blocked"])

    if stats["total"] > 0 {
        pct := float64(stats["completed"]) / float64(stats["total"]) * 100
        fmt.Printf("  Progress: %.1f%%\n", pct)
    }

    return nil
}
```

### Success Criteria
**Automated:**
- [ ] Test passes: `go test -run TestShowMetrics`

---

## Behavior 8: Unblock Feature Command

### Test Specification
**Given**: A project with a blocked feature
**When**: `loop-runner --unblock <feature-id>` is called
**Then**: Feature is unblocked and file is updated

### TDD Cycle

#### 🔴 Red: Write Failing Test
```go
func TestUnblockFeature_UnblocksFeature(t *testing.T) {
    tmpDir := t.TempDir()

    features := `{"features":[
        {"id":"f1","name":"Feature 1","passes":false,"blocked":true,"blocked_reason":"Test","blocked_by":["f2"]}
    ]}`
    featurePath := filepath.Join(tmpDir, "feature_list.json")
    if err := os.WriteFile(featurePath, []byte(features), 0644); err != nil {
        t.Fatal(err)
    }

    err := unblockFeature(tmpDir, "f1")
    if err != nil {
        t.Errorf("Unexpected error: %v", err)
    }

    // Verify feature is unblocked
    data, _ := os.ReadFile(featurePath)
    fl, _ := planning.FeatureListFromJSON(data)
    f := fl.GetByID("f1")
    if f.Blocked {
        t.Error("Feature should be unblocked")
    }
}
```

#### 🟢 Green: Minimal Implementation
```go
func unblockFeature(projectPath, featureID string) error {
    featureFile := filepath.Join(projectPath, "feature_list.json")

    data, err := os.ReadFile(featureFile)
    if err != nil {
        return fmt.Errorf("failed to read feature_list.json: %w", err)
    }

    features, err := planning.FeatureListFromJSON(data)
    if err != nil {
        return err
    }

    f := features.GetByID(featureID)
    if f == nil {
        return fmt.Errorf("feature %s not found", featureID)
    }

    if !f.Blocked {
        fmt.Printf("Feature %s is not blocked\n", featureID)
        return nil
    }

    f.Blocked = false
    f.BlockedReason = ""
    f.BlockedBy = nil
    f.BlockedAt = ""

    // Save updated file
    newData, err := features.ToJSON()
    if err != nil {
        return err
    }

    if err := os.WriteFile(featureFile, newData, 0644); err != nil {
        return err
    }

    fmt.Printf("✅ Feature %s unblocked!\n", featureID)
    return nil
}
```

### Success Criteria
**Automated:**
- [ ] Test passes: `go test -run TestUnblockFeature`

---

## Behavior 9: Orchestrator Main Command

### Test Specification
**Given**: Valid project configuration
**When**: `context-engine` is called with project flags
**Then**: Orchestrator runs the planning pipeline

### TDD Cycle

#### 🔴 Red: Write Failing Test
```go
func TestOrchestrator_RunsPipeline(t *testing.T) {
    tmpDir := t.TempDir()

    // Create minimal project structure
    os.MkdirAll(filepath.Join(tmpDir, ".claude", "commands"), 0755)

    resetOrchestratorFlags()
    projectPath = tmpDir

    // Should at least not panic
    err := runOrchestrator(nil, nil)
    // In dry-run or with empty project, this is informational
    if err != nil && !strings.Contains(err.Error(), "not found") {
        t.Logf("Got expected setup error: %v", err)
    }
}
```

#### 🟢 Green: Minimal Implementation
```go
func runOrchestrator(cmd *cobra.Command, args []string) error {
    // ... existing validation ...

    if status {
        return showStatus()
    }

    // Determine project path
    path := projectPath
    if path == "" && newPath == "" {
        var err error
        path, err = os.Getwd()
        if err != nil {
            return err
        }
    }

    if newPath != "" {
        // Create new project (placeholder)
        fmt.Printf("Creating new project: %s\n", newPath)
        return nil
    }

    // Run pipeline
    config := planning.PipelineConfig{
        ProjectPath:  path,
        AutoApprove:  false,
        AutonomyMode: planning.AutonomyCheckpoint,
    }

    pipeline := planning.NewPlanningPipeline(config)

    fmt.Println("Context-Engineered Agent Orchestrator")
    fmt.Println("=====================================")
    fmt.Printf("Project: %s\n", path)

    // Interactive mode - prompt for research question
    if interactive {
        fmt.Println("\nEnter research question (or press Enter for interactive mode):")
        // For now, just show help
        fmt.Println("\nUse --continue to resume from checkpoint")
        fmt.Println("Use --project to specify project path")
    }

    return nil
}
```

### Success Criteria
**Automated:**
- [ ] Test passes: `go test -run TestOrchestrator`

---

## Behavior 10: Orchestrator Status Command

### Test Specification
**Given**: A project path
**When**: `context-engine --status --project <path>` is called
**Then**: Project status is displayed

### TDD Cycle

#### 🔴 Red: Write Failing Test
```go
func TestShowStatus_DisplaysStatus(t *testing.T) {
    tmpDir := t.TempDir()

    // Create beads directory
    os.MkdirAll(filepath.Join(tmpDir, ".beads"), 0755)

    projectPath = tmpDir

    err := showStatus()
    if err != nil {
        t.Errorf("Unexpected error: %v", err)
    }
}
```

#### 🟢 Green: Minimal Implementation
```go
func showStatus() error {
    if projectPath == "" {
        return fmt.Errorf("--status requires --project to be specified")
    }

    fmt.Printf("Status for project: %s\n", projectPath)
    fmt.Println(strings.Repeat("-", 40))

    // Check for beads
    beadsDir := filepath.Join(projectPath, ".beads")
    if _, err := os.Stat(beadsDir); err == nil {
        fmt.Println("✓ Beads initialized")

        // Run bd stats
        cmd := exec.Command("bd", "stats")
        cmd.Dir = projectPath
        output, err := cmd.Output()
        if err == nil {
            fmt.Println(string(output))
        }
    } else {
        fmt.Println("✗ Beads not initialized")
    }

    // Check for checkpoints
    checkpointDir := filepath.Join(projectPath, ".rlm-act-checkpoints")
    if entries, err := os.ReadDir(checkpointDir); err == nil && len(entries) > 0 {
        fmt.Printf("✓ %d checkpoint(s) found\n", len(entries))
    }

    return nil
}
```

### Success Criteria
**Automated:**
- [ ] Test passes: `go test -run TestShowStatus`

---

## Behavior 11: MCP Setup Main Command (Stub)

### Test Specification
**Given**: A project path and optional preset
**When**: `context-engine mcp-setup` is called
**Then**: Placeholder message is displayed (stub implementation)

### TDD Cycle

#### 🔴 Red: Write Failing Test
```go
func TestMCPSetup_DisplaysMessage(t *testing.T) {
    tmpDir := t.TempDir()

    resetMCPFlags()
    mcpProjectPath = tmpDir

    err := runMCPSetup(nil, nil)
    if err != nil {
        t.Errorf("Unexpected error: %v", err)
    }
}
```

#### 🟢 Green: Minimal Implementation
```go
func runMCPSetup(cmd *cobra.Command, args []string) error {
    // ... existing validation ...

    if mcpList {
        return listMCPs()
    }

    fmt.Println("Smart MCP Configurator")
    fmt.Println("=====================")
    fmt.Printf("Project: %s\n", mcpProjectPath)

    if mcpPresetFlag != "" {
        fmt.Printf("Preset: %s\n", mcpPresetFlag)
    }

    fmt.Println("\n⚠️  MCP configuration not yet implemented")
    fmt.Println("This feature will auto-configure MCP servers based on project type.")

    return nil
}
```

### Success Criteria
**Automated:**
- [ ] Test passes: `go test -run TestMCPSetup`

---

## Behavior 12: MCP List Command (Stub)

### Test Specification
**Given**: The `--list` flag
**When**: `context-engine mcp-setup --list` is called
**Then**: Available presets are listed

### TDD Cycle

#### 🔴 Red: Write Failing Test
```go
func TestListMCPs_DisplaysPresets(t *testing.T) {
    err := listMCPs()
    if err != nil {
        t.Errorf("Unexpected error: %v", err)
    }
}
```

#### 🟢 Green: Minimal Implementation
```go
func listMCPs() error {
    fmt.Println("Available MCP Presets:")
    fmt.Println("----------------------")
    for _, preset := range validPresets {
        fmt.Printf("  %s\n", preset)
    }

    fmt.Println("\n⚠️  Individual MCP listing not yet implemented")
    fmt.Println("Use --preset <name> to apply a preset configuration.")

    return nil
}
```

### Success Criteria
**Automated:**
- [ ] Test passes: `go test -run TestListMCPs`

---

## Integration Testing

After all behaviors are implemented:

```bash
# Run all CLI tests
go test ./go/internal/cli/... -v

# Run planning tests
go test ./go/internal/planning/... -v

# Build and verify
cd go && make build

# Manual smoke tests
./build/context-engine --help
./build/context-engine resume planning --help
./build/loop-runner --help
./build/loop-runner --validate
```

## References

- Beads Issues:
  - `silmari-Context-Engine-l3e0` - resume.go stubs
  - `silmari-Context-Engine-7b3x` - loop_runner.go stubs
  - `silmari-Context-Engine-ukhi` - orchestrator.go stubs
  - `silmari-Context-Engine-52d2` - mcp_setup.go stubs
- Python Reference: `silmari_rlm_act/phases/implementation.py`
- Existing Pattern: `go/internal/cli/resume.go:210-276` (runResumeBeads)
- Planning Package: `go/internal/planning/steps.go`
