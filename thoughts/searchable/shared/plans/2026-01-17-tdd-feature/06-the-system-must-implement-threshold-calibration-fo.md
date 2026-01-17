# Phase 06: The system must implement threshold calibration fo...

## Requirements

### REQ_005: The system must implement threshold calibration for pre-clas

The system must implement threshold calibration for pre-classification routing with three-tier threshold strategy

#### REQ_005.1: Configure Tier 1 keyword matching with binary confidence (1.

Configure Tier 1 keyword matching with binary confidence (1.0) for direct routing on exact keyword match covering 50-60% of requirements

##### Testable Behaviors

1. Keyword classifier returns confidence of exactly 1.0 for exact keyword matches
2. Keyword classifier returns confidence of 0.0 for non-matches (no partial matching)
3. Keyword dictionary contains category-to-keywords mapping for: backend_only ('API', 'endpoint', 'database', 'repository', 'migration'), frontend_only ('UI', 'page', 'form', 'component', 'button'), middleware ('auth', 'validate', 'interceptor', 'middleware')
4. Classification latency is under 1ms per requirement
5. Coverage metric tracks percentage of requirements routed via Tier 1 (target: 50-60%)
6. Case-insensitive matching is applied to both requirement text and keyword dictionary
7. Keyword matches trigger direct category routing without proceeding to Tier 2 or Tier 3
8. Unit tests verify keyword matching for all defined categories with 100% accuracy on exact matches

#### REQ_005.2: Configure Tier 2 embedding similarity with initial threshold

Configure Tier 2 embedding similarity with initial threshold of 0.75, calibrated using fit() with 500 iterations on labeled data, covering 30-40% of remaining requirements

##### Testable Behaviors

1. EmbeddingClassifier initializes with EMBEDDING_SIMILARITY_INITIAL threshold of 0.75
2. fit() method accepts labeled training samples as list of (requirement_text, category) tuples
3. fit() method runs 500 iterations of threshold optimization using cross-validation
4. Calibrated threshold is stored and used for classification (expected post-calibration: 0.22-0.30)
5. Pre-computed reference embeddings exist for each category from labeled samples
6. classify() computes cosine similarity between input embedding and category reference embeddings
7. Requirements with similarity >= threshold are auto-routed to matched category
8. Requirements with similarity < threshold are passed to Tier 3 (LLM classification)
9. Coverage metric tracks percentage of Tier 1 pass-throughs routed via Tier 2 (target: 30-40%)
10. Classification latency is 1-10ms per requirement
11. Model supports persistence of calibrated thresholds to avoid re-training

#### REQ_005.3: Configure Tier 3 LLM classification with 0.85 auto-route con

Configure Tier 3 LLM classification with 0.85 auto-route confidence threshold and 0.70 human review threshold for ~10% most ambiguous cases

##### Testable Behaviors

1. LLMClassifier uses Claude Opus 4.5 via Agent SDK for highest quality classification
2. Classification response includes confidence score between 0.0 and 1.0
3. Confidence >= 0.85 triggers automatic routing to predicted category
4. Confidence between 0.70 and 0.85 logs warning but still routes automatically
5. Confidence < 0.70 flags requirement for human review (adds to review queue)
6. Human review queue is persisted and accessible via API or CLI
7. BAML modular API (b.request / b.parse) is used for type-safe prompt building and response parsing
8. Coverage metric tracks percentage of Tier 2 pass-throughs handled by Tier 3 (target: ~10% of total)
9. Classification includes reasoning/explanation field for audit purposes
10. Batch classification supported for efficiency (multiple requirements per LLM call)

#### REQ_005.4: Collect 15-20 training samples per category for threshold op

Collect 15-20 training samples per category for threshold optimization

##### Testable Behaviors

1. Training data collection targets minimum 15 samples per category
2. Training data collection targets maximum 20 samples per category (diminishing returns beyond this)
3. Samples are collected from existing processed requirements with verified categories
4. Each sample includes: requirement_text (str), verified_category (str), source_requirement_id (str)
5. Sample diversity is ensured (no duplicate or near-duplicate requirements)
6. Coverage report shows sample count per category with warnings for under-represented categories
7. Manual labeling interface allows adding new samples with human-verified categories
8. Export format is JSON array compatible with EmbeddingClassifier.fit() input
9. Import capability for pre-existing labeled datasets
10. Validation checks ensure all samples have non-empty text and valid category values

#### REQ_005.5: Implement ThresholdConfig class with KEYWORD_CONFIDENCE, EMB

Implement ThresholdConfig class with KEYWORD_CONFIDENCE, EMBEDDING_SIMILARITY_INITIAL, EMBEDDING_SIMILARITY_MIN, LLM_AUTO_ROUTE_CONFIDENCE, and LLM_HUMAN_REVIEW_THRESHOLD parameters

##### Testable Behaviors

1. ThresholdConfig is a frozen dataclass with all five threshold parameters
2. KEYWORD_CONFIDENCE defaults to 1.0 (binary match)
3. EMBEDDING_SIMILARITY_INITIAL defaults to 0.75
4. EMBEDDING_SIMILARITY_MIN defaults to 0.20 (post-calibration floor)
5. LLM_AUTO_ROUTE_CONFIDENCE defaults to 0.85
6. LLM_HUMAN_REVIEW_THRESHOLD defaults to 0.70
7. All parameters can be overridden via environment variables (PRECLASSIFY_KEYWORD_CONFIDENCE, etc.)
8. from_env() class method loads configuration from environment with fallback to defaults
9. to_dict() and from_dict() methods support JSON serialization
10. validate() method ensures: KEYWORD_CONFIDENCE == 1.0, EMBEDDING_SIMILARITY_MIN < EMBEDDING_SIMILARITY_INITIAL, LLM_HUMAN_REVIEW_THRESHOLD < LLM_AUTO_ROUTE_CONFIDENCE
11. Configuration is injectable into PreClassifier, EmbeddingClassifier, and LLMClassifier classes
12. Default configuration instance is available as ThresholdConfig.default()


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed