# Phase 01: The review_plan command must be incorporated into ...

## Requirements

### REQ_000: The review_plan command must be incorporated into the Go run

The review_plan command must be incorporated into the Go runtime following the established Cobra CLI command pattern used by existing commands (plan, resume, mcp-setup)

#### REQ_000.1: Create command definition in go/internal/cli/review_plan.go 

Create command definition in go/internal/cli/review_plan.go as a Cobra Command following the established pattern used by planCmd, mcpSetupCmd, and resumeCmd

##### Testable Behaviors

1. File go/internal/cli/review_plan.go exists and compiles without errors
2. Package declaration is 'package cli' matching other CLI files
3. Import statements include 'github.com/spf13/cobra' and 'github.com/silmari/context-engine/go/internal/planning'
4. Variable reviewPlanCmd is defined as *cobra.Command with Use field set to 'review-plan'
5. Command has Short description: 'Review an implementation plan before execution'
6. Command has Long description with usage examples matching style in plan.go
7. Command has RunE field pointing to runReviewPlan handler function
8. Flag variables are defined at package level following pattern in plan.go (reviewPlanPath, reviewPhase, reviewStep, reviewOutputPath, reviewAutonomyMode)
9. init() function defines all command-specific flags using Flags().StringVarP and Flags().BoolVarP patterns
10. Flags include: --plan-path (-p), --phase, --step, --output (-o), --autonomy-mode, --all-phases flag for full review
11. Flag normalization function normalizeUnderscoredFlags is applied for backward compatibility
12. Valid phase choices match PhaseType enum: research, decomposition, tdd_planning, multi_doc, beads_sync, implementation
13. Valid step choices match 5-step review framework: contracts, interfaces, promises, data_models, apis

#### REQ_000.2: Register review-plan command in root.go init() function usin

Register review-plan command in root.go init() function using rootCmd.AddCommand() following the established registration pattern

##### Testable Behaviors

1. root.go init() function includes 'rootCmd.AddCommand(reviewPlanCmd)' line
2. Registration appears in logical order with other subcommands (after planCmd, mcpSetupCmd, resumeCmd)
3. No import cycle errors after adding the command
4. Running 'context-engine --help' displays 'review-plan' in Available Commands list
5. Running 'context-engine review-plan --help' displays the command's help text
6. Command is accessible via 'context-engine review-plan' invocation
7. Build succeeds without errors after registration

#### REQ_000.3: Implement runReviewPlan handler function following the runPl

Implement runReviewPlan handler function following the runPlan pattern with parameter validation, path normalization, config creation, and pipeline invocation

##### Testable Behaviors

1. Function signature is 'func runReviewPlan(cmd *cobra.Command, args []string) error'
2. Default plan path handling: if reviewPlanPath is empty, search thoughts/searchable/shared/plans/ for recent plans
3. Path validation: if reviewPlanPath is provided, verify file exists using os.Stat
4. Path normalization: convert relative paths to absolute using filepath.Abs
5. Phase validation: if reviewPhase is provided, validate against validReviewPhases using validateChoice helper
6. Step validation: if reviewStep is provided, validate against validReviewSteps using validateChoice helper
7. Debug output: if debug flag is true, print all configuration values following pattern in runPlan
8. Create planning.ReviewConfig struct with validated parameters
9. Call planning.RunReview or equivalent function with config
10. Handle results: print success message with output path if review succeeds
11. Handle failures: print error message with failed step if review fails
12. Return nil on success, wrapped error on failure
13. Support --all-phases flag to iterate over all phases sequentially
14. Support running single phase + single step for targeted reviews

#### REQ_000.4: Add command aliases for convenient invocation of the review-

Add command aliases for convenient invocation of the review-plan command, following the pattern used by planCmd which has alias 'p'

##### Testable Behaviors

1. reviewPlanCmd has Aliases field defined in cobra.Command struct
2. Primary alias 'rp' is defined for quick invocation (context-engine rp)
3. Secondary alias 'review' is defined for clarity (context-engine review)
4. Running 'context-engine rp --help' displays same help as 'context-engine review-plan --help'
5. Running 'context-engine review --help' displays same help as 'context-engine review-plan --help'
6. All aliases accept the same flags as the primary command
7. Help text displays aliases in the format: 'Aliases: review-plan, rp, review'
8. Tab completion works for all aliases (if shell completion is configured)


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed