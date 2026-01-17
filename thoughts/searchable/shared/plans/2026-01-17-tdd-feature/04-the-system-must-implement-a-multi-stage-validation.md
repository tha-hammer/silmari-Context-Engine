# Phase 04: The system must implement a multi-stage validation...

## Requirements

### REQ_003: The system must implement a multi-stage validation cascade w

The system must implement a multi-stage validation cascade with structural, cross-reference, semantic, and category-specific validation stages

#### REQ_003.1: Implement Stage 1 structural validation that performs fast l

Implement Stage 1 structural validation that performs fast local checks (<1s) for JSON schema compliance, required field presence (id, description, type), category validation against VALID_CATEGORIES set, and parent-child relationship consistency

##### Testable Behaviors

1. MUST complete validation of 1000 requirements in under 1 second
2. MUST return ValidationIssue with code 'missing_id' when requirement.id is null or empty
3. MUST return ValidationIssue with code 'empty_description' when requirement.description is null or empty
4. MUST return ValidationIssue with code 'invalid_type' when requirement.type is not in VALID_REQUIREMENT_TYPES set
5. MUST return ValidationIssue with code 'invalid_category' when requirement.category is not in VALID_CATEGORIES set
6. MUST return ValidationIssue with code 'invalid_parent_ref' when child.parent_id does not match parent requirement.id
7. MUST validate JSON structure matches RequirementHierarchy schema before processing
8. MUST return empty list when all structural validations pass
9. MUST provide human-readable error message in each ValidationIssue
10. MUST include the failing requirement reference in ValidationIssue for debugging

#### REQ_003.2: Implement Stage 2 cross-reference validation that performs f

Implement Stage 2 cross-reference validation that performs fast local checks (<1s) for duplicate ID detection across the entire hierarchy, orphan child detection where children reference non-existent parents, circular dependency detection in parent-child chains, and acceptance criteria coverage verification

##### Testable Behaviors

1. MUST complete cross-reference validation of 1000 requirements in under 1 second
2. MUST return ValidationIssue with code 'duplicate_id' when two or more requirements share the same id
3. MUST include both the original and duplicate requirement references in duplicate_id ValidationIssue
4. MUST return ValidationIssue with code 'orphan_child' when child.parent_id references a non-existent requirement
5. MUST return ValidationIssue with code 'circular_dependency' when requirement A is ancestor of B and B is ancestor of A
6. MUST detect circular dependencies of any length (not just direct parent-child loops)
7. MUST return ValidationIssue with code 'missing_acceptance_criteria' when requirement has no acceptance_criteria array or empty array
8. MUST return ValidationIssue with code 'uncovered_acceptance_criteria' when acceptance_criteria_id is not referenced by any child requirement
9. MUST track all seen IDs in a single pass using O(n) time complexity
10. MUST use iterative (not recursive) traversal to prevent stack overflow on deep hierarchies

#### REQ_003.3: Implement Stage 3 semantic validation using the existing BAM

Implement Stage 3 semantic validation using the existing BAML ProcessGate1RequirementValidationPrompt function with approximately 2 seconds processing time per requirement, scoring requirements for clarity and completeness, and verifying alignment with the original project scope

##### Testable Behaviors

1. MUST invoke existing BAML ProcessGate1RequirementValidationPrompt for each requirement
2. MUST batch requirements to optimize LLM calls (max 10 requirements per call)
3. MUST return clarity_score (0.0-1.0) for each requirement measuring how unambiguous the description is
4. MUST return completeness_score (0.0-1.0) for each requirement measuring presence of all necessary details
5. MUST return scope_alignment_score (0.0-1.0) measuring how well requirement aligns with project scope
6. MUST flag requirements with clarity_score < 0.7 as needing revision
7. MUST flag requirements with completeness_score < 0.6 as incomplete
8. MUST flag requirements with scope_alignment_score < 0.5 as potentially out of scope
9. MUST implement retry logic with exponential backoff on BAML call failures (max 3 retries)
10. MUST support --validate-full flag to enable this stage (disabled by default for performance)
11. MUST aggregate individual requirement validations into ValidationSummary
12. MUST target average processing time of 2 seconds per requirement

#### REQ_003.4: Implement Stage 4 category-specific validation with approxim

Implement Stage 4 category-specific validation with approximately 1 second processing time per requirement, applying specialized validation rules based on requirement category: security requirements get security-specific checks (authentication, authorization, encryption), performance requirements get metrics validation (latency, throughput thresholds), and integration requirements get interface contract validation

##### Testable Behaviors

1. MUST route security category requirements through ProcessGate1CategorySecurityPrompt BAML function
2. MUST route performance category requirements through ProcessGate1CategoryPerformancePrompt BAML function
3. MUST route integration category requirements through ProcessGate1CategoryIntegrationPrompt BAML function
4. MUST validate security requirements specify authentication method (OAuth, JWT, session, API key)
5. MUST validate security requirements specify authorization model (RBAC, ABAC, ACL)
6. MUST validate security requirements mention encryption for sensitive data handling
7. MUST validate performance requirements include quantitative metrics (response time < Xms, throughput > Y/s)
8. MUST validate performance requirements specify load conditions (concurrent users, request rate)
9. MUST validate integration requirements define interface contract (request/response schema)
10. MUST validate integration requirements specify error handling strategy
11. MUST return CategoryValidationIssue with category, validation_type, and specific failure reason
12. MUST support --validate-category flag to enable this stage (disabled by default)
13. MUST skip validation for categories without specific rules (functional, usability) and return empty list
14. MUST target average processing time of 1 second per requirement

#### REQ_003.5: Create the HierarchyValidator class in planning_pipeline/val

Create the HierarchyValidator class in planning_pipeline/validators.py as the central orchestrator for the multi-stage validation cascade, exposing validate_structural, validate_cross_references, validate_semantic, and validate_category_specific methods with configurable validation stages and early-exit support

##### Testable Behaviors

1. MUST create HierarchyValidator class in new file planning_pipeline/validators.py
2. MUST accept ValidationConfig in constructor specifying which stages to run and their thresholds
3. MUST expose validate_structural(hierarchy: RequirementHierarchy) -> List[ValidationIssue] method
4. MUST expose validate_cross_references(hierarchy: RequirementHierarchy) -> List[ValidationIssue] method
5. MUST expose validate_semantic(hierarchy: RequirementHierarchy, scope: str) -> ValidationSummary method
6. MUST expose validate_category_specific(hierarchy: RequirementHierarchy) -> List[CategoryValidationIssue] method
7. MUST expose validate_all(hierarchy: RequirementHierarchy, scope: str) -> CascadeValidationResult method
8. MUST implement early exit in validate_all: if Stage 1 fails with ERROR severity, skip subsequent stages
9. MUST implement early exit in validate_all: if Stage 2 fails with ERROR severity, skip semantic/category stages
10. MUST aggregate all validation results into CascadeValidationResult with per-stage breakdown
11. MUST log validation progress and timing for each stage
12. MUST integrate with existing SemanticValidationService for Stage 3
13. MUST accept optional progress_callback to report validation progress
14. MUST be importable from planning_pipeline.validators for integration with decomposition.py


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed