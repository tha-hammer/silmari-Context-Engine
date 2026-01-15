# Phase 02: Permission Callbacks

## Timeout Constraint

**CRITICAL**: SDK permission callbacks (`can_use_tool`) have a **60-second timeout**.
The callback must return quickly - do not:
- Prompt for user input
- Make external API calls
- Perform expensive computations

If the callback times out, the tool use is denied by default.

```python
async def _auto_approve_reads(self, tool_name, input_data, context):
    # CRITICAL: This callback has 60-second timeout
    # Must return quickly - no user prompts or long operations

    # Simple pattern matching is fine
    if tool_name in self.READ_ONLY_TOOLS:
        return PermissionResultAllow(updated_input=input_data)

    # Path checks are fast - OK
    path = input_data.get("file_path", "")
    if "thoughts/" in path:
        return PermissionResultAllow(updated_input=input_data)

    return PermissionResultAllow(updated_input=input_data)
```

## Behaviors

3. **Auto-approve read operations** - Allow Read/Glob/Grep during research
4. **Auto-approve thoughts writes** - Allow Write to thoughts/ directory
9. **Implementation permissions** - Block system directory writes

---

## Behavior 3: Auto-approve Read Operations

### Test Specification

**Given**: Read, Glob, or Grep tool requested during research
**When**: can_use_tool callback fires
**Then**: Returns PermissionResultAllow with unchanged input

**Edge Cases**:
- Task tool (should also approve for sub-agent research)
- WebFetch tool (should approve for web research)

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari_rlm_act/tests/test_research_phase_sdk.py`

```python
class TestAutoApproveReadOperations:
    """Behavior 3: Auto-approve Read Operations."""

    @pytest.mark.asyncio
    async def test_approves_read_tool(self, tmp_path: Path) -> None:
        """Given Read tool, returns PermissionResultAllow."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK
        from claude_agent_sdk.types import PermissionResultAllow

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        input_data = {"file_path": str(tmp_path / "src/main.py")}

        result = await phase._auto_approve_reads("Read", input_data, {})

        assert isinstance(result, PermissionResultAllow)
        assert result.updated_input == input_data

    @pytest.mark.asyncio
    async def test_approves_glob_tool(self, tmp_path: Path) -> None:
        """Given Glob tool, returns PermissionResultAllow."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK
        from claude_agent_sdk.types import PermissionResultAllow

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        input_data = {"pattern": "**/*.py"}

        result = await phase._auto_approve_reads("Glob", input_data, {})

        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_approves_grep_tool(self, tmp_path: Path) -> None:
        """Given Grep tool, returns PermissionResultAllow."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK
        from claude_agent_sdk.types import PermissionResultAllow

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        input_data = {"pattern": "def main"}

        result = await phase._auto_approve_reads("Grep", input_data, {})

        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_approves_task_tool(self, tmp_path: Path) -> None:
        """Given Task tool (sub-agent), returns PermissionResultAllow."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK
        from claude_agent_sdk.types import PermissionResultAllow

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        input_data = {"prompt": "Research the codebase"}

        result = await phase._auto_approve_reads("Task", input_data, {})

        assert isinstance(result, PermissionResultAllow)
```

#### 🟢 Green: Minimal Implementation

**File**: `silmari_rlm_act/phases/research_sdk.py`

```python
from claude_agent_sdk.types import PermissionResultAllow, PermissionResultDeny

# At class level
READ_ONLY_TOOLS = frozenset(["Read", "Glob", "Grep", "Task", "WebFetch"])

async def _auto_approve_reads(
    self,
    tool_name: str,
    input_data: dict[str, Any],
    context: dict[str, Any],
) -> PermissionResultAllow | PermissionResultDeny:
    """Auto-approve read-only operations during research.

    Args:
        tool_name: Name of the tool being called
        input_data: Tool input parameters
        context: Additional context

    Returns:
        PermissionResultAllow for read-only tools
    """
    if tool_name in self.READ_ONLY_TOOLS:
        return PermissionResultAllow(updated_input=input_data)

    # Default: allow (will be refined in Behavior 4)
    return PermissionResultAllow(updated_input=input_data)
```

#### 🔵 Refactor: Improve Code

No refactoring needed - implementation is minimal.

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): `pytest silmari_rlm_act/tests/test_research_phase_sdk.py::TestAutoApproveReadOperations -v`
- [ ] Test passes (Green): Same command
- [ ] All tests pass after refactor

---

## Behavior 4: Auto-approve Thoughts Writes

### Test Specification

**Given**: Write tool requested with path in thoughts/ directory
**When**: can_use_tool callback fires
**Then**: Returns PermissionResultAllow

**Edge Cases**:
- Write to thoughts/searchable/ (should approve)
- Write to thoughts/maceo/ (should approve - user-specific)
- Write to src/ (should require different handling)

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari_rlm_act/tests/test_research_phase_sdk.py`

```python
class TestAutoApproveThoughtsWrites:
    """Behavior 4: Auto-approve Thoughts Writes."""

    @pytest.mark.asyncio
    async def test_approves_thoughts_write(self, tmp_path: Path) -> None:
        """Given Write to thoughts/, returns PermissionResultAllow."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK
        from claude_agent_sdk.types import PermissionResultAllow

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        input_data = {
            "file_path": str(tmp_path / "thoughts/searchable/shared/research/doc.md")
        }

        result = await phase._auto_approve_reads("Write", input_data, {})

        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_approves_research_path_write(self, tmp_path: Path) -> None:
        """Given Write with 'research' in path, returns PermissionResultAllow."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK
        from claude_agent_sdk.types import PermissionResultAllow

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        input_data = {
            "file_path": str(tmp_path / "output/research-findings.md")
        }

        result = await phase._auto_approve_reads("Write", input_data, {})

        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_allows_other_writes_by_default(self, tmp_path: Path) -> None:
        """Given Write to other path, still allows (research is permissive)."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK
        from claude_agent_sdk.types import PermissionResultAllow

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        input_data = {"file_path": str(tmp_path / "notes.md")}

        result = await phase._auto_approve_reads("Write", input_data, {})

        # Research phase is permissive - allows all writes
        assert isinstance(result, PermissionResultAllow)
```

#### 🟢 Green: Minimal Implementation

**File**: `silmari_rlm_act/phases/research_sdk.py`

```python
async def _auto_approve_reads(
    self,
    tool_name: str,
    input_data: dict[str, Any],
    context: dict[str, Any],
) -> PermissionResultAllow | PermissionResultDeny:
    """Auto-approve read-only operations during research.

    Research phase is permissive - allows reads and writes to thoughts/.
    """
    # Always approve read-only tools
    if tool_name in self.READ_ONLY_TOOLS:
        return PermissionResultAllow(updated_input=input_data)

    # Allow writes to thoughts/ or research paths
    if tool_name == "Write":
        path = input_data.get("file_path", "")
        if "thoughts/" in path or "research" in path.lower():
            return PermissionResultAllow(updated_input=input_data)

    # Default: allow (research phase is permissive)
    return PermissionResultAllow(updated_input=input_data)
```

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red)
- [ ] Test passes (Green)
- [ ] All tests pass after refactor

---

## Behavior 9: Implementation Permissions (Block System Writes)

### Test Specification

**Given**: Write or Edit tool requested with path in /etc or /sys
**When**: can_use_tool callback fires in ImplementationPhaseSDK
**Then**: Returns PermissionResultDeny with message

**Edge Cases**:
- Write to /etc/passwd (must block)
- Write to /sys/kernel (must block)
- Write to project path (should allow)
- Edit to system file (must block)

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari_rlm_act/tests/test_implementation_phase_sdk.py`

```python
"""Tests for SDK-based Implementation Phase.

This module tests ImplementationPhaseSDK which:
- Uses ClaudeSDKClient with session resumption
- Blocks system directory writes
- Maintains loop-based execution pattern
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import pytest

from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseResult, PhaseType, PhaseStatus, AutonomyMode


class TestImplementationPermissions:
    """Behavior 9: Implementation Permissions - Block System Writes."""

    @pytest.mark.asyncio
    async def test_blocks_etc_writes(self, tmp_path: Path) -> None:
        """Given Write to /etc, returns PermissionResultDeny."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK
        from claude_agent_sdk.types import PermissionResultDeny

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        input_data = {"file_path": "/etc/passwd"}

        result = await phase._implementation_permissions("Write", input_data, {})

        assert isinstance(result, PermissionResultDeny)
        assert "system" in result.message.lower() or "blocked" in result.message.lower()

    @pytest.mark.asyncio
    async def test_blocks_sys_writes(self, tmp_path: Path) -> None:
        """Given Write to /sys, returns PermissionResultDeny."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK
        from claude_agent_sdk.types import PermissionResultDeny

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        input_data = {"file_path": "/sys/kernel/debug"}

        result = await phase._implementation_permissions("Write", input_data, {})

        assert isinstance(result, PermissionResultDeny)

    @pytest.mark.asyncio
    async def test_blocks_etc_edits(self, tmp_path: Path) -> None:
        """Given Edit to /etc, returns PermissionResultDeny."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK
        from claude_agent_sdk.types import PermissionResultDeny

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        input_data = {"file_path": "/etc/hosts"}

        result = await phase._implementation_permissions("Edit", input_data, {})

        assert isinstance(result, PermissionResultDeny)

    @pytest.mark.asyncio
    async def test_allows_project_writes(self, tmp_path: Path) -> None:
        """Given Write to project path, returns PermissionResultAllow."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK
        from claude_agent_sdk.types import PermissionResultAllow

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        input_data = {"file_path": str(tmp_path / "src/main.py")}

        result = await phase._implementation_permissions("Write", input_data, {})

        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_allows_read_tools(self, tmp_path: Path) -> None:
        """Given Read tool, returns PermissionResultAllow."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK
        from claude_agent_sdk.types import PermissionResultAllow

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        input_data = {"file_path": "/etc/passwd"}  # Even system files can be read

        result = await phase._implementation_permissions("Read", input_data, {})

        assert isinstance(result, PermissionResultAllow)
```

#### 🟢 Green: Minimal Implementation

**File**: `silmari_rlm_act/phases/implementation_sdk.py`

```python
"""SDK-based Implementation Phase.

This module implements the implementation phase using Claude Agent SDK with:
- Session resumption from research phase
- Permission controls blocking system writes
- Loop-based execution pattern
"""

from pathlib import Path
from typing import Any, Optional

from claude_agent_sdk.types import PermissionResultAllow, PermissionResultDeny

from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import PhaseResult, PhaseStatus, PhaseType


class ImplementationPhaseSDK:
    """SDK-based implementation phase with permission controls."""

    BLOCKED_PATHS = ("/etc", "/sys", "/proc", "/dev")
    WRITE_TOOLS = frozenset(["Write", "Edit"])

    def __init__(
        self,
        project_path: Path,
        cwa: CWAIntegration,
    ) -> None:
        """Initialize SDK-based implementation phase."""
        self.project_path = Path(project_path)
        self.cwa = cwa

    async def _implementation_permissions(
        self,
        tool_name: str,
        input_data: dict[str, Any],
        context: dict[str, Any],
    ) -> PermissionResultAllow | PermissionResultDeny:
        """Permission callback for implementation phase.

        Blocks writes to system directories, allows everything else.
        """
        if tool_name in self.WRITE_TOOLS:
            path = input_data.get("file_path", "")
            for blocked in self.BLOCKED_PATHS:
                if path.startswith(blocked):
                    return PermissionResultDeny(
                        message=f"System directory write blocked: {blocked}"
                    )

        return PermissionResultAllow(updated_input=input_data)
```

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): `pytest silmari_rlm_act/tests/test_implementation_phase_sdk.py::TestImplementationPermissions -v`
- [ ] Test passes (Green)
- [ ] All tests pass after refactor

**Manual:**
- [ ] System paths /etc, /sys, /proc, /dev blocked
- [ ] Project directory writes allowed
- [ ] Reads allowed even for system files
