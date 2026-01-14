# Phase 03: The system must produce two distinct artifact type...

## Requirements

### REQ_002: The system must produce two distinct artifact types at diffe

The system must produce two distinct artifact types at different pipeline phases: TDD Plan Markdown files and Requirement Hierarchy JSON files

#### REQ_002.1: TDDPlanningPhase must produce human-readable Markdown files 

TDDPlanningPhase must produce human-readable Markdown files with .md extension

##### Testable Behaviors

1. TDDPlanningPhase.execute() produces one or more .md files as output artifacts
2. All generated files have .md extension, not .markdown or other variations
3. Generated Markdown files are human-readable without special tooling (viewable in any text editor)
4. Markdown syntax is valid and renders correctly in GitHub/GitLab markdown previews
5. Each generated file includes proper Markdown headers (# for H1, ## for H2, etc.)
6. Files are saved with UTF-8 encoding to support special characters
7. PhaseResult.artifacts list contains paths to all generated .md files
8. File names follow naming convention: NN-phase-N-description.md (e.g., 01-phase-1-project-setup.md)
9. 00-overview.md file is always generated as the primary entry point
10. Generated files are written atomically to prevent partial writes on failure

#### REQ_002.2: DecompositionPhase must produce machine-readable JSON files 

DecompositionPhase must produce machine-readable JSON files with .json extension

##### Testable Behaviors

1. DecompositionPhase.execute() produces exactly one .json file named requirement_hierarchy.json
2. Generated file has .json extension, not .JSON or other variations
3. JSON output is valid and parseable by standard JSON parsers (json.load() succeeds)
4. JSON is formatted with 2-space indentation for human readability while maintaining machine parseability
5. JSON includes UTF-8 encoding declaration for special character support
6. Output JSON passes RequirementHierarchy.from_dict() deserialization without errors
7. PhaseResult.artifacts list contains the path to requirement_hierarchy.json
8. JSON file is written atomically to prevent partial writes on failure
9. Generated JSON is deterministic (same input produces identical output for version control)

#### REQ_002.3: TDD Plan Markdown must contain phases, testable behaviors, a

TDD Plan Markdown must contain phases, testable behaviors, and requirements tables

##### Testable Behaviors

1. 00-overview.md contains Phase Summary table with columns: Phase, Description, Requirements, Status
2. 00-overview.md contains Requirements section with hierarchical structure (###, ####, #####)
3. Each requirement (REQ_XXX) has its own section with description and child requirements
4. Testable Behaviors are rendered as numbered lists under each leaf requirement
5. Phase files (01-phase-N-*.md) contain: Overview, Dependencies, Behaviors Covered, Changes Required sections
6. Changes Required section includes New Files table with columns: File, Purpose
7. TDD Cycle section includes Red (failing tests), Green (implement), Refactor subsections
8. Success Criteria section includes Automated and Manual checklists with [ ] checkbox syntax
9. Testable Function section includes executable Python code block demonstrating phase completion
10. All markdown tables are properly formatted with header separators (|---|---|)

#### REQ_002.4: Requirement Hierarchy JSON must contain nested requirement t

Requirement Hierarchy JSON must contain nested requirement tree with id, description, type, parent_id, children, acceptance_criteria, and category fields

##### Testable Behaviors

1. Each RequirementNode serializes with required fields: id (string), description (string), type (enum: parent|sub_process|implementation)
2. Each RequirementNode serializes parent_id as string or null for root nodes
3. Each RequirementNode serializes children as array of nested RequirementNode objects (recursive)
4. Each RequirementNode serializes acceptance_criteria as array of strings
5. Each RequirementNode serializes category as enum: functional|non_functional|security|performance|usability|integration
6. Top-level JSON object contains 'requirements' array and 'metadata' object
7. Metadata object contains source, decomposition_stats with requirements_found, subprocesses_expanded, total_nodes
8. All id fields follow REQ_XXX or REQ_XXX.N format (e.g., REQ_001, REQ_001.2)
9. parent_id correctly references the parent node's id, or is null for top-level requirements
10. JSON passes round-trip test: RequirementHierarchy.from_dict(hierarchy.to_dict()) produces equivalent object

#### REQ_002.5: Store artifacts in appropriate directory structure under tho

Store artifacts in appropriate directory structure under thoughts/searchable/shared/plans/

##### Testable Behaviors

1. All artifacts are stored under thoughts/searchable/shared/plans/ base directory
2. Each pipeline run creates a new timestamped directory: YYYY-MM-DD-HH-MM-tdd-{plan_name}/
3. Requirement hierarchy JSON is stored at: {plan_dir}/requirement_hierarchy.json
4. TDD plan overview is stored at: {plan_dir}/00-overview.md
5. Phase-specific markdown files are stored at: {plan_dir}/NN-phase-N-{slugified-name}.md
6. Directory names are slugified (lowercase, hyphens instead of spaces, no special characters)
7. Directory is created with appropriate permissions (755 for directories, 644 for files)
8. If directory already exists, append incrementing suffix (-01, -02) to avoid overwriting
9. All paths are resolved to absolute paths before storage operations
10. Storage operation is atomic: either all files are written or none (use temp directory + rename)


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed