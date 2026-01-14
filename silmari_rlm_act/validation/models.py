"""Data models for semantic validation.

This module provides Python models for validation results that complement
the BAML-generated types in baml_client.types.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class SemanticValidationResult:
    """Result of validating a single requirement.

    REQ_003.2: Construct and return a ValidationResult object containing
    requirement_id, is_valid boolean, validation_issues list, suggestions list,
    and confidence_score for each validated requirement.

    Attributes:
        requirement_id: Unique identifier matching the source requirement
        is_valid: Boolean indicating pass/fail status
        validation_issues: List of specific problem descriptions
        suggestions: List of actionable improvement recommendations
        confidence_score: Optional float between 0.0 and 1.0 (None if LLM cannot determine)
        component_name: Optional component name if applicable
        validated_at: Timestamp of when validation was performed
    """

    requirement_id: str
    is_valid: bool
    validation_issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    confidence_score: Optional[float] = None
    component_name: Optional[str] = None
    validated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validate the result fields.

        REQ_003.2: Empty validation_issues list implies is_valid=True
        unless explicitly set otherwise.
        """
        # Validate confidence score range
        if self.confidence_score is not None:
            if not 0.0 <= self.confidence_score <= 1.0:
                raise ValueError(
                    f"confidence_score must be between 0.0 and 1.0, got {self.confidence_score}"
                )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dictionary.

        REQ_003.2: All ValidationResult objects are serializable to JSON
        for persistence.

        Returns:
            Dictionary representation of the validation result.
        """
        return {
            "requirement_id": self.requirement_id,
            "is_valid": self.is_valid,
            "validation_issues": self.validation_issues,
            "suggestions": self.suggestions,
            "confidence_score": self.confidence_score,
            "component_name": self.component_name,
            "validated_at": self.validated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SemanticValidationResult":
        """Deserialize from dictionary.

        Args:
            data: Dictionary with validation result fields

        Returns:
            Reconstructed SemanticValidationResult
        """
        validated_at = datetime.now()
        if data.get("validated_at"):
            validated_at = datetime.fromisoformat(data["validated_at"])

        return cls(
            requirement_id=data["requirement_id"],
            is_valid=data["is_valid"],
            validation_issues=data.get("validation_issues", []),
            suggestions=data.get("suggestions", []),
            confidence_score=data.get("confidence_score"),
            component_name=data.get("component_name"),
            validated_at=validated_at,
        )

    @classmethod
    def from_baml_result(
        cls, baml_result: Any, validated_at: Optional[datetime] = None
    ) -> "SemanticValidationResult":
        """Create from BAML ValidationResult.

        Args:
            baml_result: BAML-generated ValidationResult object
            validated_at: Optional timestamp override

        Returns:
            SemanticValidationResult with data from BAML response
        """
        return cls(
            requirement_id=baml_result.requirement_id,
            is_valid=baml_result.is_valid,
            validation_issues=baml_result.validation_issues,
            suggestions=baml_result.suggestions,
            confidence_score=baml_result.confidence_score,
            component_name=baml_result.component_name,
            validated_at=validated_at or datetime.now(),
        )

    def __eq__(self, other: object) -> bool:
        """Compare ValidationResult objects for testing.

        REQ_003.2: ValidationResult supports comparison for testing
        and assertions.
        """
        if not isinstance(other, SemanticValidationResult):
            return NotImplemented
        return (
            self.requirement_id == other.requirement_id
            and self.is_valid == other.is_valid
            and self.validation_issues == other.validation_issues
            and self.suggestions == other.suggestions
            and self.confidence_score == other.confidence_score
        )


@dataclass
class ValidationSummary:
    """Summary of validation results for a hierarchy.

    Provides aggregate statistics about validation outcomes.
    """

    total_requirements: int
    valid_count: int
    invalid_count: int
    results: list[SemanticValidationResult] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_ms: Optional[int] = None
    llm_model: Optional[str] = None

    @property
    def all_valid(self) -> bool:
        """Check if all requirements are valid."""
        return self.invalid_count == 0

    @property
    def validity_rate(self) -> float:
        """Calculate the proportion of valid requirements."""
        if self.total_requirements == 0:
            return 1.0
        return self.valid_count / self.total_requirements

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        return {
            "total_requirements": self.total_requirements,
            "valid_count": self.valid_count,
            "invalid_count": self.invalid_count,
            "results": [r.to_dict() for r in self.results],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "processing_time_ms": self.processing_time_ms,
            "llm_model": self.llm_model,
            "all_valid": self.all_valid,
            "validity_rate": self.validity_rate,
        }
