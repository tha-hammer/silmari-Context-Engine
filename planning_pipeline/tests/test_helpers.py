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


# ==============================================================================
# REQ_005: Auto-detection and file resolution tests
# ==============================================================================

from planning_pipeline.helpers import (
    detect_file_type,
    find_sibling_hierarchy,
    resolve_file_path,
    is_sibling_pair_valid,
)
import json


class TestDetectFileType:
    """REQ_005.1: detect_file_type() function tests."""

    def test_returns_markdown_for_md_extension(self, tmp_path):
        """Returns 'markdown' for .md files."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Markdown content")
        result = detect_file_type(md_file)
        assert result == "markdown"

    def test_returns_markdown_case_insensitive(self, tmp_path):
        """Returns 'markdown' for .MD files (case-insensitive)."""
        md_file = tmp_path / "test.MD"
        md_file.write_text("# Markdown content")
        result = detect_file_type(md_file)
        assert result == "markdown"

    def test_returns_json_for_json_extension(self, tmp_path):
        """Returns 'json' for .json files."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value"}')
        result = detect_file_type(json_file)
        assert result == "json"

    def test_returns_json_case_insensitive(self, tmp_path):
        """Returns 'json' for .JSON files (case-insensitive)."""
        json_file = tmp_path / "test.JSON"
        json_file.write_text('{"key": "value"}')
        result = detect_file_type(json_file)
        assert result == "json"

    def test_returns_unknown_for_other_extensions(self, tmp_path):
        """Returns 'unknown' for other file extensions."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("plain text")
        result = detect_file_type(txt_file)
        assert result == "unknown"

    def test_returns_unknown_for_py_files(self, tmp_path):
        """Returns 'unknown' for .py files."""
        py_file = tmp_path / "test.py"
        py_file.write_text("print('hello')")
        result = detect_file_type(py_file)
        assert result == "unknown"

    def test_handles_path_objects(self, tmp_path):
        """Accepts Path objects as input."""
        md_file = tmp_path / "test.md"
        md_file.write_text("content")
        result = detect_file_type(Path(md_file))
        assert result == "markdown"

    def test_handles_string_paths(self, tmp_path):
        """Accepts string paths as input."""
        md_file = tmp_path / "test.md"
        md_file.write_text("content")
        result = detect_file_type(str(md_file))
        assert result == "markdown"

    def test_raises_file_not_found_for_missing_file(self, tmp_path):
        """Raises FileNotFoundError for non-existent files."""
        missing_file = tmp_path / "does_not_exist.md"
        with pytest.raises(FileNotFoundError):
            detect_file_type(missing_file)

    def test_handles_absolute_paths(self, tmp_path):
        """Works with absolute paths."""
        md_file = tmp_path / "test.md"
        md_file.write_text("content")
        assert md_file.is_absolute()
        result = detect_file_type(md_file)
        assert result == "markdown"

    def test_handles_relative_paths(self, tmp_path, monkeypatch):
        """Works with relative paths when file exists."""
        md_file = tmp_path / "test.md"
        md_file.write_text("content")
        monkeypatch.chdir(tmp_path)
        result = detect_file_type("test.md")
        assert result == "markdown"


class TestFindSiblingHierarchy:
    """REQ_005.2: find_sibling_hierarchy() function tests."""

    def test_finds_requirement_hierarchy_json(self, tmp_path):
        """Finds requirement_hierarchy.json in same directory as .md file."""
        plan_dir = tmp_path / "plans" / "2026-01-01-feature"
        plan_dir.mkdir(parents=True)
        md_file = plan_dir / "00-overview.md"
        md_file.write_text("# Overview")
        hierarchy_file = plan_dir / "requirement_hierarchy.json"
        hierarchy_data = {
            "requirements": [
                {"id": "REQ_001", "description": "Test", "type": "parent"}
            ],
            "metadata": {}
        }
        hierarchy_file.write_text(json.dumps(hierarchy_data))

        result = find_sibling_hierarchy(md_file)
        assert result is not None
        assert result.name == "requirement_hierarchy.json"
        assert result.is_absolute()

    def test_finds_requirements_hierarchy_json(self, tmp_path):
        """Finds requirements_hierarchy.json (plural) in same directory."""
        plan_dir = tmp_path / "plans" / "2026-01-01-feature"
        plan_dir.mkdir(parents=True)
        md_file = plan_dir / "00-overview.md"
        md_file.write_text("# Overview")
        hierarchy_file = plan_dir / "requirements_hierarchy.json"
        hierarchy_data = {
            "requirements": [
                {"id": "REQ_001", "description": "Test", "type": "parent"}
            ],
            "metadata": {}
        }
        hierarchy_file.write_text(json.dumps(hierarchy_data))

        result = find_sibling_hierarchy(md_file)
        assert result is not None
        assert result.name == "requirements_hierarchy.json"

    def test_finds_hierarchy_json(self, tmp_path):
        """Finds hierarchy.json (short name) in same directory."""
        plan_dir = tmp_path / "plans" / "2026-01-01-feature"
        plan_dir.mkdir(parents=True)
        md_file = plan_dir / "00-overview.md"
        md_file.write_text("# Overview")
        hierarchy_file = plan_dir / "hierarchy.json"
        hierarchy_data = {
            "requirements": [
                {"id": "REQ_001", "description": "Test", "type": "parent"}
            ],
            "metadata": {}
        }
        hierarchy_file.write_text(json.dumps(hierarchy_data))

        result = find_sibling_hierarchy(md_file)
        assert result is not None
        assert result.name == "hierarchy.json"

    def test_prefers_requirement_hierarchy_over_requirements(self, tmp_path):
        """Prefers requirement_hierarchy.json over requirements_hierarchy.json."""
        plan_dir = tmp_path / "plans" / "2026-01-01-feature"
        plan_dir.mkdir(parents=True)
        md_file = plan_dir / "00-overview.md"
        md_file.write_text("# Overview")

        hierarchy_data = {
            "requirements": [
                {"id": "REQ_001", "description": "Test", "type": "parent"}
            ],
            "metadata": {}
        }
        # Create both files
        (plan_dir / "requirement_hierarchy.json").write_text(json.dumps(hierarchy_data))
        (plan_dir / "requirements_hierarchy.json").write_text(json.dumps(hierarchy_data))

        result = find_sibling_hierarchy(md_file)
        assert result is not None
        assert result.name == "requirement_hierarchy.json"

    def test_returns_none_when_no_hierarchy_exists(self, tmp_path):
        """Returns None when no hierarchy file exists."""
        plan_dir = tmp_path / "plans" / "2026-01-01-feature"
        plan_dir.mkdir(parents=True)
        md_file = plan_dir / "00-overview.md"
        md_file.write_text("# Overview")

        result = find_sibling_hierarchy(md_file)
        assert result is None

    def test_validates_json_is_parseable(self, tmp_path):
        """Returns None when JSON is not parseable as RequirementHierarchy."""
        plan_dir = tmp_path / "plans" / "2026-01-01-feature"
        plan_dir.mkdir(parents=True)
        md_file = plan_dir / "00-overview.md"
        md_file.write_text("# Overview")
        hierarchy_file = plan_dir / "requirement_hierarchy.json"
        hierarchy_file.write_text("not valid json {{{")

        result = find_sibling_hierarchy(md_file)
        assert result is None

    def test_validates_hierarchy_structure(self, tmp_path):
        """Returns None when JSON doesn't have requirements field."""
        plan_dir = tmp_path / "plans" / "2026-01-01-feature"
        plan_dir.mkdir(parents=True)
        md_file = plan_dir / "00-overview.md"
        md_file.write_text("# Overview")
        hierarchy_file = plan_dir / "requirement_hierarchy.json"
        hierarchy_file.write_text('{"other_field": "value"}')

        result = find_sibling_hierarchy(md_file)
        assert result is None

    def test_returns_absolute_path(self, tmp_path):
        """Returns an absolute Path."""
        plan_dir = tmp_path / "plans" / "2026-01-01-feature"
        plan_dir.mkdir(parents=True)
        md_file = plan_dir / "00-overview.md"
        md_file.write_text("# Overview")
        hierarchy_file = plan_dir / "requirement_hierarchy.json"
        hierarchy_data = {
            "requirements": [
                {"id": "REQ_001", "description": "Test", "type": "parent"}
            ],
            "metadata": {}
        }
        hierarchy_file.write_text(json.dumps(hierarchy_data))

        result = find_sibling_hierarchy(md_file)
        assert result is not None
        assert result.is_absolute()


class TestResolveFilePathHierarchy:
    """REQ_005.4: resolve_file_path() with file_type='hierarchy' tests."""

    @pytest.fixture
    def temp_project_with_plans(self, tmp_path):
        """Create project structure with plans directories."""
        # Create thoughts/searchable/shared/plans structure
        plans_dir = tmp_path / "thoughts" / "searchable" / "shared" / "plans"
        plans_dir.mkdir(parents=True)

        # Create a plan directory with hierarchy file
        plan_subdir = plans_dir / "2026-01-01-tdd-feature"
        plan_subdir.mkdir()

        hierarchy_data = {
            "requirements": [
                {"id": "REQ_001", "description": "Test", "type": "parent"}
            ],
            "metadata": {}
        }
        (plan_subdir / "requirement_hierarchy.json").write_text(json.dumps(hierarchy_data))
        (plan_subdir / "00-overview.md").write_text("# Overview")

        return tmp_path

    def test_resolves_absolute_hierarchy_path(self, temp_project_with_plans):
        """Resolves absolute path to hierarchy file."""
        plans_dir = temp_project_with_plans / "thoughts" / "searchable" / "shared" / "plans"
        hierarchy_path = plans_dir / "2026-01-01-tdd-feature" / "requirement_hierarchy.json"

        result = resolve_file_path(temp_project_with_plans, str(hierarchy_path), "hierarchy")
        assert result is not None
        assert result.exists()
        assert result.name == "requirement_hierarchy.json"

    def test_resolves_relative_hierarchy_path(self, temp_project_with_plans):
        """Resolves relative path to hierarchy file."""
        rel_path = "thoughts/searchable/shared/plans/2026-01-01-tdd-feature/requirement_hierarchy.json"

        result = resolve_file_path(temp_project_with_plans, rel_path, "hierarchy")
        assert result is not None
        assert result.exists()

    def test_searches_plans_directories_for_json(self, temp_project_with_plans):
        """Searches plans directories for .json files when file_type='hierarchy'."""
        result = resolve_file_path(
            temp_project_with_plans,
            "requirement_hierarchy.json",
            "hierarchy"
        )
        # Should search through plans directories and find the hierarchy file
        assert result is not None
        assert result.name == "requirement_hierarchy.json"

    def test_finds_hierarchy_by_partial_name(self, temp_project_with_plans):
        """Finds hierarchy file by partial directory name match."""
        result = resolve_file_path(
            temp_project_with_plans,
            "2026-01-01-tdd-feature/requirement_hierarchy.json",
            "hierarchy"
        )
        assert result is not None
        assert result.name == "requirement_hierarchy.json"

    def test_maintains_backward_compatibility_research(self, temp_project_with_plans):
        """Maintains backward compatibility for file_type='research'."""
        # Create a research file
        research_dir = temp_project_with_plans / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-01-test-research.md"
        research_file.write_text("# Research")

        result = resolve_file_path(
            temp_project_with_plans,
            "2026-01-01-test-research.md",
            "research"
        )
        assert result is not None
        assert result.name == "2026-01-01-test-research.md"

    def test_maintains_backward_compatibility_plans(self, temp_project_with_plans):
        """Maintains backward compatibility for file_type='plans'."""
        result = resolve_file_path(
            temp_project_with_plans,
            "thoughts/searchable/shared/plans/2026-01-01-tdd-feature/00-overview.md",
            "plans"
        )
        assert result is not None
        assert result.name == "00-overview.md"

    def test_returns_none_for_nonexistent_hierarchy(self, temp_project_with_plans):
        """Returns None when hierarchy file doesn't exist."""
        result = resolve_file_path(
            temp_project_with_plans,
            "nonexistent_hierarchy.json",
            "hierarchy"
        )
        assert result is None


class TestIsSiblingPairValid:
    """REQ_005.5: is_sibling_pair_valid() function tests."""

    def test_returns_true_for_valid_pair(self, tmp_path):
        """Returns True when both requirement_hierarchy.json and 00-overview.md exist."""
        plan_dir = tmp_path / "plans" / "2026-01-01-feature"
        plan_dir.mkdir(parents=True)

        # Create 00-overview.md with reference to hierarchy
        overview_content = """# Feature Overview

## Metadata
- hierarchy: requirement_hierarchy.json

## Description
This is the feature overview.
"""
        (plan_dir / "00-overview.md").write_text(overview_content)

        # Create requirement_hierarchy.json with reference to overview
        hierarchy_data = {
            "requirements": [
                {"id": "REQ_001", "description": "Test", "type": "parent"}
            ],
            "metadata": {
                "overview_file": "00-overview.md"
            }
        }
        (plan_dir / "requirement_hierarchy.json").write_text(json.dumps(hierarchy_data))

        result = is_sibling_pair_valid(plan_dir)
        assert result is True

    def test_returns_false_when_overview_missing(self, tmp_path):
        """Returns False when 00-overview.md is missing."""
        plan_dir = tmp_path / "plans" / "2026-01-01-feature"
        plan_dir.mkdir(parents=True)

        hierarchy_data = {
            "requirements": [
                {"id": "REQ_001", "description": "Test", "type": "parent"}
            ],
            "metadata": {}
        }
        (plan_dir / "requirement_hierarchy.json").write_text(json.dumps(hierarchy_data))

        result = is_sibling_pair_valid(plan_dir)
        assert result is False

    def test_returns_false_when_hierarchy_missing(self, tmp_path):
        """Returns False when requirement_hierarchy.json is missing."""
        plan_dir = tmp_path / "plans" / "2026-01-01-feature"
        plan_dir.mkdir(parents=True)

        (plan_dir / "00-overview.md").write_text("# Overview")

        result = is_sibling_pair_valid(plan_dir)
        assert result is False

    def test_returns_false_for_empty_directory(self, tmp_path):
        """Returns False for empty directory."""
        plan_dir = tmp_path / "plans" / "2026-01-01-feature"
        plan_dir.mkdir(parents=True)

        result = is_sibling_pair_valid(plan_dir)
        assert result is False

    def test_returns_false_for_nonexistent_directory(self, tmp_path):
        """Returns False for non-existent directory."""
        plan_dir = tmp_path / "plans" / "nonexistent"

        result = is_sibling_pair_valid(plan_dir)
        assert result is False

    def test_accepts_requirements_hierarchy_json(self, tmp_path):
        """Accepts requirements_hierarchy.json (plural) as valid."""
        plan_dir = tmp_path / "plans" / "2026-01-01-feature"
        plan_dir.mkdir(parents=True)

        (plan_dir / "00-overview.md").write_text("# Overview")
        hierarchy_data = {
            "requirements": [
                {"id": "REQ_001", "description": "Test", "type": "parent"}
            ],
            "metadata": {"overview_file": "00-overview.md"}
        }
        (plan_dir / "requirements_hierarchy.json").write_text(json.dumps(hierarchy_data))

        result = is_sibling_pair_valid(plan_dir)
        assert result is True

    def test_validates_hierarchy_json_is_parseable(self, tmp_path):
        """Returns False when hierarchy JSON is not parseable."""
        plan_dir = tmp_path / "plans" / "2026-01-01-feature"
        plan_dir.mkdir(parents=True)

        (plan_dir / "00-overview.md").write_text("# Overview")
        (plan_dir / "requirement_hierarchy.json").write_text("invalid json {{{")

        result = is_sibling_pair_valid(plan_dir)
        assert result is False

    def test_validates_hierarchy_has_requirements(self, tmp_path):
        """Returns False when hierarchy JSON lacks requirements field."""
        plan_dir = tmp_path / "plans" / "2026-01-01-feature"
        plan_dir.mkdir(parents=True)

        (plan_dir / "00-overview.md").write_text("# Overview")
        (plan_dir / "requirement_hierarchy.json").write_text('{"metadata": {}}')

        result = is_sibling_pair_valid(plan_dir)
        assert result is False

    def test_accepts_hierarchy_json_shortname(self, tmp_path):
        """Accepts hierarchy.json (short name) as valid."""
        plan_dir = tmp_path / "plans" / "2026-01-01-feature"
        plan_dir.mkdir(parents=True)

        (plan_dir / "00-overview.md").write_text("# Overview")
        hierarchy_data = {
            "requirements": [
                {"id": "REQ_001", "description": "Test", "type": "parent"}
            ],
            "metadata": {}
        }
        (plan_dir / "hierarchy.json").write_text(json.dumps(hierarchy_data))

        result = is_sibling_pair_valid(plan_dir)
        assert result is True
