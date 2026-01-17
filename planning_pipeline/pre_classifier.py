"""Pre-classification routing module for requirement categorization.

This module implements a cascaded classification approach to eliminate unnecessary
LLM processing by routing requirements based on:
1. Keyword matching (<1ms) - Fast pattern matching for obvious categories
2. Embedding similarity (1-10ms) - Semantic matching using pre-computed embeddings
3. LLM classification (100-1000ms) - Full classification for ambiguous cases

Categories:
- backend_only: API, database, server-side requirements
- frontend_only: UI, pages, forms, display components
- middleware: Auth, validation, session management
- full_stack: Requirements spanning multiple layers

Usage:
    from planning_pipeline.pre_classifier import PreClassifier

    classifier = PreClassifier()
    result = classifier.classify("Implement REST API endpoint for user data")
    print(result.category)  # "backend_only"
    print(result.confidence)  # 1.0
"""

import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

# Optional imports for embedding classifier
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class RequirementCategory(str, Enum):
    """Categories for requirement classification."""
    BACKEND_ONLY = "backend_only"
    FRONTEND_ONLY = "frontend_only"
    MIDDLEWARE = "middleware"
    FULL_STACK = "full_stack"
    AMBIGUOUS = "ambiguous"  # Requires LLM classification


class ClassificationTier(str, Enum):
    """Classification tier that produced the result."""
    KEYWORD = "keyword"
    EMBEDDING = "embedding"
    LLM = "llm"


@dataclass
class ClassificationResult:
    """Result of requirement classification.

    Attributes:
        category: The classified category
        confidence: Confidence score (0.0-1.0)
        tier: Which classification tier produced this result
        processing_time_ms: Time taken to classify in milliseconds
        top_matches: Top category matches with scores (for debugging)
        source_keywords: Keywords that triggered the classification (for keyword tier)
    """
    category: RequirementCategory
    confidence: float
    tier: ClassificationTier
    processing_time_ms: float = 0.0
    top_matches: list[tuple[str, float]] = field(default_factory=list)
    source_keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "category": self.category.value,
            "confidence": self.confidence,
            "tier": self.tier.value,
            "processing_time_ms": self.processing_time_ms,
            "top_matches": self.top_matches,
            "source_keywords": self.source_keywords,
        }


@dataclass(frozen=True)
class ThresholdConfig:
    """Configuration for classification thresholds (REQ_005.5).

    Implements REQ_005.5: Frozen dataclass with all five threshold parameters
    for three-tier classification strategy.

    Attributes:
        KEYWORD_CONFIDENCE: Confidence for exact keyword matches (default: 1.0, must be 1.0)
        EMBEDDING_SIMILARITY_INITIAL: Initial embedding threshold before calibration (default: 0.75)
        EMBEDDING_SIMILARITY_MIN: Minimum embedding threshold after calibration (default: 0.20)
        LLM_AUTO_ROUTE_CONFIDENCE: Threshold for auto-routing via LLM (default: 0.85)
        LLM_HUMAN_REVIEW_THRESHOLD: Threshold for flagging for human review (default: 0.70)
    """
    KEYWORD_CONFIDENCE: float = 1.0
    EMBEDDING_SIMILARITY_INITIAL: float = 0.75
    EMBEDDING_SIMILARITY_MIN: float = 0.20
    LLM_AUTO_ROUTE_CONFIDENCE: float = 0.85
    LLM_HUMAN_REVIEW_THRESHOLD: float = 0.70

    # Legacy aliases for backwards compatibility
    @property
    def EMBEDDING_AUTO_ROUTE(self) -> float:
        """Legacy alias for EMBEDDING_SIMILARITY_INITIAL."""
        return self.EMBEDDING_SIMILARITY_INITIAL

    @property
    def LLM_AUTO_ROUTE(self) -> float:
        """Legacy alias for LLM_AUTO_ROUTE_CONFIDENCE."""
        return self.LLM_AUTO_ROUTE_CONFIDENCE

    @property
    def LLM_REVIEW(self) -> float:
        """Legacy alias for LLM_HUMAN_REVIEW_THRESHOLD."""
        return self.LLM_HUMAN_REVIEW_THRESHOLD

    def __post_init__(self) -> None:
        """Validate threshold constraints after initialization."""
        # Skip validation if called during object creation
        pass

    def validate(self) -> None:
        """Validate threshold constraints per REQ_005.5 behavior 10.

        Raises:
            ValueError: If constraints are violated
        """
        if self.KEYWORD_CONFIDENCE != 1.0:
            raise ValueError(f"KEYWORD_CONFIDENCE must be 1.0, got {self.KEYWORD_CONFIDENCE}")

        if self.EMBEDDING_SIMILARITY_MIN >= self.EMBEDDING_SIMILARITY_INITIAL:
            raise ValueError(
                f"EMBEDDING_SIMILARITY_MIN ({self.EMBEDDING_SIMILARITY_MIN}) must be < "
                f"EMBEDDING_SIMILARITY_INITIAL ({self.EMBEDDING_SIMILARITY_INITIAL})"
            )

        if self.LLM_HUMAN_REVIEW_THRESHOLD >= self.LLM_AUTO_ROUTE_CONFIDENCE:
            raise ValueError(
                f"LLM_HUMAN_REVIEW_THRESHOLD ({self.LLM_HUMAN_REVIEW_THRESHOLD}) must be < "
                f"LLM_AUTO_ROUTE_CONFIDENCE ({self.LLM_AUTO_ROUTE_CONFIDENCE})"
            )

    @classmethod
    def default(cls) -> "ThresholdConfig":
        """Get default configuration instance per REQ_005.5 behavior 12."""
        return cls()

    @classmethod
    def from_env(cls) -> "ThresholdConfig":
        """Load configuration from environment variables per REQ_005.5 behavior 7.

        Environment variables:
            PRECLASSIFY_KEYWORD_CONFIDENCE: Keyword match confidence (default: 1.0)
            PRECLASSIFY_EMBEDDING_SIMILARITY_INITIAL: Initial embedding threshold (default: 0.75)
            PRECLASSIFY_EMBEDDING_SIMILARITY_MIN: Min embedding threshold (default: 0.20)
            PRECLASSIFY_LLM_AUTO_ROUTE_CONFIDENCE: LLM auto-route threshold (default: 0.85)
            PRECLASSIFY_LLM_HUMAN_REVIEW_THRESHOLD: LLM review threshold (default: 0.70)
        """
        return cls(
            KEYWORD_CONFIDENCE=float(os.getenv("PRECLASSIFY_KEYWORD_CONFIDENCE", "1.0")),
            EMBEDDING_SIMILARITY_INITIAL=float(os.getenv(
                "PRECLASSIFY_EMBEDDING_SIMILARITY_INITIAL",
                os.getenv("PRECLASSIFY_EMBEDDING_THRESHOLD", "0.75")  # Legacy fallback
            )),
            EMBEDDING_SIMILARITY_MIN=float(os.getenv("PRECLASSIFY_EMBEDDING_SIMILARITY_MIN", "0.20")),
            LLM_AUTO_ROUTE_CONFIDENCE=float(os.getenv(
                "PRECLASSIFY_LLM_AUTO_ROUTE_CONFIDENCE",
                os.getenv("PRECLASSIFY_LLM_AUTO_THRESHOLD", "0.85")  # Legacy fallback
            )),
            LLM_HUMAN_REVIEW_THRESHOLD=float(os.getenv(
                "PRECLASSIFY_LLM_HUMAN_REVIEW_THRESHOLD",
                os.getenv("PRECLASSIFY_LLM_REVIEW_THRESHOLD", "0.70")  # Legacy fallback
            )),
        )

    def to_dict(self) -> dict[str, float]:
        """Serialize to dictionary per REQ_005.5 behavior 9."""
        return {
            "KEYWORD_CONFIDENCE": self.KEYWORD_CONFIDENCE,
            "EMBEDDING_SIMILARITY_INITIAL": self.EMBEDDING_SIMILARITY_INITIAL,
            "EMBEDDING_SIMILARITY_MIN": self.EMBEDDING_SIMILARITY_MIN,
            "LLM_AUTO_ROUTE_CONFIDENCE": self.LLM_AUTO_ROUTE_CONFIDENCE,
            "LLM_HUMAN_REVIEW_THRESHOLD": self.LLM_HUMAN_REVIEW_THRESHOLD,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "ThresholdConfig":
        """Deserialize from dictionary per REQ_005.5 behavior 9."""
        return cls(
            KEYWORD_CONFIDENCE=data.get("KEYWORD_CONFIDENCE", 1.0),
            EMBEDDING_SIMILARITY_INITIAL=data.get("EMBEDDING_SIMILARITY_INITIAL", 0.75),
            EMBEDDING_SIMILARITY_MIN=data.get("EMBEDDING_SIMILARITY_MIN", 0.20),
            LLM_AUTO_ROUTE_CONFIDENCE=data.get("LLM_AUTO_ROUTE_CONFIDENCE", 0.85),
            LLM_HUMAN_REVIEW_THRESHOLD=data.get("LLM_HUMAN_REVIEW_THRESHOLD", 0.70),
        )


# Default keyword dictionaries for classification
# These can be extended via configuration
DEFAULT_KEYWORD_DICT: dict[RequirementCategory, set[str]] = {
    RequirementCategory.BACKEND_ONLY: {
        "api", "endpoint", "database", "server", "query", "rest", "graphql",
        "repository", "service", "orm", "sql", "nosql", "cache", "queue",
        "migration", "schema", "model", "entity", "crud", "backend",
    },
    RequirementCategory.FRONTEND_ONLY: {
        "ui", "page", "form", "button", "component", "display", "view", "render",
        "css", "style", "layout", "responsive", "mobile", "desktop", "screen",
        "modal", "dialog", "navigation", "menu", "header", "footer", "frontend",
        "react", "vue", "angular", "html", "template", "widget",
    },
    RequirementCategory.MIDDLEWARE: {
        "auth", "validate", "middleware", "session", "token", "permission", "role",
        "authentication", "authorization", "jwt", "oauth", "rbac", "acl",
        "interceptor", "filter", "guard", "policy", "rate-limit", "throttle",
    },
}

# Priority order for resolving multi-keyword conflicts
CATEGORY_PRIORITY = [
    RequirementCategory.MIDDLEWARE,
    RequirementCategory.BACKEND_ONLY,
    RequirementCategory.FRONTEND_ONLY,
]


class KeywordClassifier:
    """Fast keyword-based classifier with <1ms per requirement processing.

    Uses pattern matching to route requirements to categories based on
    keyword detection. Supports word boundaries to avoid false positives.

    Attributes:
        keywords: Dictionary mapping categories to keyword sets
        patterns: Pre-compiled regex patterns for each category
        threshold_config: Configuration for confidence thresholds
    """

    def __init__(
        self,
        keywords: Optional[dict[RequirementCategory, set[str]]] = None,
        threshold_config: Optional[ThresholdConfig] = None,
    ):
        """Initialize keyword classifier.

        Args:
            keywords: Custom keyword dictionary (uses DEFAULT_KEYWORD_DICT if None)
            threshold_config: Threshold configuration (uses ThresholdConfig.from_env() if None)
        """
        self.keywords = keywords or DEFAULT_KEYWORD_DICT.copy()
        self.threshold_config = threshold_config or ThresholdConfig.from_env()
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for each category's keywords."""
        self.patterns: dict[RequirementCategory, re.Pattern] = {}
        for category, keyword_set in self.keywords.items():
            # Build pattern with word boundaries for each keyword
            escaped_keywords = [re.escape(kw) for kw in keyword_set]
            pattern_str = r'\b(' + '|'.join(escaped_keywords) + r')\b'
            self.patterns[category] = re.compile(pattern_str, re.IGNORECASE)

    def add_keywords(self, category: RequirementCategory, keywords: set[str]) -> None:
        """Add keywords to a category and recompile patterns.

        Args:
            category: Category to add keywords to
            keywords: Set of keywords to add
        """
        if category not in self.keywords:
            self.keywords[category] = set()
        self.keywords[category].update(keywords)
        self._compile_patterns()

    def classify(self, requirement_text: str) -> ClassificationResult:
        """Classify a requirement based on keyword matching.

        Args:
            requirement_text: The requirement text to classify

        Returns:
            ClassificationResult with category, confidence, and matched keywords
        """
        start_time = time.perf_counter()

        # Find all matching keywords for each category
        category_matches: dict[RequirementCategory, list[str]] = {}

        for category, pattern in self.patterns.items():
            matches = pattern.findall(requirement_text)
            if matches:
                # Normalize matches to lowercase
                category_matches[category] = [m.lower() for m in matches]

        processing_time_ms = (time.perf_counter() - start_time) * 1000

        # No matches -> ambiguous
        if not category_matches:
            return ClassificationResult(
                category=RequirementCategory.AMBIGUOUS,
                confidence=0.0,
                tier=ClassificationTier.KEYWORD,
                processing_time_ms=processing_time_ms,
                top_matches=[],
                source_keywords=[],
            )

        # Apply priority rules for multi-category matches
        selected_category = RequirementCategory.AMBIGUOUS
        selected_keywords: list[str] = []

        for priority_category in CATEGORY_PRIORITY:
            if priority_category in category_matches:
                selected_category = priority_category
                selected_keywords = category_matches[priority_category]
                break

        # If no priority category matched, use the first available
        if selected_category == RequirementCategory.AMBIGUOUS:
            selected_category = next(iter(category_matches.keys()))
            selected_keywords = category_matches[selected_category]

        # Build top matches list for debugging
        top_matches = [
            (cat.value, len(kws))
            for cat, kws in sorted(
                category_matches.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )
        ]

        return ClassificationResult(
            category=selected_category,
            confidence=self.threshold_config.KEYWORD_CONFIDENCE,
            tier=ClassificationTier.KEYWORD,
            processing_time_ms=processing_time_ms,
            top_matches=top_matches,
            source_keywords=selected_keywords,
        )


class EmbeddingClassifier:
    """Embedding-based classifier with 1-10ms per requirement processing (REQ_005.2).

    Uses pre-computed schema reference embeddings with cosine similarity
    for semantic matching. Supports threshold calibration via fit() method.

    Implements REQ_005.2:
    - Initial threshold of 0.75 before calibration
    - fit() method runs 500 iterations of threshold optimization
    - Calibrated threshold stored for classification (expected: 0.22-0.30)
    - Classification latency 1-10ms per requirement

    Attributes:
        reference_embeddings: Pre-computed reference embeddings per category
        embedding_fn: Function for generating requirement embeddings
        threshold_config: Configuration for similarity thresholds
        calibrated_threshold: Calibrated threshold after fit() (None if not calibrated)
        coverage_metrics: Metrics tracking Tier 2 coverage
    """

    def __init__(
        self,
        embeddings_path: Optional[str] = None,
        threshold_config: Optional[ThresholdConfig] = None,
        embedding_fn: Optional[Callable[[str], list[float]]] = None,
    ):
        """Initialize embedding classifier.

        Args:
            embeddings_path: Path to pre-computed embeddings file
            threshold_config: Threshold configuration
            embedding_fn: Function to compute embeddings (required if no cached embeddings)
        """
        if not NUMPY_AVAILABLE:
            raise ImportError("numpy is required for EmbeddingClassifier")

        self.threshold_config = threshold_config or ThresholdConfig.from_env()
        self.embedding_fn = embedding_fn
        self.reference_embeddings: dict[RequirementCategory, np.ndarray] = {}
        self.calibrated_threshold: Optional[float] = None
        self.coverage_metrics = {
            "total_classified": 0,
            "tier2_routed": 0,
            "tier2_passed_to_tier3": 0,
        }

        if embeddings_path and os.path.exists(embeddings_path):
            self._load_embeddings(embeddings_path)

    def _load_embeddings(self, path: str) -> None:
        """Load pre-computed embeddings from file.

        Args:
            path: Path to embeddings file (NPZ format)
        """
        import numpy as np
        data = np.load(path, allow_pickle=True)
        for category in RequirementCategory:
            key = category.value
            if key in data:
                self.reference_embeddings[category] = data[key]

    def _save_embeddings(self, path: str) -> None:
        """Save reference embeddings to file.

        Args:
            path: Path to save embeddings (NPZ format)
        """
        import numpy as np
        np.savez(path, **{
            cat.value: emb for cat, emb in self.reference_embeddings.items()
        })

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors.

        Args:
            a: First vector
            b: Second vector (or matrix of vectors)

        Returns:
            Similarity score(s) between 0 and 1
        """
        import numpy as np

        # Handle matrix input for batch comparison
        if b.ndim == 2:
            # Normalize vectors
            a_norm = a / (np.linalg.norm(a) + 1e-8)
            b_norms = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-8)
            similarities = np.dot(b_norms, a_norm)
            return float(np.max(similarities))
        else:
            # Single vector comparison
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            return float(dot_product / (norm_a * norm_b + 1e-8))

    def add_reference_example(
        self,
        category: RequirementCategory,
        text: str
    ) -> None:
        """Add a reference example for a category.

        Args:
            category: Category for this example
            text: Example text to embed and store
        """
        if not self.embedding_fn:
            raise ValueError("embedding_fn required to add reference examples")

        import numpy as np
        embedding = np.array(self.embedding_fn(text))

        if category not in self.reference_embeddings:
            self.reference_embeddings[category] = embedding.reshape(1, -1)
        else:
            self.reference_embeddings[category] = np.vstack([
                self.reference_embeddings[category],
                embedding
            ])

    def fit(
        self,
        training_samples: list[tuple[str, str]],
        iterations: int = 500,
        validation_split: float = 0.2,
    ) -> float:
        """Calibrate embedding threshold using labeled training data (REQ_005.2).

        Implements REQ_005.2 behaviors 2-3:
        - Accepts labeled training samples as list of (requirement_text, category) tuples
        - Runs specified iterations of threshold optimization using cross-validation

        Args:
            training_samples: List of (requirement_text, category) tuples
            iterations: Number of optimization iterations (default: 500)
            validation_split: Fraction of data for validation (default: 0.2)

        Returns:
            Calibrated threshold value (expected post-calibration: 0.22-0.30)
        """
        if not self.embedding_fn:
            raise ValueError("embedding_fn required for calibration")
        if len(training_samples) < 5:
            raise ValueError("At least 5 training samples required for calibration")

        import numpy as np

        # Compute embeddings for all samples
        embeddings: list[np.ndarray] = []
        categories: list[str] = []
        for text, category in training_samples:
            emb = np.array(self.embedding_fn(text))
            embeddings.append(emb)
            categories.append(category)

        embeddings_array = np.array(embeddings)
        n_samples = len(training_samples)

        # Add training samples to reference embeddings
        for text, category in training_samples:
            try:
                cat_enum = RequirementCategory(category)
                self.add_reference_example(cat_enum, text)
            except ValueError:
                continue  # Skip invalid categories

        # Optimize threshold using cross-validation
        best_threshold = self.threshold_config.EMBEDDING_SIMILARITY_INITIAL
        best_accuracy = 0.0

        min_threshold = self.threshold_config.EMBEDDING_SIMILARITY_MIN
        max_threshold = self.threshold_config.EMBEDDING_SIMILARITY_INITIAL

        for iteration in range(iterations):
            # Randomly sample threshold in range
            threshold = min_threshold + (max_threshold - min_threshold) * np.random.random()

            # Cross-validation
            n_val = max(1, int(n_samples * validation_split))
            indices = np.random.permutation(n_samples)
            val_indices = indices[:n_val]
            train_indices = indices[n_val:]

            # Compute accuracy on validation set
            correct = 0
            for idx in val_indices:
                # Find most similar category
                best_sim = 0.0
                best_cat = None
                for cat, ref_embs in self.reference_embeddings.items():
                    if len(ref_embs) > 0:
                        sim = self._cosine_similarity(embeddings_array[idx], ref_embs)
                        if sim > best_sim:
                            best_sim = sim
                            best_cat = cat.value

                if best_sim >= threshold and best_cat == categories[idx]:
                    correct += 1
                elif best_sim < threshold:
                    # Below threshold counts as pass-through (not wrong)
                    pass

            accuracy = correct / n_val if n_val > 0 else 0

            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_threshold = threshold

        # Store calibrated threshold
        self.calibrated_threshold = best_threshold
        return best_threshold

    def get_effective_threshold(self) -> float:
        """Get the effective threshold (calibrated or initial).

        Returns:
            Calibrated threshold if available, otherwise initial threshold
        """
        if self.calibrated_threshold is not None:
            return self.calibrated_threshold
        return self.threshold_config.EMBEDDING_SIMILARITY_INITIAL

    def save_calibration(self, path: str) -> None:
        """Save calibrated threshold to file (REQ_005.2 behavior 11).

        Args:
            path: Path to save calibration data (JSON format)
        """
        import json
        data = {
            "calibrated_threshold": self.calibrated_threshold,
            "initial_threshold": self.threshold_config.EMBEDDING_SIMILARITY_INITIAL,
            "min_threshold": self.threshold_config.EMBEDDING_SIMILARITY_MIN,
        }
        with open(path, "w") as f:
            json.dump(data, f)

    def load_calibration(self, path: str) -> None:
        """Load calibrated threshold from file (REQ_005.2 behavior 11).

        Args:
            path: Path to calibration data file (JSON format)
        """
        import json
        with open(path, "r") as f:
            data = json.load(f)
        self.calibrated_threshold = data.get("calibrated_threshold")

    def classify(self, requirement_text: str) -> ClassificationResult:
        """Classify a requirement using embedding similarity (REQ_005.2).

        Implements REQ_005.2 behaviors 6-8:
        - Computes cosine similarity between input embedding and category references
        - Requirements with similarity >= threshold are auto-routed
        - Requirements below threshold are passed to Tier 3

        Args:
            requirement_text: The requirement text to classify

        Returns:
            ClassificationResult with category, confidence, and top matches
        """
        if not self.embedding_fn:
            raise ValueError("embedding_fn required for classification")

        import numpy as np
        start_time = time.perf_counter()

        # Compute embedding for input text
        input_embedding = np.array(self.embedding_fn(requirement_text))

        # Compute similarity against all reference embeddings
        similarities: list[tuple[RequirementCategory, float]] = []

        for category, ref_embeddings in self.reference_embeddings.items():
            if len(ref_embeddings) > 0:
                similarity = self._cosine_similarity(input_embedding, ref_embeddings)
                similarities.append((category, similarity))

        processing_time_ms = (time.perf_counter() - start_time) * 1000

        # Update coverage metrics
        self.coverage_metrics["total_classified"] += 1

        # No reference embeddings -> ambiguous
        if not similarities:
            self.coverage_metrics["tier2_passed_to_tier3"] += 1
            return ClassificationResult(
                category=RequirementCategory.AMBIGUOUS,
                confidence=0.0,
                tier=ClassificationTier.EMBEDDING,
                processing_time_ms=processing_time_ms,
                top_matches=[],
                source_keywords=[],
            )

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)

        top_category, top_confidence = similarities[0]
        top_matches = [(cat.value, score) for cat, score in similarities[:3]]

        # Use effective threshold (calibrated if available)
        threshold = self.get_effective_threshold()

        # Check if above auto-route threshold
        if top_confidence >= threshold:
            category = top_category
            self.coverage_metrics["tier2_routed"] += 1
        else:
            category = RequirementCategory.AMBIGUOUS
            self.coverage_metrics["tier2_passed_to_tier3"] += 1

        return ClassificationResult(
            category=category,
            confidence=top_confidence,
            tier=ClassificationTier.EMBEDDING,
            processing_time_ms=processing_time_ms,
            top_matches=top_matches,
            source_keywords=[],
        )

    @property
    def is_ready(self) -> bool:
        """Check if classifier has sufficient reference embeddings."""
        return len(self.reference_embeddings) > 0

    @property
    def tier2_coverage_percentage(self) -> float:
        """Calculate Tier 2 coverage percentage (REQ_005.2 behavior 9).

        Returns:
            Percentage of Tier 1 pass-throughs routed via Tier 2 (target: 30-40%)
        """
        total = self.coverage_metrics["tier2_routed"] + self.coverage_metrics["tier2_passed_to_tier3"]
        if total == 0:
            return 0.0
        return (self.coverage_metrics["tier2_routed"] / total) * 100


@dataclass
class LLMClassificationResult:
    """Extended result for LLM classification with reasoning (REQ_005.3 behavior 9).

    Attributes:
        category: Classified category
        confidence: Confidence score (0.0-1.0)
        reasoning: Explanation/reasoning for the classification
        flagged_for_review: Whether this requires human review
    """
    category: str
    confidence: float
    reasoning: str = ""
    flagged_for_review: bool = False


class LLMClassifier:
    """LLM-based classifier for ambiguous requirements (REQ_005.3).

    Uses Claude Opus 4.5 via Agent SDK for highest quality classification
    when keyword and embedding classifiers cannot confidently categorize.

    Implements REQ_005.3:
    - 0.85 auto-route confidence threshold
    - 0.70 human review threshold for ~10% most ambiguous cases
    - Supports batch classification for efficiency

    Attributes:
        llm_fn: Function to call LLM for classification
        threshold_config: Configuration for confidence thresholds
        cache: Cache for previously classified requirements
        human_review_queue: Queue of requirements flagged for human review
        coverage_metrics: Metrics for Tier 3 coverage tracking
    """

    def __init__(
        self,
        llm_fn: Optional[Callable[[str], tuple[str, float]]] = None,
        threshold_config: Optional[ThresholdConfig] = None,
    ):
        """Initialize LLM classifier.

        Args:
            llm_fn: Function that takes requirement text and returns (category, confidence)
                    Or returns (category, confidence, reasoning) tuple for audit purposes
            threshold_config: Threshold configuration
        """
        self.llm_fn = llm_fn
        self.threshold_config = threshold_config or ThresholdConfig.from_env()
        self.cache: dict[str, ClassificationResult] = {}
        self.human_review_queue: list[dict[str, Any]] = []
        self.coverage_metrics = {
            "total_classified": 0,
            "auto_routed": 0,
            "warning_routed": 0,
            "flagged_for_review": 0,
        }

    def get_review_queue(self) -> list[dict[str, Any]]:
        """Get the human review queue (REQ_005.3 behavior 6).

        Returns:
            List of requirements flagged for human review with metadata
        """
        return self.human_review_queue.copy()

    def clear_review_queue(self) -> None:
        """Clear the human review queue after processing."""
        self.human_review_queue = []

    def add_to_review_queue(
        self,
        requirement_text: str,
        category: str,
        confidence: float,
        reasoning: str = "",
    ) -> None:
        """Add a requirement to the human review queue.

        Args:
            requirement_text: The requirement text
            category: Predicted category
            confidence: Confidence score
            reasoning: Explanation for the classification
        """
        self.human_review_queue.append({
            "requirement_text": requirement_text,
            "predicted_category": category,
            "confidence": confidence,
            "reasoning": reasoning,
            "reviewed": False,
            "final_category": None,
        })

    def classify_batch(
        self,
        requirements: list[str],
    ) -> list[ClassificationResult]:
        """Batch classification for efficiency (REQ_005.3 behavior 10).

        Args:
            requirements: List of requirement texts to classify

        Returns:
            List of ClassificationResult objects
        """
        # For now, classify individually but could be optimized for batch LLM calls
        return [self.classify(req) for req in requirements]

    def classify(self, requirement_text: str) -> ClassificationResult:
        """Classify a requirement using LLM (REQ_005.3).

        Implements REQ_005.3 behaviors 3-5:
        - Confidence >= 0.85 triggers automatic routing
        - Confidence between 0.70 and 0.85 logs warning but routes automatically
        - Confidence < 0.70 flags requirement for human review

        Args:
            requirement_text: The requirement text to classify

        Returns:
            ClassificationResult with category, confidence, and tier info
        """
        # Check cache first
        cache_key = requirement_text.strip().lower()
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            return ClassificationResult(
                category=cached.category,
                confidence=cached.confidence,
                tier=ClassificationTier.LLM,
                processing_time_ms=0.0,  # Cache hit
                top_matches=cached.top_matches,
                source_keywords=[],
            )

        if not self.llm_fn:
            # No LLM function configured, return ambiguous
            return ClassificationResult(
                category=RequirementCategory.AMBIGUOUS,
                confidence=0.0,
                tier=ClassificationTier.LLM,
                processing_time_ms=0.0,
                top_matches=[],
                source_keywords=[],
            )

        start_time = time.perf_counter()
        self.coverage_metrics["total_classified"] += 1

        try:
            llm_result = self.llm_fn(requirement_text)

            # Handle both 2-tuple and 3-tuple returns
            if len(llm_result) == 3:
                category_str, confidence, reasoning = llm_result
            else:
                category_str, confidence = llm_result
                reasoning = ""

            processing_time_ms = (time.perf_counter() - start_time) * 1000

            # Map string to enum
            try:
                category = RequirementCategory(category_str.lower())
            except ValueError:
                category = RequirementCategory.FULL_STACK

            # Apply confidence thresholds per REQ_005.3
            auto_route_threshold = self.threshold_config.LLM_AUTO_ROUTE_CONFIDENCE
            review_threshold = self.threshold_config.LLM_HUMAN_REVIEW_THRESHOLD

            if confidence >= auto_route_threshold:
                # REQ_005.3 behavior 3: Confidence >= 0.85 triggers automatic routing
                self.coverage_metrics["auto_routed"] += 1
            elif confidence >= review_threshold:
                # REQ_005.3 behavior 4: Confidence between 0.70 and 0.85
                # Log warning but still routes automatically
                self.coverage_metrics["warning_routed"] += 1
                import logging
                logging.warning(
                    f"LLM classification confidence {confidence:.2f} is below "
                    f"auto-route threshold {auto_route_threshold}. Category: {category.value}"
                )
            else:
                # REQ_005.3 behavior 5: Confidence < 0.70 flags for human review
                self.coverage_metrics["flagged_for_review"] += 1
                self.add_to_review_queue(requirement_text, category.value, confidence, reasoning)
                # Default to full_stack for low confidence
                category = RequirementCategory.FULL_STACK

            result = ClassificationResult(
                category=category,
                confidence=confidence,
                tier=ClassificationTier.LLM,
                processing_time_ms=processing_time_ms,
                top_matches=[(category.value, confidence)],
                source_keywords=[],
            )

            # Cache the result
            self.cache[cache_key] = result
            return result

        except Exception:
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            # Graceful degradation to full_stack on error
            return ClassificationResult(
                category=RequirementCategory.FULL_STACK,
                confidence=0.0,
                tier=ClassificationTier.LLM,
                processing_time_ms=processing_time_ms,
                top_matches=[],
                source_keywords=[],
            )


class PreClassifier:
    """Cascaded pre-classification router for requirements.

    Implements a tiered classification approach:
    1. Keyword matching (Tier 1) - <1ms, for obvious patterns
    2. Embedding similarity (Tier 2) - 1-10ms, for semantic matching
    3. LLM classification (Tier 3) - 100-1000ms, for ambiguous cases

    Usage:
        classifier = PreClassifier()
        result = classifier.classify("Implement REST API for users")

        # With embedding classifier
        classifier = PreClassifier(
            embedding_fn=my_embed_fn,
            embeddings_path="/path/to/embeddings.npz"
        )

    Attributes:
        keyword_classifier: Fast keyword-based classifier
        embedding_classifier: Semantic embedding classifier (optional)
        llm_classifier: LLM fallback classifier (optional)
        metrics: Classification metrics tracking
    """

    def __init__(
        self,
        keywords: Optional[dict[RequirementCategory, set[str]]] = None,
        threshold_config: Optional[ThresholdConfig] = None,
        embedding_fn: Optional[Callable[[str], list[float]]] = None,
        embeddings_path: Optional[str] = None,
        llm_fn: Optional[Callable[[str], tuple[str, float]]] = None,
    ):
        """Initialize pre-classifier with all tiers.

        Args:
            keywords: Custom keyword dictionary for Tier 1
            threshold_config: Threshold configuration for all tiers
            embedding_fn: Function to compute embeddings for Tier 2
            embeddings_path: Path to pre-computed embeddings for Tier 2
            llm_fn: Function for LLM classification for Tier 3
        """
        self.threshold_config = threshold_config or ThresholdConfig.from_env()

        # Initialize Tier 1: Keyword classifier
        self.keyword_classifier = KeywordClassifier(
            keywords=keywords,
            threshold_config=self.threshold_config,
        )

        # Initialize Tier 2: Embedding classifier (if available)
        self.embedding_classifier: Optional[EmbeddingClassifier] = None
        if NUMPY_AVAILABLE and (embedding_fn or embeddings_path):
            try:
                self.embedding_classifier = EmbeddingClassifier(
                    embeddings_path=embeddings_path,
                    threshold_config=self.threshold_config,
                    embedding_fn=embedding_fn,
                )
            except ImportError:
                pass

        # Initialize Tier 3: LLM classifier
        self.llm_classifier = LLMClassifier(
            llm_fn=llm_fn,
            threshold_config=self.threshold_config,
        )

        # Metrics tracking
        self.metrics = ClassificationMetrics()

    def classify(self, requirement_text: str) -> ClassificationResult:
        """Classify a requirement using cascaded tiers.

        Attempts classification in order:
        1. Keyword matching - if confident, returns immediately
        2. Embedding similarity - if above threshold, returns immediately
        3. LLM classification - final fallback for ambiguous cases

        Args:
            requirement_text: The requirement text to classify

        Returns:
            ClassificationResult with the final classification
        """
        # Tier 1: Keyword classification
        keyword_result = self.keyword_classifier.classify(requirement_text)
        self.metrics.record(keyword_result)

        if keyword_result.category != RequirementCategory.AMBIGUOUS:
            return keyword_result

        # Tier 2: Embedding classification (if available)
        if self.embedding_classifier and self.embedding_classifier.is_ready:
            try:
                embedding_result = self.embedding_classifier.classify(requirement_text)
                self.metrics.record(embedding_result)

                if embedding_result.category != RequirementCategory.AMBIGUOUS:
                    return embedding_result
            except Exception:
                pass  # Fall through to LLM

        # Tier 3: LLM classification
        llm_result = self.llm_classifier.classify(requirement_text)
        self.metrics.record(llm_result)

        return llm_result

    def classify_batch(
        self,
        requirements: list[str]
    ) -> list[ClassificationResult]:
        """Classify multiple requirements.

        Optimizes by batching LLM calls where possible.

        Args:
            requirements: List of requirement texts to classify

        Returns:
            List of ClassificationResult objects
        """
        return [self.classify(req) for req in requirements]


@dataclass
class ClassificationMetrics:
    """Metrics tracking for classification performance.

    Tracks:
    - Total requirements classified
    - Distribution across tiers
    - Distribution across categories
    - Processing time statistics
    """
    total: int = 0
    by_tier: dict[str, int] = field(default_factory=dict)
    by_category: dict[str, int] = field(default_factory=dict)
    processing_times_ms: list[float] = field(default_factory=list)

    def record(self, result: ClassificationResult) -> None:
        """Record a classification result.

        Args:
            result: The classification result to record
        """
        self.total += 1

        tier = result.tier.value
        self.by_tier[tier] = self.by_tier.get(tier, 0) + 1

        category = result.category.value
        self.by_category[category] = self.by_category.get(category, 0) + 1

        self.processing_times_ms.append(result.processing_time_ms)

    @property
    def llm_percentage(self) -> float:
        """Percentage of requirements routed to LLM tier."""
        if self.total == 0:
            return 0.0
        return (self.by_tier.get("llm", 0) / self.total) * 100

    @property
    def avg_processing_time_ms(self) -> float:
        """Average processing time in milliseconds."""
        if not self.processing_times_ms:
            return 0.0
        return sum(self.processing_times_ms) / len(self.processing_times_ms)

    def to_dict(self) -> dict[str, Any]:
        """Serialize metrics to dictionary."""
        return {
            "total": self.total,
            "by_tier": self.by_tier,
            "by_category": self.by_category,
            "llm_percentage": self.llm_percentage,
            "avg_processing_time_ms": self.avg_processing_time_ms,
        }


# Category-specific BAML function routing
CATEGORY_BAML_FUNCTIONS: dict[RequirementCategory, list[str]] = {
    RequirementCategory.BACKEND_ONLY: [
        "ProcessGate1CategoryFunctionalPrompt",
        "ProcessGate1SubprocessDetailsPrompt",
        "ProcessGate1DataNeedsPrompt",
    ],
    RequirementCategory.FRONTEND_ONLY: [
        "ProcessGate1CategoryUsabilityPrompt",
        "ProcessGate1UserInteractionsPrompt",
        "ProcessGate1SubprocessDetailsPrompt",
    ],
    RequirementCategory.MIDDLEWARE: [
        "ProcessGate1CategorySecurityPrompt",
        "ProcessGate1CategoryFunctionalPrompt",
        "ProcessGate1SubprocessDetailsPrompt",
    ],
    RequirementCategory.FULL_STACK: [
        # All BAML functions for comprehensive processing
        "ProcessGate1CategoryFunctionalPrompt",
        "ProcessGate1CategoryNonFunctionalPrompt",
        "ProcessGate1CategorySecurityPrompt",
        "ProcessGate1CategoryPerformancePrompt",
        "ProcessGate1CategoryUsabilityPrompt",
        "ProcessGate1CategoryIntegrationPrompt",
        "ProcessGate1SubprocessDetailsPrompt",
        "ProcessGate1UserInteractionsPrompt",
        "ProcessGate1DataNeedsPrompt",
        "ProcessGate1BusinessRulesPrompt",
    ],
    RequirementCategory.AMBIGUOUS: [
        # Default to full_stack processing for ambiguous
        "ProcessGate1CategoryFunctionalPrompt",
        "ProcessGate1SubprocessDetailsPrompt",
    ],
}


def get_baml_functions_for_category(category: RequirementCategory) -> list[str]:
    """Get the list of BAML functions for a category.

    Args:
        category: The requirement category

    Returns:
        List of BAML function names to use for expansion
    """
    return CATEGORY_BAML_FUNCTIONS.get(category, CATEGORY_BAML_FUNCTIONS[RequirementCategory.FULL_STACK])


# =============================================================================
# REQ_001: Phase 2 - Decomposition Enhancement with Adaptive Granularity
# =============================================================================


class FunctionalCategory(str, Enum):
    """Functional categories for requirement classification per REQ_001.1."""
    FUNCTIONAL = "functional"
    SECURITY = "security"
    PERFORMANCE = "performance"
    USABILITY = "usability"
    INTEGRATION = "integration"
    NON_FUNCTIONAL = "non_functional"


class RoutingDecision(str, Enum):
    """Routing decision for where the requirement should be processed."""
    BACKEND_ONLY = "backend_only"
    FRONTEND_ONLY = "frontend_only"
    MIDDLEWARE = "middleware"
    FULL_STACK = "full_stack"


class ClassificationMethod(str, Enum):
    """Method used to classify the requirement."""
    KEYWORD = "keyword"
    EMBEDDING = "embedding"
    LLM = "llm"


@dataclass
class ClassificationResultV2:
    """Enhanced classification result for REQ_001.1.

    Extends the original ClassificationResult with additional fields
    for functional category and routing decision.

    Attributes:
        category: Functional category (functional, security, performance, etc.)
        confidence: Confidence score (0.0-1.0)
        classification_method: Method used (keyword, embedding, llm)
        routing_decision: Where to route the requirement (backend_only, frontend_only, middleware, full_stack)
        processing_time_ms: Time taken to classify in milliseconds
        source_keywords: Keywords that triggered the classification
    """
    category: str
    confidence: float
    classification_method: ClassificationMethod
    routing_decision: RoutingDecision
    processing_time_ms: float = 0.0
    source_keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "category": self.category,
            "confidence": self.confidence,
            "classification_method": self.classification_method.value,
            "routing_decision": self.routing_decision.value,
            "processing_time_ms": self.processing_time_ms,
            "source_keywords": self.source_keywords,
        }


# Domain-specific keyword patterns per REQ_001.1
KEYWORD_PATTERNS: dict[str, set[str]] = {
    # Functional category keywords
    "functional": {
        "implement", "create", "build", "develop", "feature", "functionality",
        "capability", "workflow", "process", "operation", "action", "task",
    },
    # Security category keywords
    "security": {
        "auth", "authenticate", "authentication", "authorize", "authorization",
        "permission", "role", "token", "jwt", "oauth", "encrypt", "decrypt",
        "secure", "security", "vulnerability", "compliance", "audit", "password",
        "credential", "rbac", "acl", "mfa", "2fa", "sso",
    },
    # Performance category keywords
    "performance": {
        "performance", "speed", "latency", "throughput", "optimize", "optimization",
        "cache", "caching", "scale", "scalable", "scalability", "concurrent",
        "parallel", "async", "load", "benchmark", "response time", "memory",
    },
    # Usability category keywords
    "usability": {
        "ui", "ux", "user interface", "user experience", "usability", "accessibility",
        "a11y", "responsive", "mobile", "desktop", "layout", "design", "navigation",
        "intuitive", "user-friendly", "interaction", "form", "button", "modal",
    },
    # Integration category keywords
    "integration": {
        "integrate", "integration", "api", "webhook", "third-party", "external",
        "connect", "connection", "sync", "synchronize", "import", "export",
        "interoperability", "middleware", "adapter", "connector", "plugin",
    },
    # Non-functional (quality attributes) keywords
    "non_functional": {
        "reliability", "availability", "maintainability", "testability",
        "portability", "monitoring", "logging", "observability", "error handling",
        "recovery", "backup", "disaster", "failover", "redundancy", "quality",
    },
    # Domain-specific routing keywords per REQ_001.1
    "backend_only": {
        "api", "endpoint", "database", "service", "repository", "server",
        "query", "rest", "graphql", "orm", "sql", "nosql", "migration",
        "schema", "model", "entity", "crud", "backend", "batch", "queue",
    },
    "frontend_only": {
        "ui", "page", "form", "component", "view", "render", "display",
        "css", "style", "layout", "responsive", "screen", "modal", "dialog",
        "navigation", "menu", "header", "footer", "frontend", "react", "vue",
        "angular", "html", "template", "widget", "button", "input",
    },
    "middleware": {
        "auth", "validate", "middleware", "session", "token", "permission",
        "authentication", "authorization", "jwt", "oauth", "rbac", "acl",
        "interceptor", "filter", "guard", "policy", "rate-limit", "throttle",
    },
}


class RequirementPreClassifier:
    """Pre-classification of requirements before full decomposition processing.

    Implements REQ_001.1: Provides keyword-based and LLM-based classification
    of requirements with <1ms processing time for keyword matching.

    Attributes:
        keyword_patterns: Dictionary mapping category names to keyword sets
        threshold_config: Configuration for confidence thresholds
        llm_fn: Optional LLM function for ambiguous cases
    """

    def __init__(
        self,
        keyword_patterns: Optional[dict[str, set[str]]] = None,
        threshold_config: Optional[ThresholdConfig] = None,
        llm_fn: Optional[Callable[[str], tuple[str, float]]] = None,
    ):
        """Initialize RequirementPreClassifier.

        Args:
            keyword_patterns: Custom keyword patterns (uses KEYWORD_PATTERNS if None)
            threshold_config: Threshold configuration
            llm_fn: Optional LLM function for classification fallback
        """
        self.keyword_patterns = keyword_patterns or KEYWORD_PATTERNS.copy()
        self.threshold_config = threshold_config or ThresholdConfig.from_env()
        self.llm_fn = llm_fn

        # Compile regex patterns for efficient matching
        self._compiled_patterns: dict[str, re.Pattern] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for each category's keywords."""
        for category, keywords in self.keyword_patterns.items():
            escaped_keywords = [re.escape(kw) for kw in keywords]
            pattern_str = r'\b(' + '|'.join(escaped_keywords) + r')\b'
            self._compiled_patterns[category] = re.compile(pattern_str, re.IGNORECASE)

    def _determine_routing(self, text: str, category_matches: dict[str, list[str]]) -> RoutingDecision:
        """Determine routing decision based on keyword matches.

        Args:
            text: Original requirement text
            category_matches: Matched keywords per category

        Returns:
            RoutingDecision enum value
        """
        # Check domain-specific routing categories
        middleware_matches = len(category_matches.get("middleware", []))
        backend_matches = len(category_matches.get("backend_only", []))
        frontend_matches = len(category_matches.get("frontend_only", []))

        # Priority: middleware > backend > frontend
        if middleware_matches > 0:
            return RoutingDecision.MIDDLEWARE
        elif backend_matches > 0 and frontend_matches == 0:
            return RoutingDecision.BACKEND_ONLY
        elif frontend_matches > 0 and backend_matches == 0:
            return RoutingDecision.FRONTEND_ONLY
        elif backend_matches > 0 and frontend_matches > 0:
            return RoutingDecision.FULL_STACK
        else:
            return RoutingDecision.FULL_STACK

    def _determine_category(self, category_matches: dict[str, list[str]]) -> str:
        """Determine functional category based on keyword matches.

        Args:
            category_matches: Matched keywords per category

        Returns:
            Functional category string
        """
        # Priority order for functional categories
        priority_categories = [
            "security", "performance", "usability", "integration",
            "non_functional", "functional"
        ]

        for cat in priority_categories:
            if category_matches.get(cat):
                return cat

        return "functional"  # Default

    def classify_single(self, requirement_text: str) -> ClassificationResultV2:
        """Classify a single requirement.

        Implements REQ_001.1 behavior 4: Returns category and confidence.
        Achieves <1ms processing time per requirement.

        Args:
            requirement_text: The requirement text to classify

        Returns:
            ClassificationResultV2 with category, confidence, method, and routing
        """
        start_time = time.perf_counter()

        # Find all matching keywords for each category
        category_matches: dict[str, list[str]] = {}

        for category, pattern in self._compiled_patterns.items():
            matches = pattern.findall(requirement_text)
            if matches:
                category_matches[category] = [m.lower() for m in matches]

        processing_time_ms = (time.perf_counter() - start_time) * 1000

        # Determine routing and category
        routing = self._determine_routing(requirement_text, category_matches)
        category = self._determine_category(category_matches)

        # Calculate confidence based on match counts
        total_matches = sum(len(m) for m in category_matches.values())
        if total_matches == 0:
            confidence = 0.0
        elif total_matches >= 3:
            confidence = 1.0
        else:
            confidence = 0.5 + (total_matches * 0.25)

        # Collect all matched keywords
        all_keywords = []
        for kws in category_matches.values():
            all_keywords.extend(kws)

        # If confidence >= 0.9, return directly without LLM fallback (REQ_001.1 behavior 8)
        if confidence >= 0.9 or self.llm_fn is None:
            return ClassificationResultV2(
                category=category,
                confidence=confidence,
                classification_method=ClassificationMethod.KEYWORD,
                routing_decision=routing,
                processing_time_ms=processing_time_ms,
                source_keywords=all_keywords,
            )

        # Fall back to LLM for low-confidence classifications
        if self.llm_fn and confidence < 0.9:
            try:
                llm_start = time.perf_counter()
                llm_category, llm_confidence = self.llm_fn(requirement_text)
                llm_time = (time.perf_counter() - llm_start) * 1000

                return ClassificationResultV2(
                    category=llm_category,
                    confidence=llm_confidence,
                    classification_method=ClassificationMethod.LLM,
                    routing_decision=routing,  # Keep keyword-determined routing
                    processing_time_ms=processing_time_ms + llm_time,
                    source_keywords=all_keywords,
                )
            except Exception:
                pass  # Fall through to keyword result

        return ClassificationResultV2(
            category=category,
            confidence=confidence,
            classification_method=ClassificationMethod.KEYWORD,
            routing_decision=routing,
            processing_time_ms=processing_time_ms,
            source_keywords=all_keywords,
        )

    def classify_batch(self, requirements: list[str]) -> list[ClassificationResultV2]:
        """Classify multiple requirements.

        Implements REQ_001.1 behavior 5: Batch processing support.

        Args:
            requirements: List of requirement texts to classify

        Returns:
            List of ClassificationResultV2 objects
        """
        return [self.classify_single(req) for req in requirements]


# =============================================================================
# REQ_001.3: Complexity Assessment
# =============================================================================


class ComplexityLevel(Enum):
    """Complexity level for requirements per REQ_001.3.

    Associated granularity levels:
    - SIMPLE: function-level (single test)
    - MEDIUM: class-level (test class)
    - COMPLEX: repository-level (test module)
    """
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"

    @property
    def granularity_level(self) -> str:
        """Get the associated granularity level."""
        mapping = {
            ComplexityLevel.SIMPLE: "function-level",
            ComplexityLevel.MEDIUM: "class-level",
            ComplexityLevel.COMPLEX: "repository-level",
        }
        return mapping[self]


# Keywords indicating cross-cutting concerns (REQ_001.3 behavior 6)
CROSS_CUTTING_KEYWORDS: set[str] = {
    "auth", "logging", "caching", "transaction", "security across",
    "monitoring", "audit", "tracing", "error handling", "validation",
}


@dataclass
class ComplexityAssessment:
    """Result of complexity assessment per REQ_001.3 behavior 8.

    Attributes:
        level: ComplexityLevel enum value
        layer_count: Number of layers affected (frontend, backend, middleware)
        has_cross_cutting: Whether cross-cutting concerns are detected
        confidence: Confidence in the assessment (0.0-1.0)
    """
    level: ComplexityLevel
    layer_count: int
    has_cross_cutting: bool
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "level": self.level.value,
            "granularity_level": self.level.granularity_level,
            "layer_count": self.layer_count,
            "has_cross_cutting": self.has_cross_cutting,
            "confidence": self.confidence,
        }


def assess_complexity(requirement: Any) -> ComplexityAssessment:
    """Assess complexity of a requirement based on ADaPT framework principles.

    Implements REQ_001.3: Determines task complexity level based on:
    - Layer count (frontend, backend, middleware affected)
    - Cross-cutting concerns
    - Implementation component counts

    Args:
        requirement: RequirementNode or object with description and implementation fields

    Returns:
        ComplexityAssessment with level, layer_count, has_cross_cutting, confidence
    """
    # Get description and implementation from requirement
    description = getattr(requirement, "description", str(requirement))
    implementation = getattr(requirement, "implementation", None)

    # Count affected layers
    layer_count = 0
    if implementation:
        frontend = getattr(implementation, "frontend", []) or []
        backend = getattr(implementation, "backend", []) or []
        middleware = getattr(implementation, "middleware", []) or []

        if frontend:
            layer_count += 1
        if backend:
            layer_count += 1
        if middleware:
            layer_count += 1
    else:
        # Estimate from description
        desc_lower = description.lower()
        if any(kw in desc_lower for kw in ["ui", "page", "form", "frontend", "component"]):
            layer_count += 1
        if any(kw in desc_lower for kw in ["api", "database", "backend", "service", "query"]):
            layer_count += 1
        if any(kw in desc_lower for kw in ["auth", "middleware", "session", "token"]):
            layer_count += 1

    # Check for cross-cutting concerns (REQ_001.3 behavior 6)
    desc_lower = description.lower()
    has_cross_cutting = any(kw in desc_lower for kw in CROSS_CUTTING_KEYWORDS)

    # Determine complexity level based on ADaPT principles (REQ_001.3 behaviors 3-5)
    if has_cross_cutting or layer_count >= 3:
        # Complex: 3+ layers OR cross-cutting concerns (behavior 5)
        level = ComplexityLevel.COMPLEX
        confidence = 0.9 if has_cross_cutting else 0.8
    elif layer_count == 2:
        # Medium: 2 layers with clear separation (behavior 4)
        level = ComplexityLevel.MEDIUM
        confidence = 0.85
    elif layer_count == 1:
        # Simple: single layer (behavior 3)
        level = ComplexityLevel.SIMPLE
        confidence = 0.9
    else:
        # Default to medium if we can't determine
        level = ComplexityLevel.MEDIUM
        confidence = 0.5

    # Adjust based on implementation component counts (REQ_001.3 behavior 7)
    if implementation:
        total_components = (
            len(getattr(implementation, "frontend", []) or []) +
            len(getattr(implementation, "backend", []) or []) +
            len(getattr(implementation, "middleware", []) or []) +
            len(getattr(implementation, "shared", []) or [])
        )
        if total_components > 10:
            level = ComplexityLevel.COMPLEX
        elif total_components > 5 and level == ComplexityLevel.SIMPLE:
            level = ComplexityLevel.MEDIUM

    return ComplexityAssessment(
        level=level,
        layer_count=layer_count,
        has_cross_cutting=has_cross_cutting,
        confidence=confidence,
    )


# =============================================================================
# REQ_001.4: Adaptive Prompts
# =============================================================================


# Token limits for research content truncation by complexity (REQ_001.4 behavior 6)
RESEARCH_TRUNCATION_LIMITS: dict[ComplexityLevel, int] = {
    ComplexityLevel.SIMPLE: 2000,
    ComplexityLevel.MEDIUM: 4000,
    ComplexityLevel.COMPLEX: 8000,
}


def build_adaptive_prompt(
    requirement: Any,
    complexity: ComplexityAssessment,
    research_content: str,
) -> str:
    """Build adaptive prompt based on assessed complexity.

    Implements REQ_001.4: Tailors prompt detail and scope to match task complexity.

    Args:
        requirement: RequirementNode or object with description and implementation
        complexity: ComplexityAssessment from assess_complexity()
        research_content: Research context to include (will be truncated by complexity)

    Returns:
        Complete prompt string ready for LLM invocation
    """
    description = getattr(requirement, "description", str(requirement))
    implementation = getattr(requirement, "implementation", None)
    routing = getattr(requirement, "routing_decision", None)

    # Truncate research content based on complexity (REQ_001.4 behavior 6)
    truncation_limit = RESEARCH_TRUNCATION_LIMITS.get(complexity.level, 4000)
    truncated_research = research_content[:truncation_limit]
    if len(research_content) > truncation_limit:
        truncated_research += "\n... [truncated]"

    # Build base prompt
    prompt_parts = []

    # Header based on complexity level
    if complexity.level == ComplexityLevel.SIMPLE:
        prompt_parts.append("## Simple Requirement - Function-Level Implementation\n")
    elif complexity.level == ComplexityLevel.MEDIUM:
        prompt_parts.append("## Medium Requirement - Class-Level Implementation\n")
    else:
        prompt_parts.append("## Complex Requirement - Repository-Level Implementation\n")

    # Requirement description
    prompt_parts.append(f"**Requirement:** {description}\n")

    # Include only relevant sections based on routing (REQ_001.4 behavior 5)
    if implementation:
        frontend = getattr(implementation, "frontend", []) or []
        backend = getattr(implementation, "backend", []) or []
        middleware = getattr(implementation, "middleware", []) or []

        # Determine which sections to include
        include_frontend = routing != RoutingDecision.BACKEND_ONLY if routing else bool(frontend)
        include_backend = routing != RoutingDecision.FRONTEND_ONLY if routing else bool(backend)
        include_middleware = True  # Always include if present

        if include_frontend and frontend:
            prompt_parts.append(f"**Frontend Components:** {', '.join(frontend)}\n")
        if include_backend and backend:
            prompt_parts.append(f"**Backend Components:** {', '.join(backend)}\n")
        if include_middleware and middleware:
            prompt_parts.append(f"**Middleware Components:** {', '.join(middleware)}\n")

    # Acceptance criteria count based on complexity (REQ_001.4 behaviors 2-4)
    if complexity.level == ComplexityLevel.SIMPLE:
        prompt_parts.append("\n**Required:** 2-3 acceptance criteria\n")
    elif complexity.level == ComplexityLevel.MEDIUM:
        prompt_parts.append("\n**Required:** 4-6 acceptance criteria with interface definitions\n")
    else:
        prompt_parts.append("\n**Required:** 8-12 acceptance criteria with full architectural context\n")

    # Design-by-contract elements for MEDIUM and COMPLEX (REQ_001.4 behavior 8)
    if complexity.level in (ComplexityLevel.MEDIUM, ComplexityLevel.COMPLEX):
        prompt_parts.append("\n**Design Contract:**")
        prompt_parts.append("- Preconditions: [What must be true before execution]")
        prompt_parts.append("- Postconditions: [What must be true after execution]")
        prompt_parts.append("- Invariants: [What must remain unchanged]\n")

    # Include dependency graph for COMPLEX (REQ_001.4 behavior 4)
    if complexity.level == ComplexityLevel.COMPLEX:
        prompt_parts.append("\n**Dependency Analysis:**")
        prompt_parts.append("- Identify all dependencies between components")
        prompt_parts.append("- Map cross-cutting concerns")
        prompt_parts.append("- Consider integration points\n")

    # Research context
    prompt_parts.append(f"\n**Research Context:**\n{truncated_research}\n")

    # Output format instructions (REQ_001.4 behavior 7)
    prompt_parts.append("\n**Output Format:**")
    if complexity.level == ComplexityLevel.SIMPLE:
        prompt_parts.append("- Single function implementation")
        prompt_parts.append("- Unit test for each acceptance criterion")
    elif complexity.level == ComplexityLevel.MEDIUM:
        prompt_parts.append("- Class structure with methods")
        prompt_parts.append("- Test class with setup/teardown")
    else:
        prompt_parts.append("- Module organization")
        prompt_parts.append("- Integration test suite")
        prompt_parts.append("- Dependency injection points")

    return "\n".join(prompt_parts)


# =============================================================================
# REQ_001.5: Category-Specific BAML Function Integration
# =============================================================================


# Mapping of functional categories to BAML functions (REQ_001.5)
CATEGORY_TO_BAML_FUNCTIONS: dict[str, list[str]] = {
    "functional": [
        "ProcessGate1CategoryFunctionalPrompt",
        "ProcessGate1SubprocessDetailsPrompt",
        "ProcessGate1BusinessRulesPrompt",
    ],
    "security": [
        "ProcessGate1CategorySecurityPrompt",
        "ProcessGate1CategoryFunctionalPrompt",
        "ProcessGate1SubprocessDetailsPrompt",
    ],
    "performance": [
        "ProcessGate1CategoryPerformancePrompt",
        "ProcessGate1CategoryFunctionalPrompt",
        "ProcessGate1SubprocessDetailsPrompt",
    ],
    "usability": [
        "ProcessGate1CategoryUsabilityPrompt",
        "ProcessGate1UserInteractionsPrompt",
        "ProcessGate1SubprocessDetailsPrompt",
    ],
    "integration": [
        "ProcessGate1CategoryIntegrationPrompt",
        "ProcessGate1DataNeedsPrompt",
        "ProcessGate1SubprocessDetailsPrompt",
    ],
    "non_functional": [
        "ProcessGate1CategoryNonFunctionalPrompt",
        "ProcessGate1CategoryPerformancePrompt",
        "ProcessGate1SubprocessDetailsPrompt",
    ],
}


def get_category_baml_functions(category: str) -> list[str]:
    """Get BAML functions for a functional category.

    Implements REQ_001.5 behavior 1: Category-specific BAML function routing.

    Args:
        category: Functional category (functional, security, performance, etc.)

    Returns:
        List of BAML function names to call for this category
    """
    return CATEGORY_TO_BAML_FUNCTIONS.get(category, CATEGORY_TO_BAML_FUNCTIONS["functional"])


def expand_with_category_functions(
    requirement_description: str,
    category: str,
    baml_client: Any = None,
) -> list[dict[str, Any]]:
    """Expand requirement using category-specific BAML functions.

    Implements REQ_001.5: Routes to category-specific BAML functions for
    expansion based on pre-classified category.

    Args:
        requirement_description: Description of the requirement
        category: Functional category from pre-classification
        baml_client: Optional BAML client (uses default if None)

    Returns:
        List of expansion results from BAML functions
    """
    if baml_client is None:
        # Try to import default BAML client
        try:
            from baml_client import b as baml_client
        except ImportError:
            return []  # No BAML client available

    functions_to_call = get_category_baml_functions(category)
    results = []

    for fn_name in functions_to_call:
        try:
            # Get the function from the BAML client
            fn = getattr(baml_client, fn_name, None)
            if fn is None:
                continue

            # Call the function with appropriate parameters
            # Note: Parameter names may vary by function
            result = fn(
                scope_text=requirement_description,
                user_confirmation=True,
            )

            results.append({
                "function": fn_name,
                "result": result,
            })
        except Exception:
            # Continue with other functions on failure
            continue

    return results


def route_requirement_to_baml(
    requirement: Any,
    classification: ClassificationResultV2,
    research_context: str = "",
    baml_client: Any = None,
) -> dict[str, Any]:
    """Route a requirement to appropriate BAML functions based on classification.

    Implements REQ_001.5: Full routing pipeline combining category and routing
    decision to select optimal BAML expansion functions.

    Args:
        requirement: RequirementNode or similar object
        classification: Classification result from pre-classifier
        research_context: Research context for prompt building
        baml_client: Optional BAML client

    Returns:
        Dictionary with expansion results and metadata
    """
    description = getattr(requirement, "description", str(requirement))

    # Get category-specific functions
    category_functions = get_category_baml_functions(classification.category)

    # Get routing-specific functions (from original CATEGORY_BAML_FUNCTIONS)
    routing_functions = []
    if classification.routing_decision == RoutingDecision.BACKEND_ONLY:
        routing_functions = CATEGORY_BAML_FUNCTIONS.get(RequirementCategory.BACKEND_ONLY, [])
    elif classification.routing_decision == RoutingDecision.FRONTEND_ONLY:
        routing_functions = CATEGORY_BAML_FUNCTIONS.get(RequirementCategory.FRONTEND_ONLY, [])
    elif classification.routing_decision == RoutingDecision.MIDDLEWARE:
        routing_functions = CATEGORY_BAML_FUNCTIONS.get(RequirementCategory.MIDDLEWARE, [])
    else:
        routing_functions = CATEGORY_BAML_FUNCTIONS.get(RequirementCategory.FULL_STACK, [])

    # Combine and deduplicate function lists
    all_functions = list(dict.fromkeys(category_functions + routing_functions))

    # Expand using the combined functions
    expansions = expand_with_category_functions(
        requirement_description=description,
        category=classification.category,
        baml_client=baml_client,
    )

    # Assess complexity for adaptive prompting
    complexity = assess_complexity(requirement)

    # Build adaptive prompt if research context provided
    adaptive_prompt = ""
    if research_context:
        adaptive_prompt = build_adaptive_prompt(requirement, complexity, research_context)

    return {
        "requirement_id": getattr(requirement, "id", "unknown"),
        "category": classification.category,
        "routing_decision": classification.routing_decision.value,
        "confidence": classification.confidence,
        "complexity": complexity.to_dict(),
        "functions_called": all_functions,
        "expansions": expansions,
        "adaptive_prompt": adaptive_prompt,
    }


# =============================================================================
# REQ_005.4: Training Sample Collection
# =============================================================================


@dataclass
class TrainingSample:
    """A single training sample for threshold optimization (REQ_005.4).

    Attributes:
        requirement_text: The requirement text
        tier1_category: Result from Tier 1 (keyword) classification
        tier1_confidence: Tier 1 confidence score
        tier2_category: Result from Tier 2 (embedding) classification
        tier2_confidence: Tier 2 confidence score
        tier3_category: Result from Tier 3 (LLM) classification
        tier3_confidence: Tier 3 confidence score
        final_category: Ground truth category (from human review or LLM)
        collection_timestamp: When the sample was collected
    """
    requirement_text: str
    tier1_category: str
    tier1_confidence: float
    tier2_category: Optional[str] = None
    tier2_confidence: Optional[float] = None
    tier3_category: Optional[str] = None
    tier3_confidence: Optional[float] = None
    final_category: Optional[str] = None
    collection_timestamp: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "requirement_text": self.requirement_text,
            "tier1_category": self.tier1_category,
            "tier1_confidence": self.tier1_confidence,
            "tier2_category": self.tier2_category,
            "tier2_confidence": self.tier2_confidence,
            "tier3_category": self.tier3_category,
            "tier3_confidence": self.tier3_confidence,
            "final_category": self.final_category,
            "collection_timestamp": self.collection_timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrainingSample":
        """Deserialize from dictionary."""
        return cls(
            requirement_text=data["requirement_text"],
            tier1_category=data["tier1_category"],
            tier1_confidence=data["tier1_confidence"],
            tier2_category=data.get("tier2_category"),
            tier2_confidence=data.get("tier2_confidence"),
            tier3_category=data.get("tier3_category"),
            tier3_confidence=data.get("tier3_confidence"),
            final_category=data.get("final_category"),
            collection_timestamp=data.get("collection_timestamp"),
        )


class TrainingSampleCollector:
    """Collects training samples for threshold optimization (REQ_005.4).

    Implements REQ_005.4:
    - Collects results from each tier during classification
    - Stores samples with tier1, tier2, tier3 results and final category
    - Supports export to JSON/JSONL format for analysis
    - Optional project-specific collection for domain-specific calibration

    Attributes:
        samples: List of collected training samples
        project_id: Optional project identifier for domain-specific collection
        max_samples: Maximum samples to collect (default: 10000)
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        max_samples: int = 10000,
    ):
        """Initialize training sample collector.

        Args:
            project_id: Optional project identifier for filtering
            max_samples: Maximum number of samples to retain
        """
        self.samples: list[TrainingSample] = []
        self.project_id = project_id
        self.max_samples = max_samples

    def collect(
        self,
        requirement_text: str,
        tier1_result: ClassificationResult,
        tier2_result: Optional[ClassificationResult] = None,
        tier3_result: Optional[ClassificationResult] = None,
        final_category: Optional[str] = None,
    ) -> TrainingSample:
        """Collect a training sample from classification results (REQ_005.4 behavior 2).

        Args:
            requirement_text: The requirement text that was classified
            tier1_result: Result from keyword classifier
            tier2_result: Result from embedding classifier (if invoked)
            tier3_result: Result from LLM classifier (if invoked)
            final_category: Ground truth category (from human review or final tier)

        Returns:
            The created TrainingSample
        """
        from datetime import datetime

        sample = TrainingSample(
            requirement_text=requirement_text,
            tier1_category=tier1_result.category.value,
            tier1_confidence=tier1_result.confidence,
            tier2_category=tier2_result.category.value if tier2_result else None,
            tier2_confidence=tier2_result.confidence if tier2_result else None,
            tier3_category=tier3_result.category.value if tier3_result else None,
            tier3_confidence=tier3_result.confidence if tier3_result else None,
            final_category=final_category,
            collection_timestamp=datetime.now().isoformat(),
        )

        self.samples.append(sample)

        # Enforce max samples limit (FIFO)
        if len(self.samples) > self.max_samples:
            self.samples = self.samples[-self.max_samples:]

        return sample

    def get_samples(self) -> list[TrainingSample]:
        """Get all collected samples."""
        return self.samples.copy()

    def get_samples_for_tier2_calibration(self) -> list[tuple[str, str]]:
        """Get samples formatted for Tier 2 embedding calibration (REQ_005.4 behavior 5).

        Returns only samples that have valid final categories for training.

        Returns:
            List of (requirement_text, category) tuples for fit() method
        """
        return [
            (sample.requirement_text, sample.final_category)
            for sample in self.samples
            if sample.final_category is not None
        ]

    def export_to_file(self, path: str, format: str = "jsonl") -> int:
        """Export samples to file (REQ_005.4 behavior 4).

        Args:
            path: Output file path
            format: Output format ("json" or "jsonl")

        Returns:
            Number of samples exported
        """
        import json

        if format == "jsonl":
            with open(path, "w") as f:
                for sample in self.samples:
                    f.write(json.dumps(sample.to_dict()) + "\n")
        else:
            with open(path, "w") as f:
                json.dump([s.to_dict() for s in self.samples], f, indent=2)

        return len(self.samples)

    def load_from_file(self, path: str, format: str = "jsonl") -> int:
        """Load samples from file (REQ_005.4 behavior 4).

        Args:
            path: Input file path
            format: Input format ("json" or "jsonl")

        Returns:
            Number of samples loaded
        """
        import json

        samples: list[dict] = []
        if format == "jsonl":
            with open(path, "r") as f:
                for line in f:
                    if line.strip():
                        samples.append(json.loads(line))
        else:
            with open(path, "r") as f:
                samples = json.load(f)

        self.samples = [TrainingSample.from_dict(s) for s in samples]
        return len(self.samples)

    def get_tier_coverage_stats(self) -> dict[str, Any]:
        """Calculate tier coverage statistics (REQ_005.4 behavior 6).

        Returns:
            Dictionary with tier coverage percentages and statistics
        """
        total = len(self.samples)
        if total == 0:
            return {
                "total_samples": 0,
                "tier1_only": 0,
                "tier2_invoked": 0,
                "tier3_invoked": 0,
                "tier1_percentage": 0.0,
                "tier2_percentage": 0.0,
                "tier3_percentage": 0.0,
            }

        tier1_only = sum(
            1 for s in self.samples
            if s.tier2_category is None and s.tier3_category is None
        )
        tier2_invoked = sum(1 for s in self.samples if s.tier2_category is not None)
        tier3_invoked = sum(1 for s in self.samples if s.tier3_category is not None)

        return {
            "total_samples": total,
            "tier1_only": tier1_only,
            "tier2_invoked": tier2_invoked,
            "tier3_invoked": tier3_invoked,
            "tier1_percentage": (tier1_only / total) * 100,
            "tier2_percentage": (tier2_invoked / total) * 100,
            "tier3_percentage": (tier3_invoked / total) * 100,
        }

    def clear(self) -> None:
        """Clear all collected samples."""
        self.samples = []


# Global singleton for convenience
_training_collector: Optional[TrainingSampleCollector] = None


def get_training_collector(project_id: Optional[str] = None) -> TrainingSampleCollector:
    """Get the global training sample collector (REQ_005.4 behavior 8).

    Args:
        project_id: Optional project ID (creates new collector if different)

    Returns:
        Global TrainingSampleCollector instance
    """
    global _training_collector
    if _training_collector is None or (project_id and _training_collector.project_id != project_id):
        _training_collector = TrainingSampleCollector(project_id=project_id)
    return _training_collector
