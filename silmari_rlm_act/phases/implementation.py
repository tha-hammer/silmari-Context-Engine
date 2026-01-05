"""Implementation phase implementation.

This module implements the implementation phase of the silmari-rlm-act pipeline,
which executes TDD cycles for each phase document, supporting three execution modes.
"""

import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Protocol

from context_window_array.implementation_context import ImplementationContext

from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import AutonomyMode, PhaseResult, PhaseStatus, PhaseType


class ClaudeRunnerProtocol(Protocol):
    """Protocol for Claude runner."""

    def run_sync(self, prompt: str, timeout: int = 600) -> dict[str, Any]: ...


class BeadsControllerProtocol(Protocol):
    """Protocol for beads controller."""

    def close_issue(self, issue_id: str, reason: str = "") -> dict[str, Any]: ...


class ImplementationPhase:
    """Execute TDD implementation for plan phases.

    This phase:
    1. Loads phase documents and extracts behaviors
    2. Executes TDD cycles (Red-Green-Refactor) for each behavior
    3. Runs tests after each cycle
    4. Supports three autonomy modes (checkpoint, autonomous, batch)
    5. Stores results in CWA as COMMAND_RESULT entries
    6. Updates beads status on success
    7. Handles implementation failures gracefully
    8. Manages context bounds (<200 entries)
    9. Resumes from checkpoint
    10. Creates git commits after phase completion

    Attributes:
        project_path: Root directory of the project
        cwa: Context Window Array integration
        IMPLEMENTATION_TIMEOUT: Timeout for Claude invocations (seconds)
        TEST_TIMEOUT: Timeout for test runs (seconds)
        BATCH_SIZE: Number of phases per batch in batch mode
    """

    IMPLEMENTATION_TIMEOUT = 600  # 10 minutes per behavior
    TEST_TIMEOUT = 120  # 2 minutes for test runs
    BATCH_SIZE = 3  # Phases per batch in batch mode

    def __init__(
        self,
        project_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Initialize implementation phase.

        Args:
            project_path: Root directory of the project
            cwa: Context Window Array integration instance
        """
        self.project_path = Path(project_path)
        self.cwa = cwa
        self._runner: Optional[ClaudeRunnerProtocol] = None
        self._beads_controller: Optional[BeadsControllerProtocol] = None

    def _load_phase_document(self, phase_path: str) -> str:
        """Load phase document content.

        Args:
            phase_path: Path to phase document

        Returns:
            Document content as string

        Raises:
            FileNotFoundError: If document doesn't exist
        """
        path = Path(phase_path)
        if not path.is_absolute():
            path = self.project_path / path

        if not path.exists():
            raise FileNotFoundError(f"Phase document not found: {path}")

        return path.read_text(encoding="utf-8")

    def _extract_behaviors(self, phase_path: str) -> list[str]:
        """Extract testable behaviors from phase document.

        Looks for numbered list items under a "Testable Behaviors" section.

        Args:
            phase_path: Path to phase document

        Returns:
            List of behavior strings
        """
        content = self._load_phase_document(phase_path)

        behaviors: list[str] = []
        in_behaviors = False

        for line in content.split("\n"):
            # Look for behaviors section header
            if "Testable Behaviors" in line:
                in_behaviors = True
                continue

            if in_behaviors:
                # Stop at next section
                if line.strip().startswith(("#", "##")):
                    break

                # Extract numbered items
                match = re.match(r"\d+\.\s+(.+)", line.strip())
                if match:
                    behaviors.append(match.group(1))

        return behaviors

    def _build_implementation_prompt(self, behavior: str, context: str) -> str:
        """Build prompt for TDD implementation.

        Args:
            behavior: The behavior to implement
            context: Context from phase document

        Returns:
            Formatted prompt string
        """
        return f"""Implement the following behavior using TDD (Red-Green-Refactor):

## Behavior
{behavior}

## Context
{context}

## Instructions
1. **Red**: Write a failing test for this behavior
2. **Green**: Write minimal code to make the test pass
3. **Refactor**: Clean up the code while keeping tests green

After each step, run the tests to verify.
"""

    def _execute_tdd_cycle(
        self,
        behavior: str,
        phase_context: str,
    ) -> dict[str, Any]:
        """Execute Red-Green-Refactor cycle for a behavior.

        Args:
            behavior: The behavior to implement
            phase_context: Context from phase document

        Returns:
            Dict with success status and output
        """
        if self._runner is None:
            return {"success": False, "error": "No runner configured"}

        prompt = self._build_implementation_prompt(behavior, phase_context)

        try:
            result = self._runner.run_sync(
                prompt,
                timeout=self.IMPLEMENTATION_TIMEOUT,
            )
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _run_tests(self, test_path: str = "tests/") -> tuple[bool, str]:
        """Run test suite.

        Args:
            test_path: Path to tests directory

        Returns:
            Tuple of (passed, output)
        """
        try:
            result = subprocess.run(
                ["pytest", test_path, "-v"],
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=self.TEST_TIMEOUT,
            )
            return result.returncode == 0, result.stdout
        except subprocess.TimeoutExpired:
            return False, "Test run timed out"
        except Exception as e:
            return False, str(e)

    def _pause_for_review(
        self,
        phase_path: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Pause for user review (interactive).

        Args:
            phase_path: Path to completed phase
            result: Result from phase execution

        Returns:
            Dict with continue flag and optional feedback
        """
        from silmari_rlm_act.checkpoints.interactive import prompt_phase_continue

        return prompt_phase_continue(
            phase_name=Path(phase_path).stem,
            artifacts=[phase_path],
        )

    def _execute_single_phase(self, phase_path: str) -> dict[str, Any]:
        """Execute a single phase.

        Args:
            phase_path: Path to phase document

        Returns:
            Dict with success and results
        """
        behaviors = self._extract_behaviors(phase_path)
        context = self._load_phase_document(phase_path)

        results: list[dict[str, Any]] = []
        for behavior in behaviors:
            result = self._execute_tdd_cycle(behavior, context)
            results.append(result)

            # Store result in CWA
            self.cwa.store_command_result(
                command=f"implement: {behavior[:50]}...",
                result=result.get("output", str(result)),
                summary=f"TDD cycle for: {behavior[:40]}...",
            )

            if not result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed on behavior: {behavior}",
                    "results": results,
                }

            # Run tests after each cycle
            passed, output = self._run_tests()
            if not passed:
                return {
                    "success": False,
                    "error": f"Tests failed after: {behavior}",
                    "test_output": output,
                    "results": results,
                }

        return {"success": True, "results": results}

    def _execute_with_mode(
        self,
        phases: list[str],
        mode: AutonomyMode,
    ) -> list[dict[str, Any]]:
        """Execute phases according to mode.

        Args:
            phases: List of phase paths
            mode: Execution mode

        Returns:
            List of results per phase
        """
        all_results: list[dict[str, Any]] = []

        if mode == AutonomyMode.FULLY_AUTONOMOUS:
            # Run all without stopping
            for phase_path in phases:
                result = self._execute_single_phase(phase_path)
                all_results.append(result)
                if not result.get("success"):
                    break

        elif mode == AutonomyMode.CHECKPOINT:
            # Pause after each phase
            for phase_path in phases:
                result = self._execute_single_phase(phase_path)
                all_results.append(result)

                review = self._pause_for_review(phase_path, result)
                if not review.get("continue"):
                    break

        elif mode == AutonomyMode.BATCH:
            # Group phases, pause between batches
            for i in range(0, len(phases), self.BATCH_SIZE):
                batch = phases[i : i + self.BATCH_SIZE]

                for phase_path in batch:
                    result = self._execute_single_phase(phase_path)
                    all_results.append(result)
                    if not result.get("success"):
                        return all_results

                # Pause after batch
                review = self._pause_for_review(
                    batch[-1],
                    {"batch": i // self.BATCH_SIZE},
                )
                if not review.get("continue"):
                    break

        return all_results

    def _build_implementation_context(
        self,
        entry_ids: list[str],
    ) -> ImplementationContext:
        """Build implementation context respecting bounds.

        Args:
            entry_ids: Entry IDs to include

        Returns:
            ImplementationContext with entries
        """
        # Limit to max entries
        max_entries = self.cwa._max_impl_entries
        limited_ids = entry_ids[:max_entries]

        return self.cwa.build_impl_context(limited_ids)

    def _close_beads_issue(
        self,
        issue_id: str,
        reason: str = "Phase completed",
    ) -> None:
        """Close a beads issue.

        Args:
            issue_id: Issue ID to close
            reason: Close reason
        """
        if self._beads_controller is not None:
            self._beads_controller.close_issue(issue_id, reason)

    def _commit_phase(
        self,
        phase_name: str,
        message: str,
    ) -> dict[str, Any]:
        """Create git commit for phase.

        Args:
            phase_name: Name of the phase
            message: Commit message

        Returns:
            Dict with success status
        """
        try:
            # Add all changes
            add_result = subprocess.run(
                ["git", "add", "."],
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
            )
            if add_result.returncode != 0:
                return {"success": False, "error": add_result.stderr}

            # Create commit
            commit_result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
            )
            if commit_result.returncode != 0:
                return {"success": False, "error": commit_result.stderr}

            return {"success": True, "output": commit_result.stdout}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute(
        self,
        phase_paths: list[str],
        mode: AutonomyMode,
        beads_issue_ids: Optional[list[str]] = None,
        checkpoint: Optional[dict[str, Any]] = None,
    ) -> PhaseResult:
        """Execute implementation phase.

        Args:
            phase_paths: Paths to phase documents
            mode: Execution mode
            beads_issue_ids: Optional beads issue IDs to close
            checkpoint: Optional checkpoint to resume from

        Returns:
            PhaseResult with implementation status
        """
        started_at = datetime.now()
        errors: list[str] = []
        artifacts: list[str] = []
        metadata: dict[str, Any] = {}

        try:
            # Filter to remaining phases if resuming
            if checkpoint:
                completed = checkpoint.get("completed_phases", [])
                phase_paths = [p for p in phase_paths if p not in completed]
                metadata["resumed_from"] = len(completed)

            if not phase_paths:
                completed_at = datetime.now()
                duration = (completed_at - started_at).total_seconds()
                return PhaseResult(
                    phase_type=PhaseType.IMPLEMENTATION,
                    status=PhaseStatus.COMPLETE,
                    artifacts=[],
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_seconds=duration,
                    metadata={"message": "All phases already completed"},
                )

            # Execute according to mode
            results = self._execute_with_mode(phase_paths, mode)

            # Check overall success
            all_passed = all(r.get("success") for r in results)

            # Close beads issues for successful phases
            if beads_issue_ids:
                for i, result in enumerate(results):
                    if result.get("success") and i < len(beads_issue_ids):
                        self._close_beads_issue(beads_issue_ids[i])

            # Record artifacts for successful phases
            for i, result in enumerate(results):
                if result.get("success") and i < len(phase_paths):
                    artifacts.append(phase_paths[i])

            # Add errors from failed phases
            for i, result in enumerate(results):
                if not result.get("success"):
                    error = result.get("error", "Unknown error")
                    if i < len(phase_paths):
                        errors.append(f"Phase {Path(phase_paths[i]).stem}: {error}")
                    else:
                        errors.append(error)

            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            metadata.update({
                "phases_completed": sum(1 for r in results if r.get("success")),
                "phases_total": len(results),
                "mode": mode.value,
            })

            return PhaseResult(
                phase_type=PhaseType.IMPLEMENTATION,
                status=PhaseStatus.COMPLETE if all_passed else PhaseStatus.FAILED,
                artifacts=artifacts,
                errors=errors,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                metadata=metadata,
            )

        except Exception as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            return PhaseResult(
                phase_type=PhaseType.IMPLEMENTATION,
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
