# Phase 05: PhaseResult Construction

## Exception Handling

All SDK exceptions must be caught and converted to PhaseResult failures. The `_execute_sdk()` method can throw:

- `RuntimeError`: SDK connection failed
- `TimeoutError`: Query exceeded timeout
- `ValueError`: Invalid options configuration
- `Exception`: Any other SDK error

All are caught and converted to `PhaseResult(status=FAILED, errors=[str(e)])`.

### Exception Handling Pattern

```python
try:
    result = await self._execute_sdk(prompt)
except Exception as e:
    return PhaseResult(
        phase_type=PhaseType.RESEARCH,
        status=PhaseStatus.FAILED,
        errors=[f"SDK error: {type(e).__name__}: {str(e)}"],
        started_at=started_at,
        completed_at=datetime.now(),
        duration_seconds=(datetime.now() - started_at).total_seconds(),
        metadata={"error_type": type(e).__name__},
    )
```

### Context Manager Cleanup

The SDK uses async context manager pattern. Cleanup is guaranteed even on exceptions:

```python
async with ClaudeSDKClient(options=options) as client:
    try:
        await client.query(prompt)
        async for message in client.receive_response():
            ...
    except Exception as e:
        # Context manager ensures disconnect() called
        raise  # Re-raise for outer handler
```

### Test for Exception Handling

```python
def test_returns_failed_with_error_type(self, tmp_path: Path) -> None:
    """Given SDK exception, includes error type in metadata."""
    from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

    cwa = CWAIntegration()
    phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

    async def mock_execute(prompt):
        raise TimeoutError("Query timed out after 1200 seconds")

    with patch.object(phase, "_execute_sdk", mock_execute):
        result = phase.execute("Query")

    assert result.status == PhaseStatus.FAILED
    assert "TimeoutError" in result.errors[0]
    assert result.metadata.get("error_type") == "TimeoutError"
```

## Behaviors

7. **PhaseResult construction** - Build correct PhaseResult from SDK execution
11. **Completion check unchanged** - Verify beads status check works
12. **Test verification unchanged** - Verify pytest execution works
13. **Error tolerance** - SDK failures don't break loop
14. **Max iterations handling** - Proper failure on limit reached

---

## Behavior 7: PhaseResult Construction

### Test Specification

**Given**: Successful research execution via SDK
**When**: execute() returns
**Then**: PhaseResult contains artifacts, session_id, open_questions, correct status

**Edge Cases**:
- No artifacts found (should fail)
- Multiple artifacts (should include all)
- SDK error (should return FAILED status)

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari_rlm_act/tests/test_research_phase_sdk.py`

```python
class TestPhaseResultConstruction:
    """Behavior 7: PhaseResult Construction."""

    def test_returns_complete_on_success(self, tmp_path: Path) -> None:
        """Given successful execution, returns COMPLETE status."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-14-test.md"
        research_file.write_text("# Research\n\nFindings")

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        async def mock_execute(prompt):
            phase.artifacts = [str(research_file)]
            phase.session_id = "session-123"
            return {"success": True, "output": "Done"}

        with patch.object(phase, "_execute_sdk", mock_execute):
            result = phase.execute("Test query")

        assert result.status == PhaseStatus.COMPLETE
        assert result.phase_type == PhaseType.RESEARCH

    def test_includes_artifacts(self, tmp_path: Path) -> None:
        """Given artifacts tracked, includes in result."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-14-topic.md"
        research_file.write_text("# Research")

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        async def mock_execute(prompt):
            phase.artifacts = [str(research_file)]
            return {"success": True, "output": ""}

        with patch.object(phase, "_execute_sdk", mock_execute):
            result = phase.execute("Query")

        assert len(result.artifacts) > 0
        assert "2026-01-14-topic.md" in result.artifacts[0]

    def test_includes_session_id_in_metadata(self, tmp_path: Path) -> None:
        """Given session captured, includes in metadata."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-14-test.md"
        research_file.write_text("# Test")

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        async def mock_execute(prompt):
            phase.artifacts = [str(research_file)]
            phase.session_id = "session-xyz"
            return {"success": True, "output": ""}

        with patch.object(phase, "_execute_sdk", mock_execute):
            result = phase.execute("Query")

        assert result.metadata["session_id"] == "session-xyz"

    def test_includes_timing_info(self, tmp_path: Path) -> None:
        """Given execution, includes timing information."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        research_dir = tmp_path / "thoughts" / "searchable" / "shared" / "research"
        research_dir.mkdir(parents=True)
        research_file = research_dir / "2026-01-14-test.md"
        research_file.write_text("# Test")

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        async def mock_execute(prompt):
            phase.artifacts = [str(research_file)]
            return {"success": True, "output": ""}

        with patch.object(phase, "_execute_sdk", mock_execute):
            result = phase.execute("Query")

        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.duration_seconds is not None
        assert result.duration_seconds >= 0

    def test_returns_failed_on_no_artifacts(self, tmp_path: Path) -> None:
        """Given no artifacts found, returns FAILED."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        async def mock_execute(prompt):
            phase.artifacts = []  # No artifacts tracked
            return {"success": True, "output": "Done but no file"}

        with patch.object(phase, "_execute_sdk", mock_execute):
            result = phase.execute("Query")

        assert result.status == PhaseStatus.FAILED
        assert len(result.errors) > 0

    def test_returns_failed_on_sdk_error(self, tmp_path: Path) -> None:
        """Given SDK error, returns FAILED with error message."""
        from silmari_rlm_act.phases.research_sdk import ResearchPhaseSDK

        cwa = CWAIntegration()
        phase = ResearchPhaseSDK(project_path=tmp_path, cwa=cwa)

        async def mock_execute(prompt):
            raise RuntimeError("SDK connection failed")

        with patch.object(phase, "_execute_sdk", mock_execute):
            result = phase.execute("Query")

        assert result.status == PhaseStatus.FAILED
        assert "SDK" in result.errors[0] or "connection" in result.errors[0].lower()
```

#### 🟢 Green: Minimal Implementation

Already covered in previous behaviors - this is integration of all pieces.

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red)
- [ ] Test passes (Green)
- [ ] PhaseResult structure matches existing implementation

---

## Behaviors 11-12: Unchanged Behaviors

### Test Specification

These behaviors should remain unchanged from the existing implementation:
- **11: Completion check** - Uses `bd show` to check issue status
- **12: Test verification** - Runs pytest with same arguments

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari_rlm_act/tests/test_implementation_phase_sdk.py`

```python
class TestUnchangedBehaviors:
    """Behaviors 11-12: Verify unchanged behaviors."""

    def test_check_completion_uses_bd_show(self, tmp_path: Path) -> None:
        """Given issue IDs, checks status via bd show."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                stdout="Status: closed\nTitle: Test",
                returncode=0,
            )

            result = phase._check_completion(["beads-001"])

        mock_run.assert_called()
        call_args = mock_run.call_args[0][0]
        assert "bd" in call_args
        assert "show" in call_args
        assert "beads-001" in call_args

    def test_run_tests_uses_pytest(self, tmp_path: Path) -> None:
        """Given implementation, runs pytest."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="5 passed",
                stderr="",
            )

            passed, output = phase._run_tests()

        assert passed is True
        call_args = mock_run.call_args[0][0]
        assert "pytest" in call_args
```

#### 🟢 Green: Copy from Existing Implementation

**File**: `silmari_rlm_act/phases/implementation_sdk.py`

```python
# Copy _check_completion and _run_tests from implementation.py
# These methods are unchanged - just copy them

def _check_completion(self, issue_ids: list[str]) -> bool:
    """Check if all beads issues are closed.

    Copied from implementation.py - behavior unchanged.
    """
    if not issue_ids:
        return True

    try:
        for issue_id in issue_ids:
            result = subprocess.run(
                ["bd", "show", issue_id],
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=30,
            )

            output = result.stdout.lower()
            if "status: closed" not in output and "status: done" not in output:
                return False

        return True

    except Exception:
        return False

def _run_tests(self) -> tuple[bool, str]:
    """Run test suite to verify implementation.

    Copied from implementation.py - behavior unchanged.
    """
    try:
        result = subprocess.run(
            ["pytest", "-v", "--tb=short"],
            cwd=str(self.project_path),
            capture_output=True,
            text=True,
            timeout=self.TEST_TIMEOUT,
        )
        return result.returncode == 0, result.stdout + result.stderr

    except subprocess.TimeoutExpired:
        return False, f"Tests timed out after {self.TEST_TIMEOUT} seconds"
    except FileNotFoundError:
        try:
            result = subprocess.run(
                ["make", "test"],
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=self.TEST_TIMEOUT,
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception:
            return True, "No test command found, skipping"
    except Exception as e:
        return False, str(e)
```

### Success Criteria

**Automated:**
- [ ] Tests pass
- [ ] Behavior identical to existing implementation.py

---

## Behaviors 13-14: Error Handling

### Test Specification

- **13: Error tolerance** - SDK failures logged but loop continues
- **14: Max iterations** - Proper FAILED status when limit reached

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari_rlm_act/tests/test_implementation_phase_sdk.py`

```python
class TestErrorHandling:
    """Behaviors 13-14: Error Handling."""

    def test_continues_on_sdk_failure(self, tmp_path: Path) -> None:
        """Given SDK failure, logs error and continues loop."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plan = tmp_path / "00-overview.md"
        plan.write_text("# Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)
        phase.LOOP_SLEEP = 0

        call_count = [0]

        async def mock_sdk(prompt):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Connection error")
            return {"success": True, "output": "Done"}

        completion_count = [0]

        def mock_completion(ids):
            completion_count[0] += 1
            return completion_count[0] >= 2

        with patch.object(phase, "_invoke_claude_sdk", mock_sdk):
            with patch.object(phase, "_check_completion", mock_completion):
                with patch.object(phase, "_run_tests", return_value=(True, "passed")):
                    result = phase.execute(
                        phase_paths=[str(plan)],
                        mode=AutonomyMode.FULLY_AUTONOMOUS,
                        max_iterations=5,
                    )

        # Should have continued past first failure
        assert call_count[0] >= 2
        assert result.status == PhaseStatus.COMPLETE

    def test_max_iterations_returns_failed(self, tmp_path: Path) -> None:
        """Given max iterations reached, returns FAILED with error."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plan = tmp_path / "00-overview.md"
        plan.write_text("# Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)
        phase.LOOP_SLEEP = 0

        async def mock_sdk(prompt):
            return {"success": True, "output": "Still working..."}

        with patch.object(phase, "_invoke_claude_sdk", mock_sdk):
            with patch.object(phase, "_check_completion", return_value=False):
                result = phase.execute(
                    phase_paths=[str(plan)],
                    mode=AutonomyMode.FULLY_AUTONOMOUS,
                    max_iterations=3,
                )

        assert result.status == PhaseStatus.FAILED
        assert len(result.errors) > 0
        assert "max iterations" in result.errors[0].lower()
        assert result.metadata["iterations"] == 3

    def test_clears_errors_on_success(self, tmp_path: Path) -> None:
        """Given eventual success, clears previous test failure errors."""
        from silmari_rlm_act.phases.implementation_sdk import ImplementationPhaseSDK

        plan = tmp_path / "00-overview.md"
        plan.write_text("# Plan")

        cwa = CWAIntegration()
        phase = ImplementationPhaseSDK(project_path=tmp_path, cwa=cwa)
        phase.LOOP_SLEEP = 0

        test_call = [0]

        def mock_tests():
            test_call[0] += 1
            if test_call[0] == 1:
                return (False, "Test failure")
            return (True, "passed")

        async def mock_sdk(prompt):
            return {"success": True, "output": "Done"}

        with patch.object(phase, "_invoke_claude_sdk", mock_sdk):
            with patch.object(phase, "_check_completion", return_value=True):
                with patch.object(phase, "_run_tests", mock_tests):
                    result = phase.execute(
                        phase_paths=[str(plan)],
                        mode=AutonomyMode.FULLY_AUTONOMOUS,
                        max_iterations=5,
                    )

        # Should be COMPLETE with no errors (cleared on success)
        assert result.status == PhaseStatus.COMPLETE
        assert len(result.errors) == 0
```

### Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red)
- [ ] Test passes (Green)
- [ ] Error tolerance matches existing behavior
- [ ] Max iterations handled correctly

**Manual:**
- [ ] Loop continues after transient SDK errors
- [ ] Errors cleared when tests eventually pass
