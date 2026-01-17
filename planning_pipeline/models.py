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

# Valid edge case priority levels
VALID_EDGE_CASE_PRIORITIES = frozenset(["high", "medium", "low"])

# Valid categories for requirements
VALID_CATEGORIES = frozenset([
    "functional", "non_functional", "security",
    "performance", "usability", "integration"
])


@dataclass
class DesignContracts:
    """Design-by-contract specifications for a requirement.

    Encapsulates preconditions, postconditions, and invariants extracted
    during decomposition to enable design-by-contract TDD planning.

    Attributes:
        preconditions: Conditions that must be true before execution
        postconditions: Conditions guaranteed after execution
        invariants: Conditions that remain true throughout execution
    """

    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[str]]:
        """Serialize to dictionary."""
        return {
            "preconditions": self.preconditions,
            "postconditions": self.postconditions,
            "invariants": self.invariants,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DesignContracts":
        """Deserialize from dictionary."""
        return cls(
            preconditions=data.get("preconditions", []),
            postconditions=data.get("postconditions", []),
            invariants=data.get("invariants", []),
        )

    def has_contracts(self) -> bool:
        """Check if any contracts are defined."""
        return bool(self.preconditions or self.postconditions or self.invariants)


@dataclass
class EdgeCase:
    """Edge case derived from preconditions for test coverage.

    Represents a boundary condition or error scenario to test.

    Attributes:
        description: Clear description of the edge case scenario
        precondition_id: Reference to source precondition (optional)
        expected_error_type: Type of error expected (e.g., 'ValueError')
        expected_error_message: Error message pattern to match
        priority: Risk/impact priority (high, medium, low)
        is_async: Whether this is an async failure mode
    """

    description: str
    precondition_id: Optional[str] = None
    expected_error_type: Optional[str] = None
    expected_error_message: Optional[str] = None
    priority: str = "medium"
    is_async: bool = False

    def __post_init__(self):
        """Validate edge case after initialization."""
        if self.priority not in VALID_EDGE_CASE_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{self.priority}'. "
                f"Must be one of: {', '.join(sorted(VALID_EDGE_CASE_PRIORITIES))}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "description": self.description,
            "precondition_id": self.precondition_id,
            "expected_error_type": self.expected_error_type,
            "expected_error_message": self.expected_error_message,
            "priority": self.priority,
            "is_async": self.is_async,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EdgeCase":
        """Deserialize from dictionary."""
        return cls(
            description=data["description"],
            precondition_id=data.get("precondition_id"),
            expected_error_type=data.get("expected_error_type"),
            expected_error_message=data.get("expected_error_message"),
            priority=data.get("priority", "medium"),
            is_async=data.get("is_async", False),
        )


@dataclass
class GherkinScenario:
    """Gherkin format test specification for BDD alignment.

    Represents a complete Gherkin scenario with Given/When/Then steps.

    Attributes:
        name: Scenario name
        acceptance_criteria_id: Tag for traceability (e.g., '@AC_001')
        given_steps: List of Given/And precondition steps
        when_steps: List of When action steps
        then_steps: List of Then/And assertion steps
        is_outline: Whether this is a Scenario Outline with examples
        examples: Examples table for parameterized tests (if outline)
    """

    name: str
    acceptance_criteria_id: Optional[str] = None
    given_steps: list[str] = field(default_factory=list)
    when_steps: list[str] = field(default_factory=list)
    then_steps: list[str] = field(default_factory=list)
    is_outline: bool = False
    examples: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "acceptance_criteria_id": self.acceptance_criteria_id,
            "given_steps": self.given_steps,
            "when_steps": self.when_steps,
            "then_steps": self.then_steps,
            "is_outline": self.is_outline,
            "examples": self.examples,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GherkinScenario":
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            acceptance_criteria_id=data.get("acceptance_criteria_id"),
            given_steps=data.get("given_steps", []),
            when_steps=data.get("when_steps", []),
            then_steps=data.get("then_steps", []),
            is_outline=data.get("is_outline", False),
            examples=data.get("examples", []),
        )

    def to_gherkin(self) -> str:
        """Convert to Gherkin format string."""
        lines = []

        # Add tag if present
        if self.acceptance_criteria_id:
            lines.append(f"@{self.acceptance_criteria_id}")

        # Scenario type
        scenario_type = "Scenario Outline" if self.is_outline else "Scenario"
        lines.append(f"{scenario_type}: {self.name}")

        # Given steps
        for i, step in enumerate(self.given_steps):
            keyword = "Given" if i == 0 else "And"
            lines.append(f"  {keyword} {step}")

        # When steps
        for i, step in enumerate(self.when_steps):
            keyword = "When" if i == 0 else "And"
            lines.append(f"  {keyword} {step}")

        # Then steps
        for i, step in enumerate(self.then_steps):
            keyword = "Then" if i == 0 else "And"
            lines.append(f"  {keyword} {step}")

        # Examples table for outlines
        if self.is_outline and self.examples:
            lines.append("")
            lines.append("  Examples:")
            if self.examples:
                headers = list(self.examples[0].keys())
                lines.append("    | " + " | ".join(headers) + " |")
                for example in self.examples:
                    values = [str(example.get(h, "")) for h in headers]
                    lines.append("    | " + " | ".join(values) + " |")

        return "\n".join(lines)


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
    function_id: Optional[str] = None
    related_concepts: list[str] = field(default_factory=list)
    category: str = "functional"
    contracts: Optional[DesignContracts] = None
    edge_cases: list[EdgeCase] = field(default_factory=list)
    gherkin_scenarios: list[GherkinScenario] = field(default_factory=list)

    def __post_init__(self):
        """Validate requirement node after initialization."""
        if self.type not in VALID_REQUIREMENT_TYPES:
            raise ValueError(
                f"Invalid type '{self.type}'. Must be one of: {', '.join(VALID_REQUIREMENT_TYPES)}"
            )

        if not self.description or not self.description.strip():
            raise ValueError("Requirement description must not be empty")

        if self.category not in VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category '{self.category}'. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
            )

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
            "function_id": self.function_id,
            "related_concepts": self.related_concepts,
            "category": self.category,
            "contracts": self.contracts.to_dict() if self.contracts else None,
            "edge_cases": [ec.to_dict() for ec in self.edge_cases],
            "gherkin_scenarios": [gs.to_dict() for gs in self.gherkin_scenarios],
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

        # Reconstruct design contracts
        contracts = None
        if data.get("contracts"):
            contracts = DesignContracts.from_dict(data["contracts"])

        # Reconstruct edge cases
        edge_cases = [
            EdgeCase.from_dict(ec) for ec in data.get("edge_cases", [])
        ]

        # Reconstruct gherkin scenarios
        gherkin_scenarios = [
            GherkinScenario.from_dict(gs) for gs in data.get("gherkin_scenarios", [])
        ]

        return cls(
            id=data["id"],
            description=data["description"],
            type=data["type"],
            parent_id=data.get("parent_id"),
            children=children,
            acceptance_criteria=data.get("acceptance_criteria", []),
            implementation=impl,
            testable_properties=props,
            function_id=data.get("function_id"),
            related_concepts=data.get("related_concepts", []),
            category=data.get("category", "functional"),
            contracts=contracts,
            edge_cases=edge_cases,
            gherkin_scenarios=gherkin_scenarios,
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

    def next_child_id(self, parent_id: str) -> str:
        """Generate the next child ID for a parent.

        Creates IDs following the pattern: parent_id.N where N is the next
        available child number (1-indexed).

        Args:
            parent_id: ID of the parent node

        Returns:
            Next child ID (e.g., "REQ_001.1" for first child of REQ_001)

        Raises:
            ValueError: If parent_id is not found in the hierarchy
        """
        parent = self.get_by_id(parent_id)
        if parent is None:
            raise ValueError(f"Parent {parent_id} not found")
        next_num = len(parent.children) + 1
        return f"{parent_id}.{next_num}"

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
