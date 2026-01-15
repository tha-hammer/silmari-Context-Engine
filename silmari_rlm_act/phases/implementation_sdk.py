"""SDK-based Implementation Phase.

This module implements the implementation phase using claude_agent_sdk instead of
subprocess-based Claude invocation. This provides:
- Direct SDK integration with proper async support
- Single-turn execution (no loop)
- Streaming message processing
- Session management

Following plan: 2026-01-14-tdd-sdk-replacement-silmari-rlm-act
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    TextBlock,
    ToolUseBlock,
)

from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import AutonomyMode, PhaseResult, PhaseStatus, PhaseType


class ImplementationPhaseSDK:
    """Execute TDD implementation using Claude SDK.

    This phase:
    1. Creates SDK client with bypassPermissions mode
    2. Builds prompt with plan path and beads info
    3. Sends implementation request to Claude
    4. Processes streaming response
    5. Returns PhaseResult with status and artifacts

    Attributes:
        project_path: Root directory of the project
        cwa: Context Window Array integration
        CLAUDE_TIMEOUT: Max seconds per invocation
    """

    CLAUDE_TIMEOUT = 3600  # 1 hour per iteration

    # All tools needed for implementation
    ALLOWED_TOOLS = [
        "Read",
        "Write",
        "Edit",
        "Bash",
        "Glob",
        "Grep",
        "LS",
        "Task",
        "TodoWrite",
    ]

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
        self._output_buffer: list[str] = []

    # =========================================================================
    # Phase 01: SDK Client Initialization
    # =========================================================================

    def _create_agent_options(self) -> ClaudeAgentOptions:
        """Create ClaudeAgentOptions for implementation.

        Returns:
            ClaudeAgentOptions configured for autonomous implementation
        """
        return ClaudeAgentOptions(
            permission_mode="bypassPermissions",  # type: ignore[arg-type]
            allowed_tools=self.ALLOWED_TOOLS,
            cwd=self.project_path,
            stderr=self._handle_stderr,
        )

    def _create_client(self) -> ClaudeSDKClient:
        """Create ClaudeSDKClient with options.

        Returns:
            Configured ClaudeSDKClient instance
        """
        options = self._create_agent_options()
        return ClaudeSDKClient(options)

    def _handle_stderr(self, message: str) -> None:
        """Handle stderr output from CLI.

        Args:
            message: Stderr message from Claude CLI
        """
        # Could log or display progress here
        pass

    # =========================================================================
    # Phase 02: Prompt Building
    # =========================================================================

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

    # =========================================================================
    # Phase 03 & 04: Session Management and Streaming
    # =========================================================================

    async def execute_async(
        self,
        phase_paths: list[str],
        mode: AutonomyMode,  # noqa: ARG002 - kept for API compatibility
        beads_issue_ids: Optional[list[str]] = None,
        beads_epic_id: Optional[str] = None,
        max_iterations: int = 1,  # noqa: ARG002 - kept for API compatibility
        checkpoint: Optional[dict[str, Any]] = None,  # noqa: ARG002 - kept for API compatibility
    ) -> PhaseResult:
        """Execute implementation via SDK.

        Args:
            phase_paths: Paths to TDD plan documents
            mode: Execution mode (ignored - always autonomous)
            beads_issue_ids: Beads issue IDs for tracking
            beads_epic_id: Optional beads epic ID
            max_iterations: Safety limit on iterations (ignored)
            checkpoint: Optional checkpoint (ignored)

        Returns:
            PhaseResult with implementation status
        """
        # Suppress unused parameter warnings - kept for API compatibility
        _ = mode, max_iterations, checkpoint

        started_at = datetime.now()
        self._output_buffer = []
        tool_uses: list[dict[str, Any]] = []
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

        client = self._create_client()

        try:
            # Connect to SDK session
            await client.connect()

            # Build and send prompt
            prompt = self._build_implementation_prompt(plan_path, beads_epic_id, issue_ids)
            await client.query(prompt)

            # Process streaming response
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            self._output_buffer.append(block.text)
                        elif isinstance(block, ToolUseBlock):
                            tool_uses.append({
                                "id": block.id,
                                "name": block.name,
                                "input": block.input,
                            })

        except Exception as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            return PhaseResult(
                phase_type=PhaseType.IMPLEMENTATION,
                status=PhaseStatus.FAILED,
                errors=[str(e)],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
            )
        finally:
            # Always disconnect
            try:
                await client.disconnect()
            except Exception:
                pass

        completed_at = datetime.now()
        duration = (completed_at - started_at).total_seconds()
        output = "".join(self._output_buffer)

        return PhaseResult(
            phase_type=PhaseType.IMPLEMENTATION,
            status=PhaseStatus.COMPLETE,
            artifacts=phase_paths,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            metadata={
                "output": output,
                "tool_uses": tool_uses,
                "mode": "sdk",
                "beads_issues": issue_ids,
            },
        )

    def execute(
        self,
        phase_paths: list[str],
        mode: AutonomyMode,
        beads_issue_ids: Optional[list[str]] = None,
        beads_epic_id: Optional[str] = None,
        max_iterations: int = 1,
        checkpoint: Optional[dict[str, Any]] = None,
    ) -> PhaseResult:
        """Execute implementation synchronously.

        This is a wrapper around execute_async for sync contexts.

        Args:
            phase_paths: Paths to TDD plan documents
            mode: Execution mode
            beads_issue_ids: Beads issue IDs for tracking
            beads_epic_id: Optional beads epic ID
            max_iterations: Safety limit on iterations
            checkpoint: Optional checkpoint

        Returns:
            PhaseResult with implementation status
        """
        return asyncio.run(
            self.execute_async(
                phase_paths,
                mode,
                beads_issue_ids,
                beads_epic_id,
                max_iterations,
                checkpoint,
            )
        )
