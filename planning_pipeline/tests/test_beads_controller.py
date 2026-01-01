"""Tests for BeadsController extensions - Phase 7."""

import pytest
from pathlib import Path
from unittest.mock import patch

from planning_pipeline.beads_controller import BeadsController


class TestBeadsControllerExtensions:
    """Tests for new BeadsController methods."""

    def test_get_ready_issue_calls_bd_ready(self, tmp_path):
        """Given bd ready works, returns ready issue."""
        mock_result = {
            "success": True,
            "data": [{"id": "ready-1", "title": "Ready Issue"}]
        }

        with patch.object(BeadsController, '_run_bd', return_value=mock_result) as mock_bd:
            bd = BeadsController(tmp_path)
            result = bd.get_ready_issue(limit=1)

            mock_bd.assert_called_with('ready', '--limit=1')
            assert result["success"]
            assert result["data"][0]["id"] == "ready-1"

    def test_update_status_calls_bd_update(self, tmp_path):
        """Given issue id and status, calls bd update."""
        mock_result = {"success": True, "data": {"id": "issue-1", "status": "in_progress"}}

        with patch.object(BeadsController, '_run_bd', return_value=mock_result) as mock_bd:
            bd = BeadsController(tmp_path)
            result = bd.update_status("issue-1", "in_progress")

            mock_bd.assert_called_with('update', 'issue-1', '--status=in_progress')
            assert result["success"]

    def test_show_issue_calls_bd_show(self, tmp_path):
        """Given issue id, calls bd show."""
        mock_result = {"success": True, "data": {"id": "issue-1", "title": "Test", "description": "..."}}

        with patch.object(BeadsController, '_run_bd', return_value=mock_result) as mock_bd:
            bd = BeadsController(tmp_path)
            result = bd.show_issue("issue-1")

            mock_bd.assert_called_with('show', 'issue-1')
            assert result["success"]

    def test_get_ready_issue_handles_failure(self, tmp_path):
        """Given bd ready fails, returns error result."""
        mock_result = {"success": False, "error": "Command failed"}

        with patch.object(BeadsController, '_run_bd', return_value=mock_result):
            bd = BeadsController(tmp_path)
            result = bd.get_ready_issue()

            assert result["success"] is False
            assert "error" in result
