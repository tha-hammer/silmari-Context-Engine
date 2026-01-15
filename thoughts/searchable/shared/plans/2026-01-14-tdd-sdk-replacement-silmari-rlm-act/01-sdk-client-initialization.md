# Phase 01: SDK Client Initialization

## SDK Import Pattern

Use the stateful `ClaudeSDKClient` class (not the stateless `query()` function):

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, HookMatcher
from claude_agent_sdk.types import (
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    PermissionResultAllow,
    PermissionResultDeny,
)
```

**Rationale**: ClaudeSDKClient enables session management via `resume` option,
which is required for cross-phase context continuity.

**Why not `query()`?** The codebase has two patterns:
- Stateless: `from claude_agent_sdk import query` (used in `claude_runner.py`)
- Stateful: `from claude_agent_sdk import ClaudeSDKClient` (used in `test-conversation.py`)

We use stateful because:
1. Multi-turn conversations within single phase
2. Session ID capture for cross-phase continuity
3. Clean async context manager cleanup

## Behaviors

1. **SDK client initialization** - Configure ClaudeSDKClient with project settings
2. **Artifact tracking via hook** - Track written files via PostToolUse callback

---

## Behavior 1: SDK Client Initialization

### Test Specification

**Given**: Project path and CWA integration instance
**When**: ResearchPhaseSDK is created and execute() called
**Then**: ClaudeSDKClient configured with correct cwd, tools, and hooks

**Edge Cases**:
- Project path doesn't exist
- CWA is None (should raise)

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari_rlm_act/tests/test_research_phase_sdk.py`

```python
"""Tests for SDK-based Research Phase.

This module tests ResearchPhaseSDK which:
- Uses ClaudeSDKClient instead of run_claude_sync
- Tracks artifacts via PostToolUse hooks
- Captures session_id for phase continuity
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import pytest

from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseResult, PhaseType, PhaseStatus


class TestSDKClientInitialization:
    """Behavior 1: SDK Client Initialization."""

    def test_configures_client_with_project_path(self, tmp_path: Path) -> None:
        """Given project path, configures ClaudeSDKClient with cwd."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        # Mock the SDK client
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.query = AsyncMock()
        mock_client.receive_response = AsyncMock(return_value=iter([]))

        with patch("silmari_rlm_act.phases.research_sdk.ClaudeSDKClient", return_value=mock_client) as mock_cls:
            import asyncio
            asyncio.run(phase._execute_sdk("test prompt"))

        # Verify ClaudeAgentOptions passed with correct cwd
        call_kwargs = mock_cls.call_args[1]
        options = call_kwargs.get("options")
        assert options is not None
        assert options.cwd == tmp_path

    def test_configures_allowed_tools(self, tmp_path: Path) -> None:
        """Given execution, configures allowed tools for research."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.query = AsyncMock()
        mock_client.receive_response = AsyncMock(return_value=iter([]))

        with patch("silmari_rlm_act.phases.research_sdk.ClaudeSDKClient", return_value=mock_client) as mock_cls:
            import asyncio
            asyncio.run(phase._execute_sdk("test prompt"))

        call_kwargs = mock_cls.call_args[1]
        options = call_kwargs.get("options")
        assert "Read" in options.allowed_tools
        assert "Write" in options.allowed_tools
        assert "Grep" in options.allowed_tools
        assert "Glob" in options.allowed_tools

    def test_raises_on_none_cwa(self, tmp_path: Path) -> None:
        """Given None CWA, raises ValueError."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        with pytest.raises(ValueError, match="cwa"):
            ResearchPhaseSDK(project_path=tmp_path, cwa=None)
```

#### 🟢 Green: Minimal Implementation

**File**: `silmari_rlm_act/phases/research_sdk.py`

```python
"""SDK-based Research Phase implementation.

This module implements the research phase using Claude Agent SDK instead of
the CLI wrapper, enabling:
- Hook-based artifact tracking
- Session continuity via session_id
- Programmatic permission control
"""

from pathlib import Path
from typing import Any, Optional

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseResult, PhaseStatus, PhaseType


class ResearchPhaseSDK:
    """SDK-based research phase with artifact tracking via hooks."""

    ALLOWED_TOOLS = ["Read", "Write", "Grep", "Glob", "Task", "WebFetch"]
    DEFAULT_TIMEOUT = 1200

    def __init__(
        self,
        project_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Initialize SDK-based research phase.

        Args:
            project_path: Root directory of the project
            cwa: Context Window Array integration instance

        Raises:
            ValueError: If cwa is None
        """
        if cwa is None:
            raise ValueError("cwa must not be None")

        self.project_path = Path(project_path)
        self.cwa = cwa
        self.artifacts: list[str] = []
        self.session_id: Optional[str] = None

    async def _execute_sdk(self, prompt: str) -> dict[str, Any]:
        """Execute research using SDK client.

        Args:
            prompt: The research prompt

        Returns:
            Dict with success, output, session_id
        """
        options = ClaudeAgentOptions(
            cwd=self.project_path,
            allowed_tools=self.ALLOWED_TOOLS,
        )

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)

            output_chunks: list[str] = []
            async for message in client.receive_response():
                pass  # Minimal implementation

            return {
                "success": True,
                "output": "".join(output_chunks),
                "session_id": self.session_id,
            }
```

#### 🔵 Refactor: Improve Code

**File**: `silmari_rlm_act/phases/research_sdk.py`

```python
# Add type hints and docstrings, extract constants
RESEARCH_TOOLS = frozenset(["Read", "Write", "Grep", "Glob", "Task", "WebFetch"])
```

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): `pytest silmari_rlm_act/tests/test_research_phase_sdk.py::TestSDKClientInitialization -v`
- [ ] Test passes (Green): `pytest silmari_rlm_act/tests/test_research_phase_sdk.py::TestSDKClientInitialization -v`
- [ ] All tests pass after refactor: `pytest silmari_rlm_act/tests/test_research_phase_sdk.py -v`

**Manual:**
- [ ] ClaudeSDKClient receives correct options

---

## Behavior 2: Artifact Tracking via Hook

### Test Specification

**Given**: Write tool called with a research file path
**When**: PostToolUse hook fires
**Then**: Path is added to the artifacts list

**Edge Cases**:
- Write to non-research directory (should not track)
- Multiple writes (should track all research files)
- Write fails (should still track attempted path)

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari_rlm_act/tests/test_research_phase_sdk.py`

```python
class TestArtifactTrackingViaHook:
    """Behavior 2: Artifact Tracking via PostToolUse Hook."""

    @pytest.mark.asyncio
    async def test_tracks_research_file_writes(self, tmp_path: Path) -> None:
        """Given Write to research dir, tracks in artifacts."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        # Simulate PostToolUse hook call
        input_data = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(tmp_path / "thoughts/searchable/shared/research/2026-01-14-test.md")
            }
        }

        await phase._track_artifacts(input_data, "tool-use-123", {})

        assert len(phase.artifacts) == 1
        assert "2026-01-14-test.md" in phase.artifacts[0]

    @pytest.mark.asyncio
    async def test_ignores_non_research_writes(self, tmp_path: Path) -> None:
        """Given Write to non-research dir, does not track."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        input_data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(tmp_path / "src/main.py")}
        }

        await phase._track_artifacts(input_data, "tool-use-123", {})

        assert len(phase.artifacts) == 0

    @pytest.mark.asyncio
    async def test_tracks_multiple_research_writes(self, tmp_path: Path) -> None:
        """Given multiple Write calls, tracks all research files."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        paths = [
            "thoughts/searchable/shared/research/2026-01-14-topic1.md",
            "thoughts/searchable/shared/research/2026-01-14-topic2.md",
        ]

        for path in paths:
            input_data = {
                "tool_name": "Write",
                "tool_input": {"file_path": str(tmp_path / path)}
            }
            await phase._track_artifacts(input_data, "tool-use-123", {})

        assert len(phase.artifacts) == 2

    @pytest.mark.asyncio
    async def test_ignores_non_write_tools(self, tmp_path: Path) -> None:
        """Given non-Write tool, does not track."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        input_data = {
            "tool_name": "Read",
            "tool_input": {"file_path": str(tmp_path / "thoughts/research/doc.md")}
        }

        await phase._track_artifacts(input_data, "tool-use-123", {})

        assert len(phase.artifacts) == 0
```

#### 🟢 Green: Minimal Implementation

**File**: `silmari_rlm_act/phases/research_sdk.py`

```python
async def _track_artifacts(
    self,
    input_data: dict[str, Any],
    tool_use_id: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """PostToolUse hook to track written research files.

    Args:
        input_data: Tool input data including tool_name and tool_input
        tool_use_id: Unique ID of the tool use
        context: Additional context

    Returns:
        Empty dict (hook response)
    """
    if input_data.get("tool_name") != "Write":
        return {}

    file_path = input_data.get("tool_input", {}).get("file_path", "")

    # Track if it's a research file
    if "research" in file_path.lower() and "thoughts" in file_path.lower():
        self.artifacts.append(file_path)

    return {}
```

#### 🔵 Refactor: Improve Code

```python
# Extract pattern matching to constant
RESEARCH_PATH_PATTERN = re.compile(r"thoughts.*research.*\.md$", re.IGNORECASE)

def _is_research_path(self, file_path: str) -> bool:
    """Check if path is a research document."""
    return bool(self.RESEARCH_PATH_PATTERN.search(file_path))
```

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): `pytest silmari_rlm_act/tests/test_research_phase_sdk.py::TestArtifactTrackingViaHook -v`
- [ ] Test passes (Green): `pytest silmari_rlm_act/tests/test_research_phase_sdk.py::TestArtifactTrackingViaHook -v`
- [ ] All tests pass after refactor: `pytest silmari_rlm_act/tests/test_research_phase_sdk.py -v`

**Manual:**
- [ ] Artifacts populated without regex parsing of output text
- [ ] Only research files tracked (not src/ or other directories)
