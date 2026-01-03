"""Tests for _execute_phase implementation."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from planning_pipeline.autonomous_loop import LoopRunner, LoopState


class TestPromptGeneration:
    """Tests for phase prompt building."""

    @pytest.fixture
    def temp_plan_file(self, tmp_path):
        """Create a temporary plan file."""
        plan_path = tmp_path / "test-plan.md"
        plan_path.write_text("""# Test Feature Plan

## Phase 1: Setup
- Create initial structure

## Phase 2: Implementation
- Implement the feature

## Success Criteria
- [ ] Tests pass
""")
        return str(plan_path)

    @pytest.mark.asyncio
    async def test_build_prompt_includes_plan_content(self, temp_plan_file):
        """Prompt should include the plan file content."""
        runner = LoopRunner(plan_path=temp_plan_file)
        runner.current_phase = "feature-1"

        prompt = runner._build_phase_prompt()

        assert "Test Feature Plan" in prompt
        assert "Phase 1: Setup" in prompt
        assert "Success Criteria" in prompt

    @pytest.mark.asyncio
    async def test_build_prompt_includes_phase_identifier(self, temp_plan_file):
        """Prompt should include the current phase identifier."""
        runner = LoopRunner(plan_path=temp_plan_file)
        runner.current_phase = "feature-xyz"

        prompt = runner._build_phase_prompt()

        assert "feature-xyz" in prompt

    def test_build_prompt_handles_missing_file(self, tmp_path):
        """Should raise FileNotFoundError for missing plan."""
        runner = LoopRunner(plan_path=str(tmp_path / "nonexistent.md"))
        runner.current_phase = "phase-1"

        with pytest.raises(FileNotFoundError):
            runner._build_phase_prompt()

    def test_build_prompt_handles_empty_plan(self, tmp_path):
        """Should handle empty plan file gracefully."""
        empty_plan = tmp_path / "empty.md"
        empty_plan.write_text("")
        runner = LoopRunner(plan_path=str(empty_plan))
        runner.current_phase = "phase-1"

        # Should not raise, but prompt should still include phase
        prompt = runner._build_phase_prompt()
        assert "phase-1" in prompt


class TestClaudeInvocation:
    """Tests for Claude subprocess invocation."""

    @pytest.fixture
    def mock_subprocess_success(self):
        """Mock successful subprocess run."""
        with patch('planning_pipeline.phase_execution.claude_invoker.subprocess') as mock:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "Success output"
            mock_process.stderr = ""
            mock.run.return_value = mock_process
            yield mock

    @pytest.mark.asyncio
    async def test_invoke_claude_returns_result_dict(self, mock_subprocess_success):
        """Should return structured result from Claude invocation."""
        from planning_pipeline.phase_execution.claude_invoker import invoke_claude

        result = invoke_claude("Test prompt", timeout=60)

        assert "success" in result
        assert "output" in result
        assert "error" in result
        assert "elapsed" in result

    @pytest.mark.asyncio
    async def test_invoke_claude_success_on_zero_return(self, mock_subprocess_success):
        """Should report success when return code is 0."""
        from planning_pipeline.phase_execution.claude_invoker import invoke_claude

        result = invoke_claude("Test prompt", timeout=60)

        assert result["success"] is True

    def test_invoke_claude_failure_on_nonzero_return(self):
        """Should report failure when return code is non-zero."""
        with patch('planning_pipeline.phase_execution.claude_invoker.subprocess') as mock:
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stdout = ""
            mock_process.stderr = "Error occurred"
            mock.run.return_value = mock_process

            from planning_pipeline.phase_execution.claude_invoker import invoke_claude
            result = invoke_claude("Test prompt", timeout=60)

            assert result["success"] is False

    def test_invoke_claude_handles_command_not_found(self):
        """Should handle missing claude command gracefully."""
        with patch('planning_pipeline.phase_execution.claude_invoker.subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("claude not found")

            from planning_pipeline.phase_execution.claude_invoker import invoke_claude
            result = invoke_claude("Test prompt", timeout=60)

            assert result["success"] is False
            assert "not found" in result["error"].lower()

    def test_invoke_claude_handles_timeout(self):
        """Should handle subprocess timeout gracefully."""
        import subprocess as sp
        with patch('planning_pipeline.phase_execution.claude_invoker.subprocess.run') as mock_run:
            mock_run.side_effect = sp.TimeoutExpired("claude", 60)

            from planning_pipeline.phase_execution.claude_invoker import invoke_claude
            result = invoke_claude("Test prompt", timeout=60)

            assert result["success"] is False
            assert "timed out" in result["error"].lower()


class TestResultChecking:
    """Tests for execution result validation."""

    @pytest.fixture
    def temp_git_repo(self, tmp_path):
        """Create a temporary git repo."""
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
        # Create initial commit
        (tmp_path / "initial.txt").write_text("initial")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True)
        return tmp_path

    def test_check_result_success_with_changes(self, temp_git_repo):
        """Should return True when Claude succeeded and git has changes."""
        # Create a change
        (temp_git_repo / "new_file.py").write_text("# new content")

        from planning_pipeline.phase_execution.result_checker import check_execution_result

        result = check_execution_result(
            claude_result={"success": True, "output": "done", "error": "", "elapsed": 5.0},
            project_path=temp_git_repo
        )

        assert result is True

    def test_check_result_failure_on_claude_error(self, temp_git_repo):
        """Should return False when Claude returned error."""
        from planning_pipeline.phase_execution.result_checker import check_execution_result

        result = check_execution_result(
            claude_result={"success": False, "output": "", "error": "failed", "elapsed": 5.0},
            project_path=temp_git_repo
        )

        assert result is False

    def test_check_result_runs_bd_sync(self, temp_git_repo):
        """Should run bd sync after successful execution."""
        (temp_git_repo / "new_file.py").write_text("# new content")

        with patch('planning_pipeline.phase_execution.result_checker.subprocess') as mock_sub:
            # Mock git status to return changes
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="M file.py")

            from planning_pipeline.phase_execution.result_checker import check_execution_result

            check_execution_result(
                claude_result={"success": True, "output": "done", "error": "", "elapsed": 5.0},
                project_path=temp_git_repo
            )

            # Check bd sync was called
            bd_calls = [c for c in mock_sub.run.call_args_list
                       if "bd" in str(c) and "sync" in str(c)]
            assert len(bd_calls) >= 1

    def test_check_result_handles_no_beads(self, temp_git_repo):
        """Should handle projects without beads gracefully."""
        (temp_git_repo / "new_file.py").write_text("# new content")

        with patch('planning_pipeline.phase_execution.result_checker.subprocess') as mock_sub:
            # Simulate bd command not found
            def side_effect(*args, **kwargs):
                cmd = args[0] if args else kwargs.get('args', [])
                if "bd" in cmd:
                    raise FileNotFoundError("bd not found")
                return MagicMock(returncode=0, stdout="M file.py")
            mock_sub.run.side_effect = side_effect

            from planning_pipeline.phase_execution.result_checker import check_execution_result

            # Should still succeed without beads
            result = check_execution_result(
                claude_result={"success": True, "output": "done", "error": "", "elapsed": 5.0},
                project_path=temp_git_repo
            )

            assert result is True

    def test_check_result_success_without_changes(self, temp_git_repo):
        """Should return True even without git changes if Claude succeeded."""
        from planning_pipeline.phase_execution.result_checker import check_execution_result

        # No new files, no changes
        result = check_execution_result(
            claude_result={"success": True, "output": "done", "error": "", "elapsed": 5.0},
            project_path=temp_git_repo
        )

        # Still True because Claude succeeded (might be no-op phase)
        assert result is True


class TestExecutePhaseIntegration:
    """Integration tests for _execute_phase method."""

    @pytest.fixture
    def runner_with_plan(self, tmp_path):
        """Create a runner with a valid plan file."""
        plan_path = tmp_path / "plan.md"
        plan_path.write_text("""# Test Plan

## Implementation
- Do the thing
""")

        # Initialize git repo
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
        (tmp_path / "initial.txt").write_text("initial")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True)

        runner = LoopRunner(plan_path=str(plan_path))
        runner.current_phase = "test-phase"
        runner._project_path = tmp_path
        return runner

    @pytest.mark.asyncio
    async def test_execute_phase_invokes_claude(self, runner_with_plan):
        """Should invoke Claude with built prompt."""
        with patch('planning_pipeline.autonomous_loop.invoke_claude') as mock_invoke:
            mock_invoke.return_value = {
                "success": True,
                "output": "done",
                "error": "",
                "elapsed": 5.0
            }
            # Mock result checker to avoid subprocess calls
            with patch('planning_pipeline.autonomous_loop.check_execution_result') as mock_check:
                mock_check.return_value = True

                result = await runner_with_plan._execute_phase()

                mock_invoke.assert_called_once()
                call_args = mock_invoke.call_args
                prompt = call_args[0][0]
                assert "Test Plan" in prompt
                assert "test-phase" in prompt

    @pytest.mark.asyncio
    async def test_execute_phase_returns_true_on_success(self, runner_with_plan):
        """Should return True when execution succeeds."""
        with patch('planning_pipeline.autonomous_loop.invoke_claude') as mock_invoke:
            mock_invoke.return_value = {
                "success": True,
                "output": "done",
                "error": "",
                "elapsed": 5.0
            }
            with patch('planning_pipeline.autonomous_loop.check_execution_result') as mock_check:
                mock_check.return_value = True

                result = await runner_with_plan._execute_phase()

                assert result is True

    @pytest.mark.asyncio
    async def test_execute_phase_returns_false_on_claude_failure(self, runner_with_plan):
        """Should return False when Claude fails."""
        with patch('planning_pipeline.autonomous_loop.invoke_claude') as mock_invoke:
            mock_invoke.return_value = {
                "success": False,
                "output": "",
                "error": "Claude crashed",
                "elapsed": 5.0
            }
            with patch('planning_pipeline.autonomous_loop.check_execution_result') as mock_check:
                mock_check.return_value = False

                result = await runner_with_plan._execute_phase()

                assert result is False

    @pytest.mark.asyncio
    async def test_execute_phase_handles_missing_plan(self, tmp_path):
        """Should return False when plan file is missing."""
        runner = LoopRunner(plan_path=str(tmp_path / "missing.md"))
        runner.current_phase = "phase-1"
        runner._project_path = tmp_path

        result = await runner._execute_phase()

        assert result is False

    @pytest.mark.asyncio
    async def test_execute_phase_passes_project_path_to_checker(self, runner_with_plan):
        """Should pass project path to result checker."""
        with patch('planning_pipeline.autonomous_loop.invoke_claude') as mock_invoke:
            mock_invoke.return_value = {
                "success": True,
                "output": "done",
                "error": "",
                "elapsed": 5.0
            }
            with patch('planning_pipeline.autonomous_loop.check_execution_result') as mock_check:
                mock_check.return_value = True

                await runner_with_plan._execute_phase()

                mock_check.assert_called_once()
                call_args = mock_check.call_args
                assert call_args[1]['project_path'] == runner_with_plan._project_path
