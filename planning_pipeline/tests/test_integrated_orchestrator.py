"""Tests for IntegratedOrchestrator - TDD implementation."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Will import when created
# from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator
# from planning_pipeline.beads_controller import BeadsController


class TestGetProjectInfo:
    """Tests for LLM-powered project info detection."""

    def test_extracts_techstack_from_overview_file(self, tmp_path):
        """Given overview.md exists, returns techstack from LLM analysis."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

        plans_dir = tmp_path / "thoughts" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        overview = plans_dir / "2026-01-01-feature-00-overview.md"
        overview.write_text("""# Feature Implementation

## Tech Stack
- Python 3.11
- FastAPI
- PostgreSQL
""")

        mock_result = {
            "success": True,
            "output": '{"name": "Feature", "stack": "Python FastAPI PostgreSQL", "description": "A feature implementation"}'
        }

        with patch('planning_pipeline.integrated_orchestrator.run_claude_sync', return_value=mock_result):
            orchestrator = IntegratedOrchestrator(tmp_path)
            info = orchestrator.get_project_info()

            assert info["name"] == "Feature"
            assert "Python" in info["stack"]
            assert "FastAPI" in info["stack"]
            assert info["path"] == tmp_path
            assert info["model"] == "sonnet"

    def test_fallback_to_readme_when_no_overview(self, tmp_path):
        """Given no overview.md, falls back to README.md."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

        readme = tmp_path / "README.md"
        readme.write_text("""# My Project

A Python project using Flask.
""")

        mock_result = {
            "success": True,
            "output": '{"name": "My Project", "stack": "Python Flask", "description": "A Python project"}'
        }

        with patch('planning_pipeline.integrated_orchestrator.run_claude_sync', return_value=mock_result):
            orchestrator = IntegratedOrchestrator(tmp_path)
            info = orchestrator.get_project_info()

            assert info["name"] == "My Project"
            assert "Flask" in info["stack"]

    def test_returns_defaults_when_no_files_found(self, tmp_path):
        """Given no files found, returns defaults with project directory name."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

        orchestrator = IntegratedOrchestrator(tmp_path)
        info = orchestrator.get_project_info()

        assert info["name"] == tmp_path.name
        assert info["stack"] == "Unknown"
        assert info["description"] == ""
        assert info["path"] == tmp_path
        assert info["model"] == "sonnet"

    def test_handles_invalid_json_from_llm(self, tmp_path):
        """Given LLM returns invalid JSON, returns defaults."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

        readme = tmp_path / "README.md"
        readme.write_text("# Test Project")

        mock_result = {
            "success": True,
            "output": "This is not valid JSON at all!"
        }

        with patch('planning_pipeline.integrated_orchestrator.run_claude_sync', return_value=mock_result):
            orchestrator = IntegratedOrchestrator(tmp_path)
            info = orchestrator.get_project_info()

            # Should return defaults
            assert info["name"] == tmp_path.name
            assert info["stack"] == "Unknown"


class TestGetFeatureStatus:
    """Tests for beads-based feature status."""

    def test_returns_status_from_beads_list(self, tmp_path):
        """Given beads issues exist, returns correct counts."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator
        from planning_pipeline.beads_controller import BeadsController

        mock_all = {
            "success": True,
            "data": [
                {"id": "issue-1", "status": "open", "dependencies": []},
                {"id": "issue-2", "status": "closed", "dependencies": []},
                {"id": "issue-3", "status": "open", "dependencies": [{"depends_on_id": "issue-1"}]},
            ]
        }
        mock_open = {
            "success": True,
            "data": [
                {"id": "issue-1", "status": "open", "dependencies": []},
                {"id": "issue-3", "status": "open", "dependencies": [{"depends_on_id": "issue-1"}]},
            ]
        }
        mock_closed = {
            "success": True,
            "data": [{"id": "issue-2", "status": "closed", "dependencies": []}]
        }

        with patch.object(BeadsController, 'list_issues') as mock_list:
            mock_list.side_effect = [mock_all, mock_open, mock_closed]

            orchestrator = IntegratedOrchestrator(tmp_path)
            status = orchestrator.get_feature_status()

            assert status["total"] == 3
            assert status["completed"] == 1
            assert status["remaining"] == 2
            assert status["blocked"] == 1  # issue-3 blocked by issue-1
            assert len(status["features"]) == 3

    def test_returns_zeros_when_no_beads(self, tmp_path):
        """Given bd not initialized, returns zero counts."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator
        from planning_pipeline.beads_controller import BeadsController

        with patch.object(BeadsController, 'list_issues') as mock_list:
            mock_list.return_value = {"success": False, "error": "Not initialized"}

            orchestrator = IntegratedOrchestrator(tmp_path)
            status = orchestrator.get_feature_status()

            assert status["total"] == 0
            assert status["completed"] == 0
            assert status["remaining"] == 0
            assert status["blocked"] == 0

    def test_correctly_identifies_blocked_by_open_dependencies(self, tmp_path):
        """Given issue depends on open issue, it's counted as blocked."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator
        from planning_pipeline.beads_controller import BeadsController

        mock_all = {
            "success": True,
            "data": [
                {"id": "phase-1", "status": "open", "dependencies": []},
                {"id": "phase-2", "status": "open", "dependencies": [{"depends_on_id": "phase-1"}]},
                {"id": "phase-3", "status": "open", "dependencies": [{"depends_on_id": "phase-2"}]},
            ]
        }

        with patch.object(BeadsController, 'list_issues') as mock_list:
            mock_list.side_effect = [mock_all, mock_all, {"success": True, "data": []}]

            orchestrator = IntegratedOrchestrator(tmp_path)
            status = orchestrator.get_feature_status()

            # phase-2 blocked by phase-1, phase-3 blocked by phase-2
            assert status["blocked"] == 2


class TestGetNextFeature:
    """Tests for getting next ready feature."""

    def test_returns_first_ready_issue(self, tmp_path):
        """Given ready issues exist, returns first one."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator
        from planning_pipeline.beads_controller import BeadsController

        mock_ready = {
            "success": True,
            "data": [
                {"id": "phase-1", "title": "Phase 1: Setup", "priority": 1},
                {"id": "phase-2", "title": "Phase 2: Core", "priority": 2},
            ]
        }

        with patch.object(BeadsController, '_run_bd', return_value=mock_ready):
            orchestrator = IntegratedOrchestrator(tmp_path)
            feature = orchestrator.get_next_feature()

            assert feature is not None
            assert feature["id"] == "phase-1"
            assert feature["priority"] == 1

    def test_returns_none_when_no_ready_issues(self, tmp_path):
        """Given no ready issues, returns None."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator
        from planning_pipeline.beads_controller import BeadsController

        mock_ready = {"success": True, "data": []}

        with patch.object(BeadsController, '_run_bd', return_value=mock_ready):
            orchestrator = IntegratedOrchestrator(tmp_path)
            feature = orchestrator.get_next_feature()

            assert feature is None

    def test_handles_single_dict_response(self, tmp_path):
        """Given bd ready returns dict (not list), handles it."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator
        from planning_pipeline.beads_controller import BeadsController

        mock_ready = {
            "success": True,
            "data": {"id": "only-issue", "title": "Single Issue"}
        }

        with patch.object(BeadsController, '_run_bd', return_value=mock_ready):
            orchestrator = IntegratedOrchestrator(tmp_path)
            feature = orchestrator.get_next_feature()

            assert feature is not None
            assert feature["id"] == "only-issue"

    def test_returns_none_on_bd_failure(self, tmp_path):
        """Given bd ready fails, returns None."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator
        from planning_pipeline.beads_controller import BeadsController

        mock_ready = {"success": False, "error": "Command failed"}

        with patch.object(BeadsController, '_run_bd', return_value=mock_ready):
            orchestrator = IntegratedOrchestrator(tmp_path)
            feature = orchestrator.get_next_feature()

            assert feature is None


class TestSyncFeaturesWithGit:
    """Tests for beads sync."""

    def test_returns_zero_on_success(self, tmp_path):
        """Given bd sync succeeds, returns 0."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator
        from planning_pipeline.beads_controller import BeadsController

        mock_sync = {"success": True, "output": "Synced"}

        with patch.object(BeadsController, 'sync', return_value=mock_sync):
            orchestrator = IntegratedOrchestrator(tmp_path)
            result = orchestrator.sync_features_with_git()

            assert result == 0

    def test_returns_negative_one_on_failure(self, tmp_path):
        """Given bd sync fails, returns -1."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator
        from planning_pipeline.beads_controller import BeadsController

        mock_sync = {"success": False, "error": "Sync failed"}

        with patch.object(BeadsController, 'sync', return_value=mock_sync):
            orchestrator = IntegratedOrchestrator(tmp_path)
            result = orchestrator.sync_features_with_git()

            assert result == -1


class TestPhaseIssueCreation:
    """Tests for phase issue creation with priority by order."""

    def test_creates_issues_with_priority_matching_phase_order(self, tmp_path):
        """Given phase files, creates issues with priority = phase number."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator
        from planning_pipeline.beads_controller import BeadsController

        phase_files = [
            "thoughts/searchable/plans/2026-01-01-feature-01-setup.md",
            "thoughts/searchable/plans/2026-01-01-feature-02-core.md",
            "thoughts/searchable/plans/2026-01-01-feature-03-ui.md",
        ]

        created_issues = []

        def mock_create(title, issue_type, priority):
            created_issues.append({"title": title, "priority": priority})
            return {"success": True, "data": {"id": f"issue-{len(created_issues)}"}}

        with patch.object(BeadsController, 'create_issue', side_effect=mock_create):
            with patch.object(BeadsController, 'create_epic', return_value={"success": True, "data": {"id": "epic-1"}}):
                with patch.object(BeadsController, 'add_dependency', return_value={"success": True}):
                    with patch.object(BeadsController, 'sync', return_value={"success": True}):
                        orchestrator = IntegratedOrchestrator(tmp_path)
                        result = orchestrator.create_phase_issues(phase_files, "Epic Title")

        assert len(created_issues) == 3
        assert created_issues[0]["priority"] == 1
        assert created_issues[1]["priority"] == 2
        assert created_issues[2]["priority"] == 3

    def test_skips_overview_file(self, tmp_path):
        """Given overview file in list, skips it."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator
        from planning_pipeline.beads_controller import BeadsController

        phase_files = [
            "thoughts/searchable/plans/2026-01-01-feature-00-overview.md",
            "thoughts/searchable/plans/2026-01-01-feature-01-setup.md",
        ]

        created_issues = []

        def mock_create(title, issue_type, priority):
            created_issues.append({"title": title, "priority": priority})
            return {"success": True, "data": {"id": f"issue-{len(created_issues)}"}}

        with patch.object(BeadsController, 'create_issue', side_effect=mock_create):
            with patch.object(BeadsController, 'create_epic', return_value={"success": True, "data": {"id": "epic-1"}}):
                with patch.object(BeadsController, 'add_dependency', return_value={"success": True}):
                    with patch.object(BeadsController, 'sync', return_value={"success": True}):
                        orchestrator = IntegratedOrchestrator(tmp_path)
                        result = orchestrator.create_phase_issues(phase_files, "Epic Title")

        # Only 1 issue created (overview skipped)
        assert len(created_issues) == 1
        assert created_issues[0]["priority"] == 1


class TestSessionLogging:
    """Tests for session logging to .agent/sessions/."""

    def test_logs_session_to_agent_sessions_directory(self, tmp_path):
        """Given operation completes, logs to .agent/sessions/."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

        orchestrator = IntegratedOrchestrator(tmp_path)

        orchestrator.log_session(
            session_id="test-session-001",
            action="get_next_feature",
            result={"feature_id": "phase-1"}
        )

        sessions_dir = tmp_path / ".agent" / "sessions"
        assert sessions_dir.exists()

        # Find session file
        session_files = list(sessions_dir.glob("*.json"))
        assert len(session_files) >= 1

    def test_creates_sessions_directory_if_missing(self, tmp_path):
        """Given .agent/sessions/ doesn't exist, creates it."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

        orchestrator = IntegratedOrchestrator(tmp_path)

        sessions_dir = tmp_path / ".agent" / "sessions"
        assert not sessions_dir.exists()

        orchestrator.log_session(
            session_id="new-session",
            action="init",
            result={}
        )

        assert sessions_dir.exists()

    def test_session_log_contains_required_fields(self, tmp_path):
        """Given log is written, contains timestamp, action, result."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

        orchestrator = IntegratedOrchestrator(tmp_path)

        orchestrator.log_session(
            session_id="detail-session",
            action="sync",
            result={"synced": True}
        )

        sessions_dir = tmp_path / ".agent" / "sessions"
        session_file = list(sessions_dir.glob("*.json"))[0]

        content = json.loads(session_file.read_text())

        # Content is a list of log entries
        assert isinstance(content, list)
        assert len(content) == 1

        entry = content[0]
        assert "timestamp" in entry
        assert "action" in entry
        assert entry["action"] == "sync"
        assert "result" in entry


class TestIntegratedOrchestratorFlow:
    """Integration tests for full orchestration workflow."""

    def test_full_workflow_with_mocked_beads(self, tmp_path):
        """Test complete workflow: get_project_info -> get_status -> get_next -> sync."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator
        from planning_pipeline.beads_controller import BeadsController

        # Setup mock overview file
        plans_dir = tmp_path / "thoughts" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        overview = plans_dir / "2026-01-01-00-overview.md"
        overview.write_text("# Test Plan\n\n## Tech Stack\nPython, pytest")

        # Mock all external calls
        with patch('planning_pipeline.integrated_orchestrator.run_claude_sync') as mock_claude:
            mock_claude.return_value = {
                "success": True,
                "output": '{"name": "Test", "stack": "Python", "description": "Test project"}'
            }

            with patch.object(BeadsController, '_run_bd') as mock_bd:
                # Mock responses for different commands
                def bd_side_effect(*args, **kwargs):
                    cmd = args[0] if args else ""
                    if cmd == "list":
                        return {"success": True, "data": [
                            {"id": "p1", "status": "open", "dependencies": []},
                            {"id": "p2", "status": "open", "dependencies": [{"depends_on_id": "p1"}]}
                        ]}
                    elif cmd == "ready":
                        return {"success": True, "data": [{"id": "p1", "priority": 1}]}
                    elif cmd == "sync":
                        return {"success": True, "output": "Synced"}
                    return {"success": True, "data": {}}

                mock_bd.side_effect = bd_side_effect

                orchestrator = IntegratedOrchestrator(tmp_path)

                # Execute workflow
                info = orchestrator.get_project_info()
                assert info["name"] == "Test"

                status = orchestrator.get_feature_status()
                assert status["total"] == 2

                feature = orchestrator.get_next_feature()
                assert feature["id"] == "p1"

                sync_result = orchestrator.sync_features_with_git()
                assert sync_result == 0

    def test_workflow_with_session_logging(self, tmp_path):
        """Test workflow logs each step to session file."""
        from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator
        from planning_pipeline.beads_controller import BeadsController

        with patch('planning_pipeline.integrated_orchestrator.run_claude_sync') as mock_claude:
            mock_claude.return_value = {
                "success": True,
                "output": '{"name": "Test", "stack": "Python", "description": "Test"}'
            }

            with patch.object(BeadsController, '_run_bd') as mock_bd:
                mock_bd.return_value = {"success": True, "data": []}

                orchestrator = IntegratedOrchestrator(tmp_path)
                session_id = "integration-test-001"

                # Execute workflow with logging
                info = orchestrator.get_project_info()
                orchestrator.log_session(session_id, "get_project_info", info)

                status = orchestrator.get_feature_status()
                orchestrator.log_session(session_id, "get_feature_status", status)

                feature = orchestrator.get_next_feature()
                orchestrator.log_session(session_id, "get_next_feature", {"feature": feature})

                sync_result = orchestrator.sync_features_with_git()
                orchestrator.log_session(session_id, "sync_features_with_git", {"result": sync_result})

        # Verify session log
        session_file = tmp_path / ".agent" / "sessions" / f"{session_id}.json"
        assert session_file.exists()

        logs = json.loads(session_file.read_text())
        assert len(logs) == 4
        assert logs[0]["action"] == "get_project_info"
        assert logs[1]["action"] == "get_feature_status"
        assert logs[2]["action"] == "get_next_feature"
        assert logs[3]["action"] == "sync_features_with_git"
