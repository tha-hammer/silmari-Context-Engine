# Phase 04: The system must port all 18 planning pipeline modu...

## Requirements

### REQ_003: The system must port all 18 planning pipeline module files t

The system must port all 18 planning pipeline module files to Go internal packages

#### REQ_003.1: Port models.py core data models including RequirementNode, R

Port models.py core data models including RequirementNode, RequirementHierarchy, ImplementationComponents, TestableProperty, and all supporting structs to Go internal/models package with full JSON serialization and validation

##### Testable Behaviors

1. RequirementNode struct implements all 11 fields: ID, Description, Type, ParentID, Children, AcceptanceCriteria, Implementation, TestableProperties, FunctionID, RelatedConcepts, Category
2. RequirementHierarchy struct with nested RequirementNode slice and tree traversal methods
3. ImplementationComponents struct with frontend, backend, middleware, shared slices
4. TestableProperty struct with property name, generator function, and assertions
5. All structs have proper JSON tags including omitempty for optional fields
6. Pointer types used for optional fields (ParentID *string, FunctionID *string, Implementation *ImplementationComponents)
7. Validate() error method on each struct performs post-init validation equivalent to Python __post_init__
8. Type field validation against valid types: parent, sub_process, implementation
9. ID format validation for REQ_XXX(.Y.Z) pattern using regexp
10. Unit tests achieve 100% coverage for all struct methods and validation logic
11. JSON round-trip tests verify serialization/deserialization preserves all data
12. Nested Children hierarchy serializes correctly to arbitrary depth

#### REQ_003.2: Port steps.py implementing all 7 pipeline step implementatio

Port steps.py implementing all 7 pipeline step implementations as Go interfaces and concrete types with step execution, progress tracking, and error handling

##### Testable Behaviors

1. Step interface defined with Execute(ctx context.Context, input StepInput) (StepOutput, error) method
2. StepInput and StepOutput structs defined with common fields for data passing between steps
3. All 7 pipeline steps implemented: ProjectInit, FeatureDiscovery, RequirementDecomposition, ContextGeneration, PropertyGeneration, ImplementationPlanning, ValidationStep
4. Each step implements Name() string method returning step identifier
5. Each step implements Progress() float64 method for progress reporting
6. Steps accept StepConfig struct for customizable behavior
7. Context.Context passed through all steps for timeout and cancellation support
8. Error wrapping with fmt.Errorf and %w for error chain preservation
9. Step results include timing metrics (started, completed, duration)
10. Step failure states propagate correctly without crashing pipeline
11. Unit tests verify each step can execute independently
12. Integration tests verify steps chain correctly in sequence
13. Mock implementations available for testing downstream consumers

#### REQ_003.3: Port pipeline.py main PlanningPipeline orchestrator that coo

Port pipeline.py main PlanningPipeline orchestrator that coordinates 7-step execution, manages state transitions, handles checkpointing, and provides progress reporting

##### Testable Behaviors

1. PlanningPipeline struct holds ordered slice of Step implementations
2. NewPlanningPipeline constructor accepts PipelineConfig with step selection
3. Run(ctx context.Context, projectPath string) (PipelineResult, error) executes full pipeline
4. RunStep(ctx context.Context, stepName string) executes single step for debugging
5. Resume(ctx context.Context, checkpointPath string) resumes from checkpoint
6. Pipeline state machine tracks: NotStarted, Running, Paused, Completed, Failed
7. Checkpoint created after each successful step completion
8. Progress callback invoked with (currentStep, totalSteps, stepProgress) on state change
9. Graceful shutdown on context cancellation saves checkpoint before exit
10. Step dependency graph validated before execution starts
11. Parallel step execution supported for independent steps using goroutines
12. Step output from previous steps available to subsequent steps via StepInput
13. Pipeline result includes all step outputs, timing, and final artifacts
14. Error aggregation collects all step errors for comprehensive reporting
15. Unit tests verify state transitions and checkpoint creation
16. Integration tests run full pipeline on sample project

#### REQ_003.4: Port decomposition.py requirement decomposition via Claude S

Port decomposition.py requirement decomposition via Claude SDK including recursive requirement breakdown, hierarchy building, and LLM prompt construction for structured output

##### Testable Behaviors

1. Decomposer struct wraps Claude CLI or HTTP client for LLM calls
2. DecomposeRequirement(ctx context.Context, requirement string) ([]RequirementNode, error) returns child nodes
3. Recursive decomposition continues until leaf nodes (implementation type) reached
4. Maximum recursion depth configurable (default 5 levels)
5. Prompt templates stored as embedded Go strings using embed package
6. Claude response parsed into RequirementNode structs with validation
7. Streaming response support for long-running decomposition using io.Reader
8. Retry logic with exponential backoff for transient Claude API failures
9. Rate limiting to respect Claude API quotas
10. Decomposition result cached by requirement hash to avoid redundant calls
11. Parent-child relationships correctly established in returned hierarchy
12. Each node assigned unique ID following REQ_XXX.Y.Z pattern
13. Acceptance criteria extracted from Claude response for each node
14. Unit tests with mocked Claude responses verify parsing logic
15. Integration tests verify actual Claude CLI subprocess invocation

#### REQ_003.5: Port context_generation.py for tech stack detection, file gr

Port context_generation.py for tech stack detection, file grouping by purpose, dependency analysis, and project structure understanding to generate context for LLM prompts

##### Testable Behaviors

1. ContextGenerator struct analyzes project directory for tech stack
2. DetectTechStack(projectPath string) (TechStack, error) identifies languages, frameworks, build tools
3. GroupFilesByPurpose(projectPath string) (FileGroups, error) categorizes files into src, test, config, docs, assets
4. ParseDependencies(projectPath string) (Dependencies, error) extracts from package.json, go.mod, requirements.txt, Cargo.toml
5. Respects .gitignore patterns when traversing directory tree
6. Language detection based on file extensions and content patterns
7. Framework detection from dependency files and directory structure
8. Build tool detection (make, npm, cargo, go, pytest) from config files
9. File importance scoring based on size, location, and type
10. Context output formatted for LLM consumption with file summaries
11. Parallel file scanning using goroutines with worker pool
12. Memory-efficient streaming for large codebases (>10,000 files)
13. TechStack struct includes: languages, frameworks, buildTools, testFrameworks
14. FileGroups struct includes: source, tests, config, documentation, assets maps
15. Unit tests verify detection accuracy for Go, Python, TypeScript, Rust projects
16. Integration tests run on actual project directories


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed