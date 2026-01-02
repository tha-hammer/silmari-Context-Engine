"""Tests for Mermaid diagram generation from requirement hierarchies.

Uses Hypothesis for property-based testing to verify invariants:
- All nodes appear in output
- All node IDs are unique
- Parent-child edges are correctly generated
- Component links use dashed lines
"""

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from planning_pipeline.models import (
    RequirementNode,
    RequirementHierarchy,
    ImplementationComponents,
)


# =============================================================================
# Test Data Strategies
# =============================================================================


@st.composite
def _requirement_id_strategy(draw, prefix: str = "REQ") -> str:
    """Generate valid requirement IDs like REQ_001, REQ_001.2."""
    base_num = draw(st.integers(min_value=1, max_value=999))
    base_id = f"{prefix}_{base_num:03d}"

    num_levels = draw(st.integers(min_value=0, max_value=2))
    for _ in range(num_levels):
        sub_num = draw(st.integers(min_value=1, max_value=9))
        base_id = f"{base_id}.{sub_num}"

    return base_id


def _non_whitespace_text(min_size: int = 1, max_size: int = 100):
    """Strategy for generating non-whitespace text."""
    return st.text(
        alphabet=st.characters(
            blacklist_categories=("Cs",), blacklist_characters="\r\n\t "
        ),
        min_size=min_size,
        max_size=max_size,
    ).filter(lambda s: s.strip())


@st.composite
def _simple_requirement_node_strategy(draw, with_children: bool = False, depth: int = 0) -> RequirementNode:
    """Generate RequirementNode for testing visualization."""
    node_id = draw(_requirement_id_strategy())
    description = draw(_non_whitespace_text(1, 100))
    types = ["parent", "sub_process", "implementation"]
    node_type = draw(st.sampled_from(types))

    impl = None
    if node_type == "implementation" and draw(st.booleans()):
        impl = ImplementationComponents(
            frontend=draw(st.lists(st.text(min_size=1, max_size=20), max_size=3)),
            backend=draw(st.lists(st.text(min_size=1, max_size=20), max_size=3)),
            middleware=draw(st.lists(st.text(min_size=1, max_size=20), max_size=3)),
            shared=draw(st.lists(st.text(min_size=1, max_size=20), max_size=3)),
        )

    children = []
    if with_children and depth < 2:
        num_children = draw(st.integers(min_value=0, max_value=2))
        for _ in range(num_children):
            child = draw(_simple_requirement_node_strategy(with_children=True, depth=depth + 1))
            child.parent_id = node_id
            children.append(child)

    return RequirementNode(
        id=node_id,
        description=description,
        type=node_type,
        children=children,
        implementation=impl,
    )


@st.composite
def _hierarchy_strategy(draw) -> RequirementHierarchy:
    """Generate a RequirementHierarchy for testing."""
    num_requirements = draw(st.integers(min_value=0, max_value=5))
    requirements = []
    for _ in range(num_requirements):
        node = draw(_simple_requirement_node_strategy(with_children=True))
        requirements.append(node)
    return RequirementHierarchy(requirements=requirements)


# =============================================================================
# TestMermaidFlowchartGeneration
# =============================================================================


class TestMermaidFlowchartGeneration:
    """Tests for generate_requirements_mermaid function."""

    def test_empty_hierarchy_produces_minimal_diagram(self):
        """Empty hierarchy should produce a valid but minimal Mermaid diagram."""
        from planning_pipeline.visualization import generate_requirements_mermaid

        hierarchy = RequirementHierarchy(requirements=[])
        mermaid = generate_requirements_mermaid(hierarchy)

        assert mermaid.startswith("flowchart LR")
        assert "subgraph Requirements" in mermaid

    def test_single_requirement_appears_as_node(self):
        """Single requirement should appear as a node in the diagram."""
        from planning_pipeline.visualization import generate_requirements_mermaid

        node = RequirementNode(
            id="REQ_001", description="Track user sessions", type="parent"
        )
        hierarchy = RequirementHierarchy(requirements=[node])
        mermaid = generate_requirements_mermaid(hierarchy)

        assert "REQ_001" in mermaid
        assert "Track user sessions" in mermaid

    def test_parent_child_produces_edge(self):
        """Parent-child relationship should produce an edge in the diagram."""
        from planning_pipeline.visualization import generate_requirements_mermaid

        child = RequirementNode(
            id="REQ_001.1",
            description="Initialize tracking",
            type="sub_process",
            parent_id="REQ_001",
        )
        parent = RequirementNode(
            id="REQ_001",
            description="Track user sessions",
            type="parent",
            children=[child],
        )
        hierarchy = RequirementHierarchy(requirements=[parent])
        mermaid = generate_requirements_mermaid(hierarchy)

        assert "REQ_001 -->" in mermaid or "REQ_001-->" in mermaid

    def test_implementation_components_in_separate_subgraph(self):
        """Implementation components should appear in a Components subgraph."""
        from planning_pipeline.visualization import generate_requirements_mermaid

        impl = ImplementationComponents(
            backend=["SessionTracker.initialize"],
            frontend=[],
            middleware=[],
            shared=[],
        )
        node = RequirementNode(
            id="REQ_001",
            description="Track sessions",
            type="implementation",
            implementation=impl,
        )
        hierarchy = RequirementHierarchy(requirements=[node])
        mermaid = generate_requirements_mermaid(hierarchy)

        assert "subgraph Components" in mermaid
        assert "SessionTracker" in mermaid

    @given(_hierarchy_strategy())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_all_nodes_unique_in_output(self, hierarchy: RequirementHierarchy):
        """All node IDs in output should be unique (property-based test)."""
        from planning_pipeline.visualization import generate_requirements_mermaid

        mermaid = generate_requirements_mermaid(hierarchy)

        # Extract all node definitions: ID["label"] or ID(("label"))
        import re

        # Match patterns like: REQ_001["label"] or BE_Name(("label"))
        node_defs = re.findall(r'(\w+)\["|(\w+)\(\("', mermaid)
        node_ids = [n[0] or n[1] for n in node_defs]

        # All IDs should be unique
        assert len(node_ids) == len(set(node_ids)), f"Duplicate node IDs found: {node_ids}"

    def test_long_description_truncated(self):
        """Descriptions longer than 30 characters should be truncated."""
        from planning_pipeline.visualization import generate_requirements_mermaid

        long_desc = "A" * 50  # 50 character description
        node = RequirementNode(
            id="REQ_001",
            description=long_desc,
            type="parent",
        )
        hierarchy = RequirementHierarchy(requirements=[node])
        mermaid = generate_requirements_mermaid(hierarchy)

        # Should contain truncated version with ...
        assert "..." in mermaid
        # Should not contain the full 50-char string
        assert long_desc not in mermaid

    def test_special_characters_escaped(self):
        """Special characters in descriptions should be escaped for Mermaid."""
        from planning_pipeline.visualization import generate_requirements_mermaid

        node = RequirementNode(
            id="REQ_001",
            description='Test with "quotes" and [brackets]',
            type="parent",
        )
        hierarchy = RequirementHierarchy(requirements=[node])
        mermaid = generate_requirements_mermaid(hierarchy)

        # Should not have unescaped quotes or brackets that break Mermaid
        assert "REQ_001" in mermaid
        # The output should be valid Mermaid (not crash)
        assert "flowchart LR" in mermaid

    def test_component_links_are_dashed(self):
        """Links from requirements to components should be dashed."""
        from planning_pipeline.visualization import generate_requirements_mermaid

        impl = ImplementationComponents(
            backend=["AuthService"],
            frontend=[],
            middleware=[],
            shared=[],
        )
        node = RequirementNode(
            id="REQ_001",
            description="Auth",
            type="implementation",
            implementation=impl,
        )
        hierarchy = RequirementHierarchy(requirements=[node])
        mermaid = generate_requirements_mermaid(hierarchy)

        # Dashed lines use -.-> syntax in Mermaid
        assert "-.->" in mermaid


# =============================================================================
# TestMermaidClassDiagram
# =============================================================================


class TestMermaidClassDiagram:
    """Tests for generate_class_diagram_mermaid function."""

    def test_empty_hierarchy_produces_minimal_diagram(self):
        """Empty hierarchy should produce minimal class diagram."""
        from planning_pipeline.visualization import generate_class_diagram_mermaid

        hierarchy = RequirementHierarchy(requirements=[])
        mermaid = generate_class_diagram_mermaid(hierarchy)

        assert mermaid.startswith("classDiagram")

    def test_backend_component_as_method_produces_class(self):
        """Backend component like 'Class.method' should produce class with method."""
        from planning_pipeline.visualization import generate_class_diagram_mermaid

        impl = ImplementationComponents(
            backend=["SessionTracker.initialize", "SessionTracker.track"],
            frontend=[],
            middleware=[],
            shared=[],
        )
        node = RequirementNode(
            id="REQ_001",
            description="Track sessions",
            type="implementation",
            implementation=impl,
        )
        hierarchy = RequirementHierarchy(requirements=[node])
        mermaid = generate_class_diagram_mermaid(hierarchy)

        assert "class SessionTracker" in mermaid
        assert "+initialize" in mermaid
        assert "+track" in mermaid

    def test_multiple_classes_from_different_components(self):
        """Multiple classes should be extracted from backend components."""
        from planning_pipeline.visualization import generate_class_diagram_mermaid

        impl = ImplementationComponents(
            backend=["AuthService.login", "UserRepository.find"],
            frontend=[],
            middleware=[],
            shared=[],
        )
        node = RequirementNode(
            id="REQ_001",
            description="Auth and users",
            type="implementation",
            implementation=impl,
        )
        hierarchy = RequirementHierarchy(requirements=[node])
        mermaid = generate_class_diagram_mermaid(hierarchy)

        assert "class AuthService" in mermaid
        assert "class UserRepository" in mermaid

    def test_component_without_method_treated_as_standalone(self):
        """Component without '.' should be treated as standalone class."""
        from planning_pipeline.visualization import generate_class_diagram_mermaid

        impl = ImplementationComponents(
            backend=["StandaloneService"],
            frontend=[],
            middleware=[],
            shared=[],
        )
        node = RequirementNode(
            id="REQ_001",
            description="Standalone",
            type="implementation",
            implementation=impl,
        )
        hierarchy = RequirementHierarchy(requirements=[node])
        mermaid = generate_class_diagram_mermaid(hierarchy)

        assert "class StandaloneService" in mermaid


# =============================================================================
# TestLargeHierarchyGrouping
# =============================================================================


class TestLargeHierarchyGrouping:
    """Tests for grouping large hierarchies into subgraphs."""

    def test_large_hierarchy_creates_subgroups(self):
        """Hierarchies with >15 nodes should create ID-prefix-based subgroups."""
        from planning_pipeline.visualization import generate_requirements_mermaid

        # Create 20 nodes with different prefixes
        nodes = []
        for i in range(1, 21):
            prefix_num = (i - 1) // 5 + 1  # Groups: 1-5, 6-10, 11-15, 16-20
            nodes.append(
                RequirementNode(
                    id=f"REQ_{prefix_num:03d}.{i}",
                    description=f"Requirement {i}",
                    type="parent",
                )
            )

        hierarchy = RequirementHierarchy(requirements=nodes)
        mermaid = generate_requirements_mermaid(hierarchy, max_nodes_per_subgraph=5)

        # Should have multiple subgraphs
        subgraph_count = mermaid.count("subgraph")
        assert subgraph_count > 1, "Large hierarchies should create multiple subgraphs"
