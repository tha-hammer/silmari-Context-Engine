"""Beads sync phase implementation.

This module implements the beads sync phase of the silmari-rlm-act pipeline,
which creates beads issues for tracking plan implementation progress.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Protocol

from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseResult, PhaseStatus, PhaseType


class BeadsControllerProtocol(Protocol):
    """Protocol for beads controller."""

    def create_epic(self, title: str, priority: int = 1) -> dict[str, Any]: ...

    def create_issue(
        self,
        title: str,
        issue_type: str = "task",
        priority: int = 2,
    ) -> dict[str, Any]: ...

    def add_dependency(self, issue_id: str, depends_on: str) -> dict[str, Any]: ...

    def sync(self) -> dict[str, Any]: ...


class BeadsSyncPhase:
    """Sync plan phases with beads for tracking.

    This phase:
    1. Creates beads epic for the plan
    2. Creates phase issues for each phase document
    3. Links dependencies (phase N depends on phase N-1)
    4. Stores beads issue IDs in CWA metadata
    5. Optionally syncs with remote
    6. Returns PhaseResult with created issue IDs

    Attributes:
        project_path: Root directory of the project
        cwa: Context Window Array integration
        beads: Beads controller for CLI operations
    """

    def __init__(
        self,
        project_path: Path,
        cwa: CWAIntegration,
        beads_controller: BeadsControllerProtocol,
    ) -> None:
        """Initialize beads sync phase.

        Args:
            project_path: Root directory of the project
            cwa: Context Window Array integration instance
            beads_controller: Beads controller for CLI operations
        """
        self.project_path = Path(project_path)
        self.cwa = cwa
        self.beads = beads_controller

    def _parse_phase_number(self, filename: str) -> Optional[int]:
        """Parse phase number from filename.

        Args:
            filename: Filename like "01-login.md" or "00-overview.md"

        Returns:
            Phase number (0 for overview), or None if invalid
        """
        match = re.match(r"^(\d+)-", filename)
        if match:
            return int(match.group(1))
        return None

    def _extract_phase_title(self, doc_path: str) -> str:
        """Extract phase title from document.

        Args:
            doc_path: Path to phase document

        Returns:
            Title extracted from filename or document
        """
        path = Path(doc_path)
        filename = path.name

        # Remove .md extension and number prefix
        name = re.sub(r"^\d+-", "", filename)
        name = re.sub(r"\.md$", "", name)

        # Convert kebab-case to title case
        title = name.replace("-", " ").title()

        return title

    def _get_phase_docs(self, phase_docs: list[str]) -> list[tuple[int, str]]:
        """Get phase documents sorted by phase number.

        Excludes overview (00-*) documents.

        Args:
            phase_docs: List of document paths

        Returns:
            List of (phase_number, path) tuples, sorted by number
        """
        phases: list[tuple[int, str]] = []

        for doc_path in phase_docs:
            filename = Path(doc_path).name
            phase_num = self._parse_phase_number(filename)

            # Skip overview (0) and invalid files
            if phase_num is None or phase_num == 0:
                continue

            phases.append((phase_num, doc_path))

        # Sort by phase number
        phases.sort(key=lambda x: x[0])
        return phases

    def _create_epic(self, plan_name: str) -> tuple[bool, str, Optional[str]]:
        """Create beads epic for the plan.

        Args:
            plan_name: Name of the plan

        Returns:
            Tuple of (success, epic_id or error message, error if failed)
        """
        title = f"TDD: {plan_name} Implementation"
        result = self.beads.create_epic(title, priority=1)

        if result.get("success"):
            epic_id = result.get("data", {}).get("id")
            return True, epic_id, None
        else:
            error = result.get("error", "Unknown error creating epic")
            return False, "", error

    def _create_phase_issue(
        self,
        phase_num: int,
        doc_path: str,
    ) -> tuple[bool, str, Optional[str]]:
        """Create beads issue for a phase.

        Args:
            phase_num: Phase number (1-indexed)
            doc_path: Path to phase document

        Returns:
            Tuple of (success, issue_id or error message, error if failed)
        """
        title = self._extract_phase_title(doc_path)
        full_title = f"Phase {phase_num:02d}: {title}"

        result = self.beads.create_issue(
            title=full_title,
            issue_type="task",
            priority=1,
        )

        if result.get("success"):
            issue_id = result.get("data", {}).get("id")
            return True, issue_id, None
        else:
            error = result.get("error", "Unknown error creating issue")
            return False, "", error

    def _link_dependencies(
        self,
        phase_issue_ids: list[str],
    ) -> list[str]:
        """Link dependencies between phases.

        Phase N depends on Phase N-1.

        Args:
            phase_issue_ids: List of phase issue IDs in order

        Returns:
            List of errors (empty if all successful)
        """
        errors: list[str] = []

        for i in range(1, len(phase_issue_ids)):
            current_id = phase_issue_ids[i]
            depends_on_id = phase_issue_ids[i - 1]

            result = self.beads.add_dependency(current_id, depends_on_id)
            if not result.get("success"):
                error = result.get("error", "Unknown error adding dependency")
                errors.append(f"Failed to link {current_id} -> {depends_on_id}: {error}")

        return errors

    def execute(
        self,
        phase_docs: list[str],
        plan_name: str,
        sync_remote: bool = True,
    ) -> PhaseResult:
        """Execute beads sync phase.

        Args:
            phase_docs: List of phase document paths
            plan_name: Name of the plan (for epic title)
            sync_remote: If True, sync to remote after creation

        Returns:
            PhaseResult with created issue IDs
        """
        started_at = datetime.now()
        errors: list[str] = []
        metadata: dict[str, Any] = {}

        try:
            # Validate input
            if not phase_docs:
                raise ValueError("No phase documents provided")

            # Get sorted phase docs (excluding overview)
            phases = self._get_phase_docs(phase_docs)

            if not phases:
                raise ValueError("No valid phase documents found (only overview?)")

            # Create epic
            success, epic_id, error = self._create_epic(plan_name)
            if not success:
                raise RuntimeError(f"Failed to create epic: {error}")
            metadata["epic_id"] = epic_id

            # Create phase issues
            phase_issue_ids: list[str] = []
            for phase_num, doc_path in phases:
                success, issue_id, error = self._create_phase_issue(phase_num, doc_path)
                if not success:
                    raise RuntimeError(f"Failed to create issue for phase {phase_num}: {error}")
                phase_issue_ids.append(issue_id)

            metadata["phase_issue_ids"] = phase_issue_ids

            # Link dependencies
            dep_errors = self._link_dependencies(phase_issue_ids)
            if dep_errors:
                # Log warnings but don't fail
                errors.extend(dep_errors)

            # Sync to remote if requested
            if sync_remote:
                sync_result = self.beads.sync()
                if not sync_result.get("success"):
                    # Log warning but don't fail
                    errors.append(f"Sync warning: {sync_result.get('error', 'Unknown')}")
                metadata["synced"] = sync_result.get("success", False)
            else:
                metadata["synced"] = False

            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            return PhaseResult(
                phase_type=PhaseType.BEADS_SYNC,
                status=PhaseStatus.COMPLETE,
                artifacts=[],  # No file artifacts
                errors=errors,  # May have warnings
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                metadata=metadata,
            )

        except (ValueError, RuntimeError) as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            return PhaseResult(
                phase_type=PhaseType.BEADS_SYNC,
                status=PhaseStatus.FAILED,
                errors=[str(e)] + errors,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                metadata=metadata,
            )

        except Exception as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            return PhaseResult(
                phase_type=PhaseType.BEADS_SYNC,
                status=PhaseStatus.FAILED,
                errors=[str(e)] + errors,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                metadata={
                    "exception_type": type(e).__name__,
                    **metadata,
                },
            )
