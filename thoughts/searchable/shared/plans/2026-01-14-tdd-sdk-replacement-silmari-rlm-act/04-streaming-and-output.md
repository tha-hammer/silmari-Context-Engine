# Phase 04: Streaming and Output

## Behaviors

6. **Streaming output display** - Print text blocks to stdout in real-time
10. **Loop iteration with SDK** - Real-time streaming during implementation

---

## Behavior 6: Streaming Output Display

### Test Specification

**Given**: AssistantMessage with TextBlock received
**When**: Processing response stream
**Then**: Text content printed to stdout with flush

**Edge Cases**:
- Multiple TextBlocks in one message
- ToolUseBlock (should print tool name, not content)
- Empty TextBlock (should handle gracefully)
- Unicode content (should display correctly)

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari_rlm_act/tests/test_research_phase_sdk.py`

```python
class TestStreamingOutputDisplay:
    """Behavior 6: Streaming Output Display."""

    @pytest.mark.asyncio
    async def test_prints_text_blocks_to_stdout(
        self, tmp_path: Path, capsys
    ) -> None:
        """Given TextBlock, prints content to stdout."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK
        from unittest.mock import MagicMock

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        # Create mock TextBlock
        mock_text_block = MagicMock()
        mock_text_block.text = "Research findings here"

        # Create mock AssistantMessage
        mock_message = MagicMock()
        mock_message.content = [mock_text_block]

        # Process the message
        await phase._process_assistant_message(mock_message)

        captured = capsys.readouterr()
        assert "Research findings here" in captured.out

    @pytest.mark.asyncio
    async def test_prints_tool_use_indicator(
        self, tmp_path: Path, capsys
    ) -> None:
        """Given ToolUseBlock, prints tool indicator."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK
        from unittest.mock import MagicMock

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        mock_tool_block = MagicMock()
        mock_tool_block.name = "Read"
        mock_tool_block.input = {"file_path": "/path/to/file.py"}

        mock_message = MagicMock()
        mock_message.content = [mock_tool_block]

        await phase._process_assistant_message(mock_message)

        captured = capsys.readouterr()
        assert "Read" in captured.out

    @pytest.mark.asyncio
    async def test_handles_multiple_blocks(
        self, tmp_path: Path, capsys
    ) -> None:
        """Given multiple blocks, prints all."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK
        from unittest.mock import MagicMock

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        mock_text1 = MagicMock()
        mock_text1.text = "First part"

        mock_text2 = MagicMock()
        mock_text2.text = "Second part"

        mock_message = MagicMock()
        mock_message.content = [mock_text1, mock_text2]

        await phase._process_assistant_message(mock_message)

        captured = capsys.readouterr()
        assert "First part" in captured.out
        assert "Second part" in captured.out

    @pytest.mark.asyncio
    async def test_collects_output_for_result(self, tmp_path: Path) -> None:
        """Given text blocks, collects for PhaseResult output."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK
        from unittest.mock import MagicMock

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        mock_text = MagicMock()
        mock_text.text = "Collected output"

        mock_message = MagicMock()
        mock_message.content = [mock_text]

        phase.output_chunks = []  # Initialize collector
        await phase._process_assistant_message(mock_message)

        assert "Collected output" in "".join(phase.output_chunks)
```

#### 🟢 Green: Minimal Implementation

**File**: `silmari_rlm_act/phases/research_sdk.py`

```python
from claude_agent_sdk.types import AssistantMessage, TextBlock, ToolUseBlock

async def _process_assistant_message(self, message: AssistantMessage) -> None:
    """Process assistant message for streaming output.

    Args:
        message: AssistantMessage from SDK stream
    """
    for block in message.content:
        if hasattr(block, "text"):
            # TextBlock - print and collect
            print(block.text, end="", flush=True)
            self.output_chunks.append(block.text)
        elif hasattr(block, "name"):
            # ToolUseBlock - print indicator
            file_path = block.input.get("file_path", "")
            print(f"\n⏺ {block.name}({file_path})", flush=True)
```

### Success Criteria

**Automated:**
- [x] Test fails for right reason (Red)
- [x] Test passes (Green)
- [x] Output visible in real-time (flush=True)

---

## Behavior 10: Loop Iteration with SDK

### Test Specification

**Given**: Implementation iteration starts
**When**: SDK query() called in loop
**Then**: Real-time streaming to terminal, loop continues after completion

**Edge Cases**:
- SDK timeout (should continue to next iteration)
- SDK error (should log and continue)
- Interrupt signal (should exit gracefully)

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari_rlm_act/tests/test_implementation_phase_sdk.py`

```python
class TestLoopIterationWithSDK:
    """Behavior 10: Loop Iteration with SDK."""

    def test_streams_output_during_iteration(
        self, tmp_path: Path, capsys
    ) -> None:
        """Given loop iteration, streams SDK output."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK
        from unittest.mock import MagicMock, AsyncMock

        plan = tmp_path / "00-overview.md"
        plan.write_text("# Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)
        phase.LOOP_SLEEP = 0  # Speed up test

        # Create mock that yields streaming content
        mock_text = MagicMock()
        mock_text.text = "Implementing feature..."
        mock_message = MagicMock()
        mock_message.content = [mock_text]

        async def mock_response():
            yield mock_message

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.query = AsyncMock()
        mock_client.receive_response = mock_response

        with patch("silmari_rlm_act.phases.implementation_sdk.ClaudeSDKClient", return_value=mock_client):
            with patch.object(phase, "_check_completion", return_value=True):
                with patch.object(phase, "_run_tests", return_value=(True, "passed")):
                    phase.execute(
                        phase_paths=[str(plan)],
                        mode=AutonomyMode.FULLY_AUTONOMOUS,
                    )

        captured = capsys.readouterr()
        assert "Implementing" in captured.out or "IMPLEMENTATION" in captured.out

    def test_continues_after_sdk_error(self, tmp_path: Path) -> None:
        """Given SDK error, continues to next iteration."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK
        from unittest.mock import MagicMock, AsyncMock

        plan = tmp_path / "00-overview.md"
        plan.write_text("# Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)
        phase.LOOP_SLEEP = 0

        iteration_count = [0]

        async def mock_sdk_call(prompt):
            iteration_count[0] += 1
            if iteration_count[0] == 1:
                raise Exception("SDK connection error")
            return {"success": True, "output": "Done"}

        with patch.object(phase, "_invoke_claude_sdk", mock_sdk_call):
            with patch.object(phase, "_check_completion", side_effect=[False, True]):
                with patch.object(phase, "_run_tests", return_value=(True, "passed")):
                    result = phase.execute(
                        phase_paths=[str(plan)],
                        mode=AutonomyMode.FULLY_AUTONOMOUS,
                        max_iterations=3,
                    )

        # Should have continued despite first error
        assert iteration_count[0] >= 2
        assert result.status == PhaseStatus.COMPLETE

    def test_respects_max_iterations(self, tmp_path: Path) -> None:
        """Given max iterations reached, exits loop."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plan = tmp_path / "00-overview.md"
        plan.write_text("# Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)
        phase.LOOP_SLEEP = 0

        async def mock_sdk_call(prompt):
            return {"success": True, "output": "Working..."}

        with patch.object(phase, "_invoke_claude_sdk", mock_sdk_call):
            with patch.object(phase, "_check_completion", return_value=False):
                result = phase.execute(
                    phase_paths=[str(plan)],
                    mode=AutonomyMode.FULLY_AUTONOMOUS,
                    max_iterations=3,
                )

        assert result.status == PhaseStatus.FAILED
        assert "max iterations" in result.errors[0].lower()
        assert result.metadata["iterations"] == 3
```

#### 🟢 Green: Minimal Implementation

**File**: `silmari_rlm_act/phases/implementation_sdk.py`

```python
async def _invoke_claude_sdk(self, prompt: str) -> dict[str, Any]:
    """Invoke Claude via SDK with streaming output.

    Args:
        prompt: The implementation prompt

    Returns:
        Dict with success, output
    """
    output_chunks: list[str] = []

    async with ClaudeSDKClient(options=self._get_options()) as client:
        await client.query(prompt)

        async for message in client.receive_response():
            if hasattr(message, "content"):
                for block in message.content:
                    if hasattr(block, "text"):
                        print(block.text, end="", flush=True)
                        output_chunks.append(block.text)

    return {
        "success": True,
        "output": "".join(output_chunks),
    }

def execute(
    self,
    phase_paths: list[str],
    mode: AutonomyMode,
    beads_issue_ids: Optional[list[str]] = None,
    beads_epic_id: Optional[str] = None,
    max_iterations: int = 100,
    session_id: Optional[str] = None,
    checkpoint: Optional[dict[str, Any]] = None,
) -> PhaseResult:
    """Execute implementation via SDK loop."""
    started_at = datetime.now()
    errors: list[str] = []
    artifacts: list[str] = []

    # ... validation ...

    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        print(f"\n{'=' * 60}")
        print(f"IMPLEMENTATION LOOP - Iteration {iteration}")
        print(f"{'=' * 60}\n")

        try:
            asyncio.run(self._invoke_claude_sdk(prompt))
        except Exception as e:
            print(f"SDK error: {e}")
            # Continue to next iteration

        time.sleep(self.LOOP_SLEEP)

        if self._check_completion(issue_ids):
            tests_pass, test_output = self._run_tests()
            if tests_pass:
                artifacts.extend(phase_paths)
                break
            else:
                errors.append(f"Tests failed: {test_output[:500]}")
                continue
    else:
        errors.append(f"Reached max iterations ({max_iterations})")

    return PhaseResult(
        phase_type=PhaseType.IMPLEMENTATION,
        status=PhaseStatus.COMPLETE if not errors else PhaseStatus.FAILED,
        artifacts=artifacts,
        errors=errors,
        metadata={"iterations": iteration, "mode": "sdk_loop"},
    )
```

### Success Criteria

**Automated:**
- [x] Test fails for right reason (Red)
- [x] Test passes (Green)
- [x] Output streams in real-time
- [x] Loop continues after errors
- [x] Max iterations respected

**Manual:**
- [x] Terminal shows real-time output during implementation
- [x] Loop behavior matches existing implementation.py
