"""Tests for phase_execution module."""

import tempfile
from pathlib import Path

import pytest

from planning_pipeline.phase_execution.plan_discovery import (
    PlanPhase,
    discover_plan_phases,
    get_next_phase,
    iterate_plan_phases,
)
from planning_pipeline.phase_execution.prompt_builder import (
    build_overview_prompt,
    build_phase_prompt,
)


class TestPlanDiscovery:
    """Tests for plan_discovery module."""

    def test_discover_plan_phases_finds_numbered_phases(self, tmp_path: Path):
        """Test that discover_plan_phases finds correctly numbered phase files."""
        # Create test plan files
        prefix = "2026-01-03-tdd-feature"
        (tmp_path / f"{prefix}-00-overview.md").write_text("# Overview")
        (tmp_path / f"{prefix}-01-setup.md").write_text("# Setup")
        (tmp_path / f"{prefix}-02-implementation.md").write_text("# Implementation")

        phases = discover_plan_phases(tmp_path, prefix)

        assert len(phases) == 3
        assert phases[0].order == 0
        assert phases[0].name == "overview"
        assert phases[0].is_overview is True
        assert phases[1].order == 1
        assert phases[1].name == "setup"
        assert phases[2].order == 2
        assert phases[2].name == "implementation"

    def test_discover_plan_phases_ignores_non_matching_files(self, tmp_path: Path):
        """Test that non-matching files are ignored."""
        prefix = "2026-01-03-tdd-feature"
        (tmp_path / f"{prefix}-00-overview.md").write_text("# Overview")
        (tmp_path / "other-file.md").write_text("# Other")
        (tmp_path / f"different-prefix-01-setup.md").write_text("# Setup")

        phases = discover_plan_phases(tmp_path, prefix)

        assert len(phases) == 1
        assert phases[0].name == "overview"

    def test_discover_plan_phases_returns_empty_for_missing_dir(self, tmp_path: Path):
        """Test that missing directory returns empty list."""
        phases = discover_plan_phases(tmp_path / "nonexistent", "any-prefix")
        assert phases == []

    def test_get_next_phase_returns_first_non_overview(self, tmp_path: Path):
        """Test that get_next_phase skips overview by default."""
        prefix = "test-plan"
        (tmp_path / f"{prefix}-00-overview.md").write_text("# Overview")
        (tmp_path / f"{prefix}-01-first.md").write_text("# First")

        next_phase = get_next_phase(tmp_path, prefix, current_phase=None)

        assert next_phase is not None
        assert next_phase.name == "first"
        assert next_phase.order == 1

    def test_get_next_phase_advances_correctly(self, tmp_path: Path):
        """Test that get_next_phase returns the phase after current."""
        prefix = "test-plan"
        (tmp_path / f"{prefix}-00-overview.md").write_text("# Overview")
        (tmp_path / f"{prefix}-01-first.md").write_text("# First")
        (tmp_path / f"{prefix}-02-second.md").write_text("# Second")

        next_phase = get_next_phase(tmp_path, prefix, current_phase=1)

        assert next_phase is not None
        assert next_phase.name == "second"
        assert next_phase.order == 2

    def test_get_next_phase_returns_none_at_end(self, tmp_path: Path):
        """Test that get_next_phase returns None when at last phase."""
        prefix = "test-plan"
        (tmp_path / f"{prefix}-01-only.md").write_text("# Only")

        next_phase = get_next_phase(tmp_path, prefix, current_phase=1)

        assert next_phase is None

    def test_iterate_plan_phases_respects_skip_overview(self, tmp_path: Path):
        """Test that iterate_plan_phases can skip overview."""
        prefix = "test-plan"
        (tmp_path / f"{prefix}-00-overview.md").write_text("# Overview")
        (tmp_path / f"{prefix}-01-first.md").write_text("# First")

        phases = list(iterate_plan_phases(tmp_path, prefix, skip_overview=True))

        assert len(phases) == 1
        assert phases[0].name == "first"


class TestPromptBuilder:
    """Tests for prompt_builder module."""

    def test_build_phase_prompt_includes_plan_content(self, tmp_path: Path):
        """Test that build_phase_prompt includes the plan file content."""
        plan_file = tmp_path / "test-plan.md"
        plan_file.write_text("# Test Plan\n\nThis is the plan content.")

        prompt = build_phase_prompt(str(plan_file))

        assert "# Test Plan" in prompt
        assert "This is the plan content." in prompt

    def test_build_phase_prompt_includes_phase_id(self, tmp_path: Path):
        """Test that build_phase_prompt includes phase identifier."""
        plan_file = tmp_path / "test-plan.md"
        plan_file.write_text("# Content")

        prompt = build_phase_prompt(str(plan_file), current_phase="test-phase-1")

        assert "test-phase-1" in prompt

    def test_build_phase_prompt_with_phase_info(self, tmp_path: Path):
        """Test that build_phase_prompt includes PlanPhase metadata."""
        plan_file = tmp_path / "test-plan.md"
        plan_file.write_text("# Content")
        phase_info = PlanPhase(path=plan_file, order=1, name="setup", is_overview=False)

        prompt = build_phase_prompt(
            str(plan_file),
            phase_info=phase_info,
            total_phases=3,
            current_phase_num=1,
        )

        assert "setup" in prompt
        assert "Phase 1/3" in prompt or "Phase 1 of 3" in prompt

    def test_build_phase_prompt_raises_on_missing_file(self):
        """Test that build_phase_prompt raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            build_phase_prompt("/nonexistent/file.md")

    def test_build_overview_prompt_includes_phase_count(self, tmp_path: Path):
        """Test that build_overview_prompt includes phase count."""
        overview_file = tmp_path / "overview.md"
        overview_file.write_text("# Plan Overview")

        prompt = build_overview_prompt(str(overview_file), phase_count=5)

        assert "5" in prompt
        assert "phase" in prompt.lower()

    def test_build_overview_prompt_raises_on_missing_file(self):
        """Test that build_overview_prompt raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            build_overview_prompt("/nonexistent/file.md", phase_count=1)
