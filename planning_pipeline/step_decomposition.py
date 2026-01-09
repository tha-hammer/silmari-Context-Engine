"""Pipeline step for requirement decomposition.

This module provides the step function that orchestrates requirement
decomposition between step_research() and step_planning(). It:
1. Reads the research document
2. Calls decompose_requirements() to generate hierarchy
3. Generates Mermaid visualization
4. Creates property test skeletons (if acceptance criteria exist)
5. Writes all outputs to disk

Pipeline position: step_research() -> [step_requirement_decomposition()] -> step_planning()
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from planning_pipeline.decomposition import (
    DecompositionError,
    decompose_requirements,
)
from planning_pipeline.models import (
    RequirementHierarchy,
    RequirementNode,
)
from planning_pipeline.property_generator import (
    derive_properties,
    generate_full_test_file,
)
from planning_pipeline.visualization import generate_requirements_mermaid


def _print_progress(message: str) -> None:
    """Print progress message and flush stdout."""
    print(message)
    sys.stdout.flush()


def step_requirement_decomposition(
    project_path: Path,
    research_path: str,
    output_dir: Optional[str] = None,
    progress: Optional[Callable[[str], None]] = None,
) -> dict[str, Any]:
    """Execute requirement decomposition step.

    Pipeline position: step_research() -> [this] -> step_planning()

    Takes research output (typically from step_research()) and produces:
    - requirements_hierarchy.json: Full hierarchy with all metadata
    - requirements_diagram.mmd: Mermaid flowchart for visualization
    - property_tests_skeleton.py: Hypothesis test stubs (if acceptance criteria exist)

    Args:
        project_path: Root project path (Path object or string).
        research_path: Path to research document (relative to project_path).
        output_dir: Optional custom output directory. Defaults to
            {project}/thoughts/searchable/plans/{date}-requirements/
        progress: Optional callback for CLI progress updates.

    Returns:
        Dict with:
        - success: bool
        - hierarchy_path: str (path to requirements_hierarchy.json)
        - diagram_path: str (path to requirements_diagram.mmd)
        - tests_path: str | None (path to property_tests_skeleton.py)
        - requirement_count: int (total requirements including children)
        - output_dir: str (directory where outputs were written)
        - error: str (if success=False)
    """
    # Use default progress callback if none provided
    report = progress or _print_progress

    # Ensure project_path is a Path
    if not isinstance(project_path, Path):
        project_path = Path(project_path)

    # Validate research_path is provided
    if not research_path:
        return {
            "success": False,
            "error": "research_path is required but was None or empty",
        }

    # Resolve research file path - try multiple locations
    # 1. If absolute path, use directly
    # 2. Try as relative to project
    # 3. Try searchable variant (thoughts/searchable/shared vs thoughts/searchable)
    research_file = None

    if Path(research_path).is_absolute():
        research_file = Path(research_path)
    else:
        # Try direct path first
        candidate = project_path / research_path
        if candidate.exists():
            research_file = candidate
        else:
            # Try searchable variant: thoughts/searchable/X -> thoughts/searchable/shared/X
            if research_path.startswith("thoughts/searchable/"):
                searchable_path = research_path.replace(
                    "thoughts/searchable/", "thoughts/searchable/shared/", 1
                )
                candidate = project_path / searchable_path
                if candidate.exists():
                    research_file = candidate

    if research_file is None or not research_file.exists():
        return {
            "success": False,
            "error": f"Research file not found: {research_path}",
        }

    # Read research content
    report(f"  Reading research: {research_file.name}")
    try:
        research_content = research_file.read_text()
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read research file: {e}",
        }
    report(f"  ✓ Loaded {len(research_content):,} chars from research")

    # Call decomposition (progress callback passed through)
    result = decompose_requirements(research_content, progress=report)

    # Handle decomposition error
    if isinstance(result, DecompositionError):
        return {
            "success": False,
            "error": result.error,
            "error_code": result.error_code.value if result.error_code else None,
        }

    hierarchy = result

    # Add source research to metadata
    hierarchy.metadata["source_research"] = research_path
    hierarchy.metadata["decomposed_at"] = datetime.now().isoformat()

    # Determine output directory
    if output_dir:
        out_path = Path(output_dir)
    else:
        date_str = datetime.now().strftime("%Y-%m-%d-%H-%M")
        out_path = project_path / "thoughts" / "searchable" / "shared" / "plans" / f"{date_str}-requirements"

    # Create output directory
    out_path.mkdir(parents=True, exist_ok=True)

    # Write hierarchy JSON
    report("  Writing outputs...")
    hierarchy_file = out_path / "requirements_hierarchy.json"
    try:
        with open(hierarchy_file, "w") as f:
            json.dump(hierarchy.to_dict(), f, indent=2)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to write hierarchy: {e}",
        }

    # Generate and write Mermaid diagram
    diagram_content = generate_requirements_mermaid(hierarchy)
    diagram_file = out_path / "requirements_diagram.mmd"
    try:
        diagram_file.write_text(diagram_content)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to write diagram: {e}",
        }

    # Collect acceptance criteria and generate property tests
    acceptance_criteria = _collect_acceptance_criteria(hierarchy)
    tests_path = None

    if acceptance_criteria:
        # Derive properties from criteria
        properties = derive_properties(acceptance_criteria)

        if properties:
            # Generate test file with generic class name
            test_content = generate_full_test_file(
                properties=properties,
                class_name="Implementation",
                module_path="planning_pipeline.implementation",
            )

            tests_file = out_path / "property_tests_skeleton.py"
            try:
                tests_file.write_text(test_content)
                tests_path = str(tests_file)
            except Exception as e:
                # Non-fatal - we can continue without test file
                pass

    report(f"  ✓ Wrote hierarchy, diagram{', tests' if tests_path else ''}")

    # Count total requirements (including children)
    requirement_count = _count_requirements(hierarchy)

    return {
        "success": True,
        "hierarchy_path": str(hierarchy_file),
        "diagram_path": str(diagram_file),
        "tests_path": tests_path,
        "requirement_count": requirement_count,
        "output_dir": str(out_path),
    }


def _collect_acceptance_criteria(hierarchy: RequirementHierarchy) -> list[str]:
    """Collect all acceptance criteria from hierarchy recursively.

    Walks the entire hierarchy tree and collects acceptance criteria
    from all nodes at every level.

    Args:
        hierarchy: The requirement hierarchy to collect from

    Returns:
        List of unique acceptance criteria strings
    """
    criteria: list[str] = []
    seen: set[str] = set()

    def collect_from_node(node: RequirementNode) -> None:
        for criterion in node.acceptance_criteria:
            if criterion not in seen:
                seen.add(criterion)
                criteria.append(criterion)

        for child in node.children:
            collect_from_node(child)

    for req in hierarchy.requirements:
        collect_from_node(req)

    return criteria


def _count_requirements(hierarchy: RequirementHierarchy) -> int:
    """Count total requirements including all children.

    Args:
        hierarchy: The requirement hierarchy to count

    Returns:
        Total number of requirement nodes
    """
    count = 0

    def count_node(node: RequirementNode) -> int:
        total = 1  # Count this node
        for child in node.children:
            total += count_node(child)
        return total

    for req in hierarchy.requirements:
        count += count_node(req)

    return count
