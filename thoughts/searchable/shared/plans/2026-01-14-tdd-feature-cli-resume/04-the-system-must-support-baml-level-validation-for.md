# Phase 04: The system must support BAML-level validation for ...

## Requirements

### REQ_003: The system must support BAML-level validation for semantic c

The system must support BAML-level validation for semantic checking of requirements against research scope

#### REQ_003.1: Invoke ProcessGate1RequirementValidationPrompt function to p

Invoke ProcessGate1RequirementValidationPrompt function to perform semantic validation of requirements against the research scope, ensuring requirements align with the original research question and scope boundaries

##### Testable Behaviors

1. Function accepts scope_text (string) and current_requirements (string) as input parameters
2. Function calls ProcessGate1RequirementValidationPrompt BAML function with properly formatted inputs
3. scope_text contains the research document content or scope summary
4. current_requirements contains serialized requirement hierarchy in expected format
5. Function handles BAML client initialization and connection management
6. Function returns RequirementValidationResponse with validation_results array and metadata
7. Function logs validation request details for debugging and audit purposes
8. Function handles network timeouts with configurable retry logic
9. Function gracefully handles BAML service unavailability with appropriate error messages

#### REQ_003.2: Construct and return a ValidationResult object containing re

Construct and return a ValidationResult object containing requirement_id, is_valid boolean, validation_issues list, suggestions list, and confidence_score for each validated requirement

##### Testable Behaviors

1. ValidationResult contains requirement_id (string) that matches the source requirement
2. ValidationResult contains is_valid (boolean) indicating pass/fail status
3. ValidationResult contains validation_issues (list of strings) with specific problem descriptions
4. ValidationResult contains suggestions (list of strings) with actionable improvement recommendations
5. ValidationResult contains confidence_score (optional float between 0.0 and 1.0)
6. All ValidationResult objects are serializable to JSON for persistence
7. ValidationResult supports comparison for testing and assertions
8. Empty validation_issues list implies is_valid=True unless explicitly set otherwise
9. Confidence score is None when LLM cannot determine confidence level
10. ValidationResult includes timestamp of when validation was performed

#### REQ_003.3: Add optional --validate-full flag to CLI that enables compre

Add optional --validate-full flag to CLI that enables comprehensive BAML semantic checking, allowing users to choose between fast structural validation and thorough LLM-based validation

##### Testable Behaviors

1. CLI accepts --validate-full or -vf flag as optional boolean argument
2. Flag defaults to False (structural validation only) when not specified
3. When --validate-full is True, BAML ProcessGate1RequirementValidationPrompt is invoked
4. When --validate-full is False, only Python model validation (__post_init__) is performed
5. Help text clearly explains the tradeoff: '--validate-full: Enable comprehensive LLM-based semantic validation (slower but more thorough)'
6. Flag is mutually compatible with --plan-path argument
7. Flag has no effect when --plan-path is not provided (validation only applies to imported plans)
8. CLI displays warning if --validate-full used without --plan-path
9. Validation mode is logged for audit and debugging purposes

#### REQ_003.4: Handle validation latency from LLM calls appropriately by im

Handle validation latency from LLM calls appropriately by implementing async execution, progress feedback, timeout management, and graceful degradation when BAML service is slow or unavailable

##### Testable Behaviors

1. Validation executes asynchronously to prevent CLI blocking during LLM calls
2. User receives progress feedback during validation (spinner, progress bar, or status messages)
3. Configurable timeout (default 60 seconds) prevents indefinite waiting
4. Timeout triggers graceful degradation: structural validation passes, warning issued about skipped semantic validation
5. User can cancel validation with Ctrl+C without corrupting state
6. Estimated time to completion is displayed based on requirement count
7. Validation can be run in background with --batch mode
8. Failed LLM validation does not block pipeline execution (warning-only mode available)
9. Latency metrics are logged for performance monitoring
10. Retry logic attempts validation up to 3 times before degrading


## Success Criteria

- [x] All tests pass
- [x] All behaviors implemented
- [ ] Code reviewed

## Implementation Summary

**Completed: 2026-01-14**

### Files Created
- `silmari_rlm_act/validation/__init__.py` - Module exports
- `silmari_rlm_act/validation/models.py` - SemanticValidationResult, ValidationSummary models
- `silmari_rlm_act/validation/service.py` - SemanticValidationService with BAML integration
- `silmari_rlm_act/tests/test_validation.py` - 24 tests for validation module

### Files Modified
- `silmari_rlm_act/cli.py` - Added `--validate-full` / `-vf` flag
- `silmari_rlm_act/pipeline.py` - Added `_perform_semantic_validation()` method
- `silmari_rlm_act/tests/test_cli.py` - Added 7 tests for --validate-full flag

### Test Results
- 385 tests passed
- 24 new validation tests
- 7 new CLI tests for --validate-full