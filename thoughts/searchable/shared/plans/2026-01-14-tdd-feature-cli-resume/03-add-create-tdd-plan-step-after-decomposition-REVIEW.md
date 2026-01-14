# Plan Review Report: Add create_tdd_plan Step After Decomposition

**Plan Reviewed**: `thoughts/searchable/shared/plans/2026-01-14-tdd-feature/03-add-create-tdd-plan-step-after-decomposition.md`
**Review Date**: 2026-01-14
**Reviewer**: Claude Code (automated plan review)

---

## Review Summary

| Category | Status | Issues Found |
|----------|--------|--------------|
| Contracts | ⚠️ | 3 issues |
| Interfaces | ✅ | 1 minor issue |
| Promises | ⚠️ | 2 issues |
| Data Models | ✅ | 0 issues |
| APIs | ✅ | N/A (internal function) |

---

## Contract Review

### Well-Defined:
- ✅ **Input contract for Python**: `project_path: Path, hierarchy: RequirementHierarchy, plan_name: str, additional_context: str`
- ✅ **Input contract for Go**: `projectPath string, hierarchy *RequirementHierarchy, planName string, additionalContext string`
- ✅ **Output contract structure**: Returns dict/struct with `success`, `plan_paths`, `output` keys
- ✅ **Component boundary**: Clear separation - function loads instructions, invokes Claude, extracts paths
- ✅ **Precondition documented**: Requires `.claude/commands/create_tdd_plan.md` to exist

### Missing or Unclear:

- ⚠️ **Missing error code enumeration**: The plan specifies returning `{"success": False, "error": "..."}` but doesn't enumerate specific error types. The existing codebase uses `DecompositionErrorCode` enum with specific codes like `EMPTY_CONTENT`, `BAML_API_ERROR`, `INVALID_JSON`.

  **Impact**: Without enumerated error codes, callers cannot programmatically handle specific failure modes.

  **Recommendation**: Define error codes matching the existing pattern:
  ```python
  class TDDPlanErrorCode(Enum):
      MISSING_INSTRUCTION_FILE = "missing_instruction_file"
      EMPTY_HIERARCHY = "empty_hierarchy"
      CLAUDE_INVOCATION_FAILED = "claude_invocation_failed"
      NO_PLAN_FILES_CREATED = "no_plan_files_created"
  ```

- ⚠️ **Missing instruction file load error contract**: Behavior 3.1 says "returns an error if the file is missing" but doesn't specify the error structure or message format.

  **Impact**: Inconsistent error handling between Python and Go implementations.

  **Recommendation**: Specify exact error message format:
  ```python
  return {"success": False, "error": f"Instruction file not found: {path}", "error_code": "missing_instruction_file"}
  ```

- ⚠️ **Missing postcondition for plan file validation**: The plan extracts file paths but doesn't specify whether to validate that the files actually exist on disk after Claude creates them.

  **Impact**: Could return success with non-existent file paths if Claude hallucinates paths.

  **Recommendation**: Add postcondition check:
  ```python
  # Validate extracted paths exist
  valid_paths = [p for p in plan_paths if Path(project_path / p).exists()]
  ```

### Recommendations:
1. Add explicit error code enum (Python) / error constants (Go) matching existing `DecompositionErrorCode` pattern
2. Document error message format for each failure mode
3. Consider adding file existence validation as optional postcondition

---

## Interface Review

### Well-Defined:
- ✅ **Python function signature**: Complete with type hints and docstring
- ✅ **Go function signature**: Complete with parameter types and return type
- ✅ **Naming convention**: Follows existing `step_*` / `Step*` pattern
- ✅ **Return type consistency**: Python returns `dict[str, Any]`, Go returns `*StepResult` (matches existing patterns)
- ✅ **Parameter defaults**: `plan_name="feature"`, `additional_context=""` specified

### Missing or Unclear:

- ⚠️ **Go StepResult field usage**: The plan says return `*StepResult` but doesn't specify which fields to populate. The existing `StepResult` struct has `PlanPath` (single) and `PlanPaths` (multiple) fields.

  **Impact**: Unclear if both fields should be populated for backward compatibility.

  **Recommendation**: Explicitly state:
  ```go
  result.PlanPaths = ExtractAllFilePaths(output, "plan")
  if len(result.PlanPaths) > 0 {
      result.PlanPath = result.PlanPaths[0]  // First for backward compatibility
  }
  ```

### Recommendations:
1. Explicitly document which `StepResult` fields are populated in Go implementation
2. Clarify backward compatibility pattern (single path + multiple paths)

---

## Promise Review

### Well-Defined:
- ✅ **Timeout guarantee**: 20-minute timeout (1200s) specified in Behavior 3.3
- ✅ **Streaming promise**: "Streaming is enabled for progress visibility"
- ✅ **Working directory context**: "Project path is passed for working directory context"
- ✅ **Serialization guarantee**: "Hierarchy is serialized as complete JSON with ALL keys preserved"

### Missing or Unclear:

- ⚠️ **Missing timeout behavior specification**: What happens if Claude times out mid-generation? Does the function:
  - Return partial output?
  - Return empty output with error?
  - Attempt cleanup of partial files?

  **Impact**: Unclear state after timeout could leave orphaned partial files.

  **Recommendation**: Add to Behavior 3.3:
  ```
  **On timeout:**
  - Return {"success": False, "error": "Claude timed out after 1200s"}
  - Do NOT return partial output
  - Any partially created files remain on disk (no cleanup)
  ```

- ⚠️ **Missing idempotency specification**: Is this function idempotent? If called twice with the same hierarchy, does it:
  - Create duplicate plan files with different timestamps?
  - Overwrite existing plans?
  - Detect and skip if plan already exists?

  **Impact**: Unclear behavior on retry/resume scenarios.

  **Recommendation**: Document expected behavior:
  ```
  **Idempotency**: This function is NOT idempotent. Each invocation creates
  new plan files with current timestamp. Callers should track created files
  to avoid duplicates.
  ```

### Recommendations:
1. Document timeout behavior explicitly (partial output handling)
2. Document idempotency expectations
3. Consider adding optional `overwrite` parameter for existing plans

---

## Data Model Review

### Well-Defined:
- ✅ **RequirementHierarchy serialization**: Comprehensive JSON format specified
- ✅ **All 11 RequirementNode keys documented**: id, description, type, parent_id, children, acceptance_criteria, implementation, testable_properties, function_id, related_concepts, category
- ✅ **Nested serialization**: Children recursively serialized, implementation object structure shown
- ✅ **Acceptance criteria importance**: Marked as "CRITICAL for TDD"
- ✅ **Example JSON**: Complete example with nested structure provided
- ✅ **Mapping flow documented**: Clear data flow from hierarchy to test cases (Behavior 3.2.1)
- ✅ **Roundtrip test requirement**: "JSON serialization roundtrip test" in success criteria

### Missing or Unclear:
- None identified. The data model section is exceptionally thorough.

### Recommendations:
- None. This section is well-defined.

---

## API Review

### Status: N/A

This is an internal function, not an external API. No HTTP endpoints, versioning, or authentication concerns apply.

---

## Critical Issues (Must Address Before Implementation)

### 1. **Error Code Enumeration**
- **Category**: Contracts
- **Impact**: Callers cannot programmatically distinguish failure modes (missing file vs Claude timeout vs no output)
- **Recommendation**: Add error codes matching `DecompositionErrorCode` pattern in both Python and Go

### 2. **Timeout Behavior**
- **Category**: Promises
- **Impact**: Unclear state on timeout - partial files, partial output handling
- **Recommendation**: Document explicit timeout behavior in Behavior 3.3

---

## Suggested Plan Amendments

```diff
# In Behavior 3.1: Load TDD Plan Instructions

+ **Error Codes:**
+ - `MISSING_INSTRUCTION_FILE`: `.claude/commands/create_tdd_plan.md` not found
+ - `EMPTY_INSTRUCTION_FILE`: File exists but is empty

# In Behavior 3.3: Invoke Claude with Processed Prompt

+ **Timeout Behavior:**
+ - On timeout: Return {"success": False, "error": "...", "error_code": "CLAUDE_TIMEOUT"}
+ - Partial output is NOT returned
+ - Any partially created files remain on disk

# In Behavior 3.4: Extract Plan File Paths from Output

+ **File Validation (optional):**
+ - Optionally validate extracted paths exist on disk
+ - If validation enabled, filter out non-existent paths

# In Implementation Details → Go Implementation Location

+ **StepResult Field Population:**
+ result.PlanPaths = ExtractAllFilePaths(output, "plan")
+ if len(result.PlanPaths) > 0 {
+     result.PlanPath = result.PlanPaths[0]  // Backward compatibility
+ }
+ result.Output = claudeResult.Output

# In Success Criteria

+ 9. **Error handling completeness:**
+    - Error codes defined for all failure modes
+    - Error messages include actionable context
+    - Both Python and Go return consistent error structures
```

---

## Approval Status

- [ ] **Ready for Implementation** - No critical issues
- [x] **Needs Minor Revision** - Address warnings before proceeding
- [ ] **Needs Major Revision** - Critical issues must be resolved first

**Summary**: The plan is well-structured and follows existing codebase patterns. The data model serialization section is particularly thorough. Address the error code enumeration and timeout behavior documentation before implementation to ensure consistent error handling across Python and Go.

---

## Review Checklist

### Contracts
- [x] Component boundaries are clearly defined
- [x] Input/output contracts are specified
- [ ] Error contracts enumerate all failure modes ⚠️
- [x] Preconditions and postconditions are documented
- [x] Invariants are identified

### Interfaces
- [x] All public methods are defined with signatures
- [x] Naming follows codebase conventions
- [x] Interface matches existing patterns
- [x] Extension points are considered
- [x] Visibility modifiers are appropriate

### Promises
- [x] Behavioral guarantees are documented
- [ ] Async operations have timeout/cancellation handling ⚠️
- [x] Resource cleanup is specified
- [ ] Idempotency requirements are addressed ⚠️
- [x] Ordering guarantees are documented where needed

### Data Models
- [x] All fields have types
- [x] Required vs optional is clear
- [x] Relationships are documented
- [x] Migration strategy is defined (N/A - new function)
- [x] Serialization format is specified

### APIs
- [x] N/A - Internal function
