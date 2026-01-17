# Phase 02: The system must enhance the decomposition phase wi...

## Requirements

### REQ_001: The system must enhance the decomposition phase with adaptiv

The system must enhance the decomposition phase with adaptive granularity based on task complexity assessment using the ADaPT framework

#### REQ_001.1: Create new module planning_pipeline/pre_classifier.py with R

Create new module planning_pipeline/pre_classifier.py with RequirementPreClassifier class that provides keyword-based and LLM-based classification of requirements before full decomposition processing

##### Testable Behaviors

1. RequirementPreClassifier class exists in planning_pipeline/pre_classifier.py
2. Class has __init__ method that initializes keyword patterns for each category (functional, security, performance, usability, integration, non_functional)
3. Keyword patterns include domain-specific terms: backend_only keywords (API, endpoint, database, service, repository), frontend_only keywords (UI, page, form, component, view), middleware keywords (auth, validate, token, session)
4. Class has classify_single(requirement_text: str) -> ClassificationResult method returning category and confidence
5. Class has classify_batch(requirements: list[str]) -> list[ClassificationResult] method for batch processing
6. ClassificationResult dataclass includes: category (str), confidence (float 0.0-1.0), classification_method (keyword|embedding|llm), routing_decision (backend_only|frontend_only|middleware|full_stack)
7. Keyword classification achieves <1ms per requirement processing time
8. Classification correctly routes requirements with >0.9 confidence directly without LLM fallback
9. Unit tests verify keyword patterns correctly classify sample requirements from each category
10. Module includes KEYWORD_PATTERNS constant dict mapping category names to list of keyword patterns

#### REQ_001.2: Add pre_classify boolean parameter to decompose_requirements

Add pre_classify boolean parameter to decompose_requirements function to enable/disable pre-classification routing before Phase 1 extraction

##### Testable Behaviors

1. decompose_requirements() function signature includes new parameter: pre_classify: bool = True
2. DecompositionConfig dataclass has new field: pre_classify: bool = True with default enabling pre-classification
3. When pre_classify=True and RequirementPreClassifier is available, requirements are classified before LLM expansion
4. When pre_classify=False, existing decomposition flow is preserved unchanged (backward compatible)
5. Pre-classification results are stored in RequirementNode.category field for each requirement
6. Classified requirements with backend_only routing skip frontend prompt sections during expansion
7. Classified requirements with frontend_only routing skip backend prompt sections during expansion
8. DecompositionStats includes new fields: pre_classified_count, skipped_expansion_count, classification_time_ms
9. Progress callback reports classification stats: '✓ Pre-classified X requirements (Y% direct route)'
10. If pre_classifier module import fails, gracefully falls back to full expansion (logs warning)

#### REQ_001.3: Implement complexity assessment function to determine task c

Implement complexity assessment function to determine task complexity level (Simple → function-level, Medium → class-level, Complex → repository-level) based on ADaPT framework principles

##### Testable Behaviors

1. assess_complexity(requirement: RequirementNode) -> ComplexityLevel function exists in pre_classifier.py
2. ComplexityLevel enum has values: SIMPLE, MEDIUM, COMPLEX with associated granularity_level property
3. Simple complexity detected when requirement affects single layer (frontend OR backend, not both)
4. Medium complexity detected when requirement affects 2 layers with clear separation
5. Complex complexity detected when requirement affects 3+ layers OR has cross-cutting concerns
6. Cross-cutting concerns detected by keywords: 'auth', 'logging', 'caching', 'transaction', 'security across'
7. Implementation component counts used as complexity signal: len(frontend) + len(backend) + len(middleware)
8. Function returns ComplexityAssessment dataclass with: level, layer_count, has_cross_cutting, confidence
9. Granularity mapping: SIMPLE→function-level (single test), MEDIUM→class-level (test class), COMPLEX→repository-level (test module)
10. Unit tests verify complexity correctly assessed for sample requirements of each type

#### REQ_001.4: Build adaptive prompts based on assessed complexity for requ

Build adaptive prompts based on assessed complexity for requirement expansion, tailoring prompt detail and scope to match task complexity

##### Testable Behaviors

1. build_adaptive_prompt(requirement: RequirementNode, complexity: ComplexityAssessment, research_content: str) -> str function exists
2. Simple complexity prompts are concise (<2000 tokens), focus on single function implementation with 2-3 acceptance criteria
3. Medium complexity prompts include class-level structure, interface definitions, 4-6 acceptance criteria
4. Complex complexity prompts include full architectural context, dependency graphs, 8-12 acceptance criteria, preconditions/postconditions
5. Prompt includes only relevant implementation sections based on routing_decision (skip frontend for backend_only, etc.)
6. Research content truncation adaptive: SIMPLE uses 2000 chars, MEDIUM uses 4000 chars, COMPLEX uses 8000 chars
7. Prompt includes explicit output format instructions matching complexity level
8. Prompts include design-by-contract elements for MEDIUM and COMPLEX: preconditions, postconditions, invariants
9. Function returns complete prompt string ready for LLM invocation
10. Unit tests verify prompt length and content vary appropriately by complexity level

#### REQ_001.5: Integrate existing unused BAML category-specific functions (

Integrate existing unused BAML category-specific functions (ProcessGate1CategoryFunctionalPrompt, ProcessGate1CategorySecurityPrompt, ProcessGate1CategoryPerformancePrompt, ProcessGate1CategoryUsabilityPrompt, ProcessGate1CategoryIntegrationPrompt) for specialized requirement expansion

##### Testable Behaviors

1. Category-specific BAML functions are callable from decomposition module via baml_client
2. _expand_with_category_function(req: RequirementNode, research_content: str, category: str) -> ImplementationDetail function exists
3. Function maps requirement.category to appropriate BAML function: functional→ProcessGate1CategoryFunctionalPrompt, security→ProcessGate1CategorySecurityPrompt, performance→ProcessGate1CategoryPerformancePrompt, usability→ProcessGate1CategoryUsabilityPrompt, integration→ProcessGate1CategoryIntegrationPrompt
4. Non-functional requirements default to ProcessGate1CategoryNonFunctionalPrompt
5. BAML response is parsed into ImplementationComponents and acceptance_criteria
6. If BAML call fails, fallback to generic expansion prompt (existing behavior)
7. Category-specific expansion reduces LLM calls by 30-50% for well-classified requirements
8. DecompositionStats includes category_expansion_count, category_expansion_time_ms fields
9. Progress callback reports: '✓ Expanded X requirements via category-specific prompts'
10. Integration tests verify each category function returns valid structured response


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed