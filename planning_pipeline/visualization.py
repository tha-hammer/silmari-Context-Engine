"""Mermaid diagram generation from requirement hierarchies.

This module provides functions to generate Mermaid flowchart and class diagram
syntax from requirement hierarchies for visual representation:
- Flowcharts showing requirement relationships and component links
- Class diagrams extracted from backend implementation components

Output is valid Mermaid syntax that can be rendered in:
- Mermaid Live Editor (https://mermaid.live)
- VS Code with Mermaid extension
- GitHub markdown
"""

import re
from collections import defaultdict
from typing import Optional

from planning_pipeline.models import RequirementHierarchy, RequirementNode


# =============================================================================
# Constants
# =============================================================================

MAX_DESCRIPTION_LENGTH = 30
COMPONENT_TYPE_PREFIXES = {
    "frontend": "FE",
    "backend": "BE",
    "middleware": "MW",
    "shared": "SH",
}


# =============================================================================
# Helper Functions
# =============================================================================


def _escape_mermaid_text(text: str) -> str:
    """Escape special characters for Mermaid label text.

    Args:
        text: Raw text that may contain special characters

    Returns:
        Escaped text safe for use in Mermaid labels
    """
    # Replace characters that break Mermaid syntax
    text = text.replace('"', "'")
    text = text.replace("[", "(")
    text = text.replace("]", ")")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace("{", "(")
    text = text.replace("}", ")")
    return text


def _truncate_description(description: str, max_length: int = MAX_DESCRIPTION_LENGTH) -> str:
    """Truncate description to max length with ellipsis.

    Args:
        description: Original description text
        max_length: Maximum length before truncation

    Returns:
        Truncated description with ... if needed
    """
    if len(description) <= max_length:
        return description
    return description[: max_length - 3] + "..."


def _make_component_id(comp_type: str, comp_name: str) -> str:
    """Create a component ID from type and name.

    Args:
        comp_type: Component type (frontend, backend, middleware, shared)
        comp_name: Component name (may contain '.' for class.method)

    Returns:
        Formatted component ID like 'BE_SessionTracker'
    """
    prefix = COMPONENT_TYPE_PREFIXES.get(comp_type, comp_type.upper()[:2])
    # Extract class name if it's a class.method pattern
    if "." in comp_name:
        class_name = comp_name.split(".")[0]
    else:
        class_name = comp_name
    # Remove any characters that aren't valid in Mermaid IDs
    class_name = re.sub(r"[^a-zA-Z0-9_]", "", class_name)
    return f"{prefix}_{class_name}"


def _collect_components(hierarchy: RequirementHierarchy) -> set[tuple[str, str]]:
    """Collect all unique components from the hierarchy.

    Args:
        hierarchy: The requirement hierarchy to extract components from

    Returns:
        Set of (component_type, component_name) tuples
    """
    components: set[tuple[str, str]] = set()

    def collect_from_node(node: RequirementNode) -> None:
        if node.implementation:
            for comp in node.implementation.frontend:
                components.add(("frontend", comp))
            for comp in node.implementation.backend:
                components.add(("backend", comp))
            for comp in node.implementation.middleware:
                components.add(("middleware", comp))
            for comp in node.implementation.shared:
                components.add(("shared", comp))
        for child in node.children:
            collect_from_node(child)

    for req in hierarchy.requirements:
        collect_from_node(req)

    return components


def _add_requirement_nodes(
    node: RequirementNode,
    lines: list[str],
    seen_ids: set[str],
) -> None:
    """Add requirement node definitions to Mermaid lines.

    Args:
        node: The requirement node to add
        lines: List of Mermaid lines to append to
        seen_ids: Set of already seen IDs to avoid duplicates
    """
    if node.id in seen_ids:
        return
    seen_ids.add(node.id)

    # Create node definition with label
    safe_id = re.sub(r"[^a-zA-Z0-9_]", "_", node.id)
    description = _truncate_description(node.description)
    description = _escape_mermaid_text(description)
    lines.append(f'    {safe_id}["{node.id}: {description}"]')

    # Recursively add children
    for child in node.children:
        _add_requirement_nodes(child, lines, seen_ids)


def _add_requirement_edges(
    node: RequirementNode,
    lines: list[str],
    seen_edges: set[tuple[str, str]],
) -> None:
    """Add parent-child edges to Mermaid lines.

    Args:
        node: The parent node
        lines: List of Mermaid lines to append to
        seen_edges: Set of already seen edge tuples to avoid duplicates
    """
    safe_parent_id = re.sub(r"[^a-zA-Z0-9_]", "_", node.id)

    for child in node.children:
        safe_child_id = re.sub(r"[^a-zA-Z0-9_]", "_", child.id)
        edge = (safe_parent_id, safe_child_id)
        if edge not in seen_edges:
            seen_edges.add(edge)
            lines.append(f"    {safe_parent_id} --> {safe_child_id}")
        _add_requirement_edges(child, lines, seen_edges)


def _add_component_links(
    node: RequirementNode,
    lines: list[str],
    seen_links: set[tuple[str, str]],
) -> None:
    """Add dashed links from requirements to implementation components.

    Args:
        node: The requirement node
        lines: List of Mermaid lines to append to
        seen_links: Set of already seen link tuples to avoid duplicates
    """
    safe_req_id = re.sub(r"[^a-zA-Z0-9_]", "_", node.id)

    if node.implementation:
        for comp_type, components in [
            ("frontend", node.implementation.frontend),
            ("backend", node.implementation.backend),
            ("middleware", node.implementation.middleware),
            ("shared", node.implementation.shared),
        ]:
            for comp in components:
                comp_id = _make_component_id(comp_type, comp)
                link = (safe_req_id, comp_id)
                if link not in seen_links:
                    seen_links.add(link)
                    lines.append(f"    {safe_req_id} -.-> {comp_id}")

    for child in node.children:
        _add_component_links(child, lines, seen_links)


def _group_requirements_by_prefix(
    requirements: list[RequirementNode],
    max_per_group: int,
) -> dict[str, list[RequirementNode]]:
    """Group requirements by their ID prefix for subgraph organization.

    Args:
        requirements: List of requirement nodes to group
        max_per_group: Maximum nodes per group before splitting

    Returns:
        Dictionary mapping group name to list of nodes
    """
    # Flatten all nodes first
    all_nodes: list[RequirementNode] = []

    def collect_nodes(node: RequirementNode) -> None:
        all_nodes.append(node)
        for child in node.children:
            collect_nodes(child)

    for req in requirements:
        collect_nodes(req)

    # If total is under max, no need to split
    if len(all_nodes) <= max_per_group:
        return {"Requirements": requirements}

    # Group by first part of ID prefix (e.g., REQ_001 -> REQ_001)
    groups: dict[str, list[RequirementNode]] = defaultdict(list)
    for req in requirements:
        # Extract base prefix from ID (e.g., REQ_001 from REQ_001.1.2)
        match = re.match(r"(REQ_\d+)", req.id)
        if match:
            prefix = match.group(1)
        else:
            prefix = "Other"
        groups[prefix].append(req)

    return dict(groups)


# =============================================================================
# Public Functions
# =============================================================================


def generate_requirements_mermaid(
    hierarchy: RequirementHierarchy,
    max_nodes_per_subgraph: int = 15,
) -> str:
    """Generate Mermaid flowchart from requirement hierarchy.

    Creates a flowchart with:
    - Requirements as rectangles with ID and description
    - Parent-child relationships as solid arrows
    - Implementation components as circles in a separate subgraph
    - Requirement-to-component links as dashed arrows

    Args:
        hierarchy: The requirement hierarchy to visualize
        max_nodes_per_subgraph: Max nodes before splitting into subgroups

    Returns:
        Mermaid flowchart syntax string
    """
    lines = ["flowchart LR"]

    # Collect all components for later
    components = _collect_components(hierarchy)
    seen_ids: set[str] = set()
    seen_edges: set[tuple[str, str]] = set()
    seen_links: set[tuple[str, str]] = set()

    # Group requirements if there are many
    groups = _group_requirements_by_prefix(
        hierarchy.requirements,
        max_nodes_per_subgraph,
    )

    # Add requirement nodes in subgraphs
    for group_name, reqs in groups.items():
        lines.append(f"    subgraph {group_name}")
        for req in reqs:
            _add_requirement_nodes(req, lines, seen_ids)
        lines.append("    end")

    # Add edges (outside subgraphs)
    for req in hierarchy.requirements:
        _add_requirement_edges(req, lines, seen_edges)

    # Add components subgraph if there are any
    if components:
        seen_comp_ids: set[str] = set()
        lines.append("    subgraph Components")
        for comp_type, comp_name in sorted(components):
            comp_id = _make_component_id(comp_type, comp_name)
            if comp_id not in seen_comp_ids:
                seen_comp_ids.add(comp_id)
                # Extract display name
                if "." in comp_name:
                    display_name = comp_name.split(".")[0]
                else:
                    display_name = comp_name
                prefix = COMPONENT_TYPE_PREFIXES.get(comp_type, comp_type.upper()[:2])
                display_name = _escape_mermaid_text(display_name)
                lines.append(f'    {comp_id}(("{prefix}: {display_name}"))')
        lines.append("    end")

    # Add component links
    for req in hierarchy.requirements:
        _add_component_links(req, lines, seen_links)

    return "\n".join(lines)


def generate_class_diagram_mermaid(hierarchy: RequirementHierarchy) -> str:
    """Generate Mermaid class diagram from implementation components.

    Extracts class.method patterns from backend components and generates
    a class diagram showing classes with their methods.

    Args:
        hierarchy: The requirement hierarchy to extract classes from

    Returns:
        Mermaid class diagram syntax string
    """
    lines = ["classDiagram"]

    # Collect all backend components and group by class
    classes: dict[str, list[str]] = defaultdict(list)

    def extract_classes(node: RequirementNode) -> None:
        if node.implementation:
            for comp in node.implementation.backend:
                if "." in comp:
                    class_name, method = comp.split(".", 1)
                    classes[class_name].append(method)
                else:
                    # Standalone class without methods
                    if comp not in classes:
                        classes[comp] = []
        for child in node.children:
            extract_classes(child)

    for req in hierarchy.requirements:
        extract_classes(req)

    # Generate class definitions
    for class_name, methods in sorted(classes.items()):
        safe_class_name = re.sub(r"[^a-zA-Z0-9_]", "", class_name)
        lines.append(f"    class {safe_class_name} {{")
        # Add unique methods
        for method in sorted(set(methods)):
            safe_method = re.sub(r"[^a-zA-Z0-9_]", "", method)
            lines.append(f"        +{safe_method}")
        lines.append("    }")

    return "\n".join(lines)
