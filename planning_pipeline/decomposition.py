"""BAML-based requirement decomposition for research content.

This module provides functions to decompose research documents into
structured requirement hierarchies using BAML for LLM-powered analysis.
Includes CLI fallback for environments without BAML.

Main entry points:
- decompose_requirements(): Use BAML to decompose research into requirements
- decompose_requirements_cli_fallback(): Use Claude CLI when BAML unavailable
"""

import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Union

from planning_pipeline.models import (
    ImplementationComponents,
    RequirementHierarchy,
    RequirementNode,
)

# Try to import BAML client - may not be available in all environments
# Using Optional type and conditional import pattern
b: Any
try:
    from baml_client import b as _b

    b = _b
    BAML_AVAILABLE = True
except ImportError:
    b = None
    BAML_AVAILABLE = False


class DecompositionErrorCode(Enum):
    """Error codes for decomposition failures."""

    EMPTY_CONTENT = "empty_content"
    BAML_UNAVAILABLE = "baml_unavailable"
    BAML_API_ERROR = "baml_api_error"
    INVALID_JSON = "invalid_json"
    CONVERSION_ERROR = "conversion_error"
    CLI_FALLBACK_ERROR = "cli_fallback_error"


@dataclass
class DecompositionError:
    """Structured error response from decomposition.

    Attributes:
        success: Always False for errors
        error_code: Categorized error type
        error: Human-readable error message
        details: Optional additional context
    """

    success: bool = False
    error_code: DecompositionErrorCode = DecompositionErrorCode.BAML_API_ERROR
    error: str = ""
    details: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize error to dictionary."""
        return {
            "success": self.success,
            "error_code": self.error_code.value,
            "error": self.error,
            "details": self.details,
        }


@dataclass
class DecompositionConfig:
    """Configuration for decomposition behavior.

    Attributes:
        max_sub_processes: Maximum children per requirement (default 5)
        min_sub_processes: Minimum children to extract (default 2)
        include_acceptance_criteria: Include AC in children (default True)
        expand_dimensions: Expand implementation dimensions (default False)
    """

    max_sub_processes: int = 5
    min_sub_processes: int = 2
    include_acceptance_criteria: bool = True
    expand_dimensions: bool = False


# Default analysis framework for BAML calls
DEFAULT_ANALYSIS_FRAMEWORK = """
Extract requirements focusing on:
1. Functional requirements (what the system must do)
2. Non-functional requirements (quality attributes)
3. Implementation considerations
"""


# Type alias for progress callback
ProgressCallback = Callable[[str], None]


def _default_progress(message: str) -> None:
    """Default progress callback - prints to stdout."""
    print(message)
    sys.stdout.flush()


@dataclass
class DecompositionStats:
    """Statistics from decomposition for CLI summary.

    Contains only relevant summary data, not full BAML transcripts.
    """

    requirements_found: int = 0
    subprocesses_expanded: int = 0
    total_nodes: int = 0
    extraction_time_ms: int = 0
    expansion_time_ms: int = 0

    def summary(self) -> str:
        """Return human-readable summary."""
        total_time = (self.extraction_time_ms + self.expansion_time_ms) / 1000
        return (
            f"  {self.requirements_found} requirements, "
            f"{self.subprocesses_expanded} subprocesses "
            f"({total_time:.1f}s)"
        )


def decompose_requirements(
    research_content: str,
    config: Optional[DecompositionConfig] = None,
    progress: Optional[ProgressCallback] = None,
) -> Union[RequirementHierarchy, DecompositionError]:
    """Decompose research content into requirement hierarchy using BAML.

    Takes research output (typically from step_research()) and produces a
    structured RequirementHierarchy with:
    - Top-level requirements extracted via ProcessGate1InitialExtractionPrompt
    - Sub-process children via ProcessGate1SubprocessDetailsPrompt

    Uses HaikuWithOllamaFallback BAML client: tries Claude Haiku first,
    automatically falls back to local Ollama if API fails.

    Args:
        research_content: Research document text to decompose
        config: Optional decomposition configuration
        progress: Optional callback for CLI progress updates

    Returns:
        RequirementHierarchy on success, DecompositionError on failure

    Example:
        >>> result = decompose_requirements("# Research\\nImplement auth system")
        >>> if isinstance(result, RequirementHierarchy):
        ...     print(f"Found {len(result.requirements)} requirements")
    """
    if config is None:
        config = DecompositionConfig()

    # Use default progress callback if none provided
    report = progress or _default_progress

    # Validate input
    if not research_content or not research_content.strip():
        return DecompositionError(
            error_code=DecompositionErrorCode.EMPTY_CONTENT,
            error="Research content cannot be empty",
            details={"input_length": len(research_content) if research_content else 0},
        )

    # Check BAML availability
    if not BAML_AVAILABLE or b is None:
        return DecompositionError(
            error_code=DecompositionErrorCode.BAML_UNAVAILABLE,
            error="BAML client not available. Install baml-py or use CLI fallback.",
        )

    # Initialize stats for CLI summary
    stats = DecompositionStats()

    try:
        # Step 1: Extract initial requirements
        # Uses HaikuWithOllamaFallback client - tries Haiku first, falls back to Ollama
        report("  Analyzing research with AI (Haiku with Ollama fallback)...")
        extraction_start = time.time()

        initial_response = b.ProcessGate1InitialExtractionPrompt(
            scope_text=research_content,
            analysis_framework=DEFAULT_ANALYSIS_FRAMEWORK,
            user_confirmation=True,
        )

        stats.extraction_time_ms = int((time.time() - extraction_start) * 1000)
        stats.requirements_found = len(initial_response.requirements)

        report(f"  ✓ Extracted {stats.requirements_found} top-level requirements")

        # Step 2: Build hierarchy from response
        hierarchy = RequirementHierarchy(
            metadata={
                "source": "baml_decomposition",
                "research_length": len(research_content),
            }
        )

        # Count total subprocesses for progress tracking
        total_subprocs = sum(
            min(len(req.sub_processes), config.max_sub_processes)
            for req in initial_response.requirements
        )
        processed_subprocs = 0

        report(f"  Expanding {total_subprocs} subprocesses (local Ollama)...")
        expansion_start = time.time()

        # Process each top-level requirement
        for req_idx, requirement in enumerate(initial_response.requirements):
            # Create parent node
            parent_id = f"REQ_{req_idx:03d}"
            parent_node = RequirementNode(
                id=parent_id,
                description=requirement.description,
                type="parent",
            )

            # Limit sub_processes per config
            sub_processes = requirement.sub_processes[: config.max_sub_processes]

            # Step 3: Get details for each sub-process
            for sub_idx, sub_process in enumerate(sub_processes):
                child_id = f"{parent_id}.{sub_idx + 1}"
                processed_subprocs += 1

                try:
                    # Call BAML for subprocess details
                    details_response = b.ProcessGate1SubprocessDetailsPrompt(
                        sub_process=sub_process,
                        parent_description=requirement.description,
                        scope_text=research_content[:500],  # Truncate for context
                        user_confirmation=True,
                    )

                    # Convert implementation details to child node
                    child_node = _create_child_from_details(
                        child_id=child_id,
                        sub_process=sub_process,
                        details_response=details_response,
                        parent_id=parent_id,
                        config=config,
                    )
                    stats.subprocesses_expanded += 1
                except Exception:
                    # If details call fails, create basic child node
                    child_node = RequirementNode(
                        id=child_id,
                        description=sub_process,
                        type="sub_process",
                        parent_id=parent_id,
                    )

                parent_node.children.append(child_node)

            hierarchy.add_requirement(parent_node)

        stats.expansion_time_ms = int((time.time() - expansion_start) * 1000)
        stats.total_nodes = stats.requirements_found + processed_subprocs

        report(f"  ✓ Expanded {stats.subprocesses_expanded}/{total_subprocs} subprocesses")
        report(stats.summary())

        # Store stats in hierarchy metadata for downstream access
        hierarchy.metadata["decomposition_stats"] = {
            "requirements_found": stats.requirements_found,
            "subprocesses_expanded": stats.subprocesses_expanded,
            "total_nodes": stats.total_nodes,
            "extraction_time_ms": stats.extraction_time_ms,
            "expansion_time_ms": stats.expansion_time_ms,
        }

        return hierarchy

    except Exception as e:
        return DecompositionError(
            error_code=DecompositionErrorCode.BAML_API_ERROR,
            error=str(e),
            details={"exception_type": type(e).__name__},
        )


# Action verb mappings for semantic function_id generation
_ACTION_MAP: dict[str, str] = {
    "authenticate": "authenticate",
    "login": "login",
    "logout": "logout",
    "register": "register",
    "create": "create",
    "update": "update",
    "delete": "delete",
    "get": "get",
    "fetch": "fetch",
    "retrieve": "retrieve",
    "validate": "validate",
    "verify": "verify",
    "render": "render",
    "display": "display",
    "show": "show",
    "process": "process",
    "transform": "transform",
    "calculate": "calculate",
    "send": "send",
    "receive": "receive",
    "store": "store",
    "save": "save",
    "load": "load",
}

# Subject/noun mappings for semantic function_id generation
# Note: Order matters - more specific/domain terms should come first
# as we iterate and take the first match
_SUBJECT_PRIORITY: list[tuple[str, str]] = [
    # Auth-related (check before "user" since auth often involves users)
    ("authentication", "Auth"),
    ("authenticate", "Auth"),  # verb but indicates auth context
    ("auth", "Auth"),
    # Validation-related (check before "data" since validation often involves data)
    ("validation", "Validator"),
    ("validator", "Validator"),
    ("validate", "Validator"),  # verb but indicates validation context
    # Dashboard/UI
    ("dashboard", "Dashboard"),
    # Data-related
    ("data", "Data"),
    # User-related (after auth/validation since those are more specific)
    ("user", "User"),
    # Other services
    ("report", "Report"),
    ("service", "Service"),
    ("api", "API"),
    ("endpoint", "Endpoint"),
]


def _generate_function_id(description: str, parent_id: Optional[str] = None) -> str:
    """Generate a semantic function_id from requirement description.

    Maps common verbs and nouns to produce Service.action style identifiers.

    Args:
        description: Human-readable description of the requirement
        parent_id: Optional parent ID for context (affects default subject)

    Returns:
        Generated function_id in Service.action format

    Examples:
        >>> _generate_function_id("Authenticate user credentials")
        'Auth.authenticate'
        >>> _generate_function_id("Render dashboard UI")
        'Dashboard.render'
        >>> _generate_function_id("Validate input data")
        'Validator.validate'
    """
    desc_lower = description.lower()

    # Find action verb
    action: Optional[str] = None
    for verb, mapped in _ACTION_MAP.items():
        if verb in desc_lower:
            action = mapped
            break
    if not action:
        words = description.split()
        action = words[0].lower() if words else "perform"

    # Find subject noun (priority-ordered search)
    subject: Optional[str] = None
    for noun, mapped in _SUBJECT_PRIORITY:
        if noun in desc_lower:
            subject = mapped
            break
    if not subject:
        subject = "Implementation" if parent_id and "." in parent_id else "Service"

    return f"{subject}.{action}"


def _create_implementation_node(
    impl_id: str,
    detail: Any,
    parent_id: str,
    config: DecompositionConfig,
) -> RequirementNode:
    """Create an implementation-level RequirementNode from BAML detail.

    Args:
        impl_id: ID for the new implementation node (format: REQ_XXX.Y.Z)
        detail: BAML ImplementationDetail object
        parent_id: ID of parent sub_process node
        config: Decomposition configuration

    Returns:
        RequirementNode with type="implementation"
    """
    # Extract or generate function_id
    function_id: Optional[str] = None
    if hasattr(detail, "function_id") and detail.function_id:
        function_id = detail.function_id
    else:
        desc = detail.description if hasattr(detail, "description") else ""
        function_id = _generate_function_id(desc, parent_id)

    # Extract related_concepts
    related_concepts: list[str] = []
    if hasattr(detail, "related_concepts") and detail.related_concepts:
        related_concepts = list(detail.related_concepts)

    # Extract implementation components
    impl = None
    if hasattr(detail, "implementation") and detail.implementation:
        impl = ImplementationComponents(
            frontend=list(detail.implementation.frontend or []),
            backend=list(detail.implementation.backend or []),
            middleware=list(detail.implementation.middleware or []),
            shared=list(detail.implementation.shared or []),
        )

    # Extract acceptance criteria
    acceptance_criteria: list[str] = []
    if config.include_acceptance_criteria and hasattr(detail, "acceptance_criteria"):
        acceptance_criteria = list(detail.acceptance_criteria or [])

    return RequirementNode(
        id=impl_id,
        description=detail.description if hasattr(detail, "description") else "Implementation",
        type="implementation",
        parent_id=parent_id,
        acceptance_criteria=acceptance_criteria,
        implementation=impl,
        function_id=function_id,
        related_concepts=related_concepts,
    )


def _create_child_from_details(
    child_id: str,
    sub_process: str,
    details_response: Any,
    parent_id: str,
    config: DecompositionConfig,
) -> RequirementNode:
    """Create a sub_process RequirementNode with implementation children.

    Creates a 3-tier hierarchy structure:
    - sub_process node (this function's return value)
      - implementation children (one per implementation_detail from BAML)

    Args:
        child_id: ID for the sub_process node (format: REQ_XXX.Y)
        sub_process: Original sub-process description
        details_response: BAML SubprocessDetailsResponse
        parent_id: ID of parent node
        config: Decomposition configuration

    Returns:
        RequirementNode with type="sub_process" and implementation children
    """
    # Create sub_process node (no implementation data - that goes on children)
    sub_node = RequirementNode(
        id=child_id,
        description=sub_process,
        type="sub_process",
        parent_id=parent_id,
    )

    # Default to basic node if no implementation details
    if not details_response.implementation_details:
        return sub_node

    # Create implementation children from each detail
    for impl_idx, detail in enumerate(details_response.implementation_details):
        impl_id = f"{child_id}.{impl_idx + 1}"
        impl_node = _create_implementation_node(
            impl_id=impl_id,
            detail=detail,
            parent_id=child_id,
            config=config,
        )
        sub_node.children.append(impl_node)

    return sub_node


def decompose_requirements_cli_fallback(
    research_content: str,
    config: Optional[DecompositionConfig] = None,
) -> Union[RequirementHierarchy, DecompositionError]:
    """Decompose research using Claude CLI when BAML unavailable.

    Fallback implementation that uses subprocess to call Claude CLI
    for requirement extraction. Returns structured JSON that is then
    converted to RequirementHierarchy.

    Args:
        research_content: Research document text to decompose
        config: Optional decomposition configuration

    Returns:
        RequirementHierarchy on success, DecompositionError on failure

    Note:
        This is a fallback for environments without BAML. The BAML
        version (decompose_requirements) is preferred when available.
    """
    import json
    import subprocess

    if config is None:
        config = DecompositionConfig()

    # Validate input
    if not research_content or not research_content.strip():
        return DecompositionError(
            error_code=DecompositionErrorCode.EMPTY_CONTENT,
            error="Research content cannot be empty",
        )

    # Build prompt for Claude CLI
    prompt = f"""Analyze this research content and extract requirements.

Return ONLY valid JSON with this structure:
{{
    "requirements": [
        {{
            "description": "Requirement description",
            "sub_processes": ["subprocess 1", "subprocess 2"]
        }}
    ]
}}

Research content:
{research_content[:2000]}
"""

    try:
        result = subprocess.run(
            ["claude", "--print", prompt],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            return DecompositionError(
                error_code=DecompositionErrorCode.CLI_FALLBACK_ERROR,
                error=f"Claude CLI failed: {result.stderr}",
            )

        # Extract JSON from output
        output = result.stdout
        json_str = _extract_json(output)
        if not json_str:
            return DecompositionError(
                error_code=DecompositionErrorCode.INVALID_JSON,
                error="No valid JSON found in CLI output",
                details={"output_preview": output[:200]},
            )

        data = json.loads(json_str)
        return _convert_json_to_hierarchy(data, config)

    except json.JSONDecodeError as e:
        return DecompositionError(
            error_code=DecompositionErrorCode.INVALID_JSON,
            error=f"Invalid JSON: {e}",
        )
    except subprocess.TimeoutExpired:
        return DecompositionError(
            error_code=DecompositionErrorCode.CLI_FALLBACK_ERROR,
            error="Claude CLI timed out",
        )
    except FileNotFoundError:
        return DecompositionError(
            error_code=DecompositionErrorCode.CLI_FALLBACK_ERROR,
            error="Claude CLI not found. Install with: pip install claude-cli",
        )
    except Exception as e:
        return DecompositionError(
            error_code=DecompositionErrorCode.CLI_FALLBACK_ERROR,
            error=str(e),
            details={"exception_type": type(e).__name__},
        )


def _extract_json(text: str) -> Optional[str]:
    """Extract JSON object from text (find first { to last }).

    Args:
        text: Text that may contain JSON

    Returns:
        Extracted JSON string or None if not found
    """
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return None


def _convert_json_to_hierarchy(
    data: dict[str, Any],
    config: DecompositionConfig,
) -> RequirementHierarchy:
    """Convert raw JSON response to RequirementHierarchy.

    Args:
        data: Parsed JSON with requirements array
        config: Decomposition configuration

    Returns:
        RequirementHierarchy with converted nodes
    """
    hierarchy = RequirementHierarchy(
        metadata={
            "source": "cli_fallback",
        }
    )

    requirements = data.get("requirements", [])
    for req_idx, req in enumerate(requirements):
        parent_id = f"REQ_{req_idx:03d}"
        parent_node = RequirementNode(
            id=parent_id,
            description=req.get("description", "Unknown"),
            type="parent",
        )

        sub_processes = req.get("sub_processes", [])[: config.max_sub_processes]
        for sub_idx, sub_proc in enumerate(sub_processes):
            child_id = f"{parent_id}.{sub_idx + 1}"
            child_node = RequirementNode(
                id=child_id,
                description=sub_proc,
                type="sub_process",
                parent_id=parent_id,
            )
            parent_node.children.append(child_node)

        hierarchy.add_requirement(parent_node)

    return hierarchy
