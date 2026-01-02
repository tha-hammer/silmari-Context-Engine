"""Autonomous Loop Runner with orchestrator integration.

This module provides an async-first LoopRunner that can be integrated with
IntegratedOrchestrator for LLM-driven plan discovery, phase progression,
and status tracking.

Usage:
    # With orchestrator (automatic plan discovery)
    from planning_pipeline.autonomous_loop import LoopRunner
    from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

    orchestrator = IntegratedOrchestrator(project_path)
    runner = LoopRunner(orchestrator=orchestrator)
    await runner.run()

    # Without orchestrator (backward compatible)
    runner = LoopRunner(plan_path="/path/to/plan.md")
    await runner.run()
"""

import logging
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator


logger = logging.getLogger(__name__)


class LoopState(Enum):
    """States for the autonomous loop runner."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class LoopRunner:
    """Autonomous loop runner for executing plans with optional orchestrator integration.

    Supports two modes:
    1. With orchestrator: Automatic plan discovery, phase progression, status updates
    2. Without orchestrator: Manual plan path, single-phase execution (backward compat)

    Attributes:
        plan_path: Explicit path to plan file (optional if orchestrator provided)
        current_phase: Currently executing phase identifier
        orchestrator: IntegratedOrchestrator instance for advanced features
        state: Current execution state
    """

    def __init__(
        self,
        plan_path: Optional[str] = None,
        current_phase: Optional[str] = None,
        orchestrator: Optional["IntegratedOrchestrator"] = None,
    ):
        """Initialize the LoopRunner.

        Args:
            plan_path: Path to the plan file. Required if no orchestrator provided.
            current_phase: Initial phase to execute (optional).
            orchestrator: IntegratedOrchestrator for advanced features (optional).
        """
        self.plan_path = plan_path
        self.current_phase = current_phase
        self.orchestrator = orchestrator
        self.state = LoopState.IDLE

        # Internal state for orchestrator integration
        self._current_feature: Optional[Any] = None

    async def _discover_or_validate_plan(self) -> str:
        """Discover plan from orchestrator or validate explicit path.

        Returns:
            Path to the plan file to execute.

        Raises:
            ValueError: If no plan_path and no orchestrator, or no plans available.
        """
        if self.plan_path is not None:
            return self.plan_path

        if self.orchestrator is None:
            raise ValueError("No plan_path provided and no orchestrator available")

        plans = self.orchestrator.discover_plans()
        if not plans:
            raise ValueError("No plans available for execution")

        return plans[0].path

    async def _get_next_phase(self) -> Optional[str]:
        """Get next phase from orchestrator, skipping blocked features.

        Returns:
            Phase identifier for the next feature, or None if no more features.

        Raises:
            RuntimeError: If too many blocked features encountered (infinite loop protection).
        """
        if self.orchestrator is None:
            return None

        max_attempts = 100  # Prevent infinite loop
        for _ in range(max_attempts):
            feature = self.orchestrator.get_next_feature()
            if feature is None:
                return None

            # Skip blocked features (check status field from beads issue)
            status = feature.get("status", "").upper()
            if status == "BLOCKED":
                continue

            self._current_feature = feature
            # Use id as phase identifier
            return feature.get("id") or feature.get("title")

        raise RuntimeError("Too many blocked features encountered")

    def _update_feature_status(self, status: str) -> None:
        """Update current feature status in orchestrator, logging failures.

        Args:
            status: New status (IN_PROGRESS, COMPLETED, FAILED)
        """
        if self.orchestrator is None or self._current_feature is None:
            return

        try:
            feature_id = self._current_feature.get("id")
            if feature_id:
                self.orchestrator.bd.update_status(feature_id, status.lower())
                logger.debug(f"Updated {feature_id} to {status}")
        except Exception as e:
            logger.warning(
                f"Failed to update feature status for {self._current_feature.get('id')}: {e}"
            )

    async def _execute_phase(self) -> bool:
        """Execute the current phase.

        Returns:
            True if phase completed successfully, False otherwise.
        """
        # Placeholder for actual phase execution
        # In real implementation, this would invoke Claude Code
        logger.info(f"Executing phase: {self.current_phase}")
        return True

    async def _execute_loop(self) -> None:
        """Execute the main loop, progressing through phases."""
        while self.state == LoopState.RUNNING:
            # Get next phase from orchestrator if available
            if self.orchestrator:
                next_phase = await self._get_next_phase()
                if next_phase is None:
                    self.state = LoopState.COMPLETED
                    break
                self.current_phase = next_phase
                self._update_feature_status("IN_PROGRESS")

            # Execute current phase
            success = await self._execute_phase()

            if success:
                if self.orchestrator:
                    self._update_feature_status("COMPLETED")
            else:
                if self.orchestrator:
                    self._update_feature_status("FAILED")
                self.state = LoopState.FAILED
                break

            # If no orchestrator, single-phase execution
            if self.orchestrator is None:
                self.state = LoopState.COMPLETED
                break

    async def _restore_state_from_orchestrator(self) -> None:
        """Restore execution state from orchestrator if available."""
        if self.orchestrator is None:
            return

        current = self.orchestrator.get_current_feature()
        if current is not None:
            status = current.get("status", "").upper()
            if status == "IN_PROGRESS":
                self.current_phase = current.get("id") or current.get("title")
                self._current_feature = current
                logger.info(f"Resuming from {current.get('id')} at phase {self.current_phase}")

    async def run(self) -> None:
        """Run the autonomous loop.

        Discovers plan from orchestrator if not explicitly provided,
        then executes phases until completion or failure.

        Raises:
            ValueError: If no plan available (no plan_path and no orchestrator/plans).
        """
        self.state = LoopState.RUNNING
        self.plan_path = await self._discover_or_validate_plan()
        await self._execute_loop()

    async def pause(self) -> None:
        """Pause execution of the loop.

        The current phase will complete before pausing.
        """
        if self.state == LoopState.RUNNING:
            self.state = LoopState.PAUSED
            logger.info("Loop paused")

    async def resume(self) -> None:
        """Resume execution from paused state.

        If orchestrator is available, restores state from any IN_PROGRESS feature.

        Raises:
            ValueError: If not in PAUSED state.
        """
        if self.state != LoopState.PAUSED:
            raise ValueError(f"Cannot resume from state: {self.state}")

        self.state = LoopState.RUNNING
        await self._restore_state_from_orchestrator()
        await self._execute_loop()
