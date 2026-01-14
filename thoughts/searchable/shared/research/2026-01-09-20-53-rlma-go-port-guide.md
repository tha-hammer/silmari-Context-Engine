---
date: 2026-01-09T20:53:34-05:00
researcher: Claude Sonnet 4.5
git_commit: 15ed191db4ff2bb1308e2f075e0af3350605f6a4
branch: main
repository: silmari-Context-Engine
topic: "How to Port silmari_rlm_act Pipeline to Go"
tags: [research, go, python, port, rlma, pipeline, planning, implementation]
status: complete
last_updated: 2026-01-09
last_updated_by: Claude Sonnet 4.5
---

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║        PORTING GUIDE: silmari_rlm_act PIPELINE TO GO                          ║
║        From Python to Go - Complete Implementation Reference                  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

**Date**: 2026-01-09T20:53:34-05:00
**Researcher**: Claude Sonnet 4.5
**Git Commit**: 15ed191db4ff2bb1308e2f075e0af3350605f6a4
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📚 Research Question

**How do I port the silmari_rlm_act pipeline to Go?**

---

## 📊 Executive Summary

The `silmari_rlm_act` pipeline is a **6-phase autonomous TDD pipeline** implemented in Python. A **partial Go port already exists** in `go/internal/planning/` covering the first 6 steps (Research through Beads Integration), but **missing the Implementation phase**.

### Current State

| Component | Python Location | Go Port Status |
|-----------|-----------------|----------------|
| Pipeline Orchestrator | `silmari_rlm_act/pipeline.py` | ✅ `go/internal/planning/pipeline.go` |
| Research Phase | `silmari_rlm_act/phases/research.py` | ✅ `StepResearch()` in steps.go |
| Decomposition Phase | `silmari_rlm_act/phases/decomposition.py` | ✅ `StepRequirementDecomposition()` |
| TDD Planning Phase | `silmari_rlm_act/phases/tdd_planning.py` | ✅ `StepPlanning()` |
| Multi-Doc Phase | `silmari_rlm_act/phases/multi_doc.py` | ✅ `StepPhaseDecomposition()` |
| Beads Sync Phase | `silmari_rlm_act/phases/beads_sync.py` | ✅ `StepBeadsIntegration()` |
| Implementation Phase | `silmari_rlm_act/phases/implementation.py` | ❌ **NOT PORTED** |
| Checkpoint Manager | `silmari_rlm_act/checkpoints/manager.py` | ❌ Basic resume only |
| CWA Integration | `silmari_rlm_act/context/cwa_integration.py` | ❌ Direct file writes |
| Data Models | `silmari_rlm_act/models.py` | ✅ `go/internal/planning/models.go` |
| CLI | `silmari_rlm_act/cli.py` | ✅ `go/internal/cli/plan.go` |

---

## 🎯 What You Need to Port

### 1️⃣ Implementation Phase (CRITICAL - Not Ported)

The most significant missing piece. The Python implementation uses an **autonomous loop pattern**:

```
┌─────────────────────────────────────────────────────────────────┐
│  IMPLEMENTATION LOOP PATTERN (Python)                           │
├─────────────────────────────────────────────────────────────────┤
│  1. Build prompt with TDD plan + beads issue IDs                │
│  2. LOOP (max 100 iterations):                                  │
│     a. Invoke Claude with prompt (streaming output)             │
│     b. Sleep 10 seconds                                         │
│     c. Check if all beads issues are closed                     │
│     d. If all closed:                                           │
│        - Run tests (pytest or make test)                        │
│        - If tests pass: break loop, mark complete               │
│        - If tests fail: continue loop to fix                    │
│  3. Return PhaseResult with iteration count                     │
└─────────────────────────────────────────────────────────────────┘
```

**Python Source**: `silmari_rlm_act/phases/implementation.py:22-145`

### 2️⃣ Full Checkpoint System (Partial Port)

| Feature | Python | Go Current |
|---------|--------|------------|
| UUID-based checkpoint files | ✅ `.rlm-act-checkpoints/*.json` | ❌ |
| Automatic checkpoint after each phase | ✅ | ❌ |
| Resume from any phase | ✅ `resume_from_checkpoint()` | ⚠️ Manual step-based |
| Checkpoint cleanup commands | ✅ `cleanup_by_age()`, `cleanup_all()` | ❌ |
| Git commit tracking | ✅ | ❌ |

**Python Source**: `silmari_rlm_act/checkpoints/manager.py`

### 3️⃣ CWA Integration (Not Ported)

The Python implementation has a sophisticated Context Window Array system:

| Component | Purpose | Python Location |
|-----------|---------|-----------------|
| CentralContextStore | In-memory entry store with search | `context_window_array/store.py` |
| WorkingLLMContext | Summaries-only for orchestrator | `context_window_array/working_context.py` |
| ImplementationLLMContext | Full content with bounds | `context_window_array/implementation_context.py` |
| VectorSearchIndex | TF-IDF search | `context_window_array/search_index.py` |
| TaskBatcher | Batch tasks within entry limits | `context_window_array/batching.py` |

**Go Alternative**: The Go port uses direct file writes to `thoughts/` directories instead of CWA.

### 4️⃣ Interactive Checkpoints (Partial Port)

| Feature | Python | Go |
|---------|--------|-----|
| Phase action prompts | ✅ `prompt_research_action()`, etc. | ❌ |
| Multiline input collection | ✅ `collect_multiline_input()` | ❌ |
| File selection prompts | ✅ `prompt_file_selection()` | ❌ |
| Autonomy mode selection | ✅ `prompt_autonomy_mode()` | ⚠️ `--auto-approve` flag only |

**Python Source**: `silmari_rlm_act/checkpoints/interactive.py`

### 5️⃣ Three Autonomy Modes (Partial Port)

```python
# Python has 3 modes
class AutonomyMode(Enum):
    CHECKPOINT = "checkpoint"        # Pause after each phase
    BATCH = "batch"                  # Pause between groups
    FULLY_AUTONOMOUS = "autonomous"  # No pauses
```

```go
// Go has 2 modes (binary flag)
type PipelineConfig struct {
    AutoApprove bool  // true = autonomous, false = manual
}
```

**Missing**: BATCH mode grouping logic

---

## 🗺️ Component Mapping: Python → Go

### Data Models

<details>
<summary>Click to expand model mapping table</summary>

| Python Model | Go Equivalent | Status |
|--------------|---------------|--------|
| `AutonomyMode` enum | `PipelineConfig.AutoApprove` bool | ⚠️ Simplified |
| `PhaseType` enum | Step names as strings | ⚠️ No enum |
| `PhaseStatus` enum | `StepResult.Success` bool | ⚠️ Simplified |
| `PhaseResult` dataclass | `StepResult` struct | ✅ Similar |
| `PipelineState` dataclass | `PipelineResults` struct | ⚠️ Different shape |
| `RequirementHierarchy` | `RequirementHierarchy` | ✅ Ported |
| `RequirementNode` | `RequirementNode` | ✅ Ported |
| `TestableProperty` | `TestableProperty` | ✅ Ported |
| `Feature` | `Feature` | ✅ Ported |
| `FeatureList` | `FeatureList` | ✅ Ported |

</details>

### Phase Functions

| Python Phase | Go Function | Location |
|--------------|-------------|----------|
| `ResearchPhase.execute()` | `StepResearch()` | `steps.go:40-119` |
| `DecompositionPhase.execute()` | `StepRequirementDecomposition()` | `pipeline.go:198-242` |
| `TDDPlanningPhase.execute()` | `StepPlanning()` | `steps.go:121-200` |
| `MultiDocPhase.execute()` | `StepPhaseDecomposition()` | `steps.go:202-248` |
| `BeadsSyncPhase.execute()` | `StepBeadsIntegration()` | `steps.go:328-407` |
| `ImplementationPhase.execute()` | **NOT IMPLEMENTED** | - |

### Claude Runner

| Python Function | Go Function | Location |
|-----------------|-------------|----------|
| `run_claude_sync()` | `RunClaudeSync()` | `claude_runner.go:21-226` |
| N/A | `RunClaudeWithFile()` | `claude_runner.go` |
| N/A | `RunClaudeConversation()` | `claude_runner.go` |

**Key Difference**: Go has real-time streaming with goroutines; Python uses buffered capture.

---

## 🔧 Step-by-Step Porting Guide

### Step 1: Port the Implementation Phase

Create `go/internal/planning/implementation.go`:

```go
package planning

import (
    "fmt"
    "os/exec"
    "strings"
    "time"
)

const (
    IMPL_LOOP_SLEEP     = 10 * time.Second
    IMPL_MAX_ITERATIONS = 100
    IMPL_TIMEOUT        = 3600  // 1 hour per iteration
)

type ImplementationResult struct {
    Success       bool     `json:"success"`
    Error         string   `json:"error,omitempty"`
    Iterations    int      `json:"iterations"`
    TestsPassed   bool     `json:"tests_passed"`
    PhasesClosed  []string `json:"phases_closed,omitempty"`
}

func StepImplementation(
    projectPath string,
    phasePaths []string,
    beadsIssueIDs []string,
    beadsEpicID string,
    maxIterations int,
) *ImplementationResult {
    result := &ImplementationResult{Success: true}

    if maxIterations == 0 {
        maxIterations = IMPL_MAX_ITERATIONS
    }

    // Build implementation prompt
    prompt := buildImplementationPrompt(phasePaths, beadsEpicID, beadsIssueIDs)

    for i := 0; i < maxIterations; i++ {
        result.Iterations = i + 1

        // Invoke Claude
        claudeResult := RunClaudeSync(prompt, IMPL_TIMEOUT, true, projectPath)
        if !claudeResult.Success {
            // Continue loop on Claude error (may be transient)
            fmt.Printf("Claude iteration %d failed: %s\n", i+1, claudeResult.Error)
        }

        // Sleep before checking
        time.Sleep(IMPL_LOOP_SLEEP)

        // Check if all beads issues are closed
        allClosed := checkAllIssuesClosed(projectPath, beadsIssueIDs)
        if allClosed {
            // Run tests
            passed, output := runTests(projectPath)
            result.TestsPassed = passed

            if passed {
                fmt.Println("All tests passed!")
                return result
            }

            fmt.Printf("Tests failed, continuing loop:\n%s\n", output)
        }
    }

    result.Success = false
    result.Error = fmt.Sprintf("Max iterations (%d) reached", maxIterations)
    return result
}

func buildImplementationPrompt(phasePaths []string, epicID string, issueIDs []string) string {
    var sb strings.Builder

    sb.WriteString("# TDD Implementation Task\n\n")

    if len(phasePaths) > 0 {
        sb.WriteString(fmt.Sprintf("Read the TDD plan at: %s\n\n", phasePaths[0]))
    }

    if epicID != "" {
        sb.WriteString(fmt.Sprintf("## Beads Epic\nID: %s\nView: `bd show %s`\n\n", epicID, epicID))
    }

    if len(issueIDs) > 0 {
        sb.WriteString("## Phase Issues\n")
        for i, id := range issueIDs {
            sb.WriteString(fmt.Sprintf("- Phase %d: %s\n", i+1, id))
        }
        sb.WriteString("\n")
    }

    sb.WriteString(`## Instructions
1. Implement the behaviors described in the TDD plan
2. Use Red-Green-Refactor cycle for each behavior
3. Run tests after each implementation: pytest or make test
4. When a phase is complete, close the beads issue: bd close <id>
5. After closing an issue, emit /clear to reset context
6. Continue until all phases are complete and all tests pass

CRITICAL: After tests pass and after closing issues, emit /clear
`)

    return sb.String()
}

func checkAllIssuesClosed(projectPath string, issueIDs []string) bool {
    for _, id := range issueIDs {
        cmd := exec.Command("bd", "show", id)
        cmd.Dir = projectPath
        output, err := cmd.Output()
        if err != nil {
            return false
        }

        outputStr := strings.ToLower(string(output))
        if !strings.Contains(outputStr, "status: closed") &&
           !strings.Contains(outputStr, "status: done") {
            return false
        }
    }
    return true
}

func runTests(projectPath string) (bool, string) {
    // Try pytest first
    cmd := exec.Command("pytest", "-v", "--tb=short")
    cmd.Dir = projectPath
    output, err := cmd.CombinedOutput()

    if err == nil {
        return true, string(output)
    }

    // Fallback to make test
    cmd = exec.Command("make", "test")
    cmd.Dir = projectPath
    output, err = cmd.CombinedOutput()

    return err == nil, string(output)
}
```

### Step 2: Port the Checkpoint Manager

Create `go/internal/checkpoints/manager.go`:

```go
package checkpoints

import (
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
    "sort"
    "time"

    "github.com/google/uuid"
)

const CheckpointsDir = ".rlm-act-checkpoints"

type Checkpoint struct {
    ID        string                 `json:"id"`
    Phase     string                 `json:"phase"`
    Timestamp string                 `json:"timestamp"`
    State     map[string]interface{} `json:"state"`
    Errors    []string               `json:"errors,omitempty"`
    GitCommit string                 `json:"git_commit,omitempty"`
}

type CheckpointManager struct {
    projectPath    string
    checkpointsDir string
}

func NewCheckpointManager(projectPath string) *CheckpointManager {
    return &CheckpointManager{
        projectPath:    projectPath,
        checkpointsDir: filepath.Join(projectPath, CheckpointsDir),
    }
}

func (m *CheckpointManager) WriteCheckpoint(state map[string]interface{}, phase string, errors []string) (string, error) {
    // Ensure directory exists
    if err := os.MkdirAll(m.checkpointsDir, 0755); err != nil {
        return "", fmt.Errorf("failed to create checkpoints dir: %w", err)
    }

    checkpoint := Checkpoint{
        ID:        uuid.New().String(),
        Phase:     phase,
        Timestamp: time.Now().Format(time.RFC3339),
        State:     state,
        Errors:    errors,
        GitCommit: getGitCommit(m.projectPath),
    }

    filename := filepath.Join(m.checkpointsDir, checkpoint.ID+".json")
    data, err := json.MarshalIndent(checkpoint, "", "  ")
    if err != nil {
        return "", fmt.Errorf("failed to marshal checkpoint: %w", err)
    }

    if err := os.WriteFile(filename, data, 0644); err != nil {
        return "", fmt.Errorf("failed to write checkpoint: %w", err)
    }

    return filename, nil
}

func (m *CheckpointManager) DetectResumableCheckpoint() (*Checkpoint, error) {
    files, err := filepath.Glob(filepath.Join(m.checkpointsDir, "*.json"))
    if err != nil || len(files) == 0 {
        return nil, nil
    }

    // Sort by modification time (newest first)
    sort.Slice(files, func(i, j int) bool {
        fi, _ := os.Stat(files[i])
        fj, _ := os.Stat(files[j])
        return fi.ModTime().After(fj.ModTime())
    })

    // Load newest
    data, err := os.ReadFile(files[0])
    if err != nil {
        return nil, err
    }

    var checkpoint Checkpoint
    if err := json.Unmarshal(data, &checkpoint); err != nil {
        return nil, err
    }

    return &checkpoint, nil
}

func (m *CheckpointManager) CleanupByAge(days int) (int, int) {
    deleted, failed := 0, 0
    cutoff := time.Now().AddDate(0, 0, -days)

    files, _ := filepath.Glob(filepath.Join(m.checkpointsDir, "*.json"))
    for _, f := range files {
        fi, err := os.Stat(f)
        if err != nil {
            failed++
            continue
        }

        if fi.ModTime().Before(cutoff) {
            if os.Remove(f) == nil {
                deleted++
            } else {
                failed++
            }
        }
    }

    return deleted, failed
}

func (m *CheckpointManager) CleanupAll() (int, int) {
    deleted, failed := 0, 0
    files, _ := filepath.Glob(filepath.Join(m.checkpointsDir, "*.json"))

    for _, f := range files {
        if os.Remove(f) == nil {
            deleted++
        } else {
            failed++
        }
    }

    return deleted, failed
}

func getGitCommit(projectPath string) string {
    // Implementation in helpers
    return ""
}
```

### Step 3: Add AutonomyMode Enum

Update `go/internal/planning/models.go`:

```go
// AutonomyMode defines how the pipeline handles pauses
type AutonomyMode int

const (
    AutonomyCheckpoint AutonomyMode = iota  // Pause after each phase
    AutonomyBatch                           // Pause between phase groups
    AutonomyFull                            // No pauses
)

func (m AutonomyMode) String() string {
    switch m {
    case AutonomyCheckpoint:
        return "checkpoint"
    case AutonomyBatch:
        return "batch"
    case AutonomyFull:
        return "fully_autonomous"
    default:
        return "unknown"
    }
}
```

### Step 4: Update Pipeline Orchestrator

Update `go/internal/planning/pipeline.go` to integrate implementation:

```go
// Add to PipelineConfig
type PipelineConfig struct {
    ProjectPath   string
    AutoApprove   bool
    TicketID      string
    AutonomyMode  AutonomyMode  // Add this
    MaxIterations int           // Add this
}

// Add to Run() method after Step 7
func (p *PlanningPipeline) Run(researchPrompt string) *PipelineResults {
    // ... existing steps 1-7 ...

    // Step 8: Implementation (NEW)
    fmt.Println("\n" + strings.Repeat("=", 60))
    fmt.Println("STEP 8/8: IMPLEMENTATION PHASE")
    fmt.Println(strings.Repeat("=", 60))

    impl := StepImplementation(
        p.config.ProjectPath,
        decomposition.PhaseFiles,
        getIssueIDsFromBeads(beads),
        beads.EpicID,
        p.config.MaxIterations,
    )
    results.Steps["implementation"] = impl

    if !impl.Success {
        results.Success = false
        results.FailedAt = "implementation"
        results.Error = impl.Error
        return results
    }

    // ... rest of completion logic ...
}
```

---

## 📁 File Structure for Complete Go Port

```
go/
├── internal/
│   ├── planning/
│   │   ├── pipeline.go           # Main orchestrator (update)
│   │   ├── steps.go              # Step functions (existing)
│   │   ├── implementation.go     # NEW: Implementation phase
│   │   ├── models.go             # Data models (update)
│   │   ├── claude_runner.go      # Claude execution (existing)
│   │   ├── helpers.go            # Utility functions (existing)
│   │   └── decomposition.go      # Requirement decomposition (existing)
│   │
│   ├── checkpoints/              # NEW: Checkpoint package
│   │   ├── manager.go            # Checkpoint CRUD
│   │   └── interactive.go        # User prompts
│   │
│   ├── context/                  # NEW: CWA integration (optional)
│   │   ├── store.go              # Entry storage
│   │   ├── search.go             # Vector search
│   │   └── working.go            # Working context builder
│   │
│   └── cli/
│       ├── plan.go               # Plan command (existing)
│       ├── resume.go             # Resume command (update)
│       ├── status.go             # NEW: Status command
│       └── cleanup.go            # NEW: Cleanup command
│
└── cmd/
    └── context-engine/
        └── main.go               # Entry point (existing)
```

---

## 🛡️ Code References

### Python Implementation Files

| Component | File | Key Lines |
|-----------|------|-----------|
| Pipeline Orchestrator | `silmari_rlm_act/pipeline.py` | 47-470 |
| Research Phase | `silmari_rlm_act/phases/research.py` | Full file |
| Decomposition Phase | `silmari_rlm_act/phases/decomposition.py` | Full file |
| TDD Planning Phase | `silmari_rlm_act/phases/tdd_planning.py` | Full file |
| Multi-Doc Phase | `silmari_rlm_act/phases/multi_doc.py` | Full file |
| Beads Sync Phase | `silmari_rlm_act/phases/beads_sync.py` | Full file |
| Implementation Phase | `silmari_rlm_act/phases/implementation.py` | Full file |
| Checkpoint Manager | `silmari_rlm_act/checkpoints/manager.py` | Full file |
| Interactive Prompts | `silmari_rlm_act/checkpoints/interactive.py` | Full file |
| Data Models | `silmari_rlm_act/models.py` | Full file |
| CLI | `silmari_rlm_act/cli.py` | Full file |
| CWA Integration | `silmari_rlm_act/context/cwa_integration.py` | Full file |

### Go Implementation Files (Existing)

| Component | File | Key Lines |
|-----------|------|-----------|
| Pipeline | `go/internal/planning/pipeline.go` | 32-300 |
| Steps | `go/internal/planning/steps.go` | Full file |
| Models | `go/internal/planning/models.go` | Full file |
| Claude Runner | `go/internal/planning/claude_runner.go` | Full file |
| Helpers | `go/internal/planning/helpers.go` | Full file |
| Decomposition | `go/internal/planning/decomposition.go` | Full file |
| Plan CLI | `go/internal/cli/plan.go` | Full file |
| Resume CLI | `go/internal/cli/resume.go` | Full file |

---

## 📖 Historical Context

### Related Research Documents

- `thoughts/shared/research/2026-01-09-rlma-pipeline-go-port-analysis.md` - Comprehensive comparison of Python vs Go implementations
- `thoughts/shared/documentation/how-to-use-rlma-pipeline.md` - User guide for the Python RLMA pipeline
- `thoughts/shared/plans/2026-01-05-tdd-silmari-rlm-act/00-overview.md` - Original TDD plan for Python implementation

### Existing Beads Issues

- `silmari-Context-Engine-09ho` - TypeScript Port of Context Engine (related work)

---

## 🔍 Open Questions

1. **CWA Port Decision**: Should the Go port include full CWA integration or continue using direct file writes?
   - Direct file writes are simpler but lose search/compression capabilities
   - Full CWA port would require significant effort (~1000 LOC)

2. **Streaming vs Buffered Output**: The Go implementation already has better streaming than Python. Should Python be updated to match?

3. **Test Runner Selection**: Current implementation tries `pytest` then `make test`. Should this be configurable?

4. **Checkpoint Compatibility**: Should Go checkpoints be compatible with Python checkpoints for cross-language resume?

---

## ✅ Summary: What to Do

| Priority | Task | Effort |
|----------|------|--------|
| 🔴 Critical | Port Implementation Phase | 2-3 hours |
| 🟡 High | Port Checkpoint Manager | 1-2 hours |
| 🟡 High | Add status/cleanup CLI commands | 1 hour |
| 🟢 Medium | Add BATCH autonomy mode | 1 hour |
| 🟢 Medium | Add interactive prompts | 2 hours |
| ⚪ Optional | Port CWA integration | 4-6 hours |

The existing Go port covers ~80% of the pipeline. The **Implementation phase** is the critical missing piece that makes the pipeline actually useful for autonomous TDD development.
