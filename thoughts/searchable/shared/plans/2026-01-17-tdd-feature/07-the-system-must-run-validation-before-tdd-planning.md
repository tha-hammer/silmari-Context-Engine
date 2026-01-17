# Phase 07: The system must run validation BEFORE TDD planning...

## Requirements

### REQ_006: The system must run validation BEFORE TDD planning to catch 

The system must run validation BEFORE TDD planning to catch invalid requirements early and reduce wasted LLM calls on bad inputs

#### REQ_006.1: Run structural validation (Stage 1-2) immediately after deco

Run structural validation (Stage 1-2) immediately after decomposition with blocking behavior on validation failure

##### Testable Behaviors

1. MUST execute automatically after decomposition phase completes (before any TDD planning)
2. MUST validate all RequirementNode objects have non-empty 'id' field
3. MUST validate all RequirementNode objects have non-empty 'description' field
4. MUST validate RequirementNode.type is in VALID_REQUIREMENT_TYPES set
5. MUST validate RequirementNode.category is in VALID_CATEGORIES set
6. MUST detect and report duplicate requirement IDs across the entire hierarchy
7. MUST validate parent-child relationships (child.parent_id matches parent.id)
8. MUST detect orphan children (children referencing non-existent parent IDs)
9. MUST detect circular dependency chains in requirement relationships
10. MUST validate 'requirements' array exists and is non-empty in hierarchy JSON
11. MUST return list of ValidationIssue objects with issue_type, requirement_id, message, and severity
12. MUST BLOCK pipeline execution (return PhaseStatus.FAILED) if ANY structural validation issues are found
13. MUST complete validation in under 1 second for hierarchies with up to 1000 requirements
14. MUST integrate with existing _is_valid_hierarchy_json function in planning_pipeline/helpers.py
15. MUST log all validation issues at WARNING level before blocking
16. MUST include validation results in PhaseResult.metadata under 'structural_validation' key

#### REQ_006.2: Run semantic validation (Stage 3) before TDD planning on --v

Run semantic validation (Stage 3) before TDD planning on --validate-full flag

##### Testable Behaviors

1. MUST only execute when --validate-full/-vf CLI flag is provided
2. MUST execute AFTER structural validation passes and BEFORE TDD planning phase begins
3. MUST invoke existing SemanticValidationService.validate_sync() method
4. MUST call BAML ProcessGate1RequirementValidationPrompt function with scope_text and formatted requirements
5. MUST handle BAML service unavailability gracefully with retry logic (max 3 attempts with exponential backoff)
6. MUST return SemanticValidationResult for each requirement with: requirement_id, is_valid, validation_issues, suggestions, confidence_score
7. MUST flag requirements with completeness_score < 0.6 in validation output
8. MUST flag requirements with scope_alignment_score < 0.5 as potentially out of scope
9. MUST NOT block pipeline on semantic validation failures (warning-only mode)
10. MUST log validation warnings at WARNING level for requirements that fail semantic validation
11. MUST aggregate results into ValidationSummary with valid_count, invalid_count, validity_rate
12. MUST include semantic validation results in PhaseResult.metadata under 'semantic_validation' key
13. MUST respect ValidationConfig.timeout_seconds (default 60 seconds)
14. MUST target average processing time of ~2 seconds per requirement
15. MUST provide progress feedback via progress_callback during validation

#### REQ_006.3: Run category validation (Stage 4) optionally after TDD plann

Run category validation (Stage 4) optionally after TDD planning on --validate-category flag

##### Testable Behaviors

1. MUST only execute when --validate-category/-vc CLI flag is provided
2. MUST execute AFTER TDD planning phase completes
3. MUST apply category-specific validation rules based on RequirementNode.category field
4. MUST validate security requirements include: threat model reference, authentication method, authorization rules, data classification
5. MUST validate performance requirements include: measurable metric (latency, throughput), target value with units, load conditions
6. MUST validate integration requirements include: interface contract (request/response schema), error handling strategy, timeout configuration
7. MUST skip validation for categories without specific rules (functional, usability) and return empty issues list
8. MUST return CategoryValidationIssue with: category, requirement_id, validation_type, failure_reason, severity
9. MUST NOT block pipeline on category validation failures (warning-only mode)
10. MUST use LLM (Agent SDK + Opus 4.5 or BAML category functions) for complex validation rules
11. MUST support --validate-category flag that is disabled by default for performance
12. MUST target average processing time of ~1 second per requirement
13. MUST aggregate category validation results and include in final pipeline output
14. MUST log category validation warnings at WARNING level

#### REQ_006.4: Only proceed to TDD planning for validated requirements

Only proceed to TDD planning for validated requirements

##### Testable Behaviors

1. MUST filter out requirements that failed structural validation before passing to TDD planning phase
2. MUST maintain original hierarchy structure but mark invalid requirements as 'skipped'
3. MUST pass only structurally valid requirements to TDDPlanningPhase.execute()
4. MUST include count of skipped requirements in PhaseResult.metadata under 'skipped_requirements_count'
5. MUST include list of skipped requirement IDs in PhaseResult.metadata under 'skipped_requirement_ids'
6. MUST log which requirements were skipped and why at INFO level
7. MUST continue processing valid requirements even if some requirements are invalid (partial success)
8. MUST set PhaseStatus.PARTIAL_COMPLETE if some requirements were skipped but others processed successfully
9. MUST return PhaseStatus.FAILED only if ALL requirements fail validation
10. MUST update TDDPlanningPhase to accept filtered RequirementHierarchy
11. MUST preserve requirement parent-child relationships when filtering (if parent is invalid, children are also skipped)
12. MUST generate summary report of validation filtering at end of TDD planning phase
13. MUST allow --force-all flag to bypass requirement filtering and process all requirements regardless of validation status


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed