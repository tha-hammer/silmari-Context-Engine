"""Tests for helper functions - Behavior 1, 2, 3."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from planning_pipeline.helpers import extract_file_path, discover_thoughts_files


class TestExtractFilePath:
    """Behavior 1: Extract file path from Claude output."""

    def test_extracts_research_path(self):
        """Given output with research path, returns the path."""
        output = """
        Research complete!
        Created: thoughts/searchable/research/2025-01-01-test-research.md
        See the document for details.
        """
        result = extract_file_path(output, "research")
        assert result == "thoughts/searchable/research/2025-01-01-test-research.md"

    def test_extracts_plan_path(self):
        """Given output with plan path, returns the path."""
        output = "Plan written to thoughts/searchable/plans/2025-01-01-feature/00-overview.md"
        result = extract_file_path(output, "plan")
        assert result == "thoughts/searchable/plans/2025-01-01-feature/00-overview.md"

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
        Created thoughts/searchable/research/2025-01-01-first-research.md
        Also created thoughts/searchable/research/2025-01-01-second-research.md
        """
        result = extract_file_path(output, "research")
        assert result == "thoughts/searchable/research/2025-01-01-first-research.md"

    def test_handles_phase_file_type(self):
        """Given output with phase file, extracts it."""
        output = "Created thoughts/searchable/plans/2025-01-01-feat/01-phase-1-setup.md"
        result = extract_file_path(output, "phase")
        assert result == "thoughts/searchable/plans/2025-01-01-feat/01-phase-1-setup.md"


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
        - thoughts/searchable/plans/2025-01-01-feature/01-phase-1-setup.md
        - thoughts/searchable/plans/2025-01-01-feature/02-phase-2-impl.md
        - thoughts/searchable/plans/2025-01-01-feature/03-phase-3-test.md
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
        output = "Created thoughts/searchable/plans/2025-01-01-feat/00-overview.md"
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


class TestDiscoverThoughtsFiles:
    """Tests for discover_thoughts_files function."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project with thoughts directory."""
        # Create searchable/shared/research structure
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        plans_dir = tmp_path / "thoughts" / "searchable" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        return tmp_path

    def test_discovers_today_files(self, temp_project):
        """Discovers files with today's date."""
        research_dir = temp_project / "thoughts" / "searchable" / "shared" / "research"
        today = datetime.now().strftime('%Y-%m-%d')
        (research_dir / f"{today}-test-research.md").write_text("content")

        result = discover_thoughts_files(temp_project, "research", days_back=0)
        assert len(result) == 1
        assert today in result[0].name

    def test_excludes_old_files_with_days_back_0(self, temp_project):
        """Files older than today are excluded when days_back=0."""
        research_dir = temp_project / "thoughts" / "searchable" / "shared" / "research"
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        (research_dir / f"{yesterday}-old-research.md").write_text("content")

        result = discover_thoughts_files(temp_project, "research", days_back=0)
        assert len(result) == 0

    def test_includes_old_files_with_days_back(self, temp_project):
        """Files within days_back are included."""
        research_dir = temp_project / "thoughts" / "searchable" / "shared" / "research"
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        (research_dir / f"{yesterday}-old-research.md").write_text("content")

        result = discover_thoughts_files(temp_project, "research", days_back=7)
        assert len(result) == 1

    def test_returns_empty_for_missing_dir(self, tmp_path):
        """Returns empty list when thoughts dir doesn't exist."""
        result = discover_thoughts_files(tmp_path, "research")
        assert result == []

    def test_sorts_alphabetically(self, temp_project):
        """Files are sorted alphabetically by name."""
        research_dir = temp_project / "thoughts" / "searchable" / "shared" / "research"
        today = datetime.now().strftime('%Y-%m-%d')
        (research_dir / f"{today}-zebra.md").write_text("content")
        (research_dir / f"{today}-alpha.md").write_text("content")
        (research_dir / f"{today}-middle.md").write_text("content")

        result = discover_thoughts_files(temp_project, "research", days_back=0)
        assert len(result) == 3
        assert "alpha" in result[0].name
        assert "middle" in result[1].name
        assert "zebra" in result[2].name

    def test_discovers_plans_files(self, temp_project):
        """Discovers files from plans directory."""
        plans_dir = temp_project / "thoughts" / "searchable" / "shared" / "plans"
        today = datetime.now().strftime('%Y-%m-%d')
        (plans_dir / f"{today}-test-plan.md").write_text("content")

        result = discover_thoughts_files(temp_project, "plans", days_back=0)
        assert len(result) == 1
        assert "plan" in result[0].name

    def test_prefers_shared_over_searchable(self, temp_project):
        """Prefers thoughts/searchable over thoughts/searchable/shared."""
        # Create thoughts/searchable/research (higher priority)
        shared_dir = temp_project / "thoughts" / "shared" / "research"
        shared_dir.mkdir(parents=True)
        today = datetime.now().strftime('%Y-%m-%d')
        (shared_dir / f"{today}-shared.md").write_text("content")

        # Also has searchable version
        searchable_dir = temp_project / "thoughts" / "searchable" / "shared" / "research"
        (searchable_dir / f"{today}-searchable.md").write_text("content")

        result = discover_thoughts_files(temp_project, "research", days_back=0)
        # Should find the shared one (first in search order)
        assert len(result) == 1
        assert "shared" in result[0].name
