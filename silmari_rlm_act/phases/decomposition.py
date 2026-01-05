"""Decomposition phase implementation.

This module implements the decomposition phase of the silmari-rlm-act pipeline,
which breaks research documents into testable requirement hierarchies using
Claude Code and stores findings in the Context Window Array.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from silmari_rlm_act.checkpoints.interactive import (
    collect_multiline_input,
    prompt_decomposition_action,
)
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseResult, PhaseStatus, PhaseType

# Import existing decomposition infrastructure
from planning_pipeline.decomposition import (
    DecompositionConfig,
    DecompositionError,
    decompose_requirements,
)
from planning_pipeline.models import RequirementHierarchy, RequirementNode


class DecompositionPhase:
    """Execute decomposition phase using Claude Code.

    This phase:
    1. Reads research document from research phase artifacts
    2. Uses decompose_requirements() to extract requirement hierarchy
    3. Stores each requirement as TASK entry in CWA
    4. Returns a PhaseResult with artifacts

    Attributes:
        project_path: Root directory of the project
        cwa: Context Window Array integration
        config: Decomposition configuration
        DEFAULT_TIMEOUT: Default timeout in seconds (10 minutes)
    """

    DEFAULT_TIMEOUT = 600  # 10 minutes

    def __init__(
        self,
        project_path: Path,
        cwa: CWAIntegration,
        config: Optional[DecompositionConfig] = None,
    ) -> None:
        """Initialize decomposition phase.

        Args:
            project_path: Root directory of the project
            cwa: Context Window Array integration instance
            config: Optional decomposition configuration
        """
        self.project_path = Path(project_path)
        self.cwa = cwa
        self.config = config or DecompositionConfig()

    def _load_research(self, research_path: Path) -> str:
        """Load research document content.

        Args:
            research_path: Path to research document

        Returns:
            Research document content

        Raises:
            FileNotFoundError: If research document doesn't exist
        """
        if not research_path.exists():
            raise FileNotFoundError(f"Research document not found: {research_path}")
        return research_path.read_text()

    def _store_requirements_in_cwa(
        self, hierarchy: RequirementHierarchy
    ) -> list[str]:
        """Store requirements in CWA as TASK entries.

        Args:
            hierarchy: Requirement hierarchy to store

        Returns:
            List of CWA entry IDs
        """
        entry_ids = []

        for requirement in hierarchy.requirements:
            entry_id = self._store_requirement_node(requirement)
            entry_ids.append(entry_id)

            # Store children recursively
            for child in requirement.children:
                child_id = self._store_requirement_node(child)
                entry_ids.append(child_id)

                # Store grandchildren if any
                for grandchild in child.children:
                    grandchild_id = self._store_requirement_node(grandchild)
                    entry_ids.append(grandchild_id)

        return entry_ids

    def _store_requirement_node(self, node: RequirementNode) -> str:
        """Store a single requirement node in CWA.

        Args:
            node: Requirement node to store

        Returns:
            CWA entry ID
        """
        summary = self._generate_summary(node)
        return self.cwa.store_requirement(
            req_id=node.id,
            description=node.description,
            summary=summary,
        )

    def _generate_summary(self, node: RequirementNode, max_length: int = 100) -> str:
        """Generate summary for a requirement node.

        Args:
            node: Requirement node
            max_length: Maximum summary length

        Returns:
            Brief summary string
        """
        prefix = f"[{node.type}] " if node.type else ""
        summary = f"{prefix}{node.description}"

        if node.acceptance_criteria:
            criteria_count = len(node.acceptance_criteria)
            summary += f" ({criteria_count} criteria)"

        return summary[:max_length]

    def _count_nodes(self, hierarchy: RequirementHierarchy) -> int:
        """Count total nodes in hierarchy.

        Args:
            hierarchy: Requirement hierarchy

        Returns:
            Total node count
        """
        count = 0
        for req in hierarchy.requirements:
            count += 1  # Parent
            count += len(req.children)
            for child in req.children:
                count += len(child.children)
        return count

    def _serialize_hierarchy(self, hierarchy: RequirementHierarchy) -> dict[str, Any]:
        """Serialize hierarchy to JSON-compatible dict.

        Args:
            hierarchy: Requirement hierarchy

        Returns:
            Dictionary representation
        """
        return hierarchy.to_dict()

    def execute(
        self,
        research_path: Path,
        additional_context: str = "",
    ) -> PhaseResult:
        """Execute decomposition phase.

        Args:
            research_path: Path to research document
            additional_context: Optional additional context

        Returns:
            PhaseResult with requirement hierarchy or errors
        """
        started_at = datetime.now()

        try:
            # Load research content
            research_content = self._load_research(research_path)

            # Append additional context if provided
            if additional_context:
                research_content = f"{research_content}\n\nAdditional Context:\n{additional_context}"

            # Decompose requirements using existing infrastructure
            result = decompose_requirements(
                research_content=research_content,
                config=self.config,
            )

            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            # Check for decomposition errors
            if isinstance(result, DecompositionError):
                return PhaseResult(
                    phase_type=PhaseType.DECOMPOSITION,
                    status=PhaseStatus.FAILED,
                    errors=[result.error],
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_seconds=duration,
                    metadata={
                        "error_code": result.error_code.value,
                        "details": result.details,
                    },
                )

            # Store in CWA
            hierarchy: RequirementHierarchy = result
            entry_ids = self._store_requirements_in_cwa(hierarchy)

            # Calculate statistics
            node_count = self._count_nodes(hierarchy)
            parent_count = len(hierarchy.requirements)

            return PhaseResult(
                phase_type=PhaseType.DECOMPOSITION,
                status=PhaseStatus.COMPLETE,
                artifacts=[str(research_path)],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                metadata={
                    "cwa_entry_ids": entry_ids,
                    "hierarchy": self._serialize_hierarchy(hierarchy),
                    "requirements_count": parent_count,
                    "total_nodes": node_count,
                    "research_path": str(research_path),
                },
            )

        except FileNotFoundError as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            return PhaseResult(
                phase_type=PhaseType.DECOMPOSITION,
                status=PhaseStatus.FAILED,
                errors=[str(e)],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
            )

        except Exception as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            return PhaseResult(
                phase_type=PhaseType.DECOMPOSITION,
                status=PhaseStatus.FAILED,
                errors=[str(e)],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                metadata={"exception_type": type(e).__name__},
            )

    def execute_with_checkpoint(
        self,
        research_path: Path,
        auto_approve: bool = False,
        additional_context: str = "",
    ) -> PhaseResult:
        """Execute decomposition phase with interactive checkpoint.

        After decomposition completes, prompts user for action unless auto_approve is True.

        Args:
            research_path: Path to research document
            auto_approve: If True, skip user prompts
            additional_context: Optional additional context

        Returns:
            PhaseResult with requirement hierarchy and user action
        """
        current_context = additional_context

        while True:
            result = self.execute(
                research_path,
                additional_context=current_context,
            )

            # If failed or auto-approve, return immediately
            if result.status == PhaseStatus.FAILED or auto_approve:
                if auto_approve and result.status == PhaseStatus.COMPLETE:
                    result.metadata["user_action"] = "continue"
                return result

            # Prompt user for action
            action = prompt_decomposition_action()
            result.metadata["user_action"] = action

            if action == "continue":
                return result
            elif action == "revise":
                # Collect additional context and re-run
                print("\nEnter additional context (empty line to finish):")
                revision_context = collect_multiline_input("> ")
                if current_context:
                    current_context = f"{current_context}\n\n{revision_context}"
                else:
                    current_context = revision_context
                # Loop continues to re-execute
            elif action == "restart":
                # Indicate restart needed
                result.metadata["needs_restart"] = True
                return result
            elif action == "exit":
                result.metadata["user_exit"] = True
                return result
            else:
                # Unknown action, treat as continue
                return result
