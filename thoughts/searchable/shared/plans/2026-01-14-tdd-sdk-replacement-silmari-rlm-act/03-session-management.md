# Phase 03: Session Management

## Behaviors

5. **Session ID capture** - Capture session_id from ResultMessage
8. **Session resumption** - Resume session in implementation phase

---

## Behavior 5: Session ID Capture

### Test Specification

**Given**: Research execution completes successfully
**When**: ResultMessage received from SDK
**Then**: session_id is stored in phase and included in PhaseResult metadata

**Edge Cases**:
- ResultMessage has no session_id (should handle gracefully)
- Multiple ResultMessages (should capture from first/last)
- Error ResultMessage (should still capture if available)

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari_rlm_act/tests/test_research_phase_sdk.py`

```python
class TestSessionIDCapture:
    """Behavior 5: Session ID Capture."""

    @pytest.mark.asyncio
    async def test_captures_session_id_from_result(self, tmp_path: Path) -> None:
        """Given ResultMessage with session_id, captures it."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK
        from unittest.mock import MagicMock

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        # Create mock ResultMessage with session_id
        mock_result = MagicMock()
        mock_result.session_id = "session-abc-123"
        mock_result.is_error = False
        mock_result.result = "Research complete"

        # Simulate processing the result message
        phase._process_result_message(mock_result)

        assert phase.session_id == "session-abc-123"

    @pytest.mark.asyncio
    async def test_handles_missing_session_id(self, tmp_path: Path) -> None:
        """Given ResultMessage without session_id, handles gracefully."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK
        from unittest.mock import MagicMock

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        mock_result = MagicMock()
        mock_result.session_id = None
        mock_result.is_error = False

        phase._process_result_message(mock_result)

        assert phase.session_id is None

    def test_includes_session_id_in_phase_result(self, tmp_path: Path) -> None:
        """Given captured session_id, includes in PhaseResult metadata."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        # Create research file for successful execution
        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-14-test.md"
        research_file.write_text("# Test Research\n\nContent here.")

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        # Mock SDK execution to return session_id
        async def mock_execute(prompt):
            phase.session_id = "session-xyz-789"
            phase.artifacts = [str(research_file)]
            return {"success": True, "output": "Done"}

        with patch.object(phase, "_execute_sdk", mock_execute):
            result = phase.execute("Test query")

        assert result.metadata.get("session_id") == "session-xyz-789"

    def test_session_id_available_for_next_phase(self, tmp_path: Path) -> None:
        """Given research complete, session_id accessible for planning."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-14-test.md"
        research_file.write_text("# Test\n\nContent")

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        async def mock_execute(prompt):
            phase.session_id = "session-for-planning"
            phase.artifacts = [str(research_file)]
            return {"success": True, "output": "Done"}

        with patch.object(phase, "_execute_sdk", mock_execute):
            result = phase.execute("Test query")

        # Session ID should be in metadata for pipeline to pass to next phase
        session_id = result.metadata.get("session_id")
        assert session_id is not None
        assert session_id == "session-for-planning"
```

#### 🟢 Green: Minimal Implementation

**File**: `silmari_rlm_act/phases/research_sdk.py`

```python
from claude_agent_sdk.types import ResultMessage

def _process_result_message(self, message: ResultMessage) -> None:
    """Process ResultMessage to capture session_id.

    Args:
        message: ResultMessage from SDK
    """
    self.session_id = getattr(message, "session_id", None)

def execute(
    self,
    research_question: str,
    additional_context: str = "",
    timeout: Optional[int] = None,
) -> PhaseResult:
    """Execute research phase using SDK.

    Args:
        research_question: The question to research
        additional_context: Optional additional context
        timeout: Optional timeout in seconds

    Returns:
        PhaseResult with research artifacts and session_id
    """
    started_at = datetime.now()

    try:
        prompt = self._build_prompt(research_question, additional_context)
        result = asyncio.run(self._execute_sdk(prompt))

        # ... artifact processing ...

        return PhaseResult(
            phase_type=PhaseType.RESEARCH,
            status=PhaseStatus.COMPLETE,
            artifacts=self.artifacts,
            started_at=started_at,
            completed_at=datetime.now(),
            metadata={
                "session_id": self.session_id,  # Include for next phase
                "open_questions": [],
            },
        )
    except Exception as e:
        # ... error handling ...
```

### Success Criteria

**Automated:**
- [x] Test fails for right reason (Red)
- [x] Test passes (Green)
- [x] session_id present in PhaseResult metadata

---

## Behavior 8: Session Resumption

### Test Specification

**Given**: session_id from research phase
**When**: ImplementationPhaseSDK.execute() called
**Then**: ClaudeAgentOptions.resume set to session_id

**Edge Cases**:
- No session_id provided (should work without resumption)
- Invalid session_id (SDK should handle gracefully)
- Session expired (SDK should start fresh)

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari_rlm_act/tests/test_implementation_phase_sdk.py`

```python
class TestSessionResumption:
    """Behavior 8: Session Resumption."""

    def test_resumes_session_when_provided(self, tmp_path: Path) -> None:
        """Given session_id, passes to ClaudeAgentOptions.resume."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        # Create plan file
        plan = tmp_path / "00-overview.md"
        plan.write_text("# TDD Plan\n\nImplementation details.")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.query = AsyncMock()
        mock_client.receive_response = AsyncMock(return_value=iter([]))

        with patch("silmari_rlm_act.phases.implementation_sdk.ClaudeSDKClient", return_value=mock_client) as mock_cls:
            with patch.object(phase, "_check_completion", return_value=True):
                with patch.object(phase, "_run_tests", return_value=(True, "passed")):
                    phase.execute(
                        phase_paths=[str(plan)],
                        mode=AutonomyMode.FULLY_AUTONOMOUS,
                        session_id="session-from-research",
                    )

        # Verify resume option set
        call_kwargs = mock_cls.call_args[1]
        options = call_kwargs.get("options")
        assert options.resume == "session-from-research"

    def test_works_without_session_id(self, tmp_path: Path) -> None:
        """Given no session_id, executes without resumption."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plan = tmp_path / "00-overview.md"
        plan.write_text("# TDD Plan\n\nDetails.")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.query = AsyncMock()
        mock_client.receive_response = AsyncMock(return_value=iter([]))

        with patch("silmari_rlm_act.phases.implementation_sdk.ClaudeSDKClient", return_value=mock_client) as mock_cls:
            with patch.object(phase, "_check_completion", return_value=True):
                with patch.object(phase, "_run_tests", return_value=(True, "passed")):
                    result = phase.execute(
                        phase_paths=[str(plan)],
                        mode=AutonomyMode.FULLY_AUTONOMOUS,
                        # No session_id
                    )

        # Should complete successfully without session
        assert result.status == PhaseStatus.COMPLETE

        # Resume should be None or not set
        call_kwargs = mock_cls.call_args[1]
        options = call_kwargs.get("options")
        assert options.resume is None

    def test_session_id_from_inputs(self, tmp_path: Path) -> None:
        """Given session_id in execute args, uses it for resumption."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plan = tmp_path / "00-overview.md"
        plan.write_text("# Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        # Verify session_id parameter is accepted
        import inspect
        sig = inspect.signature(phase.execute)
        assert "session_id" in sig.parameters
```

#### 🟢 Green: Minimal Implementation

**File**: `silmari_rlm_act/phases/implementation_sdk.py`

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

class ImplementationPhaseSDK:
    """SDK-based implementation phase with session resumption."""

    LOOP_SLEEP = 10
    CLAUDE_TIMEOUT = 3600

    def execute(
        self,
        phase_paths: list[str],
        mode: AutonomyMode,
        beads_issue_ids: Optional[list[str]] = None,
        beads_epic_id: Optional[str] = None,
        max_iterations: int = 100,
        session_id: Optional[str] = None,  # NEW: For session resumption
        checkpoint: Optional[dict[str, Any]] = None,
    ) -> PhaseResult:
        """Execute implementation via SDK with session resumption.

        Args:
            phase_paths: Paths to TDD plan documents
            mode: Execution mode
            beads_issue_ids: Beads issue IDs for tracking
            beads_epic_id: Optional beads epic ID
            max_iterations: Safety limit on loop iterations
            session_id: Optional session ID from research phase
            checkpoint: Optional checkpoint (ignored)

        Returns:
            PhaseResult with implementation status
        """
        # Build options with optional resume
        options = ClaudeAgentOptions(
            cwd=self.project_path,
            allowed_tools=self.ALLOWED_TOOLS,
            can_use_tool=self._implementation_permissions,
            resume=session_id,  # Resume from research session
        )

        # ... rest of implementation loop ...
```

### Success Criteria

**Automated:**
- [x] Test fails for right reason (Red)
- [x] Test passes (Green)
- [x] Session resumption works when provided
- [x] Works without session (fresh start)

**Manual:**
- [x] Claude remembers research context when session resumed
- [x] Implementation can reference research findings

---

## Checkpoint Integration

Session IDs must persist across pipeline restarts. When checkpointing:

1. **Save**: Store `session_id` in PhaseResult.metadata during `to_dict()`
2. **Load**: Extract `session_id` from restored PhaseResult during resume
3. **Pass**: Include `session_id` in execute() call to ImplementationPhaseSDK

### Checkpoint Schema Addition

```python
# Checkpoint includes session_id for resumption:
{
    "phase_results": {
        "research": {
            "status": "COMPLETE",
            "artifacts": ["thoughts/searchable/shared/research/2026-01-14-topic.md"],
            "metadata": {
                "session_id": "session-abc-123",  # Persist for resumption
                "open_questions": []
            }
        }
    }
}
```

### Pipeline Resume Flow

```python
# In RLMActPipeline.resume_from_checkpoint():
research_result = state.get_phase_result(PhaseType.RESEARCH)
session_id = research_result.metadata.get("session_id") if research_result else None

# Pass session_id to implementation phase
implementation_phase.execute(
    phase_paths=plan_paths,
    mode=mode,
    session_id=session_id,  # Resume from research session
)
```

### Test for Checkpoint Flow

```python
def test_session_id_flows_through_checkpoint(self, tmp_path: Path) -> None:
    """Given checkpoint with session_id, passes to implementation."""
    from silmari_rlm_act.orchestration.pipeline import RLMActPipeline

    # Create checkpoint with session_id
    checkpoint = {
        "phase_results": {
            "research": {
                "status": "COMPLETE",
                "metadata": {"session_id": "session-from-checkpoint"}
            }
        }
    }

    pipeline = RLMActPipeline(tmp_path)

    with patch.object(pipeline.implementation_phase, "execute") as mock_execute:
        mock_execute.return_value = PhaseResult(...)
        pipeline.resume_from_checkpoint(checkpoint)

    # Verify session_id passed
    call_kwargs = mock_execute.call_args[1]
    assert call_kwargs.get("session_id") == "session-from-checkpoint"
```
