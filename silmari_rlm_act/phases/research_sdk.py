"""SDK-based Research Phase implementation.

This module implements the research phase using claude_agent_sdk instead of
subprocess-based Claude invocation. This provides:
- Direct SDK integration with proper async support
- Permission callback handling
- Streaming message processing
- Session management

Following plan: 2026-01-14-tdd-sdk-replacement-silmari-rlm-act
"""

import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    PermissionResult,
    PermissionResultAllow,
    PermissionResultDeny,
    TextBlock,
    ToolPermissionContext,
    ToolUseBlock,
)

from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseResult, PhaseStatus, PhaseType


class ResearchPhaseSDK:
    """Execute research phase using Claude SDK.

    This phase:
    1. Creates SDK client with appropriate options
    2. Sends research query to Claude
    3. Processes streaming response
    4. Extracts research document path from output
    5. Stores the research in CWA for later use
    6. Returns a PhaseResult with artifacts

    Attributes:
        project_path: Root directory of the project
        cwa: Context Window Array integration
        permission_mode: SDK permission mode
        TEMPLATE_PATH: Relative path to custom template
        DEFAULT_TIMEOUT: Default timeout in seconds
    """

    TEMPLATE_PATH = "silmari_rlm_act/commands/research_codebase.md"
    DEFAULT_TIMEOUT = 1200  # 20 minutes

    # Research tools needed for file operations
    ALLOWED_TOOLS = [
        "Read",
        "Write",
        "Glob",
        "Grep",
        "Bash",
        "LS",
        "Edit",
    ]

    # Dangerous bash patterns to deny
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/",
        r"rm\s+-rf\s+~",
        r"mkfs\.",
        r"dd\s+if=.*of=/dev",
        r">\s*/dev/sd",
        r"chmod\s+-R\s+777\s+/",
        r":\(\)\{\s*:\|:\s*&\s*\}",  # Fork bomb
    ]

    # Patterns to match research file paths
    RESEARCH_PATH_PATTERNS = [
        r"thoughts/searchable/shared/research/[\w\-\.]+\.md",
        r"/[\w/\-\.]+/thoughts/[\w/\-\.]+research[\w/\-\.]+\.md",
    ]

    def __init__(
        self,
        project_path: Path,
        cwa: CWAIntegration,
        permission_mode: str = "acceptEdits",
    ) -> None:
        """Initialize research phase.

        Args:
            project_path: Root directory of the project
            cwa: Context Window Array integration instance
            permission_mode: SDK permission mode (default: acceptEdits)
        """
        self.project_path = Path(project_path)
        self.cwa = cwa
        self.permission_mode = permission_mode
        self._output_buffer: list[str] = []

    # =========================================================================
    # Phase 01: SDK Client Initialization
    # =========================================================================

    def _create_agent_options(self) -> ClaudeAgentOptions:
        """Create ClaudeAgentOptions with appropriate settings.

        Returns:
            ClaudeAgentOptions configured for research phase
        """
        return ClaudeAgentOptions(
            permission_mode=self.permission_mode,  # type: ignore[arg-type]
            allowed_tools=self.ALLOWED_TOOLS,
            cwd=self.project_path,
            stderr=self._handle_stderr,
            can_use_tool=self._can_use_tool,
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
    # Phase 02: Permission Callbacks
    # =========================================================================

    async def _can_use_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        context: ToolPermissionContext,
    ) -> PermissionResult:
        """Handle tool permission requests.

        Args:
            tool_name: Name of the tool being requested
            tool_input: Tool input parameters
            context: Permission context

        Returns:
            PermissionResult allowing or denying the tool use
        """
        # Auto-approve safe tools
        safe_tools = {"Read", "Glob", "Grep", "LS", "Write", "Edit"}
        if tool_name in safe_tools:
            return PermissionResultAllow()

        # Check Bash commands for dangerous patterns
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            for pattern in self.DANGEROUS_PATTERNS:
                if re.search(pattern, command):
                    return PermissionResultDeny(
                        message=f"Dangerous command pattern detected: {pattern}"
                    )
            # Allow safe bash commands
            return PermissionResultAllow()

        # Default: allow
        return PermissionResultAllow()

    # =========================================================================
    # Phase 03 & 04: Session Management and Streaming
    # =========================================================================

    async def execute_async(
        self,
        research_question: str,
        additional_context: str = "",
        timeout: Optional[int] = None,
    ) -> PhaseResult:
        """Execute research phase asynchronously.

        Args:
            research_question: The question to research
            additional_context: Optional additional context
            timeout: Optional timeout in seconds

        Returns:
            PhaseResult with research artifacts or errors
        """
        started_at = datetime.now()
        self._output_buffer = []
        tool_uses: list[dict[str, Any]] = []

        client = self._create_client()

        try:
            # Connect to SDK session
            await client.connect()

            # Build and send prompt
            prompt = self._build_prompt(research_question, additional_context)
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
                phase_type=PhaseType.RESEARCH,
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

        # Process output
        completed_at = datetime.now()
        duration = (completed_at - started_at).total_seconds()
        output = "".join(self._output_buffer)

        # Extract research path
        research_path = self._extract_research_path(output)

        # Fallback: search for recently created files
        if not research_path:
            research_path = self._find_recent_research_file(started_at)

        if not research_path:
            return PhaseResult(
                phase_type=PhaseType.RESEARCH,
                status=PhaseStatus.FAILED,
                errors=["No research document path found in output or research directories"],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                metadata={"output": output, "tool_uses": tool_uses},
            )

        if not research_path.exists():
            return PhaseResult(
                phase_type=PhaseType.RESEARCH,
                status=PhaseStatus.FAILED,
                errors=[f"Research document not found: {research_path}"],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
            )

        # Store in CWA
        entry_id = self._store_research_in_cwa(research_path)

        return PhaseResult(
            phase_type=PhaseType.RESEARCH,
            status=PhaseStatus.COMPLETE,
            artifacts=[str(research_path)],
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            metadata={
                "cwa_entry_id": entry_id,
                "output": output,
                "tool_uses": tool_uses,
            },
        )

    def execute(
        self,
        research_question: str,
        additional_context: str = "",
        timeout: Optional[int] = None,
    ) -> PhaseResult:
        """Execute research phase synchronously.

        This is a wrapper around execute_async for sync contexts.

        Args:
            research_question: The question to research
            additional_context: Optional additional context
            timeout: Optional timeout in seconds

        Returns:
            PhaseResult with research artifacts or errors
        """
        return asyncio.run(
            self.execute_async(research_question, additional_context, timeout)
        )

    # =========================================================================
    # Helper Methods (reused from original ResearchPhase)
    # =========================================================================

    def _build_prompt(self, research_question: str, additional_context: str = "") -> str:
        """Build research prompt from template.

        Args:
            research_question: The question to research
            additional_context: Optional additional context to include

        Returns:
            Complete prompt string
        """
        template = self._load_template()
        prompt = template.replace("{research_question}", research_question)
        prompt = prompt.replace("{project_path}", str(self.project_path))
        if additional_context:
            prompt += f"\n\nAdditional Context:\n{additional_context}"
        return prompt

    def _load_template(self) -> str:
        """Load research command template.

        Returns:
            Template string with {research_question} placeholder
        """
        template_path = self.project_path / self.TEMPLATE_PATH
        if template_path.exists():
            return template_path.read_text()
        return self._default_template()

    def _default_template(self) -> str:
        """Return default research template.

        Returns:
            Default template string
        """
        return """# Research Task

**Project path**: {project_path}

Research the following question thoroughly:

{research_question}

Save your findings to a markdown file in {project_path}/thoughts/searchable/shared/research/.
Use the format: YYYY-MM-DD-topic-name.md

Include:
- Overview of findings
- Key details and patterns discovered
- Code examples if relevant
- Open questions that remain
"""

    def _extract_research_path(self, output: str) -> Optional[Path]:
        """Extract research document path from output.

        Args:
            output: Claude output text

        Returns:
            Path to research document or None if not found
        """
        for pattern in self.RESEARCH_PATH_PATTERNS:
            match = re.search(pattern, output)
            if match:
                path_str = match.group(0)
                path = Path(path_str)

                # If relative, resolve against project path
                if not path.is_absolute():
                    path = self.project_path / path

                return path.resolve()

        return None

    def _find_recent_research_file(self, started_at: datetime) -> Optional[Path]:
        """Find recently created research file as fallback.

        Searches thoughts/searchable/shared/research/ for files created after started_at.

        Args:
            started_at: Time when research started

        Returns:
            Path to most recent research file, or None if not found
        """
        research_dirs = [
            self.project_path / "thoughts" / "searchable" / "shared" / "research",
        ]

        recent_files: list[tuple[Path, float]] = []

        for research_dir in research_dirs:
            if not research_dir.exists():
                continue

            for file_path in research_dir.glob("*.md"):
                try:
                    mtime = file_path.stat().st_mtime
                    # Check if file was modified after research started
                    if mtime >= started_at.timestamp():
                        recent_files.append((file_path, mtime))
                except OSError:
                    continue

        if not recent_files:
            return None

        # Return most recently modified file
        recent_files.sort(key=lambda x: x[1], reverse=True)
        return recent_files[0][0]

    def _store_research_in_cwa(self, path: Path) -> str:
        """Store research document in CWA.

        Args:
            path: Path to research document

        Returns:
            Entry ID of the stored research
        """
        content = path.read_text()
        summary = self._generate_summary(content)

        return self.cwa.store_research(
            path=str(path),
            content=content,
            summary=summary,
        )

    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """Generate summary from research content.

        Extracts title and overview section to create a brief summary.

        Args:
            content: Full document content
            max_length: Maximum summary length

        Returns:
            Brief summary string
        """
        lines = content.split("\n")
        title = ""
        overview = ""

        for i, line in enumerate(lines):
            if line.startswith("# "):
                title = line[2:].strip()
            elif line.startswith("## Overview") or line.startswith("## Summary"):
                # Get next non-empty line
                idx = i + 1
                while idx < len(lines) and not lines[idx].strip():
                    idx += 1
                if idx < len(lines):
                    overview = lines[idx].strip()
                break

        if title and overview:
            summary = f"{title}: {overview}"
        elif title:
            summary = title
        else:
            # Take first non-empty, non-header line
            for line in lines:
                if line.strip() and not line.startswith("#"):
                    summary = line.strip()
                    break
            else:
                summary = "Research document"

        return summary[:max_length]
