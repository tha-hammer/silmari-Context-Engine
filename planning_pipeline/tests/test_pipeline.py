"""Tests for the full pipeline - Behavior 14."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from planning_pipeline.pipeline import PlanningPipeline
from planning_pipeline.beads_controller import BeadsController


@pytest.fixture
def project_path():
    """Return the root project path."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def beads_controller(project_path):
    """Create BeadsController with project path."""
    return BeadsController(project_path)


@pytest.fixture
def cleanup_issues(beads_controller):
    """Track and cleanup created issues after test."""
    created_ids = []
    yield created_ids
    for issue_id in created_ids:
        beads_controller.close_issue(issue_id, reason="Test cleanup")
    beads_controller.sync()


class TestPipelineInit:
    """Test PlanningPipeline initialization."""

    def test_creates_pipeline_with_project_path(self, project_path):
        """Given project path, creates pipeline instance."""
        pipeline = PlanningPipeline(project_path)
        assert pipeline.project_path == project_path.resolve()

    def test_has_beads_controller(self, project_path):
        """Given project path, pipeline has beads controller."""
        pipeline = PlanningPipeline(project_path)
        assert pipeline.beads is not None


class TestPipelineStructure:
    """Tests for pipeline module structure."""

    def test_imports_step_requirement_decomposition(self):
        """Pipeline should import step_requirement_decomposition."""
        from planning_pipeline.pipeline import step_requirement_decomposition
        assert callable(step_requirement_decomposition)

    def test_docstring_mentions_seven_steps(self):
        """Pipeline docstring should mention 7 steps."""
        from planning_pipeline.pipeline import PlanningPipeline
        docstring = PlanningPipeline.__doc__
        assert "7 steps" in docstring or "seven steps" in docstring.lower()


class TestPipelineRequirementDecomposition:
    """Tests for requirement decomposition integration in pipeline."""

    def test_calls_requirement_decomposition_after_memory_sync(self, tmp_path):
        """Pipeline should call step_requirement_decomposition after memory sync."""
        from planning_pipeline.pipeline import PlanningPipeline

        call_order = []

        def track_research(*args, **kwargs):
            call_order.append("research")
            return {"success": True, "research_path": "test/research.md", "output": ""}

        def track_memory_sync(*args, **kwargs):
            call_order.append("memory_sync")
            return {"success": True}

        def track_requirement_decomposition(*args, **kwargs):
            call_order.append("requirement_decomposition")
            return {
                "success": True,
                "hierarchy_path": str(tmp_path / "hierarchy.json"),
                "diagram_path": str(tmp_path / "diagram.mmd"),
                "tests_path": None,
                "requirement_count": 3,
                "output_dir": str(tmp_path),
            }

        def track_planning(*args, **kwargs):
            call_order.append("planning")
            return {"success": True, "plan_path": str(tmp_path / "plan.md"), "output": ""}

        def track_phase_decomposition(*args, **kwargs):
            call_order.append("phase_decomposition")
            return {"success": True, "phase_files": [str(tmp_path / "phase-1.md")], "output": ""}

        def track_beads(*args, **kwargs):
            call_order.append("beads")
            return {"success": True, "epic_id": "beads-001", "phase_issues": []}

        with patch.multiple(
            "planning_pipeline.pipeline",
            step_research=track_research,
            step_memory_sync=track_memory_sync,
            step_requirement_decomposition=track_requirement_decomposition,
            step_planning=track_planning,
            step_phase_decomposition=track_phase_decomposition,
            step_beads_integration=track_beads,
            interactive_checkpoint_research=lambda x: {"action": "continue", "answers": []},
            interactive_checkpoint_plan=lambda x: {"continue": True, "feedback": ""},
        ):
            pipeline = PlanningPipeline(tmp_path)
            result = pipeline.run("test prompt", auto_approve=True)

        assert result["success"] is True
        assert call_order.index("memory_sync") < call_order.index("requirement_decomposition")
        assert call_order.index("requirement_decomposition") < call_order.index("planning")

    def test_passes_research_path_to_requirement_decomposition(self, tmp_path):
        """Pipeline should pass research_path to step_requirement_decomposition."""
        from planning_pipeline.pipeline import PlanningPipeline

        captured_args = {}

        def capture_requirement_decomposition(project_path, research_path, **kwargs):
            captured_args["project_path"] = project_path
            captured_args["research_path"] = research_path
            return {
                "success": True,
                "hierarchy_path": str(tmp_path / "hierarchy.json"),
                "diagram_path": str(tmp_path / "diagram.mmd"),
                "tests_path": None,
                "requirement_count": 3,
                "output_dir": str(tmp_path),
            }

        with patch.multiple(
            "planning_pipeline.pipeline",
            step_research=lambda *a, **kw: {"success": True, "research_path": "thoughts/research.md", "output": ""},
            step_memory_sync=lambda *a, **kw: {"success": True},
            step_requirement_decomposition=capture_requirement_decomposition,
            step_planning=lambda *a, **kw: {"success": True, "plan_path": str(tmp_path / "plan.md"), "output": ""},
            step_phase_decomposition=lambda *a, **kw: {"success": True, "phase_files": [str(tmp_path / "p.md")], "output": ""},
            step_beads_integration=lambda *a, **kw: {"success": True, "epic_id": "b-1", "phase_issues": []},
            interactive_checkpoint_research=lambda x: {"action": "continue", "answers": []},
            interactive_checkpoint_plan=lambda x: {"continue": True, "feedback": ""},
        ):
            pipeline = PlanningPipeline(tmp_path)
            pipeline.run("test prompt", auto_approve=True)

        assert captured_args["research_path"] == "thoughts/research.md"


class TestStepNumbering:
    """Tests for correct step numbering in output."""

    def test_step_headers_show_seven_total(self, tmp_path, capsys):
        """All step headers should show /7 format."""
        from planning_pipeline.pipeline import PlanningPipeline

        with patch.multiple(
            "planning_pipeline.pipeline",
            step_research=lambda *a, **kw: {"success": True, "research_path": "r.md", "output": ""},
            step_memory_sync=lambda *a, **kw: {"success": True},
            step_requirement_decomposition=lambda *a, **kw: {
                "success": True, "hierarchy_path": str(tmp_path / "h.json"),
                "diagram_path": str(tmp_path / "d.mmd"), "tests_path": None,
                "requirement_count": 1, "output_dir": str(tmp_path)
            },
            step_planning=lambda *a, **kw: {"success": True, "plan_path": str(tmp_path / "p.md"), "output": ""},
            step_phase_decomposition=lambda *a, **kw: {"success": True, "phase_files": [str(tmp_path / "ph.md")], "output": ""},
            step_beads_integration=lambda *a, **kw: {"success": True, "epic_id": "b", "phase_issues": []},
            interactive_checkpoint_research=lambda x: {"action": "continue", "answers": []},
            interactive_checkpoint_plan=lambda x: {"continue": True, "feedback": ""},
        ):
            pipeline = PlanningPipeline(tmp_path)
            pipeline.run("test", auto_approve=True)

        output = capsys.readouterr().out
        assert "STEP 1/7" in output
        assert "STEP 2/7" in output
        assert "STEP 3/7" in output
        assert "STEP 4/7" in output  # Context Generation
        assert "STEP 5/7" in output
        assert "STEP 6/7" in output
        assert "STEP 7/7" in output
        assert "/6" not in output  # No old numbering


class TestDecompositionFailureHandling:
    """Tests for interactive failure handling in requirement decomposition."""

    def test_prompts_on_decomposition_failure(self, tmp_path, monkeypatch, capsys):
        """Should show (R)etry/(C)ontinue prompt when decomposition fails."""
        from planning_pipeline.pipeline import PlanningPipeline

        # Simulate user choosing Continue
        inputs = iter(["c"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        def failing_decomposition(*args, **kwargs):
            return {"success": False, "error": "BAML API rate limit"}

        with patch.multiple(
            "planning_pipeline.pipeline",
            step_research=lambda *a, **kw: {"success": True, "research_path": "r.md", "output": ""},
            step_memory_sync=lambda *a, **kw: {"success": True},
            step_requirement_decomposition=failing_decomposition,
            step_planning=lambda *a, **kw: {"success": True, "plan_path": str(tmp_path / "p.md"), "output": ""},
            step_phase_decomposition=lambda *a, **kw: {"success": True, "phase_files": [str(tmp_path / "ph.md")], "output": ""},
            step_beads_integration=lambda *a, **kw: {"success": True, "epic_id": "b", "phase_issues": []},
            interactive_checkpoint_research=lambda x: {"action": "continue", "answers": []},
            interactive_checkpoint_plan=lambda x: {"continue": True, "feedback": ""},
        ):
            pipeline = PlanningPipeline(tmp_path)
            pipeline.run("test", auto_approve=False)

        output = capsys.readouterr().out
        assert "(R)etry" in output or "(C)ontinue" in output, "Should show retry/continue prompt"

    def test_retry_reruns_decomposition(self, tmp_path, monkeypatch):
        """Choosing (R)etry should re-run step_requirement_decomposition."""
        from planning_pipeline.pipeline import PlanningPipeline

        call_count = {"decomposition": 0}

        # First input: retry, second: continue (to break loop)
        inputs = iter(["r", "c"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        def counting_decomposition(*args, **kwargs):
            call_count["decomposition"] += 1
            if call_count["decomposition"] < 2:
                return {"success": False, "error": "temporary failure"}
            return {
                "success": True,
                "hierarchy_path": str(tmp_path / "h.json"),
                "diagram_path": str(tmp_path / "d.mmd"),
                "tests_path": None,
                "requirement_count": 1,
                "output_dir": str(tmp_path),
            }

        with patch.multiple(
            "planning_pipeline.pipeline",
            step_research=lambda *a, **kw: {"success": True, "research_path": "r.md", "output": ""},
            step_memory_sync=lambda *a, **kw: {"success": True},
            step_requirement_decomposition=counting_decomposition,
            step_planning=lambda *a, **kw: {"success": True, "plan_path": str(tmp_path / "p.md"), "output": ""},
            step_phase_decomposition=lambda *a, **kw: {"success": True, "phase_files": [str(tmp_path / "ph.md")], "output": ""},
            step_beads_integration=lambda *a, **kw: {"success": True, "epic_id": "b", "phase_issues": []},
            interactive_checkpoint_research=lambda x: {"action": "continue", "answers": []},
            interactive_checkpoint_plan=lambda x: {"continue": True, "feedback": ""},
        ):
            pipeline = PlanningPipeline(tmp_path)
            pipeline.run("test", auto_approve=False)

        assert call_count["decomposition"] == 2, "Should retry decomposition once"

    def test_continue_skips_to_planning(self, tmp_path, monkeypatch):
        """Choosing (C)ontinue should skip decomposition and proceed to planning."""
        from planning_pipeline.pipeline import PlanningPipeline

        steps_called = []

        inputs = iter(["c"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        def failing_decomposition(*args, **kwargs):
            steps_called.append("decomposition")
            return {"success": False, "error": "BAML failed"}

        def track_planning(*args, **kwargs):
            steps_called.append("planning")
            return {"success": True, "plan_path": str(tmp_path / "p.md"), "output": ""}

        with patch.multiple(
            "planning_pipeline.pipeline",
            step_research=lambda *a, **kw: {"success": True, "research_path": "r.md", "output": ""},
            step_memory_sync=lambda *a, **kw: {"success": True},
            step_requirement_decomposition=failing_decomposition,
            step_planning=track_planning,
            step_phase_decomposition=lambda *a, **kw: {"success": True, "phase_files": [str(tmp_path / "ph.md")], "output": ""},
            step_beads_integration=lambda *a, **kw: {"success": True, "epic_id": "b", "phase_issues": []},
            interactive_checkpoint_research=lambda x: {"action": "continue", "answers": []},
            interactive_checkpoint_plan=lambda x: {"continue": True, "feedback": ""},
        ):
            pipeline = PlanningPipeline(tmp_path)
            result = pipeline.run("test", auto_approve=False)

        assert "planning" in steps_called, "Should proceed to planning after Continue"
        assert result["success"] is True

    def test_auto_approve_skips_decomposition_on_failure(self, tmp_path):
        """In auto_approve mode, decomposition failure should skip to planning."""
        from planning_pipeline.pipeline import PlanningPipeline

        steps_called = []

        with patch.multiple(
            "planning_pipeline.pipeline",
            step_research=lambda *a, **kw: {"success": True, "research_path": "r.md", "output": ""},
            step_memory_sync=lambda *a, **kw: {"success": True},
            step_requirement_decomposition=lambda *a, **kw: (steps_called.append("decomp"), {"success": False, "error": "fail"})[1],
            step_planning=lambda *a, **kw: (steps_called.append("planning"), {"success": True, "plan_path": str(tmp_path / "p.md"), "output": ""})[1],
            step_phase_decomposition=lambda *a, **kw: {"success": True, "phase_files": [str(tmp_path / "ph.md")], "output": ""},
            step_beads_integration=lambda *a, **kw: {"success": True, "epic_id": "b", "phase_issues": []},
        ):
            pipeline = PlanningPipeline(tmp_path)
            result = pipeline.run("test", auto_approve=True)

        assert "planning" in steps_called
        assert result["success"] is True


# Note: Full E2E tests are commented out as they require actual Claude calls
# and take significant time. Uncomment for integration testing.

# class TestPipelineE2E:
#     """Behavior 14: Full Pipeline E2E."""
#
#     @pytest.mark.slow
#     @pytest.mark.e2e
#     def test_full_pipeline_with_auto_approve(self, project_path, cleanup_issues):
#         """Given research prompt with auto-approve, runs complete pipeline."""
#         pipeline = PlanningPipeline(project_path)
#
#         result = pipeline.run(
#             research_prompt="What is the main purpose of this project? Brief answer.",
#             ticket_id="TEST-001",
#             auto_approve=True
#         )
#
#         assert result["success"] is True
#         assert "plan_dir" in result
#         assert result.get("epic_id") is not None
#
#         # Cleanup
#         if result.get("epic_id"):
#             cleanup_issues.append(result["epic_id"])
#         for pi in result.get("steps", {}).get("beads", {}).get("phase_issues", []):
#             if pi.get("issue_id"):
#                 cleanup_issues.append(pi["issue_id"])
