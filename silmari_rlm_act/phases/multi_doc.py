"""Multi-document phase implementation.

This module implements the multi-doc phase of the silmari-rlm-act pipeline,
which splits TDD plan documents into separate phase documents for better
organization and tracking.
"""

import json
import re
from datetime import datetime
from pathlib import Path

from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseResult, PhaseStatus, PhaseType

from planning_pipeline.models import RequirementHierarchy, RequirementNode


class MultiDocPhase:
    """Split TDD plan into multiple phase documents.

    This phase:
    1. Loads TDD plan and requirement hierarchy
    2. Splits plan into separate phase documents
    3. Creates overview document with summary table
    4. Creates numbered phase documents
    5. Maintains links between documents
    6. Stores all documents in CWA as FILE entries
    7. Returns PhaseResult with all document paths

    Attributes:
        project_path: Root directory of the project
        cwa: Context Window Array integration
        MAX_REQS_PER_PHASE: Maximum requirements per phase document
    """

    MAX_REQS_PER_PHASE = 5  # Max requirements per phase document

    def __init__(
        self,
        project_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Initialize multi-doc phase.

        Args:
            project_path: Root directory of the project
            cwa: Context Window Array integration instance
        """
        self.project_path = Path(project_path)
        self.cwa = cwa

    def _split_plan(
        self,
        plan_content: str,
        hierarchy: RequirementHierarchy,
        plan_name: str,
    ) -> list[dict[str, str]]:
        """Split plan into multiple documents.

        Args:
            plan_content: Original plan markdown
            hierarchy: Requirement hierarchy
            plan_name: Base name for plan

        Returns:
            List of document dicts with filename, title, content
        """
        docs: list[dict[str, str]] = []

        # Group requirements into phases
        phases = self._group_into_phases(hierarchy.requirements)

        # Create overview document (will be updated with links later)
        overview = self._create_overview(hierarchy, plan_name, phases)
        docs.append(overview)

        # Create phase documents
        for i, phase_reqs in enumerate(phases, 1):
            doc = self._create_phase_document(phase_reqs, i, plan_name)
            docs.append(doc)

        # Update overview with phase links
        docs[0]["content"] = self._add_phase_links(docs[0]["content"], docs[1:])

        return docs

    def _create_overview(
        self,
        hierarchy: RequirementHierarchy,
        plan_name: str,
        phases: list[list[RequirementNode]],
    ) -> dict[str, str]:
        """Create overview document.

        Args:
            hierarchy: Requirement hierarchy
            plan_name: Plan name
            phases: Grouped phases

        Returns:
            Document dict with filename, title, content
        """
        all_reqs = self._get_all_requirements(hierarchy)

        content = [
            f"# {plan_name} TDD Implementation Plan",
            "",
            "## Overview",
            "",
            f"This plan contains {len(all_reqs)} requirements in {len(phases)} phases.",
            "",
            "## Phase Summary",
            "",
            "| Phase | Description | Requirements | Status |",
            "|-------|-------------|--------------|--------|",
        ]

        for i, phase_reqs in enumerate(phases, 1):
            main_desc = phase_reqs[0].description[:40] if phase_reqs else "Empty"
            if len(main_desc) == 40:
                main_desc += "..."
            req_ids = ", ".join(r.id for r in phase_reqs)
            content.append(f"| {i:02d} | {main_desc} | {req_ids} | Pending |")

        content.extend([
            "",
            "## Requirements Summary",
            "",
            "| ID | Description | Status |",
            "|----|-------------|--------|",
        ])

        for req in all_reqs:
            desc = req.description[:40]
            if len(req.description) > 40:
                desc += "..."
            content.append(f"| {req.id} | {desc} | Pending |")

        content.extend([
            "",
            "## Phase Documents",
            "",
            "_Links will be added after generation._",
        ])

        return {
            "filename": "00-overview.md",
            "title": f"{plan_name} Overview",
            "content": "\n".join(content),
        }

    def _get_all_requirements(
        self,
        hierarchy: RequirementHierarchy,
    ) -> list[RequirementNode]:
        """Get all requirements recursively.

        Args:
            hierarchy: Requirement hierarchy

        Returns:
            Flat list of all requirements
        """
        result: list[RequirementNode] = []

        def collect(nodes: list[RequirementNode]) -> None:
            for node in nodes:
                result.append(node)
                collect(node.children)

        collect(hierarchy.requirements)
        return result

    def _group_into_phases(
        self,
        requirements: list[RequirementNode],
    ) -> list[list[RequirementNode]]:
        """Group requirements into phases.

        Keeps parent/child together, limits per phase.

        Args:
            requirements: Top-level requirements

        Returns:
            List of requirement groups (phases)
        """
        phases: list[list[RequirementNode]] = []
        current_phase: list[RequirementNode] = []

        for req in requirements:
            # Count req and all children
            req_count = 1 + self._count_children(req)

            # If adding this req would exceed limit and we have content, start new phase
            if len(current_phase) + req_count > self.MAX_REQS_PER_PHASE and current_phase:
                phases.append(current_phase)
                current_phase = []

            current_phase.append(req)

        if current_phase:
            phases.append(current_phase)

        return phases

    def _count_children(self, req: RequirementNode) -> int:
        """Count all children recursively.

        Args:
            req: Requirement node

        Returns:
            Total count of children
        """
        count = len(req.children)
        for child in req.children:
            count += self._count_children(child)
        return count

    def _create_phase_document(
        self,
        requirements: list[RequirementNode],
        phase_num: int,
        plan_name: str,
    ) -> dict[str, str]:
        """Create a phase document for requirements.

        Args:
            requirements: Requirements for this phase
            phase_num: Phase number (1-indexed)
            plan_name: Plan name

        Returns:
            Document dict with filename, title, content
        """
        # Get main title from first requirement
        main_title = requirements[0].description[:50] if requirements else f"Phase {phase_num}"
        if len(requirements) > 0 and len(requirements[0].description) > 50:
            main_title += "..."

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

    def _format_requirement(
        self,
        req: RequirementNode,
        level: int = 2,
    ) -> list[str]:
        """Format requirement as markdown.

        Args:
            req: Requirement node
            level: Heading level

        Returns:
            List of markdown lines
        """
        prefix = "#" * (level + 1)
        lines = [
            f"{prefix} {req.id}: {req.description[:60]}",
            "",
            req.description,
            "",
        ]

        if req.acceptance_criteria:
            lines.append(f"{'#' * (level + 2)} Testable Behaviors")
            lines.append("")
            for i, criterion in enumerate(req.acceptance_criteria, 1):
                lines.append(f"{i}. {criterion}")
            lines.append("")

        for child in req.children:
            lines.extend(self._format_requirement(child, level + 1))

        return lines

    def _add_phase_links(
        self,
        overview_content: str,
        phase_docs: list[dict[str, str]],
    ) -> str:
        """Add links to phase documents in overview.

        Args:
            overview_content: Overview document content
            phase_docs: List of phase documents

        Returns:
            Updated overview content with links
        """
        links = ["## Phase Documents", ""]
        for doc in phase_docs:
            links.append(f"- [{doc['title']}]({doc['filename']})")

        return overview_content.replace(
            "_Links will be added after generation._",
            "\n".join(links),
        )

    def _slugify(self, text: str) -> str:
        """Convert text to slug for filename.

        Args:
            text: Text to slugify

        Returns:
            URL-safe slug
        """
        slug = text.lower()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        return slug[:50].strip("-")

    def _create_output_dir(self, plan_name: str) -> Path:
        """Create output directory for documents.

        Args:
            plan_name: Plan name

        Returns:
            Path to output directory
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_dir = (
            self.project_path
            / "thoughts"
            / "searchable"
            / "shared"
            / "plans"
            / f"{date_str}-tdd-{self._slugify(plan_name)}"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _save_documents(
        self,
        docs: list[dict[str, str]],
        output_dir: Path,
    ) -> list[str]:
        """Save all documents to output directory.

        Args:
            docs: Documents to save
            output_dir: Output directory

        Returns:
            List of saved file paths
        """
        paths: list[str] = []
        for doc in docs:
            path = output_dir / doc["filename"]
            path.write_text(doc["content"], encoding="utf-8")
            paths.append(str(path))
        return paths

    def _store_docs_in_cwa(
        self,
        docs: list[dict[str, str]],
        output_dir: Path,
    ) -> list[str]:
        """Store documents in CWA.

        Args:
            docs: Documents to store
            output_dir: Output directory

        Returns:
            List of CWA entry IDs
        """
        entry_ids: list[str] = []
        for doc in docs:
            path = output_dir / doc["filename"]
            entry_id = self.cwa.store_plan(
                path=str(path),
                content=doc["content"],
                summary=doc["title"],
            )
            entry_ids.append(entry_id)
        return entry_ids

    def _load_hierarchy(self, hierarchy_path: str) -> RequirementHierarchy:
        """Load requirement hierarchy from JSON.

        Args:
            hierarchy_path: Path to hierarchy JSON file

        Returns:
            RequirementHierarchy instance

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        path = Path(hierarchy_path)
        if not path.is_absolute():
            path = self.project_path / path

        if not path.exists():
            raise FileNotFoundError(f"Hierarchy not found: {path}")

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        return RequirementHierarchy.from_dict(data)

    def _load_plan(self, plan_path: str) -> str:
        """Load plan content from file.

        Args:
            plan_path: Path to plan file

        Returns:
            Plan content string

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        path = Path(plan_path)
        if not path.is_absolute():
            path = self.project_path / path

        if not path.exists():
            raise FileNotFoundError(f"Plan not found: {path}")

        return path.read_text(encoding="utf-8")

    def execute(
        self,
        plan_path: str,
        hierarchy_path: str,
        plan_name: str,
    ) -> PhaseResult:
        """Execute multi-doc phase.

        Args:
            plan_path: Path to TDD plan document
            hierarchy_path: Path to hierarchy JSON
            plan_name: Base name for output directory

        Returns:
            PhaseResult with document paths
        """
        started_at = datetime.now()

        try:
            # Load inputs
            plan_content = self._load_plan(plan_path)
            hierarchy = self._load_hierarchy(hierarchy_path)

            # Split into documents
            docs = self._split_plan(plan_content, hierarchy, plan_name)

            # Create output directory
            output_dir = self._create_output_dir(plan_name)

            # Save documents
            saved_paths = self._save_documents(docs, output_dir)

            # Store in CWA
            entry_ids = self._store_docs_in_cwa(docs, output_dir)

            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            return PhaseResult(
                phase_type=PhaseType.MULTI_DOC,
                status=PhaseStatus.COMPLETE,
                artifacts=saved_paths,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                metadata={
                    "document_count": len(docs),
                    "output_dir": str(output_dir),
                    "cwa_entry_ids": entry_ids,
                    "plan_path": plan_path,
                    "hierarchy_path": hierarchy_path,
                },
            )

        except FileNotFoundError as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            return PhaseResult(
                phase_type=PhaseType.MULTI_DOC,
                status=PhaseStatus.FAILED,
                errors=[str(e)],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
            )

        except json.JSONDecodeError as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            return PhaseResult(
                phase_type=PhaseType.MULTI_DOC,
                status=PhaseStatus.FAILED,
                errors=[f"Invalid JSON: {e}"],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
            )

        except Exception as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            return PhaseResult(
                phase_type=PhaseType.MULTI_DOC,
                status=PhaseStatus.FAILED,
                errors=[str(e)],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                metadata={"exception_type": type(e).__name__},
            )
