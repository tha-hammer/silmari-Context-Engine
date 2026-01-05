"""Research phase implementation.

This module implements the research phase of the silmari-rlm-act pipeline,
which gathers context about a task using Claude Code and stores findings
in the Context Window Array.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from silmari_rlm_act.checkpoints.interactive import (
    collect_multiline_input,
    prompt_research_action,
)
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseResult, PhaseStatus, PhaseType

# Import claude runner for execution
from planning_pipeline.claude_runner import run_claude_sync


class ResearchPhase:
    """Execute research phase using Claude Code.

    This phase:
    1. Loads a research template (custom or default)
    2. Builds a prompt with the research question
    3. Executes Claude Code to gather research
    4. Extracts the research document path from output
    5. Stores the research in CWA for later use
    6. Returns a PhaseResult with artifacts

    Attributes:
        project_path: Root directory of the project
        cwa: Context Window Array integration
        TEMPLATE_PATH: Relative path to custom template
        DEFAULT_TIMEOUT: Default timeout in seconds (20 minutes)
    """

    TEMPLATE_PATH = ".claude/commands/research_codebase.md"
    DEFAULT_TIMEOUT = 1200  # 20 minutes

    # Patterns to match research file paths
    RESEARCH_PATH_PATTERNS = [
        r"thoughts/searchable/shared/research/[\w\-\.]+\.md",
        r"thoughts/shared/research/[\w\-\.]+\.md",
        r"/[\w/\-\.]+/thoughts/[\w/\-\.]+research[\w/\-\.]+\.md",
    ]

    # Patterns to detect open questions sections
    QUESTION_SECTION_PATTERNS = [
        r"(?:Open|Remaining|Unanswered)\s+Questions?:?\s*\n((?:[\-\*\d\.]\s*.+\n?)+)",
        r"Questions?(?:\s+to\s+answer)?:?\s*\n((?:[\-\*\d\.]\s*.+\n?)+)",
    ]

    def __init__(
        self,
        project_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Initialize research phase.

        Args:
            project_path: Root directory of the project
            cwa: Context Window Array integration instance
        """
        self.project_path = Path(project_path)
        self.cwa = cwa

    def _run_claude(self, prompt: str, timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
        """Run Claude Code with the given prompt.

        Args:
            prompt: The prompt to send to Claude
            timeout: Timeout in seconds

        Returns:
            Dictionary with success, output, error, and elapsed keys
        """
        return run_claude_sync(prompt=prompt, timeout=timeout, stream=True)

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

Research the following question thoroughly:

{research_question}

Save your findings to a markdown file in thoughts/searchable/shared/research/.
Use the format: YYYY-MM-DD-topic-name.md

Include:
- Overview of findings
- Key details and patterns discovered
- Code examples if relevant
- Open questions that remain
"""

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
        if additional_context:
            prompt += f"\n\nAdditional Context:\n{additional_context}"
        return prompt

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

    def _extract_open_questions(self, output: str) -> list[str]:
        """Extract open questions from output.

        Args:
            output: Claude output text

        Returns:
            List of question strings
        """
        questions = []

        for pattern in self.QUESTION_SECTION_PATTERNS:
            match = re.search(pattern, output, re.IGNORECASE | re.MULTILINE)
            if match:
                section = match.group(1)
                # Extract individual questions
                for line in section.split("\n"):
                    line = line.strip()
                    if line:
                        # Remove list markers
                        cleaned = re.sub(r"^[\-\*\d\.]+\s*", "", line).strip()
                        if cleaned:
                            questions.append(cleaned)
                break

        return questions

    def execute(
        self,
        research_question: str,
        additional_context: str = "",
        timeout: Optional[int] = None,
    ) -> PhaseResult:
        """Execute research phase.

        Args:
            research_question: The question to research
            additional_context: Optional additional context
            timeout: Optional timeout in seconds

        Returns:
            PhaseResult with research artifacts or errors
        """
        started_at = datetime.now()

        prompt = self._build_prompt(research_question, additional_context)

        try:
            result = self._run_claude(prompt, timeout=timeout or self.DEFAULT_TIMEOUT)

            elapsed = result.get("elapsed", 0)
            completed_at = datetime.now()

            if not result.get("success"):
                return PhaseResult(
                    phase_type=PhaseType.RESEARCH,
                    status=PhaseStatus.FAILED,
                    errors=[result.get("error", "Research execution failed")],
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_seconds=elapsed,
                )

            # Extract research path from output
            output = result.get("output", "")
            research_path = self._extract_research_path(output)

            if not research_path:
                return PhaseResult(
                    phase_type=PhaseType.RESEARCH,
                    status=PhaseStatus.FAILED,
                    errors=["No research document path found in output"],
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_seconds=elapsed,
                    metadata={"output": output},
                )

            if not research_path.exists():
                return PhaseResult(
                    phase_type=PhaseType.RESEARCH,
                    status=PhaseStatus.FAILED,
                    errors=[f"Research document not found: {research_path}"],
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_seconds=elapsed,
                )

            # Store in CWA
            entry_id = self._store_research_in_cwa(research_path)

            # Extract open questions
            open_questions = self._extract_open_questions(output)

            return PhaseResult(
                phase_type=PhaseType.RESEARCH,
                status=PhaseStatus.COMPLETE,
                artifacts=[str(research_path)],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=elapsed,
                metadata={
                    "cwa_entry_id": entry_id,
                    "open_questions": open_questions,
                    "output": output,
                },
            )

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

    def execute_with_checkpoint(
        self,
        research_question: str,
        auto_approve: bool = False,
        additional_context: str = "",
        timeout: Optional[int] = None,
    ) -> PhaseResult:
        """Execute research phase with interactive checkpoint.

        After research completes, prompts user for action unless auto_approve is True.

        Args:
            research_question: The question to research
            auto_approve: If True, skip user prompts
            additional_context: Optional additional context
            timeout: Optional timeout in seconds

        Returns:
            PhaseResult with research artifacts and user action
        """
        current_context = additional_context

        while True:
            result = self.execute(
                research_question,
                additional_context=current_context,
                timeout=timeout,
            )

            # If failed or auto-approve, return immediately
            if result.status == PhaseStatus.FAILED or auto_approve:
                if auto_approve and result.status == PhaseStatus.COMPLETE:
                    result.metadata["user_action"] = "continue"
                return result

            # Prompt user for action
            action = prompt_research_action()
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
                # Clear context and indicate restart needed
                result.metadata["needs_restart"] = True
                return result
            elif action == "exit":
                result.metadata["user_exit"] = True
                return result
            else:
                # Unknown action, treat as continue
                return result
