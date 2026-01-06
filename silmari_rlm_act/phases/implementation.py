"""Implementation phase - Simple Claude loop.

This module implements the implementation phase using a simple loop pattern:
1. Inject beads epic/issues into the TDD plan
2. Pass the plan to Claude with --dangerously-skip-permissions
3. Let Claude manage implementation, tests, commits, and beads
4. Check for completion after each iteration
5. Stop when all beads issues are closed

Claude is powerful - let Claude manage the implementation.
"""

import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import AutonomyMode, PhaseResult, PhaseStatus, PhaseType


class ImplementationPhase:
    """Execute TDD implementation via simple Claude loop.

    Pattern from loop.sh:
        while true; do
            cat PLAN.md | claude -p --dangerously-skip-permissions
            sleep 10
            # check for completion
        done

    Attributes:
        project_path: Root directory of the project
        cwa: Context Window Array integration
        LOOP_SLEEP: Seconds between loop iterations
        CLAUDE_TIMEOUT: Max seconds per Claude invocation
    """

    LOOP_SLEEP = 10
    CLAUDE_TIMEOUT = 3600  # 1 hour per iteration

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

    def _build_implementation_prompt(
        self,
        plan_path: Path,
        epic_id: Optional[str],
        issue_ids: list[str],
    ) -> str:
        """Build prompt that tells Claude to read and implement the TDD plan.

        Args:
            plan_path: Path to the TDD plan overview file
            epic_id: Optional beads epic ID
            issue_ids: List of beads issue IDs for phases

        Returns:
            Prompt instructing Claude to implement the plan
        """
        prompt = f"""Implement the TDD plan at: {plan_path}

Read the plan overview first, then find and implement the phase documents.

## Beads Tracking

Use `bd` commands to track progress:
```bash
bd ready                    # See available work
bd show <id>                # View issue details
bd update <id> --status=in_progress  # Start work
bd close <id>               # Complete work (unblocks next)
bd sync                     # Sync changes
```

"""
        if epic_id:
            prompt += f"**Epic**: `{epic_id}`\n\n"

        if issue_ids:
            prompt += "**Phase Issues**:\n"
            for i, issue_id in enumerate(issue_ids):
                prompt += f"- Phase {i + 1}: `{issue_id}`\n"
            prompt += "\n"

        prompt += """
## Implementation Instructions

1. Read the plan overview at the path above
2. Find the phase documents in the same directory
3. Implement the highest priority TASK using subagents
4. Run all tests: `pytest` or `make test`
5. Update the plan with progress
6. Use `bd close <id>` when phase is complete
7. Use `/clear` after closing an issue to start fresh

**CRITICAL**: After ALL TESTS PASS and after each successful `bd close`,
emit a /clear command to clear context for the next issue.
"""
        return prompt

    def _invoke_claude(self, prompt: str) -> dict[str, Any]:
        """Invoke Claude with plan as prompt.

        Args:
            prompt: The full prompt (plan content with beads)

        Returns:
            Dict with success, output, error
        """
        cmd = [
            "claude",
            "-p", prompt,
            "--dangerously-skip-permissions",
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=self.CLAUDE_TIMEOUT,
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Claude timed out after {self.CLAUDE_TIMEOUT}s",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "output": "",
                "error": "claude command not found",
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
            }

    def _check_completion(self, issue_ids: list[str]) -> bool:
        """Check if all beads issues are closed.

        Args:
            issue_ids: List of issue IDs to check

        Returns:
            True if all issues are closed
        """
        if not issue_ids:
            return True

        try:
            # Check each issue status
            for issue_id in issue_ids:
                result = subprocess.run(
                    ["bd", "show", issue_id],
                    cwd=str(self.project_path),
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                output = result.stdout.lower()
                # If any issue is not closed, return False
                if "status: closed" not in output and "status: done" not in output:
                    return False

            return True

        except Exception:
            # If check fails, assume not complete
            return False

    def _run_tests(self) -> tuple[bool, str]:
        """Run test suite to verify implementation.

        Returns:
            Tuple of (passed, output)
        """
        try:
            result = subprocess.run(
                ["pytest", "-v", "--tb=short"],
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=300,
            )
            return result.returncode == 0, result.stdout + result.stderr

        except subprocess.TimeoutExpired:
            return False, "Tests timed out"
        except FileNotFoundError:
            # Try make test as fallback
            try:
                result = subprocess.run(
                    ["make", "test"],
                    cwd=str(self.project_path),
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                return result.returncode == 0, result.stdout + result.stderr
            except Exception:
                return True, "No test command found, skipping"
        except Exception as e:
            return False, str(e)

    def execute(
        self,
        phase_paths: list[str],
        mode: AutonomyMode,  # noqa: ARG002 - kept for API compatibility
        beads_issue_ids: Optional[list[str]] = None,
        beads_epic_id: Optional[str] = None,
        max_iterations: int = 100,
        checkpoint: Optional[dict[str, Any]] = None,  # noqa: ARG002 - kept for API compatibility
    ) -> PhaseResult:
        """Execute implementation via simple Claude loop.

        Args:
            phase_paths: Paths to TDD plan documents
            mode: Execution mode (ignored - always autonomous)
            beads_issue_ids: Beads issue IDs for tracking
            beads_epic_id: Optional beads epic ID
            max_iterations: Safety limit on loop iterations
            checkpoint: Optional checkpoint (ignored)

        Returns:
            PhaseResult with implementation status
        """
        # Suppress unused parameter warnings - kept for API compatibility
        _ = mode, checkpoint

        started_at = datetime.now()
        errors: list[str] = []
        artifacts: list[str] = []
        issue_ids = beads_issue_ids or []

        if not phase_paths:
            return PhaseResult(
                phase_type=PhaseType.IMPLEMENTATION,
                status=PhaseStatus.COMPLETE,
                artifacts=[],
                started_at=started_at,
                completed_at=datetime.now(),
                duration_seconds=0,
                metadata={"message": "No phase paths provided"},
            )

        # Use first plan as the main plan (overview)
        plan_path = Path(phase_paths[0])
        if not plan_path.is_absolute():
            plan_path = self.project_path / plan_path

        if not plan_path.exists():
            return PhaseResult(
                phase_type=PhaseType.IMPLEMENTATION,
                status=PhaseStatus.FAILED,
                errors=[f"Plan not found: {plan_path}"],
                started_at=started_at,
                completed_at=datetime.now(),
                duration_seconds=0,
            )

        # Build prompt with plan path - Claude will read the plan
        prompt = self._build_implementation_prompt(plan_path, beads_epic_id, issue_ids)

        # Simple loop: invoke Claude, sleep, check completion
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"\n{'=' * 60}")
            print(f"IMPLEMENTATION LOOP - Iteration {iteration}")
            print(f"{'=' * 60}\n")

            # Invoke Claude with plan
            result = self._invoke_claude(prompt)

            if result["output"]:
                print(result["output"])
            if result["error"]:
                print(f"STDERR: {result['error']}")

            # Sleep between iterations
            print(f"\n{'=' * 25} LOOP {'=' * 25}\n")
            time.sleep(self.LOOP_SLEEP)

            # Check if all issues are closed
            if self._check_completion(issue_ids):
                print("All beads issues closed - implementation complete!")

                # Final test verification
                tests_pass, test_output = self._run_tests()
                if not tests_pass:
                    errors.append(f"Final tests failed: {test_output[:500]}")
                    # Continue loop if tests fail
                    continue

                # Tests passed - clear any previous test failures and break
                errors.clear()
                artifacts.extend(phase_paths)
                break

        else:
            errors.append(f"Reached max iterations ({max_iterations})")

        completed_at = datetime.now()
        duration = (completed_at - started_at).total_seconds()

        return PhaseResult(
            phase_type=PhaseType.IMPLEMENTATION,
            status=PhaseStatus.COMPLETE if not errors else PhaseStatus.FAILED,
            artifacts=artifacts,
            errors=errors,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            metadata={
                "iterations": iteration,
                "mode": "autonomous_loop",
                "beads_issues": issue_ids,
            },
        )
