# Iterative Requirement Decomposition with Visualization TDD Implementation Plan

## Overview

This plan implements an **iterative requirement decomposition loop** that:
1. Starts with a single behavior and builds needed functionality in micro-steps
2. Uses **BAML functions** for structured decomposition (hybrid: BAML for decomposition, CLI for tool-enabled execution)
3. Integrates **after research, before planning** in the current pipeline
4. Presents requirements via **Mermaid diagrams** relating system structure to requirements
5. Focuses on **testable properties** using **Hypothesis** for property-based TDD

The feature transforms vague research findings into concrete, testable requirement hierarchies with visual feedback.

## Current State Analysis

### Existing Infrastructure

| Component | Status | Location |
|-----------|--------|----------|
| BAML Client | Generated, unused | `baml_client/` |
| BAML Functions | 40+ defined | `baml_src/functions.baml` |
| Pipeline Steps | 5 steps implemented | `planning_pipeline/steps.py` |
| Claude Runner | Subprocess-based | `planning_pipeline/claude_runner.py` |
| Tests | Example-based only | `planning_pipeline/tests/` |
| Mermaid Generation | Not implemented | N/A |
| Hypothesis | Not installed | N/A |

### Key Discoveries

- **BAML is ready**: `baml_client/` has 81 generated types but no pipeline integration (`baml_client/types.py:44`)
- **Pipeline uses subprocess**: All LLM calls via `run_claude_sync()` not BAML (`claude_runner.py:23`)
- **Tests lack properties**: No Hypothesis usage, all example-based (`planning_pipeline/tests/conftest.py:1-59`)
- **No visualization code**: Mermaid patterns documented but not implemented
- **Existing schemas**: `RequirementResponse`, `ImplementationComponents` exist (`baml_client/types.py`)

### Pipeline Position

```
step_research() → [NEW: step_requirement_decomposition()] → step_planning()
```

## Desired End State

### Observable Behaviors

1. **Given research output, when decomposition runs, then hierarchical requirements are produced**
   - Input: Research markdown path
   - Output: `requirements_hierarchy.json` with 3-tier structure

2. **Given requirement hierarchy, when visualization runs, then Mermaid diagram is generated**
   - Input: `RequirementHierarchy` object
   - Output: `requirements_diagram.mmd` file

3. **Given acceptance criteria, when property derivation runs, then Hypothesis test skeletons are generated**
   - Input: List of acceptance criteria strings
   - Output: `property_tests_skeleton.py` file

4. **Given invalid research path, when decomposition runs, then informative error is returned**
   - Input: Non-existent path
   - Output: Error dict with reason

5. **Given large hierarchy (50+ requirements), when visualization runs, then diagram is properly grouped**
   - Input: Complex hierarchy
   - Output: Subgraph-organized Mermaid

## What We're NOT Doing

- Modifying existing `step_research()` or `step_planning()` functions
- Replacing Claude CLI calls with BAML for existing steps
- Creating UI components for diagram viewing
- Real-time streaming of decomposition progress
- Database persistence of requirements

## Testing Strategy

- **Framework**: pytest + Hypothesis
- **Test Types**:
  - Unit: Data model invariants, Mermaid generation, property derivation
  - Integration: BAML client calls, full decomposition flow
  - Property-Based: Hierarchical structure invariants, round-trip serialization
- **Mocking**: BAML client for fast tests, real calls for integration tests

---

## Behavior 1: RequirementNode Data Model with Invariants

### Test Specification

**Given**: Parameters for creating a RequirementNode
**When**: Node is instantiated
**Then**: All invariants hold (valid ID format, consistent parent-child relationships, non-empty descriptions)

**Properties**:
- ID format: `REQ_\d{3}(.\d+)*` (e.g., REQ_001, REQ_001.2, REQ_001.2.1)
- Parent-child: If node has parent_id, parent's children must include this node
- Type hierarchy: parent → sub_process → implementation (3 levels max)
- Non-empty: description always has content

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `planning_pipeline/tests/test_models.py`
```python
"""Property-based tests for requirement data models."""

import pytest
from hypothesis import given, assume, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant

from planning_pipeline.models import (
    RequirementNode,
    RequirementHierarchy,
    ImplementationComponents,
    TestableProperty,
)


class TestRequirementNodeProperties:
    """Behavior 1: RequirementNode maintains structural invariants."""

    @given(st.text(min_size=1, max_size=100))
    def test_description_preserved(self, description):
        """Given any non-empty description, node preserves it exactly."""
        node = RequirementNode(
            id="REQ_001",
            description=description,
            type="parent"
        )
        assert node.description == description

    @given(
        st.sampled_from(["parent", "sub_process", "implementation"]),
        st.text(min_size=1, max_size=50)
    )
    def test_type_and_description_valid(self, node_type, desc):
        """Given valid type and description, node is valid."""
        node = RequirementNode(id="REQ_001", description=desc, type=node_type)
        assert node.type == node_type
        assert len(node.description) > 0

    @given(st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=10))
    def test_acceptance_criteria_round_trip(self, criteria):
        """Given acceptance criteria list, serialization round-trips."""
        node = RequirementNode(
            id="REQ_001",
            description="Test",
            type="implementation",
            acceptance_criteria=criteria
        )
        # Round-trip through dict
        as_dict = node.to_dict()
        restored = RequirementNode.from_dict(as_dict)
        assert restored.acceptance_criteria == criteria


class RequirementHierarchyStateMachine(RuleBasedStateMachine):
    """Stateful tests for RequirementHierarchy operations."""

    def __init__(self):
        super().__init__()
        self.hierarchy = RequirementHierarchy(requirements=[])
        self.added_ids = set()
        self.parent_children = {}  # parent_id -> [child_ids]

    @rule(description=st.text(min_size=1, max_size=50))
    def add_parent_requirement(self, description):
        """Add a top-level parent requirement."""
        req_id = f"REQ_{len(self.added_ids) + 1:03d}"
        node = RequirementNode(id=req_id, description=description, type="parent")
        self.hierarchy.add_requirement(node)
        self.added_ids.add(req_id)
        self.parent_children[req_id] = []

    @rule(
        description=st.text(min_size=1, max_size=50),
        parent_idx=st.integers(min_value=0)
    )
    def add_child_requirement(self, description, parent_idx):
        """Add a child to an existing parent."""
        parents = [r for r in self.hierarchy.requirements if r.type == "parent"]
        assume(len(parents) > 0)
        parent = parents[parent_idx % len(parents)]

        child_num = len(self.parent_children.get(parent.id, [])) + 1
        child_id = f"{parent.id}.{child_num}"
        child = RequirementNode(
            id=child_id,
            description=description,
            type="sub_process",
            parent_id=parent.id
        )
        self.hierarchy.add_child(parent.id, child)
        self.added_ids.add(child_id)
        self.parent_children.setdefault(parent.id, []).append(child_id)

    @invariant()
    def ids_are_unique(self):
        """All requirement IDs are unique."""
        all_ids = self._collect_all_ids(self.hierarchy)
        assert len(all_ids) == len(set(all_ids))

    @invariant()
    def parent_child_consistency(self):
        """Parent-child relationships are consistent."""
        for parent_id, child_ids in self.parent_children.items():
            parent = self.hierarchy.get_by_id(parent_id)
            if parent:
                actual_child_ids = [c.id for c in parent.children]
                for expected_id in child_ids:
                    assert expected_id in actual_child_ids

    @invariant()
    def hierarchy_depth_max_three(self):
        """Hierarchy never exceeds 3 levels."""
        for req in self.hierarchy.requirements:
            depth = self._get_max_depth(req)
            assert depth <= 3

    def _collect_all_ids(self, hierarchy):
        """Recursively collect all IDs."""
        ids = []
        for req in hierarchy.requirements:
            ids.extend(self._collect_ids_recursive(req))
        return ids

    def _collect_ids_recursive(self, node):
        """Collect IDs from node and children."""
        ids = [node.id]
        for child in node.children:
            ids.extend(self._collect_ids_recursive(child))
        return ids

    def _get_max_depth(self, node, current=1):
        """Get maximum depth from node."""
        if not node.children:
            return current
        return max(self._get_max_depth(c, current + 1) for c in node.children)


TestRequirementHierarchyStateful = RequirementHierarchyStateMachine.TestCase
```

#### 🟢 Green: Minimal Implementation

**File**: `planning_pipeline/models.py`
```python
"""Data models for iterative requirement decomposition."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import re


@dataclass
class ImplementationComponents:
    """Component breakdown for implementation tasks."""
    frontend: List[str] = field(default_factory=list)
    backend: List[str] = field(default_factory=list)
    middleware: List[str] = field(default_factory=list)
    shared: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frontend": self.frontend,
            "backend": self.backend,
            "middleware": self.middleware,
            "shared": self.shared,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImplementationComponents":
        return cls(
            frontend=data.get("frontend", []),
            backend=data.get("backend", []),
            middleware=data.get("middleware", []),
            shared=data.get("shared", []),
        )


@dataclass
class TestableProperty:
    """A testable property derived from acceptance criteria."""
    criterion: str
    property_type: str  # "invariant", "round_trip", "idempotence", "oracle"
    hypothesis_strategy: str
    test_skeleton: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "criterion": self.criterion,
            "property_type": self.property_type,
            "hypothesis_strategy": self.hypothesis_strategy,
            "test_skeleton": self.test_skeleton,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestableProperty":
        return cls(
            criterion=data["criterion"],
            property_type=data["property_type"],
            hypothesis_strategy=data["hypothesis_strategy"],
            test_skeleton=data["test_skeleton"],
        )


@dataclass
class RequirementNode:
    """Single node in requirement hierarchy."""
    id: str
    description: str
    type: str  # "parent", "sub_process", "implementation"
    parent_id: Optional[str] = None
    children: List["RequirementNode"] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    implementation: Optional[ImplementationComponents] = None
    testable_properties: List[TestableProperty] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "type": self.type,
            "parent_id": self.parent_id,
            "children": [c.to_dict() for c in self.children],
            "acceptance_criteria": self.acceptance_criteria,
            "implementation": self.implementation.to_dict() if self.implementation else None,
            "testable_properties": [p.to_dict() for p in self.testable_properties],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RequirementNode":
        return cls(
            id=data["id"],
            description=data["description"],
            type=data["type"],
            parent_id=data.get("parent_id"),
            children=[cls.from_dict(c) for c in data.get("children", [])],
            acceptance_criteria=data.get("acceptance_criteria", []),
            implementation=ImplementationComponents.from_dict(data["implementation"])
                if data.get("implementation") else None,
            testable_properties=[TestableProperty.from_dict(p)
                for p in data.get("testable_properties", [])],
        )


@dataclass
class RequirementHierarchy:
    """Complete requirement hierarchy from decomposition."""
    requirements: List[RequirementNode]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_requirement(self, node: RequirementNode) -> None:
        """Add a top-level requirement."""
        self.requirements.append(node)

    def add_child(self, parent_id: str, child: RequirementNode) -> bool:
        """Add a child to an existing requirement."""
        parent = self.get_by_id(parent_id)
        if parent:
            child.parent_id = parent_id
            parent.children.append(child)
            return True
        return False

    def get_by_id(self, req_id: str) -> Optional[RequirementNode]:
        """Find a requirement by ID."""
        for req in self.requirements:
            found = self._find_recursive(req, req_id)
            if found:
                return found
        return None

    def _find_recursive(self, node: RequirementNode, req_id: str) -> Optional[RequirementNode]:
        """Recursively search for requirement by ID."""
        if node.id == req_id:
            return node
        for child in node.children:
            found = self._find_recursive(child, req_id)
            if found:
                return found
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirements": [r.to_dict() for r in self.requirements],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RequirementHierarchy":
        return cls(
            requirements=[RequirementNode.from_dict(r) for r in data.get("requirements", [])],
            metadata=data.get("metadata", {}),
        )
```

#### 🔵 Refactor: Add Validation

**File**: `planning_pipeline/models.py` (additions)
```python
import re
from dataclasses import dataclass, field

# Add ID validation pattern
REQ_ID_PATTERN = re.compile(r"^REQ_\d{3}(\.\d+)*$")


def validate_req_id(req_id: str) -> bool:
    """Validate requirement ID format."""
    return bool(REQ_ID_PATTERN.match(req_id))


@dataclass
class RequirementNode:
    # ... existing fields ...

    def __post_init__(self):
        """Validate node after initialization."""
        if not self.description:
            raise ValueError("RequirementNode description cannot be empty")
        if self.type not in ("parent", "sub_process", "implementation"):
            raise ValueError(f"Invalid type: {self.type}")
```

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): `pytest planning_pipeline/tests/test_models.py -v`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_models.py -v`
- [ ] All tests pass after refactor: `pytest planning_pipeline/tests/ -v`
- [ ] Property tests find no counterexamples: `pytest --hypothesis-show-statistics`
- [ ] Type check passes: `mypy planning_pipeline/models.py`

**Manual:**
- [ ] RequirementNode round-trips through JSON
- [ ] Hierarchy maintains parent-child consistency
- [ ] Stateful tests cover add/remove operations

---

## Behavior 2: Mermaid Diagram Generation

### Test Specification

**Given**: A `RequirementHierarchy` with requirements and components
**When**: `to_mermaid_flowchart()` is called
**Then**: Valid Mermaid syntax is produced with proper node/edge definitions

**Properties**:
- All requirement IDs appear as nodes
- All parent-child relationships appear as edges
- Implementation components appear in separate subgraph
- Output starts with `flowchart` directive
- No duplicate node definitions

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `planning_pipeline/tests/test_visualization.py`
```python
"""Tests for Mermaid diagram generation."""

import pytest
from hypothesis import given, strategies as st, assume

from planning_pipeline.models import (
    RequirementNode,
    RequirementHierarchy,
    ImplementationComponents,
)
from planning_pipeline.visualization import (
    generate_requirements_mermaid,
    generate_class_diagram_mermaid,
)


class TestMermaidFlowchartGeneration:
    """Behavior 2: Generate Mermaid flowchart from requirements."""

    def test_empty_hierarchy_produces_minimal_diagram(self):
        """Given empty hierarchy, produces valid minimal Mermaid."""
        hierarchy = RequirementHierarchy(requirements=[])
        result = generate_requirements_mermaid(hierarchy)

        assert result.startswith("flowchart LR")
        assert "subgraph Requirements" in result
        assert "end" in result

    def test_single_requirement_appears_as_node(self):
        """Given single requirement, it appears as labeled node."""
        node = RequirementNode(
            id="REQ_001",
            description="Track subagent lifecycle",
            type="parent"
        )
        hierarchy = RequirementHierarchy(requirements=[node])
        result = generate_requirements_mermaid(hierarchy)

        assert 'REQ_001["REQ_001: Track subagent lifecycle"]' in result

    def test_parent_child_produces_edge(self):
        """Given parent with child, edge is generated."""
        child = RequirementNode(
            id="REQ_001.1",
            description="Initialize tracking",
            type="sub_process",
            parent_id="REQ_001"
        )
        parent = RequirementNode(
            id="REQ_001",
            description="Track lifecycle",
            type="parent",
            children=[child]
        )
        hierarchy = RequirementHierarchy(requirements=[parent])
        result = generate_requirements_mermaid(hierarchy)

        assert "REQ_001 --> REQ_001.1" in result

    def test_implementation_components_in_separate_subgraph(self):
        """Given implementation with components, components in separate subgraph."""
        impl = ImplementationComponents(
            backend=["SubagentTracker", "AgentRegistry"],
            frontend=["AgentDashboard"]
        )
        child = RequirementNode(
            id="REQ_001.1",
            description="Register agent",
            type="implementation",
            implementation=impl
        )
        parent = RequirementNode(
            id="REQ_001",
            description="Track lifecycle",
            type="parent",
            children=[child]
        )
        hierarchy = RequirementHierarchy(requirements=[parent])
        result = generate_requirements_mermaid(hierarchy)

        assert "subgraph Components" in result
        assert "BE_SubagentTracker" in result
        assert "FE_AgentDashboard" in result

    @given(st.lists(
        st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N"))),
        min_size=1,
        max_size=10,
        unique=True
    ))
    def test_all_nodes_unique_in_output(self, descriptions):
        """Property: Each node ID appears exactly once in diagram."""
        requirements = []
        for i, desc in enumerate(descriptions):
            node = RequirementNode(
                id=f"REQ_{i+1:03d}",
                description=desc,
                type="parent"
            )
            requirements.append(node)

        hierarchy = RequirementHierarchy(requirements=requirements)
        result = generate_requirements_mermaid(hierarchy)

        # Count node definitions (ID followed by bracket)
        for i in range(len(descriptions)):
            node_id = f"REQ_{i+1:03d}"
            # Node definition pattern: ID["label"]
            count = result.count(f'{node_id}["')
            assert count == 1, f"Node {node_id} appears {count} times"

    def test_long_description_truncated(self):
        """Given long description, it's truncated in label."""
        long_desc = "A" * 100
        node = RequirementNode(
            id="REQ_001",
            description=long_desc,
            type="parent"
        )
        hierarchy = RequirementHierarchy(requirements=[node])
        result = generate_requirements_mermaid(hierarchy)

        # Label should be truncated (30 chars + ...)
        assert long_desc not in result
        assert "..." in result


class TestMermaidClassDiagram:
    """Behavior 2b: Generate class diagram from implementation components."""

    def test_backend_component_as_method_produces_class(self):
        """Given component with dot notation, produces class with method."""
        impl = ImplementationComponents(
            backend=["SubagentTracker.register", "SubagentTracker.unregister"]
        )
        child = RequirementNode(
            id="REQ_001.1",
            description="Register",
            type="implementation",
            implementation=impl
        )
        hierarchy = RequirementHierarchy(requirements=[
            RequirementNode(id="REQ_001", description="Track", type="parent", children=[child])
        ])

        result = generate_class_diagram_mermaid(hierarchy)

        assert "classDiagram" in result
        assert "class SubagentTracker" in result
        assert "+register" in result
        assert "+unregister" in result
```

#### 🟢 Green: Minimal Implementation

**File**: `planning_pipeline/visualization.py`
```python
"""Mermaid diagram generation for requirement visualization."""

from typing import Set, Tuple
from planning_pipeline.models import RequirementHierarchy, RequirementNode


def generate_requirements_mermaid(hierarchy: RequirementHierarchy) -> str:
    """Generate Mermaid flowchart from requirement hierarchy.

    Args:
        hierarchy: The requirement hierarchy to visualize.

    Returns:
        Mermaid flowchart syntax as string.
    """
    lines = ["flowchart LR"]
    lines.append("    subgraph Requirements")

    # Add requirement nodes
    for req in hierarchy.requirements:
        _add_requirement_nodes(req, lines)

    lines.append("    end")

    # Collect and add component nodes
    components = _collect_components(hierarchy)
    if components:
        lines.append("    subgraph Components")
        for comp_type, comp_name in components:
            comp_id = _make_component_id(comp_type, comp_name)
            lines.append(f'    {comp_id}(("{comp_type}: {comp_name[:25]}"))')
        lines.append("    end")

        # Link requirements to components
        for req in hierarchy.requirements:
            _add_component_links(req, lines)

    return "\n".join(lines)


def _add_requirement_nodes(node: RequirementNode, lines: list) -> None:
    """Add node and its children to lines."""
    # Truncate description for label
    desc = node.description[:30] + "..." if len(node.description) > 30 else node.description
    lines.append(f'    {node.id}["{node.id}: {desc}"]')

    for child in node.children:
        _add_requirement_nodes(child, lines)
        lines.append(f"    {node.id} --> {child.id}")


def _collect_components(hierarchy: RequirementHierarchy) -> Set[Tuple[str, str]]:
    """Collect unique components from hierarchy."""
    components = set()
    for req in hierarchy.requirements:
        _collect_components_recursive(req, components)
    return components


def _collect_components_recursive(node: RequirementNode, components: Set[Tuple[str, str]]) -> None:
    """Recursively collect components."""
    if node.implementation:
        for comp in node.implementation.backend:
            components.add(("BE", comp.split(".")[0] if "." in comp else comp))
        for comp in node.implementation.frontend:
            components.add(("FE", comp.split(".")[0] if "." in comp else comp))
        for comp in node.implementation.middleware:
            components.add(("MW", comp.split(".")[0] if "." in comp else comp))
        for comp in node.implementation.shared:
            components.add(("SH", comp.split(".")[0] if "." in comp else comp))

    for child in node.children:
        _collect_components_recursive(child, components)


def _make_component_id(comp_type: str, comp_name: str) -> str:
    """Create valid Mermaid ID from component."""
    clean_name = comp_name.replace(" ", "_").replace("-", "_")[:20]
    return f"{comp_type}_{clean_name}"


def _add_component_links(node: RequirementNode, lines: list) -> None:
    """Add dashed links from requirements to components."""
    if node.implementation:
        for comp in node.implementation.backend:
            comp_id = _make_component_id("BE", comp.split(".")[0] if "." in comp else comp)
            lines.append(f"    {node.id} -.-> {comp_id}")
        for comp in node.implementation.frontend:
            comp_id = _make_component_id("FE", comp.split(".")[0] if "." in comp else comp)
            lines.append(f"    {node.id} -.-> {comp_id}")

    for child in node.children:
        _add_component_links(child, lines)


def generate_class_diagram_mermaid(hierarchy: RequirementHierarchy) -> str:
    """Generate class diagram from implementation components.

    Args:
        hierarchy: The requirement hierarchy with implementations.

    Returns:
        Mermaid classDiagram syntax as string.
    """
    lines = ["classDiagram"]
    classes = {}  # class_name -> {"methods": [], "properties": []}

    for req in hierarchy.requirements:
        _extract_classes_recursive(req, classes)

    for class_name, members in classes.items():
        lines.append(f"    class {class_name} {{")
        for method in members["methods"]:
            lines.append(f"        +{method}")
        lines.append("    }")

    return "\n".join(lines)


def _extract_classes_recursive(node: RequirementNode, classes: dict) -> None:
    """Extract class definitions from component names."""
    if node.implementation:
        for comp in node.implementation.backend:
            if "." in comp:
                class_name, method = comp.split(".", 1)
                if class_name not in classes:
                    classes[class_name] = {"methods": [], "properties": []}
                if method not in classes[class_name]["methods"]:
                    classes[class_name]["methods"].append(method)

    for child in node.children:
        _extract_classes_recursive(child, classes)
```

#### 🔵 Refactor: Handle Large Hierarchies

**File**: `planning_pipeline/visualization.py` (additions)
```python
def generate_requirements_mermaid(
    hierarchy: RequirementHierarchy,
    max_nodes_per_subgraph: int = 15
) -> str:
    """Generate Mermaid flowchart with grouping for large hierarchies."""
    lines = ["flowchart LR"]

    # Group requirements by prefix for large hierarchies
    if len(hierarchy.requirements) > max_nodes_per_subgraph:
        # Group by first digit of requirement number
        groups = {}
        for req in hierarchy.requirements:
            prefix = req.id.split("_")[1][:1] if "_" in req.id else "0"
            groups.setdefault(prefix, []).append(req)

        for prefix, reqs in groups.items():
            lines.append(f"    subgraph Group{prefix}")
            for req in reqs:
                _add_requirement_nodes(req, lines)
            lines.append("    end")
    else:
        lines.append("    subgraph Requirements")
        for req in hierarchy.requirements:
            _add_requirement_nodes(req, lines)
        lines.append("    end")

    # ... rest of function
```

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): `pytest planning_pipeline/tests/test_visualization.py -v`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_visualization.py -v`
- [ ] Property tests pass: `pytest --hypothesis-show-statistics planning_pipeline/tests/test_visualization.py`
- [ ] Generated Mermaid parses: (manual verification in Mermaid Live Editor)

**Manual:**
- [ ] Diagram renders correctly in VS Code preview
- [ ] Large hierarchies are properly grouped
- [ ] Component links are visible

---

## Behavior 3: BAML-Based Requirement Decomposition

### Test Specification

**Given**: Research document content
**When**: BAML decomposition function is called
**Then**: Structured `RequirementHierarchy` is returned with properly typed nodes

**Properties**:
- Output always has at least one parent requirement
- Each parent has 2-5 sub-processes
- Implementation nodes have non-empty acceptance criteria
- Component lists are non-null (may be empty)

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `planning_pipeline/tests/test_decomposition.py`
```python
"""Tests for BAML-based requirement decomposition."""

import pytest
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, settings

from planning_pipeline.decomposition import (
    decompose_requirements,
    DecompositionConfig,
)
from planning_pipeline.models import RequirementHierarchy


class TestDecomposeRequirements:
    """Behavior 3: Decompose research into requirements via BAML."""

    @pytest.fixture
    def mock_baml_response(self):
        """Mock BAML client response."""
        return {
            "requirements": [
                {
                    "description": "User Authentication System",
                    "sub_processes": [
                        "Login flow implementation",
                        "Session management",
                        "Password recovery",
                    ]
                }
            ]
        }

    def test_returns_hierarchy_from_research(self, mock_baml_response):
        """Given research content, returns RequirementHierarchy."""
        research_content = "# Research: Auth System\n\nNeed to implement login."

        with patch("planning_pipeline.decomposition.b") as mock_b:
            mock_b.ProcessGate1InitialExtractionPrompt.return_value = mock_baml_response
            mock_b.ProcessGate1SubprocessDetailsPrompt.return_value = {
                "implementation_details": [
                    {
                        "description": "Implement login form",
                        "acceptance_criteria": ["Form validates email", "Shows errors"],
                        "implementation": {
                            "frontend": ["LoginForm"],
                            "backend": ["AuthService.login"],
                            "middleware": [],
                            "shared": ["User"]
                        }
                    }
                ]
            }

            result = decompose_requirements(research_content)

        assert isinstance(result, RequirementHierarchy)
        assert len(result.requirements) >= 1
        assert result.requirements[0].type == "parent"

    def test_returns_error_for_empty_research(self):
        """Given empty research, returns error dict."""
        result = decompose_requirements("")

        assert isinstance(result, dict)
        assert result.get("success") is False
        assert "error" in result

    def test_sub_processes_become_children(self, mock_baml_response):
        """Given response with sub_processes, they become child nodes."""
        research_content = "Research content here"

        with patch("planning_pipeline.decomposition.b") as mock_b:
            mock_b.ProcessGate1InitialExtractionPrompt.return_value = mock_baml_response
            mock_b.ProcessGate1SubprocessDetailsPrompt.return_value = {
                "implementation_details": []
            }

            result = decompose_requirements(research_content)

        parent = result.requirements[0]
        assert len(parent.children) == 3  # 3 sub_processes
        assert all(c.type == "sub_process" for c in parent.children)

    @pytest.mark.slow
    @pytest.mark.integration
    def test_real_baml_call_returns_valid_structure(self):
        """Integration: Real BAML call produces valid hierarchy."""
        research_content = """
        # Research: Simple Feature

        We need to add a logout button to the user dashboard.
        The button should clear the session and redirect to login.
        """

        result = decompose_requirements(research_content)

        # Structural assertions (don't depend on exact content)
        assert isinstance(result, RequirementHierarchy)
        assert len(result.requirements) >= 1
        for req in result.requirements:
            assert req.description
            assert req.type in ("parent", "sub_process", "implementation")


class TestDecompositionProperties:
    """Property-based tests for decomposition invariants."""

    @given(st.text(min_size=10, max_size=500))
    @settings(max_examples=10)  # Limit for speed
    def test_decomposition_never_crashes(self, content):
        """Property: Decomposition handles any input without crashing."""
        with patch("planning_pipeline.decomposition.b") as mock_b:
            mock_b.ProcessGate1InitialExtractionPrompt.return_value = {
                "requirements": []
            }

            # Should not raise
            result = decompose_requirements(content)
            assert result is not None
```

#### 🟢 Green: Minimal Implementation

**File**: `planning_pipeline/decomposition.py`
```python
"""BAML-based requirement decomposition."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Union

from planning_pipeline.models import (
    RequirementHierarchy,
    RequirementNode,
    ImplementationComponents,
)

# Import BAML client
try:
    from baml_client import b
    BAML_AVAILABLE = True
except ImportError:
    b = None
    BAML_AVAILABLE = False


@dataclass
class DecompositionConfig:
    """Configuration for requirement decomposition."""
    max_sub_processes: int = 5
    min_sub_processes: int = 2
    include_acceptance_criteria: bool = True
    expand_dimensions: bool = False  # For future: user interactions, data needs, business rules


def decompose_requirements(
    research_content: str,
    config: Optional[DecompositionConfig] = None
) -> Union[RequirementHierarchy, Dict[str, Any]]:
    """Decompose research content into requirement hierarchy using BAML.

    Args:
        research_content: The research document content.
        config: Optional configuration for decomposition.

    Returns:
        RequirementHierarchy on success, error dict on failure.
    """
    if not research_content.strip():
        return {"success": False, "error": "Research content cannot be empty"}

    if not BAML_AVAILABLE:
        return {"success": False, "error": "BAML client not available"}

    config = config or DecompositionConfig()

    try:
        # Step 1: Initial extraction - get top-level requirements
        initial_response = b.ProcessGate1InitialExtractionPrompt(
            scope_text=research_content,
            analysis_framework="requirement_extraction",
            user_confirmation=True
        )

        hierarchy = RequirementHierarchy(requirements=[], metadata={
            "source": "research_decomposition",
        })

        # Step 2: Process each requirement
        for idx, req_data in enumerate(initial_response.get("requirements", [])):
            parent_id = f"REQ_{idx + 1:03d}"
            parent = RequirementNode(
                id=parent_id,
                description=req_data.get("description", "Untitled"),
                type="parent"
            )

            # Step 3: Get subprocess details for each sub_process
            sub_processes = req_data.get("sub_processes", [])
            for sub_idx, sub_desc in enumerate(sub_processes[:config.max_sub_processes]):
                child_id = f"{parent_id}.{sub_idx + 1}"

                # Get implementation details via BAML
                details_response = b.ProcessGate1SubprocessDetailsPrompt(
                    parent_requirement=req_data.get("description", ""),
                    subprocess_description=sub_desc,
                    context=research_content[:500]  # Truncate context
                )

                impl_details = details_response.get("implementation_details", [])
                if impl_details:
                    detail = impl_details[0]
                    impl = ImplementationComponents(
                        frontend=detail.get("implementation", {}).get("frontend", []),
                        backend=detail.get("implementation", {}).get("backend", []),
                        middleware=detail.get("implementation", {}).get("middleware", []),
                        shared=detail.get("implementation", {}).get("shared", []),
                    )
                    child = RequirementNode(
                        id=child_id,
                        description=sub_desc,
                        type="sub_process",
                        parent_id=parent_id,
                        acceptance_criteria=detail.get("acceptance_criteria", []),
                        implementation=impl
                    )
                else:
                    child = RequirementNode(
                        id=child_id,
                        description=sub_desc,
                        type="sub_process",
                        parent_id=parent_id
                    )

                parent.children.append(child)

            hierarchy.add_requirement(parent)

        return hierarchy

    except Exception as e:
        return {"success": False, "error": str(e)}
```

#### 🔵 Refactor: Add CLI Fallback

**File**: `planning_pipeline/decomposition.py` (additions)
```python
from planning_pipeline.claude_runner import run_claude_sync
import json


def decompose_requirements_cli_fallback(
    research_content: str,
    config: Optional[DecompositionConfig] = None
) -> Union[RequirementHierarchy, Dict[str, Any]]:
    """Fallback: Use Claude CLI when BAML unavailable or for tool-enabled operations."""
    prompt = f"""Analyze this research and extract requirements in JSON format:

{research_content}

Output a JSON object with this structure:
{{
  "requirements": [
    {{
      "description": "Main requirement description",
      "sub_processes": ["task 1", "task 2", "task 3"]
    }}
  ]
}}

Return ONLY valid JSON, no markdown or explanation."""

    result = run_claude_sync(prompt, timeout=300)

    if not result.get("success"):
        return result

    try:
        # Extract JSON from output
        output = result.get("output", "")
        # Find JSON in output (may have surrounding text)
        start = output.find("{")
        end = output.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = output[start:end]
            data = json.loads(json_str)
            return _convert_json_to_hierarchy(data)
        return {"success": False, "error": "No JSON found in output"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid JSON: {e}"}


def _convert_json_to_hierarchy(data: dict) -> RequirementHierarchy:
    """Convert raw JSON to RequirementHierarchy."""
    hierarchy = RequirementHierarchy(requirements=[])

    for idx, req_data in enumerate(data.get("requirements", [])):
        parent_id = f"REQ_{idx + 1:03d}"
        parent = RequirementNode(
            id=parent_id,
            description=req_data.get("description", ""),
            type="parent"
        )

        for sub_idx, sub_desc in enumerate(req_data.get("sub_processes", [])):
            child = RequirementNode(
                id=f"{parent_id}.{sub_idx + 1}",
                description=sub_desc,
                type="sub_process",
                parent_id=parent_id
            )
            parent.children.append(child)

        hierarchy.add_requirement(parent)

    return hierarchy
```

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): `pytest planning_pipeline/tests/test_decomposition.py -v`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_decomposition.py -v`
- [ ] Mocked tests fast: `pytest planning_pipeline/tests/test_decomposition.py -v --durations=10`
- [ ] Integration test passes: `pytest planning_pipeline/tests/test_decomposition.py -v -m integration`

**Manual:**
- [ ] Real BAML call produces valid hierarchy
- [ ] CLI fallback works when BAML unavailable
- [ ] Error messages are informative

---

## Behavior 4: Property Derivation from Acceptance Criteria

### Test Specification

**Given**: List of acceptance criteria strings
**When**: Property derivation runs
**Then**: Hypothesis test skeletons are generated with appropriate strategies

**Properties**:
- Each criterion produces at least one property
- Properties have valid Hypothesis strategy syntax
- Generated code is syntactically valid Python

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `planning_pipeline/tests/test_property_generator.py`
```python
"""Tests for property derivation from acceptance criteria."""

import pytest
import ast
from hypothesis import given, strategies as st

from planning_pipeline.property_generator import (
    derive_properties,
    generate_test_skeleton,
    PropertyType,
)
from planning_pipeline.models import TestableProperty


class TestDeriveProperties:
    """Behavior 4: Derive testable properties from acceptance criteria."""

    def test_uniqueness_criterion_produces_invariant(self):
        """Given uniqueness criterion, produces invariant property."""
        criteria = ["Must validate agent_id uniqueness"]

        properties = derive_properties(criteria)

        assert len(properties) >= 1
        assert any(p.property_type == "invariant" for p in properties)
        assert any("unique" in p.criterion.lower() for p in properties)

    def test_state_criterion_produces_invariant(self):
        """Given initial state criterion, produces invariant property."""
        criteria = ["Must set initial state to PENDING"]

        properties = derive_properties(criteria)

        assert len(properties) >= 1
        assert any("state" in p.criterion.lower() for p in properties)

    def test_validation_criterion_produces_round_trip(self):
        """Given validation criterion, may produce round-trip property."""
        criteria = ["Input must be validated and normalized"]

        properties = derive_properties(criteria)

        # May produce round-trip for normalize/denormalize
        assert len(properties) >= 1

    def test_empty_criteria_returns_empty(self):
        """Given empty criteria list, returns empty properties."""
        properties = derive_properties([])
        assert properties == []


class TestGenerateTestSkeleton:
    """Behavior 4b: Generate Hypothesis test code from property."""

    def test_generates_valid_python(self):
        """Given property, generated code is valid Python syntax."""
        prop = TestableProperty(
            criterion="Must validate agent_id uniqueness",
            property_type="invariant",
            hypothesis_strategy="st.text(min_size=1)",
            test_skeleton=""  # Will be generated
        )

        skeleton = generate_test_skeleton(prop, class_name="SubagentTracker")

        # Should parse as valid Python
        try:
            ast.parse(skeleton)
        except SyntaxError as e:
            pytest.fail(f"Generated invalid Python: {e}\n{skeleton}")

    def test_includes_hypothesis_decorator(self):
        """Given property, skeleton includes @given decorator."""
        prop = TestableProperty(
            criterion="Test criterion",
            property_type="invariant",
            hypothesis_strategy="st.integers()",
            test_skeleton=""
        )

        skeleton = generate_test_skeleton(prop, class_name="MyClass")

        assert "@given" in skeleton
        assert "st.integers()" in skeleton

    def test_includes_class_under_test(self):
        """Given class name, skeleton references it."""
        prop = TestableProperty(
            criterion="Test",
            property_type="invariant",
            hypothesis_strategy="st.text()",
            test_skeleton=""
        )

        skeleton = generate_test_skeleton(prop, class_name="UserTracker")

        assert "UserTracker" in skeleton


class TestPropertyTypes:
    """Test property type classification."""

    @pytest.mark.parametrize("criterion,expected_type", [
        ("must be unique", "invariant"),
        ("must not be empty", "invariant"),
        ("must be preserved after save/load", "round_trip"),
        ("encoding then decoding returns original", "round_trip"),
        ("applying twice equals applying once", "idempotence"),
        ("sorted list stays sorted", "idempotence"),
        ("must match reference implementation", "oracle"),
    ])
    def test_classifies_criterion_correctly(self, criterion, expected_type):
        """Given criterion, classifies to expected property type."""
        properties = derive_properties([criterion])

        assert len(properties) >= 1
        assert properties[0].property_type == expected_type
```

#### 🟢 Green: Minimal Implementation

**File**: `planning_pipeline/property_generator.py`
```python
"""Generate testable properties from acceptance criteria."""

import re
from enum import Enum
from typing import List

from planning_pipeline.models import TestableProperty


class PropertyType(Enum):
    """Types of testable properties."""
    INVARIANT = "invariant"
    ROUND_TRIP = "round_trip"
    IDEMPOTENCE = "idempotence"
    ORACLE = "oracle"


# Patterns for classifying criteria
PROPERTY_PATTERNS = [
    (r"unique|distinct|no duplicate", PropertyType.INVARIANT, "st.text(min_size=1)"),
    (r"not empty|non-empty|has content", PropertyType.INVARIANT, "st.text(min_size=1)"),
    (r"state|status|must be", PropertyType.INVARIANT, "st.sampled_from([])"),
    (r"save.*load|encode.*decode|serialize|round.?trip", PropertyType.ROUND_TRIP, "st.text()"),
    (r"preserved|unchanged|maintains", PropertyType.ROUND_TRIP, "st.text()"),
    (r"twice|multiple times|idempotent|same result", PropertyType.IDEMPOTENCE, "st.lists(st.integers())"),
    (r"sorted|ordered|stable", PropertyType.IDEMPOTENCE, "st.lists(st.integers())"),
    (r"reference|oracle|matches|equals", PropertyType.ORACLE, "st.text()"),
]


def derive_properties(criteria: List[str]) -> List[TestableProperty]:
    """Derive testable properties from acceptance criteria.

    Args:
        criteria: List of acceptance criterion strings.

    Returns:
        List of TestableProperty objects.
    """
    if not criteria:
        return []

    properties = []
    for criterion in criteria:
        prop_type, strategy = _classify_criterion(criterion)
        properties.append(TestableProperty(
            criterion=criterion,
            property_type=prop_type.value,
            hypothesis_strategy=strategy,
            test_skeleton=""  # Generated separately
        ))

    return properties


def _classify_criterion(criterion: str) -> tuple:
    """Classify a criterion into property type and strategy."""
    criterion_lower = criterion.lower()

    for pattern, prop_type, strategy in PROPERTY_PATTERNS:
        if re.search(pattern, criterion_lower):
            return prop_type, strategy

    # Default to invariant
    return PropertyType.INVARIANT, "st.text()"


def generate_test_skeleton(
    prop: TestableProperty,
    class_name: str,
    method_prefix: str = "test_property"
) -> str:
    """Generate Hypothesis test skeleton for a property.

    Args:
        prop: The testable property.
        class_name: Name of the class under test.
        method_prefix: Prefix for test method name.

    Returns:
        Python code string for the test.
    """
    # Sanitize criterion for method name
    safe_name = re.sub(r'[^a-z0-9]+', '_', prop.criterion.lower())[:30]

    if prop.property_type == "invariant":
        return _generate_invariant_test(prop, class_name, safe_name)
    elif prop.property_type == "round_trip":
        return _generate_round_trip_test(prop, class_name, safe_name)
    elif prop.property_type == "idempotence":
        return _generate_idempotence_test(prop, class_name, safe_name)
    elif prop.property_type == "oracle":
        return _generate_oracle_test(prop, class_name, safe_name)
    else:
        return _generate_invariant_test(prop, class_name, safe_name)


def _generate_invariant_test(prop: TestableProperty, class_name: str, safe_name: str) -> str:
    return f'''@given({prop.hypothesis_strategy})
def test_property_{safe_name}(self, value):
    """Property: {prop.criterion}"""
    instance = {class_name}()
    # TODO: Implement invariant check
    # Given: instance with value
    # When: operation performed
    # Then: invariant holds
    assert True  # Replace with actual assertion
'''


def _generate_round_trip_test(prop: TestableProperty, class_name: str, safe_name: str) -> str:
    return f'''@given({prop.hypothesis_strategy})
def test_property_{safe_name}(self, value):
    """Property: {prop.criterion}"""
    instance = {class_name}()
    # TODO: Implement round-trip test
    # encoded = instance.encode(value)
    # decoded = instance.decode(encoded)
    # assert decoded == value
    assert True  # Replace with actual assertion
'''


def _generate_idempotence_test(prop: TestableProperty, class_name: str, safe_name: str) -> str:
    return f'''@given({prop.hypothesis_strategy})
def test_property_{safe_name}(self, value):
    """Property: {prop.criterion}"""
    instance = {class_name}()
    # TODO: Implement idempotence test
    # result_once = instance.operation(value)
    # result_twice = instance.operation(result_once)
    # assert result_once == result_twice
    assert True  # Replace with actual assertion
'''


def _generate_oracle_test(prop: TestableProperty, class_name: str, safe_name: str) -> str:
    return f'''@given({prop.hypothesis_strategy})
def test_property_{safe_name}(self, value):
    """Property: {prop.criterion}"""
    instance = {class_name}()
    # TODO: Implement oracle test
    # result = instance.operation(value)
    # expected = reference_implementation(value)
    # assert result == expected
    assert True  # Replace with actual assertion
'''


def generate_full_test_file(
    properties: List[TestableProperty],
    class_name: str,
    module_path: str
) -> str:
    """Generate complete test file with all property tests.

    Args:
        properties: List of testable properties.
        class_name: Name of class under test.
        module_path: Import path for the class.

    Returns:
        Complete Python test file content.
    """
    imports = '''"""Property-based tests generated from acceptance criteria."""

import pytest
from hypothesis import given, strategies as st

'''
    imports += f"from {module_path} import {class_name}\n\n\n"

    class_def = f"class Test{class_name}Properties:\n"
    class_def += f'    """Property-based tests for {class_name}."""\n\n'

    methods = []
    for prop in properties:
        skeleton = generate_test_skeleton(prop, class_name)
        # Indent for class method
        indented = "\n".join("    " + line for line in skeleton.split("\n"))
        methods.append(indented)

    return imports + class_def + "\n".join(methods)
```

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): `pytest planning_pipeline/tests/test_property_generator.py -v`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_property_generator.py -v`
- [ ] Generated code parses: All `ast.parse()` tests pass
- [ ] Generated code runs: Can import and execute generated test file

**Manual:**
- [ ] Generated tests have meaningful structure
- [ ] Property types match criterion semantics
- [ ] Strategies are appropriate for data types

---

## Behavior 5: Pipeline Step Integration

### Test Specification

**Given**: Research output path
**When**: `step_requirement_decomposition()` is called
**Then**: Hierarchy JSON and Mermaid diagram are written to files

**Properties**:
- Output files are created in expected locations
- JSON is valid and can be loaded back
- Mermaid syntax is valid
- Step returns success with file paths

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `planning_pipeline/tests/test_step_decomposition.py`
```python
"""Tests for requirement decomposition pipeline step."""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from planning_pipeline.step_decomposition import step_requirement_decomposition
from planning_pipeline.models import RequirementHierarchy, RequirementNode


class TestStepRequirementDecomposition:
    """Behavior 5: Pipeline step for requirement decomposition."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temporary project structure."""
        research_dir = tmp_path / "thoughts" / "shared" / "research"
        research_dir.mkdir(parents=True)
        plans_dir = tmp_path / "thoughts" / "shared" / "plans"
        plans_dir.mkdir(parents=True)

        # Create sample research file
        research_file = research_dir / "2026-01-02-test-research.md"
        research_file.write_text("""# Research: Test Feature

## Summary
We need to implement a user tracking system.

## Key Findings
- Track user sessions
- Monitor activity
""")

        return tmp_path, str(research_file)

    @pytest.fixture
    def mock_decomposition(self):
        """Mock decomposition result."""
        return RequirementHierarchy(
            requirements=[
                RequirementNode(
                    id="REQ_001",
                    description="User Tracking",
                    type="parent",
                    children=[
                        RequirementNode(
                            id="REQ_001.1",
                            description="Session tracking",
                            type="sub_process",
                            parent_id="REQ_001"
                        )
                    ]
                )
            ]
        )

    def test_creates_hierarchy_json(self, temp_project, mock_decomposition):
        """Given research path, creates requirements_hierarchy.json."""
        project_path, research_path = temp_project

        with patch("planning_pipeline.step_decomposition.decompose_requirements") as mock_decompose:
            mock_decompose.return_value = mock_decomposition

            result = step_requirement_decomposition(
                project_path=project_path,
                research_path=research_path
            )

        assert result["success"] is True
        assert "hierarchy_path" in result

        hierarchy_path = Path(result["hierarchy_path"])
        assert hierarchy_path.exists()

        # Verify JSON is valid
        with open(hierarchy_path) as f:
            data = json.load(f)
        assert "requirements" in data

    def test_creates_mermaid_diagram(self, temp_project, mock_decomposition):
        """Given research path, creates requirements_diagram.mmd."""
        project_path, research_path = temp_project

        with patch("planning_pipeline.step_decomposition.decompose_requirements") as mock_decompose:
            mock_decompose.return_value = mock_decomposition

            result = step_requirement_decomposition(
                project_path=project_path,
                research_path=research_path
            )

        assert result["success"] is True
        assert "diagram_path" in result

        diagram_path = Path(result["diagram_path"])
        assert diagram_path.exists()

        content = diagram_path.read_text()
        assert content.startswith("flowchart")

    def test_creates_property_tests_skeleton(self, temp_project, mock_decomposition):
        """Given research path, creates property_tests_skeleton.py."""
        project_path, research_path = temp_project

        # Add acceptance criteria to mock
        mock_decomposition.requirements[0].children[0].acceptance_criteria = [
            "Session ID must be unique",
            "Session must have valid timestamp"
        ]

        with patch("planning_pipeline.step_decomposition.decompose_requirements") as mock_decompose:
            mock_decompose.return_value = mock_decomposition

            result = step_requirement_decomposition(
                project_path=project_path,
                research_path=research_path
            )

        assert result["success"] is True
        assert "tests_path" in result

        tests_path = Path(result["tests_path"])
        assert tests_path.exists()

        content = tests_path.read_text()
        assert "from hypothesis import" in content
        assert "@given" in content

    def test_returns_error_for_missing_research(self, temp_project):
        """Given non-existent research path, returns error."""
        project_path, _ = temp_project

        result = step_requirement_decomposition(
            project_path=project_path,
            research_path="/nonexistent/path.md"
        )

        assert result["success"] is False
        assert "error" in result

    def test_returns_error_when_decomposition_fails(self, temp_project):
        """Given decomposition failure, returns error."""
        project_path, research_path = temp_project

        with patch("planning_pipeline.step_decomposition.decompose_requirements") as mock_decompose:
            mock_decompose.return_value = {"success": False, "error": "BAML error"}

            result = step_requirement_decomposition(
                project_path=project_path,
                research_path=research_path
            )

        assert result["success"] is False
        assert "BAML error" in result["error"]
```

#### 🟢 Green: Minimal Implementation

**File**: `planning_pipeline/step_decomposition.py`
```python
"""Pipeline step for iterative requirement decomposition."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from planning_pipeline.models import RequirementHierarchy
from planning_pipeline.decomposition import decompose_requirements
from planning_pipeline.visualization import generate_requirements_mermaid
from planning_pipeline.property_generator import derive_properties, generate_full_test_file


def step_requirement_decomposition(
    project_path: Path,
    research_path: str,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Execute requirement decomposition step.

    Args:
        project_path: Root project path.
        research_path: Path to research document.
        output_dir: Optional custom output directory.

    Returns:
        Dict with success status and output file paths.
    """
    project_path = Path(project_path)
    research_file = Path(research_path)

    # Validate research file exists
    if not research_file.exists():
        return {
            "success": False,
            "error": f"Research file not found: {research_path}"
        }

    # Read research content
    try:
        research_content = research_file.read_text()
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read research file: {e}"
        }

    # Run decomposition
    result = decompose_requirements(research_content)

    # Handle error response
    if isinstance(result, dict) and not result.get("success", True):
        return result

    hierarchy: RequirementHierarchy = result

    # Determine output directory
    if output_dir:
        out_path = Path(output_dir)
    else:
        # Use same directory as research, or plans directory
        date_str = datetime.now().strftime("%Y-%m-%d")
        out_path = project_path / "thoughts" / "shared" / "plans" / f"{date_str}-requirements"

    out_path.mkdir(parents=True, exist_ok=True)

    # Write hierarchy JSON
    hierarchy_path = out_path / "requirements_hierarchy.json"
    with open(hierarchy_path, "w") as f:
        json.dump(hierarchy.to_dict(), f, indent=2)

    # Generate and write Mermaid diagram
    diagram_content = generate_requirements_mermaid(hierarchy)
    diagram_path = out_path / "requirements_diagram.mmd"
    diagram_path.write_text(diagram_content)

    # Collect all acceptance criteria and generate property tests
    all_criteria = _collect_acceptance_criteria(hierarchy)
    if all_criteria:
        properties = derive_properties(all_criteria)
        if properties:
            # Use generic class name since we don't know specific implementation
            test_content = generate_full_test_file(
                properties,
                class_name="Implementation",
                module_path="planning_pipeline.models"
            )
            tests_path = out_path / "property_tests_skeleton.py"
            tests_path.write_text(test_content)
        else:
            tests_path = None
    else:
        tests_path = None

    return {
        "success": True,
        "hierarchy_path": str(hierarchy_path),
        "diagram_path": str(diagram_path),
        "tests_path": str(tests_path) if tests_path else None,
        "requirement_count": len(hierarchy.requirements),
        "output_dir": str(out_path)
    }


def _collect_acceptance_criteria(hierarchy: RequirementHierarchy) -> list:
    """Collect all acceptance criteria from hierarchy."""
    criteria = []
    for req in hierarchy.requirements:
        criteria.extend(_collect_criteria_recursive(req))
    return criteria


def _collect_criteria_recursive(node) -> list:
    """Recursively collect criteria from node and children."""
    criteria = list(node.acceptance_criteria)
    for child in node.children:
        criteria.extend(_collect_criteria_recursive(child))
    return criteria
```

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): `pytest planning_pipeline/tests/test_step_decomposition.py -v`
- [ ] Test passes (Green): `pytest planning_pipeline/tests/test_step_decomposition.py -v`
- [ ] All files created in correct locations
- [ ] JSON validates: `python -c "import json; json.load(open('requirements_hierarchy.json'))"`

**Manual:**
- [ ] Mermaid diagram renders correctly
- [ ] Property test skeleton is usable starting point
- [ ] Step integrates smoothly with existing pipeline

---

## Integration & E2E Testing

### Integration Scenarios

1. **Full decomposition flow**: Research → BAML → Hierarchy → Diagram → Tests
2. **CLI fallback**: When BAML unavailable, CLI produces valid hierarchy
3. **Large research documents**: Handles 10+ page research documents
4. **Edge cases**: Empty research, malformed research, Unicode content

### E2E Test Plan

**File**: `planning_pipeline/tests/test_decomposition_e2e.py`
```python
"""End-to-end tests for requirement decomposition."""

import pytest
from pathlib import Path

from planning_pipeline.step_decomposition import step_requirement_decomposition


@pytest.mark.e2e
@pytest.mark.slow
class TestDecompositionE2E:
    """End-to-end tests for full decomposition pipeline."""

    @pytest.fixture
    def real_project(self):
        """Use actual project directory."""
        return Path(__file__).parent.parent.parent

    def test_full_flow_with_real_research(self, real_project, tmp_path):
        """E2E: Full decomposition from real research file."""
        # Find a recent research file
        research_dir = real_project / "thoughts" / "searchable" / "shared" / "research"
        research_files = list(research_dir.glob("2026-*.md"))

        if not research_files:
            pytest.skip("No research files found")

        research_path = str(research_files[0])

        result = step_requirement_decomposition(
            project_path=real_project,
            research_path=research_path,
            output_dir=str(tmp_path)
        )

        # Verify outputs
        assert result["success"] is True
        assert Path(result["hierarchy_path"]).exists()
        assert Path(result["diagram_path"]).exists()

        # Verify hierarchy is non-trivial
        import json
        with open(result["hierarchy_path"]) as f:
            data = json.load(f)
        assert len(data["requirements"]) >= 1
```

## Implementation Order

| Phase | Behaviors | Dependencies |
|-------|-----------|--------------|
| **1** | Behavior 1: Data Models | None |
| **2** | Behavior 2: Visualization | Behavior 1 |
| **3** | Behavior 4: Property Generator | Behavior 1 |
| **4** | Behavior 3: BAML Decomposition | Behavior 1, BAML client |
| **5** | Behavior 5: Step Integration | All above |

## Dependencies to Install

```bash
# Add to requirements.txt or pyproject.toml
pip install hypothesis pytest-hypothesis
```

## References

- Research: `thoughts/searchable/shared/research/2026-01-02-iterative-requirement-decomposition-with-visualization.md`
- BAML Schemas: `baml_src/functions.baml:408-975`
- Existing Tests: `planning_pipeline/tests/conftest.py:1-59`
- Pipeline Steps: `planning_pipeline/steps.py:12-640`
