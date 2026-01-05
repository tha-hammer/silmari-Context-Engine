# Phase 08: Multi-Doc Phase TDD Plan

## Overview

Implement the multi-document phase that splits the TDD plan into separate phase documents (00-overview, 01-phase-1, etc.) for better organization and tracking.

## Testable Behaviors

### Behavior 1: Split Plan by Requirements
**Given**: TDD plan with multiple requirements
**When**: Running multi-doc phase
**Then**: Creates separate document per requirement group

### Behavior 2: Create Overview Document
**Given**: TDD plan
**When**: Generating documents
**Then**: 00-overview.md created with summary

### Behavior 3: Create Phase Documents
**Given**: TDD plan with 3 requirements
**When**: Generating documents
**Then**: 01-phase-1.md, 02-phase-2.md, 03-phase-3.md created

### Behavior 4: Maintain Document Links
**Given**: Phase documents
**When**: Creating overview
**Then**: Links to all phase docs included

### Behavior 5: Store Documents in CWA
**Given**: Generated documents
**When**: Phase completes
**Then**: FILE entries created for each doc

### Behavior 6: Create Output Directory
**Given**: Plan name
**When**: Generating documents
**Then**: Directory created with date prefix

### Behavior 7: Return PhaseResult
**Given**: Successful generation
**When**: Phase completes
**Then**: PhaseResult with all document paths

### Behavior 8: Handle Large Plans
**Given**: Plan with many requirements
**When**: Generating documents
**Then**: Groups requirements into reasonable phases

---

## TDD Cycle: Behavior 1-2 - Split and Overview

### 🔴 Red: Write Failing Tests

**File**: `silmari-rlm-act/tests/test_multi_doc_phase.py`
```python
import pytest
from pathlib import Path
from silmari_rlm_act.phases.multi_doc import MultiDocPhase
from silmari_rlm_act.phases.decomposition import RequirementHierarchy, Requirement
from silmari_rlm_act.context.cwa_integration import CWAIntegration


class TestSplitPlan:
    """Behavior 1: Split Plan by Requirements."""

    def test_creates_multiple_documents(self, tmp_path):
        """Given plan with requirements, creates docs."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        # Create plan content
        plan_content = """# TDD Plan

## REQ-001: Login
...content...

## REQ-002: Logout
...content...
"""
        hierarchy = RequirementHierarchy(requirements=[
            Requirement(id="REQ-001", title="Login", description="Login feature", behaviors=[]),
            Requirement(id="REQ-002", title="Logout", description="Logout feature", behaviors=[]),
        ])

        docs = phase._split_plan(plan_content, hierarchy, "login-feature")

        assert len(docs) >= 2  # At least overview + 1 phase

    def test_groups_related_requirements(self, tmp_path):
        """Given child requirements, groups together."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy(requirements=[
            Requirement(
                id="REQ-001",
                title="Auth",
                description="Authentication",
                children=[
                    Requirement(id="REQ-001.1", title="Login", description="", behaviors=[]),
                    Requirement(id="REQ-001.2", title="Logout", description="", behaviors=[]),
                ]
            )
        ])

        docs = phase._split_plan("# Plan", hierarchy, "auth")

        # Parent and children should be in same phase
        auth_phase = next(d for d in docs if "Auth" in d["title"])
        assert "Login" in auth_phase["content"] or "REQ-001.1" in auth_phase["content"]


class TestOverviewDocument:
    """Behavior 2: Create Overview Document."""

    def test_creates_overview(self, tmp_path):
        """Given plan, creates 00-overview.md."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy(requirements=[
            Requirement(id="REQ-001", title="Login", description="", behaviors=[])
        ])

        docs = phase._split_plan("# Plan", hierarchy, "feature")

        overview = next((d for d in docs if "00-overview" in d["filename"]), None)
        assert overview is not None

    def test_overview_has_summary_table(self, tmp_path):
        """Given docs, overview has status table."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy(requirements=[
            Requirement(id="REQ-001", title="Login", description="", behaviors=[]),
            Requirement(id="REQ-002", title="Logout", description="", behaviors=[]),
        ])

        docs = phase._split_plan("# Plan", hierarchy, "feature")
        overview = next(d for d in docs if "00-overview" in d["filename"])

        assert "| Phase |" in overview["content"] or "| ID |" in overview["content"]
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/phases/multi_doc.py`
```python
"""Multi-document phase implementation."""

from datetime import datetime
from pathlib import Path
from typing import List, Dict
from silmari_rlm_act.models import PhaseResult
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.phases.decomposition import RequirementHierarchy, Requirement


class MultiDocPhase:
    """Split TDD plan into multiple phase documents."""

    MAX_REQS_PER_PHASE = 3  # Max requirements per phase document

    def __init__(
        self,
        project_path: Path,
        cwa: CWAIntegration,
    ):
        self.project_path = Path(project_path)
        self.cwa = cwa

    def _split_plan(
        self,
        plan_content: str,
        hierarchy: RequirementHierarchy,
        plan_name: str
    ) -> List[Dict]:
        """Split plan into multiple documents.

        Args:
            plan_content: Original plan markdown
            hierarchy: Requirement hierarchy
            plan_name: Base name for plan

        Returns:
            List of document dicts with filename, title, content
        """
        docs = []

        # Create overview document
        overview = self._create_overview(hierarchy, plan_name)
        docs.append(overview)

        # Group requirements into phases
        phases = self._group_into_phases(hierarchy.requirements)

        for i, phase_reqs in enumerate(phases, 1):
            doc = self._create_phase_document(phase_reqs, i, plan_name)
            docs.append(doc)

        # Update overview with phase links
        docs[0]["content"] = self._add_phase_links(docs[0]["content"], docs[1:])

        return docs

    def _create_overview(
        self,
        hierarchy: RequirementHierarchy,
        plan_name: str
    ) -> Dict:
        """Create overview document."""
        content = [
            f"# {plan_name} TDD Implementation Plan",
            "",
            "## Overview",
            "",
            f"This plan contains {len(hierarchy.all_requirements())} requirements.",
            "",
            "## Phase Summary",
            "",
            "| Phase | Behavior | Status |",
            "|-------|----------|--------|",
        ]

        for req in hierarchy.all_requirements():
            content.append(f"| {req.id} | {req.title} | Pending |")

        content.extend([
            "",
            "## Phase Documents",
            "",
            "_Links will be added after generation._",
        ])

        return {
            "filename": f"00-overview.md",
            "title": f"{plan_name} Overview",
            "content": "\n".join(content),
        }

    def _group_into_phases(
        self,
        requirements: List[Requirement]
    ) -> List[List[Requirement]]:
        """Group requirements into phases.

        Keeps parent/child together, limits per phase.
        """
        phases = []
        current_phase = []

        for req in requirements:
            # Count req and all children
            req_count = 1 + len(req.children)

            if len(current_phase) + req_count > self.MAX_REQS_PER_PHASE and current_phase:
                phases.append(current_phase)
                current_phase = []

            current_phase.append(req)

        if current_phase:
            phases.append(current_phase)

        return phases

    def _create_phase_document(
        self,
        requirements: List[Requirement],
        phase_num: int,
        plan_name: str
    ) -> Dict:
        """Create a phase document for requirements."""
        # Get main title from first requirement
        main_title = requirements[0].title if requirements else f"Phase {phase_num}"

        content = [
            f"# Phase {phase_num:02d}: {main_title}",
            "",
            "## Requirements",
            "",
        ]

        for req in requirements:
            content.extend(self._format_requirement(req))

        content.extend([
            "",
            "## Success Criteria",
            "",
            "- [ ] All tests pass",
            "- [ ] All behaviors implemented",
            "- [ ] Code reviewed",
        ])

        return {
            "filename": f"{phase_num:02d}-{self._slugify(main_title)}.md",
            "title": f"Phase {phase_num}: {main_title}",
            "content": "\n".join(content),
        }

    def _format_requirement(self, req: Requirement, level: int = 2) -> List[str]:
        """Format requirement as markdown."""
        prefix = "#" * level
        lines = [
            f"{prefix} {req.id}: {req.title}",
            "",
            req.description,
            "",
        ]

        if req.behaviors:
            lines.append("### Testable Behaviors")
            lines.append("")
            for i, behavior in enumerate(req.behaviors, 1):
                lines.append(f"{i}. {behavior}")
            lines.append("")

        for child in req.children:
            lines.extend(self._format_requirement(child, level + 1))

        return lines

    def _add_phase_links(self, overview_content: str, phase_docs: List[Dict]) -> str:
        """Add links to phase documents in overview."""
        links = ["## Phase Documents", ""]
        for doc in phase_docs:
            links.append(f"- [{doc['title']}]({doc['filename']})")

        return overview_content.replace(
            "_Links will be added after generation._",
            "\n".join(links)
        )

    def _slugify(self, text: str) -> str:
        """Convert text to slug for filename."""
        import re
        slug = text.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        return slug[:50].strip('-')
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_multi_doc_phase.py::TestSplitPlan -v`
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_multi_doc_phase.py::TestOverviewDocument -v`

---

## TDD Cycle: Behavior 3-4 - Phase Documents and Links

### 🔴 Red: Write Failing Tests

**File**: `silmari-rlm-act/tests/test_multi_doc_phase.py`
```python
class TestPhaseDocuments:
    """Behavior 3: Create Phase Documents."""

    def test_creates_numbered_files(self, tmp_path):
        """Given 3 requirements, creates 3 phase docs."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy(requirements=[
            Requirement(id="REQ-001", title="Feature A", description="", behaviors=[]),
            Requirement(id="REQ-002", title="Feature B", description="", behaviors=[]),
            Requirement(id="REQ-003", title="Feature C", description="", behaviors=[]),
        ])

        docs = phase._split_plan("# Plan", hierarchy, "feature")

        # Should have overview + 3 phases (or grouped)
        phase_docs = [d for d in docs if not d["filename"].startswith("00")]
        assert len(phase_docs) >= 1

        # Check numbering
        filenames = [d["filename"] for d in docs]
        assert any("01-" in f for f in filenames)

    def test_phase_includes_requirement_content(self, tmp_path):
        """Given requirement, phase doc has its content."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy(requirements=[
            Requirement(
                id="REQ-001",
                title="Login",
                description="User login feature",
                behaviors=["Given creds, when login, then success"]
            )
        ])

        docs = phase._split_plan("# Plan", hierarchy, "auth")
        phase_doc = next(d for d in docs if "01-" in d["filename"])

        assert "REQ-001" in phase_doc["content"]
        assert "Login" in phase_doc["content"]
        assert "Given creds" in phase_doc["content"]


class TestDocumentLinks:
    """Behavior 4: Maintain Document Links."""

    def test_overview_links_to_phases(self, tmp_path):
        """Given phases, overview links to them."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        hierarchy = RequirementHierarchy(requirements=[
            Requirement(id="REQ-001", title="Login", description="", behaviors=[])
        ])

        docs = phase._split_plan("# Plan", hierarchy, "auth")
        overview = next(d for d in docs if "00-overview" in d["filename"])
        phase_doc = next(d for d in docs if "01-" in d["filename"])

        # Overview should link to phase doc
        assert phase_doc["filename"] in overview["content"]
```

### 🟢 Green
Already implemented in the previous code block.

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_multi_doc_phase.py::TestPhaseDocuments -v`
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_multi_doc_phase.py::TestDocumentLinks -v`

---

## TDD Cycle: Behavior 5-8 - Storage and Execution

### 🔴 Red: Write Failing Tests

**File**: `silmari-rlm-act/tests/test_multi_doc_phase.py`
```python
import json
from context_window_array import EntryType


class TestStoreDocs:
    """Behavior 5-6: Store Documents in CWA."""

    def test_creates_file_entries(self, tmp_path):
        """Given docs, creates FILE entries."""
        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        docs = [
            {"filename": "00-overview.md", "title": "Overview", "content": "# Overview"},
            {"filename": "01-login.md", "title": "Phase 1", "content": "# Login"},
        ]

        entry_ids = phase._store_docs_in_cwa(docs, tmp_path / "plans")

        assert len(entry_ids) == 2
        for entry_id in entry_ids:
            entry = cwa.store.get(entry_id)
            assert entry.entry_type == EntryType.FILE


class TestMultiDocExecution:
    """Behavior 7-8: Execute and Return."""

    def test_returns_all_document_paths(self, tmp_path):
        """Given successful execution, returns all paths."""
        # Create hierarchy and plan
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps({
            "requirements": [
                {"id": "REQ-001", "title": "Login", "description": "", "behaviors": [], "children": []}
            ]
        }))

        plan_path = tmp_path / "plan.md"
        plan_path.write_text("# TDD Plan\n\n## REQ-001: Login")

        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(
            plan_path=str(plan_path),
            hierarchy_path=str(hierarchy_path),
            plan_name="login"
        )

        assert result.success is True
        assert len(result.artifacts) >= 2  # Overview + at least 1 phase

    def test_creates_output_directory(self, tmp_path):
        """Given plan name, creates dated directory."""
        hierarchy_path = tmp_path / "hierarchy.json"
        hierarchy_path.write_text(json.dumps({
            "requirements": [
                {"id": "REQ-001", "title": "Login", "description": "", "behaviors": [], "children": []}
            ]
        }))

        plan_path = tmp_path / "plan.md"
        plan_path.write_text("# Plan")

        cwa = CWAIntegration()
        phase = MultiDocPhase(project_path=tmp_path, cwa=cwa)

        result = phase.execute(
            plan_path=str(plan_path),
            hierarchy_path=str(hierarchy_path),
            plan_name="login"
        )

        # Check directory exists
        assert result.success
        first_artifact = Path(result.artifacts[0])
        assert "tdd-login" in str(first_artifact.parent)
```

### 🟢 Green: Implement Execute

**File**: `silmari-rlm-act/phases/multi_doc.py`
```python
import json


class MultiDocPhase:
    # ... existing code ...

    def execute(
        self,
        plan_path: str,
        hierarchy_path: str,
        plan_name: str
    ) -> PhaseResult:
        """Execute multi-doc phase.

        Args:
            plan_path: Path to TDD plan document
            hierarchy_path: Path to hierarchy JSON
            plan_name: Base name for output directory

        Returns:
            PhaseResult with document paths
        """
        try:
            # Load inputs
            plan_content = Path(plan_path).read_text()
            with open(hierarchy_path) as f:
                hierarchy = RequirementHierarchy.from_dict(json.load(f))

            # Split into documents
            docs = self._split_plan(plan_content, hierarchy, plan_name)

            # Create output directory
            output_dir = self._create_output_dir(plan_name)

            # Save documents
            saved_paths = self._save_documents(docs, output_dir)

            # Store in CWA
            self._store_docs_in_cwa(docs, output_dir)

            return PhaseResult(
                phase="multi_doc",
                success=True,
                artifacts=saved_paths,
                output=f"Created {len(docs)} documents in {output_dir}"
            )

        except Exception as e:
            return PhaseResult(
                phase="multi_doc",
                success=False,
                error=str(e)
            )

    def _create_output_dir(self, plan_name: str) -> Path:
        """Create output directory for documents."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_dir = (
            self.project_path / "thoughts" / "searchable" / "shared" / "plans" /
            f"{date_str}-tdd-{self._slugify(plan_name)}"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _save_documents(self, docs: List[Dict], output_dir: Path) -> List[str]:
        """Save all documents to output directory."""
        paths = []
        for doc in docs:
            path = output_dir / doc["filename"]
            path.write_text(doc["content"])
            paths.append(str(path))
        return paths

    def _store_docs_in_cwa(self, docs: List[Dict], output_dir: Path) -> List[str]:
        """Store documents in CWA."""
        entry_ids = []
        for doc in docs:
            path = output_dir / doc["filename"]
            entry_id = self.cwa.store_plan(
                path=str(path),
                content=doc["content"],
                summary=doc["title"]
            )
            entry_ids.append(entry_id)
        return entry_ids
```

### Success Criteria
**Automated:**
- [ ] All multi-doc tests pass: `pytest silmari-rlm-act/tests/test_multi_doc_phase.py -v`

**Manual:**
- [ ] Documents are well-organized
- [ ] Links between documents work
- [ ] Directory structure is clean

## Summary

This phase implements multi-document generation with:
- Plan splitting by requirements
- Overview document with summary table
- Numbered phase documents
- Cross-document links
- CWA storage for all documents
- Output directory creation
