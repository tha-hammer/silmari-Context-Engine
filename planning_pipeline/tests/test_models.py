"""Property-based tests for RequirementNode and RequirementHierarchy models.

Uses Hypothesis for property-based testing to verify invariants:
- Description preserved through serialization
- Type validation (parent, sub_process, implementation)
- Acceptance criteria round-trip
- Unique IDs in hierarchy
- Parent-child consistency
- Maximum hierarchy depth of 3
"""

import pytest
from hypothesis import given, assume, settings, HealthCheck
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, Bundle


# =============================================================================
# Strategies for generating test data
# =============================================================================

# Valid requirement types
VALID_TYPES = ["parent", "sub_process", "implementation"]

# Valid categories for requirements
VALID_CATEGORIES = frozenset([
    "functional", "non_functional", "security",
    "performance", "usability", "integration"
])


@st.composite
def _requirement_id_strategy(draw, prefix: str = "REQ") -> str:
    """Generate valid requirement IDs like REQ_001, REQ_001.2, REQ_001.2.1."""
    base_num = draw(st.integers(min_value=1, max_value=999))
    base_id = f"{prefix}_{base_num:03d}"

    # Optionally add sub-levels (up to 2 additional levels for 3-tier max)
    num_levels = draw(st.integers(min_value=0, max_value=2))
    for _ in range(num_levels):
        sub_num = draw(st.integers(min_value=1, max_value=9))
        base_id = f"{base_id}.{sub_num}"

    return base_id


@st.composite
def _implementation_components_strategy(draw) -> dict:
    """Generate valid ImplementationComponents data."""
    return {
        "frontend": draw(st.lists(st.text(min_size=1, max_size=30), max_size=5)),
        "backend": draw(st.lists(st.text(min_size=1, max_size=30), max_size=5)),
        "middleware": draw(st.lists(st.text(min_size=1, max_size=30), max_size=5)),
        "shared": draw(st.lists(st.text(min_size=1, max_size=30), max_size=5)),
    }


def _non_whitespace_text(min_size: int = 1, max_size: int = 100):
    """Strategy for generating non-whitespace text."""
    return st.text(
        alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\r\n\t "),
        min_size=min_size,
        max_size=max_size,
    ).filter(lambda s: s.strip())


@st.composite
def _testable_property_strategy(draw) -> dict:
    """Generate valid TestableProperty data."""
    property_types = ["invariant", "round_trip", "idempotence", "oracle"]
    return {
        "criterion": draw(_non_whitespace_text(1, 100)),
        "property_type": draw(st.sampled_from(property_types)),
        "hypothesis_strategy": draw(_non_whitespace_text(1, 50)),
        "test_skeleton": draw(_non_whitespace_text(1, 200)),
    }


@st.composite
def _requirement_node_strategy(draw, with_children: bool = False, depth: int = 0) -> dict:
    """Generate valid RequirementNode data."""
    node_id = draw(_requirement_id_strategy())
    description = draw(_non_whitespace_text(1, 200))
    node_type = draw(st.sampled_from(VALID_TYPES))
    acceptance_criteria = draw(st.lists(_non_whitespace_text(1, 100), max_size=5))

    # Implementation is typically only for implementation-type nodes
    implementation = None
    if node_type == "implementation":
        if draw(st.booleans()):
            implementation = draw(_implementation_components_strategy())

    testable_properties = draw(
        st.lists(_testable_property_strategy(), max_size=3)
    )

    # Recursively generate children if requested and depth allows
    children = []
    if with_children and depth < 2:
        num_children = draw(st.integers(min_value=0, max_value=3))
        for _ in range(num_children):
            child = draw(_requirement_node_strategy(with_children=True, depth=depth + 1))
            child["parent_id"] = node_id
            children.append(child)

    return {
        "id": node_id,
        "description": description,
        "type": node_type,
        "parent_id": None,
        "children": children,
        "acceptance_criteria": acceptance_criteria,
        "implementation": implementation,
        "testable_properties": testable_properties,
    }


# =============================================================================
# Property-based tests for ImplementationComponents
# =============================================================================


class TestImplementationComponentsProperties:
    """Property-based tests for ImplementationComponents."""

    @given(_implementation_components_strategy())
    def test_round_trip_serialization(self, data):
        """ImplementationComponents should round-trip through dict serialization."""
        from planning_pipeline.models import ImplementationComponents

        comp = ImplementationComponents(
            frontend=data["frontend"],
            backend=data["backend"],
            middleware=data["middleware"],
            shared=data["shared"],
        )

        # Round-trip through dict
        as_dict = comp.to_dict()
        restored = ImplementationComponents.from_dict(as_dict)

        assert comp.frontend == restored.frontend
        assert comp.backend == restored.backend
        assert comp.middleware == restored.middleware
        assert comp.shared == restored.shared

    @given(_implementation_components_strategy())
    def test_dict_has_all_keys(self, data):
        """to_dict() should include all component types."""
        from planning_pipeline.models import ImplementationComponents

        comp = ImplementationComponents(
            frontend=data["frontend"],
            backend=data["backend"],
            middleware=data["middleware"],
            shared=data["shared"],
        )

        as_dict = comp.to_dict()
        assert "frontend" in as_dict
        assert "backend" in as_dict
        assert "middleware" in as_dict
        assert "shared" in as_dict


# =============================================================================
# Property-based tests for TestableProperty
# =============================================================================


class TestTestablePropertyProperties:
    """Property-based tests for TestableProperty."""

    @given(_testable_property_strategy())
    def test_round_trip_serialization(self, data):
        """TestableProperty should round-trip through dict serialization."""
        from planning_pipeline.models import TestableProperty

        prop = TestableProperty(
            criterion=data["criterion"],
            property_type=data["property_type"],
            hypothesis_strategy=data["hypothesis_strategy"],
            test_skeleton=data["test_skeleton"],
        )

        as_dict = prop.to_dict()
        restored = TestableProperty.from_dict(as_dict)

        assert prop.criterion == restored.criterion
        assert prop.property_type == restored.property_type
        assert prop.hypothesis_strategy == restored.hypothesis_strategy
        assert prop.test_skeleton == restored.test_skeleton

    @given(st.sampled_from(["invariant", "round_trip", "idempotence", "oracle"]))
    def test_valid_property_types(self, property_type):
        """Valid property types should be accepted."""
        from planning_pipeline.models import TestableProperty

        prop = TestableProperty(
            criterion="test",
            property_type=property_type,
            hypothesis_strategy="st.integers()",
            test_skeleton="@given(...)",
        )
        assert prop.property_type == property_type


# =============================================================================
# Property-based tests for RequirementNode
# =============================================================================


class TestRequirementNodeProperties:
    """Property-based tests for RequirementNode."""

    @given(_non_whitespace_text(1, 200))
    def test_description_preserved(self, description):
        """Description should be preserved through serialization."""
        from planning_pipeline.models import RequirementNode

        node = RequirementNode(
            id="REQ_001",
            description=description,
            type="parent",
        )

        as_dict = node.to_dict()
        restored = RequirementNode.from_dict(as_dict)

        assert node.description == restored.description

    @given(st.sampled_from(VALID_TYPES), _non_whitespace_text(1, 100))
    def test_type_and_description_valid(self, node_type, description):
        """Valid types should be accepted with any non-empty description."""
        from planning_pipeline.models import RequirementNode

        node = RequirementNode(
            id="REQ_001",
            description=description,
            type=node_type,
        )

        assert node.type == node_type
        assert node.description == description

    @given(st.lists(st.text(min_size=1, max_size=100), max_size=10))
    def test_acceptance_criteria_round_trip(self, criteria):
        """Acceptance criteria should round-trip through serialization."""
        from planning_pipeline.models import RequirementNode

        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="implementation",
            acceptance_criteria=criteria,
        )

        as_dict = node.to_dict()
        restored = RequirementNode.from_dict(as_dict)

        assert node.acceptance_criteria == restored.acceptance_criteria

    @given(_requirement_node_strategy(with_children=True))
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_full_node_round_trip(self, data):
        """Full RequirementNode should round-trip through serialization."""
        from planning_pipeline.models import RequirementNode, ImplementationComponents, TestableProperty

        def build_node(node_data):
            impl = None
            if node_data["implementation"]:
                impl = ImplementationComponents(
                    frontend=node_data["implementation"]["frontend"],
                    backend=node_data["implementation"]["backend"],
                    middleware=node_data["implementation"]["middleware"],
                    shared=node_data["implementation"]["shared"],
                )

            props = [
                TestableProperty(
                    criterion=p["criterion"],
                    property_type=p["property_type"],
                    hypothesis_strategy=p["hypothesis_strategy"],
                    test_skeleton=p["test_skeleton"],
                )
                for p in node_data["testable_properties"]
            ]

            children = [build_node(c) for c in node_data["children"]]

            return RequirementNode(
                id=node_data["id"],
                description=node_data["description"],
                type=node_data["type"],
                parent_id=node_data["parent_id"],
                children=children,
                acceptance_criteria=node_data["acceptance_criteria"],
                implementation=impl,
                testable_properties=props,
            )

        node = build_node(data)
        as_dict = node.to_dict()
        restored = RequirementNode.from_dict(as_dict)

        assert node.id == restored.id
        assert node.description == restored.description
        assert node.type == restored.type
        assert len(node.children) == len(restored.children)

    def test_invalid_type_raises_error(self):
        """Invalid type should raise ValueError."""
        from planning_pipeline.models import RequirementNode

        with pytest.raises(ValueError, match="Invalid type"):
            RequirementNode(
                id="REQ_001",
                description="Test",
                type="invalid_type",
            )

    def test_empty_description_raises_error(self):
        """Empty description should raise ValueError."""
        from planning_pipeline.models import RequirementNode

        with pytest.raises(ValueError, match="description"):
            RequirementNode(
                id="REQ_001",
                description="",
                type="parent",
            )


# =============================================================================
# Property-based tests for RequirementHierarchy
# =============================================================================


class TestRequirementHierarchyProperties:
    """Property-based tests for RequirementHierarchy."""

    @given(st.lists(_requirement_node_strategy(), min_size=0, max_size=5))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_round_trip_serialization(self, nodes_data):
        """RequirementHierarchy should round-trip through dict serialization."""
        from planning_pipeline.models import RequirementNode, RequirementHierarchy

        nodes = [
            RequirementNode(
                id=n["id"],
                description=n["description"],
                type=n["type"],
                acceptance_criteria=n["acceptance_criteria"],
            )
            for n in nodes_data
        ]

        hierarchy = RequirementHierarchy(requirements=nodes)

        as_dict = hierarchy.to_dict()
        restored = RequirementHierarchy.from_dict(as_dict)

        assert len(hierarchy.requirements) == len(restored.requirements)

    def test_get_by_id_returns_correct_node(self):
        """get_by_id should return the correct node."""
        from planning_pipeline.models import RequirementNode, RequirementHierarchy

        node1 = RequirementNode(id="REQ_001", description="First", type="parent")
        node2 = RequirementNode(id="REQ_002", description="Second", type="parent")

        hierarchy = RequirementHierarchy(requirements=[node1, node2])

        found = hierarchy.get_by_id("REQ_001")
        assert found is not None
        assert found.id == "REQ_001"
        assert found.description == "First"

    def test_get_by_id_returns_none_for_missing(self):
        """get_by_id should return None for missing IDs."""
        from planning_pipeline.models import RequirementNode, RequirementHierarchy

        node = RequirementNode(id="REQ_001", description="Test", type="parent")
        hierarchy = RequirementHierarchy(requirements=[node])

        assert hierarchy.get_by_id("REQ_999") is None

    def test_add_requirement(self):
        """add_requirement should add a new top-level requirement."""
        from planning_pipeline.models import RequirementNode, RequirementHierarchy

        hierarchy = RequirementHierarchy(requirements=[])
        node = RequirementNode(id="REQ_001", description="New", type="parent")

        hierarchy.add_requirement(node)

        assert len(hierarchy.requirements) == 1
        assert hierarchy.requirements[0].id == "REQ_001"

    def test_add_child_sets_parent_id(self):
        """add_child should set the child's parent_id correctly."""
        from planning_pipeline.models import RequirementNode, RequirementHierarchy

        parent = RequirementNode(id="REQ_001", description="Parent", type="parent")
        hierarchy = RequirementHierarchy(requirements=[parent])

        child = RequirementNode(id="REQ_001.1", description="Child", type="sub_process")
        hierarchy.add_child("REQ_001", child)

        assert child.parent_id == "REQ_001"
        assert len(parent.children) == 1
        assert parent.children[0].id == "REQ_001.1"


# =============================================================================
# Stateful testing with RuleBasedStateMachine
# =============================================================================


class RequirementHierarchyStateMachine(RuleBasedStateMachine):
    """Stateful testing for RequirementHierarchy operations."""

    def __init__(self):
        super().__init__()
        from planning_pipeline.models import RequirementHierarchy
        self.hierarchy = RequirementHierarchy(requirements=[])
        self.all_ids: set = set()
        self.parent_child_map: dict = {}  # child_id -> parent_id
        self._id_counter = 0

    def _generate_id(self, parent_id: str | None = None) -> str:
        """Generate a unique requirement ID."""
        self._id_counter += 1
        if parent_id:
            return f"{parent_id}.{self._id_counter}"
        return f"REQ_{self._id_counter:03d}"

    parents = Bundle("parents")
    children = Bundle("children")

    @rule(target=parents, description=_non_whitespace_text(1, 50))
    def add_parent_requirement(self, description):
        """Add a parent requirement."""
        from planning_pipeline.models import RequirementNode

        new_id = self._generate_id()
        node = RequirementNode(id=new_id, description=description, type="parent")
        self.hierarchy.add_requirement(node)
        self.all_ids.add(new_id)
        return new_id

    @rule(
        target=children,
        parent_id=parents,
        description=_non_whitespace_text(1, 50),
    )
    def add_child_to_parent(self, parent_id, description):
        """Add a child to an existing parent."""
        from planning_pipeline.models import RequirementNode

        new_id = self._generate_id(parent_id)
        child = RequirementNode(id=new_id, description=description, type="sub_process")
        self.hierarchy.add_child(parent_id, child)
        self.all_ids.add(new_id)
        self.parent_child_map[new_id] = parent_id
        return new_id

    @invariant()
    def ids_are_unique(self):
        """All IDs in the hierarchy must be unique."""
        seen_ids = set()

        def collect_ids(node):
            assert node.id not in seen_ids, f"Duplicate ID: {node.id}"
            seen_ids.add(node.id)
            for child in node.children:
                collect_ids(child)

        for req in self.hierarchy.requirements:
            collect_ids(req)

    @invariant()
    def parent_child_consistency(self):
        """Children must have correct parent_id references."""
        def check_consistency(node, expected_parent_id=None):
            if expected_parent_id is not None:
                assert node.parent_id == expected_parent_id, (
                    f"Node {node.id} has parent_id {node.parent_id}, "
                    f"expected {expected_parent_id}"
                )
            for child in node.children:
                check_consistency(child, node.id)

        for req in self.hierarchy.requirements:
            check_consistency(req)

    @invariant()
    def hierarchy_depth_reasonable(self):
        """Hierarchy depth should be reasonable (arbitrary but not infinite).

        Note: Removed 3-level max constraint to support arbitrary depth.
        We now allow any reasonable depth (up to 20 levels for sanity).
        """
        max_reasonable_depth = 20

        def check_depth(node, current_depth=1):
            assert current_depth <= max_reasonable_depth, (
                f"Node {node.id} at depth {current_depth} exceeds max depth of {max_reasonable_depth}"
            )
            for child in node.children:
                check_depth(child, current_depth + 1)

        for req in self.hierarchy.requirements:
            check_depth(req)


TestRequirementHierarchyStateful = RequirementHierarchyStateMachine.TestCase


# =============================================================================
# Manual test cases for edge cases
# =============================================================================


# =============================================================================
# Tests for function_id field on RequirementNode
# =============================================================================


class TestRequirementNodeFunctionId:
    """Tests for function_id field on RequirementNode."""

    def test_function_id_stored_on_creation(self):
        """Given function_id provided, when node created, then function_id is stored."""
        from planning_pipeline.models import RequirementNode

        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
            function_id="AuthService.login",
        )
        assert node.function_id == "AuthService.login"

    def test_function_id_serialized_to_dict(self):
        """Given node with function_id, when to_dict called, then function_id in output."""
        from planning_pipeline.models import RequirementNode

        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
            function_id="DataValidator.validate",
        )
        result = node.to_dict()
        assert result["function_id"] == "DataValidator.validate"

    def test_function_id_deserialized_from_dict(self):
        """Given dict with function_id, when from_dict called, then function_id restored."""
        from planning_pipeline.models import RequirementNode

        data = {
            "id": "REQ_001",
            "description": "Test requirement",
            "type": "parent",
            "function_id": "UserService.create",
            "parent_id": None,
            "children": [],
            "acceptance_criteria": [],
            "implementation": None,
            "testable_properties": [],
        }
        node = RequirementNode.from_dict(data)
        assert node.function_id == "UserService.create"

    def test_function_id_none_when_not_provided(self):
        """Given no function_id, when node created, then function_id is None."""
        from planning_pipeline.models import RequirementNode

        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
        )
        assert node.function_id is None

    @given(st.text(min_size=1, max_size=100).filter(lambda x: x.strip()))
    def test_function_id_roundtrip_property(self, function_id: str):
        """Property: function_id survives serialization roundtrip."""
        from planning_pipeline.models import RequirementNode

        node = RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
            function_id=function_id,
        )
        restored = RequirementNode.from_dict(node.to_dict())
        assert restored.function_id == function_id


# =============================================================================
# Manual test cases for edge cases
# =============================================================================


# =============================================================================
# Tests for related_concepts field on RequirementNode
# =============================================================================


class TestRequirementNodeRelatedConcepts:
    """Tests for related_concepts field on RequirementNode."""

    def test_related_concepts_stored_on_creation(self):
        """Given related_concepts provided, when node created, then stored."""
        from planning_pipeline.models import RequirementNode

        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
            related_concepts=["auth", "jwt", "session"],
        )
        assert node.related_concepts == ["auth", "jwt", "session"]

    def test_related_concepts_default_empty_list(self):
        """Given no related_concepts, when node created, then empty list."""
        from planning_pipeline.models import RequirementNode

        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
        )
        assert node.related_concepts == []

    def test_related_concepts_serialized_to_dict(self):
        """Given node with related_concepts, when to_dict, then in output."""
        from planning_pipeline.models import RequirementNode

        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
            related_concepts=["database", "caching"],
        )
        result = node.to_dict()
        assert result["related_concepts"] == ["database", "caching"]

    def test_related_concepts_deserialized_from_dict(self):
        """Given dict with related_concepts, when from_dict, then restored."""
        from planning_pipeline.models import RequirementNode

        data = {
            "id": "REQ_001",
            "description": "Test requirement",
            "type": "parent",
            "parent_id": None,
            "children": [],
            "acceptance_criteria": [],
            "implementation": None,
            "testable_properties": [],
            "related_concepts": ["api", "rest"],
        }
        node = RequirementNode.from_dict(data)
        assert node.related_concepts == ["api", "rest"]

    @given(st.lists(st.text(min_size=1, max_size=50), max_size=10))
    def test_related_concepts_roundtrip_property(self, concepts: list[str]):
        """Property: related_concepts survives serialization roundtrip."""
        from planning_pipeline.models import RequirementNode

        node = RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
            related_concepts=concepts,
        )
        restored = RequirementNode.from_dict(node.to_dict())
        assert restored.related_concepts == concepts


# =============================================================================
# Tests for category field on RequirementNode
# =============================================================================


class TestRequirementNodeCategory:
    """Tests for category field on RequirementNode."""

    def test_category_stored_on_creation(self):
        """Given category provided, when node created, then stored."""
        from planning_pipeline.models import RequirementNode

        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
            category="security",
        )
        assert node.category == "security"

    def test_category_default_functional(self):
        """Given no category, when node created, then defaults to functional."""
        from planning_pipeline.models import RequirementNode

        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
        )
        assert node.category == "functional"

    def test_category_serialized_to_dict(self):
        """Given node with category, when to_dict, then in output."""
        from planning_pipeline.models import RequirementNode

        node = RequirementNode(
            id="REQ_001",
            description="Test requirement",
            type="parent",
            category="performance",
        )
        result = node.to_dict()
        assert result["category"] == "performance"

    def test_category_deserialized_from_dict(self):
        """Given dict with category, when from_dict, then restored."""
        from planning_pipeline.models import RequirementNode

        data = {
            "id": "REQ_001",
            "description": "Test requirement",
            "type": "parent",
            "category": "usability",
            "parent_id": None,
            "children": [],
            "acceptance_criteria": [],
            "implementation": None,
            "testable_properties": [],
        }
        node = RequirementNode.from_dict(data)
        assert node.category == "usability"

    def test_invalid_category_raises_error(self):
        """Given invalid category, when node created, then ValueError."""
        from planning_pipeline.models import RequirementNode

        with pytest.raises(ValueError, match="Invalid category"):
            RequirementNode(
                id="REQ_001",
                description="Test requirement",
                type="parent",
                category="invalid_category",
            )

    @given(st.sampled_from(list(VALID_CATEGORIES)))
    def test_valid_categories_accepted(self, category: str):
        """Property: all valid categories are accepted."""
        from planning_pipeline.models import RequirementNode

        node = RequirementNode(
            id="REQ_001",
            description="Test",
            type="parent",
            category=category,
        )
        assert node.category == category


# =============================================================================
# Manual test cases for edge cases
# =============================================================================


# =============================================================================
# Tests for arbitrary depth ID generation
# =============================================================================


class TestArbitraryDepthIds:
    """Tests for arbitrary depth ID generation."""

    def test_four_level_hierarchy(self):
        """Given 4-level nesting, when add_child used, then IDs correct."""
        from planning_pipeline.models import RequirementNode, RequirementHierarchy

        hierarchy = RequirementHierarchy()

        # Level 1: REQ_001
        parent = RequirementNode(id="REQ_001", description="Parent", type="parent")
        hierarchy.add_requirement(parent)

        # Level 2: REQ_001.1
        sub = RequirementNode(id="REQ_001.1", description="Sub", type="sub_process")
        hierarchy.add_child("REQ_001", sub)

        # Level 3: REQ_001.1.1
        impl = RequirementNode(id="REQ_001.1.1", description="Impl", type="implementation")
        hierarchy.add_child("REQ_001.1", impl)

        # Level 4: REQ_001.1.1.1
        detail = RequirementNode(id="REQ_001.1.1.1", description="Detail", type="implementation")
        hierarchy.add_child("REQ_001.1.1", detail)

        # Assert structure
        assert hierarchy.get_by_id("REQ_001.1.1.1") is not None
        assert hierarchy.get_by_id("REQ_001.1.1.1").parent_id == "REQ_001.1.1"

    def test_next_child_id_generation(self):
        """Given parent with children, when next ID generated, then increments."""
        from planning_pipeline.models import RequirementNode

        parent = RequirementNode(id="REQ_001.2.3", description="Parent", type="implementation")

        # Simulate adding children
        next_id_1 = f"{parent.id}.1"  # REQ_001.2.3.1
        next_id_2 = f"{parent.id}.2"  # REQ_001.2.3.2

        assert next_id_1 == "REQ_001.2.3.1"
        assert next_id_2 == "REQ_001.2.3.2"

    @given(st.integers(min_value=1, max_value=10))
    def test_arbitrary_depth_property(self, depth: int):
        """Property: hierarchy supports arbitrary depth."""
        from planning_pipeline.models import RequirementNode, RequirementHierarchy

        hierarchy = RequirementHierarchy()

        # Build nested hierarchy to given depth
        current_id = "REQ_001"
        parent = RequirementNode(id=current_id, description="Root", type="parent")
        hierarchy.add_requirement(parent)

        for i in range(1, depth):
            child_id = f"{current_id}.{i}"
            child = RequirementNode(
                id=child_id,
                description=f"Level {i+1}",
                type="implementation",
            )
            hierarchy.add_child(current_id, child)
            current_id = child_id

        # Assert deepest node is findable
        assert hierarchy.get_by_id(current_id) is not None

    def test_get_depth_method(self):
        """Given node ID, when get_depth called, then correct depth returned."""
        # REQ_001 -> depth 1
        # REQ_001.1 -> depth 2
        # REQ_001.1.3 -> depth 3
        # REQ_001.1.3.2 -> depth 4

        def get_depth(node_id: str) -> int:
            """Calculate depth from ID pattern."""
            if not node_id.startswith("REQ_"):
                return 0
            parts = node_id.split(".")
            return len(parts)

        assert get_depth("REQ_001") == 1
        assert get_depth("REQ_001.1") == 2
        assert get_depth("REQ_001.1.3") == 3
        assert get_depth("REQ_001.1.3.2") == 4

    def test_next_child_id_method_on_hierarchy(self):
        """Test that RequirementHierarchy.next_child_id generates correct IDs."""
        from planning_pipeline.models import RequirementNode, RequirementHierarchy

        hierarchy = RequirementHierarchy()

        # Level 1: REQ_001
        parent = RequirementNode(id="REQ_001", description="Parent", type="parent")
        hierarchy.add_requirement(parent)

        # Generate next child ID
        next_id = hierarchy.next_child_id("REQ_001")
        assert next_id == "REQ_001.1"

        # Add child with that ID
        child1 = RequirementNode(id=next_id, description="First child", type="sub_process")
        hierarchy.add_child("REQ_001", child1)

        # Generate next child ID - should be .2
        next_id = hierarchy.next_child_id("REQ_001")
        assert next_id == "REQ_001.2"

        # Add another child
        child2 = RequirementNode(id=next_id, description="Second child", type="sub_process")
        hierarchy.add_child("REQ_001", child2)

        # Test nested depth
        next_id = hierarchy.next_child_id("REQ_001.1")
        assert next_id == "REQ_001.1.1"

    def test_next_child_id_raises_for_missing_parent(self):
        """Given missing parent, when next_child_id called, then ValueError."""
        from planning_pipeline.models import RequirementHierarchy

        hierarchy = RequirementHierarchy()

        with pytest.raises(ValueError, match="Parent REQ_999 not found"):
            hierarchy.next_child_id("REQ_999")


class TestManualEdgeCases:
    """Manual tests for specific edge cases."""

    def test_node_with_all_fields_populated(self):
        """Test node with all optional fields populated."""
        from planning_pipeline.models import (
            RequirementNode,
            ImplementationComponents,
            TestableProperty,
        )

        impl = ImplementationComponents(
            frontend=["LoginForm", "AuthContext"],
            backend=["AuthService.login", "UserRepository"],
            middleware=["validateToken"],
            shared=["User", "Session"],
        )

        prop = TestableProperty(
            criterion="Must validate email format",
            property_type="invariant",
            hypothesis_strategy="st.emails()",
            test_skeleton="@given(st.emails())\ndef test_email_valid(email): ...",
        )

        node = RequirementNode(
            id="REQ_001.1",
            description="User login implementation",
            type="implementation",
            parent_id="REQ_001",
            children=[],
            acceptance_criteria=["Email must be valid", "Password min 8 chars"],
            implementation=impl,
            testable_properties=[prop],
        )

        as_dict = node.to_dict()
        restored = RequirementNode.from_dict(as_dict)

        assert restored.implementation is not None
        assert len(restored.implementation.frontend) == 2
        assert len(restored.testable_properties) == 1
        assert restored.testable_properties[0].criterion == "Must validate email format"

    def test_hierarchy_with_nested_children(self):
        """Test hierarchy with multiple levels of nesting."""
        from planning_pipeline.models import RequirementNode, RequirementHierarchy

        # Build 3-tier hierarchy
        impl_node = RequirementNode(
            id="REQ_001.1.1",
            description="Actual implementation",
            type="implementation",
            parent_id="REQ_001.1",
        )

        sub_process = RequirementNode(
            id="REQ_001.1",
            description="Sub-process",
            type="sub_process",
            parent_id="REQ_001",
            children=[impl_node],
        )

        parent = RequirementNode(
            id="REQ_001",
            description="Parent requirement",
            type="parent",
            children=[sub_process],
        )

        hierarchy = RequirementHierarchy(requirements=[parent])

        as_dict = hierarchy.to_dict()
        restored = RequirementHierarchy.from_dict(as_dict)

        # Verify structure preserved
        assert len(restored.requirements) == 1
        assert len(restored.requirements[0].children) == 1
        assert len(restored.requirements[0].children[0].children) == 1
        assert restored.requirements[0].children[0].children[0].id == "REQ_001.1.1"

    def test_hierarchy_metadata(self):
        """Test that metadata is preserved."""
        from planning_pipeline.models import RequirementNode, RequirementHierarchy

        node = RequirementNode(id="REQ_001", description="Test", type="parent")
        hierarchy = RequirementHierarchy(
            requirements=[node],
            metadata={
                "source_research": "path/to/research.md",
                "created_at": "2026-01-02T10:00:00Z",
                "version": "1.0",
            },
        )

        as_dict = hierarchy.to_dict()
        restored = RequirementHierarchy.from_dict(as_dict)

        assert restored.metadata["source_research"] == "path/to/research.md"
        assert restored.metadata["version"] == "1.0"
