Epoch (Feature):
  - silmari-Context-Engine-0rkh4: Add create_tdd_plan Step After Decomposition

  Behaviors (Tasks):

  | ID                           | Behavior                                         | Status  | Dependencies |
  |------------------------------|--------------------------------------------------|---------|--------------|
  | silmari-Context-Engine-h6pj4 | 3.1: Load TDD Plan Instructions                  | Ready   | None         |
  | silmari-Context-Engine-fxsb7 | 3.2: Process Instructions with Hierarchy Context | Ready   | None         |
  | silmari-Context-Engine-5anva | 3.2.1: Map Acceptance Criteria to TDD Test Cases | Blocked | ← 3.2        |
  | silmari-Context-Engine-kqzbv | 3.3: Invoke Claude with Processed Prompt         | Blocked | ← 3.1, 3.2   |
  | silmari-Context-Engine-shftt | 3.4: Extract Plan File Paths from Output         | Blocked | ← 3.3        |
  | silmari-Context-Engine-ygelw | 3.5: Return Structured Result                    | Blocked | ← 3.4        |

  Dependency Chain:
  3.1 (Load Instructions) ──┐
                            ├──→ 3.3 (Invoke Claude) ──→ 3.4 (Extract Paths) ──→ 3.5 (Return Result)
  3.2 (Process Hierarchy) ──┤
           │                │
           └──→ 3.2.1 (Map Acceptance Criteria)

# TDD Plan: Add create_tdd_plan Step After Decomposition

## Overview

Add a new step function to both Python (`planning_pipeline/decomposition.py`) and Go (`go/internal/planning/decomposition.go`) that invokes the `create_tdd_plan` skill after `decompose_requirements()` returns a `RequirementHierarchy`.

## Motivation

Currently, `decompose_requirements()` returns a `RequirementHierarchy` but there's no automated step to create TDD plan documents from it. The user must manually invoke the `create_tdd_plan` skill. This feature adds a programmatic way to chain these steps.

## Design

### Function Signature

**Python:**
```python
def create_tdd_plan_from_hierarchy(
    project_path: Path,
    hierarchy: RequirementHierarchy,
    plan_name: str = "feature",
    additional_context: str = "",
) -> dict[str, Any]:
    """Create TDD plan documents from a requirement hierarchy.

    Args:
        project_path: Root path of the project
        hierarchy: RequirementHierarchy from decompose_requirements()
        plan_name: Name for the plan (used in filenames)
        additional_context: Optional additional context

    Returns:
        Dictionary with keys:
        - success: bool
        - plan_paths: list of created plan file paths
        - output: raw Claude output
    """
```

**Go:**
```go
func CreateTDDPlanFromHierarchy(
    projectPath string,
    hierarchy *RequirementHierarchy,
    planName string,
    additionalContext string,
) *StepResult
```

### Implementation Pattern

Follow the existing `step_planning()` / `StepPlanning()` pattern:

1. Load `.claude/commands/create_tdd_plan.md`
2. Process instructions (remove interactive sections, insert hierarchy context)
3. Call `run_claude_sync()` / `RunClaudeSync()` with processed prompt
4. Extract created file paths from output
5. Return result with success status and file paths

### Key Differences from `step_planning()`

| Aspect | `step_planning()` | `create_tdd_plan_from_hierarchy()` |
|--------|-------------------|-------------------------------------|
| Input | Research document path | RequirementHierarchy object |
| Context | Reads research file | Serializes hierarchy to JSON/text |
| Phase | Earlier in pipeline | After decomposition |

---

## Behaviors

### Behavior 3.1: Load TDD Plan Instructions

**Given** a valid project path with `.claude/commands/create_tdd_plan.md`
**When** `create_tdd_plan_from_hierarchy()` is called
**Then** it loads the instruction file successfully
**And** returns an error if the file is missing

**Test Cases:**
- Valid project with instruction file loads successfully
- Missing instruction file returns descriptive error
- Empty instruction file is handled gracefully

### Behavior 3.2: Process Instructions with Hierarchy Context

**Given** loaded instruction content and a RequirementHierarchy
**When** processing the prompt
**Then** the "Initial Response" section is removed
**And** a "Requirement Hierarchy" section is inserted
**And** the hierarchy is serialized as complete JSON with ALL keys preserved

**Test Cases:**
- Hierarchy with 5 requirements is serialized correctly as JSON
- Nested children are recursively serialized with all fields
- Empty hierarchy produces valid prompt with empty `requirements` array
- Date placeholders are replaced with current date
- **All requirement keys are preserved in serialization:**
  - `id` - Requirement identifier (e.g., "REQ_001.1")
  - `description` - Full requirement text
  - `type` - "parent", "sub_process", or "implementation"
  - `parent_id` - Parent reference (null for top-level)
  - `children` - Recursively serialized child array
  - `acceptance_criteria` - **CRITICAL: Complete list of testable conditions**
  - `implementation` - Object with frontend/backend/middleware/shared arrays
  - `testable_properties` - Property-based test specs
  - `function_id` - Service.method identifier
  - `related_concepts` - Technology context list
  - `category` - Requirement category
- **Acceptance criteria completeness verified:**
  - Requirements with acceptance_criteria have all items in output
  - Empty acceptance_criteria arrays are preserved (not omitted)
  - Multi-line acceptance criteria are properly escaped in JSON
- **Implementation components are preserved:**
  - Non-null implementation objects include all 4 component arrays
  - Null implementation is serialized as `null` (not omitted)
- Prompt contains explicit instructions to create tests from acceptance_criteria

### Behavior 3.2.1: Map Acceptance Criteria to TDD Test Cases

**Given** a serialized requirement hierarchy with acceptance_criteria
**When** Claude processes the prompt
**Then** each acceptance criterion in the hierarchy maps to at least one test case
**And** test case names reflect the acceptance criterion being verified
**And** requirements without acceptance_criteria still get documented (but may have fewer tests)

**Test Cases:**
- Requirement with 4 acceptance criteria produces at least 4 test cases
- Acceptance criterion "Email format validated before submission" maps to test like `test_email_format_validation_rejects_invalid_email`
- Parent requirements with empty acceptance_criteria are not skipped (children may have criteria)
- Implementation.backend items influence test file location (e.g., tests/api/ for API endpoints)
- Implementation.frontend items may skip backend unit tests but get integration tests
- function_id is used in test function naming (e.g., `AuthService.validateLoginForm` → `test_auth_service_validate_login_form_*`)

**Data Flow for Acceptance Criteria:**
```
RequirementHierarchy.to_dict()
    └── requirements[].acceptance_criteria[]
         └── "Email format validated before submission"
              └── Test Case: test_email_validation_rejects_malformed_input()
              └── Test Case: test_email_validation_accepts_valid_format()
```

**Example Mapping from JSON to TDD Plan:**

Input (from requirements_hierarchy.json):
```json
{
  "id": "REQ_000.1",
  "description": "Initialize and rebuild Working Context at session start",
  "acceptance_criteria": [
    "Working Context is completely rebuilt from scratch at session start within 5 seconds",
    "All active files from the previous session are loaded and indexed",
    "Session goals and current task state are restored from checkpoint files"
  ],
  "function_id": "WorkingContextManager.initialize_session_context"
}
```

Expected TDD Plan Output:
```markdown
### Behavior: Initialize Working Context at Session Start

**Given**: A new session starting
**When**: `WorkingContextManager.initialize_session_context()` is called
**Then**: Working context is completely rebuilt

#### 🔴 Red: Test Cases from Acceptance Criteria

```python
def test_initialize_context_completes_within_5_seconds():
    """AC: Working Context is completely rebuilt from scratch at session start within 5 seconds"""
    ...

def test_initialize_context_loads_all_active_files():
    """AC: All active files from the previous session are loaded and indexed"""
    ...

def test_initialize_context_restores_session_goals():
    """AC: Session goals and current task state are restored from checkpoint files"""
    ...
```
```

### Behavior 3.3: Invoke Claude with Processed Prompt

**Given** a processed prompt with hierarchy context
**When** calling `run_claude_sync()` / `RunClaudeSync()`
**Then** the function uses a 20-minute timeout (1200s)
**And** streaming is enabled for progress visibility
**And** the project path is passed for working directory context

**Test Cases:**
- Successful Claude invocation returns output
- Timeout handling works correctly
- Claude failure returns structured error

### Behavior 3.4: Extract Plan File Paths from Output

**Given** Claude output containing created file paths
**When** extracting plan paths
**Then** all paths matching `thoughts/searchable/shared/plans/*.md` are found
**And** the first path is available for backward compatibility
**And** multiple plan files (phase files) are all captured

**Test Cases:**
- Single plan file is extracted correctly
- Multiple plan files are all captured in `plan_paths`
- No plan file returns empty list (not failure)
- Relative paths are normalized

### Behavior 3.5: Return Structured Result

**Given** successful Claude execution
**When** the function completes
**Then** it returns `{"success": True, "plan_paths": [...], "output": "..."}`
**And** on failure it returns `{"success": False, "error": "..."}`

**Test Cases:**
- Success case includes all created file paths
- Failure case includes descriptive error message
- Output is preserved for debugging

---

## Implementation Details

### Python Implementation Location

**File:** `planning_pipeline/decomposition.py`

Add after `decompose_requirements()` function (around line 800):

```python
def create_tdd_plan_from_hierarchy(
    project_path: Path,
    hierarchy: RequirementHierarchy,
    plan_name: str = "feature",
    additional_context: str = "",
) -> dict[str, Any]:
    """Create TDD plan documents from requirement hierarchy."""
```

### Go Implementation Location

**File:** `go/internal/planning/decomposition.go`

Add after `DecomposeRequirements()` function (after line 238):

```go
// CreateTDDPlanFromHierarchy creates TDD plan documents from a requirement hierarchy.
func CreateTDDPlanFromHierarchy(
    projectPath string,
    hierarchy *RequirementHierarchy,
    planName string,
    additionalContext string,
) *StepResult {
```

### Hierarchy Serialization Format

The hierarchy **must be serialized as complete JSON** to provide Claude with all requirement data needed for TDD planning. Each requirement contains rich structured data that must be preserved:

**Required Keys for Each Requirement (from `RequirementNode.to_dict()`):**

| Key | Type | TDD Relevance |
|-----|------|---------------|
| `id` | string | **Critical** - Used to identify and trace requirements in TDD plan |
| `description` | string | **Critical** - Full requirement text for understanding scope |
| `type` | string | **Important** - "parent", "sub_process", "implementation" determines test granularity |
| `parent_id` | string? | Useful for tracing hierarchies |
| `children` | array | **Critical** - Recursive nested requirements |
| `acceptance_criteria` | array[string] | **Critical for TDD** - Exact conditions tests must verify |
| `implementation` | object? | **Important** - frontend/backend/middleware/shared component breakdown |
| `testable_properties` | array | Property-based test specifications |
| `function_id` | string? | Service.method identifier for implementation targeting |
| `related_concepts` | array[string] | Technology context for test strategy |
| `category` | string | "functional", "security", etc. for test categorization |

**Serialization Strategy:**

The hierarchy should be serialized as **structured JSON** (not summarized text) to ensure Claude receives all acceptance criteria and implementation details:

```json
{
  "requirements": [
    {
      "id": "REQ_001",
      "description": "User authentication system",
      "type": "parent",
      "parent_id": null,
      "children": [
        {
          "id": "REQ_001.1",
          "description": "Login form validation",
          "type": "sub_process",
          "parent_id": "REQ_001",
          "children": [],
          "acceptance_criteria": [
            "Email format validated before submission",
            "Password minimum 8 characters enforced",
            "Clear error messages displayed for invalid inputs",
            "Form submission blocked until all validations pass"
          ],
          "implementation": {
            "frontend": ["Login form component", "Validation feedback UI"],
            "backend": ["POST /api/auth/validate endpoint"],
            "middleware": ["Input sanitization"],
            "shared": ["ValidationResult model", "AuthError types"]
          },
          "testable_properties": [],
          "function_id": "AuthService.validateLoginForm",
          "related_concepts": ["form validation", "client-side validation", "error handling"],
          "category": "functional"
        }
      ],
      "acceptance_criteria": [],
      "implementation": null,
      "testable_properties": [],
      "function_id": null,
      "related_concepts": [],
      "category": "functional"
    }
  ],
  "metadata": {
    "source": "decomposition",
    "decomposed_at": "2026-01-14T11:35:09.973373"
  }
}
```

**Why Full JSON is Required:**

1. **Acceptance Criteria Drive TDD** - The `acceptance_criteria` array contains the exact conditions that tests must verify. Each criterion becomes a test case.

2. **Implementation Details Guide Test Structure** - The `implementation` object shows which layers (frontend/backend/middleware/shared) need tests, helping organize test files.

3. **Function IDs Provide Test Targeting** - The `function_id` (e.g., "AuthService.validateLoginForm") tells Claude exactly which function needs tests.

4. **Related Concepts Inform Mocking Strategy** - Knowing related technologies helps determine what to mock in tests.

**Prompt Insertion Format:**

```python
def _serialize_hierarchy_for_prompt(hierarchy: RequirementHierarchy) -> str:
    """Serialize hierarchy to JSON string for Claude prompt insertion."""
    return json.dumps(hierarchy.to_dict(), indent=2)
```

Insert into prompt as:

```
## Requirement Hierarchy

The following JSON contains the complete requirement hierarchy with all acceptance criteria.
Each requirement's `acceptance_criteria` array contains the conditions that TDD tests must verify.

```json
{hierarchy_json}
```

For each requirement with acceptance criteria:
1. Create test cases for EACH acceptance criterion
2. Use the `implementation` object to determine test file locations
3. Use the `function_id` to name test functions appropriately


## Dependencies

- Requires `run_claude_sync()` / `RunClaudeSync()` from `claude_runner`
- Requires `extract_file_path()` / `ExtractFilePath()` helper functions
- Requires `.claude/commands/create_tdd_plan.md` to exist in project

## Success Criteria

1. Function exists in both Python and Go implementations
2. All 6 behaviors pass their test cases (including 3.2.1)
3. Function integrates with existing pipeline (can be called after `decompose_requirements()`)
4. Created plan files follow existing naming conventions
5. Error handling matches existing patterns in codebase
6. **Requirement data completeness verified:**
   - All 11 keys from `RequirementNode.to_dict()` are preserved in serialization
   - `acceptance_criteria` arrays are passed in full (not truncated or summarized)
   - `implementation` objects include all 4 component arrays (frontend/backend/middleware/shared)
   - Nested `children` arrays are recursively serialized with complete data
7. **Acceptance criteria to test case mapping verified:**
   - Each acceptance criterion in the hierarchy results in at least one test case
   - Test function names reference the requirement ID or function_id
   - Test docstrings include the original acceptance criterion text
8. **JSON serialization roundtrip test:**
   - `hierarchy.to_dict()` output can be `json.dumps()`'d without errors
   - Output contains valid JSON parseable by Claude
   - No data loss between Python object and JSON string
