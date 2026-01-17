# Phase 01: The system must implement pre-classification routi...

## Requirements

### REQ_000: The system must implement pre-classification routing to elim

The system must implement pre-classification routing to eliminate unnecessary LLM processing by routing requirements based on keyword matching, embedding similarity, and LLM classification in a cascaded approach

#### REQ_000.1: Implement keyword classifier with <1ms per requirement proce

Implement keyword classifier with <1ms per requirement processing time for pattern matching that routes requirements to backend_only, frontend_only, or middleware categories based on keyword detection

##### Testable Behaviors

1. Classifier processes each requirement in under 1ms (verified by performance benchmarks)
2. Keywords 'API', 'endpoint', 'database', 'server', 'query', 'REST', 'GraphQL' route to backend_only category
3. Keywords 'UI', 'page', 'form', 'button', 'component', 'display', 'view', 'render' route to frontend_only category
4. Keywords 'auth', 'validate', 'middleware', 'session', 'token', 'permission', 'role' route to middleware category
5. Keyword matching is case-insensitive and supports word boundaries to avoid false positives
6. Classifier returns confidence score of 1.0 for exact keyword matches
7. Requirements with no keyword matches are flagged as 'ambiguous' for downstream processing
8. Keyword dictionary is configurable and can be extended without code changes
9. Classifier handles multi-keyword requirements by applying priority rules (middleware > backend > frontend)
10. Performance test suite validates <1ms processing for 10,000 requirements

#### REQ_000.2: Implement embedding classifier with 1-10ms per requirement p

Implement embedding classifier with 1-10ms per requirement processing time using pre-computed schema reference embeddings with 0.85 cosine similarity threshold for auto-routing

##### Testable Behaviors

1. Classifier processes each requirement in 1-10ms using cached embeddings
2. Pre-computed schema reference embeddings are loaded at startup from persistent storage
3. Cosine similarity threshold of 0.85 triggers automatic routing to matched category
4. Requirements with similarity below 0.85 are flagged as 'uncertain' for LLM classification
5. Embedding model supports batch processing for efficiency
6. Reference embeddings cover all categories: backend_only, frontend_only, middleware, full_stack
7. Each category has minimum 15-20 reference examples for accurate matching
8. Embedding cache is invalidated and regenerated when reference examples change
9. Classifier returns top-3 category matches with similarity scores for debugging
10. Threshold is configurable via environment variable or config file
11. Fallback to keyword classification if embedding service is unavailable
12. Memory footprint for cached embeddings stays under 100MB

#### REQ_000.3: Route ambiguous cases (~10% of requirements) to full LLM cla

Route ambiguous cases (~10% of requirements) to full LLM classification using existing Claude SDK flow for requirements that cannot be confidently classified by keyword or embedding methods

##### Testable Behaviors

1. Only requirements flagged as 'ambiguous' or 'uncertain' by prior classifiers are sent to LLM
2. LLM classification uses existing Claude SDK infrastructure (claude_runner.py)
3. Classification prompt includes requirement text and available categories with descriptions
4. LLM returns category assignment with confidence score between 0.0 and 1.0
5. Confidence threshold of 0.85 triggers auto-routing to assigned category
6. Confidence between 0.70-0.85 flags requirement for human review
7. Confidence below 0.70 defaults to full_stack category for comprehensive processing
8. LLM classification is batched where possible to reduce API calls
9. Classification results are cached to avoid re-processing identical requirements
10. Metrics track percentage of requirements routed through LLM tier
11. Error handling provides graceful degradation to full_stack on LLM failure

#### REQ_000.4: Implement category-specific expansion routing that directs c

Implement category-specific expansion routing that directs classified requirements to appropriate BAML expansion functions (backend_only → backend prompts only, frontend_only → frontend prompts only, full_stack → all prompts)

##### Testable Behaviors

1. backend_only requirements route only to ProcessGate1CategoryFunctionalPrompt and backend-specific BAML functions
2. frontend_only requirements route only to frontend-specific BAML functions
3. middleware requirements route to ProcessGate1CategorySecurityPrompt and middleware-specific functions
4. full_stack requirements route to ALL category BAML functions (existing behavior preserved)
5. Routing reduces LLM calls by 50-70% for non-full_stack requirements
6. Integration uses BAML modular API (b.request / b.parse) with optional Agent SDK
7. Category expansion results are merged into unified RequirementNode format
8. Routing configuration maps categories to list of applicable BAML functions
9. Metrics track expansion time savings per category
10. Fallback to full expansion if category-specific function fails
11. Expansion results include source category and functions used for traceability


## Success Criteria

- [x] All tests pass (47 tests for pre_classifier module)
- [x] All behaviors implemented
- [ ] Code reviewed

## Implementation Notes (2026-01-17)

### Files Created

1. **planning_pipeline/pre_classifier.py** - Main implementation with:
   - `KeywordClassifier` - <1ms keyword-based classification with word boundaries
   - `EmbeddingClassifier` - Semantic classification using cosine similarity (requires numpy)
   - `LLMClassifier` - Fallback classification for ambiguous cases with caching
   - `PreClassifier` - Cascaded classifier combining all tiers
   - `ClassificationMetrics` - Metrics tracking for performance monitoring
   - `ThresholdConfig` - Configurable thresholds via environment variables
   - `get_baml_functions_for_category()` - Category-specific BAML function routing

2. **planning_pipeline/tests/test_pre_classifier.py** - Comprehensive test suite with 47 tests

### Key Features

- **REQ_000.1**: Keyword classifier with <1ms processing, verified with 10,000 requirement benchmark
- **REQ_000.2**: Embedding classifier with 0.85 cosine similarity threshold
- **REQ_000.3**: LLM classification with caching and graceful degradation
- **REQ_000.4**: Category-specific BAML function routing to reduce LLM calls by 50-70%