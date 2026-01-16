"""Agent SDK-based requirement decomposition for research content.

This module provides functions to decompose research documents into
structured requirement hierarchies using the Claude agent SDK.

Main entry points:
- decompose_requirements(): Use Claude agent SDK to decompose research into requirements
- decompose_requirements_cli_fallback(): Legacy CLI subprocess fallback
"""

import json
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
from planning_pipeline.claude_runner import run_claude_sync

# BAML client for calling Ollama via ProcessGate1SubprocessDetailsPrompt
try:
    from baml_client import b as baml_client
    BAML_AVAILABLE = True
except ImportError:
    baml_client = None
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
        expansion_timeout: Timeout in seconds for expanding each requirement (default 300)
    """

    max_sub_processes: int = 5
    min_sub_processes: int = 2
    include_acceptance_criteria: bool = True
    expand_dimensions: bool = False
    expansion_timeout: int = 300  # 5 minutes per requirement expansion


# Default analysis framework for BAML calls
DEFAULT_ANALYSIS_FRAMEWORK = """
Extract requirements focusing on:
1. Functional requirements (what the system must do)
2. Non-functional requirements (quality attributes)
3. Implementation considerations
"""


# Type alias for progress callback
ProgressCallback = Callable[[str], None]

# Type alias for save callback (receives hierarchy after each requirement is added)
SaveCallback = Callable[["RequirementHierarchy"], None]


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
    save_callback: Optional[SaveCallback] = None,
) -> Union[RequirementHierarchy, DecompositionError]:
    """Decompose research content into requirement hierarchy using Claude agent SDK.

    Takes research output (typically from step_research()) and produces a
    structured RequirementHierarchy with:
    - Top-level requirements extracted from research
    - Sub-process children for each requirement

    Uses the Claude agent SDK (run_claude_sync) which provides proper
    authentication and rate limiting through the Claude CLI infrastructure.

    Args:
        research_content: Research document text to decompose
        config: Optional decomposition configuration
        progress: Optional callback for CLI progress updates
        save_callback: Optional callback invoked after each requirement is added to
            the hierarchy. Use this for incremental saving to prevent data loss
            if the process crashes mid-decomposition.

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

    # Initialize stats for CLI summary
    stats = DecompositionStats()

    try:
        # Step 1: Extract initial requirements using Claude agent SDK
        report("  Analyzing research with Claude agent SDK...")
        extraction_start = time.time()

        # Build prompt for requirement extraction
        extraction_prompt = f"""You are an expert software requirements analyst. Your task is to extract EVERY requirement from the scope text. DO NOT summarize. Extract individual requirements from EVERY section.

Research content:
{research_content}

**MANDATORY REQUIREMENTS:**
1. Count all numbered sections in the document (e.g., '## 0.', '## 1.', '## 2.', etc.)
2. Extract AT LEAST 2-5 requirements from EACH numbered section
3. For a document with 15 sections, you MUST extract 30-75+ requirements total
4. DO NOT combine multiple requirements into one - each requirement must be separate
5. Process sections in order: Section 0, then Section 1, then Section 2, etc. - do not skip any

**EXTRACTION METHOD:**

For EACH numbered section (## 0, ## 1, ## 2, etc.):

1. Read the entire section content
2. Find ALL requirement statements (look for: "must", "should", "shall", "will", "needs to", "requires", "supports", "implements", "provides")
3. Extract EACH requirement as a separate item - do not combine them
4. Include requirements from:
   - Section headers and objectives
   - Bullet points and lists
   - Tables and structured data
   - Subsections (2.1, 2.2, etc.)
   - Examples and use cases
   - Technical specifications

**REQUIREMENT TYPES TO EXTRACT:**
- Functional: What the system does (features, capabilities, workflows)
- Non-functional: How it performs (performance, scalability, reliability)
- Security: Authentication, authorization, encryption, compliance
- Integration: Third-party tools, APIs, data synchronization
- Usability: User experience, interface design, accessibility
- Technical: Infrastructure, deployment, monitoring, data storage

**EXAMPLES OF GOOD REQUIREMENTS:**
- "The system must support end-to-end encryption for private chats" (specific, actionable)
- "The system must scale to 10,000+ concurrent users" (quantitative, clear)
- "The system must integrate with Slack, Gmail, and Notion" (specific integrations)
- "The system must support ISO 27001-2022 compliance" (specific standard)

**EXAMPLES OF BAD REQUIREMENTS (DO NOT CREATE THESE):**
- "The system must be secure" (too vague - break into specific security requirements)
- "The system must have good performance" (too vague - extract specific performance metrics)
- "The system must integrate with tools" (too vague - list specific tools)

**MINIMUM REQUIREMENTS:**
- If the document has 15 sections, extract at least 30 requirements (2 per section minimum)
- More sections = more requirements (aim for 2-5 per section)
- Better to extract too many than too few

**RESPONSE FORMAT:**
Return JSON with:
1. "requirements" - Array of Requirement objects (MUST have 30+ for documents with 15 sections)
2. "metadata" - Response metadata object

**Each Requirement Object:**
- "description": Specific requirement statement (required, 25+ chars)
- "sub_processes": Array of subprocess names (can be empty [])
- "related_concepts": Array of related concepts/technologies (can be empty [])

**Metadata Object:**
- "baml_validated": true
- "schema_version": "2.0.0"
- "llm_model": string (model name)
- "processing_time_ms": optional integer
- "sections_processed": integer (count of sections you processed - should match document sections)
- "extraction_completeness": "high|medium|low" (should be "high" if you extracted 2+ requirements per section)

Output ONLY the JSON object with 'requirements' array and 'metadata' object at the top level.
NO prose, explanations, or code fences.

Return ONLY valid JSON with this exact structure (no markdown, no explanation):
{{
    "requirements": [
        {{
            "description": "Clear description of the requirement",
            "sub_processes": ["subprocess 1", "subprocess 2", "subprocess 3"]
        }}
    ]
}}

Extract 3-7 top-level requirements, each with 2-5 sub-processes.


"""

        # Call Claude via agent SDK (stream=False for JSON parsing)
        result = run_claude_sync(
            prompt=extraction_prompt,
            timeout=1300,
            stream=False,
        )

        if not result["success"]:
            return DecompositionError(
                error_code=DecompositionErrorCode.BAML_API_ERROR,
                error=f"Claude agent SDK call failed: {result.get('error', 'Unknown error')}",
            )

        # Parse JSON response
        output = result["output"]
        json_str = _extract_json(output)
        if not json_str:
            return DecompositionError(
                error_code=DecompositionErrorCode.INVALID_JSON,
                error="No valid JSON found in Claude response",
                details={"output_preview": output[:500]},
            )

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return DecompositionError(
                error_code=DecompositionErrorCode.INVALID_JSON,
                error=f"Invalid JSON in response: {e}",
                details={"json_str": json_str[:500]},
            )

        requirements_data = data.get("requirements", [])
        stats.extraction_time_ms = int((time.time() - extraction_start) * 1000)
        stats.requirements_found = len(requirements_data)

        report(f"  ✓ Extracted {stats.requirements_found} top-level requirements")

        # Step 2: Expand each requirement via LLM to get implementation details
        hierarchy = RequirementHierarchy(
            metadata={
                "source": "agent_sdk_decomposition",
                "research_length": len(research_content),
            }
        )

        report(f"  Expanding {stats.requirements_found} requirements via LLM...")
        expansion_start = time.time()

        # Process each top-level requirement with LLM call
        for req_idx, requirement in enumerate(requirements_data):
            parent_id = f"REQ_{req_idx:03d}"
            parent_description = requirement.get("description", "Unknown requirement")
            sub_processes = requirement.get("sub_processes", [])[: config.max_sub_processes]

            report(f"    [{req_idx + 1}/{stats.requirements_found}] Expanding: {parent_description}")

            # Create parent node
            parent_node = RequirementNode(
                id=parent_id,
                description=parent_description,
                type="parent",
            )

            # Call LLM for each requirement to get implementation details
            expansion_prompt = f"""You are an expert software analyst. Expand each requirement into specific implementation requirements.
The software developer needs to know what detailed requirements are needed to implement this requirement for this project. It helps to imagine you are the user of the system and you are trying to implement the requirement. Think about the user's problem and how to solve it.
For each implementation requirement:


RESEARCH CONTEXT:
{research_content}

PARENT REQUIREMENT:
{parent_description}

SUB-PROCESSES TO EXPAND:
{json.dumps(sub_processes, indent=2)}

1. Provide a clear, actionable description
2. List ALL REQUIRED STEPS to implement the requirement
3. For each step, provide specific acceptance criteria
4. Consider technical and functional aspects
5. If the requirement lists specific actions, questions or decisions, include them as acceptance criteria
6. If the requirement is a decision, include the decision and the criteria for making that decision
7. If the requirement is a question, include the question and the criteria for answering it
8. Add any related or dependent concepts
9. EACH AND EVERY STEP to implement the requirement must be included
10. For each requirement, specify exactly what components are needed:
    - frontend: UI components, pages, forms, validation, user interactions
    - backend: API endpoints, services, data processing, business logic
    - middleware: authentication, authorization, request/response processing
    - shared: data models, utilities, constants, interfaces
Assume sub-processes exist even if not stated. Propose granular steps. Imagine you are the user of the system and you are trying to implement the requirement. Think about the user's problem and how to solve it.

Return ONLY valid JSON in this exact format:
{{
  "implementation_details": [
    {{
      "function_id": "ServiceName.functionName or ComponentName.methodName",
      "description": "specific requirement description",
      "related_concepts": ["concept1", "concept2"],
      "acceptance_criteria": [
        "specific measurable criterion",
        "specific testable criterion"
      ],
      "implementation": {{
        "frontend": ["UI components needed", "user interaction requirements"],
        "backend": ["API endpoints needed", "business logic requirements"],
        "middleware": ["authentication requirements", "validation rules"],
        "shared": ["data models needed", "utility functions required"]
      }}
    }}
  ]
}}

Generate one implementation_detail for each sub-process. If no sub-processes provided, generate 2-3 implementation details based on the parent requirement.
"""

            expansion_result = run_claude_sync(
                prompt=expansion_prompt,
                timeout=config.expansion_timeout,
                stream=False,
            )

            if expansion_result["success"]:
                expansion_json = _extract_json(expansion_result["output"])
                if expansion_json:
                    try:
                        expansion_data = json.loads(expansion_json)
                        impl_details = expansion_data.get("implementation_details", [])

                        # Limit implementation details to max_sub_processes
                        impl_details = impl_details[: config.max_sub_processes]

                        # Create child nodes from implementation details
                        for impl_idx, detail in enumerate(impl_details):
                            child_id = f"{parent_id}.{impl_idx + 1}"

                            # Extract implementation components
                            impl_data = detail.get("implementation", {})
                            impl_components = ImplementationComponents(
                                frontend=impl_data.get("frontend", []),
                                backend=impl_data.get("backend", []),
                                middleware=impl_data.get("middleware", []),
                                shared=impl_data.get("shared", []),
                            )

                            child_node = RequirementNode(
                                id=child_id,
                                description=detail.get("description", f"Implementation {impl_idx + 1}"),
                                type="sub_process",
                                parent_id=parent_id,
                                function_id=detail.get("function_id", _generate_function_id(detail.get("description", ""), parent_id)),
                                related_concepts=detail.get("related_concepts", []),
                                acceptance_criteria=detail.get("acceptance_criteria", []),
                                implementation=impl_components,
                            )
                            parent_node.children.append(child_node)
                            stats.subprocesses_expanded += 1

                    except json.JSONDecodeError:
                        # Fallback to Ollama via BAML for JSON parsing failure
                        report(f"      ⚠ JSON parse failed, trying BAML/Ollama fallback...")
                        _process_with_ollama_fallback(
                            parent_id, parent_description, parent_node, sub_processes, research_content, stats
                        )
            else:
                # LLM call failed - fallback to local Ollama via BAML
                sdk_error = expansion_result.get("error", "Unknown error")
                report(f"      ⚠ Claude SDK failed: {sdk_error}")
                report(f"      Trying BAML/Ollama fallback...")
                _process_with_ollama_fallback(
                    parent_id, parent_description, parent_node, sub_processes, research_content, stats
                )

            hierarchy.add_requirement(parent_node)

            # Incremental save after each requirement is fully processed
            if save_callback is not None:
                save_callback(hierarchy)

        stats.expansion_time_ms = int((time.time() - expansion_start) * 1000)
        stats.total_nodes = stats.requirements_found + stats.subprocesses_expanded

        report(f"  ✓ Expanded {stats.subprocesses_expanded} implementation details via LLM")
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


def _process_with_ollama_fallback(
    parent_id: str,
    parent_description: str,
    parent_node: RequirementNode,
    sub_processes: list[str],
    research_content: str,
    stats: "DecompositionStats",
) -> None:
    """Process requirement expansion using BAML ProcessGate1SubprocessDetailsPrompt.

    Calls Ollama via BAML function to get implementation details for each subprocess.
    If BAML is unavailable or call fails, creates basic nodes from sub_processes.

    Args:
        parent_id: Parent requirement ID
        parent_description: Description of the parent requirement
        parent_node: Parent RequirementNode to add children to
        sub_processes: List of sub-process descriptions to expand
        research_content: Research context (scope_text for BAML function)
        stats: DecompositionStats to update
    """
    if not BAML_AVAILABLE or baml_client is None:
        # BAML not available - create basic nodes
        for sub_idx, sub_process in enumerate(sub_processes):
            child_id = f"{parent_id}.{sub_idx + 1}"
            child_node = RequirementNode(
                id=child_id,
                description=sub_process,
                type="sub_process",
                parent_id=parent_id,
                function_id=_generate_function_id(sub_process, parent_id),
            )
            parent_node.children.append(child_node)
            stats.subprocesses_expanded += 1
        return

    # Call BAML function for each subprocess
    for sub_idx, sub_process in enumerate(sub_processes):
        child_id = f"{parent_id}.{sub_idx + 1}"

        try:
            # Call ProcessGate1SubprocessDetailsPrompt via BAML
            response = baml_client.ProcessGate1SubprocessDetailsPrompt(
                sub_process=sub_process,
                parent_description=parent_description,
                scope_text=research_content[:8000],  # Limit context size
                user_confirmation=True,
            )

            # Process implementation details from response
            if response and response.implementation_details:
                for impl_idx, detail in enumerate(response.implementation_details):
                    # Use sub_idx for first detail, then append impl_idx for additional
                    if impl_idx == 0:
                        detail_child_id = child_id
                    else:
                        detail_child_id = f"{child_id}.{impl_idx}"

                    # Extract implementation components
                    impl_components = ImplementationComponents(
                        frontend=list(detail.implementation.frontend) if detail.implementation.frontend else [],
                        backend=list(detail.implementation.backend) if detail.implementation.backend else [],
                        middleware=list(detail.implementation.middleware) if detail.implementation.middleware else [],
                        shared=list(detail.implementation.shared) if detail.implementation.shared else [],
                    )

                    child_node = RequirementNode(
                        id=detail_child_id,
                        description=detail.description,
                        type="sub_process",
                        parent_id=parent_id,
                        function_id=detail.function_id or _generate_function_id(detail.description, parent_id),
                        related_concepts=list(detail.related_concepts) if detail.related_concepts else [],
                        acceptance_criteria=list(detail.acceptance_criteria) if detail.acceptance_criteria else [],
                        implementation=impl_components,
                    )
                    parent_node.children.append(child_node)
                    stats.subprocesses_expanded += 1
            else:
                # No implementation details returned - create basic node
                child_node = RequirementNode(
                    id=child_id,
                    description=sub_process,
                    type="sub_process",
                    parent_id=parent_id,
                    function_id=_generate_function_id(sub_process, parent_id),
                )
                parent_node.children.append(child_node)
                stats.subprocesses_expanded += 1

        except Exception:
            # BAML call failed - create basic node for this subprocess
            child_node = RequirementNode(
                id=child_id,
                description=sub_process,
                type="sub_process",
                parent_id=parent_id,
                function_id=_generate_function_id(sub_process, parent_id),
            )
            parent_node.children.append(child_node)
            stats.subprocesses_expanded += 1


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
{research_content}
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


# ============================================================================
# TDD Plan Generation from Requirement Hierarchy
# ============================================================================


def _serialize_hierarchy_for_prompt(hierarchy: RequirementHierarchy) -> str:
    """Serialize hierarchy to JSON string for Claude prompt insertion.

    Converts the RequirementHierarchy to a complete JSON representation
    that preserves all requirement data including acceptance criteria,
    implementation details, and nested children.

    Args:
        hierarchy: RequirementHierarchy to serialize

    Returns:
        JSON string representation of the hierarchy
    """
    return json.dumps(hierarchy.to_dict(), indent=2)


def _build_tdd_plan_prompt(
    instruction_content: str,
    hierarchy: RequirementHierarchy,
    plan_name: str,
    additional_context: str = "",
) -> str:
    """Build the full prompt for TDD plan generation.

    Combines the instruction template with hierarchy context and
    any additional context provided.

    Args:
        instruction_content: Content from create_tdd_plan.md
        hierarchy: RequirementHierarchy to include
        plan_name: Name for the plan
        additional_context: Optional additional context

    Returns:
        Complete prompt string for Claude
    """
    from datetime import datetime

    hierarchy_json = _serialize_hierarchy_for_prompt(hierarchy)
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Build the hierarchy section to insert
    hierarchy_section = f"""

## Requirement Hierarchy

The following JSON contains the complete requirement hierarchy with all acceptance criteria.
Each requirement's `acceptance_criteria` array contains the conditions that TDD tests must verify.

```json
{hierarchy_json}
```

For each requirement with acceptance criteria:
1. Create test cases for EACH acceptance criterion
2. Use the `implementation` object to determine test file locations
3. Use the `function_id` to name test functions appropriately

Plan Name: {plan_name}
Date: {current_date}

"""

    # Add additional context if provided
    if additional_context:
        hierarchy_section += f"\n## Additional Context\n\n{additional_context}\n"

    # Remove "Initial Response" section if present (for non-interactive use)
    cleaned_instructions = instruction_content
    if "## Initial Response" in instruction_content:
        # Find and remove the Initial Response section
        start = instruction_content.find("## Initial Response")
        end = instruction_content.find("##", start + 2)
        if end == -1:
            end = len(instruction_content)
        cleaned_instructions = instruction_content[:start] + instruction_content[end:]

    # Combine instruction with hierarchy context
    return cleaned_instructions + hierarchy_section


def _extract_plan_paths(output: str) -> list[str]:
    """Extract plan file paths from Claude output.

    Looks for paths matching the pattern for TDD plan files:
    - thoughts/searchable/shared/plans/*.md
    - thoughts/searchable/plans/*.md

    Args:
        output: Claude output text

    Returns:
        List of extracted file paths
    """
    import re

    paths: list[str] = []

    # Match various plan path patterns
    patterns = [
        r'thoughts/searchable/shared/plans/[^\s\"\'\)]+\.md',
        r'thoughts/searchable/plans/[^\s\"\'\)]+\.md',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, output)
        for match in matches:
            # Clean up the path
            clean_path = match.strip()
            if clean_path and clean_path not in paths:
                paths.append(clean_path)

    return paths


def create_tdd_plan_from_hierarchy(
    project_path: Any,
    hierarchy: RequirementHierarchy,
    plan_name: str = "feature",
    additional_context: str = "",
) -> dict[str, Any]:
    """Create TDD plan documents from a requirement hierarchy.

    Invokes the create_tdd_plan skill with the serialized requirement
    hierarchy to generate TDD plan documents.

    Args:
        project_path: Root path of the project
        hierarchy: RequirementHierarchy from decompose_requirements()
        plan_name: Name for the plan (used in filenames)
        additional_context: Optional additional context for Claude

    Returns:
        Dictionary with keys:
        - success: bool
        - plan_paths: list of created plan file paths
        - output: raw Claude output
        - error: error message (if success=False)

    Example:
        >>> hierarchy = decompose_requirements(research)
        >>> if isinstance(hierarchy, RequirementHierarchy):
        ...     result = create_tdd_plan_from_hierarchy(
        ...         project_path=Path("."),
        ...         hierarchy=hierarchy,
        ...         plan_name="auth-feature",
        ...     )
        ...     if result["success"]:
        ...         print(f"Created: {result['plan_paths']}")
    """
    from pathlib import Path

    # Ensure project_path is a Path object
    if not isinstance(project_path, Path):
        project_path = Path(project_path)

    # Behavior 3.1: Load TDD Plan Instructions
    instruction_file = project_path / ".claude" / "commands" / "create_tdd_plan.md"
    if not instruction_file.exists():
        return {
            "success": False,
            "plan_paths": [],
            "output": "",
            "error": f"Instruction file not found: {instruction_file}. "
                     "Expected .claude/commands/create_tdd_plan.md in project root.",
        }

    try:
        instruction_content = instruction_file.read_text()
    except Exception as e:
        return {
            "success": False,
            "plan_paths": [],
            "output": "",
            "error": f"Failed to read instruction file: {e}",
        }

    # Behavior 3.2: Process Instructions with Hierarchy Context
    prompt = _build_tdd_plan_prompt(
        instruction_content=instruction_content,
        hierarchy=hierarchy,
        plan_name=plan_name,
        additional_context=additional_context,
    )

    # Behavior 3.3: Invoke Claude with Processed Prompt
    result = run_claude_sync(
        prompt=prompt,
        timeout=1200,  # 20 minutes for complex plans
        stream=True,
        cwd=str(project_path),
    )

    if not result["success"]:
        return {
            "success": False,
            "plan_paths": [],
            "output": result.get("output", ""),
            "error": result.get("error", "Claude invocation failed"),
        }

    output = result["output"]

    # Behavior 3.4: Extract Plan File Paths from Output
    plan_paths = _extract_plan_paths(output)

    # Behavior 3.5: Return Structured Result
    return {
        "success": True,
        "plan_paths": plan_paths,
        "output": output,
    }
