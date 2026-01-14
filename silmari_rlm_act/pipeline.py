"""RLMActPipeline orchestration for silmari-rlm-act.

This module provides the main pipeline orchestrator that coordinates
all phases of the RLM-Act pipeline from research through implementation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Protocol

from silmari_rlm_act.checkpoints.manager import CheckpointManager
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import (
    AutonomyMode,
    PhaseResult,
    PhaseStatus,
    PhaseType,
    PipelineState,
)
from silmari_rlm_act.phases.beads_sync import BeadsSyncPhase
from silmari_rlm_act.phases.decomposition import DecompositionPhase
from silmari_rlm_act.phases.implementation import ImplementationPhase
from silmari_rlm_act.phases.multi_doc import MultiDocPhase
from silmari_rlm_act.phases.research import ResearchPhase
from silmari_rlm_act.phases.tdd_planning import TDDPlanningPhase
from planning_pipeline.models import RequirementHierarchy


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

    def close_issue(self, issue_id: str, reason: str = "") -> dict[str, Any]: ...


class RLMActPipeline:
    """Orchestrates the RLM-Act pipeline phases.

    Coordinates the execution of all pipeline phases in order:
    1. RESEARCH - Gather context about the task
    2. DECOMPOSITION - Break into testable behaviors
    3. TDD_PLANNING - Create Red-Green-Refactor plans
    4. MULTI_DOC - Split plan into phase documents
    5. BEADS_SYNC - Track epochs and tasks with beads
    6. IMPLEMENTATION - Execute TDD cycles

    Supports three autonomy modes:
    - CHECKPOINT: Pause at each phase for review
    - FULLY_AUTONOMOUS: Run all phases without stopping
    - BATCH: Group phases, pause between groups

    Attributes:
        project_path: Root directory of the project
        cwa: Context Window Array integration
        beads_controller: Optional beads controller for tracking
        checkpoint_manager: Manager for checkpoint files
        state: Current pipeline state
        phase_order: Sequence of phases to execute
    """

    # Phase execution order
    PHASE_ORDER = [
        PhaseType.RESEARCH,
        PhaseType.DECOMPOSITION,
        PhaseType.TDD_PLANNING,
        PhaseType.MULTI_DOC,
        PhaseType.BEADS_SYNC,
        PhaseType.IMPLEMENTATION,
    ]

    def __init__(
        self,
        project_path: Path,
        cwa: CWAIntegration,
        autonomy_mode: AutonomyMode = AutonomyMode.CHECKPOINT,
        beads_controller: Optional[BeadsControllerProtocol] = None,
    ) -> None:
        """Initialize the RLM-Act pipeline.

        Args:
            project_path: Root directory of the project
            cwa: Context Window Array integration instance
            autonomy_mode: How the pipeline handles pauses
            beads_controller: Optional beads controller for tracking
        """
        self.project_path = Path(project_path).resolve()
        self.cwa = cwa
        self.beads_controller = beads_controller
        self.checkpoint_manager = CheckpointManager(self.project_path)

        # Initialize pipeline state
        self.state = PipelineState(
            project_path=str(self.project_path),
            autonomy_mode=autonomy_mode,
            started_at=datetime.now(),
        )

        # Initialize phase instances
        self._research_phase = ResearchPhase(self.project_path, self.cwa)
        self._decomposition_phase = DecompositionPhase(self.project_path, self.cwa)
        self._tdd_planning_phase = TDDPlanningPhase(self.project_path, self.cwa)
        self._multi_doc_phase = MultiDocPhase(self.project_path, self.cwa)

        # Beads and implementation phases require controller
        self._beads_sync_phase: Optional[BeadsSyncPhase] = None
        if beads_controller:
            self._beads_sync_phase = BeadsSyncPhase(
                self.project_path, self.cwa, beads_controller
            )

        self._implementation_phase = ImplementationPhase(self.project_path, self.cwa)

    @property
    def phase_order(self) -> list[PhaseType]:
        """Get the phase execution order."""
        return self.PHASE_ORDER.copy()

    def get_next_phase(self) -> Optional[PhaseType]:
        """Get the next phase to execute.

        Returns:
            Next PhaseType to execute, or None if all complete
        """
        for phase_type in self.PHASE_ORDER:
            if not self.state.is_phase_complete(phase_type):
                return phase_type
        return None

    def _execute_phase(self, phase_type: PhaseType, **kwargs: Any) -> PhaseResult:
        """Execute a specific phase.

        Args:
            phase_type: The phase to execute
            **kwargs: Phase-specific arguments

        Returns:
            PhaseResult with execution outcome
        """
        auto_approve = self.state.autonomy_mode == AutonomyMode.FULLY_AUTONOMOUS

        if phase_type == PhaseType.RESEARCH:
            research_question = kwargs.get("research_question", "")
            additional_context = kwargs.get("additional_context", "")
            return self._research_phase.execute_with_checkpoint(
                research_question=research_question,
                auto_approve=auto_approve,
                additional_context=additional_context,
            )

        elif phase_type == PhaseType.DECOMPOSITION:
            # Get research path from previous phase
            research_result = self.state.get_phase_result(PhaseType.RESEARCH)
            if research_result and research_result.artifacts:
                research_path = Path(research_result.artifacts[0])
            else:
                research_path = Path(kwargs.get("research_path", ""))

            return self._decomposition_phase.execute_with_checkpoint(
                research_path=research_path,
                auto_approve=auto_approve,
            )

        elif phase_type == PhaseType.TDD_PLANNING:
            # Get hierarchy path from previous phase (file on disk)
            decomp_result = self.state.get_phase_result(PhaseType.DECOMPOSITION)
            hierarchy_path = None

            if decomp_result and decomp_result.metadata.get("hierarchy_path"):
                hierarchy_path = decomp_result.metadata["hierarchy_path"]
            else:
                hierarchy_path = kwargs.get("hierarchy_path")

            if not hierarchy_path:
                return PhaseResult(
                    phase_type=PhaseType.TDD_PLANNING,
                    status=PhaseStatus.FAILED,
                    errors=["No hierarchy_path found in decomposition metadata"],
                    started_at=datetime.now(),
                    completed_at=datetime.now(),
                )

            plan_name = kwargs.get("plan_name", "feature")

            # TDD planning and multi-doc are document generation phases that
            # run automatically after decomposition is approved. No separate
            # checkpoint needed - they just produce output files.
            return self._tdd_planning_phase.execute(
                plan_name=plan_name,
                hierarchy_path=hierarchy_path,
            )

        elif phase_type == PhaseType.MULTI_DOC:
            # Get plan path and hierarchy path from previous phases
            plan_result = self.state.get_phase_result(PhaseType.TDD_PLANNING)
            decomp_result = self.state.get_phase_result(PhaseType.DECOMPOSITION)

            if plan_result and plan_result.artifacts:
                plan_path = plan_result.artifacts[0]
            else:
                plan_path = kwargs.get("plan_path", "")

            if plan_result and plan_result.metadata.get("hierarchy_path"):
                hierarchy_path = plan_result.metadata["hierarchy_path"]
            elif decomp_result and decomp_result.metadata.get("hierarchy_path"):
                hierarchy_path = decomp_result.metadata["hierarchy_path"]
            else:
                hierarchy_path = kwargs.get("hierarchy_path", "")

            plan_name = kwargs.get("plan_name", "feature")

            return self._multi_doc_phase.execute(
                plan_path=plan_path,
                hierarchy_path=hierarchy_path,
                plan_name=plan_name,
            )

        elif phase_type == PhaseType.BEADS_SYNC:
            if not self._beads_sync_phase:
                return PhaseResult(
                    phase_type=PhaseType.BEADS_SYNC,
                    status=PhaseStatus.FAILED,
                    errors=["No beads controller configured"],
                )

            # Get phase docs from previous phase
            multi_doc_result = self.state.get_phase_result(PhaseType.MULTI_DOC)
            if multi_doc_result and multi_doc_result.artifacts:
                phase_docs = multi_doc_result.artifacts
            elif kwargs.get("hierarchy_path"):
                # Markdown plan: find phase docs in the same directory
                hierarchy_path = Path(kwargs["hierarchy_path"])
                plan_dir = hierarchy_path.parent
                phase_docs = sorted(
                    str(p) for p in plan_dir.glob("*.md")
                    if p.name != hierarchy_path.name  # Exclude the overview itself initially
                )
                # Include the hierarchy_path as well for the overview
                phase_docs = [str(hierarchy_path)] + phase_docs
            else:
                phase_docs = kwargs.get("phase_docs", [])

            plan_name = kwargs.get("plan_name", "feature")

            return self._beads_sync_phase.execute(
                phase_docs=phase_docs,
                plan_name=plan_name,
            )

        elif phase_type == PhaseType.IMPLEMENTATION:
            # Get phase docs and beads IDs
            multi_doc_result = self.state.get_phase_result(PhaseType.MULTI_DOC)
            beads_result = self.state.get_phase_result(PhaseType.BEADS_SYNC)

            phase_paths: list[str] = []
            if multi_doc_result and multi_doc_result.artifacts:
                phase_paths = multi_doc_result.artifacts
            elif kwargs.get("hierarchy_path"):
                # Markdown plan: use hierarchy_path directly as the plan path
                phase_paths = [kwargs["hierarchy_path"]]

            beads_issue_ids: list[str] = []
            if beads_result and beads_result.metadata.get("phase_issue_ids"):
                beads_issue_ids = beads_result.metadata["phase_issue_ids"]

            # Get epic ID from beads sync or state
            beads_epic_id = self.state.beads_epic_id
            if beads_result and beads_result.metadata.get("epic_id"):
                beads_epic_id = beads_result.metadata["epic_id"]

            return self._implementation_phase.execute(
                phase_paths=phase_paths,
                mode=self.state.autonomy_mode,
                beads_issue_ids=beads_issue_ids,
                beads_epic_id=beads_epic_id,
            )

        else:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.FAILED,
                errors=[f"Unknown phase type: {phase_type}"],
            )

    def _track_cwa_entries(self, phase_type: PhaseType, result: PhaseResult) -> None:
        """Track CWA entry IDs from phase result.

        Args:
            phase_type: The executed phase
            result: Phase result with potential entry IDs
        """
        # Track entry ID from metadata
        if "cwa_entry_id" in result.metadata:
            self.state.track_context_entry(phase_type, result.metadata["cwa_entry_id"])

        # Track multiple entry IDs
        if "cwa_entry_ids" in result.metadata:
            for entry_id in result.metadata["cwa_entry_ids"]:
                self.state.track_context_entry(phase_type, entry_id)

    def _is_markdown_plan(self, path: str) -> bool:
        """Detect if plan file is Markdown (not JSON).

        Returns True if file is Markdown, False if JSON.
        """
        path_obj = Path(path)

        # Check extension first
        if path_obj.suffix.lower() in [".md", ".markdown"]:
            return True
        if path_obj.suffix.lower() == ".json":
            return False

        # Try to parse as JSON
        try:
            with open(path_obj, "r", encoding="utf-8") as f:
                json.load(f)
            return False  # Valid JSON
        except json.JSONDecodeError:
            return True  # Not JSON, assume Markdown

    def _validate_hierarchy_path(
        self, hierarchy_path: str
    ) -> tuple[Optional[RequirementHierarchy], Optional[str], dict[str, Any]]:
        """Validate and load a hierarchy JSON file.

        Args:
            hierarchy_path: Path to the hierarchy JSON file

        Returns:
            Tuple of (hierarchy, error_message, metadata)
            If validation succeeds: (hierarchy, None, metadata)
            If validation fails: (None, error_message, {})
        """
        path = Path(hierarchy_path)

        try:
            # Load JSON
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Deserialize to RequirementHierarchy (triggers __post_init__ validation)
            hierarchy = RequirementHierarchy.from_dict(data)

            # Count nodes for metadata
            total_nodes = 0
            for req in hierarchy.requirements:
                total_nodes += 1  # Parent
                total_nodes += len(req.children)
                for child in req.children:
                    total_nodes += len(child.children)

            metadata = {
                "hierarchy_path": str(path),
                "requirements_count": len(hierarchy.requirements),
                "total_nodes": total_nodes,
                "validated": True,
                "validation_timestamp": datetime.now().isoformat(),  # REQ_004.3.6
            }

            # REQ_006.3: Propagate source field from hierarchy metadata
            if hierarchy.metadata.get("source"):
                metadata["source"] = hierarchy.metadata["source"]

            # REQ_006.4: Propagate decomposition_stats from hierarchy metadata
            if hierarchy.metadata.get("decomposition_stats"):
                metadata["decomposition_stats"] = hierarchy.metadata["decomposition_stats"]

            return hierarchy, None, metadata

        except json.JSONDecodeError as e:
            return None, f"Plan validation failed: Invalid JSON - {e}", {}
        except ValueError as e:
            return None, f"Plan validation failed: {e}", {}
        except FileNotFoundError:
            return None, f"Plan validation failed: File not found - {hierarchy_path}", {}
        except Exception as e:
            return None, f"Plan validation failed: {e}", {}

    def _perform_semantic_validation(
        self,
        hierarchy_path: str,
        research_path: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Perform BAML-level semantic validation of requirements.

        REQ_003.1: Invoke ProcessGate1RequirementValidationPrompt function to
        perform semantic validation of requirements against the research scope.

        REQ_003.4: Handle validation latency appropriately with warning-only mode.

        Args:
            hierarchy_path: Path to the hierarchy JSON file
            research_path: Optional path to research document for scope context

        Returns:
            Dictionary with validation results and metadata, or None if validation fails
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            from silmari_rlm_act.validation import (
                SemanticValidationService,
                ValidationConfig,
                ValidationError,
            )

            # Load scope text from research path if available
            scope_text = ""
            if research_path:
                try:
                    with open(research_path, "r", encoding="utf-8") as f:
                        scope_text = f.read()
                except Exception as e:
                    logger.warning(f"Could not read research document: {e}")
                    scope_text = "No research scope available"
            else:
                scope_text = "Validating requirements without research scope context"

            # Configure validation with warning-only mode (don't block pipeline)
            config = ValidationConfig(
                timeout_seconds=60,
                max_retries=3,
                warning_only=True,  # Don't fail the pipeline on validation errors
                show_progress=True,
            )

            service = SemanticValidationService(config=config)

            try:
                summary = service.validate_with_timeout(
                    scope_text=scope_text,
                    hierarchy_path=Path(hierarchy_path),
                )

                return {
                    "total_requirements": summary.total_requirements,
                    "valid_count": summary.valid_count,
                    "invalid_count": summary.invalid_count,
                    "all_valid": summary.all_valid,
                    "validity_rate": summary.validity_rate,
                    "processing_time_ms": summary.processing_time_ms,
                    "llm_model": summary.llm_model,
                }

            except ValidationError as e:
                logger.warning(f"Semantic validation failed: {e}")
                return {
                    "error": str(e),
                    "validation_skipped": True,
                }

            finally:
                service.close()

        except ImportError as e:
            logger.warning(f"Validation module not available: {e}")
            return None
        except Exception as e:
            logger.warning(f"Semantic validation error: {e}")
            return None

    def run_single_phase(
        self,
        phase_type: PhaseType,
        **kwargs: Any,
    ) -> PhaseResult:
        """Run a single pipeline phase.

        Args:
            phase_type: The phase to execute
            **kwargs: Phase-specific arguments

        Returns:
            PhaseResult with execution outcome
        """
        self.state.current_phase = phase_type

        try:
            result = self._execute_phase(phase_type, **kwargs)
        except Exception as e:
            result = PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.FAILED,
                errors=[str(e)],
                started_at=datetime.now(),
                completed_at=datetime.now(),
            )

        # Update state
        self.state.set_phase_result(phase_type, result)
        self._track_cwa_entries(phase_type, result)

        # Create checkpoint
        phase_name = f"{phase_type.value}-{'complete' if result.is_complete else 'failed'}"
        self.checkpoint_manager.write_checkpoint(
            state=self.state,
            phase=phase_name,
            errors=result.errors if result.is_failed else None,
        )

        self.state.current_phase = None
        return result

    def run(
        self,
        research_question: str,
        plan_name: str = "feature",
        **kwargs: Any,
    ) -> PhaseResult:
        """Run the full pipeline from research through implementation.

        Args:
            research_question: Initial research question
            plan_name: Name for the TDD plan
            **kwargs: Additional arguments for phases

        Returns:
            PhaseResult representing overall pipeline outcome
        """
        started_at = datetime.now()
        all_artifacts: list[str] = []
        all_errors: list[str] = []

        # Check if hierarchy_path is provided (skip research AND decomposition phases)
        hierarchy_path = kwargs.get("hierarchy_path")

        # Check if research_path is provided (skip research phase only)
        research_path = kwargs.get("research_path")

        # Check if semantic validation is requested
        validate_full = kwargs.get("validate_full", False)

        # Track if this is a Markdown plan (skip all phases except IMPLEMENTATION)
        is_markdown_plan = False

        # If hierarchy_path is provided, check if it's Markdown or JSON
        if hierarchy_path:
            is_markdown_plan = self._is_markdown_plan(hierarchy_path)

            if is_markdown_plan:
                # Markdown plan: skip phases before BEADS_SYNC, then run BEADS_SYNC -> IMPLEMENTATION
                skipped_phases = [
                    PhaseType.RESEARCH,
                    PhaseType.DECOMPOSITION,
                    PhaseType.TDD_PLANNING,
                    PhaseType.MULTI_DOC,
                ]
                for phase_type in skipped_phases:
                    synthetic_result = PhaseResult(
                        phase_type=phase_type,
                        status=PhaseStatus.COMPLETE,
                        artifacts=[],
                        started_at=started_at,
                        completed_at=datetime.now(),
                        metadata={
                            "skipped": True,
                            "reason": "markdown_plan provided",
                        },
                    )
                    self.state.set_phase_result(phase_type, synthetic_result)

                # Create checkpoint for markdown plan skip
                self.checkpoint_manager.write_checkpoint(
                    state=self.state,
                    phase="markdown-plan-skip",
                )

                all_artifacts.append(hierarchy_path)

            else:
                # JSON hierarchy: validate and skip only RESEARCH and DECOMPOSITION
                hierarchy, error, validation_metadata = self._validate_hierarchy_path(
                    hierarchy_path
                )

                if error:
                    # Validation failed - REQ_004.4
                    completed_at = datetime.now()
                    return PhaseResult(
                        phase_type=PhaseType.DECOMPOSITION,
                        status=PhaseStatus.FAILED,
                        errors=[error],
                        started_at=started_at,
                        completed_at=completed_at,
                        duration_seconds=(completed_at - started_at).total_seconds(),
                        metadata={
                            "validation_failed": True,
                            "validated": False,  # REQ_004.4.9
                            "error_count": 1,  # REQ_004.4.10
                            "hierarchy_path": hierarchy_path,
                        },
                    )

                # REQ_003.3: Perform semantic validation if --validate-full is enabled
                if validate_full:
                    semantic_result = self._perform_semantic_validation(
                        hierarchy_path=hierarchy_path,
                        research_path=research_path,
                    )
                    if semantic_result:
                        validation_metadata["semantic_validation"] = semantic_result

                # Create synthetic RESEARCH result
                synthetic_research = PhaseResult(
                    phase_type=PhaseType.RESEARCH,
                    status=PhaseStatus.COMPLETE,
                    artifacts=[],
                    started_at=started_at,
                    completed_at=datetime.now(),
                    metadata={
                        "skipped": True,
                        "reason": "hierarchy_path provided",
                    },
                )
                self.state.set_phase_result(PhaseType.RESEARCH, synthetic_research)

                # Create checkpoint for skipped research phase
                self.checkpoint_manager.write_checkpoint(
                    state=self.state,
                    phase="research-skipped",
                )

                # Create synthetic DECOMPOSITION result
                synthetic_decomp = PhaseResult(
                    phase_type=PhaseType.DECOMPOSITION,
                    status=PhaseStatus.COMPLETE,
                    artifacts=[hierarchy_path],
                    started_at=started_at,
                    completed_at=datetime.now(),
                    metadata={
                        "skipped": True,
                        "reason": "hierarchy_path provided",
                        **validation_metadata,
                    },
                )
                self.state.set_phase_result(PhaseType.DECOMPOSITION, synthetic_decomp)
                all_artifacts.append(hierarchy_path)

                # Create checkpoint for skipped decomposition phase
                self.checkpoint_manager.write_checkpoint(
                    state=self.state,
                    phase="decomposition-skipped",
                )

        # If only research_path is provided (no hierarchy_path), create synthetic research result
        elif research_path:
            research_path_obj = Path(research_path).resolve()
            synthetic_result = PhaseResult(
                phase_type=PhaseType.RESEARCH,
                status=PhaseStatus.COMPLETE,
                artifacts=[str(research_path_obj)],
                started_at=started_at,
                completed_at=datetime.now(),
                metadata={
                    "skipped": True,
                    "reason": "research_path provided",
                },
            )
            self.state.set_phase_result(PhaseType.RESEARCH, synthetic_result)
            all_artifacts.append(str(research_path_obj))

            # Create checkpoint for skipped research phase
            self.checkpoint_manager.write_checkpoint(
                state=self.state,
                phase="research-skipped",
            )

        # Prepare kwargs for each phase
        phase_kwargs = {
            PhaseType.RESEARCH: {"research_question": research_question},
            PhaseType.DECOMPOSITION: {"research_path": research_path} if research_path else {},
            PhaseType.TDD_PLANNING: {"plan_name": plan_name, "hierarchy_path": hierarchy_path} if hierarchy_path else {"plan_name": plan_name},
            PhaseType.MULTI_DOC: {"hierarchy_path": hierarchy_path} if hierarchy_path else {},
            PhaseType.BEADS_SYNC: {"plan_name": plan_name},
            PhaseType.IMPLEMENTATION: {"phase_paths": [hierarchy_path]} if is_markdown_plan else {},
        }

        # Update with any provided kwargs
        for key, value in kwargs.items():
            for phase_type in PhaseType:
                phase_kwargs[phase_type][key] = value

        # Execute phases in order
        for phase_type in self.PHASE_ORDER:
            # Skip already completed phases
            if self.state.is_phase_complete(phase_type):
                continue

            result = self.run_single_phase(phase_type, **phase_kwargs[phase_type])

            # Collect artifacts
            all_artifacts.extend(result.artifacts)

            if result.is_failed:
                all_errors.extend(result.errors)
                completed_at = datetime.now()
                return PhaseResult(
                    phase_type=phase_type,
                    status=PhaseStatus.FAILED,
                    artifacts=all_artifacts,
                    errors=all_errors,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_seconds=(completed_at - started_at).total_seconds(),
                    metadata={
                        "failed_phase": phase_type.value,
                        "phases_completed": sum(
                            1 for p in self.PHASE_ORDER if self.state.is_phase_complete(p)
                        ),
                    },
                )

            # Check for user exit in checkpoint mode
            if result.metadata.get("user_exit"):
                completed_at = datetime.now()
                return PhaseResult(
                    phase_type=phase_type,
                    status=PhaseStatus.COMPLETE,
                    artifacts=all_artifacts,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_seconds=(completed_at - started_at).total_seconds(),
                    metadata={
                        "user_exit": True,
                        "stopped_at_phase": phase_type.value,
                    },
                )

        # All phases complete
        completed_at = datetime.now()
        return PhaseResult(
            phase_type=PhaseType.IMPLEMENTATION,
            status=PhaseStatus.COMPLETE,
            artifacts=all_artifacts,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=(completed_at - started_at).total_seconds(),
            metadata={
                "all_phases_complete": True,
                "phases_count": len(self.PHASE_ORDER),
            },
        )

    def resume_from_checkpoint(self) -> bool:
        """Resume pipeline from most recent checkpoint.

        Returns:
            True if resumed successfully, False if no checkpoint found
        """
        checkpoint = self.checkpoint_manager.detect_resumable_checkpoint()
        if not checkpoint:
            return False

        # Load state from checkpoint
        self.state = self.checkpoint_manager.load_checkpoint(checkpoint["file_path"])
        return True

    def get_status_summary(self) -> dict[str, Any]:
        """Get a summary of pipeline status.

        Returns:
            Dictionary with status information
        """
        completed = [p for p in self.PHASE_ORDER if self.state.is_phase_complete(p)]
        pending = [p for p in self.PHASE_ORDER if not self.state.is_phase_complete(p)]
        next_phase = self.get_next_phase()

        return {
            "project_path": str(self.project_path),
            "autonomy_mode": self.state.autonomy_mode.value,
            "phases_completed": [p.value for p in completed],
            "phases_pending": [p.value for p in pending],
            "next_phase": next_phase.value if next_phase else None,
            "all_complete": self.state.all_phases_complete(),
            "beads_epic_id": self.state.beads_epic_id,
            "checkpoint_id": self.state.checkpoint_id,
        }
