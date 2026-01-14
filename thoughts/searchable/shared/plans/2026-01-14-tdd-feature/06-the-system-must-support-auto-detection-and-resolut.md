# Phase 06: The system must support auto-detection and resolut...

## Requirements

### REQ_005: The system must support auto-detection and resolution of pla

The system must support auto-detection and resolution of plan and hierarchy file relationships

#### REQ_005.1: Detect file type based on .md vs .json extension to determin

Detect file type based on .md vs .json extension to determine processing path

##### Testable Behaviors

1. MUST return 'markdown' for files with .md extension regardless of case (.MD, .Md)
2. MUST return 'json' for files with .json extension regardless of case (.JSON, .Json)
3. MUST return 'unknown' for files with other extensions or no extension
4. MUST handle Path objects and string paths as input
5. MUST validate file existence before type detection
6. MUST raise FileNotFoundError if file does not exist
7. MUST support both absolute and relative paths
8. SHOULD log a warning when file extension doesn't match content (e.g., .md file containing JSON)

#### REQ_005.2: If Markdown plan provided, search for sibling requirement_hi

If Markdown plan provided, search for sibling requirement_hierarchy.json in same directory

##### Testable Behaviors

1. MUST search for 'requirement_hierarchy.json' file in same directory as provided .md file
2. MUST search for alternative naming patterns: 'requirements_hierarchy.json', 'hierarchy.json'
3. MUST return absolute Path to found JSON file or None if not found
4. MUST validate JSON file is parseable as RequirementHierarchy before returning
5. MUST log info message when sibling JSON is found with path details
6. MUST log debug message when no sibling JSON found
7. SHOULD support searching parent directory if same-level search fails (configurable)
8. SHOULD cache directory listing to avoid repeated filesystem calls
9. MUST handle permission errors gracefully by returning None with warning log

#### REQ_005.3: If JSON hierarchy provided and no TDD plan exists, create TD

If JSON hierarchy provided and no TDD plan exists, create TDD plan from hierarchy

##### Testable Behaviors

1. MUST check for existing TDD plan files (00-overview.md pattern) in same directory as hierarchy JSON
2. MUST check for existing TDD plan in thoughts/searchable/shared/plans/ directory with matching date prefix
3. MUST call TDDPlanningPhase.execute() to generate plan if no existing plan found
4. MUST return path to existing plan if found, avoiding duplicate generation
5. MUST create plan directory following naming convention: YYYY-MM-DD-tdd-{plan_name}/
6. MUST generate overview (00-overview.md) and phase files (01-xxx.md, 02-xxx.md)
7. MUST preserve hierarchy_path in generated plan metadata
8. MUST log info message indicating whether existing plan was found or new plan generated
9. SHOULD validate generated plan contains all requirements from hierarchy
10. MUST handle TDDPlanningPhase failures gracefully with PhaseResult.FAILED status

#### REQ_005.4: Support path resolution via resolve_file_path() for relative

Support path resolution via resolve_file_path() for relative paths and filenames

##### Testable Behaviors

1. MUST accept absolute paths and verify existence before returning
2. MUST accept relative paths from project root and resolve to absolute
3. MUST accept just filename and search in thoughts/searchable/shared/{file_type}/ directory
4. MUST accept partial filename and perform fuzzy match on date-prefixed files
5. MUST support file_type parameter: 'research', 'plans', 'hierarchy' (new)
6. MUST search multiple directory variants: thoughts/shared/, thoughts/searchable/shared/
7. MUST return first match for fuzzy searches, prioritizing exact matches
8. MUST handle .json files when file_type='hierarchy' by searching plans directories
9. MUST return None with debug log when no match found
10. SHOULD support tilde expansion for home directory paths (~)
11. MUST maintain backward compatibility with existing resolve_file_path() signature

#### REQ_005.5: Maintain sibling file relationship pattern: plans/date-featu

Maintain sibling file relationship pattern: plans/date-feature/requirement_hierarchy.json + plans/date-feature/00-overview.md

##### Testable Behaviors

1. MUST enforce directory structure: thoughts/searchable/shared/plans/YYYY-MM-DD-{plan_name}/
2. MUST ensure requirement_hierarchy.json and 00-overview.md exist in same directory
3. MUST create missing sibling file when one is provided (hierarchy -> plan or plan -> hierarchy lookup)
4. MUST validate both files reference each other in metadata
5. MUST update hierarchy JSON metadata.plan_path when TDD plan is generated
6. MUST update plan overview front matter with hierarchy_path when plan is generated
7. MUST support atomic operations: either both files valid or operation fails
8. MUST provide method to check relationship integrity: is_sibling_pair_valid(dir_path)
9. SHOULD support listing all valid sibling pairs in project for discovery
10. MUST log warning when relationship is broken (one file exists without other)


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed