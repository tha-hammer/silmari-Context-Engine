# Phase 04: The system must maintain consistent CLI option beh...

## Requirements

### REQ_003: The system must maintain consistent CLI option behavior acro

The system must maintain consistent CLI option behavior across all orchestrator implementations

#### REQ_003.1: silmari_rlm_act/cli.py must accept JSON hierarchy files via 

silmari_rlm_act/cli.py must accept JSON hierarchy files via --plan-path, validating the JSON structure against RequirementHierarchy schema and skipping Research and Decomposition phases when a valid hierarchy is provided

##### Testable Behaviors

1. The --plan-path option must accept only files with valid JSON format
2. Invalid JSON must produce a clear error message with the parse error details
3. The JSON must validate against RequirementHierarchy.from_dict() schema
4. Each requirement node must have 'type' in ['parent', 'sub_process', 'implementation']
5. Each requirement node must have 'category' in ['functional', 'non_functional', 'security', 'performance', 'usability', 'integration']
6. Each requirement node must have a non-empty 'description' field
7. When a valid JSON hierarchy is provided, ResearchPhase must be skipped
8. When a valid JSON hierarchy is provided, DecompositionPhase must be skipped
9. The pipeline must proceed directly to TDDPlanningPhase with the loaded hierarchy
10. The result metadata must include 'requirements_count' and 'total_nodes' fields
11. The help text must clearly state: 'Path to existing requirement hierarchy JSON file (skips research and decomposition phases)'
12. The internal variable must be passed as 'hierarchy_path' to pipeline.run()
13. click.Path(exists=True, file_okay=True, dir_okay=False) must validate file existence
14. PhaseResult with status=FAILED and descriptive errors array must be returned for invalid JSON

#### REQ_003.2: resume_pipeline.py must accept Markdown plan files via --pla

resume_pipeline.py must accept Markdown plan files via --plan-path for the decomposition step, supporting both --plan-path and --plan_path argument forms with proper path validation

##### Testable Behaviors

1. The --plan-path option must accept .md (Markdown) files
2. The --plan_path alias must work identically to --plan-path
3. The dest parameter must be set to 'plan_path' for internal variable naming
4. The help text must state: 'Path to plan document (required for decomposition step)'
5. Presence check validation must be performed (file must exist)
6. The option must be required when running the decomposition step
7. Example usage in help must show: 'resume_pipeline.py decomposition --plan-path thoughts/searchable/plans/2025-12-31-plan.md'
8. The system must accept full paths, relative paths to .md files
9. Error message must clearly indicate when plan-path is missing for decomposition step
10. The Markdown file path must be passed to the decomposition orchestrator

#### REQ_003.3: planning_orchestrator.py must accept Markdown .md files via 

planning_orchestrator.py must accept Markdown .md files via --plan-path with auto-resolution capabilities, supporting full paths, relative paths, and filename-only inputs with interactive fallback

##### Testable Behaviors

1. The --plan-path option must accept Markdown .md files explicitly
2. The --plan_path alias must work identically to --plan-path
3. The dest parameter must be set to 'plan_path' for internal variable naming
4. The metavar must be set to 'FILE' for help text clarity
5. The help text must state: 'Plan .md file: full path, relative path, or just filename (auto-resolved)'
6. Full absolute paths must be accepted and validated directly
7. Relative paths must be resolved from current working directory
8. Filename-only inputs must trigger auto-resolution via resolve_file_path()
9. Auto-resolution must search in standard plan directories (e.g., thoughts/searchable/plans/)
10. When auto-resolution fails, interactive fallback must prompt user for path
11. Multiple matching files during auto-resolution must present selection to user
12. The resolved path must be validated for existence before proceeding
13. Clear error messages must be provided when file cannot be found or resolved

#### REQ_003.4: Document the expected file type for each CLI implementation 

Document the expected file type for each CLI implementation clearly in help text, ensuring users understand the distinction between JSON hierarchy files and Markdown plan files across different orchestrators

##### Testable Behaviors

1. silmari_rlm_act/cli.py help text must explicitly state: 'Path to existing requirement hierarchy JSON file (skips research and decomposition phases)'
2. silmari_rlm_act/cli.py help text must NOT use 'TDD plan/hierarchy JSON' conflated terminology
3. resume_pipeline.py help text must explicitly state: 'Path to TDD plan Markdown document (.md) required for decomposition step'
4. planning_orchestrator.py help text must explicitly state: 'Path to TDD plan Markdown file (.md): full path, relative path, or just filename (auto-resolved)'
5. Each CLI must include example usage showing correct file extension in help output
6. Help text must explain what phases are skipped when the option is used (for silmari_rlm_act)
7. Help text must explain the relationship between JSON hierarchy and Markdown plan files
8. Consider adding a --help-files option that explains the artifact file types in detail
9. Documentation must be consistent across all three CLI implementations
10. Error messages must reference the correct expected file type when validation fails


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed