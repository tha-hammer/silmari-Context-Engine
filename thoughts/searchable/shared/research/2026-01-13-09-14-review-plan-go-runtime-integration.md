---
date: 2026-01-13T09:14:22-05:00
researcher: Claude Opus 4.5
git_commit: 63cf888a167720d0fd082e55f1b0dba64c21629a
branch: main
repository: silmari-Context-Engine
topic: "Incorporating review_plan Command into Go Runtime with Nested Dependency Handling"
tags: [research, review_plan, go-runtime, dependencies, phases, loops]
status: complete
last_updated: 2026-01-13
last_updated_by: Claude Opus 4.5
---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SILMARI CONTEXT ENGINE RESEARCH                          │
│          Review Plan Go Runtime Integration with Dependency Handling        │
│                                                                             │
│  Status: ✅ Complete                         Date: 2026-01-13               │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Research: Incorporating review_plan Command into Go Runtime

**Date**: 2026-01-13T09:14:22-05:00
**Researcher**: Claude Opus 4.5
**Git Commit**: 63cf888a167720d0fd082e55f1b0dba64c21629a
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📚 Research Question

Research how to incorporate the 'review_plan' command into the Go runtime. Research how to break the review into discrete steps and to apply each step to each phase of the plan. Because plans have nested and looped dependencies, the research needs to think deeply about the proper structure of the loop to address these nested and looped dependencies.

---

## 📊 Summary

The `review_plan` command is currently implemented as a prompt template (`.claude/commands/review_plan.md`) that performs a 5-category architectural review. To incorporate it into the Go runtime, the implementation can follow the established Cobra CLI command pattern used by existing commands (`plan`, `resume`, `mcp-setup`).

The review process naturally breaks into **5 discrete analysis steps** (Contracts, Interfaces, Promises, Data Models, APIs), each of which can be applied to each phase of a plan. Plans have **sequential phase dependencies** (Phase N depends on Phase N-1) and **hierarchical requirement dependencies** (3-tier parent→sub_process→implementation). The existing codebase provides patterns for both sequential iteration and recursive tree traversal that can handle these nested structures.

---

## 🎯 Detailed Findings

### 1. Current review_plan Command Implementation

| Attribute | Value |
|-----------|-------|
| **Location** | `.claude/commands/review_plan.md` |
| **Copies** | `.cursor/commands/`, `silmari_rlm_act/commands/` |
| **File Size** | 10,703 bytes |
| **Type** | Prompt template (not executable code) |
| **Checksum** | `1cb1c284c7d8f8297593f9ddf6e3b329` |

**Purpose**: Pre-implementation architectural review that catches design gaps before code is written.

#### 5-Step Review Framework

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        REVIEW ANALYSIS STEPS                             │
├──────────────────────────────────────────────────────────────────────────┤
│  Step 1: CONTRACT ANALYSIS                                               │
│  ├── Component boundaries                                                │
│  ├── Input/output contracts                                              │
│  ├── Error contracts                                                     │
│  └── Preconditions/postconditions/invariants                             │
├──────────────────────────────────────────────────────────────────────────┤
│  Step 2: INTERFACE ANALYSIS                                              │
│  ├── Public method definitions                                           │
│  ├── Naming convention consistency                                       │
│  ├── Interface evolution/extension points                                │
│  └── Visibility modifiers                                                │
├──────────────────────────────────────────────────────────────────────────┤
│  Step 3: PROMISE ANALYSIS                                                │
│  ├── Behavioral guarantees (idempotency, ordering)                       │
│  ├── Async/concurrent operations                                         │
│  ├── Timeout/cancellation handling                                       │
│  └── Resource cleanup (RAII patterns)                                    │
├──────────────────────────────────────────────────────────────────────────┤
│  Step 4: DATA MODEL ANALYSIS                                             │
│  ├── Field definitions with types                                        │
│  ├── Optional vs required clarity                                        │
│  ├── Relationships (1:1, 1:N, N:M)                                       │
│  └── Migration/backward compatibility                                    │
├──────────────────────────────────────────────────────────────────────────┤
│  Step 5: API ANALYSIS                                                    │
│  ├── Endpoint/method definitions                                         │
│  ├── Request/response formats                                            │
│  ├── Error responses/status codes                                        │
│  └── Versioning/deprecation policies                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Severity Levels

| Level | Symbol | Meaning |
|-------|--------|---------|
| Well-Defined | ✅ | No action needed |
| Warning | ⚠️ | Should be addressed, not blocking |
| Critical | ❌ | Must be resolved before implementation |

---

### 2. Go Runtime Structure for Command Integration

#### Entry Point Pattern

**File**: `go/internal/cli/root.go`

```go
// Root command (lines 24-39)
var rootCmd = &cobra.Command{
    Use:     "context-engine",
    Short:   "Context-Engineered Agent Orchestrator",
    RunE:    runOrchestrator,
    Version: fmt.Sprintf("%s (commit: %s, built: %s)", Version, GitCommit, BuildDate),
}

// Execute function (lines 42-44)
func Execute() error {
    return rootCmd.Execute()
}
```

#### Command Registration Pattern

**File**: `go/internal/cli/root.go` (lines 46-58)

```go
func init() {
    // Global persistent flags
    rootCmd.PersistentFlags().BoolVarP(&debug, "debug", "d", false, "Show debug output")
    rootCmd.PersistentFlags().BoolVarP(&verbose, "verbose", "v", false, "Verbose output")

    // Add subcommands
    rootCmd.AddCommand(planCmd)
    rootCmd.AddCommand(mcpSetupCmd)
    rootCmd.AddCommand(resumeCmd)

    rootCmd.SetUsageTemplate(usageTemplate)
}
```

#### Existing Command Implementation Pattern (Plan Command)

**File**: `go/internal/cli/plan.go` (lines 28-159)

```go
var planCmd = &cobra.Command{
    Use:     "plan",
    Aliases: []string{"p"},
    Short:   "Create TDD implementation plan",
    RunE:    runPlan,
}

func runPlan(cmd *cobra.Command, args []string) error {
    // 1. Parameter validation
    // 2. Path normalization
    // 3. Debug output
    // 4. Create config struct
    // 5. Call planning package function
    // 6. Handle results
    // 7. Return error or nil
}
```

#### Registered Commands

| Command | File | Handler | Purpose |
|---------|------|---------|---------|
| `plan` | `plan.go` | `runPlan()` | Create TDD implementation plan |
| `resume` | `resume.go` | Multi-handlers | Resume from checkpoint |
| `mcp-setup` | `mcp_setup.go` | `runMCPSetup()` | Configure MCP servers |
| `(default)` | `orchestrator.go` | `runOrchestrator()` | Main orchestration |

---

### 3. Plan Structure and Phase Dependencies

#### Phase Type Enumeration

**File**: `go/internal/planning/models.go` (lines 509-608)

```go
type PhaseType int

const (
    PhaseResearch PhaseType = iota          // 0
    PhaseDecomposition                       // 1
    PhaseTDDPlanning                         // 2
    PhaseMultiDoc                            // 3
    PhaseBeadsSync                           // 4
    PhaseImplementation                      // 5
)
```

#### Sequential Phase Dependencies

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PHASE EXECUTION ORDER                               │
│                                                                         │
│  Research → Decomposition → TDD_Planning → Multi_Doc → Beads_Sync →    │
│                                                                         │
│                         → Implementation                                │
│                                                                         │
│  Each phase depends on the previous phase completing successfully       │
└─────────────────────────────────────────────────────────────────────────┘
```

**Navigation Methods** (`models.go` lines 561-575):
- `Next() (PhaseType, error)` - Returns next phase in sequence
- `Previous() (PhaseType, error)` - Returns previous phase

#### Phase Status State Machine

**File**: `go/internal/planning/models.go` (lines 610-692)

```go
type PhaseStatus int

const (
    StatusPending PhaseStatus = iota    // Not yet started
    StatusInProgress                    // Currently executing
    StatusComplete                      // Successfully finished
    StatusFailed                        // Encountered errors
)
```

**Valid Transitions**:
```
pending → in_progress (start)
in_progress → complete (success)
in_progress → failed (error)
failed → in_progress (retry)
complete → (terminal, no transitions)
```

#### Hierarchical Requirement Dependencies (3-Tier)

**File**: `go/internal/planning/models.go` (lines 61-115)

```go
type RequirementNode struct {
    ID                 string                // e.g., "REQ_000", "REQ_000.1", "REQ_000.1.1"
    Description        string
    Type               string                // "parent", "sub_process", "implementation"
    ParentID           string                // Reference to parent
    Children           []*RequirementNode    // Child nodes (recursive)
    AcceptanceCriteria []string
    Implementation     *ImplementationComponents
    TestableProperties []*TestableProperty
    // ...
}
```

**Hierarchy Structure**:
```
parent (REQ_000)
  ├─ sub_process (REQ_000.1)
  │   ├─ implementation (REQ_000.1.1)
  │   └─ implementation (REQ_000.1.2)
  └─ sub_process (REQ_000.2)
      └─ implementation (REQ_000.2.1)
```

---

### 4. Nested and Looped Dependency Handling Patterns

#### Pattern 1: Sequential Phase Iteration

**File**: `go/internal/planning/models.go` (lines 598-608)

```go
func AllPhases() []PhaseType {
    return []PhaseType{
        PhaseResearch,
        PhaseDecomposition,
        PhaseTDDPlanning,
        PhaseMultiDoc,
        PhaseBeadsSync,
        PhaseImplementation,
    }
}
```

**Usage for Review Loop**:
```go
// Apply each review step to each phase
for _, phase := range AllPhases() {
    for _, reviewStep := range []string{"contracts", "interfaces", "promises", "data_models", "apis"} {
        result := runReviewStep(phase, reviewStep)
        // Collect results...
    }
}
```

#### Pattern 2: Recursive Tree Traversal

**File**: `go/internal/planning/models.go` (lines 103-114)

```go
func (r *RequirementNode) GetByID(id string) *RequirementNode {
    if r.ID == id {
        return r
    }
    for _, child := range r.Children {
        if found := child.GetByID(id); found != nil {
            return found
        }
    }
    return nil
}
```

**Usage for Nested Requirement Review**:
```go
// Recursively review all requirements
func reviewRequirementTree(node *RequirementNode, step string) []ReviewFinding {
    findings := reviewNode(node, step)
    for _, child := range node.Children {
        findings = append(findings, reviewRequirementTree(child, step)...)
    }
    return findings
}
```

#### Pattern 3: Linear Dependency Chain (Beads)

**File**: `go/internal/planning/steps.go` (lines 550-557)

```go
var prevIssueID string
for i, phaseFile := range actualPhaseFiles {
    issueID := extractBeadsID(...)

    // Link dependency to previous phase (linear chain)
    if prevIssueID != "" && issueID != "" {
        cmd := exec.Command("bd", "dep", "add", issueID, prevIssueID)
        cmd.Run()
    }
    prevIssueID = issueID
}
```

#### Pattern 4: Implementation Loop with Closure Check

**File**: `go/internal/planning/implementation.go` (lines 70-120)

```go
for i := 0; i < maxIterations; i++ {
    result.Iterations = i + 1

    // Invoke Claude with implementation prompt
    claudeResult := RunClaudeSync(prompt, IMPL_TIMEOUT, true, projectPath)

    // Check if all beads issues are closed
    allClosed, closedIssues := checkAllIssuesClosed(projectPath, beadsIssueIDs)

    if allClosed {
        testsPassed, testOutput := runTests(projectPath)
        if testsPassed {
            result.Success = true
            return result
        }
        // Update prompt with test failures for next iteration
    }
}
```

#### Pattern 5: Blocking Detection

**File**: `planning_pipeline/integrated_orchestrator.py` (lines 84-93)

```python
open_ids = {issue["id"] for issue in open_issues}

blocked = 0
for issue in all_issues:
    for dep in issue.get("dependencies", []):
        if dep.get("depends_on_id") in open_ids:
            blocked += 1
            break
```

---

### 5. Step Result Structure for Review Steps

**File**: `go/internal/planning/steps.go` (lines 13-24)

```go
type StepResult struct {
    Success       bool
    Error         string
    Output        string
    ResearchPath  string
    PlanPath      string
    PlanPaths     []string
    PhaseFiles    []string
    OpenQuestions []string
    Data          map[string]interface{}
}
```

**Adapted for Review**:
```go
type ReviewStepResult struct {
    Success        bool
    Step           string     // "contracts", "interfaces", etc.
    Phase          PhaseType  // Which phase was reviewed
    WellDefined    []string   // Items marked ✅
    Warnings       []string   // Items marked ⚠️
    Critical       []string   // Items marked ❌
    Recommendations []string
}
```

---

### 6. Autonomy Mode Considerations

**File**: `go/internal/planning/orchestrator.go` (lines 39-91)

```go
type AutonomyMode int

const (
    AutonomyCheckpoint AutonomyMode = iota     // Pause after each phase
    AutonomyFullyAutonomous                    // Run all phases without stopping
    AutonomyBatch                              // Pause at group boundaries only
)
```

**Review Integration**:
- **Checkpoint Mode**: Review each phase individually, pause for approval
- **Batch Mode**: Review all phases in a group, pause at group boundaries
- **Fully Autonomous**: Complete all reviews without pausing

---

## 🔧 Code References

| File | Lines | Description |
|------|-------|-------------|
| `.claude/commands/review_plan.md` | 1-355 | Review command prompt template |
| `go/internal/cli/root.go` | 24-58 | Cobra command registration pattern |
| `go/internal/cli/plan.go` | 28-159 | Example command implementation |
| `go/internal/planning/models.go` | 509-608 | PhaseType enumeration and methods |
| `go/internal/planning/models.go` | 61-115 | RequirementNode structure |
| `go/internal/planning/models.go` | 610-692 | PhaseStatus state machine |
| `go/internal/planning/steps.go` | 13-24 | StepResult structure |
| `go/internal/planning/steps.go` | 550-557 | Linear dependency linking |
| `go/internal/planning/implementation.go` | 70-120 | Implementation loop pattern |
| `go/internal/planning/checkpoint.go` | 17-25 | Checkpoint structure |

---

## 🏗️ Architecture Documentation

### Proposed Loop Structure for Review with Nested Dependencies

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                    REVIEW LOOP ARCHITECTURE                               ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  OUTER LOOP: Iterate Over Phases (Sequential)                             ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │ for phase := range AllPhases() {                                    │  ║
║  │     // Check phase dependencies satisfied                          │  ║
║  │     if !areDependenciesMet(phase) { continue }                     │  ║
║  │                                                                     │  ║
║  │     MIDDLE LOOP: Iterate Over Review Steps                          │  ║
║  │     ┌─────────────────────────────────────────────────────────────┐ │  ║
║  │     │ for step := range ReviewSteps {                             │ │  ║
║  │     │     // contracts, interfaces, promises, data_models, apis   │ │  ║
║  │     │                                                             │ │  ║
║  │     │     INNER LOOP: Recursive Requirement Traversal              │ │  ║
║  │     │     ┌─────────────────────────────────────────────────────┐ │ │  ║
║  │     │     │ func reviewRequirements(node, step) {               │ │ │  ║
║  │     │     │     findings := reviewNode(node, step)              │ │ │  ║
║  │     │     │     for _, child := range node.Children {           │ │ │  ║
║  │     │     │         findings += reviewRequirements(child, step) │ │ │  ║
║  │     │     │     }                                               │ │ │  ║
║  │     │     │     return findings                                 │ │ │  ║
║  │     │     │ }                                                   │ │ │  ║
║  │     │     └─────────────────────────────────────────────────────┘ │ │  ║
║  │     │                                                             │ │  ║
║  │     │     results[phase][step] = runReview(phase, step)           │ │  ║
║  │     │ }                                                           │ │  ║
║  │     └─────────────────────────────────────────────────────────────┘ │  ║
║  │                                                                     │  ║
║  │     // Checkpoint after phase if in checkpoint mode                │  ║
║  │     if autonomyMode == AutonomyCheckpoint {                        │  ║
║  │         saveCheckpoint(phase, results)                             │  ║
║  │         waitForApproval()                                          │  ║
║  │     }                                                              │  ║
║  │ }                                                                   │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

### Key Design Decisions Observed in Codebase

| Decision | Pattern Used | Location |
|----------|--------------|----------|
| Phase ordering | Enum with `Next()`/`Previous()` methods | `models.go:561-575` |
| Requirement nesting | Recursive struct with `ParentID`/`Children` | `models.go:61-115` |
| Dependency linking | Linear chain via prev pointer | `steps.go:550-557` |
| Loop termination | Iteration limit + closure check | `implementation.go:70-120` |
| State persistence | JSON checkpoint files | `checkpoint.go:44-87` |
| Result collection | Map by phase/step | `pipeline.go` results struct |

---

## 📖 Historical Context (from thoughts/)

| File | Relevance |
|------|-----------|
| `thoughts/searchable/plans/2026-01-04-tdd-context-window-array/REVIEW.md` | Example output of review_plan execution showing report format |
| `thoughts/shared/plans/2026-01-01-tdd-planning-orchestrator.md` | TDD behavior structure with Red-Green-Refactor pattern |
| `thoughts/searchable/plans/2026-01-04-1-baml-integration/2026-01-04-tdd-step-decomposition-baml-integration-00-overview.md` | Phase dependency documentation pattern |

---

## 🔗 Related Research

- No prior research documents found on this specific topic

---

## ❓ Open Questions

1. **Parallel Review Steps**: Should review steps within a phase run in parallel, or must they be sequential due to potential dependencies between analysis types?

2. **Incremental Results**: Should the review checkpoint after each step within a phase, or only after completing all 5 steps for a phase?

3. **Claude Invocation Strategy**: Should each review step invoke Claude separately, or should all 5 steps be combined into a single Claude call per phase?

4. **Requirement-Level vs Phase-Level**: Should the review analyze requirements hierarchically within each phase, or treat each phase as a flat unit?

5. **Blocking Dependencies**: How should the review handle phases that have critical issues blocking subsequent phases?

---

## 📋 Implementation Checklist

Based on existing patterns, a Go `review_plan` command would need:

- [ ] Command definition in `go/internal/cli/review_plan.go`
- [ ] Registration in `root.go` init() function
- [ ] Flags: `--plan-path`, `--phase`, `--step`, `--output`, `--autonomy-mode`
- [ ] Review step functions in `go/internal/planning/review.go`
- [ ] ReviewResult struct in `go/internal/planning/models.go`
- [ ] Claude prompt templates for each review step
- [ ] Checkpoint integration for resumable reviews
- [ ] Report generation matching existing REVIEW.md format

---

*Research completed: 2026-01-13T09:14:22-05:00*
