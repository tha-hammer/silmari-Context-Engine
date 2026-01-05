# Phase 03: Interactive Prompts TDD Plan

## Overview

Implement interactive prompts for user interaction at pipeline checkpoints. These prompts allow users to control pipeline execution, provide feedback, and select options.

## Testable Behaviors

### Behavior 1: Research Action Prompt
**Given**: Research phase complete
**When**: Displaying action menu
**Then**: User can choose Continue/Revise/Restart/Exit

### Behavior 2: Checkpoint Resume Prompt
**Given**: Existing checkpoint found
**When**: Asking to use checkpoint
**Then**: User can choose Yes/No

### Behavior 3: Autonomy Mode Selection
**Given**: Implementation phase ready
**When**: Asking for execution mode
**Then**: User can choose Checkpoint/Autonomous/Batch

### Behavior 4: File Selection Menu
**Given**: List of discovered files
**When**: Displaying selection menu
**Then**: User can pick file, search, other path, or exit

### Behavior 5: Multi-line Input Collection
**Given**: Prompt for feedback
**When**: User enters multiple lines
**Then**: Returns joined string on empty line

### Behavior 6: Numeric Days Input
**Given**: Days back prompt
**When**: User enters number
**Then**: Returns integer with default

### Behavior 7: Phase Continue Prompt
**Given**: Phase complete with artifacts
**When**: Asking to continue
**Then**: User can continue or provide feedback

### Behavior 8: Custom Path Input
**Given**: Other path option selected
**When**: User enters path
**Then**: Validates path exists and returns

### Behavior 9: Cleanup Menu
**Given**: Old checkpoints exist
**When**: Showing cleanup options
**Then**: User can delete oldest/N days/all/skip

### Behavior 10: Resume Point Selection
**Given**: Checkpoint with multiple completed phases
**When**: Asking where to resume
**Then**: User can select specific phase

### Behavior 11: Invalid Input Handling
**Given**: User enters invalid choice
**When**: Validating input
**Then**: Reprompts with error message

### Behavior 12: Default Selection
**Given**: Menu with default option
**When**: User presses enter
**Then**: Returns default value

---

## TDD Cycle: Behavior 1 - Research Action Prompt

### Test Specification
**Given**: Research phase complete
**When**: User enters 'c', 'r', 's', or 'e'
**Then**: Returns corresponding action string

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_interactive.py`
```python
import pytest
from unittest.mock import patch
from silmari_rlm_act.checkpoints.interactive import prompt_research_action


class TestResearchActionPrompt:
    """Behavior 1: Research Action Prompt."""

    def test_continue_on_c(self):
        """Given 'c', returns 'continue'."""
        with patch('builtins.input', return_value='c'):
            action = prompt_research_action()
        assert action == "continue"

    def test_continue_on_empty(self):
        """Given empty input, returns 'continue' (default)."""
        with patch('builtins.input', return_value=''):
            action = prompt_research_action()
        assert action == "continue"

    def test_revise_on_r(self):
        """Given 'r', returns 'revise'."""
        with patch('builtins.input', return_value='r'):
            action = prompt_research_action()
        assert action == "revise"

    def test_restart_on_s(self):
        """Given 's', returns 'restart'."""
        with patch('builtins.input', return_value='s'):
            action = prompt_research_action()
        assert action == "restart"

    def test_exit_on_e(self):
        """Given 'e', returns 'exit'."""
        with patch('builtins.input', return_value='e'):
            action = prompt_research_action()
        assert action == "exit"

    def test_case_insensitive(self):
        """Given uppercase 'C', returns 'continue'."""
        with patch('builtins.input', return_value='C'):
            action = prompt_research_action()
        assert action == "continue"

    def test_invalid_then_valid(self):
        """Given invalid then valid input, reprompts."""
        inputs = iter(["x", "c"])
        with patch('builtins.input', lambda _: next(inputs)):
            action = prompt_research_action()
        assert action == "continue"
```

### 🟢 Green: Implement Research Action Prompt

**File**: `silmari-rlm-act/checkpoints/interactive.py`
```python
"""Interactive prompts for pipeline control."""

from pathlib import Path
from typing import Optional


def prompt_research_action() -> str:
    """Prompt user for research checkpoint action.

    Returns:
        One of: 'continue', 'revise', 'restart', 'exit'
    """
    valid_actions = {
        'c': 'continue',
        'r': 'revise',
        's': 'restart',
        'e': 'exit',
        '': 'continue'
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

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_interactive.py::TestResearchActionPrompt -v`

---

## TDD Cycle: Behavior 2 - Checkpoint Resume Prompt

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_interactive.py`
```python
from silmari_rlm_act.checkpoints.interactive import prompt_use_checkpoint


class TestCheckpointResumePrompt:
    """Behavior 2: Checkpoint Resume Prompt."""

    def test_yes_on_y(self):
        """Given 'y', returns True."""
        with patch('builtins.input', return_value='y'):
            use_it = prompt_use_checkpoint(
                timestamp="2026-01-05T10:30:00",
                phase="research-complete"
            )
        assert use_it is True

    def test_yes_on_empty(self):
        """Given empty input, returns True (default)."""
        with patch('builtins.input', return_value=''):
            use_it = prompt_use_checkpoint(
                timestamp="2026-01-05T10:30:00",
                phase="research-complete"
            )
        assert use_it is True

    def test_no_on_n(self):
        """Given 'n', returns False."""
        with patch('builtins.input', return_value='n'):
            use_it = prompt_use_checkpoint(
                timestamp="2026-01-05T10:30:00",
                phase="research-complete"
            )
        assert use_it is False

    def test_displays_checkpoint_info(self, capsys):
        """Given checkpoint, displays timestamp and phase."""
        with patch('builtins.input', return_value='y'):
            prompt_use_checkpoint(
                timestamp="2026-01-05T10:30:00",
                phase="research-complete",
                artifacts=["file1.md", "file2.md"]
            )

        captured = capsys.readouterr()
        assert "2026-01-05T10:30:00" in captured.out
        assert "research-complete" in captured.out
        assert "file1.md" in captured.out
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/checkpoints/interactive.py`
```python
def prompt_use_checkpoint(
    timestamp: str,
    phase: str,
    artifacts: Optional[list[str]] = None
) -> bool:
    """Prompt user to use existing checkpoint.

    Args:
        timestamp: Checkpoint timestamp
        phase: Phase name
        artifacts: Optional list of artifact paths

    Returns:
        True if user wants to use checkpoint
    """
    print(f"\nFound checkpoint from {timestamp[:19]}")
    print(f"  Phase: {phase}")
    if artifacts:
        print(f"  Artifacts:")
        for a in artifacts:
            print(f"    - {Path(a).name}")

    response = input("\nUse this checkpoint? [Y/n]: ").strip().lower()
    return response != 'n'
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_interactive.py::TestCheckpointResumePrompt -v`

---

## TDD Cycle: Behavior 3 - Autonomy Mode Selection

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_interactive.py`
```python
from silmari_rlm_act.checkpoints.interactive import prompt_autonomy_mode
from silmari_rlm_act.models import AutonomyMode


class TestAutonomyModeSelection:
    """Behavior 3: Autonomy Mode Selection."""

    def test_checkpoint_on_c(self):
        """Given 'c', returns CHECKPOINT mode."""
        with patch('builtins.input', return_value='c'):
            mode = prompt_autonomy_mode(phase_count=6, epic_id="beads-abc")
        assert mode == AutonomyMode.CHECKPOINT

    def test_checkpoint_on_empty(self):
        """Given empty, returns CHECKPOINT (default)."""
        with patch('builtins.input', return_value=''):
            mode = prompt_autonomy_mode(phase_count=6, epic_id="beads-abc")
        assert mode == AutonomyMode.CHECKPOINT

    def test_autonomous_on_f(self):
        """Given 'f', returns AUTONOMOUS mode."""
        with patch('builtins.input', return_value='f'):
            mode = prompt_autonomy_mode(phase_count=6, epic_id="beads-abc")
        assert mode == AutonomyMode.AUTONOMOUS

    def test_batch_on_b(self):
        """Given 'b', returns BATCH mode."""
        with patch('builtins.input', return_value='b'):
            mode = prompt_autonomy_mode(phase_count=6, epic_id="beads-abc")
        assert mode == AutonomyMode.BATCH

    def test_displays_context(self, capsys):
        """Given phase count and epic, displays them."""
        with patch('builtins.input', return_value='c'):
            prompt_autonomy_mode(phase_count=6, epic_id="beads-abc123")

        captured = capsys.readouterr()
        assert "6" in captured.out
        assert "beads-abc123" in captured.out
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/checkpoints/interactive.py`
```python
from silmari_rlm_act.models import AutonomyMode


def prompt_autonomy_mode(phase_count: int, epic_id: str) -> AutonomyMode:
    """Prompt user for implementation execution mode.

    Args:
        phase_count: Number of implementation phases
        epic_id: Beads epic ID

    Returns:
        Selected AutonomyMode
    """
    print(f"\n{'='*60}")
    print("IMPLEMENTATION READY")
    print(f"{'='*60}")
    print(f"\nPlan phases: {phase_count}")
    print(f"Beads epic: {epic_id}")

    print("\nSelect execution mode:")
    print("  [C]heckpoint - pause at each phase for review (recommended)")
    print("  [F]ully autonomous - run all phases without stopping")
    print("  [B]atch - run groups of phases, pause between groups")

    valid_modes = {
        'c': AutonomyMode.CHECKPOINT,
        'f': AutonomyMode.AUTONOMOUS,
        'b': AutonomyMode.BATCH,
        '': AutonomyMode.CHECKPOINT,
    }

    while True:
        response = input("\nMode [C/f/b]: ").strip().lower()
        if response in valid_modes:
            return valid_modes[response]
        print(f"Invalid choice: '{response}'. Please enter C, F, or B.")
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_interactive.py::TestAutonomyModeSelection -v`

---

## TDD Cycle: Behavior 4 - File Selection Menu

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_interactive.py`
```python
from silmari_rlm_act.checkpoints.interactive import prompt_file_selection


class TestFileSelectionMenu:
    """Behavior 4: File Selection Menu."""

    def test_select_by_number(self, tmp_path):
        """Given '1', returns selected file."""
        files = [tmp_path / "file1.md", tmp_path / "file2.md"]
        for f in files:
            f.touch()

        with patch('builtins.input', return_value='1'):
            action, path = prompt_file_selection(files, "research")

        assert action == "selected"
        assert path == files[0]

    def test_search_on_s(self, tmp_path):
        """Given 's', returns search action."""
        with patch('builtins.input', return_value='s'):
            action, path = prompt_file_selection([], "research")

        assert action == "search"
        assert path is None

    def test_other_on_o(self, tmp_path):
        """Given 'o', returns other action."""
        with patch('builtins.input', return_value='o'):
            action, path = prompt_file_selection([], "research")

        assert action == "other"
        assert path is None

    def test_exit_on_e(self, tmp_path):
        """Given 'e', returns exit action."""
        with patch('builtins.input', return_value='e'):
            action, path = prompt_file_selection([], "research")

        assert action == "exit"
        assert path is None

    def test_invalid_number_reprompts(self, tmp_path):
        """Given invalid number then valid, reprompts."""
        files = [tmp_path / "file1.md"]
        files[0].touch()

        inputs = iter(["5", "1"])
        with patch('builtins.input', lambda _: next(inputs)):
            action, path = prompt_file_selection(files, "research")

        assert action == "selected"
        assert path == files[0]
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/checkpoints/interactive.py`
```python
def prompt_file_selection(
    files: list[Path],
    file_type: str
) -> tuple[str, Optional[Path]]:
    """Interactive menu to select a file.

    Args:
        files: List of discovered file paths
        file_type: "research" or "plans" for display

    Returns:
        Tuple of (action, path) where action is:
        - "selected": user picked a file
        - "search": user wants to search more days
        - "other": user wants to specify custom path
        - "exit": user wants to exit
    """
    print(f"\n{'='*60}")
    print(f"SELECT {file_type.upper()} FILE")
    print(f"{'='*60}")

    if files:
        print(f"\nFound {len(files)} {file_type} file(s):")
        for i, f in enumerate(files, 1):
            print(f"  [{i}] {f.name}")
    else:
        print(f"\nNo {file_type} files found.")

    print(f"\n  [S] Search again (specify days)")
    print(f"  [O] Other (specify path)")
    print(f"  [E] Exit")

    while True:
        response = input(f"\nChoice: ").strip()

        if response.lower() == 's':
            return ("search", None)
        elif response.lower() == 'o':
            return ("other", None)
        elif response.lower() == 'e':
            return ("exit", None)
        elif response.isdigit():
            idx = int(response) - 1
            if files and 0 <= idx < len(files):
                return ("selected", files[idx])
            max_num = len(files) if files else 0
            print(f"Invalid number. Enter 1-{max_num}")
        else:
            print("Invalid choice. Enter a number, S, O, or E.")
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_interactive.py::TestFileSelectionMenu -v`

---

## TDD Cycles: Behaviors 5-12 (Summary)

Due to space, I'll provide condensed test specifications:

### Behavior 5: Multi-line Input
```python
def test_collects_until_empty_line():
    inputs = iter(["line1", "line2", ""])
    with patch('builtins.input', lambda _: next(inputs)):
        result = collect_multiline_input()
    assert result == "line1\nline2"
```

### Behavior 6: Numeric Days Input
```python
def test_returns_default_on_empty():
    with patch('builtins.input', return_value=''):
        days = prompt_search_days()
    assert days == 7  # default

def test_returns_entered_number():
    with patch('builtins.input', return_value='14'):
        days = prompt_search_days()
    assert days == 14
```

### Behavior 7: Phase Continue Prompt
```python
def test_continue_on_y():
    with patch('builtins.input', return_value='y'):
        result = prompt_phase_continue("decomposition", ["file.md"])
    assert result["continue"] is True

def test_collects_feedback_on_n():
    inputs = iter(["n", "feedback line", ""])
    with patch('builtins.input', lambda _: next(inputs)):
        result = prompt_phase_continue("decomposition", ["file.md"])
    assert result["continue"] is False
    assert "feedback line" in result["feedback"]
```

### Behavior 8: Custom Path Input
```python
def test_validates_path_exists(tmp_path):
    test_file = tmp_path / "test.md"
    test_file.touch()

    with patch('builtins.input', return_value=str(test_file)):
        path = prompt_custom_path("research")
    assert path == test_file

def test_returns_none_for_nonexistent():
    with patch('builtins.input', return_value="/nonexistent/path"):
        path = prompt_custom_path("research")
    assert path is None
```

### Behavior 9: Cleanup Menu
```python
def test_skip_on_s():
    with patch('builtins.input', return_value='s'):
        action, days = prompt_cleanup_menu(count=5, oldest="2026-01-01")
    assert action == "skip"

def test_all_requires_confirmation():
    inputs = iter(["a", "ALL"])
    with patch('builtins.input', lambda _: next(inputs)):
        action, days = prompt_cleanup_menu(count=5, oldest="2026-01-01")
    assert action == "all"
```

### Behavior 10: Resume Point Selection
```python
def test_selects_phase_by_number():
    phases = ["tdd_planning", "multi_doc", "beads_sync"]
    with patch('builtins.input', return_value='2'):
        selected = prompt_resume_point(phases)
    assert selected == "multi_doc"
```

### Behavior 11-12: Invalid Input and Defaults
Already covered in other tests via the reprompt patterns.

---

## Success Criteria

**Automated:**
- [ ] All interactive prompt tests pass: `pytest silmari-rlm-act/tests/test_interactive.py -v`

**Manual:**
- [ ] All prompts display correctly in terminal
- [ ] Default selections work with Enter key
- [ ] Invalid inputs show helpful error messages
- [ ] Case-insensitive input handling works

## Summary

This phase implements the interactive prompts module with:
- Research action menu (Continue/Revise/Restart/Exit)
- Checkpoint resume prompt (Y/n)
- Autonomy mode selection (Checkpoint/Autonomous/Batch)
- File selection menu with numbered list
- Multi-line input collection
- Days/number input with defaults
- Phase continue prompts
- Custom path input with validation
- Cleanup menu with confirmation
- Resume point selection
