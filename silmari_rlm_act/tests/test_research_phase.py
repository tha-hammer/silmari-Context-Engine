"""Tests for Research Phase - Phase 05.

This module tests the ResearchPhase class which:
- Executes research using Claude Code
- Extracts research paths from output
- Stores research in CWA
- Returns PhaseResult with artifacts
- Handles failures gracefully
- Extracts open questions
- Supports interactive checkpoints
- Supports revision with additional context
"""

from pathlib import Path
from unittest.mock import Mock, patch

from silmari_rlm_act.phases.research import ResearchPhase
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseResult, PhaseType, PhaseStatus
from context_window_array import EntryType


class TestExecuteResearch:
    """Behavior 1: Execute Research with Claude."""

    def test_invokes_claude_with_prompt(self, tmp_path: Path) -> None:
        """Given prompt, invokes Claude Code."""
        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        mock_runner = Mock()
        mock_runner.return_value = {
            "success": True,
            "output": "Research saved to thoughts/searchable/shared/research/doc.md",
            "elapsed": 10.0,
        }

        with patch.object(phase, "_run_claude", mock_runner):
            phase.execute("How does auth work?")

        mock_runner.assert_called_once()
        call_args = mock_runner.call_args
        assert "How does auth work?" in call_args[0][0]

    def test_loads_research_template(self, tmp_path: Path) -> None:
        """Given execution, loads research command template."""
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        template = commands_dir / "research_codebase.md"
        template.write_text("# Custom Research\n\n{research_question}")

        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        mock_runner = Mock()
        mock_runner.return_value = {"success": True, "output": "Done", "elapsed": 5.0}

        with patch.object(phase, "_run_claude", mock_runner):
            phase.execute("Test query")

        call_args = mock_runner.call_args
        assert "Custom Research" in call_args[0][0]

    def test_uses_default_template_when_missing(self, tmp_path: Path) -> None:
        """Given no template file, uses default template."""
        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        mock_runner = Mock()
        mock_runner.return_value = {"success": True, "output": "Done", "elapsed": 5.0}

        with patch.object(phase, "_run_claude", mock_runner):
            phase.execute("Test query")

        call_args = mock_runner.call_args
        assert "Research Task" in call_args[0][0]
        assert "Test query" in call_args[0][0]


class TestExtractResearchPath:
    """Behavior 2: Extract Research Path from Output."""

    def test_extracts_path_from_output(self, tmp_path: Path) -> None:
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

    def test_handles_absolute_path(self, tmp_path: Path) -> None:
        """Given absolute path, returns it."""
        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        abs_path = str(tmp_path / "thoughts" / "searchable" / "shared" / "research" / "doc.md")
        output = f"Saved to: {abs_path}"

        path = phase._extract_research_path(output)

        assert path is not None
        assert path.is_absolute()

    def test_returns_none_for_no_path(self, tmp_path: Path) -> None:
        """Given no path in output, returns None."""
        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        output = "Some output without a file path"

        path = phase._extract_research_path(output)

        assert path is None

    def test_handles_multiple_paths(self, tmp_path: Path) -> None:
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

    def test_extracts_path_with_hyphens_and_numbers(self, tmp_path: Path) -> None:
        """Given path with complex name, extracts it."""
        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        output = "Created: thoughts/searchable/shared/research/2026-01-05-my-complex-topic-123.md"

        path = phase._extract_research_path(output)

        assert path is not None
        assert "my-complex-topic-123.md" in str(path)


class TestStoreResearchInCWA:
    """Behavior 3: Store Research in CWA."""

    def test_creates_file_entry(self, tmp_path: Path) -> None:
        """Given research path, creates FILE entry in CWA."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text("# Research\n\nFindings here.")

        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        entry_id = phase._store_research_in_cwa(research_file)

        entry = cwa.store.get(entry_id)
        assert entry is not None
        assert entry.entry_type == EntryType.FILE
        assert "Research" in entry.content

    def test_generates_summary(self, tmp_path: Path) -> None:
        """Given research content, generates summary."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text(
            """# Authentication Research

## Overview
This document covers authentication patterns.

## Findings
- Pattern 1
- Pattern 2
"""
        )

        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        entry_id = phase._store_research_in_cwa(research_file)

        entry = cwa.store.get(entry_id)
        assert entry.summary is not None
        assert len(entry.summary) > 0
        assert "Authentication Research" in entry.summary

    def test_summary_includes_overview(self, tmp_path: Path) -> None:
        """Given research with overview, includes it in summary."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-topic.md"
        research_file.write_text(
            """# Topic Research

## Overview
Main findings about the topic are here.
"""
        )

        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        entry_id = phase._store_research_in_cwa(research_file)

        entry = cwa.store.get(entry_id)
        assert "Main findings" in entry.summary


class TestPhaseResultReturn:
    """Behavior 4: Return PhaseResult."""

    def test_returns_phase_result_on_success(self, tmp_path: Path) -> None:
        """Given successful research, returns PhaseResult."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-test.md"
        research_file.write_text("# Test Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        mock_runner = Mock()
        mock_runner.return_value = {
            "success": True,
            "output": f"Research saved to {research_file}",
            "elapsed": 10.0,
        }

        with patch.object(phase, "_run_claude", mock_runner):
            result = phase.execute("Test query")

        assert isinstance(result, PhaseResult)
        assert result.phase_type == PhaseType.RESEARCH
        assert result.status == PhaseStatus.COMPLETE
        assert len(result.artifacts) > 0

    def test_includes_artifact_path(self, tmp_path: Path) -> None:
        """Given research created, includes path in artifacts."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-test.md"
        research_file.write_text("# Test Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        mock_runner = Mock()
        mock_runner.return_value = {
            "success": True,
            "output": f"Research saved to {research_file}",
            "elapsed": 10.0,
        }

        with patch.object(phase, "_run_claude", mock_runner):
            result = phase.execute("Test query")

        assert any("2026-01-05-test.md" in a for a in result.artifacts)

    def test_includes_duration(self, tmp_path: Path) -> None:
        """Given completed research, includes duration."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-test.md"
        research_file.write_text("# Test Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        mock_runner = Mock()
        mock_runner.return_value = {
            "success": True,
            "output": f"Research saved to {research_file}",
            "elapsed": 15.5,
        }

        with patch.object(phase, "_run_claude", mock_runner):
            result = phase.execute("Test query")

        assert result.duration_seconds is not None
        assert result.duration_seconds >= 0


class TestHandleFailure:
    """Behavior 5: Handle Research Failure."""

    def test_returns_error_on_claude_failure(self, tmp_path: Path) -> None:
        """Given Claude failure, returns error PhaseResult."""
        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        mock_runner = Mock()
        mock_runner.return_value = {
            "success": False,
            "output": "",
            "error": "Connection error",
            "elapsed": 1.0,
        }

        with patch.object(phase, "_run_claude", mock_runner):
            result = phase.execute("Test query")

        assert result.status == PhaseStatus.FAILED
        assert len(result.errors) > 0
        assert "Connection error" in result.errors[0]

    def test_returns_error_on_exception(self, tmp_path: Path) -> None:
        """Given exception, returns error PhaseResult."""
        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        mock_runner = Mock()
        mock_runner.side_effect = RuntimeError("Unexpected error")

        with patch.object(phase, "_run_claude", mock_runner):
            result = phase.execute("Test query")

        assert result.status == PhaseStatus.FAILED
        assert len(result.errors) > 0
        assert "Unexpected error" in result.errors[0]

    def test_returns_error_when_no_path_extracted(self, tmp_path: Path) -> None:
        """Given no research path in output, returns error."""
        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        mock_runner = Mock()
        mock_runner.return_value = {
            "success": True,
            "output": "Done but no path mentioned",
            "elapsed": 5.0,
        }

        with patch.object(phase, "_run_claude", mock_runner):
            result = phase.execute("Test query")

        assert result.status == PhaseStatus.FAILED
        assert any("No research document" in e for e in result.errors)


class TestExtractOpenQuestions:
    """Behavior 6: Extract Open Questions."""

    def test_extracts_open_questions(self, tmp_path: Path) -> None:
        """Given output with questions, extracts them."""
        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        output = """
Research complete.

Open Questions:
1. What authentication provider is used?
2. How are sessions managed?
"""

        questions = phase._extract_open_questions(output)

        assert len(questions) == 2
        assert "authentication provider" in questions[0]
        assert "sessions" in questions[1]

    def test_returns_empty_list_when_no_questions(self, tmp_path: Path) -> None:
        """Given no questions section, returns empty list."""
        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        output = "Research complete. No questions remain."

        questions = phase._extract_open_questions(output)

        assert questions == []

    def test_handles_question_marks_section(self, tmp_path: Path) -> None:
        """Given questions with '?' format, extracts them."""
        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        output = """
Research done.

Remaining Questions:
- What is the API rate limit?
- Should we use Redis or Memcached?
"""

        questions = phase._extract_open_questions(output)

        assert len(questions) >= 2


class TestInteractiveCheckpoint:
    """Behavior 7: Interactive Checkpoint."""

    def test_prompts_user_when_not_auto(self, tmp_path: Path) -> None:
        """Given non-auto mode, prompts user."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-test.md"
        research_file.write_text("# Test\n\nContent")

        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        mock_runner = Mock()
        mock_runner.return_value = {
            "success": True,
            "output": f"Saved to {research_file}",
            "elapsed": 5.0,
        }

        with patch.object(phase, "_run_claude", mock_runner):
            with patch(
                "silmari_rlm_act.phases.research.prompt_research_action"
            ) as mock_prompt:
                mock_prompt.return_value = "continue"

                phase.execute_with_checkpoint("Query", auto_approve=False)

        mock_prompt.assert_called_once()

    def test_skips_prompt_when_auto(self, tmp_path: Path) -> None:
        """Given auto mode, skips user prompt."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-test.md"
        research_file.write_text("# Test\n\nContent")

        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        mock_runner = Mock()
        mock_runner.return_value = {
            "success": True,
            "output": f"Saved to {research_file}",
            "elapsed": 5.0,
        }

        with patch.object(phase, "_run_claude", mock_runner):
            with patch(
                "silmari_rlm_act.phases.research.prompt_research_action"
            ) as mock_prompt:
                phase.execute_with_checkpoint("Query", auto_approve=True)

        mock_prompt.assert_not_called()

    def test_returns_action_in_metadata(self, tmp_path: Path) -> None:
        """Given user action, includes in metadata."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-test.md"
        research_file.write_text("# Test\n\nContent")

        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        mock_runner = Mock()
        mock_runner.return_value = {
            "success": True,
            "output": f"Saved to {research_file}",
            "elapsed": 5.0,
        }

        with patch.object(phase, "_run_claude", mock_runner):
            with patch(
                "silmari_rlm_act.phases.research.prompt_research_action"
            ) as mock_prompt:
                mock_prompt.return_value = "continue"

                result = phase.execute_with_checkpoint("Query", auto_approve=False)

        assert result.metadata.get("user_action") == "continue"


class TestReviseWithContext:
    """Behavior 8: Revise with Additional Context."""

    def test_reruns_with_revision_context(self, tmp_path: Path) -> None:
        """Given revision action, reruns with context."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-test.md"
        research_file.write_text("# Test\n\nContent")

        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        call_count = 0

        def mock_claude_runner(prompt: str, timeout: int = 1200) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "success": True,
                    "output": f"Saved to {research_file}",
                    "elapsed": 5.0,
                }
            else:
                return {
                    "success": True,
                    "output": f"Revised and saved to {research_file}",
                    "elapsed": 5.0,
                }

        with patch.object(phase, "_run_claude", side_effect=mock_claude_runner):
            with patch(
                "silmari_rlm_act.phases.research.prompt_research_action"
            ) as mock_prompt:
                mock_prompt.side_effect = ["revise", "continue"]

                with patch(
                    "silmari_rlm_act.phases.research.collect_multiline_input"
                ) as mock_input:
                    mock_input.return_value = "More context about auth"

                    phase.execute_with_checkpoint("Query", auto_approve=False)

        assert call_count == 2

    def test_includes_additional_context_in_prompt(self, tmp_path: Path) -> None:
        """Given additional context, includes in prompt."""
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-05-test.md"
        research_file.write_text("# Test\n\nContent")

        cwa = CWAIntegration()
        phase = ResearchPhase(project_path=tmp_path, cwa=cwa)

        prompts_received = []

        def capture_prompt(prompt: str, timeout: int = 1200) -> dict:
            prompts_received.append(prompt)
            return {
                "success": True,
                "output": f"Saved to {research_file}",
                "elapsed": 5.0,
            }

        with patch.object(phase, "_run_claude", side_effect=capture_prompt):
            phase.execute("Query", additional_context="Extra info here")

        assert len(prompts_received) == 1
        assert "Extra info here" in prompts_received[0]
