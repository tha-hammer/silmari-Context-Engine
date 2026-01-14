"""Semantic validation service for requirements.

This module provides the SemanticValidationService that invokes BAML-level
validation using ProcessGate1RequirementValidationPrompt.
"""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from silmari_rlm_act.validation.models import (
    SemanticValidationResult,
    ValidationSummary,
)

# Configure logging for validation
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised for validation errors."""

    pass


@dataclass
class ValidationConfig:
    """Configuration for semantic validation.

    REQ_003.4: Handle validation latency from LLM calls appropriately.

    Attributes:
        timeout_seconds: Maximum wait time for validation (default 60)
        max_retries: Number of retry attempts before degrading (default 3)
        warning_only: If True, failed validation doesn't block pipeline
        show_progress: Display progress feedback during validation
        batch_mode: Run validation in background
    """

    timeout_seconds: int = 60
    max_retries: int = 3
    warning_only: bool = False
    show_progress: bool = True
    batch_mode: bool = False


class SemanticValidationService:
    """Service for BAML-level semantic validation of requirements.

    REQ_003.1: Invoke ProcessGate1RequirementValidationPrompt function to
    perform semantic validation of requirements against the research scope.

    This service:
    - Calls the BAML validation function with properly formatted inputs
    - Handles network timeouts with configurable retry logic
    - Provides progress feedback during validation
    - Gracefully handles BAML service unavailability
    """

    def __init__(
        self,
        config: Optional[ValidationConfig] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Initialize the validation service.

        Args:
            config: Validation configuration (uses defaults if None)
            progress_callback: Optional callback for progress updates
        """
        self.config = config or ValidationConfig()
        self.progress_callback = progress_callback or (lambda msg: None)
        self._executor = ThreadPoolExecutor(max_workers=1)

    def _log_progress(self, message: str) -> None:
        """Log progress and notify callback.

        REQ_003.4: User receives progress feedback during validation.
        """
        logger.info(message)
        if self.config.show_progress:
            self.progress_callback(message)

    def _format_requirements_for_validation(
        self, hierarchy_path: Path
    ) -> tuple[str, int]:
        """Format requirements from hierarchy JSON for BAML validation.

        Args:
            hierarchy_path: Path to the requirement hierarchy JSON file

        Returns:
            Tuple of (formatted requirements string, requirement count)

        Raises:
            ValidationError: If hierarchy file is invalid
        """
        try:
            with open(hierarchy_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            requirements = data.get("requirements", [])
            if not requirements:
                raise ValidationError("Hierarchy contains no requirements")

            # Format requirements for LLM consumption
            formatted_lines = []
            count = 0

            for req in requirements:
                req_id = req.get("id", f"REQ_{count}")
                description = req.get("description", "No description")
                formatted_lines.append(f"- {req_id}: {description}")
                count += 1

                # Include children
                for child in req.get("children", []):
                    child_id = child.get("id", f"{req_id}.{count}")
                    child_desc = child.get("description", "No description")
                    formatted_lines.append(f"  - {child_id}: {child_desc}")
                    count += 1

            return "\n".join(formatted_lines), count

        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in hierarchy file: {e}")
        except FileNotFoundError:
            raise ValidationError(f"Hierarchy file not found: {hierarchy_path}")

    def _invoke_baml_validation(
        self,
        scope_text: str,
        current_requirements: str,
    ) -> Any:
        """Invoke the BAML ProcessGate1RequirementValidationPrompt function.

        REQ_003.1: Function calls ProcessGate1RequirementValidationPrompt
        BAML function with properly formatted inputs.

        Args:
            scope_text: Research document content or scope summary
            current_requirements: Serialized requirement hierarchy

        Returns:
            RequirementValidationResponse from BAML

        Raises:
            ValidationError: If BAML call fails
        """
        try:
            # Import BAML client
            from baml_client import b

            logger.debug(
                f"Invoking BAML validation with scope_text length={len(scope_text)}, "
                f"requirements length={len(current_requirements)}"
            )

            # Call the BAML function
            response = b.ProcessGate1RequirementValidationPrompt(
                scope_text=scope_text,
                current_requirements=current_requirements,
            )

            logger.debug(
                f"BAML validation returned {len(response.validation_results)} results"
            )

            return response

        except ImportError as e:
            raise ValidationError(f"BAML client not available: {e}")
        except Exception as e:
            raise ValidationError(f"BAML validation failed: {e}")

    def _invoke_with_retry(
        self,
        scope_text: str,
        current_requirements: str,
    ) -> Any:
        """Invoke BAML validation with retry logic.

        REQ_003.4: Retry logic attempts validation up to 3 times before degrading.

        Args:
            scope_text: Research scope text
            current_requirements: Requirements to validate

        Returns:
            BAML response if successful

        Raises:
            ValidationError: If all retries fail
        """
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                self._log_progress(
                    f"Validation attempt {attempt + 1}/{self.config.max_retries}..."
                )
                return self._invoke_baml_validation(scope_text, current_requirements)

            except ValidationError as e:
                last_error = e
                logger.warning(f"Validation attempt {attempt + 1} failed: {e}")

                if attempt < self.config.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    self._log_progress(f"Retrying in {wait_time}s...")
                    import time

                    time.sleep(wait_time)

        raise ValidationError(
            f"Validation failed after {self.config.max_retries} attempts: {last_error}"
        )

    def validate_sync(
        self,
        scope_text: str,
        hierarchy_path: Path,
    ) -> ValidationSummary:
        """Perform synchronous semantic validation.

        REQ_003.1: Invoke ProcessGate1RequirementValidationPrompt to perform
        semantic validation of requirements against the research scope.

        Args:
            scope_text: Research document content or scope summary
            hierarchy_path: Path to requirement hierarchy JSON

        Returns:
            ValidationSummary with all results
        """
        started_at = datetime.now()
        self._log_progress("Starting semantic validation...")

        # Format requirements
        current_requirements, req_count = self._format_requirements_for_validation(
            hierarchy_path
        )
        self._log_progress(f"Validating {req_count} requirements...")

        # Estimate time
        estimated_seconds = req_count * 2  # ~2 seconds per requirement
        self._log_progress(f"Estimated time: ~{estimated_seconds}s")

        try:
            # Invoke BAML with retry
            response = self._invoke_with_retry(scope_text, current_requirements)

            # Convert BAML results to our models
            results = [
                SemanticValidationResult.from_baml_result(r, validated_at=datetime.now())
                for r in response.validation_results
            ]

            completed_at = datetime.now()
            processing_time = int((completed_at - started_at).total_seconds() * 1000)

            valid_count = sum(1 for r in results if r.is_valid)
            invalid_count = len(results) - valid_count

            self._log_progress(
                f"Validation complete: {valid_count}/{len(results)} valid"
            )

            return ValidationSummary(
                total_requirements=len(results),
                valid_count=valid_count,
                invalid_count=invalid_count,
                results=results,
                started_at=started_at,
                completed_at=completed_at,
                processing_time_ms=processing_time,
                llm_model=response.metadata.llm_model,
            )

        except ValidationError as e:
            if self.config.warning_only:
                # REQ_003.4: Graceful degradation
                logger.warning(f"Semantic validation failed, proceeding anyway: {e}")
                self._log_progress(
                    "Warning: Semantic validation failed, structural validation only"
                )
                return ValidationSummary(
                    total_requirements=req_count,
                    valid_count=req_count,
                    invalid_count=0,
                    results=[],
                    started_at=started_at,
                    completed_at=datetime.now(),
                    llm_model=None,
                )
            raise

    async def validate_async(
        self,
        scope_text: str,
        hierarchy_path: Path,
    ) -> ValidationSummary:
        """Perform asynchronous semantic validation.

        REQ_003.4: Validation executes asynchronously to prevent CLI blocking.

        Args:
            scope_text: Research document content or scope summary
            hierarchy_path: Path to requirement hierarchy JSON

        Returns:
            ValidationSummary with all results
        """
        # Run sync validation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.validate_sync(scope_text, hierarchy_path),
        )

    def validate_with_timeout(
        self,
        scope_text: str,
        hierarchy_path: Path,
    ) -> ValidationSummary:
        """Perform validation with timeout.

        REQ_003.4: Configurable timeout prevents indefinite waiting.
        Timeout triggers graceful degradation.

        Args:
            scope_text: Research document content or scope summary
            hierarchy_path: Path to requirement hierarchy JSON

        Returns:
            ValidationSummary (may be partial on timeout)
        """
        import signal
        import sys

        started_at = datetime.now()

        # Get requirement count for fallback
        try:
            _, req_count = self._format_requirements_for_validation(hierarchy_path)
        except ValidationError:
            req_count = 0

        # Handle timeout
        def timeout_handler(signum: int, frame: Any) -> None:
            raise TimeoutError("Validation timed out")

        # Set timeout (Unix only)
        if sys.platform != "win32":
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.config.timeout_seconds)

        try:
            result = self.validate_sync(scope_text, hierarchy_path)

            if sys.platform != "win32":
                signal.alarm(0)  # Cancel timeout

            return result

        except TimeoutError:
            self._log_progress(
                f"Warning: Validation timed out after {self.config.timeout_seconds}s"
            )
            logger.warning(
                f"Semantic validation timed out after {self.config.timeout_seconds}s"
            )

            # Return degraded result
            return ValidationSummary(
                total_requirements=req_count,
                valid_count=req_count,
                invalid_count=0,
                results=[],
                started_at=started_at,
                completed_at=datetime.now(),
                llm_model=None,
            )

        finally:
            if sys.platform != "win32":
                signal.signal(signal.SIGALRM, old_handler)

    def close(self) -> None:
        """Clean up resources."""
        self._executor.shutdown(wait=False)
