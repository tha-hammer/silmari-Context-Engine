"""Tests for SDK-based Research Phase.

This module tests the ResearchPhaseSDK class which uses claude_agent_sdk
instead of subprocess-based Claude invocation.

TDD Implementation following plan: 2026-01-14-tdd-sdk-replacement-silmari-rlm-act
"""

from pathlib import Path
from typing import Any, AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseResult, PhaseStatus, PhaseType


# =============================================================================
# Phase 01: SDK Client Initialization
# =============================================================================


class TestSDKClientInitialization:
    """Phase 01: SDK Client Initialization Tests."""

    # -------------------------------------------------------------------------
    # Behavior 1.1: Create ClaudeAgentOptions with permission_mode
    # -------------------------------------------------------------------------

    def test_creates_options_with_default_permission_mode(self, tmp_path: Path) -> None:
        """Given no mode specified, creates options with 'acceptEdits' mode."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        options = phase._create_agent_options()

        assert options.permission_mode == "acceptEdits"

    def test_creates_options_with_custom_permission_mode(self, tmp_path: Path) -> None:
        """Given custom mode, creates options with that mode."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(
            project_path=tmp_path,
            cwa=cwa,
            permission_mode="bypassPermissions",
        )

        options = phase._create_agent_options()

        assert options.permission_mode == "bypassPermissions"

    def test_creates_options_with_allowed_tools(self, tmp_path: Path) -> None:
        """Given phase, creates options with required tools."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        options = phase._create_agent_options()

        # Research phase needs file tools
        assert "Read" in options.allowed_tools
        assert "Glob" in options.allowed_tools
        assert "Grep" in options.allowed_tools
        assert "Write" in options.allowed_tools

    def test_creates_options_with_cwd(self, tmp_path: Path) -> None:
        """Given project path, sets cwd in options."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        options = phase._create_agent_options()

        assert str(options.cwd) == str(tmp_path)

    # -------------------------------------------------------------------------
    # Behavior 1.2: Initialize ClaudeSDKClient with options
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_initializes_client_with_options(self, tmp_path: Path) -> None:
        """Given options, initializes ClaudeSDKClient."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        # Mock the SDK client
        with patch(
            "silmari_rlm_act.phases.research_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            client = phase._create_client()

            mock_client_class.assert_called_once()
            call_args = mock_client_class.call_args
            options = call_args[0][0]
            assert options.permission_mode == "acceptEdits"

    # -------------------------------------------------------------------------
    # Behavior 1.3: Configure streaming callbacks
    # -------------------------------------------------------------------------

    def test_options_include_stderr_callback(self, tmp_path: Path) -> None:
        """Given phase, configures stderr callback for progress."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        options = phase._create_agent_options()

        assert options.stderr is not None
        assert callable(options.stderr)


# =============================================================================
# Phase 02: Permission Callbacks
# =============================================================================


class TestPermissionCallbacks:
    """Phase 02: Permission Callback Tests."""

    # -------------------------------------------------------------------------
    # Behavior 2.1: Handle tool permission requests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_auto_approves_read_tools(self, tmp_path: Path) -> None:
        """Given Read tool request, auto-approves."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        # Create mock context
        from claude_agent_sdk import ToolPermissionContext

        context = ToolPermissionContext()

        result = await phase._can_use_tool("Read", {"file_path": "/test"}, context)

        assert result.behavior == "allow"

    @pytest.mark.asyncio
    async def test_auto_approves_write_tools(self, tmp_path: Path) -> None:
        """Given Write tool request, auto-approves."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        from claude_agent_sdk import ToolPermissionContext

        context = ToolPermissionContext()

        result = await phase._can_use_tool(
            "Write", {"file_path": "/test", "content": "x"}, context
        )

        assert result.behavior == "allow"

    @pytest.mark.asyncio
    async def test_denies_dangerous_tools(self, tmp_path: Path) -> None:
        """Given dangerous tool request, denies."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        from claude_agent_sdk import ToolPermissionContext

        context = ToolPermissionContext()

        # Bash with dangerous command
        result = await phase._can_use_tool(
            "Bash", {"command": "rm -rf /"}, context
        )

        assert result.behavior == "deny"


# =============================================================================
# Phase 03: Session Management
# =============================================================================


class TestSessionManagement:
    """Phase 03: Session Management Tests."""

    # -------------------------------------------------------------------------
    # Behavior 3.1: Connect to SDK session
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_connects_session_on_execute(self, tmp_path: Path) -> None:
        """Given execute called, connects SDK session."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-15-test.md"
        research_file.write_text("# Test Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.research_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock query and receive_response
            mock_client.query = AsyncMock()

            # Create async iterator for receive_response
            async def mock_response() -> AsyncIterator[Any]:
                from claude_agent_sdk import AssistantMessage, TextBlock

                yield AssistantMessage(
                    content=[TextBlock(text=f"Research saved to {research_file}")],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            await phase.execute_async("Test research question")

            mock_client.connect.assert_called_once()

    # -------------------------------------------------------------------------
    # Behavior 3.2: Disconnect after completion
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_disconnects_after_execute(self, tmp_path: Path) -> None:
        """Given execute completes, disconnects SDK session."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-15-test.md"
        research_file.write_text("# Test Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.research_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.query = AsyncMock()

            async def mock_response() -> AsyncIterator[Any]:
                from claude_agent_sdk import AssistantMessage, TextBlock

                yield AssistantMessage(
                    content=[TextBlock(text=f"Research saved to {research_file}")],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            await phase.execute_async("Test research question")

            mock_client.disconnect.assert_called_once()

    # -------------------------------------------------------------------------
    # Behavior 3.3: Handle session errors gracefully
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_handles_connection_error(self, tmp_path: Path) -> None:
        """Given connection error, returns failed PhaseResult."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.research_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.connect.side_effect = Exception("Connection failed")

            result = await phase.execute_async("Test question")

            assert result.status == PhaseStatus.FAILED
            assert "Connection failed" in result.errors[0]


# =============================================================================
# Phase 04: Streaming and Output
# =============================================================================


class TestStreamingOutput:
    """Phase 04: Streaming and Output Tests."""

    # -------------------------------------------------------------------------
    # Behavior 4.1: Stream assistant messages
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_collects_text_from_response(self, tmp_path: Path) -> None:
        """Given response with text blocks, collects text."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-15-test.md"
        research_file.write_text("# Test Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.research_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.query = AsyncMock()

            async def mock_response() -> AsyncIterator[Any]:
                from claude_agent_sdk import AssistantMessage, TextBlock

                yield AssistantMessage(
                    content=[
                        TextBlock(text="I found the research."),
                        TextBlock(text=f" Saved to {research_file}"),
                    ],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            result = await phase.execute_async("Test question")

            assert result.status == PhaseStatus.COMPLETE
            assert "output" in result.metadata

    # -------------------------------------------------------------------------
    # Behavior 4.2: Handle tool use blocks
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_processes_tool_use_blocks(self, tmp_path: Path) -> None:
        """Given response with tool use, processes them."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-15-test.md"
        research_file.write_text("# Test Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.research_sdk.ClaudeSDKClient"
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
                            name="Write",
                            input={"file_path": str(research_file), "content": "# Test"},
                        ),
                        TextBlock(text=f"Created research at {research_file}"),
                    ],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            result = await phase.execute_async("Test question")

            # Should track tool uses in metadata
            assert "tool_uses" in result.metadata


# =============================================================================
# Phase 05: Phase Result Construction
# =============================================================================


class TestPhaseResultConstruction:
    """Phase 05: Phase Result Construction Tests."""

    # -------------------------------------------------------------------------
    # Behavior 5.1: Extract research path from output
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_extracts_research_path(self, tmp_path: Path) -> None:
        """Given output with path, extracts it to artifacts."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-15-test.md"
        research_file.write_text("# Test Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.research_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.query = AsyncMock()

            async def mock_response() -> AsyncIterator[Any]:
                from claude_agent_sdk import AssistantMessage, TextBlock

                yield AssistantMessage(
                    content=[TextBlock(text=f"Research saved to {research_file}")],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            result = await phase.execute_async("Test question")

            assert result.status == PhaseStatus.COMPLETE
            assert len(result.artifacts) > 0
            assert any("2026-01-15-test.md" in a for a in result.artifacts)

    # -------------------------------------------------------------------------
    # Behavior 5.2: Store research in CWA
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_stores_research_in_cwa(self, tmp_path: Path) -> None:
        """Given successful research, stores in CWA."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK
        from context_window_array import EntryType

        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-15-test.md"
        research_file.write_text("# Test Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.research_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.query = AsyncMock()

            async def mock_response() -> AsyncIterator[Any]:
                from claude_agent_sdk import AssistantMessage, TextBlock

                yield AssistantMessage(
                    content=[TextBlock(text=f"Research saved to {research_file}")],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            result = await phase.execute_async("Test question")

            assert result.status == PhaseStatus.COMPLETE
            assert "cwa_entry_id" in result.metadata

            # Verify entry exists
            entry = cwa.get_entry(result.metadata["cwa_entry_id"])
            assert entry is not None
            assert entry.entry_type == EntryType.FILE

    # -------------------------------------------------------------------------
    # Behavior 5.3: Return PhaseResult with correct type
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_returns_research_phase_type(self, tmp_path: Path) -> None:
        """Given research execution, returns RESEARCH phase type."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-15-test.md"
        research_file.write_text("# Test Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.research_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.query = AsyncMock()

            async def mock_response() -> AsyncIterator[Any]:
                from claude_agent_sdk import AssistantMessage, TextBlock

                yield AssistantMessage(
                    content=[TextBlock(text=f"Saved to {research_file}")],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            result = await phase.execute_async("Test question")

            assert isinstance(result, PhaseResult)
            assert result.phase_type == PhaseType.RESEARCH

    # -------------------------------------------------------------------------
    # Behavior 5.4: Include timing information
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_includes_timing_info(self, tmp_path: Path) -> None:
        """Given execution, includes timing information."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-15-test.md"
        research_file.write_text("# Test Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.research_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.query = AsyncMock()

            async def mock_response() -> AsyncIterator[Any]:
                from claude_agent_sdk import AssistantMessage, TextBlock

                yield AssistantMessage(
                    content=[TextBlock(text=f"Saved to {research_file}")],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            result = await phase.execute_async("Test question")

            assert result.started_at is not None
            assert result.completed_at is not None
            assert result.duration_seconds is not None
            assert result.duration_seconds >= 0


# =============================================================================
# Synchronous Wrapper Tests
# =============================================================================


class TestSyncWrapper:
    """Tests for synchronous execute() wrapper."""

    def test_execute_calls_async_version(self, tmp_path: Path) -> None:
        """Given sync execute called, calls async version."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-15-test.md"
        research_file.write_text("# Test Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch(
            "silmari_rlm_act.phases.research_sdk.ClaudeSDKClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.query = AsyncMock()

            async def mock_response() -> AsyncIterator[Any]:
                from claude_agent_sdk import AssistantMessage, TextBlock

                yield AssistantMessage(
                    content=[TextBlock(text=f"Saved to {research_file}")],
                    model="claude-sonnet-4-20250514",
                )

            mock_client.receive_response = mock_response

            # Call sync version
            result = phase.execute("Test question")

            assert isinstance(result, PhaseResult)
            assert result.phase_type == PhaseType.RESEARCH
