# Phase 06: Decomposition Phase TDD Plan

## Overview

Implement the requirement decomposition phase that breaks research findings into testable behaviors for TDD planning.

## Testable Behaviors

### Behavior 1: Read Research Document
**Given**: Research path from prior phase
**When**: Starting decomposition
**Then**: Research content loaded

### Behavior 2: Extract Requirements
**Given**: Research content
**When**: Calling Claude for decomposition
**Then**: Returns list of requirements

### Behavior 3: Create Requirement Hierarchy
**Given**: Extracted requirements
**When**: Building hierarchy
**Then**: Parent/child structure created

### Behavior 4: Store Requirements in CWA
**Given**: Requirement hierarchy
**When**: Storing in CWA
**Then**: TASK entries created for each requirement

### Behavior 5: Generate Unique IDs
**Given**: Multiple requirements
**When**: Creating hierarchy
**Then**: Each has unique ID

### Behavior 6: Return PhaseResult
**Given**: Successful decomposition
**When**: Phase completes
**Then**: PhaseResult with hierarchy path

### Behavior 7: Handle Decomposition Failure
**Given**: LLM call fails
**When**: Error occurs
**Then**: PhaseResult with error

### Behavior 8: Extract Testable Behaviors
**Given**: Requirement
**When**: Decomposing
**Then**: Behaviors in Given/When/Then format

### Behavior 9: Save Hierarchy JSON
**Given**: Complete hierarchy
**When**: Phase completes
**Then**: JSON file saved

### Behavior 10: Generate Mermaid Diagram
**Given**: Hierarchy
**When**: Visualization requested
**Then**: Mermaid flowchart generated

---

## TDD Cycle: Behavior 1 - Read Research Document

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_decomposition_phase.py`
```python
import pytest
from pathlib import Path
from silmari_rlm_act.phases.decomposition import DecompositionPhase
from silmari_rlm_act.context.cwa_integration import CWAIntegration


class TestReadResearchDocument:
    """Behavior 1: Read Research Document."""

    def test_reads_research_content(self, tmp_path):
        """Given research path, reads content."""
        # Create research file
        research_dir = tmp_path / "thoughts" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nFindings...")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        content = phase._read_research(str(research_file))

        assert content == "# Research\n\nFindings..."

    def test_resolves_relative_path(self, tmp_path):
        """Given relative path, resolves against project."""
        research_dir = tmp_path / "thoughts" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "doc.md"
        research_file.write_text("Content")

        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        content = phase._read_research("thoughts/research/doc.md")

        assert content == "Content"

    def test_raises_for_missing_file(self, tmp_path):
        """Given nonexistent path, raises FileNotFoundError."""
        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        with pytest.raises(FileNotFoundError):
            phase._read_research("nonexistent.md")
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/phases/decomposition.py`
```python
"""Decomposition phase implementation."""

from pathlib import Path
from typing import Optional, List
from silmari_rlm_act.models import PhaseResult
from silmari_rlm_act.context.cwa_integration import CWAIntegration


class DecompositionPhase:
    """Decompose research into testable requirements."""

    def __init__(
        self,
        project_path: Path,
        cwa: CWAIntegration,
    ):
        self.project_path = Path(project_path)
        self.cwa = cwa
        self._runner = None  # Claude runner

    def _read_research(self, research_path: str) -> str:
        """Read research document content.

        Args:
            research_path: Path to research document

        Returns:
            Document content

        Raises:
            FileNotFoundError: If document doesn't exist
        """
        path = Path(research_path)

        # Resolve relative paths
        if not path.is_absolute():
            path = self.project_path / path

        if not path.exists():
            raise FileNotFoundError(f"Research document not found: {path}")

        return path.read_text()
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_decomposition_phase.py::TestReadResearchDocument -v`

---

## TDD Cycle: Behavior 2-3 - Extract Requirements and Hierarchy

### 🔴 Red: Write Failing Tests

**File**: `silmari-rlm-act/tests/test_decomposition_phase.py`
```python
from unittest.mock import Mock, patch


class TestExtractRequirements:
    """Behavior 2: Extract Requirements."""

    def test_extracts_requirements_from_research(self, tmp_path):
        """Given research content, extracts requirements."""
        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        research_content = """
# Authentication Research

## Overview
Implement user authentication with login/logout.

## Features
- User login with email/password
- Session management
- Logout functionality
"""

        mock_runner = Mock()
        mock_runner.run_sync.return_value = {
            "success": True,
            "output": """
{
    "requirements": [
        {
            "id": "REQ-001",
            "title": "User Login",
            "description": "Users can login with email and password",
            "behaviors": [
                "Given valid credentials, when login submitted, then user authenticated"
            ]
        },
        {
            "id": "REQ-002",
            "title": "Session Management",
            "description": "System maintains user sessions",
            "behaviors": []
        }
    ]
}
"""
        }

        with patch.object(phase, '_runner', mock_runner):
            requirements = phase._extract_requirements(research_content)

        assert len(requirements) == 2
        assert requirements[0]["id"] == "REQ-001"


class TestCreateHierarchy:
    """Behavior 3: Create Requirement Hierarchy."""

    def test_creates_parent_child_structure(self, tmp_path):
        """Given requirements, creates hierarchy."""
        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        requirements = [
            {
                "id": "REQ-001",
                "title": "Authentication",
                "description": "User authentication system",
                "children": [
                    {
                        "id": "REQ-001.1",
                        "title": "Login",
                        "description": "User login",
                        "behaviors": ["Given..., When..., Then..."]
                    },
                    {
                        "id": "REQ-001.2",
                        "title": "Logout",
                        "description": "User logout",
                        "behaviors": []
                    }
                ]
            }
        ]

        hierarchy = phase._create_hierarchy(requirements)

        assert hierarchy.root_count == 1
        root = hierarchy.get_by_id("REQ-001")
        assert root is not None
        assert len(root.children) == 2

    def test_assigns_unique_ids(self, tmp_path):
        """Given requirements without IDs, assigns unique ones."""
        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        requirements = [
            {"title": "Feature A", "description": "Desc A"},
            {"title": "Feature B", "description": "Desc B"},
        ]

        hierarchy = phase._create_hierarchy(requirements)

        ids = [r.id for r in hierarchy.all_requirements()]
        assert len(ids) == len(set(ids))  # All unique
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/phases/decomposition.py`
```python
import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Requirement:
    """A single requirement with testable behaviors."""

    id: str
    title: str
    description: str
    behaviors: List[str] = field(default_factory=list)
    children: List["Requirement"] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "behaviors": self.behaviors,
            "children": [c.to_dict() for c in self.children],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Requirement":
        """Deserialize from dictionary."""
        return cls(
            id=d.get("id", ""),
            title=d.get("title", ""),
            description=d.get("description", ""),
            behaviors=d.get("behaviors", []),
            children=[cls.from_dict(c) for c in d.get("children", [])],
        )


@dataclass
class RequirementHierarchy:
    """Hierarchy of requirements."""

    requirements: List[Requirement] = field(default_factory=list)

    @property
    def root_count(self) -> int:
        """Count of root requirements."""
        return len(self.requirements)

    def get_by_id(self, req_id: str) -> Optional[Requirement]:
        """Find requirement by ID."""
        def search(reqs: List[Requirement]) -> Optional[Requirement]:
            for r in reqs:
                if r.id == req_id:
                    return r
                found = search(r.children)
                if found:
                    return found
            return None
        return search(self.requirements)

    def all_requirements(self) -> List[Requirement]:
        """Flatten all requirements."""
        def flatten(reqs: List[Requirement]) -> List[Requirement]:
            result = []
            for r in reqs:
                result.append(r)
                result.extend(flatten(r.children))
            return result
        return flatten(self.requirements)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "requirements": [r.to_dict() for r in self.requirements]
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RequirementHierarchy":
        """Deserialize from dictionary."""
        return cls(
            requirements=[Requirement.from_dict(r) for r in d.get("requirements", [])]
        )


class DecompositionPhase:
    # ... existing code ...

    _id_counter = 0

    def _next_id(self) -> str:
        """Generate next requirement ID."""
        self._id_counter += 1
        return f"REQ-{self._id_counter:03d}"

    def _extract_requirements(self, content: str) -> List[dict]:
        """Extract requirements from research content using LLM.

        Args:
            content: Research document content

        Returns:
            List of requirement dictionaries
        """
        prompt = self._build_extraction_prompt(content)
        result = self._runner.run_sync(prompt, timeout=300)

        if not result.get("success"):
            raise RuntimeError(f"Extraction failed: {result.get('error')}")

        output = result.get("output", "")
        return self._parse_requirements_json(output)

    def _build_extraction_prompt(self, content: str) -> str:
        """Build prompt for requirement extraction."""
        return f"""Analyze the following research document and extract testable requirements.

For each requirement, identify:
1. A unique ID (e.g., REQ-001)
2. A title
3. A description
4. Testable behaviors in Given/When/Then format
5. Child requirements if applicable

Return as JSON:
{{
    "requirements": [
        {{
            "id": "REQ-001",
            "title": "...",
            "description": "...",
            "behaviors": ["Given..., When..., Then..."],
            "children": [...]
        }}
    ]
}}

Research Document:
{content}
"""

    def _parse_requirements_json(self, output: str) -> List[dict]:
        """Parse requirements JSON from LLM output."""
        # Find JSON in output
        start = output.find("{")
        end = output.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON found in output")

        json_str = output[start:end]
        data = json.loads(json_str)
        return data.get("requirements", [])

    def _create_hierarchy(self, requirements: List[dict]) -> RequirementHierarchy:
        """Create requirement hierarchy from extracted data.

        Args:
            requirements: List of requirement dictionaries

        Returns:
            RequirementHierarchy instance
        """
        def convert(req_dict: dict, parent_id: str = "") -> Requirement:
            req_id = req_dict.get("id") or self._next_id()
            return Requirement(
                id=req_id,
                title=req_dict.get("title", "Untitled"),
                description=req_dict.get("description", ""),
                behaviors=req_dict.get("behaviors", []),
                children=[
                    convert(c, req_id) for c in req_dict.get("children", [])
                ],
            )

        return RequirementHierarchy(
            requirements=[convert(r) for r in requirements]
        )
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_decomposition_phase.py::TestExtractRequirements -v`
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_decomposition_phase.py::TestCreateHierarchy -v`

---

## TDD Cycle: Behavior 4-5 - Store in CWA

### 🔴 Red: Write Failing Tests

**File**: `silmari-rlm-act/tests/test_decomposition_phase.py`
```python
from context_window_array import EntryType


class TestStoreInCWA:
    """Behavior 4-5: Store Requirements in CWA."""

    def test_creates_task_entries(self, tmp_path):
        """Given hierarchy, creates TASK entries."""
        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy(requirements=[
            Requirement(
                id="REQ-001",
                title="Login",
                description="User login feature",
                behaviors=["Given..., When..., Then..."]
            )
        ])

        entry_ids = phase._store_in_cwa(hierarchy)

        assert len(entry_ids) == 1
        entry = cwa.store.get(entry_ids[0])
        assert entry.entry_type == EntryType.TASK

    def test_stores_all_requirements(self, tmp_path):
        """Given hierarchy with children, stores all."""
        cwa = CWAIntegration()
        phase = DecompositionPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy(requirements=[
            Requirement(
                id="REQ-001",
                title="Parent",
                description="Parent req",
                children=[
                    Requirement(id="REQ-001.1", title="Child", description="Child req")
                ]
            )
        ])

        entry_ids = phase._store_in_cwa(hierarchy)

        assert len(entry_ids) == 2  # Parent + child
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/phases/decomposition.py`
```python
class DecompositionPhase:
    # ... existing code ...

    def _store_in_cwa(self, hierarchy: RequirementHierarchy) -> List[str]:
        """Store requirements in CWA as TASK entries.

        Args:
            hierarchy: Requirement hierarchy

        Returns:
            List of entry IDs
        """
        entry_ids = []

        for req in hierarchy.all_requirements():
            entry_id = self.cwa.store_requirement(
                req_id=req.id,
                description=f"{req.title}\n\n{req.description}\n\nBehaviors:\n" +
                           "\n".join(f"- {b}" for b in req.behaviors),
                summary=f"{req.id}: {req.title}"
            )
            entry_ids.append(entry_id)

        return entry_ids
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_decomposition_phase.py::TestStoreInCWA -v`

---

## TDD Cycle: Behavior 6-10 - Remaining Behaviors

### Behavior 6: Return PhaseResult
```python
def test_returns_phase_result(tmp_path):
    """Given successful decomposition, returns PhaseResult."""
    result = phase.execute(research_path)

    assert isinstance(result, PhaseResult)
    assert result.phase == "decomposition"
    assert result.success is True
    assert len(result.artifacts) > 0
```

### Behavior 7: Handle Failure
```python
def test_handles_extraction_failure(tmp_path):
    """Given LLM failure, returns error result."""
    mock_runner = Mock()
    mock_runner.run_sync.side_effect = Exception("API error")

    result = phase.execute(research_path)

    assert result.success is False
    assert "API error" in result.error
```

### Behavior 8: Extract Testable Behaviors
```python
def test_extracts_given_when_then(tmp_path):
    """Given requirement, extracts behaviors in GWT format."""
    # Verify behaviors are in proper format
    for req in hierarchy.all_requirements():
        for behavior in req.behaviors:
            assert "Given" in behavior or "When" in behavior or "Then" in behavior
```

### Behavior 9: Save Hierarchy JSON
```python
def test_saves_hierarchy_json(tmp_path):
    """Given hierarchy, saves to JSON file."""
    result = phase.execute(research_path)

    # Find JSON artifact
    json_path = next(a for a in result.artifacts if a.endswith(".json"))
    assert Path(json_path).exists()

    with open(json_path) as f:
        data = json.load(f)

    assert "requirements" in data
```

### Behavior 10: Generate Mermaid Diagram
```python
def test_generates_mermaid_diagram(tmp_path):
    """Given hierarchy, generates Mermaid flowchart."""
    mermaid = phase._generate_mermaid(hierarchy)

    assert "flowchart" in mermaid or "graph" in mermaid
    assert "REQ-001" in mermaid
```

---

## Main Execute Method

**File**: `silmari-rlm-act/phases/decomposition.py`
```python
class DecompositionPhase:
    # ... existing code ...

    def execute(self, research_path: str) -> PhaseResult:
        """Execute decomposition phase.

        Args:
            research_path: Path to research document

        Returns:
            PhaseResult with hierarchy artifacts
        """
        try:
            # Read research
            content = self._read_research(research_path)

            # Extract requirements
            requirements = self._extract_requirements(content)

            # Create hierarchy
            hierarchy = self._create_hierarchy(requirements)

            # Store in CWA
            entry_ids = self._store_in_cwa(hierarchy)

            # Save artifacts
            output_dir = self._create_output_dir()
            hierarchy_path = self._save_hierarchy(hierarchy, output_dir)
            mermaid_path = self._save_mermaid(hierarchy, output_dir)

            return PhaseResult(
                phase="decomposition",
                success=True,
                artifacts=[str(hierarchy_path), str(mermaid_path)],
                output=f"Decomposed into {len(hierarchy.all_requirements())} requirements"
            )

        except Exception as e:
            return PhaseResult(
                phase="decomposition",
                success=False,
                error=str(e)
            )

    def _create_output_dir(self) -> Path:
        """Create output directory for artifacts."""
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_dir = self.project_path / "thoughts" / "searchable" / "shared" / "plans" / f"{date_str}-requirements"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _save_hierarchy(self, hierarchy: RequirementHierarchy, output_dir: Path) -> Path:
        """Save hierarchy to JSON file."""
        path = output_dir / "hierarchy.json"
        with open(path, "w") as f:
            json.dump(hierarchy.to_dict(), f, indent=2)
        return path

    def _save_mermaid(self, hierarchy: RequirementHierarchy, output_dir: Path) -> Path:
        """Save Mermaid diagram."""
        mermaid = self._generate_mermaid(hierarchy)
        path = output_dir / "requirements.mmd"
        path.write_text(mermaid)
        return path

    def _generate_mermaid(self, hierarchy: RequirementHierarchy) -> str:
        """Generate Mermaid flowchart from hierarchy."""
        lines = ["flowchart TD"]

        def add_node(req: Requirement, parent_id: str = ""):
            node_id = req.id.replace("-", "_").replace(".", "_")
            lines.append(f'    {node_id}["{req.id}: {req.title}"]')
            if parent_id:
                lines.append(f"    {parent_id} --> {node_id}")
            for child in req.children:
                add_node(child, node_id)

        for req in hierarchy.requirements:
            add_node(req)

        return "\n".join(lines)
```

---

## Success Criteria

**Automated:**
- [ ] All decomposition tests pass: `pytest silmari-rlm-act/tests/test_decomposition_phase.py -v`

**Manual:**
- [ ] Decomposition extracts meaningful requirements
- [ ] Hierarchy reflects research structure
- [ ] JSON and Mermaid artifacts created
- [ ] CWA entries searchable

## Summary

This phase implements decomposition with:
- Research document reading
- LLM-based requirement extraction
- Hierarchical structure creation
- CWA storage as TASK entries
- JSON hierarchy output
- Mermaid diagram generation
