"""Tests for SDK-based Implementation Phase.

This module tests the ImplementationPhaseSDK class which uses claude_agent_sdk
for TDD implementation loops.

TDD Implementation following plan: 2026-01-14-tdd-sdk-replacement-silmari-rlm-act
"""

from pathlib import Path
from typing import Any, AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import AutonomyMode, PhaseResult, PhaseStatus, PhaseType


# =============================================================================
# Phase 01: SDK Client Initialization
# =============================================================================


class TestSDKClientInitialization:
    """Phase 01: SDK Client Initialization Tests for Implementation."""

    def test_creates_options_with_bypass_permissions(self, tmp_path: Path) -> None:
        """Given implementation phase, creates options with bypassPermissions mode."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        options = phase._create_agent_options()

        # Implementation uses bypass for autonomous execution
        assert options.permission_mode == "bypassPermissions"

    def test_creates_options_with_all_tools(self, tmp_path: Path) -> None:
        """Given implementation phase, creates options with full tool access."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        options = phase._create_agent_options()

        # Implementation needs all tools
        assert "Read" in options.allowed_tools
        assert "Write" in options.allowed_tools
        assert "Bash" in options.allowed_tools
        assert "Edit" in options.allowed_tools

    def test_creates_options_with_cwd(self, tmp_path: Path) -> None:
        """Given project path, sets cwd in options."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        options = phase._create_agent_options()

        assert str(options.cwd) == str(tmp_path)


# =============================================================================
# Phase 02: Session Management
# =============================================================================


class TestSessionManagement:
    """Phase 02: Session Management Tests for Implementation."""

    @pytest.mark.asyncio
    async def test_connects_session_on_execute(self, tmp_path: Path) -> None:
        """Given execute called, connects SDK session."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        # Create a plan file
        plans_dir = tmp_path / "thoughts" / "searchable" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        plan_file = plans_dir / "00-overview.md"
        plan_file.write_text("# TDD Plan\n\n## Phase 1\n- Task 1")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.implementation_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.query = AsyncMock()

            async def mock_response() -> AsyncIterator[Any]:
                from claude_agent_sdk import AssistantMessage, TextBlock

                yield AssistantMessage(
                    content=[TextBlock(text="Implementation complete.")],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            await phase.execute_async(
                phase_paths=[str(plan_file)],
                mode=AutonomyMode.FULLY_AUTONOMOUS,
            )

            mock_client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnects_after_execute(self, tmp_path: Path) -> None:
        """Given execute completes, disconnects SDK session."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plans_dir = tmp_path / "thoughts" / "searchable" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        plan_file = plans_dir / "00-overview.md"
        plan_file.write_text("# TDD Plan\n\n## Phase 1\n- Task 1")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.implementation_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.query = AsyncMock()

            async def mock_response() -> AsyncIterator[Any]:
                from claude_agent_sdk import AssistantMessage, TextBlock

                yield AssistantMessage(
                    content=[TextBlock(text="Implementation complete.")],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            await phase.execute_async(
                phase_paths=[str(plan_file)],
                mode=AutonomyMode.FULLY_AUTONOMOUS,
            )

            mock_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_connection_error(self, tmp_path: Path) -> None:
        """Given connection error, returns failed PhaseResult."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plans_dir = tmp_path / "thoughts" / "searchable" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        plan_file = plans_dir / "00-overview.md"
        plan_file.write_text("# TDD Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.implementation_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.connect.side_effect = Exception("Connection failed")

            result = await phase.execute_async(
                phase_paths=[str(plan_file)],
                mode=AutonomyMode.FULLY_AUTONOMOUS,
            )

            assert result.status == PhaseStatus.FAILED
            assert "Connection failed" in result.errors[0]


# =============================================================================
# Phase 03: Prompt Building
# =============================================================================


class TestPromptBuilding:
    """Phase 03: Prompt Building Tests."""

    def test_builds_prompt_with_plan_path(self, tmp_path: Path) -> None:
        """Given plan path, includes it in prompt."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plans_dir = tmp_path / "thoughts" / "searchable" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        plan_file = plans_dir / "00-overview.md"
        plan_file.write_text("# TDD Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        prompt = phase._build_implementation_prompt(
            plan_path=plan_file,
            epic_id=None,
            issue_ids=[],
        )

        assert str(plan_file) in prompt

    def test_builds_prompt_with_epic_id(self, tmp_path: Path) -> None:
        """Given epic ID, includes it in prompt."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plans_dir = tmp_path / "thoughts" / "searchable" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        plan_file = plans_dir / "00-overview.md"
        plan_file.write_text("# TDD Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        prompt = phase._build_implementation_prompt(
            plan_path=plan_file,
            epic_id="beads-12345",
            issue_ids=[],
        )

        assert "beads-12345" in prompt

    def test_builds_prompt_with_issue_ids(self, tmp_path: Path) -> None:
        """Given issue IDs, includes them in prompt."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plans_dir = tmp_path / "thoughts" / "searchable" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        plan_file = plans_dir / "00-overview.md"
        plan_file.write_text("# TDD Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        prompt = phase._build_implementation_prompt(
            plan_path=plan_file,
            epic_id=None,
            issue_ids=["beads-001", "beads-002"],
        )

        assert "beads-001" in prompt
        assert "beads-002" in prompt


# =============================================================================
# Phase 04: Streaming and Output
# =============================================================================


class TestStreamingOutput:
    """Phase 04: Streaming and Output Tests."""

    @pytest.mark.asyncio
    async def test_collects_text_from_response(self, tmp_path: Path) -> None:
        """Given response with text blocks, collects text."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plans_dir = tmp_path / "thoughts" / "searchable" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        plan_file = plans_dir / "00-overview.md"
        plan_file.write_text("# TDD Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.implementation_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.query = AsyncMock()

            async def mock_response() -> AsyncIterator[Any]:
                from claude_agent_sdk import AssistantMessage, TextBlock

                yield AssistantMessage(
                    content=[
                        TextBlock(text="Starting implementation."),
                        TextBlock(text=" Tests passing."),
                    ],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            result = await phase.execute_async(
                phase_paths=[str(plan_file)],
                mode=AutonomyMode.FULLY_AUTONOMOUS,
            )

            assert result.status == PhaseStatus.COMPLETE
            assert "output" in result.metadata

    @pytest.mark.asyncio
    async def test_processes_tool_use_blocks(self, tmp_path: Path) -> None:
        """Given response with tool use, processes them."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plans_dir = tmp_path / "thoughts" / "searchable" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        plan_file = plans_dir / "00-overview.md"
        plan_file.write_text("# TDD Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.implementation_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.query = AsyncMock()

            async def mock_response() -> AsyncIterator[Any]:
                from claude_agent_sdk import (
                    AssistantMessage,
                    TextBlock,
                    ToolUseBlock,
                )

                yield AssistantMessage(
                    content=[
                        ToolUseBlock(
                            id="tool_1",
                            name="Bash",
                            input={"command": "pytest"},
                        ),
                        TextBlock(text="Tests passed!"),
                    ],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            result = await phase.execute_async(
                phase_paths=[str(plan_file)],
                mode=AutonomyMode.FULLY_AUTONOMOUS,
            )

            # Should track tool uses in metadata
            assert "tool_uses" in result.metadata


# =============================================================================
# Phase 05: Phase Result Construction
# =============================================================================


class TestPhaseResultConstruction:
    """Phase 05: Phase Result Construction Tests."""

    @pytest.mark.asyncio
    async def test_returns_implementation_phase_type(self, tmp_path: Path) -> None:
        """Given implementation execution, returns IMPLEMENTATION phase type."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plans_dir = tmp_path / "thoughts" / "searchable" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        plan_file = plans_dir / "00-overview.md"
        plan_file.write_text("# TDD Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.implementation_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.query = AsyncMock()

            async def mock_response() -> AsyncIterator[Any]:
                from claude_agent_sdk import AssistantMessage, TextBlock

                yield AssistantMessage(
                    content=[TextBlock(text="Done")],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            result = await phase.execute_async(
                phase_paths=[str(plan_file)],
                mode=AutonomyMode.FULLY_AUTONOMOUS,
            )

            assert isinstance(result, PhaseResult)
            assert result.phase_type == PhaseType.IMPLEMENTATION

    @pytest.mark.asyncio
    async def test_includes_timing_info(self, tmp_path: Path) -> None:
        """Given execution, includes timing information."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plans_dir = tmp_path / "thoughts" / "searchable" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        plan_file = plans_dir / "00-overview.md"
        plan_file.write_text("# TDD Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.implementation_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.query = AsyncMock()

            async def mock_response() -> AsyncIterator[Any]:
                from claude_agent_sdk import AssistantMessage, TextBlock

                yield AssistantMessage(
                    content=[TextBlock(text="Done")],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            result = await phase.execute_async(
                phase_paths=[str(plan_file)],
                mode=AutonomyMode.FULLY_AUTONOMOUS,
            )

            assert result.started_at is not None
            assert result.completed_at is not None
            assert result.duration_seconds is not None
            assert result.duration_seconds >= 0

    @pytest.mark.asyncio
    async def test_includes_plan_paths_in_artifacts(self, tmp_path: Path) -> None:
        """Given successful execution, includes plan paths in artifacts."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plans_dir = tmp_path / "thoughts" / "searchable" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        plan_file = plans_dir / "00-overview.md"
        plan_file.write_text("# TDD Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.implementation_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.query = AsyncMock()

            async def mock_response() -> AsyncIterator[Any]:
                from claude_agent_sdk import AssistantMessage, TextBlock

                yield AssistantMessage(
                    content=[TextBlock(text="Done")],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            result = await phase.execute_async(
                phase_paths=[str(plan_file)],
                mode=AutonomyMode.FULLY_AUTONOMOUS,
            )

            assert result.status == PhaseStatus.COMPLETE
            assert str(plan_file) in result.artifacts

    @pytest.mark.asyncio
    async def test_handles_empty_phase_paths(self, tmp_path: Path) -> None:
        """Given no phase paths, returns complete with message."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        result = await phase.execute_async(
            phase_paths=[],
            mode=AutonomyMode.FULLY_AUTONOMOUS,
        )

        assert result.status == PhaseStatus.COMPLETE
        assert "message" in result.metadata

    @pytest.mark.asyncio
    async def test_handles_missing_plan_file(self, tmp_path: Path) -> None:
        """Given missing plan file, returns failed result."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        result = await phase.execute_async(
            phase_paths=[str(tmp_path / "nonexistent.md")],
            mode=AutonomyMode.FULLY_AUTONOMOUS,
        )

        assert result.status == PhaseStatus.FAILED
        assert any("not found" in e.lower() for e in result.errors)


# =============================================================================
# Synchronous Wrapper Tests
# =============================================================================


class TestSyncWrapper:
    """Tests for synchronous execute() wrapper."""

    def test_execute_calls_async_version(self, tmp_path: Path) -> None:
        """Given sync execute called, calls async version."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plans_dir = tmp_path / "thoughts" / "searchable" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        plan_file = plans_dir / "00-overview.md"
        plan_file.write_text("# TDD Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.implementation_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.query = AsyncMock()

            async def mock_response() -> AsyncIterator[Any]:
                from claude_agent_sdk import AssistantMessage, TextBlock

                yield AssistantMessage(
                    content=[TextBlock(text="Done")],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            # Call sync version
            result = phase.execute(
                phase_paths=[str(plan_file)],
                mode=AutonomyMode.FULLY_AUTONOMOUS,
            )

            assert isinstance(result, PhaseResult)
            assert result.phase_type == PhaseType.IMPLEMENTATION


# =============================================================================
# Beads Integration Tests
# =============================================================================


class TestBeadsIntegration:
    """Tests for Beads issue tracking integration."""

    @pytest.mark.asyncio
    async def test_tracks_beads_issues_in_metadata(self, tmp_path: Path) -> None:
        """Given beads issue IDs, tracks them in metadata."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plans_dir = tmp_path / "thoughts" / "searchable" / "shared" / "plans"
        plans_dir.mkdir(parents=True)
        plan_file = plans_dir / "00-overview.md"
        plan_file.write_text("# TDD Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.implementation_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.query = AsyncMock()

            async def mock_response() -> AsyncIterator[Any]:
                from claude_agent_sdk import AssistantMessage, TextBlock

                yield AssistantMessage(
                    content=[TextBlock(text="Done")],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            result = await phase.execute_async(
                phase_paths=[str(plan_file)],
                mode=AutonomyMode.FULLY_AUTONOMOUS,
                beads_issue_ids=["beads-001", "beads-002"],
                beads_epic_id="beads-epic-001",
            )

            assert result.metadata.get("beads_issues") == ["beads-001", "beads-002"]
