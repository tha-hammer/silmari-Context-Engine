# Porting Context Engine to Go - Research Document

**Date:** 2026-01-01
**Topic:** Feasibility and approach for porting silmari-Context-Engine from Python to Go

---

## Executive Summary

The Context Engine is an autonomous AI coding agent orchestrator (~740 lines of Python in the core pipeline) that manages Claude Code sessions. The codebase is well-structured with clear separation of concerns, making a Go port feasible. The main complexity lies in subprocess orchestration and text parsing.

---

## 1. Architecture Overview

The system consists of three main entry points and a core pipeline library:

| Component | Purpose | File Reference |
|-----------|---------|----------------|
| Orchestrator | Interactive CLI for project setup | `orchestrator.py:1-50` |
| Loop Runner | Autonomous session looping | `loop-runner.py:1-30` |
| Planning Orchestrator | Five-step deterministic pipeline | `planning_orchestrator.py:20-241` |
| Planning Pipeline | Core library for pipeline execution | `planning_pipeline/pipeline.py:12-157` |

### Four-Layer Memory Architecture
1. **Research** - Codebase analysis documents
2. **Planning** - Implementation plans
3. **Phase Decomposition** - Atomic phase files
4. **Beads Integration** - Issue tracking with dependencies

---

## 2. Language & Dependencies

**Current:** Python 3.9+ (tested on 3.12)

### Standard Library Usage
| Python Module | Purpose | Go Equivalent |
|---------------|---------|---------------|
| `subprocess` | CLI invocation | `os/exec` |
| `json` | Config/data parsing | `encoding/json` |
| `pathlib` | Path operations | `path/filepath` |
| `datetime` | Timestamps | `time` |
| `argparse` | CLI parsing | `flag` or `cobra` |
| `re` | Text parsing | `regexp` |

### External Tools (Required)
- `claude` - Claude Code CLI
- `bd` - Beads issue tracking CLI
- `git` - Version control
- `bash` - Shell scripts

No Python packages required beyond stdlib - this simplifies porting.

---

## 3. Core Abstractions

### Classes to Port

**`PlanningPipeline`** (`planning_pipeline/pipeline.py:12-157`)
```go
type PlanningPipeline struct {
    ProjectPath    string
    BeadsController *BeadsController
}

func (p *PlanningPipeline) Run(researchPrompt, ticketID string, autoApprove bool) (*PipelineResult, error)
```

**`BeadsController`** (`planning_pipeline/beads_controller.py:9-91`)
```go
type BeadsController struct {
    ProjectPath string
    Timeout     time.Duration // 30s default
}

func (b *BeadsController) CreateIssue(title, issueType string, priority int) (*Issue, error)
func (b *BeadsController) CreateEpic(title string, priority int) (*Issue, error)
func (b *BeadsController) ListIssues(status string) ([]Issue, error)
func (b *BeadsController) CloseIssue(issueID, reason string) error
func (b *BeadsController) AddDependency(issueID, dependsOn string) error
func (b *BeadsController) Sync() error
```

### Key Data Structures

**Feature** (`loop-runner.py:35-38`)
```go
type Feature struct {
    ID           string   `json:"id"`
    Name         string   `json:"name"`
    Description  string   `json:"description"`
    Priority     int      `json:"priority"`
    Category     string   `json:"category"`
    Passes       bool     `json:"passes"`
    Blocked      bool     `json:"blocked"`
    BlockedReason string  `json:"blocked_reason,omitempty"`
    BlockedAt    string   `json:"blocked_at,omitempty"`
    BlockedBy    []string `json:"blocked_by,omitempty"`
    SuggestedFix string   `json:"suggested_fix,omitempty"`
    Dependencies []string `json:"dependencies,omitempty"`
    Tests        []string `json:"tests,omitempty"`
    Complexity   string   `json:"complexity,omitempty"` // "high"|"medium"|"low"
    NeedsReview  bool     `json:"needs_review,omitempty"`
    QAOrigin     string   `json:"qa_origin,omitempty"`
}
```

**PipelineResult** (`planning_pipeline/pipeline.py:32-150`)
```go
type PipelineResult struct {
    Success   bool              `json:"success"`
    Started   string            `json:"started"`
    Completed string            `json:"completed"`
    TicketID  string            `json:"ticket_id"`
    Steps     map[string]StepResult `json:"steps"`
    PlanDir   string            `json:"plan_dir"`
    EpicID    string            `json:"epic_id"`
}

type StepResult struct {
    Success       bool     `json:"success"`
    ResearchPath  string   `json:"research_path,omitempty"`
    PlanPath      string   `json:"plan_path,omitempty"`
    PhaseFiles    []string `json:"phase_files,omitempty"`
    EpicID        string   `json:"epic_id,omitempty"`
    Output        string   `json:"output,omitempty"`
    OpenQuestions []string `json:"open_questions,omitempty"`
}
```

---

## 4. Database/Storage

### Storage Mechanisms

| Type | Location | Format | Purpose |
|------|----------|--------|---------|
| Beads DB | `.beads/beads.db` | SQLite (via `bd` CLI) | Issue tracking |
| Feature List | `feature_list.json` | JSON | Master feature tracking |
| Research | `thoughts/shared/research/*.md` | Markdown | Analysis documents |
| Plans | `thoughts/shared/plans/**/` | Markdown | Implementation plans |
| Config | `.beads/config.yaml` | YAML | Beads configuration |

**No direct database access** - all DB operations go through the `bd` CLI wrapper.

---

## 5. CLI Structure

### Current Entry Points

```bash
# Interactive project setup
python orchestrator.py [--new|--continue|--status] [--model sonnet|opus]

# Autonomous loop
./loop-runner.py [PROJECT_PATH] [--max-sessions N]

# Planning pipeline
python planning_orchestrator.py --project PATH --ticket ID [--auto-approve]
```

### Subprocess Invocations
Key patterns that must be replicated:

**Claude CLI** (`claude_runner.py:27-32`)
```bash
claude --print --permission-mode bypassPermissions --output-format text -p "{prompt}"
```

**Beads CLI** (`beads_controller.py:52-91`)
```bash
bd create --title="..." --type=task --priority=2 --json
bd list --status=open --json
bd close {issue_id} --reason="..."
bd dep add {issue_id} {depends_on}
bd sync
```

---

## 6. Configuration

### Configuration Files

| File | Format | Purpose | Reference |
|------|--------|---------|-----------|
| `feature_list.json` | JSON | Feature tracking | `orchestrator.py:429-445` |
| `.beads/config.yaml` | YAML | Beads settings | `.beads/config.yaml:1-63` |
| `.claude/settings.json` | JSON | Claude Code config | `.claude/` directory |

### Environment Variables
- `CONTEXT_ENGINE_PATH` - Override harness location
- `CONTEXT_ENGINE_WRITE_MODE` - Enable auto-completion
- `BD_*` / `BEADS_*` - Beads configuration

### Default Values (`orchestrator.py:29-33`, `loop-runner.py:27-29`)
- Session timeout: 3600s
- Retry delay: 5s
- Beads timeout: 30s
- Claude timeout: 300s
- Max sessions: 100

---

## 7. Testing

### Framework
- **Python:** pytest with BDD-style organization
- **Go equivalent:** `testing` package + `testify/assert`

### Test Structure (`planning_pipeline/tests/`)
```
test_helpers.py      # Parser functions (3 behaviors)
test_beads.py        # BeadsController (3 behaviors)
test_claude.py       # Claude runner (1 behavior)
test_checkpoints.py  # Interactive checkpoints (2 behaviors)
test_steps.py        # Pipeline steps (4 behaviors)
test_pipeline.py     # Full pipeline (1 behavior)
test_orchestrator.py # Orchestrator CLI (7 behaviors)
```

### Test Patterns
- **Unit tests:** Pure parser functions with mock output
- **Integration tests:** Real subprocess/CLI calls
- **Mocking:** `unittest.mock.patch` → Go's interface-based mocking
- **Cleanup:** Fixture-based cleanup of beads issues

### Test Markers
- `@pytest.mark.slow` → `t.Skip("slow")` or build tags
- `@pytest.mark.integration` → Build tags `//go:build integration`

---

## 8. Build System

### Current Approach
- No compilation (Python scripts)
- Direct execution via shebang
- `install.sh` for symlink setup

### Go Port Build System

```makefile
# Suggested Makefile
.PHONY: build test install

build:
    go build -o bin/orchestrator ./cmd/orchestrator
    go build -o bin/loop-runner ./cmd/loop-runner
    go build -o bin/planning-orchestrator ./cmd/planning-orchestrator

test:
    go test ./...

test-integration:
    go test -tags=integration ./...

install:
    go install ./cmd/...
```

---

## 9. Recommended Go Project Structure

```
silmari-context-engine-go/
├── cmd/
│   ├── orchestrator/main.go
│   ├── loop-runner/main.go
│   └── planning-orchestrator/main.go
├── pkg/
│   ├── pipeline/
│   │   ├── pipeline.go       # PlanningPipeline
│   │   ├── steps.go          # step_research, etc.
│   │   ├── checkpoints.go    # interactive_checkpoint_*
│   │   └── helpers.go        # extract_* functions
│   ├── beads/
│   │   └── controller.go     # BeadsController
│   ├── claude/
│   │   └── runner.go         # run_claude_sync
│   └── types/
│       └── types.go          # Feature, PipelineResult
├── internal/
│   └── exec/
│       └── subprocess.go     # Subprocess wrapper
├── test/
│   └── fixtures/
│       └── sample_outputs.go
├── go.mod
├── go.sum
└── Makefile
```

---

## 10. Porting Priority Order

Files ranked by dependency order and complexity:

| Priority | File | Lines | Reason |
|----------|------|-------|--------|
| 1 | `helpers.py` | 68 | Pure functions, no side effects |
| 2 | `beads_controller.py` | 91 | Central I/O wrapper |
| 3 | `claude_runner.py` | 74 | Claude CLI invocation |
| 4 | `checkpoints.py` | 52 | Interactive input |
| 5 | `steps.py` | 234 | Step orchestration |
| 6 | `pipeline.py` | 157 | Main pipeline logic |
| 7 | `planning_orchestrator.py` | 241 | CLI entry point |
| 8 | `orchestrator.py` | ~500 | Complex business logic |
| 9 | `loop-runner.py` | ~300 | Depends on all above |

**Total core pipeline:** ~740 lines
**Estimated Go equivalent:** ~1200-1500 lines (Go is more verbose)

---

## 11. Key Porting Challenges

### 1. Subprocess Management
Python's `subprocess.run()` is flexible. Go's `os/exec` requires more explicit handling:

```go
// Python pattern (beads_controller.py:20-41)
result = subprocess.run(args, capture_output=True, timeout=30)

// Go equivalent
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()
cmd := exec.CommandContext(ctx, args[0], args[1:]...)
output, err := cmd.CombinedOutput()
```

### 2. Regular Expressions
Python's `re.search()` groups → Go's `regexp.FindStringSubmatch()`:

```go
// Python (helpers.py:7-18)
match = re.search(r'path/to/(.+\.md)', output)

// Go equivalent
re := regexp.MustCompile(`path/to/(.+\.md)`)
matches := re.FindStringSubmatch(output)
if len(matches) > 1 {
    path = matches[1]
}
```

### 3. JSON Flexibility
Python handles `dict[str, Any]` naturally. Go needs either:
- `map[string]interface{}` (flexible but type-unsafe)
- Typed structs (safer, recommended)
- `json.RawMessage` for deferred parsing

### 4. Error Handling
Python exceptions → Go explicit error returns:

```go
// Every function that can fail needs error handling
result, err := beads.CreateIssue(title, issueType, priority)
if err != nil {
    return nil, fmt.Errorf("create issue: %w", err)
}
```

### 5. Interactive Input
Python's `input()` → Go's `bufio.Scanner`:

```go
reader := bufio.NewReader(os.Stdin)
fmt.Print("Approve? [y/N]: ")
response, _ := reader.ReadString('\n')
response = strings.TrimSpace(strings.ToLower(response))
```

---

## 12. Go Library Recommendations

| Purpose | Library | Notes |
|---------|---------|-------|
| CLI | `github.com/spf13/cobra` | Industry standard |
| Flags | `github.com/spf13/pflag` | POSIX-style flags |
| YAML | `gopkg.in/yaml.v3` | Config parsing |
| Testing | `github.com/stretchr/testify` | Assertions |
| Logging | `log/slog` | Structured logging (stdlib) |
| Colors | `github.com/fatih/color` | Terminal colors |

---

## 13. Benefits of Go Port

1. **Single Binary Distribution** - No Python runtime required
2. **Cross-Compilation** - Build for any OS/arch from one machine
3. **Concurrency** - goroutines for parallel step execution
4. **Type Safety** - Catch errors at compile time
5. **Performance** - Faster startup, lower memory
6. **Deployment** - Simpler installation (copy binary)

---

## 14. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Regex behavior differences | Medium | Port tests first, validate regex patterns |
| JSON parsing edge cases | Medium | Use typed structs with custom UnmarshalJSON |
| Shell escaping differences | High | Use exec.Command with args slice (not shell string) |
| Interactive terminal handling | Medium | Consider `github.com/charmbracelet/bubbletea` |
| Test coverage gaps | High | Port tests alongside code, not after |

---

## Open Questions

1. **Concurrency model**: Should steps run in parallel where possible, or maintain sequential execution for predictability?

2. **Configuration format**: Keep YAML for beads config, or standardize on JSON/TOML for Go ecosystem compatibility?

3. **CLI library choice**: Use stdlib `flag` package for simplicity, or Cobra for better UX (subcommands, help generation)?

4. **Error handling strategy**: Return errors vs. panic for unrecoverable conditions? Use error wrapping?

5. **Logging approach**: Use `log/slog` (stdlib) or third-party structured logger?

6. **Test strategy**: Port tests incrementally with code, or write new tests from specifications?

7. **Backward compatibility**: Should Go version read/write same file formats, or is migration acceptable?

8. **MCP integration**: The Python version uses `claude mcp add` commands - how to handle MCP setup in Go?

9. **Feature parity timeline**: Port all features at once, or start with core pipeline only?

10. **Dependency graph algorithm**: The topological sort in `loop-runner.py:154-209` uses Kahn's algorithm - verify Go implementation matches exactly?
