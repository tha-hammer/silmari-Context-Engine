"""Tests for helper functions - Behavior 1, 2, 3."""

import pytest
from planning_pipeline.helpers import extract_file_path


class TestExtractFilePath:
    """Behavior 1: Extract file path from Claude output."""

    def test_extracts_research_path(self):
        """Given output with research path, returns the path."""
        output = """
        Research complete!
        Created: thoughts/shared/research/2025-01-01-test-research.md
        See the document for details.
        """
        result = extract_file_path(output, "research")
        assert result == "thoughts/shared/research/2025-01-01-test-research.md"

    def test_extracts_plan_path(self):
        """Given output with plan path, returns the path."""
        output = "Plan written to thoughts/shared/plans/2025-01-01-feature/00-overview.md"
        result = extract_file_path(output, "plan")
        assert result == "thoughts/shared/plans/2025-01-01-feature/00-overview.md"

    def test_returns_none_when_no_match(self):
        """Given output without matching path, returns None."""
        output = "No file paths here, just text."
        result = extract_file_path(output, "research")
        assert result is None

    def test_handles_empty_output(self):
        """Given empty output, returns None."""
        result = extract_file_path("", "research")
        assert result is None

    def test_extracts_first_match_when_multiple(self):
        """Given output with multiple paths, returns first match."""
        output = """
        Created thoughts/shared/research/2025-01-01-first-research.md
        Also created thoughts/shared/research/2025-01-01-second-research.md
        """
        result = extract_file_path(output, "research")
        assert result == "thoughts/shared/research/2025-01-01-first-research.md"

    def test_handles_phase_file_type(self):
        """Given output with phase file, extracts it."""
        output = "Created thoughts/shared/plans/2025-01-01-feat/01-phase-1-setup.md"
        result = extract_file_path(output, "phase")
        assert result == "thoughts/shared/plans/2025-01-01-feat/01-phase-1-setup.md"


# Import for Behavior 2
from planning_pipeline.helpers import extract_open_questions


class TestExtractOpenQuestions:
    """Behavior 2: Extract open questions from research output."""

    def test_extracts_dash_questions(self):
        """Given output with dash-prefixed questions, returns list of questions."""
        output = """
        ## Open Questions
        - What authentication method should we use?
        - Should we support multiple databases?

        ## Next Steps
        """
        result = extract_open_questions(output)
        assert result == [
            "What authentication method should we use?",
            "Should we support multiple databases?"
        ]

    def test_extracts_numbered_questions(self):
        """Given output with numbered questions, returns list of questions."""
        output = """
        Open Questions:
        1. First question here
        2. Second question here
        """
        result = extract_open_questions(output)
        assert result == ["First question here", "Second question here"]

    def test_returns_empty_list_when_no_questions(self):
        """Given output without questions section, returns empty list."""
        output = "Just some regular output without questions."
        result = extract_open_questions(output)
        assert result == []

    def test_stops_at_next_heading(self):
        """Given output with questions followed by another heading, only extracts questions."""
        output = """
        ## Open Questions
        - Only this question
        ## Summary
        - This is not a question
        """
        result = extract_open_questions(output)
        assert result == ["Only this question"]

    def test_handles_empty_output(self):
        """Given empty output, returns empty list."""
        result = extract_open_questions("")
        assert result == []

    def test_handles_asterisk_bullets(self):
        """Given output with asterisk-prefixed questions, returns list of questions."""
        output = """
        ## Open Questions
        * What framework should we use?
        * How should we handle errors?
        """
        result = extract_open_questions(output)
        assert result == [
            "What framework should we use?",
            "How should we handle errors?"
        ]

    def test_extracts_from_sample_fixture(self, sample_research_output):
        """Given sample fixture output, extracts the open questions."""
        result = extract_open_questions(sample_research_output)
        assert "What authentication method should we use?" in result
        assert "Should we support multiple databases?" in result


# Import for Behavior 3
from planning_pipeline.helpers import extract_phase_files


class TestExtractPhaseFiles:
    """Behavior 3: Extract phase files from Claude output."""

    def test_extracts_phase_files(self):
        """Given output with phase files, returns list of paths."""
        output = """
        Created phase files:
        - thoughts/shared/plans/2025-01-01-feature/01-phase-1-setup.md
        - thoughts/shared/plans/2025-01-01-feature/02-phase-2-impl.md
        - thoughts/shared/plans/2025-01-01-feature/03-phase-3-test.md
        """
        result = extract_phase_files(output)
        assert len(result) == 3
        assert "01-phase-1-setup.md" in result[0]
        assert "02-phase-2-impl.md" in result[1]

    def test_returns_empty_for_no_phases(self):
        """Given output without phase files, returns empty list."""
        output = "No phase files created."
        result = extract_phase_files(output)
        assert result == []

    def test_extracts_overview_file(self):
        """Given output with overview file, extracts it."""
        output = "Created thoughts/shared/plans/2025-01-01-feat/00-overview.md"
        result = extract_phase_files(output)
        assert len(result) == 1

    def test_handles_empty_output(self):
        """Given empty output, returns empty list."""
        result = extract_phase_files("")
        assert result == []

    def test_extracts_from_sample_fixture(self, sample_phase_output):
        """Given sample fixture output, extracts the phase files."""
        result = extract_phase_files(sample_phase_output)
        assert len(result) == 3
        assert "01-phase-1-setup.md" in result[0]
        assert "02-phase-2-impl.md" in result[1]
        assert "03-phase-3-test.md" in result[2]
