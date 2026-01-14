# Research: Adapting RLM Recursive Loop Pattern for Go Decomposition Phase

**Date**: 2026-01-11
**Focus**: Go decomposition phase adaptation using recursive LLM loop pattern
**External Reference**: `~/Dev/rlm-minimal/`

## Executive Summary

This research analyzes the Recursive Language Model (RLM) pattern from the `rlm-minimal` repository and how it can be adapted for the decomposition phase in the Go planning pipeline. The goal is to enable an LLM to decompose long plans and large JSON requirements (like `hierarchy.json` with 42+ nodes) into multiple plan files where each phase results in one human-testable function.

## 1. RLM Pattern Analysis (from rlm-minimal)

### Core Architecture

The RLM pattern consists of three main components:

```
┌─────────────────────────────────────────────────────────────┐
│                    RLM_REPL Class                           │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐   │
│  │ Root LLM    │──▶│ REPL Env    │──▶│ Sub-RLM         │   │
│  │ (gpt-5)     │   │ (exec-based)│   │ (gpt-5-nano)    │   │
│  └─────────────┘   └─────────────┘   └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Key Pattern: Main Iteration Loop

**File**: `rlm-minimal/rlm/rlm_repl.py:76-121`

```python
def completion(self, context, query):
    self.messages = self.setup_context(context, query)

    for iteration in range(self._max_iterations):  # e.g., max=10
        # 1. Query root LLM with current messages + iteration prompt
        response = self.llm.completion(
            self.messages + [next_action_prompt(query, iteration)]
        )

        # 2. Check for code blocks in response
        code_blocks = utils.find_code_blocks(response)

        # 3. Process code execution or add assistant message
        if code_blocks is not None:
            self.messages = utils.process_code_execution(
                response, self.messages, self.repl_env, ...
            )
        else:
            self.messages.append({"role": "assistant", "content": response})

        # 4. Check termination condition
        final_answer = utils.check_for_final_answer(response, self.repl_env)
        if final_answer:
            return final_answer

    # 5. Force final answer if max iterations reached
    return self.llm.completion(self.messages + [final_answer_prompt])
```

### REPL Environment with Sub-LLM Access

**File**: `rlm-minimal/rlm/repl.py:169-198`

The REPL environment provides:

1. **`llm_query(prompt)`**: Sub-LLM call function injected into exec globals
2. **`FINAL_VAR(variable_name)`**: Return mechanism for extracting results
3. **Context loading**: Can load JSON or string context into `context` variable
4. **Code execution**: `exec()`-based with captured stdout/stderr

```python
# Key functions available in REPL
self.globals['llm_query'] = lambda prompt: self.sub_rlm.completion(prompt)
self.globals['FINAL_VAR'] = lambda var_name: self.locals[var_name]
```

### Pattern Characteristics

| Aspect | RLM Pattern |
|--------|-------------|
| Loop Type | Fixed iteration count with early termination |
| LLM Calls | Root LLM per iteration + Sub-LLM on demand |
| Context | Accumulated messages + REPL state |
| Termination | `FINAL_VAR()` call or max iterations |
| Error Handling | Continue on transient failures |
| Output | Incremental building via REPL execution |

## 2. Current Go Decomposition Implementation

### File Locations

- **Core Logic**: `go/internal/planning/decomposition.go`
- **Claude Runner**: `go/internal/planning/claude_runner.go`
- **Pipeline Steps**: `go/internal/planning/steps.go`
- **Implementation Loop**: `go/internal/planning/implementation.go`

### Current Two-Phase Approach

**File**: `go/internal/planning/decomposition.go:50-238`

```go
func DecomposeRequirements(researchContent, projectPath string, ...) {
    // Phase 1: Extract initial requirements (single LLM call)
    extractionPrompt := buildExtractionPrompt(researchContent)
    result := RunClaudeSync(extractionPrompt, 1300, true, projectPath)

    // Parse JSON response into requirements[]

    // Phase 2: Expand each requirement (iterative LLM calls)
    for reqIdx, requirement := range data.Requirements {
        expansionPrompt := buildExpansionPrompt(...)
        expansionResult := RunClaudeSync(expansionPrompt, 90, true, projectPath)

        // Parse and add to hierarchy
        hierarchy.AddRequirement(parentNode)

        // Incremental save callback
        if saveCallback != nil {
            saveCallback(hierarchy)
        }
    }
}
```

### Current Implementation Loop Pattern

**File**: `go/internal/planning/implementation.go:70-126`

The implementation phase already uses a recursive loop pattern:

```go
for i := 0; i < maxIterations; i++ {
    result.Iterations = i + 1

    // Invoke Claude with prompt
    claudeResult := RunClaudeSync(prompt, IMPL_TIMEOUT, true, projectPath)

    // Continue on transient failures
    if !claudeResult.Success {
        fmt.Printf("WARNING: Claude iteration %d failed\n", result.Iterations)
        continue
    }

    // Check termination condition
    allClosed, closedIssues := checkAllIssuesClosed(projectPath, beadsIssueIDs)
    if allClosed {
        testsPassed, testOutput := runTests(projectPath)
        if testsPassed {
            return result  // Success!
        }
        // Update prompt with test failures for next iteration
        prompt = buildImplementationPrompt(...) + testFailures
    }
}
```

### Gap Analysis

| Aspect | Current Go | RLM Pattern | Gap |
|--------|------------|-------------|-----|
| Loop Type | Simple iteration | Recursive with termination check | Needs termination logic |
| Sub-LLM Calls | None in decomposition | Available via `llm_query()` | Needs sub-LLM support |
| Context Accumulation | None | Messages array grows | Needs message history |
| Dynamic Code Execution | None | REPL environment | Optional enhancement |
| Chunk Processing | Sequential | REPL-based dynamic | Needs chunking strategy |

## 3. Adaptation Strategy for Large Decomposition

### Problem: Large Requirements JSON

Example from `silmari-writer/.test/.../hierarchy.json`:
- 42 total nodes (7 parent requirements, 35 sub-processes)
- 1954 lines of JSON
- Each sub-process has: acceptance criteria, implementation details (frontend/backend/middleware/shared), function IDs

### Proposed Recursive Decomposition Pattern

```go
// DecomposeRequirementsRecursive implements RLM-style recursive decomposition
func DecomposeRequirementsRecursive(
    researchContent string,
    requirementsJSON string,  // Large hierarchy.json content
    projectPath string,
    config *DecompositionConfig,
) (*RequirementHierarchy, error) {

    messages := []ConversationMessage{}
    hierarchy := NewRequirementHierarchy()

    // Initialize context with chunked requirements
    chunks := chunkRequirements(requirementsJSON, config.ChunkSize)

    for iteration := 0; iteration < config.MaxIterations; iteration++ {
        // Build iteration prompt
        prompt := buildDecompositionIterationPrompt(
            researchContent,
            chunks,
            hierarchy,
            iteration,
        )

        // Add to message history
        messages = append(messages, ConversationMessage{
            Role: "user",
            Content: prompt,
        })

        // Call Claude
        result := RunClaudeConversation(messages, config.Timeout, true, projectPath)

        // Parse response for:
        // 1. New plan files to create
        // 2. Phase definitions
        // 3. Termination signal

        action := parseDecompositionAction(result.Output)

        switch action.Type {
        case "create_phase":
            createPhaseFile(projectPath, action.PhaseData)
            hierarchy.AddPhase(action.PhaseData)

        case "request_clarification":
            // Sub-LLM call for clarification
            clarification := RunClaudeSync(action.ClarificationPrompt, 60, true, projectPath)
            messages = append(messages, ConversationMessage{
                Role: "assistant",
                Content: clarification.Output,
            })

        case "complete":
            return hierarchy, nil
        }

        // Add response to message history
        messages = append(messages, ConversationMessage{
            Role: "assistant",
            Content: result.Output,
        })
    }

    return hierarchy, fmt.Errorf("max iterations reached")
}
```

### Chunking Strategy for Large JSON

```go
// chunkRequirements splits large JSON into processable chunks
func chunkRequirements(jsonContent string, chunkSize int) []RequirementChunk {
    var data RequirementHierarchy
    json.Unmarshal([]byte(jsonContent), &data)

    var chunks []RequirementChunk

    // Strategy 1: By parent requirement
    for _, parent := range data.Requirements {
        chunk := RequirementChunk{
            ParentID:    parent.ID,
            Description: parent.Description,
            Children:    parent.Children,
        }
        chunks = append(chunks, chunk)
    }

    // Strategy 2: By size threshold
    // Split chunks that exceed token limit

    return chunks
}
```

### Phase File Generation Pattern

Each iteration should produce one or more phase files:

```go
type PhaseDefinition struct {
    ID               string   // e.g., "01-user-authentication"
    Title            string
    FunctionID       string   // Human-testable function
    Dependencies     []string // Other phase IDs this depends on
    RequirementIDs   []string // REQ_000.1, REQ_000.2, etc.
    AcceptanceCriteria []string
    SuccessCriteria  string   // Single human-testable outcome
}

func createPhaseFile(projectPath string, phase PhaseDefinition) error {
    template := `# Phase %s: %s

## Tracking
- Issue: [To be assigned]
- Function ID: %s

## Dependencies
%s

## Requirements Covered
%s

## Success Criteria
%s

## Acceptance Criteria
%s
`
    // Write to thoughts/searchable/plans/YYYY-MM-DD-tdd-feature/NN-phase-name.md
}
```

## 4. Implementation Recommendations

### 4.1 Add Recursive Loop to Decomposition

**File to modify**: `go/internal/planning/decomposition.go`

```go
// Add these constants
const (
    DECOMP_MAX_ITERATIONS = 20
    DECOMP_TIMEOUT       = 300  // 5 minutes per iteration
    DECOMP_CHUNK_SIZE    = 10   // Requirements per chunk
)

// Add message history tracking
type DecompositionState struct {
    Messages  []ConversationMessage
    Hierarchy *RequirementHierarchy
    Iteration int
    Chunks    []RequirementChunk
}
```

### 4.2 Add Sub-LLM Support for Clarification

The current `claude_runner.go` already supports conversation mode:

```go
// Already exists - can be used for sub-LLM calls
func RunClaudeConversation(messages []ConversationMessage, ...) *ClaudeResult
```

### 4.3 Termination Conditions

1. **All requirements processed**: Check if all chunks have been expanded
2. **All phases created**: Compare expected vs actual phase files
3. **FINAL marker**: LLM outputs specific termination signal
4. **Max iterations**: Hard limit prevents infinite loops

```go
func checkDecompositionComplete(state *DecompositionState, expected int) bool {
    // Count created phase files
    phaseFiles := glob.Glob(filepath.Join(state.OutputDir, "*-phase-*.md"))

    // Check if all requirements have phases
    return len(phaseFiles) >= expected || state.Iteration >= DECOMP_MAX_ITERATIONS
}
```

### 4.4 Integration with Existing Pipeline

The pipeline already has step functions. Add new recursive decomposition:

**File**: `go/internal/planning/steps.go`

```go
// StepRequirementDecompositionRecursive uses RLM-style recursive decomposition
func StepRequirementDecompositionRecursive(
    projectPath string,
    researchPath string,
    requirementsPath string,  // Optional: pre-existing hierarchy.json
) *StepResult {
    result := NewStepResult()

    // Load inputs
    researchContent, _ := os.ReadFile(researchPath)
    requirementsJSON := ""
    if requirementsPath != "" {
        reqContent, _ := os.ReadFile(requirementsPath)
        requirementsJSON = string(reqContent)
    }

    // Run recursive decomposition
    config := &DecompositionConfig{
        MaxIterations: DECOMP_MAX_ITERATIONS,
        ChunkSize:     DECOMP_CHUNK_SIZE,
    }

    hierarchy, err := DecomposeRequirementsRecursive(
        string(researchContent),
        requirementsJSON,
        projectPath,
        config,
    )

    if err != nil {
        result.SetError(err)
        return result
    }

    result.PhaseFiles = hierarchy.GetPhaseFiles()
    return result
}
```

## 5. Key Differences from RLM Implementation

| Aspect | RLM (Python) | Proposed Go |
|--------|--------------|-------------|
| REPL Environment | Full exec-based REPL | Not needed - use structured prompts |
| Sub-LLM Calls | Via `llm_query()` in REPL | Via `RunClaudeConversation()` |
| Context Persistence | REPL locals dict | Checkpoint files |
| Termination | `FINAL_VAR()` function | Structured JSON response |
| Code Generation | Dynamic in REPL | Pre-defined phase templates |

## 6. Open Questions

1. **Token Limits**: How to handle context window overflow when message history grows?
   - Option: Summarize older messages
   - Option: Use checkpoint/resume pattern

2. **Parallelization**: Can multiple chunks be processed in parallel?
   - Parent requirements are independent
   - Sub-processes may have dependencies

3. **Error Recovery**: How to handle partial failures?
   - Current pattern: Continue on transient errors
   - RLM pattern: Retry with modified prompt

## 7. Related Files

### External (rlm-minimal)
- `~/Dev/rlm-minimal/rlm/rlm_repl.py` - Main recursive loop
- `~/Dev/rlm-minimal/rlm/repl.py` - REPL environment with sub-LLM

### This Repository
- `go/internal/planning/decomposition.go` - Current decomposition
- `go/internal/planning/implementation.go` - Existing loop pattern
- `go/internal/planning/claude_runner.go` - LLM invocation
- `go/internal/planning/steps.go` - Pipeline step functions

### silmari-writer Reference
- `hierarchy.json` - Example of large requirements (42 nodes)
- `silmari-writer/.test/.../planning-session/` - Planning session structure

## 8. Next Steps

1. **Prototype**: Implement `DecomposeRequirementsRecursive()` in Go
2. **Test**: Use `hierarchy.json` as test input
3. **Integrate**: Add to pipeline as alternative decomposition step
4. **Validate**: Ensure each phase produces one human-testable function
