# Research: RLM-Act Loop Interrupt and Session Management

**Date**: 2026-01-14
**Git Commit**: fc81f88898c3628cd32c552c85ce4ae475e517b3
**Branch**: main
**Repository**: silmari-Context-Engine

## Problem Statement

The silmari-rlm-act pipeline runs in a loop process for implementation. This loop lacks:
1. A mechanism for users to interrupt execution
2. A way to take user input/feedback during execution
3. Session state maintenance across interrupts
4. Resume capability after user pauses

This is both a **UI issue** (no interactive feedback during autonomous execution) and a **backend issue** (no graceful interrupt handling, state serialization, or session management).

---

## Key Findings

### 1. Current Implementation Analysis

#### The Implementation Loop (No Interrupt Handling)

**File**: `silmari_rlm_act/phases/implementation.py:262-299`

```python
while iteration < max_iterations:
    iteration += 1
    print(f"\n{'=' * 60}")
    print(f"IMPLEMENTATION LOOP - Iteration {iteration}")
    print(f"{'=' * 60}\n")

    # Invoke Claude with plan (output streams directly to terminal)
    result = self._invoke_claude(prompt)

    if not result["success"]:
        print(f"Claude invocation failed: {result.get('error', 'unknown error')}")

    # Sleep between iterations
    print(f"\n{'=' * 25} LOOP {'=' * 25}\n")
    time.sleep(self.LOOP_SLEEP)

    # Check if all issues are closed
    if self._check_completion(issue_ids):
        # ... completion logic
```

**Issues**:
- No KeyboardInterrupt handling
- No signal handlers (SIGINT, SIGTERM)
- No way to pause and resume
- No user input collection during loop
- State lost on Ctrl+C

#### SDK-Based Implementation (Has Interrupt But No Loop)

**File**: `silmari_rlm_act/phases/implementation_sdk.py:189-329`

The SDK implementation is single-turn (no loop) but has proper disconnect handling:

```python
finally:
    # Always disconnect
    try:
        await client.disconnect()
    except Exception:
        pass
```

**Gap**: The SDK implementation doesn't have the iterative loop pattern of the subprocess implementation.

---

### 2. Claude Agent SDK Capabilities

#### Session Management Methods

| Method | Purpose | Status |
|--------|---------|--------|
| `client.connect()` | Establish session | Available |
| `client.disconnect()` | End session cleanly | Available |
| `client.query(prompt)` | Send message | Available |
| `client.receive_response()` | Async iterator | Available |
| `client.interrupt()` | Stop current task | **Available** |

#### The `interrupt()` Method

**File**: `test-conversation.py:21-24`

```python
elif user_input.lower() == 'interrupt':
    await self.client.interrupt()  # KEY METHOD
    print("Task interrupted!")
    continue  # Skip to next input prompt
```

**Behavior**:
- Stops Claude's current execution immediately
- Session remains connected
- Context is preserved
- Can send new queries after interrupt
- Does NOT disconnect or clear session state

#### Session Lifecycle Pattern

**File**: `test-conversation.py:11-47`

```python
await client.connect()  # Start session

while True:  # Multi-turn loop
    user_input = input(f"\n[Turn {self.turn_count + 1}] You: ")

    if user_input.lower() == 'exit':
        break
    elif user_input.lower() == 'interrupt':
        await self.client.interrupt()
        continue
    elif user_input.lower() == 'new':
        await self.client.disconnect()
        await self.client.connect()  # Fresh session
        continue

    await self.client.query(user_input)
    # ... process response

await self.client.disconnect()
```

This demonstrates a **working interactive loop with interrupt support**.

---

### 3. Existing Checkpoint Infrastructure

#### CheckpointManager

**File**: `silmari_rlm_act/checkpoints/manager.py`

```python
def write_checkpoint(self, state: PipelineState, phase: str, errors: Optional[list[str]] = None) -> str:
    data = {
        "id": checkpoint_id,
        "phase": phase,
        "timestamp": datetime.now().isoformat() + "Z",
        "state": state.to_checkpoint_dict(),
        "errors": errors or [],
        "git_commit": self._get_git_commit(),
    }
```

**Capabilities**:
- UUID-based checkpoint files in `.rlm-act-checkpoints/`
- Full state serialization via `to_checkpoint_dict()`
- Automatic detection of resumable checkpoints
- Age-based cleanup

#### PipelineState Serialization

**File**: `silmari_rlm_act/models.py`

```python
@dataclass
class PipelineState:
    project_path: str
    autonomy_mode: AutonomyMode
    current_phase: Optional[PhaseType] = None
    phase_results: dict[PhaseType, PhaseResult] = field(default_factory=dict)

    def to_checkpoint_dict(self) -> dict[str, Any]:
        return self.to_dict()

    @classmethod
    def from_checkpoint_dict(cls, data: dict[str, Any]) -> "PipelineState":
        return cls.from_dict(data)
```

**This infrastructure can be extended** to save loop iteration state.

---

### 4. Interactive Prompt Patterns

#### Existing Menu Pattern

**File**: `silmari_rlm_act/checkpoints/interactive.py:19-47`

```python
def prompt_research_action() -> str:
    valid_actions = {
        "c": "continue",
        "r": "revise",
        "s": "restart",
        "e": "exit",
        "": "continue",
    }

    while True:
        print("\nWhat would you like to do?")
        print("  [C]ontinue to decomposition (default)")
        print("  [R]evise research with additional context")
        print("  [S]tart over with new prompt")
        print("  [E]xit pipeline")

        response = input("\nChoice [C/r/s/e]: ").strip().lower()

        if response in valid_actions:
            return valid_actions[response]
        print(f"Invalid choice: '{response}'. Please enter C, R, S, or E.")
```

**This pattern can be adapted** for implementation loop pauses.

---

### 5. Signal Handling Patterns

#### Python: KeyboardInterrupt Handling

**File**: `orchestrator.py:1064-1073`

```python
except KeyboardInterrupt:
    print()
    print_status("Session interrupted by user", "warning")
    return {
        "success": True,
        "output": "Session ended by user",
        "error": "",
        "elapsed": time.time() - start_time,
        "returncode": 0
    }
```

**Key Pattern**: Return success=True (user interrupt is not an error).

#### Python: Signal with Timeout (Unix)

**File**: `silmari_rlm_act/validation/service.py:344-393`

```python
def timeout_handler(signum: int, frame: Any) -> None:
    raise TimeoutError("Validation timed out")

if sys.platform != "win32":
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(self.config.timeout_seconds)

try:
    result = self.validate_sync(scope_text, hierarchy_path)
    signal.alarm(0)  # Cancel timeout
    return result
finally:
    if sys.platform != "win32":
        signal.signal(signal.SIGALRM, old_handler)  # Restore
```

#### Go: Context-Based Cancellation

**File**: `go/internal/planning/claude_runner.go:229-231`

```go
ctx, cancel := context.WithTimeout(context.Background(), time.Duration(timeoutSecs)*time.Second)
defer cancel()
```

#### Go: Signal Handler Pattern

**File**: `go/internal/concurrent/signal.go`

```go
type SignalHandler struct {
    signals    []os.Signal
    callbacks  []func(os.Signal)
    ctx        context.Context
    cancel     context.CancelFunc
    sigCh      chan os.Signal
}

func (h *SignalHandler) Start() context.Context {
    signal.Notify(h.sigCh, h.signals...)
    go h.listen()
    return h.ctx
}
```

---

### 6. Asyncio Best Practices (Web Research)

#### Signal Handler Registration

```python
import asyncio
import signal

async def shutdown(signal, loop):
    """Graceful shutdown handler."""
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)  # CRITICAL: return_exceptions=True
    loop.stop()

def main():
    loop = asyncio.get_event_loop()
    for s in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(s, loop))
        )
    loop.run_forever()
```

#### CancelledError Handling

```python
async def operation():
    try:
        await long_running_task()
    except asyncio.CancelledError:
        await save_checkpoint()  # Save state
        raise  # ALWAYS re-raise CancelledError
    finally:
        await cleanup()
```

**Key Rule**: Always re-raise `asyncio.CancelledError` after cleanup.

#### CancellableSleeps Pattern

```python
class CancellableSleeps:
    def __init__(self):
        self._sleep_tasks = set()

    async def sleep(self, delay):
        task = asyncio.current_task()
        self._sleep_tasks.add(task)
        try:
            await asyncio.sleep(delay)
        finally:
            self._sleep_tasks.discard(task)

    def cancel_all(self):
        for task in self._sleep_tasks:
            task.cancel()
```

---

## Architecture Recommendations

### Option A: SDK-Based Loop with Interactive Interrupt (Recommended)

Combine the SDK's `interrupt()` capability with a user input loop:

```python
class InteractiveImplementationPhase:
    def __init__(self, ...):
        self.client = ClaudeSDKClient(options)
        self.sleeps = CancellableSleeps()
        self._should_pause = False

    async def execute_loop(self, max_iterations: int):
        await self.client.connect()

        try:
            for iteration in range(max_iterations):
                # Check for pause request
                if self._should_pause:
                    action = await self._prompt_action()
                    if action == "exit":
                        return self._create_result("paused")
                    self._should_pause = False

                # Execute iteration
                await self.client.query(self._build_prompt(iteration))
                async for message in self.client.receive_response():
                    # Process streaming response...
                    pass

                # Interruptible sleep
                await self.sleeps.sleep(self.LOOP_SLEEP)

                # Check completion
                if self._check_completion():
                    return self._create_result("complete")

        except asyncio.CancelledError:
            await self._save_checkpoint(iteration)
            raise
        finally:
            await self.client.disconnect()

    async def pause(self):
        """Called from signal handler or input thread."""
        self._should_pause = True
        self.sleeps.cancel_all()  # Wake up immediately

    async def interrupt(self):
        """Interrupt current Claude execution."""
        await self.client.interrupt()
```

### Option B: Signal-Based Graceful Shutdown

Add signal handlers to the existing subprocess loop:

```python
class ImplementationPhase:
    def __init__(self, ...):
        self._interrupted = False
        self._current_iteration = 0

    def _handle_interrupt(self, signum, frame):
        print("\nInterrupt received. Finishing current iteration...")
        self._interrupted = True

    def execute(self, ...):
        # Register signal handlers
        old_sigint = signal.signal(signal.SIGINT, self._handle_interrupt)
        old_sigterm = signal.signal(signal.SIGTERM, self._handle_interrupt)

        try:
            while self._current_iteration < max_iterations:
                if self._interrupted:
                    return self._handle_pause()

                # ... existing loop body ...
                self._current_iteration += 1

        finally:
            signal.signal(signal.SIGINT, old_sigint)
            signal.signal(signal.SIGTERM, old_sigterm)

    def _handle_pause(self):
        self._save_checkpoint()
        action = prompt_implementation_action()  # Use existing pattern

        if action == "continue":
            self._interrupted = False
            return self.execute(...)  # Resume
        elif action == "exit":
            return self._create_result("paused")
```

### Option C: Non-Blocking Input Thread

For truly interactive feedback without interrupting:

```python
import threading
import queue

class InteractiveLoop:
    def __init__(self):
        self.input_queue = queue.Queue()
        self.running = True

    def _input_thread(self):
        """Background thread for user input."""
        while self.running:
            try:
                user_input = input()  # Blocking
                self.input_queue.put(user_input)
            except EOFError:
                break

    def execute(self):
        thread = threading.Thread(target=self._input_thread, daemon=True)
        thread.start()

        while iteration < max_iterations:
            # Check for user input (non-blocking)
            try:
                cmd = self.input_queue.get_nowait()
                if cmd == "pause":
                    action = self._prompt_action()
                    # ...
                elif cmd == "status":
                    self._print_status()
            except queue.Empty:
                pass

            # ... continue loop ...
```

---

## Implementation Priority

### Phase 1: Signal Handler + Checkpoint (Quick Win)

1. Add `signal.SIGINT` handler to implementation loop
2. Save checkpoint on interrupt with current iteration
3. Add "Resume from iteration N" option to CLI

**Effort**: Low
**Impact**: Users can Ctrl+C and resume

### Phase 2: Interactive Pause Menu

1. On SIGINT, show menu: Continue/Exit/Revise prompt
2. Integrate with existing `prompt_*_action()` patterns
3. Support feedback collection during pause

**Effort**: Medium
**Impact**: Users can provide feedback during execution

### Phase 3: SDK Loop Migration

1. Migrate from subprocess to SDK-based loop
2. Add `client.interrupt()` support
3. Implement cancellable sleeps
4. Add non-blocking input thread for commands

**Effort**: High
**Impact**: Full interactive control with preserved context

---

## Files to Modify

| File | Change |
|------|--------|
| `silmari_rlm_act/phases/implementation.py` | Add signal handlers, checkpoint on interrupt |
| `silmari_rlm_act/phases/implementation_sdk.py` | Add iterative loop with interrupt support |
| `silmari_rlm_act/checkpoints/interactive.py` | Add `prompt_implementation_action()` |
| `silmari_rlm_act/checkpoints/manager.py` | Add iteration state to checkpoint |
| `silmari_rlm_act/models.py` | Add `LoopState` dataclass for iteration tracking |
| `silmari_rlm_act/cli.py` | Add `--resume-iteration` flag |

---

## Testing Strategy

### Unit Tests

```python
# Test signal handler registration
def test_sigint_handler_registered():
    phase = ImplementationPhase(...)
    phase.execute(...)  # Mock to check signal.signal called

# Test checkpoint on interrupt
def test_checkpoint_saved_on_interrupt():
    phase = ImplementationPhase(...)
    phase._interrupted = True
    result = phase.execute(...)
    assert result.metadata["interrupted_at_iteration"] == 3
```

### Integration Tests

```python
# Test pause and resume
async def test_pause_resume_loop():
    phase = InteractiveImplementationPhase(...)

    # Start in background
    task = asyncio.create_task(phase.execute_loop(10))

    # Pause after 2 iterations
    await asyncio.sleep(5)
    await phase.pause()

    # Verify state
    assert phase._current_iteration >= 2
    assert phase._should_pause == True
```

---

## References

### Codebase Files

- `silmari_rlm_act/phases/implementation.py:262-299` - Current loop (no interrupt)
- `silmari_rlm_act/phases/implementation_sdk.py:189-329` - SDK single-turn
- `test-conversation.py:11-47` - Working interactive loop with interrupt
- `silmari_rlm_act/checkpoints/interactive.py` - Menu prompt patterns
- `silmari_rlm_act/checkpoints/manager.py` - Checkpoint infrastructure
- `go/internal/concurrent/signal.go` - Go signal handling reference
- `orchestrator.py:1064-1073` - KeyboardInterrupt handling pattern

### External Sources

- [Graceful Shutdowns with asyncio - roguelynn](https://roguelynn.com/words/asyncio-graceful-shutdowns/)
- [Asyncio Handle Control-C (SIGINT) - Super Fast Python](https://superfastpython.com/asyncio-control-c-sigint/)
- [python-graceful-shutdown - GitHub](https://github.com/wbenny/python-graceful-shutdown)
- [3 Essential Async Patterns - Elastic Blog](https://www.elastic.co/blog/async-patterns-building-python-service)
