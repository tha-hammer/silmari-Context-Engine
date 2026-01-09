# Phase 06: The system must port the planning pipeline module ...

## Requirements

### REQ_005: The system must port the planning pipeline module with all 1

The system must port the planning pipeline module with all 18 core files including 7-step pipeline, requirement decomposition, and property-based test generation

#### REQ_005.1: Port models.py RequirementNode and RequirementHierarchy data

Port models.py RequirementNode and RequirementHierarchy data structures with JSON tags

#### REQ_005.2: Port steps.py with 7 pipeline step implementations

Port steps.py with 7 pipeline step implementations

#### REQ_005.3: Port pipeline.py PlanningPipeline orchestrator (14-303 lines

Port pipeline.py PlanningPipeline orchestrator (14-303 lines)

#### REQ_005.4: Port decomposition.py for requirement decomposition via Clau

Port decomposition.py for requirement decomposition via Claude SDK

#### REQ_005.5: Port claude_runner.py Claude SDK wrapper with streaming supp

Port claude_runner.py Claude SDK wrapper with streaming support


## Success Criteria

- [x] All tests pass
- [x] All behaviors implemented
- [ ] Code reviewed

## Implementation Summary (2026-01-06)

### Implemented Files

**go/internal/planning/models.go**
- `RequirementNode` struct with ID, Description, Type, ParentID, Children, AcceptanceCriteria, Implementation, TestableProperties, FunctionID, RelatedConcepts, Category
- `RequirementHierarchy` container with metadata support
- `ImplementationComponents` (Frontend, Backend, Middleware, Shared)
- `TestableProperty` for property-based test mapping
- `DecompositionError` with typed error codes
- `PipelineResult` and `TechStackResult` models
- JSON serialization with proper tags

**go/internal/planning/steps.go**
- `StepResearch()` - Research phase execution
- `StepPlanning()` - Planning phase execution
- `StepPhaseDecomposition()` - Phase decomposition
- `StepMemorySync()` - 4-layer memory sync
- `StepBeadsIntegration()` - Beads issue creation and linking
- Helper functions: `extractBeadsID`, `extractPhaseName`, `annotateOverviewFile`, `annotatePhaseFile`

**go/internal/planning/pipeline.go**
- `PlanningPipeline` struct with `PipelineConfig`
- `Run()` method orchestrating 7-step pipeline:
  1. Research
  2. Memory Sync
  3. Requirement Decomposition
  4. Context Generation
  5. Planning
  6. Phase Decomposition
  7. Beads Integration
- `StepRequirementDecomposition()` and `StepContextGeneration()` helper steps

**go/internal/planning/decomposition.go**
- `DecomposeRequirements()` with Claude SDK integration
- `DecomposeRequirementsCLIFallback()` fallback implementation
- `DecompositionConfig` with max/min subprocess limits
- `DecompositionStats` for progress tracking
- `buildExtractionPrompt()` and `buildExpansionPrompt()` for LLM prompts

**go/internal/planning/claude_runner.go**
- `RunClaudeSync()` with timeout and streaming support
- `RunClaudeWithFile()` for file-based context
- `RunClaudeConversation()` for multi-turn conversations
- `ClaudeAvailable()` and `GetClaudeVersion()` utilities

**go/internal/planning/helpers.go**
- `ExtractFilePath()` - Extract paths from Claude output
- `ExtractOpenQuestions()` - Parse open questions sections
- `ExtractPhaseFiles()` - Extract phase file paths
- `ResolveFilePath()` - Multi-strategy path resolution
- `DiscoverThoughtsFiles()` - Discover files by type
- `ExtractResearchSummary()` - Extract summary from research
- `DetectQuestionIndicators()` - Detect question patterns
- `GenerateFunctionID()` - Generate semantic function IDs

### Test Coverage

50 tests passing:
- `claude_runner_test.go` - Claude wrapper tests
- `decomposition_test.go` - Decomposition logic tests
- `helpers_test.go` - Helper function tests
- `models_test.go` - Data model validation tests
- `pipeline_test.go` - Pipeline orchestration tests
- `steps_test.go` - Step execution tests