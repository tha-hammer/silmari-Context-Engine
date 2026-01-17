"""Tests for pre_classifier module.

Tests cover:
- REQ_000.1: Keyword classifier with <1ms processing
- REQ_000.2: Embedding classifier with 1-10ms processing
- REQ_000.3: LLM classification for ambiguous cases
- REQ_000.4: Category-specific expansion routing
"""

import time
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from planning_pipeline.pre_classifier import (
    CATEGORY_BAML_FUNCTIONS,
    DEFAULT_KEYWORD_DICT,
    NUMPY_AVAILABLE,
    ClassificationMetrics,
    ClassificationResult,
    ClassificationTier,
    EmbeddingClassifier,
    KeywordClassifier,
    LLMClassifier,
    PreClassifier,
    RequirementCategory,
    ThresholdConfig,
    get_baml_functions_for_category,
)


# =============================================================================
# REQ_000.1: Keyword Classifier Tests
# =============================================================================


class TestKeywordClassifier:
    """Tests for REQ_000.1: Keyword classifier with <1ms processing."""

    def test_backend_keywords_classification(self):
        """Keywords 'API', 'endpoint', 'database', etc. route to backend_only."""
        classifier = KeywordClassifier()

        test_cases = [
            ("Implement REST API endpoint for user data", RequirementCategory.BACKEND_ONLY),
            ("Create database schema for orders", RequirementCategory.BACKEND_ONLY),
            ("Build GraphQL server for product queries", RequirementCategory.BACKEND_ONLY),
            ("Implement CRUD operations for the repository", RequirementCategory.BACKEND_ONLY),
            ("Create SQL migration for new table", RequirementCategory.BACKEND_ONLY),
        ]

        for text, expected_category in test_cases:
            result = classifier.classify(text)
            assert result.category == expected_category, f"Failed for: {text}"
            assert result.confidence == 1.0
            assert result.tier == ClassificationTier.KEYWORD

    def test_frontend_keywords_classification(self):
        """Keywords 'UI', 'page', 'form', etc. route to frontend_only."""
        classifier = KeywordClassifier()

        test_cases = [
            ("Create login form with validation", RequirementCategory.FRONTEND_ONLY),
            ("Design user profile page layout", RequirementCategory.FRONTEND_ONLY),
            ("Implement button click handler", RequirementCategory.FRONTEND_ONLY),
            ("Build responsive navigation menu", RequirementCategory.FRONTEND_ONLY),
            ("Add modal dialog for confirmation", RequirementCategory.FRONTEND_ONLY),
        ]

        for text, expected_category in test_cases:
            result = classifier.classify(text)
            assert result.category == expected_category, f"Failed for: {text}"
            assert result.confidence == 1.0

    def test_middleware_keywords_classification(self):
        """Keywords 'auth', 'validate', 'middleware', etc. route to middleware."""
        classifier = KeywordClassifier()

        test_cases = [
            ("Implement JWT token validation", RequirementCategory.MIDDLEWARE),
            ("Create authentication middleware", RequirementCategory.MIDDLEWARE),
            ("Add role-based permission checks", RequirementCategory.MIDDLEWARE),
            ("Build OAuth integration for login", RequirementCategory.MIDDLEWARE),
            ("Implement rate-limit throttling", RequirementCategory.MIDDLEWARE),
        ]

        for text, expected_category in test_cases:
            result = classifier.classify(text)
            assert result.category == expected_category, f"Failed for: {text}"
            assert result.confidence == 1.0

    def test_case_insensitive_matching(self):
        """Keyword matching is case-insensitive."""
        classifier = KeywordClassifier()

        test_cases = [
            "Create API endpoint",
            "create api endpoint",
            "CREATE API ENDPOINT",
            "Create Api Endpoint",
        ]

        for text in test_cases:
            result = classifier.classify(text)
            assert result.category == RequirementCategory.BACKEND_ONLY, f"Failed for: {text}"

    def test_word_boundary_matching(self):
        """Keyword matching supports word boundaries to avoid false positives."""
        classifier = KeywordClassifier()

        # "api" should match as a word, not inside "application"
        result = classifier.classify("Build an application")
        assert result.category == RequirementCategory.AMBIGUOUS

        # "api" as a word should match
        result = classifier.classify("Build an API")
        assert result.category == RequirementCategory.BACKEND_ONLY

    def test_no_keywords_returns_ambiguous(self):
        """Requirements with no keyword matches are flagged as 'ambiguous'."""
        classifier = KeywordClassifier()

        result = classifier.classify("Implement the new feature")
        assert result.category == RequirementCategory.AMBIGUOUS
        assert result.confidence == 0.0

    def test_processing_time_under_1ms(self):
        """Classifier processes each requirement in under 1ms."""
        classifier = KeywordClassifier()

        # Run multiple classifications
        total_time = 0.0
        iterations = 1000

        for _ in range(iterations):
            start = time.perf_counter()
            classifier.classify("Implement REST API endpoint for user data")
            total_time += time.perf_counter() - start

        avg_time_ms = (total_time / iterations) * 1000
        assert avg_time_ms < 1.0, f"Average processing time {avg_time_ms}ms exceeds 1ms"

    def test_priority_rules_middleware_over_backend(self):
        """Multi-keyword requirements apply priority rules (middleware > backend > frontend)."""
        classifier = KeywordClassifier()

        # Contains both middleware (auth) and backend (API) keywords
        result = classifier.classify("Implement API authentication middleware")
        assert result.category == RequirementCategory.MIDDLEWARE

    def test_priority_rules_backend_over_frontend(self):
        """Backend takes priority over frontend."""
        classifier = KeywordClassifier()

        # Contains both backend (API) and frontend (display) keywords
        result = classifier.classify("Build API endpoint to display data")
        assert result.category == RequirementCategory.BACKEND_ONLY

    def test_source_keywords_returned(self):
        """Classifier returns keywords that triggered classification."""
        classifier = KeywordClassifier()

        result = classifier.classify("Create REST API and GraphQL endpoint")
        assert result.category == RequirementCategory.BACKEND_ONLY
        assert len(result.source_keywords) > 0
        assert any(kw in ["api", "rest", "graphql", "endpoint"] for kw in result.source_keywords)

    def test_custom_keywords_can_be_added(self):
        """Keyword dictionary is configurable and can be extended."""
        classifier = KeywordClassifier()

        # Initially "kubernetes" is not a keyword
        result = classifier.classify("Deploy to kubernetes cluster")
        assert result.category == RequirementCategory.AMBIGUOUS

        # Add custom keyword
        classifier.add_keywords(RequirementCategory.BACKEND_ONLY, {"kubernetes", "helm"})

        result = classifier.classify("Deploy to kubernetes cluster")
        assert result.category == RequirementCategory.BACKEND_ONLY

    def test_performance_10000_requirements(self):
        """Performance test validates <1ms processing for 10,000 requirements."""
        classifier = KeywordClassifier()

        requirements = [
            "Implement REST API endpoint for user data",
            "Create login form with validation",
            "Add authentication middleware",
            "Build responsive navigation menu",
            "Implement database query optimization",
        ] * 2000  # 10,000 requirements

        start = time.perf_counter()
        for req in requirements:
            classifier.classify(req)
        total_time = time.perf_counter() - start

        avg_time_ms = (total_time / len(requirements)) * 1000
        assert avg_time_ms < 1.0, f"Average processing time {avg_time_ms}ms exceeds 1ms for 10,000 requirements"

    def test_confidence_score_1_for_matches(self):
        """Classifier returns confidence score of 1.0 for exact keyword matches."""
        classifier = KeywordClassifier()

        result = classifier.classify("Build REST API")
        assert result.confidence == 1.0

    def test_top_matches_for_debugging(self):
        """Classifier returns top matches for debugging."""
        classifier = KeywordClassifier()

        # Text with keywords from multiple categories
        result = classifier.classify("Create form for API validation")
        assert len(result.top_matches) > 0
        # Top matches should be sorted by count descending
        for match in result.top_matches:
            assert len(match) == 2  # (category_name, count)


# =============================================================================
# REQ_000.2: Embedding Classifier Tests
# =============================================================================


class TestEmbeddingClassifier:
    """Tests for REQ_000.2: Embedding classifier with 1-10ms processing."""

    @pytest.fixture
    def mock_embedding_fn(self):
        """Create a mock embedding function."""
        def embed(text: str) -> list[float]:
            # Simple mock: return different vectors for different categories
            if "api" in text.lower() or "database" in text.lower():
                return [1.0, 0.0, 0.0, 0.0]
            elif "form" in text.lower() or "button" in text.lower():
                return [0.0, 1.0, 0.0, 0.0]
            elif "auth" in text.lower() or "token" in text.lower():
                return [0.0, 0.0, 1.0, 0.0]
            else:
                return [0.0, 0.0, 0.0, 1.0]
        return embed

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="Requires numpy")
    def test_embedding_classifier_initialization(self, mock_embedding_fn):
        """Embedding classifier initializes properly."""
        classifier = EmbeddingClassifier(embedding_fn=mock_embedding_fn)
        assert classifier is not None

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="Requires numpy")
    def test_add_reference_example(self, mock_embedding_fn):
        """Reference examples can be added for categories."""
        classifier = EmbeddingClassifier(embedding_fn=mock_embedding_fn)
        classifier.add_reference_example(
            RequirementCategory.BACKEND_ONLY,
            "Create REST API endpoint"
        )
        assert classifier.is_ready

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="Requires numpy")
    def test_classification_with_references(self, mock_embedding_fn):
        """Classification works with reference embeddings."""
        classifier = EmbeddingClassifier(embedding_fn=mock_embedding_fn)

        # Add reference examples
        classifier.add_reference_example(
            RequirementCategory.BACKEND_ONLY,
            "Create database query"
        )
        classifier.add_reference_example(
            RequirementCategory.FRONTEND_ONLY,
            "Build login form"
        )

        result = classifier.classify("Implement API endpoint")
        assert result.tier == ClassificationTier.EMBEDDING
        assert result.confidence > 0

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="Requires numpy")
    def test_cosine_similarity_threshold(self, mock_embedding_fn):
        """Cosine similarity threshold triggers automatic routing."""
        config = ThresholdConfig(EMBEDDING_SIMILARITY_INITIAL=0.85)
        classifier = EmbeddingClassifier(
            embedding_fn=mock_embedding_fn,
            threshold_config=config
        )

        # Add reference
        classifier.add_reference_example(
            RequirementCategory.BACKEND_ONLY,
            "Create API"
        )

        # Should match with high similarity
        result = classifier.classify("Create API")
        assert result.category == RequirementCategory.BACKEND_ONLY
        assert result.confidence >= 0.85

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="Requires numpy")
    def test_below_threshold_returns_ambiguous(self, mock_embedding_fn):
        """Requirements with similarity below threshold are flagged as uncertain."""
        config = ThresholdConfig(EMBEDDING_SIMILARITY_INITIAL=0.85)
        classifier = EmbeddingClassifier(
            embedding_fn=mock_embedding_fn,
            threshold_config=config
        )

        # Add reference for backend
        classifier.add_reference_example(
            RequirementCategory.BACKEND_ONLY,
            "Create database"
        )

        # Test with completely different text
        result = classifier.classify("Something completely different")
        # Low similarity should return ambiguous or the top match with low confidence
        assert result.confidence < 0.85 or result.category == RequirementCategory.AMBIGUOUS

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="Requires numpy")
    def test_top_3_matches_returned(self, mock_embedding_fn):
        """Classifier returns top-3 category matches with similarity scores."""
        classifier = EmbeddingClassifier(embedding_fn=mock_embedding_fn)

        # Add references for multiple categories
        classifier.add_reference_example(RequirementCategory.BACKEND_ONLY, "API endpoint")
        classifier.add_reference_example(RequirementCategory.FRONTEND_ONLY, "Login form")
        classifier.add_reference_example(RequirementCategory.MIDDLEWARE, "Auth token")

        result = classifier.classify("Create API")
        assert len(result.top_matches) <= 3
        for match in result.top_matches:
            assert len(match) == 2  # (category, score)


# =============================================================================
# REQ_000.3: LLM Classification Tests
# =============================================================================


class TestLLMClassifier:
    """Tests for REQ_000.3: LLM classification for ambiguous cases."""

    def test_llm_classifier_initialization(self):
        """LLM classifier initializes properly."""
        classifier = LLMClassifier()
        assert classifier is not None

    def test_returns_ambiguous_without_llm_fn(self):
        """Without llm_fn, classifier returns ambiguous."""
        classifier = LLMClassifier(llm_fn=None)
        result = classifier.classify("Some requirement")
        assert result.category == RequirementCategory.AMBIGUOUS
        assert result.tier == ClassificationTier.LLM

    def test_calls_llm_function(self):
        """LLM function is called for classification."""
        mock_fn = MagicMock(return_value=("backend_only", 0.9))
        classifier = LLMClassifier(llm_fn=mock_fn)

        result = classifier.classify("Some requirement")

        mock_fn.assert_called_once_with("Some requirement")
        assert result.category == RequirementCategory.BACKEND_ONLY
        assert result.confidence == 0.9
        assert result.tier == ClassificationTier.LLM

    def test_caches_results(self):
        """Classification results are cached."""
        mock_fn = MagicMock(return_value=("backend_only", 0.9))
        classifier = LLMClassifier(llm_fn=mock_fn)

        # First call
        result1 = classifier.classify("Some requirement")
        assert mock_fn.call_count == 1

        # Second call should use cache
        result2 = classifier.classify("Some requirement")
        assert mock_fn.call_count == 1  # Not called again

        assert result1.category == result2.category

    def test_cache_is_case_insensitive(self):
        """Cache lookup is case-insensitive."""
        mock_fn = MagicMock(return_value=("backend_only", 0.9))
        classifier = LLMClassifier(llm_fn=mock_fn)

        classifier.classify("Some Requirement")
        classifier.classify("some requirement")

        # Should only call once due to case-insensitive caching
        assert mock_fn.call_count == 1

    def test_confidence_threshold_auto_route(self):
        """Confidence >= 0.85 triggers auto-routing."""
        mock_fn = MagicMock(return_value=("backend_only", 0.90))
        config = ThresholdConfig(LLM_AUTO_ROUTE_CONFIDENCE=0.85)
        classifier = LLMClassifier(llm_fn=mock_fn, threshold_config=config)

        result = classifier.classify("Some requirement")
        assert result.category == RequirementCategory.BACKEND_ONLY
        assert result.confidence == 0.90

    def test_confidence_below_review_defaults_to_full_stack(self):
        """Confidence < 0.70 defaults to full_stack."""
        mock_fn = MagicMock(return_value=("backend_only", 0.50))
        config = ThresholdConfig(LLM_HUMAN_REVIEW_THRESHOLD=0.70)
        classifier = LLMClassifier(llm_fn=mock_fn, threshold_config=config)

        result = classifier.classify("Some requirement")
        assert result.category == RequirementCategory.FULL_STACK

    def test_graceful_degradation_on_error(self):
        """Errors in LLM function result in full_stack fallback."""
        mock_fn = MagicMock(side_effect=Exception("LLM Error"))
        classifier = LLMClassifier(llm_fn=mock_fn)

        result = classifier.classify("Some requirement")
        assert result.category == RequirementCategory.FULL_STACK
        assert result.tier == ClassificationTier.LLM

    def test_invalid_category_defaults_to_full_stack(self):
        """Invalid category strings default to full_stack."""
        mock_fn = MagicMock(return_value=("invalid_category", 0.95))
        classifier = LLMClassifier(llm_fn=mock_fn)

        result = classifier.classify("Some requirement")
        assert result.category == RequirementCategory.FULL_STACK


# =============================================================================
# PreClassifier Integration Tests
# =============================================================================


class TestPreClassifier:
    """Integration tests for the cascaded pre-classifier."""

    def test_keyword_tier_returns_immediately(self):
        """Keyword matches return immediately without calling other tiers."""
        mock_llm = MagicMock(return_value=("frontend_only", 0.9))
        classifier = PreClassifier(llm_fn=mock_llm)

        result = classifier.classify("Create REST API endpoint")

        # Should match on keywords, not call LLM
        assert result.category == RequirementCategory.BACKEND_ONLY
        assert result.tier == ClassificationTier.KEYWORD
        mock_llm.assert_not_called()

    def test_falls_through_to_llm_for_ambiguous(self):
        """Ambiguous requirements fall through to LLM tier."""
        mock_llm = MagicMock(return_value=("backend_only", 0.9))
        classifier = PreClassifier(llm_fn=mock_llm)

        result = classifier.classify("Implement the new feature")

        assert result.tier == ClassificationTier.LLM
        mock_llm.assert_called_once()

    def test_metrics_tracking(self):
        """Metrics are tracked for all classifications at each tier."""
        classifier = PreClassifier()

        classifier.classify("Create REST API")  # keyword tier only
        classifier.classify("Build login form")  # keyword tier only
        classifier.classify("Some ambiguous text")  # keyword (ambiguous) + LLM fallback

        # Metrics record each tier's result, so ambiguous goes through keyword AND LLM
        # Total = 2 keyword matches + 1 keyword ambiguous + 1 LLM = 4 records
        assert classifier.metrics.total >= 3  # At least 3 final results
        assert "keyword" in classifier.metrics.by_tier

    def test_batch_classification(self):
        """Batch classification works correctly."""
        classifier = PreClassifier()

        requirements = [
            "Create REST API endpoint",
            "Build login form",
            "Implement authentication",
        ]

        results = classifier.classify_batch(requirements)

        assert len(results) == 3
        assert results[0].category == RequirementCategory.BACKEND_ONLY
        assert results[1].category == RequirementCategory.FRONTEND_ONLY
        assert results[2].category == RequirementCategory.MIDDLEWARE


# =============================================================================
# REQ_000.4: Category-Specific Expansion Routing Tests
# =============================================================================


class TestCategoryExpansionRouting:
    """Tests for REQ_000.4: Category-specific expansion routing."""

    def test_backend_routes_to_backend_functions(self):
        """backend_only routes to backend-specific BAML functions."""
        functions = get_baml_functions_for_category(RequirementCategory.BACKEND_ONLY)

        assert "ProcessGate1CategoryFunctionalPrompt" in functions
        assert "ProcessGate1SubprocessDetailsPrompt" in functions
        assert "ProcessGate1DataNeedsPrompt" in functions
        # Should NOT include frontend-specific functions
        assert "ProcessGate1CategoryUsabilityPrompt" not in functions

    def test_frontend_routes_to_frontend_functions(self):
        """frontend_only routes to frontend-specific BAML functions."""
        functions = get_baml_functions_for_category(RequirementCategory.FRONTEND_ONLY)

        assert "ProcessGate1CategoryUsabilityPrompt" in functions
        assert "ProcessGate1UserInteractionsPrompt" in functions
        # Should include subprocess details for implementation
        assert "ProcessGate1SubprocessDetailsPrompt" in functions

    def test_middleware_routes_to_security_functions(self):
        """middleware routes to security-specific BAML functions."""
        functions = get_baml_functions_for_category(RequirementCategory.MIDDLEWARE)

        assert "ProcessGate1CategorySecurityPrompt" in functions
        assert "ProcessGate1CategoryFunctionalPrompt" in functions

    def test_full_stack_routes_to_all_functions(self):
        """full_stack routes to ALL category BAML functions."""
        functions = get_baml_functions_for_category(RequirementCategory.FULL_STACK)

        # Should include all major function types
        assert "ProcessGate1CategoryFunctionalPrompt" in functions
        assert "ProcessGate1CategoryNonFunctionalPrompt" in functions
        assert "ProcessGate1CategorySecurityPrompt" in functions
        assert "ProcessGate1CategoryPerformancePrompt" in functions
        assert "ProcessGate1CategoryUsabilityPrompt" in functions
        assert "ProcessGate1CategoryIntegrationPrompt" in functions

    def test_function_lists_are_non_empty(self):
        """All categories have non-empty function lists."""
        for category in RequirementCategory:
            functions = get_baml_functions_for_category(category)
            assert len(functions) > 0, f"Category {category} has no functions"

    def test_ambiguous_has_minimal_functions(self):
        """Ambiguous category has minimal default functions."""
        functions = get_baml_functions_for_category(RequirementCategory.AMBIGUOUS)

        # Should have basic functions but not all
        assert len(functions) < len(get_baml_functions_for_category(RequirementCategory.FULL_STACK))


# =============================================================================
# Threshold Configuration Tests
# =============================================================================


class TestThresholdConfig:
    """Tests for threshold configuration."""

    def test_default_values(self):
        """Default threshold values are set correctly."""
        config = ThresholdConfig()

        assert config.KEYWORD_CONFIDENCE == 1.0
        # New default values per REQ_005.5
        assert config.EMBEDDING_SIMILARITY_INITIAL == 0.75
        assert config.EMBEDDING_SIMILARITY_MIN == 0.20
        # Legacy aliases point to new values
        assert config.EMBEDDING_AUTO_ROUTE == 0.75  # Legacy alias
        assert config.LLM_AUTO_ROUTE_CONFIDENCE == 0.85
        assert config.LLM_HUMAN_REVIEW_THRESHOLD == 0.70

    def test_from_env(self):
        """Configuration can be loaded from environment variables."""
        with patch.dict("os.environ", {
            "PRECLASSIFY_KEYWORD_CONFIDENCE": "0.95",
            "PRECLASSIFY_EMBEDDING_THRESHOLD": "0.80",
        }):
            config = ThresholdConfig.from_env()
            assert config.KEYWORD_CONFIDENCE == 0.95
            assert config.EMBEDDING_AUTO_ROUTE == 0.80


# =============================================================================
# Classification Metrics Tests
# =============================================================================


class TestClassificationMetrics:
    """Tests for classification metrics tracking."""

    def test_initial_state(self):
        """Metrics start with zero values."""
        metrics = ClassificationMetrics()

        assert metrics.total == 0
        assert len(metrics.by_tier) == 0
        assert len(metrics.by_category) == 0

    def test_record_updates_counts(self):
        """Recording results updates counts correctly."""
        metrics = ClassificationMetrics()

        result = ClassificationResult(
            category=RequirementCategory.BACKEND_ONLY,
            confidence=1.0,
            tier=ClassificationTier.KEYWORD,
            processing_time_ms=0.5,
        )

        metrics.record(result)

        assert metrics.total == 1
        assert metrics.by_tier["keyword"] == 1
        assert metrics.by_category["backend_only"] == 1

    def test_llm_percentage(self):
        """LLM percentage is calculated correctly."""
        metrics = ClassificationMetrics()

        # Record 10 keyword and 1 LLM
        for _ in range(10):
            metrics.record(ClassificationResult(
                category=RequirementCategory.BACKEND_ONLY,
                confidence=1.0,
                tier=ClassificationTier.KEYWORD,
            ))

        metrics.record(ClassificationResult(
            category=RequirementCategory.FULL_STACK,
            confidence=0.8,
            tier=ClassificationTier.LLM,
        ))

        # 1 out of 11 = ~9.09%
        assert 9.0 < metrics.llm_percentage < 10.0

    def test_avg_processing_time(self):
        """Average processing time is calculated correctly."""
        metrics = ClassificationMetrics()

        metrics.record(ClassificationResult(
            category=RequirementCategory.BACKEND_ONLY,
            confidence=1.0,
            tier=ClassificationTier.KEYWORD,
            processing_time_ms=0.5,
        ))
        metrics.record(ClassificationResult(
            category=RequirementCategory.FRONTEND_ONLY,
            confidence=1.0,
            tier=ClassificationTier.KEYWORD,
            processing_time_ms=0.3,
        ))

        assert metrics.avg_processing_time_ms == 0.4

    def test_to_dict(self):
        """Metrics can be serialized to dictionary."""
        metrics = ClassificationMetrics()

        metrics.record(ClassificationResult(
            category=RequirementCategory.BACKEND_ONLY,
            confidence=1.0,
            tier=ClassificationTier.KEYWORD,
            processing_time_ms=0.5,
        ))

        d = metrics.to_dict()

        assert "total" in d
        assert "by_tier" in d
        assert "by_category" in d
        assert "llm_percentage" in d
        assert "avg_processing_time_ms" in d


# =============================================================================
# Classification Result Tests
# =============================================================================


class TestClassificationResult:
    """Tests for ClassificationResult dataclass."""

    def test_to_dict(self):
        """Result can be serialized to dictionary."""
        result = ClassificationResult(
            category=RequirementCategory.BACKEND_ONLY,
            confidence=1.0,
            tier=ClassificationTier.KEYWORD,
            processing_time_ms=0.5,
            source_keywords=["api", "endpoint"],
        )

        d = result.to_dict()

        assert d["category"] == "backend_only"
        assert d["confidence"] == 1.0
        assert d["tier"] == "keyword"
        assert d["processing_time_ms"] == 0.5
        assert d["source_keywords"] == ["api", "endpoint"]


# =============================================================================
# REQ_001.1: RequirementPreClassifier Tests
# =============================================================================


class TestRequirementPreClassifier:
    """Tests for REQ_001.1: RequirementPreClassifier class."""

    def test_classify_single_returns_result(self):
        """REQ_001.1 behavior 4: Returns category and confidence."""
        from planning_pipeline.pre_classifier import (
            RequirementPreClassifier,
            ClassificationResultV2,
            ClassificationMethod,
            RoutingDecision,
        )
        classifier = RequirementPreClassifier()

        result = classifier.classify_single("Implement REST API endpoint")

        assert isinstance(result, ClassificationResultV2)
        assert result.category in ["functional", "security", "performance", "usability", "integration", "non_functional"]
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.classification_method, ClassificationMethod)
        assert isinstance(result.routing_decision, RoutingDecision)

    def test_classify_batch_returns_list(self):
        """REQ_001.1 behavior 5: Batch classification support."""
        from planning_pipeline.pre_classifier import RequirementPreClassifier

        classifier = RequirementPreClassifier()
        requirements = [
            "Create REST API",
            "Build login form",
            "Implement authentication middleware",
        ]

        results = classifier.classify_batch(requirements)

        assert len(results) == 3
        assert all(r.confidence >= 0.0 for r in results)

    def test_keyword_patterns_accessible(self):
        """REQ_001.1 behavior 2: KEYWORD_PATTERNS is accessible."""
        from planning_pipeline.pre_classifier import KEYWORD_PATTERNS

        assert isinstance(KEYWORD_PATTERNS, dict)
        assert "backend_only" in KEYWORD_PATTERNS
        assert "frontend_only" in KEYWORD_PATTERNS
        assert "middleware" in KEYWORD_PATTERNS
        # Check some expected keywords exist
        assert "api" in KEYWORD_PATTERNS["backend_only"]
        assert "form" in KEYWORD_PATTERNS["frontend_only"]
        assert "auth" in KEYWORD_PATTERNS["middleware"]

    def test_backend_routing_decision(self):
        """REQ_001.1 behavior 3: Backend keywords route to backend_only."""
        from planning_pipeline.pre_classifier import RequirementPreClassifier, RoutingDecision

        classifier = RequirementPreClassifier()
        result = classifier.classify_single("Create database query and API endpoint")

        assert result.routing_decision == RoutingDecision.BACKEND_ONLY

    def test_frontend_routing_decision(self):
        """REQ_001.1: Frontend keywords route to frontend_only."""
        from planning_pipeline.pre_classifier import RequirementPreClassifier, RoutingDecision

        classifier = RequirementPreClassifier()
        result = classifier.classify_single("Build responsive UI form component")

        assert result.routing_decision == RoutingDecision.FRONTEND_ONLY

    def test_middleware_routing_decision(self):
        """REQ_001.1: Middleware keywords route to middleware."""
        from planning_pipeline.pre_classifier import RequirementPreClassifier, RoutingDecision

        classifier = RequirementPreClassifier()
        result = classifier.classify_single("Implement JWT token authentication middleware")

        assert result.routing_decision == RoutingDecision.MIDDLEWARE

    def test_processing_time_under_1ms(self):
        """REQ_001.1 behavior 9: Processing time < 1ms for keyword matching."""
        from planning_pipeline.pre_classifier import RequirementPreClassifier

        classifier = RequirementPreClassifier()

        # Run multiple classifications
        total_time = 0.0
        iterations = 1000
        for _ in range(iterations):
            result = classifier.classify_single("Implement REST API endpoint")
            total_time += result.processing_time_ms

        avg_time_ms = total_time / iterations
        assert avg_time_ms < 1.0, f"Average processing time {avg_time_ms}ms exceeds 1ms"

    def test_high_confidence_skips_llm(self):
        """REQ_001.1 behavior 8: >= 0.9 confidence skips LLM fallback."""
        from planning_pipeline.pre_classifier import (
            RequirementPreClassifier,
            ClassificationMethod,
        )
        from unittest.mock import MagicMock

        mock_llm = MagicMock(return_value=("security", 0.95))
        classifier = RequirementPreClassifier(llm_fn=mock_llm)

        # Should have high confidence from keywords and NOT call LLM
        result = classifier.classify_single("Create REST API endpoint with database query")

        assert result.confidence >= 0.9
        assert result.classification_method == ClassificationMethod.KEYWORD
        mock_llm.assert_not_called()


# =============================================================================
# REQ_001.3: Complexity Assessment Tests
# =============================================================================


class TestComplexityAssessment:
    """Tests for REQ_001.3: Complexity assessment function."""

    def test_simple_single_layer(self):
        """REQ_001.3 behavior 3: Single-layer is SIMPLE."""
        from planning_pipeline.pre_classifier import assess_complexity, ComplexityLevel

        # Mock requirement with single layer (backend only, no UI/middleware keywords)
        class MockRequirement:
            description = "Create database query for user lookup"
            implementation = None

        result = assess_complexity(MockRequirement())

        assert result.level == ComplexityLevel.SIMPLE
        assert result.layer_count == 1

    def test_medium_two_layers(self):
        """REQ_001.3 behavior 4: Two-layer is MEDIUM."""
        from planning_pipeline.pre_classifier import assess_complexity, ComplexityLevel

        class MockRequirement:
            description = "Build UI form that submits to API endpoint"
            implementation = None

        result = assess_complexity(MockRequirement())

        assert result.level == ComplexityLevel.MEDIUM
        assert result.layer_count == 2

    def test_complex_three_layers(self):
        """REQ_001.3 behavior 5: Three+ layers is COMPLEX."""
        from planning_pipeline.pre_classifier import assess_complexity, ComplexityLevel

        class MockRequirement:
            description = "Build UI form with auth middleware that submits to API backend"
            implementation = None

        result = assess_complexity(MockRequirement())

        assert result.level == ComplexityLevel.COMPLEX
        assert result.layer_count >= 3

    def test_cross_cutting_makes_complex(self):
        """REQ_001.3 behavior 6: Cross-cutting concerns make COMPLEX."""
        from planning_pipeline.pre_classifier import assess_complexity, ComplexityLevel

        class MockRequirement:
            description = "Implement logging and caching across all services"
            implementation = None

        result = assess_complexity(MockRequirement())

        assert result.level == ComplexityLevel.COMPLEX
        assert result.has_cross_cutting is True

    def test_returns_assessment_structure(self):
        """REQ_001.3 behavior 8: Returns layer_count, has_cross_cutting, confidence."""
        from planning_pipeline.pre_classifier import assess_complexity, ComplexityAssessment

        class MockRequirement:
            description = "Build API endpoint"
            implementation = None

        result = assess_complexity(MockRequirement())

        assert isinstance(result, ComplexityAssessment)
        assert hasattr(result, "level")
        assert hasattr(result, "layer_count")
        assert hasattr(result, "has_cross_cutting")
        assert hasattr(result, "confidence")
        assert 0.0 <= result.confidence <= 1.0


# =============================================================================
# REQ_001.4: Adaptive Prompts Tests
# =============================================================================


class TestAdaptivePrompts:
    """Tests for REQ_001.4: Adaptive prompt building."""

    def test_simple_has_minimal_criteria(self):
        """REQ_001.4 behavior 2: Simple requires 2-3 acceptance criteria."""
        from planning_pipeline.pre_classifier import (
            build_adaptive_prompt,
            ComplexityAssessment,
            ComplexityLevel,
        )

        class MockRequirement:
            description = "Build API endpoint"
            implementation = None
            routing_decision = None

        complexity = ComplexityAssessment(
            level=ComplexityLevel.SIMPLE,
            layer_count=1,
            has_cross_cutting=False,
            confidence=0.9,
        )

        prompt = build_adaptive_prompt(MockRequirement(), complexity, "Research context")

        assert "2-3 acceptance criteria" in prompt
        assert "Simple Requirement" in prompt
        assert "Function-Level" in prompt

    def test_medium_has_interface_definitions(self):
        """REQ_001.4 behavior 3: Medium requires interface definitions."""
        from planning_pipeline.pre_classifier import (
            build_adaptive_prompt,
            ComplexityAssessment,
            ComplexityLevel,
        )

        class MockRequirement:
            description = "Build UI form with API"
            implementation = None
            routing_decision = None

        complexity = ComplexityAssessment(
            level=ComplexityLevel.MEDIUM,
            layer_count=2,
            has_cross_cutting=False,
            confidence=0.85,
        )

        prompt = build_adaptive_prompt(MockRequirement(), complexity, "Research context")

        assert "4-6 acceptance criteria" in prompt
        assert "interface definitions" in prompt
        assert "Medium Requirement" in prompt
        assert "Class-Level" in prompt

    def test_complex_has_dependency_analysis(self):
        """REQ_001.4 behavior 4: Complex requires dependency analysis."""
        from planning_pipeline.pre_classifier import (
            build_adaptive_prompt,
            ComplexityAssessment,
            ComplexityLevel,
        )

        class MockRequirement:
            description = "Build full-stack feature"
            implementation = None
            routing_decision = None

        complexity = ComplexityAssessment(
            level=ComplexityLevel.COMPLEX,
            layer_count=3,
            has_cross_cutting=True,
            confidence=0.8,
        )

        prompt = build_adaptive_prompt(MockRequirement(), complexity, "Research context")

        assert "8-12 acceptance criteria" in prompt
        assert "Dependency Analysis" in prompt
        assert "Complex Requirement" in prompt
        assert "Repository-Level" in prompt

    def test_research_truncation_by_complexity(self):
        """REQ_001.4 behavior 6: Research content truncated by complexity."""
        from planning_pipeline.pre_classifier import (
            build_adaptive_prompt,
            ComplexityAssessment,
            ComplexityLevel,
            RESEARCH_TRUNCATION_LIMITS,
        )

        class MockRequirement:
            description = "Test requirement"
            implementation = None
            routing_decision = None

        # Create large research content
        large_research = "X" * 10000

        # Simple should truncate more aggressively
        simple_complexity = ComplexityAssessment(
            level=ComplexityLevel.SIMPLE,
            layer_count=1,
            has_cross_cutting=False,
            confidence=0.9,
        )
        simple_prompt = build_adaptive_prompt(MockRequirement(), simple_complexity, large_research)

        # Complex should include more research
        complex_complexity = ComplexityAssessment(
            level=ComplexityLevel.COMPLEX,
            layer_count=3,
            has_cross_cutting=True,
            confidence=0.8,
        )
        complex_prompt = build_adaptive_prompt(MockRequirement(), complex_complexity, large_research)

        # Verify truncation limits are applied
        assert len(simple_prompt) < len(complex_prompt)
        assert RESEARCH_TRUNCATION_LIMITS[ComplexityLevel.SIMPLE] < RESEARCH_TRUNCATION_LIMITS[ComplexityLevel.COMPLEX]

    def test_design_by_contract_for_medium_complex(self):
        """REQ_001.4 behavior 8: Design-by-contract for medium and complex."""
        from planning_pipeline.pre_classifier import (
            build_adaptive_prompt,
            ComplexityAssessment,
            ComplexityLevel,
        )

        class MockRequirement:
            description = "Test requirement"
            implementation = None
            routing_decision = None

        # Medium should have design contract
        medium_complexity = ComplexityAssessment(
            level=ComplexityLevel.MEDIUM,
            layer_count=2,
            has_cross_cutting=False,
            confidence=0.85,
        )
        medium_prompt = build_adaptive_prompt(MockRequirement(), medium_complexity, "Research")

        assert "Design Contract" in medium_prompt
        assert "Preconditions" in medium_prompt
        assert "Postconditions" in medium_prompt
        assert "Invariants" in medium_prompt

        # Simple should NOT have design contract
        simple_complexity = ComplexityAssessment(
            level=ComplexityLevel.SIMPLE,
            layer_count=1,
            has_cross_cutting=False,
            confidence=0.9,
        )
        simple_prompt = build_adaptive_prompt(MockRequirement(), simple_complexity, "Research")

        assert "Design Contract" not in simple_prompt


# =============================================================================
# REQ_001.5: Category-Specific BAML Function Tests
# =============================================================================


class TestCategoryBAMLFunctions:
    """Tests for REQ_001.5: Category-specific BAML function routing."""

    def test_functional_category_functions(self):
        """REQ_001.5: Functional category routes to functional functions."""
        from planning_pipeline.pre_classifier import get_category_baml_functions

        functions = get_category_baml_functions("functional")

        assert "ProcessGate1CategoryFunctionalPrompt" in functions
        assert len(functions) >= 2

    def test_security_category_functions(self):
        """REQ_001.5: Security category routes to security functions."""
        from planning_pipeline.pre_classifier import get_category_baml_functions

        functions = get_category_baml_functions("security")

        assert "ProcessGate1CategorySecurityPrompt" in functions

    def test_performance_category_functions(self):
        """REQ_001.5: Performance category routes to performance functions."""
        from planning_pipeline.pre_classifier import get_category_baml_functions

        functions = get_category_baml_functions("performance")

        assert "ProcessGate1CategoryPerformancePrompt" in functions

    def test_usability_category_functions(self):
        """REQ_001.5: Usability category routes to usability functions."""
        from planning_pipeline.pre_classifier import get_category_baml_functions

        functions = get_category_baml_functions("usability")

        assert "ProcessGate1CategoryUsabilityPrompt" in functions
        assert "ProcessGate1UserInteractionsPrompt" in functions

    def test_integration_category_functions(self):
        """REQ_001.5: Integration category routes to integration functions."""
        from planning_pipeline.pre_classifier import get_category_baml_functions

        functions = get_category_baml_functions("integration")

        assert "ProcessGate1CategoryIntegrationPrompt" in functions
        assert "ProcessGate1DataNeedsPrompt" in functions

    def test_unknown_category_defaults_to_functional(self):
        """REQ_001.5: Unknown categories default to functional functions."""
        from planning_pipeline.pre_classifier import get_category_baml_functions

        functions = get_category_baml_functions("unknown_category")

        # Should return functional defaults
        assert "ProcessGate1CategoryFunctionalPrompt" in functions

    def test_category_to_baml_mapping_complete(self):
        """REQ_001.5: All valid categories have BAML function mappings."""
        from planning_pipeline.pre_classifier import (
            CATEGORY_TO_BAML_FUNCTIONS,
            FunctionalCategory,
        )

        # All functional categories should have mappings
        for category in FunctionalCategory:
            assert category.value in CATEGORY_TO_BAML_FUNCTIONS, \
                f"Category {category.value} missing from CATEGORY_TO_BAML_FUNCTIONS"


# =============================================================================
# REQ_005.5: Enhanced ThresholdConfig Tests
# =============================================================================


class TestThresholdConfigEnhanced:
    """Tests for REQ_005.5: Enhanced threshold configuration."""

    def test_frozen_dataclass(self):
        """REQ_005.5 behavior 1: ThresholdConfig is a frozen dataclass."""
        config = ThresholdConfig()

        # Should raise error when trying to modify
        with pytest.raises(Exception):  # FrozenInstanceError
            config.KEYWORD_CONFIDENCE = 0.5

    def test_all_five_parameters(self):
        """REQ_005.5 behavior 2: All five threshold parameters present."""
        config = ThresholdConfig()

        assert hasattr(config, "KEYWORD_CONFIDENCE")
        assert hasattr(config, "EMBEDDING_SIMILARITY_INITIAL")
        assert hasattr(config, "EMBEDDING_SIMILARITY_MIN")
        assert hasattr(config, "LLM_AUTO_ROUTE_CONFIDENCE")
        assert hasattr(config, "LLM_HUMAN_REVIEW_THRESHOLD")

    def test_keyword_confidence_must_be_1(self):
        """REQ_005.5 behavior 3: KEYWORD_CONFIDENCE must be 1.0."""
        config = ThresholdConfig()
        assert config.KEYWORD_CONFIDENCE == 1.0

        # Validation should reject non-1.0 values
        invalid_config = ThresholdConfig(KEYWORD_CONFIDENCE=0.9)
        with pytest.raises(ValueError):
            invalid_config.validate()

    def test_embedding_initial_default_075(self):
        """REQ_005.5 behavior 4: EMBEDDING_SIMILARITY_INITIAL defaults to 0.75."""
        config = ThresholdConfig()
        assert config.EMBEDDING_SIMILARITY_INITIAL == 0.75

    def test_embedding_min_default_020(self):
        """REQ_005.5 behavior 5: EMBEDDING_SIMILARITY_MIN defaults to 0.20."""
        config = ThresholdConfig()
        assert config.EMBEDDING_SIMILARITY_MIN == 0.20

    def test_llm_thresholds_defaults(self):
        """REQ_005.5 behavior 6: LLM thresholds have correct defaults."""
        config = ThresholdConfig()
        assert config.LLM_AUTO_ROUTE_CONFIDENCE == 0.85
        assert config.LLM_HUMAN_REVIEW_THRESHOLD == 0.70

    def test_from_env_loads_all_parameters(self):
        """REQ_005.5 behavior 7: from_env() loads all parameters."""
        with patch.dict("os.environ", {
            "PRECLASSIFY_KEYWORD_CONFIDENCE": "1.0",
            "PRECLASSIFY_EMBEDDING_SIMILARITY_INITIAL": "0.80",
            "PRECLASSIFY_EMBEDDING_SIMILARITY_MIN": "0.25",
            "PRECLASSIFY_LLM_AUTO_ROUTE_CONFIDENCE": "0.90",
            "PRECLASSIFY_LLM_HUMAN_REVIEW_THRESHOLD": "0.75",
        }):
            config = ThresholdConfig.from_env()
            assert config.EMBEDDING_SIMILARITY_INITIAL == 0.80
            assert config.EMBEDDING_SIMILARITY_MIN == 0.25
            assert config.LLM_AUTO_ROUTE_CONFIDENCE == 0.90
            assert config.LLM_HUMAN_REVIEW_THRESHOLD == 0.75

    def test_to_dict_from_dict_roundtrip(self):
        """REQ_005.5 behavior 9: Serialization and deserialization work."""
        original = ThresholdConfig(
            EMBEDDING_SIMILARITY_INITIAL=0.80,
            EMBEDDING_SIMILARITY_MIN=0.25,
        )

        data = original.to_dict()
        restored = ThresholdConfig.from_dict(data)

        assert restored.EMBEDDING_SIMILARITY_INITIAL == original.EMBEDDING_SIMILARITY_INITIAL
        assert restored.EMBEDDING_SIMILARITY_MIN == original.EMBEDDING_SIMILARITY_MIN

    def test_validate_min_less_than_initial(self):
        """REQ_005.5 behavior 10: EMBEDDING_SIMILARITY_MIN < EMBEDDING_SIMILARITY_INITIAL."""
        # Valid config
        valid = ThresholdConfig(
            EMBEDDING_SIMILARITY_INITIAL=0.75,
            EMBEDDING_SIMILARITY_MIN=0.20,
        )
        valid.validate()  # Should not raise

        # Invalid config (min >= initial)
        invalid = ThresholdConfig(
            EMBEDDING_SIMILARITY_INITIAL=0.50,
            EMBEDDING_SIMILARITY_MIN=0.60,
        )
        with pytest.raises(ValueError):
            invalid.validate()

    def test_validate_review_less_than_auto_route(self):
        """REQ_005.5 behavior 10: LLM_HUMAN_REVIEW_THRESHOLD < LLM_AUTO_ROUTE_CONFIDENCE."""
        # Invalid config (review >= auto_route)
        invalid = ThresholdConfig(
            LLM_AUTO_ROUTE_CONFIDENCE=0.80,
            LLM_HUMAN_REVIEW_THRESHOLD=0.85,
        )
        with pytest.raises(ValueError):
            invalid.validate()

    def test_default_factory_method(self):
        """REQ_005.5 behavior 12: ThresholdConfig.default() returns defaults."""
        config = ThresholdConfig.default()
        assert config.KEYWORD_CONFIDENCE == 1.0
        assert config.EMBEDDING_SIMILARITY_INITIAL == 0.75


# =============================================================================
# REQ_005.2: Embedding Calibration Tests
# =============================================================================


class TestEmbeddingCalibration:
    """Tests for REQ_005.2: Embedding classifier calibration."""

    @pytest.fixture
    def mock_embedding_fn(self):
        """Create a mock embedding function for testing."""
        def embed(text: str) -> list[float]:
            if "api" in text.lower() or "database" in text.lower():
                return [1.0, 0.0, 0.0, 0.0]
            elif "form" in text.lower() or "button" in text.lower():
                return [0.0, 1.0, 0.0, 0.0]
            elif "auth" in text.lower() or "token" in text.lower():
                return [0.0, 0.0, 1.0, 0.0]
            else:
                return [0.25, 0.25, 0.25, 0.25]
        return embed

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="Requires numpy")
    def test_initial_threshold_is_075(self, mock_embedding_fn):
        """REQ_005.2 behavior 1: Initial threshold before calibration is 0.75."""
        classifier = EmbeddingClassifier(embedding_fn=mock_embedding_fn)
        assert classifier.get_effective_threshold() == 0.75
        assert classifier.calibrated_threshold is None

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="Requires numpy")
    def test_fit_accepts_training_samples(self, mock_embedding_fn):
        """REQ_005.2 behavior 2: fit() accepts labeled training samples."""
        classifier = EmbeddingClassifier(embedding_fn=mock_embedding_fn)

        training_samples = [
            ("Create API endpoint", "backend_only"),
            ("Build login form", "frontend_only"),
            ("Implement auth middleware", "middleware"),
            ("Create database query", "backend_only"),
            ("Add button handler", "frontend_only"),
        ]

        threshold = classifier.fit(training_samples, iterations=50)
        assert 0.0 <= threshold <= 1.0

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="Requires numpy")
    def test_fit_runs_iterations(self, mock_embedding_fn):
        """REQ_005.2 behavior 3: fit() runs specified iterations."""
        classifier = EmbeddingClassifier(embedding_fn=mock_embedding_fn)

        training_samples = [
            ("Create API endpoint", "backend_only"),
            ("Build login form", "frontend_only"),
            ("Implement auth middleware", "middleware"),
            ("Create database query", "backend_only"),
            ("Add button handler", "frontend_only"),
        ]

        # Should run without error with different iteration counts
        classifier.fit(training_samples, iterations=10)
        classifier.fit(training_samples, iterations=100)

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="Requires numpy")
    def test_calibrated_threshold_stored(self, mock_embedding_fn):
        """REQ_005.2 behavior 4: Calibrated threshold is stored."""
        classifier = EmbeddingClassifier(embedding_fn=mock_embedding_fn)

        training_samples = [
            ("Create API endpoint", "backend_only"),
            ("Build login form", "frontend_only"),
            ("Implement auth middleware", "middleware"),
            ("Create database query", "backend_only"),
            ("Add button handler", "frontend_only"),
        ]

        calibrated = classifier.fit(training_samples, iterations=50)
        assert classifier.calibrated_threshold == calibrated
        assert classifier.get_effective_threshold() == calibrated

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="Requires numpy")
    def test_coverage_metrics_tracking(self, mock_embedding_fn):
        """REQ_005.2 behavior 9: Tier 2 coverage metrics tracked."""
        classifier = EmbeddingClassifier(embedding_fn=mock_embedding_fn)
        classifier.add_reference_example(RequirementCategory.BACKEND_ONLY, "API query")

        # Set a low threshold to ensure routing
        classifier.calibrated_threshold = 0.1

        classifier.classify("Create API endpoint")
        classifier.classify("Something unrelated")

        assert classifier.coverage_metrics["total_classified"] == 2
        assert classifier.tier2_coverage_percentage >= 0

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="Requires numpy")
    def test_save_load_calibration(self, mock_embedding_fn, tmp_path):
        """REQ_005.2 behavior 11: Calibration can be saved and loaded."""
        classifier = EmbeddingClassifier(embedding_fn=mock_embedding_fn)
        classifier.calibrated_threshold = 0.28

        path = tmp_path / "calibration.json"
        classifier.save_calibration(str(path))

        # Load into new classifier
        classifier2 = EmbeddingClassifier(embedding_fn=mock_embedding_fn)
        classifier2.load_calibration(str(path))

        assert classifier2.calibrated_threshold == 0.28


# =============================================================================
# REQ_005.3: LLM Classification Thresholds Tests
# =============================================================================


class TestLLMClassificationThresholds:
    """Tests for REQ_005.3: LLM classification thresholds."""

    def test_auto_route_threshold_085(self):
        """REQ_005.3 behavior 3: Confidence >= 0.85 triggers automatic routing."""
        mock_fn = MagicMock(return_value=("backend_only", 0.90))
        config = ThresholdConfig()
        classifier = LLMClassifier(llm_fn=mock_fn, threshold_config=config)

        result = classifier.classify("Some requirement")

        assert result.category == RequirementCategory.BACKEND_ONLY
        assert classifier.coverage_metrics["auto_routed"] == 1

    def test_warning_threshold_070_to_085(self):
        """REQ_005.3 behavior 4: Confidence 0.70-0.85 logs warning but routes."""
        mock_fn = MagicMock(return_value=("backend_only", 0.75))
        classifier = LLMClassifier(llm_fn=mock_fn)

        result = classifier.classify("Some requirement")

        assert result.category == RequirementCategory.BACKEND_ONLY
        assert classifier.coverage_metrics["warning_routed"] == 1

    def test_human_review_threshold_below_070(self):
        """REQ_005.3 behavior 5: Confidence < 0.70 flags for human review."""
        mock_fn = MagicMock(return_value=("backend_only", 0.50))
        classifier = LLMClassifier(llm_fn=mock_fn)

        result = classifier.classify("Some requirement")

        # Should default to full_stack for low confidence
        assert result.category == RequirementCategory.FULL_STACK
        assert classifier.coverage_metrics["flagged_for_review"] == 1

    def test_human_review_queue_populated(self):
        """REQ_005.3 behavior 6: Low confidence adds to review queue."""
        mock_fn = MagicMock(return_value=("backend_only", 0.50))
        classifier = LLMClassifier(llm_fn=mock_fn)

        classifier.classify("Some requirement")

        queue = classifier.get_review_queue()
        assert len(queue) == 1
        assert queue[0]["requirement_text"] == "Some requirement"
        assert queue[0]["predicted_category"] == "backend_only"

    def test_reasoning_captured_in_result(self):
        """REQ_005.3 behavior 9: Reasoning/explanation is captured."""
        mock_fn = MagicMock(return_value=("backend_only", 0.50, "Contains database operations"))
        classifier = LLMClassifier(llm_fn=mock_fn)

        classifier.classify("Some requirement")

        queue = classifier.get_review_queue()
        assert queue[0]["reasoning"] == "Contains database operations"

    def test_batch_classification(self):
        """REQ_005.3 behavior 10: Batch classification works."""
        mock_fn = MagicMock(return_value=("backend_only", 0.90))
        classifier = LLMClassifier(llm_fn=mock_fn)

        results = classifier.classify_batch(["Req 1", "Req 2", "Req 3"])

        assert len(results) == 3
        assert mock_fn.call_count == 3


# =============================================================================
# REQ_005.4: Training Sample Collection Tests
# =============================================================================


class TestTrainingSampleCollection:
    """Tests for REQ_005.4: Training sample collection."""

    def test_training_sample_dataclass(self):
        """REQ_005.4 behavior 1: TrainingSample has required fields."""
        from planning_pipeline.pre_classifier import TrainingSample

        sample = TrainingSample(
            requirement_text="Create API",
            tier1_category="backend_only",
            tier1_confidence=1.0,
        )

        assert sample.requirement_text == "Create API"
        assert sample.tier1_category == "backend_only"
        assert sample.tier1_confidence == 1.0
        assert sample.tier2_category is None

    def test_collector_collects_samples(self):
        """REQ_005.4 behavior 2: Collector collects tier results."""
        from planning_pipeline.pre_classifier import TrainingSampleCollector

        collector = TrainingSampleCollector()

        tier1_result = ClassificationResult(
            category=RequirementCategory.BACKEND_ONLY,
            confidence=1.0,
            tier=ClassificationTier.KEYWORD,
        )

        sample = collector.collect(
            requirement_text="Create API",
            tier1_result=tier1_result,
            final_category="backend_only",
        )

        assert sample.tier1_category == "backend_only"
        assert sample.tier1_confidence == 1.0
        assert sample.final_category == "backend_only"

    def test_collector_stores_all_tiers(self):
        """REQ_005.4 behavior 3: Collector stores all tier results."""
        from planning_pipeline.pre_classifier import TrainingSampleCollector

        collector = TrainingSampleCollector()

        tier1_result = ClassificationResult(
            category=RequirementCategory.AMBIGUOUS,
            confidence=0.0,
            tier=ClassificationTier.KEYWORD,
        )
        tier2_result = ClassificationResult(
            category=RequirementCategory.BACKEND_ONLY,
            confidence=0.65,
            tier=ClassificationTier.EMBEDDING,
        )
        tier3_result = ClassificationResult(
            category=RequirementCategory.BACKEND_ONLY,
            confidence=0.85,
            tier=ClassificationTier.LLM,
        )

        sample = collector.collect(
            requirement_text="Create API",
            tier1_result=tier1_result,
            tier2_result=tier2_result,
            tier3_result=tier3_result,
            final_category="backend_only",
        )

        assert sample.tier1_category == "ambiguous"
        assert sample.tier2_category == "backend_only"
        assert sample.tier2_confidence == 0.65
        assert sample.tier3_category == "backend_only"
        assert sample.tier3_confidence == 0.85

    def test_export_to_jsonl(self, tmp_path):
        """REQ_005.4 behavior 4: Export to JSONL format."""
        from planning_pipeline.pre_classifier import TrainingSampleCollector

        collector = TrainingSampleCollector()

        tier1_result = ClassificationResult(
            category=RequirementCategory.BACKEND_ONLY,
            confidence=1.0,
            tier=ClassificationTier.KEYWORD,
        )

        collector.collect("Req 1", tier1_result, final_category="backend_only")
        collector.collect("Req 2", tier1_result, final_category="backend_only")

        path = tmp_path / "samples.jsonl"
        count = collector.export_to_file(str(path), format="jsonl")

        assert count == 2
        assert path.exists()

        # Verify can load back
        collector2 = TrainingSampleCollector()
        loaded = collector2.load_from_file(str(path), format="jsonl")
        assert loaded == 2

    def test_samples_for_tier2_calibration(self):
        """REQ_005.4 behavior 5: Get samples formatted for Tier 2 calibration."""
        from planning_pipeline.pre_classifier import TrainingSampleCollector

        collector = TrainingSampleCollector()

        tier1_result = ClassificationResult(
            category=RequirementCategory.BACKEND_ONLY,
            confidence=1.0,
            tier=ClassificationTier.KEYWORD,
        )

        collector.collect("Req 1", tier1_result, final_category="backend_only")
        collector.collect("Req 2", tier1_result, final_category="frontend_only")
        collector.collect("Req 3", tier1_result, final_category=None)  # No final

        calibration_samples = collector.get_samples_for_tier2_calibration()

        assert len(calibration_samples) == 2  # Only those with final_category
        assert ("Req 1", "backend_only") in calibration_samples
        assert ("Req 2", "frontend_only") in calibration_samples

    def test_tier_coverage_stats(self):
        """REQ_005.4 behavior 6: Calculate tier coverage statistics."""
        from planning_pipeline.pre_classifier import TrainingSampleCollector

        collector = TrainingSampleCollector()

        tier1_result = ClassificationResult(
            category=RequirementCategory.BACKEND_ONLY,
            confidence=1.0,
            tier=ClassificationTier.KEYWORD,
        )
        tier2_result = ClassificationResult(
            category=RequirementCategory.BACKEND_ONLY,
            confidence=0.8,
            tier=ClassificationTier.EMBEDDING,
        )

        # 2 tier1-only, 1 with tier2
        collector.collect("Req 1", tier1_result)
        collector.collect("Req 2", tier1_result)
        collector.collect("Req 3", tier1_result, tier2_result=tier2_result)

        stats = collector.get_tier_coverage_stats()

        assert stats["total_samples"] == 3
        assert stats["tier1_only"] == 2
        assert stats["tier2_invoked"] == 1
        assert stats["tier1_percentage"] == pytest.approx(66.67, rel=0.1)

    def test_max_samples_limit(self):
        """REQ_005.4 behavior 7: Collector respects max samples limit."""
        from planning_pipeline.pre_classifier import TrainingSampleCollector

        collector = TrainingSampleCollector(max_samples=5)

        tier1_result = ClassificationResult(
            category=RequirementCategory.BACKEND_ONLY,
            confidence=1.0,
            tier=ClassificationTier.KEYWORD,
        )

        for i in range(10):
            collector.collect(f"Req {i}", tier1_result)

        assert len(collector.get_samples()) == 5
        # Should keep the most recent samples
        assert collector.get_samples()[0].requirement_text == "Req 5"

    def test_global_collector_singleton(self):
        """REQ_005.4 behavior 8: Global collector singleton."""
        from planning_pipeline.pre_classifier import get_training_collector

        collector1 = get_training_collector()
        collector2 = get_training_collector()

        assert collector1 is collector2

        # Different project_id creates new collector
        collector3 = get_training_collector(project_id="new_project")
        assert collector3 is not collector1
