# Phase 2: File Discovery & Selection

## Overview
Add functions to discover research/plan files from `thoughts/` directory and present interactive selection menu.

## Dependencies

| Requires | Blocks |
|----------|--------|
| Phase 1: Checkpoint Management Module | Phase 3: CLI Integration |

## Changes Required

### 1. Add file discovery function
**File**: `planning_pipeline/helpers.py`

| Function | Line | Description |
|----------|------|-------------|
| `discover_thoughts_files()` | (append) | Discover research or plan files from thoughts directory |

**Function Signature**:
```python
def discover_thoughts_files(
    project_path: Path,
    file_type: str,  # "research" or "plans"
    days_back: int = 0
) -> list[Path]
```

### 2. Add interactive selection functions
**File**: `planning_pipeline/checkpoints.py`

| Function | Line | Description |
|----------|------|-------------|
| `prompt_file_selection()` | (append) | Interactive menu to select a file |
| `prompt_search_days()` | (append) | Prompt user for number of days to search |
| `prompt_custom_path()` | (append) | Prompt user to enter a custom file path |
| `prompt_checkpoint_cleanup()` | (append) | Interactive cleanup menu for old checkpoints |

### 3. Update exports
**File**: `planning_pipeline/__init__.py:9`
- Add: `discover_thoughts_files` from helpers
- Add: `prompt_file_selection`, `prompt_search_days`, `prompt_custom_path`, `prompt_checkpoint_cleanup` from checkpoints

## Human-Testable Function
`prompt_file_selection(files: list[Path], file_type: str) -> tuple[str, Path | None]`

**Test Procedure**:
1. Run interactive test:
```python
from pathlib import Path
from planning_pipeline import discover_thoughts_files, prompt_file_selection

files = discover_thoughts_files(Path.cwd(), "research", days_back=7)
print(f"Found {len(files)} files")
action, path = prompt_file_selection(files, "research")
print(f"Action: {action}, Path: {path}")
```
2. Verify: Menu displays correctly with numbered options
3. Verify: Selecting a number returns `("selected", <Path>)`
4. Verify: Pressing `S` returns `("search", None)`
5. Verify: Pressing `E` returns `("exit", None)`

## Success Criteria

### Automated Verification
- [ ] Unit tests pass: `python -m pytest planning_pipeline/tests/test_helpers.py -v`
- [ ] Unit tests pass: `python -m pytest planning_pipeline/tests/test_checkpoints.py -v`
- [ ] Module imports work: `python -c "from planning_pipeline import discover_thoughts_files, prompt_file_selection"`

### Manual Verification
- [ ] `discover_thoughts_files()` finds today's research files
- [ ] `discover_thoughts_files()` with `days_back=7` finds last week's files
- [ ] Files are sorted alphabetically by filename
- [ ] `prompt_file_selection()` displays menu correctly
- [ ] All menu options (S, O, E, number) work correctly
- [ ] Cleanup menu options all work as expected
