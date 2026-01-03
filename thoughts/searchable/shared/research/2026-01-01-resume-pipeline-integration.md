---
date: 2026-01-01T10:18:22-05:00
researcher: maceo
git_commit: 1b4d99573d75bae5e50f39db94db27ae338b849a
branch: main
repository: silmari-Context-Engine
topic: "Resume Pipeline Integration with Planning Orchestrator"
tags: [research, codebase, planning-pipeline, resume, interactive-prompts]
status: complete
last_updated: 2026-01-01
last_updated_by: maceo
last_updated_note: "Added design decisions from user feedback"
---

```
┌─────────────────────────────────────────────────────────────────┐
│          RESUME PIPELINE INTEGRATION RESEARCH                   │
│                  silmari-Context-Engine                         │
│                     2026-01-01                                  │
└─────────────────────────────────────────────────────────────────┘
```

# Research: Resume Pipeline Integration with Planning Orchestrator

**Date**: 2026-01-01T10:18:22-05:00
**Researcher**: maceo
**Git Commit**: 1b4d995
**Branch**: main
**Repository**: silmari-Context-Engine

## Research Question

How to fully incorporate `resume_pipeline.py` into `planning_orchestrator.py` to resume failed pipeline runs. When the user does not include research or plan documents, the script should read the `thoughts/` directory for research from the current day and present those as options to the user along with:
- **(S)earch again** - to pull the last N days
- **(O)ther** - for the user to specify a custom path

---

## 📊 Summary

The codebase has two separate entry points for the planning pipeline:
1. **`planning_orchestrator.py`** - Main CLI that runs the full pipeline from scratch
2. **`resume_pipeline.py`** - Standalone script for resuming from specific steps

These need to be unified. The research identified existing patterns for:
- Date-based file discovery in `thoughts/` directory
- Interactive menu selection
- CLI argument parsing with path handling
- Workflow checkpoint JSON files for tracking failed states

---

## 🎯 Detailed Findings

### Component 1: Current File Structure

| File | Purpose | Key Functions |
|------|---------|---------------|
| `planning_orchestrator.py:1-242` | Main CLI entry point | `main()`, `collect_prompt()`, `run_pipeline()` |
| `resume_pipeline.py:1-167` | Standalone resume script | `resume_pipeline()` with step dispatch |
| `planning_pipeline/pipeline.py:1-213` | Core pipeline class | `PlanningPipeline.run()` with 5 steps |
| `planning_pipeline/steps.py:1-405` | Step implementations | `step_research()`, `step_planning()`, etc. |
| `planning_pipeline/checkpoints.py:1-144` | Interactive checkpoints | `interactive_checkpoint_research()` |

### Component 2: Resume Pipeline Current Implementation

The `resume_pipeline.py` operates independently with these capabilities:

```python
# resume_pipeline.py:14-66
def resume_pipeline(step: str, **kwargs):
    """Resume pipeline from a specific step.

    Args:
        step: One of 'research', 'planning', 'decomposition', 'beads'
        **kwargs: Required arguments for the step
    """
```

**Current CLI Arguments:**
- `step` - positional, one of: `research`, `planning`, `decomposition`, `beads`
- `--research-path` / `--research_path` - Path to research document
- `--plan-path` / `--plan_path` - Path to plan document
- `--phase-files` / `--phase_files` - List of phase file paths
- `--epic-title` / `--epic_title` - Epic title for beads step
- `--additional-context` - Optional context for planning

### Component 3: Thoughts Directory Structure

```
thoughts/
├── global -> /home/maceo/thoughts/global (symlink)
├── maceo -> /home/maceo/thoughts/repos/silmari-Context-Engine/maceo (symlink)
├── shared -> /home/maceo/thoughts/repos/silmari-Context-Engine/shared (symlink)
└── searchable/
    └── shared/
        ├── research/
        │   ├── 2025-12-31-planning-command-architecture.md
        │   ├── 2025-12-31-python-deterministic-pipeline-control.md
        │   ├── 2025-12-31-codebase-architecture.md
        │   ├── 2025-12-31-context-engine-codebase.md
        │   └── 2026-01-01-baml-integration.md
        └── plans/
            ├── 2025-12-31-tdd-python-deterministic-pipeline.md
            └── 2026-01-01-tdd-planning-orchestrator.md
```

**File Naming Pattern**: `YYYY-MM-DD-description.md`

### Component 4: Workflow Checkpoints

Located in `.workflow-checkpoints/` directory with JSON structure:

```json
{
  "id": "c64eb05e-bf47-43f3-930a-0fca16a48351",
  "phase": "planning-failed",
  "timestamp": "2025-12-31T23:45:58.481662209Z",
  "state_snapshot": {
    "phase": "Plan",
    "context_usage": 0.0,
    "artifacts": [
      "./thoughts/shared/research/2025-12-31-context-engine-codebase.md"
    ],
    "errors": []
  },
  "git_commit": "93ecbef88ebb9432e7d16498822463defa7fec08"
}
```

### Component 5: Existing Interactive Patterns

#### Multi-line Input (`planning_orchestrator.py:61-79`)
```python
def collect_prompt() -> str:
    print("\nEnter your research prompt (blank line to finish):")
    print("-" * 40)
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)
```

#### Menu Selection (`checkpoints.py:17-36`)
```python
def _prompt_research_action() -> str:
    valid_actions = {'c': 'continue', 'r': 'revise', 's': 'restart', 'e': 'exit', '': 'continue'}
    while True:
        print("\nWhat would you like to do?")
        print("  [C]ontinue to planning (default)")
        print("  [R]evise research with additional context")
        print("  [S]tart over with new prompt")
        print("  [E]xit pipeline")
        response = input("\nChoice [C/r/s/e]: ").strip().lower()
        if response in valid_actions:
            return valid_actions[response]
```

### Component 6: Date-Based File Discovery Patterns

From `planning_pipeline/steps.py:26`:
```python
date_str = datetime.now().strftime('%Y-%m-%d')
```

From `orchestrator.py:1267` (session file discovery):
```python
existing = list(sessions_dir.glob("session-*.json"))
```

---

## 🏗️ Architecture: Integration Points

### Current Flow (No Resume)
```
planning_orchestrator.py
    └── run_pipeline()
        └── PlanningPipeline.run()
            ├── step_research()
            ├── step_planning()
            ├── step_phase_decomposition()
            └── step_beads_integration()
```

### Proposed Flow (With Resume)
```
planning_orchestrator.py
    ├── [NEW] --resume flag
    │   └── discover_resumable_files()
    │       ├── find_recent_research()
    │       └── find_recent_plans()
    ├── [NEW] Interactive file selection
    │   ├── Show current day files
    │   ├── (S)earch N days back
    │   └── (O)ther path input
    └── run_pipeline() OR resume_from_step()
```

---

## 📁 Code References

### Primary Files to Modify
- `planning_orchestrator.py:20-58` - Add resume-related CLI arguments
- `planning_orchestrator.py:191-241` - Modify main() to handle resume flow

### Files to Reference for Patterns
- `resume_pipeline.py:14-66` - Existing step dispatch logic to integrate
- `planning_pipeline/checkpoints.py:17-36` - Interactive menu pattern
- `orchestrator.py:345-368` - Numbered menu selection pattern

### Helper Functions Needed
- `planning_pipeline/helpers.py` - Add `discover_thoughts_files()` function

---

## 🔧 Key Implementation Details

### 1. File Discovery Function

Based on existing patterns, a new function to discover research/plan files:

```python
# Pattern from thoughts/ structure
from pathlib import Path
from datetime import datetime, timedelta

def discover_thoughts_files(
    thoughts_dir: Path,
    file_type: str,  # "research" or "plans"
    days_back: int = 0
) -> list[Path]:
    """Discover research or plan files from thoughts directory.

    Args:
        thoughts_dir: Base thoughts directory (e.g., project/thoughts)
        file_type: "research" or "plans"
        days_back: How many days back to search (0 = today only)

    Returns:
        List of matching file paths sorted by date descending
    """
    search_dir = thoughts_dir / "shared" / file_type
    if not search_dir.exists():
        # Try searchable path
        search_dir = thoughts_dir / "searchable" / "shared" / file_type

    if not search_dir.exists():
        return []

    cutoff_date = datetime.now() - timedelta(days=days_back)
    cutoff_str = cutoff_date.strftime('%Y-%m-%d')

    files = []
    for f in search_dir.glob("*.md"):
        # Files are named YYYY-MM-DD-description.md
        date_part = f.stem[:10]  # First 10 chars = YYYY-MM-DD
        if date_part >= cutoff_str:
            files.append(f)

    return sorted(files, key=lambda f: f.stem, reverse=True)
```

### 2. Interactive File Selection Menu

Based on `checkpoints.py` and `orchestrator.py` patterns:

```python
def prompt_file_selection(
    files: list[Path],
    file_type: str
) -> tuple[str, Path | None]:
    """Interactive menu to select a file or search/specify other.

    Returns:
        Tuple of (action, path) where action is:
        - "selected": user picked a file, path is the file
        - "search": user wants to search more days
        - "other": user wants to specify custom path
        - "exit": user wants to exit
    """
    print(f"\n{'='*60}")
    print(f"SELECT {file_type.upper()} FILE")
    print(f"{'='*60}")

    if files:
        print(f"\nFound {len(files)} {file_type} file(s) from today:")
        for i, f in enumerate(files, 1):
            print(f"  [{i}] {f.name}")
    else:
        print(f"\nNo {file_type} files found from today.")

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
            if 0 <= idx < len(files):
                return ("selected", files[idx])
            print(f"Invalid number. Enter 1-{len(files)}")
        else:
            print("Invalid choice. Enter a number, S, O, or E.")
```

### 3. CLI Argument Changes

```python
# Add to parse_args() in planning_orchestrator.py
parser.add_argument(
    "--resume", "-r",
    action="store_true",
    help="Resume from a previous step (interactive file selection)"
)
parser.add_argument(
    "--resume-step",
    choices=["planning", "decomposition", "beads"],
    help="Step to resume from (requires --research-path or --plan-path)"
)
parser.add_argument(
    "--research-path", "--research_path",
    dest="research_path",
    help="Path to existing research document (for resume)"
)
parser.add_argument(
    "--plan-path", "--plan_path",
    dest="plan_path",
    help="Path to existing plan document (for resume)"
)
```

---

## 📋 Integration Steps Summary

| Step | Description | Files Modified |
|------|-------------|----------------|
| 1 | Add file discovery helper | `planning_pipeline/helpers.py` |
| 2 | Add interactive selection | `planning_pipeline/checkpoints.py` |
| 3 | Add CLI arguments | `planning_orchestrator.py` |
| 4 | Integrate resume logic | `planning_orchestrator.py:main()` |
| 5 | Import step functions | Use from `resume_pipeline.py` |
| 6 | Update exports | `planning_pipeline/__init__.py` |

---

## 🔗 Historical Context (from thoughts/)

| Document | Relevance |
|----------|-----------|
| `thoughts/shared/research/2025-12-31-python-deterministic-pipeline-control.md` | Original pipeline design decisions |
| `thoughts/shared/plans/2025-12-31-tdd-python-deterministic-pipeline.md` | TDD plan for pipeline implementation |

---

## ✅ Design Decisions

| Question | Decision |
|----------|----------|
| **Checkpoint Integration** | Yes - auto-detect from `.workflow-checkpoints/` JSON files |
| **Multiple Files Sort Order** | Alphabetical (by filename) |
| **Path Storage** | Absolute paths in checkpoint files |
| **Cleanup Strategy** | Warn at 30 days with interactive cleanup menu |

### Checkpoint Cleanup Menu

When checkpoints exceed 30 days, present:
```
⚠️  You have 45 checkpoint files (oldest: 2025-11-15)

  [O] Delete oldest 10 days
  [L] Delete last N days (you specify)
  [A] Delete all (requires confirmation)
  [S] Skip cleanup

Choice: _
```

For **(A)ll** option, require double confirmation:
```
Choice: a
⚠️  This will delete ALL 45 checkpoint files. Type 'ALL' to confirm: _
```

### Auto-Detection Flow

When `--resume` is passed without explicit paths:
1. Read `.workflow-checkpoints/*.json` files
2. Find most recent failed checkpoint
3. Extract `state_snapshot.artifacts` (absolute paths)
4. Auto-populate research/plan paths
5. Present user with detected state for confirmation

```python
def detect_resumable_checkpoint(checkpoints_dir: Path) -> dict | None:
    """Find most recent failed checkpoint.

    Returns:
        Dict with 'phase', 'artifacts', 'timestamp' or None if no checkpoints
    """
    if not checkpoints_dir.exists():
        return None

    checkpoints = []
    for f in checkpoints_dir.glob("*.json"):
        with open(f) as fp:
            data = json.load(fp)
            checkpoints.append(data)

    if not checkpoints:
        return None

    # Sort by timestamp descending
    checkpoints.sort(key=lambda c: c.get("timestamp", ""), reverse=True)
    return checkpoints[0]
```
