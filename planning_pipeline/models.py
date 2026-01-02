"""Core data models for requirement hierarchy and decomposition.

This module provides dataclasses for representing requirements in a hierarchical
structure with support for:
- 3-tier hierarchy: parent -> sub_process -> implementation
- Implementation component breakdown (frontend, backend, middleware, shared)
- Testable properties derived from acceptance criteria
- JSON serialization/deserialization
"""

from dataclasses import dataclass, field
from typing import Any, Optional


# Valid requirement types for the 3-tier hierarchy
VALID_REQUIREMENT_TYPES = frozenset(["parent", "sub_process", "implementation"])

# Valid property types for testable properties
VALID_PROPERTY_TYPES = frozenset(["invariant", "round_trip", "idempotence", "oracle"])


@dataclass
class ImplementationComponents:
    """Component breakdown for implementation requirements.

    Categorizes implementation work into architectural layers:
    - frontend: UI components, pages, forms
    - backend: API endpoints, services, repositories
    - middleware: Auth, validation, interceptors
    - shared: Data models, utilities, types

    Attributes:
        frontend: List of frontend components (e.g., ["LoginForm", "AuthContext"])
        backend: List of backend components (e.g., ["AuthService.login"])
        middleware: List of middleware components (e.g., ["validateToken"])
        shared: List of shared components (e.g., ["User", "Session"])
    """

    frontend: list[str] = field(default_factory=list)
    backend: list[str] = field(default_factory=list)
    middleware: list[str] = field(default_factory=list)
    shared: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[str]]:
        """Serialize to dictionary."""
        return {
            "frontend": self.frontend,
            "backend": self.backend,
            "middleware": self.middleware,
            "shared": self.shared,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImplementationComponents":
        """Deserialize from dictionary."""
        return cls(
            frontend=data.get("frontend", []),
            backend=data.get("backend", []),
            middleware=data.get("middleware", []),
            shared=data.get("shared", []),
        )


@dataclass
class TestableProperty:
    """A testable property derived from an acceptance criterion.

    Maps acceptance criteria to property-based tests using Hypothesis strategies.

    Attributes:
        criterion: Original acceptance criterion text
        property_type: Type of property test (invariant, round_trip, idempotence, oracle)
        hypothesis_strategy: Hypothesis strategy string (e.g., "st.text(min_size=1)")
        test_skeleton: Generated test code skeleton
    """

    criterion: str
    property_type: str
    hypothesis_strategy: str
    test_skeleton: str

    def to_dict(self) -> dict[str, str]:
        """Serialize to dictionary."""
        return {
            "criterion": self.criterion,
            "property_type": self.property_type,
            "hypothesis_strategy": self.hypothesis_strategy,
            "test_skeleton": self.test_skeleton,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TestableProperty":
        """Deserialize from dictionary."""
        return cls(
            criterion=data["criterion"],
            property_type=data["property_type"],
            hypothesis_strategy=data["hypothesis_strategy"],
            test_skeleton=data["test_skeleton"],
        )


@dataclass
class RequirementNode:
    """Single node in the requirement hierarchy.

    Represents a requirement at any level of the 3-tier hierarchy:
    - parent: Top-level behavioral requirement
    - sub_process: Breakdown of parent into sub-tasks
    - implementation: Concrete implementation details with components

    ID Format: REQ_XXX or REQ_XXX.Y or REQ_XXX.Y.Z (max 3 levels)

    Attributes:
        id: Unique requirement ID (format: REQ_\\d{3}(\\.\\d+)*)
        description: Human-readable description (must be non-empty)
        type: Requirement type (parent, sub_process, implementation)
        parent_id: ID of parent node (None for root nodes)
        children: List of child RequirementNode objects
        acceptance_criteria: List of testable acceptance criteria
        implementation: Component breakdown (for implementation nodes)
        testable_properties: Derived property-based test specifications

    Raises:
        ValueError: If type is invalid or description is empty
    """

    id: str
    description: str
    type: str
    parent_id: Optional[str] = None
    children: list["RequirementNode"] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    implementation: Optional[ImplementationComponents] = None
    testable_properties: list[TestableProperty] = field(default_factory=list)

    def __post_init__(self):
        """Validate requirement node after initialization."""
        if self.type not in VALID_REQUIREMENT_TYPES:
            raise ValueError(
                f"Invalid type '{self.type}'. Must be one of: {', '.join(VALID_REQUIREMENT_TYPES)}"
            )

        if not self.description or not self.description.strip():
            raise ValueError("Requirement description must not be empty")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary with recursive children."""
        return {
            "id": self.id,
            "description": self.description,
            "type": self.type,
            "parent_id": self.parent_id,
            "children": [child.to_dict() for child in self.children],
            "acceptance_criteria": self.acceptance_criteria,
            "implementation": self.implementation.to_dict() if self.implementation else None,
            "testable_properties": [prop.to_dict() for prop in self.testable_properties],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RequirementNode":
        """Deserialize from dictionary with recursive children reconstruction."""
        # Reconstruct implementation components
        impl = None
        if data.get("implementation"):
            impl = ImplementationComponents.from_dict(data["implementation"])

        # Reconstruct testable properties
        props = [
            TestableProperty.from_dict(p) for p in data.get("testable_properties", [])
        ]

        # Reconstruct children recursively
        children = [cls.from_dict(c) for c in data.get("children", [])]

        return cls(
            id=data["id"],
            description=data["description"],
            type=data["type"],
            parent_id=data.get("parent_id"),
            children=children,
            acceptance_criteria=data.get("acceptance_criteria", []),
            implementation=impl,
            testable_properties=props,
        )


@dataclass
class RequirementHierarchy:
    """Complete requirement hierarchy from decomposition.

    Container for multiple top-level requirements with methods for
    adding, querying, and serializing the hierarchy.

    Attributes:
        requirements: List of top-level RequirementNode objects
        metadata: Additional metadata (source_research, created_at, version)
    """

    requirements: list[RequirementNode] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_requirement(self, node: RequirementNode) -> None:
        """Add a top-level requirement to the hierarchy.

        Args:
            node: RequirementNode to add as a top-level requirement
        """
        self.requirements.append(node)

    def add_child(self, parent_id: str, child: RequirementNode) -> bool:
        """Add a child node to an existing parent.

        Sets the child's parent_id and adds it to the parent's children list.

        Args:
            parent_id: ID of the parent node
            child: RequirementNode to add as a child

        Returns:
            True if parent was found and child was added, False otherwise
        """
        parent = self.get_by_id(parent_id)
        if parent is None:
            return False

        child.parent_id = parent_id
        parent.children.append(child)
        return True

    def get_by_id(self, req_id: str) -> Optional[RequirementNode]:
        """Find a requirement by ID at any level of the hierarchy.

        Args:
            req_id: Requirement ID to search for

        Returns:
            RequirementNode if found, None otherwise
        """

        def search(nodes: list[RequirementNode]) -> Optional[RequirementNode]:
            for node in nodes:
                if node.id == req_id:
                    return node
                found = search(node.children)
                if found:
                    return found
            return None

        return search(self.requirements)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "requirements": [req.to_dict() for req in self.requirements],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RequirementHierarchy":
        """Deserialize from dictionary."""
        requirements = [
            RequirementNode.from_dict(req) for req in data.get("requirements", [])
        ]
        return cls(
            requirements=requirements,
            metadata=data.get("metadata", {}),
        )
