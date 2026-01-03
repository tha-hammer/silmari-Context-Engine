"""Autonomous Loop Runner with orchestrator integration.

This module provides an async-first LoopRunner that can be integrated with
IntegratedOrchestrator for LLM-driven plan discovery, phase progression,
and status tracking. Complexity is computed from the beads dependency graph.

Usage:
    # With orchestrator (automatic plan discovery)
    from planning_pipeline.autonomous_loop import LoopRunner
    from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

    orchestrator = IntegratedOrchestrator(project_path)
    runner = LoopRunner(orchestrator=orchestrator)
    await runner.run()

    # With plan prefix (iterate through plan phase files)
    runner = LoopRunner(
        plan_dir="thoughts/searchable/shared/plans",
        plan_prefix="2026-01-03-tdd-execute-phase-implementation"
    )
    await runner.run()

    # Without orchestrator (backward compatible - single plan file)
    runner = LoopRunner(plan_path="/path/to/plan.md")
    await runner.run()
"""

import json
import logging
import subprocess
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Optional

from planning_pipeline.phase_execution.prompt_builder import build_phase_prompt, build_overview_prompt
from planning_pipeline.phase_execution.claude_invoker import invoke_claude
from planning_pipeline.phase_execution.result_checker import check_execution_result
from planning_pipeline.phase_execution.plan_discovery import (
    PlanPhase,
    discover_plan_phases,
    get_next_phase,
)

if TYPE_CHECKING:
    from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator


logger = logging.getLogger(__name__)


# =============================================================================
# Test Detection and Execution
# =============================================================================


def detect_test_command(project_path: Path) -> Optional[str]:
    """Detect the appropriate test command for the project.

    Args:
        project_path: Path to the project directory

    Returns:
        Test command string or None if not detected
    """
    if (project_path / "Cargo.toml").exists():
        return "cargo test"
    elif (project_path / "package.json").exists():
        return "npm test"
    elif (project_path / "go.mod").exists():
        return "go test ./..."
    elif (project_path / "requirements.txt").exists() or (project_path / "pyproject.toml").exists():
        return "pytest"
    elif (project_path / "Makefile").exists():
        return "make test"
    return None


def run_tests(project_path: Path) -> tuple[bool, str]:
    """Run tests and return (passed, output).

    Args:
        project_path: Path to the project directory

    Returns:
        Tuple of (passed: bool, output: str)
    """
    test_cmd = detect_test_command(project_path)

    if not test_cmd:
        return True, "No test command detected, skipping"

    try:
        result = subprocess.run(
            test_cmd,
            shell=True,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300  # 5 min timeout for tests
        )

        passed = result.returncode == 0
        output = result.stdout + result.stderr

        return passed, output
    except subprocess.TimeoutExpired:
        return False, "Tests timed out after 5 minutes"
    except Exception as e:
        return False, f"Error running tests: {e}"


# =============================================================================
# Subagent Instructions
# =============================================================================


def get_subagent_instructions(
    complexity: str,
    feature_id: str,
    description: str,
    test_cmd: Optional[str]
) -> str:
    """Generate subagent instructions based on complexity level.

    Args:
        complexity: 'high', 'medium', or 'low'
        feature_id: The feature/issue ID
        description: Feature description
        test_cmd: The test command or None

    Returns:
        Formatted subagent instructions string
    """
    if complexity == 'high':
        return f"""## STEP 7: Invoke Subagents (MANDATORY - High Complexity)
You MUST invoke these subagents:

### Code Review
```
@code-reviewer Review the changes for feature {feature_id}
```
Wait for review. Address any issues.

### Test Runner
```
@test-runner Run the test suite and analyze results
```

### Feature Verifier
```
@feature-verifier Verify feature {feature_id}: {description}
```

After all subagents pass, proceed to STEP 8."""

    elif complexity == 'medium':
        return f"""## STEP 7: Verify Tests (Medium Complexity)
```
@test-runner Run the test suite and analyze results
```

After tests pass, proceed to STEP 8."""

    else:  # low
        return """## STEP 7: Verify Tests (Low Complexity)
Tests should already pass from STEP 6. If they do, proceed directly to STEP 8.
No subagent review needed for simple changes - just mark complete."""


class LoopState(Enum):
    """States for the autonomous loop runner."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class LoopRunner:
    """Autonomous loop runner for executing plans with optional orchestrator integration.

    Supports three modes:
    1. With orchestrator: Automatic plan discovery, phase progression, status updates
    2. With plan_dir + plan_prefix: Iterate through numbered phase files
    3. Without orchestrator: Manual plan path, single-phase execution (backward compat)

    Attributes:
        plan_path: Explicit path to plan file (optional if orchestrator provided)
        plan_dir: Directory containing plan phase files
        plan_prefix: Prefix for plan phase files (e.g., "2026-01-03-tdd-feature")
        current_phase: Currently executing phase identifier
        orchestrator: IntegratedOrchestrator instance for advanced features
        state: Current execution state
    """

    def __init__(
        self,
        plan_path: Optional[str] = None,
        plan_dir: Optional[str] = None,
        plan_prefix: Optional[str] = None,
        current_phase: Optional[str] = None,
        orchestrator: Optional["IntegratedOrchestrator"] = None,
        project_path: Optional[Path] = None,
        skip_overview: bool = False,
    ):
        """Initialize the LoopRunner.

        Args:
            plan_path: Path to a single plan file. Used for single-phase execution.
            plan_dir: Directory containing plan phase files (e.g., "thoughts/shared/plans").
            plan_prefix: Prefix for plan files to iterate through.
            current_phase: Initial phase to execute (optional).
            orchestrator: IntegratedOrchestrator for advanced features (optional).
            project_path: Path to project directory for git/beads operations (optional).
            skip_overview: If True, skip the overview phase (phase 00).
        """
        self.plan_path = plan_path
        self.plan_dir = Path(plan_dir) if plan_dir else None
        self.plan_prefix = plan_prefix
        self.current_phase = current_phase
        self.orchestrator = orchestrator
        self.state = LoopState.IDLE
        self.skip_overview = skip_overview

        # Project path for git/beads operations
        self._project_path = project_path or Path.cwd()

        # Internal state for orchestrator integration
        self._current_feature: Optional[Any] = None

        # Plan phase iteration state
        self._plan_phases: List[PlanPhase] = []
        self._current_phase_index: int = 0
        self._current_plan_phase: Optional[PlanPhase] = None

    def get_issue_complexity(self, issue_id: str) -> str:
        """Compute complexity from beads dependency graph.

        Complexity factors:
        - Number of dependencies (issues this depends on)
        - Number of dependents (issues that depend on this)

        Args:
            issue_id: The beads issue ID

        Returns:
            'high', 'medium', or 'low' complexity level
        """
        if self.orchestrator is None:
            return "medium"  # Default when no orchestrator

        try:
            # Get the issue details
            issue_result = self.orchestrator.bd.show_issue(issue_id)
            if not issue_result.get("success"):
                return "medium"

            issue = issue_result.get("data", {})
            if isinstance(issue, str):
                return "medium"  # Fallback if data is not a dict

            # Count direct dependencies
            dependencies = issue.get("dependencies", [])
            dep_count = len(dependencies) if isinstance(dependencies, list) else 0

            # Count dependents (issues blocked by this one)
            all_issues_result = self.orchestrator.bd.list_issues()
            if not all_issues_result.get("success"):
                dependent_count = 0
            else:
                all_issues = all_issues_result.get("data", [])
                if not isinstance(all_issues, list):
                    all_issues = []

                dependent_count = 0
                for i in all_issues:
                    if not isinstance(i, dict):
                        continue
                    issue_deps = i.get("dependencies", [])
                    if not isinstance(issue_deps, list):
                        continue
                    for dep in issue_deps:
                        if isinstance(dep, dict) and dep.get("depends_on_id") == issue_id:
                            dependent_count += 1
                            break
                        elif isinstance(dep, str) and dep == issue_id:
                            dependent_count += 1
                            break

            # Compute complexity score
            # Issues that block many others are high risk
            score = dep_count + (dependent_count * 2)

            if score >= 5:
                return "high"
            elif score >= 2:
                return "medium"
            return "low"

        except Exception as e:
            logger.warning(f"Failed to compute complexity for {issue_id}: {e}")
            return "medium"

    def _track_metrics(self, event: str, feature_id: str, extra: Optional[str] = None) -> None:
        """Track metrics for feedback loops via .agent/hooks/.

        Args:
            event: Event type (e.g., 'session_start', 'session_complete')
            feature_id: The feature/issue ID
            extra: Optional extra data
        """
        metrics_script = self._project_path / ".agent" / "hooks" / "track-metrics.sh"
        if metrics_script.exists():
            try:
                cmd = ["bash", str(metrics_script), event, feature_id]
                if extra:
                    cmd.append(extra)
                subprocess.run(cmd, cwd=str(self._project_path), capture_output=True, timeout=30)
                logger.debug(f"Tracked metric: {event} for {feature_id}")
            except Exception as e:
                logger.warning(f"Failed to track metric: {e}")

    def _save_session_diff(self, session_num: int, feature_id: str) -> None:
        """Save a diff artifact for the current session.

        Args:
            session_num: Session number
            feature_id: The feature/issue ID
        """
        diff_script = self._project_path / ".agent" / "hooks" / "save-session-diff.sh"
        if diff_script.exists():
            try:
                subprocess.run(
                    ["bash", str(diff_script), str(session_num), feature_id],
                    cwd=str(self._project_path),
                    capture_output=True,
                    timeout=60
                )
            except Exception as e:
                logger.warning(f"Failed to save session diff: {e}")

    async def _discover_or_validate_plan(self) -> str:
        """Discover plan from orchestrator, plan_dir, or validate explicit path.

        Returns:
            Path to the plan file to execute.

        Raises:
            ValueError: If no plan_path/plan_dir and no orchestrator, or no plans available.
        """
        # Mode 1: Explicit plan path
        if self.plan_path is not None:
            return self.plan_path

        # Mode 2: Plan directory with prefix (iterate through phase files)
        if self.plan_dir is not None and self.plan_prefix is not None:
            self._plan_phases = discover_plan_phases(self.plan_dir, self.plan_prefix)
            if not self._plan_phases:
                raise ValueError(
                    f"No plan phases found in {self.plan_dir} with prefix {self.plan_prefix}"
                )

            # Filter out overview if skip_overview is set
            if self.skip_overview:
                self._plan_phases = [p for p in self._plan_phases if not p.is_overview]

            if not self._plan_phases:
                raise ValueError("No non-overview phases found")

            logger.info(f"Discovered {len(self._plan_phases)} plan phases")
            for phase in self._plan_phases:
                logger.debug(f"  Phase {phase.order}: {phase.name}")

            # Return the first phase path
            self._current_phase_index = 0
            self._current_plan_phase = self._plan_phases[0]
            return str(self._current_plan_phase.path)

        # Mode 3: Orchestrator-based discovery
        if self.orchestrator is None:
            raise ValueError(
                "No plan_path, plan_dir/plan_prefix, or orchestrator available"
            )

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

    def _build_phase_prompt(self) -> str:
        """Build prompt for the current phase.

        Uses plan_phases metadata if available for better context.
        """
        if self.plan_path is None:
            raise ValueError("Cannot build phase prompt: plan_path is None")

        # If we have plan phase metadata, use it for richer context
        if self._current_plan_phase is not None:
            total_phases = len(self._plan_phases)
            # Phase number is 1-indexed for display, skip counting overview
            non_overview_phases = [p for p in self._plan_phases if not p.is_overview]
            if self._current_plan_phase.is_overview:
                # For overview, use the overview-specific prompt
                return build_overview_prompt(
                    self.plan_path,
                    len(non_overview_phases),
                )
            else:
                # For regular phases, include progress info
                current_num = non_overview_phases.index(self._current_plan_phase) + 1
                return build_phase_prompt(
                    self.plan_path,
                    current_phase=self.current_phase,
                    phase_info=self._current_plan_phase,
                    total_phases=len(non_overview_phases),
                    current_phase_num=current_num,
                )

        # Fallback to simple prompt
        return build_phase_prompt(self.plan_path, self.current_phase)

    async def _execute_phase(self) -> bool:
        """Execute the current phase.

        Builds prompt, invokes Claude, and validates result.

        Returns:
            True if phase completed successfully, False otherwise.
        """
        try:
            # Build prompt
            prompt = self._build_phase_prompt()
        except FileNotFoundError as e:
            logger.error(f"Plan file not found: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to build prompt: {e}")
            return False

        # Invoke Claude
        logger.info(f"Executing phase: {self.current_phase}")
        claude_result = invoke_claude(prompt, timeout=3600)  # 1 hour timeout

        # Check result
        return check_execution_result(claude_result, project_path=self._project_path)

    def _advance_to_next_plan_phase(self) -> bool:
        """Advance to the next plan phase.

        Returns:
            True if there's a next phase, False if we've completed all phases.
        """
        if not self._plan_phases:
            return False

        self._current_phase_index += 1
        if self._current_phase_index >= len(self._plan_phases):
            return False

        self._current_plan_phase = self._plan_phases[self._current_phase_index]
        self.plan_path = str(self._current_plan_phase.path)
        self.current_phase = self._current_plan_phase.phase_id
        return True

    async def _execute_loop(self) -> None:
        """Execute the main loop, progressing through phases.

        Includes complexity detection, metrics tracking, and session management.
        Supports three modes:
        1. Orchestrator mode: Get phases from IntegratedOrchestrator
        2. Plan phase mode: Iterate through discovered plan phase files
        3. Single plan mode: Execute one plan file
        """
        session_num = 0
        while self.state == LoopState.RUNNING:
            session_num += 1

            # Mode 1: Get next phase from orchestrator
            if self.orchestrator:
                next_phase = await self._get_next_phase()
                if next_phase is None:
                    self.state = LoopState.COMPLETED
                    break
                self.current_phase = next_phase
                self._update_feature_status("IN_PROGRESS")

            feature_id = self.current_phase or "unknown"

            # Track session start
            self._track_metrics("session_start", feature_id)

            # Log phase info
            if self._current_plan_phase:
                total = len(self._plan_phases)
                idx = self._current_phase_index + 1
                logger.info(f"Executing phase {idx}/{total}: {self._current_plan_phase.name}")
            elif self.orchestrator and self._current_feature:
                complexity = self.get_issue_complexity(feature_id)
                logger.info(f"Executing {feature_id} [{complexity.upper()}]")

            # Execute current phase
            success = await self._execute_phase()

            if success:
                if self.orchestrator:
                    self._update_feature_status("COMPLETED")
                    self._track_metrics("feature_complete", feature_id)
                self._track_metrics("session_complete", feature_id)
                self._save_session_diff(session_num, feature_id)

                # Mode 2: Plan phase iteration - advance to next phase
                if self._plan_phases:
                    if not self._advance_to_next_plan_phase():
                        logger.info("All plan phases completed successfully")
                        self.state = LoopState.COMPLETED
                        break
                    # Continue to next iteration
                    continue
            else:
                if self.orchestrator:
                    self._update_feature_status("FAILED")
                self._track_metrics("session_failed", feature_id)
                self.state = LoopState.FAILED
                break

            # Mode 3: Single plan, no orchestrator - complete after one execution
            if self.orchestrator is None and not self._plan_phases:
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
