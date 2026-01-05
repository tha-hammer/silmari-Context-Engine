# Phase 05: Research Phase TDD Plan

## Overview

Implement the research phase of the silmari-rlm-act pipeline. This phase gathers context about the task through Claude Code execution and stores findings in the Context Window Array.

## Testable Behaviors

### Behavior 1: Execute Research with Claude
**Given**: Research prompt
**When**: Running research phase
**Then**: Claude Code invoked with research instructions

### Behavior 2: Extract Research Path from Output
**Given**: Claude output with file path
**When**: Parsing output
**Then**: Research document path extracted

### Behavior 3: Store Research in CWA
**Given**: Research document created
**When**: Phase completes
**Then**: FILE entry added to store

### Behavior 4: Return PhaseResult
**Given**: Successful research
**When**: Phase completes
**Then**: PhaseResult with artifacts returned

### Behavior 5: Handle Research Failure
**Given**: Claude execution fails
**When**: Error occurs
**Then**: PhaseResult with error returned

### Behavior 6: Extract Open Questions
**Given**: Research with open questions
**When**: Parsing output
**Then**: Questions extracted for user

### Behavior 7: Interactive Checkpoint
**Given**: Research complete
**When**: Not in auto mode
**Then**: User prompted for action

### Behavior 8: Revise with Additional Context
**Given**: User provides revision context
**When**: Action is "revise"
**Then**: Research re-run with context

---

## TDD Cycle: Behavior 1 - Execute Research with Claude

### Test Specification
**Given**: Research prompt "How does auth work?"
**When**: Calling execute(prompt)
**Then**: Claude Code invoked with research instructions

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_research_phase.py`
```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from silmari_rlm_act.phases.research import ResearchPhase
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PipelineState


class TestExecuteResearch:
    """Behavior 1: Execute Research with Claude."""

    def test_invokes_claude_with_prompt(self, tmp_path):
        """Given prompt, invokes Claude Code."""
        cwa = CWAIntegration()
        phase = ResearchPhase(
            project_path=tmp_path,
            cwa=cwa,
        )

        mock_runner = Mock()
        mock_runner.run_sync.return_value = {
            "success": True,
            "output": "Research saved to thoughts/research/doc.md"
        }

        with patch.object(phase, '_runner', mock_runner):
            result = phase.execute("How does auth work?")

        mock_runner.run_sync.assert_called_once()
        call_args = mock_runner.run_sync.call_args
        assert "How does auth work?" in call_args[0][0]  # Prompt contains query

    def test_loads_research_template(self, tmp_path):
        """Given execution, loads research command template."""
        # Create template
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        template = commands_dir / "research_codebase.md"
        template.write_text("# Research\n\n{research_question}")

        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        mock_runner = Mock()
        mock_runner.run_sync.return_value = {"success": True, "output": "Done"}

        with patch.object(phase, '_runner', mock_runner):
            phase.execute("Test query")

        # Verify template was used
        call_args = mock_runner.run_sync.call_args
        assert "Research" in call_args[0][0]
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/phases/research.py`
```python
"""Research phase implementation."""

from pathlib import Path
from typing import Optional
from silmari_rlm_act.models import PhaseResult
from silmari_rlm_act.context.cwa_integration import CWAIntegration


class ResearchPhase:
    """Execute research phase using Claude Code."""

    TEMPLATE_PATH = ".claude/commands/research_codebase.md"
    DEFAULT_TIMEOUT = 1200  # 20 minutes

    def __init__(
        self,
        project_path: Path,
        cwa: CWAIntegration,
    ):
        self.project_path = Path(project_path)
        self.cwa = cwa
        self._runner = None  # Claude runner, injected or created

    def _load_template(self) -> str:
        """Load research command template."""
        template_path = self.project_path / self.TEMPLATE_PATH
        if template_path.exists():
            return template_path.read_text()
        return self._default_template()

    def _default_template(self) -> str:
        """Return default research template."""
        return """# Research Task

Research the following question thoroughly:

{research_question}

Save your findings to a markdown file in thoughts/searchable/shared/research/.
"""

    def _build_prompt(self, research_question: str, additional_context: str = "") -> str:
        """Build research prompt from template."""
        template = self._load_template()
        prompt = template.replace("{research_question}", research_question)
        if additional_context:
            prompt += f"\n\nAdditional Context:\n{additional_context}"
        return prompt

    def execute(
        self,
        research_question: str,
        additional_context: str = "",
        timeout: Optional[int] = None
    ) -> PhaseResult:
        """Execute research phase.

        Args:
            research_question: The question to research
            additional_context: Optional additional context
            timeout: Optional timeout in seconds

        Returns:
            PhaseResult with research artifacts
        """
        prompt = self._build_prompt(research_question, additional_context)

        try:
            result = self._runner.run_sync(
                prompt,
                timeout=timeout or self.DEFAULT_TIMEOUT
            )

            if not result.get("success"):
                return PhaseResult(
                    phase="research",
                    success=False,
                    error=result.get("error", "Research execution failed")
                )

            # Extract research path from output
            output = result.get("output", "")
            research_path = self._extract_research_path(output)

            artifacts = []
            if research_path:
                artifacts.append(str(research_path))
                # Store in CWA
                self._store_research_in_cwa(research_path)

            return PhaseResult(
                phase="research",
                success=True,
                output=output,
                artifacts=artifacts
            )

        except Exception as e:
            return PhaseResult(
                phase="research",
                success=False,
                error=str(e)
            )

    def _extract_research_path(self, output: str) -> Optional[Path]:
        """Extract research document path from output."""
        # Implementation in next behavior
        pass

    def _store_research_in_cwa(self, path: Path) -> str:
        """Store research document in CWA."""
        # Implementation in behavior 3
        pass
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_research_phase.py::TestExecuteResearch -v`

---

## TDD Cycle: Behavior 2 - Extract Research Path

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_research_phase.py`
```python
class TestExtractResearchPath:
    """Behavior 2: Extract Research Path from Output."""

    def test_extracts_path_from_output(self, tmp_path):
        """Given output with path, extracts it."""
        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        output = """
Research complete!
Saved findings to: thoughts/searchable/shared/research/2026-01-05-auth.md
"""

        path = phase._extract_research_path(output)

        assert path is not None
        assert "2026-01-05-auth.md" in str(path)

    def test_handles_absolute_path(self, tmp_path):
        """Given absolute path, returns it."""
        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        abs_path = str(tmp_path / "thoughts" / "research" / "doc.md")
        output = f"Saved to: {abs_path}"

        path = phase._extract_research_path(output)

        assert path is not None
        assert path.is_absolute()

    def test_returns_none_for_no_path(self, tmp_path):
        """Given no path in output, returns None."""
        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        output = "Some output without a file path"

        path = phase._extract_research_path(output)

        assert path is None

    def test_handles_multiple_paths(self, tmp_path):
        """Given multiple paths, extracts research path."""
        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        output = """
Read file: src/main.py
Saved research to: thoughts/searchable/shared/research/2026-01-05-topic.md
Updated: other/file.txt
"""

        path = phase._extract_research_path(output)

        assert path is not None
        assert "research" in str(path)
        assert "2026-01-05" in str(path)
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/phases/research.py`
```python
import re


class ResearchPhase:
    # ... existing code ...

    # Patterns to match research file paths
    RESEARCH_PATH_PATTERNS = [
        r"thoughts/searchable/shared/research/[\w\-\.]+\.md",
        r"thoughts/shared/research/[\w\-\.]+\.md",
        r"/[\w/\-\.]+/thoughts/[\w/\-\.]+research[\w/\-\.]+\.md",
    ]

    def _extract_research_path(self, output: str) -> Optional[Path]:
        """Extract research document path from output.

        Args:
            output: Claude output text

        Returns:
            Path to research document or None
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
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_research_phase.py::TestExtractResearchPath -v`

---

## TDD Cycle: Behavior 3 - Store Research in CWA

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_research_phase.py`
```python
from context_window_array import EntryType


class TestStoreResearchInCWA:
    """Behavior 3: Store Research in CWA."""

    def test_creates_file_entry(self, tmp_path):
        """Given research path, creates FILE entry in CWA."""
        # Create research file
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nFindings here.")

        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        entry_id = phase._store_research_in_cwa(research_file)

        # Verify entry created
        entry = cwa.store.get(entry_id)
        assert entry is not None
        assert entry.entry_type == EntryType.FILE
        assert "Research" in entry.content

    def test_generates_summary(self, tmp_path):
        """Given research content, generates summary."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("""# Authentication Research

## Overview
This document covers authentication patterns.

## Findings
- Pattern 1
- Pattern 2
""")

        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        entry_id = phase._store_research_in_cwa(research_file)

        entry = cwa.store.get(entry_id)
        assert entry.summary is not None
        assert len(entry.summary) > 0
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/phases/research.py`
```python
class ResearchPhase:
    # ... existing code ...

    def _store_research_in_cwa(self, path: Path) -> str:
        """Store research document in CWA.

        Args:
            path: Path to research document

        Returns:
            Entry ID
        """
        content = path.read_text()
        summary = self._generate_summary(content)

        return self.cwa.store_research(
            path=str(path),
            content=content,
            summary=summary
        )

    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """Generate summary from research content.

        Args:
            content: Full document content
            max_length: Maximum summary length

        Returns:
            Brief summary string
        """
        # Extract title from markdown
        lines = content.split("\n")
        title = ""
        overview = ""

        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
            elif line.startswith("## Overview") or line.startswith("## Summary"):
                # Get next non-empty line
                idx = lines.index(line) + 1
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
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_research_phase.py::TestStoreResearchInCWA -v`

---

## TDD Cycle: Behavior 4-8 - Remaining Behaviors

### Behavior 4: Return PhaseResult
```python
def test_returns_phase_result_on_success(tmp_path):
    """Given successful research, returns PhaseResult."""
    # Setup...
    result = phase.execute("Test query")

    assert isinstance(result, PhaseResult)
    assert result.phase == "research"
    assert result.success is True
    assert len(result.artifacts) > 0
```

### Behavior 5: Handle Failure
```python
def test_returns_error_on_failure(tmp_path):
    """Given Claude failure, returns error PhaseResult."""
    mock_runner = Mock()
    mock_runner.run_sync.side_effect = Exception("Connection error")

    result = phase.execute("Test query")

    assert result.success is False
    assert "Connection error" in result.error
```

### Behavior 6: Extract Open Questions
```python
def test_extracts_open_questions(tmp_path):
    """Given output with questions, extracts them."""
    output = """
Research complete.

Open Questions:
1. What authentication provider is used?
2. How are sessions managed?
"""

    questions = phase._extract_open_questions(output)

    assert len(questions) == 2
    assert "authentication provider" in questions[0]
```

### Behavior 7: Interactive Checkpoint
```python
def test_prompts_user_when_not_auto(tmp_path):
    """Given non-auto mode, prompts user."""
    with patch('silmari_rlm_act.phases.research.prompt_research_action') as mock:
        mock.return_value = "continue"

        result = phase.execute_with_checkpoint("Query", auto_approve=False)

    mock.assert_called_once()
```

### Behavior 8: Revise with Context
```python
def test_reruns_with_revision_context(tmp_path):
    """Given revision action, reruns with context."""
    # First run returns with open questions
    # User provides answers
    # Second run includes answers as context

    with patch.object(phase, '_runner') as mock_runner:
        mock_runner.run_sync.side_effect = [
            {"success": True, "output": "Questions: Q1?"},
            {"success": True, "output": "Complete. Path: doc.md"}
        ]

        # Mock interactive to return revise then continue
        with patch(...) as mock_prompt:
            mock_prompt.side_effect = [
                {"action": "revise", "revision_context": "Answer to Q1"},
                {"action": "continue"}
            ]

            result = phase.execute_with_checkpoint("Query", auto_approve=False)

    assert mock_runner.run_sync.call_count == 2
```

---

## Success Criteria

**Automated:**
- [ ] All research phase tests pass: `pytest silmari-rlm-act/tests/test_research_phase.py -v`

**Manual:**
- [ ] Research phase executes end-to-end
- [ ] Research document created in correct location
- [ ] CWA entry searchable
- [ ] Interactive checkpoint works

## Summary

This phase implements the research phase with:
- Claude Code execution for research
- Research path extraction from output
- CWA storage with summary generation
- PhaseResult return with artifacts
- Error handling
- Open question extraction
- Interactive checkpoints
- Revision with additional context
